"""Mã hoá field nhạy cảm khi lưu (encryption at rest) — SQLite là 1 file
đĩa thô, ai đọc được file là đọc được hết nếu không mã hoá. `EncryptedString`
mã hoá TRONG SUỐT ở tầng ORM: code gọi model vẫn đọc/ghi chuỗi thường như
bình thường (`bank_account.account_no == "0123456789"`), SQLAlchemy tự mã
hoá lúc INSERT/UPDATE và tự giải mã lúc SELECT — không phải sửa bất kỳ chỗ
nào khác (tools/masking.py, seed_db.py, tests) đang dùng field này.

Dùng Fernet (AES128-CBC + HMAC, thư viện `cryptography`) — đối xứng, đủ cho
bài toán "file DB bị đọc trộm thì vẫn không đọc được nội dung", không phải
mã hoá tìm-kiếm-được (không cần WHERE account_no = ... nên không cần
deterministic encryption đánh đổi bảo mật yếu hơn)."""
from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import String, Text
from sqlalchemy.types import TypeDecorator

from src.config import FIELD_ENCRYPTION_KEY

_fernet = Fernet(FIELD_ENCRYPTION_KEY.encode())


class EncryptedString(TypeDecorator):
    """Cột String mã hoá trong suốt. Đổi FIELD_ENCRYPTION_KEY sau khi đã có
    dữ liệu -> mất khả năng đọc dữ liệu cũ, không có cách khôi phục."""

    impl = String
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect) -> str | None:
        if value is None:
            return None
        return _fernet.encrypt(value.encode()).decode()

    def process_result_value(self, value: str | None, dialect) -> str | None:
        if value is None:
            return None
        try:
            return _fernet.decrypt(value.encode()).decode()
        except InvalidToken:
            # Dữ liệu cũ nạp trước khi bật mã hoá (plaintext) — vẫn đọc được
            # nguyên bản thay vì lỗi cứng, để không chặn migrate dần dữ liệu cũ.
            return value


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
        if value is None:
            return None
        try:
            return _fernet.decrypt(value.encode()).decode()
        except InvalidToken:
            return value
