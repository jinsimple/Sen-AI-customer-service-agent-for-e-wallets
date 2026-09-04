"""ADR-064(b) — CSKH nhận vé chủ động, chỉ thấy pool+của mình.

Test qua HTTP thật (role gate, row-level scoping, BOLA), theo đúng khuôn
`test_ticket_state_transitions.py` (client fixture + create_ticket trực tiếp
để dựng ticket, không cần đi qua toàn bộ luồng AI agent)."""
from __future__ import annotations

import datetime as dt

import pytest
from fastapi.testclient import TestClient

from src.api.deps import get_session
from src.api.main import app
from src.auth import create_access_token
from src.db.models import ChatSession
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


def _make_ticket(sample_db, *, user_id: str = "USR-A", trans_id: str = "TXN-0002") -> str:
    r = create_ticket(
        sample_db, user_id=user_id, complaint_type="wrong_recipient", scope="to_bank",
        description_raw="test", trans_id=trans_id,
    )
    sample_db.commit()
    return r["ticket_id"]


def _token(user_id: str, role: str) -> str:
    return create_access_token(user_id=user_id, role=role)


_CSKH_A = ("USR-CSKH", "cskh")
_CSKH_B = ("USR-0201", "cskh")  # 2 CSKH riêng biệt sẵn có trong sample_db — BOLA cần đủ 2 người
_SUP = ("USR-SUP", "supervisor")


# --- POST /tickets/{id}/claim ------------------------------------------------


def test_claim_unclaimed_ticket_succeeds(client, sample_db):
    tid = _make_ticket(sample_db)
    resp = client.post(f"/tickets/{tid}/claim", headers={"Authorization": f"Bearer {_token(*_CSKH_A)}"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ticket_id"] == tid
    assert body["claimed_by"] == "USR-CSKH"
    assert body["claimed_at"] is not None


def test_claim_idempotent_for_same_cskh(client, sample_db):
    tid = _make_ticket(sample_db)
    r1 = client.post(f"/tickets/{tid}/claim", headers={"Authorization": f"Bearer {_token(*_CSKH_A)}"})
    r2 = client.post(f"/tickets/{tid}/claim", headers={"Authorization": f"Bearer {_token(*_CSKH_A)}"})
    assert r1.status_code == 200 and r2.status_code == 200
    # Mốc nhận LẦN ĐẦU giữ nguyên — bấm lại không ghi đè claimed_at.
    assert r1.json()["claimed_at"] == r2.json()["claimed_at"]


def test_claim_by_other_cskh_returns_409(client, sample_db):
    tid = _make_ticket(sample_db)
    r1 = client.post(f"/tickets/{tid}/claim", headers={"Authorization": f"Bearer {_token(*_CSKH_A)}"})
    assert r1.status_code == 200
    r2 = client.post(f"/tickets/{tid}/claim", headers={"Authorization": f"Bearer {_token(*_CSKH_B)}"})
    assert r2.status_code == 409, r2.text


def test_claim_nonexistent_ticket_404(client):
    resp = client.post("/tickets/TCK-khong-ton-tai/claim", headers={"Authorization": f"Bearer {_token(*_CSKH_A)}"})
    assert resp.status_code == 404


def test_claim_requires_cskh_role_supervisor_bi_chan(client, sample_db):
    tid = _make_ticket(sample_db)
    resp = client.post(f"/tickets/{tid}/claim", headers={"Authorization": f"Bearer {_token(*_SUP)}"})
    assert resp.status_code == 403


# --- GET /tickets — row-level scoping / BOLA --------------------------------


def test_list_tickets_cskh_thay_pool_va_cua_minh_khong_thay_cua_nguoi_khac(client, sample_db):
    tid_pool = _make_ticket(sample_db, trans_id="TXN-0002")
    tid_a = _make_ticket(sample_db, trans_id="TXN-0003")
    tid_b = _make_ticket(sample_db, trans_id="TXN-0001")
    client.post(f"/tickets/{tid_a}/claim", headers={"Authorization": f"Bearer {_token(*_CSKH_A)}"})
    client.post(f"/tickets/{tid_b}/claim", headers={"Authorization": f"Bearer {_token(*_CSKH_B)}"})

    resp = client.get("/tickets", headers={"Authorization": f"Bearer {_token(*_CSKH_A)}"})
    assert resp.status_code == 200
    ids = {t["ticket_id"] for t in resp.json()}
    assert tid_pool in ids, "vé chưa claim (pool) phải thấy được"
    assert tid_a in ids, "vé của chính mình phải thấy được"
    assert tid_b not in ids, "BOLA: KHÔNG được thấy vé CSKH khác đã claim"


def test_list_tickets_supervisor_khong_bi_loc_van_thay_tat_ca(client, sample_db):
    tid_a = _make_ticket(sample_db, trans_id="TXN-0002")
    tid_b = _make_ticket(sample_db, trans_id="TXN-0003")
    client.post(f"/tickets/{tid_a}/claim", headers={"Authorization": f"Bearer {_token(*_CSKH_A)}"})
    client.post(f"/tickets/{tid_b}/claim", headers={"Authorization": f"Bearer {_token(*_CSKH_B)}"})

    resp = client.get("/tickets", headers={"Authorization": f"Bearer {_token(*_SUP)}"})
    assert resp.status_code == 200
    ids = {t["ticket_id"] for t in resp.json()}
    assert tid_a in ids and tid_b in ids, "supervisor không đổi quyền — vẫn thấy TẤT CẢ"


# --- GET /tickets/{id}/transcript — CÙNG LUẬT, anti-enumeration 404 ---------


def test_transcript_404_cho_ve_cskh_khac_da_claim(client, sample_db):
    tid_b = _make_ticket(sample_db, trans_id="TXN-0001")
    client.post(f"/tickets/{tid_b}/claim", headers={"Authorization": f"Bearer {_token(*_CSKH_B)}"})

    resp = client.get(f"/tickets/{tid_b}/transcript", headers={"Authorization": f"Bearer {_token(*_CSKH_A)}"})
    assert resp.status_code == 404, resp.text


def test_transcript_cho_qua_khi_cung_nguoi_claim(client, sample_db):
    tid_a = _make_ticket(sample_db, trans_id="TXN-0002")
    client.post(f"/tickets/{tid_a}/claim", headers={"Authorization": f"Bearer {_token(*_CSKH_A)}"})

    resp = client.get(f"/tickets/{tid_a}/transcript", headers={"Authorization": f"Bearer {_token(*_CSKH_A)}"})
    assert resp.status_code != 404, resp.text


def test_transcript_cho_qua_khi_ve_con_trong_pool(client, sample_db):
    tid_pool = _make_ticket(sample_db, trans_id="TXN-0002")
    resp = client.get(f"/tickets/{tid_pool}/transcript", headers={"Authorization": f"Bearer {_token(*_CSKH_A)}"})
    assert resp.status_code != 404, resp.text


# --- GET /tickets/{id} (detail) — Review bắt lỗ thật, ban đầu bị bỏ sót ---


def test_detail_404_cho_ve_cskh_khac_da_claim(client, sample_db):
    tid_b = _make_ticket(sample_db, trans_id="TXN-0001")
    client.post(f"/tickets/{tid_b}/claim", headers={"Authorization": f"Bearer {_token(*_CSKH_B)}"})

    resp = client.get(f"/tickets/{tid_b}", headers={"Authorization": f"Bearer {_token(*_CSKH_A)}"})
    assert resp.status_code == 404, resp.text


def test_detail_cho_qua_khi_ve_con_trong_pool_hoac_cua_minh(client, sample_db):
    tid_pool = _make_ticket(sample_db, trans_id="TXN-0002")
    resp_pool = client.get(f"/tickets/{tid_pool}", headers={"Authorization": f"Bearer {_token(*_CSKH_A)}"})
    assert resp_pool.status_code == 200, resp_pool.text

    tid_a = _make_ticket(sample_db, trans_id="TXN-0003")
    client.post(f"/tickets/{tid_a}/claim", headers={"Authorization": f"Bearer {_token(*_CSKH_A)}"})
    resp_own = client.get(f"/tickets/{tid_a}", headers={"Authorization": f"Bearer {_token(*_CSKH_A)}"})
    assert resp_own.status_code == 200, resp_own.text


def test_detail_supervisor_khong_bi_loc(client, sample_db):
    tid_b = _make_ticket(sample_db, trans_id="TXN-0001")
    client.post(f"/tickets/{tid_b}/claim", headers={"Authorization": f"Bearer {_token(*_CSKH_B)}"})

    resp = client.get(f"/tickets/{tid_b}", headers={"Authorization": f"Bearer {_token(*_SUP)}"})
    assert resp.status_code == 200, resp.text


def test_transcript_supervisor_khong_bi_loc(client, sample_db):
    tid_b = _make_ticket(sample_db, trans_id="TXN-0001")
    client.post(f"/tickets/{tid_b}/claim", headers={"Authorization": f"Bearer {_token(*_CSKH_B)}"})

    resp = client.get(f"/tickets/{tid_b}/transcript", headers={"Authorization": f"Bearer {_token(*_SUP)}"})
    assert resp.status_code != 404, resp.text


# --- POST /tickets/{id}/request-more-info — Review soát toàn bộ, bắt thêm --


def test_request_more_info_404_cho_ve_cskh_khac_da_claim(client, sample_db):
    tid_b = _make_ticket(sample_db, trans_id="TXN-0001")
    client.post(f"/tickets/{tid_b}/claim", headers={"Authorization": f"Bearer {_token(*_CSKH_B)}"})

    resp = client.post(
        f"/tickets/{tid_b}/request-more-info",
        json={"note": "cần thêm thông tin"},
        headers={"Authorization": f"Bearer {_token(*_CSKH_A)}"},
    )
    assert resp.status_code == 404, resp.text


def test_request_more_info_cho_qua_khi_ve_con_trong_pool(client, sample_db):
    tid_pool = _make_ticket(sample_db, trans_id="TXN-0002")
    resp = client.post(
        f"/tickets/{tid_pool}/request-more-info",
        json={"note": "cần thêm thông tin"},
        headers={"Authorization": f"Bearer {_token(*_CSKH_A)}"},
    )
    assert resp.status_code == 200, resp.text


def test_request_more_info_supervisor_khong_bi_loc(client, sample_db):
    tid_b = _make_ticket(sample_db, trans_id="TXN-0001")
    client.post(f"/tickets/{tid_b}/claim", headers={"Authorization": f"Bearer {_token(*_CSKH_B)}"})

    resp = client.post(
        f"/tickets/{tid_b}/request-more-info",
        json={"note": "cần thêm thông tin"},
        headers={"Authorization": f"Bearer {_token(*_SUP)}"},
    )
    assert resp.status_code == 200, resp.text


# --- POST /tools/propose_resolution — ticket_id từ BODY --------------------


def test_propose_resolution_404_cho_ve_cskh_khac_da_claim(client, sample_db):
    tid_b = _make_ticket(sample_db, trans_id="TXN-0001")
    client.post(f"/tickets/{tid_b}/claim", headers={"Authorization": f"Bearer {_token(*_CSKH_B)}"})

    resp = client.post(
        "/tools/propose_resolution",
        json={"ticket_id": tid_b, "action_type": "no_action", "rationale": "test"},
        headers={"Authorization": f"Bearer {_token(*_CSKH_A)}"},
    )
    assert resp.status_code == 404, resp.text


def test_propose_resolution_cho_qua_khi_da_claim_dung_nguoi(client, sample_db):
    tid_a = _make_ticket(sample_db, trans_id="TXN-0002")
    client.post(f"/tickets/{tid_a}/claim", headers={"Authorization": f"Bearer {_token(*_CSKH_A)}"})

    resp = client.post(
        "/tools/propose_resolution",
        json={"ticket_id": tid_a, "action_type": "no_action", "rationale": "test"},
        headers={"Authorization": f"Bearer {_token(*_CSKH_A)}"},
    )
    assert resp.status_code == 200, resp.text


# --- POST /tools/escalate_ticket — ticket_id từ BODY ------------------------


def test_escalate_ticket_404_cho_ve_cskh_khac_da_claim(client, sample_db):
    tid_b = _make_ticket(sample_db, trans_id="TXN-0001")
    client.post(f"/tickets/{tid_b}/claim", headers={"Authorization": f"Bearer {_token(*_CSKH_B)}"})

    resp = client.post(
        "/tools/escalate_ticket",
        json={"ticket_id": tid_b, "target": "supervisor", "reason": "test"},
        headers={"Authorization": f"Bearer {_token(*_CSKH_A)}"},
    )
    assert resp.status_code == 404, resp.text


def test_escalate_ticket_cho_qua_khi_con_trong_pool(client, sample_db):
    tid_pool = _make_ticket(sample_db, trans_id="TXN-0002")
    resp = client.post(
        "/tools/escalate_ticket",
        json={"ticket_id": tid_pool, "target": "supervisor", "reason": "test"},
        headers={"Authorization": f"Bearer {_token(*_CSKH_A)}"},
    )
    assert resp.status_code == 200, resp.text


# --- GET /resolutions — đường vòng rò cùng dữ liệu, Review bắt -------------


def test_list_resolutions_cskh_khong_thay_cua_nguoi_khac(client, sample_db):
    tid_a = _make_ticket(sample_db, trans_id="TXN-0002")
    client.post(f"/tickets/{tid_a}/claim", headers={"Authorization": f"Bearer {_token(*_CSKH_A)}"})
    r1 = client.post(
        "/tools/propose_resolution",
        json={"ticket_id": tid_a, "action_type": "no_action", "rationale": "vé của A"},
        headers={"Authorization": f"Bearer {_token(*_CSKH_A)}"},
    )
    assert r1.status_code == 200, r1.text

    tid_b = _make_ticket(sample_db, trans_id="TXN-0001")
    client.post(f"/tickets/{tid_b}/claim", headers={"Authorization": f"Bearer {_token(*_CSKH_B)}"})
    r2 = client.post(
        "/tools/propose_resolution",
        json={"ticket_id": tid_b, "action_type": "no_action", "rationale": "vé của B"},
        headers={"Authorization": f"Bearer {_token(*_CSKH_B)}"},
    )
    assert r2.status_code == 200, r2.text

    resp = client.get("/resolutions?status=all", headers={"Authorization": f"Bearer {_token(*_CSKH_A)}"})
    assert resp.status_code == 200
    ticket_ids_thay = {r["ticket_id"] for r in resp.json()}
    assert tid_a in ticket_ids_thay, "resolution của chính mình phải thấy"
    assert tid_b not in ticket_ids_thay, "BOLA: KHÔNG thấy resolution của CSKH khác"


def test_list_resolutions_supervisor_khong_bi_loc(client, sample_db):
    tid_b = _make_ticket(sample_db, trans_id="TXN-0001")
    client.post(f"/tickets/{tid_b}/claim", headers={"Authorization": f"Bearer {_token(*_CSKH_B)}"})
    client.post(
        "/tools/propose_resolution",
        json={"ticket_id": tid_b, "action_type": "no_action", "rationale": "vé của B"},
        headers={"Authorization": f"Bearer {_token(*_CSKH_B)}"},
    )

    resp = client.get("/resolutions?status=all", headers={"Authorization": f"Bearer {_token(*_SUP)}"})
    assert resp.status_code == 200
    ticket_ids_thay = {r["ticket_id"] for r in resp.json()}
    assert tid_b in ticket_ids_thay, "supervisor không đổi quyền — vẫn thấy TẤT CẢ"


# --- GET /live-chat/sessions/by-ticket/{id} — rò SĐT khách thật ------------


def test_live_chat_by_ticket_404_cho_ve_cskh_khac_da_claim(client, sample_db):
    tid_b = _make_ticket(sample_db, trans_id="TXN-0001")
    client.post(f"/tickets/{tid_b}/claim", headers={"Authorization": f"Bearer {_token(*_CSKH_B)}"})

    resp = client.get(
        f"/live-chat/sessions/by-ticket/{tid_b}", headers={"Authorization": f"Bearer {_token(*_CSKH_A)}"}
    )
    assert resp.status_code == 404, resp.text


def test_live_chat_by_ticket_cho_qua_khi_con_trong_pool(client, sample_db):
    tid_pool = _make_ticket(sample_db, trans_id="TXN-0002")
    resp = client.get(
        f"/live-chat/sessions/by-ticket/{tid_pool}", headers={"Authorization": f"Bearer {_token(*_CSKH_A)}"}
    )
    assert resp.status_code == 200, resp.text


def test_live_chat_by_ticket_supervisor_khong_bi_loc(client, sample_db):
    tid_b = _make_ticket(sample_db, trans_id="TXN-0001")
    client.post(f"/tickets/{tid_b}/claim", headers={"Authorization": f"Bearer {_token(*_CSKH_B)}"})

    resp = client.get(
        f"/live-chat/sessions/by-ticket/{tid_b}", headers={"Authorization": f"Bearer {_token(*_SUP)}"}
    )
    assert resp.status_code == 200, resp.text


# --- GET /live-chat/sessions/{id}/messages — Review độc lập soát tìm ra ----


def _make_chat_session(sample_db, *, ticket_id: str, customer_id: str = "USR-A") -> str:
    cs = ChatSession(
        chat_session_id=f"CHS-{ticket_id}",
        ticket_id=ticket_id,
        customer_id=customer_id,
        status="waiting",
        started_at=dt.datetime.utcnow(),
    )
    sample_db.add(cs)
    sample_db.commit()
    return cs.chat_session_id


def test_live_chat_messages_404_cho_ve_cskh_khac_da_claim(client, sample_db):
    tid_b = _make_ticket(sample_db, trans_id="TXN-0001")
    chs = _make_chat_session(sample_db, ticket_id=tid_b)
    client.post(f"/tickets/{tid_b}/claim", headers={"Authorization": f"Bearer {_token(*_CSKH_B)}"})

    resp = client.get(f"/live-chat/sessions/{chs}/messages", headers={"Authorization": f"Bearer {_token(*_CSKH_A)}"})
    assert resp.status_code == 404, resp.text


def test_live_chat_messages_cho_qua_khi_con_trong_pool(client, sample_db):
    tid_pool = _make_ticket(sample_db, trans_id="TXN-0002")
    chs = _make_chat_session(sample_db, ticket_id=tid_pool)

    resp = client.get(f"/live-chat/sessions/{chs}/messages", headers={"Authorization": f"Bearer {_token(*_CSKH_A)}"})
    assert resp.status_code == 200, resp.text


def test_live_chat_messages_supervisor_khong_bi_loc(client, sample_db):
    tid_b = _make_ticket(sample_db, trans_id="TXN-0001")
    chs = _make_chat_session(sample_db, ticket_id=tid_b)
    client.post(f"/tickets/{tid_b}/claim", headers={"Authorization": f"Bearer {_token(*_CSKH_B)}"})

    resp = client.get(f"/live-chat/sessions/{chs}/messages", headers={"Authorization": f"Bearer {_token(*_SUP)}"})
    assert resp.status_code == 200, resp.text


def test_live_chat_messages_customer_ownership_van_dung_khong_doi(client, sample_db):
    """Kiểm KHÔNG hồi quy: check 403 sẵn có cho customer (khác chủ phiên) —
    ADR-064(b) chỉ thêm nhánh cskh, không đụng nhánh customer đã có từ trước."""
    tid_pool = _make_ticket(sample_db, trans_id="TXN-0002")
    chs = _make_chat_session(sample_db, ticket_id=tid_pool, customer_id="USR-A")

    resp = client.get(
        f"/live-chat/sessions/{chs}/messages", headers={"Authorization": f"Bearer {_token('USR-B', 'customer')}"}
    )
    assert resp.status_code == 403, resp.text
