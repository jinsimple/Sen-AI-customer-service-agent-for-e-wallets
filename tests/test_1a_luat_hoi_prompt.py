"""1A.1 — bộ ca eval cho 5 luật hỏi R1–R5 (`docs/giao-viec/2026-08-24-luong-
chatbot-1A-1B.md`, PO thật duyệt 24/08). Viết TRƯỚC khi Coder vá prompt (1A.2)
— bởi vai không đọc `src/`, để ca kiểm không phản chiếu bản vá.

> ⚠️ **Chạy TỪ HOST, cần `docker` CLI.** Điều khiển container qua `docker
> exec`, giống `test_a2_dong_y_truoc_khi_tao_ve.py`.
> ⚠️ **TỐN TIỀN** — 6 lượt LLM. Mặc định TẮT, bật bằng `FIN05_CHO_PHEP_TON_TIEN=1`.

## Năm luật, cách đo — quyết định của tester (Luật 7: công cụ đo là vùng này)

Kiểm THÔNG TIN CÓ MẶT theo NHÓM Ý NGHĨA (số tiền / thời gian / người nhận / mã
giao dịch), không khớp câu chữ cố định — đúng ranh giới đã dùng ở
`eval/do_cong_presence.py`. `_truc_hoi()` bên dưới là bộ dò dùng chung cho
R1/R3, cùng một cơ chế, hai câu hỏi khác nhau (đếm SỐ trục ở R1, SO SÁNH trục
ở R3).

## R2 và R3 — khai rõ giới hạn, không dựng phép khớp lỏng

**R2** đòi agent THỰC SỰ đi tới nhánh xin mã giao dịch — nhánh đó chỉ nổ khi
các slot khác không đủ phân biệt giao dịch, một trạng thái tôi không ép được
từ ngoài (không đọc được logic phân biệt trong `src/`). Assertion viết dạng
**suy diễn có điều kiện**: NẾU reply xin mã giao dịch THÌ phải kèm hướng dẫn.
Nếu agent không bao giờ xin mã (chọn hỏi slot khác trước), ca này **không xác
nhận được gì** — ghi rõ trong log, không phải một PASS giả.

**R3** đòi hai lượt hỏi-lại LIÊN TIẾP trong cùng hội thoại, cả hai đều "chưa
đủ" — phụ thuộc hành vi thật của agent ở lượt 2 (có thể nó đã đủ dữ liệu và
tạo vé luôn, không hỏi lại lần hai). Ca được viết để CỐ tạo tình huống hai lần
hỏi, nhưng nếu agent hội tụ nhanh hơn dự kiến, ca tự báo "không quan sát được
lượt hỏi thứ hai" thay vì ép một kết luận.
"""
from __future__ import annotations

import json
import re
import subprocess
import uuid

import pytest

from tests._docker_co_mat import container_song
from tests._dong_bang import LY_DO, dang_dong_bang
from tests._ton_tien import duoc_phep_ton_tien, ly_do

CT = "fin05do-backend-1"
API = "http://localhost:8010"

# Nhóm ý nghĩa dùng chung cho R1 (đếm) và R3 (so trục) — khớp THEO NHÓM, không
# khớp một cụm từ cố định (đúng ranh giới cổng presence).
_TRUC = {
    "so_tien": ("số tiền", "bao nhiêu tiền", "số dư", "giá trị giao dịch"),
    "thoi_gian": ("khi nào", "lúc nào", "ngày nào", "giờ nào", "hôm nào", "thời gian nào", "thời điểm nào"),
    "nguoi_nhan": ("chuyển cho ai", "người nhận", "tên người", "tài khoản nhận"),
    "ma_gd": ("mã giao dịch", "mã gd", "mã tham chiếu", "txn"),
}
_HUONG_DAN_TIM_MA = ("lịch sử", "bấm vào", "vào mục", "vào phần", "chọn giao dịch")
_TU_GIO_CHINH_XAC = re.compile(r"\bmấy giờ\b|\bgiờ nào\b|\bphút nào\b|\bchính xác lúc\b")
_MOC_NEO_TG = ("hôm nay", "hôm qua", "hôm trước", "sáng", "chiều", "tối", "gần đây", "tuần này", "tuần trước")


def _truc_hoi(reply: str) -> set[str]:
    """Trục nào được HỎI (câu chứa dấu `?` và một từ khoá nhóm đó)."""
    cau_hoi = [c.strip() for c in re.split(r"(?<=[.!?])\s+", reply) if "?" in c]
    n = reply.lower()
    trung = set()
    for truc, tu_khoa in _TRUC.items():
        for c in cau_hoi:
            cl = c.lower()
            if any(tk in cl for tk in tu_khoa):
                trung.add(truc)
                break
        else:
            # phòng trường hợp câu hỏi không tách được (thiếu dấu câu chuẩn) —
            # rơi về khớp trên TOÀN reply, chỉ khi reply có ít nhất một `?`.
            if "?" in reply and any(tk in n for tk in tu_khoa):
                trung.add(truc)
    return trung


def _song() -> bool:
    return container_song(CT)


pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(not duoc_phep_ton_tien(),
                       reason=ly_do(90_000, "6 lượt chat thật qua /agent/chat, R1-R5")),
    pytest.mark.skipif(not _song(), reason=f"cần ngăn xếp ĐO DÙNG RIÊNG {CT} (Luật 15)"),
    pytest.mark.skipif(dang_dong_bang(), reason=LY_DO),
]


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
    j = json.loads(r.stdout.strip().splitlines()[-1])
    return {"tra": j, "reply": j["than"].get("reply") or "",
            "tool": [x.get("tool_name") for x in (j["than"].get("tool_calls") or [])]}


def _thread() -> str:
    return f"1A-{uuid.uuid4().hex[:8]}"


# ---------------------------------------------------------------------------
# R1 — một câu hỏi một lượt, khi thiếu ≥2 slot
# ---------------------------------------------------------------------------

def test_r1_thieu_hai_slot_chi_hoi_mot_thu():
    """Khách không cho số tiền lẫn thời gian — reply chỉ được hỏi ĐÚNG MỘT trục."""
    o = _chat("Tôi bị mất tiền trong ví, giúp tôi với.", _thread())
    truc = _truc_hoi(o["reply"])
    assert len(truc) <= 1, (
        f"Thiếu số tiền VÀ thời gian mà reply hỏi {len(truc)} trục CÙNG LƯỢT: {truc}\n"
        f"  reply: {o['reply'][:300]}\n"
        "R1 đòi mỗi lượt chỉ mở một nhánh quyết định."
    )


# ---------------------------------------------------------------------------
# R1 — ca ÂM: câu hỏi chính sách chung không được kích hỏi-slot
# ---------------------------------------------------------------------------

def test_r1_cau_hoi_chinh_sach_khong_bi_hoi_slot():
    """Khách hỏi chính sách chung (không phải khiếu nại) — KHÔNG được hỏi slot điều tra.

    Thiếu ca này, một bản vá 'luôn hỏi cho đủ slot' sẽ làm ca dương ở trên
    xanh VÀ làm agent tra-hỏi-slot ngay cả khi khách chỉ hỏi thông tin chung
    — đúng Luật 2 (đối chứng chiều ngược)."""
    o = _chat("Phí chuyển tiền trong ví là bao nhiêu vậy?", _thread())
    truc = _truc_hoi(o["reply"])
    assert not truc, (
        f"Câu hỏi CHÍNH SÁCH CHUNG mà agent vẫn hỏi slot điều tra: {truc}\n"
        f"  reply: {o['reply'][:300]}\n"
        "Không có khiếu nại/giao dịch nào được nhắc tới — không có gì để điều tra."
    )


# ---------------------------------------------------------------------------
# R2 — hỏi mã giao dịch phải kèm đường đi (suy diễn có điều kiện)
# ---------------------------------------------------------------------------

def test_r2_hoi_ma_giao_dich_kem_duong_di():
    """NẾU reply xin mã giao dịch THÌ phải kèm hướng dẫn tìm — không nói trống."""
    o = _chat(
        "Tôi có một giao dịch bị lỗi nhưng không nhớ số tiền hay ngày giờ gì cả, "
        "giúp tôi tra được không?",
        _thread(),
    )
    n = o["reply"].lower()
    if not any(tk in n for tk in _TRUC["ma_gd"]):
        pytest.skip(
            "Reply không xin mã giao dịch (có thể agent chọn hỏi slot khác trước) "
            "— ca này KHÔNG xác nhận được gì cho R2 ở lượt này, không phải PASS/FAIL."
        )
    assert any(hd in n for hd in _HUONG_DAN_TIM_MA), (
        f"Agent xin mã giao dịch nhưng KHÔNG kèm hướng dẫn tìm ở đâu:\n"
        f"  reply: {o['reply'][:300]}\n"
        "R2: không được nói trống 'cho em xin mã' — phải kèm đường đi (vd 'vào Lịch sử...')."
    )


# ---------------------------------------------------------------------------
# R3 — lần hỏi lại thứ hai phải đổi trục (phụ thuộc hội thoại thật)
# ---------------------------------------------------------------------------

def test_r3_lan_hoi_lai_thu_hai_doi_truc():
    """Hai lượt hỏi-lại liên tiếp trong CÙNG hội thoại không được hỏi cùng trục."""
    th = _thread()
    o1 = _chat("Tôi chuyển nhầm tiền cho người lạ.", th)
    truc1 = _truc_hoi(o1["reply"])
    if not truc1:
        pytest.skip("Lượt 1 không hỏi trục nào (có thể đã tạo ticket/khác nhánh) — không quan sát được R3.")
    o2 = _chat("Tôi không nhớ rõ, để tôi coi lại đã.", th)
    truc2 = _truc_hoi(o2["reply"])
    if not truc2:
        pytest.skip(
            "Lượt 2 không hỏi trục nào (agent có thể đã bàn giao/tạo ticket thay vì "
            "hỏi tiếp) — không quan sát được lượt hỏi thứ hai để so trục."
        )
    assert not (truc1 & truc2), (
        f"Lượt hỏi lại THỨ HAI lặp cùng trục với lượt trước: {truc1 & truc2}\n"
        f"  lượt 1: {o1['reply'][:200]}\n"
        f"  lượt 2: {o2['reply'][:200]}\n"
        "R3: hỏi lại lần hai phải đổi trục (thời gian/người nhận...), không lặp nguyên câu."
    )


# ---------------------------------------------------------------------------
# R4 — tóm tắt đủ slot trước create_ticket (nâng A2, KHÔNG thay A2)
# ---------------------------------------------------------------------------

def test_r4_tom_tat_slot_truoc_create_ticket():
    """Reply dẫn tới/ngay trước create_ticket phải đọc lại đủ SỐ TIỀN + THỜI GIAN + LOẠI.

    A2 (`test_a2_dong_y_truoc_khi_tao_ve.py`) canh 'có chờ đồng ý không' — vật
    khác. Ca này canh NỘI DUNG của chính câu chờ-đồng-ý/xác nhận đó."""
    th = _thread()
    o1 = _chat("Tôi chuyển nhầm 500 nghìn cho người lạ hôm qua chiều, mở khiếu nại giúp tôi.", th)
    reply = o1["reply"]
    if "tickets" not in json.dumps(o1["tool"]) and "create_ticket" not in o1["tool"]:
        o2 = _chat("Đúng rồi, tạo giúp tôi.", th)
        reply = o2["reply"] if not o1["reply"] else o1["reply"] + "\n" + o2["reply"]
    n = (o1["reply"] + " " + reply).lower()
    co_tien = bool(re.search(r"\d[\d.,]*\s*(nghìn|k|đ|vnd|triệu)", n))
    co_thoi_gian = any(tk in n for tk in ("hôm qua", "hôm nay", "chiều", "sáng", "tối", "ngày"))
    co_loai = any(tk in n for tk in ("chuyển nhầm", "sai người", "nhầm người", "khiếu nại"))
    assert co_tien and co_thoi_gian and co_loai, (
        f"Trước/quanh create_ticket, reply thiếu tóm tắt slot — "
        f"tiền={co_tien} thời_gian={co_thoi_gian} loại={co_loai}\n"
        f"  reply: {n[:400]}\n"
        "R4: phải đọc lại đủ số tiền + thời gian + loại để khách tự sửa TRƯỚC khi tạo vé."
    )


# ---------------------------------------------------------------------------
# R5 — hỏi thời gian bằng mốc neo, không đòi giờ chính xác
# ---------------------------------------------------------------------------

def test_r5_hoi_thoi_gian_bang_moc_neo():
    """Câu hỏi thời gian không được đòi giờ chính xác ('mấy giờ') — phải cho mốc neo."""
    o = _chat("Tôi chuyển tiền nhầm 300 nghìn, không nhớ chi tiết lắm.", _thread())
    n = o["reply"].lower()
    if "thoi_gian" not in _truc_hoi(o["reply"]):
        pytest.skip("Reply không hỏi trục thời gian ở lượt này — không quan sát được R5.")
    assert not _TU_GIO_CHINH_XAC.search(n), (
        f"Câu hỏi thời gian đòi GIỜ CHÍNH XÁC thay vì mốc neo:\n  reply: {o['reply'][:300]}\n"
        "R5: hỏi 'hôm nay hay hôm trước, sáng hay chiều', không hỏi 'mấy giờ'."
    )
    assert any(m in n for m in _MOC_NEO_TG), (
        f"Câu hỏi thời gian không thấy mốc neo nào ({_MOC_NEO_TG}):\n  reply: {o['reply'][:300]}"
    )
