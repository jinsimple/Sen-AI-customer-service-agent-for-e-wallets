"""Nạp 1 tài liệu chính sách/FAQ đã upload — điểm vào duy nhất gọi từ
`POST /policy-docs` (src/api/main.py). Không viết logic parse/chia đoạn/embed
ở đây, chỉ điều phối các bước + xử lý lỗi nhất quán.

Thứ tự ghi: DB trước (nguồn sự thật, có thể phục hồi), Chroma sau (index phái
sinh, xây lại được từ DB nếu cần) — lỗi ở bước embed/Chroma thì DB đã có
PolicyDocument.status='failed' để không lặng thinh mất tài liệu.
"""
from __future__ import annotations

from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.config import MAX_UPLOAD_SIZE_MB, RAG_CHUNK_OVERLAP, RAG_CHUNK_SIZE
from src.db.models import PolicyChunk, PolicyDocument
from src.rag import store
from src.rag.parsers import UnsupportedDocumentError, extract_text
from src.tools.base import ToolError, new_id

_MAX_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024


def ingest_document(session: Session, *, file_bytes: bytes, filename: str, uploaded_by: str) -> PolicyDocument:
    if not file_bytes:
        raise ToolError("File rỗng")
    if len(file_bytes) > _MAX_BYTES:
        raise ToolError(f"File vượt quá giới hạn {MAX_UPLOAD_SIZE_MB}MB")

    doc_id = new_id("DOC")
    doc = PolicyDocument(
        doc_id=doc_id,
        filename=filename,
        uploaded_by=uploaded_by,
        status="processing",
        chunk_count=0,
    )
    session.add(doc)
    session.flush()

    try:
        text = extract_text(filename, file_bytes)
    except UnsupportedDocumentError as e:
        doc.status = "failed"
        doc.error_message = str(e)
        session.flush()
        raise

    splitter = RecursiveCharacterTextSplitter(chunk_size=RAG_CHUNK_SIZE, chunk_overlap=RAG_CHUNK_OVERLAP)
    pieces = [p.strip() for p in splitter.split_text(text) if p.strip()]
    if not pieces:
        doc.status = "failed"
        doc.error_message = "Không tách được đoạn nội dung nào từ tài liệu"
        session.flush()
        raise ToolError(doc.error_message)

    chunk_ids = [new_id("CHK") for _ in pieces]
    for i, (chunk_id, piece) in enumerate(zip(chunk_ids, pieces)):
        session.add(PolicyChunk(chunk_id=chunk_id, doc_id=doc_id, chunk_index=i, text=piece))
    session.flush()

    try:
        store.add_chunks(doc_id, chunk_ids, pieces)
    except Exception as e:
        doc.status = "failed"
        doc.error_message = f"Lỗi lập chỉ mục vector: {e}"
        session.flush()
        raise ToolError(doc.error_message) from e

    doc.status = "indexed"
    doc.chunk_count = len(pieces)
    session.flush()
    return doc


def delete_document(session: Session, doc_id: str) -> None:
    doc = session.get(PolicyDocument, doc_id)
    if doc is None:
        raise ToolError(f"doc_id không tồn tại: {doc_id}")
    store.delete_document(doc_id)
    for chunk in session.scalars(select(PolicyChunk).where(PolicyChunk.doc_id == doc_id)).all():
        session.delete(chunk)
    session.delete(doc)
    session.flush()
