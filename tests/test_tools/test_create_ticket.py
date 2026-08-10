"""T2 — Data Brief §6.3 hàng 3: từ chối trans_id không tồn tại, trừ đúng
trường hợp not_found (trans_id=None) được cho phép."""
import pytest

from src.tools.base import ToolError
from src.tools.create_ticket import create_ticket


def test_rejects_nonexistent_trans_id(sample_db):
    with pytest.raises(ToolError):
        create_ticket(
            sample_db,
            user_id="USR-A",
            complaint_type="money_not_received",
            scope="internal_wallet",
            description_raw="test",
            trans_id="TXN-BIA-RA",
        )


def test_allows_not_found_case_with_trans_id_none(sample_db):
    r = create_ticket(
        sample_db,
        user_id="USR-A",
        complaint_type="money_not_received",
        scope="from_bank",
        description_raw="khong tim thay giao dich",
        trans_id=None,
    )
    assert r["ticket_id"].startswith("TCK-")


def test_ticket_always_starts_assigned_to_cskh_not_supervisor(sample_db):
    from src.db.models import Ticket

    r = create_ticket(
        sample_db,
        user_id="USR-A",
        complaint_type="wrong_recipient",
        scope="internal_wallet",
        description_raw="test",
        trans_id="TXN-0001",
    )
    ticket = sample_db.get(Ticket, r["ticket_id"])
    assert ticket.assigned_role == "cskh"


def test_non_fs06_signal_does_not_escalate(sample_db):
    r = create_ticket(
        sample_db,
        user_id="USR-A",
        complaint_type="wrong_recipient",
        scope="to_bank",
        description_raw="chuyen 500tr luc 23h de tat toan mua xe",
        trans_id="TXN-0002",
        fraud_signals=["FS-05"],
    )
    assert r["should_escalate"] is False


def test_fs06_signal_escalates_immediately(sample_db):
    r = create_ticket(
        sample_db,
        user_id="USR-A",
        complaint_type="money_not_received",
        scope="to_bank",
        description_raw="rut sach vi sau khi nhap sai otp nhieu lan",
        trans_id="TXN-0002",
        fraud_signals=["FS-06"],
    )
    assert r["should_escalate"] is True
    assert r["priority"] == "critical"
    assert r["escalation_target"] == "supervisor"
