"""F-13 (tầng logic) — `hitl_status` phải bám resolution MỚI NHẤT, ngay lập tức.

Nguồn đặc tả: `contracts/resolution-state-machine.yaml` v2.1.0
§`ticket_hitl_status.dan_xuat` + `docs/security/review-phase01-ap-that.md` F-13.
Viết từ đặc tả, KHÔNG đọc `src/`.

PHÂN VAI VỚI TEST ANH EM: `tests/test_migrations/test_trang_thai_dich_nhip_
note_f11_f13.py` canh **dữ liệu lịch sử** trên DB thật (backfill có chạy đúng
không). File này canh **luật ở tầng logic** (từ nay về sau có giữ đúng không).
Thiếu file này thì backfill xong là số sạch một lần, rồi trôi lại ngay khi có
hoạt động mới — đúng cách QA-02 sinh ra ban đầu.

Contract nói rõ hai điều dễ bị nhập làm một:
  1. `hitl_status` cập nhật trong CÙNG TRANSACTION với lần đổi trạng thái
     resolution — **không job nền**. Job nền nghĩa là có một khoảng thời gian
     báo cáo nói sai, và không ai biết khoảng đó dài bao lâu.
  2. Nó VẪN là trục RIÊNG, không phải bản sao của `resolution.status`:
     `need_more_info` không có tương ứng bên resolution, và ticket chưa có
     resolution nào vẫn là `pending`.
"""
from __future__ import annotations

import datetime as dt

import pytest
from fastapi.testclient import TestClient

from src.api.deps import get_session
from src.api.main import app
from src.auth import create_access_token
from src.db.models import Ticket
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


def _ticket_va_resolution(sample_db) -> tuple[str, str]:
    ticket = create_ticket(
        sample_db, user_id="USR-A", complaint_type="wrong_recipient", scope="internal_wallet",
        description_raw="test F-13", trans_id="TXN-0001",
    )
    res = propose_resolution(
        sample_db, ticket_id=ticket["ticket_id"], action_type="refund_to_wallet",
        rationale="ly do test", amount=92_000, created_by="USR-CSKH",
    )
    return ticket["ticket_id"], res["resolution_id"]


def _hitl(sample_db, ticket_id: str) -> str:
    sample_db.expire_all()
    return sample_db.get(Ticket, ticket_id).hitl_status


def test_ticket_chua_co_resolution_thi_pending(sample_db):
    """Trục riêng, không phải bản sao: chưa có đề xuất nào thì chưa có phán
    quyết HITL nào để phản ánh."""
    ticket = create_ticket(
        sample_db, user_id="USR-A", complaint_type="wrong_recipient", scope="internal_wallet",
        description_raw="chua co resolution", trans_id="TXN-0001",
    )
    sample_db.commit()
    assert _hitl(sample_db, ticket["ticket_id"]) == "pending"


def test_resolution_moi_trinh_van_giu_pending(sample_db):
    """`pending_approval` là ĐANG CHỜ, chưa phải phán quyết — ticket giữ
    `pending`. Đây là mặt "không quét quá tay" của cùng một luật."""
    ticket_id, _ = _ticket_va_resolution(sample_db)
    sample_db.commit()
    assert _hitl(sample_db, ticket_id) == "pending"


def test_tu_choi_qua_route_dong_bo_hitl_status_ngay(client, sample_db):
    """Từ chối xong là báo cáo phải đúng NGAY, không đợi job nền.

    Đây chính là QA-02: cột này từng kẹt `pending` vĩnh viễn, khiến mọi thống
    kê duyệt/từ chối không dùng được — mà thống kê sai thì không phát hiện
    được, nó chỉ âm thầm dẫn tới quyết định sai.
    """
    ticket_id, resolution_id = _ticket_va_resolution(sample_db)
    resp = client.post(
        f"/resolutions/{resolution_id}/reject",
        json={"reason": "sai_so_lieu"},
        headers=_auth("supervisor", "USR-SUP"),
    )
    assert resp.status_code == 200, resp.text
    assert _hitl(sample_db, ticket_id) == "rejected", (
        "Từ chối xong mà ticket vẫn không phản ánh — QA-02 tái phát."
    )


def test_duyet_qua_route_dong_bo_hitl_status_ngay(client, sample_db):
    ticket_id, resolution_id = _ticket_va_resolution(sample_db)
    headers = _auth("supervisor", "USR-SUP")
    otp = client.post(f"/resolutions/{resolution_id}/request-approval-otp", headers=headers).json()
    resp = client.post(
        f"/resolutions/{resolution_id}/approve",
        json={"session_id": otp["session_id"], "otp_code": otp["otp_code"]},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert _hitl(sample_db, ticket_id) == "approved"


def test_need_more_info_khong_co_tuong_ung_ben_resolution(client, sample_db):
    """`need_more_info` chỉ tồn tại ở trục ticket — sếp trả case ngược cho CSKH
    bổ sung mà KHÔNG từ chối hẳn.

    Nếu hai trục bị gộp làm một, đường này biến mất và sếp chỉ còn lựa chọn
    nhị phân duyệt/từ chối — mất luôn khả năng phân biệt "sửa được" với "sai
    hẳn", đúng ranh giới mà taxonomy `thieu_can_cu` cố giữ.
    """
    ticket_id, _ = _ticket_va_resolution(sample_db)
    resp = client.post(
        f"/tickets/{ticket_id}/request-more-info",
        json={"reason": "Bổ sung thêm ảnh chụp màn hình giao dịch."},
        headers=_auth("supervisor", "USR-SUP"),
    )
    assert resp.status_code == 200, resp.text
    assert _hitl(sample_db, ticket_id) == "need_more_info"

    from src.db.models import Resolution

    sample_db.expire_all()
    trang_thai_resolution = {
        r.status for r in sample_db.query(Resolution).filter_by(ticket_id=ticket_id).all()
    }
    assert "need_more_info" not in trang_thai_resolution, (
        "'need_more_info' rò sang resolution.status — hai trục bị gộp."
    )
