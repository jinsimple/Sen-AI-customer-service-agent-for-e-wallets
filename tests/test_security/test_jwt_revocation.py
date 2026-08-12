"""FIN05-StressTest-Plan-v2 ST2-P0-5 (docs/FIN05-Feature-Inventory-Security-
Review.md §11, câu hỏi "JWT 8 giờ, không có refresh token/revocation list").

`src/auth.py::get_current_user` xác thực JWT THUẦN qua chữ ký (`jwt.decode`)
— không tra cứu bất kỳ trạng thái phía server nào (DB/cache/session store)
để biết token đã bị thu hồi hay chưa. "Đăng xuất" ở frontend
(`frontend/src/components/TopbarActions.tsx::logout`) chỉ gọi `DELETE
/api/session` — route Next.js NỘI BỘ xoá cookie phía trình duyệt, không hề
chạm backend/JWT. Hệ quả: 1 JWT bị đánh cắp (session cookie hijack, log
rò rỉ...) vẫn dùng được TRỌN 8 giờ dù người dùng đã "đăng xuất" hay đổi mật
khẩu.

Test khẳng định HÀNH VI AN TOÀN MONG MUỐN (backend phải có ít nhất 1 cơ chế
thu hồi JWT trước khi hết hạn tự nhiên) — FAIL NGAY hôm nay bằng bằng chứng
CẤU TRÚC (không có route/cơ chế nào như vậy tồn tại trong `app.routes`),
không phải suy đoán."""
from __future__ import annotations

import pytest

from src.api.main import app


@pytest.mark.security_finding
def test_backend_has_a_jwt_revocation_mechanism():
    revocation_paths = {"/auth/logout", "/auth/revoke", "/auth/sessions/revoke"}
    existing_paths = {r.path for r in app.routes if hasattr(r, "path")}
    matched = revocation_paths & existing_paths

    assert matched, (
        "Không có route logout/revoke nào ở backend "
        f"(đã kiểm: {sorted(revocation_paths)}) — JWT phát hành ra luôn có "
        "hiệu lực cho tới khi hết hạn tự nhiên (JWT_EXPIRE_MINUTES=8*60, "
        "src/config.py), kể cả sau khi 'đăng xuất' (chỉ xoá cookie phía "
        "frontend, xem TopbarActions.tsx::logout) hay đổi mật khẩu. Cần "
        "thêm cơ chế thu hồi (blacklist token đã logout, hoặc session "
        "store tra cứu mỗi request, hoặc rút ngắn TTL + refresh token) "
        "trước khi chấp nhận test này pass — xem "
        "docs/FIN05-Feature-Inventory-Security-Review.md §11."
    )
