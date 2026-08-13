"""Engine + session factory dùng chung cho seed script, tools, và API."""
from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.config import DATABASE_URL

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = None  # lazily created via get_engine() so tests can override DATABASE_URL


def get_engine(database_url: str | None = None) -> Engine:
    from sqlalchemy import create_engine

    url = database_url or DATABASE_URL
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    # pool_pre_ping — phát hiện thật (FIN05-StressTest-Plan-v4 6.3): THIẾU cờ
    # này là đúng gotcha "Redis/DB client bật socket_keepalive +
    # health_check_interval" đã đúc kết trong checklist đóng gói production —
    # container Postgres restart/mạng nội bộ cloud âm thầm đóng connection
    # nhàn rỗi, pool KHÔNG biết, request tiếp theo tái dùng connection chết
    # -> `OperationalError: server closed the connection unexpectedly` ngẫu
    # nhiên trên production dù local chạy hoàn hảo (SQLite không có khái
    # niệm "connection chết qua mạng" nên không lộ ra lúc dev). `pool_pre_ping`
    # tự SELECT 1 kiểm tra trước khi phát connection từ pool, âm thầm tái kết
    # nối nếu chết — không tăng round-trip đáng kể (chỉ 1 lần/connection lấy
    # từ pool, không phải 1 lần/query).
    # Kích thước pool — TÍNH TOÁN, không để mặc định (5 + 10 overflow = 15).
    #
    # Từ 2026-08-13 backend chạy nhiều worker (ADR-014/015). Mỗi worker mở pool
    # RIÊNG, nên tổng kết nối tới Postgres là:
    #     workers x (DB_POOL_SIZE + DB_MAX_OVERFLOW + CHECKPOINT_POOL_MAX)
    # Postgres mặc định max_connections=100 (đã kiểm bằng SHOW max_connections).
    # Với mặc định dưới đây: 4 x (10 + 5 + 5) = 80 < 100, còn chỗ cho psql/
    # migration/monitoring. Tăng worker mà quên tính lại chỗ này sẽ ra lỗi
    # "FATAL: sorry, too many clients already" — lỗi chỉ lộ ra khi tải cao,
    # đúng lúc không muốn gặp nhất.
    pool_kwargs = {}
    if not url.startswith("sqlite"):
        pool_kwargs = {
            "pool_size": int(os.environ.get("DB_POOL_SIZE", "10")),
            "max_overflow": int(os.environ.get("DB_MAX_OVERFLOW", "5")),
            # Trả connection nhàn rỗi về sau 30 phút — tránh giữ chỗ vô hạn
            # trong max_connections khi tải xuống thấp.
            "pool_recycle": 1800,
        }
    eng = create_engine(
        url, connect_args=connect_args, future=True, pool_pre_ping=True, **pool_kwargs
    )

    if url.startswith("sqlite"):
        # SQLite không bật FK constraint mặc định — I1 (toàn vẹn khoá ngoại)
        # cần cờ này để CHECK/FK thật sự chặn, không chỉ là trang trí.
        #
        # journal_mode=WAL + busy_timeout — phát hiện thật (FIN05-StressTest-
        # Plan-v4 GAP): chạy e2e với nhiều BrowserContext đồng thời (khách +
        # CSKH + sếp, mỗi context tự gọi OTP/tool-call ghi DB) liên tục dính
        # `sqlite3.OperationalError: database is locked` — xác nhận qua log
        # backend thật (20 lần lặp lại), không phải suy đoán. Chế độ mặc định
        # của SQLite (rollback journal, "delete") khoá ĐỘC QUYỀN cả file khi
        # có 1 transaction đang ghi, chặn luôn cả những connection khác chỉ
        # ĐỌC — WAL cho phép đọc đồng thời trong lúc có 1 writer đang chạy.
        # `busy_timeout` bổ sung: nếu 2 writer THẬT SỰ trùng thời điểm (WAL
        # không giải quyết được ca này), SQLite tự đợi rồi thử lại thay vì
        # trả lỗi ngay lập tức. Chỉ áp dụng nhánh SQLite — production dùng
        # Postgres (DATABASE_URL khác), không ảnh hưởng.
        @event.listens_for(eng, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record):  # noqa: ANN001
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA busy_timeout=5000")
            cursor.close()

    return eng


_default_engine = get_engine()
SessionLocal = sessionmaker(bind=_default_engine, expire_on_commit=False, future=True)


@contextmanager
def session_scope(session_factory: sessionmaker | None = None) -> Iterator[Session]:
    factory = session_factory or SessionLocal
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
