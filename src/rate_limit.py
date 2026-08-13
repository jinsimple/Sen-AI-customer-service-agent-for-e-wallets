"""Sliding-window rate limiter dùng chung trên Redis (đợt nâng cấp Auth Flow,
2026-08-12) — thay `InMemoryRateLimiter` cũ (src/api/live_chat_ws.py, in-process
dict) để rate-limit sống sót qua restart backend và nhất quán trạng thái với
JWT revocation (cũng trên Redis, xem src/auth.py). Cùng thuật toán sliding
window (ZSET, score=timestamp) — chỉ đổi NƠI LƯU, không đổi ngữ nghĩa.
"""
from __future__ import annotations

import secrets
import time

from src.redis_client import get_default_client


class RedisSlidingWindowLimiter:
    def __init__(self, *, max_calls: int, window_seconds: float):
        self._max_calls = max_calls
        self._window_seconds = window_seconds

    def allow(self, key: str) -> bool:
        client = get_default_client()
        now = time.time()
        window_start = now - self._window_seconds
        redis_key = f"ratelimit:{key}"
        client.zremrangebyscore(redis_key, 0, window_start)
        if client.zcard(redis_key) >= self._max_calls:
            return False
        # member phải DUY NHẤT — 2 lệnh gọi cùng 1 timestamp float (rất có
        # thể xảy ra, đồng hồ hệ thống không đủ độ phân giải) sẽ bị ZADD gộp
        # thành 1 member nếu chỉ dùng timestamp làm member, đếm thiếu.
        member = f"{now}:{secrets.token_hex(4)}"
        client.zadd(redis_key, {member: now})
        client.expire(redis_key, int(self._window_seconds) + 1)
        return True
