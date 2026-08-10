"""T2 — Data Brief §6.3 hàng 5: bắt buộc reason; ghi log ai/khi nào;
target phải hợp lệ."""
import pytest

from src.tools.base import ToolError
from src.tools.create_ticket import create_ticket
from src.tools.escalate_ticket import escalate_ticket


def _make_ticket(sample_db):
    r = create_ticket(
        sample_db,
        user_id="USR-A",
        complaint_type="wrong_recipient",
        scope="to_bank",
        description_raw="test",
        trans_id="TXN-0002",
    )
    return r["ticket_id"]


def test_reason_required(sample_db):
    ticket_id = _make_ticket(sample_db)
    with pytest.raises(ToolError):
        escalate_ticket(sample_db, ticket_id=ticket_id, target="supervisor", reason="", created_by="USR-CSKH")


def test_invalid_target_rejected(sample_db):
    ticket_id = _make_ticket(sample_db)
    with pytest.raises(ToolError):
        escalate_ticket(
            sample_db, ticket_id=ticket_id, target="random_role", reason="FS-05", created_by="USR-CSKH"
        )


def test_records_who_and_when(sample_db):
    ticket_id = _make_ticket(sample_db)
    r = escalate_ticket(
        sample_db, ticket_id=ticket_id, target="supervisor", reason="FS-06, FS-10", created_by="USR-CSKH"
    )
    assert r["created_by"] == "USR-CSKH"
    assert r["created_at"] is not None
