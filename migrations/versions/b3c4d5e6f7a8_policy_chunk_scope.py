"""policy_chunks scope column (ADR-061 nháp — Finding ①, lớp 1)

Revision ID: b3c4d5e6f7a8
Revises: a8b9c0d1e2f3
Create Date: 2026-09-03

Chỉ THÊM cột, nullable, CHECK constraint y hệt `ck_complaints_scope`
(`internal_wallet`/`from_bank`/`to_bank`/`unknown`). KHÔNG backfill ở đây —
backfill là bước riêng SAU khi BA review xong bản nháp auto-phân-loại (script
đo baseline/phân loại không thuộc phạm vi migration). Cột để NULL cho tới lúc
đó — `search_policy_text` CHƯA đọc cột này (code lọc theo scope land ở một
đợt sau, sau khi ADR-061 được duyệt chính thức), nên thêm cột không đổi hành
vi hệ thống hiện tại.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3c4d5e6f7a8'
down_revision: Union[str, Sequence[str], None] = 'a8b9c0d1e2f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SCOPE_CHECK = "scope IN ('internal_wallet','from_bank','to_bank','unknown')"


def upgrade() -> None:
    with op.batch_alter_table('policy_chunks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('scope', sa.String(), nullable=True))
        batch_op.create_check_constraint('ck_policy_chunks_scope', _SCOPE_CHECK)


def downgrade() -> None:
    with op.batch_alter_table('policy_chunks', schema=None) as batch_op:
        batch_op.drop_constraint('ck_policy_chunks_scope', type_='check')
        batch_op.drop_column('scope')
