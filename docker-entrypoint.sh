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

# UVICORN_WORKERS mặc định 4 — hợp lý cho máy 10 vCPU, chừa chỗ cho Postgres/
# Redis/Caddy cùng chạy. Tổng kết nối DB = workers x (pool ORM + pool
# checkpointer) phải nhỏ hơn max_connections của Postgres (mặc định 100).
: "${UVICORN_WORKERS:=4}"

# 🔴 HÂM NÓNG lược đồ checkpointer MỘT LẦN, TUẦN TỰ, TRƯỚC khi spawn worker
# nào — KHÔNG được bỏ dòng này. [ĐO DevOps 20/08, tái hiện+xác nhận Coder]:
# `src/agents/graph.py::_build_checkpointer()` chạy lại ở MỖI worker (module-
# level, không phải một lần cho cả app) và gọi `PostgresSaver.setup()`. Trên
# DB RỖNG (lần đầu deploy, hoặc sau `docker compose down -v`), N worker cùng
# CREATE TABLE lần đầu ⟹ UniqueViolation trên pg_type — Postgres tự đăng ký
# type cho mỗi bảng mới, và chỉ WORKER ĐẦU TIÊN thắng cuộc đua. uvicorn tự
# respawn worker chết nên KHÔNG chặn container lên "healthy", nhưng log khởi
# động có traceback trông như chết hẳn và có cửa sổ vài giây chỉ 1/N worker
# phục vụ. Dòng dưới import `graph` một lần NGOÀI uvicorn (tuần tự, không đua
# với ai) để `setup()` chạy đúng MỘT lần, rồi đóng pool đã mở ra — sau đó
# `setup()` ở mỗi worker thật là no-op (lược đồ đã có), đúng như chú thích
# "idempotent" tại chỗ gọi nó. Xem docstring `_build_checkpointer()` — Coder
# đã ghi chi tiết ở đó, dòng này chỉ THI HÀNH điều docstring mô tả.
exec su appuser -c "alembic upgrade head && python3 -c 'import src.agents.graph as g; g.close_checkpointer()' && uvicorn src.api.main:app --host 0.0.0.0 --port 8010 --workers ${UVICORN_WORKERS}"
