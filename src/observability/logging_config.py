"""Structured JSON logging shared across the app — replaces free-form string logs/print().
Each log line is one JSON event, automatically tagged with `correlation_id`/
`user_id` from contextvars (src/observability/context.py), no manual threading.

Writes to stdout (12-factor — see the production-packaging-checklist.md playbook applied to
packaging), NOT to a file — unlike `logs/access.log`
(the separate security audit log, src/api/main.py, left untouched here)."""
from __future__ import annotations

import datetime as dt
import json
import logging
import sys

from src.observability.context import get_context_user_id, get_correlation_id

# Standard LogRecord fields — excluded when collecting the "extra" fields a caller passes
# via logger.info(..., extra={...}), to avoid duplicating/swallowing system fields.
_STANDARD_RECORD_FIELDS = frozenset(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {
    "message",
    "asctime",
    "correlation_id",
    "user_id",
}


class ContextFilter(logging.Filter):
    """Attach the current correlation_id/user_id (contextvars) to EVERY LogRecord —
    this is the "automatic inheritance" mechanism instead of threading them through parameters."""

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
        # Exceptions MUST NOT be swallowed during JSON serialisation (phase 2, item
        # "dedicated exception handling") — the full traceback is formatted into one field.
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        for key, value in record.__dict__.items():
            if key not in _STANDARD_RECORD_FIELDS and key not in payload:
                payload[key] = value
        return json.dumps(payload, ensure_ascii=False, default=str)


_configured = False


def configure_logging(level: int = logging.INFO) -> None:
    """Idempotent — safe to call repeatedly (e.g. tests re-importing the module) without
    duplicating handlers."""
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
