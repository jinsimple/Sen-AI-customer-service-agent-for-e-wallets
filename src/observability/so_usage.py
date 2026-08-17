"""Sổ usage — ghi token của MỖI lượt vào JSONL trên volume, để có MỐC NỀN.

VÌ SAO TỒN TẠI (đo 17/08): `grep` usage trong log cả ba ngăn xếp ra **0 dòng**,
và không bảng nào lưu token. Usage chỉ sống trong stdout của tiến trình, mà
`docker logs` là PER-CONTAINER — mỗi lần recreate là mất sạch. Riêng chiều đó
tôi recreate 6 lần trong hai giờ.

⟹ Hôm nay dự án **không trả lời được** "tiêu bao nhiêu, ở đâu". Nặng hơn cho
đợt tiết kiệm token: **không có mốc nền để chứng minh một bản cắt có tác dụng**
— cắt xong không so được với gì, và "đã tối ưu" sẽ thành một câu không kiểm
chứng được.

Cùng họ F-33c: số sinh ra rồi bay mất.

## Vì sao JSONL trên volume, KHÔNG phải bảng mới trong DB

Đo trước khi chọn, không chọn theo thói quen:

    ghi /app/logs/... -> recreate -> đọc lại được          ✅ (đã thử thật)
    stdout container  -> recreate -> log container cũ MẤT  ✅ (đã thử thật)

`logs_data:/app/logs` là **named volume** (docker-compose.yml), sống qua
recreate và qua `down` (chỉ mất khi `down -v`).

Bảng mới trong DB cũng chạy được, nhưng nó kéo theo migration + `models.py`,
và đường JSONL cho ta mốc nền **ngay hôm nay** thay vì xếp sau ba ADR đang
treo. Đây là công cụ ĐO, không phải dữ liệu nghiệp vụ — nó không cần join với
`tickets`, không cần ràng buộc toàn vẹn, và không nên nằm trong đường ghi của
sản phẩm.

## Giới hạn, khai trước

· mất khi `docker compose down -v` (cùng số phận `postgres_data`)
· mỗi ngăn xếp một sổ riêng, không gộp
· không join được với bản ghi nghiệp vụ — chỉ có `thread_id` làm mối nối
· KHÔNG BAO GIỜ ghi nội dung hội thoại. Chỉ số đếm và nhãn.
"""
from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path

_logger = logging.getLogger("fin05.usage")

DUONG_SO = Path(os.environ.get("DUONG_SO_USAGE", "/app/logs/usage.jsonl"))

# Ghi từ nhiều worker/thread vào cùng file: mỗi dòng là một lần `write` ngắn
# (< PIPE_BUF) nên POSIX append đã nguyên tử ở mức dòng. Khoá này chỉ chống
# xen kẽ giữa các thread TRONG một tiến trình.
_khoa = threading.Lock()
_da_canh_bao = False


def ghi_usage(ban_ghi: dict) -> None:
    """Ghi một dòng. KHÔNG BAO GIỜ làm hỏng lượt chat vì lỗi ghi sổ.

    Nuốt lỗi ở đây là đúng — sổ đo hỏng không được phép làm khách mất câu trả
    lời. Nhưng nuốt IM LẶNG thì không: cảnh báo MỘT lần (không mỗi lượt, tránh
    đúng cái còi kêu bừa rồi bị tắt), và sổ rỗng sẽ tự lộ khi ai đó đi đọc.
    """
    global _da_canh_bao
    try:
        DUONG_SO.parent.mkdir(parents=True, exist_ok=True)
        dong = json.dumps(ban_ghi, ensure_ascii=False)
        with _khoa, DUONG_SO.open("a", encoding="utf-8") as f:
            f.write(dong + "\n")
    except Exception as e:  # noqa: BLE001 — xem docstring
        if not _da_canh_bao:
            _da_canh_bao = True
            _logger.error(
                "khong_ghi_duoc_so_usage",
                extra={"duong": str(DUONG_SO), "loi": type(e).__name__,
                       "hau_qua": "mat moc nen cho moi phep so truoc/sau"},
            )
