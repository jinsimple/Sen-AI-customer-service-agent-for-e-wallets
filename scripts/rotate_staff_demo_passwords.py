#!/usr/bin/env python3
"""Đổi mật khẩu cho 3 tài khoản NHÂN VIÊN demo (cskh/supervisor/partner_admin)
— KHÔNG đụng tài khoản customer.

Lý do tồn tại: `Demo@123` (SHARED_TEST_PASSWORD, `gen_dataset.py:49`) là hằng
số TRONG GIT — hợp lý cho 25 tài khoản khách phát cho người lạ test, nhưng
sai hoàn toàn cho tài khoản có quyền DUYỆT HOÀN TIỀN (supervisor) hay quản trị
kho chính sách (partner_admin). Trang `/dang-nhap-noi-bo` công khai + hiện số
điện thoại supervisor ⟹ ai biết `Demo@123` là vào được `/approve`.

Mật khẩu mới đọc từ biến môi trường `STAFF_DEMO_PASSWORD`, BẮT BUỘC, KHÔNG có
giá trị mặc định — đúng khuôn `JWT_SECRET_KEY`/`FIELD_ENCRYPTION_KEY` đã dùng
trong dự án. Script KHÔNG BAO GIỜ tự sinh mật khẩu và KHÔNG in nó ra bất cứ
đâu — không có nhánh nào trong code này khiến giá trị đó lọt vào log/git.

Tự sinh một giá trị mạnh (chạy được trên MỌI máy có Docker, không phụ thuộc
openssl/python cài sẵn):
    docker compose exec -T backend python -c "import secrets; print(secrets.token_urlsafe(24))"

Rồi export biến TRƯỚC khi chạy script này:
    export STAFF_DEMO_PASSWORD="<dán giá trị vừa sinh>"
    python scripts/rotate_staff_demo_passwords.py

⚠️ Lệnh sinh ở trên VẪN in giá trị ra terminal — không có nghĩa là "không in
ra đâu cả". Khác biệt thật: KHÔNG có nhánh code nào tự sinh/tự in, người chạy
CHỦ ĐỘNG gọi và biết mình đang cầm một bí mật. Sau khi dán vào biến: XOÁ dòng
lệnh sinh khỏi lịch sử terminal hoặc đóng cửa sổ đó — giá trị vừa in vẫn còn
trong scrollback.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from scripts.gen_dataset import _PASSWORD_HASHER
from src.db.models import User
from src.db.session import get_engine

BIEN_MOI_TRUONG = "STAFF_DEMO_PASSWORD"

# 🔴 CỐ Ý ghim CẢ số điện thoại LẪN role mong đợi — không chỉ lọc role trong
# truy vấn (điều kiện an toàn của PO), mà còn đối chiếu TỪNG tài khoản tìm
# được đúng role mong đợi trước khi ghi. Data drift (ai đó đổi role một trong
# ba số này) sẽ làm script DỪNG thay vì âm thầm đổi mật khẩu cho role khác.
VAI_MONG_DOI = {
    "0353000201": "cskh",
    "0905000205": "supervisor",
    "0900000001": "partner_admin",
}


def main() -> None:
    mat_khau_moi = os.environ.get(BIEN_MOI_TRUONG)
    if not mat_khau_moi:
        raise SystemExit(
            f"{BIEN_MOI_TRUONG} chưa đặt. Tự sinh một giá trị mạnh rồi export biến trước khi chạy:\n"
            '  docker compose exec -T backend python -c "import secrets; print(secrets.token_urlsafe(24))"\n'
            f"Dán kết quả vào biến {BIEN_MOI_TRUONG}. KHÔNG lưu giá trị đó vào file nào trong git."
        )

    print("🔴 Sắp đổi mật khẩu cho 3 tài khoản NHÂN VIÊN (cskh/supervisor/partner_admin).")
    print("   Mật khẩu mới KHÔNG được in ra ở đây.")
    print()

    engine = get_engine()
    factory = sessionmaker(bind=engine, future=True)
    session = factory()

    # Lọc role NGAY TRONG TRUY VẤN — không lọc bằng ý định. KHÔNG chạm
    # customer: 25 tài khoản demo sinh ra để phát cho người lạ, phải giữ
    # nguyên SHARED_TEST_PASSWORD.
    stmt = select(User).where(
        User.phone.in_(VAI_MONG_DOI.keys()),
        User.role.in_(("cskh", "supervisor", "partner_admin")),
    )
    tim_duoc = list(session.scalars(stmt))
    phone_tim_duoc = {u.phone for u in tim_duoc}
    thieu = set(VAI_MONG_DOI) - phone_tim_duoc
    if thieu:
        raise SystemExit(
            f"Không tìm thấy tài khoản (role đúng) cho số: {sorted(thieu)}. "
            "Dừng, không ghi gì — kiểm tra DB trước khi chạy lại."
        )

    for u in tim_duoc:
        vai_dung = VAI_MONG_DOI[u.phone]
        if u.role != vai_dung:
            raise SystemExit(
                f"{u.phone} có role='{u.role}', mong đợi '{vai_dung}'. "
                "Dừng, KHÔNG ghi gì — dữ liệu đã lệch so với giả định của script."
            )

    hash_moi = _PASSWORD_HASHER.hash(mat_khau_moi)
    for u in tim_duoc:
        u.password_hash = hash_moi
    session.commit()

    print(f"Đã đổi mật khẩu cho {len(tim_duoc)} tài khoản: {sorted(phone_tim_duoc)}")
    print()
    print("XOÁ dòng lệnh sinh mật khẩu khỏi lịch sử terminal, hoặc đóng cửa sổ đó —")
    print("giá trị vừa in ra lúc sinh vẫn còn trong scrollback.")


if __name__ == "__main__":
    main()
