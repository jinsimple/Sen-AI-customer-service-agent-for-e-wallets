"""Trích text từ file chính sách/FAQ do partner_admin upload
(POST /policy-docs, src/api/main.py).

Chỉ hỗ trợ .md/.txt/.pdf/.docx — CỐ Ý không hỗ trợ .doc nhị phân cũ (OLE):
không có parser Python thuần an toàn cho định dạng này, ép dùng công cụ hệ
thống (antiword/LibreOffice headless) để mở file người dùng tải lên đi ngược
lại tinh thần "bảo mật RAG cấp cao" của tính năng này. Người upload cần lưu
lại thành .docx trước.

Luôn kiểm magic bytes THẬT trước khi parse — không tin đuôi file client tự
khai, chặn kiểu tấn công đổi đuôi file để né validate.
"""
from __future__ import annotations

import io

from src.tools.base import ToolError

_PDF_MAGIC = b"%PDF-"
_ZIP_MAGIC = b"PK\x03\x04"  # .docx là 1 file zip (Office Open XML)

_ALLOWED_TEXT_EXTENSIONS = (".md", ".txt")


class UnsupportedDocumentError(ToolError):
    """File không đúng định dạng hỗ trợ hoặc đuôi file không khớp nội dung thật."""


def _extension(filename: str) -> str:
    idx = filename.rfind(".")
    return filename[idx:].lower() if idx != -1 else ""


def _extract_pdf(content: bytes) -> str:
    from pypdf import PdfReader

    try:
        reader = PdfReader(io.BytesIO(content))
        pages = [page.extract_text() or "" for page in reader.pages]
    except Exception as e:  # pypdf raises nhiều loại lỗi khác nhau tuỳ file hỏng
        raise UnsupportedDocumentError(f"Không đọc được nội dung PDF: {e}") from e
    text = "\n\n".join(p.strip() for p in pages if p.strip())
    if not text.strip():
        raise UnsupportedDocumentError("PDF không có text trích xuất được (có thể là bản scan ảnh)")
    return text


def _extract_docx(content: bytes) -> str:
    from docx import Document

    try:
        doc = Document(io.BytesIO(content))
    except Exception as e:
        raise UnsupportedDocumentError(f"Không đọc được nội dung DOCX: {e}") from e
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    text = "\n".join(paragraphs)
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
    """Điểm vào duy nhất — dispatch theo đuôi file, xác minh magic bytes thật
    trước khi parse, ném UnsupportedDocumentError với thông báo rõ ràng cho
    mọi trường hợp không parse được (agent/API hiển thị lại cho người upload)."""
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
