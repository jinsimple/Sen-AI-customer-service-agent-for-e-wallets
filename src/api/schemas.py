"""Pydantic request bodies for the tool endpoints — boundary validation, before touching
the business logic in src/tools/.

Security fix: there is NO LONGER any field carrying the caller's identity (user_id,
requesting_user_id, approved_by, rejected_by, created_by, requested_by).
Previously the client declared these fields in the body — meaning anyone calling the API
could impersonate any user (e.g. claim approved_by = some supervisor to approve a refund).
Identity now ALWAYS comes from the signed JWT (src/auth.py,
`Depends(get_current_user)` in src/api/main.py), with no other path."""
from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.config import RAG_SEARCH_TOP_K


class LookupTransactionRequest(BaseModel):
    trans_id: str | None = None
    rec_code: str | None = None
    phone: str | None = None
    amount: int | None = None
    date_from: dt.datetime | None = None
    date_to: dt.datetime | None = None


class GetCustomerHistoryRequest(BaseModel):
    days: int = 90
    limit_transactions: int = 20


class CreateTicketRequest(BaseModel):
    complaint_type: str
    scope: str
    # A2 — 2,000-character cap (ADR-025 decision 5). Enforcing it HERE is the only layer that
    # is ACCURATE per CHARACTER; the DB layer can't do it because the column is encrypted
    # (see models.py).
    description_raw: str = Field(max_length=2000)
    trans_id: str | None = None
    otp_disclosed: bool = False
    # fraud_signals is not accepted from the caller — the service layer (complaint_intake.py)
    # computes them from DB data via fraud_engine.py (Data Brief §4.2: "computed by the service
    # layer, not filled in by the agent").


class ProposeResolutionRequest(BaseModel):
    ticket_id: str
    action_type: str
    rationale: str
    amount: int | None = None
    destination_ref: str | None = None
    cited_tool_result_ids: list[str] | None = None


class ApproveResolutionRequest(BaseModel):
    """AUTH5-04/05/05B (Auth Flow upgrade 2026-08-12) — the supervisor must first request an
    OTP for EXACTLY this resolution_id (POST .../request-approval-otp) before approving —
    an OTP already verified for another case cannot be reused.

    `session_id` (race-condition fix, 2026-08-13 — same reason as OtpVerifyRequest)
    — looked up directly by the AuthSession primary key, no longer "latest by
    resolution_id"."""

    session_id: str
    otp_code: str


class RejectResolutionRequest(BaseModel):
    """ADR-019 — a rejection MUST include a structured reason.

    `Literal` rather than `str`: a wrong value is blocked right at the schema layer with a
    message listing all options, instead of letting a CHECK constraint throw an
    IntegrityError 500 at the user. Two layers guarding the same rule is DELIBERATE —
    the schema handles user experience, the CHECK handles integrity even if someone writes
    straight to the DB (full reasoning in ADR-019).

    `note` (ADR-024, TM-03 security sign-off) — free-text note on rejection.
    PII scrubbing + the real injection flag happen in the route (`src/api/main.py`), NOT
    here: the schema only cares about shape (length, present/missing) and never touches
    sensitive data before it reaches the scrub layer.

    `max_length=500` catches a 501-character note at the SCHEMA LAYER (422, clear message)
    rather than letting the DB-layer CHECK constraint throw IntegrityError 500 — the same
    "schema handles UX, CHECK handles integrity" philosophy applied to `reason` above.

    Empty/whitespace-only is normalised INTO missing (`None`) before applying the rule
    "required when reason='khac' (other)": this is the classic bypass — a validator that only
    checks `note is not None` lets a single space through.
    """

    reason: Literal[
        "sai_so_lieu",
        "sai_phan_loai",
        "thieu_can_cu",
        "sai_chinh_sach",
        "trung_case",
        "khach_rut",
        "khac",
    ]
    note: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _note_required_when_other(self) -> RejectResolutionRequest:
        if self.note is not None and not self.note.strip():
            self.note = None
        if self.reason == "khac" and not self.note:
            raise ValueError(
                "note bắt buộc khi reason='khac' — 'lý do khác' không có ghi chú "
                "thì bản ghi kiểm toán rỗng nghĩa"
            )
        return self


class EscalateTicketRequest(BaseModel):
    ticket_id: str
    target: str
    reason: str


class LoginRequest(BaseModel):
    """Login with a real password (decision 2026-08-12 — replaced the earlier hand-picked
    phone+role flow). There is NO `role` field any more — the role comes from the user found
    via `phone` in the DB, not declared by the client (the "identity is never self-declared"
    principle applied throughout this file)."""

    phone: str
    password: str


class RefreshTokenRequest(BaseModel):
    """AUTH5-02/03 (Auth Flow upgrade 2026-08-12) — refresh_token is NOT a JWT (a random
    string, see src/auth.py::mint_refresh_token), sent in the body because the backend has no
    access to browser cookies (BFF architecture — only the Next.js route handler reads the
    httpOnly cookie and forwards it)."""

    refresh_token: str


class RequestMoreInfoRequest(BaseModel):
    note: str | None = None


class OtpVerifyRequest(BaseModel):
    """AUTH5-01 (Auth Flow upgrade 2026-08-12) — `security_answer` was removed:
    security questions are no longer an authenticator (NIST SP 800-63B-4); the OTP code is
    the only step-up factor.

    `session_id` (race-condition fix, 2026-08-13) — mandatory, must match EXACTLY the
    AuthSession returned by the /auth/otp/request just called. Previously verify only looked
    up "the user's latest AuthSession" — under real concurrent load (FastAPI runs sync routes
    in a threadpool, several threads writing to SQLite WAL), a verify request could read an
    OLD snapshot that didn't yet see the newly created AuthSession, compare against the
    previous session's OTP and wrongly reject a correct code. Looking up by session_id
    (primary key) removes that ambiguity entirely — no more reliance on "latest by time"."""

    session_id: str
    otp_code: str


class AgentChatRequest(BaseModel):
    # max_length=4000 (CONSUME-001, FIN05_QA_TestCases.jsonl, OWASP LLM10:2025
    # Unbounded Consumption) — previously there was NO limit; one abnormally long message
    # (e.g. a flood of tens of thousands of characters) went straight into the LLM context,
    # burning tokens/money uncontrollably. 4,000 characters is ample for real customer-service
    # conversations (the longest complaint in the sample dataset is under 500 characters), and
    # FastAPI/Pydantic return a clear 422 when exceeded — no hand-written code needed.
    message: str = Field(max_length=4000)
    # EXPLICIT flag from the frontend (scratchpad/nhap-cong-thu-slot-sau-otp.md
    # item 1) — signals that this turn is ChatClient.tsx::submitOtp() AUTOMATICALLY RE-SENDING the
    # message that was blocked by OTP, rather than inferring it from the time gap between
    # otp_verified_at and the message's arrival (a COMPLETELY different message typed right after
    # OTP would be misclassified if measured by timestamps). Default False preserves behaviour for
    # every old client/test that doesn't send this field.
    vua_xac_thuc_de_gui_lai: bool = False


class PolicySearchRequest(BaseModel):
    """Before this version there was only `query`, and the endpoint did NOT pass `k` — every
    call returned exactly `RAG_SEARCH_TOP_K`=4 regardless of what the client sent.

    The number 4 is intentional. IGNORING the client's `k` was not: Pydantic by default
    **silently drops unknown fields**, so a client sending `{"query":..., "k":3}` got
    4 results with HTTP 200 and not a single warning. Both the tester's measurement suite and
    the tech-lead's own probes sent `k` and read "4 results" without anyone asking why — same
    family as `skipped_missing_chunk`: a silent branch that looks exactly like a valid result.

    `extra="forbid"` kills that whole FAMILY of bugs for this model, not just the `k` case:
    a wrong field name is now a 422, not a silently wrong number.

    Cap `le=8`: the client-supplied `k` goes straight into the vector query; without a cap a
    single request could pull out the whole store.
    """

    model_config = ConfigDict(extra="forbid")

    query: str
    top_k: int = Field(default=RAG_SEARCH_TOP_K, ge=1, le=8)
    # ADR-062 — Layer 1 (scope filter, ADR-061) needs to know which ticket CSKH is looking up
    # policy FOR, to filter by the right transaction scope. Optional: NOT passing it
    # = the OLD behaviour (no scope filtering), old clients don't break. The route looks up
    # `Complaint.scope` itself — it never trusts a client-declared `scope` (the client may not
    # STATE the scope itself, only STATE which ticket it is looking up).
    complaint_id: str | None = None


class LiveChatWsTicketRequest(BaseModel):
    """Live chat (2026-08-11) — the customer clicks "talk to a human" for an EXISTING ticket
    (human_handoff_requested, created via request_human_handoff)."""
    ticket_id: str


class LiveChatCsatRequest(BaseModel):
    score: int = Field(ge=1, le=5)
