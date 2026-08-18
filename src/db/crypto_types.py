"""Mã hoá field nhạy cảm khi lưu (encryption at rest) — SQLite là 1 file
đĩa thô, ai đọc được file là đọc được hết nếu không mã hoá. `EncryptedString`
mã hoá TRONG SUỐT ở tầng ORM: code gọi model vẫn đọc/ghi chuỗi thường như
bình thường (`bank_account.account_no == "0123456789"`), SQLAlchemy tự mã
hoá lúc INSERT/UPDATE và tự giải mã lúc SELECT — không phải sửa bất kỳ chỗ
nào khác (tools/masking.py, seed_db.py, tests) đang dùng field này.

Dùng Fernet (AES128-CBC + HMAC, thư viện `cryptography`) — đối xứng, đủ cho
bài toán "file DB bị đọc trộm thì vẫn không đọc được nội dung", không phải
mã hoá tìm-kiếm-được (không cần WHERE account_no = ... nên không cần
deterministic encryption đánh đổi bảo mật yếu hơn).

BA TRẠNG THÁI, KHÔNG PHẢI HAI — vì sao file này được viết lại 18/08/2026
-----------------------------------------------------------------------
Bản trước bắt `InvalidToken` rồi `return value`, tức gộp **hai chuyện khác
hẳn nhau** vào một nhánh:

    (2) giá trị CHƯA BAO GIỜ được mã hoá   -> trả nguyên văn là ĐÚNG
    (3) giá trị mã hoá bằng KHOÁ KHÁC      -> trả nguyên văn là BỊA NỘI DUNG

Ở ca (3), thứ đi ra là **bản mã** `gAAAAABqg6vU…` mang kiểu `str`, đúng chỗ,
đúng kiểu, **không exception, không log, không cờ** — và nơi gọi không có cách
nào phân biệt nó với ca (2). [ĐO] dựng lại bằng hai khoá Fernet: khoá sai trả
đúng chuỗi bản mã, im lặng hoàn toàn.

Hệ quả thực tế, và đây là lý do việc này được xếp NGAY: **xoay
`FIELD_ENCRYPTION_KEY` sẽ không báo lỗi.** Mọi dòng đã mã hoá lặng lẽ biến
thành rác đọc-được-nhưng-vô-nghĩa. Cảnh báo "không được xoay khoá" trong
`docs/STATE.md` §1 nặng hơn nó đang được viết ra.

Và nó vi phạm **ràng buộc cứng 3** của hiến pháp ở tầng thấp nhất: *"không tra
được → nói rõ là không tra được"*. Hệ thống đang KHÔNG nói; nó đưa ra một chuỗi
trông như nội dung khách.

⚠️ Luật H, dạng mạnh nhất đội gặp: các ca trước, nhánh lỗi **in ra kết luận**
thay vì triệu chứng. Ca này nhánh lỗi **không in gì cả** — nó **giả trang thành
thành công**. Không có triệu chứng nào để ai đó đọc nhầm, vì không có triệu
chứng nào hết.

[ĐO] 18/08 trước khi vá, `psql` toàn bảng — cột `KHOÁ KHÁC` là số quyết định:

    cột                          giải mã ĐƯỢC   chưa mã hoá   KHOÁ KHÁC
    complaints.description_raw            23           738           0
    messages.content                     467             0           0
    bank_accounts.account_no             245             0           0
    policy_chunks.text                   378             0           0

⟹ Nhánh (3) **chưa bắn trên dữ liệu thật hôm nay**; bản vá không đổi một lượt
đọc nào, nó **lên đạn** cho lần xoay khoá. 738 dòng `description_raw` plaintext
(05/05→14/08, trước khi `EncryptedText` được gắn ~15/08) là việc RIÊNG: script
nạp lại thuộc `migrations/`, **chưa tồn tại**.
"""
from __future__ import annotations

import base64
import binascii
import logging

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import String, Text
from sqlalchemy.types import TypeDecorator

from src.config import FIELD_ENCRYPTION_KEY

_fernet = Fernet(FIELD_ENCRYPTION_KEY.encode())
_logger = logging.getLogger("fin05.db.crypto")

# Cấu trúc một token Fernet (spec Fernet, không phải quy ước của ta):
#   1 byte phiên bản (0x80) + 8 byte timestamp + 16 byte IV + N byte ciphertext
#   + 32 byte HMAC  ⟹ tối thiểu 57 byte kể cả khi ciphertext rỗng.
_FERNET_PHIEN_BAN = 0x80
_FERNET_TOI_THIEU_BYTE = 57


class KhongGiaiMaDuocError(RuntimeError):
    """Giá trị CÓ hình dạng token Fernet nhưng khoá hiện tại không mở được.

    Gần như luôn nghĩa là **`FIELD_ENCRYPTION_KEY` đã bị xoay** mà chưa chạy
    script mã hoá lại.

    VÌ SAO NÉM chứ không trả cờ / không trả `None`:
    · trả bản mã  = **bịa nội dung** (ràng buộc cứng 3) — đúng lỗi đang vá;
    · trả `None`  = lẫn với `NULL` hợp lệ, nơi gọi không phân biệt được;
    · trả cờ      = nơi gọi **quên đọc cờ** là quay về đúng trạng thái cũ.
    Chỉ ném mới là thứ nơi gọi không thể vô tình bỏ qua — cùng nếp fail-closed
    đã dùng cho `src/dau_ma_nguon.py` (`.bam_ma_nguon` rỗng ⟹ TỪ CHỐI khởi
    động).
    """


def _co_hinh_dang_fernet(value: str) -> bool:
    """Phân biệt "chưa mã hoá" với "mã hoá bằng khoá khác" — theo CẤU TRÚC.

    CỐ Ý KHÔNG dùng `value.startswith("gAAAAA")` dù phép ấy cho cùng kết quả
    trên dữ liệu hôm nay: tiền tố chuỗi là **trùng hợp của base64**, còn byte
    phiên bản là **spec**. Hai thứ đang bằng nhau và sẽ không mãi bằng nhau —
    và một phép kiểm đúng vì trùng hợp là phép kiểm sẽ hỏng trong im lặng.

    Fail-safe có HƯỚNG: mọi thứ không giải nổi base64 (văn bản tiếng Việt của
    khách, dấu cách, dấu tiếng Việt) trả `False` ⟹ rơi vào nhánh "chưa mã hoá"
    ⟹ **trả nguyên văn**, hành vi CŨ. Tức khi phép này sai, nó sai về phía
    **không đổi hành vi đang chạy**, không phải về phía ném lung tung.

    [ĐO] 738 dòng khiếu nại tiếng Việt thật: 738/738 vào đúng rổ, 0 lạc.
    """
    try:
        # `validate=True` BẮT BUỘC. Mặc định (`validate=False`) **âm thầm bỏ
        # qua** mọi ký tự ngoài bảng chữ cái base64 rồi giải phần còn lại — tức
        # một chuỗi tiếng Việt có dấu, có khoảng trắng vẫn có thể giải ra byte
        # và lọt vào nhánh "nghi sai khoá". Với `validate=True`, ký tự lạ ⟹ ném
        # ⟹ rơi đúng vào nhánh "chưa mã hoá".
        # (`b64decode(altchars=b"-_")` là đường DUY NHẤT nhận `validate`;
        # `urlsafe_b64decode` không có tham số đó. Hai hàm cùng bảng chữ cái.)
        raw = base64.b64decode(value.encode("ascii"), altchars=b"-_", validate=True)
    except (ValueError, binascii.Error, UnicodeEncodeError):
        # `UnicodeEncodeError`: chuỗi có ký tự ngoài ASCII (tiếng Việt có dấu)
        # ⟹ chắc chắn không phải token Fernet, khỏi cần giải base64.
        return False
    return len(raw) >= _FERNET_TOI_THIEU_BYTE and raw[0] == _FERNET_PHIEN_BAN


def _giai_ma(value: str | None, *, cot: str) -> str | None:
    """Giải mã một giá trị đọc từ DB. BA kết cục, không phải hai.

    `cot` chỉ để đi vào log — không có nó thì cảnh báo "còn dòng chưa mã hoá"
    không nói được **cột nào**, và người chạy script nạp lại không biết bắt đầu
    từ đâu.
    """
    if value is None:
        return None
    try:
        return _fernet.decrypt(value.encode()).decode()
    except InvalidToken:
        pass

    if _co_hinh_dang_fernet(value):
        # (3) Có hình dạng bản mã Fernet nhưng khoá hiện tại không mở được.
        # KHÔNG log nội dung/bản mã — bản mã là dữ liệu khách đã mã hoá, đẩy nó
        # vào log là gỡ đúng lớp bảo vệ vừa dựng.
        _logger.error(
            "giai_ma_that_bai_nghi_xoay_khoa",
            extra={"cot": cot, "do_dai": len(value)},
        )
        raise KhongGiaiMaDuocError(
            f"{cot}: giá trị có hình dạng token Fernet nhưng FIELD_ENCRYPTION_KEY "
            f"hiện tại không giải mã được — nghi khoá đã bị xoay mà chưa mã hoá lại. "
            f"KHÔNG trả bản mã ra ngoài như thể là nội dung."
        )

    # (2) Dữ liệu cũ nạp trước khi bật mã hoá (plaintext) — vẫn đọc được nguyên
    # bản để không chặn migrate dần. KHÁC bản trước ở chỗ: giờ nó ĐẾM ĐƯỢC.
    # Đây là điều kiện tiên quyết của bước nạp lại: không có số đếm thì script
    # nạp lại chạy xong không ai biết nó đã phủ hết chưa.
    _logger.warning(
        "doc_gia_tri_chua_ma_hoa",
        extra={"cot": cot, "do_dai": len(value)},
    )
    return value


class EncryptedString(TypeDecorator):
    """Cột String mã hoá trong suốt.

    Đổi `FIELD_ENCRYPTION_KEY` sau khi đã có dữ liệu ⟹ mất khả năng đọc dữ liệu
    cũ, không có cách khôi phục. Từ 18/08 việc đó **KÊU** (`KhongGiaiMaDuocError`)
    thay vì âm thầm trả bản mã — xem docstring đầu file.
    """

    impl = String
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect) -> str | None:
        if value is None:
            return None
        return _fernet.encrypt(value.encode()).decode()

    def process_result_value(self, value: str | None, dialect) -> str | None:
        return _giai_ma(value, cot="EncryptedString")


class EncryptedText(TypeDecorator):
    """Như EncryptedString nhưng impl=Text — dùng cho nội dung dài (đoạn tài
    liệu chính sách/FAQ đã chia nhỏ, src/rag/) thay vì giá trị ngắn cố định
    kiểu account_no. Cùng khoá/logic mã hoá — chỉ khác kiểu cột nền."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect) -> str | None:
        if value is None:
            return None
        return _fernet.encrypt(value.encode()).decode()

    def process_result_value(self, value: str | None, dialect) -> str | None:
        return _giai_ma(value, cot="EncryptedText")
