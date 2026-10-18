"""Tool 2/5 — `get_customer_history` (PRD §6, Data Brief §6.3 row 2).

Required test: calling with customer A's `user_id` NEVER returns customer B's data —
an authorisation test, not just a functional one (this is where an agent tricked into
"show me X's history" with a guessed phone number would most easily leak).
Every query in this function is filtered STRICTLY by the `user_id` passed in — there is no
path for another parameter (e.g. `phone`) to widen it to another user.
"""
from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models import Complaint, Transaction, User, Wallet
from src.observability.logging_config import get_logger
from src.tools.base import ToolError, record_tool_result

_logger = get_logger("fin05.tools.get_customer_history")


def get_customer_history(
    session: Session,
    *,
    user_id: str,
    days: int = 90,
    limit_transactions: int = 20,
    limit_complaints: int = 10,
    amount: int | None = None,
) -> dict[str, Any]:
    """`amount`: approximate filter on the amount the customer described (±2% tolerance, enough
    to absorb rounding like "270k"/"270.000đ") — used when the customer only gives a vague
    description (approximate amount + time, no transaction ID). WITHOUT this filter, a very
    active customer (real dataset: median ~232 transactions/user) easily has the transaction
    pushed out of the top `limit_transactions` by older ones even though it is still within
    `days` — a real finding from eval/run_golden_set.py (the agent failed to find the
    transaction and had to ask again despite having a full description).

    With `amount` → the result also includes `amount_match` (status found/multiple_matches/
    not_found, same pattern as lookup_transaction) — an explicit STRUCTURAL SIGNAL for the
    agent to branch on, rather than having the agent read the list and reason about whether it
    is ambiguous. Why we moved away from prompt instructions alone: experiments with
    eval/run_golden_set.py showed that a plain prompt instruction ("if there are several
    matches, ask again") is NOT followed reliably at scale (industry practice —
    see the OpenAI agent safety guide: "design workflows so ambiguous data never
    directly drives agent behavior", so ambiguity detection is pushed down to the tool layer
    rather than relying on wording)."""
    # This function does NOT receive correlation_id — the log still gets the correct
    # correlation_id + user_id of the in-flight request via contextvars (src/observability/
    # context.py), proving that "bind once at the entry point, callees inherit" works even at the
    # deepest layer (tools), with no signature changes to thread it through.
    _logger.info("get_customer_history_called", extra={"days": days, "has_amount": amount is not None})

    user = session.get(User, user_id)
    if user is None:
        raise ToolError(f"user_id không tồn tại: {user_id}")

    wallets = list(session.scalars(select(Wallet).where(Wallet.user_id == user_id)))
    wallet_ids = [w.wallet_id for w in wallets]

    since = dt.datetime.utcnow() - dt.timedelta(days=days)
    txn_stmt = select(Transaction).where(
        Transaction.created_at >= since,
        (Transaction.send_wal_id.in_(wallet_ids)) | (Transaction.rec_wal_id.in_(wallet_ids)),
    )
    amount_match: dict[str, Any] | None = None
    if amount is not None:
        tolerance = max(round(amount * 0.02), 1)
        amount_stmt = txn_stmt.where(Transaction.amount.between(amount - tolerance, amount + tolerance))
        # limit_transactions is NOT applied here — amount already narrows the results; an extra
        # limit would drop exactly the candidates that must all be listed for the agent to ask back
        # (just as lookup_transaction does not cap the number of candidates returned).
        amount_matches = list(session.scalars(amount_stmt.order_by(Transaction.created_at.desc()))) if wallet_ids else []
        if len(amount_matches) == 0:
            amount_match = {"status": "not_found"}
        elif len(amount_matches) == 1:
            # scope MUST be present here (not just trans_id) — without it the agent has to guess the
            # scope when creating a ticket via the amount_match=found branch (unlike the
            # multiple_matches
            # branch below, which already carries scope per candidate). A real finding from
            # functional_qa_set.jsonl: money_not_received/double_charge cases that found the
            # transaction
            # via amount_match (not via lookup_transaction) all had the wrong scope because this
            # field was
            # missing — not because of an agent reasoning error.
            match = amount_matches[0]
            amount_match = {
                "status": "found",
                "trans_id": match.trans_id,
                "scope": match.scope,
                "amount": match.amount,
                "created_at": match.created_at.isoformat() if match.created_at else None,
                "direction": "out" if match.send_wal_id in wallet_ids else "in",
            }
        else:
            amount_match = {
                "status": "multiple_matches",
                "candidates": [
                    {
                        "trans_id": t.trans_id,
                        "amount": t.amount,
                        "created_at": t.created_at.isoformat() if t.created_at else None,
                        "scope": t.scope,
                        "direction": "out" if t.send_wal_id in wallet_ids else "in",
                    }
                    for t in amount_matches
                ],
            }
        txn_stmt = amount_stmt
    txn_stmt = txn_stmt.order_by(Transaction.created_at.desc()).limit(limit_transactions)
    transactions = list(session.scalars(txn_stmt)) if wallet_ids else []

    complaints = list(
        session.scalars(
            select(Complaint).where(Complaint.user_id == user_id).order_by(Complaint.created_at.desc())
        )
    )

    result = {
        "user_id": user_id,
        "kyc_level": user.kyc_level,
        "wallets": [{"wallet_id": w.wallet_id, "balance": w.balance, "status": w.status} for w in wallets],
        **({"amount_match": amount_match} if amount_match is not None else {}),
        "recent_transactions": [
            {
                "trans_id": t.trans_id,
                "amount": t.amount,
                "status": t.status,
                "scope": t.scope,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "direction": "out" if t.send_wal_id in wallet_ids else "in",
            }
            for t in transactions
        ],
        "complaint_count_90d": len(
            [c for c in complaints if c.created_at and c.created_at >= since]
        ),
        "complaints_tong": len(complaints),
        "complaints": [
            {
                "complaint_id": c.complaint_id,
                "type": c.type,
                "status": c.status,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in complaints
        ],
    }

    # T3 — RECORD IN FULL, RETURN TRIMMED. Two different jobs, deliberately separated:
    #
    # `record_tool_result` receives the UNTOUCHED `result` -> traceability is intact.
    # Hard constraint 3 requires every number the agent states to trace back to `tool_results`;
    # trimming before recording would truncate the very evidence record, destroying exactly what
    # we are protecting.
    #
    # Only the COPY RETURNED to the LLM is trimmed. Measured: `complaints` takes 13,349/16,722
    # characters (79.8%) of this tool's output, and this tool is 41% of the whole prompt — and
    # each ReAct step re-sends EVERYTHING, so an 8-step turn pays 8 times.
    #
    # ⚠️ `complaints_tong` (total) is MANDATORY, not decoration. Silently trimming so the LLM sees
    # 10 records would make it believe the customer has 10 complaints and SAY that number —
    # manufacturing a wrong figure out of correct data. Exactly what hard constraint 3 forbids.
    # The real count must travel with the trimmed part, and it is present in BOTH copies, so an
    # LLM quoting `complaints_tong` can still be traced back.
    tool_result_id = record_tool_result(session, "get_customer_history", result)
    return {
        **result,
        "complaints": result["complaints"][:limit_complaints],
        "complaints_da_cat": len(complaints) > limit_complaints,
        "tool_result_id": tool_result_id,
    }
