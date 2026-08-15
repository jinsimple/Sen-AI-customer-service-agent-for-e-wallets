#!/usr/bin/env bash
# deploy_home.sh — bản WSL/Linux/macOS của scripts/deploy_home.ps1.
#
# Giữ ĐÚNG cùng chuỗi cổng kiểm và cùng thông điệp với bản .ps1. Hai bản lệch
# nhau là kiểu lỗi đợt này đã trả giá (F-24 áp hai nhánh, F-25 chỉ áp một) —
# sửa một bản thì sửa cả hai.
#
#   bash scripts/deploy_home.sh
set -euo pipefail
cd "$(dirname "$0")/.."

ok()   { printf '  \033[32m[OK]\033[0m    %s\n' "$1"; }
bad()  { printf '  \033[31m[LOI]\033[0m   %s\n' "$1"; }
warn() { printf '  \033[33m[LUU Y]\033[0m %s\n' "$1"; }

echo; echo "=== FIN-05 — deploy tai nha (profile: home) ==="; echo

# --- CỔNG 1: .env + 3 biến sống-chết -------------------------------------
# Fail-fast nằm ở ĐÂY chứ không ở docker-compose.yml: compose nội suy biến cho
# MỌI service kể cả service bị profile loại ra, nên `${VAR:?}` trong compose sẽ
# làm chết luôn `docker compose up` thường trên máy dev (đo thật).
[ -f .env ] || { bad ".env khong ton tai. Chep tu may cu sang."; exit 1; }

thieu=0
kiem_bien() {
  local ten="$1" giai_thich="$2"
  if grep -qE "^[[:space:]]*${ten}[[:space:]]*=[[:space:]]*[^[:space:]]" .env; then
    ok "${ten} co gia tri"
  else
    bad "${ten} chua co gia tri trong .env"; warn "        ${giai_thich}"; thieu=1
  fi
}
kiem_bien CLOUDFLARE_TUNNEL_TOKEN "Lay tren dashboard Cloudflare: Zero Trust > Networks > Tunnels > Install connector. Buoc TAY."
kiem_bien FIELD_ENCRYPTION_KEY    "PHAI la khoa CU tu may Mac. Doi khoa = moi cot ma hoa thanh rac VINH VIEN."
kiem_bien JWT_SECRET_KEY          "PHAI la khoa CU. Doi = moi phien dang nhap hien co bi vo."
[ "$thieu" -eq 0 ] || { echo; bad "Dung lai. Bo sung .env roi chay lai."; exit 1; }

# --- CỔNG 2: biến phụ thuộc máy còn sót ----------------------------------
if v=$(grep -E "^[[:space:]]*SSL_CERT_FILE[[:space:]]*=" .env | head -1 | cut -d= -f2- | xargs 2>/dev/null) && [ -n "${v:-}" ]; then
  case "$v" in
    /Library/*|/Users/*|/opt/homebrew/*)
      warn "SSL_CERT_FILE dang tro duong dan may Mac: $v"
      warn "        Khong chan deploy (compose da ghi de cho container), nhung nen xoa dong nay." ;;
  esac
fi

docker info >/dev/null 2>&1 || { bad "Docker chua chay."; exit 1; }
ok "Docker dang chay"

echo; echo "--- Cap nhat ma nguon ---"
git pull --ff-only origin main || { bad "git pull --ff-only that bai — co thay doi cuc bo?"; warn "        KHONG tu dong ghi de. Xem 'git status'."; exit 1; }
ok "Da o main moi nhat: $(git rev-parse --short HEAD)"

echo; echo "--- Build + khoi dong (profile home) ---"
docker compose --profile home build
docker compose --profile home up -d

# --- SMOKE — khong tin "up -d khong bao loi" -----------------------------
echo; echo "--- Kiem tra thuc te ---"
loi=0

echo "  cho backend san sang..."
san=0
for _ in $(seq 1 30); do
  if curl -fsS -m 5 http://localhost/health >/dev/null 2>&1; then san=1; break; fi
  sleep 2
done
[ "$san" -eq 1 ] && ok "/health tra 200" || { bad "/health khong tra 200 sau 60s"; loi=$((loi+1)); }

if curl -fsS -m 10 http://localhost/login >/dev/null 2>&1; then ok "Trang dang nhap tra 200"
else bad "Khong mo duoc trang dang nhap"; loi=$((loi+1)); fi

dang_chay=$(docker compose --profile home ps --services --filter status=running)
for s in postgres redis backend frontend caddy cloudflared; do
  if printf '%s\n' "$dang_chay" | grep -qx "$s"; then ok "service $s dang chay"
  else bad "service $s KHONG chay"; loi=$((loi+1)); fi
done

if docker compose --profile home logs --tail 40 cloudflared 2>&1 | grep -qE "Registered tunnel connection|Connection .* registered"; then
  ok "Cloudflare Tunnel da ket noi"
else
  bad "Chua thay tunnel ket noi trong log"
  warn "        Xem: docker compose --profile home logs cloudflared"
  loi=$((loi+1))
fi

echo
if [ "$loi" -eq 0 ]; then
  echo "=== TAT CA XANH ==="; echo
  warn "CHUA XONG: buoc nghiem thu cuoi KHONG chay tu may nay duoc."
  echo "  Mo https://app.adaptivealgo.uk tu MOT MAY KHAC (hoac 4G dien thoai, TAT WiFi)"
  echo "  va thay man dang nhap. Chi khi do moi goi la xong."
  exit 0
else
  echo "=== CO $loi MUC DO ==="; exit 1
fi
