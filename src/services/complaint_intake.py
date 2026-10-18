"""Wires `scripts/fraud_engine.py` (a pure script, no DB access) into the
`create_ticket` tool (§4.1 FIN05-Backend-Handoff.md).

Data Brief §4.2: `complaints.fraud_signals` is "computed by the service layer from data,
not filled in by the agent" — this is that service layer. The `create_ticket` tool stays
thin and computes no signals itself; this is the ONLY place that converts DB data
(SQLAlchemy rows) into the `LedgerIndex` format (list[dict] like JSONL) that
`fraud_engine.py` needs.

Uses `FraudEngine.evaluate()` to compute ALL signals (reusing the engine as-is after it
passed 16 dataset validation groups, not rewritten — codes other than FS-06 are still stored
in `complaints.fraud_signals`; surplus data is harmless).
The escalate/priority decision is then made by `src.tools.fraud_policy.evaluate_escalation()`
— MVP scope is `FS-06` only (PRD §5). `FraudEngine.decide()` is NOT used
— that is the old 2-tier policy of the original dataset, now only used internally by
`scripts/validate_dataset.py` to self-validate the dataset, never applied to the product.
"""
from __future__ import annotations

import datetime as dt
from functools import lru_cache
from typing import Any

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from scripts.fraud_engine import FraudEngine, LedgerIndex
from src.config import DATA_SCHEMA_DIR
from src.db.models import AuthSession, BankAccount, Complaint, Ticket, Transaction, User, Wallet
from src.tools.create_ticket import create_ticket as _create_ticket

# A2 (ADR-025 decision 5) — ≈300-400 Vietnamese words: enough to narrate one case in
# detail, many times a typical complaint, while blocking a 20,000-character flood.
MAX_DESCRIPTION_CHARS = 2000


@lru_cache(maxsize=1)
def _load_fraud_config() -> dict:
    path = DATA_SCHEMA_DIR / "fraud_signals.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _rows_as_dicts(session: Session, model: Any) -> list[dict]:
    cols = model.__table__.columns.keys()
    return [{c: getattr(row, c) for c in cols} for row in session.scalars(select(model))]


def _build_engine(session: Session) -> FraudEngine:
    """Load all existing reference data from the DB into a LedgerIndex. At demo scale
    (60k transactions, a few hundred rows in other tables) reloading on every call is fast
    enough — no cache needed, avoiding the risk of reading stale data after a new
    ticket/complaint."""
    idx = LedgerIndex(
        _rows_as_dicts(session, User),
        _rows_as_dicts(session, Wallet),
        _rows_as_dicts(session, BankAccount),
        _rows_as_dicts(session, Transaction),
        _rows_as_dicts(session, Complaint),
        _rows_as_dicts(session, AuthSession),
        _rows_as_dicts(session, Ticket),
    )
    return FraudEngine(_load_fraud_config(), idx)


def create_ticket_with_fraud_check(
    session: Session,
    *,
    user_id: str,
    complaint_type: str,
    scope: str,
    description_raw: str,
    trans_id: str | None = None,
    otp_disclosed: bool = False,
    now: dt.datetime | None = None,
    # ADR-044 — the EFFECTIVE thread_id of the turn that produced this complaint, written into
    # Complaint.thread_id at CREATION (PERMANENTLY NULLABLE if None — old callers/REST without a
    # chat session). Threaded through to _create_ticket, NEVER inferred.
    thread_id: str | None = None,
) -> dict[str, Any]:
    """Compute fraud signals from DB data, then create the ticket — instead of letting the agent
    pass `fraud_signals` by hand (risk of the agent forgetting/fabricating signals). This is
    the entry point the agent/API should call instead of `create_ticket` directly when
    `trans_id` has a value; the not_found case (`trans_id=None`) can still compute
    FS-09/FS-10/FS-11 (no transaction needed) before creating the ticket.
    """
    now = now or dt.datetime.utcnow()

    # A2 — 2,000-character cap, enforced HERE because this is where BOTH write paths CONVERGE:
    # REST (`main.py:538`) and AGENT (`customer_tools.py:620`). Putting the cap only on
    # `CreateTicketRequest` misses the agent path — the `create_ticket` tool has NO `args_schema`;
    # it uses bare type hints, so Pydantic applies no constraints. Exactly the ADR-019/024 lesson:
    # validating only at the route does not protect the second door.
    #
    # REJECT rather than TRUNCATE: truncating means altering the customer's statement — against
    # hard constraint 3 and damaging its evidentiary value, the same reason group A must not be
    # masked on write.
    if len(description_raw) > MAX_DESCRIPTION_CHARS:
        raise ValueError(
            f"description_raw {len(description_raw)} ký tự, vượt trần "
            f"{MAX_DESCRIPTION_CHARS}. Không tự cắt bớt lời khai của khách — "
            f"tách thành nhiều khiếu nại hoặc yêu cầu khách tóm tắt."
        )

    engine = _build_engine(session)
    # IMPORTANT: take tx from engine.idx.tx_by_id (do not query Transaction separately) —
    # LedgerIndex attaches the "_created" key on the object itself while building the index;
    # evaluate()/receiver_first_time() read "_created" from that same object, so a detached dict
    # would lack the key and break with KeyError.
    tx_dict = engine.idx.tx_by_id.get(trans_id) if trans_id is not None else None

    fired = engine.evaluate(
        user_id=user_id,
        tx=tx_dict,
        complaint_at=now,
        utterance_text=description_raw,
        otp_disclosed=otp_disclosed,
        refund_dest_ref=None,  # not determined at ticket-creation time, only available at propose_resolution
    )

    return _create_ticket(
        session,
        user_id=user_id,
        complaint_type=complaint_type,
        scope=scope,
        description_raw=description_raw,
        trans_id=trans_id,
        otp_disclosed=otp_disclosed,
        fraud_signals=fired,
        now=now,
        thread_id=thread_id,
    )


def merge_fraud_signals(
    session: Session,
    *,
    thread_id: str,
    utterance_text: str,
    add_code: list[str] | None = None,
) -> list[str] | None:
    """PIECE 4 (⑨/FS-13) — score fraud signals on a LATER TURN and MERGE them into the
    complaint already created for that same thread.

    Before this version, `engine.evaluate()` was called EXACTLY ONCE, with
    `utterance_text=description_raw` at TICKET CREATION. Measured consequence: even if FS-13
    existed, it could only catch customers who SELF-REPORTED "someone was guiding me" in their
    very first description — and a customer who calls what happened a "wrong transfer" would
    never trigger it. The signal only fired when we no longer needed it.

    Returns the signal list AFTER merging, or `None` if no complaint is found for the thread
    (not an error — the thread hasn't created a ticket yet).

    🔴 MERGE, NEVER OVERWRITE. The later turn calls `evaluate()` with `tx=None`, so
    FS-01…08/FS-12 CANNOT be recomputed (they need a transaction). Directly assigning
    `complaint.fraud_signals = fired_moi` would WIPE OUT the signals caught at ticket
    creation — **including FS-06, the ONLY signal that escalates** — silently, with no error,
    no log, nobody noticing. A union is idempotent: calling it any number of times yields the
    same result.

    Keyed by `Complaint.thread_id` (ADR-044), NEVER guessed from timestamps.
    ⚠️ DECLARED LIMITATION: one thread may carry several complaints; this function picks the
    LATEST by `created_at`. On the current call path that is structurally correct — gate ⑨
    fires AT MOST ONCE per thread, right after a `create_ticket` — so "latest" is exactly the
    ticket just created. If another call path appears later, re-read this sentence before
    using it.
    """
    complaint = session.scalar(
        select(Complaint)
        .where(Complaint.thread_id == thread_id)
        .order_by(Complaint.created_at.desc())
        .limit(1)
    )
    if complaint is None:
        return None

    engine = _build_engine(session)
    fired = engine.evaluate(
        user_id=complaint.user_id,
        tx=None,  # the later turn is not tied to any specific transaction
        complaint_at=complaint.created_at,
        utterance_text=utterance_text,
        otp_disclosed=False,  # already computed at ticket creation; DO NOT lower old flags here
    )
    prev = list(complaint.fraud_signals or [])
    merged_items = sorted(set(prev) | set(fired) | set(add_code or []))
    if merged_items != sorted(set(prev)):
        complaint.fraud_signals = merged_items
        session.flush()
    return merged_items


def flag_human_handoff(
    session: Session,
    *,
    user_id: str,
    reason: str,
    ticket_id: str | None = None,
    now: dt.datetime | None = None,
    # ADR-044 — used ONLY when creating a NEW ticket (the ticket_id=None branch below), threaded
    # down to create_ticket_with_fraud_check. PO-agent 19/08: the ticket-creation path is NOT only
    # the create_ticket tool — flag_human_handoff also creates a ticket when the customer asks for
    # a human without having one; missing thread_id HERE would mean the kind of ticket that NEEDS a
    # transcript most (handoff) would have NO transcript.
    thread_id: str | None = None,
) -> dict[str, Any]:
    """CTRL-001 (FIN05_QA_TestCases.jsonl, 2026-08-11) — the customer actively asks to talk
    to a real person (ISO/IEC 25059 'user controllability'). The CSKH architecture is still
    asynchronous (dashboard, not live chat) — this function creates/flags a REAL Ticket with
    `human_handoff_requested=True` so CSKH can see and prioritise it, WITHOUT pretending a
    person is chatting live right now.

    `ticket_id`: if the agent HAS ALREADY created a ticket for exactly the issue being
    discussed in this conversation (avoiding duplicates, same principle as create_ticket)
    — only set the flag on that ticket, which MUST belong to `user_id` (stops an agent tricked
    into flagging someone else's ticket via this parameter).
    No `ticket_id` — create a NEW ticket, complaint_type='other' (a customer asking for a
    human doesn't necessarily describe one of the 4 specific complaint types).
    """
    now = now or dt.datetime.utcnow()

    if ticket_id is not None:
        ticket = session.get(Ticket, ticket_id)
        if ticket is None:
            raise ValueError(f"ticket_id không tồn tại: {ticket_id}")
        complaint = session.get(Complaint, ticket.complaint_id)
        if complaint is None or complaint.user_id != user_id:
            raise ValueError(f"ticket_id không thuộc user_id đang chat: {ticket_id}")
        ticket.human_handoff_requested = True
        # ADR-044 item 4 — the real HANDOFF timestamp, NOT when the ticket was created
        # (ticket.created_at already exists, with a completely different meaning). The UI draws a
        # conversation divider at this timestamp. `updated_at` also changes per that column's
        # existing
        # convention (every ticket edit); the two columns answer two different questions
        # ("when was it last edited" vs "when was it handed off") — not merged.
        ticket.handoff_at = now
        ticket.updated_at = now
        session.flush()
        return {"ticket_id": ticket.ticket_id, "human_handoff_requested": True, "created_new_ticket": False}

    created = create_ticket_with_fraud_check(
        session,
        user_id=user_id,
        complaint_type="other",
        # 🔴 BEFORE 17/08 this was "internal_wallet" — a HARD-CODED CONSTANT, i.e. this path
        # FABRICATED one of the three real scopes without looking up any transaction.
        #
        # The tester caught it via a DB diff of a single timed-out turn on the measurement stack:
        # `tool_results` 0->1 (only ONE row, and it was create_ticket),
        # `investigation_logs` 0->0, `trans_id` empty — and yet
        # `scope=internal_wallet`. No transaction had been looked up.
        #
        # The value 'unknown' was added to the CHECK constraint on 11/08 FOR EXACTLY THIS CASE
        # (see models.py): "previously the agent was forced to guess one of the 3 real values...
        # let CSKH determine it manually instead of the AI fabricating". The mechanism had existed
        # for
        # six days; this fallback path was never updated — the fix was applied to the AGENT path and
        # missed the CODE path.
        #
        # Applies to BOTH callers (graph.py timeout · request_human_handoff):
        # neither path looks up a transaction, so any specific scope value here would be fabricated.
        scope="unknown",
        description_raw=reason,
        trans_id=None,
        now=now,
        thread_id=thread_id,
    )
    ticket = session.get(Ticket, created["ticket_id"])
    ticket.human_handoff_requested = True
    # ADR-044 item 4 — a NEW ticket born FROM this very handoff turn (no existing
    # ticket_id to flag), so handoff_at == created_at with the SAME value
    # `now` — correct, not a coincidence: handoff and ticket creation happen "simultaneously" in
    # business terms on this branch.
    ticket.handoff_at = now
    session.flush()
    return {**created, "human_handoff_requested": True, "created_new_ticket": True}
