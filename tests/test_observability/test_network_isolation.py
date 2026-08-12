"""FIN05-StressTest-Plan-v2 ST2-E-05/F-07/F-08/F-09 (docs/FIN05-Feature-
Inventory-Security-Review.md §1) — test CẤU HÌNH TĨNH, đọc trực tiếp
`Caddyfile`/`docker-compose.yml`. GIỚI HẠN THẬT cần nói rõ (không giả vờ đã
test đủ): CI hiện tại (`lint-and-test`, `.github/workflows/ci.yml`) chạy
uvicorn/npm TRỰC TIẾP trên runner, KHÔNG qua `docker compose up` — không có
mạng Docker/Caddy thật để probe. Xác nhận network THẬT (curl từ ngoài
container, xem không lọt được vào Postgres/backend) chỉ có ý nghĩa khi chạy
tay `docker compose up` cục bộ hoặc trên VPS thật — xem docs/TESTING.md mục
"v2 bổ sung" cho checklist thao tác tay tương ứng."""
from __future__ import annotations

import re

from src.config import ROOT_DIR


def test_caddyfile_has_exactly_one_direct_backend_exception_for_live_chat_ws():
    caddyfile = (ROOT_DIR / "Caddyfile").read_text(encoding="utf-8")

    handle_blocks = re.findall(r"handle\s+([^\s{]*)\s*\{[^}]*reverse_proxy\s+([^\s\n]+)", caddyfile)
    direct_backend_paths = [path for path, target in handle_blocks if target.startswith("backend:")]

    assert direct_backend_paths == ["/ws/live-chat*"], (
        f"Kỳ vọng ĐÚNG 1 path forward thẳng backend ('/ws/live-chat*'), "
        f"tìm thấy: {direct_backend_paths} — mọi path khác PHẢI qua "
        "frontend:3000 (BFF), không được thêm ngoại lệ mới mà không rà soát "
        "lại nguyên tắc 'backend không lộ ra ngoài trừ qua BFF'."
    )

    frontend_targets = [target for _, target in handle_blocks if target.startswith("frontend:")]
    assert frontend_targets, "Phải còn ít nhất 1 khối handle mặc định forward về frontend:3000"


def test_docker_compose_backend_and_postgres_do_not_publish_ports_to_host():
    compose = (ROOT_DIR / "docker-compose.yml").read_text(encoding="utf-8")

    for service in ("backend", "postgres", "frontend"):
        match = re.search(rf"\n  {service}:\s*\n((?:.*\n)*?)(?=\n  \S|\Z)", compose)
        assert match is not None, f"Không tìm thấy service '{service}' trong docker-compose.yml"
        block = match.group(1)
        assert "ports:" not in block, (
            f"Service '{service}' đang publish port ra host (có khối 'ports:') — "
            "vi phạm nguyên tắc chỉ Caddy là cửa ra internet duy nhất."
        )


def test_jaeger_ui_only_binds_loopback():
    compose = (ROOT_DIR / "docker-compose.yml").read_text(encoding="utf-8")
    match = re.search(r"\n  jaeger:\s*\n((?:.*\n)*?)(?=\n  \S|\Z)", compose)
    assert match is not None, "Không tìm thấy service 'jaeger' trong docker-compose.yml"
    block = match.group(1)

    port_lines = [
        line.strip() for line in block.splitlines() if re.search(r"\d+:\d+", line) and not line.strip().startswith("#")
    ]
    assert port_lines, "Service jaeger phải có ít nhất 1 dòng publish port cho UI (16686)"
    for line in port_lines:
        normalized = line.lstrip("- ").strip('"')
        assert normalized.startswith("127.0.0.1:"), (
            f"Port Jaeger UI phải chỉ bind 127.0.0.1 (không public ra mọi "
            f"interface): {line}"
        )
