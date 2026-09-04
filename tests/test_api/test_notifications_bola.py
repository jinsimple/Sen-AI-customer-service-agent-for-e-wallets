"""BOLA cho notifications (ADR-063 · contracts/authority-matrix.yaml v2.2.0).

Nguồn (đọc, KHÔNG đọc src/):
  - contracts/authority-matrix.yaml — 6 route notification/presence, roles
    [cskh, supervisor]; "Cô lập theo người nhận (recipient_user_id = người
    đăng nhập, chống BOLA) ép ở tầng SERVICE, không ở route — route chỉ ép ROLE."
  - docs/DECISIONS.md ADR-063 — ràng buộc bất di #1: "Cô lập theo người nhận
    (recipient_user_id = người đăng nhập) ép ở tầng SERVICE khi truy vấn —
    chống BOLA, không tin tham số client."
  - docs/giao-viec/2026-09-04-po-build-chuong-thong-bao.md — PO nhắc tester
    viết ca "BOLA thật (CSKH A không đọc/không mark-read được noti của CSKH B)".

Vì sao 404 (không 403): cả cskh lẫn supervisor đều QUA cổng ROLE của route —
ranh giới ở đây là SỞ HỮU bản ghi, không phải thẩm quyền. Tiền lệ repo ADR-044
(docs/DECISIONS.md) đặt "user_id khớp" ở tầng 404-handler phụ, KHÔNG phải ranh
giới thẩm quyền; cô lập bằng bộ lọc recipient_user_id ở service ⟹ bản ghi của
người khác đơn giản "không tồn tại" với người gọi ⟹ 404. 404 cũng chống liệt
kê (anti-enumeration): không phân biệt được "id không có" với "id của người
khác".

Đây là ca ÂM BẢN quan trọng nhất của tính năng tài chính này: điều KHÔNG được
xảy ra — A ghi đè read_at của B — thì không xảy ra.
"""
from __future__ import annotations

import datetime as dt

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.api.deps import get_session
from src.api.main import app
from src.auth import create_access_token
from src.db.models import Complaint, Notification, Ticket

CONTRACT_VERSION = {
    "authority-matrix.yaml": "82682d415144",
}

# recipient_user_id lấy từ user có sẵn trong sample_db (tests/conftest.py):
#   USR-CSKH  role=cskh   · USR-0201 role=cskh · USR-SUP role=supervisor
NOTI_CUA_CSKH = "NT-OWNED-BY-CSKH"       # thuộc USR-CSKH
NOTI_CUA_NGUOI_KHAC = "NT-OWNED-BY-0201"  # thuộc USR-0201 (một cskh KHÁC)


def _auth_headers(role: str, user_id: str) -> dict:
    token = create_access_token(user_id=user_id, role=role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def client(sample_db: Session):
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


@pytest.fixture()
def seed_notifications(sample_db: Session):
    """Dựng chuỗi hợp lệ complaint→ticket→2 notification (FK bật trên engine
    test). Hai noti CÙNG một vé nhưng KHÁC recipient — cô lập phải theo người
    nhận, không theo vé."""
    now = dt.datetime(2026, 9, 4, 10, 0, 0)
    sample_db.add(
        Complaint(
            complaint_id="CMP-BOLA-1",
            user_id="USR-A",
            type="wrong_recipient",
            scope="internal_wallet",
            description_raw="seed cho test BOLA notifications",
            created_at=now,
        )
    )
    sample_db.flush()
    sample_db.add(
        Ticket(
            ticket_id="TCK-BOLA-1",
            complaint_id="CMP-BOLA-1",
            sla_due_at=now + dt.timedelta(days=1),
            created_at=now,
            updated_at=now,
        )
    )
    sample_db.flush()
    sample_db.add_all(
        [
            Notification(
                notification_id=NOTI_CUA_CSKH,
                recipient_user_id="USR-CSKH",
                event_type="ve_moi",
                ticket_id="TCK-BOLA-1",
                created_at=now,
                read_at=None,
            ),
            Notification(
                notification_id=NOTI_CUA_NGUOI_KHAC,
                recipient_user_id="USR-0201",
                event_type="ve_moi",
                ticket_id="TCK-BOLA-1",
                created_at=now,
                read_at=None,
            ),
        ]
    )
    sample_db.flush()
    sample_db.commit()
    yield


def _read_at(sample_db: Session, notification_id: str):
    sample_db.expire_all()
    row = sample_db.get(Notification, notification_id)
    assert row is not None, f"seed hỏng: {notification_id} không có trong DB"
    return row.read_at


# ---------------------------------------------------------------------------
# 1. ĐƯỜNG ÂM BẢN — ca giá trị nhất: mark-read noti của người khác → 404
# ---------------------------------------------------------------------------
def test_notifications_cskh_mark_read_noti_cua_cskh_khac_tra_404(client, sample_db, seed_notifications):
    # ADR-063 ràng buộc #1 + contracts/authority-matrix.yaml (cô lập recipient_user_id)
    resp = client.post(
        f"/notifications/{NOTI_CUA_NGUOI_KHAC}/read",
        headers=_auth_headers("cskh", "USR-CSKH"),
    )
    assert resp.status_code == 404, (
        f"CSKH mark-read noti của CSKH khác PHẢI 404 (chống liệt kê), được "
        f"{resp.status_code}: {resp.text[:200]}. "
        "403 = lộ 'id này tồn tại'; 200 = BOLA thật (ghi đè bản ghi người khác)."
    )


def test_notifications_bola_khong_ghi_de_read_at_cua_nguoi_khac(client, sample_db, seed_notifications):
    # ADR-063 ràng buộc #1 — điều KHÔNG được xảy ra thì không xảy ra
    assert _read_at(sample_db, NOTI_CUA_NGUOI_KHAC) is None, "tiền đề: noti người khác chưa đọc"
    client.post(
        f"/notifications/{NOTI_CUA_NGUOI_KHAC}/read",
        headers=_auth_headers("cskh", "USR-CSKH"),
    )
    assert _read_at(sample_db, NOTI_CUA_NGUOI_KHAC) is None, (
        "read_at của noti người khác BỊ GHI ĐÈ sau lời gọi của USR-CSKH — "
        "BOLA ghi thật, cô lập tầng service THỦNG."
    )


def test_notifications_supervisor_khong_mark_read_noti_cua_cskh(client, sample_db, seed_notifications):
    # contracts/authority-matrix.yaml — supervisor kế thừa ROLE của cskh nhưng
    # KHÔNG kế thừa quyền sở hữu bản ghi của người khác. Cô lập là theo NGƯỜI
    # NHẬN, không theo cấp bậc.
    resp = client.post(
        f"/notifications/{NOTI_CUA_CSKH}/read",
        headers=_auth_headers("supervisor", "USR-SUP"),
    )
    assert resp.status_code == 404, (
        f"supervisor mark-read noti của CSKH PHẢI 404 (không sở hữu), được {resp.status_code}. "
        "Cô lập theo recipient, không theo cấp bậc."
    )
    assert _read_at(sample_db, NOTI_CUA_CSKH) is None


def test_notifications_list_khong_lo_noti_cua_nguoi_khac(client, sample_db, seed_notifications):
    # ADR-063 — "CSKH A không ĐỌC được noti của CSKH B"
    resp = client.get("/notifications", headers=_auth_headers("cskh", "USR-CSKH"))
    assert resp.status_code == 200, f"GET /notifications role đúng phải 200, được {resp.status_code}"
    body = resp.text
    assert NOTI_CUA_NGUOI_KHAC not in body, (
        f"danh sách noti của USR-CSKH LỘ noti của USR-0201 ({NOTI_CUA_NGUOI_KHAC}) — "
        "BOLA đọc: bộ lọc recipient_user_id THỦNG ở tầng list."
    )
    assert NOTI_CUA_CSKH in body, (
        "danh sách noti của USR-CSKH KHÔNG chứa noti của chính mình — cô lập quá tay."
    )


# ---------------------------------------------------------------------------
# 2. ĐƯỜNG HẠNH PHÚC — mark-read noti CỦA MÌNH phải thành công
# ---------------------------------------------------------------------------
def test_notifications_cskh_mark_read_noti_cua_minh_thanh_cong(client, sample_db, seed_notifications):
    # ADR-063 — người nhận đọc noti của chính mình
    assert _read_at(sample_db, NOTI_CUA_CSKH) is None, "tiền đề: chưa đọc"
    resp = client.post(
        f"/notifications/{NOTI_CUA_CSKH}/read",
        headers=_auth_headers("cskh", "USR-CSKH"),
    )
    assert resp.status_code < 400, (
        f"CSKH mark-read noti CỦA MÌNH phải thành công (2xx), được {resp.status_code}: {resp.text[:200]}"
    )
    assert _read_at(sample_db, NOTI_CUA_CSKH) is not None, (
        "mark-read trả 2xx nhưng read_at vẫn null — hành động không có tác dụng thật."
    )


# ---------------------------------------------------------------------------
# 3. BIÊN — id không tồn tại KHÔNG phân biệt được với id của người khác (404)
# ---------------------------------------------------------------------------
def test_notifications_mark_read_id_khong_ton_tai_tra_404(client, sample_db, seed_notifications):
    # Anti-enumeration: "không có" và "của người khác" cùng trả 404 — không rò
    # thông tin về sự tồn tại của bản ghi.
    resp = client.post(
        "/notifications/NT-KHONG-HE-TON-TAI/read",
        headers=_auth_headers("cskh", "USR-CSKH"),
    )
    assert resp.status_code == 404, (
        f"mark-read id không tồn tại phải 404, được {resp.status_code}: {resp.text[:200]}"
    )
