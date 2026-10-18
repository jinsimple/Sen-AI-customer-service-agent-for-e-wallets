"""Shared sliding-window rate limiter on Redis (Auth Flow upgrade,
2026-08-12) — replaces the old `InMemoryRateLimiter` (src/api/live_chat_ws.py, an in-process
dict) so rate limits survive backend restarts and stay consistent with
JWT revocation (also on Redis, see src/auth.py). Same sliding-window algorithm
(ZSET, score=timestamp) — only WHERE it is stored changed, not the semantics.

🔴 FAIL-OPEN when Redis errors (24/08 — the Tester switched Redis off and `/agent/chat` WENT
DOWN COMPLETELY, returning no response at all, because neither this class NOR slowapi's
`@limiter.limit` handled `ConnectionError`). Same philosophy as
`thread_signals.py`/`llm_pool.py`: this is SUPPORTING infrastructure (overload protection),
not an entry gate — a Redis incident must not turn into a system-wide incident. Unlike
`egress_gate.py` (spending cap, deliberately fail-CLOSED because it protects MONEY): here,
temporarily losing overload protection while Redis is down is still CHEAPER than every
customer getting a connection error. slowapi (`src/api/main.py`,
`Limiter(in_memory_fallback_enabled=True)`) fixes the `@limiter.limit` layer; this file
fixes the direct-call layer.

🔴 "FAIL-OPEN" in `RedisSlidingWindowLimiter` means LET THROUGH (no cap at all while Redis is
down — acceptable, this is FREQUENCY rate limiting). In `RedisConcurrencyLimiter`
(CONCURRENCY limiting) it means something DIFFERENT — see the "IN-PROCESS FALLBACK NET"
comment block right above that class: the 24/08 review caught the first fix here failing
open with NO CAP, so the very layer created to stop "150 people pressing send at once"
vanished entirely when Redis died. It now fails open WITH A CAP, the same pattern slowapi
chose for itself (`in_memory_fallback_enabled` — weakened per process, not wiped out).
"""
from __future__ import annotations

import logging
import secrets
import threading
import time

from src.redis_client import get_default_client

_logger = logging.getLogger("fin05.rate_limit")

# Token prefix for the IN-PROCESS fallback net (RedisConcurrencyLimiter, see the class
# below) — `release()` recognises it by this prefix and returns the slot to the in-RAM counter
# instead of `zrem`-ing a Redis token that was never written.
_FALLBACK_PREFIX = "fb:"


class RedisSlidingWindowLimiter:
    """`name` is MANDATORY — each limiter must have its own Redis key space.

    Without this parameter every limiter shares the key `ratelimit:{key}`,
    and since `key` is usually `user_id`, DIFFERENT limits for the same person bleed into
    each other. Measured (2026-08-13): a customer sent 5 live-chat messages
    (its own limit: 60 messages/hour) and then opened a chat session for the FIRST time (its
    own limit: 5/minute, never used) -> got a 429 immediately. The reverse is even worse:
    the 60s-window limiter's `zremrangebyscore` DELETED the data inside the other limiter's
    3600s window, silently disabling the 60-messages/hour limit.
    The name must be passed explicitly (no default) so this bug can't come back via some new
    limiter that forgets to set one.
    """

    def __init__(self, *, max_calls: int, window_seconds: float, name: str):
        self._max_calls = max_calls
        self._window_seconds = window_seconds
        self._name = name

    def allow(self, key: str) -> bool:
        """Redis error -> fail-open (`True`), log a warning, NEVER raise — see the comment
        block at the top of the file."""
        try:
            client = get_default_client()
            now = time.time()
            window_start = now - self._window_seconds
            redis_key = f"ratelimit:{self._name}:{key}"
            client.zremrangebyscore(redis_key, 0, window_start)
            if client.zcard(redis_key) >= self._max_calls:
                return False
            # members must be UNIQUE — 2 calls with the same float timestamp (quite possible; the
            # system clock's resolution isn't enough) would be merged by ZADD into
            # 1 member if the timestamp alone were the member, under-counting.
            member = f"{now}:{secrets.token_hex(4)}"
            client.zadd(redis_key, {member: now})
            client.expire(redis_key, int(self._window_seconds) + 1)
            return True
        except Exception as e:  # noqa: BLE001
            # 🔴 DO NOT use the key `name` in `extra=` — it is a RESERVED attribute of
            # `logging.LogRecord` (the logger name); reusing it raises `KeyError: "Attempt
            # to overwrite 'name'"` RIGHT INSIDE THE FAIL-OPEN BRANCH — exactly the bug
            # `ingest.py` hit with `filename` (see the comment there). You can't catch this without
            # writing it out: it was measured FOR REAL through a Redis-down scenario.
            _logger.warning(
                "rate_limit_allow_that_bai_fail_open",
                extra={"ten_limiter": self._name, "loi": repr(e)},
            )
            return True


class RedisConcurrencyLimiter:
    """Limits the number of tasks RUNNING CONCURRENTLY (unlike a rate limit, which counts frequency).

    WHY IT IS NEEDED, HOW IT DIFFERS FROM A RATE LIMIT
    --------------------------------------------------
    A rate limit blocks by *number of calls within a time window*. It CANNOT stop the
    scenario of 150 people pressing send within 1 second and all waiting together: each person
    calls only once (no rate limit exceeded) but 150 agent turns running at once would
    (a) exhaust Starlette's 40-thread threadpool, (b) hit OpenAI simultaneously and get
    stormed with 429s for exceeding 200K TPM.

    Measured 2026-08-13: 1 chat turn = ~15,136 tokens, quota 200,000 TPM
    => a theoretical ceiling of ~13 turns/minute for the WHOLE system. Limiting concurrency
    turns "chaotic failure" (mass 429s, hanging requests) into "controlled failure"
    (a clear busy message, inviting a retry).

    WHY REDIS, NOT AN IN-PROCESS VARIABLE
    -------------------------------------
    OpenAI's TPM quota is GLOBAL for the whole account. Counting in each process's RAM would
    multiply the quota by the number of workers — running 4 workers exceeds the ceiling
    4 times while each worker still believes it is within the rules.

    MECHANISM: a ZSET with score = deadline. Slots expire on their own after `ttl_seconds` —
    a MANDATORY SAFETY NET: a process dying midway (OOM, SIGKILL, deploy) will never return
    its slot; without a TTL the system would lock itself permanently with 0 requests running.
    The TTL should be LARGER than the task timeout (45s) so a slot is not reclaimed while its
    task is still legitimately running.

    🔴 IN-PROCESS FALLBACK NET when Redis dies (24/08 — the review read `1a33239` and found the
    commit message FLATTENED an asymmetry: slowapi (`src/api/main.py`,
    `in_memory_fallback_enabled=True`) still keeps ONE cap when Redis dies — falling back to
    per-worker RAM, WEAKENED but not lost; the first fix of this class only returned a
    fail-open sentinel with NO cap — LOST ENTIRELY. And this is exactly the class created to
    stop *"150 people pressing send at once"* (docstring above) — exactly the scenario of the
    150-real-user test the real PO was preparing. One Redis hiccup in the middle of that
    session and the protection for THAT very scenario would vanish with nothing in its place.

    The same pattern slowapi chose for itself is applied: a `threading.Lock` + an in-RAM dict
    (`_fallback_slots`, token -> deadline), with the SAME declared `max_concurrent`/
    `ttl_seconds` — when Redis comes back, `acquire()` automatically returns to the ZSET.

    ⚠️ Measured by the review (24/08): cleanup ONLY happens at the START of each subsequent
    `_fallback_acquire()` — PASSIVE, with no clock-driven background sweeper. The accurate
    statement: the TTL guarantees garbage doesn't LIVE TOO LONG once cleaned, NOT that it is
    cleaned the INSTANT it expires. `len(_fallback_slots)` may temporarily hold expired tokens
    until the next `acquire()` — it doesn't accumulate across windows and doesn't break the
    cap (proven by the review), but it is NOT "self-expiring exactly like Redis".

    🔴 THE TRADE-OFF MUST BE STATED, not left implicit: this counter is PER-PROCESS (unlike
    the Redis ZSET — SHARED by all workers). With N workers
    (`docker-entrypoint.sh` — `UVICORN_WORKERS=4`) ⟹ while Redis is down the system's ACTUAL
    ceiling is **~N × max_concurrent**, no longer the **shared max_concurrent** it is while
    Redis is alive — exactly the trade-off "WHY REDIS, NOT AN IN-PROCESS VARIABLE" above
    warned about, now ACTIVELY accepted FOR A SHORT WINDOW (while supporting infrastructure is
    down) rather than accepted PERMANENTLY. This is CONTROLLED WEAKENING (N× cap), not TOTAL
    LOSS (0 cap) — exactly the nature of the trade-off slowapi chose, not a new pattern.
    """

    def __init__(self, *, max_concurrent: int, ttl_seconds: float, name: str = "agent_turn"):
        self._max = max_concurrent
        self._ttl = ttl_seconds
        self._key = f"concurrency:{name}"
        self._fallback_lock = threading.Lock()
        self._fallback_slots: dict[str, float] = {}  # token (with fb: prefix) -> deadline

    def _fallback_acquire(self) -> str | None:
        now = time.time()
        with self._fallback_lock:
            for tok in [t for t, deadline in self._fallback_slots.items() if deadline <= now]:
                del self._fallback_slots[tok]  # PASSIVE cleanup — only runs when the next acquire() gets here
            if len(self._fallback_slots) >= self._max:
                return None
            token = _FALLBACK_PREFIX + secrets.token_hex(8)
            self._fallback_slots[token] = now + self._ttl
            return token

    def _fallback_release(self, token: str) -> None:
        with self._fallback_lock:
            self._fallback_slots.pop(token, None)

    def acquire(self) -> str | None:
        """Returns a token holding a slot if there is room, None if full. NEVER waits, NEVER blocks.

        Deliberately no queueing: holding requests waiting inside a single worker is exactly
        what causes cascading congestion. Answering "busy, try again" immediately is better
        for both users and the system.

        Redis error -> fail-open WITH A CAP: falls back to the in-process net (see the
        comment block above the class), NEVER raises, NEVER loses the limit entirely.
        """
        try:
            client = get_default_client()
            now = time.time()
            client.zremrangebyscore(self._key, 0, now)  # clean up expired slots
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
        """Always call in `finally` — forgetting to release a slot makes the system strangle itself.

        Fallback tokens (prefix `fb:`) correspond to no Redis key — they are returned to the
        in-process net instead of `zrem`-ing a Redis token that was never written (which would
        only add another Redis error just like at acquire time). A Redis error HERE (unlike at
        acquire, with a real Redis token) -> log, NEVER raise: we're in `finally`, and raising
        here would SWALLOW the original exception currently propagating.
        """
        if not token:
            return
        if token.startswith(_FALLBACK_PREFIX):
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
        """Redis error -> count the slots held in the in-process fallback net (correct ONLY
        for THIS WORKER, not the whole system — see the per-process trade-off in the comment
        block above the class), no longer a blind `-1` — when a real number exists, use it,
        even if its scope is narrower than when Redis is alive."""
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
