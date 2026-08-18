"""Một chỗ DUY NHẤT trả lời *"cây này có `eval/` không"* — và trả lời mà không nổ.

## Lỗi nó sửa, đo được 18/08 — LẦN THỨ HAI cùng một họ trong một ngày

`.dockerignore:11` loại `eval/` khỏi ảnh **có chủ đích**: `eval/heldout_set.jsonl`
là **tập NIÊM PHONG**, chỉ chạy một lần, và nó **không được vào ảnh**.

Nhưng ba tệp trong `tests/` đọc `eval/` **lúc IMPORT**:

    tests/test_bo_ca_luot_don_toan_ven.py:18        json.loads(FILE.read_text())
    tests/test_data/test_backoff_429_va_luot_khong.py:23   from eval._harness import …
    tests/test_data/test_bo_cham_da_luot_khong_bao_nham.py:31  from eval._harness import …

⟹ Trong container, pytest ném lỗi ở giai đoạn **thu thập**:

    docker exec … pytest tests/   →  Interrupted: 3 errors  →  0 CA CHẠY
    cùng lúc, từ HOST             →  579 passed · 2 failed · 42 skipped

🔴 **Và đây là phần đắt:** người chạy cổng bằng `docker exec` thấy **`0 failed`**
rồi đọc thành **xanh**. Một lượt chạy **không có ca nào chạy** và một lượt chạy
**mọi ca đều đạt** trông giống hệt nhau nếu chỉ nhìn số `failed`.

> Trạng thái đúng là **SKIP KÈM LÝ DO** — *"cây này không có `eval/`"* — chứ
> không phải *"tệp này hỏng"*. Luật 6: lý do skip phải **kiểm được bằng máy**,
> và `eval/` có mặt hay không thì kiểm được.

## Vì sao một file chung, không phải ba lần `try/except`

Cùng lý lẽ `tests/_dong_bang.py` và `tests/_docker_co_mat.py`: **vá một HỌ lỗi
thì phải đi tìm HỌ**, và cách chắc chắn nhất để không phải tìm lần sau là **để
chỉ còn một chỗ**.

🚫 **KHÔNG vá bằng cách bỏ `eval/` khỏi `.dockerignore`** — làm thế là đưa tập
**NIÊM PHONG** vào ảnh. Đó là quyết định của PO, không phải việc dọn dẹp.
"""
from __future__ import annotations

import pathlib

import pytest

GOC = pathlib.Path(__file__).resolve().parent.parent
THU_MUC_EVAL = GOC / "eval"

LY_DO = (
    "cây này KHÔNG có `eval/` — phép kiểm cần dữ liệu/harness trong `eval/` "
    "không chạy được ở đây. Thường gặp khi chạy TRONG container: "
    "`.dockerignore` loại `eval/` CÓ CHỦ ĐÍCH vì `eval/heldout_set.jsonl` là "
    "tập NIÊM PHONG, không được vào ảnh. Đây là SKIP vì THIẾU DỮ LIỆU, kiểm "
    "được bằng máy (Luật 6) — KHÔNG phải 'tệp test hỏng', và tuyệt đối không "
    "được để thành `Interrupted` (khi ấy 0 ca chạy mà bảng tổng báo 0 failed)."
)


def co_eval() -> bool:
    return THU_MUC_EVAL.is_dir()


def doi_hoi_eval() -> None:
    """Gọi ở ĐẦU module đọc `eval/`. Thiếu ⟹ skip cả module, kèm lý do."""
    if not co_eval():
        pytest.skip(LY_DO, allow_module_level=True)


def doi_hoi_tep(*ten: str) -> pathlib.Path:
    """Như trên, nhưng cho một tệp cụ thể trong `eval/`. Trả về đường dẫn."""
    doi_hoi_eval()
    p = THU_MUC_EVAL.joinpath(*ten)
    if not p.exists():
        pytest.skip(f"{LY_DO}\n(thiếu cụ thể: eval/{'/'.join(ten)})",
                    allow_module_level=True)
    return p
