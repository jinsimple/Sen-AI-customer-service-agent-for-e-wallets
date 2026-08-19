"""BỂ MODEL cho tính năng đổi/xoay (GĐ3, PO thật chốt 19/08 — `876a240`).

Đảo có khai một quyết định cũ CÓ CHỦ ĐÍCH (`a3fb125`: ghim model theo NGÀY, vì
"đổi model = đổi VẬT" — mọi phép đo A/B phụ thuộc danh tính model). Xoay ở đây
là chế độ DEMO/TEST: `usage.jsonl` vẫn ghi `model` PER-LƯỢT (không đổi) — đó là
thứ cứu ta khi đọc số sau này; mọi phép đo eval NGHIÊM TÚC vẫn phải GHIM một
model, không được chạy qua module này.

TRẠNG THÁI "model đã cạn" ở REDIS, KHÔNG phải biến tiến trình — cùng bài học
`docker-entrypoint.sh:16 UVICORN_WORKERS=4` đã buộc `cong_ra_ngoai.py` phải làm
vậy: 4 worker độc lập, một biến trong RAM chỉ đúng cho 1/4 số lượt.

FAIL-OPEN khi Redis lỗi (coi như "chưa cạn") — cùng triết lý `thread_signals.py`:
đây là tính năng PHỤ (giúp né một model đã biết hỏng), không phải cửa vào. Đọc
sai theo hướng "thử lại một model đã cạn" chỉ tốn tối đa MỘT lời gọi hỏng, vòng
xoay tự sửa ở lần thử kế; đọc sai theo hướng ngược lại (coi mọi model đều cạn)
sẽ làm KHÁCH THẬT nhận "bể cạn toàn phần" trong khi mọi model đều ổn — tệ hơn
nhiều. Đây là quyết định NGƯỢC với trần chi tiêu ở `cong_ra_ngoai.py` (fail-
CLOSED, vì đó là cơ chế BẢO VỆ TIỀN, không phải tiện ích né lỗi) — đọc kỹ trước
khi "làm cho nhất quán", hai nơi khác câu hỏi nên khác chiều lỗi cố ý.
"""
from __future__ import annotations

import logging

from src.config import LLM_MODEL_POOL
from src.redis_client import get_default_client

_logger = logging.getLogger("fin05.llm_pool")

# KHÔNG tiền tố "fin05:" — khác `thread_signals.py`, CỐ Ý: đây là tên đã KHAI
# cho QA/QC trước khi họ viết cổng (`test_llm_pool_gd3.py`, viết từ đặc tả,
# không đọc src/). Đổi tiền tố ở đây mà không báo là đúng lớp lỗi "khai một
# đằng, code một nẻo" — sửa CODE khớp đã khai, không bắt test viết lại.
_KHOA_PREFIX = "model_can:"
# TTL là BACKOFF — "bao lâu thì THỬ LẠI model này", KHÔNG PHẢI suy đoán chu kỳ
# reset hạn ngạch thật của nhà cung cấp (ta không biết, và không cần biết để
# chọn con số này đúng). Sai hướng ngắn -> tốn một lượt thử rồi cạn lại (rẻ).
# Sai hướng dài -> chậm nhận ra model đã hồi, tối đa bằng chính TTL (rẻ).
TTL_MODEL_CAN_GIAY = 15 * 60


def _khoa(model: str) -> str:
    return f"{_KHOA_PREFIX}{model}"


def model_dang_can(model: str) -> bool:
    """Model này đang bị đánh dấu cạn không? Redis lỗi -> False (fail-open)."""
    try:
        return get_default_client().exists(_khoa(model)) > 0
    except Exception as e:  # noqa: BLE001
        _logger.warning("model_dang_can_that_bai", extra={"model": model, "loi": repr(e)})
        return False


def danh_dau_can(model: str) -> None:
    """Đánh dấu `model` cạn trong `TTL_MODEL_CAN_GIAY` giây. Ghi sự kiện log
    `model_rotated` — KHÔNG log key/token, chỉ tên model (đã tự khai không
    nhạy cảm, xem `config.py:298`, cùng nếp `LLM_MODEL`)."""
    try:
        client = get_default_client()
        client.set(_khoa(model), "1", ex=TTL_MODEL_CAN_GIAY)
    except Exception as e:  # noqa: BLE001
        _logger.warning("danh_dau_can_that_bai", extra={"model": model, "loi": repr(e)})
    _logger.warning("model_rotated", extra={"model_can": model, "ttl_giay": TTL_MODEL_CAN_GIAY})


def model_dau_luot(da_thu: set[str] | None = None) -> str | None:
    """Model tiếp theo cho ĐẦU LƯỢT — model đầu tiên trong bể (theo thứ tự ưu
    tiên khai ở `LLM_MODEL_POOL`) CHƯA bị đánh dấu cạn và CHƯA có trong
    `da_thu` (những model lượt xoay này đã thử và thất bại).

    Trả `None` khi TOÀN BỘ bể đã cạn/đã thử — người gọi phải xử lý ca này bằng
    một thông điệp tử tế, KHÔNG lặp vô hạn (đúng ràng buộc PO `876a240`).

    KHÔNG có tham số `thread_id`: chọn model là quyết định TOÀN CỤC theo bể,
    không theo từng khách — "model X cạn" là sự thật chung cho mọi hội thoại.
    """
    thu = da_thu or set()
    for model in LLM_MODEL_POOL:
        if model in thu:
            continue
        if not model_dang_can(model):
            return model
    return None
