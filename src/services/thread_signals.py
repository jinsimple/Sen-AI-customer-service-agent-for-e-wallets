"""Per-CONVERSATION signal counting — a shared primitive, designed ONCE.

Three places need exactly the same thing (round-2 plan, 15de5eb):
  · 5a ES-01  — frustration escalating over ≥N CONSECUTIVE turns
  · 5b output filter — how many times a reply matched groups O1–O4 within one conversation
  · 5c guardrail — signals accumulated across the conversation (multi-turn Crescendo probing)

Several matches within ONE conversation is a signal; a single match is usually noise — so
all three need counting per conversation, not per turn.

FOUR CHOICES, each learned after paying for it somewhere
-------------------------------------------------------
1. REDIS, NOT an in-process dict. The app runs 4 uvicorn workers and a conversation is NOT
   guaranteed to land on the same worker — exactly how WS tickets used to fail ~3/4 of the
   time (QA-01). An in-RAM counter would miscount by the same mechanism, except it reports
   no error: it just UNDER-counts, and ES-01 quietly never fires.

2. A TTL, reset on every write. F-14 paid for this lesson: an unbounded counter both grows
   forever and keeps wrong state forever. 2 hours ~ the life of a conversation; after expiry
   the next conversation starts at 0, which is the intended meaning.

3. THE COUNTING UNIT IS `thread_id`, NOT `user_id`. `thread_id` = `user_id:iat`
   (ADR-007), so logging in to a new session is a new conversation. Counting by `user_id`
   would let a customer who was upset yesterday carry that counter into today's chat —
   ES-01 fires over something already resolved, and the customer can't tell why.

4. FAIL-OPEN. Redis error -> treated as NO signal, the conversation proceeds normally. The
   exact opposite of WS tickets (fail-closed), and this is the easiest place to get it wrong:
   a WS ticket is an ENTRY GATE, so when in doubt, block; signal counting only SUGGESTS and
   WARNS, so when in doubt, let it through. A convenience feature must never break the main
   path because its secondary infrastructure died.
"""
from __future__ import annotations

import logging

from src.redis_client import get_default_client

_logger = logging.getLogger("fin05.thread_signals")

_SIGNAL_KEY_PREFIX = "fin05:thread_signal:"
# 2 hours — wider than a real conversation, narrower than a work shift. Reset on every write,
# so an ongoing conversation never expires midway.
SIGNAL_TTL_SECONDS = 2 * 3600


def _key(signal_name: str, thread_id: str) -> str:
    return f"{_SIGNAL_KEY_PREFIX}{signal_name}:{thread_id}"


def bump(signal_name: str, thread_id: str) -> int:
    """Increment the counter, return the value after incrementing. Redis error -> return 0 (fail-open).

    Return 0 rather than raise: callers compare this value to a threshold, and 0 is always
    below every threshold ⟹ "no signal". Raising would let a Redis incident break the
    customer's chat turn because of a secondary feature.
    """
    try:
        client = get_default_client()
        key_name = _key(signal_name, thread_id)
        val = int(client.incr(key_name))
        # expire is RESET on every increment: while the conversation is active the counter lives;
        # after 2 hours of silence it cleans itself up.
        client.expire(key_name, SIGNAL_TTL_SECONDS)
        return val
    except Exception as e:  # noqa: BLE001
        _logger.warning(
            "thread_signal_tang_that_bai",
            extra={"ten_tin_hieu": signal_name, "thread_id": thread_id, "loi": repr(e)},
        )
        return 0


def doc(signal_name: str, thread_id: str) -> int:
    """Read the counter WITHOUT incrementing. Redis error -> 0 (fail-open)."""
    try:
        raw = get_default_client().get(_key(signal_name, thread_id))
        return int(raw) if raw else 0
    except Exception as e:  # noqa: BLE001
        _logger.warning(
            "thread_signal_doc_that_bai",
            extra={"ten_tin_hieu": signal_name, "thread_id": thread_id, "loi": repr(e)},
        )
        return 0


def read_or_unknown(signal_name: str, thread_id: str) -> int | None:
    """Read the counter — SAME as `doc()` when Redis is alive, DIFFERENT when Redis errors:
    returns `None` (UNREADABLE) instead of lumping it together with `0` (no signal yet).

    🔴 Caught in review 24/08 (1B, slot-collection gate): `doc()` returns `0` for BOTH "not
    asked yet" AND "Redis is down" — for ES-01/O1-O4/guardrail (accumulating thresholds)
    that direction is CORRECT (0 is always below threshold, "no signal" is the safe
    direction). But 1B uses `doc()==0` to decide "may the gate fire this time" — lumping
    "not asked" with "unknown" means a dead Redis ⟹ the gate treats EVERY turn as the first
    ⟹ fires REPEATEDLY instead of at most once per conversation. The very opening sentence
    of this module was violated by 1B: "Safe failure = when in doubt, go FULL" — an unknown
    state must take `day_du` (full), not "not asked yet".

    `doc()` is NOT changed — the three old callers (ES-01/O1-O4/guardrail) still get the
    same old `int` contract, nobody has to follow suit. This function ONLY serves callers
    that need to distinguish those two states to pick the safe direction for THEIR own
    feature — 1B is the first such caller, not the last."""
    try:
        raw = get_default_client().get(_key(signal_name, thread_id))
        return int(raw) if raw else 0
    except Exception as e:  # noqa: BLE001
        _logger.warning(
            "thread_signal_doc_khong_ro",
            extra={"ten_tin_hieu": signal_name, "thread_id": thread_id, "loi": repr(e)},
        )
        return None


def store_value(signal_name: str, thread_id: str, val: str) -> None:
    """Store ONE STRING (not a counter) — used when the caller needs to remember WHAT
    (e.g. the trans_id awaiting processing), not just WHETHER/HOW MANY TIMES as with
    `bump`/`doc`. Same key + TTL scheme, different Redis command (`SET` instead of `INCR`).

    Redis error: SWALLOWED, never raised — same "a secondary feature must not break the chat
    turn" principle as the whole module. The caller reads it back with `read_value` and
    handles "what if it couldn't be stored" itself (see gate ⑨ item 4, `graph.py`)."""
    try:
        client = get_default_client()
        key_name = _key(signal_name, thread_id)
        client.set(key_name, val, ex=SIGNAL_TTL_SECONDS)
    except Exception as e:  # noqa: BLE001
        _logger.warning(
            "thread_signal_luu_gia_tri_that_bai",
            extra={"ten_tin_hieu": signal_name, "thread_id": thread_id, "loi": repr(e)},
        )


def read_value(signal_name: str, thread_id: str) -> str | None:
    """Read back the string stored by `store_value`. Missing/Redis error → `None` —
    the caller MUST distinguish "never stored" from "stored but read failed" itself if that
    matters to it (see `read_or_unknown` above, same reason): this function does NOT pick the
    safe direction on the caller's behalf, because it is a shared primitive for many
    different purposes, not specific to any gate."""
    try:
        # `decode_responses=True` on the shared client (redis_client.py) — already a
        # `str`, not `bytes`, no manual decoding needed.
        return get_default_client().get(_key(signal_name, thread_id))
    except Exception as e:  # noqa: BLE001
        _logger.warning(
            "thread_signal_doc_gia_tri_that_bai",
            extra={"ten_tin_hieu": signal_name, "thread_id": thread_id, "loi": repr(e)},
        )
        return None


def reset(signal_name: str, thread_id: str) -> None:
    """Reset the counter to 0.

    NOT a cleanup utility — this is what gives ES-01 its "CONSECUTIVE" semantics. Without it,
    what gets counted is "total frustrated turns in the conversation", something entirely
    different: a customer upset for 1 turn, calm, upset again, calm, upset again still hits
    the threshold of 3 — while not escalating at all. Callers MUST reset() on a turn that
    carries NO signal, otherwise the threshold N loses all meaning.
    """
    try:
        get_default_client().delete(_key(signal_name, thread_id))
    except Exception as e:  # noqa: BLE001
        _logger.warning(
            "thread_signal_dat_lai_that_bai",
            extra={"ten_tin_hieu": signal_name, "thread_id": thread_id, "loi": repr(e)},
        )
