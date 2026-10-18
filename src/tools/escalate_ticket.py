"""Tool 5/5 — `escalate_ticket` (PRD §6, Data Brief §6.3 row 5).

Required tests: `reason` is mandatory; who/when is logged; `target` must be valid
according to the authority matrix (PRD §3 / scenarios.yaml `authority_map`).

For suspected-fraud cases (§4.5.4): `reason` MUST be signal codes
(`"FS-03, FS-05"`), not a conclusion sentence — that rule lives at the calling layer
(the agent). This function only enforces a non-empty `reason`; it cannot check whether
the content is a signal code (that is test T5 at the eval layer).
"""
from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy.orm import Session

from src.db.models import Escalation, Ticket, User
from src.tools.base import ToolError, new_id, record_tool_result

VALID_TARGETS = {"supervisor", "partner_bank", "authority"}


def escalate_ticket(
    session: Session,
    *,
    ticket_id: str,
    target: str,
    reason: str,
    created_by: str,
) -> dict[str, Any]:
    if target not in VALID_TARGETS:
        raise ToolError(f"target không hợp lệ: {target} — phải thuộc {sorted(VALID_TARGETS)}")
    if not reason or not reason.strip():
        raise ToolError("reason bắt buộc — không được escalate mà không ghi lý do")
    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        raise ToolError(f"ticket_id không tồn tại: {ticket_id}")
    if session.get(User, created_by) is None:
        raise ToolError(f"created_by (user_id) không tồn tại: {created_by}")

    now = dt.datetime.utcnow()
    escalation_id = new_id("ESC")
    escalation = Escalation(
        escalation_id=escalation_id,
        ticket_id=ticket_id,
        target=target,
        reason=reason,
        created_by=created_by,
        created_at=now,
        partner_response_status="waiting" if target == "partner_bank" else None,
        responded_at=None,
    )
    session.add(escalation)

    # Recorded on the ticket itself so CSKH/supervisor see the latest state immediately.
    ticket.updated_at = now
    session.flush()

    result = {
        "escalation_id": escalation_id,
        "ticket_id": ticket_id,
        "target": target,
        "created_by": created_by,
        "created_at": now.isoformat(),
    }
    tool_result_id = record_tool_result(session, "escalate_ticket", result)
    return {**result, "tool_result_id": tool_result_id}
