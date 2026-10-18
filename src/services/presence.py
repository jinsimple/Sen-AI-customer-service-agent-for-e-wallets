"""ADR-063 — CSKH/supervisor presence via Redis TTL. NO state is kept in-process —
the backend runs several independent workers (multiprocessing); state held in a process
variable would only be correct for the ONE worker that received the request and wrong for
the other N-1.
"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.db.models import ChatSession, Resolution
from src.redis_client import get_redis_client

_TTL_S = 45
_PREFIX = "presence:staff:"


def heartbeat(user_id: str) -> None:
    get_redis_client().set(f"{_PREFIX}{user_id}", "1", ex=_TTL_S)


def is_online(user_id: str) -> bool:
    return bool(get_redis_client().exists(f"{_PREFIX}{user_id}"))


def online_user_ids(candidate_user_ids: list[str]) -> set[str]:
    r = get_redis_client()
    return {uid for uid in candidate_user_ids if r.exists(f"{_PREFIX}{uid}")}


def open_ticket_count(session: Session, *, user_id: str) -> int:
    """ADR-063 — formula fixed by the PO: live-chat sessions in `active` state claimed by
    this agent + resolutions proposed by this agent still in `pending_approval`. The ticket pool
    is SHARED (no `claimed_by` on Complaint), so this is a DIRECTLY measurable workload
    estimate, not ticket ownership."""
    chat_count = (
        session.scalar(
            select(func.count())
            .select_from(ChatSession)
            .where(ChatSession.claimed_by == user_id, ChatSession.status == "active")
        )
        or 0
    )
    resolution_count = (
        session.scalar(
            select(func.count())
            .select_from(Resolution)
            .where(Resolution.created_by == user_id, Resolution.status == "pending_approval")
        )
        or 0
    )
    return chat_count + resolution_count
