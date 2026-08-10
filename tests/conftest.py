"""Fixture DB tối giản cho test_tools — KHÔNG dùng data/generated (60k dòng,
chậm và không cần thiết cho unit test hành vi tool). Mỗi test được một DB
SQLite file riêng trong thư mục tạm, tạo schema thẳng từ models.py qua
`create_all` (không qua Alembic — Alembic test riêng ở test_migrations, nếu
có), và có đúng vài bản ghi cần cho mỗi test bên trong `sample_db`.
"""
from __future__ import annotations

import datetime as dt

import pytest
from sqlalchemy.orm import Session, sessionmaker

from src.db.models import BankAccount, Base, Transaction, User, Wallet
from src.db.session import get_engine


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


@pytest.fixture()
def sample_db(db_session: Session) -> Session:
    """2 khách, 1 CSKH, 1 supervisor; vài ví/TK ngân hàng; 3 giao dịch."""
    now = dt.datetime(2026, 8, 1, 10, 0, 0)

    users = [
        User(user_id="USR-A", role="customer", full_name="Nguyễn Văn A", phone="0901000001", kyc_level=2, created_at=now),
        User(user_id="USR-B", role="customer", full_name="Trần Thị B", phone="0901000002", kyc_level=1, created_at=now),
        User(user_id="USR-CSKH", role="cskh", full_name="CSKH Một", phone="0901000003", kyc_level=2, created_at=now),
        User(user_id="USR-SUP", role="supervisor", full_name="Sếp Một", phone="0901000004", kyc_level=2, created_at=now),
    ]
    db_session.add_all(users)
    db_session.flush()  # không có relationship() giữa models -> UOW không tự suy được
    # thứ tự phụ thuộc từ cột FK thô; flush theo từng nhóm để giữ đúng thứ tự cha->con.

    wallets = [
        Wallet(wallet_id="900000000001", user_id="USR-A", balance=1_000_000, status="active"),
        Wallet(wallet_id="900000000002", user_id="USR-B", balance=2_000_000, status="active"),
    ]
    db_session.add_all(wallets)

    bank_accounts = [
        BankAccount(
            bank_account_id="880000000001",
            user_id="USR-A",
            bank_code="VCB",
            account_no="880000000001",
            card_last4="1234",
            status="active",
            linked_at=now,
        ),
    ]
    db_session.add_all(bank_accounts)
    db_session.flush()

    transactions = [
        Transaction(
            trans_id="TXN-0001",
            rec_code="RC-0001",
            send_wal_id="900000000001",
            rec_wal_id="900000000002",
            amount=270_000,
            fee=0,
            status="success",
            scope="internal_wallet",
            channel="p2p",
            idempotency_key="IDK-0001",
            created_at=now,
            completed_at=now,
            des="chuyen nham",
        ),
        # Cặp double_charge — cùng idempotency_key, cách nhau < 60s, cùng amount (I6).
        Transaction(
            trans_id="TXN-0002",
            rec_code="RC-0002",
            send_wal_id="900000000001",
            rec_bank_account_id="880000000001",
            amount=500_000,
            fee=3300,
            status="success",
            scope="to_bank",
            channel="withdrawal",
            idempotency_key="IDK-0002",
            created_at=now,
            completed_at=now,
            des="rut tien",
        ),
        Transaction(
            trans_id="TXN-0003",
            rec_code="RC-0003",
            send_wal_id="900000000001",
            rec_bank_account_id="880000000001",
            amount=500_000,
            fee=3300,
            status="success",
            scope="to_bank",
            channel="withdrawal",
            idempotency_key="IDK-0002",
            created_at=now + dt.timedelta(seconds=30),
            completed_at=now + dt.timedelta(seconds=30),
            des="rut tien",
        ),
    ]
    db_session.add_all(transactions)
    db_session.commit()
    return db_session
