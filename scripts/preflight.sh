#!/usr/bin/env bash
# preflight.sh — kiểm tra xung đột môi trường TRƯỚC khi chạy stack dev cục bộ.
#
# VÌ SAO CÓ FILE NÀY
# ------------------
# 2026-08-13: Docker stack (Caddy :80 -> Postgres) đang chạy sẵn, ai đó khởi
# động thêm stack dev cục bộ (next dev :3000 -> uvicorn :8010 -> SQLite). Hai
# giao diện GIỐNG HỆT NHAU nhưng là hai hệ thống với hai database khác nhau.
# Mở cửa sổ khách ở `localhost` và cửa sổ CSKH ở `localhost:3000` -> khách ghi
# vào Postgres, CSKH đọc SQLite, vĩnh viễn thấy 0 ticket. Mất nhiều giờ điều
# tra trong khi mọi tầng code đều đúng. Xem ADR-009.
#
# Script này KHÔNG chặn cứng — chạy 2 stack song song đôi khi là chủ đích
# (vd so sánh hành vi). Nó CẢNH BÁO to và bắt xác nhận, để việc đó luôn là
# lựa chọn có ý thức chứ không phải tai nạn.
#
# DÙNG
#   bash scripts/preflight.sh            # kiểm tra, hỏi xác nhận nếu có xung đột
#   bash scripts/preflight.sh --quiet    # chỉ trả exit code, không hỏi (dùng trong script khác)

set -uo pipefail

QUIET=0
[[ "${1:-}" == "--quiet" ]] && QUIET=1

DO='\033[2m'; VANG='\033[33m'; DO_DAM='\033[31m'; XANH='\033[32m'; TAT='\033[0m'
[[ -t 1 ]] || { DO=''; VANG=''; DO_DAM=''; XANH=''; TAT=''; }

xung_dot=0

echo "── Kiểm tra môi trường ──────────────────────────────────────────"

# 1) Docker stack có đang chạy không?
#
# HỨNG OUTPUT VÀO BIẾN, không dùng `... | grep -q`: `grep -q` thoát NGAY khi
# khớp dòng đầu -> SIGPIPE giết `docker compose` -> với `set -o pipefail`,
# pipeline trả mã lỗi của docker và điều kiện thành SAI dù docker đang chạy.
# Lỗi thật gặp lúc viết script này (2026-08-13) — script báo "không chạy"
# trong khi 6 container đang sống.
dich_vu=""
if command -v docker >/dev/null 2>&1; then
  dich_vu=$(docker compose ps --services --status running 2>/dev/null || true)
fi

if [[ -n "$dich_vu" ]]; then
  echo -e "${VANG}  ⚠  DOCKER STACK ĐANG CHẠY${TAT}: $(echo "$dich_vu" | tr '\n' ' ')"
  # Docker phục vụ qua Caddy ở cổng 80/443 — dùng Postgres.
  if echo "$dich_vu" | grep -q '^caddy$'; then
    echo -e "     Phục vụ tại ${XANH}http://localhost/${TAT} (Caddy) — database ${XANH}Postgres${TAT}"
  fi
  xung_dot=1
else
  echo -e "${DO}  ·  Docker stack: không chạy${TAT}"
fi

# 2) Có tiến trình dev cục bộ nào đang giữ cổng không?
for cong in 3000 8010; do
  if lsof -iTCP:"$cong" -sTCP:LISTEN -P >/dev/null 2>&1; then
    ai=$(lsof -iTCP:"$cong" -sTCP:LISTEN -P -Fc 2>/dev/null | grep '^c' | head -1 | cut -c2-)
    echo -e "${VANG}  ⚠  Cổng ${cong} đang bị giữ${TAT} bởi: ${ai:-?}"
    xung_dot=1
  else
    echo -e "${DO}  ·  Cổng ${cong}: trống${TAT}"
  fi
done

echo "─────────────────────────────────────────────────────────────────"

if [[ "$xung_dot" -eq 0 ]]; then
  echo -e "${XANH}Không có xung đột. Chạy dev cục bộ an toàn.${TAT}"
  exit 0
fi

cat <<'CANHBAO'

  ┌───────────────────────────────────────────────────────────────┐
  │  NGUY CƠ: HAI STACK, HAI DATABASE                             │
  │                                                               │
  │  Docker  : http://localhost/       -> Postgres                │
  │  Dev cục bộ: http://localhost:3000 -> SQLite (data/app.db)    │
  │                                                               │
  │  Hai giao diện GIỐNG HỆT NHAU nhưng KHÔNG dùng chung dữ liệu.  │
  │  Mở 2 cửa sổ ở 2 cổng khác nhau = 2 hệ thống khác nhau:        │
  │  khách tạo ticket ở bên này, CSKH bên kia vĩnh viễn không      │
  │  thấy, F5 bao nhiêu lần cũng vô ích.                          │
  │                                                               │
  │  Cách kiểm nhanh: NHÃN MÔI TRƯỜNG ở góc trên phải mọi trang    │
  │  (và ở màn đăng nhập). Hai cửa sổ phải cùng nhãn.             │
  │                                                               │
  │  Muốn chỉ dùng Docker : docker compose up -d                   │
  │  Muốn chỉ dùng dev    : docker compose down                    │
  └───────────────────────────────────────────────────────────────┘

CANHBAO

if [[ "$QUIET" -eq 1 ]]; then
  exit 1
fi

read -r -p "Vẫn tiếp tục chạy stack dev cục bộ? [y/N] " tra_loi
case "$tra_loi" in
  [yY]|[yY][eE][sS])
    echo -e "${VANG}Tiếp tục — nhớ kiểm nhãn môi trường ở cả 2 cửa sổ trước khi kết luận có bug.${TAT}"
    exit 0
    ;;
  *)
    echo "Đã dừng."
    exit 1
    ;;
esac
