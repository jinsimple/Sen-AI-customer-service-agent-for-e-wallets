#!/bin/sh
# Container khởi động dưới quyền root (xem Dockerfile — không còn USER
# appuser cố định ở build time nữa). Named volume Docker Compose mount vào
# /app/data (chroma_data) và /app/logs (logs_data) được TẠO MỚI thuộc quyền
# root:root — appuser không ghi được (chromadb.errors.InternalError: unable
# to open database file). Chown lại NGAY LÚC CONTAINER CHẠY (không phải lúc
# build — volume chưa tồn tại lúc build), rồi hạ quyền xuống appuser trước
# khi chạy ứng dụng thật, không giữ tiến trình chính chạy root.
set -e

chown -R appuser:appuser /app/data /app/logs

exec su appuser -c "alembic upgrade head && uvicorn src.api.main:app --host 0.0.0.0 --port 8010"
