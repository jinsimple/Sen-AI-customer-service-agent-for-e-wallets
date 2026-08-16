"""Cổng ĐÓNG BĂNG LLM — một nguồn sự thật cho mọi test gọi model.

## Vì sao là một file riêng thay vì mỗi nơi một hàm

Tôi dựng cổng đóng băng, rồi **vi phạm chính nó hai lần**:

1. Lần một — cổng chỉ đọc biến môi trường; tôi quên `export` và đốt 3 lượt.
   Vá bằng file marker `.DANG-DONG-BANG-LLM` ở gốc repo.
2. Lần hai — tôi vá marker **chỉ ở `eval/`**, không mang sang `tests/`, rồi
   chạy bộ F-31/F-32 và đốt ~14 lượt nữa.

Lần hai đúng cùng một hình dạng với hai lỗi khác trong tuần: bug gộp khoảng
trắng (**ba** chỗ, tôi vá **một**) và bug nuốt mã trạng thái (**hai** chỗ, vá
**một**).

> **Vá một họ lỗi thì phải đi tìm HỌ, không vá cái đang cầm.**

Và cách chắc chắn nhất để không phải đi tìm lần sau: **để chỉ còn một chỗ**.
Bốn nơi gọi model trong `tests/` nay import chung hàm này. `eval/` giữ bản
riêng vì không import ngược được từ `tests/` — đó là chỗ duy nhất còn trùng
lặp, và nó được ghi ra ở đây để người sau biết mà sửa cả hai.

## Hai cổng, hai nghĩa — đừng gộp

    dang_dong_bang()      không được dùng model lúc này (người khác đang cần hạn mức)
    FIN05_CHO_PHEP_EP_429 được phép CỐ Ý đốt cạn hạn mức

Bỏ đóng băng nghĩa là *được dùng model bình thường*, **không** phải *được phép
làm cạn hạn mức của cả đội*.
"""
from __future__ import annotations

import os
import pathlib

GOC = pathlib.Path(__file__).resolve().parent.parent
MOC = GOC / ".DANG-DONG-BANG-LLM"

LY_DO = (
    "ĐANG ĐÓNG BĂNG LLM — test này gọi model nên không chạy. "
    "Trần TPM 200k dùng chung với 3 phiên Claude khác + PO thật; đo được 16/08: "
    "một người, 21 lượt, 2 phút đẩy org tới 193k/200k, và 429 ra tới khách thành "
    f"HTTP 500. Bỏ: unset FIN05_DONG_BANG_LLM · rm {MOC.name}"
)


def dang_dong_bang() -> bool:
    """True nếu có biến môi trường HOẶC file marker ở gốc repo.

    File marker sống qua shell, qua phiên, qua nén ngữ cảnh, và `ls` là thấy —
    biến môi trường thì chết theo shell, tức chỉ chặn được người đang nhớ bật
    nó, đúng người không cần chặn.
    """
    if os.environ.get("FIN05_DONG_BANG_LLM", "").strip() not in ("", "0", "false"):
        return True
    return MOC.exists()
