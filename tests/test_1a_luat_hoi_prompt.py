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

import datetime as dt
import inspect
import json
import pathlib
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
# 🔴 [ĐO 24/08, Review] Bộ dò từng ĐẾM THIẾU (không bắt "thời điểm gần đây"
# vì chỉ khớp "thời điểm nào") — nguy hiểm hơn đếm thừa, vì nó tạo XANH GIẢ
# có hệ thống trên MỌI ca (không riêng ca đang xét). Mở rộng biến thể tự
# nhiên, không chỉ dạng câu hỏi chuẩn "X nào"/"khi nào".
_TRUC = {
    "so_tien": ("số tiền", "bao nhiêu tiền", "số dư", "giá trị giao dịch",
                "mất bao nhiêu", "trừ bao nhiêu", "bị mất bao nhiêu"),
    "thoi_gian": ("khi nào", "lúc nào", "ngày nào", "giờ nào", "hôm nào", "thời gian nào",
                  "thời điểm nào", "thời gian giao dịch", "khoảng thời gian",
                  "thời điểm", "bao giờ", "ngày giờ"),
    "nguoi_nhan": ("chuyển cho ai", "người nhận", "tên người", "tài khoản nhận", "ai nhận", "cho ai"),
    "ma_gd": ("mã giao dịch", "mã gd", "mã tham chiếu", "txn"),
}
_HUONG_DAN_TIM_MA = ("lịch sử", "bấm vào", "vào mục", "vào phần", "chọn giao dịch")
_TU_GIO_CHINH_XAC = re.compile(r"\bmấy giờ\b|\bgiờ nào\b|\bphút nào\b|\bchính xác lúc\b")
_MOC_NEO_TG = ("hôm nay", "hôm qua", "hôm trước", "sáng", "chiều", "tối", "gần đây", "tuần này", "tuần trước")

# 🔴 [ĐO 24/08] Câu HỎI của LLM luôn có dấu `?`; câu YÊU CẦU tất định của
# `thu_slot` (`phan_luong.py::HOI_THIEU_CA_HAI`/`HOI_THIEU_SO_TIEN`) là câu
# ĐỀ NGHỊ, không có `?` — "Dạ bạn cho mình xin ... giúp mình nhé." R3 từng
# SKIP oan vì bộ dò cũ chỉ nhận dạng `?`, mù hoàn toàn với phong cách này.
# `thu_slot` là đường THẬT của sản phẩm (không phải giả định lý thuyết) nên
# bộ dò PHẢI đọc được cả hai phong cách.
_MAU_YEU_CAU = ("cho mình xin", "cho em xin", "cho mình biết", "cho biết", "vui lòng cho")

# 🔴 [ĐO 24/08, Review duyệt] Ví dụ minh hoạ KHÔNG PHẢI yêu cầu — "Bạn thấy
# tiền bị mất trong trường hợp nào vậy? Ví dụ như: Bạn chuyển..." chỉ hỏi
# MỘT trục (loại khiếu nại), phần sau "Ví dụ như" là gợi ý cách trả lời, không
# phải trục thứ hai. Cắt bỏ phần này TRƯỚC khi so khớp — rẻ, không cần NLP.
# ⚠️ KHÔNG được áp để làm R1 xanh: vi phạm R1 nằm ở GẠCH ĐẦU DÒNG (câu hỏi
# thật, không phải ví dụ) — sau khi cắt, R1 vẫn phải đỏ. Nếu áp xong R1 hoá
# xanh, luật này cài sai.
_MOC_VI_DU = re.compile(r"\b(ví dụ như|ví dụ|vd[:.]|chẳng hạn)\b", re.IGNORECASE)


def _truc_hoi(reply: str) -> set[str]:
    """Trục nào được HỎI/ĐỀ NGHỊ CUNG CẤP — nhận cả câu hỏi (`?`) lẫn câu yêu
    cầu tất định (`cho mình xin...`, không dấu `?`). Cắt bỏ phần SAU mốc ví
    dụ minh hoạ trước khi so khớp."""
    khop_vi_du = _MOC_VI_DU.search(reply)
    if khop_vi_du:
        reply = reply[: khop_vi_du.start()]
    n = reply.lower()
    la_cau_hoi_hoac_yeu_cau = "?" in reply or any(m in n for m in _MAU_YEU_CAU)
    if not la_cau_hoi_hoac_yeu_cau:
        return set()

    manh = [c.strip() for c in re.split(r"(?<=[.!?—-])\s+", reply)
            if "?" in c or any(m in c.lower() for m in _MAU_YEU_CAU)]
    trung = set()
    for truc, tu_khoa in _TRUC.items():
        for c in manh:
            if any(tk in c.lower() for tk in tu_khoa):
                trung.add(truc)
                break
        else:
            # phòng trường hợp không tách mảnh được (thiếu dấu câu chuẩn) —
            # rơi về khớp trên TOÀN reply, đã xác nhận CÓ hỏi/yêu cầu ở trên.
            if any(tk in n for tk in tu_khoa):
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


def _login() -> str:
    """Đăng nhập + xác thực OTP phiên MỘT LẦN, trả `access_token`.

    🔴 [ĐO 24/08, cùng cơ chế đã vá ở A2] `main.py:645` suy `thread_id` TỪ
    `user_id:iat` của JWT — trường `thread_id` trong body bị BỎ QUA LẶNG LẼ
    (ADR-044). Đăng nhập lại giữa hai lượt CÙNG kịch bản (R3, R4) sinh `iat`
    MỚI ⟹ hai lượt rơi vào HAI thread khác nhau dù truyền cùng `thread` —
    R3/R4 khi đó không bao giờ quan sát được nhánh cần đo (lượt 2 luôn là
    lượt ĐẦU của một hội thoại rỗng). Đồng thời thiếu OTP-xác-thực khiến các
    tool tra dữ liệu bị `_OTP_REQUIRED_ERROR` — dùng lại NGUYÊN đường chính
    danh của `test_a2_dong_y_truoc_khi_tao_ve.py::_login()`."""
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


# 🔴 [ĐO 24/08, Review] Chấm lại một ca đỏ = gọi lại model = có thể đọc một
# văn bản KHÁC (LLM không xác định, đúng ca R3 vừa gặp). Không có kho reply
# thật thì mỗi lần sửa bộ dò là một lần tốn tiền để biết bộ dò đúng hay sai.
# Ghi MỌI lượt (không chỉ lúc fail) ra JSONL — 0 token thêm (chỉ I/O trên dữ
# liệu đã có sẵn trong bộ nhớ), cho phép CHẤM LẠI toàn bộ bằng bộ dò mới sau
# này mà không gọi model thêm lần nào.
_LOG_REPLY = pathlib.Path(__file__).resolve().parent.parent / "eval" / "results" / "1a_reply_log.jsonl"


def _ghi_log_reply(cau: str, reply: dict) -> None:
    """Ghi TOÀN VĂN `reply["reply"]` — KHÔNG cắt. Thông điệp lỗi trong assertion
    được phép cắt ngắn để đọc trên terminal (`[:200]`/`[:300]`...); kho lưu ở
    đây là NGUỒN GỐC trước khi bất kỳ ai cắt gì — hai việc tách nhau, đừng gộp."""
    ten_ca = inspect.stack()[2].function  # 2 tầng lên: _chat() -> hàm test gọi nó
    _LOG_REPLY.parent.mkdir(parents=True, exist_ok=True)
    with open(_LOG_REPLY, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "ts": dt.datetime.now(dt.UTC).isoformat(),
            "ca": ten_ca, "cau": cau, "reply": reply["reply"], "tool": reply["tool"],
            "chep_tay": False,  # True chỉ khi backfill thủ công từ hội thoại — xem README kho
        }, ensure_ascii=False) + "\n")


def _chat(cau: str, token: str, thread: str) -> dict:
    # `thread_id` vẫn gửi trong body — vô hại, nhưng nối lượt thật = dùng LẠI
    # cùng `token` (xem `_login()`), không phải cùng biến `thread` truyền tay.
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
    ket_qua = {"tra": j, "reply": j["than"].get("reply") or "",
               "tool": [x.get("tool_name") for x in (j["than"].get("tool_calls") or [])]}
    _ghi_log_reply(cau, ket_qua)
    return ket_qua


def _thread() -> str:
    return f"1A-{uuid.uuid4().hex[:8]}"


# ---------------------------------------------------------------------------
# R1 — một Ý một lượt, khi thiếu ≥2 slot
# ---------------------------------------------------------------------------
# 🔴 ĐỔI NGHĨA 25/08 (đợt "OTP trước token", phiếu §2b — quyết QA/QC, "vùng
# của bạn" theo Coder/Lead): R1 KHÔNG có nghĩa "một YÊU CẦU mỗi tin" như bản
# đầu hàm này giả định (tên cũ `test_r1_thieu_hai_slot_chi_hoi_mot_thu`, đổi
# tên tại đây) — chuyên gia CSKH xác nhận R1 thật là "một Ý mỗi tin", và
# thời gian+số tiền là MỘT cặp neo tìm kiếm, khách trả lời trong cùng một
# hơi thở (kịch bản chuyên gia, lượt 2). ADR/Q2 (24/08) CHỦ Ý cho cổng sau
# OTP hỏi CẢ HAI trong một tin. Bản đầu của assertion này encode đúng cách
# đọc SAI ("một YÊU CẦU") — sửa lại đây, KHÔNG xoá lịch sử: đây chính là
# nguyên nhân Đ1 (đợt này) đo được cổng bắn oan 6/11 lần vì tách hỏi cô lập.
#
# Vẫn PHẢI giữ khả năng bắt "hỏi quá nhiều Ý cùng lúc" — cặp {so_tien,
# thoi_gian} là NGOẠI LỆ DUY NHẤT được phép đi cùng nhau; bất kỳ trục thứ ba
# nào (vd `ma_gd`, `nguoi_nhan`) xuất hiện CÙNG câu vẫn là vi phạm R1 thật.

_CAP_DUOC_PHEP_HOI_CHUNG = frozenset({"so_tien", "thoi_gian"})


def test_r1_thieu_hai_slot_hoi_gop_thoi_gian_va_so_tien():
    """Khách không cho số tiền lẫn thời gian — reply được hỏi CẢ HAI trong
    MỘT tin (đúng "một Ý"), nhưng KHÔNG được kéo thêm trục thứ ba (mã GD,
    người nhận...) vào cùng lượt — đó mới là vi phạm R1 thật."""
    o = _chat("Tôi bị mất tiền trong ví, giúp tôi với.", _login(), _thread())
    truc = _truc_hoi(o["reply"])
    assert truc.issubset(_CAP_DUOC_PHEP_HOI_CHUNG), (
        f"Reply hỏi trục NGOÀI cặp được phép {sorted(_CAP_DUOC_PHEP_HOI_CHUNG)}: {truc}\n"
        f"  reply: {o['reply'][:300]}\n"
        "R1 đòi mỗi lượt chỉ mở MỘT Ý — thời gian+số tiền là một cặp neo được "
        "phép đi cùng nhau (Q2, phiếu §2b), trục khác thì không."
    )


# ---------------------------------------------------------------------------
# R1 — ca ÂM: câu hỏi chính sách chung không được kích hỏi-slot
# ---------------------------------------------------------------------------

def test_r1_cau_hoi_chinh_sach_khong_bi_hoi_slot():
    """Khách hỏi chính sách chung (không phải khiếu nại) — KHÔNG được hỏi slot điều tra.

    Thiếu ca này, một bản vá 'luôn hỏi cho đủ slot' sẽ làm ca dương ở trên
    xanh VÀ làm agent tra-hỏi-slot ngay cả khi khách chỉ hỏi thông tin chung
    — đúng Luật 2 (đối chứng chiều ngược)."""
    o = _chat("Phí chuyển tiền trong ví là bao nhiêu vậy?", _login(), _thread())
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
    """NẾU reply xin mã giao dịch THÌ phải kèm hướng dẫn tìm — không nói trống.

    🔴 [ĐO 24/08] SKIP ở lượt đóng đợt 1A+S8 (03fd9a6) — lượt 1 nội dung THẬT
    (không dính lỗi provider), agent chọn hỏi phân loại giao dịch thay vì mã
    GD, đúng nghĩa gốc của điều kiện skip — KHÔNG PHẢI hệ quả của
    APIConnectionError (đã đối chiếu `eval/results/1a_reply_log.jsonl`, field
    `ca`, xem cùng có ghi chú ở R5 bên dưới cho ca THẬT SỰ dính lỗi provider).
    R2 đã PASSED ở lượt 139K token 19/08 — không mua lại chỉ vì lượt này SKIP."""
    o = _chat(
        "Tôi có một giao dịch bị lỗi nhưng không nhớ số tiền hay ngày giờ gì cả, "
        "giúp tôi tra được không?",
        _login(), _thread(),
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
    """Hai lượt hỏi-lại liên tiếp trong CÙNG hội thoại không được hỏi cùng trục.

    🔴 [ĐO 24/08] CHƯA ĐO ĐƯỢC — SKIP nhiều lượt liên tiếp, MỖI LẦN một
    nguyên nhân KHÁC NHAU (từng gặp: OTP chưa xác thực, lượt 1 không hỏi
    trục, lượt 2 không hỏi trục). PO-agent 24/08: đây là finding về KHẢ NĂNG
    QUAN SÁT của chính test (kịch bản hai-lượt-hỏi-liên-tiếp hiếm khi thật
    sự xảy ra trong luồng agent hiện tại), KHÔNG PHẢI kết luận về sản phẩm —
    khác hẳn R1 (đỏ THẬT, tái hiện được). Lượt 03fd9a6: cả hai lượt nội dung
    THẬT (không dính APIConnectionError), skip vì lượt 2 không hỏi trục nào —
    đối chiếu `eval/results/1a_reply_log.jsonl`. Không tự ý chạy lại chỉ để
    đổi kết quả SKIP — xem ADR liên quan A2 nếu cần đổi cách canh (tất định
    thay vì phụ thuộc hành vi LLM)."""
    th = _thread()
    tok = _login()  # MỘT lần cho cả hai lượt — nối thật cùng thread (xem _login())
    o1 = _chat("Tôi chuyển nhầm tiền cho người lạ.", tok, th)
    truc1 = _truc_hoi(o1["reply"])
    if not truc1:
        pytest.skip("Lượt 1 không hỏi trục nào (có thể đã tạo ticket/khác nhánh) — không quan sát được R3.")
    o2 = _chat("Tôi không nhớ rõ, để tôi coi lại đã.", tok, th)
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
# R3-cầu — 24/08, PO-agent: từ khi 1B có đường `thu_slot` (tất định) + `day_du`
# (LLM), R3 "không hỏi lại cùng trục" phải soi được CẢ hai bên cây cầu, không
# chỉ hai lượt LLM liên tiếp như bản gốc. Cổng tất định hỏi X (0 token) rồi
# khách TRẢ LỜI X — câu hỏi thật: LLM ở lượt sau có ĐỌC ĐƯỢC câu cổng đã hỏi
# trong lịch sử hội thoại không, hay hỏi lại y hệt (với khách: "tôi vừa nói
# rồi mà"). Chưa ai đo được trục này trước hôm nay vì trước đó chỉ có MỘT
# đường (LLM), không có cầu nào để bắc.
# ---------------------------------------------------------------------------

def test_r3_cau_cong_hoi_gi_llm_khong_hoi_lai_cai_do():
    """Cổng tất định hỏi số tiền (thu_slot) → khách cho số tiền → LLM lượt
    sau KHÔNG được hỏi lại số tiền (đã có trong lịch sử hội thoại)."""
    th = _thread()
    tok = _login()
    o1 = _chat("Tôi chuyển nhầm tiền cho người lạ.", tok, th)
    truc1 = _truc_hoi(o1["reply"])
    if "so_tien" not in truc1:
        pytest.skip(
            f"Lượt 1 không hỏi số tiền (trục thấy được: {truc1 or 'không trục nào'}) "
            "— không đúng nhánh cần cho ca cầu này, không quan sát được."
        )
    o2 = _chat("Khoảng 500 nghìn.", tok, th)
    truc2 = _truc_hoi(o2["reply"])
    assert "so_tien" not in truc2, (
        f"Cổng tất định VỪA hỏi số tiền, khách VỪA trả lời '500 nghìn' — "
        f"mà lượt LLM sau vẫn hỏi lại số tiền:\n"
        f"  lượt 1 (cổng): {o1['reply'][:200]}\n"
        f"  lượt 2 (LLM):  {o2['reply'][:200]}\n"
        "R3-cầu: câu cổng đã hỏi phải nằm trong lịch sử LLM đọc được — hỏi lại "
        "là bắt khách lặp lại thứ vừa nói."
    )


# ---------------------------------------------------------------------------
# R4 — tóm tắt đủ slot trước create_ticket (nâng A2, KHÔNG thay A2)
# ---------------------------------------------------------------------------

def test_r4_tom_tat_slot_truoc_create_ticket():
    """Reply dẫn tới/ngay trước create_ticket phải đọc lại đủ SỐ TIỀN + THỜI GIAN + LOẠI.

    A2 (`test_a2_dong_y_truoc_khi_tao_ve.py`) canh 'có chờ đồng ý không' — vật
    khác. Ca này canh NỘI DUNG của chính câu chờ-đồng-ý/xác nhận đó."""
    th = _thread()
    tok = _login()  # MỘT lần cho cả hai lượt — nối thật cùng thread (xem _login())
    o1 = _chat("Tôi chuyển nhầm 500 nghìn cho người lạ hôm qua chiều, mở khiếu nại giúp tôi.", tok, th)
    reply = o1["reply"]
    if "tickets" not in json.dumps(o1["tool"]) and "create_ticket" not in o1["tool"]:
        o2 = _chat("Đúng rồi, tạo giúp tôi.", tok, th)
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
    """Câu hỏi thời gian không được đòi giờ chính xác ('mấy giờ') — phải cho mốc neo.

    🔴 [ĐO 24/08] CHƯA ĐO ĐƯỢC, LÝ DO CỤ THỂ (khác R2/R3-lần-2 — xem ghi chú
    ở đó): lượt duy nhất dính `APIConnectionError` thoáng qua từ nhà cung cấp
    (0 token, fail nhanh <1s, `ly_do_fallback: "nha_cung_cap_thoang_qua"`) —
    reply trả về là câu fallback graceful ("hệ thống đang bận...") KHÔNG hỏi
    trục nào, vô tình trùng điều kiện skip bên dưới. Không phải nhánh nghiệp
    vụ thật. Đối chiếu `eval/results/1a_reply_log.jsonl`. PO-agent 24/08: tỉ
    lệ lỗi provider cả ngày 24/08 là 9,4%/53 lượt gọi thật — KHÔNG bất thường,
    không phải bug cần vá."""
    o = _chat("Tôi chuyển tiền nhầm 300 nghìn, không nhớ chi tiết lắm.", _login(), _thread())
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
