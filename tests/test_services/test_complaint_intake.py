"""§4.1 FIN05-Backend-Handoff.md — create_ticket_with_fraud_check() phải tự
tính fraud_signals từ dữ liệu DB (qua fraud_engine.py), không nhận tay từ
caller. Phạm vi MVP: chỉ FS-06 kích hoạt escalate (PRD §5)."""
from __future__ import annotations

import datetime as dt

import pytest
from sqlalchemy.orm import Session, sessionmaker

from src.db.models import AuthSession, BankAccount, Base, Complaint, Transaction, User, Wallet
from src.db.session import get_engine
from src.services.complaint_intake import create_ticket_with_fraud_check

NOW = dt.datetime(2026, 8, 1, 12, 0, 0)


@pytest.fixture()
def db_session(tmp_path) -> Session:
    db_path = tmp_path / "test.db"
    engine = get_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, future=True)
    session = factory()
    try:
        yield session
    finally:
        session.close()


def _seed_user_wallet_bank(session: Session, *, balance_after: int) -> None:
    session.add(
        User(
            user_id="USR-A", role="customer", full_name="Nguyen Van A",
            phone="0901000001", kyc_level=2, created_at=NOW,
        )
    )
    session.flush()
    session.add(Wallet(wallet_id="900000000001", user_id="USR-A", balance=balance_after, status="active"))
    session.add(
        BankAccount(
            bank_account_id="880000000001", user_id="USR-A", bank_code="VCB",
            account_no="880000000001", card_last4="1234", status="active", linked_at=NOW,
        )
    )
    session.flush()


def test_fs06_auto_computed_from_db_and_escalates(db_session: Session):
    """3 lần OTP sai trong 24h + rút ≥90% số dư → FS-06 tự tính, escalate
    ngay — không ai truyền fraud_signals bằng tay."""
    _seed_user_wallet_bank(db_session, balance_after=100_000)
    db_session.add(
        AuthSession(
            session_id="SES-0001", user_id="USR-A", otp_status="failed",
            failed_attempts=3, created_at=NOW - dt.timedelta(hours=1),
        )
    )
    db_session.add(
        Transaction(
            trans_id="TXN-0001", rec_code="RC-0001",
            send_wal_id="900000000001", rec_bank_account_id="880000000001",
            amount=900_000, fee=0, status="success", scope="to_bank", channel="withdrawal",
            idempotency_key="IDK-0001", created_at=NOW, completed_at=NOW,
            des="rut tien",
        )
    )
    db_session.commit()

    r = create_ticket_with_fraud_check(
        db_session,
        user_id="USR-A",
        complaint_type="money_not_received",
        scope="to_bank",
        description_raw="da rut tien nhung chua thay bao ve tai khoan",
        trans_id="TXN-0001",
    )

    assert r["should_escalate"] is True
    assert r["priority"] == "critical"
    assert r["escalation_target"] == "supervisor"

    complaint = db_session.get(Complaint, r["complaint_id"])
    assert complaint.fraud_signals == ["FS-06"]


def test_no_auth_anomaly_does_not_escalate(db_session: Session):
    """Rút tiền bình thường, không có phiên xác thực bất thường trước đó —
    không tín hiệu nào bật, không escalate."""
    _seed_user_wallet_bank(db_session, balance_after=900_000)
    db_session.add(
        Transaction(
            trans_id="TXN-0002", rec_code="RC-0002",
            send_wal_id="900000000001", rec_bank_account_id="880000000001",
            amount=100_000, fee=0, status="success", scope="to_bank", channel="withdrawal",
            idempotency_key="IDK-0002", created_at=NOW, completed_at=NOW,
            des="rut tien",
        )
    )
    db_session.commit()

    r = create_ticket_with_fraud_check(
        db_session,
        user_id="USR-A",
        complaint_type="money_not_received",
        scope="to_bank",
        description_raw="chua thay tien ve tai khoan",
        trans_id="TXN-0002",
    )

    assert r["should_escalate"] is False
    assert r["priority"] == "normal"

    complaint = db_session.get(Complaint, r["complaint_id"])
    assert complaint.fraud_signals == []


def test_not_found_case_still_creates_ticket_without_crashing(db_session: Session):
    """trans_id=None (case không tra ra giao dịch) vẫn phải chạy được — engine
    chỉ tính được FS-09/FS-10/FS-11 (không cần tx), không phải lỗi."""
    _seed_user_wallet_bank(db_session, balance_after=500_000)
    db_session.commit()

    r = create_ticket_with_fraud_check(
        db_session,
        user_id="USR-A",
        complaint_type="money_not_received",
        scope="from_bank",
        description_raw="khong tim thay giao dich nao ca",
        trans_id=None,
    )

    assert r["ticket_id"].startswith("TCK-")
    assert r["should_escalate"] is False
