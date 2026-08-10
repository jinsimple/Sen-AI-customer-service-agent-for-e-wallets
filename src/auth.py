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

from src.config import JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_SECRET_KEY

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    role: str
    iat: int  # timestamp lúc đăng nhập — dùng làm mã định danh PHIÊN đăng nhập
    # (khác lần đăng nhập khác nhau -> iat khác nhau), xem run_agent_turn()
    # thread_id trong src/api/main.py::agent_chat.


def create_access_token(*, user_id: str, role: str) -> str:
    now = dt.datetime.utcnow()
    payload = {
        "sub": user_id,
        "role": role,
        "iat": now,
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
    return CurrentUser(user_id=user_id, role=role, iat=int(iat))


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
