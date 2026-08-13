"""ST2-P0-5/AUTH5-02/03/06 — VIẾT LẠI sau khi implement (đợt nâng cấp Auth
Flow, 2026-08-12): backend giờ CÓ cơ chế thu hồi JWT thật —
`POST /auth/logout` (src/api/main.py) xoá refresh token + set
`revoked_before[user_id]` (Redis, src/auth.py::set_revoked_before_now) —
access token cũ hơn mốc đó bị từ chối ở các route có check
`is_access_token_revoked` (require_otp_verified, approve/reject — xem lý do
phạm vi có chủ đích trong docstring require_otp_verified).

Không còn `@pytest.mark.security_finding` — route đã tồn tại thật, test này
giờ là regression cấu trúc bình thường (bảo vệ route không bị xoá nhầm),
không phải bằng chứng 1 finding chưa vá."""
from __future__ import annotations

from src.api.main import app


def test_backend_has_a_jwt_revocation_mechanism():
    revocation_paths = {"/auth/logout", "/auth/revoke", "/auth/sessions/revoke"}
    existing_paths = {r.path for r in app.routes if hasattr(r, "path")}
    matched = revocation_paths & existing_paths

    assert matched, (
        "Không có route logout/revoke nào ở backend "
        f"(đã kiểm: {sorted(revocation_paths)}) — regression: route "
        "/auth/logout đã bị xoá nhầm khỏi src/api/main.py."
    )
