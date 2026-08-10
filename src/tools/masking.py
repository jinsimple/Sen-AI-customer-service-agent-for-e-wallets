"""BR-06 — masking PDPA cho thông tin bên thứ ba.

Nguyên tắc (BR-07): masking chỉ xảy ra ở TẦNG NÀY (tool/API). DB
(bank_accounts, users...) luôn lưu bản đầy đủ. Không bao giờ lưu sẵn bản
đã che vào DB — nếu làm vậy sẽ không test được logic masking (Data Brief
§4.2).
"""
from __future__ import annotations

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
