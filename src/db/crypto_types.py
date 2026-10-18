"""Encryption at rest for sensitive fields — SQLite is a raw disk file; anyone who can read
the file can read everything unless it is encrypted. `EncryptedString` encrypts
TRANSPARENTLY at the ORM layer: code using the model still reads/writes plain strings
(`bank_account.account_no == "0123456789"`); SQLAlchemy encrypts on INSERT/UPDATE and
decrypts on SELECT — nothing else that uses these fields (tools/masking.py, seed_db.py,
tests) has to change.

Uses Fernet (AES128-CBC + HMAC, `cryptography` library) — symmetric, enough for the problem
"if the DB file is stolen the contents are still unreadable"; this is not searchable
encryption (we never need WHERE account_no = ..., so no need for deterministic encryption
and its weaker security trade-off).

THREE STATES, NOT TWO — why this file was rewritten on 18/08/2026
----------------------------------------------------------------
The previous version caught `InvalidToken` and then `return value`, i.e. it merged **two
completely different situations** into one branch:

    (2) a value that was NEVER encrypted       -> returning it verbatim is CORRECT
    (3) a value encrypted with a DIFFERENT KEY -> returning it verbatim FABRICATES CONTENT

In case (3), what comes out is the **ciphertext** `gAAAAABqg6vU…` typed as `str`, in the
right place, of the right type, **with no exception, no log, no flag** — and callers have no
way to tell it apart from case (2). [MEASURED] reproduced with two Fernet keys: the wrong
key returns exactly the ciphertext string, completely silently.

Practical consequence, and the reason this was prioritised IMMEDIATELY: **rotating
`FIELD_ENCRYPTION_KEY` would raise no error.** Every encrypted row would silently turn into
readable-but-meaningless garbage. The "never rotate the key" warning in
`docs/STATE.md` §1 is more serious than it is written.

And it violates **hard constraint 3** of the constitution at the lowest layer: *"if it
cannot be looked up → say clearly that it cannot be looked up"*. The system was NOT saying
so; it produced a string that looks like customer content.

⚠️ Rule H, in the strongest form the team has met: in earlier cases the error branch
**printed a conclusion** instead of a symptom. Here the error branch **prints nothing at
all** — it **masquerades as success**. There is no symptom for anyone to misread, because
there is no symptom at all.

[MEASURED] 18/08 before the fix, `psql` over full tables — the `OTHER KEY` column is the
deciding number:

    column                         decrypts OK   not encrypted   OTHER KEY
    complaints.description_raw            23           738           0
    messages.content                     467             0           0
    bank_accounts.account_no             245             0           0
    policy_chunks.text                   378             0           0

⟹ Branch (3) **has not fired on real data today**; the fix changes no read at all, it
**arms** the check for the next key rotation. The 738 plaintext `description_raw` rows
(05/05→14/08, before `EncryptedText` was attached ~15/08) are a SEPARATE job: a re-encryption
script belonging in `migrations/`, **which does not exist yet**.
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

# Structure of a Fernet token (Fernet spec, not our convention):
#   1 version byte (0x80) + 8-byte timestamp + 16-byte IV + N bytes of ciphertext
#   + 32-byte HMAC  ⟹ at least 57 bytes even when the ciphertext is empty.
_FERNET_VERSION = 0x80
_FERNET_MIN_BYTES = 57


class UndecryptableError(RuntimeError):
    """A value that HAS the shape of a Fernet token but cannot be opened with the current key.

    Almost always means **`FIELD_ENCRYPTION_KEY` was rotated** without running the
    re-encryption script.

    WHY RAISE rather than return a flag / return `None`:
    · return the ciphertext = **fabricated content** (hard constraint 3) — the very bug being fixed;
    · return `None`         = indistinguishable from a valid `NULL`;
    · return a flag         = a caller that **forgets to check the flag** is back to the old state.
    Only raising is something a caller cannot accidentally ignore — same fail-closed habit
    as `src/build_stamp.py` (empty `.source_hash` ⟹ REFUSE to start).
    """


def _looks_like_fernet(value: str) -> bool:
    """Distinguish "not encrypted" from "encrypted with another key" — by STRUCTURE.

    DELIBERATELY NOT using `value.startswith("gAAAAA")` even though it gives the same result
    on today's data: the string prefix is a **base64 coincidence**, whereas the version byte
    is **the spec**. The two are equal today and won't stay equal forever —
    and a check that is right by coincidence is a check that will break silently.

    Fail-safe with a DIRECTION: anything that doesn't decode as base64 (customers' Vietnamese
    text, spaces, Vietnamese diacritics) returns `False` ⟹ falls into the "not encrypted"
    branch ⟹ **returned verbatim**, the OLD behaviour. So when this check is wrong, it errs
    towards **not changing running behaviour**, not towards raising randomly.

    [MEASURED] 738 real Vietnamese complaint rows: 738/738 in the right bucket, 0 misplaced.
    """
    try:
        # `validate=True` is MANDATORY. The default (`validate=False`) **silently skips** every
        # character outside the base64 alphabet and decodes the rest — so a Vietnamese string with
        # diacritics and spaces could still decode into bytes and slip into the "suspected wrong
        # key"
        # branch. With `validate=True`, a foreign character ⟹ raises
        # ⟹ lands correctly in the "not encrypted" branch.
        # (`b64decode(altchars=b"-_")` is the ONLY path that accepts `validate`;
        # `urlsafe_b64decode` has no such parameter. Both use the same alphabet.)
        raw = base64.b64decode(value.encode("ascii"), altchars=b"-_", validate=True)
    except (ValueError, binascii.Error, UnicodeEncodeError):
        # `UnicodeEncodeError`: the string has non-ASCII characters (accented Vietnamese)
        # ⟹ certainly not a Fernet token, no need to decode base64.
        return False
    return len(raw) >= _FERNET_MIN_BYTES and raw[0] == _FERNET_VERSION


def _decrypt(value: str | None, *, column: str) -> str | None:
    """Decrypt a value read from the DB. THREE outcomes, not two.

    `column` is only for the log — without it the "unencrypted rows remain" warning can't say
    **which column**, and whoever runs the re-encryption script won't know where to start.
    """
    if value is None:
        return None
    try:
        return _fernet.decrypt(value.encode()).decode()
    except InvalidToken:
        pass

    if _looks_like_fernet(value):
        # (3) Has the shape of Fernet ciphertext but the current key cannot open it.
        # DO NOT log the content/ciphertext — ciphertext is encrypted customer data; pushing it
        # into logs removes exactly the protection layer just built.
        _logger.error(
            "giai_ma_that_bai_nghi_xoay_khoa",
            extra={"cot": column, "do_dai": len(value)},
        )
        raise UndecryptableError(
            f"{column}: giá trị có hình dạng token Fernet nhưng FIELD_ENCRYPTION_KEY "
            f"hiện tại không giải mã được — nghi khoá đã bị xoay mà chưa mã hoá lại. "
            f"KHÔNG trả bản mã ra ngoài như thể là nội dung."
        )

    # (2) Legacy data ingested before encryption was enabled (plaintext) — still readable as-is
    # so gradual migration isn't blocked. UNLIKE the previous version: it is now COUNTED.
    # This is a prerequisite for the re-encryption step: without a count, nobody knows whether
    # the script covered everything once it finishes.
    _logger.warning(
        "doc_gia_tri_chua_ma_hoa",
        extra={"cot": column, "do_dai": len(value)},
    )
    return value


class EncryptedString(TypeDecorator):
    """Transparently encrypted String column.

    Changing `FIELD_ENCRYPTION_KEY` after data exists ⟹ old data can no longer be read, with
    no way to recover. Since 18/08 this **FAILS LOUDLY** (`UndecryptableError`)
    instead of silently returning ciphertext — see the module docstring.
    """

    impl = String
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect) -> str | None:
        if value is None:
            return None
        return _fernet.encrypt(value.encode()).decode()

    def process_result_value(self, value: str | None, dialect) -> str | None:
        return _decrypt(value, column="EncryptedString")


class EncryptedText(TypeDecorator):
    """Like EncryptedString but impl=Text — for long content (chunked policy/FAQ document
    passages, src/rag/) rather than short fixed values like account_no. Same key/encryption
    logic — only the underlying column type differs."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect) -> str | None:
        if value is None:
            return None
        return _fernet.encrypt(value.encode()).decode()

    def process_result_value(self, value: str | None, dialect) -> str | None:
        return _decrypt(value, column="EncryptedText")
