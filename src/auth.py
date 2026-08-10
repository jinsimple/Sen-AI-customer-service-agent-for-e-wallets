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

import datetime as dt
from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.config import JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_SECRET_KEY, OTP_STEPUP_FRESH_MINUTES

_bearer = HTTPBearer(auto_error=False)


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
        "exp": now + dt.timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


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
    OTP phiên + câu hỏi bảo mật trước thao tác nhạy cảm). TRƯỚC bản vá này, OTP
    chỉ là gate UI ở frontend (`ChatClient.tsx`) — backend không kiểm tra gì cả,
    nghĩa là gọi thẳng API (curl/Postman) với JWT hợp lệ vẫn lấy được dữ liệu
    nhạy cảm mà không cần xác thực OTP — phát hiện thật khi đối chiếu bộ QA
    test AUTH-*. KHÔNG gắn dependency này vào toàn bộ /agent/chat (sẽ chặn cả
    câu hỏi chung, phá AUTH-004) — chỉ gắn vào route THỰC SỰ chạm dữ liệu:
    lookup_transaction, get_customer_history, create_ticket.

    CHỈ áp cho role `customer` — CSKH/supervisor/partner_admin không đi qua
    luồng OTP khách hàng, danh tính của họ đã được xác lập qua đăng nhập nhân
    viên riêng (`require_role`), không cần thêm lớp OTP (vd CSKH tra cứu
    `lookup_transaction` khi xử lý ticket — route này cho phép mọi role).

    Dependency này CHỈ gắn vào /tools/create_ticket (hành động có hậu quả tài
    chính thật) nên dùng ngưỡng step-up CHẶT hơn (OTP_STEPUP_FRESH_MINUTES,
    xem src/config.py) — quyết định AUTH-008 (2026-08-10): create_ticket cần
    xác thực TƯƠI HƠN thao tác chỉ xem."""
    if current_user.role == "customer" and not current_user.otp_fresh_within(OTP_STEPUP_FRESH_MINUTES):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cần xác thực OTP phiên làm việc + câu hỏi bảo mật trước khi thao tác này (POST /auth/otp/request rồi /auth/otp/verify)",
        )
    return current_user
