"""ticket claim (ADR-064(b) — CSKH chỉ thấy pool+của mình)

Revision ID: 6d36fb6e303e
Revises: c4d5e6f7a8b9
Create Date: 2026-09-04

`claimed_by` NULL = vé còn trong pool chung, mọi CSKH thấy+claim được (dùng
IS NULL, không dùng giá trị sentinel) — đúng khuôn NULLABLE VĨNH VIỄN đã lặp
lại nhiều lần trong dự án cho các cột "chưa/không có" (vd Ticket.handoff_at).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6d36fb6e303e'
down_revision: Union[str, Sequence[str], None] = 'c4d5e6f7a8b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tickets', sa.Column('claimed_by', sa.String(), nullable=True))
    op.add_column('tickets', sa.Column('claimed_at', sa.DateTime(), nullable=True))
    # F-MIG — batch_alter_table: SQLite không ALTER được constraint (test
    # local dùng sqlite, prod dùng Postgres — batch chạy ALTER thẳng trên
    # Postgres, không chép bảng). Cùng khuôn `b2c3d4e5f6a7_resolution_
    # created_by.py` đã dùng cho đúng tình huống này.
    with op.batch_alter_table('tickets') as batch:
        batch.create_foreign_key('fk_tickets_claimed_by', 'users', ['claimed_by'], ['user_id'])


def downgrade() -> None:
    with op.batch_alter_table('tickets') as batch:
        batch.drop_constraint('fk_tickets_claimed_by', type_='foreignkey')
    op.drop_column('tickets', 'claimed_at')
    op.drop_column('tickets', 'claimed_by')
