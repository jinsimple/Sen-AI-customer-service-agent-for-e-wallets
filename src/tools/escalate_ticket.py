"""Tool 5/5 — `escalate_ticket` (PRD §6, Data Brief §6.3 hàng 5).

Test bắt buộc: bắt buộc có `reason`; ghi log ai/khi nào; `target` phải hợp
lệ theo ma trận thẩm quyền (PRD §3 / scenarios.yaml `authority_map`).

Với case nghi gian lận (§4.5.4): `reason` PHẢI là mã tín hiệu
(`"FS-03, FS-05"`), không phải câu kết luận — đây là quy tắc ở tầng gọi
hàm (agent), hàm này chỉ ép `reason` không rỗng, không kiểm được nội dung
có phải mã tín hiệu hay không (việc đó là test T5 ở tầng eval).
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

    # Ghi nhận trên chính ticket để CSKH/sếp thấy ngay trạng thái mới nhất.
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
