"""FIN-05 — FastAPI app.

Route groups, deliberately separated so the HITL boundary (Data Brief §6.6, design decision #1
in the project context) is visible right at the routing layer:

  /tools/*        — called by the agent to investigate/create tickets/propose/escalate.
                    NO route in this group can write `approved`.
  /resolutions/{id}/approve  — callable ONLY by a supervisor (role=supervisor). This is the
                    ONLY path in the entire system that writes the approved state — for every
                    transaction scope, including internal wallet transfers
                    (a corrected design decision, see project context §4.1).
  /tickets*       — reads, used by the CSKH/supervisor UI.

Security fix (session after the first demo): EVERY route that needs identity now declares
`Depends(get_current_user)` or `Depends(require_role(...))` — identity comes from the signed JWT
(src/auth.py), NEVER from a client-declared body field (user_id/approved_by/rejected_by/
created_by/requested_by were removed from schemas.py). Previously anyone calling the API could
impersonate any user — the most serious vulnerability fixed.
"""
from __future__ import annotations

import calendar
import datetime as dt
import json
import logging
import os
import random
import secrets
import time
import uuid

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from src.agents.graph import close_checkpointer, read_handoff_transcript, run_agent_turn
from src.agents.tools.customer_tools import _classify_tier
from src.api.deps import get_session
from src.api.live_chat_ws import live_chat_websocket_endpoint
from src.api.live_chat_ws import manager as _live_chat_manager
from src.api.schemas import (
    AgentChatRequest,
    ApproveResolutionRequest,
    CreateTicketRequest,
    EscalateTicketRequest,
    GetCustomerHistoryRequest,
    LiveChatCsatRequest,
    LiveChatWsTicketRequest,
    LoginRequest,
    LookupTransactionRequest,
    OtpVerifyRequest,
    PolicySearchRequest,
    ProposeResolutionRequest,
    RefreshTokenRequest,
    RejectResolutionRequest,
    RequestMoreInfoRequest,
)
from src.auth import (
    CurrentUser,
    create_access_token,
    get_current_user,
    is_access_token_revoked,
    mint_refresh_token,
    require_otp_verified,
    require_role,
    require_unrevoked_token,
    revoke_refresh_token,
    rotate_refresh_token,
    set_revoked_before_now,
    try_decode,
)
from src.config import (
    AGENT_TURN_TIMEOUT_SECONDS,
    APP_ENV,
    BUILD_AT,
    BUILD_COMMIT,
    DB_KIND,
    DB_NAME,
    DIALABLE,
    ENABLE_API_DOCS,
    OPENAI_MAX_RETRIES,
    OPENAI_TIMEOUT_SECONDS,
    OTP_DEMO_MODE,
    OTP_MAX_FAILED_ATTEMPTS,
    REDIS_URL,
    RESOLUTION_APPROVAL_OTP_FRESH_MINUTES,
    ROOT_DIR,
)
from src.build_stamp import HASH_METHOD, STAMP_PATH, hash_source, build_time_stamp
from src.db.models import (
    AuthSession,
    ChatSession,
    Complaint,
    Escalation,
    InvestigationLog,
    Message,
    PolicyChunk,
    PolicyDocument,
    Resolution,
    Ticket,
    ToolResult,
    User,
)
from src.observability.context import bind_context, clear_context
from src.observability.logging_config import configure_logging
from src.observability.pii import scrub_pii
from src.observability.tracing import configure_tracing, instrument_fastapi_app
from src.rag.ingest import delete_document as _delete_policy_document
from src.rag.ingest import ingest_document
from src.rag.search import search_policy_text
from src.rate_limit import RedisConcurrencyLimiter, RedisSlidingWindowLimiter
from src.services import live_chat, reporting
from src.services.complaint_intake import create_ticket_with_fraud_check
from src.services.notifications import (
    mark_read,
    mark_all_read,
    count_unread,
    notify_decided,
)
from src.services.notifications import (
    listing as list_my_notifications,
)
from src.services.presence import heartbeat as presence_heartbeat
from src.services.presence import online_user_ids, open_ticket_count
from src.tools.base import ToolError, new_id
from src.tools.escalate_ticket import escalate_ticket as _escalate_ticket
from src.tools.get_customer_history import get_customer_history as _get_customer_history
from src.tools.lookup_transaction import lookup_transaction as _lookup_transaction
from src.tools.masking import che_pii_van_ban
from src.tools.propose_resolution import propose_resolution as _propose_resolution

configure_logging()  # JSON stdout, correlation_id/user_id attached automatically — see
# src/observability/logging_config.py. Called HERE (at module import time, before any
# route/middleware runs) so EVERY logger in the process (including uvicorn.access if it
# propagates) shares one format from the very first request.
configure_tracing()  # OTel -> Jaeger (OTEL_EXPORTER_OTLP_ENDPOINT, default
# localhost:4317) — degrades gracefully if Jaeger is down, see tracing.py.

# AUTH5 (Auth Flow upgrade, 2026-08-12) — rate limits synchronised to Redis
# (the same store as JWT revocation) instead of scattered in-memory counters: they survive
# backend restarts, and security/rate-limit state is consistent system-wide in ONE source.
# `fake://` (CI/test) falls back to slowapi's default in-memory storage — no regression, no real
# Redis needed to run tests.
#
# 🔴 `in_memory_fallback_enabled=True` (24/08 — the Tester switched Redis off and `/agent/chat`
# WENT DOWN COMPLETELY: `ConnectionError` flew out of slowapi's EVALSHA, NOT A SINGLE response).
# slowapi's default when the Redis storage dies is to RAISE (read directly from
# `slowapi/extension.py::_check_request_limit` — `except Exception: ... else: raise`, because
# `swallow_errors`/`in_memory_fallback_enabled` are both `False` when not passed). This flag is
# slowapi's own OFFICIAL, TESTED mechanism for exactly this incident — it switches to in-memory
# counting (inheriting the declared limits AS IS) when Redis can't be read, and recovers when
# Redis comes back. Fixing it here fixes the `@limiter.limit(...)` layer, shared by EVERY route
# with this decorator — not just `/agent/chat`. The layer calling Redis DIRECTLY
# (RedisConcurrencyLimiter, RedisSlidingWindowLimiter — src/rate_limit.py) is fixed separately in
# that file.
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=None if REDIS_URL.startswith("fake://") else REDIS_URL,
    in_memory_fallback_enabled=True,
)

# Auto-generated docs are OFF BY DEFAULT — enabled explicitly via ENABLE_API_DOCS.
#
# Security measured inside the container: `/openapi.json` returned HTTP 200, 28,470 bytes,
# **31 paths** — including the parameter schemas and authentication model of the whole API.
#
# NOT LEAKING TODAY: Caddy only proxies the frontend; these three paths are not exposed. So this
# is latent, not an incident — but it is **most expensive when it leaks and cheapest to turn
# off**, and what it exposes is not one endpoint but the complete map.
#
# 🔴 CORRECTION 05/09 — PREVIOUSLY gated on `APP_ENV != production`, exactly the design
# "dev needs /docs, gate by environment rather than disable entirely" originally declared.
# CHANGED because of a REAL exposure: the judge-facing production (VPS `home`) needs
# `APP_ENV != production` ONLY to enable `OTP_DEMO_MODE` (showing the demo OTP code to judges, see
# `config.py::OTP_DEMO_MODE`) — the old flag read that SAME variable, so enabling the OTP demo
# accidentally ALSO opened `/docs` on real production. Two unrelated decisions tied to one
# variable. Split into a SEPARATE flag (`ENABLE_API_DOCS`, default FALSE) — local dev enables it
# explicitly when needed, no more implicit inference from APP_ENV.
#
# `INV-00` already ignores these three prefixes (tests/test_invariants.py), so their appearing/
# disappearing with this flag does NOT turn the contract gate red — checked before editing,
# because a security fix that turns another gate red would be hastily reverted.
app = FastAPI(
    title="FIN-05 AI Agent CSKH — Backend",
    version="0.1.0",
    docs_url="/docs" if ENABLE_API_DOCS else None,
    redoc_url="/redoc" if ENABLE_API_DOCS else None,
    openapi_url="/openapi.json" if ENABLE_API_DOCS else None,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
instrument_fastapi_app(app)  # auto-instruments the HTTP layer (phase 4) — request/response
# spans are automatic; DON'T hand-write spans for what the framework already handles.

# NO CORSMiddleware — on purpose. The frontend (Next.js, frontend/) calls through a BFF proxy
# (server-side route handlers, see frontend/src/app/api/), i.e. server-to-server, not
# browser-originated requests, so CORS doesn't apply and isn't needed. The JWT lives in an
# httpOnly cookie that browser JS can't read to attach an Authorization header itself — opening
# CORS for localhost:3000 would help nothing (there's no token to call with) and would only add
# attack surface (e.g. a malicious site running in the victim's browser fetching this origin
# directly). For manual debugging, use Swagger UI on the API's own origin (same-origin, no CORS
# needed) or curl.


# ---------------------------------------------------------------------------
# Audit log — who called which API, when, with what result. Written to a separate file
# (logs/access.log), apart from the application log, so security incidents can be investigated
# without digging through everyday debug logs.
# ---------------------------------------------------------------------------

_LOG_DIR = ROOT_DIR / "logs"
_LOG_DIR.mkdir(exist_ok=True)
_access_logger = logging.getLogger("fin05.access")
_access_logger.setLevel(logging.INFO)
if not _access_logger.handlers:
    _handler = logging.FileHandler(_LOG_DIR / "access.log", encoding="utf-8")
    _handler.setFormatter(logging.Formatter("%(message)s"))
    _access_logger.addHandler(_handler)
    _access_logger.propagate = False

_logger = logging.getLogger("fin05.api")


@app.middleware("http")
async def audit_log_middleware(request: Request, call_next):
    start = time.monotonic()
    identity = "anonymous"
    user_id = None
    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        current_user = try_decode(auth_header.split(" ", 1)[1])
        if current_user:
            identity = f"{current_user.user_id}:{current_user.role}"
            user_id = current_user.user_id
        else:
            identity = "invalid-token"

    # correlation_id: reuse `X-Request-ID` if the client/proxy already set it (e.g.
    # Caddy, see docs/DEPLOY.md), generate one otherwise — bound ONCE HERE via
    # contextvars (src/observability/context.py), so every log/span inside this request (even deep
    # in
    # the agent/tools) inherits it automatically, no manual threading through function parameters.
    # `reset()` in finally — MANDATORY per phase 2 of the observability checklist, preventing
    # context
    # leaking into the next request if the thread/task is reused.
    correlation_id = request.headers.get("x-request-id") or f"req-{uuid.uuid4().hex[:16]}"
    tokens = bind_context(correlation_id=correlation_id, user_id=user_id)
    try:
        response = await call_next(request)
    finally:
        clear_context(tokens)
    response.headers["X-Correlation-Id"] = correlation_id

    _access_logger.info(
        json.dumps(
            {
                "ts": dt.datetime.utcnow().isoformat(),
                "correlation_id": correlation_id,
                "ip": request.client.host if request.client else None,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "identity": identity,
                "duration_ms": round((time.monotonic() - start) * 1000, 1),
            },
            ensure_ascii=False,
        )
    )
    return response


def _handle_tool_error(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except ToolError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


# ADR-064(b) (04/09) — ONE shared condition for EVERY route reading/writing data scoped to a
# specific Ticket, instead of repeating 3 lines in each route (repetition invites drift between
# routes — exactly the bug class the review caught when GET /tickets/{ticket_id} was initially
# missed). A supervisor is NEVER blocked by this function (unconditional return False) —
# supervisors don't claim and aren't filtered.
def _agent_blocked_by_claim(current_user: CurrentUser, ticket: Ticket) -> bool:
    return (
        current_user.role == "cskh"
        and ticket.claimed_by is not None
        and ticket.claimed_by != current_user.user_id
    )


# ---------------------------------------------------------------------------
# /auth/login — a REAL password (decision 2026-08-12, replacing the earlier hand-picked
# phone+role flow — see LoginRequest). The role comes from the user found via phone, not declared
# by the client. A stricter rate limit than other routes — against bulk phone/password probing.
#
# AUTH5-08 (Auth Flow upgrade 2026-08-12) — BEFORE the fix: `@limiter.limit`
# (slowapi) keyed PURELY on `get_remote_address` (IP) — all real customers come through the SAME
# `frontend` container (BFF architecture), so this was effectively a limit SHARED by every
# customer (one customer spamming wrong passwords locked out other customers on the same IP,
# recorded in
# tests/test_api/test_auth_login.py::test_login_rate_limit_shared_across_different_users_behind_same_ip).
# slowapi's key_func only receives `Request` and is called SYNCHRONOUSLY (can't await), so it
# can't read the parsed JSON body to key by phone — the slowapi decorator was removed from this
# route entirely and replaced with 2 manual layers sharing
# RedisSlidingWindowLimiter (Redis-synchronised, see src/rate_limit.py):
# (1) by PHONE — blocks brute force targeting one specific user PRECISELY, even from
#     MANY different IPs (the spirit of AUTH5-08).
# (2) by IP — a much WIDER threshold (only stopping crude floods/credential stuffing across many
#     phones from one source), no longer wrongly locking out other legitimate users sharing an IP.
# ---------------------------------------------------------------------------

_login_phone_limiter = RedisSlidingWindowLimiter(max_calls=10, window_seconds=60, name="login_phone")
_login_ip_limiter = RedisSlidingWindowLimiter(max_calls=60, window_seconds=60, name="login_ip")
_password_hasher = PasswordHasher()
# A "decoy" hash that is FORMAT-valid (matching no real password) — used for a FAKE verify
# when no user is found for the phone, keeping the PROCESSING TIME equivalent to the "user found
# but wrong password" branch. Without this step, an attacker measuring response latency could
# distinguish "phone number doesn't exist" (instant reply, no hashing) from "phone number exists"
# (verify costs ~50-100ms of argon2id CPU) — enumerating the list of real registered phone numbers
# without guessing a single password.
_DUMMY_PASSWORD_HASH = PasswordHasher().hash(secrets.token_urlsafe(32))


@app.post("/auth/login")
def login(request: Request, req: LoginRequest, session: Session = Depends(get_session)):
    if not _login_ip_limiter.allow(get_remote_address(request)):
        raise HTTPException(status_code=429, detail="Quá nhiều yêu cầu đăng nhập, thử lại sau")
    if not _login_phone_limiter.allow(req.phone):
        raise HTTPException(status_code=429, detail="Quá nhiều lần thử đăng nhập cho số điện thoại này, thử lại sau")

    user = session.scalar(select(User).where(User.phone == req.phone))
    stored_hash = user.password_hash if user and user.password_hash else _DUMMY_PASSWORD_HASH
    try:
        _password_hasher.verify(stored_hash, req.password)
        password_ok = user is not None and user.password_hash is not None
    except VerifyMismatchError:
        password_ok = False
    if not password_ok:
        raise HTTPException(status_code=401, detail="Số điện thoại hoặc mật khẩu không đúng")
    assert user is not None  # narrowing for the type checker — password_ok=True only when the user exists
    now = dt.datetime.utcnow()
    token = create_access_token(user_id=user.user_id, role=user.role, iat=now)
    # AUTH5-02 (Auth Flow upgrade 2026-08-12) — access_token is now short-lived
    # (15 minutes, JWT_ACCESS_EXPIRE_MINUTES), so it MUST come with a refresh_token for the frontend
    # to refresh on its own without making customers log in repeatedly.
    #
    # GOTCHA (a real finding while writing test_refresh_preserves_original_iat_for_
    # thread_continuity — off by exactly 7 hours = the machine's timezone): `datetime.timestamp()`
    # on a NAIVE datetime (utcnow() without tzinfo) interprets the time in the machine's LOCAL
    # timezone, not UTC — UNLIKE how PyJWT itself encodes the iat/exp claims (calendar.timegm(),
    # which always treats naive datetimes AS UTC, the real intent). Using .timestamp() here and
    # later
    # having rotate_refresh_token() rebuild it via utcfromtimestamp() + pass it back through
    # create_access_token() (which goes through PyJWT/timegm CORRECTLY) gives the NEW access_token
    # an
    # `iat` OFFSET from the original — breaking the AI conversation thread_id (user_id:iat, see
    # src/agents/graph.py) right after the first refresh. calendar.timegm() is mandatory here to
    # match
    # EXACTLY how PyJWT encodes it, round-tripping intact through utcfromtimestamp() later.
    login_iat = calendar.timegm(now.utctimetuple())
    refresh_token = mint_refresh_token(user_id=user.user_id, role=user.role, login_iat=login_iat, otp_verified_at=None)
    return {
        "user_id": user.user_id,
        "role": user.role,
        "full_name": user.full_name,
        "access_token": token,
        "refresh_token": refresh_token,
    }


# ---------------------------------------------------------------------------
# AUTH5-02/03/03B (Auth Flow upgrade, 2026-08-12) — short-lived access tokens (15 minutes) need a
# paired refresh token to renew; rotation + reuse detection
# (src/auth.py::rotate_refresh_token) prevents replay if a refresh token is stolen.
# `/auth/logout` directly satisfies the original ST2-P0-5/AUTH5 finding: previously there was NO
# JWT revocation mechanism at all in the backend (see
# tests/test_security/test_jwt_revocation.py).
# ---------------------------------------------------------------------------


@app.post("/auth/refresh")
@limiter.limit("30/minute")
def refresh_token_route(request: Request, req: RefreshTokenRequest):
    result = rotate_refresh_token(req.refresh_token)
    if result is None:
        raise HTTPException(status_code=401, detail="Refresh token không hợp lệ, đã hết hạn, hoặc đã bị thu hồi")
    return result


@app.post("/auth/logout")
def logout(req: RefreshTokenRequest, current_user: CurrentUser = Depends(get_current_user)):
    revoke_refresh_token(req.refresh_token)
    # AUTH5-06 — immediately invalidate this user's current access token (and every older access
    # token), without waiting for natural expiry. Only truly effective on routes that check
    # is_access_token_revoked (require_otp_verified, approve/reject) — see the reasoning for that
    # deliberate scope in src/auth.py.
    set_revoked_before_now(current_user.user_id)
    return {"ok": True}


# ---------------------------------------------------------------------------
# /auth/otp/* — REAL session OTP in the backend (Brief §7 #4; AUTH5-01,
# 2026-08-12: no longer paired with a security question). BEFORE the original fix, OTP was only a
# simulated UI gate in the frontend (ChatClient.tsx) — the backend checked nothing, meaning a
# direct call to /tools/lookup_transaction with a valid JWT could still fetch sensitive data
# without OTP verification (a real finding while cross-checking the AUTH-* QA suite).
# `AuthSession` already existed in the data model — it now finally has real endpoints writing/
# reading it at runtime.
# ---------------------------------------------------------------------------

# AUTH5-05E (Auth Flow upgrade 2026-08-12) — the slowapi decorator below
# (10/minute) still keys purely by IP (it can't be switched to phone/user the same way as the
# login route, because slowapi's key_func can't await the body/current_user resolved via Depends)
# — a second layer keyed by the REAL user_id is added (current_user is available here, unlike
# /auth/login), blocking OTP brute force targeting one specific user even if an attacker keeps
# changing IPs.
_otp_request_user_limiter = RedisSlidingWindowLimiter(max_calls=10, window_seconds=60, name="otp_request")

# Concurrency limit for /agent/chat (ADR-012). The number 20 comes from REAL MEASUREMENT, not
# guesswork: 1 chat turn = ~15,136 tokens, OpenAI quota 200,000 TPM => ~13 turns/minute
# sustained. 20 slots allow short bursts (a chat turn lasts ~10-45s, so 20 slots does NOT mean 20
# turns/minute) while staying below the 429-storm threshold.
# ttl 90s = 2x AGENT_TURN_TIMEOUT_SECONDS (45s): a safety net reclaiming slots from processes that
# died midway, set LARGER than the timeout so it never steals a slot from a legitimately running
# turn. Tune via environment variables once real load-test numbers exist.
_AGENT_MAX_CONCURRENT = int(os.environ.get("AGENT_MAX_CONCURRENT", "20"))
# A DERIVED TTL, not hard-coded. Before 17/08 it was the constant `90`, with the relationship
# "2× AGENT_TURN_TIMEOUT" living only in a COMMENT — i.e. with no constraint at all.
# Raising `AGENT_TURN_TIMEOUT_SECONDS` to 90 (one of three options under consideration) would make
# the turn ceiling EQUAL the ttl ⟹ the reclaim net would STEAL SLOTS from legitimately running
# turns — exactly what that comment was written to prevent, and it fails SILENTLY: over-admission
# with no log complaining, precisely when the limiter is the only thing keeping us under the 429
# threshold.
_AGENT_LIMITER_TTL_FACTOR = 2
_agent_turn_limiter = RedisConcurrencyLimiter(
    max_concurrent=_AGENT_MAX_CONCURRENT,
    ttl_seconds=int(AGENT_TURN_TIMEOUT_SECONDS * _AGENT_LIMITER_TTL_FACTOR),
    name="agent_turn",
)


@app.post("/auth/otp/request")
@limiter.limit("10/minute")
def request_otp(
    request: Request,
    current_user: CurrentUser = Depends(require_role("customer")),
    session: Session = Depends(get_session),
):
    if not _otp_request_user_limiter.allow(current_user.user_id):
        raise HTTPException(status_code=429, detail="Quá nhiều lần xin mã OTP, thử lại sau")
    user = session.get(User, current_user.user_id)
    otp_code = f"{random.randint(0, 999999):06d}"
    otp_session_id = new_id("SES")
    session.add(
        AuthSession(
            session_id=otp_session_id,
            user_id=current_user.user_id,
            otp_code=otp_code,
            otp_status="pending",
            security_q_passed=False,
            failed_attempts=0,
            created_at=dt.datetime.utcnow(),
        )
    )
    # EU/US benchmark 27/08, Finding #2 — otp_code ONLY goes into the response when OTP_DEMO_MODE
    # is enabled manually (OFF by default, fail-fast if enabled together with production —
    # see src/config.py). There is no real SMS-sending branch: this is a gate against LEAKAGE, not
    # an
    # implementation of a real delivery channel — real production must have its own SMS provider
    # before running with OTP_DEMO_MODE=false and still working.
    response: dict[str, object] = {
        "session_id": otp_session_id,
        "security_question": user.security_question,  # only helps CSKH identify callers on the hotline, does NOT gate OTP verify
    }
    if OTP_DEMO_MODE:
        response["otp_code"] = otp_code
        response["note"] = (
            "Môi trường demo — mã OTP trả trực tiếp ở đây để tiện test/tự động hoá "
            "(sản phẩm thật sẽ gửi qua SMS, KHÔNG BAO GIỜ trả OTP qua API response)."
        )
    return response


@app.post("/auth/otp/verify")
@limiter.limit("10/minute")
def verify_otp(
    request: Request,
    req: OtpVerifyRequest,
    current_user: CurrentUser = Depends(require_role("customer")),
    session: Session = Depends(get_session),
):
    # Looked up directly by session_id (primary key) — NO longer "the user's latest
    # AuthSession" (race-condition fix 2026-08-13, see the OtpVerifyRequest docstring).
    # auth_session.user_id != current_user.user_id means someone is trying to verify an OTP session
    # that ISN'T THEIR OWN — treated as non-existent, without revealing whether that session is
    # real.
    auth_session = session.get(AuthSession, req.session_id)
    if auth_session is not None and auth_session.user_id != current_user.user_id:
        auth_session = None
    if auth_session is None:
        raise HTTPException(status_code=400, detail="Chưa yêu cầu OTP — gọi /auth/otp/request trước")
    if auth_session.locked_at is not None:
        raise HTTPException(
            status_code=403, detail="Phiên xác thực đã bị khoá do sai quá nhiều lần — yêu cầu OTP mới"
        )

    # AUTH5-01 (Auth Flow upgrade, 2026-08-12, NIST SP 800-63B-4) — security questions (KBA) are
    # NO longer used as an authenticator, not even combined with OTP — attackers can easily find the
    # answers through data breaches/social media. The OTP code is the ONLY step-up factor here.
    # `User.security_question`/`security_answer_hash` are STILL kept in the model, only to help CSKH
    # identify customers calling the hotline (gating no route at all).
    # EU/US benchmark 27/08, Finding #3 — the same control family as
    # approve_resolution (main.py, Layer 3 above): compare OTPs in constant time,
    # not with `==` (which leaks the length of the correct prefix through response timing).
    otp_ok = secrets.compare_digest(req.otp_code or "", auth_session.otp_code or "")

    if not otp_ok:
        auth_session.failed_attempts += 1
        # commit() HERE, BEFORE raising — get_session() (src/api/deps.py) rolls back on any
        # exception
        # leaving the route, including deliberately raised HTTPExceptions. Without this commit() the
        # freshly incremented failed_attempts is ROLLED BACK every time, and the lock after N
        # failures
        # NEVER actually happens over real HTTP — a real finding while testing manually through the
        # UI
        # (many consecutive wrong entries never locked), even though automated tests had passed
        # WRONGLY
        # because the test fixture shared one Session that doesn't go through commit/rollback like
        # the
        # real get_session() (see test_otp.py).
        if auth_session.failed_attempts >= OTP_MAX_FAILED_ATTEMPTS:
            auth_session.locked_at = dt.datetime.utcnow()
            session.commit()
            raise HTTPException(
                status_code=403,
                detail=f"Sai quá {OTP_MAX_FAILED_ATTEMPTS} lần — phiên xác thực đã bị khoá, yêu cầu OTP mới",
            )
        session.commit()
        # 🔴 400, NOT 401 (changed 27/08). 401 means "I don't know who you are" — but for someone who
        # mistyped the OTP we KNOW EXACTLY who they are: their login session is fully alive, they
        # just
        # mistyped six digits.
        # [MEASURED 27/08] every 401 in the backend: main.py 316/362/978/1140 + auth.py
        # 257/259/264/281/346 — 9/10 of them mean "the session is no longer usable".
        # This line used to be the ONLY EXCEPTION, and its cost showed up in the layer above:
        # the frontend has a rule "401 ⟹ session dead ⟹ kick to /login" that is right in 9/10
        # places,
        # so it had to MATCH THE STRING "Mã OTP không đúng" (incorrect OTP) just to exclude this ONE
        # line.
        # Real consequence (caught by the review 27/08): mistyping the OTP ⟹ losing a live session.
        # 400 matches this very route (which already uses 400 for "OTP not requested yet") — the
        # same
        # family "there's a problem with your request", completely different from "who are you".
        # ⚠️ 401 on this route STILL EXISTS, raised by require_role/auth BEFORE the function body
        # when
        # the session is really dead ⟹ the frontend's rule is now right WITHOUT EXCEPTION, even
        # here.
        # ⚠️ The two 403 branches (locked after too many failures) are NOT touched — they
        # distinguish
        # "mistyped" from "out of attempts", and tests/ has control cases asserting exactly that
        # boundary.
        raise HTTPException(status_code=400, detail="Mã OTP không đúng")

    auth_session.otp_status = "verified"
    auth_session.security_q_passed = True
    # utcfromtimestamp (NOT fromtimestamp — avoiding the server's timezone offset) to reconstruct
    # the original iat exactly, keeping the conversation thread_id (user_id:iat,
    # see src/agents/graph.py) unchanged mid-chat when issuing a new JWT.
    now = dt.datetime.utcnow()
    new_token = create_access_token(
        user_id=current_user.user_id,
        role=current_user.role,
        otp_verified_at=now,
        iat=dt.datetime.utcfromtimestamp(current_user.iat),
    )
    # NOTE (set_revoked_before_now is NOT called here, unlike logout) — the NEW token keeps the
    # ORIGINAL `iat` (mandatory, to keep the AI conversation thread_id, see
    # create_access_token) — is_access_token_revoked() compares `iat < revoked_before`;
    # bumping revoked_before=now here would make THE VERY TOKEN JUST ISSUED (with an iat older than
    # "now") count as revoked immediately, wrongly locking the session that just verified.
    # Caught at design time (not by trial and error) — revoked_before is only right for logout,
    # where
    # the NEXT login certainly has a newer `iat` (login() always sets iat=now).
    #
    # A new refresh token is minted alongside (a new family — sensible because this is an "upgrade"
    # of
    # the authentication level, not an ordinary rotation) so an otp_verified session can also
    # refresh
    # without asking for OTP again midway.
    new_refresh = mint_refresh_token(
        user_id=current_user.user_id,
        role=current_user.role,
        login_iat=current_user.iat,
        # calendar.timegm (not .timestamp()) — the same reason recorded in
        # login(): the later round trip through utcfromtimestamp() (rotate_refresh_token)
        # must match EXACTLY how PyJWT/create_access_token interpret it.
        otp_verified_at=calendar.timegm(now.utctimetuple()),
    )
    return {"access_token": new_token, "refresh_token": new_refresh, "otp_verified": True}


# ---------------------------------------------------------------------------
# /tools/* — called by the agent. Identity (user_id) always comes from the token, never from the
# body — closing the "declare any user_id to read/create data on someone else's behalf" hole.
# ---------------------------------------------------------------------------


@app.post("/tools/lookup_transaction")
def lookup_transaction(
    req: LookupTransactionRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    # require_otp_verified is NOT attached here (even though the agent path has it — see
    # customer_tools.py) — this route also serves CSKH/supervisors looking things up while handling
    # tickets (ALL_ROLES), and customers indirectly via the "Recent transactions" rail
    # (ChatClient.tsx) AS SOON AS they open the page, before they have a chance to verify OTP —
    # blocking here would break the UX of viewing basic information that existed before this work.
    # The REALLY sensitive actions (the agent actively investigating/creating tickets
    # mid-conversation)
    # are blocked in the right place — see create_ticket below and customer_tools.py.
    # C4/BOLA — tightened BY ROLE, not unconditionally: the contract lists this route as
    # `any_authenticated` with the note "who may see which data is enforced at the lower layer".
    # CSKH/supervisors MUST be able to look up any customer's transactions while handling tickets;
    # only `customer` is restricted to their own transactions.
    return _handle_tool_error(
        _lookup_transaction,
        session,
        requesting_user_id=current_user.user_id,
        only_callers_transactions=(current_user.role == "customer"),
        **req.model_dump(),
    )


@app.post("/tools/get_customer_history")
def get_customer_history(
    req: GetCustomerHistoryRequest,
    current_user: CurrentUser = Depends(require_role("customer")),
    session: Session = Depends(get_session),
):
    # Why require_otp_verified is not attached: see the comment on lookup_transaction.
    return _handle_tool_error(
        _get_customer_history, session, user_id=current_user.user_id, **req.model_dump()
    )


@app.post("/tools/create_ticket")
def create_ticket(
    req: CreateTicketRequest,
    current_user: CurrentUser = Depends(require_role("customer")),
    _otp: CurrentUser = Depends(require_otp_verified),
    session: Session = Depends(get_session),
):
    # fraud_signals are NOT passed by the caller — computed at the service layer (§4.1
    # FIN05-Backend-Handoff.md) from DB data, so the agent can't fabricate/forget signals.
    return _handle_tool_error(
        create_ticket_with_fraud_check, session, user_id=current_user.user_id, **req.model_dump()
    )


@app.post("/tools/propose_resolution")
def propose_resolution(
    req: ProposeResolutionRequest,
    current_user: CurrentUser = Depends(require_role("cskh", "supervisor")),
    # ADR-055 Tier 1 (fixed by the PO 30/08) — touches investigation data but needs NO OTP, so it
    # previously fell outside require_otp_verified (see the require_unrevoked_token docstring). A
    # separate Depends, declared AFTER require_role — keeping the error order 403 (wrong role)
    # before
    # 401 (token revoked).
    _revoked: CurrentUser = Depends(require_unrevoked_token),
    session: Session = Depends(get_session),
):
    # ADR-064(b) (04/09) — ticket_id comes from the BODY (not the path) but the same rule applies:
    # CSKH can't propose a resolution for a ticket someone else is handling. The Ticket is looked up
    # BEFORE calling the service — the service looks it up again by ticket_id (its behaviour is
    # unchanged); this only adds one authorisation layer.
    ticket = session.get(Ticket, req.ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="ticket không tồn tại")
    if _agent_blocked_by_claim(current_user, ticket):
        raise HTTPException(status_code=404, detail="ticket không tồn tại")
    return _handle_tool_error(
        _propose_resolution, session, created_by=current_user.user_id, **req.model_dump()
    )


@app.post("/tools/escalate_ticket")
def escalate_ticket(
    req: EscalateTicketRequest,
    current_user: CurrentUser = Depends(require_role("cskh", "supervisor")),
    # ADR-055 Tier 1 (fixed by the PO 30/08) — see the comment on propose_resolution.
    _revoked: CurrentUser = Depends(require_unrevoked_token),
    session: Session = Depends(get_session),
):
    # ADR-064(b) (04/09) — the same reason as propose_resolution just above. Does NOT touch the AI's
    # AUTOMATIC escalation path (fraud_policy/FS-06 runs inside create_ticket, a completely
    # different
    # code path) — this route ONLY serves cskh/supervisors escalating manually, exactly ADR-064's
    # target.
    ticket = session.get(Ticket, req.ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="ticket không tồn tại")
    if _agent_blocked_by_claim(current_user, ticket):
        raise HTTPException(status_code=404, detail="ticket không tồn tại")
    return _handle_tool_error(
        _escalate_ticket, session, created_by=current_user.user_id, **req.model_dump()
    )


# ---------------------------------------------------------------------------
# /agent/chat — the real AI agent (LangGraph, src/agents/), replacing the old scripted flow in the
# frontend. Only serves role=customer — the agent isn't used by CSKH/supervisors, who act directly
# through the web app (not via chat).
# ---------------------------------------------------------------------------


@app.post("/agent/chat")
@limiter.limit("20/minute")
def agent_chat(
    request: Request,
    req: AgentChatRequest,
    current_user: CurrentUser = Depends(require_role("customer")),
    session: Session = Depends(get_session),
):
    # CONCURRENCY limiting (2026-08-13) — different from the rate limit above: `20/minute` can't
    # stop
    # 150 people pressing send within 1 second (each calls only once).
    # Without this layer, 150 agent turns running at once would exhaust Starlette's 40-thread
    # threadpool AND hit OpenAI simultaneously, getting a 429 storm for exceeding
    # 200,000 TPM (measured: ~15,136 tokens/turn => a ceiling of ~13 turns/minute).
    # Reject IMMEDIATELY with a clear message, NO queueing — holding requests waiting inside one
    # worker is exactly what causes cascading congestion. See ADR-012.
    slot = _agent_turn_limiter.acquire()
    if slot is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Hệ thống đang xử lý nhiều yêu cầu cùng lúc, bạn vui lòng thử lại "
                "sau khoảng 30 giây giúp mình nhé."
            ),
            headers={"Retry-After": "30"},
        )
    try:
        # thread_id is bound to the LOGIN session (user_id + iat at login), not just user_id — the
        # checkpointer (src/agents/graph.py) uses one instance for the whole process lifetime; keyed
        # only
        # by user_id, logging out and back in (same process, not restarted) would continue the old
        # session's conversation, contradicting PRD US-010 ("no context kept across different login
        # sessions").
        result = _handle_tool_error(
            run_agent_turn,
            session,
            user_id=current_user.user_id,
            message=req.message,
            thread_id=f"{current_user.user_id}:{current_user.iat}",
            otp_verified_at=current_user.otp_verified_at,
            vua_xac_thuc_de_gui_lai=req.vua_xac_thuc_de_gui_lai,
        )
        # Block `null` AT THE client BOUNDARY, without changing the meaning INSIDE: an internal
        # `None`
        # (e.g. graph.py, the tool-loop/timeout path) means "result lost", unlike `[]` = "genuinely
        # no
        # tool called" — that distinction is valuable for logs/checkpoints but NOT for the client
        # (the
        # client can't do anything different with "unknown", and `ly_do_fallback` already tells it
        # this
        # was a failed turn). `ChatClient.tsx` calls `.length` on this field — without the line
        # below,
        # `null` goes straight into the JSON and breaks there.
        # DELIBERATELY fixed HERE (the agent_chat route), NOT in `_handle_tool_error` — that
        # function is
        # shared by more than a dozen other routes, most without a `tool_calls` key; inserting it
        # there
        # would wrongly add the field to unrelated routes' responses.
        result["tool_calls"] = result.get("tool_calls") or []
        return result
    finally:
        # finally is MANDATORY: leaving via an exception (timeout, ToolError, 500) without releasing
        # the
        # slot makes the system strangle itself after a few errors.
        _agent_turn_limiter.release(slot)


# ---------------------------------------------------------------------------
# /tickets* — reads for the CSKH/supervisor UI. Not data customers view directly (customers follow
# up via /agent/chat), so limited to the 2 internal roles.
# ---------------------------------------------------------------------------


_TICKET_PAGE_SIZES = (30, 50, 100)


@app.get("/tickets")
def list_tickets(
    hitl_status: str | None = None,
    # [polish before filming 04/09] AND filtering — several criteria can be combined; any
    # parameter left empty doesn't filter on that criterion.
    complaint_type: str | None = None,
    scope: str | None = None,
    priority: str | None = None,
    # SLA "time remaining" — 2 SELECTABLE bounds, no buckets hard-coded in the backend (e.g.
    # "overdue"/"<24h left"): the frontend computes the bounds from the current time and passes
    # `sla_before`/`sla_after`; the backend simply compares `Ticket.sla_due_at` directly — one pair
    # of parameters serves any bucket the UI wants to draw, with no backend change whenever bucket
    # definitions change.
    sla_before: dt.datetime | None = None,
    sla_after: dt.datetime | None = None,
    # The old `limit` is replaced with real pagination — 660+ tickets loaded at once is why the PO
    # requested this polish round. `page_size` ONLY accepts one of the 3 values the PO fixed, not
    # free
    # input — so the FE can't send an arbitrary number pulling the whole table.
    page: int = 1,
    page_size: int = 50,
    current_user: CurrentUser = Depends(require_role("cskh", "supervisor")),
    session: Session = Depends(get_session),
):
    if page < 1:
        raise HTTPException(status_code=422, detail="page phải >= 1")
    if page_size not in _TICKET_PAGE_SIZES:
        raise HTTPException(
            status_code=422,
            detail=f"page_size phải là 1 trong {list(_TICKET_PAGE_SIZES)}",
        )

    # A real JOIN (not a join in Python as before) — filtering by
    # complaint_type/scope/priority needs WHERE at the SQL layer for COUNT/OFFSET to be right;
    # joining after selecting Tickets (the old way) couldn't filter.
    stmt = select(Ticket).join(Complaint, Ticket.complaint_id == Complaint.complaint_id, isouter=True)
    if hitl_status:
        stmt = stmt.where(Ticket.hitl_status == hitl_status)
    if complaint_type:
        stmt = stmt.where(Complaint.type == complaint_type)
    if scope:
        stmt = stmt.where(Complaint.scope == scope)
    if priority:
        stmt = stmt.where(Complaint.priority == priority)
    if sla_before:
        stmt = stmt.where(Ticket.sla_due_at <= sla_before)
    if sla_after:
        stmt = stmt.where(Ticket.sla_due_at >= sla_after)
    # ADR-064(b) — row-level scoping (routes/roles unchanged). CSKH only see UNCLAIMED tickets
    # (the shared pool) + their OWN tickets. Supervisors are NOT filtered —
    # keeping their existing rights; supervisors don't claim, they only manage/approve.
    if current_user.role == "cskh":
        stmt = stmt.where(or_(Ticket.claimed_by.is_(None), Ticket.claimed_by == current_user.user_id))

    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    tickets = session.scalars(
        stmt.order_by(Ticket.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    # The CSKH dashboard needs type/scope/priority/fraud signals right in the table
    # (US-011, US-014) — one join via complaint_id instead of N+1 requests.
    complaints = {
        c.complaint_id: c
        for c in session.scalars(
            select(Complaint).where(Complaint.complaint_id.in_([t.complaint_id for t in tickets]))
        ).all()
    }
    users = {
        u.user_id: u
        for u in session.scalars(
            select(User).where(User.user_id.in_([c.user_id for c in complaints.values()]))
        ).all()
    }
    out = []
    for t in tickets:
        c = complaints.get(t.complaint_id)
        u = users.get(c.user_id) if c else None
        out.append(
            {
                "ticket_id": t.ticket_id,
                "complaint_id": t.complaint_id,
                "hitl_status": t.hitl_status,
                "sla_due_at": t.sla_due_at.isoformat(),
                "partner_wait_status": t.partner_wait_status,
                "created_at": t.created_at.isoformat(),
                "complaint_type": c.type if c else None,
                "scope": c.scope if c else None,
                "priority": c.priority if c else None,
                "fraud_signals": c.fraud_signals if c else [],
                "customer_name": u.full_name if u else None,
                "human_handoff_requested": t.human_handoff_requested,
                # ADR-064(b) — the frontend needs this to decide whether to show the "Claim ticket"
                # button:
                # null = pool (button shown), a value = already claimed
                # (for cskh the backend already filtered above, so "a value" is ALWAYS
                # THEMSELVES; for supervisors the route doesn't filter, so it may be SOMEONE ELSE
                # — supervisors have no claim button, it is display only).
                "claimed_by": t.claimed_by,
            }
        )
    return {"items": out, "total": total, "page": page, "page_size": page_size}


@app.get("/tickets/{ticket_id}")
def get_ticket_detail(
    ticket_id: str,
    current_user: CurrentUser = Depends(require_role("cskh", "supervisor")),
    session: Session = Depends(get_session),
):
    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="ticket không tồn tại")
    # ADR-064(b) (04/09, a real hole caught by the review) — the SAME row-level scoping rule as
    # GET /tickets and the transcript. The real exploitation path: notify_new_ticket
    # (ADR-063) fans the ticket_id out to EVERY cskh agent the moment a ticket is created, before
    # anyone claims it — every CSKH agent has a valid ticket_id via their own GET /notifications,
    # and
    # THIS route (UNLIKE list/transcript) returns full detail:
    # description_raw (often containing third-party PII), fraud_signals, ALL
    # resolutions (amounts/rationale), ALL investigation_logs — far heavier than the transcript.
    # 404 (not 403) — the same anti-enumeration pattern.
    if _agent_blocked_by_claim(current_user, ticket):
        raise HTTPException(status_code=404, detail="ticket không tồn tại")
    complaint = session.get(Complaint, ticket.complaint_id)
    resolutions = session.scalars(
        select(Resolution).where(Resolution.ticket_id == ticket_id).order_by(Resolution.created_at)
    ).all()
    escalations = session.scalars(
        select(Escalation).where(Escalation.ticket_id == ticket_id).order_by(Escalation.created_at)
    ).all()
    logs = session.scalars(
        select(InvestigationLog)
        .where(InvestigationLog.ticket_id == ticket_id)
        .order_by(InvestigationLog.step_no)
    ).all()
    return {
        "ticket": {
            "ticket_id": ticket.ticket_id,
            "hitl_status": ticket.hitl_status,
            "sla_due_at": ticket.sla_due_at.isoformat(),
            "partner_wait_status": ticket.partner_wait_status,
            "human_handoff_requested": ticket.human_handoff_requested,
        },
        "complaint": {
            "complaint_id": complaint.complaint_id,
            "user_id": complaint.user_id,
            "trans_id": complaint.trans_id,
            "type": complaint.type,
            "scope": complaint.scope,
            "priority": complaint.priority,
            "description_raw": complaint.description_raw,
            "fraud_signals": complaint.fraud_signals,
        }
        if complaint
        else None,
        # M-02 (ADR-019) — returns the full audit trail for BOTH branches. This route is already
        # gated
        # with `require_role("cskh","supervisor")` in its signature, so this is a STAFF path;
        # customers
        # have no route reading resolutions (checked by the authz matrix test). Anyone adding a
        # customer
        # route reading tickets later MUST filter on their own — don't reuse this dict block as is.
        "resolutions": [
            {
                "resolution_id": r.resolution_id,
                "action_type": r.action_type,
                "amount": r.amount,
                "status": r.status,
                "rationale": r.rationale,
                "approved_by": r.approved_by,
                "approved_at": r.approved_at.isoformat() if r.approved_at else None,
                "rejected_by": r.rejected_by,
                "rejected_at": r.rejected_at.isoformat() if r.rejected_at else None,
                "reject_reason": r.reject_reason,
                # ADR-024 — this route is DELIBERATELY gated to cskh/supervisor in its signature
                # (see the M-02 block docstring above): exactly the "staff route" where test_11
                # requires the note
                # to appear. No customer-callable route reuses this dict block.
                "note": r.note,
                "note_flagged": r.note_flagged,
            }
            for r in resolutions
        ],
        "escalations": [
            {"escalation_id": e.escalation_id, "target": e.target, "reason": e.reason}
            for e in escalations
        ],
        "investigation_logs": [
            {
                "step_no": log.step_no,
                "tool_called": log.tool_called,
                "tool_input": log.tool_input_json,
                "tool_result_id": log.tool_result_id,
                "tool_result": session.get(ToolResult, log.tool_result_id).raw_json
                if log.tool_result_id
                else None,
                "agent_note": log.agent_note,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
    }


# ---------------------------------------------------------------------------
# ADR-044 (approved directly by the real PO 19/08) — CSKH read the bot↔customer conversation of a
# ticket they handle once the customer has handed over to a human. The rate limit reuses the
# existing @limiter.limit from /agent/chat; auditing is automatic via the _access_logger
# middleware — NO new infrastructure, exactly ADR-044 item 6.
# ---------------------------------------------------------------------------
@app.get("/tickets/{ticket_id}/transcript")
# 5/minute, NOT 20/minute like /agent/chat (caught by Security 20/08 — the UNIT was wrong, not
# the number, when the threshold was copied while writing the route). 20/minute is calibrated
# for a customer's TYPING speed; this route answers a different question: how fast CSKH can
# READ+PROCESS a full conversation. Reading to understand one conversation takes at least ~30
# seconds ⟹ 5/minute is still enough for quick skimming. The purpose is to stop high-speed
# exfiltration through leaked CSKH credentials (~1,200 transcripts/hour at the old threshold), not
# to stop ID probing. No legitimate scenario needs to open many transcripts in rapid succession —
# approving resolutions is inherently one at a time via OTP step-up, and backlog review uses
# GET /tickets (listing), not opening full transcripts.
@limiter.limit("5/minute")
def get_ticket_transcript(
    request: Request,
    ticket_id: str,
    current_user: CurrentUser = Depends(require_role("cskh", "supervisor")),
    session: Session = Depends(get_session),
):
    # 🔴 THE MAIN GUARD (ADR-044 item 3, wording fixed by Security) — the route ONLY accepts
    # `ticket_id` via the path. There is NO `thread_id` parameter in this function's signature in
    # any
    # form (query/body/header) — `thread_id` is derived SOLELY from `complaint.thread_id` read from
    # the DB just below. Don't add a `thread_id` parameter to this route even "for debugging
    # convenience" — that is exactly how the route would silently become "read a raw thread_id",
    # which ADR-044 forbids.
    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="ticket không tồn tại")
    # ADR-064(b) (04/09) — CHANGED from the original ADR-044: this route now applies the SAME
    # row-level scoping rule as GET /tickets. cskh can only read transcripts of UNCLAIMED tickets
    # (the pool — any on-shift CSKH agent can still pick up a handoff) OR tickets claimed_by
    # THEMSELVES. 404 (NOT 403) for tickets claimed by someone else — the same anti-enumeration
    # pattern used for notifications (not revealing existence through different status codes).
    # Supervisors are NOT filtered, as before.
    if _agent_blocked_by_claim(current_user, ticket):
        raise HTTPException(status_code=404, detail="ticket không tồn tại")
    complaint = session.get(Complaint, ticket.complaint_id)
    if complaint is None:
        # Should never happen (FK complaint_id NOT NULL) — 404 so as not to reveal a behavioural
        # difference from the "ticket doesn't exist" case above (the same class of bug: probing
        # which
        # tickets exist via status codes).
        raise HTTPException(status_code=404, detail="ticket không tồn tại")
    # "user_id matches" is NOT this route's OWN authorisation boundary
    # (ADR-044 item 3) — the real boundary is now the claimed_by rule above
    # (ADR-064(b)), applied IN COMMON with GET /tickets, not a separate mechanism for transcripts.

    handoff_at = ticket.handoff_at.isoformat() if ticket.handoff_at else None

    if complaint.thread_id is None:
        return {
            "transcript": None,
            "ly_do": (
                "Vé này được tạo TRƯỚC khi hệ thống ghi thread_id (ADR-044) — "
                "không có cách nào xác định chắc chắn phiên hội thoại nào đã "
                "sinh ra vé này, nên không hiện transcript thay vì đoán theo "
                "mốc thời gian gần nhất."
            ),
            "handoff_at": handoff_at,
        }

    outcome = read_handoff_transcript(complaint.thread_id)
    if outcome is None:
        return {
            "transcript": None,
            "ly_do": (
                "Vé có thread_id nhưng không tìm thấy checkpoint hội thoại "
                "tương ứng — có thể phiên chat đã bị dọn khỏi bộ nhớ checkpoint "
                "hoặc lỗi ghi lúc tạo vé."
            ),
            "handoff_at": handoff_at,
            "chi_so_bang_giao": None,
        }
    return {
        "transcript": outcome["luot"],
        "ly_do": None,
        "handoff_at": handoff_at,
        # ADR-044 — the (0-based) position of the LAST turn "above the line", derived from the real
        # request_human_handoff tool call in the conversation (NOT comparing timestamps — there is
        # no
        # per-message timestamp to compare with handoff_at).
        "chi_so_bang_giao": outcome["chi_so_bang_giao"],
    }


# ---------------------------------------------------------------------------
# ADR-064(b) (04/09, approved by the real PO) — CSKH "claim a ticket" EXPLICITLY, not
# automatically. Matches the existing "Open & claim" pattern in the live-chat dashboard
# (ChatSession's claim-based routing, see src/db/models.py:504-508) — the same philosophy,
# extended to Ticket.
# ---------------------------------------------------------------------------
@app.post("/tickets/{ticket_id}/claim")
def claim_ticket(
    ticket_id: str,
    current_user: CurrentUser = Depends(require_role("cskh")),
    session: Session = Depends(get_session),
):
    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="ticket không tồn tại")
    if ticket.claimed_by is not None and ticket.claimed_by != current_user.user_id:
        # 409, NOT 404/403 — unlike BOLA on GET (hiding existence), here CSKH ARE acting on a ticket
        # they just saw in the pool (or an old URL opened before someone else claimed it) — they
        # need to
        # know CLEARLY why they "can't claim" it (already claimed) so the UI says the right thing,
        # not a
        # vague 404.
        raise HTTPException(status_code=409, detail="ticket đã được CSKH khác nhận")
    if ticket.claimed_by == current_user.user_id:
        # Idempotent — clicking "Claim ticket" again on a ticket you already claimed is not an
        # error,
        # and doesn't overwrite claimed_at (keeping the FIRST claim time).
        return {"ticket_id": ticket.ticket_id, "claimed_by": ticket.claimed_by, "claimed_at": ticket.claimed_at.isoformat()}
    ticket.claimed_by = current_user.user_id
    ticket.claimed_at = dt.datetime.utcnow()
    session.commit()
    return {"ticket_id": ticket.ticket_id, "claimed_by": ticket.claimed_by, "claimed_at": ticket.claimed_at.isoformat()}


# ---------------------------------------------------------------------------
# HITL gate — callable ONLY by a supervisor. The ONLY path writing status='approved'.
# approved_by/rejected_by are now ALWAYS current_user.user_id (authenticated via
# JWT) — previously the client declared approved_by, meaning anyone could "approve" as long as
# they guessed the user_id of some supervisor. This was the 2nd most serious vulnerability fixed,
# in the same group as /agent/chat.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# AUTH5-04/05/05B (Auth Flow upgrade, 2026-08-12, PSD2 dynamic linking):
# approving a resolution is the financial action with the most real impact in the system;
# previously it was only role-gated — now it needs a DEDICATED OTP for EXACTLY the resolution_id
# being approved, bound to the amount at the moment the OTP was requested (changing the amount
# afterwards forces a new request). Reuses AuthSession (newly added resolution_id/amount_snapshot)
# instead of a separate table — see the model docstring.
# ---------------------------------------------------------------------------


@app.post("/resolutions/{resolution_id}/request-approval-otp")
@limiter.limit("10/minute")
def request_resolution_approval_otp(
    request: Request,
    resolution_id: str,
    current_user: CurrentUser = Depends(require_role("supervisor")),
    # ADR-055 Tier 1 (fixed by the PO 30/08) — the same MONEY-TOUCHING route family as approve/
    # reject (which already check revocation inline themselves), but this OTP-REQUEST route
    # previously didn't check — a revoked supervisor could still request a challenge even though
    # they
    # couldn't complete the approval. See the comment on propose_resolution.
    _revoked: CurrentUser = Depends(require_unrevoked_token),
    session: Session = Depends(get_session),
):
    resolution = session.get(Resolution, resolution_id)
    if resolution is None:
        raise HTTPException(status_code=404, detail="resolution không tồn tại")

    otp_code = f"{random.randint(0, 999999):06d}"
    otp_session_id = new_id("SES")
    session.add(
        AuthSession(
            session_id=otp_session_id,
            user_id=current_user.user_id,
            resolution_id=resolution_id,
            amount_snapshot=resolution.amount,
            otp_code=otp_code,
            otp_status="pending",
            security_q_passed=False,
            failed_attempts=0,
            created_at=dt.datetime.utcnow(),
        )
    )
    # EU/US benchmark 27/08, Finding #2 (extended 30/08 — the FINANCIAL approval route leaked
    # exactly like the login route, not just /auth/otp/request). The same OTP_DEMO_MODE gate, the
    # same reason — see the comment in request_otp().
    response: dict[str, object] = {
        "session_id": otp_session_id,
        "resolution_id": resolution_id,
    }
    if OTP_DEMO_MODE:
        response["otp_code"] = otp_code
        response["note"] = (
            "Môi trường demo — mã OTP trả trực tiếp ở đây để tiện test/tự động hoá "
            "(sản phẩm thật sẽ gửi qua SMS/app riêng cho sếp). Mã CHỈ dùng được cho "
            f"ĐÚNG resolution_id={resolution_id} này, hết hạn sau "
            f"{RESOLUTION_APPROVAL_OTP_FRESH_MINUTES} phút, và mất hiệu lực nếu số tiền "
            "resolution thay đổi sau khi xin mã."
        )
    return response


@app.post("/resolutions/{resolution_id}/approve")
def approve_resolution(
    resolution_id: str,
    req: ApproveResolutionRequest,
    current_user: CurrentUser = Depends(require_role("supervisor")),
    session: Session = Depends(get_session),
):
    # AUTH5-06 — a REAL financial approval is one of the FEW routes that deliberately pay for one
    # Redis GET per request to check revocation (see the rationale in
    # src/auth.py::require_otp_verified) — not applied via the shared require_role (which would
    # affect
    # EVERY other route); called directly here.
    if is_access_token_revoked(current_user.user_id, current_user.iat):
        raise HTTPException(status_code=401, detail="Phiên đã bị thu hồi — đăng nhập lại")
    resolution = session.get(Resolution, resolution_id)
    if resolution is None:
        raise HTTPException(status_code=404, detail="resolution không tồn tại")
    # SEC-B — ONLY `pending_approval`. The contract: `pending_approval → approved` is the
    # ONLY DOOR to approved (ADR-002). Allowing `draft` would open a shortcut skipping the
    # submission step; allowing `rejected` would overturn a rejection someone has already taken
    # responsibility for. Neither exists in the contract.
    if resolution.status != "pending_approval":
        raise HTTPException(
            status_code=400, detail=f"resolution đang ở trạng thái {resolution.status}, không duyệt được"
        )

    # AUTH5-05 — look up EXACTLY the challenge just requested (by session_id, the primary key —
    # race-condition fix 2026-08-13, same reason as /auth/otp/verify), NO longer the user's/
    # resolution's "latest" challenge (ambiguous under real concurrent load, and it once allowed an
    # OTP requested for case A to approve case B).
    # F-12 — SEPARATE "challenge not found" from "wrong code". The old version merged all 4
    # conditions (including `otp_code != req.otp_code`) into ONE check returning a generic 403,
    # so nowhere counted wrong attempts: brute-forcing a 6-digit code for a MONEY-TOUCHING action
    # was unlimited. The three layers below must stay in EXACTLY this order.
    auth_session = session.get(AuthSession, req.session_id)

    # Layer 1 — IDENTITY BINDING. Nothing is counted here: for someone else's challenge we must not
    # touch their counter (otherwise an attacker sending random session_ids of other supervisors
    # could
    # lock their accounts — DoS via the counter). A single generic message is kept so as not to
    # reveal
    # which sessions are real or which are bound to the right resolution.
    if (
        auth_session is None
        or auth_session.user_id != current_user.user_id
        or auth_session.resolution_id != resolution_id
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "Cần xác thực OTP riêng cho resolution này trước khi duyệt "
                "(POST /resolutions/{id}/request-approval-otp rồi truyền otp_code vào approve)"
            ),
        )

    # Layer 2 — ALREADY LOCKED is blocked BEFORE comparing the code. Placing it after the comparison
    # would be pointless: someone who brute-forced the right code could still approve, i.e. the lock
    # would protect nothing. The lock does NOT reopen over time — approving requires requesting a
    # new
    # challenge (each challenge is hard-bound to 1 resolution + 1 amount snapshot, so requesting a
    # new
    # one is no bypass: it rebuilds the entire dynamic-linking binding of AUTH5-05B).
    if auth_session.locked_at is not None:
        raise HTTPException(
            status_code=403,
            detail="Challenge duyệt đã bị khoá do sai quá nhiều lần — xin mã duyệt mới",
        )

    # Layer 3 — compare the code with a CONSTANT-TIME function. `!=` exits at the first mismatched
    # character, leaking the length of the correct prefix through response timing; with only 6
    # digits
    # the difference is small, but this is a money-touching path and the fix costs nothing.
    if not secrets.compare_digest(auth_session.otp_code or "", req.otp_code or ""):
        auth_session.failed_attempts += 1
        if auth_session.failed_attempts >= OTP_MAX_FAILED_ATTEMPTS:
            auth_session.locked_at = dt.datetime.utcnow()
        # commit() BEFORE raising — get_session() (src/api/deps.py) rolls back on every exception
        # leaving the route, including HTTPExceptions we raise deliberately.
        # Without this line the freshly incremented failed_attempts is rolled back every time and
        # the lock
        # NEVER happens over real HTTP — exactly the trap that already sprang once at
        # /auth/otp/verify
        # (see the comment on that route), repeated identically here.
        session.commit()
        if auth_session.locked_at is not None:
            raise HTTPException(
                status_code=403,
                detail=f"Sai quá {OTP_MAX_FAILED_ATTEMPTS} lần — challenge duyệt đã bị khoá, xin mã mới",
            )
        # 403 is KEPT (not changed to 401 as at /auth/otp/verify). Changing the status code is an
        # API
        # BEHAVIOUR change, outside the scope of F-12 — this fix only adds COUNTING and LOCKING. The
        # two
        # situations remain distinguishable via `detail`.
        # A separate proposal for the PO/tester (not done): unify 401="wrong code",
        # 403="locked" across both authentication routes, which needs updating the tests currently
        # hard-coding 403 (tests/ is outside my write zone).
        raise HTTPException(status_code=403, detail="Mã OTP duyệt không đúng")
    age_minutes = (dt.datetime.utcnow() - auth_session.created_at).total_seconds() / 60
    if age_minutes > RESOLUTION_APPROVAL_OTP_FRESH_MINUTES:
        raise HTTPException(status_code=403, detail="Mã OTP duyệt đã hết hạn — xin mã mới")
    # AUTH5-05B — dynamic linking: the amount must MATCH the snapshot taken when the OTP was
    # requested; changing the amount afterwards (CSKH editing the proposal) forces the supervisor to
    # request a new OTP for the new amount.
    if auth_session.amount_snapshot != resolution.amount:
        raise HTTPException(
            status_code=403,
            detail="Số tiền resolution đã thay đổi kể từ lúc xin OTP — xin mã mới cho đúng số tiền hiện tại",
        )

    # BR-12 maker-checker (ADR-020) — BLOCKED HERE, even though the DB already has the CHECK
    # ck_resolutions_maker_checker_br12. Not redundant defence: relying only on the CHECK, a
    # supervisor
    # approving their own proposal would get HTTP 500 with an IntegrityError — the user wouldn't
    # understand what happened, and the log would look like a broken system rather than a business
    # rule doing its job. The DB layer is the FINAL lock (blocking direct writes, scripts, sloppy
    # migrations too); this layer is the HUMAN-READABLE lock.
    #
    # This door is real: the proposal route allows both cskh AND supervisor, and the approval route
    # requires a supervisor — one supervisor could walk both ends.
    if resolution.created_by is not None and resolution.created_by == current_user.user_id:
        raise HTTPException(
            status_code=403,
            detail=(
                "Người đề xuất không được tự duyệt đề xuất của chính mình "
                "(maker-checker) — cần một supervisor khác duyệt"
            ),
        )

    resolution.status = "approved"
    resolution.approved_by = current_user.user_id
    resolution.approved_at = dt.datetime.utcnow()
    # CONSUME the challenge right after a successful approval — the approval OTP is a SINGLE-USE
    # code. Without marking it, the same session_id/otp_code could be reused during the remaining 10
    # minutes of validity: enough to flip another resolution to approved if another state hole
    # surfaced later, and it would destroy the meaning of "dynamic linking" (the code is bound to
    # EXACTLY one decision, not to a time window).
    auth_session.otp_status = "consumed"
    auth_session.otp_code = None
    _sync_hitl_status(session, resolution)
    # ADR-063 — notify BACK exactly the 1 CSKH agent who proposed it. `created_by` may be None
    # (resolutions created before ADR-020/BR-12) — if nobody can be notified, skip it; this is
    # legacy
    # data, not today's bug.
    if resolution.created_by is not None:
        notify_decided(
            session, ticket_id=resolution.ticket_id, cskh_user_id=resolution.created_by, approved=True
        )
    session.flush()
    return {"resolution_id": resolution_id, "status": resolution.status, "approved_by": current_user.user_id}


def _sync_hitl_status(session: Session, resolution: Resolution) -> None:
    """Fix for QA-02 — `Ticket.hitl_status` follows the ticket's LATEST resolution.

    Before the fix this column was stuck at `pending` forever: both the approve and reject
    branches only changed `resolution.status` without touching the ticket. Measured consequences:
    the CSKH queue filtering by `hitl_status` displayed wrongly, the two values `approved`/
    `rejected` in the CHECK constraint were never reachable, and the guard
    "ticket already in a final state" in /tickets/{id}/request-more-info could never fire.

    Runs IN THE SAME transaction as the resolution state change (no background job) — exactly
    `dan_xuat.quy_tac` (derivation rule) of contract v2.1.0. The two axes remain ORTHOGONAL
    rather than copies: `need_more_info` has no counterpart on the resolution side, so this
    function doesn't overwrite it, and a ticket with no resolution yet stays `pending`.
    """
    ticket = session.get(Ticket, resolution.ticket_id)
    if ticket is None:  # the FK already guards this; this branch only avoids blowing up if the data drifts
        return
    latest = session.scalars(
        select(Resolution)
        .where(Resolution.ticket_id == resolution.ticket_id)
        .order_by(Resolution.created_at.desc(), Resolution.resolution_id.desc())
        .limit(1)
    ).first()
    if latest is not None and latest.status in ("approved", "rejected"):
        ticket.hitl_status = latest.status
        ticket.updated_at = dt.datetime.utcnow()


@app.post("/resolutions/{resolution_id}/reject")
def reject_resolution(
    resolution_id: str,
    req: RejectResolutionRequest,
    current_user: CurrentUser = Depends(require_role("supervisor")),
    session: Session = Depends(get_session),
):
    """ADR-019 — a rejection MUST include a structured reason. NO OTP needed (rejecting doesn't
    touch money, per the contract), but all 3 audit fields are recorded symmetrically with the
    approval branch: who rejected, when, and why."""
    if is_access_token_revoked(current_user.user_id, current_user.iat):
        raise HTTPException(status_code=401, detail="Phiên đã bị thu hồi — đăng nhập lại")
    resolution = session.get(Resolution, resolution_id)
    if resolution is None:
        raise HTTPException(status_code=404, detail="resolution không tồn tại")
    # ONLY `pending_approval` — contract v2.1.0 lists exactly one transition to
    # `rejected`, with no path from `draft`. (My first version copied the state list from the
    # approval
    # branch and accidentally allowed draft too; the test the tester wrote FROM THE CONTRACT caught
    # it
    # — exactly why that role isn't allowed to read src/.)
    if resolution.status != "pending_approval":
        raise HTTPException(
            status_code=400,
            detail=f"resolution đang ở trạng thái {resolution.status}, không từ chối được",
        )

    # F-21 — SYMMETRIC with the guard of the same content in approve_resolution. After F-18 opened
    # CHECK ck_resolutions_maker_checker_br12 to cover `rejected_by` too, a supervisor rejecting
    # their
    # own proposal would violate the CHECK at the DB layer -> IntegrityError -> HTTP 500. The
    # argument
    # I wrote for the approval branch applies verbatim here: the user wouldn't understand what
    # happened, and the log would look like a broken system rather than a business rule doing its
    # job
    # CORRECTLY.
    #
    # NOT a vulnerability (the DB still blocks it; nobody can reject their own proposal) — an
    # operational bug: a 500 pollutes the logs and hides the very rule that is working correctly.
    # It isn't reachable today only because 10/10 old resolutions have created_by NULL; the door
    # opens
    # as soon as the first resolution created after F-17 exists.
    if resolution.created_by is not None and resolution.created_by == current_user.user_id:
        raise HTTPException(
            status_code=403,
            detail=(
                "Người đề xuất không được tự từ chối đề xuất của chính mình "
                "(maker-checker) — cần một supervisor khác xem xét"
            ),
        )

    # ADR-024 (TM-03 security sign-off) — PII scrubbed AT WRITE TIME, FAIL-CLOSED.
    # `note` is the ONLY place in the system where free text typed by STAFF goes into the same
    # record
    # as audit data. Scrub BEFORE any DB-writing transaction, and if the scrubbing itself fails
    # NEVER
    # write the raw version intending to mask it later — stop entirely, return 500, don't touch the
    # resolution.
    scrubbed_note: str | None = None
    note_flagged = False
    if req.note is not None:
        try:
            # Phase 4 (Security 19/08): purpose="log" — resolution.note is typed by staff and NEVER
            # sent to
            # the LLM; the existing fail-closed behaviour (ADR-024) is the originally chosen
            # maximally careful
            # design, kept in that direction.
            scrubbed_note = scrub_pii(req.note, purpose="log")
        except Exception as exc:  # noqa: BLE001 — fail-closed, regardless of the error type
            _logger.error("reject_note_scrub_that_bai", extra={"resolution_id": resolution_id})
            raise HTTPException(
                status_code=500,
                detail="Không xử lý được ghi chú — vui lòng thử lại",
            ) from exc
        # Reuses Rule 18 (ADR-023) — NO separate injection patterns written for note.
        # The flag is computed on the SCRUBBED content: that is what is actually stored and what
        # reviewers
        # actually read, not the raw version that has vanished from the system.
        note_flagged = bool(_classify_tier(scrubbed_note))

    resolution.status = "rejected"
    resolution.reject_reason = req.reason
    resolution.rejected_by = current_user.user_id
    resolution.rejected_at = dt.datetime.utcnow()
    resolution.note = scrubbed_note
    resolution.note_flagged = note_flagged
    _sync_hitl_status(session, resolution)
    # ADR-063 — symmetric with the approval branch.
    if resolution.created_by is not None:
        notify_decided(
            session, ticket_id=resolution.ticket_id, cskh_user_id=resolution.created_by, approved=False
        )
    session.flush()
    return {
        "resolution_id": resolution_id,
        "status": resolution.status,
        "reject_reason": resolution.reject_reason,
        "rejected_by": resolution.rejected_by,
    }


# ---------------------------------------------------------------------------
# /resolutions — the approval queue for supervisors
# ---------------------------------------------------------------------------


@app.get("/resolutions")
def list_resolutions(
    status: str | None = "pending_approval",
    limit: int = 50,
    current_user: CurrentUser = Depends(require_role("cskh", "supervisor")),
    session: Session = Depends(get_session),
):
    stmt = select(Resolution).order_by(Resolution.created_at.desc()).limit(limit)
    if status and status != "all":
        stmt = stmt.where(Resolution.status == status)
    resolutions = session.scalars(stmt).all()
    approvers = {
        u.user_id: u
        for u in session.scalars(
            select(User).where(User.user_id.in_([r.approved_by for r in resolutions if r.approved_by]))
        ).all()
    }
    out = []
    for r in resolutions:
        ticket = session.get(Ticket, r.ticket_id)
        # ADR-064(b) (04/09, caught by the review — a ROUNDABOUT path leaking the same data even
        # though
        # GET /tickets was locked) — CSKH skip resolutions of tickets someone else is handling
        # entirely,
        # NOT merely hiding sensitive fields: amount/rationale/destination_ref are exactly what
        # ADR-064
        # set out to hide.
        if ticket is not None and _agent_blocked_by_claim(current_user, ticket):
            continue
        complaint = session.get(Complaint, ticket.complaint_id) if ticket else None
        approver = approvers.get(r.approved_by) if r.approved_by else None
        out.append(
            {
                "resolution_id": r.resolution_id,
                "ticket_id": r.ticket_id,
                "action_type": r.action_type,
                "amount": r.amount,
                "destination_ref": r.destination_ref,
                "rationale": r.rationale,
                "cited_tool_result_ids": r.cited_tool_result_ids,
                "status": r.status,
                "created_at": r.created_at.isoformat(),
                "complaint_type": complaint.type if complaint else None,
                "scope": complaint.scope if complaint else None,
                "approved_by_name": approver.full_name if approver else None,
                "approved_at": r.approved_at.isoformat() if r.approved_at else None,
            }
        )
    return out


# ---------------------------------------------------------------------------
# /tickets/{id}/request-more-info — CSKH request further investigation (US-012).
# Not a HITL gate — never writes approved, only changes hitl_status.
# ---------------------------------------------------------------------------


@app.post("/tickets/{ticket_id}/request-more-info")
def request_more_info(
    ticket_id: str,
    req: RequestMoreInfoRequest,
    current_user: CurrentUser = Depends(require_role("cskh", "supervisor")),
    session: Session = Depends(get_session),
):
    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="ticket không tồn tại")
    # ADR-064(b) (04/09) — a WRITE action on a specific ticket, the same rule as the read routes:
    # CSKH can't act on tickets claimed by someone else.
    if _agent_blocked_by_claim(current_user, ticket):
        raise HTTPException(status_code=404, detail="ticket không tồn tại")
    # FIN05-StressTest-Plan-v4 S4-06 — a real finding: this route had NO state guard (unlike
    # approve_resolution/reject_resolution in the same file, which both block if the resolution is
    # already decided) — CSKH could accidentally call request-more-info again on a ticket ALREADY
    # approved/rejected, silently flipping it back to need_more_info, breaking the audit trail (a
    # "done" ticket showing "needs more info" again). Exactly the 2 terminal states are blocked.
    if ticket.hitl_status in ("approved", "rejected"):
        raise HTTPException(
            status_code=400,
            detail=f"Ticket đã ở trạng thái cuối ({ticket.hitl_status}) — không thể yêu cầu thêm thông tin",
        )

    now = dt.datetime.utcnow()
    ticket.hitl_status = "need_more_info"
    ticket.updated_at = now

    last_step = session.scalar(
        select(InvestigationLog.step_no)
        .where(InvestigationLog.ticket_id == ticket_id)
        .order_by(InvestigationLog.step_no.desc())
    )
    session.add(
        InvestigationLog(
            log_id=new_id("LOG"),
            ticket_id=ticket_id,
            step_no=(last_step or 0) + 1,
            tool_called="cskh_request_more_info",
            tool_input_json={"requested_by": current_user.user_id},
            agent_note=req.note,
            created_at=now,
        )
    )
    session.flush()
    return {"ticket_id": ticket_id, "hitl_status": ticket.hitl_status}


# ---------------------------------------------------------------------------
# /reports/summary — US-018, figures computed directly from the DB (PRD §12: no estimates)
# ---------------------------------------------------------------------------


@app.get("/reports/summary")
def report_summary(
    date_from: dt.datetime | None = None,
    date_to: dt.datetime | None = None,
    current_user: CurrentUser = Depends(require_role("cskh", "supervisor")),
    session: Session = Depends(get_session),
):
    return reporting.build_summary(session, date_from=date_from, date_to=date_to)


# ---------------------------------------------------------------------------
# /policy-docs* — policy/FAQ RAG (src/rag/). Upload/delete ONLY by role
# partner_admin (the e-wallet partner, separate from the internal supervisor) — this is the only
# actor allowed to bring new documents into the system that the agent/CSKH will trust, so
# permissions are stricter than the other /tools/* routes.
# ---------------------------------------------------------------------------


@app.post("/policy-docs")
@limiter.limit("20/hour")
def upload_policy_doc(
    request: Request,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(require_role("partner_admin")),
    session: Session = Depends(get_session),
):
    file_bytes = file.file.read()
    doc = _handle_tool_error(
        ingest_document,
        session,
        file_bytes=file_bytes,
        filename=file.filename or "untitled",
        uploaded_by=current_user.user_id,
        load_source="upload_api",
    )
    return {
        "doc_id": doc.doc_id,
        "filename": doc.filename,
        "status": doc.status,
        "chunk_count": doc.chunk_count,
        "error_message": doc.error_message,
    }


@app.get("/policy-docs")
def list_policy_docs(
    current_user: CurrentUser = Depends(require_role("partner_admin")),
    session: Session = Depends(get_session),
):
    docs = session.scalars(select(PolicyDocument).order_by(PolicyDocument.uploaded_at.desc())).all()
    uploaders = {
        u.user_id: u
        for u in session.scalars(select(User).where(User.user_id.in_([d.uploaded_by for d in docs]))).all()
    }
    return [
        {
            "doc_id": d.doc_id,
            "filename": d.filename,
            "uploaded_at": d.uploaded_at.isoformat(),
            "uploaded_by_name": uploaders[d.uploaded_by].full_name if d.uploaded_by in uploaders else None,
            "status": d.status,
            "chunk_count": d.chunk_count,
            "error_message": d.error_message,
        }
        for d in docs
    ]


@app.delete("/policy-docs/{doc_id}")
def delete_policy_doc(
    doc_id: str,
    current_user: CurrentUser = Depends(require_role("partner_admin")),
    session: Session = Depends(get_session),
):
    _handle_tool_error(_delete_policy_document, session, doc_id)
    return {"doc_id": doc_id, "status": "deleted"}


# ---------------------------------------------------------------------------
# /policy-search — a policy lookup tool dedicated to CSKH (pure retrieval, no LLM generating
# answers — see the design decision in the plan). Shares logic with the agent's search_policy tool
# (src/rag/search.py).
# ---------------------------------------------------------------------------


@app.post("/policy-search")
def policy_search(
    req: PolicySearchRequest,
    current_user: CurrentUser = Depends(require_role("cskh", "supervisor")),
    session: Session = Depends(get_session),
):
    # ADR-062 — Layer 1: the route LOOKS UP the scope itself from complaint_id, NEVER trusting a
    # client-declared `scope` (the client may only SAY which ticket it is looking up, not STATE the
    # scope itself). A `complaint_id` that doesn't exist/can't be looked up ⟹ treated as having
    # NO scope (no filtering) — NO error, the lookup flow isn't broken.
    # The role is already guarded by `require_role` above (cskh/supervisor only) — the same pattern
    # as
    # `get_ticket_detail` (main.py:774); that route also enforces no complaint ownership beyond the
    # role, since cskh/supervisor can see EVERY ticket anyway.
    scope = None
    if req.complaint_id is not None:
        complaint = session.get(Complaint, req.complaint_id)
        if complaint is not None:
            scope = complaint.scope
    return _handle_tool_error(
        search_policy_text, session, query=req.query, k=req.top_k, lookup_path="cskh", scope=scope
    )


# ---------------------------------------------------------------------------
# ADR-065 (05/09) — a deep link for reading the full text of a /policy-search result.
# ONLY returns status="indexed" documents ingested via /policy-docs — doc_id is looked up in the
# DB (not the filesystem), so there is no path-traversal route: unknown/not-yet-indexed/deleted
# doc_ids all return the same 404, indistinguishably (not revealing which documents ever existed).
# ---------------------------------------------------------------------------


@app.get("/policy-doc/{doc_id}")
def get_policy_doc(
    doc_id: str,
    chunk_id: str | None = None,
    current_user: CurrentUser = Depends(require_role("cskh", "supervisor")),
    session: Session = Depends(get_session),
):
    doc = session.get(PolicyDocument, doc_id)
    if doc is None or doc.status != "indexed":
        raise HTTPException(status_code=404, detail="tài liệu không tồn tại")

    highlight = None
    # `chunk_id` is optional — wrong/not matching doc_id/not locatable in the full text all ONLY
    # skip the highlighting (graceful degradation), never failing the whole request.
    # Documents without full_text (the 4 documents indexed BEFORE this column, see
    # migration f1a2b3c4d5e6) naturally fall into this branch too.
    if chunk_id and doc.full_text:
        chunk = session.get(PolicyChunk, chunk_id)
        if chunk is not None and chunk.doc_id == doc_id:
            start = doc.full_text.find(chunk.text)
            if start != -1:
                highlight = {"start": start, "end": start + len(chunk.text)}

    return {
        "doc_id": doc.doc_id,
        "filename": doc.filename,
        "full_text": doc.full_text,
        "highlight": highlight,
    }


# ---------------------------------------------------------------------------
# Live chat (2026-08-11) — upgrades CTRL-001 from an asynchronous ticket flag to real-time two-way
# chat. The WS handshake uses a single-use ticket (ws-ticket, short TTL) instead of an
# Authorization: Bearer header — browsers can't attach arbitrary headers to `new WebSocket(url)`,
# and the real JWT is never put in a query parameter. See src/api/live_chat_ws.py for the
# connection manager and the reasoning around Redis.
# ---------------------------------------------------------------------------


@app.post("/live-chat/ws-ticket")
def live_chat_ws_ticket(
    req: LiveChatWsTicketRequest,
    current_user: CurrentUser = Depends(require_role("customer")),
    session: Session = Depends(get_session),
):
    # NO OTP gate here (require_otp_view_fresh was removed, a real finding
    # 2026-08-11 via manual testing) — request_human_handoff (the AI tool creating the ticket that
    # leads
    # to this route) DELIBERATELY needs no OTP because it is only a routing request, not an action
    # touching data (see the tool docstring in customer_tools.py).
    # Forcing customers to verify OTP JUST TO OPEN the chat window after they were allowed to
    # request a
    # human WITHOUT OTP is a logical contradiction — and since the 403 was silently swallowed in the
    # frontend (no UI showing it), customers clicking "talk to a human" saw nothing happen and
    # thought
    # the feature was broken. Consistent with request_human_handoff: opening a chat session is not
    # in
    # itself a sensitive action; sensitive content (if any) lives in the messages of the
    # conversation,
    # not in opening the connection.
    if not _live_chat_manager.ws_ticket_limiter.allow(current_user.user_id):
        raise HTTPException(status_code=429, detail="Bạn mở phiên chat quá nhanh, vui lòng thử lại sau ít phút")
    chat_session = _handle_tool_error(
        live_chat.open_chat_session, session, ticket_id=req.ticket_id, customer_id=current_user.user_id
    )
    ws_ticket = _live_chat_manager.mint_ticket(
        user_id=current_user.user_id, role=current_user.role, chat_session_id=chat_session["chat_session_id"]
    )
    return {"ws_ticket": ws_ticket, "chat_session_id": chat_session["chat_session_id"]}


@app.post("/live-chat/staff/ws-ticket")
def live_chat_staff_ws_ticket(current_user: CurrentUser = Depends(require_role("cskh", "supervisor"))):
    if not _live_chat_manager.staff_ws_ticket_limiter.allow(current_user.user_id):
        raise HTTPException(status_code=429, detail="Bạn xin vé kết nối quá nhanh, thử lại sau ít phút giúp mình nhé")
    ws_ticket = _live_chat_manager.mint_ticket(user_id=current_user.user_id, role=current_user.role)
    return {"ws_ticket": ws_ticket}


@app.get("/live-chat/sessions/by-ticket/{ticket_id}")
def live_chat_session_by_ticket(
    ticket_id: str,
    current_user: CurrentUser = Depends(require_role("cskh", "supervisor")),
    session: Session = Depends(get_session),
):
    """CSKH open the chat panel for a ticket with human_handoff_requested — they need the
    chat_session_id to claim/join, which isn't remembered anywhere (the frontend doesn't keep
    this id long-term, and the customer is the side that creates the session via ws-ticket).
    TAKES THE MOST RECENT SESSION REGARDLESS OF STATUS (including 'closed') — a real finding
    2026-08-11: a customer pressing F5/leaving mid-chat makes the session auto-close (see
    release_staff_sessions/close_customer_session_on_disconnect), but CSKH reopening that ticket
    still need to see the conversation history + the customer's phone number to call back, not
    only while the session is 'waiting'/'active'. The context (including the customer's phone)
    is ALWAYS returned — previously it was only pushed via WS on a successful claim, so CSKH
    opening a ticket with a closed session never received claim_success and never saw the
    phone number."""
    # ADR-064(b) (04/09, caught by the review — leaking real customer phone numbers) — the same
    # row-level scoping rule. The Ticket is looked up BEFORE the ChatSession: a ticket that doesn't
    # exist/is claimed by someone else both return the same 404, revealing no difference.
    ticket = session.get(Ticket, ticket_id)
    if ticket is None or _agent_blocked_by_claim(current_user, ticket):
        raise HTTPException(status_code=404, detail="ticket không tồn tại")
    chat_session = session.scalars(
        select(ChatSession).where(ChatSession.ticket_id == ticket_id).order_by(ChatSession.started_at.desc())
    ).first()
    if chat_session is None:
        return {"chat_session": None, "context": None}
    context = _handle_tool_error(live_chat.get_handoff_context, session, ticket_id=ticket_id)
    return {
        "chat_session": {
            "chat_session_id": chat_session.chat_session_id,
            "status": chat_session.status,
            "claimed_by": chat_session.claimed_by,
        },
        "context": context,
    }


@app.get("/live-chat/sessions/{chat_session_id}/messages")
def live_chat_session_messages(
    chat_session_id: str,
    current_user: CurrentUser = Depends(require_role("customer", "cskh", "supervisor")),
    session: Session = Depends(get_session),
):
    """The real message history of a session — previously NO route read back the `messages` table;
    there was only realtime push via WS while the connection was open.
    CSKH reopening a ticket whose session has closed (the customer left) need to be able to SEE
    AGAIN what the customer typed before leaving, not just know generically that "the customer
    once wanted a human"."""
    chat_session = session.get(ChatSession, chat_session_id)
    if chat_session is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên chat")
    if current_user.role == "customer" and chat_session.customer_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Phiên chat này không thuộc về bạn")
    # ADR-064(b) (04/09, caught by the review — paths to the chat_session_id: by-ticket
    # OR /live-chat/sessions/waiting before anyone claims, readable FOREVER after a colleague claims
    # unless blocked here). The content is PII-masked (che_pii_van_ban just below) but it is still a
    # real transcript — the same rule applies.
    if current_user.role == "cskh":
        ticket = session.get(Ticket, chat_session.ticket_id)
        if ticket is not None and _agent_blocked_by_claim(current_user, ticket):
            raise HTTPException(status_code=404, detail="Không tìm thấy phiên chat")
    messages = session.scalars(
        select(Message).where(Message.chat_session_id == chat_session_id).order_by(Message.created_at)
    ).all()
    return {
        "messages": [
            # M3 — masked at the READ layer (fixed by the real PO 25/08). `m.content` in the DB is
            # still
            # VERBATIM; this route is one of the two read paths, the other being the return value of
            # live_chat.record_message (the WS broadcast).
            # Adding a new read path for `messages` MUST mask there too — masking lives at the read
            # layer, so
            # it does NOT spread on its own.
            {"message_id": m.message_id, "role": m.role,
             "content": che_pii_van_ban(m.content), "created_at": m.created_at.isoformat()}
            for m in messages
        ]
    }


@app.get("/live-chat/sessions/waiting")
async def live_chat_sessions_waiting(
    current_user: CurrentUser = Depends(require_role("cskh", "supervisor")),
    session: Session = Depends(get_session),
):
    # A lazy sweep of orphaned 'waiting' sessions BEFORE returning the list —
    # a real finding 2026-08-11: a customer logging out/losing the network suddenly may not send the
    # WS
    # close frame, leaving the session hanging in the queue long after the customer left (see
    # sweep_stale_waiting_sessions).
    await _live_chat_manager.sweep_stale_waiting_sessions()
    waiting = session.scalars(select(ChatSession).where(ChatSession.status == "waiting").order_by(ChatSession.started_at)).all()
    return {
        "sessions": [
            {"chat_session_id": s.chat_session_id, "ticket_id": s.ticket_id, "customer_id": s.customer_id, "started_at": s.started_at.isoformat()}
            for s in waiting
        ]
    }


@app.post("/live-chat/sessions/{chat_session_id}/claim")
async def live_chat_claim_session(
    chat_session_id: str,
    current_user: CurrentUser = Depends(require_role("cskh", "supervisor")),
    session: Session = Depends(get_session),
):
    claimed = _handle_tool_error(
        live_chat.claim_session,
        session,
        chat_session_id=chat_session_id,
        staff_id=current_user.user_id,
        is_cskh=current_user.role == "cskh",
    )
    if claimed is None:
        raise HTTPException(status_code=409, detail="Phiên chat này đã có chuyên viên khác nhận")
    context = _handle_tool_error(live_chat.get_handoff_context, session, ticket_id=claimed["ticket_id"])
    await _live_chat_manager.notify_claimed(chat_session_id=chat_session_id, staff_user_id=current_user.user_id, context=context)
    return claimed


@app.post("/live-chat/sessions/{chat_session_id}/close")
async def live_chat_close_session(
    chat_session_id: str,
    current_user: CurrentUser = Depends(require_role("cskh", "supervisor")),
    session: Session = Depends(get_session),
):
    """CSKH end the chat session — the customer is moved to the CSAT rating screen immediately
    (a "closed" broadcast to the session's participants via WS)."""
    chat_session = session.get(ChatSession, chat_session_id)
    if chat_session is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên chat")
    closed = _handle_tool_error(live_chat.close_session, session, chat_session_id=chat_session_id)
    await _live_chat_manager.send_to_session(chat_session_id, {"type": "session_closed", "chat_session_id": chat_session_id})
    return closed


# ---------------------------------------------------------------------------
# ADR-063 — the notification bell + CSKH/supervisor presence.
# Recipient isolation is enforced at the SERVICE LAYER (src/services/notifications.py) —
# routes only enforce ROLE. The returned content is ONLY event_type + ticket_id + created_at/
# read_at — NO amounts/PII/phone numbers (hard constraint #3 + PDPA).
# ---------------------------------------------------------------------------


@app.get("/notifications")
def list_notifications(
    current_user: CurrentUser = Depends(require_role("cskh", "supervisor")),
    _revoked: CurrentUser = Depends(require_unrevoked_token),
    session: Session = Depends(get_session),
):
    items = list_my_notifications(session, user_id=current_user.user_id)
    # [polish before filming 04/09] The round the PO fixed: JOIN to Ticket/Complaint AT RENDER
    # TIME, NO snapshot stored at fan-out (ADR-063 addendum) — `priority` is NOT immutable after
    # creation (`_raise_priority_by_emotion`, graph.py:654, overwrites `complaint.priority` AFTER
    # the
    # ticket exists, based on the customer's emotion signals). A snapshot at fan-out would show the
    # OLD priority if the case was raised AFTER the notification was sent — exactly the kind of
    # "stale
    # figure that looks right". Loaded once as a BATCH (joined via ticket_id/complaint_id), not N+1
    # per notification.
    tickets = {
        t.ticket_id: t
        for t in session.scalars(
            select(Ticket).where(Ticket.ticket_id.in_([n.ticket_id for n in items]))
        ).all()
    }
    complaints = {
        c.complaint_id: c
        for c in session.scalars(
            select(Complaint).where(
                Complaint.complaint_id.in_([t.complaint_id for t in tickets.values()])
            )
        ).all()
    }
    out = []
    for n in items:
        t = tickets.get(n.ticket_id)
        c = complaints.get(t.complaint_id) if t else None
        out.append(
            {
                "notification_id": n.notification_id,
                "event_type": n.event_type,
                "ticket_id": n.ticket_id,
                "created_at": n.created_at.isoformat(),
                "read_at": n.read_at.isoformat() if n.read_at else None,
                # 4 non-PII fields, displayed exactly as GET /tickets already shows them
                # ("normal / 29 days left") — a deleted/unresolvable ticket
                # (shouldn't happen, the FK constrains it) yields None, no guessing.
                "complaint_type": c.type if c else None,
                "scope": c.scope if c else None,
                "priority": c.priority if c else None,
                "sla_due_at": t.sla_due_at.isoformat() if t else None,
            }
        )
    return {"items": out}


@app.get("/notifications/unread-count")
def notifications_unread_count(
    current_user: CurrentUser = Depends(require_role("cskh", "supervisor")),
    _revoked: CurrentUser = Depends(require_unrevoked_token),
    session: Session = Depends(get_session),
):
    return {"unread_count": count_unread(session, user_id=current_user.user_id)}


@app.post("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: str,
    current_user: CurrentUser = Depends(require_role("cskh", "supervisor")),
    _revoked: CurrentUser = Depends(require_unrevoked_token),
    session: Session = Depends(get_session),
):
    # Not existing AND not belonging to the logged-in user_id return the SAME 404 —
    # distinguishing the two would let a client probe whether other users' notifications exist
    # (see the mark_read docstring).
    ok = mark_read(session, user_id=current_user.user_id, notification_id=notification_id)
    if not ok:
        raise HTTPException(status_code=404, detail="notification không tồn tại")
    return {"notification_id": notification_id, "read": True}


@app.post("/notifications/read-all")
def mark_all_notifications_read(
    current_user: CurrentUser = Depends(require_role("cskh", "supervisor")),
    _revoked: CurrentUser = Depends(require_unrevoked_token),
    session: Session = Depends(get_session),
):
    marked_count = mark_all_read(session, user_id=current_user.user_id)
    return {"marked_read": marked_count}


@app.post("/presence/heartbeat")
def presence_heartbeat_route(
    current_user: CurrentUser = Depends(require_role("cskh", "supervisor")),
    _revoked: CurrentUser = Depends(require_unrevoked_token),
):
    # NO DB session needed — presence lives entirely in Redis TTLs, per the principle "no state kept
    # in-process" (4-5 independent workers).
    presence_heartbeat(current_user.user_id)
    return {"status": "ok"}


@app.get("/presence/staff")
def presence_staff_list(
    current_user: CurrentUser = Depends(require_role("supervisor")),
    _revoked: CurrentUser = Depends(require_unrevoked_token),
    session: Session = Depends(get_session),
):
    cskh_users = session.scalars(select(User).where(User.role == "cskh")).all()
    online_ids = online_user_ids([u.user_id for u in cskh_users])
    return {
        "items": [
            {
                "user_id": u.user_id,
                "full_name": u.full_name,
                "online": u.user_id in online_ids,
                "so_ve_dang_xu_ly": open_ticket_count(session, user_id=u.user_id),
            }
            for u in cskh_users
        ]
    }


@app.post("/live-chat/sessions/{chat_session_id}/csat")
def live_chat_submit_csat(
    chat_session_id: str,
    req: LiveChatCsatRequest,
    current_user: CurrentUser = Depends(require_role("customer")),
    session: Session = Depends(get_session),
):
    chat_session = session.get(ChatSession, chat_session_id)
    if chat_session is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên chat")
    if chat_session.customer_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Phiên chat này không thuộc về bạn")
    return _handle_tool_error(live_chat.submit_csat, session, chat_session_id=chat_session_id, score=req.score)


app.add_api_websocket_route("/ws/live-chat", live_chat_websocket_endpoint)


def _check_time_budget_coherence() -> None:
    """A config with ABSURD timing can NOT be deployed — fail-fast at import.

    Measured 17/08: three clocks unaware of each other.

        OPENAI_TIMEOUT_SECONDS   20.0   ceiling for ONE call
        OPENAI_MAX_RETRIES        1     SDK retries on its own
        AGENT_TURN_TIMEOUT_SEC   45.0   ceiling for the WHOLE TURN

    ⟹ one slow call + one retry = 40s = **89% of the whole turn's budget**, while a typical turn
    needs 2–5 calls. A real turn measured 30.7s when everything was normal; exactly one more
    retry exceeds the ceiling ⟹ `agent_turn_timeout` ⟹ and that branch **CREATES A TICKET**. A
    misaligned config produces real complaint records.

    This check does NOT pick the right numbers — it only rejects a **self-contradictory** set.
    Picking numbers is still a human job, and needs the real latency distribution (p99 = 11.6s
    over n=70 calls measured 17/08), not the observed maximum.

    Why fail-fast rather than warn: the consequence doesn't show up where the mistake is. It
    shows up as one customer's failed turn, hours later, in the form of a ticket nobody asked for
    — so far from the cause that nobody can connect them.
    """
    per_call_budget = OPENAI_TIMEOUT_SECONDS * (OPENAI_MAX_RETRIES + 1)
    if per_call_budget > AGENT_TURN_TIMEOUT_SECONDS:
        raise RuntimeError(
            f"Ngân sách thời gian tự mâu thuẫn: MỘT lời gọi có thể tiêu "
            f"{per_call_budget:.0f}s (OPENAI_TIMEOUT_SECONDS="
            f"{OPENAI_TIMEOUT_SECONDS} × (OPENAI_MAX_RETRIES="
            f"{OPENAI_MAX_RETRIES} + 1)) trong khi trần CẢ LƯỢT chỉ "
            f"{AGENT_TURN_TIMEOUT_SECONDS:.0f}s. Một lượt cần nhiều lời gọi ⟹ "
            f"timeout là chắc chắn chứ không phải rủi ro, và nhánh timeout TẠO VÉ."
        )


_check_time_budget_coherence()


@app.on_event("startup")
def _declare_source_image_drift():
    """Catches the `docker cp` mechanism AUTOMATICALLY — re-hashes the RUNNING code and compares
    it with the build-time label.

    17/08: `fin05-backend-1` reported `build_commit=7450184` while `graph.py` had been modified
    via `docker cp`. The label didn't budge because `docker cp` copies FILES and doesn't touch
    environment variables. It was only caught because SOMEONE WENT CHECKING with `docker diff` —
    not thanks to any mechanism.

    This check does that automatically on every startup. It does NOT replace `docker diff`:
    `docker cp` without a restart isn't caught yet (the writable layer survives restarts, but
    already-loaded modules don't reload themselves). The two complement each other — this one is
    cheap and always runs, the other is expensive and has to be remembered.

    FAIL-VISIBLE, not fail-fast: code drifting from the image is a sign of a broken process, NOT
    proof that the code is wrong. Killing the service for it turns a suspicion into an incident —
    the same reason applied to `HOTLINE_CSKH` and to `/ready` not gating.
    """
    label_text = build_time_stamp()
    if label_text is None:
        return  # outside an image (local dev, pytest) — no label to compare, stay quiet
    if not label_text:
        # INSIDE an image but the label is empty/broken: DIE, don't skip.
        #
        # Contrast with `HOTLINE_CSKH` (FAIL-VISIBLE, not fail-fast) — the two cases differ in WHAT
        # IS
        # LOST WITHOUT IT:
        #   missing hotline -> the PRODUCT degrades; killing the service turns a local degradation
        # into
        #                      total loss of service.
        #   missing label   -> the VERIFICATION MECHANISM disappears, and disappears SILENTLY.
        #                      There is no "degradation" here, only blindness — and a blind gate
        # looks
        #                      exactly like a gate that is protecting.
        raise RuntimeError(
            f"Nhãn băm mã nguồn rỗng/hỏng tại {STAMP_PATH}. Ảnh này không do "
            f"Dockerfile của dự án dựng, hoặc bước tính nhãn đã hỏng. TỪ CHỐI "
            f"khởi động: chạy tiếp nghĩa là chạy với một cổng kiểm chứng đã tắt "
            f"mà không ai biết."
        )
    running = hash_source()
    if running != label_text:
        _logger.error(
            "ma_nguon_lech_anh",
            extra={
                "bam_luc_dung": label_text,
                "bam_dang_chay": running,
                "cach_bam": HASH_METHOD,
                "y_nghia": (
                    "ma /app/src dang chay KHAC ma duoc dong vao anh — dau hieu "
                    "docker cp hoac sua tay trong container"
                ),
            },
        )


@app.on_event("startup")
def _declare_support_channel_gap():
    """FAIL-VISIBLE for `HOTLINE_CSKH` (ADR-025 decision 4) — NOT fail-fast.

    When a provider error falls in the "needs intervention" group (401/403/400/404), the agent
    returns a soft reply and DELIBERATELY creates no ticket. The path to a human is the only
    remaining measure for a customer who may be trying to report fraud — the cost of losing track
    is NOT uniform, and we can't tell the cases apart because the agent failed BEFORE it could
    classify.

    WHY NOT fail-fast even though missing it degrades exactly that reply:
      · fail-fast is the rule for SECRETS — an empty/default key is a hole pretending to be
        security. `HOTLINE_CSKH` is not a secret: missing it degrades an apology sentence, it
        opens no hole.
      · the cost is heavily asymmetric: every running stack would die until someone filled it in
        — turning a LOCAL degradation into TOTAL loss of service. The same shape as the reason
        `/ready` must not gate on external dependencies.

    ⟹ The gap DECLARES ITSELF, the service stays alive. A dedicated event name so it can be
    grepped today and alerts can be attached to the NAME later, without code changes.
    """
    if DIALABLE:
        return
    raw_value = os.environ.get("HOTLINE_CSKH", "").strip()
    # TWO different cases, and merging them would lose exactly the information operators need:
    # "nobody filled it in" vs "a placeholder was filled in". The second case is MORE DANGEROUS
    # because
    # the field has text in it and looks done at a glance — the warning must KEEP LIVING, not be
    # switched off just because the field is filled.
    _logger.error(
        "hotline_cskh_khong_bam_duoc" if raw_value else "thieu_hotline_cskh",
        extra={
            "gia_tri_tho": raw_value or None,
            "hau_qua": (
                "khach gap loi nha cung cap nhom can-can-thiep nhan cau mem KHONG kem "
                "so tong dai — loi di sang nguoi that chi la cum chung chung"
            ),
            "cach_va": "dat HOTLINE_CSKH = so THAT bam duoc roi recreate container",
        },
    )


@app.on_event("startup")
async def _start_live_chat_fanout():
    """Runs the background loop receiving live-chat fan-out from other workers (ADR-015).

    WITHOUT it, enabling multi-worker breaks live chat SILENTLY: the customer on worker 1, CSKH
    on worker 2, each side's messages only reach sockets on the same worker — no error raised,
    messages just vanish.
    """
    import asyncio

    from src.api.live_chat_ws import _subscriber_loop

    app.state.live_chat_subscriber = asyncio.create_task(
        _subscriber_loop(_live_chat_manager)
    )


@app.on_event("shutdown")
def _close_resources_on_shutdown():
    """Graceful shutdown — closes the checkpointer pool (ADR-014).

    psycopg's ConnectionPool runs background threads; without an explicit close it raises
    PythonFinalizationError when the interpreter exits, and holds Postgres connections until the
    TCP timeout — eating into max_connections during continuous deploys.
    """
    close_checkpointer()
    task = getattr(app.state, "live_chat_subscriber", None)
    if task is not None:
        task.cancel()


@app.get("/health")
def health():
    """Liveness — DELIBERATELY doesn't touch the DB/Redis (only readiness may).

    Returns the ENVIRONMENT IDENTITY too (2026-08-13), so you can tell at a glance which stack
    you are talking to, rather than inferring from port numbers. Born from a real incident: the
    Docker stack (Postgres) and the local dev stack (SQLite) ran side by side, two identical
    browser windows on different databases — see the note in src/config.py and ADR-009.

    `db_kind`/`db_name` are only the scheme + database name, with NO host/user/password
    (this endpoint is public and requires no authentication).
    """
    return {
        "status": "ok",
        "env": APP_ENV,
        # The CODE identity label, alongside `build_commit`, the REPO identity label.
        # DELIBERATELY only returns the BUILD-TIME label, not the result of comparing it with the
        # running
        # code: this endpoint is PUBLIC, and a flag saying "this box has hand-edited code" is
        # operational
        # state — the same kind of information already refused exposure here before.
        # The comparison result lives in the log event `ma_nguon_lech_anh` (source/image drift).
        "build_src_hash": build_time_stamp() or "ngoai-anh",
        # Readers of this endpoint will compare it with a hash they compute themselves. Without the
        # line below they'd have to GUESS how it's computed — and guessing wrong turns two different
        # strings into "the code has drifted".
        "build_src_hash_cach_bam": HASH_METHOD,
        "db_kind": DB_KIND,
        "db_name": DB_NAME,
        # Answers the question 16/08 COULDN'T answer: "has production received the 429 fix?". That
        # day we had to read `git merge-base` on a dev machine because the running product carried
        # no
        # build label at all.
        "build_commit": BUILD_COMMIT,
        "build_at": BUILD_AT,
    }
