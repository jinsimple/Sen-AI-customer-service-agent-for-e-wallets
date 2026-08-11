"""human handoff flag + complaint type other

Revision ID: 956258b225f4
Revises: c251b8af7649
Create Date: 2026-08-11 15:13:09.389086

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '956258b225f4'
down_revision: Union[str, Sequence[str], None] = 'c251b8af7649'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_OLD_TYPE_CHECK = "type IN ('wrong_recipient','money_not_received','double_charge','refund')"
_NEW_TYPE_CHECK = "type IN ('wrong_recipient','money_not_received','double_charge','refund','other')"


def upgrade() -> None:
    """Upgrade schema."""
    # human_handoff_requested — server_default bắt buộc (không chỉ nullable=
    # False) vì bảng tickets đã có dữ liệu thật (demo DB hàng trăm ticket) —
    # thiếu default, ADD COLUMN NOT NULL trên bảng không rỗng sẽ lỗi ở SQLite.
    # batch mode (không phải add_column trần) vì autogenerate không tự sinh
    # server_default cho cột KHÔNG NULL — cùng lý do cần batch cho phần
    # CheckConstraint bên dưới (SQLite không ALTER CONSTRAINT trực tiếp).
    with op.batch_alter_table('tickets', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'human_handoff_requested', sa.Boolean(), nullable=False, server_default=sa.false()
            )
        )

    # 'other' (CTRL-001, 2026-08-11) — khách yêu cầu gặp người thật không
    # kèm mô tả khớp 1 trong 4 loại khiếu nại giao dịch cụ thể.
    with op.batch_alter_table('complaints', schema=None) as batch_op:
        batch_op.drop_constraint('ck_complaints_type', type_='check')
        batch_op.create_check_constraint('ck_complaints_type', _NEW_TYPE_CHECK)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('complaints', schema=None) as batch_op:
        batch_op.drop_constraint('ck_complaints_type', type_='check')
        batch_op.create_check_constraint('ck_complaints_type', _OLD_TYPE_CHECK)

    with op.batch_alter_table('tickets', schema=None) as batch_op:
        batch_op.drop_column('human_handoff_requested')
