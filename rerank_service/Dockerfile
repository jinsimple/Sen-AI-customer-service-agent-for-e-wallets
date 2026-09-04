# ADR-061 — sidecar rerank, service RIÊNG khỏi backend chính (xem app.py).
# Multi-stage: cài dependency nặng (torch) ở builder, TẢI MODEL NGAY LÚC
# BUILD (không phải lúc chạy) — hai lý do: (1) container appuser không có
# HOME ghi được, tải lúc chạy vỡ quyền; (2) tải sẵn = khởi động nhanh, không
# phụ thuộc mạng/HuggingFace Hub sống lúc container start (quan trọng cho
# một service chỉ tồn tại để phục vụ NỘI BỘ, không nên có thêm phụ thuộc
# mạng ngoài lúc runtime).

FROM python:3.12-slim AS builder
WORKDIR /install
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install/deps -r requirements.txt

# Tải model VỀ ĐÚNG một thư mục cố định (không phải $HOME mặc định của
# builder — builder chạy root nên không vỡ quyền, nhưng vẫn ghim đường dẫn
# tường minh để runtime biết chính xác nơi COPY).
ENV HF_HOME=/model_cache
ENV PYTHONPATH=/install/deps/lib/python3.12/site-packages
ARG RAG_RERANK_MODEL=cross-encoder/mmarco-mMiniLMv2-L12-H384-v1
RUN python -c "from sentence_transformers import CrossEncoder; CrossEncoder('${RAG_RERANK_MODEL}', max_length=512)"

FROM python:3.12-slim
WORKDIR /app

RUN addgroup --system appgroup && adduser --system --ingroup appgroup --home /app appuser
ENV HOME=/app
ENV HF_HOME=/app/.cache/huggingface
# HF_HUB_OFFLINE=1 — model đã có sẵn từ bước build, KHÔNG được phép gọi ra
# mạng lúc runtime (nếu thiếu gì đó, phải NỔ RÕ lúc khởi động, không âm thầm
# thử tải rồi treo/rớt quyền).
ENV HF_HUB_OFFLINE=1

COPY --from=builder /install/deps /usr/local
COPY --from=builder --chown=appuser:appgroup /model_cache /app/.cache/huggingface
COPY app.py .

USER appuser
EXPOSE 8020
ENV PORT=8020

# Không dùng curl (image slim, có thể thiếu) — dùng python có sẵn, đúng
# khuôn HEALTHCHECK của backend chính (Dockerfile:138).
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8020/health')" || exit 1

CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8020}"]
