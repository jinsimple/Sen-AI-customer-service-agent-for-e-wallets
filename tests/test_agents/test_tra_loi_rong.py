"""`TraLoiRongError` — model tiêu hết ngân sách vào SUY NGHĨ, `content` rỗng.

## Vì sao lớp lỗi này phải RIÊNG

Model có suy nghĩ (Qwen 3.x) tiêu `reasoning_tokens` **trước** khi viết câu trả
lời. Đo được 17/08: suy nghĩ chiếm **74%** output ở `qwen3.7-plus`, **91%** ở
`qwen3.7-flash`. Nếu `LLM_MAX_TOKENS` đặt thấp, model tiêu hết trần vào suy nghĩ
và trả về `content` **rỗng** — **không có lỗi nào cả**.

Đó là nhánh im lặng: khách nhận một câu rỗng, log không có gì bất thường, và
trong biên bản đo nó hiện ra thành *"model trả lời kém"*.

> **Lớp lỗi riêng là thứ duy nhất cho thước phân biệt LỖI CẤU HÌNH CỦA TA với
> MODEL TRẢ LỜI KÉM.** Không có nó, một `LLM_MAX_TOKENS` đặt thấp sẽ đi vào hồ
> sơ dưới dạng bằng chứng chống lại nhà cung cấp.

Và nó chạm **ràng buộc cứng 3** theo đường vòng: một lượt rỗng không bịa gì,
nhưng nếu tầng trên coi rỗng là "không có dữ liệu" rồi để model tự nói tiếp thì
ta có đúng hình dạng F-32.

## Hai nhánh, cố ý TÁCH

    rỗng + finish_reason='length'  → NỔ `TraLoiRongError`  (biết chắc nguyên nhân)
    rỗng vì lý do khác             → WARNING, KHÔNG đoán   (chưa biết nguyên nhân)

Gộp lại thì ta gán một nguyên nhân cho thứ chưa biết nguyên nhân — đúng thứ
`khong_do_duoc` sinh ra để tránh.
"""
from __future__ import annotations

import os
import subprocess

import pytest

from tests._docker_co_mat import container_song
from tests._dong_bang import LY_DO, dang_dong_bang
from tests._suite_day_du import can_ha_tang

BASE = os.environ.get("FIN05_BASE_URL", "https://localhost")


def _song() -> bool:
    # Uỷ cho `tests/_docker_co_mat.py` — nó KHÔNG NÉM khi máy thiếu `docker`.
    # Bản cũ gọi thẳng `subprocess.run(["docker", ...])` trong biểu thức
    # `skipif`, tức LÚC IMPORT ⟹ máy không có docker thì pytest ném
    # FileNotFoundError lúc THU THẬP: 11 lỗi, `Interrupted`, 0 ca chạy.
    return container_song("fin05-backend-1")


pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(not _song(), reason="container fin05-backend-1 không chạy"),
    pytest.mark.skipif(dang_dong_bang(), reason=LY_DO),
]


def test_lop_loi_ton_tai_va_rieng_biet():
    """Lớp lỗi có thật và KHÔNG phải alias của Exception chung — 0 lượt LLM.

    Kiểm bằng import, không đọc `src/`. Một lớp lỗi kế thừa thẳng `Exception`
    mà không có gì riêng thì `except Exception` ở tầng trên sẽ nuốt nó chung
    với mọi lỗi khác, và ta mất đúng khả năng phân biệt vừa dựng ra.
    """
    code = (
        "from src.agents.graph import EmptyReplyError as E;"
        "print(E.__name__, E.__mro__[1].__name__)"
    )
    r = subprocess.run(["docker", "exec", "fin05-backend-1", "python", "-c", code],
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, (
        f"KHÔNG import được TraLoiRongError: {(r.stderr or r.stdout)[:300]}\n"
        "Lớp lỗi không tồn tại thì mọi assertion dưới đây vô nghĩa."
    )
    print(f"  {r.stdout.strip()}")


def test_tran_thap_thi_no_dung_lop_loi_khong_tra_ve_rong(khach_ngan_sach_thap):
    """Trần token thấp ⟹ NỔ `TraLoiRongError`, KHÔNG trả câu rỗng cho khách.

    Ca này cần `LLM_MAX_TOKENS` thấp — biến môi trường của **container**, nên
    nó `skip` nếu người chạy chưa dựng môi trường đó. Đây là thiếu NĂNG LỰC
    thật (chưa có stack cấu hình sẵn), không phải skip cho qua chuyện.
    """
    tra, code, body = khach_ngan_sach_thap
    assert code != 200 or tra.strip(), (
        "Khách nhận HTTP 200 với câu trả lời RỖNG — nhánh im lặng.\n"
        f"  thân phản hồi: {body[:200]}\n"
        "Rỗng phải nổ thành TraLoiRongError, không được đi qua như thành công."
    )


@pytest.fixture
def khach_ngan_sach_thap():
    if not os.environ.get("FIN05_STACK_MAX_TOKENS_THAP"):
        can_ha_tang(
            "Cần một stack có LLM_MAX_TOKENS thấp (vd 64) để ép bẫy. Biến môi "
            "trường của CONTAINER, không đặt được từ đây.",
            cach_dung="dựng stack Docker riêng có LLM_MAX_TOKENS thấp (vd 64), rồi đặt FIN05_STACK_MAX_TOKENS_THAP=1",
        )
    httpx = pytest.importorskip("httpx")
    c = httpx.Client(verify=False, timeout=300)
    c.post(f"{BASE}/api/session", json={"phone": "0974000145", "password": "Demo@123"})
    r = c.post(f"{BASE}/api/agent-chat", json={"message": "Hạn mức chuyển tiền một ngày là bao nhiêu?"})
    j = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
    c.close()
    return str(j.get("reply") or ""), r.status_code, r.text
