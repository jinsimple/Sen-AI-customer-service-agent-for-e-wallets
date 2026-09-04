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

from fastapi import FastAPI
from pydantic import BaseModel

MODEL_NAME = os.environ.get("RAG_RERANK_MODEL", "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1")

app = FastAPI(title="fin05-rerank-sidecar")

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import CrossEncoder

        _model = CrossEncoder(MODEL_NAME, max_length=512)
    return _model


class Ung_vien(BaseModel):
    chunk_id: str
    text: str


class RerankRequest(BaseModel):
    query: str
    ung_vien: list[Ung_vien]


class RerankResultItem(BaseModel):
    chunk_id: str
    score: float


class RerankResponse(BaseModel):
    ket_qua: list[RerankResultItem]


@app.get("/health")
def health() -> dict:
    # KHÔNG load model ở đây — health phải trả lời NGAY LÚC KHỞI ĐỘNG, trước
    # khi model tải xong (vài giây). Backend tự chịu trách nhiệm timeout/retry
    # khi gọi /rerank nếu service vừa mới lên (cùng nguyên tắc liveness/
    # readiness ở CLAUDE.md — health ở đây đóng vai liveness thuần).
    return {"status": "ok", "model": MODEL_NAME}


@app.post("/rerank", response_model=RerankResponse)
def rerank(req: RerankRequest) -> RerankResponse:
    if not req.ung_vien:
        return RerankResponse(ket_qua=[])
    model = _get_model()
    pairs = [(req.query, uv.text) for uv in req.ung_vien]
    scores = model.predict(pairs)
    ket_qua = [
        RerankResultItem(chunk_id=uv.chunk_id, score=float(s))
        for uv, s in zip(req.ung_vien, scores)
    ]
    ket_qua.sort(key=lambda x: x.score, reverse=True)
    return RerankResponse(ket_qua=ket_qua)
