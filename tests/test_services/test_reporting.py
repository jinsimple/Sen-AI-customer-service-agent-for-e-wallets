"""FIN05-StressTest-Plan-v4 S4-04 — `build_summary` (src/services/reporting.py)
chỉ được test NÔNG qua `test_authz_matrix.py` (`safe_success_check=True` —
chỉ xác nhận route trả 200, KHÔNG xác nhận số liệu tính ra đúng). Seed dữ
liệu ĐÃ BIẾT TRƯỚC (N ticket trạng thái X, M resolution approved/rejected,
K escalation) rồi assert build_summary trả ĐÚNG số, không lệch 1 đơn vị —
số liệu này CSKH/supervisor dùng để ra quyết định vận hành thật, sai số
liệu nguy hiểm hơn route lỗi rõ ràng (route lỗi thấy ngay, số liệu sai âm
thầm không ai phát hiện)."""
from __future__ import annotations

import datetime as dt

from src.db.models import Escalation
from src.services.complaint_intake import create_ticket_with_fraud_check
from src.services.reporting import build_summary
from src.tools.propose_resolution import propose_resolution


def _make_ticket(sample_db, *, user_id: str, complaint_type: str = "wrong_recipient", trans_id: str | None = "TXN-0001") -> str:
    created = create_ticket_with_fraud_check(
        sample_db, user_id=user_id, complaint_type=complaint_type, scope="internal_wallet",
        description_raw="test reporting", trans_id=trans_id,
    )
    sample_db.commit()
    return created["ticket_id"]


def test_total_tickets_matches_exact_seeded_count(sample_db):
    for _ in range(3):
        _make_ticket(sample_db, user_id="USR-A")
    summary = build_summary(sample_db)
    assert summary["total_tickets"] == 3


def test_pct_ai_proposal_approved_counts_only_decided_resolutions(sample_db):
    """2 approved, 1 rejected, 1 vẫn 'pending_approval' (chưa quyết) — %
    duyệt phải tính trên 3 CÁI ĐÃ QUYẾT (2/3 ≈ 66.7%), KHÔNG tính luôn 4
    resolution như thể cái pending cũng là 1 lần từ chối."""
    t1 = _make_ticket(sample_db, user_id="USR-A", trans_id="TXN-0001")
    t2 = _make_ticket(sample_db, user_id="USR-A", trans_id="TXN-0002")
    t3 = _make_ticket(sample_db, user_id="USR-A", trans_id="TXN-0003")
    t4 = _make_ticket(sample_db, user_id="USR-A", trans_id=None)

    # `amount` là BẮT BUỘC cho refund_* từ hotfix V3.2 (14/08): số tiền hoàn
    # phải > 0 và không vượt số tiền giao dịch được trích. Truyền đúng số tiền
    # của từng giao dịch trong conftest (TXN-0001: 270.000 · TXN-0002/0003:
    # 500.000); t4 không có trans_id nên chỉ cần > 0. Test này kiểm TỈ LỆ DUYỆT
    # (pct_ai_proposal_approved), không kiểm số tiền — thêm `amount` không làm
    # đổi thứ nó canh.
    r1 = propose_resolution(sample_db, ticket_id=t1, action_type="refund_to_wallet", rationale="test", amount=270_000)
    r2 = propose_resolution(sample_db, ticket_id=t2, action_type="refund_to_wallet", rationale="test", amount=500_000)
    r3 = propose_resolution(sample_db, ticket_id=t3, action_type="refund_to_wallet", rationale="test", amount=500_000)
    propose_resolution(sample_db, ticket_id=t4, action_type="refund_to_wallet", rationale="test", amount=100_000)  # r4, vẫn pending
    sample_db.commit()

    now = dt.datetime.utcnow()
    from src.db.models import Resolution

    for rid in (r1["resolution_id"], r2["resolution_id"]):
        resolution = sample_db.get(Resolution, rid)
        resolution.status = "approved"
        resolution.approved_at = now
        resolution.approved_by = "USR-SUP"  # BR-10: approved bắt buộc có approver
    # BR-11 (INV-14, ADR-019 — 14/08): 'rejected' giờ BẮT BUỘC có đủ
    # reject_reason + rejected_by + rejected_at, ép ở tầng DB. Set thiếu là
    # IntegrityError ngay tại commit này. Test đang kiểm TỈ LỆ DUYỆT, không
    # kiểm lý do từ chối — thêm 3 trường không làm đổi thứ nó canh.
    rejected = sample_db.get(Resolution, r3["resolution_id"])
    rejected.status = "rejected"
    rejected.reject_reason = "sai_so_lieu"
    rejected.rejected_by = "USR-SUP"
    rejected.rejected_at = now
    sample_db.commit()

    summary = build_summary(sample_db)
    assert summary["pct_ai_proposal_approved"] == 66.7


def test_pct_escalated_matches_exact_count(sample_db):
    t1 = _make_ticket(sample_db, user_id="USR-A", trans_id="TXN-0001")
    _make_ticket(sample_db, user_id="USR-A", trans_id="TXN-0002")
    _make_ticket(sample_db, user_id="USR-A", trans_id="TXN-0003")
    _make_ticket(sample_db, user_id="USR-A", trans_id=None)

    sample_db.add(
        Escalation(
            escalation_id="ESC-test-001", ticket_id=t1, target="supervisor",
            reason="test", created_by="USR-CSKH", created_at=dt.datetime.utcnow(),
        )
    )
    sample_db.commit()

    summary = build_summary(sample_db)
    assert summary["pct_escalated"] == 25.0  # 1/4


def test_by_complaint_type_and_scope_breakdown_is_exact(sample_db):
    _make_ticket(sample_db, user_id="USR-A", complaint_type="wrong_recipient", trans_id="TXN-0001")
    _make_ticket(sample_db, user_id="USR-A", complaint_type="wrong_recipient", trans_id="TXN-0002")
    _make_ticket(sample_db, user_id="USR-A", complaint_type="double_charge", trans_id="TXN-0003")

    summary = build_summary(sample_db)
    assert summary["by_complaint_type"] == {"wrong_recipient": 2, "double_charge": 1}
    assert summary["by_scope"] == {"internal_wallet": 3}


def test_date_range_filter_excludes_tickets_outside_window(sample_db):
    """Ticket TRƯỚC date_from phải bị loại — sai sót thường gặp: quên lọc
    theo created_at, cộng nhầm cả ticket ngoài kỳ báo cáo."""
    old_ticket_id = _make_ticket(sample_db, user_id="USR-A", trans_id="TXN-0001")
    from src.db.models import Ticket

    sample_db.get(Ticket, old_ticket_id).created_at = dt.datetime(2020, 1, 1)
    sample_db.commit()

    _make_ticket(sample_db, user_id="USR-A", trans_id="TXN-0002")  # tạo hôm nay — trong kỳ

    summary = build_summary(sample_db, date_from=dt.datetime.utcnow() - dt.timedelta(days=1))
    assert summary["total_tickets"] == 1


def test_no_tickets_returns_none_percentages_not_zero_division_error():
    """DB rỗng — không được crash chia cho 0, và None (không rõ) khác 0%
    (0% ngụ ý CÓ dữ liệu nhưng tỷ lệ duyệt là 0, sai lệch ý nghĩa nếu
    nhầm 'chưa có gì để tính' thành 'toàn bộ bị từ chối')."""
    from sqlalchemy.orm import Session

    from src.db.models import Base
    from src.db.session import get_engine as _get_engine

    engine = _get_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as empty_db:
        summary = build_summary(empty_db)
        assert summary["total_tickets"] == 0
        assert summary["pct_ai_proposal_approved"] is None
        assert summary["pct_escalated"] is None
        assert summary["avg_processing_hours"] is None
