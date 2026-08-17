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

⚠️ ĐIỂM MÙ — phát biểu CHÍNH XÁC, vì một câu nói quá sẽ bị dùng để giải thích
oan một báo động, và giải thích sai một báo động là cách nhanh nhất để tắt nó.

Băm NỘI DUNG chứ không băm đường dẫn (giống hệt bản gốc bên `eval/`) — nhưng
`sorted(rglob("*.py"))` sắp theo ĐƯỜNG DẪN rồi băm nội dung THEO THỨ TỰ ĐÓ.
Nên đổi tên file:

    · làm DỊCH vị trí sắp xếp  ->  băm ĐỔI    (đo: 6335a5b899e3 -> bdd05b87c4e4
                                               khi src/config.py -> zzz_config.py)
    · GIỮ nguyên vị trí        ->  băm KHÔNG đổi  (đo: config.py -> configz.py,
                                               vẫn 6335a5b899e3)

Tức điểm mù hẹp hơn nhiều so với "mọi lần đổi tên": nó chỉ là ca đổi tên KHÔNG
làm xê dịch thứ tự. Bản mô tả trước của file này nói quá về phía yếu hơn —
security bắt được, và cả hai số trên là đo, không phải suy.

Vẫn không bịt: giữ băm này BẰNG ĐÚNG bản bên `eval/` quan trọng hơn bịt một ca
hiếm, và bịt ở một bên sẽ tạo ra đúng sự lệch mà module này sinh ra để chống.
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


# Nhãn đóng vào ảnh lúc `docker build`, do chính `bam_ma_nguon()` tính ra ngay
# sau `COPY . .` (xem Dockerfile). KHÔNG có file này = không chạy trong ảnh do
# Dockerfile của dự án dựng.
DUONG_NHAN = Path("/app/.bam_ma_nguon")


def nhan_luc_dung() -> str | None:
    """Nhãn băm đóng vào ảnh, hoặc None khi chạy ngoài ảnh (dev cục bộ, test).

    Phân biệt None (ngoài ảnh) với chuỗi rỗng/hỏng (trong ảnh nhưng nhãn sai)
    là điều kiện để phép kiểm lúc khởi động CHẾT thay vì im lặng bỏ qua —
    xem `_khai_ma_nguon_lech_anh` ở main.py.
    """
    if not DUONG_NHAN.exists():
        return None
    return DUONG_NHAN.read_text().strip()
