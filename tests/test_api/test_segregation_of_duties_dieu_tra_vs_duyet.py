"""Punch-list bảo mật 30/08 (#9) — segregation-of-duties GIỮA điều tra và duyệt.

`docs/security/review-2026-08-27-benchmark-eu-us.md` Phát hiện #5: BR-12
maker-checker (`ck_resolutions_maker_checker_br12`) chỉ chặn ĐÚNG một
supervisor vừa `created_by` một resolution vừa tự `approve` CHÍNH resolution
đó. Nó KHÔNG chặn việc một supervisor A tự `lookup_transaction`/
`propose_resolution` cho một case rồi để supervisor B duyệt hộ — tức không
có ràng buộc "người duyệt phải độc lập với người đã điều tra case".

🔴 Test này KHÔNG phải bug report — nó là CA ĐẶC TẢ ĐẶC ĐIỂM (characterization
test), xác nhận hành vi HIỆN TẠI đang CHO PHÉP kịch bản trên, để PO có số liệu
cụ thể quyết định có cần chặn theo SOC2 CC6.3 (segregation-of-duties cho vai
có quyền tài chính cao nhất) hay không — xem `contracts/authority-matrix.yaml`
mục `open_questions`, câu hỏi này đã treo mở từ trước.

Nếu sau này PO quyết CHẶN kịch bản này: assert dưới phải ĐỔI sang mong đợi
403/400, và đổi CÓ CHỦ Ý — không phải sửa vì test "tự nhiên đỏ".
"""
from __future__ import annotations

import datetime as dt

import pytest
from fastapi.testclient import TestClient

from src.api.deps import get_session
from src.api.main import app
from src.auth import create_access_token
from src.db.models import User
from src.tools.create_ticket import create_ticket
from src.tools.lookup_transaction import lookup_transaction
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


def _them_supervisor_thu_hai(sample_db) -> None:
    """`sample_db` (tests/conftest.py) chỉ seed đúng 1 supervisor (USR-SUP).
    Ca này CẦN 2 supervisor độc lập nên thêm 1 người trực tiếp vào session,
    cùng cách `tests/test_hop_nhat_tin_hieu_gian_lan.py` thêm fixture riêng
    thay vì sửa fixture dùng chung (`sample_db` được nhiều file khác tin cậy
    ở đúng hình dạng hiện tại)."""
    from argon2 import PasswordHasher

    pw_hash = PasswordHasher().hash("Demo@123")
    sample_db.add(
        User(
            user_id="USR-SUP-2",
            role="supervisor",
            full_name="Sếp Hai",
            phone="0901000205",
            kyc_level=2,
            password_hash=pw_hash,
            created_at=dt.datetime(2026, 8, 1, 10, 0, 0),
        )
    )
    sample_db.flush()


def _duyet_voi_otp_moi(client, resolution_id: str, headers: dict):
    otp_resp = client.post(f"/resolutions/{resolution_id}/request-approval-otp", headers=headers)
    assert otp_resp.status_code == 200, otp_resp.text
    otp = otp_resp.json()
    return client.post(
        f"/resolutions/{resolution_id}/approve",
        headers=headers,
        json={"session_id": otp["session_id"], "otp_code": otp["otp_code"]},
    )


def test_supervisor_khac_duoc_duyet_case_ma_supervisor_kia_da_tu_dieu_tra(client, sample_db):
    """Supervisor A tự lookup_transaction + propose_resolution cho case X,
    supervisor B (khác người) duyệt — [ĐO 30/08] xác nhận HIỆN TẠI luồng này
    THÀNH CÔNG (không có gate nào chặn), khác với ca `created_by == approver`
    (BR-12) mà `test_resolution_approval.py`/migration test đã canh."""
    _them_supervisor_thu_hai(sample_db)

    # Supervisor A "điều tra": tự tra cứu giao dịch trước khi đề xuất.
    tra_cuu = lookup_transaction(sample_db, trans_id="TXN-0001", requesting_user_id="USR-SUP")
    assert tra_cuu.get("transaction", {}).get("trans_id") == "TXN-0001", (
        "seed TXN-0001 phải tồn tại — kiểm lại tests/conftest.py"
    )

    ticket = create_ticket(
        sample_db,
        user_id="USR-A",
        complaint_type="wrong_recipient",
        scope="internal_wallet",
        description_raw="ca canh segregation-of-duties, supervisor A tu dieu tra",
        trans_id="TXN-0001",
    )
    resolution = propose_resolution(
        sample_db,
        ticket_id=ticket["ticket_id"],
        action_type="no_action",
        rationale="supervisor A tu dieu tra roi tu de xuat",
        created_by="USR-SUP",  # supervisor A — CHÍNH NGƯỜI vừa lookup_transaction ở trên
    )

    # Supervisor B (KHÁC người điều tra) duyệt.
    resp = _duyet_voi_otp_moi(client, resolution["resolution_id"], _auth("supervisor", "USR-SUP-2"))

    assert resp.status_code == 200, (
        f"Kỳ vọng HIỆN TẠI (chưa có gate segregation-of-duties mở rộng) là "
        f"THÀNH CÔNG (200), nhận {resp.status_code}: {resp.text}. "
        "Nếu ai đó đã thêm gate chặn kịch bản này mà chưa cập nhật test: đây "
        "là tin TỐT về mặt bảo mật, nhưng phải đổi assert này CÓ CHỦ Ý kèm "
        "ADR/quyết định PO, không phải coi failure này là hồi quy cần revert."
    )
    body = resp.json()
    assert body["status"] == "approved"
    assert body["approved_by"] == "USR-SUP-2"

    from src.db.models import Resolution

    row = sample_db.get(Resolution, resolution["resolution_id"])
    assert row.created_by == "USR-SUP", "resolution phải ghi đúng người ĐỀ XUẤT (supervisor A)"
    assert row.approved_by == "USR-SUP-2", "resolution phải ghi đúng người DUYỆT (supervisor B)"
