#!/bin/bash
# FIN05-StressTest-Plan-v4 6.3 — Postgres reconnect-after-drop. Backend giữ
# 1 connection pool SQLAlchemy sống suốt vòng đời process (src/db/
# session.py::SessionLocal) — nếu Postgres restart/mạng nội bộ đóng
# connection nhàn rỗi mà pool KHÔNG tự phát hiện, request tiếp theo tái
# dùng connection chết -> lỗi ngẫu nhiên trên production dù local (SQLite,
# không có khái niệm "connection chết qua mạng") chạy hoàn hảo — đúng gotcha
# đã đúc kết trong checklist đóng gói production của người dùng.
#
# Script này verify TRỰC TIẾP hiệu quả của `pool_pre_ping=True`
# (src/db/session.py, thêm khi viết script này) — restart CONTAINER
# postgres (không phải backend) giữa lúc backend đang chạy, rồi xác nhận
# backend TỰ hồi phục request tiếp theo mà KHÔNG cần restart chính nó.
#
# Chạy: bash scripts/chaos/postgres_reconnect_after_drop.sh (cần
# `docker compose up -d` sẵn, dùng đúng Postgres thật — DATABASE_URL SQLite
# mặc định dev cục bộ KHÔNG tái hiện được lớp lỗi này).
#
# LƯU Ý THIẾT KẾ (bài học từ bản đầu của script này): baseline/verify PHẢI
# là 1 request HTTP THẬT tới server uvicorn ĐANG CHẠY (dùng httpx qua
# `python3 -c` bên trong container — image slim không có curl), KHÔNG được
# `docker compose exec ... python3 -c "from src.db.session import
# SessionLocal..."` — cách đó mở 1 process Python MỚI mỗi lần gọi, tạo lại
# engine/pool từ đầu, không bao giờ tái dùng connection cũ nên KHÔNG test
# được đúng thứ cần test (pool CỦA SERVER THẬT, sống suốt vòng đời uvicorn).
#
# ĐÃ VERIFY THẬT (2026-08-12): chạy bản có lỗi thiết kế trên → luôn "pass"
# giả (mỗi lần đều tạo connection mới nên không bao giờ đụng phải connection
# chết). Sửa xong, chạy lại: TRƯỚC khi thêm pool_pre_ping — request đã fail
# thật với "psycopg2.OperationalError: server closed the connection
# unexpectedly" (baseline, ngay cả TRƯỚC bước restart Postgres — connection
# cũ trong pool đã chết từ 1 sự kiện earlier, xác nhận lớp lỗi này CÓ THẬT,
# không phải lý thuyết). SAU khi thêm pool_pre_ping=True + rebuild image:
# cả baseline lẫn request sau khi restart Postgres đều 200 OK.
set -euo pipefail

cd "$(dirname "$0")/../.."

echo "=== [1/6] Xác nhận docker compose đang chạy healthy (backend + postgres) ==="
docker compose ps --format json | python3 -c "
import json, sys
bad = [json.loads(l) for l in sys.stdin if json.loads(l).get('Health') not in ('healthy', '')]
if bad:
    print('Service chưa healthy:', bad, file=sys.stderr)
    sys.exit(1)
print('OK — mọi service healthy hoặc không có healthcheck.')
"

echo "=== [2/6] Xác nhận backend đang dùng Postgres thật (không phải SQLite dev) ==="
docker compose exec -T backend su appuser -c "python3 -c \"
from src.config import DATABASE_URL
assert DATABASE_URL.startswith('postgresql'), f'DATABASE_URL không phải Postgres: {DATABASE_URL!r} — chaos test này vô nghĩa với SQLite (không có connection qua mạng để rớt).'
print('OK —', DATABASE_URL.split('@')[-1])
\""

echo "=== [3/6] Request baseline THÀNH CÔNG qua HTTP tới CHÍNH server đang chạy (không phải subprocess riêng) ==="
docker compose exec -T backend su appuser -c "python3 -c \"
import httpx
r = httpx.post('http://localhost:8010/auth/login', json={'phone': '0387000001', 'role': 'customer'}, timeout=10)
r.raise_for_status()
print(f'OK — baseline HTTP request tới server thật thành công, status={r.status_code}')
\""

echo "=== [4/6] Restart CONTAINER postgres (KHÔNG restart backend) — mô phỏng đúng lớp lỗi: Postgres phục hồi ở địa chỉ cũ nhưng connection cũ trong pool backend đã chết ==="
docker compose restart postgres

echo "=== [5/6] Chờ Postgres healthy trở lại (timeout 60s) ==="
for i in $(seq 1 30); do
  STATUS=$(docker inspect --format='{{.State.Health.Status}}' fin05-postgres-1 2>/dev/null || echo "starting")
  if [ "$STATUS" = "healthy" ]; then
    echo "Postgres healthy trở lại sau ~$((i * 2))s"
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "LỖI: postgres KHÔNG healthy lại sau 60s" >&2
    exit 1
  fi
  sleep 2
done

echo "=== [6/6] Request LẠI qua CÙNG server đó (KHÔNG restart backend) — đây là bài test thật của pool_pre_ping ==="
docker compose exec -T backend su appuser -c "python3 -c \"
import httpx
r = httpx.post('http://localhost:8010/auth/login', json={'phone': '0387000001', 'role': 'customer'}, timeout=10)
r.raise_for_status()
print(f'OK — backend TỰ PHỤC HỒI, HTTP request thành công sau khi Postgres restart, status={r.status_code}')
print('Nếu dòng này KHÔNG in ra (script dừng vì lỗi phía trên: 500/OperationalError/')
print('server closed the connection unexpectedly) — nghĩa là pool_pre_ping KHÔNG có tác')
print('dụng hoặc bị gỡ khỏi src/db/session.py, cần điều tra lại.')
\""

echo
echo "=== HOÀN TẤT ==="
echo "Backend tự phục hồi kết nối Postgres SAU KHI container postgres restart mà"
echo "KHÔNG cần tự restart chính nó — xác nhận pool_pre_ping=True (src/db/session.py)"
echo "hoạt động đúng như kỳ vọng."
