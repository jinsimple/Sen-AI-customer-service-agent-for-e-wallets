"""Context propagation via `contextvars` — `correlation_id`/`user_id` are bound EXACTLY
ONCE at the entry point (HTTP middleware, see src/api/main.py); every callee
(agent, tool, log) inherits them automatically through contextvars without threading
them through every function parameter.

Safe for asyncio (each Starlette request runs in its own Task; contextvars are copied when
a Task is created, so set() in request A never leaks into request B)
AND safe for the threadpool (sync `def` routes run via `anyio.to_thread.run_sync`, which
also copies the context into the thread) — yet we still use the `Token` + `reset()`
pattern in try/finally (NOT setting straight back to None), as the standard `contextvars`
guidance recommends, so we never accidentally wipe a parent scope's context
(defence in depth, not relying solely on the natural isolation of asyncio Tasks)."""
from __future__ import annotations

import contextvars

_correlation_id: contextvars.ContextVar[str | None] = contextvars.ContextVar("correlation_id", default=None)
_user_id: contextvars.ContextVar[str | None] = contextvars.ContextVar("ctx_user_id", default=None)


def bind_context(*, correlation_id: str, user_id: str | None = None) -> tuple[contextvars.Token, contextvars.Token]:
    """Call ONCE at the start of each request (middleware). Returns a token so the caller
    can `reset()` at exactly the end of the request — see clear_context()."""
    token_corr = _correlation_id.set(correlation_id)
    token_user = _user_id.set(user_id)
    return token_corr, token_user


def clear_context(tokens: tuple[contextvars.Token, contextvars.Token]) -> None:
    """Must be called in `finally` after every request — see the module docstring."""
    token_corr, token_user = tokens
    _correlation_id.reset(token_corr)
    _user_id.reset(token_user)


def get_correlation_id() -> str | None:
    return _correlation_id.get()


def get_context_user_id() -> str | None:
    return _user_id.get()
