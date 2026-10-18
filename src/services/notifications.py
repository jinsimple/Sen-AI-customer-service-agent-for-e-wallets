"""ADR-063 — notification bell: fan-out + read/mark-as-read.

Fan-out: ONE Notification row per recipient, created in the SAME transaction as the
originating event (ticket created/proposal/approval/rejection) — no `session.commit()`
here, the caller commits; if the ticket rolls back the notification rolls back with it,
so there are no "ghost" notifications for events that never really happened.

Recipient isolation (anti-BOLA): EVERY read/mark-read function below filters
`recipient_user_id == user_id` inside the SQL itself — never read-then-compare, so there is
no path that leaks someone else's notifications via timing/errors.
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


def notify_new_ticket(session: Session, *, ticket_id: str) -> list[str]:
    """New ticket created — notify ALL CSKH agents (the ticket pool is shared, unclaimed)."""
    cskh_ids = list(session.scalars(select(User.user_id).where(User.role == "cskh")).all())
    return fan_out(session, event_type="ve_moi", ticket_id=ticket_id, recipient_user_ids=cskh_ids)


def notify_pending_approval(session: Session, *, ticket_id: str) -> list[str]:
    """Resolution moved to pending_approval — notify ALL supervisors (any of them may approve)."""
    sup_ids = list(session.scalars(select(User.user_id).where(User.role == "supervisor")).all())
    return fan_out(session, event_type="cho_duyet", ticket_id=ticket_id, recipient_user_ids=sup_ids)


def notify_decided(
    session: Session, *, ticket_id: str, cskh_user_id: str, approved: bool
) -> list[str]:
    """Supervisor approved/rejected — notify BACK exactly the 1 CSKH agent who proposed it (Resolution.created_by)."""
    event_type = "da_duyet" if approved else "da_tu_choi"
    return fan_out(
        session, event_type=event_type, ticket_id=ticket_id, recipient_user_ids=[cskh_user_id]
    )


def count_unread(session: Session, *, user_id: str) -> int:
    return (
        session.scalar(
            select(func.count())
            .select_from(Notification)
            .where(Notification.recipient_user_id == user_id, Notification.read_at.is_(None))
        )
        or 0
    )


def listing(session: Session, *, user_id: str, limit: int = 50) -> list[Notification]:
    return list(
        session.scalars(
            select(Notification)
            .where(Notification.recipient_user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        ).all()
    )


def mark_read(session: Session, *, user_id: str, notification_id: str, now: dt.datetime | None = None) -> bool:
    """True if marked — False if it does not exist OR does not belong to
    `user_id` (both cases deliberately collapse into ONE result: distinguishing
    "doesn't exist" from "not yours" would let a client probe whether other users'
    notifications exist — exactly the subtle kind of IDOR leak)."""
    n = session.get(Notification, notification_id)
    if n is None or n.recipient_user_id != user_id:
        return False
    n.read_at = now or dt.datetime.utcnow()
    session.flush()
    return True


def mark_all_read(session: Session, *, user_id: str, now: dt.datetime | None = None) -> int:
    now = now or dt.datetime.utcnow()
    unread = session.scalars(
        select(Notification).where(
            Notification.recipient_user_id == user_id, Notification.read_at.is_(None)
        )
    ).all()
    for n in unread:
        n.read_at = now
    if unread:
        session.flush()
    return len(unread)
