"""resolution approval otp challenge

Revision ID: e49e271bef7b
Revises: ed9ff56b8f7c
Create Date: 2026-08-12 21:17:36.846276

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e49e271bef7b'
down_revision: Union[str, Sequence[str], None] = 'ed9ff56b8f7c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # batch_alter_table — SQLite không hỗ trợ ALTER ADD CONSTRAINT trực tiếp
    # (auth_sessions có thể đã có dữ liệu OTP dev thật), cùng pattern đã dùng
    # ở migration 956258b225f4.
    with op.batch_alter_table('auth_sessions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('resolution_id', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('amount_snapshot', sa.Integer(), nullable=True))

    # FK riêng ở batch KHÁC — gộp chung với add_column ở trên gây
    # CircularDependencyError lúc alembic tự sắp lại thứ tự cột khi tạo bảng
    # mới (batch mode SQLite = copy-and-move), phát hiện thật lúc chạy
    # `alembic upgrade head` cục bộ.
    with op.batch_alter_table('auth_sessions', schema=None) as batch_op:
        batch_op.create_foreign_key(
            'fk_auth_sessions_resolution_id', 'resolutions', ['resolution_id'], ['resolution_id']
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('auth_sessions', schema=None) as batch_op:
        batch_op.drop_constraint('fk_auth_sessions_resolution_id', type_='foreignkey')

    with op.batch_alter_table('auth_sessions', schema=None) as batch_op:
        batch_op.drop_column('amount_snapshot')
        batch_op.drop_column('resolution_id')
