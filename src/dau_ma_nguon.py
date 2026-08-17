"""Băm nội dung `src/**/*.py` — nhãn định danh MÃ SẢN PHẨM, không phải kho.

VÌ SAO TỒN TẠI: `build_commit` đã bị chứng minh nói dối được theo CẢ HAI chiều
trong cùng một ngày (17/08).

    nhãn ĐỨNG YÊN, mã DỊCH   fin05-backend-1 khai `7450184` trong khi
                             `graph.py` đã bị `docker cp` sửa
    nhãn DỊCH, mã ĐỨNG YÊN   fin05ttl-backend-1 khai `36d6a1a` — một commit
                             chỉ đổi `docs/`, ảnh không chứa gì của nó

⟹ `commit` KHÔNG phải một hàm của `src/`, theo cả hai chiều. Dùng nó làm nhãn
ảnh là dùng SAI LOẠI ĐỊNH DANH: nó định danh TRẠNG THÁI KHO, còn thứ cần định
danh là NỘI DUNG ĐƯỢC ĐÓNG GÓI.

THUẬT TOÁN LẤY NGUYÊN của `eval/measure_quality.py::dau_thuoc()` (trường
`he_thong`) — cố ý dùng lại, không viết mới. Hai định nghĩa của "mã sản phẩm
nào" là hai thứ sẽ lệch nhau, và lệch trong im lặng: tầng đo lường và tầng
đóng gói sẽ nói về hai vật khác nhau bằng cùng một từ.

⚠️ Băm NỘI DUNG, không băm đường dẫn — giống hệt bản gốc bên `eval/`. Nghĩa là
đổi tên một file mà giữ nguyên nội dung KHÔNG đổi băm. Chấp nhận có ý thức: giữ
hai bên bằng nhau quan trọng hơn bịt một ca hiếm, và bịt nó ở một bên sẽ tạo ra
đúng sự lệch mà module này sinh ra để chống.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

# Cùng độ dài với các nhãn băm khác trong dự án, và cùng CÁCH BĂM được khai
# tường minh — "một con số băm không kèm cách băm thì không phải bằng chứng".
CACH_BAM = "sha256-noi-dung-src-py-da-sap-xep-12"
DO_DAI = 12


def bam_ma_nguon(goc: Path | str | None = None) -> str:
    """Băm mọi `*.py` dưới `goc` (mặc định: thư mục `src/` chứa chính file này)."""
    goc = Path(goc) if goc is not None else Path(__file__).resolve().parent
    h = hashlib.sha256()
    for f in sorted(goc.rglob("*.py")):
        h.update(f.read_bytes())
    return h.hexdigest()[:DO_DAI]
