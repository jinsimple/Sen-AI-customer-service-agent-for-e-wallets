"""Dependency injection cho FastAPI — 1 session SQLAlchemy / 1 request."""
from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy.orm import Session

from src.db.session import SessionLocal


def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
