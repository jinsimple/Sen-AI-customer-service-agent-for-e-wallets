"""Backfill `complaints.description_raw` — mã hoá 738 dòng plaintext còn lại.

ADR-032 ② · 18/08/2026 · dự báo công bố trước tại
`scripts/DU-BAO-backfill-738-dong-2026-08-18.md`.

🔴 KHÔNG PHẢI MỘT ALEMBIC REVISION — CÓ CHỦ ĐÍCH
------------------------------------------------
[ĐO] `docker-entrypoint.sh:17` chạy `alembic upgrade head` **mỗi lần container
khởi động**, trên **cả ba ngăn xếp** VÀ trên **production** (`app.adaptivealgo.uk`,
nơi mọi phiên chỉ được CHỈ ĐỌC — STATE §1).

Làm việc này thành một revision nghĩa là: lần tới ai đó `docker compose up`,
**738 dòng lời khai của khách bị viết đè TỰ ĐỘNG** — không sao lưu, không ai
bấm nút, không ai đọc số trước/sau.

    Di trú LƯỢC ĐỒ nên tự động — hoàn nguyên được bằng `downgrade`.
    Di trú NỘI DUNG thì KHÔNG — bản gốc không còn ở đâu để lấy lại.

⟹ Đây là script **chạy bằng tay, một lần, sau khi đã sao lưu và đã KIỂM PHỤC
HỒI bản sao lưu đó**. Mặc định của nó là **KHÔNG GHI GÌ** (xem `--ghi`).

BA BẤT BIẾN — cái ① là cái sống còn
------------------------------------
**① IDEMPOTENT.** Chạy hai lần mà không chặn ⟹ `encrypt(encrypt(text))`. Giải
mã một lần cho ra **chuỗi bản mã**, đúng kiểu `str`, đúng chỗ — tức **chính xác
lỗi `crypto_types` vừa vá**, nhưng lần này **ta tự tay tạo ra** và **bản gốc đã
bị ghi đè**. Chặn bằng `_co_hinh_dang_fernet()` **của chính `crypto_types`** —
KHÔNG viết phép thứ hai: hai định nghĩa của cùng một vật sẽ lệch trong im lặng.

**② ĐỌC RAW, KHÔNG QUA ORM.** Đọc qua ORM là đã giải mã rồi ⟹ ta sẽ mã hoá lại
một thứ vừa được giải mã và **không nhìn thấy dòng nào đang ở trạng thái nào**.

**③ DÙNG LẠI `_fernet` CỦA `crypto_types`**, không dựng `Fernet()` mới. Lý do ①.

CÁCH DÙNG
---------
    # 1. XEM THỬ — mặc định, không ghi một byte nào
    docker exec fin05-backend-1 python /app/migrations/backfill_ma_hoa_description_raw.py

    # 2. GHI THẬT — chỉ sau khi đã sao lưu VÀ đã phục hồi thử bản sao lưu đó
    docker exec fin05-backend-1 python /app/migrations/backfill_ma_hoa_description_raw.py --ghi
"""
from __future__ import annotations

import argparse
import sys

from sqlalchemy import create_engine, text

from src.config import DATABASE_URL
from src.db.crypto_types import _co_hinh_dang_fernet, _fernet

BANG = "complaints"
COT = "description_raw"
KHOA = "complaint_id"


def dem(conn) -> dict[str, int]:
    """MỘT hàm đếm, gọi ở CẢ HAI đầu.

    🔴 Hai câu lệnh khác nhau cho hai đầu là **hai phép đo**, không phải một
    hiệu số — nên đầu trước và đầu sau bắt buộc đi qua đúng hàm này.

    Phân loại bằng `_co_hinh_dang_fernet` (cấu trúc token), KHÔNG bằng
    `LIKE 'gAAAAA%'` (trùng hợp của base64) — cùng phép mà `crypto_types` dùng
    lúc đọc, nên hai tầng không thể bất đồng về "dòng này đã mã hoá chưa".
    """
    ket = {"tong": 0, "da_ma_hoa": 0, "plaintext": 0}
    for (v,) in conn.execute(text(f"SELECT {COT} FROM {BANG}")):
        ket["tong"] += 1
        if v is None:
            continue
        if _co_hinh_dang_fernet(v):
            ket["da_ma_hoa"] += 1
        else:
            ket["plaintext"] += 1
    return ket


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--ghi",
        action="store_true",
        help="GHI THẬT vào DB. Không có cờ này thì chỉ xem thử, không ghi một byte nào.",
    )
    args = p.parse_args()

    eng = create_engine(DATABASE_URL)
    with eng.begin() as conn:
        truoc = dem(conn)
        print(f"MẪU SỐ ĐẦU   tổng {truoc['tong']} · đã mã hoá {truoc['da_ma_hoa']} "
              f"· plaintext {truoc['plaintext']}")

        if truoc["plaintext"] == 0:
            print("Không còn dòng plaintext nào — KHÔNG CÓ GÌ ĐỂ LÀM (idempotent).")
            return 0

        # Đọc RAW, phân loại, chỉ động vào dòng KHÔNG có hình dạng Fernet.
        can_sua: list[tuple[str, str]] = []
        for kh, v in conn.execute(text(f"SELECT {KHOA}, {COT} FROM {BANG}")):
            if v is None or _co_hinh_dang_fernet(v):
                continue
            can_sua.append((kh, _fernet.encrypt(v.encode()).decode()))

        print(f"SẼ ĐỘNG VÀO  {len(can_sua)} dòng")
        if len(can_sua) != truoc["plaintext"]:
            print(f"🔴 DỪNG: số dòng sẽ động vào ({len(can_sua)}) ≠ rổ plaintext "
                  f"({truoc['plaintext']}). Hai phép phân loại đã lệch nhau.", file=sys.stderr)
            return 3

        if not args.ghi:
            print("\n-- XEM THỬ, KHÔNG GHI GÌ. Thêm `--ghi` để chạy thật.")
            print("-- Trước khi `--ghi`: đã sao lưu chưa, và đã PHỤC HỒI THỬ bản sao lưu đó chưa?")
            return 0

        for kh, moi in can_sua:
            conn.execute(
                text(f"UPDATE {BANG} SET {COT} = :moi WHERE {KHOA} = :kh"),
                {"moi": moi, "kh": kh},
            )

        sau = dem(conn)
        print(f"MẪU SỐ SAU   tổng {sau['tong']} · đã mã hoá {sau['da_ma_hoa']} "
              f"· plaintext {sau['plaintext']}")

        # Ba phép kiểm TRONG CÙNG giao dịch — sai thì `raise` để rollback, chứ
        # không in cảnh báo rồi commit. Một script ghi dữ liệu mà chỉ CẢNH BÁO
        # khi phát hiện sai là một script đã ghi rồi mới nói.
        if sau["tong"] != truoc["tong"]:
            raise RuntimeError(
                f"số dòng đổi {truoc['tong']} -> {sau['tong']}: script đã THÊM hoặc XOÁ dòng"
            )
        if sau["plaintext"] != 0:
            raise RuntimeError(f"còn {sau['plaintext']} dòng plaintext sau khi chạy")
        if sau["da_ma_hoa"] != truoc["tong"]:
            raise RuntimeError(
                f"đã mã hoá {sau['da_ma_hoa']} ≠ tổng {truoc['tong']}"
            )

        print("\n⚠️ BA PHÉP KIỂM TRÊN CHỈ KIỂM HÌNH DẠNG, KHÔNG KIỂM NỘI DUNG.")
        print("   Một dòng mã hoá bằng KHOÁ SAI cũng cho `gAAAAA` và cũng làm chúng xanh.")
        print("   Phép kết luận duy nhất: giải mã lại và so TỪNG DÒNG với bản sao lưu.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
