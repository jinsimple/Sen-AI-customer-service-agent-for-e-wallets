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

import unicodedata

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


# DAU PHIEN BAN CHUAN HOA — tang moi khi cach bien text thanh vector doi.
#
# Vi sao CAN: don 2 bo dau o CA HAI ve (index + query). Neu kho duoc dung bang
# code CU (con dau) ma query chay code MOI (da bo dau) thi hai ve LECH — va ca
# do KHONG CO TRIEU CHUNG NAO: search van tra du k ket qua, chi la ket qua sai.
# Khong loi, khong log, khong canh bao. Doc text trong kho cung khong phat hien
# duoc, vi thay doi nam o VECTOR chu khong o chu.
#
# Mot buoc "phai nho re-index" ma quen thi im lang = min. Dau nay bien no thanh
# thu MAY kiem duoc.
#
#   1 = truoc don 2 (embed text nguyen ban)
#   2 = don 2 (embed ban da bo dau)
CHUAN_HOA_VERSION = 2


def _get_collection():
    return _get_client().get_or_create_collection(
        _COLLECTION_NAME, metadata={"chuan_hoa": CHUAN_HOA_VERSION}
    )


def phien_ban_kho() -> int | None:
    """Phien ban chuan hoa cua kho DANG NAM TREN DIA (None neu kho trong/chua co dau)."""
    col = _get_client().get_or_create_collection(_COLLECTION_NAME)
    if col.count() == 0:
        return None
    return (col.metadata or {}).get("chuan_hoa")


def kho_da_cu() -> bool:
    """True khi kho tren dia duoc dung bang phien ban chuan hoa CU hon code."""
    pb = phien_ban_kho()
    return pb is not None and pb != CHUAN_HOA_VERSION


def bo_dau(s: str) -> str:
    """Bo dau tieng Viet, thuong hoa — dung cho CA HAI ve cua phep so khop.

    DON 2. Do duoc (probe-8, kho 419 chunk): cung 8 cau, **co dau 3/8 · KHONG
    DAU 0/8**. Thi nghiem mot-bien, dau la bien duy nhat doi. Ma khach that —
    va chinh bo demo case D1-D4 cua du an — go KHONG DAU. Tuc che do
    nguoi-dung-that dang o vung 0/8.

    Goc: embedding cua "phi chuyen tien" nam xa embedding cua "phi chuyen tien"
    co dau trong khong gian vector. Khong phai mo hinh kem — hai chuoi ky tu do
    THAT SU khac nhau; ta moi la ben biet chung cung nghia.

    Cach va: bo dau CA text luc index LAN query luc tra. Hai ve cung mot phep
    chuan hoa thi chung hoi tu ve cung mot chuoi, khoang cach vector ve dung
    cho no nen o.

    CO MAT MAT, ghi ro de khong ai tuong day la bua trua mien phi: bo dau lam
    ma/ma/ma/ma thanh mot. Danh doi nay phai DO chu khong lap luan — neu che do
    co-dau TUT thi ban va sai huong, du che do khong-dau co tang.
    """
    s = s.lower().replace("\u0111", "d")
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def add_chunks(doc_id: str, chunk_ids: list[str], texts: list[str]) -> None:
    """Embed + index. `texts` chỉ dùng để TÍNH embedding — không được lưu lại
    trong Chroma, `documents=chunk_ids` mới là thứ thật sự ghi vào collection."""
    if not chunk_ids:
        return
    # Embed ban DA BO DAU — phai khop dung phep chuan hoa o `search()`.
    # Lech mot ve la toan bo index vo dung ma khong co trieu chung nao.
    vectors = _get_embeddings().embed_documents([bo_dau(t) for t in texts])
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
    vector = _get_embeddings().embed_query(bo_dau(query))
    result = collection.query(query_embeddings=[vector], n_results=min(k, collection.count()))
    ids = result.get("ids", [[]])[0]
    distances = result.get("distances", [[]])[0]
    return list(zip(ids, distances))
