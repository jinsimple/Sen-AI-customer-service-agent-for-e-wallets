"""ADR-063 — chuông thông báo: fan-out + đọc/đánh dấu đã đọc.

Fan-out: MỘT hàng Notification/người nhận, tạo trong CÙNG transaction với sự
kiện gốc (tạo vé/đề xuất/duyệt/từ chối) — không `session.commit()` ở đây,
caller chịu trách nhiệm commit; vé rollback thì thông báo rollback theo,
không có thông báo "ma" cho sự kiện chưa từng xảy ra thật.

Cô lập theo người nhận (chống BOLA): MỌI hàm đọc/ghi trạng thái đọc ở dưới
đều lọc `recipient_user_id == user_id` ngay trong câu SQL — không đọc rồi so
sánh sau, để không có đường nào lộ thông báo của người khác qua timing/lỗi.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.db.models import Notification, User
from src.tools.base import new_id


def fan_out(
    session: Session,
    *,
    event_type: str,
    ticket_id: str,
    recipient_user_ids: list[str],
    now: dt.datetime | None = None,
) -> list[str]:
    now = now or dt.datetime.utcnow()
    ids: list[str] = []
    for uid in recipient_user_ids:
        nid = new_id("NOTI")
        session.add(
            Notification(
                notification_id=nid,
                recipient_user_id=uid,
                event_type=event_type,
                ticket_id=ticket_id,
                created_at=now,
            )
        )
        ids.append(nid)
    if ids:
        session.flush()
    return ids


def notify_ve_moi(session: Session, *, ticket_id: str) -> list[str]:
    """Vé mới tạo — báo TOÀN BỘ CSKH (vé là kho chung, chưa ai nhận)."""
    cskh_ids = list(session.scalars(select(User.user_id).where(User.role == "cskh")).all())
    return fan_out(session, event_type="ve_moi", ticket_id=ticket_id, recipient_user_ids=cskh_ids)


def notify_cho_duyet(session: Session, *, ticket_id: str) -> list[str]:
    """Resolution chuyển pending_approval — báo TOÀN BỘ Sếp (ai duyệt cũng được)."""
    sup_ids = list(session.scalars(select(User.user_id).where(User.role == "supervisor")).all())
    return fan_out(session, event_type="cho_duyet", ticket_id=ticket_id, recipient_user_ids=sup_ids)


def notify_da_quyet_dinh(
    session: Session, *, ticket_id: str, cskh_user_id: str, approved: bool
) -> list[str]:
    """Sếp duyệt/từ chối — báo NGƯỢC đúng 1 CSKH đã đề xuất (Resolution.created_by)."""
    event_type = "da_duyet" if approved else "da_tu_choi"
    return fan_out(
        session, event_type=event_type, ticket_id=ticket_id, recipient_user_ids=[cskh_user_id]
    )


def dem_chua_doc(session: Session, *, user_id: str) -> int:
    return (
        session.scalar(
            select(func.count())
            .select_from(Notification)
            .where(Notification.recipient_user_id == user_id, Notification.read_at.is_(None))
        )
        or 0
    )


def liet_ke(session: Session, *, user_id: str, limit: int = 50) -> list[Notification]:
    return list(
        session.scalars(
            select(Notification)
            .where(Notification.recipient_user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        ).all()
    )


def danh_dau_da_doc(session: Session, *, user_id: str, notification_id: str, now: dt.datetime | None = None) -> bool:
    """True nếu đánh dấu được — False nếu không tồn tại HOẶC không thuộc
    `user_id` (hai trường hợp gộp CHUNG một kết quả, có chủ đích: phân biệt
    "không có" với "không phải của bạn" sẽ lộ cho client dò được thông báo
    người khác có tồn tại hay không — đúng loại rò IDOR tinh vi)."""
    n = session.get(Notification, notification_id)
    if n is None or n.recipient_user_id != user_id:
        return False
    n.read_at = now or dt.datetime.utcnow()
    session.flush()
    return True


def danh_dau_tat_ca_da_doc(session: Session, *, user_id: str, now: dt.datetime | None = None) -> int:
    now = now or dt.datetime.utcnow()
    chua_doc = session.scalars(
        select(Notification).where(
            Notification.recipient_user_id == user_id, Notification.read_at.is_(None)
        )
    ).all()
    for n in chua_doc:
        n.read_at = now
    if chua_doc:
        session.flush()
    return len(chua_doc)
