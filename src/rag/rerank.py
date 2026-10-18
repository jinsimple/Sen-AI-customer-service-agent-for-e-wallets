"""Layer-2 abstention gate (ADR-061, Finding ①) — calls the rerank SIDECAR over HTTP.

WHY A SIDECAR instead of loading the model in-process (measured, see the ADR-061 update of
04/09): the backend runs 4-5 INDEPENDENT uvicorn worker processes — loading the
cross-encoder here would multiply RAM by the worker count (measured 3.2-5 GB).
`rerank_service/` is a SEPARATE service that loads the model exactly ONCE; all workers
share it over the internal HTTP (docker network).

🔴 INVARIANT (ADR-061): a dead/timed-out sidecar or a network error MUST NOT CRASH
`search_policy_text`. It is treated as "no candidate passed rerank" (empty list)
⟹ the caller sees `results=[]` ⟹ `status=not_found`. Why fail-closed rather than
"return UNFILTERED results when the sidecar is down": returning unfiltered results then
recreates Finding ① IN FULL exactly when Layer 2 is needed most — a breach of hard
constraint #3. Accepted trade-off: an unstable sidecar ⟹ the feature is less available
(more not_found), which is safer than available-but-wrong.
"""
from __future__ import annotations

import httpx

from src.config import RAG_RERANK_SERVICE_URL, RAG_RERANK_THRESHOLD, RAG_RERANK_TIMEOUT_S
from src.observability.logging_config import get_logger

_logger = get_logger("fin05.rag")


def rerank_and_filter(
    query: str, candidate: list[tuple[str, str]], *, threshold: float | None = None
) -> list[tuple[str, float]]:
    """`candidate`: [(chunk_id, text), ...] — RAW candidates from Chroma.

    Returns [(chunk_id, score), ...] containing ONLY candidates with score >= threshold,
    SORTED by descending score. Empty when: every candidate is below the threshold (by
    design), OR the sidecar is unreachable (fail-closed fallback — see the module
    docstring), OR `RAG_RERANK_SERVICE_URL` is not configured (feature fully disabled for
    this stack, not an error).

    `threshold`: `None` (default) uses `RAG_RERANK_THRESHOLD` (the agent path, the
    5 tools of `build_customer_tools` — UNCHANGED). Pass it explicitly when the caller needs
    a different threshold (see `search_policy_text` — the CSKH `/policy-search` path uses
    `RAG_RERANK_THRESHOLD_CSKH`, fixed by the PO on 05/09: excerpts for a HUMAN reader, not
    AI assertions, so the recall/precision trade-off can be tuned INDEPENDENTLY of the
    agent path).
    """
    if threshold is None:
        threshold = RAG_RERANK_THRESHOLD
    if not candidate:
        return []
    if not RAG_RERANK_SERVICE_URL:
        _logger.info("rag_rerank_tat", extra={"ly_do": "RAG_RERANK_SERVICE_URL rỗng"})
        return []

    payload = {
        "query": query,
        "ung_vien": [{"chunk_id": cid, "text": text} for cid, text in candidate],
    }
    # 🔴 Review 04/09: the previous version only wrapped try/except around the HTTP call +
    # `.json()` (network/timeout/HTTP error) — READING the response schema (`item["chunk_id"]`,
    # `item["score"]`, `data["ket_qua"][0]["score"]` in the log line) sat OUTSIDE it,
    # so a sidecar returning 200 with WRONG-SCHEMA JSON (missing key / score not parseable as a
    # number) would raise `KeyError`/`ValueError`/`IndexError` straight out, NOT falling into
    # the fail-closed fallback — exactly the invariant breach described in the module docstring.
    # All reading of `data` now lives in the SAME protected block as the network call — EVERY
    # error from sending the request to finishing reading the response fails closed the same
    # way, with no gap between the two.
    try:
        resp = httpx.post(
            f"{RAG_RERANK_SERVICE_URL}/rerank",
            json=payload,
            timeout=RAG_RERANK_TIMEOUT_S,
        )
        resp.raise_for_status()
        data = resp.json()

        over_threshold = [
            (item["chunk_id"], float(item["score"]))
            for item in data.get("ket_qua", [])
            if float(item["score"]) >= threshold
        ]
        _logger.info(
            "rag_rerank",
            extra={
                "so_ung_vien": len(candidate),
                "so_qua_nguong": len(over_threshold),
                "diem_cao_nhat": data["ket_qua"][0]["score"] if data.get("ket_qua") else None,
                "nguong": threshold,
            },
        )
        return over_threshold
    except Exception as e:
        # EXACTLY the group of errors that fail closed: network/timeout/HTTP error/broken JSON/
        # WRONG SCHEMA (missing key, unparseable score) — all treated as "sidecar unreachable/
        # unusable", WITHOUT distinguishing error types (deliberate simplification: distinguishing
        # further would not change behaviour, only log detail).
        _logger.warning(
            "rag_rerank_sidecar_loi",
            extra={"loi": str(e), "loi_kieu": type(e).__name__, "service_url": RAG_RERANK_SERVICE_URL},
        )
        return []
