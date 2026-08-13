"""Live chat thật (WebSocket) — nâng cấp CTRL-001 từ "gắn cờ ticket" bất đồng
bộ lên "chat 2 chiều thời gian thực" (kế hoạch 2026-08-11). Mọi phiên chat
LUÔN gắn 1 ticket có sẵn (`ChatSession.ticket_id` NOT NULL) — đúng tinh thần
"escalation path, không phải kênh song song với AI" đã chốt: khách phải đã
được `flag_human_handoff`/AI tạo ticket trước, live chat chỉ nâng cấp cách
CSKH xử lý ticket đó, không tạo luồng nghiệp vụ riêng.

Định tuyến claim-based đơn giản (không round-robin/ML) — `claim_session()`
dùng UPDATE có điều kiện (`claimed_by IS NULL`) làm optimistic concurrency,
đủ cho quy mô ~4 CSKH + 2 supervisor / ~50 phiên đồng thời đã khảo sát.
"""
from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from src.db.models import ChatSession, Complaint, InvestigationLog, Message, Ticket, User
from src.tools.base import ToolError, new_id


def open_chat_session(session: Session, *, ticket_id: str, customer_id: str, now: dt.datetime | None = None) -> dict[str, Any]:
    """Tạo phiên chat mới cho 1 ticket, hoặc tái dùng phiên `waiting`/`active`
    đã có cho ĐÚNG ticket đó (khách bấm lại nút mở chat không tạo trùng phiên
    — cùng nguyên tắc chống trùng đã áp dụng cho create_ticket/flag_human_handoff)."""
    now = now or dt.datetime.utcnow()

    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        raise ToolError(f"ticket_id không tồn tại: {ticket_id}")
    complaint = session.get(Complaint, ticket.complaint_id)
    if complaint is None or complaint.user_id != customer_id:
        raise ToolError(f"ticket_id không thuộc customer_id đang mở chat: {ticket_id}")

    existing = session.scalars(
        select(ChatSession)
        .where(ChatSession.ticket_id == ticket_id, ChatSession.status.in_(("waiting", "active")))
        .order_by(ChatSession.started_at.desc())
    ).first()
    if existing is not None:
        return _session_to_dict(existing)

    chat_session = ChatSession(
        chat_session_id=new_id("CHS"),
        ticket_id=ticket_id,
        customer_id=customer_id,
        status="waiting",
        started_at=now,
    )
    session.add(chat_session)
    session.flush()
    return _session_to_dict(chat_session)


def claim_session(session: Session, *, chat_session_id: str, staff_id: str, now: dt.datetime | None = None) -> dict[str, Any] | None:
    """Optimistic-concurrency claim — chỉ thành công nếu CHƯA ai nhận
    (`claimed_by IS NULL`). Trả None nếu đã bị người khác nhận trước (caller
    tự xử lý thông báo "đã có người nhận"), không raise — đây là tình huống
    bình thường khi 2 CSKH cùng bấm nhận 1 lúc, không phải lỗi hệ thống."""
    now = now or dt.datetime.utcnow()

    result = session.execute(
        update(ChatSession)
        .where(ChatSession.chat_session_id == chat_session_id, ChatSession.claimed_by.is_(None))
        .values(claimed_by=staff_id, status="active", claimed_at=now)
    )
    session.flush()
    if result.rowcount == 0:
        return None

    chat_session = session.get(ChatSession, chat_session_id)
    return _session_to_dict(chat_session)


def close_session(session: Session, *, chat_session_id: str, now: dt.datetime | None = None) -> dict[str, Any]:
    now = now or dt.datetime.utcnow()
    chat_session = session.get(ChatSession, chat_session_id)
    if chat_session is None:
        raise ToolError(f"chat_session_id không tồn tại: {chat_session_id}")
    chat_session.status = "closed"
    chat_session.closed_at = now
    session.flush()
    return _session_to_dict(chat_session)


def transfer_session(session: Session, *, chat_session_id: str) -> dict[str, Any]:
    """Chuyển ca (shift handoff) — gỡ claimed_by, quay lại hàng chờ. KHÔNG
    cần cơ chế note bàn giao riêng: transcript (messages) + ngữ cảnh AI
    (qua ticket_id) đã đủ để CSKH tiếp theo thấy toàn bộ ngay lập tức."""
    chat_session = session.get(ChatSession, chat_session_id)
    if chat_session is None:
        raise ToolError(f"chat_session_id không tồn tại: {chat_session_id}")
    chat_session.claimed_by = None
    chat_session.status = "waiting"
    chat_session.claimed_at = None
    session.flush()
    return _session_to_dict(chat_session)


def record_message(
    session: Session,
    *,
    chat_session_id: str,
    role: str,
    content: str,
    now: dt.datetime | None = None,
) -> dict[str, Any]:
    now = now or dt.datetime.utcnow()
    chat_session = session.get(ChatSession, chat_session_id)
    if chat_session is None:
        raise ToolError(f"chat_session_id không tồn tại: {chat_session_id}")

    message = Message(
        message_id=new_id("MSG"),
        chat_session_id=chat_session_id,
        ticket_id=chat_session.ticket_id,
        role=role,
        content=content,
        tool_call_ids=[],
        created_at=now,
    )
    session.add(message)
    session.flush()
    return {
        "message_id": message.message_id,
        "chat_session_id": chat_session_id,
        "role": role,
        "content": content,
        "created_at": message.created_at.isoformat(),
    }


def submit_csat(session: Session, *, chat_session_id: str, score: int, now: dt.datetime | None = None) -> dict[str, Any]:
    if not 1 <= score <= 5:
        raise ToolError(f"csat score không hợp lệ (phải 1-5): {score}")
    now = now or dt.datetime.utcnow()
    chat_session = session.get(ChatSession, chat_session_id)
    if chat_session is None:
        raise ToolError(f"chat_session_id không tồn tại: {chat_session_id}")
    chat_session.csat_score = score
    chat_session.csat_submitted_at = now
    session.flush()
    return _session_to_dict(chat_session)


def get_handoff_context(session: Session, *, ticket_id: str) -> dict[str, Any]:
    """Bàn giao TOÀN BỘ ngữ cảnh AI đã điều tra cho CSKH ngay khi nhận ca —
    tránh khách phải lặp lại thông tin (yêu cầu nghiệp vụ đã chốt). Chỉ đọc
    dữ liệu đã có (Ticket/Complaint/InvestigationLog), không suy diễn thêm."""
    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        raise ToolError(f"ticket_id không tồn tại: {ticket_id}")
    complaint = session.get(Complaint, ticket.complaint_id)
    customer = session.get(User, complaint.user_id) if complaint else None
    logs = session.scalars(
        select(InvestigationLog).where(InvestigationLog.ticket_id == ticket_id).order_by(InvestigationLog.step_no)
    ).all()

    return {
        "ticket": {
            "ticket_id": ticket.ticket_id,
            "hitl_status": ticket.hitl_status,
            "sla_due_at": ticket.sla_due_at.isoformat(),
            "human_handoff_requested": ticket.human_handoff_requested,
        },
        "complaint": (
            {
                "complaint_id": complaint.complaint_id,
                "type": complaint.type,
                "scope": complaint.scope,
                "priority": complaint.priority,
                "trans_id": complaint.trans_id,
                "description_raw": complaint.description_raw,
                "fraud_signals": complaint.fraud_signals,
            }
            if complaint
            else None
        ),
        "customer": (
            {"user_id": customer.user_id, "full_name": customer.full_name, "phone": customer.phone}
            if customer
            else None
        ),
        "investigation_logs": [
            {
                "step_no": log.step_no,
                "tool_called": log.tool_called,
                "tool_input_json": log.tool_input_json,
                "agent_note": log.agent_note,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
    }


def _session_to_dict(chat_session: ChatSession) -> dict[str, Any]:
    return {
        "chat_session_id": chat_session.chat_session_id,
        "ticket_id": chat_session.ticket_id,
        "customer_id": chat_session.customer_id,
        "status": chat_session.status,
        "claimed_by": chat_session.claimed_by,
        "started_at": chat_session.started_at.isoformat(),
        "claimed_at": chat_session.claimed_at.isoformat() if chat_session.claimed_at else None,
        "closed_at": chat_session.closed_at.isoformat() if chat_session.closed_at else None,
        "csat_score": chat_session.csat_score,
    }
