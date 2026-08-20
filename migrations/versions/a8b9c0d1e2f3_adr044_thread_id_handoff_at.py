"""ADR-044: complaints.thread_id + tickets.handoff_at

CSKH đọc hội thoại bot↔khách của vé mình xử lý khi khách bàn giao gặp
người thật (PO thật 19/08, docs/DECISIONS.md ADR-044).

complaints.thread_id — NULLABLE VĨNH VIỄN, KHÔNG backfill. Không có cách
nào suy ngược thread nào sinh ra một complaint đã tạo TRƯỚC cột này tồn
tại (thread_id gắn theo PHIÊN ĐĂNG NHẬP `f"{user_id}:{iat}"`, không phải
theo user — một user đăng nhập nhiều lần = nhiều thread, không đoán được
thread nào đúng). Đoán theo mốc thời gian gần nhất là heuristic đội lốt
sự thật — route transcript phải trả `transcript: null` kèm lý do cho các
complaint cũ, TUYỆT ĐỐI không suy đoán. Không FK: đây là định danh phiên
LangGraph checkpointer, không phải khoá ngoại tới bảng nào trong DB.

tickets.handoff_at — NULLABLE, ghi lúc `flag_human_handoff()` chạy. Đặt ở
Ticket chứ không Complaint: một complaint có thể sinh nhiều ticket, bàn
giao gắn với MỘT ticket cụ thể. `[ĐO]` hàm `flag_human_handoff()` hiện
CHỈ set `human_handoff_requested=True` + `updated_at` — CHƯA ghi mốc bàn
giao; cột này đứng NULL cho tới khi code (§10 bước ③) nối vào.

Revision ID: a8b9c0d1e2f3
Revises: a7b8c9d0e1f2
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "a8b9c0d1e2f3"
down_revision = "a7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("complaints", sa.Column("thread_id", sa.String(), nullable=True))
    op.add_column("tickets", sa.Column("handoff_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("tickets", "handoff_at")
    op.drop_column("complaints", "thread_id")
