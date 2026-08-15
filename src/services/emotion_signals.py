"""Tín hiệu cảm xúc ES-xx — TẦNG SERVICE, luật tất định (ADR-022, PO ký 15/08).

CHƯA NỐI VÀO ĐƯỜNG NÓNG. File này chỉ tính tín hiệu; việc đưa `goi_y_handoff`
vào envelope và nâng ưu tiên ticket là bước riêng, làm sau khi tester xong lượt
đo nền (cần cặp trước/sau sạch).

Ba ràng buộc kế thừa từ ADR-022, nhắc lại vì chúng quyết định toàn bộ thiết kế:
  · KHÔNG gọi LLM. Không thêm một lượt nào vào đường nóng.
  · KHÔNG đi vào prompt. Agent không bao giờ NÓI ra rằng nó thấy khách đang bực
    — đó sẽ là agent khẳng định một kết luận tâm lý về một con người dựa trên bộ
    phân loại có thể sai (tinh thần ràng buộc cứng 3).
  · KHÔNG lưu nhãn. Chỉ bộ đếm số, ở Redis, có TTL (xem thread_signals.py).

CÁI BẪY LỚN NHẤT CỦA MIỀN NÀY — TỪ VỰNG NGHIỆP VỤ TRÙNG TỪ VỰNG GIẬN DỮ
----------------------------------------------------------------------
Đây là một agent xử lý KHIẾU NẠI GIAN LẬN. Câu "em bị lừa đảo", "bị mất tiền",
"bị trừ tiền oan" là MÔ TẢ VỤ VIỆC — chúng xuất hiện ở gần như mọi hội thoại
hợp lệ, kể cả khi khách hoàn toàn bình tĩnh. Nhét những từ đó vào từ điển giận
dữ thì ES-01 bật ở hầu hết case thật, và tín hiệu mất sạch ý nghĩa: một tín hiệu
luôn bật thì không phải tín hiệu.

Nên từ điển ở đây CỐ Ý chỉ gồm ngôn ngữ hướng vào DỊCH VỤ/NGƯỜI PHỤC VỤ ("làm
ăn kiểu gì", "vô trách nhiệm", "quá đáng"), không gồm ngôn ngữ mô tả SỰ VIỆC.
Đây đúng lớp lỗi mà bộ lọc injection hiện tại đang mắc theo chiều ngược lại —
mẫu `tu dong hoan tien` chặn luôn cả câu chính sách thật. Cùng một bài học: khi
từ vựng tấn công/giận dữ trùng từ vựng nghiệp vụ, danh sách từ phải chọn theo
ĐỐI TƯỢNG được nói tới, không theo chủ đề.
"""
from __future__ import annotations

import re
import unicodedata

from src.services import thread_signals

# Ngưỡng N của ES-01 — PO thật chốt 15/08 làm GIÁ TRỊ LÀM VIỆC, canh lại sau khi
# bộ đa-lượt của tester có số. Để ở đây (không rải rác trong logic) để lần chỉnh
# sau chỉ sửa một chỗ.
ES01_SO_LUOT_LIEN_TIEP = 3

ES01 = "ES-01"
ES02 = "ES-02"


def _bo_dau(text: str) -> str:
    """Cùng cách `_strip_diacritics` của customer_tools/fraud_engine — so khớp
    trên bản bỏ dấu để không phụ thuộc người gõ có dấu hay không. Bài học
    ADV-041: mẫu viết CÓ dấu thì câu gõ KHÔNG dấu lọt sạch."""
    text = text.lower().replace("đ", "d")
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


# Ngôn ngữ hướng vào DỊCH VỤ/NGƯỜI PHỤC VỤ. KHÔNG có "lua dao", "mat tien",
# "tru tien oan"... — đó là mô tả vụ việc, xem docstring.
_MAU_BUC_XUC = [
    r"lam an (kieu gi|nhu the nao|the nay)",
    r"vo trach nhiem",
    r"qua dang",
    r"khong the chap nhan",
    r"te (hai|that)|qua te|chan (that|qua)",
    r"(doi|cho) (gap|noi chuyen voi) (quan ly|nguoi co trach nhiem|cap tren)",
    r"bao nhieu lan (roi|nua)",
    r"(hoi|noi) may lan roi",
    r"lam mat thoi gian",
    r"khong ai (giai quyet|tra loi|xu ly)",
]

# ES-02 — khủng hoảng NGHIỆP VỤ. PO thật chốt: KHÔNG phủ tổn thương tâm lý.
# Nếu ai định thêm mẫu cho nhóm đó, dừng lại và đọc `khong_bao_gom` trong
# contracts/resolution-state-machine.yaml trước.
_MAU_KHUNG_HOANG = [
    r"(bo|xoa|go|khong dung) (vi|app|ung dung) (nay )?(nua|luon)",
    r"dong (tai khoan|vi)",
    r"chuyen sang (vi|app|ngan hang) khac",
    r"(se |sap )?kien",
    r"luat su",
    r"(bao|dang|len) (bao chi|bao|facebook|mang xa hoi|tiktok)",
    r"phan anh len (ngan hang nha nuoc|cong an|bao ve nguoi tieu dung)",
]

_RE_BUC_XUC = [re.compile(p) for p in _MAU_BUC_XUC]
_RE_KHUNG_HOANG = [re.compile(p) for p in _MAU_KHUNG_HOANG]

# DẤU HIỆU CƯỜNG ĐỘ (viết hoa cả câu, "!!!") — ĐÃ CÂN NHẮC VÀ BỎ Ở v1, ghi lại
# để phiên sau không tưởng là thiếu sót rồi thêm vào:
#   · Một mình chúng KHÔNG nói lên giận dữ. Rất nhiều người gõ hoa cả câu vì
#     thói quen bàn phím điện thoại, và người lớn tuổi hay dùng "!!!" như dấu
#     kết câu bình thường. Dùng làm tín hiệu độc lập là dán nhãn theo cách gõ.
#   · Đi KÈM mẫu trách móc thì cũng không thêm thông tin: mẫu đã đủ để tính
#     lượt đó là tiêu cực mạnh rồi, cường độ chỉ làm điều kiện chặt hơn mà
#     không rõ chặt như thế có đúng hơn không — mà "không rõ có đúng hơn không"
#     thì chưa đủ căn cứ để đưa vào một tín hiệu định tuyến.
# Nếu sau này bộ đa-lượt của tester cho thấy ES-01 bật quá sớm, cường độ là
# tham số đầu tiên nên thử — nhưng phải có SỐ trước, không thêm theo cảm tính.


def luot_co_buc_xuc(tin_nhan: str) -> bool:
    """Một LƯỢT có mang nhãn tiêu cực mạnh không. KHÔNG phải ES-01 —
    ES-01 cần ≥N lượt LIÊN TIẾP, xem `danh_gia_luot`."""
    if not tin_nhan:
        return False
    sach = _bo_dau(tin_nhan)
    return any(r.search(sach) for r in _RE_BUC_XUC)


def luot_co_khung_hoang(tin_nhan: str) -> bool:
    """ES-02 bật ngay trong MỘT lượt — doạ rời dịch vụ/kiện/đăng công khai
    không cần leo thang, nó đã là đỉnh."""
    if not tin_nhan:
        return False
    return any(r.search(_bo_dau(tin_nhan)) for r in _RE_KHUNG_HOANG)


def danh_gia_luot(tin_nhan: str, thread_id: str) -> set[str]:
    """Tính tín hiệu ES cho MỘT lượt của khách. Trả về tập mã đang bật.

    Đây là nơi ngữ nghĩa "LIÊN TIẾP" của ES-01 được thực thi: lượt KHÔNG bức xúc
    thì `dat_lai()` bộ đếm. Thiếu dòng đó, thứ đếm được sẽ là "tổng số lượt bực
    trong hội thoại" — khách bực rồi nguôi rồi bực lại vẫn chạm ngưỡng 3 trong
    khi họ không hề leo thang, và ES-01 mất đúng ý nghĩa của cái tên nó mang.

    KHÔNG raise trong mọi trường hợp: thread_signals đã fail-open, và hàm này
    nằm trên đường nóng của lượt chat.
    """
    dang_bat: set[str] = set()

    if luot_co_buc_xuc(tin_nhan):
        if thread_signals.tang(ES01, thread_id) >= ES01_SO_LUOT_LIEN_TIEP:
            dang_bat.add(ES01)
    else:
        thread_signals.dat_lai(ES01, thread_id)

    # ES-02 KHÔNG dùng bộ đếm: doạ rời dịch vụ/kiện/đăng công khai đã là đỉnh
    # ngay ở lượt đầu, không cần leo thang. Đếm nó là bắt khách phải doạ ba lần
    # mới được nghe.
    if luot_co_khung_hoang(tin_nhan):
        dang_bat.add(ES02)

    return dang_bat
