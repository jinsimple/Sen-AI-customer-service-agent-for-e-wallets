"""ADR-065 (05/09) — GET /policy-doc/{doc_id}, deep-link đọc toàn văn cho kết
quả /policy-search. Theo khuôn test_ticket_pagination_filters.py (client
fixture qua sample_db + gọi thẳng hàm nghiệp vụ để dựng dữ liệu)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.api.deps import get_session
from src.api.main import app
from src.auth import create_access_token
from src.db.models import PolicyChunk, PolicyDocument
from src.rag.ingest import ingest_document


@pytest.fixture()
def client(sample_db):
    def _override_session():
        try:
            yield sample_db
            sample_db.commit()
        except Exception:
            sample_db.rollback()
            raise

    app.dependency_overrides[get_session] = _override_session
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _stub_vector_store(monkeypatch):
    monkeypatch.setattr("src.rag.ingest.store.add_chunks", lambda *a, **k: None)
    monkeypatch.setattr("src.rag.ingest.store.delete_document", lambda *a, **k: None)


def _token(user_id: str, role: str) -> str:
    return create_access_token(user_id=user_id, role=role)


_CSKH = {"Authorization": f"Bearer {_token('USR-CSKH', 'cskh')}"}
_SUP = {"Authorization": f"Bearer {_token('USR-SUP', 'supervisor')}"}
_CUSTOMER = {"Authorization": f"Bearer {_token('USR-A', 'customer')}"}


def _ingest(sample_db, text: str, filename: str = "faq.md") -> PolicyDocument:
    doc = ingest_document(sample_db, file_bytes=text.encode("utf-8"), filename=filename, uploaded_by="USR-SUP")
    sample_db.commit()
    return doc


def test_doc_khong_ton_tai_tra_404(client):
    resp = client.get("/policy-doc/DOC-KHONG-TON-TAI", headers=_CSKH)
    assert resp.status_code == 404, resp.text


def test_doc_dang_processing_khong_duoc_doc(client, sample_db):
    doc = _ingest(sample_db, "Nội dung chính sách " * 50)
    doc = sample_db.get(PolicyDocument, doc.doc_id)
    doc.status = "processing"
    sample_db.commit()
    resp = client.get(f"/policy-doc/{doc.doc_id}", headers=_CSKH)
    assert resp.status_code == 404, resp.text


def test_doc_ngan_1_chunk_tra_dung_toan_van(client, sample_db):
    text = "FAQ ngắn — phí rút tiền là 5.500đ mỗi lần."
    doc = _ingest(sample_db, text)
    assert doc.chunk_count == 1

    resp = client.get(f"/policy-doc/{doc.doc_id}", headers=_CSKH)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["full_text"] == text
    assert body["filename"] == "faq.md"


def test_chunk_id_dung_tra_ve_dung_offset_to_sang(client, sample_db):
    text = "Đoạn mở đầu không liên quan. " * 30 + "PHÍ RÚT TIỀN LÀ ĐÂY ĐOẠN QUAN TRỌNG. " + "Đoạn kết thúc. " * 30
    doc = _ingest(sample_db, text)
    chunks = sample_db.query(PolicyChunk).filter(PolicyChunk.doc_id == doc.doc_id).order_by(PolicyChunk.chunk_index).all()
    # Lấy đúng chunk chứa câu quan trọng để giả lập kết quả /policy-search thật.
    target = next(c for c in chunks if "PHÍ RÚT TIỀN" in c.text)

    resp = client.get(f"/policy-doc/{doc.doc_id}", params={"chunk_id": target.chunk_id}, headers=_CSKH)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["highlight"] is not None
    start, end = body["highlight"]["start"], body["highlight"]["end"]
    assert "PHÍ RÚT TIỀN LÀ ĐÂY ĐOẠN QUAN TRỌNG" in body["full_text"][start:end]


def test_chunk_id_khong_khop_doc_id_bo_qua_to_sang_khong_loi(client, sample_db):
    doc_a = _ingest(sample_db, "Tài liệu A " * 50, filename="a.md")
    doc_b = _ingest(sample_db, "Tài liệu B hoàn toàn khác " * 50, filename="b.md")
    chunk_cua_b = sample_db.query(PolicyChunk).filter(PolicyChunk.doc_id == doc_b.doc_id).first()

    resp = client.get(f"/policy-doc/{doc_a.doc_id}", params={"chunk_id": chunk_cua_b.chunk_id}, headers=_CSKH)
    assert resp.status_code == 200, resp.text
    assert resp.json()["highlight"] is None


def test_chunk_id_khong_ton_tai_bo_qua_to_sang_khong_loi(client, sample_db):
    doc = _ingest(sample_db, "Nội dung " * 50)
    resp = client.get(f"/policy-doc/{doc.doc_id}", params={"chunk_id": "CHK-khong-ton-tai"}, headers=_CSKH)
    assert resp.status_code == 200, resp.text
    assert resp.json()["highlight"] is None


def test_doc_chua_co_full_text_van_tra_200_khong_loi(client, sample_db):
    """Mô phỏng 4 tài liệu index TRƯỚC migration f1a2b3c4d5e6 (full_text=None
    chưa backfill) — route KHÔNG được crash, chỉ không tô sáng được."""
    doc = _ingest(sample_db, "Nội dung cũ " * 50)
    doc = sample_db.get(PolicyDocument, doc.doc_id)
    chunk = sample_db.query(PolicyChunk).filter(PolicyChunk.doc_id == doc.doc_id).first()
    doc.full_text = None
    sample_db.commit()

    resp = client.get(f"/policy-doc/{doc.doc_id}", params={"chunk_id": chunk.chunk_id}, headers=_CSKH)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["full_text"] is None
    assert body["highlight"] is None


def test_supervisor_doc_duoc(client, sample_db):
    doc = _ingest(sample_db, "Nội dung " * 50)
    resp = client.get(f"/policy-doc/{doc.doc_id}", headers=_SUP)
    assert resp.status_code == 200, resp.text


def test_customer_bi_chan_403(client, sample_db):
    doc = _ingest(sample_db, "Nội dung " * 50)
    resp = client.get(f"/policy-doc/{doc.doc_id}", headers=_CUSTOMER)
    assert resp.status_code == 403, resp.text
