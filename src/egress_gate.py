"""EGRESS GATE — a block + counter for EVERY call to an LLM provider.

WHY IT EXISTS (§5.F, 18/08/2026)
--------------------------------
Two INDEPENDENT sources pointed at the same hole on the same day:

    tester   a "disable consequences first" probe over 620/620 cases -> caught exactly
             ONE call leaving the machine: POST api.openai.com/v1/embeddings, from
             `tests/test_api/test_injection.py` — a file with NO gate at all
    coder    building an acceptance case, calling `search_policy` -> went straight out to
             OpenAI, stopped only by a fake key (401). With a real key that would be money
             outside budget A3.

None of the three existing bill-protection layers could stop either path:

    ① FIN05_ALLOW_PAID_CALLS   is a `skipif` LIVING INSIDE THE TEST FILE
                               -> a test file that forgets to declare it fires nothing
    ② .DANG-DONG-BANG-LLM       (LLM-freeze marker) — the real PO decided 18/08: dropped
                               (demo video done)
    ③ TRIAGE_ENABLED            only routes CHAT turns

⟹ The block must live where **EVERY call passes through**, not inside `tests/`.

🔴 WHY AT THE TRANSPORT LAYER, NOT IN `_key_for_provider()`
-----------------------------------------------------------
I (coder) proposed `_key_for_provider()` first, and it was WRONG. [MEASURED] that function is
called **exactly twice, at module level** (`config.py:283` and `:303`) — it ISSUES KEYS, it
does not gate calls. A counter placed there would **forever read 2 and look like it was
counting** — exactly the kind of lying instrument the project is busy fixing.

The mistake: both paths (chat + embedding) TOUCH that function, so I concluded both PASS
THROUGH it. *Touching it once* ≠ *passing through it every time* — **Rule G**.

The right seam, [MEASURED] not inferred (openai 3.0.0 · httpx 0.28.1): both `ChatOpenAI`
and `OpenAIEmbeddings` accept `http_client` ⟹ **one shared `httpx.Client`** is the only place
every real call actually passes through.

⭐ And it sees **the REAL requests ON THE WIRE**, including **SDK automatic retries**
(`max_retries=2`, `graph.py`). Any counter placed ABOVE the SDK records **1** for **3**
requests sent — under-counting exactly the most expensive kind of call, the same trap shape
as `so_luot_goi_model = 0` (STATE §8).

⚠️ THE EMBEDDING PATH DOES NOT GO THROUGH `graph.py`
---------------------------------------------------
`search_policy` -> `search_policy_text` -> `store.search` -> `embed_query` ->
provider. A block placed only on the chat path would let through **exactly the path with the
fewest gates** — and that is the very path both tester and coder ran into. So the acceptance
case MUST run on the embedding path, **not be inferred from the chat path**.

TWO MECHANISMS, NOT ONE
-----------------------
    ALLOW FLAG (binary)       -> BLOCKS immediately, NO number needed
    THREE-BUCKET COUNTER (#)  -> COUNTS immediately, NO threshold

Hole §5.F is a **yes/no** question (*"is any call going out to the Internet unintentionally"*),
not a **how much** question. Conversely, setting a THRESHOLD now would mean setting it from a
made-up number — A3 is *"nothing topped up yet"*, **not a numeric quota** — and a gate that
has been loosened once is never trusted again. Counting first gives us a REAL DENOMINATOR to
set a well-founded threshold later.
"""
from __future__ import annotations

import logging
import os
import sys
import threading
from datetime import UTC, datetime
from pathlib import Path

import httpx

from src.config import LLM_BASE_URL, LLM_DAILY_TOKEN_CAP
from src.build_stamp import hash_source
from src.observability.usage_ledger import record_usage
from src.redis_client import get_default_client

_logger = logging.getLogger("fin05.cong_ra_ngoai")

# A SEPARATE ledger, on the same volume as `usage.jsonl` — NOT the same file.
# `usage.jsonl` is *one line per CHAT TURN*; this ledger is *one line per HTTP REQUEST*.
# Different grain, different population — see the `record_usage` docstring.
EGRESS_LEDGER_PATH = Path(os.environ.get("EGRESS_LEDGER_FILE", "/app/logs/egress_ledger.jsonl"))

EGRESS_FLAG_ENV = "FIN05_ALLOW_EGRESS"
_OFF_VALUES = {"", "0", "false", "no", "off"}


class EgressBlockedError(RuntimeError):
    """A call to the provider blocked BEFORE it reaches the wire.

    Raise rather than return empty: a blocked call returning "no results" is
    **indistinguishable** from a real call that genuinely found nothing —
    exactly the `except InvalidToken` bug class of `crypto_types`, and exactly hard
    constraint 3 (*if it can't be looked up, SAY CLEARLY that it can't be looked up*).
    """


def is_blocked(err: BaseException | None, max_after: int = 8) -> bool:
    """Is this error (or its cause) due to the GATE?

    🔴 USE THIS FUNCTION, DON'T `isinstance` DIRECTLY — and here is why, measured rather than
    precautionary:

        [MEASURED] store.search(...) with the flag OFF
             caller sees : openai.APIConnectionError — "Connection error."
             __cause__   : src.egress_gate.EgressBlockedError
             counter     : bi_chan (blocked) +3, da_phat (sent) 0

    The provider's SDK **wraps every transport error** into `APIConnectionError`.
    So at the call site, a call **we deliberately blocked** looks **exactly like** a call
    **that hit a real network failure**. Someone debugging reads *"Connection error"* and goes
    hunting a network bug, when the truth is that one of our own gates is closed.

    That is **Rule H at a layer we can't fix**: the error branch prints a CONCLUSION
    (*"connection lost"*) instead of a SYMPTOM (*"refused by the gate"*). We can't change the
    SDK, so the job is **to keep the truth reachable** — the `__cause__` chain preserves the
    original error, and this function is the way to it.

    ⚠️ Plus a measured property, not a bug: the SDK **retries 3 times** against a closed gate
    (`max_retries=2` + the first attempt) ⟹ one blocked call produces **3** `bi_chan` entries
    and **3** log lines. It costs 0 dong, but anyone reading the counter must know that
    `bi_chan` counts **BLOCKED WIRE ATTEMPTS**, not **user calls**.
    """
    cur, n = err, 0
    while cur is not None and n < max_after:
        if isinstance(cur, EgressBlockedError):
            return True
        cur = cur.__cause__ or cur.__context__
        n += 1
    return False


def _explicitly_declared() -> bool | None:
    """`None` = NOT DECLARED (completely different from "declared as off"). Three states, not two."""
    v = os.environ.get(EGRESS_FLAG_ENV)
    if v is None:
        return None
    return v.strip().lower() not in _OFF_VALUES


# ---------------------------------------------------------------------------
# MINIMAL SPENDING CAP (phase 3, fixed by the real PO 19/08 — `876a240`)
#
# 🔴 ONLY CHAT-model (LLM) tokens, NOT embedding spend — even though both
# go through THIS same transport (`shared_http_client()` is shared by `ChatOpenAI`
# and `OpenAIEmbeddings`). Why NOT combine them: embeddings use a DIFFERENT provider
# (`EMBEDDING_BASE_URL` != `LLM_BASE_URL`, see config.py) — adding two providers' tokens into one
# cap means adding two different units and comparing them to one threshold, producing a number
# that LOOKS valid and means nothing. The variable name `LLM_DAILY_TOKEN_CAP` declares this
# limitation itself — and it is TRUE BY STRUCTURE, not just by name:
# `spend_gate()` CURRENTLY has EXACTLY ONE call site in the repo, at
# `src/agents/graph.py::_write_ledger` (the LLM path) — `src/rag/store.py` (the embedding path)
# never calls this function anywhere.
#
# 🔴 IT WILL BECOME TWO, deliberately (PO-agent fixed 19/08, after a real deepseek probe ping):
# the pool-declaration ping function (`MODEL_POOL_PING`, NOT YET WRITTEN — waiting for QA/QC to
# switch the call-site gate from COUNTING to a LIST OF NAMES first) WILL be the second call
# site — pings also spend real money; if they bypass the cap, the cap lies exactly when
# `MODEL_POOL_PING=eager` burns quota fastest (crashloop = rapid-fire pings).
# Once the ping function exists, the valid list is { `_write_ledger`, <fixed ping function
# name> } — NOT "count == 2", per the lesson "pin by NAME, not by NUMBER" already applied to
# the pool-entry gate.
#
# FAIL-CLOSED when Redis errors — the OPPOSITE of `llm_pool.py` (fail-open) and
# `thread_signals.py` (fail-open), DELIBERATELY: this is a MONEY-PROTECTION mechanism, not an
# error-avoidance convenience. Can't read the spending state ⟹
# DON'T KNOW whether the cap is exceeded ⟹ treat it as exceeded, block. Misreading in the
# other direction (treat as not exceeded) turns an infrastructure incident into UNLIMITED
# spending — exactly the failure a spending cap exists to prevent.
#
# RACE WINDOW — declared, not fixed: `egress_allowed()` reads the total BEFORE the call,
# `spend_gate()` adds to it AFTER the turn finishes. Several concurrent turns may all read
# "not exceeded" and all call, overshooting the cap somewhat.
# Acceptable for a DAILY cap (small error relative to a day's volume) — recorded so a later
# reader doesn't mistake it for a bug when rediscovering it.
_SPEND_KEY_PREFIX = "fin05:chi_tieu_llm_token:"
# TTL longer than 1 day so nothing is deleted by mistake during slightly skewed-timezone
# reads/writes — the key already carries the DATE in its name so it is never reused; the TTL
# only cleans up garbage.
_SPEND_TTL_SECONDS = 3 * 24 * 3600

# Counts TURNS (not tokens — tokens are exactly what couldn't be read), alongside the
# spending counter. Lead measured 19/08: `graph.py` has written the flag `token_khong_doc_duoc`
# (token unreadable) into usage.jsonl since the None-vs-0 fix, but NOTHING READS it —
# state that is recorded but never watched has the same effect as not recording it.
# This counter turns it into ONE READABLE NUMBER in the same place as the spending cap,
# rather than a flag waiting for someone to happen to open the log.
_UNREADABLE_SPEND_KEY_PREFIX = "fin05:chi_tieu_llm_khong_doc_duoc:"


def _spend_key_today() -> str:
    return f"{_SPEND_KEY_PREFIX}{datetime.now(UTC).strftime('%Y%m%d')}"


def _unreadable_key_today() -> str:
    return f"{_UNREADABLE_SPEND_KEY_PREFIX}{datetime.now(UTC).strftime('%Y%m%d')}"


def record_unreadable_spend() -> None:
    """+1 to TODAY's counter of TURNS where "the model was called but tokens couldn't be read".

    NOT added to the spending cap (there is no number to add) — this is an OBSERVATION
    instrument, not a second blocking mechanism. Read `unreadable_count_today()` to see how
    far the cap's blind spot has grown during the day.

    Redis error -> log a warning, NEVER raise — same philosophy as `spend_gate()`.
    """
    try:
        client = get_default_client()
        key_name = _unreadable_key_today()
        client.incrby(key_name, 1)
        client.expire(key_name, _SPEND_TTL_SECONDS)
    except Exception as e:  # noqa: BLE001
        _logger.warning("ghi_nhan_khong_doc_duoc_that_bai", extra={"loi": repr(e)})


def unreadable_count_today() -> int | None:
    """How many turns TODAY called the model without being able to read the tokens.

    `None` = unreadable (Redis error) — DIFFERENT from `0` = readable and genuinely no such
    turns yet, the same "None is not 0" convention used throughout this file.
    """
    try:
        raw = get_default_client().get(_unreadable_key_today())
    except Exception as e:  # noqa: BLE001
        _logger.warning("doc_khong_doc_duoc_that_bai", extra={"loi": repr(e)})
        return None
    return int(raw) if raw else 0


def spend_gate(tokens: int | None) -> None:
    """Add `tokens` to TODAY's (UTC) total LLM spend. Called for EVERY LLM turn
    (including failed ones), NOT for embedding calls (see the comment block
    above) — designed to be called unconditionally from `graph._write_ledger`, a function that
    ALREADY runs on all 5 return paths (light · 3 fallbacks · heavy).

    🔴 `tokens=None` (not `0`) means UNREADABLE — the same "None is not 0" convention used
    throughout `graph.py`/`usage_ledger.py`. Skipped ON PURPOSE, not a bug: a failed turn
    with unknown cost (timeout/network drop) cannot add a non-existent number to the cap
    without fabricating one — this is a DECLARED LIMITATION of the "minimal cap" version
    (PO `876a240` deliberately did not build a full cost guard), not an overlooked gap.

    Redis error -> log a warning, NEVER raise: a turn that has ALREADY been billed must not
    break because ledger-writing failed (exactly the contract of `record_usage`, called just
    below in this same file) — losing one accumulation line does not lose money already spent.
    """
    if tokens is None:
        _logger.info("cong_chi_tieu_bo_qua_khong_biet")
        return
    if tokens <= 0:
        return
    try:
        client = get_default_client()
        key_name = _spend_key_today()
        client.incrby(key_name, tokens)
        client.expire(key_name, _SPEND_TTL_SECONDS)
    except Exception as e:  # noqa: BLE001
        _logger.warning("cong_chi_tieu_that_bai", extra={"tokens": tokens, "loi": repr(e)})


def _under_daily_spend_cap() -> bool:
    """Is today's total LLM spend still BELOW the cap?

    `LLM_DAILY_TOKEN_CAP is None` (variable empty/missing) ⟹ always `True` — NO
    limit, exactly the behaviour before this cap existed.

    FAIL-CLOSED: Redis error ⟹ `False` (treated as ALREADY exceeded) — see the reasoning in
    the comment block at the top of the "SPENDING CAP" section above. This is the ONLY
    function in this file that reverses the fail-open philosophy of the other supporting
    mechanisms — on purpose.
    """
    if LLM_DAILY_TOKEN_CAP is None:
        return True
    try:
        raw = get_default_client().get(_spend_key_today())
        spent = int(raw) if raw else 0
    except Exception as e:  # noqa: BLE001
        _logger.warning("doc_chi_tieu_that_bai_coi_nhu_vuot_tran", extra={"loi": repr(e)})
        return False
    return spent < LLM_DAILY_TOKEN_CAP


def egress_allowed() -> tuple[bool, str]:
    """May we call out to the provider, AND why — return both.

    Returning the REASON is mandatory, not a convenience: a flag returning only `True/False`
    tells an investigator *"blocked"* without saying *"blocked by declaration or by
    inference"* — and a wrong inference means fixing the inference, while a wrong declaration
    means fixing `.env`. Two different jobs.

    🔴 THE DEFAULT IS **DENY** (flipped 18/08, phase 2 ②).

    The first version defaulted to ALLOW, and the reason at the time was sound: three running
    containers had no `FIN05_ALLOW_EGRESS` in `Config.Env`, and environment variables are
    **pinned at container CREATION** (STATE §9) ⟹ default-deny would **kill the product** as
    soon as the image was rebuilt.

    That condition has since been removed: `docker-compose.yml` declares
    `FIN05_ALLOW_EGRESS: ${…:-1}` for the `backend` service, and [MEASURED]
    `docker compose config` interpolates it to `"1"` on **all three** stacks.

    🔴 ONE-WAY ORDER (ADR-035) — whoever comes later, read this before flipping back:
        add the compose entry before flipping the default  ->  HARMLESS
        flip the default before adding the compose entry   ->  PRODUCT DIES on the next build
    Anyone reverting one half **must revert the other half first**, not after.

    WHY FLIP — it closes the LAST hole, and it was a hole I walked into myself:

        phase 1   pytest ✅ · chat turn ✅ · scratch script ❌
        phase 2   all three ✅

    A scratch script running `python x.py` is **indistinguishable from the product** — so the
    only thing that can tell them apart is **the product DECLARING itself to be the product**
    (compose sets the flag), and anything that doesn't declare itself is by default **not
    allowed to spend money**. This is fail-closed in the true sense: same habit as
    `build_stamp.py` (empty `.source_hash` ⟹ REFUSE to start).

    ⚠️ The `suy_tu_pytest` (inferred from pytest) branch is KEPT even though the default is
    now deny. It is no longer needed for BLOCKING, but it still carries something else: the
    **REASON**. A call blocked under pytest and a call blocked for lack of a declaration are
    two different stories during an investigation, and `egress_ledger.jsonl` records that
    `ly_do` (reason). Merging them loses a state — three states, not two.
    """
    declared = _explicitly_declared()
    if declared is not None:
        # The spending cap is an INDEPENDENT block that stands BEHIND the allow declaration — a
        # `=1` declaration opens the ALLOW path in principle, but does NOT buy the right to exceed
        # the
        # self-imposed cap. Redis is only queried when this branch CAN return True —
        # the False branch (declared=0) doesn't need the cap; the result is already a block.
        if declared and not _under_daily_spend_cap():
            return False, "tran_chi_tieu"
        return declared, "khai_tuong_minh"
    # `pytest` in `sys.modules` = running under the test suite. This is an INFERENCE,
    # not a declaration — so it gets a different label, and it ranks BELOW an explicit
    # declaration (anyone needing to run tests that spend real money declares `=1`).
    if "pytest" in sys.modules:
        return False, "suy_tu_pytest"
    # Nobody declared anything ⟹ DENY. The product declares via compose; anything that doesn't
    # declare may not spend money.
    return False, "mac_dinh_tu_choi"


# ---------------------------------------------------------------------------
# THREE-BUCKET COUNTER — `calls_issued`
#
# 🔴 THESE THREE BUCKETS ARE NOT `hit · miss · error`. Security asked for those three buckets
# for the CACHE layer; the transport layer **cannot count `hit`** because, by definition, a
# cache hit NEVER reaches the transport. Counting it here would give a `hit` column that is
# **always 0** — yet another lying instrument. When a cache exists, `hit` is counted at the
# cache layer, and that is an **INDEPENDENT SOURCE** from this counter (Rule D: two real
# sources, not one variable written twice).
#
# The RIGHT three buckets for this layer, by what the transport can actually distinguish:
_counters: dict[str, int] = {"da_phat": 0, "bi_chan": 0, "hong": 0}
_counter_key = threading.Lock()


def calls_issued() -> dict[str, int]:
    """Counter snapshot. THREE SEPARATE DENOMINATORS — readers **must not** add them up.

        da_phat   (sent)      reached the wire AND got a response (any status)  -> MAY be billed
        bi_chan   (blocked)   flag denied, NEVER reached the wire               -> certainly 0 dong
        hong      (broken)    reached the wire then failed (timeout · drop ·
                              we abandoned)                                     -> 🔴 UNREADABLE

    🔴 `hong` is the bucket most easily squashed to 0 and the most important one.
    [MEASURED STATE §6.⓷] at `14:26:44` we abandoned a request → at `14:26:45.335` DashScope
    returned **a complete HTTP 200, 1.2s LATER**: providers bill for what they GENERATE, not
    for what we READ. ⟹ a call in the `hong` bucket **may have cost money and we have no way
    of knowing**. It is NOT 0, it is *"unreadable"*.

    ⟹ **NO `sum(... or 0)`.** Adding the three buckets turns *"unknown"* into a number that
    looks certain — exactly the §8 bug the project already paid for.
    """
    with _counter_key:
        return dict(_counters)


def _record_outcome(outcome_kind: str, *, host: str | None = None, route: str | None = None,
            reason_text: str | None = None) -> None:
    """Increment the in-process counter AND write a line to the LEDGER ON THE VOLUME.

    🔴 WHY BOTH ARE NEEDED, and why the counter alone is NOT ENOUGH — I (coder) landed the
    counter on the morning of 18/08 and then rejected the way it had been described:

        [MEASURED] docker-entrypoint.sh:16   UVICORN_WORKERS defaults to 4
             ⟹ FOUR processes ⟹ FOUR independent counters, none aware of the others
             ⟹ all four reset to 0 on every recreate
             ⟹ no endpoint, no file ⟹ NOT readable from outside the process

    The PO-agent was about to record it in STATE as *"the project's first baseline"*. Wrong —
    and it is **exactly the kind of valid-looking number** the project has paid for (§8).

    A ledger on a named volume closes all three gaps: **it aggregates the 4 workers** (all
    writing one file), **survives recreate**, **is readable from outside**. And it does
    something an endpoint CANNOT — an endpoint only returns the number of **one** random
    worker while **looking like** it returns the whole.

    The in-RAM counter is kept: it is what **control cases** can read directly within the
    same process, without opening a file.
    """
    with _counter_key:
        _counters[outcome_kind] += 1
    # `record_usage` has the contract "NEVER break a turn because of a ledger-write error" —
    # so call it directly, with no extra try: double-wrapping would hide its own warn-once.
    record_usage(
        {
            "ts": datetime.now(UTC).isoformat(),
            "ro": outcome_kind,
            # host + PATH only. 🔴 NO query string: some providers carry parameters there, and
            # building
            # a leak into the log RIGHT INSIDE the mechanism created to stop leaks would be failing
            # in the
            # most ironic way possible.
            "host": host,
            "duong": route,
            "ly_do": reason_text,
            "bam_ma_nguon": hash_source(),
            # PID to separate the FOUR workers again. Without it the ledger can be aggregated but
            # never
            # split apart again — and "aggregated but not separable" is how a mixed population
            # forms.
            "pid": os.getpid(),
        },
        route=EGRESS_LEDGER_PATH,
    )


class _GatedTransport(httpx.BaseTransport):
    """Wraps the real transport: ask the flag BEFORE reaching the wire, then record the bucket by outcome.

    The order ask-then-send is MANDATORY. Send-then-ask means the money is already spent, and
    this whole mechanism would be reduced to a ledger.
    """

    def __init__(self, real: httpx.BaseTransport) -> None:
        self._real = real

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        # [MEASURED 26/08] An empty `LLM_BASE_URL` blocks nothing in `_key_for_provider`
        # (it only asks "did the DESTINATION change"; base_url=None ⟹ unchanged ⟹ no raise)
        # — yet the SDK still picks its default destination (the real api.openai.com) and
        # `LLM_MODEL` falls back to `OPENAI_MODEL`. Three fallbacks in the same direction ⟹ the call
        # SUCCEEDS against a different provider, without a single error line. Blocked here
        # because this is where the REAL DESTINATION is known (`request.url.path`), not inferred
        # from
        # environment flags — CI and production read the flags identically; only the destination at
        # send time differs. `/embeddings` is excluded: falling back to OpenAI there is
        # INTENTIONAL (EMBEDDING_BASE_URL is empty by default); blocking the whole group would break
        # RAG.
        if not LLM_BASE_URL and not request.url.path.endswith("/embeddings"):
            _record_outcome("bi_chan", host=request.url.host, route=request.url.path,
                    reason_text="llm_base_url_trong")
            _logger.error(
                "goi_ra_ngoai_dich_roi_mac_dinh",
                extra={"host": request.url.host, "duong": request.url.path},
            )
            raise EgressBlockedError(
                f"Lời gọi chat tới {request.url.host}{request.url.path} bị "
                f"CHẶN: LLM_BASE_URL trống. Không đặt LLM_BASE_URL, SDK rơi "
                f"về đích mặc định (OpenAI thật) thay vì nhà cung cấp đã "
                f"ghim — đúng loại rò tiền + đo nhầm model mà cơ chế này "
                f"sinh ra để chặn. Đặt LLM_BASE_URL tường minh trước khi "
                f"gọi chat thật."
            )
        permitted, reason_text = egress_allowed()
        if not permitted:
            _record_outcome("bi_chan", host=request.url.host, route=request.url.path, reason_text=reason_text)
            # DO NOT log the full URL: some providers carry parameters in the query string, and we
            # don't want to build yet another leak into the log right inside the mechanism created
            # to
            # stop leaks.
            _logger.error(
                "goi_ra_ngoai_bi_chan",
                extra={"host": request.url.host, "duong": request.url.path, "ly_do": reason_text},
            )
            raise EgressBlockedError(
                f"Lời gọi tới {request.url.host}{request.url.path} bị CHẶN "
                f"({reason_text}). Đây là chốt chặn chi phí ở tầng transport: mọi lời "
                f"gọi tới nhà cung cấp LLM/embedding đều đi qua đây. "
                f"Cần gọi thật thì đặt {EGRESS_FLAG_ENV}=1 — và biết rằng nó TỐN TIỀN."
            )
        try:
            response = self._real.handle_request(request)
        except Exception:
            # Reached the wire and then failed ⟹ we DON'T KNOW whether it cost money. Goes into the
            # `hong` bucket, NOT `da_phat` (overstating) and NOT skipped (understating).
            _record_outcome("hong", host=request.url.host, route=request.url.path)
            raise
        _record_outcome("da_phat", host=request.url.host, route=request.url.path)
        return response

    def close(self) -> None:
        self._real.close()


_client: httpx.Client | None = None
_client_lock = threading.Lock()


def shared_http_client() -> httpx.Client:
    """`httpx.Client` SHARED by both `ChatOpenAI` and `OpenAIEmbeddings`.

    ONE client for both is the condition for the counter and the flag to be meaningful: two
    separate clients = two separate counters = nobody can answer *"how many calls went out in
    total"*, which is exactly the question §5.F needs answered.

    `httpx.Client` is thread-safe; built once for the whole process.
    """
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                _client = httpx.Client(transport=_GatedTransport(httpx.HTTPTransport()))
    return _client
