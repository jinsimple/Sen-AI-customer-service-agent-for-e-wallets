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

🔴 "FAIL-OPEN" ở `RedisSlidingWindowLimiter` nghĩa là CHO QUA (không còn trần
nào lúc Redis chết — chấp nhận được, đây là rate-limit theo TẦN SUẤT). Ở
`RedisConcurrencyLimiter` (chặn ĐỒNG THỜI) nghĩa KHÁC — xem khối comment
"LƯỚI DỰ PHÒNG IN-PROCESS" ngay trên lớp đó: Review 24/08 bắt bản vá đầu ở
đây fail-open KHÔNG TRẦN, đúng lớp sinh ra để chặn "150 người cùng bấm gửi"
lại là lớp mất hẳn khi Redis chết. Giờ fail-open CÓ TRẦN, cùng khuôn slowapi
đã tự chọn (`in_memory_fallback_enabled` — suy yếu per-process, không mất trắng).
"""
from __future__ import annotations

import logging
import secrets
import threading
import time

from src.redis_client import get_default_client

_logger = logging.getLogger("fin05.rate_limit")

# Tiền tố token của lưới dự phòng IN-PROCESS (RedisConcurrencyLimiter, xem
# lớp dưới) — `release()` nhận biết qua tiền tố này để trả slot vào bộ đếm
# trong RAM thay vì `zrem` một token Redis chưa từng được ghi.
_TIEN_TO_FALLBACK = "fb:"


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

    🔴 LƯỚI DỰ PHÒNG IN-PROCESS khi Redis chết (24/08 — Review đọc `1a33239`,
    thấy commit message làm PHẲNG một bất đối xứng: slowapi (`src/api/main.py`,
    `in_memory_fallback_enabled=True`) khi Redis chết vẫn còn MỘT trần — rơi về
    RAM mỗi worker, SUY YẾU chứ không mất; lớp này bản vá đầu chỉ trả sentinel
    fail-open KHÔNG kèm trần nào — MẤT HẲN. Và đây đúng là lớp sinh ra để chặn
    *"150 người cùng bấm gửi"* (đoạn docstring trên) — đúng kịch bản buổi test
    150 người dùng thật PO thật đang chuẩn bị. Redis nấc một nhịp giữa buổi đó
    thì lớp bảo vệ cho CHÍNH kịch bản ấy biến mất không còn gì thay thế.

    Áp cùng khuôn slowapi đã tự chọn cho mình: một `threading.Lock` + dict
    trong RAM (`_fallback_slots`, token -> deadline), CÙNG `max_concurrent`/
    `ttl_seconds` đã khai — khi Redis sống lại, `acquire()` tự quay về ZSET,
    không cần dọn gì (`_fallback_slots` không rò rỉ vì slot tự hết hạn qua TTL
    giống hệt cơ chế Redis).

    🔴 ĐÁNH ĐỔI PHẢI NÓI RÕ, không để trôi: bộ đếm này là PER-PROCESS (khác
    ZSET Redis — dùng CHUNG cho mọi worker). Server chạy N worker
    (`docker-entrypoint.sh` — `UVICORN_WORKERS=4`) ⟹ lúc Redis chết, trần THỰC
    TẾ toàn hệ thống là **~N × max_concurrent**, không còn là **max_concurrent
    dùng chung** như lúc Redis sống — đúng đánh đổi "VÌ SAO DÙNG REDIS, KHÔNG
    DÙNG BIẾN TRONG PROCESS" ở trên đã cảnh báo, giờ CHỦ ĐỘNG chấp nhận nó
    TRONG MỘT CỬA SỔ NGẮN (lúc hạ tầng phụ trợ chết) thay vì chấp nhận nó VĨNH
    VIỄN. Đây là SUY YẾU CÓ KIỂM SOÁT (N× trần), không phải MẤT TRẮNG (0 trần)
    — đúng bản chất đánh đổi slowapi đã chọn, không phải một khuôn mới.
    """

    def __init__(self, *, max_concurrent: int, ttl_seconds: float, name: str = "agent_turn"):
        self._max = max_concurrent
        self._ttl = ttl_seconds
        self._key = f"concurrency:{name}"
        self._fallback_lock = threading.Lock()
        self._fallback_slots: dict[str, float] = {}  # token(có tiền tố fb:) -> deadline

    def _fallback_acquire(self) -> str | None:
        now = time.time()
        with self._fallback_lock:
            for tok in [t for t, deadline in self._fallback_slots.items() if deadline <= now]:
                del self._fallback_slots[tok]  # dọn slot quá hạn, cùng ý nghĩa TTL bên Redis
            if len(self._fallback_slots) >= self._max:
                return None
            token = _TIEN_TO_FALLBACK + secrets.token_hex(8)
            self._fallback_slots[token] = now + self._ttl
            return token

    def _fallback_release(self, token: str) -> None:
        with self._fallback_lock:
            self._fallback_slots.pop(token, None)

    def acquire(self) -> str | None:
        """Trả token giữ slot nếu còn chỗ, None nếu đã đầy. KHÔNG chờ, KHÔNG chặn.

        Cố ý không xếp hàng chờ: giữ request nằm chờ trong 1 worker duy nhất
        chính là thứ gây nghẽn dây chuyền. Trả lời "đang bận, thử lại" ngay
        lập tức tốt hơn cho người dùng lẫn hệ thống.

        Redis lỗi -> fail-open CÓ TRẦN: rơi về lưới dự phòng in-process (xem
        khối comment trên lớp), KHÔNG raise, KHÔNG mất hẳn giới hạn.
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
                "concurrency_acquire_redis_loi_roi_ve_fallback",
                extra={"key": self._key, "loi": repr(e)},
            )
            return self._fallback_acquire()

    def release(self, token: str | None) -> None:
        """Luôn gọi trong `finally` — quên trả slot thì hệ thống tự bóp cổ mình.

        Token fallback (tiền tố `fb:`) không ứng với khoá Redis nào — trả về
        lưới in-process thay vì `zrem` một token Redis chưa từng ghi (chỉ ăn
        thêm một lỗi Redis giống hệt lúc acquire). Redis lỗi Ở ĐÂY (khác lúc
        acquire, với token Redis thật) -> log, KHÔNG raise: đang ở `finally`,
        raise tại đây sẽ NUỐT MẤT exception gốc đang bay lên.
        """
        if not token:
            return
        if token.startswith(_TIEN_TO_FALLBACK):
            self._fallback_release(token)
            return
        try:
            get_default_client().zrem(self._key, token)
        except Exception as e:  # noqa: BLE001
            _logger.warning(
                "concurrency_release_that_bai",
                extra={"key": self._key, "loi": repr(e)},
            )

    def in_flight(self) -> int:
        """Redis lỗi -> đếm slot đang giữ ở lưới dự phòng in-process (CHỈ đúng
        cho WORKER NÀY, không phải toàn hệ thống — xem đánh đổi per-process ở
        khối comment trên lớp), KHÔNG còn trả `-1` mù — có số thật thì dùng
        số thật, dù phạm vi hẹp hơn lúc Redis sống."""
        try:
            client = get_default_client()
            client.zremrangebyscore(self._key, 0, time.time())
            return int(client.zcard(self._key))
        except Exception as e:  # noqa: BLE001
            _logger.warning(
                "concurrency_in_flight_redis_loi_roi_ve_fallback",
                extra={"key": self._key, "loi": repr(e)},
            )
            now = time.time()
            with self._fallback_lock:
                return sum(1 for deadline in self._fallback_slots.values() if deadline > now)
