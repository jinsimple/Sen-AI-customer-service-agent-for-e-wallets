"""SEC-A/SEC-B — `approve` và `reject` chỉ hợp lệ TỪ `pending_approval`.

Viết từ đặc tả `contracts/resolution-state-machine.yaml` v2.1.0
(§resolution.status.transitions), KHÔNG đọc `src/`.

Vì sao cần canh riêng CỬA VÀO của hai nhánh này, dù mỗi nhánh đã có test
happy-path: máy trạng thái chỉ an toàn khi cả *đích* lẫn *nguồn* đều bị khoá.
Test hiện có chứng minh "pending_approval → approved/rejected chạy được";
chúng KHÔNG chứng minh "approved → rejected bị chặn". Thiếu nửa sau thì một
resolution đã duyệt vẫn có thể bị lật sang từ chối (hoặc ngược lại) — mất tính
chung cuộc của quyết định HITL, và mọi con số thống kê duyệt/từ chối thành vô
nghĩa vì cùng một case đếm được ở cả hai phía.

Contract chỉ khai đúng 2 transition tới trạng thái cuối, cả hai đều
`from: pending_approval`. Mọi nguồn khác phải bị từ chối.
"""
from __future__ import annotations

import datetime as dt

import pytest
from fastapi.testclient import TestClient

from src.api.deps import get_session
from src.api.main import app
from src.auth import create_access_token
from src.db.models import Resolution
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
        sample_db, user_id="USR-A", complaint_type="wrong_recipient", scope="internal_wallet",
        description_raw="test SEC-A/SEC-B", trans_id="TXN-0001",
    )
    resolution = propose_resolution(
        sample_db, ticket_id=ticket["ticket_id"], action_type="refund_to_wallet",
        rationale="ly do test", amount=amount, created_by="USR-CSKH",
    )
    return resolution["resolution_id"]


def _dat_trang_thai(sample_db, resolution_id: str, status: str) -> None:
    """Đưa resolution về đúng trạng thái nguồn cần test — set kèm các trường
    BR-10/BR-11 bắt buộc, nếu không chính CHECK constraint sẽ chặn ở bước dựng
    dữ liệu và test hỏng vì lý do không liên quan."""
    res = sample_db.get(Resolution, resolution_id)
    res.status = status
    if status == "approved":
        res.approved_by, res.approved_at = "USR-SUP", dt.datetime.utcnow()
    elif status == "rejected":
        res.reject_reason = "sai_so_lieu"
        res.rejected_by, res.rejected_at = "USR-SUP", dt.datetime.utcnow()
    sample_db.commit()


# --------------------------------------------------------------------------
# SEC-A — reject chỉ từ pending_approval
# --------------------------------------------------------------------------


@pytest.mark.parametrize("nguon", ["draft", "approved", "rejected"])
def test_sec_a_reject_tu_trang_thai_khac_pending_bi_tu_choi(client, sample_db, nguon):
    """Contract chỉ có MỘT transition tới `rejected`, từ `pending_approval`.

    Ca nặng nhất là `approved → rejected`: lật ngược một quyết định đã duyệt
    mà không để lại vết của việc lật.
    """
    resolution_id = _make_resolution(sample_db)
    _dat_trang_thai(sample_db, resolution_id, nguon)

    resp = client.post(
        f"/resolutions/{resolution_id}/reject",
        json={"reason": "sai_so_lieu"},
        headers=_auth("supervisor", "USR-SUP"),
    )
    assert resp.status_code == 400, (
        f"reject từ '{nguon}' trả {resp.status_code}, phải là 400. "
        f"Contract chỉ cho pending_approval → rejected. Body: {resp.text[:200]}"
    )
    assert sample_db.get(Resolution, resolution_id).status == nguon, (
        "Trạng thái bị đổi dù request bị từ chối — rollback không sạch."
    )


def test_sec_a_reject_thieu_ly_do_bi_tu_choi(client, sample_db):
    """BR-11 ở tầng API: lý do là BẮT BUỘC, không được để tầng DB đỡ hộ.

    CHECK constraint là lưới cuối; để nó là lớp duy nhất thì người dùng nhận
    HTTP 500 thay vì một thông báo dùng được.
    """
    resolution_id = _make_resolution(sample_db)
    resp = client.post(
        f"/resolutions/{resolution_id}/reject", json={},
        headers=_auth("supervisor", "USR-SUP"),
    )
    assert resp.status_code in (400, 422), (
        f"reject không kèm lý do trả {resp.status_code} — phải là 400/422, "
        f"và tuyệt đối không được 500 (để CHECK constraint ném ra ngoài)."
    )


def test_sec_a_reject_ly_do_ngoai_taxonomy_bi_tu_choi(client, sample_db):
    """Lý do phải thuộc enum ADR-019 — chuỗi tự do phá vòng học Phase 2."""
    resolution_id = _make_resolution(sample_db)
    resp = client.post(
        f"/resolutions/{resolution_id}/reject",
        json={"reason": "sep_khong_thich"},
        headers=_auth("supervisor", "USR-SUP"),
    )
    assert resp.status_code in (400, 422), (
        f"Lý do ngoài taxonomy được chấp nhận ({resp.status_code}) — "
        "case này sẽ lọt vào bộ ứng viên eval mà không tra được `la_tin_hieu_hoc`."
    )


def test_sec_a_cskh_khong_duoc_reject(client, sample_db):
    """authority-matrix: `POST /resolutions/{id}/reject` → roles: [supervisor].

    Ràng buộc cứng 1: CSKH điều tra, KHÔNG quyết định — kể cả quyết định
    'không làm gì'. Từ chối cũng là một quyết định chung cuộc.
    """
    resolution_id = _make_resolution(sample_db)
    resp = client.post(
        f"/resolutions/{resolution_id}/reject",
        json={"reason": "sai_so_lieu"},
        headers=_auth("cskh", "USR-CSKH"),
    )
    assert resp.status_code == 403, f"CSKH reject được ({resp.status_code}) — vượt quyền."


# --------------------------------------------------------------------------
# SEC-B — approve chỉ từ pending_approval
# --------------------------------------------------------------------------


@pytest.mark.parametrize("nguon", ["draft", "approved", "rejected"])
def test_sec_b_approve_tu_trang_thai_khac_pending_bi_tu_choi(client, sample_db, nguon):
    """`draft → approved` là đường tắt bỏ qua bước trình duyệt; `rejected →
    approved` là lật ngược một lần từ chối. Cả hai đều không có trong contract.

    ĐI QUA CỔNG OTP THẬT (xin OTP hợp lệ rồi mới approve) là điểm mấu chốt của
    test này, và là bài học từ chính bản đầu của nó: bản đầu gửi OTP rác rồi
    chỉ assert `status_code >= 400`. Nó XANH — nhưng xanh vì request chết ở
    cổng OTP, KHÔNG BAO GIỜ chạm tới guard trạng thái phía sau. Tức là nó
    không hề chứng minh điều nó tuyên bố, và che mất đúng lỗ SEC-B mà nó sinh
    ra để canh.

    Bài học chung: một assertion đủ lỏng (`>= 400`) trên một request chết sớm
    là test luôn-xanh trá hình. Muốn canh tầng N thì request phải sống qua
    được tầng N-1.
    """
    resolution_id = _make_resolution(sample_db)
    headers = _auth("supervisor", "USR-SUP")
    # Xin OTP TRƯỚC khi đổi trạng thái: route xin OTP nhiều khả năng cũng chỉ
    # cấp cho resolution đang chờ duyệt. Ta cần OTP hợp lệ để loại trừ tầng
    # OTP khỏi phép thử, cô lập đúng thứ đang đo là guard TRẠNG THÁI.
    otp = client.post(f"/resolutions/{resolution_id}/request-approval-otp", headers=headers).json()
    _dat_trang_thai(sample_db, resolution_id, nguon)

    resp = client.post(
        f"/resolutions/{resolution_id}/approve",
        json={"session_id": otp["session_id"], "otp_code": otp["otp_code"]},
        headers=headers,
    )
    assert resp.status_code == 400, (
        f"approve từ '{nguon}' với OTP HỢP LỆ trả {resp.status_code}, phải là 400. "
        f"Contract chỉ cho pending_approval → approved (CỬA DUY NHẤT, ADR-002). "
        f"Body: {resp.text[:200]}"
    )
    assert sample_db.get(Resolution, resolution_id).status == nguon, (
        "Trạng thái bị đổi dù request thất bại."
    )
