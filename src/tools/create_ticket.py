"""Tool 3/5 — `create_ticket` (PRD §6, Data Brief §6.3 hàng 3).

Test bắt buộc: từ chối nếu `trans_id` không tồn tại, TRỪ đúng trường hợp
not_found được cho phép (khách khiếu nại nhưng agent chưa tra ra giao dịch
nào khớp — `complaints.trans_id` NULL, Data Brief §4.2).

Luôn tạo Complaint + Ticket trong cùng một transaction. `assigned_role`
luôn là 'cskh' — AI không bao giờ vượt cấp thẳng lên supervisor, mọi kết
quả điều tra phải qua CSKH tiếp nhận trước (business_rules.md nguyên tắc
Brief §6.5 / thiết kế đã sửa ở FIN-05 §4 quyết định 1-2).
"""
from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy.orm import Session

from src.db.models import Complaint, Ticket, Transaction, User
from src.services.notifications import notify_ve_moi
from src.tools.base import ToolError, _new_id, record_tool_result
from src.tools.fraud_policy import evaluate_escalation
from src.tools.lookup_transaction import la_mot_ben_cua_giao_dich
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
    # ADR-044 — ghi thẳng vào Complaint.thread_id lúc INSERT. None hợp lệ
    # (NULLABLE VĨNH VIỄN) — caller không có phiên chat (REST trực tiếp,
    # test cũ) không truyền được giá trị này, không phải lỗi.
    thread_id: str | None = None,
) -> dict[str, Any]:
    if complaint_type not in VALID_COMPLAINT_TYPES:
        raise ToolError(f"complaint_type không hợp lệ: {complaint_type}")
    if scope not in VALID_SCOPES:
        raise ToolError(f"scope không hợp lệ: {scope}")
    if session.get(User, user_id) is None:
        raise ToolError(f"user_id không tồn tại: {user_id}")

    if trans_id is not None:
        # (từ chối nếu trans_id không tồn tại) — not_found hợp lệ chỉ khi
        # trans_id là None, tức agent đã tra và không ra kết quả nào.
        txn = session.get(Transaction, trans_id)
        if txn is None:
            raise ToolError(
                f"trans_id không tồn tại: {trans_id} — nếu đây là case không tra ra "
                "giao dịch, gọi lại với trans_id=None thay vì đoán một mã"
            )
        # C4/BOLA (ADR-021) — tồn tại là CHƯA ĐỦ, phải THUỘC VỀ người khiếu nại.
        # Siết vô điều kiện được vì contract cho route /tools/create_ticket đúng
        # một vai `customer`; và vì cả đường REST lẫn đường AI cùng đi qua hàm
        # này, một chỗ sửa phủ cả hai. Không kiểm thì một khách tạo được ticket
        # tham chiếu giao dịch của khách KHÁC — không lộ số liệu (tool không trả
        # chi tiết) nhưng CSKH có thể xử lý nhầm trên dữ liệu không thuộc người
        # khiếu nại, và đó là nhiễu vào chính hồ sơ kiểm toán.
        if not la_mot_ben_cua_giao_dich(session, txn, user_id):
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

    # ADR-063 — fan-out CÙNG transaction: vé rollback thì thông báo rollback
    # theo, không có thông báo "ma" cho vé chưa từng thành hình.
    notify_ve_moi(session, ticket_id=ticket_id)

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
