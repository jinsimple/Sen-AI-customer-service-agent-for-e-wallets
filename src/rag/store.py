"""Vector store cho RAG chính sách/FAQ — ChromaDB local, persistent, chạy
in-process (`data/rag_index/`, KHÔNG commit — xem .gitignore). Không dùng
managed vector DB bên thứ 3 (Pinecone/Qdrant Cloud...) để giữ đúng cam kết
"dữ liệu không rời khỏi hạ tầng" đã nêu ở trang đăng nhập.

QUAN TRỌNG — "bảo mật RAG cấp cao": Chroma ở đây CHỈ lưu embedding vector +
chunk_id, KHÔNG lưu text thật của tài liệu (tham số `documents=` truyền vào
Chroma là chunk_id, không phải nội dung). Text thật nằm mã hoá trong bảng
SQLite `policy_chunks` (EncryptedText, src/db/crypto_types.py) — tra cứu phải
qua 2 bước: hỏi Chroma lấy chunk_id theo độ tương đồng, rồi giải mã text thật
từ SQLite (xem search.py). Nhờ vậy dù thư mục data/rag_index/ bị đọc trộm
cũng không lộ nội dung chính sách, chỉ lộ các vector số không đảo ngược được
thành văn bản gốc.
"""
from __future__ import annotations

import chromadb
from langchain_openai import OpenAIEmbeddings

from src.config import OPENAI_API_KEY, RAG_EMBEDDING_MODEL, RAG_INDEX_DIR

_COLLECTION_NAME = "policy_faq"

_client: chromadb.ClientAPI | None = None
_embeddings: OpenAIEmbeddings | None = None


def _get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        RAG_INDEX_DIR.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(RAG_INDEX_DIR))
    return _client


def _get_embeddings() -> OpenAIEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = OpenAIEmbeddings(model=RAG_EMBEDDING_MODEL, api_key=OPENAI_API_KEY)
    return _embeddings


def _get_collection():
    return _get_client().get_or_create_collection(_COLLECTION_NAME)


def add_chunks(doc_id: str, chunk_ids: list[str], texts: list[str]) -> None:
    """Embed + index. `texts` chỉ dùng để TÍNH embedding — không được lưu lại
    trong Chroma, `documents=chunk_ids` mới là thứ thật sự ghi vào collection."""
    if not chunk_ids:
        return
    vectors = _get_embeddings().embed_documents(texts)
    _get_collection().add(
        ids=chunk_ids,
        embeddings=vectors,
        documents=chunk_ids,  # cố ý: placeholder, KHÔNG phải nội dung thật
        metadatas=[{"doc_id": doc_id} for _ in chunk_ids],
    )


def delete_document(doc_id: str) -> None:
    _get_collection().delete(where={"doc_id": doc_id})


def search(query: str, k: int) -> list[tuple[str, float]]:
    """Trả về [(chunk_id, distance)], gần nhất trước. distance càng nhỏ càng
    liên quan (Chroma mặc định cosine/L2 tuỳ cấu hình, không cần agent quan
    tâm — chỉ dùng để sắp xếp)."""
    collection = _get_collection()
    if collection.count() == 0:
        return []
    vector = _get_embeddings().embed_query(query)
    result = collection.query(query_embeddings=[vector], n_results=min(k, collection.count()))
    ids = result.get("ids", [[]])[0]
    distances = result.get("distances", [[]])[0]
    return list(zip(ids, distances))
