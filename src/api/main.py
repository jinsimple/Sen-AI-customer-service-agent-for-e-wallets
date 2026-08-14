"""FIN-05 — FastAPI app.

Hai nhóm route, cố ý tách bạch để ranh giới HITL (Data Brief §6.6, quyết
định thiết kế #1 trong ngữ cảnh dự án) hiện rõ ngay ở tầng routing:

  /tools/*        — agent gọi để điều tra/tạo ticket/đề xuất/escalate.
                    KHÔNG route nào trong nhóm này có thể ghi `approved`.
  /resolutions/{id}/approve  — CHỈ sếp (role=supervisor) gọi được. Đây là
                    con đường DUY NHẤT trong toàn hệ thống ghi trạng thái
                    approved — mọi phạm vi giao dịch, kể cả nội bộ ví
                    (quyết định thiết kế đã sửa, xem ngữ cảnh dự án §4.1).
  /tickets*       — đọc, dùng cho UI CSKH/sếp.

Vá bảo mật (phiên làm việc sau demo đầu): MỌI route cần danh tính giờ khai
báo `Depends(get_current_user)` hoặc `Depends(require_role(...))` — danh
tính lấy từ JWT đã ký (src/auth.py), KHÔNG BAO GIỜ từ field client tự khai
trong body (user_id/approved_by/rejected_by/created_by/requested_by đã bị
xoá khỏi schemas.py). Trước đây bất kỳ ai gọi API cũng mạo danh được bất kỳ
user nào — đây là lỗ hổng nghiêm trọng nhất đã vá.
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
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.agents.graph import close_checkpointer, run_agent_turn
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
    revoke_refresh_token,
    rotate_refresh_token,
    set_revoked_before_now,
    try_decode,
)
from src.config import (
    APP_ENV,
    DB_KIND,
    DB_NAME,
    OTP_MAX_FAILED_ATTEMPTS,
    REDIS_URL,
    RESOLUTION_APPROVAL_OTP_FRESH_MINUTES,
    ROOT_DIR,
)
from src.db.models import (
    AuthSession,
    ChatSession,
    Complaint,
    Escalation,
    InvestigationLog,
    Message,
    PolicyDocument,
    Resolution,
    Ticket,
    ToolResult,
    User,
)
from src.observability.context import bind_context, clear_context
from src.observability.logging_config import configure_logging
from src.observability.tracing import configure_tracing, instrument_fastapi_app
from src.rag.ingest import delete_document as _delete_policy_document
from src.rag.ingest import ingest_document
from src.rag.search import search_policy_text
from src.rate_limit import RedisConcurrencyLimiter, RedisSlidingWindowLimiter
from src.services import live_chat, reporting
from src.services.complaint_intake import create_ticket_with_fraud_check
from src.tools.base import ToolError, new_id
from src.tools.escalate_ticket import escalate_ticket as _escalate_ticket
from src.tools.get_customer_history import get_customer_history as _get_customer_history
from src.tools.lookup_transaction import lookup_transaction as _lookup_transaction
from src.tools.propose_resolution import propose_resolution as _propose_resolution

configure_logging()  # JSON stdout, gắn correlation_id/user_id tự động — xem
# src/observability/logging_config.py. Gọi Ở ĐÂY (module import time, trước
# khi bất kỳ route/middleware nào chạy) để MỌI logger trong process (kể cả
# uvicorn.access nếu propagate) dùng chung 1 format ngay từ request đầu tiên.
configure_tracing()  # OTel -> Jaeger (OTEL_EXPORTER_OTLP_ENDPOINT, mặc định
# localhost:4317) — graceful-degrade nếu Jaeger không sống, xem tracing.py.

# AUTH5 (đợt nâng cấp Auth Flow, 2026-08-12) — đồng bộ rate-limit lên Redis
# (cùng nơi lưu JWT revocation) thay vì in-memory rời rạc: sống sót qua
# restart backend, nhất quán trạng thái bảo mật/rate-limit toàn hệ thống ở 1
# nguồn duy nhất. `fake://` (CI/test) rơi về in-memory mặc định của slowapi —
# không regression, không cần Redis thật để chạy test.
limiter = Limiter(key_func=get_remote_address, storage_uri=None if REDIS_URL.startswith("fake://") else REDIS_URL)

app = FastAPI(title="FIN-05 AI Agent CSKH — Backend", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
instrument_fastapi_app(app)  # auto-instrument tầng HTTP (Giai đoạn 4) — span
# request/response tự động, KHÔNG tự viết tay span cho những gì framework đã lo.

# KHÔNG có CORSMiddleware — cố ý. Frontend (Next.js, frontend/) gọi qua BFF
# proxy (route handler server-side, xem frontend/src/app/api/), tức là
# server-to-server, không phải request từ trình duyệt nên không bị/cần CORS
# chi phối. JWT nằm trong cookie httpOnly, JS phía trình duyệt không đọc
# được để tự gắn Authorization header — mở CORS cho localhost:3000 sẽ không
# giúp ích gì (không có token để gọi) mà chỉ mở thêm bề mặt tấn công (VD
# site độc hại chạy trên trình duyệt nạn nhân fetch thẳng origin này). Nếu
# cần debug tay, dùng Swagger UI tại chính origin của API (same-origin,
# không cần CORS) hoặc curl.


# ---------------------------------------------------------------------------
# Audit log — ai gọi API nào, khi nào, kết quả gì. Ghi ra file riêng
# (logs/access.log), tách khỏi log ứng dụng, để tra cứu sự cố bảo mật không
# phải lục log lẫn với debug thường ngày.
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

    # correlation_id: nhận lại `X-Request-ID` nếu client/proxy đã gắn sẵn (vd
    # Caddy, xem docs/DEPLOY.md), tự sinh nếu không có — gắn 1 LẦN Ở ĐÂY qua
    # contextvars (src/observability/context.py), mọi log/span bên trong
    # request này (kể cả sâu trong agent/tool) tự động thừa hưởng, không cần
    # truyền tay qua tham số hàm. `reset()` trong finally — BẮT BUỘC theo
    # đúng checklist observability Giai đoạn 2, chống rò rỉ context sang
    # request kế tiếp nếu thread/task bị tái sử dụng.
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


# ---------------------------------------------------------------------------
# /auth/login — mật khẩu THẬT (quyết định 2026-08-12, thay luồng phone+role
# chọn tay trước đó — xem LoginRequest). Vai trò lấy từ user tìm được qua
# phone, không do client tự khai. Rate-limit chặt hơn route khác — chống dò
# số điện thoại/mật khẩu hàng loạt.
#
# AUTH5-08 (đợt nâng cấp Auth Flow 2026-08-12) — TRƯỚC bản vá: `@limiter.limit`
# (slowapi) khoá THUẦN theo `get_remote_address` (IP) — mọi khách hàng thật
# đi qua CHUNG 1 container `frontend` (kiến trúc BFF) nên đây thực chất là
# giới hạn DÙNG CHUNG cho mọi khách (1 khách spam sai mật khẩu khoá luôn
# khách khác cùng IP, đã ghi nhận ở
# tests/test_api/test_auth_login.py::test_login_rate_limit_shared_across_different_users_behind_same_ip).
# slowapi's key_func chỉ nhận `Request`, gọi ĐỒNG BỘ (không await được) nên
# không tự đọc được body JSON đã parse để khoá theo phone — bỏ hẳn decorator
# slowapi ở route này, thay bằng 2 lớp thủ công dùng chung
# RedisSlidingWindowLimiter (đồng bộ Redis, xem src/rate_limit.py):
# (1) theo PHONE — chặn CHÍNH XÁC brute-force nhắm 1 user cụ thể, kể cả từ
#     NHIỀU IP khác nhau (đúng tinh thần AUTH5-08).
# (2) theo IP — ngưỡng RỘNG hơn hẳn (chỉ chặn flood thô/credential stuffing
#     hàng loạt phone khác nhau từ 1 nguồn), không còn khoá nhầm người dùng
#     hợp lệ khác chung IP như trước.
# ---------------------------------------------------------------------------

_login_phone_limiter = RedisSlidingWindowLimiter(max_calls=10, window_seconds=60, name="login_phone")
_login_ip_limiter = RedisSlidingWindowLimiter(max_calls=60, window_seconds=60, name="login_ip")
_password_hasher = PasswordHasher()
# Hash "mồi" hợp lệ về ĐỊNH DẠNG (không khớp mật khẩu thật nào) — dùng để
# verify GIẢ khi không tìm thấy user theo phone, giữ THỜI GIAN XỬ LÝ tương
# đương nhánh "tìm thấy user nhưng sai mật khẩu". Thiếu bước này, kẻ tấn
# công đo độ trễ response phân biệt được "số điện thoại không tồn tại"
# (trả lời ngay, không hash) với "số điện thoại tồn tại" (verify tốn ~50-100ms
# CPU cho argon2id) — dò được danh sách số điện thoại thật đã đăng ký mà
# không cần đoán đúng mật khẩu nào.
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
    assert user is not None  # narrow cho type checker — password_ok=True chỉ khi user tồn tại
    now = dt.datetime.utcnow()
    token = create_access_token(user_id=user.user_id, role=user.role, iat=now)
    # AUTH5-02 (đợt nâng cấp Auth Flow 2026-08-12) — access_token giờ ngắn hạn
    # (15 phút, JWT_ACCESS_EXPIRE_MINUTES) nên PHẢI đi kèm refresh_token để
    # frontend tự làm mới mà không bắt khách đăng nhập lại liên tục.
    #
    # GOTCHA (phát hiện thật lúc viết test_refresh_preserves_original_iat_for_
    # thread_continuity — lệch đúng 7 giờ = timezone máy chạy): `datetime.timestamp()`
    # trên datetime NAIVE (utcnow() không gắn tzinfo) diễn giải giờ theo LOCAL
    # timezone của máy, không phải UTC — KHÁC với cách PyJWT tự mã hoá claim
    # iat/exp (calendar.timegm(), luôn coi naive datetime LÀ UTC, đúng ý định
    # thật). Dùng .timestamp() ở đây rồi sau này rotate_refresh_token() dựng
    # lại bằng utcfromtimestamp() + đưa lại qua create_access_token() (chạy
    # qua PyJWT/timegm ĐÚNG) làm access_token MỚI có `iat` LỆCH khỏi bản gốc —
    # phá thread_id hội thoại AI (user_id:iat, xem src/agents/graph.py) ngay
    # sau lần refresh đầu tiên. Bắt buộc dùng calendar.timegm() ở đây để khớp
    # CHÍNH XÁC cách PyJWT tự mã hoá, round-trip được nguyên vẹn qua
    # utcfromtimestamp() sau này.
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
# AUTH5-02/03/03B (đợt nâng cấp Auth Flow, 2026-08-12) — access token ngắn
# hạn (15 phút) cần cặp refresh token để làm mới; rotation + reuse detection
# (src/auth.py::rotate_refresh_token) chống replay nếu refresh token bị đánh
# cắp. `/auth/logout` thoả mãn trực tiếp finding ST2-P0-5/AUTH5 gốc: trước
# đây KHÔNG có cơ chế thu hồi JWT nào ở backend (xem
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
    # AUTH5-06 — vô hiệu hoá NGAY access token hiện tại (và mọi access token
    # cũ hơn) của user này, không chờ hết hạn tự nhiên. Chỉ có tác dụng thật
    # ở route nào có check is_access_token_revoked (require_otp_verified,
    # approve/reject) — xem lý do phạm vi có chủ đích ở src/auth.py.
    set_revoked_before_now(current_user.user_id)
    return {"ok": True}


# ---------------------------------------------------------------------------
# /auth/otp/* — OTP phiên làm việc THẬT ở backend (Brief §7 #4; AUTH5-01,
# 2026-08-12: không còn kèm câu hỏi bảo mật). TRƯỚC bản vá gốc, OTP chỉ là
# gate UI mô phỏng ở frontend (ChatClient.tsx) — backend không kiểm tra gì,
# nghĩa là gọi thẳng /tools/lookup_transaction bằng JWT hợp lệ vẫn lấy được
# dữ liệu nhạy cảm mà không cần xác thực OTP (phát hiện thật khi đối chiếu bộ
# QA test AUTH-*). `AuthSession` đã có sẵn trong data model — giờ mới có
# endpoint thật ghi/đọc lúc runtime.
# ---------------------------------------------------------------------------

# AUTH5-05E (đợt nâng cấp Auth Flow 2026-08-12) — decorator slowapi phía dưới
# (10/minute) vẫn khoá theo IP thuần (không đổi được sang phone/user theo
# cùng cách route login, vì key_func slowapi không async-await được body/
# current_user resolve qua Depends) — thêm lớp thứ 2 khoá theo user_id THẬT
# (đã có current_user ở đây, khác /auth/login), chặn brute-force mã OTP nhắm
# 1 user cụ thể kể cả nếu 1 kẻ tấn công đổi IP liên tục.
_otp_request_user_limiter = RedisSlidingWindowLimiter(max_calls=10, window_seconds=60, name="otp_request")

# Chặn đồng thời cho /agent/chat (ADR-012). Con số 20 chọn từ ĐO THẬT, không
# phải đoán: 1 lượt chat = ~15.136 token, hạn mức OpenAI 200.000 TPM => ~13
# lượt/phút bền vững. 20 slot cho phép bùng ngắn (lượt chat kéo dài ~10-45s
# nên 20 slot KHÔNG có nghĩa 20 lượt/phút) mà vẫn dưới ngưỡng gây bão 429.
# ttl 90s = 2x AGENT_TURN_TIMEOUT_SECONDS(45s): lưới an toàn thu hồi slot của
# process chết giữa chừng, đặt LỚN HƠN timeout để không cướp slot của lượt
# đang chạy hợp lệ. Chỉnh qua biến môi trường khi có số đo từ load test thật.
_AGENT_MAX_CONCURRENT = int(os.environ.get("AGENT_MAX_CONCURRENT", "20"))
_agent_turn_limiter = RedisConcurrencyLimiter(
    max_concurrent=_AGENT_MAX_CONCURRENT, ttl_seconds=90, name="agent_turn"
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
    return {
        "session_id": otp_session_id,
        "security_question": user.security_question,  # chỉ hỗ trợ CSKH nhận diện qua hotline, KHÔNG gate OTP verify
        "otp_code": otp_code,
        "note": (
            "Môi trường demo — mã OTP trả trực tiếp ở đây để tiện test/tự động hoá "
            "(sản phẩm thật sẽ gửi qua SMS, KHÔNG BAO GIỜ trả OTP qua API response)."
        ),
    }


@app.post("/auth/otp/verify")
@limiter.limit("10/minute")
def verify_otp(
    request: Request,
    req: OtpVerifyRequest,
    current_user: CurrentUser = Depends(require_role("customer")),
    session: Session = Depends(get_session),
):
    # Tra thẳng theo session_id (khoá chính) — KHÔNG còn "AuthSession mới
    # nhất của user" (vá race condition 2026-08-13, xem docstring
    # OtpVerifyRequest). auth_session.user_id != current_user.user_id nghĩa
    # là ai đó đang thử verify session OTP KHÔNG PHẢI của chính mình — coi
    # như không tồn tại, không tiết lộ session đó có thật hay không.
    auth_session = session.get(AuthSession, req.session_id)
    if auth_session is not None and auth_session.user_id != current_user.user_id:
        auth_session = None
    if auth_session is None:
        raise HTTPException(status_code=400, detail="Chưa yêu cầu OTP — gọi /auth/otp/request trước")
    if auth_session.locked_at is not None:
        raise HTTPException(
            status_code=403, detail="Phiên xác thực đã bị khoá do sai quá nhiều lần — yêu cầu OTP mới"
        )

    # AUTH5-01 (đợt nâng cấp Auth Flow, 2026-08-12, NIST SP 800-63B-4) — câu
    # hỏi bảo mật (KBA) KHÔNG còn được dùng làm authenticator, kể cả kết hợp
    # cùng OTP — kẻ tấn công dễ dàng tra được đáp án qua rò rỉ dữ liệu/mạng xã
    # hội. Mã OTP là yếu tố step-up DUY NHẤT ở đây. `User.security_question`/
    # `security_answer_hash` VẪN giữ trong model, chỉ để hỗ trợ CSKH nhận
    # diện khách khi gọi hotline (không gate route nào cả).
    otp_ok = req.otp_code == auth_session.otp_code

    if not otp_ok:
        auth_session.failed_attempts += 1
        # commit() Ở ĐÂY, TRƯỚC KHI raise — get_session() (src/api/deps.py)
        # rollback() bất kỳ exception nào thoát khỏi route, kể cả
        # HTTPException chủ động raise. Thiếu commit() này thì failed_attempts
        # vừa tăng bị CUỐN NGƯỢC mỗi lần, khoá sau N lần sai KHÔNG BAO GIỜ
        # thật sự xảy ra qua HTTP thật — phát hiện thật lúc test tay qua UI
        # (bấm sai nhiều lần liên tục không thấy khoá), dù test tự động
        # trước đó pass NHẦM vì fixture test dùng chung 1 Session không qua
        # commit/rollback như get_session() thật (xem test_otp.py).
        if auth_session.failed_attempts >= OTP_MAX_FAILED_ATTEMPTS:
            auth_session.locked_at = dt.datetime.utcnow()
            session.commit()
            raise HTTPException(
                status_code=403,
                detail=f"Sai quá {OTP_MAX_FAILED_ATTEMPTS} lần — phiên xác thực đã bị khoá, yêu cầu OTP mới",
            )
        session.commit()
        raise HTTPException(status_code=401, detail="Mã OTP không đúng")

    auth_session.otp_status = "verified"
    auth_session.security_q_passed = True
    # utcfromtimestamp (KHÔNG phải fromtimestamp — tránh lệch theo timezone máy
    # chủ) để tái tạo đúng iat gốc, giữ nguyên thread_id hội thoại (user_id:iat,
    # xem src/agents/graph.py) không đổi giữa chừng phiên chat khi cấp JWT mới.
    now = dt.datetime.utcnow()
    new_token = create_access_token(
        user_id=current_user.user_id,
        role=current_user.role,
        otp_verified_at=now,
        iat=dt.datetime.utcfromtimestamp(current_user.iat),
    )
    # LƯU Ý (KHÔNG gọi set_revoked_before_now ở đây, khác logout) — token MỚI
    # vẫn giữ NGUYÊN `iat` gốc (bắt buộc, giữ thread_id hội thoại AI, xem
    # create_access_token) — is_access_token_revoked() so `iat < revoked_before`,
    # nếu bump revoked_before=now ở đây thì CHÍNH token vừa cấp (iat cũ hơn
    # "now") sẽ bị coi là đã thu hồi ngay lập tức, khoá nhầm chính phiên vừa
    # xác thực xong. Phát hiện được lúc thiết kế (không phải chạy thử mới
    # thấy) — revoked_before chỉ dùng đúng cho logout, nơi lần đăng nhập KẾ
    # TIẾP chắc chắn có `iat` mới hơn (login() luôn set iat=now).
    #
    # Mint kèm 1 refresh token mới (family mới — hợp lý vì đây là lần "nâng
    # cấp" mức xác thực, không phải rotation thường) để phiên đã otp_verified
    # cũng làm mới được mà không phải xin OTP lại giữa chừng.
    new_refresh = mint_refresh_token(
        user_id=current_user.user_id,
        role=current_user.role,
        login_iat=current_user.iat,
        # calendar.timegm (không phải .timestamp()) — cùng lý do đã ghi ở
        # login(): round-trip qua utcfromtimestamp() sau này (rotate_refresh_token)
        # phải khớp CHÍNH XÁC cách PyJWT/create_access_token tự diễn giải.
        otp_verified_at=calendar.timegm(now.utctimetuple()),
    )
    return {"access_token": new_token, "refresh_token": new_refresh, "otp_verified": True}


# ---------------------------------------------------------------------------
# /tools/* — agent gọi. Danh tính (user_id) luôn lấy từ token, không nhận từ
# body — đóng lỗ hổng "tự khai user_id bất kỳ để đọc/tạo dữ liệu hộ người khác".
# ---------------------------------------------------------------------------


@app.post("/tools/lookup_transaction")
def lookup_transaction(
    req: LookupTransactionRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    # KHÔNG gắn require_otp_verified ở đây (dù có ở agent path — xem
    # customer_tools.py) — route này còn phục vụ CSKH/sếp tra cứu khi xử lý
    # ticket (ALL_ROLES) và khách hàng dùng gián tiếp qua rail "Giao dịch gần
    # đây" (ChatClient.tsx) NGAY KHI vào trang, trước khi có cơ hội xác thực
    # OTP — chặn ở đây sẽ phá UX xem thông tin cơ bản đã có từ trước khi làm
    # việc này. Thao tác THẬT SỰ nhạy cảm (agent chủ động điều tra/tạo ticket
    # giữa hội thoại) đã được chặn đúng chỗ — xem create_ticket bên dưới và
    # customer_tools.py.
    return _handle_tool_error(
        _lookup_transaction, session, requesting_user_id=current_user.user_id, **req.model_dump()
    )


@app.post("/tools/get_customer_history")
def get_customer_history(
    req: GetCustomerHistoryRequest,
    current_user: CurrentUser = Depends(require_role("customer")),
    session: Session = Depends(get_session),
):
    # Lý do không gắn require_otp_verified: xem comment ở lookup_transaction.
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
    # fraud_signals KHÔNG do caller truyền — tự tính ở tầng service (§4.1
    # FIN05-Backend-Handoff.md) từ dữ liệu DB, tránh agent tự bịa/quên tín hiệu.
    return _handle_tool_error(
        create_ticket_with_fraud_check, session, user_id=current_user.user_id, **req.model_dump()
    )


@app.post("/tools/propose_resolution")
def propose_resolution(
    req: ProposeResolutionRequest,
    current_user: CurrentUser = Depends(require_role("cskh", "supervisor")),
    session: Session = Depends(get_session),
):
    return _handle_tool_error(_propose_resolution, session, **req.model_dump())


@app.post("/tools/escalate_ticket")
def escalate_ticket(
    req: EscalateTicketRequest,
    current_user: CurrentUser = Depends(require_role("cskh", "supervisor")),
    session: Session = Depends(get_session),
):
    return _handle_tool_error(
        _escalate_ticket, session, created_by=current_user.user_id, **req.model_dump()
    )


# ---------------------------------------------------------------------------
# /agent/chat — AI agent thật (LangGraph, src/agents/), thay luồng kịch bản
# cũ ở frontend. Chỉ phục vụ role=customer — agent không dùng cho CSKH/Sếp,
# CSKH/Sếp thao tác trực tiếp qua webapp (không qua chat).
# ---------------------------------------------------------------------------


@app.post("/agent/chat")
@limiter.limit("20/minute")
def agent_chat(
    request: Request,
    req: AgentChatRequest,
    current_user: CurrentUser = Depends(require_role("customer")),
    session: Session = Depends(get_session),
):
    # Chặn ĐỒNG THỜI (2026-08-13) — khác rate limit ở trên: `20/minute` không
    # chặn được 150 người cùng bấm gửi trong 1 giây (mỗi người chỉ gọi 1 lần).
    # Không có lớp này, 150 lượt agent cùng chạy sẽ vét sạch threadpool 40
    # luồng của Starlette VÀ bắn đồng loạt vào OpenAI, ăn bão 429 vì vượt
    # 200.000 TPM (đo thật: ~15.136 token/lượt => trần ~13 lượt/phút).
    # Từ chối NGAY với thông báo rõ ràng, KHÔNG xếp hàng chờ — giữ request nằm
    # chờ trong 1 worker chính là thứ gây nghẽn dây chuyền. Xem ADR-012.
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
        # thread_id gắn theo PHIÊN đăng nhập (user_id + iat lúc login), không chỉ
        # user_id — checkpointer (src/agents/graph.py) dùng chung 1 instance suốt
        # vòng đời process, nếu chỉ khoá theo user_id thì đăng xuất rồi đăng nhập
        # lại (cùng process chưa restart) sẽ vẫn nối tiếp hội thoại phiên cũ, trái
        # PRD US-010 ("không giữ ngữ cảnh xuyên phiên đăng nhập khác nhau").
        return _handle_tool_error(
            run_agent_turn,
            session,
            user_id=current_user.user_id,
            message=req.message,
            thread_id=f"{current_user.user_id}:{current_user.iat}",
            otp_verified_at=current_user.otp_verified_at,
        )
    finally:
        # finally BẮT BUỘC: thoát bằng exception (timeout, ToolError, 500) mà
        # không trả slot thì hệ thống tự bóp cổ mình sau vài lỗi.
        _agent_turn_limiter.release(slot)


# ---------------------------------------------------------------------------
# /tickets* — đọc, dùng cho UI CSKH/sếp. Không phải data khách hàng tự xem
# trực tiếp (khách theo dõi qua /agent/chat), nên giới hạn 2 role nội bộ.
# ---------------------------------------------------------------------------


@app.get("/tickets")
def list_tickets(
    hitl_status: str | None = None,
    limit: int = 50,
    current_user: CurrentUser = Depends(require_role("cskh", "supervisor")),
    session: Session = Depends(get_session),
):
    stmt = select(Ticket).order_by(Ticket.created_at.desc()).limit(limit)
    if hitl_status:
        stmt = stmt.where(Ticket.hitl_status == hitl_status)
    tickets = session.scalars(stmt).all()
    # Dashboard CSKH cần loại/phạm vi/ưu tiên/tín hiệu gian lận ngay trên bảng
    # (US-011, US-014) — join 1 lần qua complaint_id thay vì N+1 request.
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
            }
        )
    return out


@app.get("/tickets/{ticket_id}")
def get_ticket_detail(
    ticket_id: str,
    current_user: CurrentUser = Depends(require_role("cskh", "supervisor")),
    session: Session = Depends(get_session),
):
    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
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
        # M-02 (ADR-019) — trả đủ dấu vết kiểm toán CẢ HAI nhánh. Route này đã
        # gated `require_role("cskh","supervisor")` ở chữ ký hàm, nên đây là
        # đường của NHÂN VIÊN; khách hàng không có route nào đọc resolution
        # (kiểm bằng test authz matrix). Ai thêm route customer đọc ticket sau
        # này PHẢI tự lọc — đừng tái dùng nguyên khối dict này.
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
# HITL gate — CHỈ sếp gọi được. Con đường DUY NHẤT ghi status='approved'.
# approved_by/rejected_by giờ LUÔN là current_user.user_id (đã xác thực qua
# JWT) — trước đây client tự khai approved_by, nghĩa là ai cũng "duyệt" được
# miễn đoán đúng user_id của một sếp bất kỳ. Đây là lỗ hổng nghiêm trọng thứ 2
# đã vá, cùng nhóm với /agent/chat.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# AUTH5-04/05/05B (đợt nâng cấp Auth Flow, 2026-08-12, PSD2 dynamic linking):
# duyệt resolution là hành động tài chính có tác động thật nhất hệ thống,
# trước đây chỉ gate role — giờ cần OTP RIÊNG cho ĐÚNG resolution_id đang
# duyệt, gắn chặt với amount tại thời điểm xin OTP (đổi amount sau đó buộc
# xin lại). Tái dùng AuthSession (resolution_id/amount_snapshot mới thêm)
# thay vì bảng riêng — xem docstring model.
# ---------------------------------------------------------------------------


@app.post("/resolutions/{resolution_id}/request-approval-otp")
@limiter.limit("10/minute")
def request_resolution_approval_otp(
    request: Request,
    resolution_id: str,
    current_user: CurrentUser = Depends(require_role("supervisor")),
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
    return {
        "session_id": otp_session_id,
        "resolution_id": resolution_id,
        "otp_code": otp_code,
        "note": (
            "Môi trường demo — mã OTP trả trực tiếp ở đây để tiện test/tự động hoá "
            "(sản phẩm thật sẽ gửi qua SMS/app riêng cho sếp). Mã CHỈ dùng được cho "
            f"ĐÚNG resolution_id={resolution_id} này, hết hạn sau "
            f"{RESOLUTION_APPROVAL_OTP_FRESH_MINUTES} phút, và mất hiệu lực nếu số tiền "
            "resolution thay đổi sau khi xin mã."
        ),
    }


@app.post("/resolutions/{resolution_id}/approve")
def approve_resolution(
    resolution_id: str,
    req: ApproveResolutionRequest,
    current_user: CurrentUser = Depends(require_role("supervisor")),
    session: Session = Depends(get_session),
):
    # AUTH5-06 — duyệt tài chính THẬT là 1 trong số Ít route cố ý trả giá 1
    # lần GET Redis/request để check revocation (xem rationale ở
    # src/auth.py::require_otp_verified) — không áp dụng qua require_role
    # dùng chung (sẽ ảnh hưởng MỌI route khác), gọi thẳng ở đây.
    if is_access_token_revoked(current_user.user_id, current_user.iat):
        raise HTTPException(status_code=401, detail="Phiên đã bị thu hồi — đăng nhập lại")
    resolution = session.get(Resolution, resolution_id)
    if resolution is None:
        raise HTTPException(status_code=404, detail="resolution không tồn tại")
    if resolution.status not in ("draft", "pending_approval"):
        raise HTTPException(
            status_code=400, detail=f"resolution đang ở trạng thái {resolution.status}, không duyệt được"
        )

    # AUTH5-05 — tra ĐÚNG challenge vừa xin (theo session_id, khoá chính — vá
    # race condition 2026-08-13, cùng lý do /auth/otp/verify), KHÔNG dùng
    # challenge "mới nhất" của user/resolution nữa (vừa mơ hồ dưới tải đồng
    # thời thật, vừa từng cho phép OTP xin cho case A duyệt được case B).
    auth_session = session.get(AuthSession, req.session_id)
    if (
        auth_session is None
        or auth_session.user_id != current_user.user_id
        or auth_session.resolution_id != resolution_id
        or auth_session.otp_code != req.otp_code
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "Cần xác thực OTP riêng cho resolution này trước khi duyệt "
                "(POST /resolutions/{id}/request-approval-otp rồi truyền otp_code vào approve)"
            ),
        )
    age_minutes = (dt.datetime.utcnow() - auth_session.created_at).total_seconds() / 60
    if age_minutes > RESOLUTION_APPROVAL_OTP_FRESH_MINUTES:
        raise HTTPException(status_code=403, detail="Mã OTP duyệt đã hết hạn — xin mã mới")
    # AUTH5-05B — dynamic linking: số tiền phải KHỚP snapshot lúc xin OTP, đổi
    # amount sau đó (CSKH sửa lại đề xuất) buộc sếp xin OTP mới cho số tiền mới.
    if auth_session.amount_snapshot != resolution.amount:
        raise HTTPException(
            status_code=403,
            detail="Số tiền resolution đã thay đổi kể từ lúc xin OTP — xin mã mới cho đúng số tiền hiện tại",
        )

    resolution.status = "approved"
    resolution.approved_by = current_user.user_id
    resolution.approved_at = dt.datetime.utcnow()
    _dong_bo_hitl_status(session, resolution)
    session.flush()
    return {"resolution_id": resolution_id, "status": resolution.status, "approved_by": current_user.user_id}


def _dong_bo_hitl_status(session: Session, resolution: Resolution) -> None:
    """Vá QA-02 — `Ticket.hitl_status` bám theo resolution MỚI NHẤT của ticket.

    Trước bản vá, cột này kẹt `pending` vĩnh viễn: cả hai nhánh duyệt/từ chối
    đều chỉ đổi `resolution.status` mà không chạm ticket. Hệ quả đo được: hàng
    chờ CSKH lọc theo `hitl_status` hiển thị sai, hai giá trị `approved`/
    `rejected` trong CHECK constraint không bao giờ đạt tới được, và guard
    "ticket đã ở trạng thái cuối" ở /tickets/{id}/request-more-info không bao
    giờ kích hoạt nổi.

    Chạy TRONG CÙNG transaction với lần đổi trạng thái resolution (không job
    nền) — đúng `dan_xuat.quy_tac` của contract v2.1.0. Hai trục vẫn TRỰC GIAO
    chứ không phải bản sao: `need_more_info` không có tương ứng bên resolution
    nên không bị hàm này ghi đè, và ticket chưa có resolution nào vẫn `pending`.
    """
    ticket = session.get(Ticket, resolution.ticket_id)
    if ticket is None:  # FK đã canh, nhánh này chỉ để không nổ nếu dữ liệu lệch
        return
    moi_nhat = session.scalars(
        select(Resolution)
        .where(Resolution.ticket_id == resolution.ticket_id)
        .order_by(Resolution.created_at.desc(), Resolution.resolution_id.desc())
        .limit(1)
    ).first()
    if moi_nhat is not None and moi_nhat.status in ("approved", "rejected"):
        ticket.hitl_status = moi_nhat.status
        ticket.updated_at = dt.datetime.utcnow()


@app.post("/resolutions/{resolution_id}/reject")
def reject_resolution(
    resolution_id: str,
    req: RejectResolutionRequest,
    current_user: CurrentUser = Depends(require_role("supervisor")),
    session: Session = Depends(get_session),
):
    """ADR-019 — từ chối PHẢI kèm lý do có cấu trúc. KHÔNG cần OTP (từ chối
    không chạm tiền, đúng contract), nhưng ghi đủ 3 trường kiểm toán đối xứng
    với nhánh duyệt: ai từ chối, lúc nào, vì sao."""
    if is_access_token_revoked(current_user.user_id, current_user.iat):
        raise HTTPException(status_code=401, detail="Phiên đã bị thu hồi — đăng nhập lại")
    resolution = session.get(Resolution, resolution_id)
    if resolution is None:
        raise HTTPException(status_code=404, detail="resolution không tồn tại")
    # CHỈ `pending_approval` — contract v2.1.0 liệt kê đúng một transition tới
    # `rejected`, không có đường từ `draft`. (Bản đầu của tôi copy danh sách
    # trạng thái từ nhánh duyệt nên lỡ cho phép cả draft; test tester viết TỪ
    # CONTRACT bắt được — đúng lý do vai đó không được đọc src/.)
    if resolution.status != "pending_approval":
        raise HTTPException(
            status_code=400,
            detail=f"resolution đang ở trạng thái {resolution.status}, không từ chối được",
        )

    resolution.status = "rejected"
    resolution.reject_reason = req.reason
    resolution.rejected_by = current_user.user_id
    resolution.rejected_at = dt.datetime.utcnow()
    _dong_bo_hitl_status(session, resolution)
    session.flush()
    return {
        "resolution_id": resolution_id,
        "status": resolution.status,
        "reject_reason": resolution.reject_reason,
        "rejected_by": resolution.rejected_by,
    }


# ---------------------------------------------------------------------------
# /resolutions — hàng chờ phê duyệt cho Sếp
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
# /tickets/{id}/request-more-info — CSKH yêu cầu điều tra thêm (US-012).
# Không phải HITL gate — không ghi approved, chỉ đổi hitl_status.
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
    # FIN05-StressTest-Plan-v4 S4-06 — phát hiện thật: route này KHÔNG có
    # guard trạng thái (khác approve_resolution/reject_resolution cùng file,
    # cả 2 đều chặn nếu resolution đã quyết) — CSKH có thể vô tình gọi lại
    # request-more-info trên 1 ticket ĐÃ approved/rejected, âm thầm lật
    # ngược về need_more_info, phá vỡ audit trail (ticket "đã xong" lại hiện
    # "cần thêm thông tin"). Chặn đúng 2 trạng thái cuối (terminal).
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
# /reports/summary — US-018, số liệu tính trực tiếp từ DB (PRD §12: không ước lượng)
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
# /policy-docs* — RAG chính sách/FAQ (src/rag/). Upload/xoá CHỈ role
# partner_admin (đối tác ví điện tử, tách khỏi supervisor nội bộ) — đây là
# actor duy nhất được đưa tài liệu mới vào hệ thống mà agent/CSKH sẽ tin
# tưởng, nên phân quyền chặt hơn các route /tools/* khác.
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
# /policy-search — công cụ tra cứu chính sách riêng cho CSKH (retrieval
# thuần, không qua LLM sinh câu trả lời — xem quyết định thiết kế trong
# plan). Dùng chung logic với tool search_policy của agent (src/rag/search.py).
# ---------------------------------------------------------------------------


@app.post("/policy-search")
def policy_search(
    req: PolicySearchRequest,
    current_user: CurrentUser = Depends(require_role("cskh", "supervisor")),
    session: Session = Depends(get_session),
):
    return _handle_tool_error(search_policy_text, session, query=req.query)


# ---------------------------------------------------------------------------
# Live chat (2026-08-11) — nâng cấp CTRL-001 từ ticket-flag bất đồng bộ lên
# chat 2 chiều thời gian thực. WS handshake dùng vé dùng-1-lần (ws-ticket,
# TTL ngắn) thay vì header Authorization: Bearer — browser không gắn được
# header tuỳ ý vào `new WebSocket(url)`, và JWT thật không bao giờ nhét vào
# query param. Xem src/api/live_chat_ws.py cho lý do không cần Redis + toàn
# bộ connection-manager.
# ---------------------------------------------------------------------------


@app.post("/live-chat/ws-ticket")
def live_chat_ws_ticket(
    req: LiveChatWsTicketRequest,
    current_user: CurrentUser = Depends(require_role("customer")),
    session: Session = Depends(get_session),
):
    # KHÔNG gác OTP ở đây (đã bỏ require_otp_view_fresh, phát hiện thật
    # 2026-08-11 qua test tay) — request_human_handoff (tool AI tạo ticket
    # dẫn tới route này) CỐ Ý không cần OTP vì đây chỉ là routing request,
    # không phải thao tác chạm dữ liệu (docstring tool trong customer_tools.py).
    # Bắt khách xác thực OTP CHỈ ĐỂ MỞ được cửa sổ chat sau khi đã được phép
    # yêu cầu người thật KHÔNG cần OTP là mâu thuẫn logic — và vì lỗi 403 bị
    # nuốt âm thầm ở frontend (không có UI hiển thị), khách bấm "gặp người
    # thật" xong không thấy gì xảy ra, tưởng tính năng hỏng. Nhất quán với
    # request_human_handoff: mở phiên chat không tự nó là hành động nhạy cảm,
    # nội dung nhạy cảm (nếu có) nằm ở tin nhắn trong hội thoại, không phải ở
    # việc mở kết nối.
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
    """CSKH mở panel chat cho 1 ticket đã human_handoff_requested — cần biết
    chat_session_id để claim/tham gia, không tự nhớ (frontend không lưu id
    này lâu dài, khách là bên tạo phiên qua ws-ticket). LẤY PHIÊN GẦN NHẤT
    BẤT KỂ STATUS (kể cả 'closed') — phát hiện thật 2026-08-11: khách F5/
    thoát khi đang chat khiến phiên tự đóng (xem release_staff_sessions/
    close_customer_session_on_disconnect), nhưng CSKH mở lại ticket đó vẫn
    cần thấy lịch sử hội thoại + số điện thoại khách để liên hệ lại, không
    chỉ khi phiên còn 'waiting'/'active'. Trả kèm context (có SĐT khách)
    LUÔN LUÔN — trước đây chỉ đẩy qua WS lúc claim thành công, CSKH mở ticket
    có phiên đã đóng sẽ không bao giờ nhận được claim_success nên không thấy
    được SĐT."""
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
    """Lịch sử tin nhắn thật của 1 phiên — trước đây KHÔNG có route nào đọc
    lại bảng `messages`, chỉ có push realtime qua WS lúc đang mở kết nối.
    CSKH mở lại 1 ticket có phiên đã đóng (khách đã thoát) cần xem LẠI ĐƯỢC
    nội dung khách đã gõ trước khi rời đi, không chỉ biết "khách từng muốn
    gặp người thật" một cách chung chung."""
    chat_session = session.get(ChatSession, chat_session_id)
    if chat_session is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên chat")
    if current_user.role == "customer" and chat_session.customer_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Phiên chat này không thuộc về bạn")
    messages = session.scalars(
        select(Message).where(Message.chat_session_id == chat_session_id).order_by(Message.created_at)
    ).all()
    return {
        "messages": [
            {"message_id": m.message_id, "role": m.role, "content": m.content, "created_at": m.created_at.isoformat()}
            for m in messages
        ]
    }


@app.get("/live-chat/sessions/waiting")
async def live_chat_sessions_waiting(
    current_user: CurrentUser = Depends(require_role("cskh", "supervisor")),
    session: Session = Depends(get_session),
):
    # Dọn lười (lazy sweep) phiên 'waiting' mồ côi TRƯỚC khi trả danh sách —
    # phát hiện thật 2026-08-11: khách đăng xuất/mất mạng đột ngột có thể
    # không gửi được khung đóng kết nối WS, phiên treo mãi ở hàng chờ dù
    # khách đã đi từ lâu (xem sweep_stale_waiting_sessions).
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
        live_chat.claim_session, session, chat_session_id=chat_session_id, staff_id=current_user.user_id
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
    """CSKH kết thúc phiên chat — khách được chuyển sang màn hình đánh giá
    CSAT ngay (broadcast "closed" tới participant của phiên qua WS)."""
    chat_session = session.get(ChatSession, chat_session_id)
    if chat_session is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên chat")
    closed = _handle_tool_error(live_chat.close_session, session, chat_session_id=chat_session_id)
    await _live_chat_manager.send_to_session(chat_session_id, {"type": "session_closed", "chat_session_id": chat_session_id})
    return closed


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


@app.on_event("startup")
async def _khoi_dong_fanout_live_chat():
    """Chạy nền vòng lặp nhận fan-out live-chat từ worker khác (ADR-015).

    KHÔNG có nó thì bật multi-worker sẽ làm live-chat vỡ ÂM THẦM: khách ở
    worker 1, CSKH ở worker 2, tin nhắn mỗi bên chỉ tới socket cùng worker —
    không lỗi nào được ném ra, chỉ là tin nhắn biến mất.
    """
    import asyncio

    from src.api.live_chat_ws import _vong_lap_subscriber

    app.state.live_chat_subscriber = asyncio.create_task(
        _vong_lap_subscriber(_live_chat_manager)
    )


@app.on_event("shutdown")
def _dong_tai_nguyen_khi_tat():
    """Graceful shutdown — đóng pool checkpointer (ADR-014).

    ConnectionPool của psycopg chạy thread nền; không đóng tường minh sẽ ném
    PythonFinalizationError lúc interpreter thoát, và giữ kết nối Postgres cho
    tới khi TCP timeout — ăn vào max_connections khi deploy liên tục.
    """
    close_checkpointer()
    tac_vu = getattr(app.state, "live_chat_subscriber", None)
    if tac_vu is not None:
        tac_vu.cancel()


@app.get("/health")
def health():
    """Liveness — CỐ Ý không chạm DB/Redis (readiness mới được phép).

    Trả kèm ĐỊNH DANH MÔI TRƯỜNG (2026-08-13) để nhìn là biết đang nói chuyện
    với stack nào, không phải suy từ số cổng. Sinh ra sau sự cố thật: Docker
    stack (Postgres) và stack dev cục bộ (SQLite) chạy song song, hai cửa sổ
    trình duyệt giống hệt nhau nhưng khác database — xem ghi chú ở
    src/config.py và ADR-009.

    `db_kind`/`db_name` chỉ là scheme + tên database, KHÔNG có host/user/mật
    khẩu (endpoint này công khai, không yêu cầu xác thực).
    """
    return {
        "status": "ok",
        "env": APP_ENV,
        "db_kind": DB_KIND,
        "db_name": DB_NAME,
    }
