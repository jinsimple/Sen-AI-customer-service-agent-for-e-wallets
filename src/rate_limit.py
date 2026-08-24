"""Sliding-window rate limiter dùng chung trên Redis (đợt nâng cấp Auth Flow,
2026-08-12) — thay `InMemoryRateLimiter` cũ (src/api/live_chat_ws.py, in-process
dict) để rate-limit sống sót qua restart backend và nhất quán trạng thái với
JWT revocation (cũng trên Redis, xem src/auth.py). Cùng thuật toán sliding
window (ZSET, score=timestamp) — chỉ đổi NƠI LƯU, không đổi ngữ nghĩa.

🔴 FAIL-OPEN khi Redis lỗi (24/08 — Tester tắt Redis, `/agent/chat` SẬP HẲN,
không trả response nào, vì cả lớp này VÀ `@limiter.limit` của slowapi đều
không che `ConnectionError`). Cùng triết lý `thread_signals.py`/`llm_pool.py`:
đây là hạ tầng PHỤ TRỢ (chặn quá tải), không phải cửa vào — một sự cố Redis
không được phép biến thành một sự cố toàn hệ thống. Khác `cong_ra_ngoai.py`
(trần chi tiêu, fail-CLOSED có chủ đích vì đó là cơ chế bảo vệ TIỀN): ở đây
mất bảo vệ-quá-tải tạm thời trong lúc Redis chết vẫn RẺ HƠN việc mọi khách
nhận lỗi kết nối. slowapi (`src/api/main.py`, `Limiter(in_memory_fallback_
enabled=True)`) vá lớp `@limiter.limit`; file này vá lớp gọi trực tiếp.
"""
from __future__ import annotations

import logging
import secrets
import time

from src.redis_client import get_default_client

_logger = logging.getLogger("fin05.rate_limit")

# Token sentinel cho lượt fail-open ở RedisConcurrencyLimiter.acquire() —
# KHÔNG phải khoá Redis thật, `release()` nhận biết để bỏ qua thay vì zrem
# một token chưa từng được ghi (sẽ chỉ ăn thêm một lỗi Redis giống hệt).
_TOKEN_FAIL_OPEN = "fail_open_redis_loi"


class RedisSlidingWindowLimiter:
    """`name` BẮT BUỘC — mỗi limiter phải có vùng khoá Redis riêng.

    Không có tham số này thì mọi limiter dùng chung khoá `ratelimit:{key}`,
    và vì `key` thường là `user_id`, các hạn mức KHÁC NHAU của cùng một người
    ăn lẫn vào nhau. Đo thật (2026-08-13): khách gửi 5 tin live-chat
    (hạn mức riêng 60 tin/giờ) rồi mở phiên chat LẦN ĐẦU (hạn mức riêng
    5 lần/phút, chưa dùng lần nào) -> bị 429 ngay. Chiều ngược lại còn tệ
    hơn: `zremrangebyscore` của limiter cửa sổ 60s XOÁ luôn dữ liệu trong
    cửa sổ 3600s của limiter kia, làm hạn mức 60 tin/giờ bị vô hiệu âm thầm.
    Bắt buộc truyền tên (không đặt mặc định) để lỗi này không quay lại qua
    một limiter mới nào đó quên đặt tên.
    """

    def __init__(self, *, max_calls: int, window_seconds: float, name: str):
        self._max_calls = max_calls
        self._window_seconds = window_seconds
        self._name = name

    def allow(self, key: str) -> bool:
        """Redis lỗi -> fail-open (`True`), log cảnh báo, KHÔNG raise — xem
        khối comment đầu file."""
        try:
            client = get_default_client()
            now = time.time()
            window_start = now - self._window_seconds
            redis_key = f"ratelimit:{self._name}:{key}"
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
        except Exception as e:  # noqa: BLE001
            # 🔴 KHÔNG đặt tên `name` trong `extra=` — thuộc tính DÀNH RIÊNG của
            # `logging.LogRecord` (tên logger), đặt trùng ném `KeyError: "Attempt
            # to overwrite 'name'"` NGAY TRONG NHÁNH FAIL-OPEN — đúng lớp lỗi
            # `ingest.py` đã vấp với `filename` (xem comment ở đó). Không viết
            # bằng tay thì không bắt được: đã đo THẬT qua kịch bản Redis chết.
            _logger.warning(
                "rate_limit_allow_that_bai_fail_open",
                extra={"ten_limiter": self._name, "loi": repr(e)},
            )
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

        Redis lỗi -> fail-open: trả `_TOKEN_FAIL_OPEN` (lượt vẫn được xử lý),
        KHÔNG raise. Đánh đổi có chủ đích, log rõ để không âm thầm: mất lớp
        chặn-đồng-thời trong đúng lúc Redis chết vẫn RẺ HƠN `/agent/chat` sập
        hẳn cho mọi khách vì một ConnectionError không được che.
        """
        try:
            client = get_default_client()
            now = time.time()
            client.zremrangebyscore(self._key, 0, now)  # dọn slot quá hạn
            if client.zcard(self._key) >= self._max:
                return None
            token = secrets.token_hex(8)
            client.zadd(self._key, {token: now + self._ttl})
            client.expire(self._key, int(self._ttl) + 60)
            return token
        except Exception as e:  # noqa: BLE001
            _logger.warning(
                "concurrency_acquire_that_bai_fail_open",
                extra={"key": self._key, "loi": repr(e)},
            )
            return _TOKEN_FAIL_OPEN

    def release(self, token: str | None) -> None:
        """Luôn gọi trong `finally` — quên trả slot thì hệ thống tự bóp cổ mình.

        Token fail-open không ứng với khoá Redis thật nào — bỏ qua thay vì
        `zrem` một token chưa từng ghi (chỉ ăn thêm một lỗi Redis giống hệt
        lúc acquire). Redis lỗi Ở ĐÂY (khác lúc acquire) -> log, KHÔNG raise:
        đang ở `finally`, raise tại đây sẽ NUỐT MẤT exception gốc đang bay lên.
        """
        if not token or token == _TOKEN_FAIL_OPEN:
            return
        try:
            get_default_client().zrem(self._key, token)
        except Exception as e:  # noqa: BLE001
            _logger.warning(
                "concurrency_release_that_bai",
                extra={"key": self._key, "loi": repr(e)},
            )

    def in_flight(self) -> int:
        """Redis lỗi -> `-1` (KHÔNG ĐỌC ĐƯỢC, phân biệt với `0` = thật sự rảnh)."""
        try:
            client = get_default_client()
            client.zremrangebyscore(self._key, 0, time.time())
            return int(client.zcard(self._key))
        except Exception as e:  # noqa: BLE001
            _logger.warning(
                "concurrency_in_flight_that_bai",
                extra={"key": self._key, "loi": repr(e)},
            )
            return -1
