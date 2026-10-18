"""MODEL POOL for the switch/rotate feature (phase 3, fixed by the real PO on 19/08 — `876a240`).

This deliberately reverses an earlier decision, openly (`a3fb125`: pin the model PER DAY,
because "changing the model = changing the OBJECT" — every A/B measurement depends on model
identity). Rotation here is a DEMO/TEST mode: `usage.jsonl` still records `model` PER TURN
(unchanged) — that is what saves us when reading the numbers later; every SERIOUS eval
measurement must still PIN one model and must not run through this module.

The "model exhausted" STATE lives in REDIS, NOT in a process variable — the same lesson
(`docker-entrypoint.sh:16 UVICORN_WORKERS=4`) that forced `egress_gate.py` to do the same:
4 independent workers, so an in-RAM variable is right for only 1/4 of turns.

FAIL-OPEN when Redis errors (treated as "not exhausted") — same philosophy as
`thread_signals.py`: this is a SECONDARY feature (helps avoid a model known to be failing),
not a gate. Misreading towards "retry an exhausted model" costs at most ONE failed call and
the rotation self-corrects on the next try; misreading the other way (treating every model
as exhausted) would give REAL CUSTOMERS "pool fully exhausted" while every model is fine —
far worse. This is deliberately the OPPOSITE of the spending cap in `egress_gate.py`
(fail-CLOSED, because that is a MONEY-PROTECTION mechanism, not an error-avoidance
convenience) — read carefully before "making them consistent": two places answering
different questions should fail in different directions, on purpose.
"""
from __future__ import annotations

import logging

from src.config import LLM_MODEL_POOL
from src.redis_client import get_default_client

_logger = logging.getLogger("fin05.llm_pool")

# NO "fin05:" prefix — unlike `thread_signals.py`, ON PURPOSE: this name was DECLARED to
# QA/QC before they wrote the gate (`test_llm_pool_gd3.py`, written from the spec without
# reading src/). Changing the prefix here without notice is exactly the "declare one thing,
# code another" class of bug — fix the CODE to match what was declared; don't force the test
# to be rewritten.
_KEY_PREFIX = "model_can:"
# The TTL is a BACKOFF — "how long before RETRYING this model", NOT a guess at the
# provider's real quota reset cycle (we don't know it, and don't need to in order to choose
# this number correctly). Erring short -> one wasted retry then exhausted again (cheap).
# Erring long -> slower to notice the model recovered, by at most the TTL itself (cheap).
EXHAUSTED_MODEL_TTL_SECONDS = 15 * 60


def _key(model: str) -> str:
    return f"{_KEY_PREFIX}{model}"


def exhausted_model(model: str) -> bool:
    """Is this model currently marked exhausted? Redis error -> False (fail-open)."""
    try:
        return get_default_client().exists(_key(model)) > 0
    except Exception as e:  # noqa: BLE001
        _logger.warning("model_dang_can_that_bai", extra={"model": model, "loi": repr(e)})
        return False


def mark_exhausted(model: str) -> None:
    """Mark `model` exhausted for `EXHAUSTED_MODEL_TTL_SECONDS` seconds. Emits the log event
    `model_rotated` — NEVER logs key/token, only the model name (self-declared as
    non-sensitive, see `config.py:298`, same convention as `LLM_MODEL`)."""
    try:
        client = get_default_client()
        client.set(_key(model), "1", ex=EXHAUSTED_MODEL_TTL_SECONDS)
    except Exception as e:  # noqa: BLE001
        _logger.warning("danh_dau_can_that_bai", extra={"model": model, "loi": repr(e)})
    _logger.warning("model_rotated", extra={"model_can": model, "ttl_giay": EXHAUSTED_MODEL_TTL_SECONDS})


def turn_start_model(tried: set[str] | None = None) -> str | None:
    """Next model for the START OF A TURN — the first model in the pool (in the priority order
    declared in `LLM_MODEL_POOL`) that is NOT marked exhausted and NOT in
    `tried` (models this rotation round already tried and failed).

    Returns `None` when the WHOLE pool is exhausted/tried — the caller must handle this case
    with a polite message, NEVER loop forever (PO constraint `876a240`).

    NO `thread_id` parameter: choosing a model is a GLOBAL pool-wide decision, not
    per-customer — "model X is exhausted" is a shared fact for every conversation.
    """
    attempt = tried or set()
    for model in LLM_MODEL_POOL:
        if model in attempt:
            continue
        if not exhausted_model(model):
            return model
    return None
