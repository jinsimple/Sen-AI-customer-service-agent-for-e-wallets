"""F-33 — 429 của nhà cung cấp ra tới KHÁCH dưới dạng HTTP 500.

Bắt được 16/08 trong lúc chạy `eval/do_token_latency.py --lap 3`. Log backend:

    openai.RateLimitError: Error code: 429 —
      "Rate limit reached for gpt-4o-mini … on tokens per min (TPM):
       Limit 200000, Used 193274, Requested 11332.
       **Please try again in 1.381s**"

Khách nhận: `HTTP 500 {"detail":"Internal Server Error"}`.

## Vì sao đây là finding chứ không phải "hạ tầng quá tải, chịu thôi"

Nhà cung cấp **nói rõ trong phản hồi** rằng chờ **1,381 giây** là gọi lại được.
Thông tin để phục hồi nằm sẵn trong tay; không ai dùng nó. Một sự cố **1,4 giây**
biến thành một lỗi cứng, và khách thấy màn hình trắng thay vì một câu xin lỗi.

Nó cũng là chế độ hỏng **dễ gặp nhất trên demo**: trần TPM dùng chung, và đo
được rằng **một người gõ 21 lượt trong 2 phút** đủ chạm 193k/200k.

## Ba lớp, ba mức chấp nhận — cố ý KHÔNG gộp

    1. không được trả 500          — 500 là "lỗi của server", đây là lỗi tạm thời
    2. nên retry theo đúng số giây nhà cung cấp trả về
    3. nếu hết khe thì phải là câu xin lỗi tử tế, không phải mã lỗi

Gộp ba lớp thành một assertion thì một bản vá chỉ đổi mã 500 -> 503 sẽ "đạt"
trong khi khách vẫn nhận một mã lỗi trần trụi.

## Trạng thái: chưa chạy được, và điều đó được ghi rõ

Muốn tái hiện thì phải **cố ý ép 429**, tức đốt gần hết trần TPM dùng chung —
đúng thứ đang bị đóng băng. Nên ca này `skip` với lý do **thiếu tài nguyên dùng
chung**, không phải "chưa viết xong". Khi TPM rảnh và coder đã vá, bỏ biến môi
trường là nó chạy.

⚠️ Đừng chạy file này trong lúc có người đang quay demo.
"""
from __future__ import annotations

import os
import subprocess

import pytest

BASE = os.environ.get("FIN05_BASE_URL", "https://localhost")
SO_KHACH = os.environ.get("FIN05_TEST_CUSTOMER_PHONE", "0974000145")
MAT_KHAU = os.environ.get("FIN05_TEST_PASSWORD", "Demo@123")
# Ca này ĐỐT TPM có chủ đích. Phải bật RIÊNG một biến nữa, không đi chung với
# việc bỏ đóng băng — bỏ đóng băng chỉ có nghĩa "được dùng model bình thường",
# không có nghĩa "được phép cố tình làm cạn hạn mức của cả đội".
CHO_PHEP = os.environ.get("FIN05_CHO_PHEP_EP_429", "").strip() not in ("", "0", "false")


def _song() -> bool:
    r = subprocess.run(["docker", "ps", "-q", "-f", "name=fin05-backend-1"],
                       capture_output=True, text=True)
    return bool(r.stdout.strip())


pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(not _song(), reason="container fin05-backend-1 không chạy"),
    pytest.mark.skipif(
        not CHO_PHEP,
        reason=(
            "F-33 cần ÉP 429, tức đốt gần hết trần TPM 200k dùng chung với 3 phiên "
            "khác + PO thật. Đây là thiếu TÀI NGUYÊN DÙNG CHUNG, không phải test "
            "chưa viết xong. Bật: FIN05_CHO_PHEP_EP_429=1 — và chỉ khi chắc chắn "
            "không ai đang quay demo."
        ),
    ),
]


@pytest.fixture(scope="module")
def khach():
    httpx = pytest.importorskip("httpx")
    c = httpx.Client(verify=False, timeout=600)
    r = c.post(f"{BASE}/api/session", json={"phone": SO_KHACH, "password": MAT_KHAU})
    assert r.status_code == 200, f"đăng nhập hỏng: {r.status_code}"
    assert r.json().get("role") == "customer", "cần vai customer, nếu không /agent-chat trả 403"
    yield c
    c.close()


def _ep_429(c) -> list:
    """Gõ liên tục tới khi có lượt KHÔNG phải 200. Trả danh sách phản hồi lạ.

    Dùng đúng câu D3 của bộ lệnh (nặng nhất) trong MỘT phiên để lịch sử cộng
    dồn — cách rẻ nhất để chạm trần, và cũng là cách khách hàng thật chạm nó.
    """
    cau = ("Tháng này tôi tiêu bao nhiêu qua ví, khoản nào lớn nhất, "
           "và có khoản nào trùng lặp không?")
    la = []
    for _ in range(30):
        r = c.post(f"{BASE}/api/agent-chat", json={"message": cau})
        if r.status_code != 200:
            la.append(r)
            break
    return la


def test_f33_429_khong_ra_toi_khach_thanh_500(khach):
    """Lớp 1: lỗi tạm thời của nhà cung cấp KHÔNG được thành 500."""
    la = _ep_429(khach)
    if not la:
        pytest.skip("30 lượt liên tiếp vẫn 200 — không ép được 429 lúc này, "
                    "không kết luận gì (khác với 'đã vá')")
    r = la[0]
    assert r.status_code != 500, (
        f"F-33: nhà cung cấp trả 429 (lỗi TẠM THỜI, có kèm số giây chờ), "
        f"khách nhận 500 'Internal Server Error'.\n"
        f"  thân phản hồi: {r.text[:200]}\n"
        "500 nói với khách rằng server hỏng. Nó không hỏng — nó bận 1,4 giây."
    )


def test_f33_co_cau_xin_loi_thay_vi_ma_loi_tran_trui(khach):
    """Lớp 3: hết khe thì phải là câu tiếng Việt tử tế, không phải mã lỗi."""
    la = _ep_429(khach)
    if not la:
        pytest.skip("không ép được 429 lúc này")
    than = la[0].text.lower()
    assert any(t in than for t in ("xin lỗi", "vui lòng thử lại", "đang bận", "quá tải")), (
        f"F-33: khách nhận một mã lỗi trần trụi, không có câu nào giải thích.\n"
        f"  thân phản hồi: {la[0].text[:200]}"
    )
