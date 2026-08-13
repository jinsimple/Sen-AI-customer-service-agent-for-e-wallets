"""FIN05-StressTest-Plan-v2 — Nhóm A (auth) trên `/auth/login`.

ST2-A-01/A-02/A-03: rate-limit + JWT tampered/expired — gap thật, chưa có
test nào chạm `/auth/login` qua HTTP trước file này.

AUTH5-08 (đợt nâng cấp Auth Flow 2026-08-12) — `/auth/login` giờ đăng nhập
bằng MẬT KHẨU thật (`LoginRequest` có `password`, không còn `role` — xem
src/api/schemas.py). Rate-limit khoá theo PHONE (không còn theo IP —
ST2-P0-4 cũ đã vá, xem src/api/main.py::_login_phone_limiter/_login_ip_limiter).
"""
from __future__ import annotations

import datetime as dt

import jwt
import pytest
from fastapi.testclient import TestClient

from src.api.deps import get_session
from src.api.main import app
from src.auth import create_access_token
from src.config import JWT_ALGORITHM, JWT_SECRET_KEY

# Khớp password_hash mà tests/conftest.py::sample_db gán cho mọi user fixture.
_TEST_PASSWORD = "Demo@123"


@pytest.fixture()
def client(sample_db):
    def _override_session():
        try:
            yield sample_db
            sample_db.commit()
        except Exception:
            sample_db.rollback()
            raise

    app.dependency_overrides[get_session] = _override_session
    # slowapi Limiter là singleton module-level (src/api/main.py::limiter) —
    # state rate-limit sống SUỐT phiên pytest nếu không reset, làm test sau
    # phụ thuộc thứ tự chạy của test trước (phát hiện thật lúc viết file
    # này: chưa test nào trước đây chạm /auth/login qua HTTP nên chưa lộ ra).
    app.state.limiter.reset()
    yield TestClient(app)
    app.state.limiter.reset()
    app.dependency_overrides.clear()


def test_login_rate_limit_triggers_after_threshold(client):
    """ST2-A-01 — đúng ngưỡng 10/phút (RedisSlidingWindowLimiter theo phone,
    src/api/main.py::_login_phone_limiter)."""
    for _ in range(10):
        resp = client.post("/auth/login", json={"phone": "0901000001", "password": _TEST_PASSWORD})
        assert resp.status_code == 200
    blocked = client.post("/auth/login", json={"phone": "0901000001", "password": _TEST_PASSWORD})
    assert blocked.status_code == 429


def test_login_rate_limit_shared_across_different_users_behind_same_ip(client):
    """AUTH5-08 — rate-limit `/auth/login` khoá theo PHONE, không theo IP
    (ST2-P0-4 cũ đã vá). Khách A spam SAI MẬT KHẨU (401, vẫn tính vào
    rate-limit của CHÍNH SỐ 0901000001) tới ngưỡng, khách B (số điện thoại
    KHÁC hoàn toàn, cùng IP nguồn trong môi trường test) đăng nhập ĐÚNG lần
    đầu tiên KHÔNG bị khoá theo — vì khoá theo phone, không theo IP."""
    for _ in range(10):
        resp = client.post("/auth/login", json={"phone": "0901000001", "password": "sai-mat-khau"})
        assert resp.status_code == 401  # sai mật khẩu — vẫn tính vào rate-limit theo phone 0901000001

    user_b_first_attempt = client.post("/auth/login", json={"phone": "0901000002", "password": _TEST_PASSWORD})
    assert user_b_first_attempt.status_code != 429, (
        "Khách B (0901000002) chưa từng gọi request nào trước đó nhưng vẫn "
        "bị 429 — regression: rate-limit /auth/login đã quay lại khoá theo "
        "IP thay vì phone."
    )


def test_login_wrong_password_rejected(client):
    resp = client.post("/auth/login", json={"phone": "0901000001", "password": "sai-mat-khau"})
    assert resp.status_code == 401
    assert "mật khẩu" in resp.json()["detail"].lower()


def test_login_unknown_phone_returns_same_error_as_wrong_password(client):
    """Chống dò số điện thoại đã đăng ký qua thông điệp lỗi khác nhau — số
    điện thoại KHÔNG tồn tại phải trả về ĐÚNG cùng 1 câu lỗi với sai mật khẩu
    (không phải "không tìm thấy user" riêng biệt), xem
    src/api/main.py::login _DUMMY_PASSWORD_HASH."""
    unknown = client.post("/auth/login", json={"phone": "0999999999", "password": _TEST_PASSWORD})
    wrong_password = client.post("/auth/login", json={"phone": "0901000001", "password": "sai-mat-khau"})
    assert unknown.status_code == wrong_password.status_code == 401
    assert unknown.json()["detail"] == wrong_password.json()["detail"]


def test_login_correct_password_returns_role_from_db_not_client(client):
    """AUTH5-08 — LoginRequest không còn field role; vai trò PHẢI đến từ user
    tìm được qua phone trong DB."""
    resp = client.post("/auth/login", json={"phone": "0901000003", "password": _TEST_PASSWORD})  # USR-CSKH
    assert resp.status_code == 200, resp.text
    assert resp.json()["role"] == "cskh"


def test_tampered_signature_jwt_returns_401(client):
    """ST2-A-02 — khác test_fake_token_returns_401 có sẵn (chuỗi rác hoàn
    toàn): đây là JWT ĐÚNG cấu trúc, ký bằng secret SAI — mô phỏng kẻ tấn
    công cố sửa payload (đổi role/user_id) rồi tự ký lại bằng key đoán mò."""
    now = dt.datetime.utcnow()
    tampered = jwt.encode(
        {"sub": "USR-A", "role": "supervisor", "iat": now, "exp": now + dt.timedelta(hours=1)},
        "khong-phai-secret-that",
        algorithm=JWT_ALGORITHM,
    )
    resp = client.get("/tickets", headers={"Authorization": f"Bearer {tampered}"})
    assert resp.status_code == 401


def test_expired_jwt_returns_401_not_500(client):
    """ST2-A-03 — JWT ký ĐÚNG secret thật nhưng `exp` đã ở quá khứ."""
    now = dt.datetime.utcnow()
    expired = jwt.encode(
        {"sub": "USR-CSKH", "role": "cskh", "iat": now - dt.timedelta(hours=9), "exp": now - dt.timedelta(hours=1)},
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )
    resp = client.get("/tickets", headers={"Authorization": f"Bearer {expired}"})
    assert resp.status_code == 401


def test_valid_token_still_works_after_expired_token_test(client):
    """Bảo vệ khỏi false-negative: nếu 2 test JWT ở trên PASS chỉ vì toàn bộ
    route lỗi (vd get_session override hỏng) chứ không phải do check JWT
    thật, test tích cực này sẽ lộ ra ngay (token hợp lệ phải luôn qua)."""
    token = create_access_token(user_id="USR-CSKH", role="cskh")
    resp = client.get("/tickets", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
