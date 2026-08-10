"""Context propagation qua `contextvars` — gắn `correlation_id`/`user_id` ĐÚNG
1 LẦN ở entry point (middleware HTTP, xem src/api/main.py), mọi hàm con
(agent, tool, log) tự động thừa hưởng qua contextvars mà không cần truyền tay
qua từng tham số hàm.

An toàn cho asyncio (mỗi request Starlette chạy trong 1 Task riêng, contextvars
được copy khi Task tạo mới nên set() trong request A không lộ sang request B)
VÀ an toàn cho threadpool (route `def` đồng bộ chạy qua `anyio.to_thread.run_sync`
cũng copy context sang thread) — nhưng vẫn dùng pattern `Token` + `reset()`
trong try/finally (KHÔNG set thẳng về None) theo đúng khuyến nghị chuẩn của
`contextvars`, để không vô tình xoá mất context của một scope cha nào đó
(phòng hờ, không chỉ dựa vào tính cô lập tự nhiên của asyncio Task)."""
from __future__ import annotations

import contextvars

_correlation_id: contextvars.ContextVar[str | None] = contextvars.ContextVar("correlation_id", default=None)
_user_id: contextvars.ContextVar[str | None] = contextvars.ContextVar("ctx_user_id", default=None)


def bind_context(*, correlation_id: str, user_id: str | None = None) -> tuple[contextvars.Token, contextvars.Token]:
    """Gọi 1 LẦN ở đầu mỗi request (middleware). Trả về token để caller
    `reset()` đúng lúc kết thúc request — xem clear_context()."""
    token_corr = _correlation_id.set(correlation_id)
    token_user = _user_id.set(user_id)
    return token_corr, token_user


def clear_context(tokens: tuple[contextvars.Token, contextvars.Token]) -> None:
    """Bắt buộc gọi ở `finally` sau mỗi request — xem docstring module."""
    token_corr, token_user = tokens
    _correlation_id.reset(token_corr)
    _user_id.reset(token_user)


def get_correlation_id() -> str | None:
    return _correlation_id.get()


def get_context_user_id() -> str | None:
    return _user_id.get()
