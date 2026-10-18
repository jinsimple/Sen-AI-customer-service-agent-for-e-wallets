"""GĐ3 (đổi model + tự xoay, docs/giao-viec/2026-08-19-gd3-doi-model-xoay-tu-dong.md,
`876a240`) — cổng xoay 0-token, phần seam `src/agents/llm_pool.py`.

🔴 **ĐỎ CÓ LÝ DO — khác hẳn AUTH-007/008 của GĐ2.5.** Viết TRƯỚC khi
`src/agents/llm_pool.py` tồn tại/ổn định, theo đúng khuôn "cổng nghiệm thu
dựng sẵn": viết từ HỢP ĐỒNG Coder đã khai (tên hàm/biến, không phải suy đoán)
trước khi code có, để khi code xanh thì nó chứng minh khớp HỢP ĐỒNG, không
chỉ khớp CHÍNH NÓ. Lý do đỏ hôm nay là **"bộ phận đang được viết"**, KHÔNG
phải "rào mạng" (đó là lý do của AUTH-008 — hai lý do khác nhau, không gộp).
**Không chạy file này cho tới khi Coder xác nhận `llm_pool.py` đứng yên** —
`git status` lúc viết ca này cho thấy nó đang untracked/mid-edit; import một
module đang được ghi dở không đo được gì có nghĩa, kể cả đỏ.

Hợp đồng (nguyên văn Coder khai qua tin nhắn, KHÔNG đọc `src/`):
    llm_pool.LLM_MODEL_POOL: list[str]        parse từ env LLM_MODEL_POOL
                                               (phân cách dấu phẩy, thứ tự =
                                               ưu tiên). Thiếu biến ⟹ [LLM_MODEL].
    llm_pool.model_dau_luot(da_thu=None) -> str | None
                                               model tiếp theo CHƯA cạn, bỏ
                                               qua da_thu. None = bể cạn.
    llm_pool.danh_dau_can(model) -> None      ghi Redis `model_can:{model}`
                                               kèm TTL, log `model_rotated`.
    llm_pool.model_dang_can(model) -> bool

Tên model dùng trong test ("model-a"/"model-b"/"model-c") là giá trị TỰ ĐẶT,
không phải tên model thật — tránh mọi coupling với danh sách deepseek thật
(danh sách đó có thể đổi mà không ai cần sửa test chọn model)."""
from __future__ import annotations

import os
import subprocess
import sys

import pytest

from src.agents import llm_pool
from src.config import ROOT_DIR
from src.redis_client import get_default_client

# ─────────────────────── ca cần subprocess (hằng đọc LÚC IMPORT) ───────────

_BASE_ENV = {
    "JWT_SECRET_KEY": "test-jwt-secret-key-for-subprocess-check",
    "FIELD_ENCRYPTION_KEY": "MTIzNDU2Nzg5MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTI9",
    "REDIS_URL": "fake://ci",
    "LLM_BASE_URL": "",
    "LLM_API_KEY": "",
    "OPENAI_API_KEY": "sk-proj-SENTINEL-KHONG-DUOC-ROI-KHOI-MAY-000",
}


def _doc_be_trong_subprocess(llm_model_pool: str | None) -> subprocess.CompletedProcess:
    env = {**os.environ, **_BASE_ENV}
    if llm_model_pool is None:
        env["LLM_MODEL_POOL"] = ""  # rỗng tường minh, không bỏ trống (bẫy load_dotenv, xem test_config)
    else:
        env["LLM_MODEL_POOL"] = llm_model_pool
    return subprocess.run(
        [sys.executable, "-c",
         "from src.agents import llm_pool; print(','.join(llm_pool.LLM_MODEL_POOL))"],
        cwd=str(ROOT_DIR), env=env, capture_output=True, text=True, timeout=30,
    )


def test_be_theo_moi_truong_doi_LLM_MODEL_POOL_be_doi_theo_khong_can_dung_anh():
    """Ca "bể theo môi trường" — đổi biến, bể đổi, không cần đổi code/ảnh."""
    a = _doc_be_trong_subprocess("deepseek-v4-pro-0813,deepseek-v4-flash")
    assert a.returncode == 0, f"stderr:\n{a.stderr}"
    assert a.stdout.strip() == "deepseek-v4-pro-0813,deepseek-v4-flash"

    b = _doc_be_trong_subprocess("qwen3.7-plus-2026-05-26,deepseek-v3.2,deepseek-v4-flash-0731")
    assert b.returncode == 0, f"stderr:\n{b.stderr}"
    assert b.stdout.strip() == "qwen3.7-plus-2026-05-26,deepseek-v3.2,deepseek-v4-flash-0731"

    assert a.stdout != b.stdout, "hai bể khác nhau qua env phải cho hai kết quả khác nhau"


def test_thieu_bien_LLM_MODEL_POOL_hanh_vi_cu_mot_model():
    """Ca "thiếu biến" — bể chỉ còn đúng 1 phần tử, bằng LLM_MODEL đang cấu
    hình (không phải một tên hardcode tôi tự đoán — so sánh động với chính
    src.config.LLM_MODEL của lần chạy đó, qua cùng subprocess)."""
    outcome = subprocess.run(
        [sys.executable, "-c",
         "from src.agents import llm_pool; from src import config; "
         "print(','.join(llm_pool.LLM_MODEL_POOL)); print(config.LLM_MODEL)"],
        cwd=str(ROOT_DIR),
        env={**os.environ, **_BASE_ENV, "LLM_MODEL_POOL": ""},
        capture_output=True, text=True, timeout=30,
    )
    assert outcome.returncode == 0, f"stderr:\n{outcome.stderr}"
    line = outcome.stdout.strip().splitlines()
    assert len(line) == 2, f"stdout bất thường:\n{outcome.stdout}"
    be_str, llm_model = line
    assert be_str == llm_model, (
        f"LLM_MODEL_POOL rỗng phải cho bể đúng 1 phần tử = LLM_MODEL hiện tại "
        f"({llm_model!r}), đo được {be_str!r}"
    )


# ─────────────────────── ca chạy in-process (Redis giả của conftest) ───────


@pytest.fixture(autouse=True)
def _be_gia_lap(monkeypatch):
    """Không đụng LLM_MODEL_POOL thật của tiến trình test — mỗi ca tự đặt
    bể riêng qua monkeypatch, không rò giữa các ca."""
    monkeypatch.setattr(llm_pool, "LLM_MODEL_POOL", ["model-a", "model-b", "model-c"])
    yield


def test_model_dau_luot_theo_dung_thu_tu_uu_tien():
    assert llm_pool.turn_start_model() == "model-a"
    assert llm_pool.turn_start_model(tried={"model-a"}) == "model-b"
    assert llm_pool.turn_start_model(tried={"model-a", "model-b"}) == "model-c"


def test_be_can_toan_phan_qua_da_thu_tra_ve_none():
    assert llm_pool.turn_start_model(tried={"model-a", "model-b", "model-c"}) is None


def test_danh_dau_can_khien_model_dang_can_dung_va_bi_model_dau_luot_bo_qua():
    llm_pool.mark_exhausted("model-a")
    assert llm_pool.exhausted_model("model-a") is True
    assert llm_pool.exhausted_model("model-b") is False
    # Không truyền da_thu — model_dau_luot phải TỰ bỏ qua model đã đánh dấu
    # cạn qua Redis, không chỉ qua tập da_thu do người gọi truyền tay.
    assert llm_pool.turn_start_model() == "model-b"


def test_ca_be_bi_redis_danh_dau_can_het_thi_model_dau_luot_tra_none():
    llm_pool.mark_exhausted("model-a")
    llm_pool.mark_exhausted("model-b")
    llm_pool.mark_exhausted("model-c")
    assert llm_pool.turn_start_model() is None, "cả bể đã cạn qua Redis (không dùng da_thu) vẫn phải trả None"


def test_danh_dau_can_dat_TTL_khong_song_vinh_vien():
    """Cạn quota là tạm thời (nhà cung cấp reset hạn mức) — đánh dấu vĩnh
    viễn là bug, model không bao giờ được thử lại nữa dù đã hồi hạn mức."""
    llm_pool.mark_exhausted("model-a")
    ttl = get_default_client().ttl("model_can:model-a")
    assert ttl is not None and ttl > 0, f"model_can:model-a phải có TTL dương, đo được {ttl!r}"


def test_trang_thai_can_doc_lai_duoc_qua_ham_cong_khai_khong_qua_bo_nho_python():
    """Xấp xỉ hoá 'giữa 4 worker không lệch nhau' — CHỈ chứng minh trạng
    thái nằm ở Redis (đọc lại được qua `model_dang_can()`/key Redis trực
    tiếp), không phải biến Python cục bộ nào giữ trong hàm.

    🔴 GIỚI HẠN đã biết, ghi rõ để không ai đọc quá tay: fakeredis trong
    pytest dùng MỘT FakeServer singleton cho cả tiến trình (xem
    tests/conftest.py) — ca này KHÔNG chứng minh được đa-tiến-trình THẬT
    (4 worker uvicorn thật, 4 tiến trình hệ điều hành riêng). Muốn chứng
    minh đủ, cần một ca tích hợp chạy trên ngăn xếp có `UVICORN_WORKERS=4`
    thật, đo ở tầng khác — ngoài phạm vi unit test này."""
    llm_pool.mark_exhausted("model-a")
    assert get_default_client().exists("model_can:model-a")
    assert llm_pool.exhausted_model("model-a") is True
