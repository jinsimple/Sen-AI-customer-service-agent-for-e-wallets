"""FIN05-StressTest-Plan-v2 ST2-A-04/ST2-G-01 (docs/FIN05-Feature-Inventory-
Security-Review.md §10) — `src/config.py` đã có sẵn cơ chế fail-fast cho
`JWT_SECRET_KEY`/`FIELD_ENCRYPTION_KEY` (raise `RuntimeError` NGAY lúc import
nếu thiếu, xem dòng 84-99) nhưng CHƯA từng có test regression bảo vệ hành vi
đó — ai đó vô tình đổi `os.environ.get(...)` thành có default rỗng
(`os.environ.get("JWT_SECRET_KEY", "")` chẳng hạn) sẽ không bị bắt bởi bất kỳ
test nào hiện có.

Chạy qua SUBPROCESS (không `importlib.reload` trong tiến trình pytest) —
tránh làm bẩn `sys.modules['src.config']` cho các test khác chạy sau trong
cùng phiên pytest (nhiều module khác đã `from src.config import X`, reload
giữa chừng có thể để lại trạng thái nửa vời nếu raise xảy ra giữa lúc module
đang thực thi)."""
from __future__ import annotations

import os
import subprocess
import sys

from src.config import ROOT_DIR

_BASE_ENV = {
    "JWT_SECRET_KEY": "test-jwt-secret-key-for-subprocess-check",
    "FIELD_ENCRYPTION_KEY": "MTIzNDU2Nzg5MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTI9",
}


def _import_config_in_subprocess(env_overrides: dict[str, str | None]) -> subprocess.CompletedProcess:
    env = {**os.environ, **_BASE_ENV}
    for key, value in env_overrides.items():
        if value is None:
            # src/config.py gọi load_dotenv(ROOT_DIR / ".env") — mặc định
            # KHÔNG override biến đã có sẵn trong os.environ, nhưng SẼ tự
            # điền lại nếu biến hoàn toàn vắng mặt (key not in os.environ).
            # Phải đặt CHUỖI RỖNG (key vẫn "có mặt", value falsy) thay vì
            # pop hẳn key ra khỏi env — nếu không, .env thật của máy dev sẽ
            # âm thầm điền lại giá trị thật, làm test không mô phỏng đúng
            # "thiếu secret" (phát hiện thật lúc chạy lần đầu: cả 2 test
            # fail-fast đều pass nhầm vì lý do này).
            env[key] = ""
        else:
            env[key] = value
    return subprocess.run(
        [sys.executable, "-c", "import src.config"],
        cwd=str(ROOT_DIR),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_missing_jwt_secret_key_fails_fast_at_import():
    result = _import_config_in_subprocess({"JWT_SECRET_KEY": None})
    assert result.returncode != 0, "import src.config phải raise NGAY khi thiếu JWT_SECRET_KEY, không được chạy tiếp"
    assert "JWT_SECRET_KEY" in result.stderr


def test_missing_field_encryption_key_fails_fast_at_import():
    result = _import_config_in_subprocess({"FIELD_ENCRYPTION_KEY": None})
    assert result.returncode != 0, "import src.config phải raise NGAY khi thiếu FIELD_ENCRYPTION_KEY, không được chạy tiếp"
    assert "FIELD_ENCRYPTION_KEY" in result.stderr


def test_all_required_secrets_present_imports_cleanly():
    """Test tích cực — tránh false-negative nếu 2 test trên chỉ pass vì
    subprocess bị lỗi environment gì khác, không thật sự do thiếu key."""
    result = _import_config_in_subprocess({})
    assert result.returncode == 0, f"import src.config phải chạy sạch khi đủ secret:\n{result.stderr}"


def test_missing_openai_api_key_does_not_fail_fast_at_import():
    """Ghi nhận HÀNH VI HIỆN TẠI (không phải bug tự tạo, không phải finding
    P0) — KHÁC với JWT_SECRET_KEY/FIELD_ENCRYPTION_KEY, `OPENAI_API_KEY`
    (src/config.py:77) đọc qua `os.environ.get(...)` KHÔNG có guard
    `raise RuntimeError` — thiếu key này app vẫn khởi động bình thường, chỉ
    lỗi sau ở lần gọi OpenAI thật đầu tiên. Có thể chấp nhận được (nhiều
    route CSKH/supervisor không cần OpenAI) — test này CHỈ để không ai vô
    tình nghĩ 3 secret được đối xử giống nhau khi đọc lướt code."""
    result = _import_config_in_subprocess({"OPENAI_API_KEY": None})
    assert result.returncode == 0, (
        "OPENAI_API_KEY giờ ĐÃ fail-fast — nếu đây là thay đổi có chủ đích, "
        "sửa lại test này cho khớp (không phải bug)."
    )
