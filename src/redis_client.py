"""Shared Redis client — JWT refresh-token revocation store (src/auth.py) and
synchronised rate limiting (login/OTP/live-chat, Auth Flow upgrade 2026-08-12).

Supports `REDIS_URL=fake://...` -> fakeredis.FakeStrictRedis, for CI/tests that need
no real Redis (per playbooks/production-packaging-checklist.md convention
"REDIS_URL: fake://"). Real Redis enables `socket_keepalive` + `health_check_interval`
(same checklist, "Reliability & Scaling") — cloud internal networks (NAT/proxy) silently
close idle connections; without these two flags the next request reuses a dead socket
-> random production errors even though everything works perfectly locally.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from src.config import REDIS_URL

if TYPE_CHECKING:
    from redis import Redis

_client: Redis | None = None  # lazily created via get_redis_client() so tests can override REDIS_URL


def get_redis_client(redis_url: str | None = None) -> Redis:
    url = redis_url or REDIS_URL

    if url.startswith("fake://"):
        import fakeredis

        # server= keeps the same fakeredis.FakeServer for every client with the same URL in
        # one process — otherwise each new get_redis_client() creates its own separate "server",
        # and data written in one place cannot be read in another despite the same URL (every call
        # would create a new, empty fake data store).
        return fakeredis.FakeStrictRedis.from_url(
            url.replace("fake://", "redis://"), server=_fake_server(), decode_responses=True
        )

    import redis

    return redis.Redis.from_url(url, socket_keepalive=True, health_check_interval=30, decode_responses=True)


_fake_server_singleton = None


def _fake_server():
    global _fake_server_singleton
    if _fake_server_singleton is None:
        import fakeredis

        _fake_server_singleton = fakeredis.FakeServer()
    return _fake_server_singleton


def get_default_client() -> Redis:
    """Singleton used on the real request path (unlike get_redis_client(), which tests
    use to inject their own URL/instance via dependency override)."""
    global _client
    if _client is None:
        _client = get_redis_client()
    return _client
