"""Một chỗ DUY NHẤT trả lời *"máy này có `docker` không"* — và trả lời mà không nổ.

## Lỗi nó sửa, đo được 18/08

Bảy module trong `tests/` dò container bằng `subprocess.run(["docker", ...])`
**ngay trong biểu thức `skipif`**, tức **lúc IMPORT**. Trên một máy không có
`docker`, `subprocess` ném `FileNotFoundError` **trong lúc pytest thu thập**:

```
có docker      634 tests collected
KHÔNG docker   594 collected, 11 errors,  Interrupted  ⟹  0 CA CHẠY
```

🔴 **Một tệp nhị phân vắng mặt biến cả bộ ca thành "không ca nào chạy".** Và nó
**không phải cái chết lặng lẽ** — nó ồn ào. Nhưng nó sai hình dạng theo hướng
đắt hơn: **`Interrupted` xoá sạch kết quả của 577 ca không liên quan gì tới
docker.** Người đọc thấy "0 passed" và không có cách nào biết 577 ca kia lẽ ra
đã xanh.

> Trạng thái đúng ở đây là **SKIP KÈM LÝ DO** — *"môi trường này không chạy được
> phép kiểm ấy"* — chứ không phải *"tệp này hỏng"*. Đúng **Luật 6**: một `skip`
> phải tự chứng minh lý do skip là THẬT, và lý do "không có docker" **kiểm được
> bằng máy**.

## Vì sao một file chung thay vì bảy lần `try/except`

Cùng lý lẽ `tests/_dong_bang.py` đã ghi: **vá một HỌ lỗi thì phải đi tìm HỌ,
đừng vá cái đang cầm** — và cách chắc chắn nhất để không phải đi tìm lần sau là
**để chỉ còn một chỗ**. Bảy nơi dò docker nay gọi chung hàm này.
"""
from __future__ import annotations

import subprocess

LY_DO = (
    "máy này không có `docker` trên PATH — phép kiểm cần container không chạy "
    "được ở đây. Đây là SKIP vì THIẾU CÔNG CỤ, kiểm được bằng máy (Luật 6), "
    "không phải skip cho qua chuyện."
)


def co_docker() -> bool:
    """`docker` có gọi được không. **Không bao giờ ném.**"""
    try:
        return subprocess.run(["docker", "version"], capture_output=True,
                              timeout=30).returncode == 0
    except (FileNotFoundError, OSError, subprocess.SubprocessError):
        return False


def container_song(name_text: str) -> bool:
    """Container `ten` có đang chạy không. **Không bao giờ ném.**

    Trả `False` khi thiếu `docker` — nên nơi gọi chỉ cần **một** điều kiện
    `skipif`, không phải hai điều kiện lồng nhau mà ai đó sẽ quên một nửa.
    """
    try:
        r = subprocess.run(["docker", "ps", "-q", "-f", f"name={name_text}"],
                           capture_output=True, text=True, timeout=30)
    except (FileNotFoundError, OSError, subprocess.SubprocessError):
        return False
    return bool(r.stdout.strip())
