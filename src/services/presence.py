"""ADR-063 — presence CSKH/Sếp qua Redis TTL. KHÔNG giữ state trong process —
backend chạy nhiều worker độc lập (multiprocessing), state trong biến process
sẽ chỉ đúng cho ĐÚNG worker nhận request đó, sai cho N-1 worker còn lại.
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


def so_ve_dang_xu_ly(session: Session, *, user_id: str) -> int:
    """ADR-063 — công thức PO chốt: phiên live-chat đang `active` CSKH này
    nhận + resolution CSKH này đề xuất còn `pending_approval`. Vé là kho
    CHUNG (không `claimed_by` trên Complaint) nên đây là ước lượng khối
    lượng công việc TRỰC TIẾP đo được, không phải sở hữu vé."""
    so_chat = (
        session.scalar(
            select(func.count())
            .select_from(ChatSession)
            .where(ChatSession.claimed_by == user_id, ChatSession.status == "active")
        )
        or 0
    )
    so_resolution = (
        session.scalar(
            select(func.count())
            .select_from(Resolution)
            .where(Resolution.created_by == user_id, Resolution.status == "pending_approval")
        )
        or 0
    )
    return so_chat + so_resolution
