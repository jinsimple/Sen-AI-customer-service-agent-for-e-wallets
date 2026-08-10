"""Tra cứu chính sách/FAQ — điểm vào DUY NHẤT dùng chung bởi tool agent
(`search_policy`, src/agents/tools/customer_tools.py) và endpoint CSKH
(`POST /policy-search`, src/api/main.py).

2 bước: hỏi Chroma lấy chunk_id theo độ tương đồng (src/rag/store.py) rồi
giải mã text thật từ SQLite (policy_chunks.text là EncryptedText) — xem
store.py để hiểu vì sao tách 2 bước thay vì hỏi thẳng Chroma.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.config import RAG_SEARCH_TOP_K
from src.db.models import PolicyChunk, PolicyDocument
from src.rag import store
from src.tools.base import record_tool_result


def search_policy_text(session: Session, *, query: str, k: int = RAG_SEARCH_TOP_K) -> dict:
    """Trả {"status": "found"|"not_found", "results": [...], "tool_result_id": ...}.
    Mỗi result: {"text", "source_filename", "doc_id"} — không kèm chunk_id/
    score ra ngoài, giữ output gọn cho cả agent lẫn UI CSKH."""
    hits = store.search(query, k=k)

    results: list[dict] = []
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
    return payload
