"""Phân luồng lượt chat — quyết định NHỊ PHÂN: lượt này có cần bộ đồ nghề đầy đủ không?

Sau cờ `PHAN_LUONG_BAT`, **mặc định TẮT**. Tắt thì `run_agent_turn` chạy y hệt
trước khi có file này.

═══ VÌ SAO QUY TẮC, KHÔNG PHẢI MODEL ══════════════════════════════════════

Đã khảo sát `semantic-router` + encoder cục bộ. Đo thật (17/08): greenfield
~609MB, trong đó `litellm` **115M** — một cổng gọi 100+ nhà cung cấp LLM mà ta
không dùng một dòng nào — để làm một việc là **so cosine hai vector**. Ảnh sản
phẩm hiện tại `site-packages` là **892M**, nên ~473M (bỏ semantic-router) vẫn
là **+53%**. PO thật bác.

Quy tắc thuần: **0 byte phụ thuộc · 0 token · 0 model · 0 cold start**. Và nó
là hướng DUY NHẤT đánh giá được mà không tốn gì.

═══ BA NGUYÊN TẮC ═════════════════════════════════════════════════════════

**① DANH SÁCH CHO PHÉP, không danh sách cấm.** Đi nhẹ CHỈ KHI **mọi** token
thuộc tập đóng `XA_GIAO`; một token lạ ⟹ đầy đủ.

Hai loại danh sách hụt theo **hai chiều ngược nhau**: danh sách CẤM hụt ⟹ bỏ
sót khiếu nại thật. Danh sách CHO PHÉP hụt ⟹ mất một lượt đơn, tốn thêm token,
**không ai bị bỏ rơi**. Cùng nguyên tắc đã áp cho `DIALABLE` và cho việc che
bí mật.

**② KHÔNG có mệnh đề độ dài.** Bản nháp có `DAI_TOI_DA=40`. Đo: gỡ hẳn thì bộ
âm 124 câu **vẫn chặn 124/124**, và 21 ca từng chỉ đứng trên độ dài chuyển
sang bị chặn bằng danh-sách-cho-phép — tức bằng **lý do đúng**. Một hằng số
tuỳ tiện gánh 17% bộ ca là thứ ai đó sẽ nới lên 60 vì một lý do nghe hợp lý,
và `124/124` sẽ vẫn xanh cho tới lúc đó.

**③ CÓ CHỮ SỐ ⟹ đầy đủ, vô điều kiện.** Tiền, mã giao dịch, SĐT, ngày giờ —
mọi thứ đáng tra cứu đều mang số. Chấp nhận chặn nhầm `"cảm ơn 1000 lần"`; che
nhầm rẻ hơn bỏ sót. Đây cũng là mệnh đề chặn `"mất 500k"` (8 ký tự, là khiếu
nại) — ca giết mọi luật kiểu "ngắn ⟹ đơn giản".

═══ RANH GIỚI CỨNG ════════════════════════════════════════════════════════

**Lớp này KHÔNG quyết định nghiệp vụ.** Nó chỉ trả lời *"lượt này có cần bộ đồ
nghề đầy đủ không"*. Nó **không** được tự trả lời khách một câu nghiệp vụ nào.

**Đường nhẹ KHÔNG tạo bản ghi nghiệp vụ nào.** Nếu một lượt cần tạo bản ghi thì
tự nó đã không phải lượt đơn, và việc nó đi được đường nhẹ chính là **bằng
chứng phân loại sai**. Bất biến đo được: `đường nhẹ ⟹ Δcomplaints = Δtickets = 0`.

**Phân loại theo TỪNG LƯỢT, không theo PHIÊN.** Khách gõ `"alo"` rồi câu sau
mới kể mất tiền — câu sau phải đi đầy đủ. Không nhớ trạng thái nào giữa các lượt.

**Sai an toàn = nghi ngờ thì đi ĐẦY ĐỦ.** Chỉ cho đi nhẹ khi KHẲNG ĐỊNH được
là đơn; mọi thứ khác — lỗi, câu rỗng, token lạ — đi đầy đủ.
"""
from __future__ import annotations

import hashlib
import logging
import re
import unicodedata
from pathlib import Path

_logger = logging.getLogger("fin05.phan_luong")

DUONG_NHE = "nhe"
DUONG_THU_SLOT = "thu_slot"
DUONG_DAY_DU = "day_du"

# Tập đóng token xã giao. CHỈ mở rộng khi có ca THẬT, không mở theo dự đoán —
# mỗi token thêm vào là một chỗ khiếu nại thật có thể lọt qua.
XA_GIAO = {
    "alo", "a lô", "alô", "hello", "hi", "hey", "chào", "xin chào", "chao",
    "ê", "e", "ơi", "oi",
    "shop", "chị", "chi", "anh", "em", "bạn", "ban", "ad", "admin", "cskh",
    "bot", "ạ", "a", "nhé", "nhe", "nha", "với", "voi",
    "cảm ơn", "cam on", "cám ơn", "thanks", "thank", "tks", "ok", "oke", "okay",
    "được", "duoc", "rồi", "roi", "vâng", "vang", "ừ", "u", "dạ", "da",
    "tạm biệt", "tam biet", "bye", "goodbye",
    "à", "ừm", "hmm", "haha", "hihi", "^^", ":)", ":d",
}
_CUM = sorted((c for c in XA_GIAO if " " in c), key=len, reverse=True)

_CO_CHU_SO = re.compile(r"\d")
_DAU_CAU = re.compile(r"[.,!?;:~\-_/\\\"'()\[\]{}…]+")

# Câu trả lời đường nhẹ. HẰNG SỐ ở tầng code, KHÔNG nhờ model sinh — cả điểm
# của đường này là không gọi model. CỐ Ý không trả lời bất kỳ điều gì thuộc
# nghiệp vụ, chỉ mở lời và mời khách nói vấn đề.
TRA_LOI_NHE = (
    "Dạ mình nghe ạ! Bạn cho mình biết mình có thể hỗ trợ gì cho bạn nhé — "
    "nếu có vấn đề với giao dịch nào, bạn kể giúp mình chi tiết ạ."
)

# ═══ 1B — CỔNG THU SLOT TẤT ĐỊNH (docs/giao-viec/2026-08-24-luong-chatbot-1A-1B.md) ═══
#
# NHÓM B — dấu hiệu SỞ HỮU/CÁ NHÂN + ĐỘNG TỪ GIAO DỊCH (đã xảy ra), HOẶC
# "mất"/"bị mất"/"bị trừ" đứng NGAY TRƯỚC một khuôn số tiền (một chiều — PO-
# agent đính chính 24/08: hai chiều sẽ bắt oan "...20k thì mất phí gì?", vì
# "20k" chỉ cách "mất" một từ theo chiều ngược).
_SO_HUU = ("tôi", "toi", "của tôi", "cua toi", "mình", "minh",
           "tài khoản tôi", "tk tôi", "bên tôi", "ben toi")
_DONG_TU_GD = ("chuyển", "chuyen", "bị trừ", "bi tru", "trừ tiền", "tru tien",
               "nhận", "nhan", "gửi", "gui", "rút", "rut", "nạp", "nap",
               "thanh toán", "thanh toan")
_MAT_NEO = ("mất", "mat", "bị mất", "bi mat", "bị trừ", "bi tru")

_re_word = lambda tu: re.compile(r"\b" + re.escape(tu) + r"\b")  # noqa: E731
_RE_SO_HUU = [_re_word(t) for t in _SO_HUU]
_RE_DONG_TU_GD = [_re_word(t) for t in _DONG_TU_GD]

# Khuôn số tiền (mục 3.1) — CHỈ số viết bằng chữ số + đơn vị tuỳ chọn. Số viết
# CHỮ THUẦN ("năm trăm nghìn", "nửa triệu") CỐ Ý không bóc — khai rõ, không cố
# đoán (phạm vi riêng nếu cần, không lẫn vào 1B).
_SO_TIEN = re.compile(
    r"\d[\d.,]*\s*(k|nghìn|nghin|ngàn|ngan|tr|triệu|trieu|đ|d|vnd|vnđ)?", re.IGNORECASE
)

# Khuôn mốc thời gian (mục 3.2) — ngày tuyệt đối, neo tương đối rõ, thứ trong
# tuần (giả định TUẦN GẦN NHẤT). Mốc mơ hồ ("mấy hôm trước", "dạo này") CỐ Ý
# không khớp — slot coi như THIẾU, không suy diễn.
_THOI_GIAN = re.compile(
    r"\d{1,2}[/-]\d{1,2}([/-]\d{2,4})?"
    r"|ngày\s*\d{1,2}\s*tháng\s*\d{1,2}"
    r"|hôm nay|hom nay|hôm qua|hom qua|hôm kia|hom kia|hôm trước|hom truoc"
    r"|thứ\s*[2-7]\b|thu\s*[2-7]\b|t[2-7]\b"
    r"|thứ\s*(hai|ba|tư|tu|năm|nam|sáu|sau|bảy|bay)\b|thu\s*(hai|ba|tu|nam|sau|bay)\b",
    re.IGNORECASE,
)

# Khuôn mã (mục 3.3) — KHÔNG bắt buộc, chỉ để ghi nhận nếu có, KHÔNG gate
# routing. Mã giao dịch xác nhận khớp scripts/gen_dataset.py:135-138 (TXN +
# 8 số ngày + 6 số thứ tự = 14 số). Mã vé PHẢI khớp CẢ HAI hình dạng thật:
# `TCK-\d{5}` (scripts/gen_dataset.py:152-153, seed/demo data) VÀ
# `TCK-[0-9a-f]{12}` (src/tools/base.py::new_id, vé tạo THẬT lúc chat) — hai
# đường sinh ID lệch hình dạng nhau (đã đối chiếu runtime thật trước khi
# viết, không chỉ đọc gen_dataset.py như nháp gốc trích) — bỏ sót nhánh nào
# thì mã vé tạo trong chính phiên chat sẽ không bao giờ được nhận diện lại.
_MA_GD = re.compile(r"\bTXN\d{14}\b", re.IGNORECASE)
_MA_VE = re.compile(r"\bTCK-(?:\d{5}|[0-9a-f]{12})\b", re.IGNORECASE)


def _nhom_b(s: str) -> bool:
    co_so_huu = any(p.search(s) for p in _RE_SO_HUU)
    co_dong_tu = any(p.search(s) for p in _RE_DONG_TU_GD)
    if co_so_huu and co_dong_tu:
        return True
    # (ii) một chiều: neo "mất/bị mất/bị trừ" rồi mới tới khuôn số tiền,
    # trong cửa sổ ≤2 từ NGAY SAU neo — không xét chiều ngược.
    tu = s.split()
    for neo in _MAT_NEO:
        so_tu_neo = len(neo.split())
        for i, t in enumerate(tu):
            if " ".join(tu[i : i + so_tu_neo]) != neo:
                continue
            cua_so = " ".join(tu[i + so_tu_neo : i + so_tu_neo + 2])
            if _SO_TIEN.search(cua_so):
                return True
    return False


def boc_slot(cau: object) -> dict[str, bool]:
    """Bóc slot BẮT BUỘC (số tiền, thời gian) từ MỘT câu — KHÔNG ghép ngữ
    cảnh liên-lượt (mục 5 — ghép là việc của model, tầng này chỉ đọc một câu
    tại một thời điểm, đúng bất biến "phân loại theo TỪNG LƯỢT").

    Trả `{"so_tien": bool, "thoi_gian": bool}` — CHỈ presence, không trả giá
    trị đã bóc: mục 4 chỉ cần biết THIẾU CÁI GÌ để chọn đúng 1 trong 3 mẫu câu
    cố định, không cần điền lại giá trị (giá trị thật khách gõ vẫn nguyên vẹn
    trong lịch sử hội thoại, model đọc lại được ở lượt sau). KHÔNG BAO GIỜ
    ném — input không phải chuỗi thì coi như thiếu cả hai (an toàn, đi hỏi
    hoặc đi day_du tuỳ nơi gọi, không đoán bừa)."""
    if not isinstance(cau, str):
        return {"so_tien": False, "thoi_gian": False}
    s = _chuan_hoa(cau)
    return {"so_tien": bool(_SO_TIEN.search(s)), "thoi_gian": bool(_THOI_GIAN.search(s))}


# Bốn mẫu câu hỏi cố định (mục 4) — HẰNG SỐ, KHÔNG nhờ model sinh, cùng
# nguyên tắc TRA_LOI_NHE. Một tin gộp khi thiếu ≥2 slot (không tách hai dòng
# — cùng tinh thần R1). Câu "thiếu cả hai" kèm đường đi 3 bước tìm mã, khớp
# R2 (1A), tái dùng một chỗ, không lặp logic.
HOI_THIEU_CA_HAI = (
    "Dạ bạn cho mình xin khoảng thời gian giao dịch (hôm nay, hôm qua, hay ngày cụ thể) và số "
    "tiền giúp mình nhé — nếu có mã giao dịch thì cho mình xin luôn, không có cũng không sao ạ, "
    "bạn có thể vào mục Lịch sử giao dịch, bấm vào đúng giao dịch đó là thấy mã ạ."
)
HOI_THIEU_SO_TIEN = "Dạ bạn cho mình xin thêm số tiền giao dịch giúp mình nhé."
HOI_THIEU_THOI_GIAN = (
    "Dạ bạn cho mình xin khoảng thời gian giao dịch giúp mình — hôm nay, hôm qua, hay ngày cụ thể "
    "ạ."
)

# Băm của CHÍNH FILE NÀY, tính lúc import. KHÔNG gõ tay.
#
# Bản đầu tôi gõ cứng `"0885bab00a04"` — băm của một file NHÁP ở nơi khác. Đúng
# lúc viết, sai ngay khi một trong hai file đổi. Và tester vừa trả giá cho đúng
# chuyện đó: họ chấm 15/20 trên `1edd51dff555` rồi chạy cổng trên
# `0885bab00a04` mà không có gì báo — "luật đổi dưới chân tôi giữa hai lần đo".
#
# Một băm tự khai thì không thể lệch với thứ nó định danh.
CACH_BAM_LUAT = "md5-toan-file-12"
BAM_LUAT = hashlib.md5(Path(__file__).read_bytes()).hexdigest()[:12]


def _chuan_hoa(s: str) -> str:
    return _DAU_CAU.sub(" ", unicodedata.normalize("NFC", s).lower().strip())


def phan_luong(cau: object) -> tuple[str, str]:
    """Trả `(duong, ly_do)`. **KHÔNG BAO GIỜ ném.** Mọi bất thường -> `day_du`.

    Nhận `object` chứ không phải `str`: tester bắt được `phan_luong(12345)` ném
    `AttributeError` (`int` không có `.strip()`). Nghe hiếm, nhưng ở tầng hàm
    này cắm vào thì không hiếm — `{"message": 12345}` là JSON hợp lệ và tầng
    dựng request chưa chắc ép kiểu.

    Vì sao bắt TẤT CẢ ngoại lệ chứ không chỉ ép kiểu: hợp đồng của lớp này là
    *"bất kỳ ngoại lệ nào ⟹ lượt đó đi ĐẦY ĐỦ, không chặn khách"*. Nếu hàm ném
    thì hành vi phụ thuộc vào việc NGƯỜI GỌI có bắt hay không — mà đó đúng là
    thứ hợp đồng này tồn tại để không phải phụ thuộc. Một cổng an toàn không
    được để cách gọi nó quyết định nó có an toàn hay không.

    FAIL-VISIBLE: hướng sai là chiều đắt-tiền-nhưng-vô-hại (tốn token, không ai
    bị bỏ rơi), nên nuốt lỗi ở đây là đúng — nhưng nuốt IM LẶNG thì không.
    """
    try:
        return _phan_luong(cau)
    except Exception as e:  # noqa: BLE001 — xem docstring
        _logger.error(
            "phan_luong_nem_loi",
            extra={"lop_loi": type(e).__name__, "kieu_dau_vao": type(cau).__name__,
                   "hau_qua": "luot nay di duong DAY DU (huong an toan)"},
        )
        return DUONG_DAY_DU, f"lớp phân loại ném {type(e).__name__} — đi đường an toàn"


def _phan_luong(cau: object) -> tuple[str, str]:
    if not isinstance(cau, str):
        return DUONG_DAY_DU, f"đầu vào không phải chuỗi ({type(cau).__name__})"
    if not cau or not cau.strip():
        return DUONG_DAY_DU, "câu rỗng — không khẳng định được gì"

    s = _chuan_hoa(cau)

    if _CO_CHU_SO.search(s):
        # 1B — NHÓM A (có số, ĐÃ khớp ở nhánh này) VÀ NHÓM B (mục docstring
        # trên `_nhom_b`) ĐÒI ĐỒNG THỜI, không đòi một trong hai: danh từ
        # giao dịch một mình ("phí chuyển tiền") khớp cả câu chính sách lẫn
        # khiếu nại thật — tách hai loại là việc của sở-hữu-cá-nhân + động
        # từ ĐÃ XẢY RA, không phải việc riêng của động từ.
        if _nhom_b(s) and not all(boc_slot(cau).values()):
            return DUONG_THU_SLOT, "có số + dấu hiệu sở hữu/giao dịch cá nhân, thiếu slot bắt buộc"
        return DUONG_DAY_DU, "có chữ số (tiền/mã GD/SĐT/ngày đều mang số)"

    con = s
    for c in _CUM:
        con = con.replace(c, " ")
    la = [t for t in con.split() if t and t not in XA_GIAO]

    if la:
        return DUONG_DAY_DU, f"token ngoài tập xã giao: {la[:3]}"
    if not s.strip():
        return DUONG_DAY_DU, "sau chuẩn hoá không còn gì — không khẳng định được"

    return DUONG_NHE, "mọi token thuộc tập xã giao đóng"
