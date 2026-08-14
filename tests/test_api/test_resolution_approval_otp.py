"""AUTH5-04/05/05B/AAL-002 (đợt nâng cấp Auth Flow, 2026-08-12, PSD2 dynamic
linking) — `POST /resolutions/{id}/approve` giờ đòi OTP RIÊNG cho ĐÚNG
resolution_id đang duyệt, gắn chặt với số tiền tại thời điểm xin OTP (xem
src/api/main.py::request_resolution_approval_otp/approve_resolution).
`test_resolution_approval.py` đã phủ happy-path qua đủ 3 scope; file này tập
trung vào CHÍNH cơ chế OTP step-up mới — case sai/thiếu/lệch.
"""
from __future__ import annotations

import datetime as dt

import pytest
from fastapi.testclient import TestClient

from src.api.deps import get_session
from src.api.main import app
from src.auth import create_access_token
from src.config import RESOLUTION_APPROVAL_OTP_FRESH_MINUTES
from src.db.models import AuthSession
from src.tools.base import new_id
from src.tools.create_ticket import create_ticket
from src.tools.propose_resolution import propose_resolution


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


def _auth(role: str, user_id: str) -> dict:
    token = create_access_token(user_id=user_id, role=role, otp_verified_at=dt.datetime.utcnow())
    return {"Authorization": f"Bearer {token}"}


def _make_resolution(sample_db, *, amount: int = 92_000) -> str:
    ticket = create_ticket(
        sample_db,
        user_id="USR-A",
        complaint_type="wrong_recipient",
        scope="internal_wallet",
        description_raw="test AUTH5-04",
        trans_id="TXN-0001",
    )
    resolution = propose_resolution(
        sample_db,
        ticket_id=ticket["ticket_id"],
        action_type="refund_to_wallet",
        rationale="ly do test",
        created_by="USR-CSKH",
        amount=amount,
    )
    return resolution["resolution_id"]


def test_approve_without_requesting_otp_first_is_rejected(client, sample_db):
    """AUTH5-04 — approve trực tiếp (không gọi request-approval-otp trước)
    phải bị từ chối, không phải lỗi 422 thiếu field."""
    resolution_id = _make_resolution(sample_db)
    resp = client.post(
        f"/resolutions/{resolution_id}/approve",
        json={"session_id": "SES-khong-ton-tai", "otp_code": "000000"},
        headers=_auth("supervisor", "USR-SUP"),
    )
    assert resp.status_code == 403


def test_otp_from_one_resolution_cannot_approve_a_different_resolution(client, sample_db):
    """AUTH5-05 — 'case A không dùng cho case B' (dynamic linking theo ID)."""
    resolution_a = _make_resolution(sample_db)
    resolution_b = _make_resolution(sample_db)
    headers = _auth("supervisor", "USR-SUP")

    otp_a = client.post(f"/resolutions/{resolution_a}/request-approval-otp", headers=headers).json()

    # Dùng OTP xin cho A để duyệt B -> phải bị từ chối.
    resp = client.post(
        f"/resolutions/{resolution_b}/approve",
        json={"session_id": otp_a["session_id"], "otp_code": otp_a["otp_code"]},
        headers=headers,
    )
    assert resp.status_code == 403

    # Đối chứng: OTP đó vẫn duyệt ĐÚNG resolution A được (không phải OTP sai
    # hoàn toàn, chỉ là bị gắn nhầm case).
    resp_a = client.post(
        f"/resolutions/{resolution_a}/approve",
        json={"session_id": otp_a["session_id"], "otp_code": otp_a["otp_code"]},
        headers=headers,
    )
    assert resp_a.status_code == 200, resp_a.text


def test_amount_change_after_requesting_otp_invalidates_it(client, sample_db):
    """AUTH5-05B — PSD2 dynamic linking theo SỐ TIỀN: CSKH sửa amount của
    resolution SAU KHI sếp đã xin OTP -> OTP đó không dùng được nữa, phải xin
    lại OTP mới khớp số tiền hiện tại."""
    from src.db.models import Resolution

    resolution_id = _make_resolution(sample_db, amount=92_000)
    headers = _auth("supervisor", "USR-SUP")
    otp = client.post(f"/resolutions/{resolution_id}/request-approval-otp", headers=headers).json()

    # CSKH sửa lại số tiền đề xuất SAU KHI sếp đã xin OTP.
    resolution_row = sample_db.get(Resolution, resolution_id)
    resolution_row.amount = 150_000
    sample_db.commit()

    resp = client.post(
        f"/resolutions/{resolution_id}/approve",
        json={"session_id": otp["session_id"], "otp_code": otp["otp_code"]},
        headers=headers,
    )
    assert resp.status_code == 403
    assert "số tiền" in resp.json()["detail"].lower() or "tiền" in resp.json()["detail"].lower()

    # Xin lại OTP mới (khớp số tiền MỚI) -> duyệt được.
    new_otp = client.post(f"/resolutions/{resolution_id}/request-approval-otp", headers=headers).json()
    resp2 = client.post(
        f"/resolutions/{resolution_id}/approve",
        json={"session_id": new_otp["session_id"], "otp_code": new_otp["otp_code"]},
        headers=headers,
    )
    assert resp2.status_code == 200, resp2.text


def test_approve_with_correct_fresh_otp_succeeds(client, sample_db):
    resolution_id = _make_resolution(sample_db)
    headers = _auth("supervisor", "USR-SUP")
    otp = client.post(f"/resolutions/{resolution_id}/request-approval-otp", headers=headers).json()
    resp = client.post(
        f"/resolutions/{resolution_id}/approve",
        json={"session_id": otp["session_id"], "otp_code": otp["otp_code"]},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "approved"


def test_stale_approval_otp_beyond_freshness_window_rejected(client, sample_db):
    """OTP duyệt xin QUÁ LÂU trước (vượt RESOLUTION_APPROVAL_OTP_FRESH_MINUTES)
    không còn dùng được, dù đúng resolution_id/đúng mã — hành động tài chính
    thật đòi hỏi step-up TƯƠI, không phải chỉ đúng mã 1 lần mãi mãi."""
    resolution_id = _make_resolution(sample_db)
    stale_at = dt.datetime.utcnow() - dt.timedelta(minutes=RESOLUTION_APPROVAL_OTP_FRESH_MINUTES + 1)
    stale_session_id = new_id("SES")
    sample_db.add(
        AuthSession(
            session_id=stale_session_id,
            user_id="USR-SUP",
            resolution_id=resolution_id,
            amount_snapshot=92_000,
            otp_code="123456",
            otp_status="verified",
            security_q_passed=False,
            failed_attempts=0,
            created_at=stale_at,
        )
    )
    sample_db.commit()

    resp = client.post(
        f"/resolutions/{resolution_id}/approve",
        json={"session_id": stale_session_id, "otp_code": "123456"},
        headers=_auth("supervisor", "USR-SUP"),
    )
    assert resp.status_code == 403


def test_wrong_otp_code_rejected(client, sample_db):
    resolution_id = _make_resolution(sample_db)
    headers = _auth("supervisor", "USR-SUP")
    otp = client.post(f"/resolutions/{resolution_id}/request-approval-otp", headers=headers).json()
    resp = client.post(
        f"/resolutions/{resolution_id}/approve",
        json={"session_id": otp["session_id"], "otp_code": "000000"},
        headers=headers,
    )
    assert resp.status_code == 403
