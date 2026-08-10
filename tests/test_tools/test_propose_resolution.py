"""T2 — Data Brief §6.3 hàng 4: kết quả luôn chờ duyệt; không tham số nào
cho phép approved thẳng. Guardrail phụ: cited_tool_result_ids phải có thật."""
import pytest

from src.tools.base import ToolError
from src.tools.create_ticket import create_ticket
from src.tools.lookup_transaction import lookup_transaction
from src.tools.propose_resolution import propose_resolution


def _make_ticket(sample_db):
    r = create_ticket(
        sample_db,
        user_id="USR-A",
        complaint_type="wrong_recipient",
        scope="internal_wallet",
        description_raw="test",
        trans_id="TXN-0001",
    )
    return r["ticket_id"]


def test_resolution_always_pending_approval(sample_db):
    ticket_id = _make_ticket(sample_db)
    r = propose_resolution(sample_db, ticket_id=ticket_id, action_type="no_action", rationale="ly do")
    assert r["status"] == "pending_approval"


def test_propose_resolution_signature_has_no_status_param():
    import inspect

    sig = inspect.signature(propose_resolution)
    assert "status" not in sig.parameters


def test_rejects_fabricated_cited_tool_result_id(sample_db):
    ticket_id = _make_ticket(sample_db)
    with pytest.raises(ToolError):
        propose_resolution(
            sample_db,
            ticket_id=ticket_id,
            action_type="refund_to_wallet",
            rationale="ly do",
            amount=270_000,
            cited_tool_result_ids=["TR-KHONG-TON-TAI"],
        )


def test_accepts_real_cited_tool_result_id(sample_db):
    ticket_id = _make_ticket(sample_db)
    lookup = lookup_transaction(sample_db, trans_id="TXN-0001")
    r = propose_resolution(
        sample_db,
        ticket_id=ticket_id,
        action_type="refund_to_wallet",
        rationale="khop voi tra cuu",
        amount=270_000,
        cited_tool_result_ids=[lookup["tool_result_id"]],
    )
    assert r["status"] == "pending_approval"


def test_empty_rationale_rejected(sample_db):
    ticket_id = _make_ticket(sample_db)
    with pytest.raises(ToolError):
        propose_resolution(sample_db, ticket_id=ticket_id, action_type="no_action", rationale="   ")
