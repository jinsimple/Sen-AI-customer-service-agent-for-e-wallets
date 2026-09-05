"""Đồng bộ claim live-chat ("Mở & nhận") với claim Ticket (ADR-064(b)).

Bối cảnh (05/09): 30 test cũ ở `test_ticket_claim_adr064.py` chỉ phủ đường
"Nhận vé" (`POST /tickets/{id}/claim`) — KHÔNG phủ đường "Mở & nhận" (claim
chat session qua `POST /live-chat/sessions/{id}/claim`), vốn là nút CSKH THẬT
SỰ dùng trong toàn bộ luồng live-chat B6-B9. Hậu quả đo được qua UI thật
(QA/QC, po-demo): CSKH-A "Mở & nhận" → `Ticket.claimed_by` KHÔNG được set →
CSKH-B mở `GET /tickets/{id}` vẫn 200 (BOLA thật, không phải giả thuyết).

3 ca theo đúng yêu cầu vá (không đọc `src/`, chỉ đối chiếu HTTP + DB thật qua
`sample_db`, theo khuôn `test_live_chat_ws.py`/`test_ticket_claim_adr064.py`)."""
from __future__ import annotations

import datetime as dt

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from src.api.deps import get_session
from src.api.live_chat_ws import ConnectionManager
from src.api.main import app
from src.auth import create_access_token
from src.db.models import ChatSession, Ticket
from src.services.complaint_intake import create_ticket_with_fraud_check


def _setup_client(sample_db, monkeypatch):
    def _override_session():
        try:
            yield sample_db
            sample_db.commit()
        except Exception:
            sample_db.rollback()
            raise

    app.dependency_overrides[get_session] = _override_session
    test_factory = sessionmaker(bind=sample_db.get_bind(), future=True)
    manager = ConnectionManager()
    monkeypatch.setattr("src.api.live_chat_ws.SessionLocal", test_factory)
    monkeypatch.setattr("src.api.live_chat_ws.manager", manager)
    monkeypatch.setattr("src.api.main._live_chat_manager", manager)
    return TestClient(app)


def _make_ticket_and_chat_session(sample_db, client, *, user_id: str = "USR-A", trans_id: str = "TXN-0001") -> tuple[str, str]:
    created = create_ticket_with_fraud_check(
        sample_db, user_id=user_id, complaint_type="wrong_recipient", scope="internal_wallet",
        description_raw="test dong bo claim", trans_id=trans_id,
    )
    sample_db.commit()
    ticket_id = created["ticket_id"]
    customer_token = create_access_token(user_id=user_id, role="customer", otp_verified_at=dt.datetime.utcnow())
    resp = client.post("/live-chat/ws-ticket", json={"ticket_id": ticket_id}, headers={"Authorization": f"Bearer {customer_token}"})
    assert resp.status_code == 200, resp.text
    chat_session_id = resp.json()["chat_session_id"]
    return ticket_id, chat_session_id


_CSKH_A = ("USR-CSKH", "cskh")
_CSKH_B = ("USR-0201", "cskh")
_SUP = ("USR-SUP", "supervisor")


def _token(user_id: str, role: str) -> str:
    return create_access_token(user_id=user_id, role=role)


def test_cskh_claim_chat_session_cung_khoa_ticket_theo_adr064(sample_db, monkeypatch):
    """"Mở & nhận" (claim chat session) bởi CSKH PHẢI set Ticket.claimed_by —
    đây CHÍNH LÀ khoảng trống gây BOLA thật đo được qua UI (05/09)."""
    client = _setup_client(sample_db, monkeypatch)
    ticket_id, chat_session_id = _make_ticket_and_chat_session(sample_db, client)

    claim_resp = client.post(
        f"/live-chat/sessions/{chat_session_id}/claim", headers={"Authorization": f"Bearer {_token(*_CSKH_A)}"}
    )
    assert claim_resp.status_code == 200, claim_resp.text

    sample_db.expire_all()
    ticket = sample_db.get(Ticket, ticket_id)
    assert ticket.claimed_by == "USR-CSKH", "Mở & nhận PHẢI set Ticket.claimed_by — đây là gap gây BOLA"

    # CSKH-A (người vừa claim) vẫn đọc được ticket của chính mình.
    resp_own = client.get(f"/tickets/{ticket_id}", headers={"Authorization": f"Bearer {_token(*_CSKH_A)}"})
    assert resp_own.status_code == 200, resp_own.text

    # CSKH-B (không liên quan) PHẢI bị chặn 404 — đúng luật ADR-064 đã có,
    # giờ áp dụng được vì claimed_by đã thật sự được set.
    resp_other = client.get(f"/tickets/{ticket_id}", headers={"Authorization": f"Bearer {_token(*_CSKH_B)}"})
    assert resp_other.status_code == 404, resp_other.text


def test_supervisor_claim_chat_session_khong_khoa_ticket(sample_db, monkeypatch):
    """Sếp claim chat session (vẫn hợp lệ ở tầng live-chat) KHÔNG được phép
    khoá Ticket — ADR-064(b) cố ý: supervisor không có route claim ticket,
    "không claim" nghĩa là Ticket.claimed_by phải giữ nguyên None."""
    client = _setup_client(sample_db, monkeypatch)
    ticket_id, chat_session_id = _make_ticket_and_chat_session(sample_db, client, trans_id="TXN-0002")

    claim_resp = client.post(
        f"/live-chat/sessions/{chat_session_id}/claim", headers={"Authorization": f"Bearer {_token(*_SUP)}"}
    )
    assert claim_resp.status_code == 200, claim_resp.text

    sample_db.expire_all()
    ticket = sample_db.get(Ticket, ticket_id)
    assert ticket.claimed_by is None, "Sếp claim chat session KHÔNG được khoá Ticket (Sếp không có route /claim)"

    # Vé vẫn ở pool — CSKH bất kỳ vẫn thấy 200 và claim được qua ADR-064.
    resp_pool = client.get(f"/tickets/{ticket_id}", headers={"Authorization": f"Bearer {_token(*_CSKH_A)}"})
    assert resp_pool.status_code == 200, resp_pool.text

    claim_ticket_resp = client.post(f"/tickets/{ticket_id}/claim", headers={"Authorization": f"Bearer {_token(*_CSKH_A)}"})
    assert claim_ticket_resp.status_code == 200, claim_ticket_resp.text


def test_ticket_da_claim_thi_claim_chat_session_nguoi_khac_bi_chan(sample_db, monkeypatch):
    """Chống cướp CHIỀU NGƯỢC LẠI: nếu Ticket đã bị CSKH-B claim (qua "Nhận
    vé" ADR-064) TRƯỚC, thì CSKH-A không được claim chat session của CHÍNH
    ticket đó nữa — 409, và ChatSession.claimed_by phải giữ nguyên None (không
    bị claim nửa chừng rồi mới phát hiện xung đột)."""
    client = _setup_client(sample_db, monkeypatch)
    ticket_id, chat_session_id = _make_ticket_and_chat_session(sample_db, client, trans_id="TXN-0003")

    claim_ticket_resp = client.post(f"/tickets/{ticket_id}/claim", headers={"Authorization": f"Bearer {_token(*_CSKH_B)}"})
    assert claim_ticket_resp.status_code == 200, claim_ticket_resp.text

    claim_chat_resp = client.post(
        f"/live-chat/sessions/{chat_session_id}/claim", headers={"Authorization": f"Bearer {_token(*_CSKH_A)}"}
    )
    assert claim_chat_resp.status_code == 409, claim_chat_resp.text

    sample_db.expire_all()
    chat_session = sample_db.get(ChatSession, chat_session_id)
    assert chat_session.claimed_by is None, "Claim chat session bị chặn PHẢI là all-or-nothing — không claim nửa chừng"
