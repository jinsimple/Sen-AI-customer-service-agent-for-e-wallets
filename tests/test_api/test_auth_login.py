"""FIN05-StressTest-Plan-v2 — Nhóm A (auth) trên `/auth/login` chưa có test
riêng trước đây (chỉ OTP có test_otp.py). `LoginRequest` không có mật khẩu
(`src/api/schemas.py:58` — chỉ phone+role, xem docstring) nên "đoán thông
tin đăng nhập" ở đây nghĩa là đoán phone, không phải brute-force password.

ST2-A-01/A-02/A-03: rate-limit + JWT tampered/expired — gap thật, chưa có
test nào chạm `/auth/login` qua HTTP trước file này.

ST2-P0-4 (docs/FIN05-Feature-Inventory-Security-Review.md §11): rate-limit
`10/minute` khoá theo `get_remote_address` (IP) — mọi khách hàng thật đều đi
qua CHUNG 1 container `frontend` (kiến trúc BFF), nên trên thực tế đây là
giới hạn DÙNG CHUNG cho toàn bộ khách, không phải riêng từng người. Test này
khẳng định HÀNH VI AN TOÀN MONG MUỐN (rate-limit phải tách theo user, không
để 1 người dùng bị khoá vì hành vi của người khác) — FAIL NGAY hôm nay, cố
tình, không tự sửa `src/api/main.py` cùng lúc.
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
    """ST2-A-01 — đúng ngưỡng 10/phút khai báo ở src/api/main.py:197."""
    for _ in range(10):
        resp = client.post("/auth/login", json={"phone": "0901000001", "role": "customer"})
        assert resp.status_code == 200
    blocked = client.post("/auth/login", json={"phone": "0901000001", "role": "customer"})
    assert blocked.status_code == 429


@pytest.mark.security_finding
def test_login_rate_limit_shared_across_different_users_behind_same_ip(client):
    """ST2-P0-4 — khách A tự spam sai role (401, nhưng vẫn tính vào rate-limit
    vì slowapi đếm request bất kể status) tới ngưỡng, khách B (số điện thoại
    KHÁC hoàn toàn, chưa từng gọi request nào) đăng nhập ĐÚNG lần đầu tiên
    vẫn bị khoá theo — vì cả 2 cùng đi qua 1 IP nguồn trong môi trường test
    (đúng thực tế production: cùng đi qua 1 container `frontend`)."""
    for _ in range(10):
        resp = client.post("/auth/login", json={"phone": "0901000001", "role": "cskh"})
        assert resp.status_code == 401  # sai role — vẫn tính vào rate-limit

    user_b_first_attempt = client.post("/auth/login", json={"phone": "0901000002", "role": "customer"})
    assert user_b_first_attempt.status_code != 429, (
        "Khách B (0901000002) chưa từng gọi request nào trước đó nhưng vẫn "
        "bị 429 vì rate-limit khoá theo IP (get_remote_address), không theo "
        "user — 1 IP nguồn chung (đúng kiến trúc BFF thật) khiến giới hạn "
        "thực chất là DÙNG CHUNG cho mọi khách, không phải riêng từng người. "
        "Cần đổi key rate-limit sang theo định danh user/phone thay vì IP "
        "cho route /auth/login — xem "
        "docs/FIN05-Feature-Inventory-Security-Review.md §11."
    )


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
