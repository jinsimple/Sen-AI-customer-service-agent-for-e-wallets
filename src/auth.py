"""JWT — replaces every route trusting `user_id`/`approved_by`/... declared by the client in
the body (an impersonation hole — anyone calling the API could claim to be any user).
After the fix: the caller's identity ALWAYS comes from the signed token,
NEVER from the request body.

Flow: POST /auth/login authenticates phone+role → issues an access_token. Every route that
needs identity declares `current_user: CurrentUser = Depends(get_current_user)`
(or `Depends(require_role("supervisor"))` when exactly one role is required) instead of
accepting user_id/approved_by/... parameters from the Pydantic request body.
"""
from __future__ import annotations

import contextvars
import datetime as dt
import hashlib
import json
import secrets
from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.config import (
    JWT_ACCESS_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_REFRESH_EXPIRE_DAYS_CUSTOMER,
    JWT_REFRESH_EXPIRE_DAYS_STAFF,
    JWT_SECRET_KEY,
    OTP_STEPUP_FRESH_MINUTES,
)
from src.observability.logging_config import get_logger
from src.redis_client import get_default_client

_bearer = HTTPBearer(auto_error=False)
_STAFF_ROLES = {"cskh", "supervisor", "partner_admin"}


@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    role: str
    iat: int  # login timestamp — used as the identifier of the login SESSION
    # (different logins -> different iat), see run_agent_turn()
    # thread_id in src/api/main.py::agent_chat.
    otp_verified_at: int | None = None  # timestamp of passing /auth/otp/verify
    # most recently — None means never verified in this session. Stores the timestamp
    # (not a bool) so "is it still fresh" can be computed PER type of action
    # (see otp_fresh_within) — decided after comparing against industry standards
    # NIST 800-63B/step-up authentication (docs/TESTING.md, 2026-08-10):
    # view-only actions accept a longer window (12h) than actions with financial consequences
    # such as create_ticket (15 minutes — "step-up" must be fresher).

    def otp_fresh_within(self, max_minutes: int) -> bool:
        if self.otp_verified_at is None:
            return False
        age_minutes = (dt.datetime.utcnow().timestamp() - self.otp_verified_at) / 60
        return age_minutes <= max_minutes


def create_access_token(
    *, user_id: str, role: str, otp_verified_at: dt.datetime | None = None, iat: dt.datetime | None = None
) -> str:
    """`iat` is passed explicitly when RE-ISSUING the token after OTP verification (keeping the
    original login `iat`, NOT minting a new timestamp) — otherwise a new `iat` would change
    the conversation `thread_id` (user_id:iat, see src/agents/graph.py) mid-chat, making the
    agent "forget" the context discussed before verification."""
    now = dt.datetime.utcnow()
    payload = {
        "sub": user_id,
        "role": role,
        "otp_verified_at": otp_verified_at.timestamp() if otp_verified_at else None,
        "iat": iat or now,
        "exp": now + dt.timedelta(minutes=JWT_ACCESS_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


# ---------------------------------------------------------------------------
# Refresh token (AUTH5-02/02B/02C/03/03B, Auth Flow upgrade 2026-08-12)
# — NOT a JWT: a random string (secrets.token_urlsafe, same pattern as the existing
# ws-ticket in src/api/live_chat_ws.py); the server keeps state in
# Redis (keyed by hash — the raw token is never stored, same "never store secrets in raw form"
# principle applied to security answers). Enables real REVOCATION
# (plain JWTs can't be revoked without a server-side state lookup) and ROTATION
# + REUSE DETECTION: every use issues a new token; an old token used a second time
# is treated as a sign of theft -> the whole "family" (every token descended from the same
# original login) is revoked, forcing a fresh login.
# ---------------------------------------------------------------------------


def _refresh_ttl_seconds(role: str) -> int:
    days = JWT_REFRESH_EXPIRE_DAYS_STAFF if role in _STAFF_ROLES else JWT_REFRESH_EXPIRE_DAYS_CUSTOMER
    return days * 24 * 60 * 60


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def mint_refresh_token(
    *,
    user_id: str,
    role: str,
    login_iat: int,
    otp_verified_at: int | None,
    family_id: str | None = None,
) -> str:
    """`family_id` is passed explicitly on ROTATE (keeping the original family) — leave it empty
    on first mint (login/verify_otp) to generate a new family."""
    token = secrets.token_urlsafe(32)
    family_id = family_id or secrets.token_urlsafe(16)
    data = {
        "user_id": user_id,
        "role": role,
        "family_id": family_id,
        "login_iat": login_iat,
        "otp_verified_at": otp_verified_at,
        "rotated": False,
    }
    get_default_client().setex(f"refresh:{_hash_token(token)}", _refresh_ttl_seconds(role), json.dumps(data))
    return token


def is_family_revoked(family_id: str) -> bool:
    return get_default_client().exists(f"revoked_family:{family_id}") == 1


# TIER 0 (security 2cff494) — before this version `auth.py` had NOT A SINGLE LOG LINE
# in its 294 lines, not even in `revoke_family()` — so the event "refresh token reused,
# suspected theft, whole session revoked" fired COMPLETELY SILENTLY.
#
# Why log BEFORE fixing: tuning a control without being able to observe when it fires is
# TUNING BLIND. And right now it is also the EYE for watching the very bug being hunted
# (the refresh race at handoff) — without it, "session died" and "token genuinely stolen"
# look identical from the outside.
_logger = get_logger("fin05.auth")

# Label of the BRANCH that fired the revocation. A contextvar is used instead of adding a
# parameter to `revoke_family()` because that function is the module's public API — adding a
# mandatory parameter would break every future call site and tempt people to pass an arbitrary
# string. Today there is only ONE branch (`reuse_that` — real reuse); tier 2 will add
# `phat_lai_trong_grace` (re-issued within grace) if the grace window lands.
_revoked_branch: contextvars.ContextVar[str] = contextvars.ContextVar("nhanh_thu_hoi", default="khong_ro")


def revoke_family(family_id: str, *, role: str) -> None:
    """Revoke the WHOLE family — called when a refresh token is reused after it was already
    rotated (AUTH5-03, a sign of theft). The key expires on its own with the refresh TTL
    (no need to enumerate/delete each child token by hand)."""
    get_default_client().setex(f"revoked_family:{family_id}", _refresh_ttl_seconds(role), "1")
    # WARNING rather than INFO: this is a security event and must surface under every default
    # filter. NEVER log the token (not even its hash) — family_id is enough to link the events of
    # one session without creating yet another secret that could leak.
    _logger.warning(
        "refresh_family_revoked",
        extra={
            "su_kien": "refresh_family_revoked",
            "family_id": family_id,
            "role": role,
            "nhanh": _revoked_branch.get(),
        },
    )


def rotate_refresh_token(token: str) -> dict | None:
    """Returns None if the token is invalid/expired/its family revoked (including by reuse
    detection on THIS very call). Returns a dict with access_token/
    refresh_token/user_id/role if valid."""
    client = get_default_client()
    key = f"refresh:{_hash_token(token)}"
    raw = client.get(key)
    if raw is None:
        return None
    data = json.loads(raw)
    if is_family_revoked(data["family_id"]):
        return None
    if data.get("rotated"):
        # AUTH5-03 — THIS token was already used for a rotation earlier, and now it is being used
        # again -> this can only be due to copying/theft (the legitimate client already received the
        # NEW token and has no reason to reuse the old one).
        _revoked_branch.set("reuse_that")
        revoke_family(data["family_id"], role=data["role"])
        return None

    # Mark as ROTATED rather than delete immediately — kept BRIEFLY (60s), long enough to catch
    # a second request reusing it (reuse), cleaned up by TTL, no separate cron needed.
    data["rotated"] = True
    client.setex(key, 60, json.dumps(data))
    # Log the SUCCESS branch too, not just the revocation branch — without it the tier-0 logs
    # CANNOT determine N for the grace window.
    #
    # Reason: N is the gap between two racing refresh calls, and security fixed that N may only
    # be taken from SERVER-SIDE TIMESTAMPS (gaps measured on the client are artefacts of the
    # measuring tool — spawning curl/tabs — not of the product).
    # But `revoke_family` only fires for the LOSER. With a single timestamp there is no gap to
    # measure. The pair `refresh_rotated` -> `refresh_family_revoked` with the SAME
    # `family_id` is what yields N.
    #
    # INFO rather than WARNING: a successful rotation is a normal, constant occurrence; raising it
    # to WARNING would dilute exactly the alert on the other branch.
    _logger.info(
        "refresh_rotated",
        extra={
            "su_kien": "refresh_rotated",
            "family_id": data["family_id"],
            "role": data["role"],
        },
    )

    otp_verified_at = (
        dt.datetime.utcfromtimestamp(data["otp_verified_at"]) if data["otp_verified_at"] is not None else None
    )
    login_iat_dt = dt.datetime.utcfromtimestamp(data["login_iat"])
    new_access = create_access_token(
        user_id=data["user_id"], role=data["role"], otp_verified_at=otp_verified_at, iat=login_iat_dt
    )
    new_refresh = mint_refresh_token(
        user_id=data["user_id"],
        role=data["role"],
        login_iat=data["login_iat"],
        otp_verified_at=data["otp_verified_at"],
        family_id=data["family_id"],
    )
    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "user_id": data["user_id"],
        "role": data["role"],
    }


def revoke_refresh_token(token: str) -> None:
    """Logout — delete one specific refresh token (NOT the whole family, only the current
    session logging out; other devices stay logged in normally)."""
    get_default_client().delete(f"refresh:{_hash_token(token)}")


def set_revoked_before_now(user_id: str) -> None:
    """AUTH5-06 — every access token with an `iat` OLDER than this mark is treated as revoked
    immediately, without waiting for natural expiry (see is_access_token_revoked). Called at
    logout/after OTP verification (the new token replaces the old one)."""
    get_default_client().set(f"revoked_before:{user_id}", str(dt.datetime.utcnow().timestamp()))


def is_access_token_revoked(user_id: str, iat: int) -> bool:
    raw = get_default_client().get(f"revoked_before:{user_id}")
    if raw is None:
        return False
    return float(iat) < float(raw)


def _decode(token: str) -> CurrentUser:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Phiên đăng nhập đã hết hạn")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token không hợp lệ")
    user_id = payload.get("sub")
    role = payload.get("role")
    iat = payload.get("iat")
    if not user_id or not role or iat is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token không hợp lệ")
    otp_verified_at = payload.get("otp_verified_at")
    return CurrentUser(
        user_id=user_id,
        role=role,
        iat=int(iat),
        otp_verified_at=int(otp_verified_at) if otp_verified_at is not None else None,
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> CurrentUser:
    """Dependency for EVERY route that needs to know exactly who is calling. No valid
    Authorization header -> 401 immediately, no guessing."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Thiếu Authorization: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _decode(credentials.credentials)


def try_decode(token: str) -> CurrentUser | None:
    """Non-raising version of _decode — only for auxiliary purposes (the audit log recording who
    called the API), NEVER for authorisation. Authorisation must always go through
    get_current_user/require_role so the right 401/403 is returned to the client."""
    try:
        return _decode(token)
    except HTTPException:
        return None


def require_role(*allowed_roles: str):
    """Factory dependency — enforces the exact role instead of trusting a client-declared `role`.
    E.g. Depends(require_role("supervisor")) for the refund-approval route."""

    def _dep(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cần role thuộc {sorted(allowed_roles)}, tài khoản hiện tại là {current_user.role}",
            )
        return current_user

    return _dep


def require_otp_verified(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Guards routes that TOUCH sensitive transaction/account data (Brief §7 #4:
    session OTP before sensitive actions — AUTH5-01, 2026-08-12: NO LONGER paired with a
    security question; KBA was removed as an authenticator). BEFORE this fix, OTP was only a
    UI gate in the frontend (`ChatClient.tsx`) — the backend checked nothing, meaning a direct
    API call (curl/Postman) with a valid JWT could still fetch sensitive data without OTP
    verification — a real finding while cross-checking the AUTH-* QA suite. This dependency
    is NOT attached to the whole of /agent/chat (that would block general questions too,
    breaking AUTH-004) — only to routes that REALLY touch data:
    lookup_transaction, get_customer_history, create_ticket.

    Applies ONLY to the `customer` role — CSKH/supervisor/partner_admin do not go through the
    customer OTP flow; their identity is established through a separate staff login
    (`require_role`), so no extra OTP layer is needed (e.g. CSKH looking up
    `lookup_transaction` while handling a ticket — that route allows every role).

    This dependency is attached ONLY to /tools/create_ticket (an action with real financial
    consequences), so it uses a STRICTER step-up threshold (OTP_STEPUP_FRESH_MINUTES,
    see src/config.py) — decision AUTH-008 (2026-08-10): create_ticket requires FRESHER
    verification than view-only actions.

    AUTH5-06 (2026-08-12) — the revocation check is added HERE (the customer's most sensitive
    route), NOT applied to every ordinary route via get_current_user —
    a deliberate decision: access tokens are already very short-lived (15 minutes), and adding
    a Redis GET to EVERY request would make Redis a single point of failure for the whole
    system for very little marginal benefit; routes that really TOUCH DATA/MONEY are worth
    that price, ordinary read routes are not."""
    if current_user.role == "customer" and not current_user.otp_fresh_within(OTP_STEPUP_FRESH_MINUTES):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cần xác thực OTP phiên làm việc trước khi thao tác này (POST /auth/otp/request rồi /auth/otp/verify)",
        )
    if is_access_token_revoked(current_user.user_id, current_user.iat):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Phiên đã bị thu hồi — đăng nhập lại")
    return current_user


def require_unrevoked_token(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """ONLY checks whether the token was revoked — does NOT check OTP freshness. Can be attached
    to routes that DON'T need OTP but still touch data (e.g. `propose_resolution`).

    🔴 WHY IT NEEDS SEPARATING — the PRINCIPLE was not wrong, the MECHANISM was:
    The AUTH5-06 note just above (`require_otp_verified`) weighed it correctly: DO NOT apply
    revocation checks to EVERY request, because adding a Redis GET to every call makes Redis
    a single point of failure for the whole system. Only routes that TOUCH DATA/MONEY are
    worth that price. That principle is right, and it stays.
    [MEASURED 27/08] But the mechanism enforcing it was HITCHING A RIDE: the revocation check
    lived INSIDE `require_otp_verified`, so it ONLY reached routes that NEED OTP.
    Data-touching routes that DON'T need OTP (`propose_resolution` 11 lines,
    `escalate_ticket` 18 lines, `request-approval-otp`) fell outside — not because anyone
    forgot, but because the ride never went there.
    ⟹ Split into its own Depends so "which route is worth the Redis price" becomes an
    EXPLICITLY ATTACHED choice, rather than a side effect of whether the route needs OTP.

    🔴 WHY `require_otp_verified` DOES NOT `Depends` ON THIS FUNCTION — considered and REJECTED:
    FastAPI resolves dependencies BEFORE the function body ⟹ the revocation check would run
    BEFORE the OTP-freshness check, reversing the current order. A user who is BOTH REVOKED
    and has a STALE OTP gets 403 ("OTP verification required") today; after merging they
    would get 401 ("session revoked"). Both are "correct", but THAT IS AN OBSERVABLE
    BEHAVIOUR CHANGE — whereas this is a MECHANISM refactor, deliberately changing nothing
    externally.
    So `require_otp_verified` KEEPS its inline call. Both paths call the same pure function
    `is_access_token_revoked()` — DELIBERATE duplication, one line, in exchange for not
    touching the error order of a gate that is in production.

    ⚠️ NOT YET ATTACHED TO ANY ROUTE. Attaching it (`propose_resolution` · `escalate_ticket`
    · `request-approval-otp`) is Tier 1, pending the PO. This Depends exists in advance so
    that at that point only ONE parameter needs adding, rather than copy-pasting the check —
    copy-pasting is exactly how the "hitching a ride" bug was born in the first place."""
    if is_access_token_revoked(current_user.user_id, current_user.iat):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Phiên đã bị thu hồi — đăng nhập lại"
        )
    return current_user
