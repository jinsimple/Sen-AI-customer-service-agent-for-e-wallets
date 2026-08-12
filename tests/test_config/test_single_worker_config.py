"""FIN05-StressTest-Plan-v2 ST2-P0-6 (docs/FIN05-Feature-Inventory-Security-
Review.md §1, §6) — backend PHẢI chạy đúng 1 uvicorn worker, quyết định kiến
trúc có chủ đích: `MemorySaver` (src/agents/graph.py, state hội thoại AI) và
`ConnectionManager` (src/api/live_chat_ws.py, state live-chat) đều giữ trong
RAM 1 process — nhiều worker sẽ làm khách mất trí nhớ agent / vỡ ngầm state
live-chat mà KHÔNG có lỗi rõ ràng nào báo ra lúc đó (chỉ lộ ra khi 2 request
liên tiếp của cùng 1 khách rơi vào 2 worker khác nhau — race hiếm, khó tái
hiện).

Test đọc TRỰC TIẾP file khởi động thật (`docker-entrypoint.sh`, KHÔNG phải
`Dockerfile` — lệnh uvicorn thật nằm ở entrypoint, xem ENTRYPOINT trong
Dockerfile) — regression chặn ai đó vô tình thêm `--workers N>1` mà quên
thêm Redis pub/sub cho cả 2 state trên."""
from __future__ import annotations

import re

from src.config import ROOT_DIR


def test_docker_entrypoint_does_not_set_multiple_uvicorn_workers():
    entrypoint = (ROOT_DIR / "docker-entrypoint.sh").read_text(encoding="utf-8")
    assert "uvicorn" in entrypoint, "Không tìm thấy lệnh uvicorn trong docker-entrypoint.sh — file đã đổi cấu trúc?"

    match = re.search(r"--workers\s+(\d+)", entrypoint)
    if match is not None:
        worker_count = int(match.group(1))
        assert worker_count == 1, (
            f"docker-entrypoint.sh đang chạy uvicorn với --workers {worker_count} — "
            "vi phạm quyết định kiến trúc 1-worker (MemorySaver/ConnectionManager "
            "giữ state in-memory). Nếu CỐ Ý muốn scale >1 worker, phải thêm Redis "
            "pub/sub cho CẢ HAI state trước, không chỉ xoá test này."
        )
    # Không có --workers nào = mặc định uvicorn (1 worker) — đúng ý muốn.


def test_docker_compose_does_not_scale_backend_replicas():
    compose = (ROOT_DIR / "docker-compose.yml").read_text(encoding="utf-8")
    match = re.search(r"backend:\s*\n(?:.*\n)*?(\s+deploy:\s*\n(?:.*\n)*?\s+replicas:\s*(\d+))", compose)
    if match is not None:
        replicas = int(match.group(2))
        assert replicas == 1, (
            f"docker-compose.yml đặt replicas={replicas} cho service backend — "
            "cùng lý do ở test_docker_entrypoint_does_not_set_multiple_uvicorn_workers, "
            "nhiều instance backend cũng vỡ state in-memory y hệt nhiều worker."
        )
