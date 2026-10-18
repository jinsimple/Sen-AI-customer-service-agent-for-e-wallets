"""GĐ3 (đổi model + tự xoay, docs/giao-viec/2026-08-19-gd3-doi-model-xoay-tu-dong.md,
`876a240`) — ca "key thiếu" của cổng xoay 0-token, phần LIVE-READINESS.

Sự cố THẬT làm sinh ra cơ chế đang được canh ở đây: `LLM_BASE_URL` trỏ sang
nhà cung cấp khác (deepseek/dashscope) mà `LLM_API_KEY` để trống từng khiến
khoá OpenAI `sk-proj…` bị gửi thẳng sang máy chủ của nhà cung cấp kia (xem
`docs/security/2026-08-17-lo-khoa-dashscope-va-403-thanh-500.md`). Cơ chế vá
(`src/config.py::_khoa_cho_nha_cung_cap`, dòng ~237-300) ĐÃ CÓ SẴN trước GĐ3
— ca này là test regression chưa từng tồn tại cho nó, không phải việc mới.

Hai vế PHẢI khẳng định riêng, không gộp (Lead/PO 19/08):
    ① thiếu LLM_API_KEY khi LLM_BASE_URL trỏ nhà cung cấp khác ⟹ CHẾT lúc
       khởi động (import `src.config` raise NGAY, không chạy ngầm)
    ② và KHÔNG có đường nào rơi về OPENAI_API_KEY thay thế
① mà xanh trong khi ② hỏng là đúng loại "xanh giả" đã đếm nhiều lần trong dự
án này (cùng họ với `unlockTxnRail`).

## Vì sao đây là hộp đen, không phải patch hàm nội bộ

Bản nháp đầu của ca này định `monkeypatch` thẳng hàm kiểm khoá — Lead chỉ ra
lỗ: patch một hàm chỉ chứng minh "hàm X ném lỗi", không chứng minh KHÔNG CÓ
đường nào khác né qua hàm X mà vẫn để lọt khoá. Đổi sang quan sát HÀNH VI
KHỞI ĐỘNG (import chết hay sống, thông điệp nói gì) — đúng thứ người vận hành
thật trải qua, và đúng lý do vách "tester không đọc `src/`" tồn tại: bám hợp
đồng, không bám cách cài đặt.

Chạy qua SUBPROCESS (giữ đúng khuôn `test_fail_fast_secrets.py` cùng thư mục)
— không `importlib.reload` trong tiến trình pytest, tránh làm bẩn
`sys.modules['src.config']` cho các test chạy sau.

## Sentinel, không bao giờ khoá thật (Bảo Mật 19/08, near-miss đã chặn)

Muốn CHỨNG MINH một bí mật không rò, đừng bao giờ dùng CHÍNH bí mật đó làm dữ
liệu thử — dùng một giá trị vô hại nhưng ĐỘC NHẤT. Mọi giá trị "khoá" trong
tệp này là sentinel tự nhận diện (`SENTINEL-KHONG-DUOC-ROI-KHOI-MAY`), không
phải khoá thật đọc từ `.env`. `env` truyền cho subprocess được dựng TƯỜNG
MINH đủ ba biến (`LLM_BASE_URL`/`LLM_API_KEY`/`OPENAI_API_KEY`) — nếu bỏ
trống bất kỳ biến nào (thay vì đặt chuỗi rỗng), `src/config.py` gọi
`load_dotenv(ROOT_DIR / ".env")` sẽ tự điền giá trị THẬT của máy dev vào chỗ
trống đó, làm ca không mô phỏng đúng "thiếu" (bẫy đã đo được lúc viết ca này:
bỏ trống `LLM_BASE_URL` khiến `load_dotenv` điền `base_url` thật của máy này
vào thông điệp lỗi)."""
from __future__ import annotations

import os
import subprocess
import sys

from src.config import ROOT_DIR

_BASE_ENV = {
    "JWT_SECRET_KEY": "test-jwt-secret-key-for-subprocess-check",
    "FIELD_ENCRYPTION_KEY": "MTIzNDU2Nzg5MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTI9",
}

_LLM_BASE_URL_NHA_CUNG_CAP_KHAC = "https://api.deepseek.com"
_SENTINEL_LLM_API_KEY = "sk-deepseek-SENTINEL-KHONG-DUOC-ROI-KHOI-MAY-000"
_SENTINEL_OPENAI_API_KEY = "sk-proj-SENTINEL-KHONG-DUOC-ROI-KHOI-MAY-000"


def _import_config_in_subprocess(env_overrides: dict[str, str]) -> subprocess.CompletedProcess:
    # Ba biến LUÔN có mặt tường minh (chuỗi rỗng nếu "thiếu") — không bao giờ
    # bỏ trống key để load_dotenv tự điền giá trị thật của máy dev vào đó.
    env = {
        **os.environ,
        **_BASE_ENV,
        "LLM_BASE_URL": "",
        "LLM_API_KEY": "",
        "OPENAI_API_KEY": _SENTINEL_OPENAI_API_KEY,
        **env_overrides,
    }
    return subprocess.run(
        [sys.executable, "-c", "import src.config; print('IMPORT_OK')"],
        cwd=str(ROOT_DIR),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_thieu_llm_api_key_khi_base_url_tro_noi_khac_chet_ngay_luc_khoi_dong():
    """Vế ①. `LLM_BASE_URL` trỏ nhà cung cấp khác, `LLM_API_KEY` rỗng."""
    outcome = _import_config_in_subprocess({
        "LLM_BASE_URL": _LLM_BASE_URL_NHA_CUNG_CAP_KHAC,
        "LLM_API_KEY": "",
    })
    assert outcome.returncode != 0, (
        "import src.config phải raise NGAY khi LLM_BASE_URL trỏ nhà cung cấp "
        f"khác mà LLM_API_KEY rỗng, không được chạy ngầm.\nstdout:\n{outcome.stdout}"
    )
    # Đọc THÔNG ĐIỆP, không chỉ exit code (Luật A) — phải đúng LÝ DO này, không
    # phải chết vì thiếu DATABASE_URL/JWT_SECRET_KEY hay lý do khác trùng hợp.
    assert "LLM_API_KEY" in outcome.stderr
    assert _LLM_BASE_URL_NHA_CUNG_CAP_KHAC in outcome.stderr


def test_thieu_llm_api_key_KHONG_roi_ve_openai_api_key_thay_the():
    """Vế ②. Cùng tình huống ①, kèm `OPENAI_API_KEY` sentinel CÓ giá trị —
    nếu tồn tại đường vòng nào âm thầm dùng `OPENAI_API_KEY` thay thế khi
    `LLM_API_KEY` thiếu, ca này sẽ XANH SAI (import chạy được, khoá OpenAI bị
    dùng nhầm cho nhà cung cấp khác) thay vì đỏ đúng thứ ① đã đỏ.

    Không assert riêng gì thêm ngoài ①: nếu ① đã đỏ (chết ngay, không chạy
    ngầm) thì by construction OPENAI_API_KEY sentinel này KHÔNG BAO GIỜ có cơ
    hội được dùng — cái phải canh là ① và ② PHẢI đỏ CÙNG NHAU, không tách rời.
    Đây chính là lý do có ca đối chứng bên dưới."""
    outcome = _import_config_in_subprocess({
        "LLM_BASE_URL": _LLM_BASE_URL_NHA_CUNG_CAP_KHAC,
        "LLM_API_KEY": "",
        "OPENAI_API_KEY": _SENTINEL_OPENAI_API_KEY,
    })
    assert outcome.returncode != 0
    # Thông điệp phải tự nêu tên CẢ HAI biến — bằng chứng cơ chế BIẾT về nguy
    # cơ này (không phải chết vì lý do khác rồi tình cờ không dùng OPENAI_API_KEY).
    assert "LLM_API_KEY" in outcome.stderr
    assert "OPENAI_API_KEY" in outcome.stderr


def test_du_llm_api_key_import_sach_ke_ca_base_url_khac_va_openai_khac_sentinel():
    """Ca ĐỐI CHỨNG (Luật A) — thiếu nó thì hai ca đỏ trên có thể đỏ vì MỌI
    import đều đỏ trên máy này (subprocess hỏng, thiếu dependency...), không
    thật sự do thiếu LLM_API_KEY. Đổi ĐÚNG MỘT biến so với hai ca trên:
    LLM_API_KEY từ rỗng sang sentinel không rỗng — mọi biến khác giữ nguyên."""
    outcome = _import_config_in_subprocess({
        "LLM_BASE_URL": _LLM_BASE_URL_NHA_CUNG_CAP_KHAC,
        "LLM_API_KEY": _SENTINEL_LLM_API_KEY,
        "OPENAI_API_KEY": _SENTINEL_OPENAI_API_KEY,
    })
    assert outcome.returncode == 0, f"import src.config phải chạy sạch khi đủ LLM_API_KEY:\n{outcome.stderr}"
    assert "IMPORT_OK" in outcome.stdout


def test_llm_base_url_rong_thi_thieu_llm_api_key_KHONG_chet_hanh_vi_cu_mot_nha_cung_cap():
    """Ca 2 của brief ("thiếu biến ⟹ hành vi cũ một-model") áp cho đúng biến
    này: khi `LLM_BASE_URL` rỗng (mặc định OpenAI, chưa cấu hình bể xoay),
    thiếu `LLM_API_KEY` KHÔNG được fail-fast — đây là hành vi ĐÃ CÓ TRƯỚC GĐ3
    (khác hẳn `OPENAI_API_KEY`, xem `test_missing_openai_api_key_does_not_fail_fast_at_import`
    trong tệp `test_fail_fast_secrets.py` cùng thư mục — CÙNG MỘT tinh thần,
    khác biến). Đo thật lúc viết ca này (subprocess cô lập, không qua transport
    thật): `LLM_BASE_URL=""` + `LLM_API_KEY=""` ⟹ import sạch, không raise."""
    outcome = _import_config_in_subprocess({
        "LLM_BASE_URL": "",
        "LLM_API_KEY": "",
    })
    assert outcome.returncode == 0, (
        "Thiếu LLM_API_KEY khi LLM_BASE_URL RỖNG (chưa trỏ nhà cung cấp khác) "
        f"không được fail-fast — đây là hành vi cũ, không phải ca ①/②.\nstderr:\n{outcome.stderr}"
    )
