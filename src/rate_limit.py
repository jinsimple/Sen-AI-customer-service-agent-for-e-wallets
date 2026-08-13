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


class RedisConcurrencyLimiter:
    """Giới hạn số tác vụ CHẠY SONG SONG (khác rate limit: đếm tần suất).

    VÌ SAO CẦN, KHÁC GÌ RATE LIMIT
    ------------------------------
    Rate limit chặn theo *số lần gọi trong một khoảng thời gian*. Nó KHÔNG
    chặn được kịch bản 150 người cùng bấm gửi trong 1 giây rồi tất cả cùng
    nằm chờ: mỗi người chỉ gọi 1 lần (không vượt rate limit nào cả) nhưng
    150 lượt agent cùng chạy sẽ (a) vét sạch threadpool 40 luồng của
    Starlette, (b) bắn đồng loạt vào OpenAI và ăn bão 429 vì vượt 200K TPM.

    Đo thật 2026-08-13: 1 lượt chat = ~15.136 token, hạn mức 200.000 TPM
    => trần lý thuyết ~13 lượt/phút cho TOÀN hệ thống. Chặn đồng thời là
    cách biến "hỏng hỗn loạn" (429 hàng loạt, request treo) thành "hỏng có
    kiểm soát" (báo bận rõ ràng, mời thử lại).

    VÌ SAO DÙNG REDIS, KHÔNG DÙNG BIẾN TRONG PROCESS
    ------------------------------------------------
    Hạn mức TPM của OpenAI là hạn mức TOÀN CỤC cho cả tài khoản. Đếm trong
    RAM từng process sẽ nhân hạn mức lên theo số worker — chạy 4 worker là
    vượt trần gấp 4 lần mà mỗi worker vẫn tưởng mình đúng luật.

    CƠ CHẾ: ZSET với score = deadline. Slot tự hết hạn sau `ttl_seconds` —
    đây là LƯỚI AN TOÀN bắt buộc: process chết giữa chừng (OOM, SIGKILL,
    deploy) sẽ không trả slot, không có TTL thì hệ thống tự khoá vĩnh viễn
    với 0 request chạy. TTL nên đặt LỚN HƠN timeout tác vụ (45s) để slot
    không bị thu hồi khi tác vụ còn đang chạy hợp lệ.
    """

    def __init__(self, *, max_concurrent: int, ttl_seconds: float, name: str = "agent_turn"):
        self._max = max_concurrent
        self._ttl = ttl_seconds
        self._key = f"concurrency:{name}"

    def acquire(self) -> str | None:
        """Trả token giữ slot nếu còn chỗ, None nếu đã đầy. KHÔNG chờ, KHÔNG chặn.

        Cố ý không xếp hàng chờ: giữ request nằm chờ trong 1 worker duy nhất
        chính là thứ gây nghẽn dây chuyền. Trả lời "đang bận, thử lại" ngay
        lập tức tốt hơn cho người dùng lẫn hệ thống.
        """
        client = get_default_client()
        now = time.time()
        client.zremrangebyscore(self._key, 0, now)  # dọn slot quá hạn
        if client.zcard(self._key) >= self._max:
            return None
        token = secrets.token_hex(8)
        client.zadd(self._key, {token: now + self._ttl})
        client.expire(self._key, int(self._ttl) + 60)
        return token

    def release(self, token: str | None) -> None:
        """Luôn gọi trong `finally` — quên trả slot thì hệ thống tự bóp cổ mình."""
        if not token:
            return
        get_default_client().zrem(self._key, token)

    def in_flight(self) -> int:
        client = get_default_client()
        client.zremrangebyscore(self._key, 0, time.time())
        return int(client.zcard(self._key))
