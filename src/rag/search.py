"""Policy/FAQ search — the SINGLE entry point shared by the agent tool
(`search_policy`, src/agents/tools/customer_tools.py) and the CSKH endpoint
(`POST /policy-search`, src/api/main.py).

2 steps: ask Chroma for chunk_ids by similarity (src/rag/store.py), then decrypt the real
text from SQL (policy_chunks.text is EncryptedText) — see store.py for why it is split into
2 steps instead of asking Chroma directly.
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

# A SEPARATE key for log hashing, derived from a key that is already mandatory (fail-fast in
# config), so no new environment variable is needed. The `info` string separates usage
# domains — log hashing and column encryption never share key material.
_LOG_HASH_KEY = hmac.new(
    FIELD_ENCRYPTION_KEY.encode(), b"fin05-log-query-hash-v1", hashlib.sha256
).digest()


def _hash_query(query: str) -> str:
    """HMAC of the query — NOT a single character of content is stored.

    Why not log the raw text, and why not log a scrubbed version either (security's
    suggestion, which I followed): `scrub_pii` over-blocks 40% of Vietnamese business text
    (S-01), and policy queries ARE exactly that kind of text. A "scrubbed query" yields a
    string that can still leak AND has lost its meaning — bad on both ends, and useless as
    evidence because nobody knows which words were removed.

    Hash + length answer exactly the two questions an incident record needs: "how many
    times was the same query repeated" and "machine burst or human typing".
    """
    return hmac.new(_LOG_HASH_KEY, query.encode(), hashlib.sha256).hexdigest()[:16]


def search_policy_text(
    session: Session,
    *,
    query: str,
    k: int = RAG_SEARCH_TOP_K,
    lookup_path: str = "khong_ro",
    scope: str | None = None,
) -> dict:
    """Returns {"status": "found"|"not_found", "results": [...], "tool_result_id": ...}.
    Each result: {"text", "source_filename", "doc_id", "chunk_id"} — score is NOT exposed.
    `chunk_id` added 05/09 (ADR-065) so the FE can build the "View full text" deep link —
    not PII; the agent path ignores this extra field.

    `lookup_path`: "agent" (via the tool, WITH tier filtering in `_sanitize_policy_results`)
    or "cskh" (POST /policy-search, DELIBERATELY unfiltered — Y5). Used for logging (both
    paths hit the same function but with different consequences; the incident record must
    tell them apart without guessing) AND (05/09, decided by the PO) to pick the rerank
    threshold: "cskh" uses `RAG_RERANK_THRESHOLD_CSKH` (recall first — a human reads the
    excerpt directly, no AI assertion), "agent" keeps the default `RAG_RERANK_THRESHOLD`
    (behaviour/precision unchanged).

    `scope`: ADR-061 Layer 1. `None` = NO filtering (exactly the behaviour before Layer 1 —
    the agent path's state TODAY, `build_customer_tools()` has no scope to pass). With a
    value (one of 4: internal_wallet/from_bank/to_bank/unknown) ⟹ only keep candidates with
    `chunk.scope == scope` OR `chunk.scope == "unknown"` (chunks orthogonal to every scope —
    see ADR-061 §5.2). 🔴 UNASSIGNED chunks (`chunk.scope is None`, backfill not yet run /
    freshly uploaded chunk) are filtered out — treated as matching NO specific scope (safe:
    better to miss one than to let through a chunk nobody has confirmed).

    ADR-061 Layer 2: fetch RAG_RERANK_CANDIDATE_K candidates (WIDER than the final `k` —
    the 03/09 measurement REL-IW-01 showed a narrow top-1/top-k can miss the right chunk
    sitting further down the distance-sorted list), filter by scope (if any), rerank the
    REMAINDER with a cross-encoder, drop chunks below RAG_RERANK_THRESHOLD — this IS the
    abstention gate, not a secondary filter.
    """
    hits = store.search(query, k=RAG_RERANK_CANDIDATE_K)

    results: list[dict] = []
    returned_chunk_ids: list[str] = []
    skipped_missing_chunk = 0
    scope_filtered_count = 0
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
        # RAW candidates for rerank — skip chunk_ids that no longer exist (document just deleted
        # but the index hasn't synced yet). Counted separately as
        # `skipped_missing_chunk` (Chroma/Postgres drift) — ENTIRELY different from candidates
        # rerank drops as irrelevant; two different reasons for "disappearing", never merged in
        # the log.
        # ADR-061 Layer 1 — filter by scope BEFORE rerank (cheaper: no sidecar call for candidates
        # already known to be out of scope). `scope is None` ⟹ no filtering (exactly the pre-Layer-1
        # branch).
        candidate: list[tuple[str, str]] = []
        for chunk_id, _distance in hits:
            chunk = chunks_by_id.get(chunk_id)
            if chunk is None:
                skipped_missing_chunk += 1
                continue
            if scope is not None and chunk.scope not in (scope, "unknown"):
                scope_filtered_count += 1
                continue
            candidate.append((chunk_id, chunk.text))

        # Decided by the PO 05/09 — a SEPARATE threshold for the CSKH path (`/policy-search`, see
        # main.py): the page shows excerpts directly, with no AI synthesis/assertion (the page
        # subtitle says so), so the precision concern of Finding ① does not apply — recall is
        # prioritised for short queries/keywords. The agent path
        # (`lookup_path="agent"`, 5 tools) keeps the default `RAG_RERANK_THRESHOLD` UNCHANGED
        # (passes `None` to `rerank_and_filter` — old behaviour unchanged).
        threshold_value = RAG_RERANK_THRESHOLD_CSKH if lookup_path == "cskh" else None
        over_threshold = rerank.rerank_and_filter(query, candidate, threshold=threshold_value)[:k]
        for chunk_id, _score in over_threshold:
            chunk = chunks_by_id[chunk_id]
            doc = docs_by_id.get(chunk.doc_id)
            returned_chunk_ids.append(chunk_id)
            results.append(
                {
                    "text": chunk.text,
                    "source_filename": doc.filename if doc else "(không rõ nguồn)",
                    "doc_id": chunk.doc_id,
                    # ADR-065 — used by the FE to build the "View full text" deep link
                    # (GET /policy-doc/{doc_id}?chunk_id=...). chunk_id is not
                    # PII and does not widen read scope (the target route itself
                    # checks chunk.doc_id matches doc_id).
                    "chunk_id": chunk_id,
                }
            )

    payload = {"status": "found" if results else "not_found", "results": results}
    tool_result_id = record_tool_result(session, "search_policy", payload)
    payload["tool_result_id"] = tool_result_id

    # F-LOG-3. Fields chosen by the INCIDENT QUESTION, not "log everything":
    # "within window X→Y, who received content from document Z?" — `user_id` +
    # `chunk_id[]`/`doc_id[]` answer it directly, without needing the query content.
    # `user_id`/`correlation_id` are added by the formatter from contextvars, not passed by hand.
    #
    # `skipped_missing_chunk` — a field I ADDED beyond the spec, because it is what hid
    # today's bug: the loop above SILENTLY skipped chunk_ids Postgres no longer had. When the
    # server holds a deleted Chroma segment, Chroma still returns k hits with OLD chunk_ids, all
    # are skipped, `results` is empty, `status="not_found"` — looking exactly like "nothing
    # found". Two numbers side by side make it obvious to a machine: hits > 0 but all skipped =
    # Chroma and Postgres are talking about two different stores.
    #
    # 🔴 ADR-061: NO LONGER computed as `len(hits) - len(results)` — that difference mixes ALL
    # THREE different causes (missing in Postgres / filtered out by scope / dropped by rerank as
    # irrelevant OR fell outside the final top-k). Three separate counts let the log answer
    # "why are there fewer results than hits" without guessing.
    rerank_rejected_count = len(hits) - skipped_missing_chunk - scope_filtered_count - len(results)
    _logger.info(
        "policy_search",
        extra={
            "duong_tra": lookup_path,
            "qua_loc_tier": lookup_path == "agent",
            "query_hash": _hash_query(query),
            "query_len": len(query),
            "k": k,
            "scope_loc": scope,
            "so_hit_chroma": len(hits),
            "so_ket_qua": len(results),
            "bo_qua_thieu_chunk": skipped_missing_chunk,
            "so_bi_loc_scope": scope_filtered_count,
            "so_bi_rerank_loai": rerank_rejected_count,
            "chunk_ids": returned_chunk_ids,
            "doc_ids": sorted({r["doc_id"] for r in results}),
            "status": payload["status"],
        },
    )
    if skipped_missing_chunk > 0:
        _logger.warning(
            "policy_search_lech_kho",
            extra={
                "so_hit_chroma": len(hits),
                "so_ket_qua": len(results),
                "bo_qua_thieu_chunk": skipped_missing_chunk,
                "ghi_chu": "Chroma trả chunk_id mà Postgres không có — "
                "gần như chắc chắn tiến trình phục vụ đang cầm segment cũ. "
                "Xem scripts/kho_rag.py::_server_dang_cam_kho_cu.",
            },
        )
    return payload
