#!/bin/sh
# Retry `pip install` trong CI — CHỈ cho lỗi MẠNG, không bao giờ cho lỗi
# giải phụ thuộc. [ĐO 20/08] lượt CI #299: 4 job đỏ cùng lúc (invariants ·
# lint-and-test · appsec · dependency-and-secret-scan), tất cả cùng một
# nguyên nhân: `Connection broken: IncompleteRead(...)` khi tải gói — lỗi
# mạng, không phải lỗi code, nhưng không phân biệt được từ bảng CI đỏ.
#
# AN TOÀN để retry ở đây vì mọi lời gọi đều nhắm requirements.lock.txt
# (ghim cứng ==, không có gì để "giải" — pip không cần resolver quyết định
# phiên bản nào). Với requirements.txt (khoảng phiên bản >=/~=) retry sẽ
# KHÔNG an toàn theo cùng lý lẽ: một lần giải ra phiên bản A, lần retry sau
# server có thể trả về set khác — CẤM dùng script này cho requirements.txt.
#
# Cách tách lỗi mạng khỏi lỗi thật: match nguyên văn thông báo lỗi đã biết.
# Khớp -> thử lại (lỗi mạng thật). KHÔNG khớp -> dừng ngay, không thử lại
# (lỗi thật — vd sai tên gói, thiếu compiler, xung đột nội tại của chính
# lock file). Một retry-loop thử tới khi xanh là một cổng không còn đỏ
# được — không được phép xảy ra ở đây.
#
# Dùng: scripts/ci_pip_install_retry.sh requirements.lock.txt [gói thêm...]
set -eu

LOCK_FILE="$1"
shift
EXTRA_PKGS="$*"

case "$LOCK_FILE" in
  *.lock.txt) ;;
  *)
    echo "LỖI DÙNG SAI: script này CHỈ nhận file *.lock.txt (ghim cứng)." >&2
    echo "  Nhận được: $LOCK_FILE — nếu đây là requirements.txt thường," >&2
    echo "  ĐỪNG dùng retry (xem comment đầu file này để biết vì sao)." >&2
    exit 2
    ;;
esac

MAX_LAN=3
LOG="$(mktemp)"
trap 'rm -f "$LOG"' EXIT

n=0
while [ "$n" -lt "$MAX_LAN" ]; do
  n=$((n + 1))
  if pip install --no-cache-dir -r "$LOCK_FILE" $EXTRA_PKGS >"$LOG" 2>&1; then
    cat "$LOG"
    exit 0
  fi

  if grep -qE 'Connection broken|IncompleteRead|ConnectionResetError|ReadTimeoutError|ProtocolError|Connection aborted|Temporary failure in name resolution|Remote end closed connection' "$LOG"; then
    echo "[ci_pip_install_retry] lần $n/$MAX_LAN: LỖI MẠNG, thử lại sau 5s" >&2
    cat "$LOG" >&2
    sleep 5
    continue
  fi

  echo "[ci_pip_install_retry] LỖI KHÔNG PHẢI MẠNG — DỪNG, không thử lại." >&2
  echo "[ci_pip_install_retry] (retry chỉ áp cho lỗi mạng đã biết — xem" >&2
  echo "[ci_pip_install_retry]  docs/devops/2026-08-20-doc-bang-ci-do.md)" >&2
  cat "$LOG" >&2
  exit 1
done

echo "[ci_pip_install_retry] hết $MAX_LAN lần, vẫn lỗi mạng — dừng" >&2
cat "$LOG" >&2
exit 1
