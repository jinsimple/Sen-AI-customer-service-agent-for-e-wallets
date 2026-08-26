#!/usr/bin/env python3
"""Đặt mật khẩu demo cho N tài khoản `customer` ĐÃ TỒN TẠI — để nhiều người
test cùng lúc, mỗi người một tài khoản riêng (tránh chung tài khoản, thấy vé
của nhau).

KHÔNG sinh user mới, KHÔNG đổi dữ liệu (`user_id`/`phone`/`kyc_level`...) —
chỉ backfill `password_hash`. Cùng khuôn với
`seed_demo_scenarios.py:110-131` (đã làm việc này cho 1 `partner_admin`),
lặp lại cho N `customer`.

Chạy:
    python scripts/seed_demo_customer_passwords.py [N mặc định 25]

Idempotent: chạy lại nhiều lần, cùng N -> cùng N tài khoản (chọn tất định
theo `user_id` tăng dần), không lỗi trùng khoá. Tăng N ở lần sau -> giữ
nguyên nhóm cũ, thêm đúng phần chênh lệch.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from scripts.gen_dataset import _PASSWORD_HASHER, SHARED_TEST_PASSWORD, TEST_ACCOUNT_USER_IDS
from src.db.models import User
from src.db.session import get_engine

CANH_BAO = (
    "🔴 CẢNH BÁO: các tài khoản này có mật khẩu CÔNG KHAI BIẾT ĐƯỢC "
    f"(\"{SHARED_TEST_PASSWORD}\"). CHỈ dùng cho demo. "
    "KHÔNG chạy script này trên hệ thống có dữ liệu khách hàng thật."
)


def main() -> None:
    n = 25
    if len(sys.argv) > 1:
        n = int(sys.argv[1])

    print(CANH_BAO)
    print()

    engine = get_engine()
    factory = sessionmaker(bind=engine, future=True)
    session = factory()

    # 🔴 Lọc role NGAY TRONG CÂU TRUY VẤN — không lọc bằng ý định. Một tài
    # khoản cskh/supervisor/partner_admin mang mật khẩu công khai trên hệ
    # thống sắp công khai là phát chìa khoá két (supervisor duyệt hoàn tiền).
    # Loại trừ 4 tài khoản demo hiện có (TEST_ACCOUNT_USER_IDS,
    # gen_dataset.py) — chúng đang được dùng test, đổi là gãy.
    stmt = (
        select(User)
        .where(User.role == "customer", User.user_id.not_in(TEST_ACCOUNT_USER_IDS))
        .order_by(User.user_id.asc())
        .limit(n)
    )
    khach = list(session.scalars(stmt))

    if not khach:
        raise SystemExit("Không tìm thấy tài khoản role=customer nào trong DB — chạy `make db` trước.")

    hash_dung_chung = _PASSWORD_HASHER.hash(SHARED_TEST_PASSWORD)
    for u in khach:
        u.password_hash = hash_dung_chung
    session.commit()

    print(f"Đã đặt mật khẩu demo cho {len(khach)} tài khoản customer (yêu cầu N={n}):")
    for u in khach:
        print(f"  {u.user_id}  {u.phone}")
    print()
    print(f"Mật khẩu chung: {SHARED_TEST_PASSWORD}")
    print()
    print(CANH_BAO)


if __name__ == "__main__":
    main()
