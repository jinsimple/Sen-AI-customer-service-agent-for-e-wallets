"""Tool 4/5 — `propose_resolution` (PRD §6, Data Brief §6.3 row 4).

Required test: the result is always PENDING APPROVAL; no parameter allows setting
`approved` directly (BR-10). This is the most important block in the entire system — this
function DELIBERATELY takes no `status` parameter, so there is no way, not even through a
programming mistake, to create a pre-approved resolution.

Secondary guardrail (not in the original test spec but sensible — anti-fabrication T4 at
the write layer, not only the read layer): `cited_tool_result_ids`
must point to tool_results that REALLY EXIST in the DB; otherwise creation is refused.
"""
from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy.orm import Session

from src.db.models import Complaint, Resolution, Ticket, ToolResult, Transaction
from src.services.notifications import notify_pending_approval
from src.tools.base import ToolError, new_id, record_tool_result

VALID_ACTION_TYPES = {
    "refund_to_wallet",
    "refund_to_bank",
    "ledger_adjustment",
    "no_action",
    "manual_review",
}

# The two actions that TOUCH REAL MONEY — the amount must be checked, unlike
# ledger_adjustment (a ledger correction whose reference need not be the original transaction
# amount) and no_action/manual_review (no amount at all).
_REFUND_ACTION_TYPES = {"refund_to_wallet", "refund_to_bank"}


def _check_refund_amount(session: Session, *, ticket_id: str, amount: int | None) -> None:
    """Block meaningless refund amounts RIGHT AT THE WRITE LAYER (V3.2, hotfix 14/08).

    Real finding: the DB had `RES-b8d2c7798d53` proposing a refund of **6 dong** for a
    107,000đ transaction — the amount field was FREE-FORM, not tied to any transaction.
    That amount could not be traced to any tool result, i.e. it violated the spirit of hard
    constraint 3, and it went straight to the supervisor's approval screen.

    Placed in the tool layer (not the route or the form) because this is the ONLY place
    every resolution write passes through — CSKH clicking the button in the web app and any
    future caller are all checked by the same rule, in the same spirit as
    `cited_tool_result_ids` having to point at a real tool_result just below.

    The reference is the transaction amount tied to the ticket (ticket → complaint →
    transaction). A complaint with NO identified transaction (`complaint.trans_id
    IS NULL` — the `not_found` path) has no ceiling to compare against: `amount > 0` is still
    enforced but there is NO ceiling check, because blocking here would also lock out valid
    cases where the agent has not found the transaction yet. This limitation is stated
    explicitly rather than pretending full coverage.
    """
    if amount is None or amount <= 0:
        raise ToolError(
            "Số tiền hoàn phải lớn hơn 0 — không đề xuất hoàn tiền mà thiếu số tiền"
        )

    trans = (
        session.query(Transaction)
        .join(Complaint, Complaint.trans_id == Transaction.trans_id)
        .join(Ticket, Ticket.complaint_id == Complaint.complaint_id)
        .filter(Ticket.ticket_id == ticket_id)
        .one_or_none()
    )
    if trans is None:
        return  # complaint with no identified transaction — no ceiling to compare against

    if amount > trans.amount:
        raise ToolError(
            f"Số tiền hoàn ({amount:,}đ) vượt quá số tiền giao dịch "
            f"{trans.trans_id} ({trans.amount:,}đ) — không hoàn nhiều hơn số đã trừ"
        )


def propose_resolution(
    session: Session,
    *,
    ticket_id: str,
    action_type: str,
    rationale: str,
    amount: int | None = None,
    destination_ref: str | None = None,
    cited_tool_result_ids: list[str] | None = None,
    # F-17 — NO default value, ON PURPOSE. Previously `= None` let every caller that forgot to
    # pass it run smoothly and produce resolutions with `created_by
    # IS NULL` — and that very NULL is what makes the maker-checker CHECK (BR-12) skip the row.
    # In other words: forgetting one parameter silently granted the record immunity from the
    # HITL constraint, at BOTH enforcement layers.
    # Removing the default turns "forgetting" from a vulnerability into a `TypeError` at
    # import/test time. Same fail-fast principle as secrets having no default in config.
    created_by: str | None,
) -> dict[str, Any]:
    if action_type not in VALID_ACTION_TYPES:
        raise ToolError(f"action_type không hợp lệ: {action_type}")
    if session.get(Ticket, ticket_id) is None:
        raise ToolError(f"ticket_id không tồn tại: {ticket_id}")
    if not rationale or not rationale.strip():
        raise ToolError("rationale bắt buộc — mọi đề xuất phải có căn cứ bằng lời")

    if action_type in _REFUND_ACTION_TYPES:
        _check_refund_amount(session, ticket_id=ticket_id, amount=amount)

    cited_tool_result_ids = cited_tool_result_ids or []
    for tr_id in cited_tool_result_ids:
        if session.get(ToolResult, tr_id) is None:
            raise ToolError(
                f"cited_tool_result_ids chứa id không tồn tại: {tr_id} — "
                "không được trích dẫn một tool_result bịa ra"
            )

    resolution_id = new_id("RES")
    resolution = Resolution(
        resolution_id=resolution_id,
        ticket_id=ticket_id,
        action_type=action_type,
        amount=amount,
        destination_ref=destination_ref,
        rationale=rationale,
        cited_tool_result_ids=cited_tool_result_ids,
        status="pending_approval",  # takes NO status parameter — BR-10
        # The proposer's identity ALWAYS comes from the JWT at the route layer, never from the
        # body — groundwork for the maker-checker CHECK of ADR-020.
        created_by=created_by,
        approved_by=None,
        approved_at=None,
        created_at=dt.datetime.utcnow(),
    )
    session.add(resolution)
    session.flush()

    # ADR-063 — fan-out in the SAME transaction, same pattern as create_ticket.py.
    notify_pending_approval(session, ticket_id=ticket_id)

    result = {
        "resolution_id": resolution_id,
        "status": resolution.status,
        "action_type": action_type,
    }
    tool_result_id = record_tool_result(session, "propose_resolution", result)
    return {**result, "tool_result_id": tool_result_id}
