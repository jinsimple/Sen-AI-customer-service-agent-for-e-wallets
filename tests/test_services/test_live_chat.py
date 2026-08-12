"""Live chat (2026-08-11) — mirror test_complaint_intake.py style. Dùng
sample_db (tests/conftest.py: USR-A/USR-B khách hàng, USR-CSKH/USR-SUP nhân
viên, TXN-0001 giữa USR-A/USR-B) — tạo 1 ticket thật qua
create_ticket_with_fraud_check() trước khi test live_chat.py, không tự chế
Ticket/Complaint tay (giữ đúng bất biến FK/CHECK constraint thật)."""
from __future__ import annotations

import pytest

from src.services import live_chat
from src.services.complaint_intake import create_ticket_with_fraud_check
from src.tools.base import ToolError


def _make_ticket(sample_db, *, user_id: str = "USR-A") -> str:
    created = create_ticket_with_fraud_check(
        sample_db,
        user_id=user_id,
        complaint_type="wrong_recipient",
        scope="internal_wallet",
        description_raw="test live chat",
        trans_id="TXN-0001",
    )
    return created["ticket_id"]


def test_open_chat_session_creates_waiting_session(sample_db):
    ticket_id = _make_ticket(sample_db)
    result = live_chat.open_chat_session(sample_db, ticket_id=ticket_id, customer_id="USR-A")
    assert result["status"] == "waiting"
    assert result["ticket_id"] == ticket_id
    assert result["claimed_by"] is None


def test_open_chat_session_reuses_existing_waiting_session(sample_db):
    """Khách bấm lại nút mở chat không tạo phiên trùng cho CÙNG 1 ticket."""
    ticket_id = _make_ticket(sample_db)
    first = live_chat.open_chat_session(sample_db, ticket_id=ticket_id, customer_id="USR-A")
    second = live_chat.open_chat_session(sample_db, ticket_id=ticket_id, customer_id="USR-A")
    assert first["chat_session_id"] == second["chat_session_id"]


def test_open_chat_session_rejects_ticket_not_owned_by_customer(sample_db):
    ticket_id = _make_ticket(sample_db, user_id="USR-A")
    with pytest.raises(ToolError):
        live_chat.open_chat_session(sample_db, ticket_id=ticket_id, customer_id="USR-B")


def test_claim_session_race_second_claim_is_noop(sample_db):
    """2 CSKH cùng bấm nhận 1 phiên — chỉ người ĐẦU TIÊN thành công, người
    sau nhận None (không phải lỗi hệ thống, không raise)."""
    ticket_id = _make_ticket(sample_db)
    chat_session = live_chat.open_chat_session(sample_db, ticket_id=ticket_id, customer_id="USR-A")
    chat_session_id = chat_session["chat_session_id"]

    first_claim = live_chat.claim_session(sample_db, chat_session_id=chat_session_id, staff_id="USR-CSKH")
    second_claim = live_chat.claim_session(sample_db, chat_session_id=chat_session_id, staff_id="USR-SUP")

    assert first_claim is not None
    assert first_claim["claimed_by"] == "USR-CSKH"
    assert first_claim["status"] == "active"
    assert second_claim is None


def test_record_message_persists_and_encrypts_at_rest(sample_db, tmp_path):
    ticket_id = _make_ticket(sample_db)
    chat_session = live_chat.open_chat_session(sample_db, ticket_id=ticket_id, customer_id="USR-A")
    saved = live_chat.record_message(
        sample_db, chat_session_id=chat_session["chat_session_id"], role="customer", content="số điện thoại của tôi là 0901000001"
    )
    sample_db.commit()
    assert saved["content"] == "số điện thoại của tôi là 0901000001"

    # Đọc THẲNG bytes thô qua raw connection (bỏ qua tầng ORM tự giải mã) —
    # xác nhận content KHÔNG nằm plaintext trong DB, cùng kỹ thuật đã dùng
    # để xác nhận EncryptedText hoạt động cho PolicyChunk.text.
    raw = sample_db.connection().exec_driver_sql(
        "SELECT content FROM messages WHERE message_id = ?", (saved["message_id"],)
    ).scalar()
    assert "0901000001" not in raw


def test_submit_csat_rejects_out_of_range_score(sample_db):
    ticket_id = _make_ticket(sample_db)
    chat_session = live_chat.open_chat_session(sample_db, ticket_id=ticket_id, customer_id="USR-A")
    with pytest.raises(ToolError):
        live_chat.submit_csat(sample_db, chat_session_id=chat_session["chat_session_id"], score=6)


def test_get_handoff_context_includes_ticket_and_complaint(sample_db):
    ticket_id = _make_ticket(sample_db)
    context = live_chat.get_handoff_context(sample_db, ticket_id=ticket_id)
    assert context["ticket"]["ticket_id"] == ticket_id
    assert context["complaint"]["type"] == "wrong_recipient"
    assert context["customer"]["user_id"] == "USR-A"
