"""Test src/rag/parsers.py — mỗi định dạng trích đúng text, đuôi file giả
mạo/không hỗ trợ bị từ chối rõ ràng thay vì crash hay âm thầm parse sai."""
from __future__ import annotations

import io

import pytest
from docx import Document

from src.rag.parsers import UnsupportedDocumentError, extract_text


def _build_minimal_pdf(text: str) -> bytes:
    """PDF hợp lệ tối thiểu (không phụ thuộc reportlab/fpdf) — 1 trang, 1
    dòng text, xref table tính offset đúng để pypdf đọc được."""
    objs = [
        b"<</Type/Catalog/Pages 2 0 R>>",
        b"<</Type/Pages/Kids[3 0 R]/Count 1>>",
        b"<</Type/Page/Parent 2 0 R/Resources<</Font<</F1 4 0 R>>>>/MediaBox[0 0 300 300]/Contents 5 0 R>>",
        b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>",
    ]
    stream_content = f"BT /F1 12 Tf 10 100 Td ({text}) Tj ET".encode()
    objs.append(b"<</Length %d>>\nstream\n" % len(stream_content) + stream_content + b"\nendstream")

    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objs, start=1):
        offsets.append(out.tell())
        out.write(f"{i} 0 obj".encode() + body + b"endobj\n")
    xref_pos = out.tell()
    n = len(objs) + 1
    out.write(f"xref\n0 {n}\n".encode())
    out.write(b"0000000000 65535 f \n")
    for off in offsets:
        out.write(f"{off:010d} 00000 n \n".encode())
    out.write(f"trailer<</Size {n}/Root 1 0 R>>\nstartxref\n{xref_pos}\n%%EOF".encode())
    return out.getvalue()


def _build_docx(paragraphs: list[str]) -> bytes:
    doc = Document()
    for p in paragraphs:
        doc.add_paragraph(p)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_extract_md():
    content = "# Chính sách\nHoàn tiền trong 3 ngày.".encode("utf-8")
    assert "Hoàn tiền trong 3 ngày" in extract_text("policy.md", content)


def test_extract_txt():
    content = "Phí rút tiền 0.5%.".encode("utf-8")
    assert "Phí rút tiền" in extract_text("fee.txt", content)


def test_extract_pdf():
    pdf_bytes = _build_minimal_pdf("Hello RAG test policy content")
    text = extract_text("policy.pdf", pdf_bytes)
    assert "Hello RAG test policy content" in text


def test_extract_docx():
    docx_bytes = _build_docx(["Chính sách hoàn tiền", "Áp dụng từ 2026."])
    text = extract_text("policy.docx", docx_bytes)
    assert "Chính sách hoàn tiền" in text
    assert "Áp dụng từ 2026" in text


def test_reject_legacy_doc():
    with pytest.raises(UnsupportedDocumentError, match=r"\.doc"):
        extract_text("old.doc", b"anything")


def test_reject_unknown_extension():
    with pytest.raises(UnsupportedDocumentError):
        extract_text("script.exe", b"MZ\x90\x00")


def test_reject_spoofed_pdf_extension():
    """Đuôi .pdf nhưng nội dung không phải PDF thật — phải bị chặn bởi kiểm
    magic bytes, không được đưa thẳng vào pypdf parse mù."""
    with pytest.raises(UnsupportedDocumentError, match="không phải PDF"):
        extract_text("fake.pdf", b"day khong phai pdf that")


def test_reject_spoofed_docx_extension():
    with pytest.raises(UnsupportedDocumentError, match="không phải DOCX"):
        extract_text("fake.docx", b"day khong phai docx that")


def test_reject_empty_file():
    with pytest.raises(UnsupportedDocumentError):
        extract_text("empty.txt", b"")


def test_reject_non_utf8_text():
    with pytest.raises(UnsupportedDocumentError, match="UTF-8"):
        extract_text("bad.txt", b"\xff\xfe\x00\x01invalid")
