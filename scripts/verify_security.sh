#!/usr/bin/env bash
# Kiểm tra lại các lỗ hổng đã vá (JWT, RBAC, mã hoá at-rest, CORS, BFF proxy).
# Chạy sau khi `make run` (backend :8010) và `npm run dev` (frontend :3000)
# đã lên. Không sửa dữ liệu — chỉ đọc + 1 lượt agent chat thật (tốn 1 lần
# gọi OpenAI).
set -uo pipefail

BACKEND="http://localhost:8010"
FRONTEND="http://localhost:3000"
JAR_CSKH=$(mktemp)
JAR_CUST=$(mktemp)
JAR_SUP=$(mktemp)
trap 'rm -f "$JAR_CSKH" "$JAR_CUST" "$JAR_SUP"' EXIT

PASS=0
FAIL=0

check() {
  local desc="$1" got="$2" want="$3"
  if [ "$got" = "$want" ]; then
    echo "  OK   $desc (status=$got)"
    PASS=$((PASS+1))
  else
    echo "  FAIL $desc (muốn $want, thực tế $got)"
    FAIL=$((FAIL+1))
  fi
}

echo "== Lấy user mẫu từ DB =="
read -r CUST_PHONE CUST_ID CSKH_PHONE CSKH_ID SUP_PHONE SUP_ID <<EOF
$(cd "$(dirname "$0")/.." && source .venv/bin/activate && python3 -c "
from src.api.deps import get_session
from src.db.models import User
with next(get_session()) as s:
    out = []
    for role in ('customer','cskh','supervisor'):
        u = s.query(User).filter(User.role==role).first()
        out += [u.phone, u.user_id]
    print(' '.join(out))
")
EOF
echo "  customer=$CUST_PHONE/$CUST_ID  cskh=$CSKH_PHONE/$CSKH_ID  supervisor=$SUP_PHONE/$SUP_ID"

echo
echo "== 1) Backend FastAPI (:8010) — không có token =="
s=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND/tickets")
check "GET /tickets không token phải 401" "$s" "401"

echo
echo "== 2) Backend FastAPI (:8010) — CORS đã tắt (browser không gọi thẳng được) =="
hdr=$(curl -s -D - -o /dev/null "$BACKEND/health" -H "Origin: http://evil.example")
if echo "$hdr" | grep -qi "access-control-allow-origin"; then
  echo "  FAIL Vẫn còn header Access-Control-Allow-Origin — CORS chưa tắt hẳn"
  FAIL=$((FAIL+1))
else
  echo "  OK   Không có Access-Control-Allow-Origin — origin lạ không tự gọi được"
  PASS=$((PASS+1))
fi

echo
echo "== 3) Login qua BFF (Next.js :3000/api/session), không phải gọi thẳng backend =="
body=$(curl -s -c "$JAR_CSKH" -o /dev/null -w "%{http_code}" -X POST "$FRONTEND/api/session" \
  -H "Content-Type: application/json" -d "{\"phone\":\"$CSKH_PHONE\",\"role\":\"cskh\"}")
check "Login cskh qua BFF" "$body" "200"
if grep -q "access_token" "$JAR_CSKH" 2>/dev/null && grep -q "HttpOnly" "$JAR_CSKH" 2>/dev/null; then
  echo "  OK   Cookie session là HttpOnly và có access_token bên trong (JS trình duyệt không đọc được)"
  PASS=$((PASS+1))
else
  echo "  FAIL Không thấy cookie HttpOnly chứa access_token như kỳ vọng"
  FAIL=$((FAIL+1))
fi

curl -s -c "$JAR_CUST" -o /dev/null -X POST "$FRONTEND/api/session" \
  -H "Content-Type: application/json" -d "{\"phone\":\"$CUST_PHONE\",\"role\":\"customer\"}"
curl -s -c "$JAR_SUP" -o /dev/null -X POST "$FRONTEND/api/session" \
  -H "Content-Type: application/json" -d "{\"phone\":\"$SUP_PHONE\",\"role\":\"supervisor\"}"

echo
echo "== 4) Phân quyền theo role qua BFF =="
s=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND/api/tickets")
check "GET /api/tickets không đăng nhập phải 401" "$s" "401"

s=$(curl -s -b "$JAR_CSKH" -o /dev/null -w "%{http_code}" "$FRONTEND/api/tickets")
check "cskh xem /api/tickets phải 200" "$s" "200"

s=$(curl -s -b "$JAR_CUST" -o /dev/null -w "%{http_code}" "$FRONTEND/api/tickets")
check "customer xem /api/tickets phải 403 (chỉ cskh/supervisor)" "$s" "403"

s=$(curl -s -b "$JAR_CSKH" -o /dev/null -w "%{http_code}" -X POST "$FRONTEND/api/resolutions/RES-FAKE/approve")
check "cskh duyệt resolution phải 403 (chỉ supervisor)" "$s" "403"

s=$(curl -s -b "$JAR_SUP" -o /dev/null -w "%{http_code}" -X POST "$FRONTEND/api/resolutions/RES-KHONG-TON-TAI/approve")
check "supervisor duyệt resolution không tồn tại phải 404 (đúng role, sai data)" "$s" "404"

echo
echo "== 5) Không thể mạo danh user khác qua body request =="
out=$(curl -s -b "$JAR_CUST" -X POST "$FRONTEND/api/tools/customer-history" \
  -H "Content-Type: application/json" -d '{"user_id":"USR-9999-KHONG-PHAI-TOI"}')
seen_id=$(echo "$out" | python3 -c "import json,sys; print(json.load(sys.stdin).get('user_id',''))" 2>/dev/null)
if [ "$seen_id" = "$CUST_ID" ]; then
  echo "  OK   Dù body cố khai user_id khác, dữ liệu trả về vẫn đúng $CUST_ID (danh tính lấy từ JWT, không phải body)"
  PASS=$((PASS+1))
else
  echo "  FAIL Trả về user_id=$seen_id — có thể đã bị mạo danh"
  FAIL=$((FAIL+1))
fi

echo
echo "== 6) Mã hoá dữ liệu nhạy cảm at-rest (account_no) =="
# Mặc định kiểm SQLite cục bộ (data/app.db). Muốn kiểm DB Postgres (vd container
# docker-compose) — export DATABASE_URL=postgresql://... trước khi chạy script,
# hoặc kiểm tay: docker compose exec postgres psql -U $POSTGRES_USER -d
# $POSTGRES_DB -c "SELECT account_no FROM bank_accounts LIMIT 1;"
if [ -n "${DATABASE_URL:-}" ] && [[ "$DATABASE_URL" == postgresql* ]]; then
  raw=$(psql "$DATABASE_URL" -tAc "SELECT account_no FROM bank_accounts LIMIT 1;" 2>/dev/null | tr -d '[:space:]')
else
  raw=$(cd "$(dirname "$0")/.." && sqlite3 data/app.db "SELECT account_no FROM bank_accounts LIMIT 1;" 2>/dev/null)
fi
if [[ "$raw" == gAAAAA* ]]; then
  echo "  OK   account_no trong file DB là ciphertext Fernet (gAAAAA...), không phải số thật"
  PASS=$((PASS+1))
else
  echo "  FAIL account_no trong DB không có dạng mã hoá — đang lộ dạng thô: $raw"
  FAIL=$((FAIL+1))
fi

echo
echo "== 7) Rate limit chống dò số điện thoại (10 lần login/phút) =="
codes=""
for i in $(seq 1 12); do
  c=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$FRONTEND/api/session" \
    -H "Content-Type: application/json" -d '{"phone":"0000000000","role":"customer"}')
  codes="$codes$c "
done
if echo "$codes" | grep -q "429"; then
  echo "  OK   Có request bị chặn 429 trong 12 lần gọi liên tiếp — rate limit hoạt động"
  echo "       (chuỗi status: $codes)"
  PASS=$((PASS+1))
else
  echo "  FAIL Không thấy 429 nào — rate limit có thể chưa áp dụng"
  echo "       (chuỗi status: $codes)"
  FAIL=$((FAIL+1))
fi

echo
echo "== 8) Đăng xuất huỷ session thật (không phải chỉ xoá ở client) =="
curl -s -c "$JAR_CSKH" -b "$JAR_CSKH" -o /dev/null -X DELETE "$FRONTEND/api/session"
s=$(curl -s -b "$JAR_CSKH" -o /dev/null -w "%{http_code}" "$FRONTEND/api/tickets")
check "Gọi lại /api/tickets sau logout phải 401" "$s" "401"

echo
echo "== 9) Observability — correlation_id gắn vào MỌI response (đủ để nối trace-log-request) =="
corr=$(curl -s -D - -o /dev/null "$BACKEND/health" | grep -i "^x-correlation-id:" | tr -d '\r\n')
if [[ -n "$corr" ]]; then
  echo "  OK   Header X-Correlation-Id có mặt ($corr)"
  PASS=$((PASS+1))
else
  echo "  FAIL Thiếu header X-Correlation-Id — xem src/api/main.py::audit_log_middleware"
  FAIL=$((FAIL+1))
fi

echo
echo "=============================================="
echo "KẾT QUẢ: $PASS pass / $FAIL fail"
echo "=============================================="
[ "$FAIL" -eq 0 ]
