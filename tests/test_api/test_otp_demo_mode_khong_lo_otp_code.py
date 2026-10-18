"""Punch-list bảo mật 30/08 (#7) — `OTP_DEMO_MODE=False` (mặc định PRODUCTION)
⟹ response KHÔNG được có `otp_code` ở CẢ HAI route, sau bản vá `bdaf17e`
(benchmark EU/US 27/08, Phát hiện #2).

Trước bản vá: cả hai route trả THẲNG `otp_code` vô điều kiện — xoá mất yếu tố
"sở hữu" của SCA/AAL2 (dù dynamic linking + step-up thiết kế đúng). Sau vá:
chỉ trả khi `OTP_DEMO_MODE=true` (mặc định TẮT, fail-fast nếu bật cùng
`APP_ENV=production` — xem `src/config.py:198-203`).

Cổng NÀY canh mặt TẮT (production thật). Cổng SONG SINH canh mặt BẬT (demo
vẫn hoạt động, không phải chặn nhầm cả đường hợp lệ) là các test đã có từ
trước (`test_api/test_otp.py`, `test_api/test_resolution_approval.py`) — giờ
chỉ chạy đúng khi ngăn xếp có `OTP_DEMO_MODE=true` (CI + `.env.example` đã
đặt sẵn; ngăn `fin05-qa-stripe` đặt qua `docker-compose.qa-stripe.override.yml`).

Patch `src.api.main.OTP_DEMO_MODE` (KHÔNG phải biến môi trường) — cờ được
`import` theo GIÁ TRỊ vào `main.py` (`from src.config import (..., OTP_DEMO_MODE,
...)`, dòng 87), nên sửa env var lúc chạy test không đổi được giá trị đã
cache trong module. `monkeypatch.setattr` đúng chỗ nó được ĐỌC, không phải
đúng chỗ nó được ĐỊNH NGHĨA — cùng khuôn `TRIAGE_ENABLED`/`OTEL_EXPORTER_...`
(cờ đọc lúc import) đã ghi chú ở `docker-compose.yml`.
"""
from __future__ import annotations

import datetime as dt

import pytest
from fastapi.testclient import TestClient

import src.api.main as main_module
from src.api.deps import get_session
from src.api.main import app
from src.auth import create_access_token
from src.tools.create_ticket import create_ticket
from src.tools.propose_resolution import propose_resolution


@pytest.fixture()
def client(sample_db, monkeypatch):
    monkeypatch.setattr(main_module, "OTP_DEMO_MODE", False)

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


def _auth(role: str, user_id: str) -> dict:
    token = create_access_token(user_id=user_id, role=role, otp_verified_at=dt.datetime.utcnow())
    return {"Authorization": f"Bearer {token}"}


def test_auth_otp_request_khong_co_otp_code_khi_demo_tat(client):
    """`POST /auth/otp/request` — route xác thực phiên (login OTP)."""
    resp = client.post("/auth/otp/request", headers=_auth("customer", "USR-A"))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "otp_code" not in body, (
        f"otp_code LỘ trong response khi OTP_DEMO_MODE=False: {body!r}. "
        "Đây đúng Phát hiện #2 (benchmark EU/US 27/08) — yếu tố 'sở hữu' của "
        "SCA/AAL2 không tồn tại nếu route này còn trả OTP qua CÙNG kênh với request."
    )
    assert "session_id" in body, "gỡ otp_code không được kéo theo mất session_id — verify vẫn cần nó"


def test_resolution_approval_otp_khong_co_otp_code_khi_demo_tat(client, sample_db):
    """`POST /resolutions/{id}/request-approval-otp` — route OTP duyệt hoàn tiền,
    route CHẠM TIỀN nhất hệ thống, security bổ sung vào phạm vi vá 30/08."""
    ticket = create_ticket(
        sample_db,
        user_id="USR-A",
        complaint_type="wrong_recipient",
        scope="internal_wallet",
        description_raw="test punch-list 7 - demo tat",
        trans_id="TXN-0001",
    )
    resolution = propose_resolution(
        sample_db, ticket_id=ticket["ticket_id"], action_type="no_action", rationale="ly do test", created_by="USR-CSKH"
    )

    resp = client.post(
        f"/resolutions/{resolution['resolution_id']}/request-approval-otp",
        headers=_auth("supervisor", "USR-SUP"),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "otp_code" not in body, (
        f"otp_code LỘ trong response duyệt-hoàn-tiền khi OTP_DEMO_MODE=False: {body!r}. "
        "Route CHẠM TIỀN nhất hệ thống — lộ ở đây nghiêm trọng hơn route login."
    )
    assert "session_id" in body, "gỡ otp_code không được kéo theo mất session_id — approve vẫn cần nó"
