"""Engine + session factory dùng chung cho seed script, tools, và API."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

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
    eng = create_engine(url, connect_args=connect_args, future=True)

    if url.startswith("sqlite"):
        # SQLite không bật FK constraint mặc định — I1 (toàn vẹn khoá ngoại)
        # cần cờ này để CHECK/FK thật sự chặn, không chỉ là trang trí.
        @event.listens_for(eng, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record):  # noqa: ANN001
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
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
