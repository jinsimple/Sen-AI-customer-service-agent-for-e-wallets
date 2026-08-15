import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Cho phép `import src.*` khi chạy alembic từ thư mục gốc repo.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import DATABASE_URL  # noqa: E402
from src.db.models import Base  # noqa: E402

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# URL luôn lấy từ src/config.py — một nguồn sự thật duy nhất, không lệch
# với alembic.ini (tránh đúng lớp lỗi "schema đổi giữa chừng, máy lệch
# nhau" mà Data Brief §7 cảnh báo).
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # F-MIG — `render_as_batch` cho SQLite. Không có nó thì
        # `alembic upgrade head` trên DB TRẮNG chết ở `a1b2c3d4e5f6` (ADR-019)
        # với `NotImplementedError: No support for ALTER of constraints in
        # SQLite dialect`, và MỌI revision sau đó không bao giờ chạy.
        #
        # Vì sao lỗi này sống lâu mà không ai thấy: test suite dựng schema bằng
        # `Base.metadata.create_all()` (đọc thẳng models.py), KHÔNG qua alembic.
        # Hai đường dựng schema tách biệt, chỉ MỘT được canh — đúng Luật 14
        # (nhánh không gọi được từ test là nhánh không ai canh). 540 test xanh
        # không nói gì về việc chuỗi migration có chạy được hay không.
        #
        # Bật theo DIALECT chứ không bật vô điều kiện: Postgres ALTER được
        # trực tiếp, ép batch ở đó là dựng-bảng-chép-dữ-liệu vô ích trên bảng
        # có thể rất lớn.
        la_sqlite = connection.dialect.name == "sqlite"
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=la_sqlite,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
