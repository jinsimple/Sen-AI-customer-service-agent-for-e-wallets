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

# Tên tín hiệu Redis (thread_signals.py) đánh dấu "đã hỏi slot lần nào chưa"
# trong hội thoại này — mục 5+6 thiết kế 1B: cổng chỉ được bắn TỐI ĐA MỘT
# LẦN mỗi hội thoại, đọc/ghi ở TẦNG GỌI (graph.py), không phải ở đây —
# phan_luong.py là hàm THUẦN (không side-effect), đúng nguyên tắc "0 trạng
# thái" xuyên suốt module này.
TEN_TIN_HIEU_1B = "1b_da_hoi_slot"

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
# NHÓM B — (i) SỞ HỮU/CÁ NHÂN + ĐỘNG TỪ GIAO DỊCH (đã xảy ra) + TÍN HIỆU
# KHIẾU NẠI TỐI THIỂU (thêm 24/08, Review bắt oan "tôi chuyển khoản thì phí
# bao nhiêu" — sở hữu+động từ không đủ, câu hỏi chính sách cũng khớp), HOẶC
# (ii) "mất"/"bị mất"/"bị trừ" đứng NGAY TRƯỚC một khuôn số tiền (một chiều
# — PO-agent đính chính 24/08: hai chiều sẽ bắt oan "...20k thì mất phí
# gì?", vì "20k" chỉ cách "mất" một từ theo chiều ngược).
_SO_HUU = ("tôi", "toi", "của tôi", "cua toi", "mình", "minh",
           "tài khoản tôi", "tk tôi", "bên tôi", "ben toi")
_DONG_TU_GD = ("chuyển", "chuyen", "bị trừ", "bi tru", "trừ tiền", "tru tien",
               "nhận", "nhan", "gửi", "gui", "rút", "rut", "nạp", "nap",
               "thanh toán", "thanh toan")
_MAT_NEO = ("mất", "mat", "bị mất", "bi mat", "bị trừ", "bi tru")

# 🔴 Review bắt oan 24/08 (chạy phan_luong() thật, không phải đọc tĩnh):
# "tôi chuyển khoản thì phí bao nhiêu vậy" / "tôi cần rút tiền, thủ tục thế
# nào" — CÓ sở hữu+động từ giao dịch nhưng là câu hỏi CHÍNH SÁCH/THỦ TỤC,
# không phải khiếu nại. Đặc tả PO duyệt: "câu chính sách tuyệt đối không
# kích cổng". Sửa bằng SIẾT ĐIỀU KIỆN VÀO (thêm tín hiệu khiếu nại tối
# thiểu bắt buộc), KHÔNG liệt kê từ ngoại lệ (phí/thủ tục/quy định...) —
# danh sách loại trừ luôn thiếu một chữ, điều kiện vào chặt thì bỏ sót
# đúng hướng đã chốt (thà bỏ sót còn hơn bắt oan).
# "sao"/"mất" CỐ Ý KHÔNG có mặt dù ví dụ NEO cũ ("sao mất tiền vậy") dùng
# chúng — [ĐO] Tester thêm ca sau bản vá đầu: "...thì làm sao" (thủ tục,
# không phải khiếu nại — "sao" khớp bừa trong "làm sao"/"thế nào", cụm hỏi
# trung tính rất phổ biến) và "...thì mất bao lâu" (hỏi THỜI LƯỢNG, "mất"
# nghĩa "tốn" chứ không phải "mất tiền") đều bị bắt oan khi hai từ này còn
# trong danh sách. "mất tiền" thật vẫn được NHÓM B(ii) bắt riêng (mất kề
# ngay một khuôn số tiền) — không mất khả năng nhận diện, chỉ bớt mơ hồ.
_TIN_HIEU_KHIEU_NAI = ("bị", "bi", "nhầm", "nham", "lỗi", "loi",
                       "chưa nhận", "chua nhan", "không nhận", "khong nhan",
                       "chưa thấy", "chua thay", "không thấy", "khong thay",
                       "chưa tới", "chua toi", "chưa về", "chua ve")

# PO-agent bắt 24/08, tự chạy cổng trên HEAD: "Tôi lo quá, chuyển nhầm tiền
# học phí của con cho người lạ rồi, giúp tôi với." — ca nặng nhất cổng có
# thể gặp. Cổng 0 token không có khả năng xoa dịu, trong khi prompt.py:21
# BẮT BUỘC câu đầu tiên phải xoa dịu trước khi nêu kết quả tra — cổng tất
# định đi VÒNG QUA đúng luật đó. Có tín hiệu cảm xúc mạnh ⟹ ĐI day_du, để
# LLM xử lý (nó có khả năng xoa dịu, cổng tất định thì không) — cùng tinh
# thần "thà bỏ sót còn hơn bắt oan", chỉ khác trục (cảm xúc thay vì chính
# sách). Không đặt ngưỡng "gần đúng" (vd chỉ "lo"/"sợ" đơn lẻ, dễ khớp bừa
# trong từ khác) — dùng cụm đủ dài để KHÔNG mơ hồ.
_TIN_HIEU_CAM_XUC_MANH = ("lo quá", "lo qua", "hoảng", "hoang", "sợ quá", "so qua",
                          "gấp lắm", "gap lam", "khẩn cấp", "khan cap",
                          "giúp tôi với", "giup toi voi", "giúp em với", "giup em voi",
                          "giúp mình với", "giup minh voi", "làm sao bây giờ", "lam sao bay gio",
                          "cứu tôi", "cuu toi", "cứu với", "cuu voi")

_re_word = lambda tu: re.compile(r"\b" + re.escape(tu) + r"\b")  # noqa: E731
_RE_SO_HUU = [_re_word(t) for t in _SO_HUU]
_RE_DONG_TU_GD = [_re_word(t) for t in _DONG_TU_GD]
_RE_TIN_HIEU_KHIEU_NAI = [_re_word(t) for t in _TIN_HIEU_KHIEU_NAI]
_RE_TIN_HIEU_CAM_XUC_MANH = [_re_word(t) for t in _TIN_HIEU_CAM_XUC_MANH]


def _co_cam_xuc_manh(s: str) -> bool:
    return any(p.search(s) for p in _RE_TIN_HIEU_CAM_XUC_MANH)


# Review bắt 24/08: "tôi bị trừ hai trăm bảy mươi nghìn" → thu_slot, cổng hỏi
# lại "cho mình xin số tiền" NGAY SAU KHI khách vừa nói số tiền — bằng CHỮ,
# không phải chữ số. `boc_slot()` (mục 3.1) CỐ Ý không bóc số viết chữ (khai
# rõ trong docstring, không phải lỗ mới) — nhưng hệ quả MỚI: cổng làm TỆ HƠN
# không có cổng, vì nó CHẶN TRƯỚC LLM (thứ đọc được "hai trăm bảy mươi
# nghìn") bằng một lớp lọc thô hơn.
#
# Vá RẺ — KHÔNG xây bộ bóc số viết chữ (không cần biết GIÁ TRỊ, chỉ cần biết
# "có thể khách đã nói số tiền" rồi NHƯỜNG LLM, đúng "thà bỏ sót còn hơn bắt
# oan"). Điều kiện: đơn vị (trăm/nghìn/ngàn/triệu/tỷ) đứng NGAY CẠNH một từ
# số (một/hai/.../mười/mươi/lẻ) — cùng bài học "cụm đủ dài": đơn vị PHẢI kề
# từ số, "nghìn" một mình trong "cảm ơn nghìn lần" không kích.
#
# 🔴 CHỐT 24/08, PO-agent — bản đầu CỐ Ý loại "nửa"/"rưỡi" để không lẫn với
# ca S4 corpus ("tôi chuyển nửa triệu hôm qua..." → thu_slot). PO-agent đọc
# lại S4 và lật: corpus TỰ KHAI đúng vấn đề trong `vi_sao` ("THIẾU dù khách
# ĐÃ NÓI") rồi ghi nhận nó là kỳ vọng ĐÚNG — một ca test ghi hành vi SAI
# thành chuẩn, sinh từ đặc tả 1B ("bóc bằng regex" không đọc được tiếng Việt
# viết chữ), không phải lỗi đọc code. Với khách, "nửa triệu" là số tiền họ
# VỪA NÓI RA — hỏi lại phiền y hệt "hai trăm bảy mươi nghìn". Nguyên tắc
# chốt: cổng tất định KHÔNG có nhiệm vụ phán xét con số khách đưa có đủ
# CHÍNH XÁC hay không (ước lượng/làm tròn/khoảng chừng là việc LLM làm tốt
# hơn) — chỉ trả lời "câu này có dấu hiệu khách đã nói số tiền không?", có
# thì NHƯỜNG. Tester đã sửa `ky_vong` của S4 + bổ sung ca cho corpus.
_TU_SO_CHU = ("một", "mot", "hai", "ba", "bốn", "bon", "năm", "nam", "sáu", "sau",
              "bảy", "bay", "tám", "tam", "chín", "chin", "mười", "mươi", "muoi", "lẻ", "le",
              "nửa", "nua", "rưỡi", "ruoi")
_DON_VI_SO_CHU = ("trăm", "tram", "nghìn", "nghin", "ngàn", "ngan", "triệu", "trieu", "tỷ", "ty")


def _co_so_viet_chu(s: str) -> bool:
    tu = s.split()
    for i, t in enumerate(tu):
        if t not in _DON_VI_SO_CHU:
            continue
        if (i > 0 and tu[i - 1] in _TU_SO_CHU) or (i + 1 < len(tu) and tu[i + 1] in _TU_SO_CHU):
            return True
    return False


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
    co_khieu_nai = any(p.search(s) for p in _RE_TIN_HIEU_KHIEU_NAI)
    if co_so_huu and co_dong_tu and co_khieu_nai:
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


def _chuan_hoa_nhe(s: str) -> str:
    """Chuẩn hoá NHẸ cho bóc slot — CHỈ NFC + hạ chữ thường, KHÔNG chạy
    `_DAU_CAU` (thứ `_chuan_hoa()` dùng cho khớp từ khoá NHÓM A/B).

    🔴 BUG THẬT tự bắt trước khi báo cáo: `_chuan_hoa()` thay `/`, `.`, `,`
    bằng khoảng trắng ("26/06" → "26 06", "340.000đ" → "340 000đ") — dùng nó
    cho `boc_slot()` làm khuôn ngày `\\d{1,2}[/-]\\d{1,2}` KHÔNG BAO GIỜ khớp
    được bất kỳ ngày dạng số nào, vì dấu `/` đã biến mất trước khi regex kịp
    thấy. [ĐO] chạy cổng eval/cong_phan_luong.py thật trên golden_set.jsonl:
    lỗi này một mình gây phần lớn trong 47/124 ca "âm gốc" báo sai `thu_slot`
    (số tiền có nhưng ngày báo THIẾU dù câu ghi rõ "Ngày 26/06"). Tách hàm
    nhẹ riêng cho bóc slot, giữ nguyên `_chuan_hoa()` cho khớp từ khoá (không
    đổi hành vi NHÓM A/B, chỉ đổi hành vi bóc slot)."""
    return unicodedata.normalize("NFC", s).lower().strip()


def co_ma_giao_dich_hoac_thoi_gian(cau: object) -> bool:
    """Bóc mã giao dịch/vé (`_MA_GD`/`_MA_VE`) HOẶC mốc thời gian (`boc_slot`)
    từ MỘT câu — dùng cho cổng thu-slot-SAU-KHI-xác-thực-OTP (graph.py,
    docs Lead 24/08 "nhap-cong-thu-slot-sau-otp"), KHÔNG dùng cho routing 1B
    (đó xét `so_tien`, khác slot mục tiêu). Tái dùng NGUYÊN regex đã có ở
    trên, không viết bản bóc thứ hai — lý do khác slot: 1B áp cho lượt ĐẦU
    TIÊN chưa biết gì (số tiền là neo mạnh nhất); cổng sau-OTP áp cho điểm
    khách đã mô tả đủ để gọi tool (đó là lý do tool chạy và bị OTP chặn),
    cái còn thiếu là thứ giúp tool THU HẸP xuống một kết quả — vai trò của
    mã/ngày, không phải số tiền."""
    if not isinstance(cau, str):
        return False
    s = _chuan_hoa_nhe(cau)
    return bool(_MA_GD.search(s) or _MA_VE.search(s)) or boc_slot(cau)["thoi_gian"]


def boc_slot(cau: object) -> dict[str, bool]:
    """Bóc slot BẮT BUỘC (số tiền, thời gian) từ MỘT câu — KHÔNG ghép ngữ
    cảnh liên-lượt (mục 5 — ghép là việc của model, tầng này chỉ đọc một câu
    tại một thời điểm, đúng bất biến "phân loại theo TỪNG LƯỢT").

    Trả `{"so_tien": bool, "thoi_gian": bool}` — CHỈ presence, không trả giá
    trị đã bóc (giá trị thật khách gõ vẫn nguyên vẹn trong lịch sử hội thoại,
    model đọc lại được ở lượt sau). `"so_tien"` là trường DUY NHẤT dùng để
    gate/chọn mẫu câu (R1 chốt 24/08 — cổng chỉ hỏi ĐÚNG MỘT thứ, xem
    HOI_THIEU_SO_TIEN); `"thoi_gian"` giữ lại vì vẫn là một slot có ý nghĩa
    bóc được, dù hiện KHÔNG có nơi gọi nào tiêu thụ nó — không xoá để tránh
    dựng lại đúng khuôn regex nếu một nhu cầu sau này cần lại. KHÔNG BAO GIỜ
    ném — input không phải chuỗi thì coi như thiếu cả hai (an toàn, đi hỏi
    hoặc đi day_du tuỳ nơi gọi, không đoán bừa)."""
    if not isinstance(cau, str):
        return {"so_tien": False, "thoi_gian": False}
    s = _chuan_hoa_nhe(cau)
    return {"so_tien": bool(_SO_TIEN.search(s)), "thoi_gian": bool(_THOI_GIAN.search(s))}


# 🔴 CHỐT 24/08 (PO-agent+Lead, sau khi chạy cổng thật lộ mâu thuẫn OR/AND —
# xem lịch sử trao đổi): SLOT BẮT BUỘC DUY NHẤT là SỐ TIỀN, không phải cặp
# (số tiền, thời gian). Căn cứ: L3 chuyên gia — "số tiền là neo tìm kiếm
# MẠNH NHẤT"; có số tiền là get_customer_history(amount=...) tra được NGAY,
# multiple_matches (nếu có) đã có đường xử lý riêng qua LLM (hỏi lại đúng
# ngữ cảnh ứng viên) — hỏi thời gian TRƯỚC, tất định, là hỏi một thứ có thể
# không cần. Thời gian vẫn BÓC nếu có (đi kèm reply cho model đọc), nhưng
# KHÔNG BAO GIỜ một mình là lý do chặn/hỏi. Hệ quả: mẫu "chỉ thiếu thời
# gian" bị XOÁ — không nhánh nào còn dùng tới.
#
# 🔴 CHỐT 24/08, PO-agent — R1 (1A, đặc tả chuyên gia CSKH, hành vi ĐO ĐƯỢC):
# "reply khi thiếu ≥2 slot chỉ chứa MỘT yêu cầu thông tin". `HOI_THIEU_CA_HAI`
# (bản trước) hỏi BA thứ trong một tin (thời gian + số tiền + mã giao dịch)
# — đọc "không tách hai dòng, cùng tinh thần R1" là đọc SAI: R1 đo được viết
# là "một tin MỘT yêu cầu", không phải "một tin, dù gộp mấy yêu cầu". Đặc tả
# nghiệp vụ thắng mục tiêu tiết kiệm token khi hai thứ va nhau.
#
# Và luật slot đã chốt (số tiền là slot BẮT BUỘC DUY NHẤT, thời gian không
# bao giờ một mình là lý do hỏi) làm mâu thuẫn tự giải: cổng CHỈ CÓ MỘT lý
# do để hỏi — thiếu số tiền — nên chỉ cần MỘT mẫu câu, hỏi ĐÚNG MỘT thứ.
# Mã giao dịch/thời gian để đường LLM hỏi tiếp theo R1 ở lượt sau nếu cần.
#
# Đánh đổi CÓ CHỦ, không phải sơ ý: hỏi một thứ có thể tốn thêm một lượt so
# với gộp ba — chấp nhận, vì R1 đến từ nghiệp vụ chuyên gia thật.
HOI_THIEU_SO_TIEN = "Dạ bạn cho mình xin thêm số tiền giao dịch giúp mình nhé."

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

    # 1B — 🔴 LỆCH SO VỚI NHÁP GỐC, ĐÃ BÁO PO-agent/Lead trước khi land: nháp
    # đặt NHÓM B (dòng dưới) PHÍA SAU cổng "có chữ số" (_CO_CHU_SO), với lý do
    # "câu không số đã đi day_du từ nhánh có sẵn, không cần luật mới". Nhưng
    # chính ca mẫu PO-agent dùng làm kịch bản nghiệm thu — "tôi bị trừ tiền"
    # — KHÔNG có chữ số nào cả (khách chưa nói số tiền, đúng lúc cần hỏi số
    # tiền nhất). Đặt NHÓM B sau cổng số sẽ làm chính ca mẫu đó KHÔNG BAO GIỜ
    # kích được cổng — mâu thuẫn với kịch bản nghiệm thu bằng chính ví dụ hộ
    # tống nó. Kiểm NHÓM B TRƯỚC, không điều kiện theo có-số-hay-không; slot
    # số tiền vẫn tự nhiên bắt được "chưa nói số nào" (boc_slot trả so_tien=
    # False), nên vẫn hỏi lại đúng chỗ thiếu — không cần chữ số để BẮT ĐẦU
    # hỏi, chỉ cần nó để BÓC được nếu khách đã lỡ nói.
    if _nhom_b(s):
        # 🔴 CHỐT 24/08 (PO-agent+Lead): SLOT BẮT BUỘC DUY NHẤT là SỐ TIỀN —
        # không phải cặp (số tiền, thời gian). Căn cứ: L3 chuyên gia "số tiền
        # là neo tìm kiếm MẠNH NHẤT"; có số tiền là get_customer_history
        # (amount=...) tra được ngay, multiple_matches (nếu có) đã có đường
        # xử lý riêng qua LLM đúng ngữ cảnh ứng viên — hỏi thời gian TRƯỚC,
        # tất định, là hỏi một thứ có thể không cần, phiền khách miễn phí.
        # [ĐO] 124 câu golden_set: cả 36 câu từng vỡ dưới luật "thiếu MỘT
        # TRONG HAI" đều so_tien=True — chúng qua được nhờ ĐÚNG CÁI NEO này,
        # không phải vì "giàu thông tin" (mệnh đề độ dài đội lốt, đã cân
        # nhắc và BÁC — phan_luong.py cấm mệnh đề độ dài từ trước 1B).
        #
        # Mã giao dịch (TXN...) đã có ⟹ đè slot số tiền, luôn đi day_du — mã
        # định danh CHÍNH XÁC một giao dịch, đặc hiệu hơn số tiền.
        #
        # Hệ quả: mọi câu kích NHÓM B(ii) ("mất"/"bị mất"/"bị trừ" kề số
        # tiền) LUÔN có so_tien=True theo đúng định nghĩa của B(ii) ⟹ B(ii)
        # KHÔNG BAO GIỜ tự sinh ra `thu_slot` — nó chỉ còn là tầng NHẬN DIỆN
        # (vẫn ĐẠT, Tester canh riêng), không phải tầng QUYẾT ĐỊNH slot.
        # B(i) (vd "tôi bị trừ tiền" — không có số tiền nào cả) mới là nguồn
        # thu_slot thật sự.
        if (
            not _MA_GD.search(s)
            and not boc_slot(cau)["so_tien"]
            and not _co_cam_xuc_manh(s)
            and not _co_so_viet_chu(s)
        ):
            return DUONG_THU_SLOT, "dấu hiệu sở hữu/giao dịch cá nhân, thiếu số tiền"
        # Có tín hiệu cảm xúc mạnh (đo được ở s) rơi xuống nhánh dưới — nếu
        # không có chữ số thì đi tiếp qua nhánh xã-giao (vẫn day_du vì có
        # token ngoài tập, không xã giao thuần), không quay lại thu_slot.
        # Có số tiền (hoặc có mã) ⟹ rơi xuống nhánh dưới, luôn khớp
        # _CO_CHU_SO (số tiền/mã đều mang chữ số), đi day_du bình thường.

    if _CO_CHU_SO.search(s):
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
