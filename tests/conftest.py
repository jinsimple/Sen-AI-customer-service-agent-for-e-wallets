"""Fixture DB tối giản cho test_tools — KHÔNG dùng data/generated (60k dòng,
chậm và không cần thiết cho unit test hành vi tool). Mỗi test được một DB
SQLite file riêng trong thư mục tạm, tạo schema thẳng từ models.py qua
`create_all` (không qua Alembic — Alembic test riêng ở test_migrations, nếu
có), và có đúng vài bản ghi cần cho mỗi test bên trong `sample_db`.
"""
from __future__ import annotations

import datetime as dt
import os

# Test/CI không có Jaeger sống — `OTEL_SDK_DISABLED` là biến chuẩn của OTel
# SDK (không phải tự chế), khiến get_tracer() trả no-op tracer, tránh spam
# lỗi "failed to connect... 4317" mỗi lần chạy pytest (đã xác nhận thật: xem
# lịch sử — không set biến này log lỗi export che mất kết quả test thật).
# PHẢI set TRƯỚC khi bất kỳ module nào import src.observability.tracing.
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

# DATABASE_URL giờ BẮT BUỘC, không còn fallback SQLite im lặng (ADR-013 —
# fallback đó từng làm hệ thống âm thầm tách đôi database). Test KHÔNG thực sự
# dùng biến này: mỗi test được một engine SQLite tạm riêng qua fixture
# `sample_db` bên dưới. Nhưng src/config.py đọc nó lúc IMPORT nên phải có giá
# trị hợp lệ trước khi bất kỳ module src nào được nạp — cùng lý do và cùng chỗ
# với OTEL_SDK_DISABLED ở trên.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest
from argon2 import PasswordHasher
from sqlalchemy.orm import Session, sessionmaker

from src.db.models import BankAccount, Base, Transaction, User, Wallet
from src.db.session import get_engine
from src.redis_client import get_default_client

# Đăng nhập bằng mật khẩu (quyết định 2026-08-12) — mọi user fixture cần
# password_hash hợp lệ, nếu không MỌI test gọi /auth/login qua sample_db sẽ
# 401 (đúng chủ đích của _DUMMY_PASSWORD_HASH ở src/api/main.py::login khi
# password_hash NULL). Cùng giá trị "Demo@123" dùng ở scripts/gen_dataset.py
# (không import trực tiếp script đó vào test — giữ tests/ tách biệt khỏi
# scripts/, chỉ trùng giá trị hằng số để người đọc không phải nhớ 2 mật khẩu
# khác nhau).
TEST_PASSWORD = "Demo@123"
_TEST_PASSWORD_HASHER = PasswordHasher()


@pytest.fixture(autouse=True)
def _flush_redis_between_tests():
    """Đợt nâng cấp Auth Flow (2026-08-12) — JWT revocation/refresh-token
    (src/auth.py) VÀ rate-limit (src/rate_limit.py, thay InMemoryRateLimiter
    cũ) giờ lưu trên Redis (fakeredis trong test, xem src/redis_client.py).
    fakeredis dùng 1 FakeServer SINGLETON cho cả tiến trình pytest (khác DB —
    mỗi test có 1 SQLite file riêng qua db_session/tmp_path) — nếu không dọn,
    state rate-limit/revocation RÒ RỈ giữa các test dùng chung user_id (rất
    phổ biến, "USR-A" xuất hiện khắp nơi), gây fail giả kiểu 429 ở test không
    liên quan gì tới rate-limit. flushdb() TRƯỚC mỗi test — cô lập hoàn toàn,
    cùng tinh thần db_session tạo SQLite file mới mỗi test."""
    get_default_client().flushdb()
    yield


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

    pw_hash = _TEST_PASSWORD_HASHER.hash(TEST_PASSWORD)
    users = [
        User(user_id="USR-A", role="customer", full_name="Nguyễn Văn A", phone="0901000001", kyc_level=2, password_hash=pw_hash, created_at=now),
        User(user_id="USR-B", role="customer", full_name="Trần Thị B", phone="0901000002", kyc_level=1, password_hash=pw_hash, created_at=now),
        User(user_id="USR-CSKH", role="cskh", full_name="CSKH Một", phone="0901000003", kyc_level=2, password_hash=pw_hash, created_at=now),
        User(user_id="USR-SUP", role="supervisor", full_name="Sếp Một", phone="0901000004", kyc_level=2, password_hash=pw_hash, created_at=now),
        # USR-0119/USR-0201 — dùng riêng cho tests/test_api/test_reject_note_doi_khang.py
        # (test 10/11), CỐ Ý khác USR-A/USR-CSKH: hai test đó kiểm `note` không
        # rò qua route/tool của MỘT user cụ thể, dùng lại USR-A (đã xuất hiện ở
        # khắp file test khác) sẽ không phân biệt được "sạch vì đúng cơ chế" với
        # "sạch vì trùng ca đã kiểm ở nơi khác".
        User(user_id="USR-0119", role="customer", full_name="Khách 0119", phone="0901000119", kyc_level=2, password_hash=pw_hash, created_at=now),
        User(user_id="USR-0201", role="cskh", full_name="CSKH 0201", phone="0901000201", kyc_level=2, password_hash=pw_hash, created_at=now),
    ]
    db_session.add_all(users)
    db_session.flush()  # không có relationship() giữa models -> UOW không tự suy được
    # thứ tự phụ thuộc từ cột FK thô; flush theo từng nhóm để giữ đúng thứ tự cha->con.

    wallets = [
        Wallet(wallet_id="900000000001", user_id="USR-A", balance=1_000_000, status="active"),
        Wallet(wallet_id="900000000002", user_id="USR-B", balance=2_000_000, status="active"),
        # Ví riêng của USR-0119 — TXN-0001 đã thuộc USR-A/USR-B (send/rec cố
        # định trên schema, mỗi giao dịch chỉ có đúng 2 bên), nên không thể
        # cho USR-0119 "mượn" TXN-0001. Cần giao dịch riêng, xem TXN-0119-A.
        Wallet(wallet_id="900000000119", user_id="USR-0119", balance=500_000, status="active"),
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
        # USR-0119 là MỘT BÊN thật (người gửi) — cần cho tests/test_api/
        # test_reject_note_doi_khang.py test 10/11 tạo ticket + tự tra cứu
        # đúng giao dịch của mình qua route/tool khách.
        Transaction(
            trans_id="TXN-0119-A",
            rec_code="RC-0119",
            send_wal_id="900000000119",
            rec_wal_id="900000000002",
            amount=92_000,
            fee=0,
            status="success",
            scope="internal_wallet",
            channel="p2p",
            idempotency_key="IDK-0119",
            created_at=now,
            completed_at=now,
            des="test note doi khang",
        ),
    ]
    db_session.add_all(transactions)
    db_session.commit()
    return db_session
