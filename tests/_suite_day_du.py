"""Cổng META cho suite — phân biệt "chưa chạy được ở máy này" với "đỏ thật".

## Vì sao cổng này tồn tại

[PO đo 25/08] Lead hạ vài ngăn Docker để lấy RAM cho buổi chạy thật ⑬. Hệ quả:

    667 passed · 50 skipped · 2 failed
    630 passed · 90 skipped · 1 failed     ← "1 failed" TRÔNG NHƯ CẢI THIỆN

`test_inv_ngan_sach_token` chuyển từ ĐỎ sang SKIP — cổng canh ràng buộc cứng
TỰ TẮT TIẾNG đúng lúc đáng kêu nhất, và không ai được báo. Lead chỉ bắt được
vì đi tìm hiểu VÌ SAO nó tốt lên, thay vì mừng.

Coder đo bằng máy (`pytest -rs` + phân loại), 21 chỗ toàn suite (loại trừ
skip vì TỐN TIỀN/đóng băng), chia bốn nhóm:

    A · HẠ TẦNG VẮNG LÚC CHẠY   (Postgres/Docker/pip-audit/seam)   15 chỗ
    B · NĂNG LỰC TEST CHƯA TỒN TẠI (không có gì để đo)              3 chỗ
    C · CỔNG TẮT CÓ CHỦ ĐÍCH (CỔNG-96)                              1 chỗ
    D · DỮ LIỆU/PHẠM VI KHÔNG ÁP DỤNG (COMP-002 + 1 khác)           2 chỗ

Chỉ NHÓM A chịu cổng này. B/C/D là skip VĨNH VIỄN theo thiết kế — không ai
"dựng hạ tầng" mà làm chúng chạy được, nên bật cờ không đổi gì ở đó (xem chú
thích "vì sao được miễn" ngay tại từng chỗ B/C/D trong file tương ứng).

## Cách dùng — chỉ áp cho đúng NHÓM A

Gọi `can_ha_tang(ly_do, cach_dung=...)` THAY CHO `pytest.skip(...)` tại đúng
những chỗ hạ tầng THẬT SỰ vắng mặt (Postgres không reachable, Docker stack
không tới được, pip-audit chưa cài, stack đặc biệt chưa dựng...). KHÔNG dùng
hàm này cho skip vì lý do KHÁC (dữ liệu sai population — vd DB rỗng CI dựng
mới, không phải DB demo file đang canh; năng lực chưa tồn tại; ngoài phạm vi
sản phẩm) — những skip đó PHẢI giữ nguyên `pytest.skip()` thường, gọi nhầm
hàm này ở đó sẽ biến một skip-vĩnh-viễn-đúng-đắn thành đỏ giả khi bật cờ.

    FIN05_SUITE_DAY_DU=1   ⟹  NHÓM A không skip nữa — FAIL rõ ràng, kèm
                               "KHÔNG CHẠY ĐƯỢC vì thiếu X" (+ cách dựng nếu
                               có), để người trực sự cố không đi tìm bug
                               trong code cho một thứ chỉ đơn giản là thiếu
                               hạ tầng.
    mặc định (không đặt)  ⟹  skip như hiện nay, máy dev yên.

🔴 KHOÁ VÀO CỜ TƯỜNG MINH NÀY, KHÔNG khoá vào `CI=true` — [ĐO] CI chưa từng
chạy tới nơi (`ruff` đỏ ⟹ `pytest` bị skip), và PO thật đã ra lệnh DỪNG việc
sửa CI. Khoá vào CI là một cái còi treo trong phòng không ai ngồi. Cổng này
dùng cho MỌI buổi nghiệm thu chạy tay, không phụ thuộc CI có sửa hay chưa.

Dùng khi cần: mọi buổi nghiệm thu bật `FIN05_SUITE_DAY_DU=1` trước khi chạy
`pytest tests/` — không ai được tuyên bố "suite xanh" trên một quần thể đã
teo, kể cả khi họ quên đếm dòng skip.
"""
from __future__ import annotations

import os

import pytest

BAT_DAY_DU = os.environ.get("FIN05_SUITE_DAY_DU") == "1"


def can_ha_tang(ly_do: str, cach_dung: str | None = None, *, allow_module_level: bool = False) -> None:
    """NHÓM A — gọi thay `pytest.skip(...)` đúng chỗ hạ tầng vắng lúc chạy.

    Xem docstring module này để biết chỗ nào ĐƯỢC và KHÔNG ĐƯỢC gọi hàm này.
    """
    if not BAT_DAY_DU:
        pytest.skip(ly_do, allow_module_level=allow_module_level)
        return
    thong_bao = f"🔴 KHÔNG CHẠY ĐƯỢC (FIN05_SUITE_DAY_DU=1) — {ly_do}"
    if cach_dung:
        thong_bao += f"\n   Cách dựng: {cach_dung}"
    pytest.fail(thong_bao, pytrace=False)
