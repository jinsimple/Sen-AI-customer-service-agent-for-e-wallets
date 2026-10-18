"""Tool 3/5 — `create_ticket` (PRD §6, Data Brief §6.3 row 3).

Required tests: reject if `trans_id` does not exist, EXCEPT the one allowed not_found case
(the customer complains but the agent has not found any matching transaction —
`complaints.trans_id` is NULL, Data Brief §4.2).

Complaint + Ticket are always created in the same transaction. `assigned_role`
is always 'cskh' — the AI never escalates straight to a supervisor; every investigation
result must first be taken in by CSKH (business_rules.md principle
Brief §6.5 / the corrected design in FIN-05 §4 decisions 1-2).
"""
from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy.orm import Session

from src.db.models import Complaint, Ticket, Transaction, User
from src.services.notifications import notify_new_ticket
from src.tools.base import ToolError, _new_id, record_tool_result
from src.tools.fraud_policy import evaluate_escalation
from src.tools.lookup_transaction import is_party_to_transaction
from src.tools.sla import compute_sla_due_at

VALID_COMPLAINT_TYPES = {"wrong_recipient", "money_not_received", "double_charge", "refund", "other"}
VALID_SCOPES = {"internal_wallet", "from_bank", "to_bank", "unknown"}


def create_ticket(
    session: Session,
    *,
    user_id: str,
    complaint_type: str,
    scope: str,
    description_raw: str,
    trans_id: str | None = None,
    otp_disclosed: bool = False,
    fraud_signals: list[str] | None = None,
    now: dt.datetime | None = None,
    # ADR-044 — written straight into Complaint.thread_id on INSERT. None is valid
    # (PERMANENTLY NULLABLE) — callers without a chat session (direct REST, old tests) cannot
    # pass this value; that is not an error.
    thread_id: str | None = None,
) -> dict[str, Any]:
    if complaint_type not in VALID_COMPLAINT_TYPES:
        raise ToolError(f"complaint_type không hợp lệ: {complaint_type}")
    if scope not in VALID_SCOPES:
        raise ToolError(f"scope không hợp lệ: {scope}")
    if session.get(User, user_id) is None:
        raise ToolError(f"user_id không tồn tại: {user_id}")

    if trans_id is not None:
        # (reject if trans_id does not exist) — not_found is valid only when
        # trans_id is None, i.e. the agent looked it up and found nothing.
        txn = session.get(Transaction, trans_id)
        if txn is None:
            raise ToolError(
                f"trans_id không tồn tại: {trans_id} — nếu đây là case không tra ra "
                "giao dịch, gọi lại với trans_id=None thay vì đoán một mã"
            )
        # C4/BOLA (ADR-021) — existing is NOT ENOUGH, it must BELONG to the complainant.
        # This can be enforced unconditionally because the contract allows exactly one role
        # (`customer`) on route /tools/create_ticket; and since both the REST path and the AI path
        # go
        # through this function, one fix covers both. Without the check a customer could create a
        # ticket referencing ANOTHER customer's transaction — no figures leak (the tool returns no
        # details), but CSKH could act on data that does not belong to the complainant, and that is
        # noise in the audit record itself.
        if not is_party_to_transaction(session, txn, user_id):
            raise ToolError(
                f"trans_id không thuộc về người khiếu nại: {trans_id} — chỉ tạo hồ sơ "
                "cho giao dịch mà chính khách là một bên"
            )

    now = now or dt.datetime.utcnow()
    fraud_signals = fraud_signals or []
    decision = evaluate_escalation(fraud_signals)
    priority = decision.priority if decision.should_escalate else "normal"

    complaint_id = _new_id("CMP")
    complaint = Complaint(
        complaint_id=complaint_id,
        user_id=user_id,
        trans_id=trans_id,
        type=complaint_type,
        scope=scope,
        status="investigating",
        priority=priority,
        description_raw=description_raw,
        fraud_signals=fraud_signals,
        otp_disclosed=otp_disclosed,
        created_at=now,
        thread_id=thread_id,
    )
    session.add(complaint)
    session.flush()

    ticket_id = _new_id("TCK")
    ticket = Ticket(
        ticket_id=ticket_id,
        complaint_id=complaint_id,
        assigned_role="cskh",
        hitl_status="pending",
        sla_due_at=compute_sla_due_at(now, scope),
        partner_wait_status="waiting" if scope in ("from_bank", "to_bank") else "n/a",
        created_at=now,
        updated_at=now,
    )
    session.add(ticket)
    session.flush()

    # ADR-063 — fan-out in the SAME transaction: if the ticket rolls back, so does the
    # notification — no "ghost" notifications for a ticket that never materialised.
    notify_new_ticket(session, ticket_id=ticket_id)

    result = {
        "complaint_id": complaint_id,
        "ticket_id": ticket_id,
        "priority": priority,
        "sla_due_at": ticket.sla_due_at.isoformat(),
        "should_escalate": decision.should_escalate,
        "escalation_target": decision.target,
    }
    tool_result_id = record_tool_result(session, "create_ticket", result)
    return {**result, "tool_result_id": tool_result_id}
