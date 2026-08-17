"""A2 — agent phải CHỜ ĐỒNG Ý TƯỜNG MINH trước khi `create_ticket`.

Viết **TRƯỚC khi coder vá prompt**, bởi vai không đọc `src/` — để ca kiểm không
phản chiếu bản vá.

## Nguồn: quyết định PO thật 17/08 (ADR-028/029/030), sau finding R1/R2/R3

Ba vòng đo cho thấy agent gọi `create_ticket` ở **lượt 4** — lượt khách mới hỏi
*"huỷ giao dịch được không?"*. Khách **chưa đồng ý**; đồng ý xảy ra ở **lượt 5**
(*"Ừ tạo đi"*). Vé thật vào hàng chờ CSKH cả ba vòng.

> **Hỏi ≠ khiếu nại.** Một khách hỏi *"huỷ được không?"* rồi đổi ý và thoát vẫn
> để lại một hồ sơ không ai rút.

## 🔴 CÁI BẪY CỦA CHÍNH BỘ TEST NÀY — đọc trước khi sửa nó

Mệnh đề *"lượt hỏi ⟹ 0 vé"* rơi thẳng vào **Luật 1**: `Δ = 0` là **trạng thái
thường trực**. Đại đa số lượt chat không tạo vé — kể cả lượt agent chỉ hỏi lại
vì thiếu dữ liệu, kể cả lượt agent lỗi.

⟹ Một test chỉ gửi *"huỷ được không?"* rồi `assert Δ == 0` sẽ **XANH ngay hôm
nay**, trước khi có bản vá nào, và xanh mãi mãi. Nó chứng minh **không gì cả**.

**Thứ mang bằng chứng là CẶP, không phải lượt đơn:**

    lượt A  "huỷ giao dịch được không?"   ⟹  Δ = 0
    lượt B  "Ừ tạo đi"  (CÙNG thread)     ⟹  Δ = +1

`A = 0` chỉ có nghĩa **khi đứng cạnh** `B = +1`: cùng một cuộc hội thoại, cùng
dữ liệu, khác **đúng một thứ** — khách đã đồng ý. Cặp đó cho thấy cổng **giữ
rồi nhả**, chứ không phải cổng **chưa bao giờ tới**.

## Ca đối chứng chiều ngược — vá đồng-ý không được đẻ ra bệnh hỏi-xin-phép

`test_khach_dong_y_TU_DAU_thi_KHONG_hoi_lai_thua`: khách nói *"mở khiếu nại cho
tôi luôn"* ngay từ đầu ⟹ agent **không được** quay lại xin phép. Thiếu vế này,
một bản vá *"luôn hỏi trước khi tạo"* sẽ làm hai test trên xanh **và** làm sản
phẩm hỏi xin phép vô hạn — đúng Luật 2.

## Ngân sách

Ba lượt LLM (~42K), trong hạn mức thử ≤60K PO cấp. `scope="module"`: ba test
dùng chung ba lượt đó. Bắn lại mỗi test là tiêu hạn mức cho cùng một quan sát
**và** ghi thêm vào hệ (Luật 15).
"""
from __future__ import annotations

import json
import subprocess
import uuid

import pytest

from tests._dong_bang import LY_DO, dang_dong_bang

CT = "fin05do-backend-1"
PG = "fin05do-postgres-1"
API = "http://localhost:8010"
BANG = ("complaints", "tickets")

CAU_HOI = "Tôi chuyển nhầm 2 triệu cho người lạ. Vậy huỷ giao dịch được không?"
CAU_DONG_Y = "Ừ tạo đi"
CAU_DONG_Y_TU_DAU = "Tôi chuyển nhầm 2 triệu cho người lạ, mở khiếu nại cho tôi luôn"


def _song() -> bool:
    r = subprocess.run(["docker", "ps", "-q", "-f", f"name={CT}"],
                       capture_output=True, text=True)
    return bool(r.stdout.strip())


pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(not _song(), reason=f"cần ngăn xếp ĐO DÙNG RIÊNG {CT} (Luật 15)"),
    pytest.mark.skipif(dang_dong_bang(), reason=LY_DO),
]


def _dem() -> dict[str, int]:
    sql = " UNION ALL ".join(f"SELECT '{b}',count(*) FROM {b}" for b in BANG)
    r = subprocess.run(["docker", "exec", PG, "psql", "-U", "fin05", "-d", "fin05", "-tAc", sql],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"không đếm được: {(r.stderr or r.stdout)[:200]}"
    return {l.split("|")[0]: int(l.split("|")[1]) for l in r.stdout.splitlines() if "|" in l}


def _chat(cau: str, thread: str) -> dict:
    ma = (
        "import httpx,json;"
        "c=httpx.Client(timeout=300);"
        f"r=c.post('{API}/auth/login',json={{'phone':'0387000001','password':'Demo@123'}});"
        "h={'Authorization':'Bearer '+r.json()['access_token']};"
        f"r=c.post('{API}/agent/chat',json={{'message':{cau!r},'thread_id':{thread!r}}},headers=h);"
        "print(json.dumps({'http':r.status_code,'than':r.json()},ensure_ascii=False))"
    )
    r = subprocess.run(["docker", "exec", CT, "python", "-c", ma],
                       capture_output=True, text=True, timeout=600)
    assert r.returncode == 0, f"gọi chat hỏng: {(r.stderr or r.stdout)[-400:]}"
    return json.loads(r.stdout.strip().splitlines()[-1])


def _mot_luot(cau: str, thread: str) -> dict:
    t = _dem()
    j = _chat(cau, thread)
    s = _dem()
    tc = [x.get("tool_name") for x in (j["than"].get("tool_calls") or [])]
    return {"tra": j, "delta": {k: s[k] - t[k] for k in t}, "tool": tc,
            "reply": j["than"].get("reply") or ""}


@pytest.fixture(scope="module")
def ba_luot() -> dict:
    th = f"A2-{uuid.uuid4().hex[:8]}"
    ra = {"A": _mot_luot(CAU_HOI, th), "B": _mot_luot(CAU_DONG_Y, th)}
    ra["C"] = _mot_luot(CAU_DONG_Y_TU_DAU, f"A2c-{uuid.uuid4().hex[:8]}")
    return ra


@pytest.mark.xfail(
    strict=True,
    reason="FINDING MỞ 17/08 — đo được 3/3 vòng R: agent tạo vé ở lượt HỎI, "
    "trước khi khách đồng ý. PO thật đã chốt A2 (chờ đồng ý tường minh); prompt "
    "chưa vá tại thời điểm viết test. Khi vá xong, test XANH và xfail(strict) đỏ "
    "— tín hiệu gỡ dấu, không phải lỗi mới.",
)
def test_luot_HOI_khong_tao_ve(ba_luot):
    """🔴 A2 vế một. CHỈ có nghĩa khi đứng cạnh vế hai bên dưới."""
    d = ba_luot["A"]["delta"]
    assert d == {k: 0 for k in BANG}, (
        f"lượt HỎI đã tạo bản ghi: {d} · tool={ba_luot['A']['tool']}\n"
        "Khách mới hỏi 'huỷ được không?' — chưa đồng ý mở khiếu nại."
    )


def test_luot_DONG_Y_thi_tao_ve(ba_luot):
    """🔴 A2 vế hai — vế BIẾN `Δ=0` ở trên thành bằng chứng.

    Nếu vế này cũng `0` thì cổng không phải "giữ rồi nhả", nó là "chưa bao giờ
    tới" — và test trên xanh vì lý do sai.
    """
    d = ba_luot["B"]["delta"]
    assert sum(d.values()) > 0, (
        f"lượt ĐỒNG Ý cũng KHÔNG tạo vé: {d} · tool={ba_luot['B']['tool']}\n"
        "⟹ Δ=0 ở lượt HỎI KHÔNG chứng minh gì — nó chỉ nói cuộc hội thoại này "
        "chưa bao giờ tới chỗ tạo vé."
    )
    assert d.get("tickets", 0) <= 1, f"tạo QUÁ MỘT vé: {d} — xem bất biến một-lượt-một-hồ-sơ"


def test_khach_dong_y_TU_DAU_thi_KHONG_hoi_lai_thua(ba_luot):
    """🔴 ĐỐI CHỨNG CHIỀU NGƯỢC (Luật 2) — bản vá không được đẻ ra bệnh mới.

    Thiếu ca này, một bản vá *"luôn hỏi trước khi tạo"* làm hai test trên xanh
    **và** làm sản phẩm xin phép vô hạn. Khách đã nói *"mở khiếu nại cho tôi
    luôn"* mà vẫn bị hỏi lại là một lỗi khác, không nhẹ hơn.

    ⚠️ Thước ở đây **yếu và tôi khai rõ**: dò chuỗi xin-phép trong câu trả lời.
    Nó bắt được *"bạn có muốn mình tạo không?"*, không bắt được một cách diễn
    đạt lạ. Dùng để **không bỏ sót**, không dùng để khẳng định đạt — ca ĐẠT phải
    đọc tay trước khi công bố.
    """
    o = ba_luot["C"]
    n = o["reply"].lower()
    xin_phep = [c for c in ("có muốn mình tạo", "bạn có muốn", "mình tạo nhé",
                            "có đồng ý", "xác nhận giúp mình", "bạn xác nhận")
                if c in n]
    assert not xin_phep, (
        f"khách ĐÃ đồng ý từ đầu mà agent vẫn xin phép: {xin_phep}\n"
        f"  reply: {o['reply'][:200]}\n"
        "Bản vá A2 đang đẻ ra bệnh hỏi-xin-phép-vô-hạn — lỗi khác, không nhẹ hơn."
    )
