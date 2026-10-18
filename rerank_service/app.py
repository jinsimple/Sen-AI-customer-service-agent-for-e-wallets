"""ADR-061 (Finding ① Lớp 2) — service RIÊNG cho cross-encoder rerank.

VÌ SAO SERVICE RIÊNG, không nằm trong backend chính (đọc ADR-061, cập nhật
04/09 trước khi sửa gì ở đây): backend chạy 4-5 tiến trình uvicorn worker
ĐỘC LẬP (multiprocessing) — load model trực tiếp trong backend sẽ nhân RAM
theo số worker (đo được: 3,2-5GB). Service này load model ĐÚNG MỘT LẦN, mọi
worker backend gọi qua HTTP nội bộ (docker network `fin05-po-demo_default`
hoặc tương đương) thay vì tự load — RAM cố định ~1 instance bất kể backend
có bao nhiêu worker.

Không xác thực (JWT) — CHỈ nghe trên mạng nội bộ compose, không publish ra
Caddy/ra ngoài (xem docker-compose.yml, service này KHÔNG có `ports:` publish
ra host). Nếu sau này cần public, phải thêm xác thực trước, không giả định
"nội bộ = an toàn mãi mãi".
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

MODEL_NAME = os.environ.get("RAG_RERANK_MODEL", "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1")

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import CrossEncoder

        _model = CrossEncoder(MODEL_NAME, max_length=512)
    return _model


@asynccontextmanager
async def lifespan(app: FastAPI):
    # [04/09, PO bắt qua log thật] Model trước đây chỉ tải LƯỜI (lần gọi
    # `/rerank` ĐẦU TIÊN) — `/health` (bên dưới) trả lời ngay mà KHÔNG đụng
    # model, nên container báo "healthy" trong khi request thật đầu tiên vẫn
    # phải đợi tải model xong. Trên VM RAM mỏng, thời gian tải đó vượt
    # `RAG_RERANK_TIMEOUT_S` (mặc định 5s) → backend fail-closed → not_found
    # oan cho câu hỏi ĐÚNG (đo được: "hoàn tiền" — không phải kho rỗng, không
    # phải lỗi ngưỡng, thuần tuý cold-start). Tải model NGAY LÚC KHỞI ĐỘNG,
    # CHẶN (không async) trước khi Uvicorn nhận request — kết hợp
    # `start_period: 60s` của healthcheck (docker-compose.yml), lần gọi
    # `/rerank` THẬT ĐẦU TIÊN không còn phải trả giá tải model nữa.
    _get_model()
    yield


app = FastAPI(title="fin05-rerank-sidecar", lifespan=lifespan)


class Ung_vien(BaseModel):
    chunk_id: str
    text: str


class RerankRequest(BaseModel):
    query: str
    candidate: list[Ung_vien]


class RerankResultItem(BaseModel):
    chunk_id: str
    score: float


class RerankResponse(BaseModel):
    outcome: list[RerankResultItem]


@app.get("/health")
def health() -> dict:
    # Vẫn KHÔNG tự đụng model ở đây (đúng nguyên tắc liveness thuần,
    # CLAUDE.md) — model giờ đã tải xong TRƯỚC KHI Uvicorn nhận request nào
    # (xem `lifespan` ở trên), nên endpoint này không còn "đua" với việc tải
    # model như trước 04/09, chỉ đơn thuần không có lý do gì để chạm vào nó.
    return {"status": "ok", "model": MODEL_NAME}


@app.post("/rerank", response_model=RerankResponse)
def rerank(req: RerankRequest) -> RerankResponse:
    if not req.candidate:
        return RerankResponse(outcome=[])
    model = _get_model()
    pairs = [(req.query, uv.text) for uv in req.candidate]
    scores = model.predict(pairs)
    outcome = [
        RerankResultItem(chunk_id=uv.chunk_id, score=float(s))
        for uv, s in zip(req.candidate, scores)
    ]
    outcome.sort(key=lambda x: x.score, reverse=True)
    return RerankResponse(outcome=outcome)
