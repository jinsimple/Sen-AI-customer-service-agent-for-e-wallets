#!/usr/bin/env bash
# Sao chép lại toàn bộ hồ sơ nộp từ NGUỒN GỐC trong repo vào gate/.
#
# 🔴 gate/ LÀ BẢN SAO, KHÔNG PHẢI NGUỒN.
#    Sửa tài liệu thì sửa ở nguồn (docs/, contracts/, gốc repo) rồi chạy lại script này.
#    Sửa thẳng trong gate/ sẽ bị ghi đè, và tệ hơn: tạo ra một nguồn sự thật thứ hai.
#
# 🔴 XOÁ gate/ KHÔNG ẢNH HƯỞNG GÌ. [ĐO 20/08] scripts/check_contracts.py chỉ quét
#    SCAN_DIRS = tests · docs · src · eval · frontend/e2e — không có gate/.
#    Không test nào, không job CI nào, không script nào của đội đọc thư mục này.
#
# Dùng:  bash gate/lam-moi.sh

set -euo pipefail
GOC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
G="$GOC/gate"
cd "$GOC"

rm -rf "$G/01-tong-quan" "$G/02-kien-truc" "$G/03-dac-ta-thiet-ke" "$G/04-kiem-thu"
mkdir -p "$G/01-tong-quan" "$G/02-kien-truc" "$G/03-dac-ta-thiet-ke/contracts" "$G/04-kiem-thu"

cp README.md                              "$G/01-tong-quan/README.md"
cp docs/architecture_diagram.md           "$G/02-kien-truc/so-do-kien-truc.md"
cp FIN05-PRD.md                           "$G/03-dac-ta-thiet-ke/PRD.md"
cp FIN05-Brief.md                         "$G/03-dac-ta-thiet-ke/Brief.md"
cp docs/DECISIONS.md                      "$G/03-dac-ta-thiet-ke/nhat-ky-quyet-dinh-ADR.md"
cp contracts/authority-matrix.yaml         "$G/03-dac-ta-thiet-ke/contracts/"
cp contracts/agent-tools.yaml              "$G/03-dac-ta-thiet-ke/contracts/"
cp contracts/resolution-state-machine.yaml "$G/03-dac-ta-thiet-ke/contracts/"
cp docs/TESTING.md                        "$G/04-kiem-thu/cach-chay-kiem-thu.md"
cp tests/CHUAN-VIET-TEST.md               "$G/04-kiem-thu/chuan-viet-test.md"

# ---- MANIFEST: nguồn · commit · băm, để phát hiện bản sao đã trôi ----
{
  echo "# MANIFEST — bản sao này lấy từ đâu"
  echo
  echo "Sinh lúc: \`$(date '+%Y-%m-%d %H:%M')\` · HEAD: \`$(git rev-parse --short HEAD)\`"
  echo
  echo "Băm dưới đây là băm của **bản gốc trong repo** tại thời điểm sao chép."
  echo "Băm khác đi ⟹ bản gốc đã đổi, bản sao trong \`gate/\` đã cũ ⟹ chạy lại \`bash gate/lam-moi.sh\`."
  echo
  echo '| bản sao trong gate/ | nguồn gốc trong repo | sha256 (12) |'
  echo '|---|---|---|'
  while IFS='|' read -r dich nguon; do
    [ -f "$nguon" ] || continue
    b=$(shasum -a 256 "$nguon" | cut -c1-12)
    echo "| \`$dich\` | \`$nguon\` | \`$b\` |"
  done <<'EOF'
01-tong-quan/README.md|README.md
02-kien-truc/so-do-kien-truc.md|docs/architecture_diagram.md
03-dac-ta-thiet-ke/PRD.md|FIN05-PRD.md
03-dac-ta-thiet-ke/Brief.md|FIN05-Brief.md
03-dac-ta-thiet-ke/nhat-ky-quyet-dinh-ADR.md|docs/DECISIONS.md
03-dac-ta-thiet-ke/contracts/authority-matrix.yaml|contracts/authority-matrix.yaml
03-dac-ta-thiet-ke/contracts/agent-tools.yaml|contracts/agent-tools.yaml
03-dac-ta-thiet-ke/contracts/resolution-state-machine.yaml|contracts/resolution-state-machine.yaml
04-kiem-thu/cach-chay-kiem-thu.md|docs/TESTING.md
04-kiem-thu/chuan-viet-test.md|tests/CHUAN-VIET-TEST.md
EOF
  echo
  echo "> \`05-nhat-ky-tuan.md\`, \`06-pitch-deck.md\`, \`07-project-knowledge.md\` **không có bản gốc nơi khác** —"
  echo "> chúng được viết riêng cho hồ sơ nộp, sống ngay trong \`gate/\`. Script này không đụng tới."
} > "$G/MANIFEST.md"

echo "✅ Đã sao chép lại. Xem gate/MANIFEST.md"
