#!/usr/bin/env python3
"""Tạo phiên ĐÃ XÁC THỰC OTP cho tài khoản HẠT GIỐNG — dùng cho bộ đo.

    python scripts/phien_do.py --sdt 0387000001
    python scripts/phien_do.py --sdt 0387000001 --ra token.txt

VÌ SAO TỒN TẠI: tester bắn lượt thật qua `/agent/chat` và `create_ticket`
KHÔNG BAO GIỜ chạy — cửa OTP chặn ngay ở `get_customer_history`, vì phiên tạo
qua `/api/session` chưa xác thực OTP. Chạy 20 lượt như thế là **đo cửa OTP**,
không phải đo hành vi điều tra. Và cả 20 lượt sẽ nhất quán, trông rất thuyết
phục — đúng hình dạng "đo trúng thứ khác rồi đọc thành thứ mình muốn".

Đây là thiếu NĂNG LỰC, không phải thiếu cố gắng: tester không tạo được phiên
đó từ vùng của họ.

═══ HAI ĐIỀU SCRIPT NÀY CỐ Ý KHÔNG LÀM ═══════════════════════════════════

**KHÔNG nới cửa OTP.** Không có cờ `SKIP_OTP`, không có nhánh môi trường, không
chạm `src/`. Nó đi ĐÚNG ba bước của sản phẩm:
    POST /auth/login  ->  POST /auth/otp/request  ->  POST /auth/otp/verify
Nếu đo bằng một đường KHÔNG TỒN TẠI trong sản phẩm thì ta lại đo một vật khác
— đúng lớp lỗi đã cắn năm lần trong ngày.

**KHÔNG tạo được token cho tài khoản người thật.** Guard ở đây là CẤU TRÚC chứ
không phải một câu lệnh kiểm: script chỉ biết `SHARED_TEST_PASSWORD` của bộ
sinh dữ liệu. Tài khoản thật có mật khẩu khác ⟹ `/auth/login` trả 401 và script
dừng. Không có đường nào để nới guard này mà không sửa chính file — khác hẳn
một cờ `--cho-phep-tai-khoan-that` mà ai đó sẽ bật lúc 2 giờ sáng.

Thêm một cổng nữa: từ chối chạy khi `APP_ENV=production`.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx  # noqa: E402

from src.config import APP_ENV  # noqa: E402

# Lấy TỪ bộ sinh dữ liệu, không gõ lại — gõ lại là tạo một nguồn sự thật thứ hai.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_dataset import SHARED_TEST_PASSWORD  # noqa: E402

API = "http://localhost:8010"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sdt", required=True, help="số điện thoại tài khoản hạt giống")
    ap.add_argument("--api", default=API)
    ap.add_argument("--ra", default=None, help="ghi token ra file thay vì stdout")
    a = ap.parse_args()

    if APP_ENV == "production":
        print("  TỪ CHỐI: APP_ENV=production. Script này chỉ dùng để đo.", file=sys.stderr)
        return 2

    c = httpx.Client(base_url=a.api, timeout=40)

    # ① đăng nhập — mật khẩu CHỈ tài khoản hạt giống mới khớp
    r = c.post("/auth/login", json={"phone": a.sdt, "password": SHARED_TEST_PASSWORD})
    if r.status_code != 200:
        print(f"  login HTTP {r.status_code} — KHÔNG phải tài khoản hạt giống, hoặc sai SĐT.",
              file=sys.stderr)
        print("  Script này CỐ Ý chỉ mở được tài khoản hạt giống.", file=sys.stderr)
        return 3
    tok = r.json()["access_token"]
    hd = {"Authorization": f"Bearer {tok}"}

    # ② xin OTP — dev trả `otp_code` trong response (mô phỏng, xem main.py)
    r = c.post("/auth/otp/request", headers=hd)
    if r.status_code != 200:
        print(f"  otp/request HTTP {r.status_code}: {r.text[:120]}", file=sys.stderr)
        return 4
    d = r.json()
    ma, sid = d.get("otp_code"), d.get("session_id")
    if not ma or not sid:
        # KHÔNG đoán. Thiếu trường nghĩa là luồng OTP đã đổi, và đoán ở đây sẽ
        # tạo ra một token "trông hợp lệ" cho một luồng không còn tồn tại.
        print(f"  otp/request thiếu otp_code/session_id — luồng OTP đã đổi, DỪNG. "
              f"khoá nhận được: {sorted(d)}", file=sys.stderr)
        return 5

    # ③ xác thực — ĐÚNG endpoint sản phẩm dùng
    r = c.post("/auth/otp/verify", headers=hd, json={"session_id": sid, "otp_code": ma})
    if r.status_code != 200:
        print(f"  otp/verify HTTP {r.status_code}: {r.text[:120]}", file=sys.stderr)
        return 6
    tok2 = r.json()["access_token"]

    if a.ra:
        Path(a.ra).write_text(tok2)
        print(f"  token ĐÃ XÁC THỰC OTP -> {a.ra}", file=sys.stderr)
    else:
        print(tok2)
    print(f"  (sdt {a.sdt} · otp_verified=True · dùng cho bộ đo, hết hạn theo "
          f"JWT_ACCESS_EXPIRE_MINUTES)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
