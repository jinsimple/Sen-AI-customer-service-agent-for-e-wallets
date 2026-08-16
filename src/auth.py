"""JWT — thay cho việc mọi route tin thẳng `user_id`/`approved_by`/... do
client tự khai trong body (lỗ hổng mạo danh — bất kỳ ai gọi API cũng tự xưng
là user bất kỳ). Sau khi vá: danh tính người gọi LUÔN lấy từ token đã ký,
KHÔNG BAO GIỜ từ body request.

Luồng: POST /auth/login xác thực phone+role → phát access_token. Mọi route
cần danh tính khai báo `current_user: CurrentUser = Depends(get_current_user)`
(hoặc `Depends(require_role("supervisor"))` khi cần đúng 1 role) thay vì nhận
tham số user_id/approved_by/... từ Pydantic request body.
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
    iat: int  # timestamp lúc đăng nhập — dùng làm mã định danh PHIÊN đăng nhập
    # (khác lần đăng nhập khác nhau -> iat khác nhau), xem run_agent_turn()
    # thread_id trong src/api/main.py::agent_chat.
    otp_verified_at: int | None = None  # timestamp lúc qua /auth/otp/verify
    # gần nhất — None nghĩa là chưa từng xác thực trong phiên này. Lưu thời
    # điểm (không phải bool) để tính "còn tươi không" theo TỪNG loại thao tác
    # (xem otp_fresh_within) — quyết định sau khi đối chiếu chuẩn ngành
    # NIST 800-63B/step-up authentication (docs/TESTING.md, 2026-08-10):
    # thao tác chỉ xem chấp nhận cửa sổ dài hơn (12h) so với thao tác có hậu
    # quả tài chính như create_ticket (15 phút, "step-up" phải tươi hơn).

    def otp_fresh_within(self, max_minutes: int) -> bool:
        if self.otp_verified_at is None:
            return False
        age_minutes = (dt.datetime.utcnow().timestamp() - self.otp_verified_at) / 60
        return age_minutes <= max_minutes


def create_access_token(
    *, user_id: str, role: str, otp_verified_at: dt.datetime | None = None, iat: dt.datetime | None = None
) -> str:
    """`iat` truyền tay khi CẤP LẠI token lúc xác thực OTP xong (giữ nguyên
    `iat` gốc lúc login, KHÔNG phát sinh timestamp mới) — nếu không, `iat` mới
    sẽ đổi `thread_id` hội thoại (user_id:iat, xem src/agents/graph.py) giữa
    chừng phiên chat, làm agent "quên" ngữ cảnh đã nói trước khi xác thực."""
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
# Refresh token (AUTH5-02/02B/02C/03/03B, đợt nâng cấp Auth Flow 2026-08-12)
# — KHÔNG phải JWT: chuỗi ngẫu nhiên (secrets.token_urlsafe, cùng pattern
# ws-ticket đã có ở src/api/live_chat_ws.py), server lưu trạng thái trong
# Redis (khoá theo hash — không lưu token thô, cùng nguyên tắc "không lưu bí
# mật dạng thô" đã áp dụng cho câu trả lời bảo mật). Cho phép REVOKE thật sự
# (JWT thuần không thu hồi được nếu không tra cứu state phía server) và ROTATE
# + REUSE DETECTION: mỗi lần dùng phát hành token mới, token cũ dùng lại lần 2
# coi là dấu hiệu bị đánh cắp -> thu hồi toàn bộ "family" (mọi token sinh ra
# từ cùng 1 lần đăng nhập gốc), buộc đăng nhập lại.
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
    """`family_id` truyền tay khi ROTATE (giữ nguyên gia đình gốc) — để trống
    khi mint lần đầu (login/verify_otp), tự sinh family mới."""
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


# TẦNG 0 (security 2cff494) — `auth.py` trước bản này KHÔNG CÓ MỘT DÒNG LOG
# NÀO trong 294 dòng, kể cả `revoke_family()` — tức sự kiện "refresh token bị
# dùng lại, nghi đánh cắp, thu hồi cả phiên" bắn HOÀN TOÀN IM LẶNG.
#
# Vì sao log TRƯỚC khi vá: chỉnh một control mà không quan sát được nó bắn khi
# nào là CHỈNH MÙ. Và ngay lúc này nó còn là con MẮT để nhìn chính cái bug đang
# truy (đua-refresh ở handoff) — không có nó thì "phiên chết" và "token bị đánh
# cắp thật" nhìn từ ngoài giống hệt nhau.
_logger = get_logger("fin05.auth")

# Nhãn NHÁNH bắn thu hồi. Dùng contextvar thay vì thêm tham số vào
# `revoke_family()` vì hàm đó là API công khai của module — thêm tham số bắt
# buộc sẽ vỡ mọi call-site tương lai và cám dỗ người ta truyền bừa một chuỗi.
# Hôm nay chỉ có MỘT nhánh (`reuse_that`); tầng 2 sẽ thêm `phat_lai_trong_grace`
# nếu grace-window được land.
_nhanh_thu_hoi: contextvars.ContextVar[str] = contextvars.ContextVar("nhanh_thu_hoi", default="khong_ro")


def revoke_family(family_id: str, *, role: str) -> None:
    """Thu hồi TOÀN BỘ family — gọi khi phát hiện refresh token bị dùng lại
    sau khi đã rotate (AUTH5-03, dấu hiệu bị đánh cắp). Key tự hết hạn theo
    đúng TTL refresh (không cần enumerate/xoá tay từng token con)."""
    get_default_client().setex(f"revoked_family:{family_id}", _refresh_ttl_seconds(role), "1")
    # WARNING chứ không INFO: đây là sự kiện bảo mật, phải nổi lên trong mọi
    # bộ lọc mặc định. KHÔNG log token (kể cả bản băm) — family_id đủ để nối
    # các sự kiện của cùng một phiên mà không tự tạo thêm một bí mật để rò.
    _logger.warning(
        "refresh_family_revoked",
        extra={
            "su_kien": "refresh_family_revoked",
            "family_id": family_id,
            "role": role,
            "nhanh": _nhanh_thu_hoi.get(),
        },
    )


def rotate_refresh_token(token: str) -> dict | None:
    """Trả None nếu token không hợp lệ/hết hạn/family đã bị thu hồi (kể cả
    do reuse detection ở CHÍNH lần gọi này). Trả dict access_token/
    refresh_token/user_id/role nếu hợp lệ."""
    client = get_default_client()
    key = f"refresh:{_hash_token(token)}"
    raw = client.get(key)
    if raw is None:
        return None
    data = json.loads(raw)
    if is_family_revoked(data["family_id"]):
        return None
    if data.get("rotated"):
        # AUTH5-03 — token NÀY đã được dùng để rotate trước đó, mà giờ lại bị
        # dùng lại lần nữa -> chỉ có thể do bị sao chép/đánh cắp (client hợp
        # pháp đã nhận token MỚI và không còn lý do gì dùng lại token cũ).
        _nhanh_thu_hoi.set("reuse_that")
        revoke_family(data["family_id"], role=data["role"])
        return None

    # Đánh dấu ROTATED thay vì xoá ngay — giữ lại NGẮN (60s) đủ để bắt được
    # request thứ 2 dùng lại (reuse), tự dọn qua TTL, không cần cron riêng.
    data["rotated"] = True
    client.setex(key, 60, json.dumps(data))
    # Log NHÁNH THÀNH CÔNG, không chỉ nhánh thu hồi — thiếu vế này thì log của
    # tầng 0 KHÔNG định được N cho grace-window.
    #
    # Lý do: N là khoảng cách giữa hai lượt refresh đua nhau, và security đã
    # chốt N chỉ được lấy từ DẤU THỜI GIAN SERVER-SIDE (khoảng cách đo ở client
    # là hiện vật của công cụ đo — spawn curl/tab — không phải của sản phẩm).
    # Nhưng `revoke_family` chỉ bắn ở đứa THUA. Có một mốc thì không có khoảng
    # cách nào để đo. Cặp `refresh_rotated` -> `refresh_family_revoked` CÙNG
    # `family_id` mới cho ra N.
    #
    # INFO chứ không WARNING: rotate thành công là chuyện bình thường xảy ra
    # liên tục, đẩy lên WARNING là làm loãng đúng cái cảnh báo ở nhánh kia.
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
    """Logout — xoá 1 refresh token cụ thể (KHÔNG xoá cả family, chỉ phiên
    đăng xuất hiện tại; các thiết bị khác vẫn đăng nhập bình thường)."""
    get_default_client().delete(f"refresh:{_hash_token(token)}")


def set_revoked_before_now(user_id: str) -> None:
    """AUTH5-06 — mọi access token có `iat` CŨ HƠN mốc này coi như bị thu hồi
    ngay, không chờ hết hạn tự nhiên (xem is_access_token_revoked). Gọi lúc
    logout/xác thực OTP xong (token mới thay thế token cũ)."""
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
    """Dependency dùng cho MỌI route cần biết chính xác ai đang gọi. Không
    có header Authorization hợp lệ -> 401 ngay, không suy đoán."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Thiếu Authorization: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _decode(credentials.credentials)


def try_decode(token: str) -> CurrentUser | None:
    """Bản không raise của _decode — chỉ dùng cho mục đích phụ trợ (audit
    log ghi ai gọi API), KHÔNG dùng để gác quyền. Gác quyền luôn phải qua
    get_current_user/require_role để lỗi 401/403 trả về đúng cho client."""
    try:
        return _decode(token)
    except HTTPException:
        return None


def require_role(*allowed_roles: str):
    """Factory dependency — ép đúng role thay vì tin `role` client tự khai.
    VD: Depends(require_role("supervisor")) cho route duyệt hoàn tiền."""

    def _dep(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cần role thuộc {sorted(allowed_roles)}, tài khoản hiện tại là {current_user.role}",
            )
        return current_user

    return _dep


def require_otp_verified(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Gác các route CHẠM dữ liệu giao dịch/tài khoản nhạy cảm (Brief §7 #4:
    OTP phiên trước thao tác nhạy cảm — AUTH5-01, 2026-08-12: KHÔNG còn kèm
    câu hỏi bảo mật, KBA đã bỏ khỏi vai trò authenticator). TRƯỚC bản vá này,
    OTP chỉ là gate UI ở frontend (`ChatClient.tsx`) — backend không kiểm tra
    gì cả, nghĩa là gọi thẳng API (curl/Postman) với JWT hợp lệ vẫn lấy được
    dữ liệu nhạy cảm mà không cần xác thực OTP — phát hiện thật khi đối chiếu
    bộ QA test AUTH-*. KHÔNG gắn dependency này vào toàn bộ /agent/chat (sẽ
    chặn cả câu hỏi chung, phá AUTH-004) — chỉ gắn vào route THỰC SỰ chạm dữ
    liệu: lookup_transaction, get_customer_history, create_ticket.

    CHỈ áp cho role `customer` — CSKH/supervisor/partner_admin không đi qua
    luồng OTP khách hàng, danh tính của họ đã được xác lập qua đăng nhập nhân
    viên riêng (`require_role`), không cần thêm lớp OTP (vd CSKH tra cứu
    `lookup_transaction` khi xử lý ticket — route này cho phép mọi role).

    Dependency này CHỈ gắn vào /tools/create_ticket (hành động có hậu quả tài
    chính thật) nên dùng ngưỡng step-up CHẶT hơn (OTP_STEPUP_FRESH_MINUTES,
    xem src/config.py) — quyết định AUTH-008 (2026-08-10): create_ticket cần
    xác thực TƯƠI HƠN thao tác chỉ xem.

    AUTH5-06 (2026-08-12) — thêm check revocation Ở ĐÂY (route nhạy cảm nhất
    của khách hàng), KHÔNG áp cho toàn bộ route thường qua get_current_user —
    quyết định có chủ đích: access token đã rất ngắn hạn (15 phút), thêm 1 lần
    GET Redis vào MỌI request sẽ biến Redis thành single point of failure cho
    cả hệ thống trong khi lợi ích biên rất nhỏ; route CHẠM DỮ LIỆU/TÀI CHÍNH
    thật xứng đáng trả giá đó, route đọc thường thì không."""
    if current_user.role == "customer" and not current_user.otp_fresh_within(OTP_STEPUP_FRESH_MINUTES):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cần xác thực OTP phiên làm việc trước khi thao tác này (POST /auth/otp/request rồi /auth/otp/verify)",
        )
    if is_access_token_revoked(current_user.user_id, current_user.iat):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Phiên đã bị thu hồi — đăng nhập lại")
    return current_user
