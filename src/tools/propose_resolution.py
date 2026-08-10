"""Tool 4/5 — `propose_resolution` (PRD §6, Data Brief §6.3 hàng 4).

Test bắt buộc: kết quả luôn ở trạng thái CHỜ DUYỆT; không có tham số nào
cho phép đặt thẳng `approved` (BR-10). Đây là chỗ chặn quan trọng nhất của
toàn hệ thống — hàm này CỐ Ý không nhận tham số `status`, để không có cách
nào, kể cả do lỗi lập trình gọi sai, tạo ra một resolution đã duyệt sẵn.

Guardrail phụ (không có trong test spec gốc nhưng hợp lý để thêm — chống
bịa số liệu T4 ở tầng ghi, không chỉ tầng đọc): `cited_tool_result_ids`
phải trỏ tới tool_results CÓ THẬT trong DB, nếu không từ chối tạo.
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Optional

from sqlalchemy.orm import Session

from src.db.models import Resolution, Ticket, ToolResult
from src.tools.base import ToolError, new_id, record_tool_result

VALID_ACTION_TYPES = {
    "refund_to_wallet",
    "refund_to_bank",
    "ledger_adjustment",
    "no_action",
    "manual_review",
}


def propose_resolution(
    session: Session,
    *,
    ticket_id: str,
    action_type: str,
    rationale: str,
    amount: Optional[int] = None,
    destination_ref: Optional[str] = None,
    cited_tool_result_ids: Optional[list[str]] = None,
) -> dict[str, Any]:
    if action_type not in VALID_ACTION_TYPES:
        raise ToolError(f"action_type không hợp lệ: {action_type}")
    if session.get(Ticket, ticket_id) is None:
        raise ToolError(f"ticket_id không tồn tại: {ticket_id}")
    if not rationale or not rationale.strip():
        raise ToolError("rationale bắt buộc — mọi đề xuất phải có căn cứ bằng lời")

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
        status="pending_approval",  # KHÔNG nhận tham số ngoài — BR-10
        approved_by=None,
        approved_at=None,
        created_at=dt.datetime.utcnow(),
    )
    session.add(resolution)
    session.flush()

    result = {
        "resolution_id": resolution_id,
        "status": resolution.status,
        "action_type": action_type,
    }
    tool_result_id = record_tool_result(session, "propose_resolution", result)
    return {**result, "tool_result_id": tool_result_id}
