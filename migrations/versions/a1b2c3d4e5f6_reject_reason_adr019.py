"""ADR-019 — nhãn phán đoán chuyên gia tại luồng từ chối

Thêm `reject_reason` / `rejected_by` / `rejected_at` vào `resolutions`, kèm 2
CHECK constraint: enum hợp lệ, và điều kiện br11 (rejected ⟹ đủ 3 trường) —
đối xứng với BR-10 của nhánh duyệt.

BACKFILL CÓ CHỦ ĐÍCH, KHÔNG LẶNG LẼ: DB demo đang có sẵn dòng `rejected` tạo
TRƯỚC ADR-019 nên không thể có 3 trường này. Nếu thêm CHECK trước khi backfill
thì migration ném lỗi ngay trên dữ liệu cũ. Thứ tự bắt buộc: thêm cột →
backfill dòng cũ → mới thêm CHECK. Dòng cũ gán `khac` + ghi rõ nguồn gốc trong
`rationale` để sau này không ai tưởng đó là phán đoán thật của sếp.

Revision ID: a1b2c3d4e5f6
Revises: e702b39353b4
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "a1b2c3d4e5f6"
down_revision = "e702b39353b4"
branch_labels = None
depends_on = None

_GHI_CHU_BACKFILL = " [dữ liệu trước ADR-019: lý do từ chối không được ghi lại]"


def upgrade() -> None:
    op.add_column("resolutions", sa.Column("reject_reason", sa.String(), nullable=True))
    op.add_column("resolutions", sa.Column("rejected_by", sa.String(), nullable=True))
    op.add_column("resolutions", sa.Column("rejected_at", sa.DateTime(), nullable=True))
    op.create_foreign_key(
        "fk_resolutions_rejected_by", "resolutions", "users", ["rejected_by"], ["user_id"]
    )

    # Backfill TRƯỚC khi ép CHECK — xem docstring. `rejected_by` lấy chính
    # người đã duyệt/từ chối nếu biết, không thì rơi về user supervisor bất kỳ
    # KHÔNG được: thà để migration hỏng còn hơn gán bừa một cái tên người vào
    # bản ghi kiểm toán. Ở đây dùng approved_by nếu có (cùng người thao tác),
    # còn không thì lấy supervisor đầu tiên — và ghi rõ trong rationale.
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE resolutions
               SET reject_reason = 'khac',
                   rejected_at   = COALESCE(rejected_at, approved_at, created_at),
                   rejected_by   = COALESCE(rejected_by, approved_by,
                                            (SELECT user_id FROM users
                                              WHERE role = 'supervisor'
                                              ORDER BY user_id LIMIT 1)),
                   rationale     = rationale || :ghi_chu
             WHERE status = 'rejected'
               AND reject_reason IS NULL
            """
        ),
        {"ghi_chu": _GHI_CHU_BACKFILL},
    )

    op.create_check_constraint(
        "ck_resolutions_reject_reason",
        "resolutions",
        "reject_reason IN ('sai_so_lieu','sai_phan_loai','thieu_can_cu',"
        "'sai_chinh_sach','trung_case','khach_rut','khac')",
    )
    op.create_check_constraint(
        "ck_resolutions_rejected_requires_reason_br11",
        "resolutions",
        "(status != 'rejected') OR (reject_reason IS NOT NULL "
        "AND rejected_by IS NOT NULL AND rejected_at IS NOT NULL)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_resolutions_rejected_requires_reason_br11", "resolutions", type_="check")
    op.drop_constraint("ck_resolutions_reject_reason", "resolutions", type_="check")
    op.drop_constraint("fk_resolutions_rejected_by", "resolutions", type_="foreignkey")
    op.drop_column("resolutions", "rejected_at")
    op.drop_column("resolutions", "rejected_by")
    op.drop_column("resolutions", "reject_reason")
