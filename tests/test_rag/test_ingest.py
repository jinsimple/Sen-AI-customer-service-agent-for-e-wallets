"""Test src/rag/ingest.py — ingest_document/delete_document. Không gọi Chroma/
OpenAI thật (monkeypatch src.rag.ingest.store) — unit test tầng điều phối +
ghi DB (chia đoạn, mã hoá, status), không phải tầng vector search (đã verify
thủ công qua smoke test end-to-end lúc build tính năng)."""
from __future__ import annotations

import pytest

from src.db.models import PolicyChunk, PolicyDocument
from src.rag.ingest import delete_document, ingest_document
from src.rag.parsers import UnsupportedDocumentError
from src.tools.base import ToolError


@pytest.fixture(autouse=True)
def _stub_vector_store(monkeypatch):
    """Không gọi OpenAI embeddings/Chroma thật trong unit test — chỉ verify
    ingest.py gọi đúng store.add_chunks/delete_document với đúng tham số."""
    calls = {"add": [], "delete": []}

    def fake_add_chunks(doc_id, chunk_ids, texts):
        calls["add"].append((doc_id, chunk_ids, texts))

    def fake_delete_document(doc_id):
        calls["delete"].append(doc_id)

    monkeypatch.setattr("src.rag.ingest.store.add_chunks", fake_add_chunks)
    monkeypatch.setattr("src.rag.ingest.store.delete_document", fake_delete_document)
    return calls


def test_ingest_md_creates_indexed_document(sample_db, _stub_vector_store):
    content = ("Chính sách hoàn tiền. " * 100).encode("utf-8")  # đủ dài để chia >1 đoạn
    doc = ingest_document(sample_db, file_bytes=content, filename="policy.md", uploaded_by="USR-SUP")

    assert doc.status == "indexed"
    assert doc.chunk_count > 1
    assert doc.error_message is None

    chunks = sample_db.query(PolicyChunk).filter(PolicyChunk.doc_id == doc.doc_id).all()
    assert len(chunks) == doc.chunk_count
    # Text đọc lại qua ORM phải đúng nội dung gốc (mã hoá/giải mã trong suốt)
    assert "Chính sách hoàn tiền" in chunks[0].text

    assert len(_stub_vector_store["add"]) == 1
    called_doc_id, called_chunk_ids, called_texts = _stub_vector_store["add"][0]
    assert called_doc_id == doc.doc_id
    assert len(called_chunk_ids) == doc.chunk_count
    assert len(called_texts) == doc.chunk_count


def test_ingest_rejects_legacy_doc(sample_db, _stub_vector_store):
    with pytest.raises(UnsupportedDocumentError):
        ingest_document(sample_db, file_bytes=b"x", filename="old.doc", uploaded_by="USR-SUP")

    doc = sample_db.query(PolicyDocument).filter(PolicyDocument.filename == "old.doc").one()
    assert doc.status == "failed"
    assert doc.error_message is not None
    # Không được gọi tới vector store khi parse đã thất bại
    assert _stub_vector_store["add"] == []


def test_ingest_rejects_oversized_file(sample_db, _stub_vector_store):
    from src.config import MAX_UPLOAD_SIZE_MB

    oversized = b"a" * (MAX_UPLOAD_SIZE_MB * 1024 * 1024 + 1)
    with pytest.raises(ToolError, match="giới hạn"):
        ingest_document(sample_db, file_bytes=oversized, filename="big.txt", uploaded_by="USR-SUP")


def test_delete_document_removes_db_rows_and_calls_store(sample_db, _stub_vector_store):
    content = "Nội dung chính sách cần xoá.".encode("utf-8")
    doc = ingest_document(sample_db, file_bytes=content, filename="temp.txt", uploaded_by="USR-SUP")
    doc_id = doc.doc_id

    delete_document(sample_db, doc_id)

    assert sample_db.get(PolicyDocument, doc_id) is None
    assert sample_db.query(PolicyChunk).filter(PolicyChunk.doc_id == doc_id).count() == 0
    assert _stub_vector_store["delete"] == [doc_id]


def test_delete_unknown_document_raises(sample_db, _stub_vector_store):
    with pytest.raises(ToolError, match="không tồn tại"):
        delete_document(sample_db, "DOC-KHONG-TON-TAI")
