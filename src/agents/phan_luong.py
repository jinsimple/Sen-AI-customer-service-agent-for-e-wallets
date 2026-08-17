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

import re
import unicodedata

DUONG_NHE = "nhe"
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

BAM_LUAT = "0885bab00a04"  # md5-toan-file-12 của bản nháp đã chấm 124/124 bộ âm


def _chuan_hoa(s: str) -> str:
    return _DAU_CAU.sub(" ", unicodedata.normalize("NFC", s).lower().strip())


def phan_luong(cau: str) -> tuple[str, str]:
    """Trả `(duong, ly_do)`. Mọi nhánh không khẳng định được -> `day_du`."""
    if not cau or not cau.strip():
        return DUONG_DAY_DU, "câu rỗng — không khẳng định được gì"

    s = _chuan_hoa(cau)

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
