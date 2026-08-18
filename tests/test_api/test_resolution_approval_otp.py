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
from src.db.models import AuthSession, Resolution
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
    # 🔴 COMMIT hạt giống, không phải cho gọn: fixture `client` dùng CHUNG
    # session với route, và `_override_session` ROLLBACK khi route ném
    # HTTPException. Hạt giống chưa commit sẽ bị chính cú rollback ấy cuốn đi
    # ⟹ sau một 403, `sample_db.get(Resolution, ...)` trả `None` và ta MẤT
    # KHẢ NĂNG QUAN SÁT đúng thứ cần đo (đo được 18/08: ca `approve` khi chưa
    # xin OTP báo KHÔNG ĐO ĐƯỢC vì lý do này, không phải vì thủng HITL).
    #
    # Ba ca OTP còn lại vô tình thoát bẫy vì có một request THÀNH CÔNG
    # (`request-approval-otp`) commit hộ trước đó — tức chúng quan sát được
    # nhờ MAY, không nhờ thiết kế. Commit ở đây làm điều đó thành tất định.
    sample_db.commit()
    return resolution["resolution_id"]


def _van_con_cho_duyet(sample_db, resolution_id: str, *, sau_khi: str) -> None:
    """Mốc CHUNG CUỘC của HITL **sau** một request duyệt bị từ chối.

    Vì sao cần, dù ca đã assert 403 (`eval/QUET-TEN-HUA-KHAC-ASSERTION.md`,
    17/08): **`403` chứng minh REQUEST bị từ chối, nó KHÔNG chứng minh HÀNH
    ĐỘNG không xảy ra.** Một endpoint trả 403 rồi vẫn duyệt là chuyện lạ —
    nhưng "lạ" chính là thứ cổng an toàn tồn tại để bắt.

    Trục bám lấy từ `contracts/resolution-state-machine.yaml`, không từ `src/`:

    - `transitions`: **CỬA DUY NHẤT** tới `approved` là
      `pending_approval → approved`, `boi: [supervisor]`, `cham_tien: true`
    - `invariant_db` **BR-10** `ck_resolutions_approved_requires_approver_br10`
      `(status != 'approved') OR (approved_by IS NOT NULL AND approved_at IS NOT NULL)`
    - contract khai chưa có state `executed` — hệ dừng ở `approved` ⟹
      `status='approved'` **CHÍNH LÀ** hậu quả tài chính quan sát được, không
      có vật nào sâu hơn để bám.

    Bám **CẶP** `(status, approved_by, approved_at)` chứ không riêng `status`
    (Luật D — nguồn độc lập): `status` do tầng application ghi, hai cột kia bị
    CHECK constraint tầng DB ràng. Đường lách chỉ chỉnh một bên sẽ vỡ ở bên kia.

    Bám **mốc tường minh** `"pending_approval"` chứ không bám `Δ` "không đổi"
    (Luật 1): `Δ=0` là trạng thái mặc định; nếu hạt giống `propose_resolution`
    đổi mặc định thì ca này phải KÊU, không được im.

    `expire_all()` là bắt buộc, không phải cho chắc: fixture `client` dùng
    CHUNG session với route (xem docstring `_override_session` ở
    `test_injection.py`) ⟹ không đuổi cache thì ta đọc **đối tượng trong bộ
    nhớ**, không đọc **hàng trong CSDL** — đúng lớp lỗi đã che một bug thật
    ngày 10/08.
    """
    sample_db.expire_all()
    res = sample_db.get(Resolution, resolution_id)
    assert res is not None, (
        f"KHÔNG ĐO ĐƯỢC: không đọc được resolution sau {sau_khi} — "
        "đừng đọc trạng thái này thành ĐẠT."
    )
    assert (res.status, res.approved_by, res.approved_at) == ("pending_approval", None, None), (
        f"🔴 RÀNG BUỘC CỨNG 1 (HITL): {sau_khi} trả 403 nhưng MỐC CHUNG CUỘC ĐÃ ĐỔI — "
        f"status={res.status!r} approved_by={res.approved_by!r} approved_at={res.approved_at!r}. "
        "Request bị chặn mà hành động vẫn xảy ra: đây là thủng HITL, không phải lỗi test."
    )


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
    _van_con_cho_duyet(sample_db, resolution_id, sau_khi="approve khi CHƯA hề xin OTP")


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
    _van_con_cho_duyet(sample_db, resolution_b, sau_khi="duyệt B bằng OTP xin cho A")

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
    _van_con_cho_duyet(
        sample_db, resolution_id,
        sau_khi=f"approve bằng OTP xin quá {RESOLUTION_APPROVAL_OTP_FRESH_MINUTES} phút trước",
    )


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
    _van_con_cho_duyet(sample_db, resolution_id, sau_khi="approve bằng mã OTP SAI")
