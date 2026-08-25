"""BR-06 — masking PDPA cho thông tin bên thứ ba.

Nguyên tắc (BR-07): masking chỉ xảy ra ở TẦNG NÀY (tool/API). DB
(bank_accounts, users...) luôn lưu bản đầy đủ. Không bao giờ lưu sẵn bản
đã che vào DB — nếu làm vậy sẽ không test được logic masking (Data Brief
§4.2).
"""
from __future__ import annotations

import re

from src.config import (
    BANK_ACCOUNT_MASK_VISIBLE_SUFFIX,
    PHONE_MASK_VISIBLE_PREFIX,
    PHONE_MASK_VISIBLE_SUFFIX,
)


def mask_phone(phone: str | None) -> str | None:
    """`0901234567` -> `090***4567`."""
    if not phone:
        return phone
    if len(phone) <= PHONE_MASK_VISIBLE_PREFIX + PHONE_MASK_VISIBLE_SUFFIX:
        return "*" * len(phone)
    prefix = phone[:PHONE_MASK_VISIBLE_PREFIX]
    suffix = phone[-PHONE_MASK_VISIBLE_SUFFIX:]
    return f"{prefix}***{suffix}"


def mask_full_name(full_name: str | None) -> str | None:
    """`Trần Hữu Trang` -> `T. H. Trang` (chỉ hiện chữ cái đầu mỗi từ, trừ từ cuối)."""
    if not full_name:
        return full_name
    parts = full_name.split()
    if len(parts) <= 1:
        return full_name
    masked_head = [f"{p[0]}." for p in parts[:-1]]
    return " ".join(masked_head + [parts[-1]])


def mask_account_no(account_no: str | None) -> str | None:
    """Hiện 4 số cuối, còn lại che — `88000000000001` -> `**********0001`."""
    if not account_no:
        return account_no
    if len(account_no) <= BANK_ACCOUNT_MASK_VISIBLE_SUFFIX:
        return "*" * len(account_no)
    return "*" * (len(account_no) - BANK_ACCOUNT_MASK_VISIBLE_SUFFIX) + account_no[-BANK_ACCOUNT_MASK_VISIBLE_SUFFIX:]


# ---------------------------------------------------------------------------
# M3 — che PII trong VĂN BẢN TỰ DO ở tầng ĐỌC (PO thật chốt 25/08, ADR ghi tại
# docs/nhat-ky/2026-08-25-P0-live-chat-PII-ba-muc-che-cho-PO-chon.md)
#
# 🔴 Vì sao che ở tầng ĐỌC chứ không phải lúc GHI — đây là chỗ đã có XUNG ĐỘT
# giữa hai văn bản của chính dự án, PO thật đã phân xử, ĐỪNG MỞ LẠI:
#   · test P0 (tests/test_api/test_live_chat_pii_gap.py) mô tả "che trước khi lưu"
#   · BR-07 ngay đầu tệp này CẤM lưu sẵn bản đã che vào DB
#   ⟹ PO thật chọn BR-07. Bản lưu GIỮ ĐỦ (đã mã hoá at-rest qua EncryptedText).
# Lý do quyết định: khung chat KHÔNG có bản đầy đủ ở đâu khác (khác hẳn
# users/bank_accounts) ⟹ che lúc ghi là MẤT VĨNH VIỄN, kể cả khi sau này cần
# đúng câu ấy để phân xử một khiếu nại.
# ---------------------------------------------------------------------------

# SĐT Việt Nam — cùng khuôn với src/observability/pii.py::_VN_PHONE_REGEX, cố ý
# KHÔNG import chéo: pii.py phục vụ log/trace (thay hẳn bằng [PHONE]), tệp này
# phục vụ HIỂN THỊ cho người (giữ 4 số cuối để CSKH đối chiếu được).
_RE_SDT = re.compile(r"(?<![\w-])(?:\+84|0)\d{9}(?!\d)")

# Đơn vị tiền tệ đứng NGAY SAU dãy số ⟹ dãy đó là SỐ TIỀN, không phải số tài
# khoản. Danh sách lấy từ eval/cong_phan_luong.py:334 (đã dùng thật, không tự
# nghĩ ra). Không dùng `_SO_TIEN` của phan_luong.py: ở đó đơn vị là TUỲ CHỌN
# (`?`) nên nó khớp cả dãy số trần — vô dụng làm dấu hiệu phân biệt.
_RE_DUOI_TIEN = re.compile(
    r"\s*(nghìn|nghin|ngàn|ngan|triệu|trieu|đồng|dong|vnđ|vnd|tr|k|đ|d)(?![\w])",
    re.IGNORECASE,
)

# Dãy số dài kiểu số tài khoản/CCCD. Chạy SAU khi đã che SĐT (chuỗi đã che có
# dấu `*` nên không còn khớp khuôn này) ⟹ không che chồng.
_RE_DAY_SO_DAI = re.compile(r"(?<![\w-])\d{9,19}(?!\d)")


def che_pii_van_ban(text: str | None) -> str | None:
    """Che SĐT/số tài khoản khách gõ TAY trong văn bản tự do, lúc HIỂN THỊ.

    `"…qua số 0987654321 nhé"`      -> `"…qua số 098***4321 nhé"`
    `"…tài khoản 88000000000001"`   -> `"…tài khoản **********0001"`
    `"…chuyển 1500000000 đồng"`     -> GIỮ NGUYÊN (có đuôi tiền tệ ⟹ là SỐ TIỀN)

    🔴 GIỚI HẠN ĐÃ BIẾT, khai ra thay vì giấu: dãy ≥9 chữ số viết TRẦN, không
    dấu phân cách và KHÔNG đuôi tiền tệ (`"Mình chuyển 1500000000 mà chưa thấy"`)
    vẫn bị che. Đây là đánh đổi CÓ CHỦ ĐÍCH theo nguyên tắc PII của dự án —
    che nhầm một số tiền còn hơn để lọt một số tài khoản thật — và CSKH vẫn
    tra được số tiền từ bản ghi giao dịch qua tool. Đừng nới khuôn này chỉ để
    giảm che nhầm.
    """
    if not text:
        return text
    out = _RE_SDT.sub(lambda m: mask_phone(m.group()) or m.group(), text)

    def _che_neu_khong_phai_tien(m: re.Match[str]) -> str:
        if _RE_DUOI_TIEN.match(out, m.end()):
            return m.group()
        return mask_account_no(m.group()) or m.group()

    return _RE_DAY_SO_DAI.sub(_che_neu_khong_phai_tien, out)
