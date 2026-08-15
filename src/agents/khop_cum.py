"""Khớp CỤM tiếng Việt CHO PHÉP CHÈN HƯ TỪ — sửa CẢ MỘT LỚP LỖI, không vá từng ca.

Ba lần cùng một họ lỗi trước khi có file này (security 2fc55b0 gọi tên nó ở lần
thứ ba, và đúng là một họ):

    F-24  mẫu injection cho đúng MỘT từ bổ nghĩa
          -> "ignore ALL PREVIOUS instructions", câu injection phổ biến NHẤT, lọt sạch
    F-27  O1 đòi có đúng chữ "OTP"
          -> "sếp duyệt phải xin mã riêng, hết hạn sau 10 phút" lọt, dù lộ đúng
             con số cấu hình RESOLUTION_APPROVAL_OTP_FRESH_MINUTES
    O2    mỏ neo đòi cụm LIỀN KỀ
          -> "mình cũng KHÔNG ĐƯỢC kết luận gian lận" đếm 0, dù đúng ý mỏ neo

Cùng một hình dạng: **mẫu bắt được cách nói TA NGHĨ RA, trượt cách nói NGƯỜI TA
NÓI THẬT.** Và điểm quan trọng nhất, thứ làm nó thành lỗi lớp chứ không phải ba
lỗi lẻ: chèn hư từ giữa các thành phần là **ngữ pháp tiếng Việt bình thường**,
không phải kỹ xảo né tránh. "không kết luận" -> "không ĐƯỢC kết luận" -> "cũng
KHÔNG BAO GIỜ kết luận". Người viết bình thường chèn những chữ này một cách tự
nhiên. Nên mẫu đòi liền kề sai ngay ở **ca thường**, chứ không riêng ca tấn công
— nó vừa bỏ sót kẻ tấn công, vừa đo lệch chính khách hàng thật.

TÍNH CHẤT THIẾT KẾ — THUẦN CỘNG, chứng minh được chứ không phải hy vọng:
với 0 hư từ, `_GAP` rút về `\\s*`, tức mẫu mới khớp được MỌI thứ mẫu cũ (so chuỗi
con với đúng một dấu cách) khớp, cộng thêm biến thể chèn hư từ và biến thể dính
liền. Hệ quả để đọc đúng khi review: Luật 18 **không thể làm sót thêm**, nhưng
**có thể chặn thêm** — nên mọi nơi áp nó vào đường CHẶN phải kèm số ca âm tính.

CỐ Ý ĐỨNG NGOÀI: nhóm O4 (`_O4_DONG_TU/_O4_TIEN/_O4_HUONG_KHACH`). O4 khớp theo
ranh giới từ CÓ THỨ TỰ và là nhóm từng chặn nhầm nhiều nhất — 4/5 ca chặn nhầm
còn lại của đợt trước đều do đúng một chữ ("hoan" nằm trong "khoang"). Nới ở đó
là nới đúng chỗ mỏng nhất. Đây là quyết định, không phải bỏ quên.
"""
from __future__ import annotations

import re

# Hư từ được phép chèn — viết KHÔNG DẤU vì mọi nơi dùng đều so trên chuỗi đã bỏ
# dấu. Danh sách CỐ Ý NGẮN và chỉ gồm hư từ (từ chức năng): một dương tính giả
# đòi hỏi các từ NỘI DUNG của cụm xuất hiện đúng thứ tự, chỉ cách nhau bằng
# những chữ này — mà như vậy thì câu đã mang đúng nghĩa của cụm rồi.
#
# KHÔNG thêm từ nội dung vào đây. Riêng "hoan"/"toan" ("hoàn toàn") đã bị loại
# có chủ đích: "hoan" là token TIỀN của O4, cho nó làm hư từ là mở một đường bắc
# cầu giữa hai vế không liên quan.
TU_DEM = (
    "duoc", "phai", "se", "cung", "nen", "can", "luon", "van",
    "bao", "gio", "he", "the", "tuyet", "doi", "da", "dang",
)
# HỌ THỨ HAI — lượng từ / định ngữ. Tách khỏi hư từ vì chúng chèn vào chỗ khác
# ("bỏ qua TOÀN BỘ ràng buộc" chứ không phải "không ĐƯỢC kết luận"), nhưng cùng
# một lỗi lớp: F-24 đã phải liệt kê tay `(moi |tat ca |cac |nhung |truoc do |o
# tren )*` — và **thiếu "toàn bộ"**, nên "bỏ qua toàn bộ hướng dẫn" KHÔNG khớp
# ở bản 5f643f71. Đúng minh hoạ vì sao liệt kê tay thua: danh sách nào cũng
# thiếu đúng cái người ta sắp gõ.
TU_DINH_NGU = (
    "moi", "tat", "ca", "toan", "bo", "cac", "nhung", "truoc", "do",
    "o", "tren", "phia", "ben", "het", "sach",
)
# Trần 4 token giữa hai thành phần: đủ cho "cũng không bao giờ" (3) và
# "tất cả các" / "toàn bộ các" (3); cao hơn nữa thì hai thành phần đã xa nhau
# tới mức không còn là một cụm.
SO_TU_DEM_TOI_DA = 4

# `\s*` chứ không `\s+`: chuỗi dính liền ("bo qua" -> "boqua") là đúng thứ lượt
# so thứ hai của `_khop_mau` (customer_tools) sinh ra để bắt, và ở đó mẫu bị
# `.replace(" ", "")` nên mọi dấu cách LITERAL biến mất. `_GAP` không chứa dấu
# cách literal nào -> nó sống sót qua phép replace đó và vẫn khớp đúng.
GAP = (
    r"\s*(?:(?:" + "|".join(TU_DEM + TU_DINH_NGU) + r")\s*){0,"
    + str(SO_TU_DEM_TOI_DA) + r"}"
)


def mau_cum(cum: str) -> re.Pattern[str]:
    """Một CỤM (các từ cách nhau bằng dấu cách) -> regex cho phép chèn hư từ.

    Dùng cho danh sách cụm THUẦN VĂN BẢN. Với regex viết tay có nhóm/lựa chọn,
    đừng gọi hàm này — hãy chèn thẳng `GAP` vào đúng chỗ nối trong mẫu, vì thay
    mọi dấu cách một cách máy móc sẽ đụng cả dấu cách nằm trong nhóm lựa chọn.
    """
    return re.compile(GAP.join(re.escape(t) for t in cum.split()))


def cum(*cac_cum: str) -> tuple[re.Pattern[str], ...]:
    return tuple(mau_cum(c) for c in cac_cum)


def khop_bat_ky(mau: tuple[re.Pattern[str], ...], text: str) -> bool:
    return any(m.search(text) for m in mau)
