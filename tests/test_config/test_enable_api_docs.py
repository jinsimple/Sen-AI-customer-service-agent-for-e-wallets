"""05/09 — production judge-xem (VPS `home`) bật `OTP_DEMO_MODE=true` (hiện
mã OTP demo cho giám khảo, cần `APP_ENV != production`) VÔ TÌNH mở luôn
`/docs`/`/redoc`/`/openapi.json` ra production thật, vì gate cũ đọc CHUNG
`APP_ENV != production` cho cả hai quyết định không liên quan. Vá: tách cờ
RIÊNG `ENABLE_API_DOCS` (config.py), mặc định FALSE — `main.py` đọc cờ này
thay vì suy luận từ APP_ENV.

Chạy qua SUBPROCESS (cùng khuôn test_fail_fast_secrets.py) — `app = FastAPI(...)`
ở main.py chạy NGAY lúc import module, không reload được an toàn trong cùng
tiến trình pytest."""
from __future__ import annotations

import json
import os
import subprocess
import sys

from src.config import ROOT_DIR

_BASE_ENV = {
    "JWT_SECRET_KEY": "test-jwt-secret-key-for-subprocess-check",
    "FIELD_ENCRYPTION_KEY": "IJVDfID59_AVFnicIewobfpdeVwV560yACrgwYm8SJ4=",
    "DATABASE_URL": "sqlite:///:memory:",
    "REDIS_URL": "fake://ci",
}

_PROBE = (
    "import src.api.main as m, json;"
    "print(json.dumps({'docs_url': m.app.docs_url, 'redoc_url': m.app.redoc_url, "
    "'openapi_url': m.app.openapi_url}))"
)


def _docs_state(env_overrides: dict[str, str]) -> dict:
    env = {**os.environ, **_BASE_ENV, **env_overrides}
    result = subprocess.run(
        [sys.executable, "-c", _PROBE],
        cwd=str(ROOT_DIR),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, f"import lỗi:\nSTDOUT={result.stdout}\nSTDERR={result.stderr}"
    return json.loads(result.stdout.strip().splitlines()[-1])


def test_mac_dinh_tat_khong_khai_gi_ca():
    state = _docs_state({"ENABLE_API_DOCS": "", "APP_ENV": "", "OTP_DEMO_MODE": ""})
    assert state == {"docs_url": None, "redoc_url": None, "openapi_url": None}


def test_khai_enable_api_docs_thi_bat():
    state = _docs_state({"ENABLE_API_DOCS": "true", "APP_ENV": "", "OTP_DEMO_MODE": ""})
    assert state == {"docs_url": "/docs", "redoc_url": "/redoc", "openapi_url": "/openapi.json"}


def test_otp_demo_mode_bat_KHONG_con_vo_tinh_mo_docs():
    """Ca THẬT gây lỗi (05/09) — production judge-xem cần OTP_DEMO_MODE=true +
    APP_ENV=development (KHÁC production) để hợp lệ với guard config.py:199.
    Trước vá: gate cũ đọc APP_ENV != production ⟹ docs BẬT theo. Sau vá:
    ENABLE_API_DOCS bỏ trống ⟹ docs vẫn TẮT dù APP_ENV != production."""
    state = _docs_state({"APP_ENV": "development", "OTP_DEMO_MODE": "true", "ENABLE_API_DOCS": ""})
    assert state == {"docs_url": None, "redoc_url": None, "openapi_url": None}


def test_enable_api_docs_doc_lap_voi_app_env_production():
    """Đảo chiều: APP_ENV=production KHÔNG còn tự tắt docs — chỉ ENABLE_API_DOCS
    quyết định. (Không phải cấu hình khuyến nghị cho production thật — đây là
    test CHỨNG MINH 2 cờ đã tách rời, không phải hướng dẫn vận hành.)"""
    state = _docs_state({"APP_ENV": "production", "ENABLE_API_DOCS": "true", "OTP_DEMO_MODE": ""})
    assert state == {"docs_url": "/docs", "redoc_url": "/redoc", "openapi_url": "/openapi.json"}
