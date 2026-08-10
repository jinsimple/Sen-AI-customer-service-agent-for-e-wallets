"""Giai đoạn 2 (observability checklist) — xác nhận contextvars không rò rỉ
correlation_id/user_id giữa 2 request THẬT SỰ đồng thời (asyncio.gather), qua
đúng đường HTTP → middleware → tầng tool sâu nhất
(src/tools/get_customer_history.py — hàm này KHÔNG hề nhận correlation_id).

Nếu contextvars bị dùng sai (vd threading.local thay vì contextvars, hoặc
quên `reset()`), log của request A có thể lộ ra correlation_id/user_id của
request B khi 2 request xen kẽ nhau trên cùng thread pool — test này bắt lỗi
đó bằng chứng cứ thật (log JSON capture), không suy luận từ đọc code."""
from __future__ import annotations

import asyncio
import json
import logging

import httpx
import pytest
from httpx import ASGITransport
from sqlalchemy.orm import sessionmaker

from src.api.deps import get_session
from src.api.main import app
from src.auth import create_access_token


class _ListCaptureHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.lines: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.lines.append(self.format(record))


@pytest.mark.asyncio
async def test_concurrent_requests_do_not_leak_correlation_id(sample_db):
    # 2 request thật sự chạy SONG SONG (route sync `def` -> threadpool) không
    # được dùng CHUNG 1 Session/connection SQLite (không thread-safe khi 2
    # thread cùng execute trên 1 connection) — commit dữ liệu seed rồi cấp
    # MỖI request 1 Session riêng trên CÙNG engine (đã bật check_same_thread=
    # False, xem src/db/session.py), giống cách production thật (mỗi request
    # 1 session, xem src/api/deps.py::get_session).
    sample_db.commit()
    factory = sessionmaker(bind=sample_db.get_bind(), future=True)

    def _override_session():
        s = factory()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_session] = _override_session

    capture = _ListCaptureHandler()
    capture.setFormatter(logging.getLogger().handlers[0].formatter)  # dùng đúng JsonFormatter đã configure_logging()
    root = logging.getLogger()
    root.addHandler(capture)
    try:
        token_a = create_access_token(user_id="USR-A", role="customer")
        token_b = create_access_token(user_id="USR-B", role="customer")

        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp_a, resp_b = await asyncio.gather(
                client.post(
                    "/tools/get_customer_history",
                    headers={"Authorization": f"Bearer {token_a}", "X-Request-ID": "req-A-11111"},
                    json={},
                ),
                client.post(
                    "/tools/get_customer_history",
                    headers={"Authorization": f"Bearer {token_b}", "X-Request-ID": "req-B-22222"},
                    json={},
                ),
            )
    finally:
        root.removeHandler(capture)
        app.dependency_overrides.clear()

    assert resp_a.status_code == 200
    assert resp_b.status_code == 200
    # Header trả về đúng correlation_id request đó gửi lên — xác nhận tầng
    # HTTP không trộn lẫn giữa 2 request.
    assert resp_a.headers["X-Correlation-Id"] == "req-A-11111"
    assert resp_b.headers["X-Correlation-Id"] == "req-B-22222"

    tool_events = [json.loads(line) for line in capture.lines if '"get_customer_history_called"' in line]
    assert len(tool_events) == 2, f"Kỳ vọng đúng 2 log event từ tầng tool sâu nhất, có {len(tool_events)}"

    by_corr = {e["correlation_id"]: e for e in tool_events}
    assert set(by_corr) == {"req-A-11111", "req-B-22222"}
    # ĐÂY LÀ CHỖ BẮT LỖI RÒ RỈ THẬT: user_id gắn vào log event của tầng tool
    # (không hề nhận correlation_id/user_id qua tham số) PHẢI khớp ĐÚNG user
    # đã gọi request tương ứng — sai ở đây nghĩa là contextvars đã rò rỉ.
    assert by_corr["req-A-11111"]["user_id"] == "USR-A"
    assert by_corr["req-B-22222"]["user_id"] == "USR-B"
