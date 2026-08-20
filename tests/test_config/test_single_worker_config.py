"""FIN05-StressTest-Plan-v2 ST2-P0-6 (docs/FIN05-Feature-Inventory-Security-
Review.md §1, §6) — quyết định kiến trúc ban đầu: backend chạy đúng 1 uvicorn
worker vì `MemorySaver` (checkpointer AI) và `ConnectionManager` (state
live-chat, `src/api/live_chat_ws.py`) giữ state trong RAM 1 process — nhiều
worker sẽ làm khách mất trí nhớ agent / vỡ ngầm state live-chat KHÔNG có lỗi
rõ ràng nào báo ra lúc đó (race hiếm, khó tái hiện).

🔴 ĐÍNH CHÍNH 20/08 — quyết định đã ĐẢO, và cổng cũ ở đây XANH GIẢ trong lúc
đảo: `docker-entrypoint.sh` đổi từ `--workers 1` (ngầm định) sang
`--workers ${UVICORN_WORKERS}` (biến shell, mặc định 4, commit `0683792` +
`8890cd9`). Regex cũ (`--workers` theo sau bởi khoảng trắng rồi CHỮ SỐ) chỉ khớp SỐ LITERAL — biến shell
không khớp gì cả, rơi vào nhánh "không có --workers = 1 worker mặc định" và
XANH, dù hệ thống thật đã chạy 4 worker. Test tồn tại đúng hình thức, mất
tác dụng thật khi vật nó canh đổi dưới chân — cùng lớp lỗi đã bắt 3 lần khác
trong ngày (`--che-do moc`, cổng OTP rail, mock thiếu kwarg).

[ĐO Lead, đọc code trước khi kết luận, không suy luận]: multi-worker AN TOÀN
vì cả hai cơ chế chia sẻ state đã có TỪ TRƯỚC khi bật `UVICORN_WORKERS=4`:
  - Checkpointer: `MemorySaver` → `PostgresSaver` (state AI ra Postgres dùng
    chung, không còn RAM 1 process) — entrypoint hâm nóng lược đồ MỘT LẦN,
    TUẦN TỰ trước khi spawn worker (`8890cd9`, xem chú thích tại đó).
  - Live-chat: `ConnectionManager` đã có fan-out Redis pub/sub từ ADR-015
    (`docs/DECISIONS.md:266`, 13/08 — TRƯỚC đợt scale worker) — giao local
    trước, publish sau, `_INSTANCE_ID` để worker gốc bỏ qua tiếng vọng
    chính mình. Đã qua ít nhất một vòng vá thêm sau đó (mất tin đo thật
    25/60, đã sửa gốc), tức được đo bằng phép thử THẬT, không chỉ đọc code.

⟹ Test này ĐỔI Ý ĐỊNH: không còn cấm multi-worker tuyệt đối, mà đảm bảo
multi-worker CHỈ được bật khi CẢ HAI cơ chế chia-sẻ-state trên đều CÓ MẶT.
Nếu sau này ai gỡ MỘT trong hai (vô tình revert PostgresSaver hoặc pub/sub)
mà vẫn để `--workers` > 1, ca này phải ĐỎ ĐÚNG LÝ DO — không phải "im lặng
xanh vì regex không khớp" như trước."""
from __future__ import annotations

import re

from src.config import ROOT_DIR


def test_multi_worker_chi_duoc_bat_khi_du_ca_hai_co_che_chia_se_state():
    entrypoint = (ROOT_DIR / "docker-entrypoint.sh").read_text(encoding="utf-8")
    assert "uvicorn" in entrypoint, "Không tìm thấy lệnh uvicorn trong docker-entrypoint.sh — file đã đổi cấu trúc?"

    # 🔴 Luật PO-agent chốt 20/08, áp CHO CHÍNH ca này trước tiên: "không tìm
    # thấy thứ đang tìm" phải KÊU (đỏ), không phải IM (bỏ qua rồi coi là an
    # toàn) — thực tế hiện tại LUÔN có `--workers` trong entrypoint (dù giá
    # trị 1 hay biến shell); nếu ngày nào đó biến mất hẳn, đó là cấu trúc đã
    # đổi theo cách không ai lường trước, đáng dừng lại đọc, không phải suy
    # diễn "vắng mặt = mặc định 1, an toàn".
    match = re.search(r"--workers\s+(\S+)", entrypoint)
    assert match is not None, (
        "Không tìm thấy '--workers' nào trong docker-entrypoint.sh — cấu trúc lệnh khởi động đã "
        "đổi (có thể chuyển sang cơ chế khác hoàn toàn, vd Gunicorn/uvicorn-worker riêng). "
        "KHÔNG suy diễn 'vắng mặt = 1 worker mặc định, an toàn' — kiểm tra lại thủ công trước khi "
        "sửa lại ca này theo cấu trúc mới."
    )
    worker_token = match.group(1)
    la_so_1 = worker_token.isdigit() and int(worker_token) == 1

    if la_so_1:
        return  # 1 worker khai tường minh — không cần hai cơ chế chia sẻ state.

    # Từ đây: multi-worker CÓ THỂ được bật (số literal > 1, hoặc biến shell
    # cấu hình được — không biết giá trị runtime thật từ text tĩnh, nên coi
    # là "có thể" và đòi cả hai cơ chế, an toàn hơn là bỏ qua).
    assert "close_checkpointer" in entrypoint or "_build_checkpointer" in entrypoint, (
        f"docker-entrypoint.sh cho phép multi-worker (--workers {worker_token}) nhưng KHÔNG thấy "
        "bước hâm nóng lược đồ checkpointer tuần tự trước khi spawn worker — thiếu cơ chế #1 "
        "(PostgresSaver an toàn multi-worker). Xem commit 8890cd9."
    )

    import src.api.live_chat_ws as live_chat_ws

    thieu = [
        n for n in ("_PUBSUB_CHANNEL", "_vong_lap_subscriber")
        if not hasattr(live_chat_ws, n)
    ] + [
        n for n in ("_publish", "_giao_tu_pubsub")
        if not hasattr(live_chat_ws.ConnectionManager, n)
    ]
    assert not thieu, (
        f"docker-entrypoint.sh cho phép multi-worker (--workers {worker_token}) nhưng "
        f"src.api.live_chat_ws THIẾU cơ chế #2 (Redis pub/sub, ADR-015): {thieu!r}. "
        "ConnectionManager giữ state RAM 1 process — nhiều worker mà thiếu pub/sub sẽ "
        "vỡ ngầm live-chat (race hiếm, khó tái hiện, đúng cảnh báo gốc của test này)."
    )


def test_docker_compose_does_not_scale_backend_replicas():
    compose = (ROOT_DIR / "docker-compose.yml").read_text(encoding="utf-8")
    # Khẳng định NEO trước khi tin `match is None` là "không khai replicas,
    # an toàn" — nếu file đổi cấu trúc tới mức mất luôn service "backend:",
    # regex bên dưới cũng cho None, và không có dòng này thì hai tình huống
    # ("an toàn" và "mù") không phân biệt được, cùng cho xanh (PO-agent 20/08).
    assert "backend:" in compose, "Không tìm thấy service 'backend' trong docker-compose.yml — file đã đổi cấu trúc?"
    match = re.search(r"backend:\s*\n(?:.*\n)*?(\s+deploy:\s*\n(?:.*\n)*?\s+replicas:\s*(\d+))", compose)
    if match is not None:
        replicas = int(match.group(2))
        assert replicas == 1, (
            f"docker-compose.yml đặt replicas={replicas} cho service backend — nhiều INSTANCE "
            "(khác nhiều WORKER trong 1 instance) là một trục khác, chưa được đo/quyết định an "
            "toàn ở đây — PostgresSaver + Redis pub/sub chứng minh an toàn cho multi-WORKER cùng "
            "1 instance, không tự động suy ra an toàn cho multi-INSTANCE."
        )
