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


def test_fs07_ho_thu_thu_hop_phap_khong_escalate(sample_db):
    """Punch-list bảo mật 30/08 (#8) — FS-07 (`fan_in_roi_rut_ngay`: ví nhận
    từ ≥5 người rồi rút ≥80% trong 60 phút) mô tả ĐÚNG hành vi của một ví thu
    hộ hợp pháp (chủ shop nhỏ nhận tiền khách rồi rút về ngân hàng cuối ngày).

    `contracts/resolution-state-machine.yaml` khối `fraud.chinh_sach_escalate`
    nói rõ: PHẠM VI MVP CHỈ FS-06 kích hoạt escalate, Tầng A/B đã BỎ HẲN. Ca
    này nghiệm thu ĐÚNG chính sách hiện tại (FS-07 một mình KHÔNG escalate) —
    làm nền để nếu sau này ai mở lại Tầng A/B thì test này phải ĐỔI CÓ CHỦ Ý,
    không lặng lẽ đổi màu và vô tình biến ví thu hộ hợp pháp thành ca khẩn.

    Cùng khuôn `test_non_fs06_signal_does_not_escalate` — không giả lập lại
    FraudEngine/LedgerIndex (nặng, không phải thứ ca này canh); canh CHÍNH SÁCH
    tiêu thụ tín hiệu, giống các ca FS-05/FS-06 bên trên.
    """
    r = create_ticket(
        sample_db,
        user_id="USR-A",
        complaint_type="money_not_received",
        scope="internal_wallet",
        description_raw="vi nhan tien tu nhieu nguoi roi rut ve ngan hang cuoi ngay",
        trans_id="TXN-0002",
        fraud_signals=["FS-07"],
    )
    assert r["should_escalate"] is False, (
        f"FS-07 một mình đang ESCALATE ({r!r}) — vi phạm chính sách MVP hiện "
        "hành (contracts/resolution-state-machine.yaml: chỉ FS-06 escalate). "
        "Nếu đây là thay đổi CÓ CHỦ Ý (mở lại Tầng A/B), phải đi qua CLAUDE.md "
        "§3 (ADR + PO duyệt) TRƯỚC, và đo tỉ lệ dương tính giả FS-07 trên dữ "
        "liệu seed/eval trước khi gắn vào escalate — xem docs/security/"
        "review-2026-08-27-benchmark-eu-us.md Phát hiện #4."
    )
