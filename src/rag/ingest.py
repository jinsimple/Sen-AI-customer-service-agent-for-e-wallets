"""Ingest one uploaded policy/FAQ document — the single entry point, called from
`POST /policy-docs` (src/api/main.py). No parsing/chunking/embedding logic lives here;
it only orchestrates the steps + handles errors consistently.

Write order: DB first (source of truth, recoverable), Chroma second (derived index,
rebuildable from the DB if needed) — if the embed/Chroma step fails, the DB already holds
PolicyDocument.status='failed', so a document is never silently lost.
"""
from __future__ import annotations

from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.config import MAX_UPLOAD_SIZE_MB, RAG_CHUNK_OVERLAP, RAG_CHUNK_SIZE
from src.db.models import PolicyChunk, PolicyDocument
from src.observability.logging_config import get_logger
from src.rag import store
from src.rag.parsers import UnsupportedDocumentError, extract_text
from src.tools.base import ToolError, new_id

_MAX_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024


_logger = get_logger("fin05.rag")


def ingest_document(
    session: Session,
    *,
    file_bytes: bytes,
    filename: str,
    uploaded_by: str,
    load_source: str = "khong_ro",
) -> PolicyDocument:
    """`load_source`: "upload_api" | "script_noi_bo" | "eval". Default "khong_ro" (unknown)
    ON PURPOSE: any ingestion path that hasn't declared itself gives itself away in the log,
    instead of silently getting a plausible-looking label."""
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

    # ADR-065 — store the ORIGINAL full text BEFORE chunking (not after — re-joining chunks does
    # not reproduce the text because of overlap). Used by the full-text reading page deep-linked
    # from /policy-search; the existing chunk/rerank flow is unchanged.
    doc.full_text = text

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
    # F-LOG-3. Incident of 16/08: the access log HAD two `POST /policy-docs` lines
    # but did NOT say which file — security had to infer it from the store state. This line
    # answers it directly. `nguon` is deliberately named the same as the provenance-on-chunk
    # field security is building, so it won't need renaming later.
    _logger.info(
        "policy_doc_nap",
        extra={
            "doc_id": doc_id,
            # 🔴 MUST NOT be named `filename`. That is a **reserved attribute**
            # of `logging.LogRecord` (Python sets it to the SOURCE file name), so
            # `logging/__init__.py` raises `KeyError: "Attempt to overwrite
            # 'filename' in LogRecord"`.
            #
            # And a raising log ⟹ a raising REQUEST: a `partner_admin` uploading a document
            # gets **HTTP 500**, because of a field name. Not a logging bug.
            #
            # It stayed silent until the day this branch ran: no other log call passed
            # `extra=`, so nobody noticed. The tester caught it on 17/08 via 3 red tests
            # on the document-upload path.
            "ten_tep": filename,
            "uploaded_by": uploaded_by,
            "chunk_count": len(pieces),
            "status": doc.status,
            "nguon_nap": load_source,
        },
    )
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
