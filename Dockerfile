# Backend FastAPI — xem docs/DEPLOY.md cho bối cảnh triển khai (Docker Compose
# trên Oracle Cloud Always Free, ARM64/aarch64).
#
# ---- Stage 1: Build ----
FROM python:3.12-slim AS builder

WORKDIR /app

# build-essential: một số dependency của chromadb (onnxruntime/hnswlib) có thể
# thiếu sẵn wheel arm64 trên PyPI tuỳ phiên bản — nếu vậy pip tự build từ
# source, cần compiler có sẵn thay vì lỗi build giữa chừng.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Cài vào /install (không phải mặc định /root/.local) — /root thường mode 700,
# user không phải root (appuser ở stage sau) không traverse vào được dù đã
# chown nội dung bên trong, gây lỗi "Permission denied" khi chạy alembic/uvicorn.
ENV PYTHONUSERBASE=/install
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt
# Model NER cho PII scrubbing hybrid (src/observability/pii.py) — dùng thẳng
# `pip install --user <wheel URL>` thay vì `spacy download` (lệnh tiện ích
# của spaCy KHÔNG tôn trọng PYTHONUSERBASE/--user — phát hiện thật lúc build:
# model cài vào site-packages toàn cục của stage builder, KHÔNG nằm trong
# /install nên bị rớt mất khi COPY --from=builder /install sang stage 2,
# runtime báo "Can't find model 'xx_ent_wiki_sm'"). pip install --user thì
# tôn trọng PYTHONUSERBASE, model nằm chung chỗ với các gói khác, copy đúng.
RUN pip install --no-cache-dir --user \
    https://github.com/explosion/spacy-models/releases/download/xx_ent_wiki_sm-3.8.0/xx_ent_wiki_sm-3.8.0-py3-none-any.whl

# ---- Stage 2: Production ----
FROM python:3.12-slim

WORKDIR /app

# libpq5: psycopg2-binary cần thư viện client Postgres lúc runtime dù đã có
# sẵn trong wheel binary — libpq-dev không cần (chỉ cần lúc build/compile).
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder — /install là thư mục top-level trung
# lập, không dính quyền hạn chế của /root, appuser (non-root) đọc/thực thi
# được bình thường.
COPY --from=builder /install /install
ENV PYTHONUSERBASE=/install
ENV PATH=/install/bin:$PATH

# Non-root user cho tiến trình ứng dụng thật (không chạy uvicorn bằng root) —
# việc hạ quyền thực hiện trong docker-entrypoint.sh lúc container khởi động,
# không phải ở đây, vì named volume (chroma_data/logs_data) chỉ tồn tại lúc
# container chạy, không tồn tại lúc build image.
RUN useradd -m appuser

# Copy application code
COPY . .
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh && mkdir -p /app/data /app/logs

EXPOSE 8010

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8010/health')" || exit 1

# entrypoint chown /app/data + /app/logs (volume mount, quyền root mặc định
# lúc Docker tạo mới) rồi mới hạ quyền xuống appuser để chạy migration +
# uvicorn — xem docker-entrypoint.sh. ĐÚNG 1 worker (mặc định uvicorn không
# truyền --workers) — xem docs/DEPLOY.md phần "Backend chạy đúng 1 worker":
# MemorySaver (src/agents/graph.py) giữ bộ nhớ hội thoại trong RAM 1 process,
# nhiều worker sẽ làm khách mất trí nhớ agent giữa hội thoại nếu bị định
# tuyến sang worker khác.
ENTRYPOINT ["/docker-entrypoint.sh"]
