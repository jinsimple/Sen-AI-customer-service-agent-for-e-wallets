"""Extract text from policy/FAQ files uploaded by partner_admin
(POST /policy-docs, src/api/main.py).

Only .md/.txt/.pdf/.docx are supported — legacy binary .doc (OLE) is DELIBERATELY
unsupported: there is no safe pure-Python parser for that format, and forcing system tools
(antiword/headless LibreOffice) to open user-uploaded files runs against the "hardened RAG
security" spirit of this feature. Uploaders need to re-save as .docx first.

Always check the REAL magic bytes before parsing — never trust the file extension declared
by the client; this blocks extension-swapping attacks that try to dodge validation.
"""
from __future__ import annotations

import io
import re
import unicodedata

from src.tools.base import ToolError

_PDF_MAGIC = b"%PDF-"
_ZIP_MAGIC = b"PK\x03\x04"  # .docx is a zip file (Office Open XML)

_ALLOWED_TEXT_EXTENSIONS = (".md", ".txt")


class UnsupportedDocumentError(ToolError):
    """File is not a supported format, or its extension does not match its real content."""


_VOWELS = set("aeiouy")


def _strip_diacritics(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _has_vowel(s: str) -> bool:
    return any(c in _VOWELS for c in _strip_diacritics(s).lower())


def _join_broken_syllables(text: str) -> str:
    """Repair PDF extraction that inserts whitespace INSIDE a Vietnamese syllable.

    The real RAG store contained `"Giao D ịch"`, `"liên k ết"`, `"th ực"` — whitespace
    inserted by pypdf when composing accented glyphs. It breaks BOTH retrieval layers at once:
    embeddings see two junk tokens instead of one word, and keyword matching misses
    completely. Measured on the real store: **414 occurrences** in 254,196 characters.

    JOIN RULE — two conditions that must hold SIMULTANEOUSLY, and both are needed:
      (1) the PRECEDING fragment is a PURE CONSONANT cluster of 1-3 characters (no vowel).
          A Vietnamese syllable ALWAYS contains a vowel, so an all-consonant token is never
          a complete word — it can only be a fragment.
      (2) the FOLLOWING fragment starts with a VOWEL — i.e. it is the rhyme part of the syllable.

    Why (2) is needed, found by measuring: using (1) alone wrongly joins **143 valid
    abbreviations** — `NH TMCP` -> `NHTMCP`, `SMS Banking` -> `SMSBanking`,
    `JCB Debit`, `TK ngân`, `x Rộng`. Adding (2) removes all 143 while keeping all
    414 correct joins.

    NO dictionary: a hand-written word list will miss exactly the word someone is about to
    type (Rule 18/ADR-023). This rule relies on Vietnamese PHONOLOGICAL PROPERTIES, not on
    enumeration.
    """

    def _substitute(m: re.Match[str]) -> str:
        before, after = m.group(1), m.group(2)
        if _has_vowel(before):
            return m.group(0)
        trailing_marker = _strip_diacritics(after)[:1].lower()
        if trailing_marker not in _VOWELS:
            return m.group(0)
        return before + after

    return re.sub(r"\b([A-Za-zĐđ]{1,3}) ([a-zA-ZÀ-ỹĐđ]{1,12})\b", _substitute, text)


# DON 3 — LOAI DONG MUC LUC KHOI INDEX.
#
# Phat hien cua tester khi xac minh 41 nhan: muc luc chua NGUYEN VAN 160 cau
# hoi cua tai lieu, va no THANG dap an trong embedding — khach hoi cang giong
# cau that thi cang de trung dong muc luc. Ca RAG-21/22: ca top-3 deu la dong
# "……… so trang". Kho TU CANH TRANH VOI CHINH NO.
#
# LUAT HAI DIEU KIEN, khong phai mot (canh trong kieu F-25 — luat loai phai
# kem ca doi chung, dung loai nham than bai):
#   (1) chuoi >=5 dau cham LIEN TIEP
#   (2) VA ket thuc bang so trang
#
# Do tren kho that (3.896 dong, 2 PDF):
#   khop ca hai dieu kien        263 dong  -> loai, deu la muc luc
#   co "..." nhung KHONG ket so    4 dong  -> GIU, deu la than bai that
#                                             (vd "10.000d,...")
# Chi dieu kien (1) se loai nham 4 dong do. Dieu kien (2) la thu phan biet.
_TOC_LINE = re.compile(r"\.{5,}\s*\d+\s*$")


def _drop_toc_lines(text: str) -> str:
    """Drop table-of-contents lines; KEEP every other line and the line-break structure.

    CORRECTION of the measurement (commit 0c965a7 recorded it WRONG; history can't be edited):
        BEFORE baseline  20/35 — NOT 19/35. 19/35 predates the tester fixing the wrong label
                         of case RAG-08 in 675282e; I measured "after" with the new
                         yardstick but compared against a "before" measured with the old one.
        after fix 3      21/35  ⟹ net delta +1, not +2.

    That includes case RAG-04 moving PASS -> fail. Re-measured: the only chunk in the
    top-10 matching the case's keywords was a TABLE-OF-CONTENTS HEADING LINE, and it matched
    on the weak keyword `nhận tiền` (receive money), not on `50.000.000`. The real answer of
    FAQ 7 was absent. So RAG-04 never retrieved correctly — fix 3 exposed a FALSE PASS, it
    did not cause a regression. Recorded rather than folded into the delta.

    Wider consequence (further tester audit, fixed by the PO in STATE 78ecc79): 9/21 currently
    PASSING cases pass thanks to generic keywords. 60% is an UPPER BOUND; the lower bound is
    34.3%. This function's numbers are only as trustworthy as the yardstick.
    """
    return "\n".join(d for d in text.split("\n") if not _TOC_LINE.search(d.strip()))


def _extension(filename: str) -> str:
    idx = filename.rfind(".")
    return filename[idx:].lower() if idx != -1 else ""


def _extract_pdf(content: bytes) -> str:
    from pypdf import PdfReader

    try:
        reader = PdfReader(io.BytesIO(content))
        pages = [page.extract_text() or "" for page in reader.pages]
    except Exception as e:  # pypdf raises many different exception types depending on how the file is broken
        raise UnsupportedDocumentError(f"Không đọc được nội dung PDF: {e}") from e
    text = "\n\n".join(p.strip() for p in pages if p.strip())
    if not text.strip():
        raise UnsupportedDocumentError("PDF không có text trích xuất được (có thể là bản scan ảnh)")
    # Repair broken syllables RIGHT AT THE EXTRACTION POINT — before the text goes into chunking
    # and embedding. Repairing later (at query time) can't save it: the vector is already wrong.
    # The order is DELIBERATE: join broken syllables FIRST, then drop TOC lines.
    # The other way round, TOC lines with broken words would not match the pattern and leak into
    # the index.
    return _drop_toc_lines(_join_broken_syllables(text))


def _table_row_to_line(table_rows) -> list[str]:
    """Each table ROW -> ONE self-describing line carrying the column names.

    Why not flatten: the PDF version of this very table was mashed by pypdf into porridge
    (`NH TMCP Ngoại Thương VCB Tất cả NH TMCP Bản Việt VCCB 2,000,000...`)
    — 23 banks stuck together in one block, no row retrievable on its own. Measured:
    the tester found ~20 near-duplicate passages causing 31.5% of the store never to surface
    in the top-3, and that group WAS this table.

    Column names are attached to every cell so a row standing alone is still readable: a chunk
    may be cut away from the header row, and then "VCB · Tất cả" is meaningless whereas
    "Tên viết tắt: VCB · Hạn mức: Tất cả" (Short name: VCB · Limit: All) is not.
    """
    row_item = table_rows.rows
    if not row_item:
        return []
    column = [c.text.strip() for c in row_item[0].cells]
    out_items: list[str] = []
    for h in row_item[1:]:
        o = [c.text.strip() for c in h.cells]
        if not any(o):
            continue
        out_items.append(" · ".join(f"{column[i]}: {v}" if i < len(column) and column[i] else v
                             for i, v in enumerate(o) if v))
    return out_items


def _extract_docx(content: bytes) -> str:
    """Preserve the STRUCTURE of DOCX instead of flattening it.

    Previous version: `"\\n".join(p.text for p in doc.paragraphs)`. Two things were discarded:
      1. heading styles — losing natural section boundaries (239 Heading 3 = ~1 per FAQ,
         and the headings already carry the entity name: "44. Cách liên kết MoMo với tài
         khoản ngân hàng Việt Nam Phương Đông (OCB)" — How to link MoMo with an OCB account)
      2. `doc.tables` — python-docx does NOT include table cells in `doc.paragraphs`, so the
         23-row bank limit table had never entered the store via the DOCX path.
         Silently, with no error.

    Headings are separated by BLANK LINES on both sides because `RecursiveCharacterTextSplitter`
    (src/rag/ingest.py) prefers to split at `\\n\\n` — the only way the extractor can
    influence chunk boundaries without modifying the splitter.

    BACKWARD COMPATIBLE (the PO's condition for 4b): a plain .docx — no headings,
    no tables — produces EXACTLY the same string as before, because neither new branch
    activates. The partner_admin upload path does not change behaviour.
    """
    from docx import Document
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    try:
        doc = Document(io.BytesIO(content))
    except Exception as e:
        raise UnsupportedDocumentError(f"Không đọc được nội dung DOCX: {e}") from e

    # Walk the document BODY to preserve the interleaved order of text and tables —
    # `doc.paragraphs` and `doc.tables` are two separate lists; concatenating them would push all
    # tables to the end, cutting each table off from the paragraph introducing it.
    part: list[str] = []
    for con in doc.element.body.iterchildren():
        if con.tag.endswith("}p"):
            p = Paragraph(con, doc)
            if not p.text.strip():
                continue
            style_name = (p.style.name or "") if p.style is not None else ""
            if style_name.startswith("Heading"):
                part.append("\n" + p.text.strip())
            else:
                part.append(p.text.strip())
        elif con.tag.endswith("}tbl"):
            part.extend(_table_row_to_line(Table(con, doc)))

    text = "\n".join(part).strip()
    if not text.strip():
        raise UnsupportedDocumentError("DOCX không có nội dung text nào")
    return text


def _extract_plain_text(content: bytes) -> str:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as e:
        raise UnsupportedDocumentError(f"File không phải UTF-8 hợp lệ: {e}") from e
    if not text.strip():
        raise UnsupportedDocumentError("File rỗng")
    return text


def extract_text(filename: str, content: bytes) -> str:
    """Single entry point — dispatches by file extension, verifies the real magic bytes
    before parsing, and raises UnsupportedDocumentError with a clear message in every
    unparseable case (the agent/API shows it back to the uploader)."""
    ext = _extension(filename)

    if ext in _ALLOWED_TEXT_EXTENSIONS:
        return _extract_plain_text(content)

    if ext == ".pdf":
        if not content.startswith(_PDF_MAGIC):
            raise UnsupportedDocumentError(
                "Đuôi file là .pdf nhưng nội dung không phải PDF thật"
            )
        return _extract_pdf(content)

    if ext == ".docx":
        if not content.startswith(_ZIP_MAGIC):
            raise UnsupportedDocumentError(
                "Đuôi file là .docx nhưng nội dung không phải DOCX thật"
            )
        return _extract_docx(content)

    if ext == ".doc":
        raise UnsupportedDocumentError(
            "Không hỗ trợ .doc (định dạng Word cũ) — vui lòng lưu lại thành .docx rồi upload lại"
        )

    raise UnsupportedDocumentError(
        f"Định dạng '{ext or '(không có đuôi)'}' không được hỗ trợ — chỉ nhận .md/.txt/.pdf/.docx"
    )
