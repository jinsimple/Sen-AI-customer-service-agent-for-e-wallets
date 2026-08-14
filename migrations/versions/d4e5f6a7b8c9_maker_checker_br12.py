"""BR-12 maker-checker: người đề xuất không được tự duyệt (ADR-020)

CHECK dạng CÓ ĐIỀU KIỆN — `created_by IS NULL OR approved_by != created_by`.
Vế NULL không phải nới lỏng cho dễ chạy: `created_by` nullable VĨNH VIỄN
(b2c3d4e5f6a7) vì resolution có trước cột đó không có cách nào biết ai đề xuất,
và đoán một cái tên vào sổ kiểm toán còn tệ hơn để trống. CHECK vô điều kiện sẽ
vỡ ngay trên chính các dòng ấy.

Không cần thêm vế cho resolution chưa duyệt: khi `approved_by` là NULL thì
`approved_by != created_by` cho NULL, và SQL coi CHECK cho ra NULL là THOẢ.

NÓI RÕ GIỚI HẠN, để không ai đọc sự tồn tại của constraint thành bằng chứng dữ
liệu cũ đã sạch: đo tại thời điểm viết, 10/10 resolution đều `created_by IS
NULL` ⟹ ràng buộc này hiện KHÔNG ràng dòng nào. Nó chỉ bắt đầu bảo vệ từ các
resolution tạo qua route mới (route đã truyền created_by lấy từ JWT, không lấy
từ body).

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None

_TEN = "ck_resolutions_maker_checker_br12"
_BIEU_THUC = "(created_by IS NULL) OR (approved_by != created_by)"


def upgrade() -> None:
    # Kiểm TRƯỚC khi ép: nếu có dòng vi phạm thì `create_check_constraint` sẽ
    # nổ với thông báo của Postgres, không nói được dòng nào. Dừng sớm với câu
    # đọc ra được vẫn hơn — cùng lý do đã dùng ở nhịp F-11/F-13.
    conn = op.get_bind()
    vi_pham = conn.execute(
        sa.text(
            "SELECT count(*) FROM resolutions "
            "WHERE created_by IS NOT NULL AND approved_by = created_by"
        )
    ).scalar()
    if vi_pham:
        raise RuntimeError(
            f"BR-12: {vi_pham} resolution đang có người đề xuất = người duyệt. "
            "Phải xử lý từng ca (ai thật sự duyệt?) trước khi ép ràng buộc — "
            "KHÔNG được sửa dữ liệu hàng loạt cho constraint chạy qua."
        )
    op.create_check_constraint(_TEN, "resolutions", _BIEU_THUC)


def downgrade() -> None:
    op.drop_constraint(_TEN, "resolutions", type_="check")
