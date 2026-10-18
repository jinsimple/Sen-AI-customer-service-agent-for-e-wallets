"""Engine + session factory shared by the seed script, tools and the API."""
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
    # pool_pre_ping — real finding (FIN05-StressTest-Plan-v4 6.3): MISSING this flag is
    # exactly the "Redis/DB client must enable socket_keepalive + health_check_interval" gotcha
    # captured in the production packaging checklist — a Postgres container restart or the cloud
    # internal network silently closes idle connections, the pool does NOT know, and the next
    # request reuses a dead connection
    # -> random `OperationalError: server closed the connection unexpectedly` in production even
    # though local runs are perfect (SQLite has no notion of "connection died over the network",
    # so it never shows up in dev). `pool_pre_ping` issues SELECT 1 before handing out a pooled
    # connection and silently reconnects if it is dead — negligible extra round-trips (once per
    # connection checkout, not once per query).
    # Pool size — CALCULATED, not left at the default (5 + 10 overflow = 15).
    #
    # Since 2026-08-13 the backend runs several workers (ADR-014/015). Each worker opens its OWN
    # pool, so the total number of Postgres connections is:
    #     workers x (DB_POOL_SIZE + DB_MAX_OVERFLOW + CHECKPOINT_POOL_MAX)
    # Postgres defaults to max_connections=100 (verified with SHOW max_connections).
    # With the defaults below: 4 x (10 + 5 + 5) = 80 < 100, leaving room for psql/
    # migrations/monitoring. Adding workers without recomputing this yields
    # "FATAL: sorry, too many clients already" — an error that only appears under high load,
    # exactly when you least want it.
    pool_kwargs = {}
    if not url.startswith("sqlite"):
        pool_kwargs = {
            "pool_size": int(os.environ.get("DB_POOL_SIZE", "10")),
            "max_overflow": int(os.environ.get("DB_MAX_OVERFLOW", "5")),
            # Return idle connections after 30 minutes — avoids holding max_connections slots
            # indefinitely when load drops.
            "pool_recycle": 1800,
        }
    eng = create_engine(
        url, connect_args=connect_args, future=True, pool_pre_ping=True, **pool_kwargs
    )

    if url.startswith("sqlite"):
        # SQLite does not enable FK constraints by default — I1 (foreign-key integrity)
        # needs this flag so CHECK/FK actually block, rather than being decoration.
        #
        # journal_mode=WAL + busy_timeout — real finding (FIN05-StressTest-Plan-v4 GAP): running
        # e2e with several concurrent BrowserContexts (customer + CSKH + supervisor, each calling
        # OTP/tool endpoints that write to the DB) kept hitting
        # `sqlite3.OperationalError: database is locked` — confirmed in real backend logs
        # (20 repetitions), not guessed. SQLite's default mode (rollback journal, "delete") takes an
        # EXCLUSIVE lock on the whole file while one transaction is writing, blocking even
        # connections that only READ — WAL allows concurrent reads while one writer runs.
        # `busy_timeout` complements it: if 2 writers REALLY collide (which WAL cannot solve),
        # SQLite waits and retries instead of failing immediately. Applies only to the SQLite
        # branch — production uses Postgres (different DATABASE_URL), unaffected.
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
