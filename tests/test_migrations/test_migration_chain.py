"""FIN05-StressTest-Plan-v4 M4-01/M4-02/M4-03 — rủi ro cao nhất khi deploy
domain thật lần đầu: DB production sẽ chạy `alembic upgrade head` từ RỖNG,
qua TOÀN BỘ chuỗi migration hiện có, trên Postgres THẬT (không phải SQLite
— migrations dùng `batch_alter_table` để tương thích 2 engine, nhưng
Postgres có ràng buộc FK/type CHẶT hơn nhiều, migration "chạy được" trên
SQLite không chứng minh chạy được trên Postgres thật).

Chạy `alembic` qua SUBPROCESS (không gọi `alembic.command` trong tiến
trình pytest) — `migrations/env.py` đọc `DATABASE_URL` từ `src.config`,
vốn đã bị BIND CỨNG lúc import module đầu tiên trong phiên pytest (không
reload lại theo os.environ sau đó, cùng lý do đã áp dụng cho
`tests/test_config/test_fail_fast_secrets.py`).

Skip graceful nếu không có Postgres thật reachable (không phá dev/CI nào
chỉ chạy SQLite) — verify thật bằng cách chạy TRONG network Docker:
`docker compose exec backend su appuser -c "python -m pytest tests/test_migrations/ -v"`.
CI (`ci.yml`) dùng GitHub Actions `services: postgres:` để có Postgres thật
trên `localhost`, publish port mặc định (khác hẳn `docker-compose.yml` của
app — service đó CỐ Ý không publish port ra host, xem test_network_isolation.py)."""
from __future__ import annotations

import os
import subprocess
import sys
import uuid

import pytest
import sqlalchemy as sa
from sqlalchemy.engine import make_url

from src.config import DATABASE_URL, ROOT_DIR
from tests._suite_day_du import can_ha_tang

_BASE_URL = make_url(DATABASE_URL)
_IS_POSTGRES = _BASE_URL.get_backend_name().startswith("postgresql")


def _maintenance_engine() -> sa.Engine:
    admin_url = _BASE_URL.set(database="postgres")
    return sa.create_engine(admin_url, isolation_level="AUTOCOMMIT")


def _postgres_reachable() -> bool:
    if not _IS_POSTGRES:
        return False
    try:
        _maintenance_engine().connect().close()
        return True
    except Exception:
        return False


@pytest.fixture(scope="module", autouse=True)
def _yeu_cau_postgres_that():
    """NHÓM A (`tests/_suite_day_du.py`) — thay cho `pytestmark = skipif(...)`
    cũ để `FIN05_SUITE_DAY_DU=1` biến skip thành FAIL rõ ràng."""
    if not _postgres_reachable():
        can_ha_tang(
            "Cần Postgres thật reachable qua DATABASE_URL (không phải SQLite "
            "mặc định của pytest local)",
            cach_dung=(
                'chạy trong network Docker: `docker compose exec backend su appuser -c '
                '"python -m pytest tests/test_migrations/ -v"`, hoặc CI job có service '
                "postgres (xem ci.yml)"
            ),
            allow_module_level=True,
        )


@pytest.fixture()
def temp_migration_db() -> str:
    """Tạo 1 database Postgres RIÊNG, RỖNG cho mỗi test — không đụng DB thật
    app đang dùng, không lẫn giữa các lần chạy song song."""
    db_name = f"fin05_migration_test_{uuid.uuid4().hex[:12]}"
    admin_engine = _maintenance_engine()
    with admin_engine.connect() as conn:
        conn.execute(sa.text(f'CREATE DATABASE "{db_name}"'))
    try:
        # render_as_string(hide_password=False) — KHÔNG dùng str(url) trần,
        # SQLAlchemy hiện đại tự che mật khẩu thành "***" trong str() (an
        # toàn khi log), nhưng đây là chuỗi cần dùng THẬT để kết nối subprocess
        # — phát hiện thật lúc chạy: str(url) làm alembic subprocess nhận
        # đúng chữ "***" làm mật khẩu, "password authentication failed".
        yield _BASE_URL.set(database=db_name).render_as_string(hide_password=False)
    finally:
        with admin_engine.connect() as conn:
            conn.execute(
                sa.text(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    "WHERE datname = :db AND pid <> pg_backend_pid()"
                ),
                {"db": db_name},
            )
            conn.execute(sa.text(f'DROP DATABASE IF EXISTS "{db_name}"'))
    admin_engine.dispose()


def _run_alembic(*args: str, database_url: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=str(ROOT_DIR),
        env={**os.environ, "DATABASE_URL": database_url},
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_upgrade_head_applies_cleanly_from_empty_database(temp_migration_db):
    """M4-01/M4-03 — TOÀN BỘ chuỗi migration (không chỉ bản mới nhất) áp
    được từ database rỗng, đúng kịch bản lần đầu deploy domain thật."""
    result = _run_alembic("upgrade", "head", database_url=temp_migration_db)
    assert result.returncode == 0, f"alembic upgrade head thất bại:\n{result.stdout}\n{result.stderr}"

    engine = sa.create_engine(temp_migration_db)
    inspector = sa.inspect(engine)
    tables = set(inspector.get_table_names())
    expected_core_tables = {
        "users", "wallets", "bank_accounts", "transactions", "complaints",
        "tickets", "resolutions", "chat_sessions", "messages", "policy_documents",
    }
    missing = expected_core_tables - tables
    assert not missing, f"Thiếu bảng sau khi upgrade head: {missing} (có: {tables})"
    engine.dispose()


def test_downgrade_to_base_then_upgrade_again_is_stable(temp_migration_db):
    """M4-02 — roundtrip downgrade toàn bộ về base rồi upgrade lại head
    không lỗi FK/constraint — chứng minh mọi bước downgrade() viết đúng,
    không chỉ upgrade() được test (lỗi downgrade thường bị bỏ sót vì ít
    khi thật sự chạy tới khi cần rollback production)."""
    up1 = _run_alembic("upgrade", "head", database_url=temp_migration_db)
    assert up1.returncode == 0, f"Lần upgrade đầu thất bại:\n{up1.stderr}"

    down = _run_alembic("downgrade", "base", database_url=temp_migration_db)
    assert down.returncode == 0, f"alembic downgrade base thất bại:\n{down.stdout}\n{down.stderr}"

    engine = sa.create_engine(temp_migration_db)
    inspector = sa.inspect(engine)
    remaining = {t for t in inspector.get_table_names() if t != "alembic_version"}
    assert not remaining, f"Downgrade base vẫn còn sót bảng: {remaining}"
    engine.dispose()

    up2 = _run_alembic("upgrade", "head", database_url=temp_migration_db)
    assert up2.returncode == 0, f"Upgrade lại head sau downgrade thất bại:\n{up2.stdout}\n{up2.stderr}"
