"""Client Redis dùng chung — revocation store JWT refresh token (src/auth.py),
rate-limit đồng bộ (login/OTP/live-chat, đợt nâng cấp Auth Flow 2026-08-12).

Hỗ trợ `REDIS_URL=fake://...` -> fakeredis.FakeStrictRedis, dùng cho CI/test
không cần Redis thật (đúng convention playbooks/production-packaging-checklist.md
"REDIS_URL: fake://"). Redis thật bật `socket_keepalive` + `health_check_interval`
(cùng checklist, mục "Reliability & Scaling") — mạng nội bộ cloud (NAT/proxy) âm
thầm đóng connection nhàn rỗi, thiếu 2 cờ này thì request sau dùng lại socket
chết -> lỗi ngẫu nhiên trên production dù local chạy hoàn hảo.
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

        # server= giữ cùng 1 fakeredis.FakeServer cho mọi client cùng URL trong
        # 1 process — nếu không, mỗi get_redis_client() mới tự tạo 1 "server"
        # riêng biệt, dữ liệu ghi ở nơi này không đọc được ở nơi khác dù cùng
        # URL (mỗi lần gọi lại tạo ra 1 kho dữ liệu giả lập mới, rỗng).
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
    """Singleton dùng ở request path thật (khác get_redis_client(), vốn dùng để
    test tự inject URL/instance riêng qua dependency override)."""
    global _client
    if _client is None:
        _client = get_redis_client()
    return _client
