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

from src.config import (
    EMBEDDING_API_KEY,
    EMBEDDING_BASE_URL,
    EMBEDDING_BATCH_SIZE,
    RAG_EMBEDDING_MODEL,
    RAG_INDEX_DIR,
)

_COLLECTION_GOC = "policy_faq"


def _ten_collection() -> str:
    """Tên collection MANG THEO model nhúng — công tắc, không phải migrate.

    Chiều vector khác nhau (`text-embedding-3-small` 1536 · Qwen
    `text-embedding-v4` 1024) và Chroma GHIM chiều lúc TẠO collection, nên hai
    model KHÔNG dùng chung một collection được. Làm ngây thơ thì mỗi lần đổi
    nhà cung cấp là nạp lại toàn bộ kho.

    Đặt tên theo model -> hai kho sống SONG SONG, mỗi kho nạp MỘT LẦN, đổi qua
    đổi lại là đổi biến môi trường và 0 giây nạp lại.

    Và nó CỨU CHUỖI ĐO: kho `3-small` còn nguyên vẹn nên mọi số truy hồi cũ
    (nền 23/47, rerank 38/47, trần Recall@20, 47 ca golden) vẫn đo lại được
    trên đúng vật cũ — chỉ cần lật biến về.
    """
    return f"{_COLLECTION_GOC}__{RAG_EMBEDDING_MODEL}"


def _doi_ten_kho_cu_mot_lan(client) -> None:
    """Kho dựng TRƯỚC quy ước đặt tên này nằm ở tên trần `policy_faq`.

    Đổi quy ước mà không xử nó = 378 vector trở thành VÔ HÌNH, và `kiem` sẽ
    báo TRONG rồi bảo người ta nạp lại một kho vốn hoàn toàn đúng — tốn tiền
    nhúng lại và cắt chuỗi đo, đúng hai thứ quy ước này sinh ra để tránh.

    Đổi TÊN chứ không nhúng lại: vector giữ nguyên, 0 lượt gọi API.

    ⚠️ CHỈ đổi khi model hiện tại ĐÚNG LÀ model đã dựng kho cũ. Kho trần đó
    dựng bằng `text-embedding-3-small` (hardcode thời đó); nếu ai chạy lần đầu
    với model khác thì gán nhãn model mới cho vector cũ là tạo ra đúng loại
    lệch-một-vế mà cả `chuan_hoa` lẫn `model_embed` tồn tại để chặn.
    """
    if RAG_EMBEDDING_MODEL != "text-embedding-3-small":
        return
    ten_moi = _ten_collection()
    co = {c.name for c in client.list_collections()}
    if _COLLECTION_GOC in co and ten_moi not in co:
        cu = client.get_collection(_COLLECTION_GOC)
        if cu.count() > 0:
            cu.modify(name=ten_moi, metadata={"chuan_hoa": CHUAN_HOA_VERSION,
                                              "model_embed": RAG_EMBEDDING_MODEL})

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
        # `check_embedding_ctx_length=False` CHỈ khi trỏ nhà cung cấp khác.
        #
        # Mặc định LangChain TOKENISE phía client rồi gửi MẢNG SỐ NGUYÊN.
        # OpenAI nhận; endpoint "tương thích OpenAI" của Qwen TỪ CHỐI:
        #   400 InvalidParameter: contents is neither str nor list of str
        # Tắt cờ đó -> gửi chuỗi thô, đúng thứ mọi endpoint đều hiểu.
        #
        # CÓ ĐIỀU KIỆN chứ không bật luôn: cờ này cũng tắt phép cắt-theo-ngữ-
        # cảnh phía client. Chunk của ta 800 ký tự nên không chạm trần, nhưng
        # bật nó cho đường OpenAI là ĐỔI VẬT trên kho 378 vector đang giữ cả
        # chuỗi đo — không đổi thứ đang chạy đúng để chiều một nhà cung cấp
        # chưa dùng.
        _embeddings = OpenAIEmbeddings(
            model=RAG_EMBEDDING_MODEL,
            api_key=EMBEDDING_API_KEY,
            base_url=EMBEDDING_BASE_URL,
            **({"check_embedding_ctx_length": False} if EMBEDDING_BASE_URL else {}),
            **({"chunk_size": EMBEDDING_BATCH_SIZE} if EMBEDDING_BATCH_SIZE else {}),
        )
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
    c = _get_client()
    _doi_ten_kho_cu_mot_lan(c)
    return c.get_or_create_collection(_ten_collection())


def _dong_dau(col) -> None:
    """Ghi dau phien ban len collection.

    `get_or_create_collection(name, metadata=...)` CHI ap metadata luc TAO. Kho
    da ton tai thi metadata bi BO QUA im lang — do that tren kho demo:
    418 chunk, `metadata = None`. Nen phai `modify()` TUONG MINH sau moi lan
    nap, khong dua vao tham so luc lay collection.
    """
    # Ghi CẢ model embedding, khong chi `chuan_hoa`. Truoc day dau phien ban
    # chi theo doi cach BIEN TEXT (bo dau hay khong); model sinh ra vector thi
    # hardcode nen khong the lech. Tu khi `EMBEDDING_MODEL` doc tu env, no LECH
    # DUOC — va do la dung lop loi don 2: doi model -> moi vector trong kho vo
    # nghia, ma search van tra du k ket qua, khong loi, khong log.
    col.modify(metadata={"chuan_hoa": CHUAN_HOA_VERSION, "model_embed": RAG_EMBEDDING_MODEL})


# Ba trang thai PHAN BIET DUOC — gop chung la nguon goc cua bug dau tien:
#   TRONG        kho khong co chunk nao
#   KHONG_DAU    co chunk nhung khong co dau  -> kho CU (dung truoc don 2)
#   LECH         co dau nhung khac phien ban code
#   KHOP         dau == phien ban code
#   LECH_MODEL   dau khop nhung MODEL EMBEDDING khac -> vector vo nghia
TRANG_THAI_TRONG = "trong"
TRANG_THAI_KHONG_DAU = "khong_dau"
TRANG_THAI_LECH = "lech"
TRANG_THAI_LECH_MODEL = "lech_model"
TRANG_THAI_KHOP = "khop"


def trang_thai_kho() -> tuple[str, int | None]:
    """(trang_thai, phien_ban_tren_dia)."""
    col = _get_collection()
    if col.count() == 0:
        return TRANG_THAI_TRONG, None
    pb = (col.metadata or {}).get("chuan_hoa")
    if pb is None:
        return TRANG_THAI_KHONG_DAU, None
    if pb != CHUAN_HOA_VERSION:
        return TRANG_THAI_LECH, pb
    # Kho dung TRUOC ban nay khong co `model_embed` -> KHONG ket luan lech.
    # Fail-open o day la CO CHU DICH va hep: thieu dau model nghia la kho dung
    # boi code chua biet ghi dau, khi do model chac chan van la mac dinh
    # hardcode cu. Coi no la LECH se bat ca doi nap lai mot kho hoan toan dung.
    # Chi khi CO dau va dau KHAC moi la lech that.
    me = (col.metadata or {}).get("model_embed")
    if me is not None and me != RAG_EMBEDDING_MODEL:
        return TRANG_THAI_LECH_MODEL, pb
    return TRANG_THAI_KHOP, pb


def kho_can_nap_lai() -> bool:
    """True khi kho KHONG dam bao khop phien ban chuan hoa cua code.

    KHONG_DAU tinh la CAN NAP LAI — day la cho ban dau toi lam NGUOC: coi
    "khong co dau" la "khong sao", tuc canh cong bao AN TOAN dung o ca nguy
    hiem nhat (kho dung truoc don 2, chua bo dau, trong khi query da bo dau).
    Mot canh cong sai huong con te hon khong co cong.
    """
    tt, _ = trang_thai_kho()
    return tt != TRANG_THAI_KHOP


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
    col = _get_collection()
    col.add(
        ids=chunk_ids,
        embeddings=vectors,
        documents=chunk_ids,  # cố ý: placeholder, KHÔNG phải nội dung thật
        metadatas=[{"doc_id": doc_id} for _ in chunk_ids],
    )
    _dong_dau(col)


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
