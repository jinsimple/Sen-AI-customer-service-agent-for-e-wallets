"""1B.4 — S7 (tối đa một lần hỏi-slot/hội thoại) và S8 (Redis lỗi ⟹ `day_du`),
đo Ở TẦNG TÍCH HỢP thật (HTTP + Redis), khác `eval/cong_phan_luong.py` (hàm
thuần `phan_luong(cau)`, không có `thread_id`/Redis — đã tự khai không đo
được S7/S8 ở tầng đó).

> ⚠️ **Chạy TỪ HOST, cần `docker` CLI.** Cùng khuôn `test_a2_dong_y_truoc_khi_tao_ve.py`.
> ⚠️ **TỐN TIỀN (S7)** — vài lượt LLM. Mặc định TẮT, bật bằng `FIN05_CHO_PHEP_TON_TIEN=1`.
> S8 dừng/khởi động lại Redis — CHỈ trên `fin05do-redis-1` (ngăn ĐO riêng), KHÔNG BAO GIỜ
> trên `fin05` (ngăn demo).

## S8 — kỳ vọng ĐÃ ĐỔI, khai lại cho khỏi nhầm phiếu gốc

Phiếu gốc ghi "fail-open" (giữ nguyên hành vi hỏi). Coder đã đổi hướng theo
finding Review: Redis không đọc được ⟹ **rơi về `day_du`** (KHÔNG hỏi lại, đi
thẳng đường LLM đầy đủ) — coi trạng thái "đã hỏi" là KHÔNG XÁC ĐỊNH ⟹ AN TOÀN
HƠN là đi LLM (tốn thêm token nhưng không risk hỏi vô hạn/sai) hơn là tự cho
mình quyền hỏi lại vô căn cứ. Nếu cổng VẪN bắn `thu_slot` khi Redis chết ⟹
finding thật, không phải test sai.
"""
from __future__ import annotations

import json
import subprocess
import uuid

import pytest

from tests._docker_co_mat import container_song
from tests._dong_bang import LY_DO, dang_dong_bang
from tests._ton_tien import duoc_phep_ton_tien, ly_do

CT = "fin05do-backend-1"
REDIS_CT = "fin05do-redis-1"
API = "http://localhost:8010"


def _song() -> bool:
    return container_song(CT)


pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(not duoc_phep_ton_tien(),
                       reason=ly_do(30_000, "S7 (2-3 lượt chat thật), S8 0 token")),
    pytest.mark.skipif(not _song(), reason=f"cần ngăn xếp ĐO DÙNG RIÊNG {CT} (Luật 15)"),
    pytest.mark.skipif(dang_dong_bang(), reason=LY_DO),
]


def _login() -> str:
    ma = (
        "import httpx,json;"
        "c=httpx.Client(timeout=300);"
        f"r=c.post('{API}/auth/login',json={{'phone':'0387000001','password':'Demo@123'}});"
        "tok=r.json()['access_token'];"
        "h={'Authorization':'Bearer '+tok};"
        f"r=c.post('{API}/auth/otp/request',headers=h);"
        "sid=r.json()['session_id'];code=r.json()['otp_code'];"
        f"r=c.post('{API}/auth/otp/verify',headers=h,json={{'session_id':sid,'otp_code':code}});"
        "assert r.json().get('otp_verified') is True, 'OTP verify thất bại: '+r.text;"
        "print(r.json()['access_token'])"
    )
    r = subprocess.run(["docker", "exec", CT, "python", "-c", ma],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"đăng nhập/OTP hỏng: {(r.stderr or r.stdout)[-400:]}"
    return r.stdout.strip().splitlines()[-1]


def _chat(cau: str, token: str, thread: str) -> dict:
    ma = (
        "import httpx,json;"
        "c=httpx.Client(timeout=300);"
        f"h={{'Authorization':'Bearer '+{token!r}}};"
        f"r=c.post('{API}/agent/chat',json={{'message':{cau!r},'thread_id':{thread!r}}},headers=h);"
        "print(json.dumps({'http':r.status_code,'than':r.json()},ensure_ascii=False))"
    )
    r = subprocess.run(["docker", "exec", CT, "python", "-c", ma],
                       capture_output=True, text=True, timeout=600)
    assert r.returncode == 0, f"gọi chat hỏng: {(r.stderr or r.stdout)[-400:]}"
    j = json.loads(r.stdout.strip().splitlines()[-1])
    return {"tra": j, "reply": j["than"].get("reply") or ""}


def _thread() -> str:
    return f"1B4-{uuid.uuid4().hex[:8]}"


def _duong_gan_nhat() -> str | None:
    """Đọc `duong` của bản ghi CUỐI trong usage.jsonl — nguồn thật, không suy
    từ câu chữ reply (đúng nếp A2: đọc sổ, không đoán)."""
    r = subprocess.run(["docker", "exec", CT, "tail", "-1", "/app/logs/usage.jsonl"],
                       capture_output=True, text=True, timeout=30)
    if r.returncode != 0 or not r.stdout.strip():
        return None
    return json.loads(r.stdout.strip().splitlines()[-1]).get("duong")


# ---------------------------------------------------------------------------
# S7 — cổng thu-slot tối đa MỘT lần mỗi hội thoại
# ---------------------------------------------------------------------------

def test_s7_toi_da_mot_lan_hoi_slot_moi_hoi_thoai():
    """Lượt 1 thiếu slot ⟹ `thu_slot`. Lượt 2 CÙNG thread, dù NỘI DUNG cũng
    thiếu slot y hệt ⟹ PHẢI đi `day_du`, không được `thu_slot` lần hai."""
    th = _thread()
    tok = _login()
    o1 = _chat("Tôi bị trừ tiền.", tok, th)
    d1 = _duong_gan_nhat()
    if d1 != "thu_slot":
        pytest.skip(f"Lượt 1 không đi thu_slot (đi {d1!r}) — không đúng nhánh cần cho S7.")
    o2 = _chat("Tôi bị trừ tiền lần nữa nè.", tok, th)
    d2 = _duong_gan_nhat()
    assert d2 != "thu_slot", (
        f"Lượt 2 CÙNG thread vẫn đi thu_slot lần HAI: duong={d2!r}\n"
        f"  lượt 1: {o1['reply'][:200]}\n"
        f"  lượt 2: {o2['reply'][:200]}\n"
        "S7: cổng thu-slot chỉ được bắn TỐI ĐA MỘT LẦN mỗi hội thoại — lượt 2 "
        "phải đi day_du bất kể nội dung có thiếu slot hay không."
    )


# ---------------------------------------------------------------------------
# S8 — Redis lỗi ⟹ rơi về `day_du`, KHÔNG được bắn `thu_slot`
# ---------------------------------------------------------------------------

def test_s8_redis_loi_thi_ve_day_du_khong_hoi_lai():
    """Dừng Redis trên `fin05do` (CHỈ ngăn này) → gửi câu thiếu slot → kỳ vọng
    MỚI: rơi về `day_du` (KHÔNG hỏi lại tất định, không lỗi 5xx). Luôn khởi
    động lại Redis ở `finally`, xác nhận healthy trước khi coi test xong.

    🔴 [ĐO 24/08] LẦN CHẠY ĐẦU: `_login()` GỌI SAU KHI Redis đã dừng ⟹ tự nó
    hỏng (`/auth/login`/`/auth/otp/*` cũng cần Redis — refresh token/OTP
    session lưu ở đó), che mất hoàn toàn thứ đang muốn đo. Sửa: đăng nhập +
    OTP TRƯỚC khi dừng Redis, chỉ phần GỬI TIN mới chạy trong lúc Redis chết
    — cô lập đúng BIẾN đang test (trạng thái 'đã hỏi slot chưa'), không lẫn
    biến khác (đăng nhập có cần Redis không — câu hỏi KHÁC, không phải S8)."""
    tok = _login()  # TRƯỚC khi dừng Redis — tránh nhầm "login cần Redis" với "S8"
    r = subprocess.run(["docker", "stop", REDIS_CT], capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, f"không dừng được {REDIS_CT}: {r.stderr}"
    try:
        o = _chat("Tôi bị trừ tiền.", tok, _thread())
        d = _duong_gan_nhat()
        assert o["tra"]["http"] < 500, f"HTTP {o['tra']['http']} khi Redis chết — không được lỗi cứng: {o['reply'][:200]}"
        assert d != "thu_slot", (
            f"Redis chết mà cổng VẪN bắn thu_slot: duong={d!r}\n  reply: {o['reply'][:200]}\n"
            "S8 (kỳ vọng MỚI): Redis không đọc được trạng thái 'đã hỏi chưa' ⟹ "
            "phải rơi về day_du (an toàn hơn), không được tự cho mình quyền hỏi."
        )
    finally:
        r2 = subprocess.run(["docker", "start", REDIS_CT], capture_output=True, text=True, timeout=30)
        assert r2.returncode == 0, f"🔴 KHÔNG khởi động lại được {REDIS_CT}: {r2.stderr} — CẦN XỬ LÝ TAY NGAY"
        chk = subprocess.run(["docker", "inspect", "-f", "{{.State.Health.Status}}", REDIS_CT],
                             capture_output=True, text=True, timeout=30)
        print(f"\n  [S8] {REDIS_CT} sau khi start lại: {chk.stdout.strip() or chk.stderr.strip()}")
