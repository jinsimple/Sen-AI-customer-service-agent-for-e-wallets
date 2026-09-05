"""notifications table (ADR-063 — chuông thông báo vé mới)

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-09-04

Fan-out: một hàng/người nhận (không phải một hàng gắn danh sách người nhận) —
`read_at` riêng từng người thì bảng phải tách hàng theo người từ đầu, không
gộp rồi lọc lúc đọc.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4d5e6f7a8b9'
down_revision: Union[str, Sequence[str], None] = 'b3c4d5e6f7a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_EVENT_TYPE_CHECK = "event_type IN ('ve_moi','cho_duyet','da_duyet','da_tu_choi')"


def upgrade() -> None:
    op.create_table(
        'notifications',
        sa.Column('notification_id', sa.String(), primary_key=True),
        sa.Column('recipient_user_id', sa.String(), sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('ticket_id', sa.String(), sa.ForeignKey('tickets.ticket_id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint(_EVENT_TYPE_CHECK, name='ck_notifications_event_type'),
    )
    # Truy vấn nóng nhất: "N thông báo chưa đọc của user X" — index kép đúng
    # thứ tự lọc (recipient trước, read_at sau) để không phải quét toàn bảng
    # theo người dùng tăng dần.
    op.create_index(
        'ix_notifications_recipient_unread',
        'notifications',
        ['recipient_user_id', 'read_at'],
    )


def downgrade() -> None:
    op.drop_index('ix_notifications_recipient_unread', table_name='notifications')
    op.drop_table('notifications')
