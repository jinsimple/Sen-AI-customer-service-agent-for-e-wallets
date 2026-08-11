"""scope unknown fallback

Revision ID: 59fa55b72a23
Revises: 956258b225f4
Create Date: 2026-08-11 16:51:48.102189

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '59fa55b72a23'
down_revision: Union[str, Sequence[str], None] = '956258b225f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_OLD_SCOPE_CHECK = "scope IN ('internal_wallet','from_bank','to_bank')"
_NEW_SCOPE_CHECK = "scope IN ('internal_wallet','from_bank','to_bank','unknown')"


def upgrade() -> None:
    with op.batch_alter_table('complaints', schema=None) as batch_op:
        batch_op.drop_constraint('ck_complaints_scope', type_='check')
        batch_op.create_check_constraint('ck_complaints_scope', _NEW_SCOPE_CHECK)


def downgrade() -> None:
    with op.batch_alter_table('complaints', schema=None) as batch_op:
        batch_op.drop_constraint('ck_complaints_scope', type_='check')
        batch_op.create_check_constraint('ck_complaints_scope', _OLD_SCOPE_CHECK)
