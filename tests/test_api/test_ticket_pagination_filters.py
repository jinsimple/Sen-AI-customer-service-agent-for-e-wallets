"""[polish trước quay 04/09] GET /tickets — phân trang thật (page/page_size)
+ bộ lọc complaint_type/scope/priority/status/SLA, kết hợp AND.

Theo khuôn `test_ticket_claim_adr064.py` (client fixture + create_ticket trực
tiếp để dựng dữ liệu, không cần đi qua toàn bộ luồng AI agent). Ticket dựng
bằng `create_ticket(trans_id=None)` — nhánh not_found hợp lệ, không phụ
thuộc transaction nào đã seed sẵn cho user — rồi mutate trực tiếp
priority/scope/type/hitl_status/sla_due_at qua session, cùng cách
`test_ticket_state_transitions.py` đã làm với hitl_status."""
from __future__ import annotations

import datetime as dt

import pytest
from fastapi.testclient import TestClient

from src.api.deps import get_session
from src.api.main import app
from src.auth import create_access_token
from src.db.models import Complaint, Ticket
from src.tools.create_ticket import create_ticket


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


def _token(user_id: str, role: str) -> str:
    return create_access_token(user_id=user_id, role=role)


_SUP_HEADERS = {"Authorization": f"Bearer {_token('USR-SUP', 'supervisor')}"}


def _make_ticket(
    sample_db,
    *,
    user_id: str = "USR-A",
    complaint_type: str = "other",
    scope: str = "unknown",
    priority: str = "normal",
    hitl_status: str = "pending",
    sla_due_at: dt.datetime | None = None,
) -> str:
    r = create_ticket(
        sample_db, user_id=user_id, complaint_type=complaint_type, scope=scope,
        description_raw="test phân trang/lọc", trans_id=None,
    )
    sample_db.commit()
    ticket_id = r["ticket_id"]
    ticket = sample_db.get(Ticket, ticket_id)
    complaint = sample_db.get(Complaint, ticket.complaint_id)
    complaint.priority = priority
    ticket.hitl_status = hitl_status
    if sla_due_at is not None:
        ticket.sla_due_at = sla_due_at
    sample_db.commit()
    return ticket_id


# --- Phân trang ---------------------------------------------------------


def test_page_size_ngoai_danh_sach_cho_phep_bi_422(client):
    resp = client.get("/tickets", params={"page_size": 40}, headers=_SUP_HEADERS)
    assert resp.status_code == 422, resp.text


def test_page_nho_hon_1_bi_422(client):
    resp = client.get("/tickets", params={"page": 0}, headers=_SUP_HEADERS)
    assert resp.status_code == 422, resp.text


def test_page_size_hop_le_deu_qua_duoc(client):
    for size in (30, 50, 100):
        resp = client.get("/tickets", params={"page_size": size}, headers=_SUP_HEADERS)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["page_size"] == size
        assert len(body["items"]) <= size


def test_khong_truyen_page_page_size_dung_mac_dinh(client):
    resp = client.get("/tickets", headers=_SUP_HEADERS)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["page"] == 1
    assert body["page_size"] == 50


def test_total_khop_tong_so_ticket_khop_bo_loc_khong_phai_so_dong_tren_trang(client, sample_db):
    for _ in range(3):
        _make_ticket(sample_db, complaint_type="refund")
    resp = client.get("/tickets", params={"complaint_type": "refund", "page_size": 30}, headers=_SUP_HEADERS)
    body = resp.json()
    assert body["total"] == 3
    assert len(body["items"]) == 3


def test_hai_trang_lien_tiep_khong_trung_khong_thieu(client, sample_db):
    # page_size nhỏ nhất cho phép là 30 — dựng 31 ticket riêng (đánh dấu bằng
    # complaint_type='double_charge' để cô lập khỏi ticket sinh bởi test
    # khác trong cùng phiên sample_db) để có ĐÚNG 2 trang thật.
    ids = {_make_ticket(sample_db, complaint_type="double_charge") for _ in range(31)}
    assert len(ids) == 31

    p1 = client.get(
        "/tickets", params={"complaint_type": "double_charge", "page": 1, "page_size": 30}, headers=_SUP_HEADERS
    ).json()
    p2 = client.get(
        "/tickets", params={"complaint_type": "double_charge", "page": 2, "page_size": 30}, headers=_SUP_HEADERS
    ).json()
    assert p1["total"] == p2["total"] == 31
    assert len(p1["items"]) == 30
    assert len(p2["items"]) == 1
    ids_p1 = {t["ticket_id"] for t in p1["items"]}
    ids_p2 = {t["ticket_id"] for t in p2["items"]}
    assert ids_p1.isdisjoint(ids_p2), "2 trang liên tiếp KHÔNG được trùng ticket"
    assert ids_p1 | ids_p2 == ids, "hợp 2 trang phải phủ ĐỦ và ĐÚNG toàn bộ ticket đã tạo"


# --- Lọc từng tiêu chí ----------------------------------------------------


def test_loc_theo_complaint_type(client, sample_db):
    _make_ticket(sample_db, complaint_type="money_not_received")
    other_id = _make_ticket(sample_db, complaint_type="other")
    resp = client.get("/tickets", params={"complaint_type": "money_not_received", "page_size": 100}, headers=_SUP_HEADERS)
    ids = {t["ticket_id"] for t in resp.json()["items"]}
    assert other_id not in ids
    assert all(t["complaint_type"] == "money_not_received" for t in resp.json()["items"])


def test_loc_theo_scope(client, sample_db):
    tid = _make_ticket(sample_db, scope="internal_wallet")
    resp = client.get("/tickets", params={"scope": "internal_wallet", "page_size": 100}, headers=_SUP_HEADERS)
    ids = {t["ticket_id"] for t in resp.json()["items"]}
    assert tid in ids
    assert all(t["scope"] == "internal_wallet" for t in resp.json()["items"])


def test_loc_theo_priority(client, sample_db):
    tid = _make_ticket(sample_db, priority="critical")
    resp = client.get("/tickets", params={"priority": "critical", "page_size": 100}, headers=_SUP_HEADERS)
    ids = {t["ticket_id"] for t in resp.json()["items"]}
    assert tid in ids
    assert all(t["priority"] == "critical" for t in resp.json()["items"])


def test_loc_theo_hitl_status_khong_doi_hanh_vi_cu(client, sample_db):
    tid = _make_ticket(sample_db, hitl_status="approved")
    resp = client.get("/tickets", params={"hitl_status": "approved", "page_size": 100}, headers=_SUP_HEADERS)
    ids = {t["ticket_id"] for t in resp.json()["items"]}
    assert tid in ids
    assert all(t["hitl_status"] == "approved" for t in resp.json()["items"])


def test_loc_theo_khoang_sla(client, sample_db):
    som = dt.datetime(2026, 1, 1, 0, 0, 0)
    muon = dt.datetime(2030, 1, 1, 0, 0, 0)
    tid_som = _make_ticket(sample_db, sla_due_at=som)
    tid_muon = _make_ticket(sample_db, sla_due_at=muon)

    resp = client.get(
        "/tickets",
        params={"sla_before": "2027-01-01T00:00:00", "page_size": 100},
        headers=_SUP_HEADERS,
    )
    ids = {t["ticket_id"] for t in resp.json()["items"]}
    assert tid_som in ids
    assert tid_muon not in ids

    resp2 = client.get(
        "/tickets",
        params={"sla_after": "2027-01-01T00:00:00", "page_size": 100},
        headers=_SUP_HEADERS,
    )
    ids2 = {t["ticket_id"] for t in resp2.json()["items"]}
    assert tid_muon in ids2
    assert tid_som not in ids2


def test_ket_hop_nhieu_tieu_chi_la_AND_khong_phai_OR(client, sample_db):
    # Khớp CẢ HAI tiêu chí — phải hiện.
    tid_khop = _make_ticket(sample_db, complaint_type="refund", priority="high")
    # Khớp complaint_type nhưng SAI priority — không được lọt qua bộ lọc AND.
    tid_sai_priority = _make_ticket(sample_db, complaint_type="refund", priority="low")
    # Khớp priority nhưng SAI complaint_type.
    tid_sai_type = _make_ticket(sample_db, complaint_type="other", priority="high")

    resp = client.get(
        "/tickets",
        params={"complaint_type": "refund", "priority": "high", "page_size": 100},
        headers=_SUP_HEADERS,
    )
    ids = {t["ticket_id"] for t in resp.json()["items"]}
    assert tid_khop in ids
    assert tid_sai_priority not in ids
    assert tid_sai_type not in ids


def test_khong_loc_gi_tra_ve_tat_ca_khong_khac_hanh_vi_cu(client, sample_db):
    tid = _make_ticket(sample_db)
    resp = client.get("/tickets", params={"page_size": 100}, headers=_SUP_HEADERS)
    assert resp.status_code == 200
    ids = {t["ticket_id"] for t in resp.json()["items"]}
    assert tid in ids
