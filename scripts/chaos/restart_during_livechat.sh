#!/bin/bash
# FIN05-StressTest-Plan-v4 L4-08 — restart backend giữa lúc có live-chat
# đang mở. Trước đây CHỈ verify TAY qua docker compose — script này tự
# động hoá phần MÁY ĐO ĐƯỢC (mở phiên thật qua API, restart backend, xác
# nhận DB/health hồi phục đúng) — PHẦN CÒN LẠI (khách THẤY thông báo "mất
# kết nối" rõ ràng trên UI, không phải treo im lặng) vẫn cần xác nhận BẰNG
# MẮT qua trình duyệt thật hoặc Playwright riêng (WebSocket đóng đột ngột
# giữa `docker compose restart` không có cách nào bắt được từ phía script
# bash/curl thuần — cần 1 WS client thật đang mở kết nối tại đúng thời
# điểm restart). Không giả vờ script này đã kiểm đủ.
#
# Chạy: bash scripts/chaos/restart_during_livechat.sh (cần docker compose
# up -d sẵn, .env có OPENAI_API_KEY thật không bắt buộc — chỉ cần mở được
# phiên live-chat qua request_human_handoff giả lập trực tiếp qua DB,
# không cần gọi AI thật).
set -euo pipefail

cd "$(dirname "$0")/../.."

echo "=== [1/5] Xác nhận docker compose đang chạy healthy ==="
docker compose ps --format json | python3 -c "
import json, sys
bad = [json.loads(l) for l in sys.stdin if json.loads(l).get('Health') not in ('healthy', '')]
if bad:
    print('Service chưa healthy:', bad, file=sys.stderr)
    sys.exit(1)
print('OK — mọi service healthy hoặc không có healthcheck.')
"

echo "=== [2/5] Mở 1 phiên live-chat thật qua DB trực tiếp (bỏ qua AI để không tốn OpenAI call) ==="
CHAT_SESSION_ID=$(docker compose exec -T backend su appuser -c "python3 -c \"
from src.db.session import SessionLocal
from src.services.complaint_intake import create_ticket_with_fraud_check
from src.services import live_chat

s = SessionLocal()
created = create_ticket_with_fraud_check(
    s, user_id='USR-0001', complaint_type='wrong_recipient', scope='internal_wallet',
    description_raw='chaos test restart_during_livechat', trans_id=None,
)
s.commit()
chat_session = live_chat.open_chat_session(s, ticket_id=created['ticket_id'], customer_id='USR-0001')
s.commit()
print(chat_session['chat_session_id'])
s.close()
\"" | tail -1)

echo "Đã mở phiên: $CHAT_SESSION_ID"

echo "=== [3/5] Restart backend NGAY GIỮA LÚC phiên đang 'waiting' (mô phỏng mất kết nối đột ngột) ==="
docker compose restart backend

echo "=== [4/5] Chờ backend healthy trở lại (timeout 60s) ==="
for i in $(seq 1 30); do
  STATUS=$(docker inspect --format='{{.State.Health.Status}}' fin05-backend-1 2>/dev/null || echo "starting")
  if [ "$STATUS" = "healthy" ]; then
    echo "Backend healthy trở lại sau ~$((i * 2))s"
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "LỖI: backend KHÔNG healthy lại sau 60s" >&2
    exit 1
  fi
  sleep 2
done

echo "=== [5/5] Xác nhận phiên chat cũ vẫn còn trong DB (không mất dữ liệu), trạng thái hợp lý sau restart ==="
docker compose exec -T backend su appuser -c "python3 -c \"
from src.db.session import SessionLocal
from src.db.models import ChatSession

s = SessionLocal()
cs = s.get(ChatSession, '$CHAT_SESSION_ID')
assert cs is not None, 'Phiên chat biến mất khỏi DB sau restart — MẤT DỮ LIỆU, đây là bug nghiêm trọng'
print(f'OK — phiên {cs.chat_session_id} vẫn còn, status={cs.status}')
print('LƯU Ý: status vẫn có thể là waiting/active — restart backend KHÔNG tự đóng phiên')
print('(đúng giới hạn đã biết: MemorySaver/ConnectionManager mất state in-memory,')
print('nhưng dữ liệu Postgres KHÔNG mất — client phải tự phát hiện WS đóng và')
print('báo lỗi rõ ràng, verify phần UI này BẰNG MẮT/Playwright riêng, không phải script này).')
s.close()
\""

echo
echo "=== HOÀN TẤT phần tự động hoá được ==="
echo "CÒN THIẾU (cần làm thủ công hoặc Playwright riêng, script này KHÔNG kiểm):"
echo "  - Mở /chat thật trên trình duyệt, xác nhận UI hiện rõ 'mất kết nối'"
echo "    ngay sau bước [3/5] ở trên, không phải treo im lặng chờ vô thời hạn."
echo "  - Xác nhận khách reload lại trang thì luồng live-chat hoạt động bình"
echo "    thường trở lại (không kẹt ở trạng thái lỗi cũ)."
