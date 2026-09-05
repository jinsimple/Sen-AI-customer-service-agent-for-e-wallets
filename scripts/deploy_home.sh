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

# 05/09 — MỌI lệnh `docker compose` của script này PHẢI đi qua đúng biến
# này, KHÔNG gõ tay `--profile home` rời rạc nữa. Lý do: y hệt chú thích ở
# bản .ps1 — `docker-compose.home-judge.yml` ghim build-arg
# NEXT_PUBLIC_QUICK_LOGIN/NEXT_PUBLIC_HIDE_ENV_BADGE cho frontend, thiếu
# đúng một `-f` ở một trong nhiều lệnh là build ra ảnh sai mà không ai biết.
COMPOSE_ARGS=(-f docker-compose.yml -f docker-compose.home-judge.yml --profile home)

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

# APP_ENV: CUNG HO bay voi SSL_CERT_FILE o tren. `.env` tren may nay la ban
# CHEP tu may Mac (chinh script nay dan chep, vi khoa ma hoa phai la khoa cu),
# nen no mang theo ca nhung dong CHI DUNG o may dev. `.env` cang duoc mang sang
# trung thanh thi loi cang chac chan tai hien.
# CANH BAO chu KHONG CHAN: sai nhan moi truong khong lam hong dich vu. Khac
# FIELD_ENCRYPTION_KEY (thieu = du lieu thanh rac vinh vien) nen cai do chan cung.
if grep -qE "^[[:space:]]*APP_ENV[[:space:]]*=[[:space:]]*development" .env; then
  warn "APP_ENV=development tren may chay 24/7 — /api/env-info se bao 'development'"
  warn "        Sua .env thanh APP_ENV=production roi chay lai."
fi

docker info >/dev/null 2>&1 || { bad "Docker chua chay."; exit 1; }
ok "Docker dang chay"

echo; echo "--- Cap nhat ma nguon ---"
git pull --ff-only origin main || { bad "git pull --ff-only that bai — co thay doi cuc bo?"; warn "        KHONG tu dong ghi de. Xem 'git status'."; exit 1; }
ok "Da o main moi nhat: $(git rev-parse --short HEAD)"

echo; echo "--- Build + khoi dong (profile home) ---"
# DAU VAT: doc git ngay TRUOC khi build, tren may co `.git`. Image runtime
# khong co `.git` nen khong the tu doc — xem ghi chu trong Dockerfile.
export BUILD_COMMIT=$(git rev-parse --short HEAD)
export BUILD_AT=$(date -u +%Y-%m-%dT%H:%M:%S+00:00)
ok "Dau build: $BUILD_COMMIT · $BUILD_AT"
docker compose "${COMPOSE_ARGS[@]}" build
docker compose "${COMPOSE_ARGS[@]}" up -d

# --- SMOKE — khong tin "up -d khong bao loi" -----------------------------
echo; echo "--- Kiem tra thuc te ---"
loi=0

# --- KHO RAG: kiem lech phien ban, tu nap lai neu can -------------------
# KHONG de nguoi dung phai NHO buoc nay. Don 2 bo dau o CA HAI ve (index +
# query); kho dung bang code CU + query code MOI = lech mot ve, va ca do
# KHONG CO TRIEU CHUNG NAO — search van tra du k ket qua, chi la ket qua sai.
# Mot buoc phai-nho ma quen thi im lang chinh la min.
echo; echo "--- Kho RAG ---"
if ! docker compose "${COMPOSE_ARGS[@]}" exec -T backend python scripts/kho_rag.py kiem; then
  echo "  -> nap lai kho (mat vai phut, co goi API embedding)"
  if docker compose "${COMPOSE_ARGS[@]}" exec -T backend python scripts/kho_rag.py nap-lai; then
    # BAT BUOC restart sau khi nap lai. `chromadb.PersistentClient` khong ho tro
    # nhieu tien trinh dung chung mot persist dir: nap-lai chay trong tien trinh
    # RIENG, con uvicorn giu `_client` cache o cap module tro toi segment vua bi
    # xoa -> /policy-search tra 0 ket qua, HTTP 200, khong loi, khong log.
    # Va no KHONG TAT DINH: `_get_client()` khoi tao LUOI, nen server nao chua
    # truy van lan nao truoc khi nap lai thi lai chay tot. Do that: 1 luot co
    # ket qua roi 12 luot lien tiep rong, trong khi Chroma dung yen 378 vector.
    # nap-lai khong the tu restart: no chay BEN TRONG chinh container do.
    docker compose "${COMPOSE_ARGS[@]}" restart backend >/dev/null 2>&1 \
      || { bad "Restart backend sau nap lai that bai"; loi=$((loi+1)); }
    ok "Da restart backend de no doc kho moi"
  else
    bad "Nap lai kho RAG that bai"; loi=$((loi+1))
  fi
fi

# Cong nay chay CA KHI khong nap lai — bat ca "ai do vua nap tay roi quen restart".
if ! docker compose "${COMPOSE_ARGS[@]}" exec -T backend python scripts/kho_rag.py kiem; then
  bad "Kho RAG van chua san sang sau buoc tren"; loi=$((loi+1))
fi


echo "  cho backend san sang..."
san=0
for _ in $(seq 1 30); do
  if curl -fsS -m 5 http://localhost/health >/dev/null 2>&1; then san=1; break; fi
  sleep 2
done
[ "$san" -eq 1 ] && ok "/health tra 200" || { bad "/health khong tra 200 sau 60s"; loi=$((loi+1)); }

if curl -fsS -m 10 http://localhost/login >/dev/null 2>&1; then ok "Trang dang nhap tra 200"
else bad "Khong mo duoc trang dang nhap"; loi=$((loi+1)); fi

dang_chay=$(docker compose "${COMPOSE_ARGS[@]}" ps --services --filter status=running)
for s in postgres redis backend frontend caddy cloudflared; do
  if printf '%s\n' "$dang_chay" | grep -qx "$s"; then ok "service $s dang chay"
  else bad "service $s KHONG chay"; loi=$((loi+1)); fi
done

if docker compose "${COMPOSE_ARGS[@]}" logs --tail 40 cloudflared 2>&1 | grep -qE "Registered tunnel connection|Connection .* registered"; then
  ok "Cloudflare Tunnel da ket noi"
else
  bad "Chua thay tunnel ket noi trong log"
  warn "        Xem: docker compose ${COMPOSE_ARGS[*]} logs cloudflared"
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
