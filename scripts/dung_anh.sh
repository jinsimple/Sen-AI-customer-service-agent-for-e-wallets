#!/usr/bin/env bash
# Bọc lệnh dựng ảnh — biến MỘT THỨ PHẢI NHỚ thành MỘT THỨ MẶC ĐỊNH ĐÚNG.
#
# VÌ SAO TỒN TẠI (18/08/2026) — hai lỗi nhãn trong MỘT lần dựng:
#
#   ① THIẾU BIẾN.  Dựng không truyền `BUILD_COMMIT` ⟹ nhãn = `khong-ro`
#      (`docker-compose.yml:51`). Lỗi thao tác, sửa được bằng cách nhớ gõ —
#      tức sẽ tái diễn.
#
#   ② 🔴 LỆCH NGỮ NGHĨA, cái này KHÔNG sửa được bằng cách nhớ gõ.
#      Ảnh dựng từ CÂY LÀM VIỆC; nhãn trỏ về HEAD. Nếp của đội là
#      *chạy → xác minh → MỚI commit*, nên hai thứ đó **thường khác nhau**.
#      [ĐO] lần dựng 18/08: nhãn `bf1bd5a`, nhưng `git show bf1bd5a:` cho ra
#      `customer_tools.py` **vẫn còn docstring 376 token đã bị gỡ** trong ảnh.
#      ⟹ ai lần theo nhãn sẽ tìm thấy đúng đoạn mã vừa được xoá.
#      Đây là lần THỨ BA nhãn ấy lệch trong dự án ⟹ không phải tai nạn.
#
# CÁI NÀY KHÔNG CỐ LÀM NHÃN ĐÚNG — không làm được: mã trong ảnh có thể chưa
# từng tồn tại trong bất kỳ commit nào. Nó làm nhãn **THÔI NÓI DỐI**:
#
#     khớp HEAD   ->  bb20f6f                  (tra được, tin được)
#     LỆCH HEAD   ->  bb20f6f-CAY-KHAC-HEAD    (KHÔNG `git show` được -> TỰ LỘ)
#     không biết  ->  khong-ro                 (mặc định của compose)
#
# Ba trạng thái thay vì hai — cùng công thức `xanh·đỏ·SKIP`,
# `đo được·không đọc được·đúng 0`, và ba trạng thái giải mã ở `crypto_types`.
# Phần làm nó HOẠT ĐỘNG là hậu tố **tra không ra**: một nhãn sai mà tra được
# thì người ta tin nó; một nhãn sai mà tra không ra thì người ta đi hỏi.
#
# 🔴 CỐ Ý KHÔNG đóng băm `src/` vào nhãn này. Băm đã có ở `/app/.source_hash`,
# **tự tính trong Dockerfile, không qua tay người**. Thêm một bản sao do script
# này tính là tạo đúng thứ `src/build_stamp.py` sinh ra để chống:
# *hai định nghĩa của cùng một vật sẽ lệch nhau, và lệch trong im lặng.*
#
# DÙNG:
#     scripts/dung_anh.sh fin05
#     scripts/dung_anh.sh fin05ttl
#     scripts/dung_anh.sh fin05do
#
# Tham số `-f` lấy TỪ NHÃN CONTAINER ĐANG CHẠY, không gõ từ trí nhớ — bàn giao
# 17/08 ghi hỏng tham số `-f` **hai lần trong một buổi**, và thiếu `-p` đã hạ
# ngăn xếp demo một lần.
set -euo pipefail

GOC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$GOC"

NGAN_XEP="${1:-}"
if [[ -z "$NGAN_XEP" ]]; then
    echo "dùng: $0 <fin05|fin05ttl|fin05do>" >&2
    exit 2
fi

# Lấy `-f` từ nhãn container đang chạy của chính ngăn xếp đó.
CT="${NGAN_XEP}-backend-1"
FILES="$(docker inspect "$CT" \
    --format '{{index .Config.Labels "com.docker.compose.project.config_files"}}' 2>/dev/null || true)"
if [[ -z "$FILES" ]]; then
    echo "🔴 không đọc được nhãn config_files của $CT — container không chạy?" >&2
    echo "   KHÔNG đoán tham số -f. Khởi động ngăn xếp rồi chạy lại." >&2
    exit 3
fi

ARGS_F=()
IFS=',' read -ra DS <<< "$FILES"
for d in "${DS[@]}"; do ARGS_F+=(-f "$d"); done

# Nhãn TỰ KHAI. Chỉ soi `src/` — đó là thứ đi vào ảnh và là thứ băm phủ;
# đổi `docs/` không làm ảnh khác đi nên không nên làm nhãn kêu.
HEAD_NGAN="$(git rev-parse --short HEAD)"
if git diff --quiet HEAD -- src/; then
    BUILD_COMMIT="$HEAD_NGAN"
    GHI_CHU="cây khớp HEAD"
else
    BUILD_COMMIT="${HEAD_NGAN}-CAY-KHAC-HEAD"
    GHI_CHU="🔴 cây LỆCH HEAD ở src/ — nhãn tự khai, đừng git show nó"
fi
BUILD_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

echo "ngăn xếp     : $NGAN_XEP"
echo "tham số -f   : ${ARGS_F[*]}   (lấy từ nhãn container, không gõ tay)"
echo "BUILD_COMMIT : $BUILD_COMMIT   ($GHI_CHU)"
echo "BUILD_AT     : $BUILD_AT"
echo

export BUILD_COMMIT BUILD_AT
# KHÔNG `>/dev/null` ở đâu cả — một lần nuốt output đã làm người tiền nhiệm đọc
# trạng thái cũ thành kết quả mới (bàn giao ④).
docker compose -p "$NGAN_XEP" "${ARGS_F[@]}" build backend
docker compose -p "$NGAN_XEP" "${ARGS_F[@]}" up -d backend

echo
echo "— ba phép kiểm sau khi dựng —"
sleep 3
echo "băm cây  : $(python3 -c "
import hashlib, pathlib
h = hashlib.sha256()
for f in sorted(pathlib.Path('src').rglob('*.py')): h.update(f.read_bytes())
print(h.hexdigest()[:12])")"
echo "băm ảnh  : $(docker exec "$CT" cat /app/.source_hash 2>/dev/null || echo '(chưa sẵn sàng)')"
echo "sửa-tay  : $(docker diff "$CT" 2>/dev/null | grep -E '^C /app/src.*\.py$' | grep -v __pycache__ | wc -l | tr -d ' ')"
