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
from typing import Any

from sqlalchemy.orm import Session

from src.db.models import Complaint, Resolution, Ticket, ToolResult, Transaction
from src.tools.base import ToolError, new_id, record_tool_result

VALID_ACTION_TYPES = {
    "refund_to_wallet",
    "refund_to_bank",
    "ledger_adjustment",
    "no_action",
    "manual_review",
}

# Hai hướng xử lý CHẠM TIỀN THẬT — số tiền phải chịu kiểm, khác
# ledger_adjustment (điều chỉnh sổ cái, mốc so sánh không nhất thiết là số
# tiền giao dịch gốc) và no_action/manual_review (không có số tiền).
_ACTION_TYPES_HOAN_TIEN = {"refund_to_wallet", "refund_to_bank"}


def _kiem_so_tien_hoan(session: Session, *, ticket_id: str, amount: int | None) -> None:
    """Chặn số tiền hoàn vô nghĩa NGAY TẠI TẦNG GHI (V3.2, hotfix 14/08).

    Phát hiện thật: DB có `RES-b8d2c7798d53` đề xuất hoàn **6 đồng** cho một
    giao dịch 107.000đ — ô nhập số tiền đang là ô TỰ DO, không gắn với giao
    dịch nào. Đó là số tiền không truy vết được về bất kỳ kết quả tool nào,
    tức trái tinh thần ràng buộc cứng 3, và nó đi thẳng tới màn duyệt của sếp.

    Đặt ở tầng tool (không phải ở route hay ở form) vì đây là nơi DUY NHẤT mọi
    đường ghi resolution đi qua — CSKH bấm nút trên webapp và bất kỳ nơi gọi
    nào sau này đều bị kiểm cùng một luật, cùng tinh thần với `cited_tool_
    result_ids` phải trỏ tới tool_result có thật ở ngay dưới.

    Mốc so sánh là số tiền giao dịch gắn với ticket (ticket → complaint →
    transaction). Khiếu nại KHÔNG xác định được giao dịch (`complaint.trans_id
    IS NULL` — đường `not_found`) thì không có trần để so: vẫn ép `amount > 0`
    nhưng KHÔNG chặn theo trần, vì chặn ở đây sẽ khoá luôn những case hợp lệ
    mà agent chưa tra ra giao dịch. Nói rõ giới hạn này thay vì giả vờ đã phủ
    kín.
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
        return  # khiếu nại chưa xác định được giao dịch — không có trần để so

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
) -> dict[str, Any]:
    if action_type not in VALID_ACTION_TYPES:
        raise ToolError(f"action_type không hợp lệ: {action_type}")
    if session.get(Ticket, ticket_id) is None:
        raise ToolError(f"ticket_id không tồn tại: {ticket_id}")
    if not rationale or not rationale.strip():
        raise ToolError("rationale bắt buộc — mọi đề xuất phải có căn cứ bằng lời")

    if action_type in _ACTION_TYPES_HOAN_TIEN:
        _kiem_so_tien_hoan(session, ticket_id=ticket_id, amount=amount)

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
