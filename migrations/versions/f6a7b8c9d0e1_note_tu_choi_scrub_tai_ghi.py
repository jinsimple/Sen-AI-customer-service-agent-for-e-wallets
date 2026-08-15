"""resolutions.note + note_flagged — ghi chú từ chối, scrub tại điểm ghi (ADR-024)

`reject_reason='khac'` đã được tài liệu hoá từ ADR-019 là "BẮT BUỘC kèm ghi chú
tự do" nhưng chưa từng có cột nào chứa ghi chú đó. Đây là chỗ DUY NHẤT trong hệ
thống nơi văn bản tự do do NHÂN VIÊN gõ đi vào cùng bản ghi với dữ liệu kiểm
toán — sign-off TM-03 (`docs/security/review-phase01-ap-that.md`).

`note`: Text NULLABLE ở tầng cột (resolution chưa bị từ chối thì không có gì
để ghi — đúng mẫu `reject_reason`/`rejected_by`), CHECK ép có điều kiện đối
xứng `ck_resolutions_rejected_requires_reason_br11` (INV-14): bắt buộc CÓ NỘI
DUNG (sau strip khoảng trắng) khi `reject_reason = 'khac'`.

`note_flagged`: Boolean NOT NULL DEFAULT false — route set khi `note` khớp
tier-1/tier-2 injection (tái dùng `_phan_loai_tier`, Luật 18/ADR-023), cho
người duyệt ứng viên Phase 2 thấy ngay dấu hiệu mà không phải tự đọc ra ý đồ.

CHECK KHÔNG VIẾT ĐƯỢC BẰNG `sa.text` cho biểu thức TRIM trực tiếp trong mọi
backend SQLite/Postgres như nhau — dùng `length(trim(note)) > 0`, hàm có ở cả
hai (SQLite `trim`/`length` built-in, Postgres `trim`/`length` chuẩn SQL).

AN TOÀN — SỬA LẠI SAU KHI ĐO THẬT, KHÔNG PHẢI SUY LUẬN TĨNH: bản nháp đầu của
docstring này viết "0 resolution hiện có ở trạng thái rejected với
reject_reason='khac'" — ĐÓ LÀ SUY LUẬN TỪ CODE TĨNH, KHÔNG PHẢI ĐO. Chạy thật
trên DB dev lộ ra 1 dòng: `RES-3b3026227331`, `rejected_by = USR-SYS-UNKNOWN`.
Đây CHÍNH LÀ dòng đã được migration F-11/F-13 (c3d4e5f6a7b8) backfill sentinel
— nó là ca "rejected genuine nhưng người thật đã mất dấu vết", không phải residue
QA. Theo ĐÚNG tiền lệ migration đó đã đặt ra (`_SENTINEL_NAME = "[HỆ THỐNG]
không xác định — backfill ADR-019"`), backfill `note` cho ĐÚNG những dòng mang
sentinel này bằng một chuỗi TỰ KHAI RÕ nó là placeholder, không phải một câu
nghe như ghi chú thật — đó là ranh giới giữa "đánh dấu dữ liệu thiếu" (được
phép) và "bịa số liệu" (cấm, §2.3): bịa là viết ra cái NGHE CÓ VẺ THẬT, còn ở
đây chuỗi tự tố cáo chính nó không phải dữ liệu gốc.

`_kiem_truoc_khi_ep` chạy SAU backfill sentinel, vẫn giữ nguyên vai trò chặn:
nếu còn dòng KHÔNG mang sentinel mà thiếu note, đó là ca thật cần người xử lý
từng dòng — migration vẫn nổ RuntimeError, không tự động hoá nốt phần đó.

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "f6a7b8c9d0e1"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None

_TEN_CHECK = "ck_resolutions_note_bat_buoc_khi_khac"
_BIEU_THUC = "(reject_reason != 'khac') OR (note IS NOT NULL AND length(trim(note)) > 0)"

# Cùng sentinel identity với c3d4e5f6a7b8 (F-11/F-13) — KHÔNG định nghĩa lại,
# tái dùng đúng giá trị đã có trong bảng users để backfill nhất quán.
_SENTINEL_ID = "USR-SYS-UNKNOWN"
_NOTE_BACKFILL_SENTINEL = (
    "[HỆ THỐNG] không có ghi chú gốc — dòng này được migration c3d4e5f6a7b8 "
    "(F-11/F-13) backfill sentinel trước khi cột `note` tồn tại (ADR-024). "
    "KHÔNG phải ghi chú thật của supervisor đã từ chối."
)


def _backfill_sentinel(conn) -> None:
    ket_qua = conn.execute(
        sa.text(
            "UPDATE resolutions SET note = :note "
            "WHERE reject_reason = 'khac' AND rejected_by = :sentinel "
            "AND (note IS NULL OR length(trim(note)) = 0)"
        ),
        {"note": _NOTE_BACKFILL_SENTINEL, "sentinel": _SENTINEL_ID},
    )
    if ket_qua.rowcount:
        print(
            f"[f6a7b8c9d0e1] backfill note cho {ket_qua.rowcount} dòng sentinel "
            f"({_SENTINEL_ID}) — xem docstring migration để biết vì sao đây "
            "KHÔNG phải bịa số liệu."
        )


def _kiem_truoc_khi_ep(conn) -> None:
    vi_pham = conn.execute(
        sa.text(
            "SELECT count(*) FROM resolutions WHERE reject_reason = 'khac' "
            "AND (note IS NULL OR length(trim(note)) = 0)"
        )
    ).scalar()
    if vi_pham:
        raise RuntimeError(
            f"ADR-024: {vi_pham} resolution có reject_reason='khac' mà note rỗng, "
            f"và KHÔNG mang sentinel {_SENTINEL_ID} nên không được backfill tự "
            "động. Phải xử lý từng ca trước khi ép CHECK — KHÔNG bịa nội dung "
            "note hàng loạt cho constraint chạy qua (cấm bịa số liệu §2.3)."
        )


def upgrade() -> None:
    conn = op.get_bind()
    op.add_column("resolutions", sa.Column("note", sa.Text(), nullable=True))
    op.add_column(
        "resolutions",
        sa.Column("note_flagged", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    _backfill_sentinel(conn)
    _kiem_truoc_khi_ep(conn)
    op.create_check_constraint(_TEN_CHECK, "resolutions", _BIEU_THUC)


def downgrade() -> None:
    op.drop_constraint(_TEN_CHECK, "resolutions", type_="check")
    op.drop_column("resolutions", "note_flagged")
    op.drop_column("resolutions", "note")
