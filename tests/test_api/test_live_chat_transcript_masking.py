"""M3 (`d8e4ff9`, niêm `992e382`) — đường đọc THỨ HAI: route GET
`/live-chat/sessions/{id}/messages` (`src/api/main.py`) che PII khi đọc lại,
tách biệt với đường đọc thứ nhất (giá trị trả về của `record_message`, WS
broadcast — xem `tests/test_services/test_live_chat.py`). Commit vá nói rõ
CẢ HAI đường đọc đều cần che riêng; test này canh đường thứ hai, không trùng
đường thứ nhất."""
from __future__ import annotations

import datetime as dt

from fastapi.testclient import TestClient

from src.api.deps import get_session
from src.api.main import app
from src.auth import create_access_token
from src.services import live_chat
from src.services.complaint_intake import create_ticket_with_fraud_check


def test_transcript_route_masks_phone_and_bank_account_but_keeps_amount(sample_db):
    ticket_id = create_ticket_with_fraud_check(
        sample_db, user_id="USR-A", complaint_type="wrong_recipient", scope="internal_wallet",
        description_raw="test transcript masking", trans_id="TXN-0001",
    )["ticket_id"]
    sample_db.commit()
    opened = live_chat.open_chat_session(sample_db, ticket_id=ticket_id, customer_id="USR-A")
    live_chat.record_message(
        sample_db,
        chat_session_id=opened["chat_session_id"],
        role="customer",
        content="Gọi mình 0987654321 nhé, STK 88000000000001. Mình chuyển 1500000000 đồng.",
    )
    sample_db.commit()

    def _override_session():
        try:
            yield sample_db
            sample_db.commit()
        except Exception:
            sample_db.rollback()
            raise

    app.dependency_overrides[get_session] = _override_session
    try:
        client = TestClient(app)
        owner_token = create_access_token(user_id="USR-A", role="customer", otp_verified_at=dt.datetime.utcnow())
        resp = client.get(
            f"/live-chat/sessions/{opened['chat_session_id']}/messages",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert resp.status_code == 200
        noi_dung = resp.json()["messages"][0]["content"]
    finally:
        app.dependency_overrides.clear()

    assert "0987654321" not in noi_dung, f"Route transcript vẫn trả SĐT thô: {noi_dung!r}"
    assert "88000000000001" not in noi_dung, f"Route transcript vẫn trả STK thô: {noi_dung!r}"
    assert "0001" in noi_dung, f"STK phải giữ 4 số cuối sau khi che: {noi_dung!r}"
    assert "1500000000 đồng" in noi_dung, (
        f"Số tiền BỊ ĂN MẤT khi che ở route transcript: {noi_dung!r}"
    )
