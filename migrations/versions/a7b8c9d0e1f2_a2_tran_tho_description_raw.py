"""A2 — lưới chặn cuối trên `complaints.description_raw` (ADR-025 QĐ 5)

CON SỐ 12.000 Ở ĐÂY KHÔNG PHẢI TRẦN NGHIỆP VỤ. Đọc kỹ trước khi "sửa cho khớp
2.000" — nó sẽ chặn nhầm khách thật.

Trần nghiệp vụ = **2.000 KÝ TỰ**, ép ở hai chỗ khác:
  · `src/services/complaint_intake.MAX_DESCRIPTION_CHARS` — điểm HỘI TỤ của cả
    đường REST (`main.py:538`) lẫn đường AGENT (`customer_tools.py:620`). Đây
    mới là lớp chính xác.
  · `src/api/schemas.CreateTicketRequest` — Pydantic `max_length=2000`, trả 422
    cho caller REST.
  (Đặt trần CHỈ ở schema là hụt đường agent: tool `create_ticket` không có
  `args_schema`, dùng type hint trần nên Pydantic không áp ràng buộc nào.)

VÌ SAO TẦNG DB KHÔNG DIỄN ĐẠT ĐƯỢC TRẦN THEO KÝ TỰ
--------------------------------------------------
`description_raw` là `EncryptedText` (A1, cùng đợt) nên `length()` đếm
CIPHERTEXT. Fernet nở theo BYTE utf-8, còn trần nghiệp vụ tính theo KÝ TỰ, mà
số byte mỗi ký tự thì thay đổi. Đo thật trên đúng 2.000 ký tự:

    ASCII thuần               2.764   (x1.38)
    tiếng Việt điển hình      3.596   (x1.80)
    tiếng Việt DÀY dấu        5.708   (x2.85)
    emoji 4 byte             10.764   (x5.38)

Tỉ lệ chạy từ x1.38 tới x5.38 trên CÙNG một độ dài ký tự ⟹ không tồn tại một
bound ciphertext nào tương đương 2.000 ký tự. Bound 4.000 (suy ra từ tỉ lệ
x1.90 đo ở 500 ký tự) CHẶN NHẦM hai ca cuối — đó là lý do con số ở đây là
12.000, và nó đến từ phép đo chứ không từ phép nhân.

CÁI GIÁ, ghi rõ để không ai tưởng lớp này chặt hơn thực tế: 12.000 ciphertext
≈ 8.700 ký tự ASCII vẫn lọt qua tầng DB. Lớp này CHỈ chặn thảm hoạ — flood
20.000 ký tự cho ~27.600 ciphertext, trượt CHECK. Độ chính xác nằm ở tầng
service.

Đây là chỗ nguyên tắc "ép ở TẦNG DB, không chỉ ở route" của ADR-024 KHÔNG
chuyển sang được nguyên vẹn: mã hoá at-rest và ràng buộc-theo-nội-dung kéo
ngược nhau. ADR-025 QĐ 5 chấp nhận đánh đổi đó một cách có ý thức thay vì bỏ
một trong hai.

AN TOÀN VỚI DỮ LIỆU CŨ: hàng plaintext ghi trước A1 có `length()` = số ký tự
thật, luôn nhỏ hơn ciphertext tương ứng ⟹ không hàng cũ nào vi phạm CHECK mới.
Đo trước khi phát biểu: xem phần kiểm ở `upgrade()`.

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-08-15
"""
from alembic import op
import sqlalchemy as sa

revision = "a7b8c9d0e1f2"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None

_TEN = "ck_complaints_description_raw_tran_tho"
_DIEU_KIEN = "length(description_raw) <= 12000"


def upgrade() -> None:
    # Đo TRƯỚC khi áp: hàng nào đang vi phạm thì CREATE CONSTRAINT sẽ nổ giữa
    # chừng ở Postgres. Fail sớm với thông điệp đọc được hơn là fail muộn với
    # lỗi driver.
    bind = op.get_bind()
    vi_pham = bind.execute(
        sa.text("SELECT count(*) FROM complaints WHERE length(description_raw) > 12000")
    ).scalar()
    if vi_pham:
        raise RuntimeError(
            f"{vi_pham} hàng complaints có description_raw vượt 12.000 ký tự "
            f"(đã tính ciphertext). Xử lý dữ liệu trước, KHÔNG nới bound để "
            f"migration chạy được — nới bound là bỏ luôn lớp chặn flood."
        )

    # batch_alter_table: SQLite không ADD CONSTRAINT được, alembic dựng bảng
    # mới rồi chép sang. Postgres đi đường ALTER thẳng.
    with op.batch_alter_table("complaints") as batch:
        batch.create_check_constraint(_TEN, _DIEU_KIEN)


def downgrade() -> None:
    with op.batch_alter_table("complaints") as batch:
        batch.drop_constraint(_TEN, type_="check")
