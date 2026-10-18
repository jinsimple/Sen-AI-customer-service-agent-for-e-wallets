"""BR-06 — PDPA masking of third-party information.

Principle (BR-07): masking happens ONLY at THIS LAYER (tool/API). The DB
(bank_accounts, users...) always stores the full version. Never pre-store a masked copy in
the DB — doing so would make the masking logic untestable (Data Brief §4.2).
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
    """`Trần Hữu Trang` -> `T. H. Trang` (only the initial of each word, except the last)."""
    if not full_name:
        return full_name
    parts = full_name.split()
    if len(parts) <= 1:
        return full_name
    masked_head = [f"{p[0]}." for p in parts[:-1]]
    return " ".join(masked_head + [parts[-1]])


def mask_account_no(account_no: str | None) -> str | None:
    """Show the last 4 digits, mask the rest — `88000000000001` -> `**********0001`."""
    if not account_no:
        return account_no
    if len(account_no) <= BANK_ACCOUNT_MASK_VISIBLE_SUFFIX:
        return "*" * len(account_no)
    return "*" * (len(account_no) - BANK_ACCOUNT_MASK_VISIBLE_SUFFIX) + account_no[-BANK_ACCOUNT_MASK_VISIBLE_SUFFIX:]


# ---------------------------------------------------------------------------
# M3 — mask PII in FREE TEXT at READ time (fixed by the real PO 25/08, ADR recorded at
# docs/nhat-ky/2026-08-25-P0-live-chat-PII-ba-muc-che-cho-PO-chon.md)
#
# 🔴 Why mask at READ time rather than on WRITE — there was a CONFLICT here between two of
# the project's own documents; the real PO adjudicated it, DO NOT REOPEN:
#   · the P0 test (tests/test_api/test_live_chat_pii_gap.py) describes "mask before storing"
#   · BR-07 at the top of this file FORBIDS pre-storing masked copies in the DB
#   ⟹ The real PO chose BR-07. The stored copy is KEPT IN FULL (encrypted at rest via
# EncryptedText).
# Deciding reason: the chat window has NO full copy anywhere else (unlike
# users/bank_accounts) ⟹ masking on write LOSES IT FOREVER, even if that exact sentence is
# later needed to adjudicate a complaint.
# ---------------------------------------------------------------------------

# Vietnamese phone numbers — same pattern as src/observability/pii.py::_VN_PHONE_REGEX,
# deliberately NOT cross-imported: pii.py serves logs/traces (replaces with [PHONE] entirely),
# this file serves DISPLAY to humans (keeps the last 4 digits so CSKH can cross-check).
_RE_PHONE = re.compile(r"(?<![\w-])(?:\+84|0)\d{9}(?!\d)")

# A currency unit IMMEDIATELY AFTER a digit run ⟹ that run is an AMOUNT, not an account
# number. The list is taken from eval/cong_phan_luong.py:334 (used in practice, not invented).
# Not using `_AMOUNT_RE` from triage.py: there the unit is OPTIONAL
# (`?`), so it matches bare digit runs too — useless as a distinguishing signal.
_RE_MONEY_SUFFIX = re.compile(
    r"\s*(nghìn|nghin|ngàn|ngan|triệu|trieu|đồng|dong|vnđ|vnd|tr|k|đ|d)(?![\w])",
    re.IGNORECASE,
)

# Long digit runs like account/ID-card numbers. Runs AFTER phone masking (the masked string
# contains `*`, so it no longer matches this pattern) ⟹ no double masking.
_RE_LONG_DIGIT_SEQUENCE = re.compile(r"(?<![\w-])\d{9,19}(?!\d)")


def che_pii_van_ban(text: str | None) -> str | None:
    """Mask phone/account numbers that the customer TYPED in free text, at DISPLAY time.

    `"…qua số 0987654321 nhé"`      -> `"…qua số 098***4321 nhé"`
    `"…tài khoản 88000000000001"`   -> `"…tài khoản **********0001"`
    `"…chuyển 1500000000 đồng"`     -> UNCHANGED (currency suffix ⟹ it's an AMOUNT)

    🔴 KNOWN LIMITATION, declared rather than hidden: a run of ≥9 digits written BARE, with
    no separators and NO currency suffix (`"Mình chuyển 1500000000 mà chưa thấy"`)
    is still masked. This is a DELIBERATE trade-off under the project's PII principle —
    better to mask an amount by mistake than to leak a real account number — and CSKH can
    still look up the amount from the transaction record via a tool. Don't loosen this
    pattern just to reduce false masking.
    """
    if not text:
        return text
    out = _RE_PHONE.sub(lambda m: mask_phone(m.group()) or m.group(), text)

    def _mask_unless_money(m: re.Match[str]) -> str:
        if _RE_MONEY_SUFFIX.match(out, m.end()):
            return m.group()
        return mask_account_no(m.group()) or m.group()

    return _RE_LONG_DIGIT_SEQUENCE.sub(_mask_unless_money, out)
