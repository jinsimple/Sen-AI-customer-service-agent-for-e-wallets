"""FIN-05 — shared configuration for the DB, seeding and the API.

Read before editing: every path here is relative to the repo root,
so `make db` runs on any machine without manual tweaks.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

DATA_RAW_DIR = ROOT_DIR / "data" / "raw"
DATA_SCHEMA_DIR = ROOT_DIR / "data" / "schema"
DATA_GENERATED_DIR = ROOT_DIR / "data" / "generated"
EVAL_DIR = ROOT_DIR / "eval"

# ---------------------------------------------------------------------------
# DATABASE_URL — MANDATORY, with NO default value (ADR-013).
#
# BEFORE 2026-08-13 this line was:
#     DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH}")
#
# That silent fallback caused a real incident that took hours to investigate: the Docker
# stack ran Postgres, while everything running on the host (uvicorn dev, the seed script,
# load tests, verify_security.sh) SILENTLY fell back to SQLite. Two browser windows looked
# identical but wrote/read TWO DIFFERENT DATABASES — a customer created a ticket on one side,
# CSKH on the other never saw it, no matter how many times they pressed F5.
#
# The environment label (ADR-009) helps DETECT drift once it has happened. Removing the fallback
# here stops it at the ROOT: a missing variable fails immediately at startup with a clear
# message, instead of quietly spawning a second database nobody knows about.
#
# Set explicitly for EACH environment:
#   .env (dev/docker) : postgresql+psycopg2://...@127.0.0.1:5432/fin05
#   CI                : sqlite:///:memory: or ephemeral Postgres
#   pytest            : tests/conftest.py creates its own temporary SQLite engine,
#                       does NOT use this variable (see get_engine below)
# ---------------------------------------------------------------------------
DB_PATH = ROOT_DIR / "data" / "app.db"  # only still used by old hand-pointed seed scripts
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "Thiếu DATABASE_URL trong .env — KHÔNG còn fallback SQLite tự động "
        "(xem ADR-013: fallback im lặng từng làm hệ thống tách đôi database).\n"
        "  Dev/Docker : DATABASE_URL=postgresql+psycopg2://<user>:<pass>@127.0.0.1:5432/<db>\n"
        "  Test/CI    : DATABASE_URL=sqlite:///:memory:"
    )

# ---------------------------------------------------------------------------
# ENVIRONMENT IDENTITY (2026-08-13) — born from a real incident, not a decorative feature.
#
# The incident: the Docker stack (Caddy :80 -> Postgres) and the local dev stack
# (next dev :3000 -> uvicorn :8010 -> SQLite) ran SIDE BY SIDE. The PO opened the customer
# window at `localhost` and the CSKH window at `localhost:3000` — two IDENTICAL-looking UIs
# talking to TWO DIFFERENT DATABASES. The customer created tickets in
# Postgres, CSKH read from SQLite and so always saw 0, no matter how many F5s. Hours lost
# investigating, because every layer of code was correct.
#
# General lesson: an INVISIBLE environment is a design flaw. The system must DECLARE
# who it is — visible at a glance, not inferred from port numbers.
#
# Derived ONLY from the scheme + database name. NEVER include user/password/host here: this
# value is returned via /health (a public endpoint).
# ---------------------------------------------------------------------------
# Fail-CLOSED, not fail-open (caught by Security 20/08): a missing variable used to fall
# back to "development" — the LOOSER branch, enabling `/docs`/`/redoc`/`/openapi.json`
# (34 routes with schemas) on EVERY image that forgot to set APP_ENV, including real deployments
# following `.env.example`. The default was flipped to "production" (the STRICTER branch) so
# forgetting pushes towards safety — the cost falls on the right party: dev machines must set
# `APP_ENV=development` to get `/docs`, rather than a deploy machine forgetting and throwing the
# API surface wide open. NOT made fail-fast (like JWT_SECRET_KEY) — the cost of a mandatory
# variable would spread to every test/CI/local run, while a safe default already delivers what
# is needed without forcing it to be set everywhere.
APP_ENV = os.environ.get("APP_ENV", "production")

# 🔴 CORRECTION 05/09 — the comment ABOVE is still right for EVERYTHING else that reads
# APP_ENV (e.g. the OTP_DEMO_MODE guard below), but its sentence "enable /docs when APP_ENV
# != production" is NO LONGER TRUE since this `ENABLE_API_DOCS` flag — see the reasoning just
# below. The old paragraph is kept as is (Rule P — seal in place, don't delete the reasoning
# history); only the point that drifted is corrected.
#
# The real production (VPS `home`, viewed by the judges) needs `APP_ENV != "production"` to
# enable `OTP_DEMO_MODE` (showing the demo OTP code to judges) — but the OLD flag
# (`docs_url=None if APP_ENV=="production" else "/docs"`, main.py) treated every
# `APP_ENV != production` as a "dev environment", so enabling the OTP demo ACCIDENTALLY also
# opened `/docs`/`/redoc`/`/openapi.json` (31 routes + parameter/auth schemas)
# on real production — two UNRELATED decisions (showing the demo OTP to judges · opening API
# documentation) tied to ONE variable.
#
# Split out SEPARATELY, default FALSE (fail-safe OFF) — same pattern as OTP_DEMO_MODE:
# forgetting to set it keeps API docs off; no more implicit inference from APP_ENV. Enable it
# explicitly with `ENABLE_API_DOCS=true` when REALLY needed (local dev).
ENABLE_API_DOCS = os.environ.get("ENABLE_API_DOCS", "").strip().lower() in ("1", "true", "yes")

# Build fingerprints, set by Dockerfile ARGs at build time. "khong-ro" (unknown) = couldn't be
# passed — it gives itself away instead of silently pretending to be valid.
# Chat-turn triage (T1). OFF BY DEFAULT — enabling it changes product behaviour, and there are
# no numbers yet for `f` (the real share of simple turns) to know what it is worth.
TRIAGE_ENABLED = os.environ.get("TRIAGE_ENABLED", "").strip().lower() in ("1", "true", "yes")

# T0 · the slot-collection gate AFTER OTP verification (src/agents/graph.py). A SEPARATE flag,
# NOT shared with `TRIAGE_ENABLED` — the two gates decide different things (T0: "does this
# post-OTP resend turn carry enough to narrow the lookup"; T1: "which toolkit does this turn
# need"), so they must be switchable independently.
#
# 🔴 Why this flag exists (Đ4, raised by the review 24/08 · "OTP before token" ticket ⑦):
# BEFORE the fix, T0 ran independently of `TRIAGE_ENABLED` and had NO switch of its own. An
# on-call engineer switching off `TRIAGE_ENABLED` to fight a fire would believe every
# deterministic pre-LLM path was off — while T0 WAS STILL RUNNING, with no signal saying so. A
# switch the user believes turns everything off while it only turns off half is more dangerous
# than no switch at all.
#
# ON BY DEFAULT — unlike `TRIAGE_ENABLED` (OFF by default), DELIBERATELY: T0 currently runs on
# every stack, so defaulting it OFF would be a covert product-behaviour change smuggled in with an
# operational fix. This flag only ADDS an off switch; it doesn't change the default.
T0_GATE_ENABLED = os.environ.get("T0_GATE_ENABLED", "1").strip().lower() in ("1", "true", "yes")

# ④ · the deterministic OTP gate for personal complaints (GROUP B). A SEPARATE switch — the
# Đ4 lesson: every deterministic gate must be switchable independently; the on-call engineer must
# not believe everything is off when only half is.
#
# 🔴 NOT A SECURITY LAYER. The security layer of hard constraint 4 lives at the TOOL LAYER
# (`customer_tools.py`, `_OTP_REQUIRED_ERROR`/`_OTP_EXPIRED_ERROR`) and in the route's
# `require_otp_verified`. This gate only avoids SPENDING TOKENS on a turn that the tool will
# certainly block. ⟹ It must be LOOSER THAN OR EQUAL TO the tool, never stricter: it uses
# `OTP_VIEW_MAX_MINUTES` (12h), NOT the 15-minute step-up window.
# Anyone who reads this gate as a security gate and then removes the lock in the tool OPENS hard
# constraint 4.
#
# ON BY DEFAULT: the invariant of this round is "no turn spends tokens before OTP verification is
# complete" — a gate that is OFF by default can't deliver that invariant. Declared clearly: this
# IS a product-behaviour change, not a measurement flag.
OTP_GATE_GROUP_B_ENABLED = os.environ.get("OTP_GATE_GROUP_B_ENABLED", "1").strip().lower() in ("1", "true", "yes")

# T3 · the model's reasoning switch. DEFAULT CHANGED 1 -> 0 on 18/08: this is no longer a
# MEASUREMENT flag, it is the fix for a product that WAS BROKEN.
#
# [MEASURED] same `qwen3.7-plus-2026-05-26`, same real CSKH question:
#     default (reasoning ON)    20.88s · out 1161 · reasoning 980
#     enable_thinking=False      2.48s · out  101 · reasoning   0     ← 8.4× faster
#     thinking_budget=0          HTTP 400 — this path is NOT usable
# [MEASURED by tester] one real agent turn: median 18.6s · SLOWEST 49.1s
# [MEASURED] AGENT_TURN_TIMEOUT_SECONDS = 45.0
# ⟹ 49.1 > 45 ⟹ "show my recent transactions" — a question customers WILL ask — was
# falling back on timeout. Reasoning ON was the state that pushed the product over the ceiling.
#
# 🔴 This flag buys SPEED, NOT TOKENS. [MEASURED] the real ledger, last 5 turns:
# input 10,920–23,520 · output 236–709 ⟹ input is >95% of the cost. The real token lever is the
# ~14K input (system prompt + tool schemas + history), which is a DIFFERENT job. Anyone reading
# this flag as "costs optimised" is misreading it.
#
# 🔴 DO NOT add a second variable (`FIN05_LLM_SUY_LUAN`…) for the same switch:
# two definitions of the same thing will drift, and drift silently — the same reason
# `hash_source` and `BUILD_COMMIT` exist. To re-enable: `REASONING_ENABLED=1`.
#
# ⚠️ Read AT IMPORT ⟹ changing it requires RECREATING the container. `docker exec -e` only
# changes a child process; it doesn't touch the uvicorn already serving.
REASONING_ENABLED = os.environ.get("REASONING_ENABLED", "0").strip().lower() not in ("0", "false", "no")

BUILD_COMMIT = os.environ.get("BUILD_COMMIT") or "khong-ro"
BUILD_AT = os.environ.get("BUILD_AT") or "khong-ro"


def _db_identity(url: str) -> tuple[str, str]:
    """Returns (db_kind, db_name) from DATABASE_URL, with all sensitive information removed."""
    scheme = url.split("://", 1)[0].split("+", 1)[0] or "unknown"
    tail = url.rsplit("/", 1)[-1].split("?", 1)[0] if "/" in url else ""
    if scheme == "sqlite":
        tail = tail or "(bộ nhớ)"
    return scheme, tail or "(không rõ)"


DB_KIND, DB_NAME = _db_identity(DATABASE_URL)

# BR-13: threshold N of clarifying questions before creating a manual-investigation ticket —
# NOT YET agreed with the team (business_rules.md BR-13, verified: false). Isolated here so it
# changes in one place when the PO decides.
CLARIFY_QUESTION_MAX_ROUNDS = 2

# BR-01/BR-02: legal ceilings used to compute sla_due_at — verified: false, see
# data/schema/scenarios.yaml §sla.legal.
SLA_LEGAL_BANK_BUSINESS_DAYS = 4
SLA_LEGAL_GENERAL_DAYS = 30

# BR-03: internal service commitment (wording given to customers) — NOT used to compute
# sla_due_at (see BR-04). Only used in agent replies.
SLA_SERVICE_FIRST_RESPONSE_HOURS = 48
SLA_SERVICE_FRAUD_BUSINESS_DAYS = 7

# Fixed seed used when generating the dataset (scripts/gen_dataset.py --seed, default
# 20260802 — PRD §9). The backend needs this value again to recompute the demo security answer
# (User.security_answer_hash = sha256(f"ans-{seed}-{user_id}")) during real OTP verification
# (src/auth.py) — the answer is NEVER stored in plaintext anywhere; only the formula is
# reconstructed to compare hashes, keeping the principle of never storing secrets in raw form.
DATASET_SEED = 20260802

# Threshold for locking an OTP verification session after N failures — REUSES exactly the
# min_failed_attempts of FS-06 (data/schema/fraud_signals.yaml) for consistency with the
# "authentication anomaly" definition fraud_engine.py already uses, rather than inventing a
# separate number.
OTP_MAX_FAILED_ATTEMPTS = 3

# EU/US benchmark 27/08, Finding #2 — `/auth/otp/request` and
# `/resolutions/{id}/request-approval-otp` returned `otp_code` directly in the response body,
# erasing the "possession" factor (PSD2 dynamic linking only true on paper, NIST 800-63B dropping
# from designed AAL2 to runtime AAL1). OFF BY DEFAULT (fail-closed, per the APP_ENV principle
# above) — enabled manually with OTP_DEMO_MODE=true, and NOT allowed together with
# APP_ENV=production: a deploy machine forgetting to remove the demo flag would leak transaction
# OTPs to production — not an acceptable "forgot to set it" mistake like APP_ENV, so this fails
# fast at startup rather than waiting for runtime.
OTP_DEMO_MODE = os.environ.get("OTP_DEMO_MODE", "").strip().lower() in ("1", "true", "yes")
if OTP_DEMO_MODE and APP_ENV == "production":
    raise RuntimeError(
        "OTP_DEMO_MODE=true nhưng APP_ENV=production — không được trả otp_code "
        "qua response body ở môi trường production (benchmark EU/US 27/08, "
        "Phát hiện #2). Tắt OTP_DEMO_MODE hoặc sửa APP_ENV cho đúng."
    )

# AUTH-005/007/008 (FIN05_QA_TestCases.jsonl) — design decisions settled after comparing
# against industry standards (research 2026-08-10, see docs/TESTING.md):
# - VIEW-ONLY actions (lookup_transaction, get_customer_history — including viewing the status of
#   existing tickets/complaints, AUTH-005 branch (e)): apply exactly
#   NIST SP 800-63B / OWASP ASVS 5.0 Level 2 for an AAL2 session — at most 12 hours
#   from OTP verification, regardless of activity (a simplification of "30 minutes of inactivity OR
#   a 12-hour maximum" — the current system uses stateless JWTs and doesn't track real-time
#   activity between requests, so only the absolute limit applies, not the inactivity one).
OTP_VIEW_MAX_MINUTES = 12 * 60

# - create_ticket (which can lead to a real refund, a financial consequence) requires
#   FRESHER verification — a 2-tier risk-based step-up model (industry practice: step-up validity
#   windows are commonly 15-60 minutes; the strict 15-minute mark was chosen because this is an
#   action with financial consequences, not merely viewing).
OTP_STEPUP_FRESH_MINUTES = 15

# AUTH5-04 (Auth Flow upgrade, 2026-08-12) — a SEPARATE step-up OTP for
# POST /resolutions/{id}/approve (PSD2 dynamic linking, see AuthSession.
# resolution_id/amount_snapshot). Shorter than OTP_STEPUP_FRESH_MINUTES because this is a REAL
# financial approval (not just unlocking further actions like create_ticket) — the supervisor
# must request the OTP right before clicking approve.
RESOLUTION_APPROVAL_OTP_FRESH_MINUTES = 10

# BR-06: PDPA masking format for third-party information.
PHONE_MASK_VISIBLE_PREFIX = 3
PHONE_MASK_VISIBLE_SUFFIX = 4
BANK_ACCOUNT_MASK_VISIBLE_SUFFIX = 4

# Agent (src/agents/) — PRD §15.3: prefer cheap/fast models for lookup + classification,
# matching the "low AI cost" positioning (Brief §3). Changed via env, not code.
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

# Real measurement 2026-08-13 (stressing /agent/chat via Playwright repeat-each): the
# openai-python SDK has NO timeout by default (waiting until the OS/socket closes), and
# ChatOpenAI defaults to `max_retries=2` — one slow/transiently failing call can drag on for tens
# of seconds (23-33s measured), and since the `/agent/chat` route runs synchronously in the
# threadpool, a Playwright request that times out and gives up CANNOT cancel the OpenAI call
# still running server-side — it keeps holding a thread + rate-limit budget, piling up across
# tests and slowing down many requests AFTER it too. An explicit ceiling makes a failing call
# always fail fast, without dragging the whole chain with it.
OPENAI_TIMEOUT_SECONDS = float(os.environ.get("OPENAI_TIMEOUT_SECONDS", "20"))
OPENAI_MAX_RETRIES = int(os.environ.get("OPENAI_MAX_RETRIES", "1"))

# --- PROVIDERS: CHAT separated from EMBEDDING -------------------------------
# Switch providers via environment variables, not code. Every variable below FALLS BACK to
# `OPENAI_*` -> setting nothing behaves exactly as before.
#
# WHY SPLIT IN TWO rather than one shared base_url/key pair:
# changing the CHAT model changes behaviour — re-measurable, failures visible immediately.
# Changing the EMBEDDING model changes the OBJECT — every vector in the store becomes meaningless,
# everything must be re-ingested, and every retrieval number measured before breaks its chain. Two
# jobs of different weight; one shared variable invites an operator to do the second while
# believing they are only doing the first.
# ---------------------------------------------------------------------------
# The two SDK variables are FORBIDDEN outright. Don't reason about them — block them.
#
# The openai SDK reads `OPENAI_BASE_URL` and `OPENAI_API_BASE` from the environment itself, and
# they BEAT even an explicitly passed `base_url=None`. Measured:
#     ChatOpenAI(api_key=...)                       -> dashscope-intl…/v1/
#     ChatOpenAI(api_key=..., base_url=None)        -> dashscope-intl…/v1/
#     OpenAIEmbeddings(api_key=..., base_url=None)  -> dashscope-intl…/v1/
#
# ⟹ `_key_for_provider` below is NOT enough on its own: it asks "did WE change the destination?"
# (is `LLM_BASE_URL` set). The right question is "did the DESTINATION change?" — and the
# destination is the UNION of our variables AND the SDK's. Setting `OPENAI_BASE_URL` and leaving
# `LLM_API_KEY` empty reproduces EXACTLY the 17/08 incident, silently, with no startup error.
#
# And that is the MOST INTUITIVE move: tell someone "point the system at the new provider", and
# the first thing they look for is `OPENAI_BASE_URL`. The old fix blocked the DOCUMENTED path;
# the intuitive path stayed open.
#
# Forbidden rather than supported: the project already has dedicated variables for EACH ROLE
# (`LLM_*` for chat, `EMBEDDING_*` for embeddings). The SDK variables apply to BOTH at once, so
# they can only ever BYPASS that separation, never serve it.
for _forbidden_var in ("OPENAI_BASE_URL", "OPENAI_API_BASE"):
    if os.environ.get(_forbidden_var):
        raise RuntimeError(
            f"{_forbidden_var} bị CẤM trong dự án này.\n"
            f"  SDK đọc nó và nó THẮNG cả base_url truyền tường minh, nên nó đổi\n"
            f"  đích đến của CẢ chat lẫn embedding cùng lúc mà không cơ chế nào\n"
            f"  của ta nhìn thấy — đúng đường đã làm rò khoá OpenAI sang bên thứ\n"
            f"  ba ngày 17/08.\n"
            f"  Dùng LLM_BASE_URL (chat) hoặc EMBEDDING_BASE_URL (embedding)."
        )


def _key_for_provider(key_label: str, base_url: str | None) -> str | None:
    """The key may ONLY fall back to OPENAI_API_KEY when the DESTINATION is still OpenAI.

    🔴 My first version wrote `os.environ.get("LLM_API_KEY") or OPENAI_API_KEY`
    UNCONDITIONALLY. With `LLM_BASE_URL` pointing at another provider and the key forgotten, it
    SENT THE OPENAI KEY TO A THIRD-PARTY SERVER. Measured: dashscope base_url +
    empty LLM_API_KEY -> the `sk-proj…` key went to Alibaba.

    No error fires: the other side just returns 401, the operator reads "401" and looks in the
    wrong place, while the production key has already left the system.

    A fallback is only safe when the DESTINATION doesn't change. Changing the destination while
    keeping the fallback turns a convenience into a leak.
    """
    key_name = os.environ.get(key_label)
    if key_name:
        return key_name
    if base_url:
        raise RuntimeError(
            f"Thiếu {key_label} trong khi đã đặt base_url tới nhà cung cấp khác "
            f"({base_url}). KHÔNG tự dùng OPENAI_API_KEY thay thế — làm vậy là "
            f"gửi khoá OpenAI sang máy chủ của họ. Đặt {key_label} trong .env."
        )
    return OPENAI_API_KEY


LLM_BASE_URL = os.environ.get("LLM_BASE_URL") or None

# The channel offered to customers when the agent CAN'T serve them and we DELIBERATELY don't
# create a ticket (provider errors needing intervention: 401/403/400/404). This is the only path
# left for a customer who may be trying to report fraud — see the comment in graph.py.
#
# The default is DELIBERATELY a generic phrase with NO phone number: fabricating a hotline number
# in a reply to a customer violates hard constraint 3 in the literal sense — the customer would
# CALL it. When the PO sets `HOTLINE_CSKH`, replies carry the real number.
_hotline = os.environ.get("HOTLINE_CSKH", "").strip()

# Is the number DIALABLE — a POSITIVE test, not a denylist.
#
# 17/08 the PO set `HOTLINE_CSKH=1900-XXXX (SỐ TẠM — CHƯA CẤU HÌNH)` (temporary number — not yet
# configured): deliberately undialable, so the field is filled yet declares itself unconfigured.
# Right for operations — but the old code interpolated that value DIRECTLY into what the customer
# is told, i.e. the customer would read "please contact customer service at 1900-XXXX (SỐ TẠM —
# CHƯA CẤU HÌNH)".
#
# So this place must ask "is this value DIALABLE", not "is the variable set". A denylist
# ("XXXX", "TODO", "chưa cấu hình"...) will miss the fourth placeholder someone invents; a
# positive test won't.
_MIN_DIGITS = 8
DIALABLE = bool(re.fullmatch(r"[0-9 ()+.\-]+", _hotline)) and \
    sum(c.isdigit() for c in _hotline) >= _MIN_DIGITS

# The customer ONLY sees the number when it is dialable. Not dialable -> fall back to the
# generic phrase, because an uncallable number is worse than no number: it turns "no path" into
# "a path leading nowhere", and the customer believes they have a way forward.
OTHER_SUPPORT_CHANNELS = (
    f"tổng đài chăm sóc khách hàng {_hotline}" if DIALABLE
    else "tổng đài chăm sóc khách hàng"
)
# `or OPENAI_MODEL` has the SAME SHAPE as the key hole above, but NEEDS no guard —
# written down so later readers can tell "considered" from "overlooked": the payload here is
# benign. Forget to set it and we ask the new provider for a model named "gpt-4o-mini" and get
# their error. It reveals WHAT WE USE, no SECRET.
LLM_MODEL = os.environ.get("LLM_MODEL") or OPENAI_MODEL
LLM_API_KEY = _key_for_provider("LLM_API_KEY", LLM_BASE_URL)

# Phase 3 — model pool for the switch/rotate feature (fixed by the real PO 19/08, `876a240`).
# A comma-separated list, ORDER = rotation priority. The first element MUST be
# `LLM_MODEL` — never auto-added/reordered: a pool that doesn't start with the pinned model
# SILENTLY changes default behaviour even when nobody uses the rotation feature.
# MISSING variable ⟹ the pool contains only `LLM_MODEL` — the old behaviour, one model, no
# rotation.
_raw_pool = os.environ.get("LLM_MODEL_POOL", "").strip()
LLM_MODEL_POOL: list[str] = (
    [m.strip() for m in _raw_pool.split(",") if m.strip()] if _raw_pool else [LLM_MODEL]
)
# WITHDREW a guard "first element must == LLM_MODEL" written here, then rejected it myself:
# [MEASURED] test_llm_pool_gd3.py (QA/QC, written from the spec) requires being able to change
# the WHOLE pool via env WITHOUT also changing `LLM_MODEL` — exactly the original constraint
# "change LLM_MODEL_POOL, the pool follows, NO code/image change NEEDED". A guard forcing the two
# variables into sync would BLOCK that very scenario. `LLM_MODEL` and `LLM_MODEL_POOL` are two
# DELIBERATELY INDEPENDENT variables; the rotation reads `LLM_MODEL_POOL`, not `LLM_MODEL`
# directly — they don't need to match to be correct.

# Minimal spending cap (fixed by the real PO 19/08) — ONLY CHAT-model (LLM) tokens, 🔴
# NOT embeddings: embeddings go through the SAME transport (egress_gate.py) but a DIFFERENT
# provider (EMBEDDING_BASE_URL != LLM_BASE_URL, see below) — adding two providers' tokens into one
# cap means adding two different units, producing a number that looks valid and means nothing.
# The variable name states this limitation so nobody misreads it as "all spending" — see
# egress_gate._under_daily_spend_cap().
# EMPTY/MISSING ⟹ NO limit (the old behaviour, nothing extra blocked).
_raw_cap = os.environ.get("LLM_DAILY_TOKEN_CAP", "").strip()
LLM_DAILY_TOKEN_CAP: int | None = int(_raw_cap) if _raw_cap else None

# Pool-declaration ping mode — "eager" test-calls EVERY model when declaring the pool ready
# (dev, 0 cost); "lazy" only marks "unverified" and pings a model the first time it is CHOSEN
# (live, pings cost real money). Defaults to "eager" — the more thorough check when nobody sets
# anything, safer if someone forgets to set it on a paid environment.
MODEL_POOL_PING = os.environ.get("MODEL_POOL_PING", "eager").strip().lower()
if MODEL_POOL_PING not in ("eager", "lazy"):
    raise RuntimeError(f"MODEL_POOL_PING phải là 'eager' hoặc 'lazy', nhận được {MODEL_POOL_PING!r}.")

# Output token cap. DEFAULT None = the parameter is NOT passed -> exactly today's behaviour
# (relying on the provider's default). DELIBERATELY no number:
# adding a cap here would TRUNCATE long answers that currently work fine, i.e. fixing a bug that
# hasn't happened by creating one that certainly will.
#
# Why this knob is needed: reasoning models (Qwen) spend tokens on THINKING before producing
# content. A low cap -> all spent on thinking -> EMPTY `content`, with NO error. When switching to
# such a model, set this variable explicitly rather than hoping their default is enough.
# ⚠️ MEASURED PER MODEL — how much of the OUTPUT tokens the hidden thinking takes:
#     qwen3.7-plus  61%        qwen3.8-max  77%
# The higher it is, the wider this cap must be. Tightening it to save money on a reasoning model
# buys empty answers: the model spends the whole cap thinking, leaving no room for content
# -> `EmptyReplyError` (graph.py). Saving here doesn't reduce thinking costs; it only throws away
# what you already paid for.
LLM_MAX_TOKENS = int(os.environ["LLM_MAX_TOKENS"]) if os.environ.get("LLM_MAX_TOKENS") else None

EMBEDDING_BASE_URL = os.environ.get("EMBEDDING_BASE_URL") or None
EMBEDDING_API_KEY = _key_for_provider("EMBEDDING_API_KEY", EMBEDDING_BASE_URL)

# Number of chunks sent in ONE embedding call. LangChain defaults to 1000 — OpenAI accepts it,
# Qwen rejects it: "batch size is invalid, it should not be larger than 10".
# There is NO common standard for this limit across providers, so it must be a variable.
# Defaults to 10 when pointing at another provider (the safest value encountered), and keeps the
# library default for the OpenAI path so the object doesn't change.
EMBEDDING_BATCH_SIZE = int(os.environ.get("EMBEDDING_BATCH_SIZE") or (10 if EMBEDDING_BASE_URL else 0))

# --- The eval YARDSTICK: PINNED AS A CONSTANT, NOT tied to the product model --------
# An adversarial turn has THREE roles calling a model:
#     SUBJECT      the agent under test      (run_agent_turn -> LLM_MODEL)
#     STIMULUS     the simulated attacker    (eval/_harness.py)
#     REFEREE      the grader                (eval/_llm_judge.py)
# If all three read one shared variable, switching providers changes all three at once, and
# `96/96 -> 94/96` can't be attributed: did the agent get weaker, the attacker stronger, or the
# referee grade differently? Three variables, one number — exactly the trap that killed the
# 41.4/35.7 pair, this time inside the SAFETY measurement suite.
#
# DELIBERATELY pinned to a literal string, NOT `or OPENAI_MODEL`: an operator's most natural way
# of switching providers is editing `OPENAI_MODEL` in `.env`, and if the yardstick were anchored
# to it, it would quietly follow the object. The yardstick must stay still even when people
# change the object by a path nobody anticipated.
#
# Changing the yardstick is a SEPARATE decision: the variable must be set deliberately, and
# everything must be re-graded.
_DEFAULT_MODEL = "gpt-4o-mini"
JUDGE_MODEL = os.environ.get("EVAL_JUDGE_MODEL") or os.environ.get("JUDGE_MODEL") or _DEFAULT_MODEL
EVAL_SIM_MODEL = os.environ.get("EVAL_SIM_MODEL") or _DEFAULT_MODEL

# 1 /agent/chat turn = 1 multi-step ReAct loop (LLM generation + interleaved tool calls,
# up to _AGENT_RECURSION_LIMIT=20 steps) — OPENAI_TIMEOUT_SECONDS above only caps EACH individual
# OpenAI call, not the TOTAL time of the chat turn (measured: one /agent/chat request took 70s
# because it needed many steps, each nearly hitting OPENAI_TIMEOUT_SECONDS). This is the TOTAL
# ceiling for the whole agent.invoke(), handled like GraphRecursionError (switching to human
# handoff instead of hanging indefinitely or returning 500) — see
# src/agents/graph.py::run_agent_turn.
AGENT_TURN_TIMEOUT_SECONDS = float(os.environ.get("AGENT_TURN_TIMEOUT_SECONDS", "45"))

# Security (src/auth.py, src/db/crypto_types.py) — NO default value for these 2 keys:
# a guessable/empty key is a hole pretending to be security, worse than nothing (it looks like
# JWT is enforced while anyone can forge tokens). Missing key -> error immediately at import, not
# a silent error at runtime.
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise RuntimeError(
        "Thiếu JWT_SECRET_KEY trong .env — sinh bằng: "
        "python3 -c \"import secrets; print(secrets.token_urlsafe(48))\""
    )
JWT_ALGORITHM = "HS256"
# AUTH5-02 (Auth Flow upgrade 2026-08-12, NIST SP 800-63B-4/PSD2) — cut from 8 hours to
# 15 minutes. Old tokens (8h, issued before the upgrade) STILL pass
# _decode() normally until they expire naturally (no new mandatory field was added to the
# payload) — live sessions are not abruptly locked out (AUTH5-MIGRATE-001).
# Read from env (default STAYS 15) — added 2026-08-16 to be able to stand up a short-TTL test
# instance. Why it's worth it: reproducing the refresh-race bug class means waiting for the last
# 120s window of a session, i.e. ~minute 13 every time; k=10 takes over 2 hours. With TTL=1
# minute, k=30 fits in 20 minutes, and regression tests for the auth area can EXIST at all
# — nobody lets CI wait 13 minutes per case.
#
# ⚠️ LOWERING this value LOWERS A SECURITY CONTROL (AUTH5-02, cut from 8h to 15 minutes per
# NIST SP 800-63B-4/PSD2). Only for TEST instances running under a SEPARATE project name. NEVER
# set it in the real stack's `.env`.
JWT_ACCESS_EXPIRE_MINUTES = int(os.environ.get("JWT_ACCESS_EXPIRE_MINUTES", "15"))

# Refresh token (NOT a JWT — a random string stored in Redis, see
# src/auth.py::mint_refresh_token) — internal roles (cskh/supervisor/
# partner_admin) carry higher risk if stolen (they touch many customers' data), so their TTL is
# much shorter than customers' (AUTH5-02B).
JWT_REFRESH_EXPIRE_DAYS_CUSTOMER = 7
JWT_REFRESH_EXPIRE_DAYS_STAFF = 1

FIELD_ENCRYPTION_KEY = os.environ.get("FIELD_ENCRYPTION_KEY")
if not FIELD_ENCRYPTION_KEY:
    raise RuntimeError(
        "Thiếu FIELD_ENCRYPTION_KEY trong .env — sinh bằng: "
        "python3 -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
    )

# Redis (Auth Flow upgrade, 2026-08-12) — JWT refresh-token revocation store + shared rate
# limiting (login, OTP, live-chat ws-ticket/message).
# NO default pointing at a real Redis (same fail-fast principle as
# JWT_SECRET_KEY above) — but the explicit "fake://" scheme IS ALLOWED (using
# fakeredis, see src/redis_client.py) for CI/tests that need no real Redis, per the
# playbooks/production-packaging-checklist.md convention ("REDIS_URL: fake://").
REDIS_URL = os.environ.get("REDIS_URL")
if not REDIS_URL:
    raise RuntimeError(
        "Thiếu REDIS_URL trong .env — dùng redis://<host>:6379/0 cho môi trường "
        "thật, hoặc fake://ci cho CI/test không cần Redis thật (fakeredis)."
    )

# Policy/FAQ RAG (src/rag/) — uploaded by the e-wallet partner (role partner_admin),
# searched by the agent + CSKH (search_policy tool, POST /policy-search).
RAG_INDEX_DIR = ROOT_DIR / "data" / "rag_index"  # Chroma persistent store — not committed (.gitignore)
# Read from the `EMBEDDING_MODEL` env var. ONE constant for ONE thing — deliberately no second
# name `EMBEDDING_MODEL` at the Python layer; two names for one value is a sure way for them to
# drift apart later.
#
# ⚠️ CHANGING THIS VARIABLE = CHANGING THE OBJECT, and store.py HAS A GUARD (see `_stamp`): the
# store's version stamp used to record only `chuan_hoa` (normalisation), NOT the model. Left that
# way, changing the embedding model would make every vector one-sidedly drift while `kiem` stayed
# green — search returns k results, wrong ones, with no symptom. Exactly bug class #2.
RAG_EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL") or "text-embedding-3-small"
RAG_CHUNK_SIZE = 800
RAG_CHUNK_OVERLAP = 150
RAG_SEARCH_TOP_K = 4

# ADR-061 (03/09) — Finding ① layer 2: an abstention gate via cross-encoder rerank
# instead of a single bi-encoder distance threshold (measured and REJECTED — see the ADR).
# Mechanism: fetch RAG_RERANK_CANDIDATE_K candidates from Chroma (wider than
# RAG_SEARCH_TOP_K so the right chunk isn't missed outside a narrow top-K — case
# REL-IW-01 measured 03/09 is the evidence: Chroma's top-1 was wrong, but the top-8 contained the
# right chunk), rerank ALL of them, drop chunks below the threshold, and trim the rest to
# RAG_SEARCH_TOP_K by rerank score (not the old distance order).
RAG_RERANK_MODEL = os.environ.get("RAG_RERANK_MODEL") or "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
RAG_RERANK_CANDIDATE_K = int(os.environ.get("RAG_RERANK_CANDIDATE_K", "8"))
# ADR-061 update 04/09 — SIDECAR architecture (measured: a 4-5 worker backend multiplies RAM
# if the model is loaded directly in-process). Empty = feature FULLY OFF
# (rerank.py treats the sidecar as always "unreachable", fail-closed fallback —
# not an error, a valid state for stacks that haven't enabled this service).
RAG_RERANK_SERVICE_URL = os.environ.get("RAG_RERANK_SERVICE_URL", "")
# 5s → 15s (04/09, caught by the PO in real logs) — a SECONDARY safety margin, after
# `rerank_service/app.py` received the root fix (loading the model at startup instead of lazily
# on the first request). 15s now only has to absorb genuinely slow networks/momentary machine
# load, no longer model loading time (moved off the request path). Don't lower it back to 5s
# without re-measuring — 5s was PROVEN insufficient on the RAM-thin po-demo VM (real timeout logs
# 04/09).
RAG_RERANK_TIMEOUT_S = float(os.environ.get("RAG_RERANK_TIMEOUT_S", "15"))
# Threshold measured 03/09 on 18 real cases (Vietnamese, top-k→rerank): fully separated,
# relevant 7.03–10.91 / irrelevant -7.52–-0.98, gap midpoint ~3.0. DO NOT change this number
# without re-measuring — exactly the lesson of the single threshold that already failed once in
# another approach (bi-encoder distance).
RAG_RERANK_THRESHOLD = float(os.environ.get("RAG_RERANK_THRESHOLD", "3.0"))
# A SEPARATE threshold for /policy-search (CSKH reads excerpts directly — the page subtitle
# states "NOT through AI synthesis"; fixed by the real PO 05/09: the precision concern of
# Finding ① [the AI QUOTING a wrong-scope chunk inside an ASSERTION] doesn't apply here; humans
# read/filter the excerpts themselves) — NOT applied to the agent path (the 5 tools of
# `build_customer_tools` keep RAG_RERANK_THRESHOLD=3.0 exactly as before.
#
# Measured 05/09 on eval/rag_policy_set.jsonl (34 cases, built by PO+QA), sweeping in
# 0.5-point steps: -2.5 to -2.9 give EXACTLY 2/28 off cases (both the same hard keyword "tranh
# chấp" — dispute; NO precision case leaks — 9/9 garbage/off-topic/internal-probing cases stay
# not_found). From -3.0 downwards, "giá vàng hôm nay bao nhiêu" (what's the gold price today,
# P2-01, CLEARLY off-topic) starts leaking — -2.5 is a SAFE stopping point with margin (not right
# against the -3.0 wall). DO NOT lower it further without re-measuring the 34 cases.
#
# 🔴 Review 05/09 re-measured 12 queries on the live sidecar and found the REAL margin thinner
# than the totals (26/28+9/9) suggest: "phí rút"/"hạn mức" (withdrawal fee/limit — found, right
# side) are only ~0.4 points above the threshold; "giá vàng" (garbage, right side) is only ~0.4
# points BELOW it — the gap between the lowest short found query and the highest garbage is only
# ~0.8 points, while most other cases are separated by 3-5+ points. Not a reason to reject this
# threshold (all 34 existing cases fall on the right side) — but a thin margin means another
# slightly different short query (e.g. "hạn mức tối đa", "phí chuyển" — maximum limit, transfer
# fee) MAY fall on the wrong side in ways the 34-case set never measured. Watch for new reports of
# wrong not_found/found on differently phrased short queries — don't re-measure from scratch,
# consult this log directly.
RAG_RERANK_THRESHOLD_CSKH = float(os.environ.get("RAG_RERANK_THRESHOLD_CSKH", "-2.5"))
MAX_UPLOAD_SIZE_MB = 10

# Live chat (2026-08-11) — the SECOND line of defence alongside cleaning up sessions on a CLEAN
# WS disconnect (release_staff_sessions/close_customer_session_on_disconnect,
# src/api/live_chat_ws.py): a sudden network drop/killed browser can't send a close frame, so the
# server may never receive WebSocketDisconnect — a 'waiting' session would hang forever if we
# relied only on the disconnect signal. Any 'waiting' session (unclaimed) that is too old is
# treated as the customer having left long ago — 30 minutes is wide enough not to wrongly close
# a customer genuinely waiting (the ETA shown to customers is only an estimate; there is no hard
# SLA commitment at the live-chat layer).
LIVE_CHAT_STALE_WAITING_MINUTES = 30

# ---------------------------------------------------------------------------
# F-30 — LangSmith/LangChain tracing EXPLICITLY OFF (2026-08-15)
# ---------------------------------------------------------------------------
# The `langsmith` package ships with `langchain`, so it is already in the environment.
# LangChain's NATIVE tracer is enabled entirely via environment variables — no code needed —
# and it sends prompts/responses straight to LangSmith Cloud.
#
# Why this is a separate issue, not a duplicate of existing observability: the project's
# `_scrub_and_truncate` layer lives in a HAND-WRITTEN callback
# (src/observability/langchain_callback.py). The native tracer does NOT go through that layer —
# it is a PARALLEL data export channel, bypassing all PII scrubbing, and it can be switched on
# without leaving any trace in git.
#
# Setting false EXPLICITLY here turns an IMPLICIT configuration into a VISIBLE decision:
# to really enable it, this line must be edited ⟹ there is a diff, a review, and a record under
# Law 91/2025/QH15 (transferring personal data abroad — specific article numbers NOT yet verified
# against the new law, see docs/security/2026-08-30-niem-luat-91-2025-*.md;
# don't assign old Decree 13/2023 article numbers). `setdefault` rather than overwriting:
# operators can still deliberately enable it via env var, but the silent default is never "on".
os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")
os.environ.setdefault("LANGSMITH_TRACING", "false")  # the new name of the same flag
