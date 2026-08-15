"""Chuẩn bị maker–checker: resolutions.created_by

Thêm cột ghi AI ĐỀ XUẤT resolution, để đợt ADR-020 ép được
`approved_by != created_by` (một người vừa đề xuất vừa tự duyệt là mất toàn bộ
ý nghĩa của HITL).

NULLABLE VĨNH VIỄN, KHÔNG backfill: resolution tạo trước cột này không có cách
nào biết ai đề xuất. Đoán một cái tên vào bản ghi kiểm toán còn tệ hơn để
trống — dữ liệu sai trong sổ kiểm toán nguy hiểm hơn dữ liệu thiếu, vì nó
được tin tưởng. CHECK maker–checker của ADR-020 sau này PHẢI viết dạng có điều
kiện (`created_by IS NULL OR approved_by != created_by`) để không vỡ trên các
dòng cũ đó.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("resolutions", sa.Column("created_by", sa.String(), nullable=True))
    # F-MIG — batch_alter_table: SQLite không ALTER được constraint.
    # Trên Postgres batch chạy ALTER thẳng, không chép bảng.
    with op.batch_alter_table("resolutions") as batch:
        batch.create_foreign_key("fk_resolutions_created_by", "users", ["created_by"], ["user_id"])


def downgrade() -> None:
    with op.batch_alter_table("resolutions") as batch:
        batch.drop_constraint("fk_resolutions_created_by", type_="foreignkey")
    op.drop_column("resolutions", "created_by")
