"""Cổng cho test TỐN TIỀN — mặc định TẮT, bật bằng cờ tường minh.

## Lỗi thiết kế nó sửa, và lỗi đó là của tôi

`tests/test_a2_dong_y_truoc_khi_tao_ve.py` gọi **3 lượt LLM thật ≈ 42K token**.
Tôi đặt cổng `skip` của nó theo **HẠ TẦNG SỐNG** — *"skip nếu container không
chạy"*. Nhưng container **luôn** chạy trong lúc ta làm việc, nên trên thực tế
bộ ca đó **mặc định BẬT**: một lần `pytest tests/` sau khi dựng ảnh là đốt 42K
mà không ai định làm thế.

> **Cổng đặt theo "có chạy được không" trả lời sai câu hỏi. Câu đúng là "có
> ĐỊNH chạy không".** Điều kiện khả thi ≠ điều kiện cho phép.

Coder chỉ ra nó cùng hình dạng với `PHAN_LUONG_BAT` — **và ngược dấu**: thứ an
toàn được mặc định bật, thứ **tốn tiền** phải mặc định **tắt**. Cùng nguyên tắc
danh-sách-cho-phép đã xuất hiện năm lần hôm nay, lần này ở trục **chi phí**.

## Vì sao khai CHI PHÍ trong thông điệp skip

Người đọc dòng skip là người sắp quyết định bật nó. Một dòng *"cần cờ X"* bắt
họ đi tìm; một dòng *"cần cờ X — bộ này tốn ~42K token"* cho họ quyết ngay. Chi
phí là **thông tin cần cho quyết định**, không phải chi tiết triển khai.
"""
from __future__ import annotations

import os

CO = "FIN05_CHO_PHEP_TON_TIEN"


def duoc_phep_ton_tien() -> bool:
    return os.environ.get(CO, "").strip() not in ("", "0", "false", "False")


def ly_do(uoc_token: int, mo_ta: str) -> str:
    return (
        f"TEST TỐN TIỀN — ước ~{uoc_token:,} token ({mo_ta}). Mặc định TẮT.\n"
        f"Bật: {CO}=1\n"
        "Mặc định tắt vì cổng cũ đặt theo 'hạ tầng có sống không' — mà hạ tầng "
        "luôn sống trong lúc làm việc, nên nó thành mặc-định-BẬT. Điều kiện khả "
        "thi không phải điều kiện cho phép."
    )
