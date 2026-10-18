"""Vector store for the policy/FAQ RAG — local, persistent ChromaDB running in-process
(`data/rag_index/`, NOT committed — see .gitignore). No third-party managed vector DB
(Pinecone/Qdrant Cloud...) is used, to keep the "data never leaves our infrastructure"
promise stated on the login page.

IMPORTANT — "hardened RAG security": Chroma here stores ONLY embedding vectors +
chunk_ids, NOT the documents' real text (the `documents=` argument passed to Chroma is the
chunk_id, not the content). The real text lives encrypted in the SQL table
`policy_chunks` (EncryptedText, src/db/crypto_types.py) — lookups take 2 steps: ask Chroma
for chunk_ids by similarity, then decrypt the real text from SQL (see search.py). So even if
the data/rag_index/ directory is stolen, no policy content leaks — only numeric vectors that
cannot be inverted back into the original text.
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
from src.egress_gate import shared_http_client

_BASE_COLLECTION = "policy_faq"


def _collection_name() -> str:
    """The collection name CARRIES the embedding model — a switch, not a migration.

    Vector dimensions differ (`text-embedding-3-small` 1536 · Qwen
    `text-embedding-v4` 1024) and Chroma PINS the dimension when the collection is CREATED,
    so two models CANNOT share one collection. A naive approach would re-ingest the whole
    store every time the provider changes.

    Naming by model -> two stores live SIDE BY SIDE, each ingested ONCE; switching back and
    forth is an environment-variable change with 0 seconds of re-ingestion.

    And it SAVES THE MEASUREMENT CHAIN: the `3-small` store is intact, so every old retrieval
    number (baseline 23/47, rerank 38/47, Recall@20 ceiling, 47 golden cases) can still be
    re-measured on exactly the same object — just flip the variable back.
    """
    return f"{_BASE_COLLECTION}__{RAG_EMBEDDING_MODEL}"


def _rename_legacy_store_once(client) -> None:
    """Stores built BEFORE this naming convention live under the bare name `policy_faq`.

    Changing the convention without handling it = 378 vectors become INVISIBLE, and `kiem`
    would report EMPTY and tell people to re-ingest a store that is perfectly correct —
    costing re-embedding money and breaking the measurement chain, exactly the two things
    this convention exists to avoid.

    RENAME rather than re-embed: the vectors stay the same, 0 API calls.

    ⚠️ ONLY rename when the current model REALLY IS the model that built the old store. That
    bare store was built with `text-embedding-3-small` (hard-coded at the time); if someone
    runs for the first time with a different model, labelling old vectors with the new model
    creates exactly the one-sided drift that both `chuan_hoa` and `model_embed` exist to
    prevent.
    """
    if RAG_EMBEDDING_MODEL != "text-embedding-3-small":
        return
    new_name = _collection_name()
    found = {c.name for c in client.list_collections()}
    if _BASE_COLLECTION in found and new_name not in found:
        prev = client.get_collection(_BASE_COLLECTION)
        if prev.count() > 0:
            prev.modify(name=new_name, metadata={"chuan_hoa": NORMALIZATION_VERSION,
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
        # ⚠️ "OpenAI-COMPATIBLE" MEANS COMPATIBLE AT THE HTTP LEVEL, NOT AT THE CLIENT-LIBRARY
        # LEVEL. The endpoint accepts the right path and the right JSON shape, but the
        # `langchain-openai` client sends things only OpenAI accepts. The two errors below CANNOT be
        # found by reading any documentation, only by making real calls — each one costs a 400 and
        # half a day if you don't know in advance.
        #
        # `check_embedding_ctx_length=False` ONLY when pointing at another provider.
        #
        # By default LangChain TOKENISES on the client and sends an ARRAY OF INTEGERS.
        # OpenAI accepts it; Qwen's "OpenAI-compatible" endpoint REJECTS it:
        #   400 InvalidParameter: contents is neither str nor list of str
        # Turning the flag off -> sends raw strings, which every endpoint understands.
        #
        # CONDITIONAL rather than always on: this flag also disables client-side context-length
        # truncation. Our chunks are 800 characters so they never hit the limit, but enabling it on
        # the OpenAI path would CHANGE THE OBJECT on the 378-vector store that anchors the whole
        # measurement chain — don't change something that works correctly to accommodate a provider
        # we don't use yet.
        _embeddings = OpenAIEmbeddings(
            # DUNG CHUNG http_client voi duong chat (src/agents/graph.py) —
            # xem src/egress_gate.py. BAT BUOC o day: duong embedding KHONG
            # di qua graph.py, nen mot chot chan chi cam o duong chat se de lot
            # DUNG duong it cong nhat — va do la duong ca tester lan coder da
            # dam vao trong cung mot ngay (§5.F).
            http_client=shared_http_client(),
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
NORMALIZATION_VERSION = 2


def _get_collection():
    c = _get_client()
    _rename_legacy_store_once(c)
    return c.get_or_create_collection(_collection_name())


def _stamp(col) -> None:
    """Ghi dau phien ban len collection.

    `get_or_create_collection(name, metadata=...)` CHI ap metadata luc TAO. Kho
    da ton tai thi metadata bi BO QUA im lang — do that tren kho demo:
    418 chunk, `metadata = None`. Nen phai `modify()` TUONG MINH sau moi lan
    nap, khong dua vao tham so luc lay collection.
    """
    # Record the embedding model TOO, not just `chuan_hoa` (normalisation). Previously the
    # version stamp only tracked how TEXT was transformed (diacritics stripped or not); the model
    # producing the vectors was hard-coded, so it could not drift. Since `EMBEDDING_MODEL` is read
    # from env, it CAN drift — and that is exactly bug class #2: change the model -> every vector
    # in the store becomes meaningless, yet search still returns k results, no error, no log.
    col.modify(metadata={"chuan_hoa": NORMALIZATION_VERSION, "model_embed": RAG_EMBEDDING_MODEL})


# Ba trang thai PHAN BIET DUOC — gop chung la nguon goc cua bug dau tien:
#   TRONG        kho khong co chunk nao
#   KHONG_DAU    co chunk nhung khong co dau  -> kho CU (dung truoc don 2)
#   LECH         co dau nhung khac phien ban code
#   KHOP         dau == phien ban code
#   LECH_MODEL   dau khop nhung MODEL EMBEDDING khac -> vector vo nghia
STATUS_EMPTY = "trong"
STATUS_NO_STAMP = "khong_dau"
STATUS_DRIFT = "lech"
STATUS_MODEL_DRIFT = "lech_model"
STATUS_MATCH = "khop"


def store_status() -> tuple[str, int | None]:
    """(trang_thai, phien_ban_tren_dia)."""
    col = _get_collection()
    if col.count() == 0:
        return STATUS_EMPTY, None
    pb = (col.metadata or {}).get("chuan_hoa")
    if pb is None:
        return STATUS_NO_STAMP, None
    if pb != NORMALIZATION_VERSION:
        return STATUS_DRIFT, pb
    # Kho dung TRUOC ban nay khong co `model_embed` -> KHONG ket luan lech.
    # Fail-open o day la CO CHU DICH va hep: thieu dau model nghia la kho dung
    # boi code chua biet ghi dau, khi do model chac chan van la mac dinh
    # hardcode cu. Coi no la LECH se bat ca doi nap lai mot kho hoan toan dung.
    # Chi khi CO dau va dau KHAC moi la lech that.
    me = (col.metadata or {}).get("model_embed")
    if me is not None and me != RAG_EMBEDDING_MODEL:
        return STATUS_MODEL_DRIFT, pb
    return STATUS_MATCH, pb


def stores_to_reload() -> bool:
    """True khi kho KHONG dam bao khop phien ban chuan hoa cua code.

    KHONG_DAU tinh la CAN NAP LAI — day la cho ban dau toi lam NGUOC: coi
    "khong co dau" la "khong sao", tuc canh cong bao AN TOAN dung o ca nguy
    hiem nhat (kho dung truoc don 2, chua bo dau, trong khi query da bo dau).
    Mot canh cong sai huong con te hon khong co cong.
    """
    tt, _ = store_status()
    return tt != STATUS_MATCH


def strip_diacritics(s: str) -> str:
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
    """Embed + index. `texts` is only used to COMPUTE embeddings — it must not be stored in
    Chroma; `documents=chunk_ids` is what actually gets written to the collection."""
    if not chunk_ids:
        return
    # Embed ban DA BO DAU — phai khop dung phep chuan hoa o `search()`.
    # Lech mot ve la toan bo index vo dung ma khong co trieu chung nao.
    vectors = _get_embeddings().embed_documents([strip_diacritics(t) for t in texts])
    col = _get_collection()
    col.add(
        ids=chunk_ids,
        embeddings=vectors,
        documents=chunk_ids,  # deliberate: placeholder, NOT real content
        metadatas=[{"doc_id": doc_id} for _ in chunk_ids],
    )
    _stamp(col)


def delete_document(doc_id: str) -> None:
    _get_collection().delete(where={"doc_id": doc_id})


def search(query: str, k: int) -> list[tuple[str, float]]:
    """Returns [(chunk_id, distance)], nearest first. Smaller distance = more relevant
    (Chroma defaults to cosine/L2 depending on config; the agent need not care — it is only
    used for ordering)."""
    collection = _get_collection()
    if collection.count() == 0:
        return []
    vector = _get_embeddings().embed_query(strip_diacritics(query))
    result = collection.query(query_embeddings=[vector], n_results=min(k, collection.count()))
    ids = result.get("ids", [[]])[0]
    distances = result.get("distances", [[]])[0]
    return list(zip(ids, distances))
