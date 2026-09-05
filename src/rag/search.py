"""Tra cứu chính sách/FAQ — điểm vào DUY NHẤT dùng chung bởi tool agent
(`search_policy`, src/agents/tools/customer_tools.py) và endpoint CSKH
(`POST /policy-search`, src/api/main.py).

2 bước: hỏi Chroma lấy chunk_id theo độ tương đồng (src/rag/store.py) rồi
giải mã text thật từ SQLite (policy_chunks.text là EncryptedText) — xem
store.py để hiểu vì sao tách 2 bước thay vì hỏi thẳng Chroma.
"""
from __future__ import annotations

import hashlib
import hmac

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.config import (
    FIELD_ENCRYPTION_KEY,
    RAG_RERANK_CANDIDATE_K,
    RAG_RERANK_THRESHOLD_CSKH,
    RAG_SEARCH_TOP_K,
)
from src.db.models import PolicyChunk, PolicyDocument
from src.observability.logging_config import get_logger
from src.rag import rerank, store
from src.tools.base import record_tool_result

_logger = get_logger("fin05.rag")

# Khoá RIÊNG cho băm log, dẫn xuất từ khoá đã bắt buộc có (fail-fast ở config)
# nên không thêm biến môi trường mới. Chuỗi `info` tách miền sử dụng — băm log
# và mã hoá cột không bao giờ dùng chung nguyên liệu khoá.
_KHOA_BAM_LOG = hmac.new(
    FIELD_ENCRYPTION_KEY.encode(), b"fin05-log-query-hash-v1", hashlib.sha256
).digest()


def _bam_truy_van(query: str) -> str:
    """HMAC của câu tra — KHÔNG lưu một ký tự nội dung nào.

    Vì sao không log nguyên văn, và vì sao cũng không log bản đã scrub (đề
    xuất của security, tôi theo): `scrub_pii` chặn nhầm 40% trên văn bản
    nghiệp vụ tiếng Việt (S-01), mà câu tra chính sách CHÍNH LÀ loại văn bản
    đó. "Query đã scrub" cho ra chuỗi vừa còn khả năng rò, vừa hỏng nghĩa —
    tệ cả hai đầu, và vô dụng làm bằng chứng vì không ai biết chữ nào đã mất.

    Băm + độ dài trả lời được đúng hai câu hồ sơ sự cố cần: "cùng một câu lặp
    bao nhiêu lần" và "burst máy hay người gõ".
    """
    return hmac.new(_KHOA_BAM_LOG, query.encode(), hashlib.sha256).hexdigest()[:16]


def search_policy_text(
    session: Session,
    *,
    query: str,
    k: int = RAG_SEARCH_TOP_K,
    duong_tra: str = "khong_ro",
    scope: str | None = None,
) -> dict:
    """Trả {"status": "found"|"not_found", "results": [...], "tool_result_id": ...}.
    Mỗi result: {"text", "source_filename", "doc_id", "chunk_id"} — KHÔNG kèm
    score ra ngoài. `chunk_id` thêm 05/09 (ADR-065) cho FE dựng deep-link
    "Xem toàn văn" — không phải PII, agent path bỏ qua field thừa này.

    `duong_tra`: "agent" (qua tool, CÓ lọc tier ở `_sanitize_policy_results`) hoặc
    "cskh" (POST /policy-search, CỐ Ý không lọc — Y5). Dùng để ghi log (hai
    đường cùng chạm một hàm nhưng hậu quả khác nhau, hồ sơ sự cố phải phân
    biệt được mà không phải suy) VÀ (05/09, PO chốt) chọn ngưỡng rerank:
    "cskh" dùng `RAG_RERANK_THRESHOLD_CSKH` (ưu tiên recall — người đọc
    excerpt trực tiếp, không phải AI khẳng định), "agent" giữ nguyên
    `RAG_RERANK_THRESHOLD` mặc định (không đổi hành vi/precision).

    `scope`: ADR-061 Lớp 1. `None` = KHÔNG lọc (hành vi y hệt trước khi có
    Lớp 1 — đúng trạng thái đường agent HÔM NAY, `build_customer_tools()`
    không có scope nào để truyền). Có giá trị (1 trong 4: internal_wallet/
    from_bank/to_bank/unknown) ⟹ chỉ giữ ứng viên có `chunk.scope == scope`
    HOẶC `chunk.scope == "unknown"` (chunk trực giao mọi phạm vi — xem
    ADR-061 §5.2). 🔴 Lọc CHUNK CHƯA GÁN (`chunk.scope is None`, backfill
    chưa chạy/chunk mới upload) — coi như KHÔNG khớp bất kỳ scope cụ thể nào
    (an toàn: thà bỏ sót còn hơn cho qua nhầm một chunk chưa ai xác nhận).

    ADR-061 Lớp 2: lấy RAG_RERANK_CANDIDATE_K ứng viên (RỘNG hơn `k` cuối
    cùng — ca đo 03/09 REL-IW-01 cho thấy top-1/top-k hẹp có thể bỏ lỡ chunk
    đúng nằm xa hơn trong danh sách gần theo distance), lọc scope (nếu có),
    rerank phần CÒN LẠI bằng cross-encoder, loại chunk dưới ngưỡng
    RAG_RERANK_THRESHOLD — đây CHÍNH LÀ cổng abstention, không phải bộ lọc phụ.
    """
    hits = store.search(query, k=RAG_RERANK_CANDIDATE_K)

    results: list[dict] = []
    chunk_ids_tra_ve: list[str] = []
    bo_qua_thieu_chunk = 0
    so_bi_loc_scope = 0
    if hits:
        chunk_ids = [chunk_id for chunk_id, _ in hits]
        rows = session.scalars(
            select(PolicyChunk).where(PolicyChunk.chunk_id.in_(chunk_ids))
        ).all()
        chunks_by_id = {c.chunk_id: c for c in rows}
        doc_ids = {c.doc_id for c in rows}
        docs_by_id = {
            d.doc_id: d for d in session.scalars(select(PolicyDocument).where(PolicyDocument.doc_id.in_(doc_ids))).all()
        }
        # Ứng viên THÔ cho rerank — bỏ qua chunk_id không còn tồn tại (tài
        # liệu vừa bị xoá nhưng index chưa kịp đồng bộ). Đếm riêng
        # `bo_qua_thieu_chunk` (lệch Chroma/Postgres) — KHÁC hẳn ứng viên bị
        # rerank loại vì không liên quan, hai nguyên nhân "biến mất" khác
        # nhau, không được gộp log chung.
        # ADR-061 Lớp 1 — lọc scope TRƯỚC khi đưa vào rerank (rẻ hơn: khỏi
        # tốn lời gọi sidecar cho ứng viên đã biết chắc sai phạm vi). `scope
        # is None` ⟹ không lọc gì (nhánh y hệt trước khi có Lớp 1).
        ung_vien: list[tuple[str, str]] = []
        for chunk_id, _distance in hits:
            chunk = chunks_by_id.get(chunk_id)
            if chunk is None:
                bo_qua_thieu_chunk += 1
                continue
            if scope is not None and chunk.scope not in (scope, "unknown"):
                so_bi_loc_scope += 1
                continue
            ung_vien.append((chunk_id, chunk.text))

        # PO chốt 05/09 — ngưỡng RIÊNG cho đường CSKH (`/policy-search`, xem
        # main.py): trang đọc excerpt trực tiếp, không qua AI tổng hợp/khẳng
        # định (phụ đề trang tự khai điều đó), nên mối lo precision Finding
        # ① không áp dụng — ưu tiên recall cho câu ngắn/từ khoá. Đường agent
        # (`duong_tra="agent"`, 5 tool) giữ NGUYÊN `RAG_RERANK_THRESHOLD` mặc
        # định (truyền `None` cho `rerank_va_loc` — không đổi hành vi cũ).
        nguong = RAG_RERANK_THRESHOLD_CSKH if duong_tra == "cskh" else None
        qua_nguong = rerank.rerank_va_loc(query, ung_vien, threshold=nguong)[:k]
        for chunk_id, _score in qua_nguong:
            chunk = chunks_by_id[chunk_id]
            doc = docs_by_id.get(chunk.doc_id)
            chunk_ids_tra_ve.append(chunk_id)
            results.append(
                {
                    "text": chunk.text,
                    "source_filename": doc.filename if doc else "(không rõ nguồn)",
                    "doc_id": chunk.doc_id,
                    # ADR-065 — FE dùng dựng link deep-link "Xem toàn văn"
                    # (GET /policy-doc/{doc_id}?chunk_id=...). chunk_id không
                    # phải PII, không mở thêm phạm vi đọc (route đích tự
                    # kiểm chunk.doc_id khớp doc_id).
                    "chunk_id": chunk_id,
                }
            )

    payload = {"status": "found" if results else "not_found", "results": results}
    tool_result_id = record_tool_result(session, "search_policy", payload)
    payload["tool_result_id"] = tool_result_id

    # F-LOG-3. Trường chọn theo CÂU HỎI SỰ CỐ, không theo "log cho đủ":
    # "trong cửa sổ X→Y, ai nhận được nội dung từ tài liệu Z?" — `user_id` +
    # `chunk_id[]`/`doc_id[]` trả lời thẳng, không cần tới nội dung truy vấn.
    # `user_id`/`correlation_id` do formatter lấy từ contextvars, không truyền tay.
    #
    # `bo_qua_thieu_chunk` — trường TỰ TÔI THÊM ngoài đặc tả, vì nó là thứ đã
    # giấu bug hôm nay: vòng lặp trên ÂM THẦM bỏ qua chunk_id mà Postgres không
    # còn. Khi server cầm segment Chroma đã bị xoá, Chroma vẫn trả đủ k hit
    # bằng chunk_id CŨ, tất cả bị bỏ, `results` rỗng, `status="not_found"` —
    # trông y hệt "không tìm thấy gì". Hai số cạnh nhau thì máy nhìn ra ngay:
    # hit > 0 mà bỏ hết = Chroma và Postgres đang nói về hai kho khác nhau.
    #
    # 🔴 ADR-061: KHÔNG còn tính bằng `len(hits) - len(results)` — hiệu số đó
    # lẫn CẢ BA nguyên nhân khác nhau (thiếu ở Postgres / bị lọc sai scope /
    # bị rerank loại vì không liên quan HOẶC rớt ngoài top-k cuối). Ba số
    # đếm riêng để log trả lời được "vì sao results ít hơn hits" mà không
    # cần suy đoán.
    so_bi_rerank_loai = len(hits) - bo_qua_thieu_chunk - so_bi_loc_scope - len(results)
    _logger.info(
        "policy_search",
        extra={
            "duong_tra": duong_tra,
            "qua_loc_tier": duong_tra == "agent",
            "query_hash": _bam_truy_van(query),
            "query_len": len(query),
            "k": k,
            "scope_loc": scope,
            "so_hit_chroma": len(hits),
            "so_ket_qua": len(results),
            "bo_qua_thieu_chunk": bo_qua_thieu_chunk,
            "so_bi_loc_scope": so_bi_loc_scope,
            "so_bi_rerank_loai": so_bi_rerank_loai,
            "chunk_ids": chunk_ids_tra_ve,
            "doc_ids": sorted({r["doc_id"] for r in results}),
            "status": payload["status"],
        },
    )
    if bo_qua_thieu_chunk > 0:
        _logger.warning(
            "policy_search_lech_kho",
            extra={
                "so_hit_chroma": len(hits),
                "so_ket_qua": len(results),
                "bo_qua_thieu_chunk": bo_qua_thieu_chunk,
                "ghi_chu": "Chroma trả chunk_id mà Postgres không có — "
                "gần như chắc chắn tiến trình phục vụ đang cầm segment cũ. "
                "Xem scripts/kho_rag.py::_server_dang_cam_kho_cu.",
            },
        )
    return payload
