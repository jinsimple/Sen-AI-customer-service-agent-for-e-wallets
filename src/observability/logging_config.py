"""Structured JSON logging dùng chung toàn app — thay cho log dạng chuỗi tự
do/print(). Mỗi dòng log là 1 sự kiện JSON, tự động gắn `correlation_id`/
`user_id` từ contextvars (src/observability/context.py), không cần truyền tay.

Ghi ra stdout (12-factor — xem playbook production-packaging-checklist.md đã
áp dụng cho phần đóng gói), KHÔNG phải file — khác với `logs/access.log`
(audit log bảo mật riêng, src/api/main.py, giữ nguyên không đổi ở đây)."""
from __future__ import annotations

import datetime as dt
import json
import logging
import sys

from src.observability.context import get_context_user_id, get_correlation_id

# Field chuẩn của LogRecord — loại trừ khi gom "extra" field người gọi truyền
# qua logger.info(..., extra={...}), tránh lặp/nuốt field hệ thống.
_STANDARD_RECORD_FIELDS = frozenset(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {
    "message",
    "asctime",
    "correlation_id",
    "user_id",
}


class ContextFilter(logging.Filter):
    """Gắn correlation_id/user_id hiện hành (contextvars) vào MỌI LogRecord —
    đây là cơ chế "tự động thừa hưởng" thay vì truyền tay qua tham số hàm."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = get_correlation_id()
        record.user_id = get_context_user_id()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": dt.datetime.now(dt.UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", None),
            "user_id": getattr(record, "user_id", None),
        }
        # exception KHÔNG được nuốt mất khi serialize JSON (Giai đoạn 2, mục
        # "xử lý riêng cho exception") — format nguyên traceback vào 1 field.
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        for key, value in record.__dict__.items():
            if key not in _STANDARD_RECORD_FIELDS and key not in payload:
                payload[key] = value
        return json.dumps(payload, ensure_ascii=False, default=str)


_configured = False


def configure_logging(level: int = logging.INFO) -> None:
    """Idempotent — an toàn gọi nhiều lần (vd test import lại module) mà
    không nhân đôi handler."""
    global _configured
    if _configured:
        return
    root = logging.getLogger()
    root.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(ContextFilter())
    root.handlers = [handler]
    _configured = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
