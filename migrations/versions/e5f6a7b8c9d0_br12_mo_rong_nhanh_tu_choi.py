"""BR-12 mở rộng sang nhánh TỪ CHỐI (F-18, gộp vào ADR-020 trước khi ký)

Bản BR-12 đầu chỉ chặn `approved_by = created_by`. Nhánh từ chối bỏ ngỏ, nên
`rejected_by = created_by` vẫn ghi được: người tự đề xuất rồi tự từ chối chính
đề xuất của mình. Nghe như vô hại vì "từ chối thì có mất tiền đâu" — nhưng
ADR-019 quy định `reject_reason` có `la_tin_hieu_hoc`, tức lý do từ chối chảy
thẳng vào phễu chọn case cho bộ eval Phase 2. Một người tự dán nhãn "đề xuất
của tôi sai" cho chính mình là vòng tự khen/tự chê khép kín, và nó bơm tín hiệu
giả vào chính cái thước dùng để chấm cải tiến.

BIỂU THỨC DẠNG "C" — dài hơn hai dạng còn lại, cố ý:
    (created_by IS NULL) OR (
        (approved_by IS NULL OR approved_by != created_by) AND
        (rejected_by IS NULL OR rejected_by != created_by))
Security dựng bảng chân trị 6 ca: cả ba dạng đều ĐÚNG như nhau, không dạng nào
sai. Chọn C vì hai lý do vận hành, không phải vì đúng hơn:
  · dạng ngắn (`approved_by != created_by`) đúng nhờ logic BA TRỊ (NULL != x cho
    NULL, CHECK coi NULL là thoả). Đúng, nhưng người sau phải tự dựng lại lập
    luận đó mỗi lần đọc — và rất dễ "rút gọn" nhầm thành sai.
  · dạng `IS DISTINCT FROM` cần SQLite >= 3.39. Test chạy SQLite trên CI và trên
    máy người khác; không xác minh được phiên bản ở mọi nơi thì không gánh.
C chỉ dùng `IS NULL` và `!=` — hành xử giống hệt nhau ở mọi backend.

CHECK KHÔNG SỬA ĐƯỢC TẠI CHỖ: phải DROP rồi CREATE lại cùng tên.

An toàn: đo trước khi viết, 0 dòng có `created_by = rejected_by` (10/10 vẫn
`created_by IS NULL`), nên ràng buộc mới không vỡ trên dữ liệu hiện có.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None

_TEN = "ck_resolutions_maker_checker_br12"
_CU = "(created_by IS NULL) OR (approved_by != created_by)"
_MOI = (
    "(created_by IS NULL) OR ("
    "(approved_by IS NULL OR approved_by != created_by) AND "
    "(rejected_by IS NULL OR rejected_by != created_by))"
)


def _kiem_truoc_khi_ep(conn, cot: str) -> None:
    vi_pham = conn.execute(
        sa.text(
            f"SELECT count(*) FROM resolutions WHERE created_by IS NOT NULL AND {cot} = created_by"
        )
    ).scalar()
    if vi_pham:
        raise RuntimeError(
            f"BR-12: {vi_pham} resolution có {cot} = created_by. Phải xử lý từng ca "
            "(ai thật sự quyết định?) trước khi ép — KHÔNG sửa dữ liệu hàng loạt "
            "cho constraint chạy qua."
        )


def upgrade() -> None:
    conn = op.get_bind()
    _kiem_truoc_khi_ep(conn, "approved_by")
    _kiem_truoc_khi_ep(conn, "rejected_by")
    op.drop_constraint(_TEN, "resolutions", type_="check")
    op.create_check_constraint(_TEN, "resolutions", _MOI)


def downgrade() -> None:
    op.drop_constraint(_TEN, "resolutions", type_="check")
    op.create_check_constraint(_TEN, "resolutions", _CU)
