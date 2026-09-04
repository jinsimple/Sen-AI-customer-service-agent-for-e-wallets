"""Cổng abstention Lớp 2 (ADR-061, Finding ①) — gọi SIDECAR rerank qua HTTP.

VÌ SAO SIDECAR thay vì load model tại chỗ (đã đo, xem ADR-061 cập nhật 04/09):
backend chạy 4-5 tiến trình uvicorn worker ĐỘC LẬP — load cross-encoder trực
tiếp ở đây sẽ nhân RAM theo số worker (đo được 3,2-5GB). `rerank_service/`
là service RIÊNG load model đúng MỘT LẦN, mọi worker gọi chung qua HTTP nội
bộ (docker network).

🔴 RÀNG BUỘC BẤT DI (ADR-061): sidecar chết/timeout/lỗi mạng KHÔNG ĐƯỢC LÀM
`search_policy_text` CRASH. Coi như "không có ứng viên nào qua được rerank"
(danh sách rỗng) ⟹ tầng gọi thấy `results=[]` ⟹ `status=not_found`. Lý do
chọn fail-closed thay vì "trả kết quả CHƯA lọc khi sidecar hỏng": trả chưa
lọc lúc sidecar hỏng tái tạo NGUYÊN VẸN Finding ① đúng lúc cần Lớp 2 nhất —
vi phạm Ràng buộc cứng #3. Đánh đổi chấp nhận: sidecar không ổn định ⟹ tính
năng kém khả dụng hơn (nhiều not_found hơn), an toàn hơn khả dụng-nhưng-sai.
"""
from __future__ import annotations

import httpx

from src.config import RAG_RERANK_SERVICE_URL, RAG_RERANK_THRESHOLD, RAG_RERANK_TIMEOUT_S
from src.observability.logging_config import get_logger

_logger = get_logger("fin05.rag")


def rerank_va_loc(query: str, ung_vien: list[tuple[str, str]]) -> list[tuple[str, float]]:
    """`ung_vien`: [(chunk_id, text), ...] — ứng viên THÔ từ Chroma.

    Trả về [(chunk_id, score), ...] CHỈ gồm ứng viên score >= RAG_RERANK_THRESHOLD,
    sắp XẾP GIẢM DẦN theo score. Rỗng khi: tất cả ứng viên dưới ngưỡng (đúng
    thiết kế), HOẶC sidecar không tới được (fallback fail-closed — xem
    docstring module), HOẶC `RAG_RERANK_SERVICE_URL` chưa cấu hình (tính năng
    tắt hẳn cho ngăn này, không phải lỗi).
    """
    if not ung_vien:
        return []
    if not RAG_RERANK_SERVICE_URL:
        _logger.info("rag_rerank_tat", extra={"ly_do": "RAG_RERANK_SERVICE_URL rỗng"})
        return []

    payload = {
        "query": query,
        "ung_vien": [{"chunk_id": cid, "text": text} for cid, text in ung_vien],
    }
    try:
        resp = httpx.post(
            f"{RAG_RERANK_SERVICE_URL}/rerank",
            json=payload,
            timeout=RAG_RERANK_TIMEOUT_S,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        # ĐÚNG NHÓM lỗi được fail-closed: mạng/timeout/HTTP lỗi/JSON hỏng —
        # tất cả coi như "sidecar không tới được", KHÔNG phân biệt loại lỗi
        # (đơn giản hoá có chủ đích: phân biệt thêm không đổi hành vi, chỉ
        # đổi chi tiết log).
        _logger.warning(
            "rag_rerank_sidecar_loi",
            extra={"loi": str(e), "service_url": RAG_RERANK_SERVICE_URL},
        )
        return []

    qua_nguong = [
        (item["chunk_id"], float(item["score"]))
        for item in data.get("ket_qua", [])
        if float(item["score"]) >= RAG_RERANK_THRESHOLD
    ]
    _logger.info(
        "rag_rerank",
        extra={
            "so_ung_vien": len(ung_vien),
            "so_qua_nguong": len(qua_nguong),
            "diem_cao_nhat": data["ket_qua"][0]["score"] if data.get("ket_qua") else None,
            "nguong": RAG_RERANK_THRESHOLD,
        },
    )
    return qua_nguong
