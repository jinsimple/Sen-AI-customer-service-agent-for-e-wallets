"""PERM-002 (FIN05_QA_TestCases.jsonl) — sếp phải duyệt được ở MỌI phạm vi
giao dịch (nội bộ ví / từ ngân hàng / ra ngân hàng), không có nhánh nào bị
chặn riêng. `approve_resolution` (src/api/main.py) vốn không rẽ nhánh theo
scope — test này XÁC NHẬN THẬT điều đó qua cả 3 phạm vi bằng TestClient, thay
vì chỉ suy luận từ đọc code. Cũng xác nhận log actor+timestamp đầy đủ
(`approved_by`/`approved_at`) như PERM-002 yêu cầu.

AUTH5-04 (đợt nâng cấp Auth Flow 2026-08-12): `approve` giờ đòi OTP riêng cho
ĐÚNG resolution_id (xin qua `request-approval-otp` trước) — helper
`_approve_with_fresh_otp()` làm đúng 2 bước này thay vì gọi approve trực
tiếp như trước."""
from __future__ import annotations

import datetime as dt

import pytest
from fastapi.testclient import TestClient

from src.api.deps import get_session
from src.api.main import app
from src.auth import create_access_token
from src.tools.create_ticket import create_ticket
from src.tools.propose_resolution import propose_resolution

SCOPES = ["internal_wallet", "from_bank", "to_bank"]


@pytest.fixture()
def client(sample_db):
    def _override_session():
        # Phải commit/rollback ĐÚNG như get_session() thật (src/api/deps.py)
        # — xem ghi chú tương tự ở tests/test_api/test_otp.py (bug thật tìm
        # được 2026-08-10: fixture chỉ yield không commit/rollback che mất 1
        # lỗi rollback thật trong verify_otp()).
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


def _approve_with_fresh_otp(client, resolution_id: str, headers: dict):
    """AUTH5-04 — xin OTP riêng cho ĐÚNG resolution_id rồi mới duyệt, đúng
    luồng API mới (2 bước, không còn duyệt trực tiếp)."""
    otp_resp = client.post(f"/resolutions/{resolution_id}/request-approval-otp", headers=headers)
    assert otp_resp.status_code == 200, otp_resp.text
    otp = otp_resp.json()
    return client.post(
        f"/resolutions/{resolution_id}/approve",
        headers=headers,
        json={"session_id": otp["session_id"], "otp_code": otp["otp_code"]},
    )


@pytest.mark.parametrize("scope", SCOPES)
def test_supervisor_can_approve_every_scope(client, sample_db, scope):
    ticket = create_ticket(
        sample_db,
        user_id="USR-A",
        complaint_type="wrong_recipient",
        scope=scope,
        description_raw=f"test PERM-002 scope={scope}",
        trans_id="TXN-0001",
    )
    resolution = propose_resolution(
        sample_db, ticket_id=ticket["ticket_id"], action_type="no_action", rationale="ly do test", created_by="USR-CSKH"
    )

    resp = _approve_with_fresh_otp(client, resolution["resolution_id"], _auth("supervisor", "USR-SUP"))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "approved"
    # Log đầy đủ actor + timestamp (PERM-002 expected_output_contains).
    assert body["approved_by"] == "USR-SUP"

    from src.db.models import Resolution

    row = sample_db.get(Resolution, resolution["resolution_id"])
    assert row.approved_by == "USR-SUP"
    assert row.approved_at is not None
