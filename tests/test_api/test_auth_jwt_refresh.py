"""AUTH5-02/02B/02C/03/03B/06/MIGRATE-001/002 (đợt nâng cấp Auth Flow,
2026-08-12) — JWT access token ngắn hạn (15 phút) + refresh token rotation/
reuse-detection/revocation trên Redis (src/auth.py, xem docstring module đó
để biết thiết kế đầy đủ, đặc biệt gotcha `iat` giữ nguyên qua refresh để
không phá `thread_id` hội thoại AI — src/agents/graph.py).
"""
from __future__ import annotations

import jwt
import pytest
from fastapi.testclient import TestClient

from src.api.deps import get_session
from src.api.main import app
from src.auth import create_access_token, mint_refresh_token
from src.config import (
    JWT_ACCESS_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_REFRESH_EXPIRE_DAYS_CUSTOMER,
    JWT_REFRESH_EXPIRE_DAYS_STAFF,
    JWT_SECRET_KEY,
)
from src.redis_client import get_default_client

# Đăng nhập bằng mật khẩu (quyết định 2026-08-12) — khớp password_hash mà
# tests/conftest.py::sample_db gán cho mọi user fixture (TEST_PASSWORD).
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
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_access_token_expires_in_15_minutes():
    """AUTH5-02 — rút từ 8h (cũ) xuống JWT_ACCESS_EXPIRE_MINUTES=15."""
    token = create_access_token(user_id="USR-A", role="customer")
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    lifetime_minutes = (payload["exp"] - payload["iat"]) / 60
    assert lifetime_minutes == pytest.approx(JWT_ACCESS_EXPIRE_MINUTES, abs=0.01)
    assert JWT_ACCESS_EXPIRE_MINUTES == 15


def test_login_response_includes_refresh_token(client):
    resp = client.post("/auth/login", json={"phone": "0901000001", "password": _TEST_PASSWORD})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["refresh_token"]
    # AUTH5-02C — refresh_token KHÔNG phải JWT (chuỗi ngẫu nhiên đơn giản,
    # không có cấu trúc 3-phần header.payload.signature).
    assert body["refresh_token"].count(".") == 0
    assert body["refresh_token"] != body["access_token"]


def test_refresh_rotates_token_and_old_one_stops_working(client):
    """AUTH5-03 — refresh token CŨ (đã dùng để rotate) không dùng lại được."""
    login = client.post("/auth/login", json={"phone": "0901000001", "password": _TEST_PASSWORD}).json()
    first_refresh = login["refresh_token"]

    rotated = client.post("/auth/refresh", json={"refresh_token": first_refresh})
    assert rotated.status_code == 200, rotated.text
    new_body = rotated.json()
    # KHÔNG assert access_token khác chuỗi cũ — JWT là hàm THUẦN của payload+
    # secret, login và refresh xảy ra trong CÙNG 1 giây thực tế có thể ra
    # payload (iat/exp) giống hệt (iat PHẢI giữ nguyên, xem test riêng
    # test_refresh_preserves_original_iat_for_thread_continuity), nên chữ ký
    # trùng nhau là HỢP LỆ, không phải bug. Chỉ refresh_token (chuỗi ngẫu
    # nhiên, không phụ thuộc payload) chắc chắn phải đổi.
    assert new_body["refresh_token"] != first_refresh

    reuse_attempt = client.post("/auth/refresh", json={"refresh_token": first_refresh})
    assert reuse_attempt.status_code == 401


def test_refresh_token_reuse_revokes_whole_family(client):
    """AUTH5-03 — dùng lại refresh token CŨ (đã rotate) không chỉ tự nó bị từ
    chối, mà còn kéo theo THU HỒI CẢ token MỚI đã phát ra từ lần rotate đó
    (dấu hiệu bị đánh cắp -> không tin bất kỳ token nào trong family nữa)."""
    login = client.post("/auth/login", json={"phone": "0901000001", "password": _TEST_PASSWORD}).json()
    first_refresh = login["refresh_token"]

    rotated = client.post("/auth/refresh", json={"refresh_token": first_refresh}).json()
    second_refresh = rotated["refresh_token"]

    # Dùng lại token CŨ (reuse) -> kích hoạt thu hồi cả family.
    reuse = client.post("/auth/refresh", json={"refresh_token": first_refresh})
    assert reuse.status_code == 401

    # token MỚI (hợp pháp, chưa từng bị lộ) giờ CŨNG không dùng được nữa.
    legit_second_use = client.post("/auth/refresh", json={"refresh_token": second_refresh})
    assert legit_second_use.status_code == 401, (
        "Reuse detection phải thu hồi CẢ family, không chỉ token bị dùng lại — "
        "nếu không, kẻ đánh cắp token cũ không gây hại gì thêm nhưng nạn nhân "
        "hợp pháp vẫn coi như an toàn dù thực ra đã bị lộ."
    )


def test_refresh_preserves_original_iat_for_thread_continuity(client):
    """`thread_id` hội thoại AI = user_id:iat (src/agents/graph.py) — refresh
    KHÔNG được đổi `iat`, nếu không agent "mất trí nhớ" hội thoại giữa chừng
    mỗi lần access token tự làm mới (~15 phút/lần, tần suất cao hơn hẳn OTP)."""
    login = client.post("/auth/login", json={"phone": "0901000001", "password": _TEST_PASSWORD}).json()
    original_iat = jwt.decode(login["access_token"], JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])["iat"]

    rotated = client.post("/auth/refresh", json={"refresh_token": login["refresh_token"]}).json()
    new_iat = jwt.decode(rotated["access_token"], JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])["iat"]

    assert new_iat == original_iat


def test_refresh_ttl_differs_by_role(sample_db):
    """AUTH5-02B — role nội bộ (rủi ro cao hơn) có TTL refresh NGẮN HƠN hẳn
    khách hàng. Đọc thẳng TTL thật trong Redis (fakeredis ở test), không suy
    đoán từ config."""
    customer_token = mint_refresh_token(user_id="USR-A", role="customer", login_iat=0, otp_verified_at=None)
    staff_token = mint_refresh_token(user_id="USR-SUP", role="supervisor", login_iat=0, otp_verified_at=None)

    client_redis = get_default_client()
    import hashlib

    customer_ttl = client_redis.ttl(f"refresh:{hashlib.sha256(customer_token.encode()).hexdigest()}")
    staff_ttl = client_redis.ttl(f"refresh:{hashlib.sha256(staff_token.encode()).hexdigest()}")

    assert customer_ttl == pytest.approx(JWT_REFRESH_EXPIRE_DAYS_CUSTOMER * 86400, abs=5)
    assert staff_ttl == pytest.approx(JWT_REFRESH_EXPIRE_DAYS_STAFF * 86400, abs=5)
    assert staff_ttl < customer_ttl


def test_invalid_refresh_token_returns_401_not_500(client):
    resp = client.post("/auth/refresh", json={"refresh_token": "khong-ton-tai-token-nao-nhu-vay"})
    assert resp.status_code == 401


def test_logout_revokes_refresh_token(client):
    """AUTH5-06 — sau logout, refresh_token đã dùng không refresh được nữa."""
    login = client.post("/auth/login", json={"phone": "0901000001", "password": _TEST_PASSWORD}).json()

    logout_resp = client.post(
        "/auth/logout",
        json={"refresh_token": login["refresh_token"]},
        headers={"Authorization": f"Bearer {login['access_token']}"},
    )
    assert logout_resp.status_code == 200

    refresh_after_logout = client.post("/auth/refresh", json={"refresh_token": login["refresh_token"]})
    assert refresh_after_logout.status_code == 401


def test_logout_revokes_current_access_token_for_sensitive_routes(client):
    """AUTH5-06 — access token phát TRƯỚC lúc logout không còn dùng được ở
    route nhạy cảm (require_otp_verified) NGAY, không chờ hết hạn tự nhiên
    (access token 15 phút vẫn còn "sống" theo chữ ký, nhưng phải bị chặn qua
    check revocation — xem src/auth.py::is_access_token_revoked)."""
    login = client.post("/auth/login", json={"phone": "0901000001", "password": _TEST_PASSWORD}).json()
    old_access_token = login["access_token"]

    client.post(
        "/auth/logout",
        json={"refresh_token": login["refresh_token"]},
        headers={"Authorization": f"Bearer {old_access_token}"},
    )

    resp = client.post(
        "/tools/create_ticket",
        headers={"Authorization": f"Bearer {old_access_token}"},
        json={"complaint_type": "wrong_recipient", "scope": "internal_wallet", "description_raw": "test"},
    )
    assert resp.status_code in (401, 403)


def test_migrate_001_pre_upgrade_style_token_still_authenticates(client):
    """AUTH5-MIGRATE-001 — access token tạo qua create_access_token() ĐƠN LẺ
    (không mint refresh_token đi kèm — đúng hình dạng token đã phát hành
    TRƯỚC đợt nâng cấp này) vẫn phải qua được get_current_user bình thường
    tới khi hết hạn tự nhiên — không khoá đột ngột session đang sống chỉ vì
    thiếu refresh_token đi kèm."""
    old_style_token = create_access_token(user_id="USR-CSKH", role="cskh")
    resp = client.get("/tickets", headers={"Authorization": f"Bearer {old_style_token}"})
    assert resp.status_code == 200
