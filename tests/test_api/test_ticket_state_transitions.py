"""FIN05-StressTest-Plan-v4 S4-05/S4-06.

S4-05: `POST /tools/escalate_ticket` trước đây chỉ test qua gọi hàm Python
trực tiếp (tests/test_tools/test_escalate_ticket.py) — chưa có test đi qua
HTTP thật (role gate, request schema, response shape), theo đúng mẫu
`test_resolution_approval.py` đã làm cho `/resolutions/{id}/approve`.

S4-06: `POST /tickets/{id}/request-more-info` — phát hiện thật lúc viết
test này: route KHÔNG có guard trạng thái (khác approve_resolution/
reject_resolution cùng file `src/api/main.py`, cả 2 đều chặn nếu đã quyết)
— đã VÁ trực tiếp (thêm chặn khi ticket đã approved/rejected, xem
src/api/main.py::request_more_info) vì đây là bug rõ ràng, không phải
quyết định thiết kế cần chờ PO."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.api.deps import get_session
from src.api.main import app
from src.auth import create_access_token
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


def _make_ticket(sample_db) -> str:
    r = create_ticket(
        sample_db, user_id="USR-A", complaint_type="wrong_recipient", scope="to_bank",
        description_raw="test", trans_id="TXN-0002",
    )
    sample_db.commit()
    return r["ticket_id"]


def _cskh_token() -> str:
    return create_access_token(user_id="USR-CSKH", role="cskh")


def _supervisor_token() -> str:
    return create_access_token(user_id="USR-SUP", role="supervisor")


# --- S4-05: /tools/escalate_ticket qua HTTP thật -----------------------------


def test_escalate_ticket_via_http_records_actor_and_timestamp(client, sample_db):
    ticket_id = _make_ticket(sample_db)
    resp = client.post(
        "/tools/escalate_ticket",
        json={"ticket_id": ticket_id, "target": "supervisor", "reason": "FS-06, FS-10"},
        headers={"Authorization": f"Bearer {_cskh_token()}"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["created_by"] == "USR-CSKH"
    assert body["created_at"] is not None


def test_escalate_ticket_via_http_rejects_empty_reason(client, sample_db):
    ticket_id = _make_ticket(sample_db)
    resp = client.post(
        "/tools/escalate_ticket",
        json={"ticket_id": ticket_id, "target": "supervisor", "reason": ""},
        headers={"Authorization": f"Bearer {_cskh_token()}"},
    )
    assert resp.status_code >= 400


def test_escalate_ticket_via_http_rejects_invalid_target(client, sample_db):
    ticket_id = _make_ticket(sample_db)
    resp = client.post(
        "/tools/escalate_ticket",
        json={"ticket_id": ticket_id, "target": "random_role", "reason": "FS-05"},
        headers={"Authorization": f"Bearer {_cskh_token()}"},
    )
    assert resp.status_code >= 400


# --- S4-06: request-more-info state machine ---------------------------------


def test_request_more_info_transitions_pending_to_need_more_info(client, sample_db):
    ticket_id = _make_ticket(sample_db)
    resp = client.post(
        f"/tickets/{ticket_id}/request-more-info",
        json={"note": "cần thêm ảnh chụp màn hình"},
        headers={"Authorization": f"Bearer {_cskh_token()}"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["hitl_status"] == "need_more_info"


def test_request_more_info_rejects_already_approved_ticket(client, sample_db):
    """Regression cho bug thật vừa vá — trước đây route này lật ngược 1
    ticket ĐÃ approved về need_more_info mà không báo lỗi gì."""
    from src.db.models import Ticket

    ticket_id = _make_ticket(sample_db)
    sample_db.get(Ticket, ticket_id).hitl_status = "approved"
    sample_db.commit()

    resp = client.post(
        f"/tickets/{ticket_id}/request-more-info",
        json={"note": "..."},
        headers={"Authorization": f"Bearer {_cskh_token()}"},
    )
    assert resp.status_code == 400, resp.text

    sample_db.expire_all()
    assert sample_db.get(Ticket, ticket_id).hitl_status == "approved", "trạng thái KHÔNG được đổi khi bị từ chối"


def test_request_more_info_rejects_already_rejected_ticket(client, sample_db):
    from src.db.models import Ticket

    ticket_id = _make_ticket(sample_db)
    sample_db.get(Ticket, ticket_id).hitl_status = "rejected"
    sample_db.commit()

    resp = client.post(
        f"/tickets/{ticket_id}/request-more-info",
        json={"note": "..."},
        headers={"Authorization": f"Bearer {_supervisor_token()}"},
    )
    assert resp.status_code == 400, resp.text
