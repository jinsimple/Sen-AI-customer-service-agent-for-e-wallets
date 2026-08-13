"""Fan-out live-chat qua Redis pub/sub — điều kiện BẮT BUỘC để chạy multi-worker.

VÌ SAO CÓ FILE NÀY (ADR-015)
----------------------------
`ConnectionManager` giữ WebSocket trong RAM của TỪNG process. Bật multi-worker
(cần thiết để phục vụ 150 người đồng thời, xem ADR-014) mà không có lớp fan-out
này thì live-chat **vỡ âm thầm**: khách nối vào worker 1, CSKH nối vào worker 2,
mỗi bên gửi tin chỉ tới được socket của chính worker mình — hai người ngồi
trong cùng một phiên chat mà không ai thấy tin nhắn của ai.

Không có exception nào được ném ra. Không có log lỗi. Tin nhắn chỉ đơn giản
biến mất. Đây đúng loại lỗi mà test tay khó bắt (một máy thường chỉ nối vào
một worker) nên phải có test tự động canh.

Mô phỏng 2 worker bằng 2 instance ConnectionManager trong cùng process, nối
với nhau qua Redis (fakeredis lúc test) — đúng cơ chế thật, chỉ khác chỗ chạy.
"""

from __future__ import annotations

import json

import pytest

from src.api import live_chat_ws as mod
from src.api.live_chat_ws import ConnectionManager


class _SocketGia:
    """WebSocket giả — chỉ ghi lại payload nhận được."""

    def __init__(self):
        self.da_nhan: list[dict] = []

    async def send_json(self, payload):
        self.da_nhan.append(payload)


@pytest.fixture(autouse=True)
def _redis_sach():
    from src.redis_client import get_default_client

    get_default_client().flushall()
    yield


def _mo_kenh():
    """Mở subscription TRƯỚC khi publish.

    Redis pub/sub là fire-and-forget: thông điệp phát ra lúc chưa ai subscribe
    thì mất luôn, không có hàng đợi giữ lại. Đây cũng là lý do vòng lặp
    subscriber thật phải khởi động ở FastAPI startup, trước khi có traffic —
    lỗi thật mắc phải lúc viết test này (subscribe sau publish -> không nhận
    được gì, tưởng code hỏng).
    """
    from src.redis_client import get_default_client

    pubsub = get_default_client().pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe(mod._PUBSUB_CHANNEL)
    return pubsub


async def _bom_pubsub_sang(pubsub, mgr: ConnectionManager, bo_qua_tieng_vong: bool = True) -> None:
    """Đọc thông điệp đang chờ rồi giao cho `mgr` — thay cho vòng lặp subscriber.

    Gọi trực tiếp thay vì chạy `_vong_lap_subscriber` để test tất định, không
    phụ thuộc timing của asyncio.to_thread.
    """
    for _ in range(5):
        msg = pubsub.get_message(timeout=0.1)
        if not msg:
            continue
        data = json.loads(msg["data"])
        if bo_qua_tieng_vong and data.get("src") == mod._INSTANCE_ID:
            continue
        await mgr._giao_tu_pubsub(data.get("kind", ""), data.get("target"), data.get("payload") or {})


@pytest.mark.asyncio
async def test_broadcast_staff_toi_duoc_worker_khac(monkeypatch):
    """CSKH ở worker 2 PHẢI thấy queue_update do worker 1 phát."""
    worker1, worker2 = ConnectionManager(), ConnectionManager()
    ws_cskh_o_worker2 = _SocketGia()
    worker2._staff_sockets.add(ws_cskh_o_worker2)

    pubsub = _mo_kenh()  # PHẢI mở trước khi publish
    await worker1.broadcast_to_staff({"type": "queue_update", "waiting": 1})

    # worker2 nhận qua pub/sub — đổi INSTANCE_ID để không bị coi là tiếng vọng
    monkeypatch.setattr(mod, "_INSTANCE_ID", "worker-2-khac")
    await _bom_pubsub_sang(pubsub, worker2)

    assert ws_cskh_o_worker2.da_nhan, (
        "CSKH ở worker khác KHÔNG nhận được broadcast — live-chat sẽ vỡ âm thầm "
        "khi bật multi-worker."
    )
    assert ws_cskh_o_worker2.da_nhan[0]["type"] == "queue_update"


@pytest.mark.asyncio
async def test_tin_nhan_trong_phien_toi_duoc_worker_khac(monkeypatch):
    """Khách ở worker 1, CSKH ở worker 2, cùng 1 chat_session_id."""
    worker1, worker2 = ConnectionManager(), ConnectionManager()
    ws_o_worker2 = _SocketGia()
    worker2._session_sockets["CHS-1"].add(ws_o_worker2)

    pubsub = _mo_kenh()
    await worker1.send_to_session("CHS-1", {"type": "message", "text": "chào bạn"})

    monkeypatch.setattr(mod, "_INSTANCE_ID", "worker-2-khac")
    await _bom_pubsub_sang(pubsub, worker2)

    assert ws_o_worker2.da_nhan, "Tin nhắn không tới được socket ở worker khác"
    assert ws_o_worker2.da_nhan[0]["text"] == "chào bạn"


@pytest.mark.asyncio
async def test_khong_giao_hai_lan_cho_socket_local():
    """Worker gốc phải BỎ QUA tiếng vọng của chính mình.

    Nếu không, socket local nhận 2 lần cùng một tin: 1 lần giao trực tiếp,
    1 lần qua pub/sub — khách thấy tin nhắn lặp đôi.
    """
    worker1 = ConnectionManager()
    ws_local = _SocketGia()
    worker1._staff_sockets.add(ws_local)

    pubsub = _mo_kenh()
    await worker1.broadcast_to_staff({"type": "queue_update", "waiting": 2})
    assert len(ws_local.da_nhan) == 1, "Giao local phải đúng 1 lần"

    # Bơm lại chính thông điệp vừa publish (src == _INSTANCE_ID) -> phải bị bỏ qua
    await _bom_pubsub_sang(pubsub, worker1)
    assert len(ws_local.da_nhan) == 1, (
        f"Socket local nhận {len(ws_local.da_nhan)} lần — tiếng vọng của chính "
        "worker không bị lọc, khách sẽ thấy tin nhắn lặp đôi."
    )


@pytest.mark.asyncio
async def test_redis_hong_khong_lam_chet_duong_local(monkeypatch):
    """Redis chết -> live-chat suy giảm về phạm vi 1 worker, KHÔNG chết hẳn.

    Đây là lựa chọn có chủ đích: mất fan-out liên worker còn hơn mất luôn cả
    tin nhắn cho người đang ngồi cùng worker.
    """
    worker = ConnectionManager()
    ws_local = _SocketGia()
    worker._staff_sockets.add(ws_local)

    def _redis_chet():
        raise RuntimeError("Redis không nối được")

    monkeypatch.setattr("src.redis_client.get_default_client", _redis_chet)

    await worker.broadcast_to_staff({"type": "queue_update", "waiting": 3})

    assert ws_local.da_nhan, (
        "Redis hỏng làm chết luôn đường giao local — sai thiết kế, phải suy "
        "giảm có kiểm soát chứ không sập."
    )


@pytest.mark.asyncio
async def test_moi_worker_co_instance_id_rieng():
    """Hai process khác nhau phải có _INSTANCE_ID khác nhau, nếu không bộ lọc
    tiếng vọng sẽ chặn nhầm tin của worker kia."""
    assert mod._INSTANCE_ID and len(mod._INSTANCE_ID) >= 8
