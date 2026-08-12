"""live chat sessions

Revision ID: ed9ff56b8f7c
Revises: 59fa55b72a23
Create Date: 2026-08-11 20:29:57.688562

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from src.db.crypto_types import EncryptedText

# revision identifiers, used by Alembic.
revision: str = 'ed9ff56b8f7c'
down_revision: Union[str, Sequence[str], None] = '59fa55b72a23'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'chat_sessions',
        sa.Column('chat_session_id', sa.String(), nullable=False),
        sa.Column('ticket_id', sa.String(), nullable=False),
        sa.Column('customer_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('claimed_by', sa.String(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('claimed_at', sa.DateTime(), nullable=True),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.Column('csat_score', sa.Integer(), nullable=True),
        sa.Column('csat_submitted_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint("status IN ('waiting','active','closed')", name='ck_chat_sessions_status'),
        sa.CheckConstraint('csat_score IS NULL OR csat_score BETWEEN 1 AND 5', name='ck_chat_sessions_csat_score'),
        sa.ForeignKeyConstraint(['ticket_id'], ['tickets.ticket_id']),
        sa.ForeignKeyConstraint(['customer_id'], ['users.user_id']),
        sa.ForeignKeyConstraint(['claimed_by'], ['users.user_id']),
        sa.PrimaryKeyConstraint('chat_session_id'),
    )

    # messages chưa từng dùng thật (0 dòng dữ liệu, xác nhận qua grep toàn bộ
    # src/ trước khi viết migration này) — session_id trước đó FK sai đối
    # tượng (auth_sessions = phiên ĐĂNG NHẬP, không phải phiên CHAT). Vì bảng
    # trống, drop/create lại an toàn hơn batch_alter_table (không có dữ liệu
    # cần giữ, khác 2 migration trước đó phải dùng batch vì bảng CÓ dữ liệu
    # thật). content đổi sang EncryptedText (mã hoá at-rest, cùng khoá/kiểu
    # với PolicyChunk.text — src/db/crypto_types.py).
    op.drop_table('messages')
    op.create_table(
        'messages',
        sa.Column('message_id', sa.String(), nullable=False),
        sa.Column('chat_session_id', sa.String(), nullable=False),
        sa.Column('ticket_id', sa.String(), nullable=True),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('content', EncryptedText(), nullable=False),
        sa.Column('tool_call_ids', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint("role IN ('customer','agent','staff','system')", name='ck_messages_role'),
        sa.ForeignKeyConstraint(['chat_session_id'], ['chat_sessions.chat_session_id']),
        sa.ForeignKeyConstraint(['ticket_id'], ['tickets.ticket_id']),
        sa.PrimaryKeyConstraint('message_id'),
    )


def downgrade() -> None:
    op.drop_table('messages')
    op.create_table(
        'messages',
        sa.Column('message_id', sa.String(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('ticket_id', sa.String(), nullable=True),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('tool_call_ids', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint("role IN ('customer','agent','staff','system')", name='ck_messages_role'),
        sa.ForeignKeyConstraint(['session_id'], ['auth_sessions.session_id']),
        sa.ForeignKeyConstraint(['ticket_id'], ['tickets.ticket_id']),
        sa.PrimaryKeyConstraint('message_id'),
    )
    op.drop_table('chat_sessions')
