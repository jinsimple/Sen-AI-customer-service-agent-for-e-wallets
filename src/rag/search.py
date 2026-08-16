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

from src.config import FIELD_ENCRYPTION_KEY, RAG_SEARCH_TOP_K
from src.db.models import PolicyChunk, PolicyDocument
from src.observability.logging_config import get_logger
from src.rag import store
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
) -> dict:
    """Trả {"status": "found"|"not_found", "results": [...], "tool_result_id": ...}.
    Mỗi result: {"text", "source_filename", "doc_id"} — không kèm chunk_id/
    score ra ngoài, giữ output gọn cho cả agent lẫn UI CSKH.

    `duong_tra`: "agent" (qua tool, CÓ lọc tier ở `_sanitize_policy_results`) hoặc
    "cskh" (POST /policy-search, CỐ Ý không lọc — Y5). Chỉ dùng để ghi log:
    hai đường cùng chạm một hàm nhưng hậu quả khác nhau, hồ sơ sự cố phải
    phân biệt được mà không phải suy.
    """
    hits = store.search(query, k=k)

    results: list[dict] = []
    chunk_ids_tra_ve: list[str] = []
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
        # Giữ đúng thứ tự liên quan Chroma trả về (gần nhất trước), bỏ qua
        # chunk_id không còn tồn tại (tài liệu vừa bị xoá nhưng index chưa kịp
        # đồng bộ — hiếm, không nên chặn cả lượt tra cứu).
        for chunk_id, _distance in hits:
            chunk = chunks_by_id.get(chunk_id)
            if chunk is None:
                continue
            doc = docs_by_id.get(chunk.doc_id)
            chunk_ids_tra_ve.append(chunk_id)
            results.append(
                {
                    "text": chunk.text,
                    "source_filename": doc.filename if doc else "(không rõ nguồn)",
                    "doc_id": chunk.doc_id,
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
    bo_qua = len(hits) - len(results)
    _logger.info(
        "policy_search",
        extra={
            "duong_tra": duong_tra,
            "qua_loc_tier": duong_tra == "agent",
            "query_hash": _bam_truy_van(query),
            "query_len": len(query),
            "k": k,
            "so_hit_chroma": len(hits),
            "so_ket_qua": len(results),
            "bo_qua_thieu_chunk": bo_qua,
            "chunk_ids": chunk_ids_tra_ve,
            "doc_ids": sorted({r["doc_id"] for r in results}),
            "status": payload["status"],
        },
    )
    if bo_qua > 0:
        _logger.warning(
            "policy_search_lech_kho",
            extra={
                "so_hit_chroma": len(hits),
                "so_ket_qua": len(results),
                "bo_qua_thieu_chunk": bo_qua,
                "ghi_chu": "Chroma trả chunk_id mà Postgres không có — "
                "gần như chắc chắn tiến trình phục vụ đang cầm segment cũ. "
                "Xem scripts/kho_rag.py::_server_dang_cam_kho_cu.",
            },
        )
    return payload
