"""F-11 + F-13: xoá residue QA → sentinel → backfill hitl_status

BA VIỆC NÀY KHÔNG GIAO HOÁN. Thứ tự dưới đây là điều kiện nghiệm thu số 1 của
tiền-kiểm bảo mật (docs/security/pre-review-nhip-migration-note-f11-f13.md §1),
không phải sở thích trình bày:

  1. XOÁ 2 resolution residue QA (F-11)
  2. Tạo sentinel + gán cho dòng rejected genuine còn lại
  3. BACKFILL tickets.hitl_status (F-13)

Nếu đảo 3 trước 1: `TCK-518527ab869f` được set `hitl_status='rejected'` rồi cả
hai resolution chống đỡ cho nó bị xoá ⟹ ticket khẳng định một phán quyết HITL
mà KHÔNG CÒN bản ghi nào chứng minh. Đó là dữ liệu kiểm toán bịa đúng nghĩa, và
trái `dan_xuat.quy_tac` của contract v2.1.0 ("ticket chưa có resolution nào vẫn
là pending"). Làm đúng thứ tự thì sau bước 1 ticket đó còn 0 resolution, bước 3
tự bỏ qua nó và nó giữ `pending` — đúng contract, không cần ngoại lệ tay.

Cả ba nằm trong CÙNG MỘT transaction (alembic trên Postgres bọc sẵn): hỏng nửa
chừng thì rollback trọn, không để lại trạng thái lai.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
"""
from __future__ import annotations

import datetime as dt

import sqlalchemy as sa
from alembic import op

revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None

# 2 dòng residue do phiên QA/QC sinh ra khi thử luồng từ chối, PO ra lệnh xoá.
_RESIDUE = ("RES-663769e6d9dc", "RES-b9b1f9344dc6")

# Sentinel — KHÔNG phải người. Bốn lựa chọn dưới đây đều là điều kiện nghiệm thu
# ở §4 của tiền-kiểm, ghi ngay tại đây để người đọc sau không phải đi tìm:
#
# * `user_id` bắt đầu bằng "USR-SYS-": trong ASCII 'S'(83) > '0'(48), nên
#   'USR-0205' < 'USR-SYS-UNKNOWN'. Câu SQL từng GÂY RA F-11
#   (`SELECT user_id FROM users WHERE role='supervisor' ORDER BY user_id LIMIT 1`,
#   nằm ở migration a1b2c3d4e5f6) vì thế vẫn vớ đúng supervisor thật, không vớ
#   sentinel. Đã kiểm bằng truy vấn thật trên DB hiện tại, không chỉ suy luận
#   từ bảng mã.
# * `role='supervisor'`: chọn có cân nhắc, không phải mặc định. `rejected_by`
#   nghĩa là "sếp nào đã từ chối", gán một `customer` vào đó tạo ra bản ghi kiểm
#   toán vô nghĩa cho người đọc sau. Điều kiện kèm theo của tiền-kiểm là phải
#   chỉ ra mọi chỗ liệt kê supervisor đã loại trừ nó — đã rà: src/ KHÔNG có truy
#   vấn nào chọn user theo role (chỉ có `_STAFF_ROLES` xét role của người ĐANG
#   đăng nhập, và ESCALATION_TARGET là hằng chuỗi, không phải tra bảng users).
#   Rủi ro còn lại là code TƯƠNG LAI liệt kê supervisor — nhãn `full_name` và
#   tiền tố id được chọn để lộ ngay khi điều đó xảy ra.
# * `password_hash=NULL`: đường login (`main.py`) chỉ cho qua khi
#   `user.password_hash is not None`, nên NULL = không đăng nhập được. Nghiệm
#   thu bằng gọi thật POST /auth/login, không bằng đọc code.
# * `phone` KHÔNG phải chuỗi số: cột này UNIQUE NOT NULL nên buộc phải có giá
#   trị. Đặt một chuỗi không thể là số điện thoại vừa tránh đụng dữ liệu thật,
#   vừa khiến `lookup_transaction` (tra user theo phone) không có đường chạm tới.
_SENTINEL_ID = "USR-SYS-UNKNOWN"
_SENTINEL_NAME = "[HỆ THỐNG] không xác định — backfill ADR-019"
_SENTINEL_PHONE = "SENTINEL-ADR019-KHONG-DANG-NHAP-DUOC"

# Ghi chú phải khai ĐỦ BA thứ bị suy ra, không chỉ lý do (điều kiện §4.5). Bản
# ghi chú cũ chỉ nói "lý do không được ghi lại" — người đọc sẽ tưởng người và
# thời điểm là thật, trong khi `rejected_at` đang bằng đúng `created_at` tức là
# cũng suy ra. Dọn được nửa vấn đề còn nguy hiểm hơn không dọn: nó tạo cảm giác
# dữ liệu đã sạch.
# Dấu hiệu nhận biết dòng do migration a1b2c3d4e5f6 backfill. PHẢI copy đúng
# từng ký tự từ `_GHI_CHU_BACKFILL` của migration đó — bản nháp của tôi viết
# '%[BACKFILL ADR-019]%' theo trí nhớ, không khớp chuỗi thật, nên câu UPDATE sẽ
# lặng lẽ sửa 0 dòng và migration vẫn "thành công". Không có gì báo lỗi.
_DAU_HIEU_BACKFILL_CU = " [dữ liệu trước ADR-019: lý do từ chối không được ghi lại]"

_GHI_CHU = (
    "\n\n[BACKFILL ADR-019 / F-11] Bản ghi này có TRƯỚC khi hệ thống bắt buộc "
    "ghi lý do từ chối. BA thông tin sau là SUY RA, không phải dữ liệu thật: "
    "(1) lý do từ chối — không được ghi lại ở thời điểm đó; "
    "(2) người từ chối — gán cho tài khoản hệ thống "
    f"{_SENTINEL_ID}, KHÔNG phải người thật nào; "
    "(3) thời điểm từ chối — suy ra bằng created_at của chính bản ghi. "
    "Không dùng bản ghi này làm bằng chứng về người hay thời điểm."
)


def upgrade() -> None:
    conn = op.get_bind()

    # --- BƯỚC 1: xoá residue (F-11) -------------------------------------
    # Xoá tham chiếu FK trước dù đã kiểm là 0 dòng: giữa lúc viết migration và
    # lúc nó chạy trên máy khác, một challenge duyệt mới có thể đã sinh ra.
    # Migration phải đúng theo dữ liệu LÚC CHẠY, không theo ảnh chụp lúc viết.
    conn.execute(
        # F-MIG — `expanding=True` BẮT BUỘC cho `IN :ids`. Không có nó,
        # SQLAlchemy đẩy nguyên tuple thành MỘT tham số: psycopg2 tình cờ adapt
        # tuple thành `(a,b)` nên Postgres chạy được, còn SQLite nổ
        # `near "?": syntax error`. Đây là lý do migration này chưa từng chạy
        # trên SQLite — nó phụ thuộc một hành vi riêng của driver Postgres.
        sa.text(
            "UPDATE auth_sessions SET resolution_id = NULL WHERE resolution_id IN :ids"
        ).bindparams(sa.bindparam("ids", expanding=True)),
        {"ids": list(_RESIDUE)},
    )
    da_xoa = conn.execute(
        sa.text("DELETE FROM resolutions WHERE resolution_id IN :ids").bindparams(
            sa.bindparam("ids", expanding=True)
        ),
        {"ids": list(_RESIDUE)},
    ).rowcount
    if da_xoa not in (0, len(_RESIDUE)):
        # 0 = đã chạy rồi / DB sạch (chấp nhận). Xoá NỬA VỜI thì dừng hẳn: nó
        # nghĩa là dữ liệu không như giả định của cả nhịp này.
        raise RuntimeError(f"F-11: chờ xoá 0 hoặc {len(_RESIDUE)} dòng, thực tế {da_xoa}")

    # --- BƯỚC 2: sentinel + gán cho dòng genuine ------------------------
    # F-MIG — KIỂM-RỒI-CHÈN thay cho `ON CONFLICT ... DO NOTHING`. Cú pháp
    # upsert khác nhau giữa các backend (Postgres `ON CONFLICT`, SQLite cần
    # phiên bản đủ mới / `INSERT OR IGNORE`, MySQL `ON DUPLICATE KEY`) — một
    # migration phải chạy được trên MỌI backend dự án dùng, kể cả SQLite của
    # môi trường test. Đây là chèn MỘT dòng sentinel, không có đua ghi, nên
    # kiểm-rồi-chèn tương đương về ngữ nghĩa và trung lập về phương ngữ.
    da_co = conn.execute(
        sa.text("SELECT 1 FROM users WHERE user_id = :id"), {"id": _SENTINEL_ID}
    ).scalar()
    if not da_co:
        conn.execute(
            sa.text(
                """
                INSERT INTO users (user_id, role, full_name, phone, kyc_level, created_at)
                VALUES (:id, 'supervisor', :ten, :phone, 0, :now)
                """
            ),
            {
                "id": _SENTINEL_ID,
                "ten": _SENTINEL_NAME,
                "phone": _SENTINEL_PHONE,
                "now": dt.datetime.utcnow(),
            },
        )
    # CHỈ những dòng đang mang ghi chú backfill cũ — không quét bừa mọi dòng
    # rejected. Dòng do người thật từ chối sau này phải giữ nguyên `rejected_by`.
    conn.execute(
        sa.text(
            """
            UPDATE resolutions
               SET rejected_by = :sentinel,
                   rationale   = rationale || :ghi_chu
             WHERE status = 'rejected'
               AND rationale LIKE :dau_hieu_cu
               AND rejected_by <> :sentinel
            """
        ),
        {"sentinel": _SENTINEL_ID, "ghi_chu": _GHI_CHU, "dau_hieu_cu": f"%{_DAU_HIEU_BACKFILL_CU}%"},
    )

    # --- BƯỚC 3: backfill hitl_status (F-13) ----------------------------
    # DISTINCT ON ... ORDER BY created_at DESC, resolution_id DESC — CỐ Ý khớp
    # từng chữ với `_dong_bo_hitl_status()` ở runtime (src/api/main.py). Câu
    # `JOIN resolutions WHERE status IN (...)` đơn giản hơn nhưng KHÔNG XÁC ĐỊNH
    # khi một ticket có nhiều resolution khác trạng thái — và ticket nhiều
    # resolution đã tồn tại thật (TCK-173cee0218a0 có 2). Hôm nay cả hai cùng
    # `approved` nên chưa lộ; để nguyên thì dữ liệu lịch sử và dữ liệu mới chạy
    # theo hai luật khác nhau, và sai lệch sẽ xuất hiện im lặng.
    conn.execute(
        sa.text(
            """
            -- F-MIG — VIẾT LẠI TRUNG LẬP PHƯƠNG NGỮ. Bản cũ dùng
            -- `SELECT DISTINCT ON (...)` + `UPDATE tickets t ... FROM ...`:
            -- cả hai là cú pháp RIÊNG của Postgres, SQLite nổ `near "ON"`.
            -- Đây là lý do thứ hai (sau bind param mở rộng) khiến migration
            -- từng chạy trên SQLite — nó được viết cho đúng một backend.
            -- ROW_NUMBER() + subquery tương quan chạy trên CẢ HAI, ngữ nghĩa
            -- giữ nguyên: lấy resolution MỚI NHẤT của mỗi ticket, chỉ cập
            -- nhật khi trạng thái là approved/rejected VÀ đang lệch.
            WITH moi_nhat AS (
                SELECT ticket_id, status FROM (
                    SELECT ticket_id, status,
                           ROW_NUMBER() OVER (
                               PARTITION BY ticket_id
                               ORDER BY created_at DESC, resolution_id DESC
                           ) AS rn
                      FROM resolutions
                ) x WHERE rn = 1
            )
            UPDATE tickets
               SET hitl_status = (
                       SELECT m.status FROM moi_nhat m
                        WHERE m.ticket_id = tickets.ticket_id
                   )
             WHERE EXISTS (
                       SELECT 1 FROM moi_nhat m
                        WHERE m.ticket_id = tickets.ticket_id
                          AND m.status IN ('approved', 'rejected')
                          AND tickets.hitl_status <> m.status
                   )
            """
        )
    )

    # --- Tự kiểm ngay trong transaction --------------------------------
    # Sai thì rollback trọn, không để lại DB nửa vời rồi mới phát hiện lúc test.
    con_lech = conn.execute(
        sa.text(
            """
            -- F-MIG — cùng lý do khối trên: DISTINCT ON là cú pháp riêng
            -- Postgres. ROW_NUMBER() chạy cả hai, ngữ nghĩa giữ nguyên.
            WITH moi_nhat AS (
                SELECT ticket_id, status FROM (
                    SELECT ticket_id, status,
                           ROW_NUMBER() OVER (
                               PARTITION BY ticket_id
                               ORDER BY created_at DESC, resolution_id DESC
                           ) AS rn
                      FROM resolutions
                ) x WHERE rn = 1
            )
            SELECT count(*) FROM tickets t JOIN moi_nhat m
                   ON m.ticket_id = t.ticket_id
             WHERE m.status IN ('approved','rejected') AND t.hitl_status <> m.status
            """
        )
    ).scalar()
    if con_lech:
        raise RuntimeError(f"F-13: còn {con_lech} ticket lệch sau backfill")

    mo_coi = conn.execute(
        sa.text(
            "SELECT count(*) FROM resolutions WHERE status='rejected' AND rejected_by IS NULL"
        )
    ).scalar()
    if mo_coi:
        raise RuntimeError(f"F-11: còn {mo_coi} dòng rejected không có người từ chối")


def downgrade() -> None:
    # Downgrade CỐ Ý KHÔNG ĐỐI XỨNG, và đây là lý do — không phải lười:
    #
    # * KHÔNG dựng lại 2 dòng residue đã xoá. Đó là rác do phiên QA sinh ra;
    #   "khôi phục" chúng là bịa lại dữ liệu kiểm toán, đúng thứ cả nhịp này
    #   đang dọn.
    # * KHÔNG gỡ sentinel, KHÔNG set `rejected_by = NULL`. Bản nháp của tôi làm
    #   đúng hai việc đó và nó SẼ NỔ: CHECK
    #   `ck_resolutions_rejected_requires_reason_br11` cấm `rejected_by IS NULL`
    #   khi status='rejected'. Muốn gỡ sentinel thì phải gán một người thật vào
    #   chỗ đó — tức là quay lại đúng lỗi F-11. Nên downgrade để nguyên: một
    #   dòng users vô hại, không đăng nhập được, đọc ra là nhãn hệ thống.
    #
    # Chỉ trả `hitl_status` về `pending`. Ở đây `pending` cũng chính là trạng
    # thái trước nhịp này (đã kiểm: mọi ticket lệch đều đang `pending`), nên
    # không mất thông tin nào.
    conn = op.get_bind()
    conn.execute(
        sa.text("UPDATE tickets SET hitl_status='pending' WHERE hitl_status IN ('approved','rejected')")
    )
