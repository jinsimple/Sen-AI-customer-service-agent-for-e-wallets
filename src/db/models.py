"""FIN-05 — SQLAlchemy 2.0 models.

Source of truth for the schema: docs/FIN05-Data-Brief.md §4.1 (ERD) and §4.2 (table
definitions). Every change here MUST be synced back to that document — this is where the
invariants I1-I7 (§6.2) and the HITL constraints (BR-10, BR-11) are enforced at the DB
layer, not only at the prompt layer (see Data Brief §6.6 "guardrails are tested at the
service/DB layer, not the prompt layer").
"""
from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.db.crypto_types import EncryptedString, EncryptedText


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Identity & accounts
# ---------------------------------------------------------------------------


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        # partner_admin — a separate role for the e-wallet partner, distinct from
        # supervisor (internal CSKH lead). ONLY this role may upload/delete
        # policy/FAQ documents (src/rag/, src/api/main.py::/policy-docs).
        CheckConstraint(
            "role IN ('customer','cskh','supervisor','partner_admin')", name="ck_users_role"
        ),
    )

    user_id: Mapped[str] = mapped_column(String, primary_key=True)
    role: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    kyc_level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    security_question: Mapped[str | None] = mapped_column(Text, nullable=True)
    security_answer_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Password login (decision 2026-08-12, replacing the earlier hand-picked phone+role
    # flow) — salted argon2id (same library/pattern used
    # for security_answer_hash, see scripts/gen_dataset.py). Nullable for technical migration
    # reasons (adding a column to a table that already has data), but IN PRACTICE
    # it is always fully seeded — verify_otp creates no "password-less users" after this change.
    password_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False)


class Wallet(Base):
    __tablename__ = "wallets"
    __table_args__ = (
        CheckConstraint("status IN ('active','frozen','closed')", name="ck_wallets_status"),
        CheckConstraint("balance >= 0", name="ck_wallets_balance_nonneg"),
    )

    wallet_id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    balance: Mapped[int] = mapped_column(Integer, nullable=False)  # VND, INTEGER — I7
    status: Mapped[str] = mapped_column(String, nullable=False, default="active")


class BankAccount(Base):
    __tablename__ = "bank_accounts"
    __table_args__ = (
        CheckConstraint("status IN ('active','closed')", name="ck_bank_accounts_status"),
    )

    bank_account_id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    bank_code: Mapped[str] = mapped_column(String, nullable=False)
    # Transparently encrypted at the ORM layer (src/db/crypto_types.py) — the full number must
    # still be stored (BR-07, account holders may see their own full number), but the SQLite file
    # on disk now only contains ciphertext, not raw account numbers.
    account_no: Mapped[str] = mapped_column(EncryptedString, nullable=False)
    card_last4: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="active")
    linked_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False)


# ---------------------------------------------------------------------------
# Transactions — core table
# ---------------------------------------------------------------------------

_SCOPE_DIRECTION_CHECK = """
    (
        scope = 'internal_wallet'
        AND send_wal_id IS NOT NULL AND rec_wal_id IS NOT NULL
        AND send_bank_account_id IS NULL AND rec_bank_account_id IS NULL
    ) OR (
        scope = 'from_bank'
        AND send_bank_account_id IS NOT NULL AND rec_wal_id IS NOT NULL
        AND send_wal_id IS NULL AND rec_bank_account_id IS NULL
    ) OR (
        scope = 'to_bank'
        AND send_wal_id IS NOT NULL AND rec_bank_account_id IS NOT NULL
        AND send_bank_account_id IS NULL AND rec_wal_id IS NULL
    )
"""


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending','processing','success','failed','refunded','on_hold')",
            name="ck_transactions_status",
        ),
        CheckConstraint(
            "scope IN ('internal_wallet','from_bank','to_bank')",
            name="ck_transactions_scope",
        ),
        CheckConstraint(
            "channel IN ('p2p','bank_transfer','card_topup','withdrawal')",
            name="ck_transactions_channel",
        ),
        CheckConstraint("amount > 0", name="ck_transactions_amount_positive"),
        CheckConstraint("fee >= 0", name="ck_transactions_fee_nonneg"),
        # I2 — each scope matches exactly one sender/receiver combination (Data Brief §4.2/§6.2)
        CheckConstraint(_SCOPE_DIRECTION_CHECK, name="ck_transactions_scope_direction_i2"),
    )

    trans_id: Mapped[str] = mapped_column(String, primary_key=True)
    rec_code: Mapped[str] = mapped_column(String, nullable=False)
    send_wal_id: Mapped[str | None] = mapped_column(ForeignKey("wallets.wallet_id"), nullable=True)
    send_bank_account_id: Mapped[str | None] = mapped_column(
        ForeignKey("bank_accounts.bank_account_id"), nullable=True
    )
    rec_wal_id: Mapped[str | None] = mapped_column(ForeignKey("wallets.wallet_id"), nullable=True)
    rec_bank_account_id: Mapped[str | None] = mapped_column(
        ForeignKey("bank_accounts.bank_account_id"), nullable=True
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    fee: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String, nullable=False)
    scope: Mapped[str] = mapped_column(String, nullable=False)
    channel: Mapped[str] = mapped_column(String, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    des: Mapped[str | None] = mapped_column(Text, nullable=True)


class TransactionEvent(Base):
    __tablename__ = "transaction_events"
    __table_args__ = (
        CheckConstraint(
            "event_type IN ('initiated','debited','sent_to_partner','partner_ack',"
            "'credited','failed','held','refund_initiated','refunded')",
            name="ck_events_event_type",
        ),
        CheckConstraint(
            "actor IN ('wallet_system','partner_bank','cskh')", name="ck_events_actor"
        ),
    )

    event_id: Mapped[str] = mapped_column(String, primary_key=True)
    trans_id: Mapped[str] = mapped_column(ForeignKey("transactions.trans_id"), nullable=False)
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    actor: Mapped[str] = mapped_column(String, nullable=False)
    status_from: Mapped[str] = mapped_column(String, nullable=False)
    status_to: Mapped[str] = mapped_column(String, nullable=False)
    occurred_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False)
    payload_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)


# ---------------------------------------------------------------------------
# Complaint → ticket → investigation → proposal → approval
# ---------------------------------------------------------------------------


class Complaint(Base):
    __tablename__ = "complaints"
    __table_args__ = (
        CheckConstraint(
            # 'other' (2026-08-11, CTRL-001 FIN05_QA_TestCases.jsonl) — a customer asking for a real
            # person WITHOUT a description matching one of the 4 specific transaction complaint
            # types
            # (e.g. a general enquiry, no problem described yet) —
            # still needs a real Complaint/Ticket so CSKH can identify & handle it, rather than
            # forcing
            # the agent to guess one of 4 types that don't fit reality.
            "type IN ('wrong_recipient','money_not_received','double_charge','refund','other')",
            name="ck_complaints_type",
        ),
        CheckConstraint(
            # 'unknown' (2026-08-11, found via functional_qa_set.jsonl case
            # NOTFOUND) — after asking all {CLARIFY_QUESTION_MAX_ROUNDS} rounds +
            # 1 scope question and the customer still can't tell (e.g. a customer unfamiliar with
            # how
            # wallet-to-wallet differs from bank transfers), the agent used to be forced to guess
            # one of
            # the 3 real values — mirroring 'other' for complaint_type above, this lets CSKH
            # determine it
            # manually instead of the AI fabricating it.
            "scope IN ('internal_wallet','from_bank','to_bank','unknown')", name="ck_complaints_scope"
        ),
        CheckConstraint(
            "priority IN ('low','normal','high','critical')", name="ck_complaints_priority"
        ),
        CheckConstraint(
            # A2 — A FINAL SAFETY NET, NOT THE BUSINESS LIMIT.
            #
            # The business limit is 2,000 CHARACTERS, enforced in `complaint_intake.
            # MAX_DESCRIPTION_CHARS` (where REST + agent converge) and
            # `CreateTicketRequest`. The 12,000 below counts CIPHERTEXT and
            # CANNOT be converted into 2,000 characters — nobody should "fix it to match".
            #
            # Why it can't be converted: Fernet grows by utf-8 BYTES while the business limit counts
            # CHARACTERS, and bytes per character vary.
            # Measured on exactly 2,000 characters:
            #     pure ASCII                  2,764  (x1.38)
            #     typical Vietnamese          3,596  (x1.80)
            #     DIACRITIC-HEAVY Vietnamese  5,708  (x2.85)
            #     4-byte emoji               10,764  (x5.38)
            # A bound of 4,000 (inferred from the x1.9 ratio measured at 500 characters) WRONGLY
            # BLOCKS
            # the last two cases — that is why the number here is 12,000, not 4,000.
            #
            # The cost, stated so nobody thinks this layer is stricter than it is:
            # 12,000 ciphertext ≈ 8,700 ASCII characters get past the DB layer. This layer
            # ONLY stops catastrophes (a 20,000-character flood ⟹ ~27,600, rejected). Precision
            # lives in
            # the service layer, not here — this is where ADR-024's "enforce at the DB layer"
            # principle
            # does NOT carry over, and ADR-025 decision 5 accepts that trade-off consciously.
            "length(description_raw) <= 12000",
            name="ck_complaints_description_raw_tran_tho",
        ),
    )

    complaint_id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    trans_id: Mapped[str | None] = mapped_column(ForeignKey("transactions.trans_id"), nullable=True)
    type: Mapped[str] = mapped_column(String, nullable=False)
    scope: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="investigating")
    priority: Mapped[str] = mapped_column(String, nullable=False, default="normal")
    # A1 — THE CUSTOMER'S STATEMENT, encrypted at rest. This was the only untrusted entry
    # point still in plaintext after chat content (:475) and RAG (:513) adopted
    # EncryptedText: not a new mechanism, just bringing it up to the existing standard.
    #
    # NO scrubbing at write time (unlike `resolutions.note`/ADR-024): note is text typed by
    # STAFF, whereas this is the CUSTOMER'S STATEMENT — masking on write loses the original and
    # its evidentiary value if the complaint goes to the State Bank of Vietnam/court. Masking for
    # group A lives at the READ layer, pending ADR-025.
    #
    # A1-04 — NO BACKFILL, AND THIS IS A RECORDED DECISION, not a silent side effect of the
    # implementation. `complaints` rows written BEFORE 2026-08-15 remain PLAINTEXT on disk
    # permanently. The `InvalidToken` path only makes them READABLE —
    # "readable" and "encrypted at rest" are two different things; don't read the former as the
    # latter.
    # Acceptable TODAY because existing data is seed/test and the pilot has been postponed.
    # Once there is REAL customer data, backfill is a SEPARATE decision that must be made
    # before opening the pilot — it does not happen automatically thanks to this fix.
    #
    # NO length CHECK at the DB layer (unlike ADR-024 decision 1) — not an oversight: on an
    # encrypted column `length()` measures CIPHERTEXT, and the growth ratio is NOT
    # fixed (measured: x1.90 at 500 accented Vietnamese characters → x1.72 at 20,000,
    # because Fernet grows by utf-8 BYTES while the business limit counts CHARACTERS). A
    # CHECK on ciphertext cannot express a per-character limit. The real limit is enforced at the
    # schema layer (`CreateTicketRequest`), see A2.
    description_raw: Mapped[str] = mapped_column(EncryptedText, nullable=False)
    # Computed by the service layer (fraud_engine.py), NOT filled in by the agent — Data Brief §4.2.
    fraud_signals: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    otp_disclosed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False)
    # ADR-044 — the LangGraph checkpointer session that produced this complaint (`f"{user_id}:
    # {iat}"`, see src/api/main.py). PERMANENTLY NULLABLE, NO backfill — complaints created BEFORE
    # this column have no way of correctly reconstructing their thread (one user logging in many
    # times = many threads for the same user_id; guessing by timestamp is a heuristic disguised as
    # fact). NO FK — it identifies a checkpointer session, not a DB foreign key. Written AT
    # complaint CREATION time, threaded through four layers:
    # run_agent_turn → build_customer_tools → tool create_ticket → complaint_intake.
    thread_id: Mapped[str | None] = mapped_column(String, nullable=True)


class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = (
        CheckConstraint(
            "hitl_status IN ('pending','approved','rejected','need_more_info')",
            name="ck_tickets_hitl_status",
        ),
        CheckConstraint(
            "partner_wait_status IN ('n/a','waiting','overdue','responded')",
            name="ck_tickets_partner_wait_status",
        ),
    )

    ticket_id: Mapped[str] = mapped_column(String, primary_key=True)
    complaint_id: Mapped[str] = mapped_column(ForeignKey("complaints.complaint_id"), nullable=False)
    assigned_role: Mapped[str] = mapped_column(String, nullable=False, default="cskh")
    hitl_status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    sla_due_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False)
    partner_wait_status: Mapped[str] = mapped_column(String, nullable=False, default="n/a")
    # CTRL-001 (2026-08-11) — the customer actively asks to talk to a real person (not every
    # urgent/prioritised ticket is customer-requested — kept separate from
    # priority/fraud_signals, in the spirit of ISO/IEC 25059 "user
    # controllability"). The CSKH dashboard filters/marks this flag separately.
    human_handoff_requested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False)
    # ADR-044 — the moment `flag_human_handoff()` actually ran (NOT when the ticket was
    # created). Lives on Ticket rather than Complaint: one complaint may produce several
    # tickets, and a handoff belongs to ONE specific ticket. NULLABLE: tickets that never went
    # through the handoff path (most of them) have no such timestamp. The UI draws a conversation
    # divider at this timestamp — above the line is what caused the handoff, below it what happened
    # after (the transcript is read LIVE and may continue after the customer asked for a human).
    handoff_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    # ADR-064(b) — CSKH "claim ticket" is explicit (POST /tickets/{id}/claim), NOT
    # automatic. NULL = still in the shared pool, any CSKH agent can see+claim it. No special
    # CASCADE FK constraint — if a user were deleted (which doesn't happen in the product; there is
    # no delete-user route) the value simply stays NULL; not a priority axis here.
    claimed_by: Mapped[str | None] = mapped_column(ForeignKey("users.user_id"), nullable=True)
    claimed_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)


class ToolResult(Base):
    """The single source of truth for anti-fabrication cross-checking (T4, Data Brief §6.5)."""

    __tablename__ = "tool_results"

    tool_result_id: Mapped[str] = mapped_column(String, primary_key=True)
    tool_name: Mapped[str] = mapped_column(String, nullable=False)
    raw_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    content_hash: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=dt.datetime.utcnow)


class InvestigationLog(Base):
    __tablename__ = "investigation_logs"

    log_id: Mapped[str] = mapped_column(String, primary_key=True)
    ticket_id: Mapped[str] = mapped_column(ForeignKey("tickets.ticket_id"), nullable=False)
    step_no: Mapped[int] = mapped_column(Integer, nullable=False)
    tool_called: Mapped[str] = mapped_column(String, nullable=False)
    tool_input_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    tool_result_id: Mapped[str | None] = mapped_column(
        ForeignKey("tool_results.tool_result_id"), nullable=True
    )
    agent_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=dt.datetime.utcnow)


class Resolution(Base):
    """BR-10: the agent only proposes — always draft/pending_approval, there is no path that
    writes approved directly. approved ⟹ approved_by NOT NULL, enforced by a CHECK here."""

    __tablename__ = "resolutions"
    __table_args__ = (
        CheckConstraint(
            "action_type IN ('refund_to_wallet','refund_to_bank','ledger_adjustment',"
            "'no_action','manual_review')",
            name="ck_resolutions_action_type",
        ),
        CheckConstraint(
            "status IN ('draft','pending_approval','approved','rejected')",
            name="ck_resolutions_status",
        ),
        CheckConstraint(
            "(status != 'approved') OR (approved_by IS NOT NULL AND approved_at IS NOT NULL)",
            name="ck_resolutions_approved_requires_approver_br10",
        ),
        # ADR-019 · INV-14 — SYMMETRIC with BR-10 above, for the rejection branch.
        # The supervisor's judgement label is data used to SCORE the agent later, so
        # it must be enforced at the DB layer, not in the route: a raw SQL UPDATE or a new route
        # that
        # forgets to check are both rejected by the database itself. Without this, the learning
        # dataset would have holes exactly where they are hardest to detect.
        CheckConstraint(
            "reject_reason IN ('sai_so_lieu','sai_phan_loai','thieu_can_cu',"
            "'sai_chinh_sach','trung_case','khach_rut','khac')",
            name="ck_resolutions_reject_reason",
        ),
        CheckConstraint(
            "(status != 'rejected') OR (reject_reason IS NOT NULL "
            "AND rejected_by IS NOT NULL AND rejected_at IS NOT NULL)",
            name="ck_resolutions_rejected_requires_reason_br11",
        ),
        # BR-12 maker-checker (ADR-020). The `created_by IS NULL` condition is
        # MANDATORY, not a loosening: that column is permanently nullable for resolutions that
        # predate it (migration b2c3d4e5f6a7 — guessing a name into the audit record is worse than
        # leaving it blank), so an unconditional CHECK would break immediately on old data.
        # While `approved_by` is still NULL, `approved_by != created_by` yields NULL,
        # and CHECK treats NULL as SATISFIED — so no extra clause is needed for unapproved
        # resolutions.
        # The expression is written LONG ON PURPOSE (form "C", which security fixed after building a
        # 6-case truth table). All three forms are EQUALLY correct; this one was chosen because:
        #  · the short form `approved_by != created_by` is correct thanks to SQL's THREE-VALUED
        # logic
        #    (NULL != x yields NULL, and CHECK treats NULL as satisfied) — correct, but correct in a
        #    way that forces every later reader to rebuild the reasoning in their head, and it is
        # very
        #    easy to "simplify" by mistake. A hard constraint should not rely on subtle reasoning
        # that
        #    each person has to redo.
        #  · the `IS DISTINCT FROM` form needs SQLite >= 3.39; tests run SQLite in CI and on other
        #    people's machines, and the version can't be verified everywhere.
        # This form uses only `IS NULL` and `!=` — it behaves identically on every backend.
        CheckConstraint(
            "(created_by IS NULL) OR ("
            "(approved_by IS NULL OR approved_by != created_by) AND "
            "(rejected_by IS NULL OR rejected_by != created_by))",
            name="ck_resolutions_maker_checker_br12",
        ),
        # ADR-024/INV-17 — symmetric with br11 above. `khac` = "other reason"; without a note
        # the audit record is meaningless: a later reader wouldn't know why the case was rejected.
        # `length(trim(note)) > 0` blocks both NULL and whitespace-only strings — validating only in
        # the route can't stop a raw SQL UPDATE, the ADR-019 lesson repeated.
        CheckConstraint(
            "(reject_reason != 'khac') OR (note IS NOT NULL AND length(trim(note)) > 0)",
            name="ck_resolutions_note_bat_buoc_khi_khac",
        ),
    )

    resolution_id: Mapped[str] = mapped_column(String, primary_key=True)
    ticket_id: Mapped[str] = mapped_column(ForeignKey("tickets.ticket_id"), nullable=False)
    action_type: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    destination_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    cited_tool_result_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String, nullable=False, default="draft")
    approved_by: Mapped[str | None] = mapped_column(ForeignKey("users.user_id"), nullable=True)
    approved_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    # ADR-019 — the expert's judgement label on the rejection path. Nullable at the column
    # level (a resolution not yet rejected has nothing to record); the requirement is enforced
    # CONDITIONALLY via the br11 CHECK above, exactly as BR-10 did.
    # ADR-020 (draft) prepares the maker-checker column in advance: who PROPOSED it, so that
    # `approved_by != created_by` can be enforced later. PERMANENTLY nullable for old data —
    # resolutions created before this column have no way of knowing the proposer, and fabricating
    # a name into the audit record is worse than leaving it blank.
    created_by: Mapped[str | None] = mapped_column(ForeignKey("users.user_id"), nullable=True)
    reject_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    rejected_by: Mapped[str | None] = mapped_column(ForeignKey("users.user_id"), nullable=True)
    rejected_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    # ADR-024 (TM-03 security sign-off) — the SUPERVISOR's free-text note when rejecting.
    # DIFFERENT from `InvestigationLog.agent_note` (the AGENT's note during investigation) despite
    # the similar name — don't confuse one column for the other; they are in different tables with
    # different risks (the note here is text typed by STAFF, PII-scrubbed AT WRITE TIME before it
    # gets here — see the reject route).
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    note_flagged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=dt.datetime.utcnow)


class Escalation(Base):
    __tablename__ = "escalations"
    __table_args__ = (
        CheckConstraint(
            "target IN ('supervisor','partner_bank','authority')", name="ck_escalations_target"
        ),
    )

    escalation_id: Mapped[str] = mapped_column(String, primary_key=True)
    ticket_id: Mapped[str] = mapped_column(ForeignKey("tickets.ticket_id"), nullable=False)
    target: Mapped[str] = mapped_column(String, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)  # NOT NULL — signal codes, not conclusions
    created_by: Mapped[str] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=dt.datetime.utcnow)
    partner_response_status: Mapped[str | None] = mapped_column(String, nullable=True)
    responded_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)


# ---------------------------------------------------------------------------
# Authentication & conversations
# ---------------------------------------------------------------------------


class AuthSession(Base):
    """`resolution_id IS NULL` = the customer's step-up OTP challenge (the original
    flow). `resolution_id IS NOT NULL` = a dedicated OTP challenge for one specific financial
    approval by a supervisor (Auth Flow upgrade 2026-08-12, AUTH5-04/05/05B) — reusing the
    existing failed_attempts/locked_at mechanism instead of creating a new table.
    `amount_snapshot` captures `Resolution.amount` AT THE MOMENT the OTP is requested — PSD2
    dynamic linking: if CSKH edits the amount afterwards, the snapshot no longer matches the
    resolution's current amount, forcing a new OTP (AUTH5-05B)."""

    __tablename__ = "auth_sessions"

    session_id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    otp_code: Mapped[str | None] = mapped_column(String, nullable=True)
    otp_status: Mapped[str | None] = mapped_column(String, nullable=True)
    security_q_passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    failed_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    resolution_id: Mapped[str | None] = mapped_column(ForeignKey("resolutions.resolution_id"), nullable=True)
    amount_snapshot: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=dt.datetime.utcnow)


class ChatSession(Base):
    """Live chat (2026-08-11) — one real-time two-way chat session between a customer and
    CSKH, ALWAYS attached to an existing ticket (ticket_id NOT NULL) — in line with the
    agreed principle "an escalation path, not a channel parallel to the AI", and guaranteeing
    there is always a Complaint/InvestigationLog to hand over the AI's investigation context
    to the CSKH agent taking the case. claimed_by NULL = waiting; a value = some CSKH agent
    has claimed it (claim-based routing, no round-robin/ML)."""

    __tablename__ = "chat_sessions"
    __table_args__ = (
        CheckConstraint("status IN ('waiting','active','closed')", name="ck_chat_sessions_status"),
        CheckConstraint("csat_score IS NULL OR csat_score BETWEEN 1 AND 5", name="ck_chat_sessions_csat_score"),
    )

    chat_session_id: Mapped[str] = mapped_column(String, primary_key=True)
    ticket_id: Mapped[str] = mapped_column(ForeignKey("tickets.ticket_id"), nullable=False)
    customer_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="waiting")
    claimed_by: Mapped[str | None] = mapped_column(ForeignKey("users.user_id"), nullable=True)
    started_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=dt.datetime.utcnow)
    claimed_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    closed_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    csat_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    csat_submitted_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)


class Message(Base):
    """Before 2026-08-11 this table existed but had never been used (0 rows; the session_id FK
    pointed at the wrong object, auth_sessions = LOGIN sessions instead of CHAT sessions) —
    repurposed for live chat, with the FK switched to ChatSession.
    content uses EncryptedText (encrypted at rest, same key as
    PolicyChunk.text) — chat transcripts may contain phone/account numbers/amounts and must
    not be stored in plaintext."""

    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint(
            "role IN ('customer','agent','staff','system')", name="ck_messages_role"
        ),
    )

    message_id: Mapped[str] = mapped_column(String, primary_key=True)
    chat_session_id: Mapped[str] = mapped_column(ForeignKey("chat_sessions.chat_session_id"), nullable=False)
    ticket_id: Mapped[str | None] = mapped_column(ForeignKey("tickets.ticket_id"), nullable=True)
    role: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(EncryptedText, nullable=False)
    tool_call_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=dt.datetime.utcnow)


# ---------------------------------------------------------------------------
# Policy/FAQ RAG (src/rag/) — uploaded by the e-wallet partner (role partner_admin),
# searched by the agent + CSKH. Document content (PolicyChunk.text) is encrypted in place
# (EncryptedText) — the vector store (Chroma, data/rag_index/) holds only embeddings +
# chunk_ids, NOT the real text (see src/rag/store.py).
# ---------------------------------------------------------------------------


class PolicyDocument(Base):
    __tablename__ = "policy_documents"
    __table_args__ = (
        CheckConstraint(
            "status IN ('processing','indexed','failed')", name="ck_policy_documents_status"
        ),
    )

    doc_id: Mapped[str] = mapped_column(String, primary_key=True)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    uploaded_by: Mapped[str] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    uploaded_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=dt.datetime.utcnow)
    status: Mapped[str] = mapped_column(String, nullable=False, default="processing")
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # ADR-065 (05/09) — the ORIGINAL full text, read BEFORE chunking (see
    # src/rag/ingest.py). PolicyChunk.text only stores CHUNKED AND OVERLAPPING passages
    # (overlap=150) — re-joining by chunk_index does NOT reproduce the original text, so the
    # full-text reading page (deep-linked from /policy-search) needs this separate column rather
    # than guessing from chunks. PERMANENTLY NULLABLE for the 4 documents indexed BEFORE this
    # column existed (backfill is a separate operational task, not a migration requirement).
    full_text: Mapped[str | None] = mapped_column(EncryptedText, nullable=True)


class PolicyChunk(Base):
    __tablename__ = "policy_chunks"
    __table_args__ = (
        # ADR-061 draft (03/09) — Finding ① layer 1. NULL = unassigned (the default for new
        # documents, and for all 378 existing chunks until BA finishes reviewing the
        # auto-classification
        # draft). This column is NOT read anywhere in search_policy until the ADR is formally
        # approved
        # — the column is added first to separate "preparing the schema" from "changing behaviour",
        # two things with different approval processes.
        CheckConstraint(
            "scope IN ('internal_wallet','from_bank','to_bank','unknown')",
            name="ck_policy_chunks_scope",
        ),
    )

    chunk_id: Mapped[str] = mapped_column(String, primary_key=True)
    doc_id: Mapped[str] = mapped_column(ForeignKey("policy_documents.doc_id"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    # Transparently encrypted (Fernet, like BankAccount.account_no) — "hardened RAG
    # security": the SQLite file on disk contains no raw policy content.
    text: Mapped[str] = mapped_column(EncryptedText, nullable=False)
    scope: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=dt.datetime.utcnow)


class Notification(Base):
    """ADR-063 — notification bell. Fan-out: ONE row per recipient (not one row carrying a
    list of recipients) — `read_at` is per person, so rows must be split per person FROM THE
    START rather than merged and filtered at read time. Displayed content can ONLY be derived
    from `event_type` + `ticket_id` — there is NO amount/PII/phone column in this table,
    honouring hard constraint #3 + PDPA (a constraint at the SCHEMA LAYER, not just the
    display code)."""

    __tablename__ = "notifications"
    __table_args__ = (
        CheckConstraint(
            "event_type IN ('ve_moi','cho_duyet','da_duyet','da_tu_choi')",
            name="ck_notifications_event_type",
        ),
    )

    notification_id: Mapped[str] = mapped_column(String, primary_key=True)
    recipient_user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    ticket_id: Mapped[str] = mapped_column(ForeignKey("tickets.ticket_id"), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=dt.datetime.utcnow)
    read_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
