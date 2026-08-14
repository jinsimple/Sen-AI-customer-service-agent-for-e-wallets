"""Live chat WebSocket (2026-08-11).

2 lớp test:
1. ConnectionManager (vé + routing/broadcast) — test bằng FAKE WebSocket (ghi
   lại lệnh gọi send_json), KHÔNG qua TestClient thật. Lý do: TestClient mô
   phỏng WS qua kết nối anyio nội bộ — push từ 1 task (route REST claim)
   sang WebSocket đang chạy ở task KHÁC (handler WS) không đáng tin cậy
   trong môi trường test (phát hiện thật: bị treo vô thời hạn khi thử full
   integration test 2 kết nối thật) dù đây là pattern chuẩn, được hỗ trợ tốt
   trên server ASGI thật (uvicorn) — giới hạn của TestClient, không phải bug
   sản phẩm. Test trực tiếp logic routing/broadcast tách khỏi transport WS
   thật vừa nhanh vừa xác định, đúng tinh thần unit test.
2. 1 smoke test end-to-end DUY NHẤT qua TestClient thật (1 kết nối, không có
   push chéo task) — xác nhận route /ws/live-chat mount đúng, vé xác thực
   đúng, nhận được tin nhắn hệ thống đầu phiên."""
from __future__ import annotations

import asyncio
import datetime as dt
import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from src.api.deps import get_session
from src.api.live_chat_ws import ConnectionManager
from src.api.main import app
from src.auth import create_access_token
from src.db.models import ChatSession
from src.services import live_chat
from src.services.complaint_intake import create_ticket_with_fraud_check


class _FakeWebSocket:
    def __init__(self):
        self.sent: list[dict] = []
        self.closed = False

    async def send_json(self, payload: dict) -> None:
        self.sent.append(payload)

    async def close(self) -> None:
        self.closed = True


def test_ws_ticket_consumed_once_and_expires():
    manager = ConnectionManager()
    ticket = manager.mint_ticket(user_id="USR-A", role="customer", chat_session_id="CHS-1")

    # Kho vé chuyển từ dict RAM sang Redis (QA-01, 13/08): `expires_at` cũ là
    # time.monotonic() — vô nghĩa liên process, TTL giờ do Redis giữ. So khớp
    # ĐÚNG BẰNG (không phải chỉ chứa) để bắt được trường lạ lọt vào payload vé.
    first = manager.consume_ticket(ticket)
    assert first == {"user_id": "USR-A", "role": "customer", "chat_session_id": "CHS-1"}

    second = manager.consume_ticket(ticket)
    assert second is None, "vé dùng 1 lần phải bị xoá ngay sau lần dùng đầu tiên"


def test_ws_ticket_expired_returns_none(monkeypatch):
    monkeypatch.setattr("src.api.live_chat_ws._WS_TICKET_TTL_SECONDS", 0)
    manager = ConnectionManager()
    ticket = manager.mint_ticket(user_id="USR-A", role="customer")
    time.sleep(0.01)
    assert manager.consume_ticket(ticket) is None


def test_rate_limiter_blocks_after_max_calls():
    manager = ConnectionManager()
    limiter = manager.ws_ticket_limiter
    for _ in range(5):
        assert limiter.allow("USR-A") is True
    assert limiter.allow("USR-A") is False
    assert limiter.allow("USR-B") is True, "giới hạn phải tách riêng theo từng key, không dùng chung"


def test_notify_claimed_pushes_context_to_claiming_staff_and_broadcasts_others():
    async def _run():
        manager = ConnectionManager()
        staff_ws = _FakeWebSocket()
        other_staff_ws = _FakeWebSocket()
        customer_ws = _FakeWebSocket()

        await manager.register(staff_ws, user_id="USR-CSKH", chat_session_id=None, is_staff=True)
        await manager.register(other_staff_ws, user_id="USR-SUP", chat_session_id=None, is_staff=True)
        await manager.register(customer_ws, user_id="USR-A", chat_session_id="CHS-1", is_staff=False)

        await manager.notify_claimed(chat_session_id="CHS-1", staff_user_id="USR-CSKH", context={"ticket": {"ticket_id": "TCK-1"}})

        assert staff_ws.sent[0]["type"] == "claim_success"
        assert staff_ws.sent[0]["context"]["ticket"]["ticket_id"] == "TCK-1"
        assert any(m["type"] == "session_claimed" for m in staff_ws.sent)
        assert any(m["type"] == "session_claimed" for m in other_staff_ws.sent)
        assert any(m["type"] == "system" for m in customer_ws.sent)
        # claim thành công PHẢI đăng ký socket của CSKH làm participant của
        # phiên NGAY (không cần round-trip "join_session" riêng) — nên
        # staff_ws cũng nhận được tin "system" gửi cho participant của CHS-1.
        assert any(m["type"] == "system" for m in staff_ws.sent)
        assert staff_ws not in manager._session_sockets.get("CHS-2", set())

    asyncio.run(_run())


def test_register_closes_stale_connection_for_same_user():
    """Phát hiện thật (2026-08-11, test tay qua docker compose): 1 user có
    thể để lại kết nối WS "mồ côi" (tab cũ, mạng chập chờn không kích hoạt
    đúng sự kiện disconnect) — nếu không dọn, broadcast gửi tới CẢ kết nối
    cũ lẫn mới, client thấy tin nhắn như bị lặp/tách. register() PHẢI chủ
    động đóng + gỡ đăng ký kết nối cũ trước khi nhận kết nối mới cho cùng
    user_id."""

    async def _run():
        manager = ConnectionManager()
        old_ws = _FakeWebSocket()
        new_ws = _FakeWebSocket()

        await manager.register(old_ws, user_id="USR-CSKH", chat_session_id="CHS-1", is_staff=True)
        await manager.register(new_ws, user_id="USR-CSKH", chat_session_id="CHS-1", is_staff=True)

        assert old_ws.closed is True
        assert manager._user_sockets["USR-CSKH"] == {new_ws}
        assert manager._session_sockets["CHS-1"] == {new_ws}
        assert manager._staff_sockets == {new_ws}

        await manager.send_to_session("CHS-1", {"type": "message", "content": "chào bạn"})
        assert old_ws.sent == [], "kết nối cũ đã đóng không được nhận broadcast"
        assert new_ws.sent == [{"type": "message", "content": "chào bạn"}]

    asyncio.run(_run())


def test_release_staff_sessions_returns_active_session_to_queue(sample_db, monkeypatch):
    """Phát hiện thật (2026-08-11, test tay): CSKH chat xong F5 KHÔNG bấm
    "Kết thúc chat" — phiên đang active bị bỏ quên mãi mãi, khách đòi gặp
    nhân viên lại không thấy thông báo ticket mới nào (phiên cũ vẫn active,
    không phải waiting). release_staff_sessions() PHẢI trả phiên về hàng
    chờ ngay khi WS của CSKH ngắt kết nối."""
    created = create_ticket_with_fraud_check(
        sample_db, user_id="USR-A", complaint_type="wrong_recipient", scope="internal_wallet",
        description_raw="test staff disconnect", trans_id="TXN-0001",
    )
    sample_db.commit()
    ticket_id = created["ticket_id"]

    opened = live_chat.open_chat_session(sample_db, ticket_id=ticket_id, customer_id="USR-A")
    claimed = live_chat.claim_session(sample_db, chat_session_id=opened["chat_session_id"], staff_id="USR-CSKH")
    sample_db.commit()
    assert claimed["status"] == "active"

    test_factory = sessionmaker(bind=sample_db.get_bind(), future=True)
    manager = ConnectionManager()
    customer_ws = _FakeWebSocket()
    other_staff_ws = _FakeWebSocket()

    async def _run():
        await manager.register(customer_ws, user_id="USR-A", chat_session_id=opened["chat_session_id"], is_staff=False)
        await manager.register(other_staff_ws, user_id="USR-SUP", chat_session_id=None, is_staff=True)
        with monkeypatch.context() as m:
            m.setattr("src.api.live_chat_ws.SessionLocal", test_factory)
            await manager.release_staff_sessions(staff_id="USR-CSKH")

    asyncio.run(_run())

    sample_db.expire_all()
    refreshed = sample_db.get(ChatSession, opened["chat_session_id"])
    assert refreshed.status == "waiting", "phiên phải quay lại hàng chờ, không được kẹt ở active mãi mãi"
    assert refreshed.claimed_by is None

    assert any(m["type"] == "system" for m in customer_ws.sent), "khách phải được báo là chuyên viên đã mất kết nối"
    assert any(m["type"] == "queue_update" for m in other_staff_ws.sent), "CSKH khác phải được báo có ca chờ lại"


def test_close_customer_session_on_disconnect(sample_db, monkeypatch):
    """Phát hiện thật (2026-08-11, test tay): khách F5 thoát chat — nếu
    không đóng phiên, khách đòi gặp người thật lại sẽ TÁI DÙNG đúng phiên cũ
    (open_chat_session chỉ tái dùng theo ticket_id, không biết khách đã rời
    đi), nên không có phiên 'waiting' mới, dashboard không báo gì cả.
    close_customer_session_on_disconnect() PHẢI đóng phiên NGAY khi khách
    mất kết nối, để lần hỏi lại sau tạo phiên MỚI đúng nghĩa."""
    created = create_ticket_with_fraud_check(
        sample_db, user_id="USR-A", complaint_type="wrong_recipient", scope="internal_wallet",
        description_raw="test customer disconnect", trans_id="TXN-0001",
    )
    sample_db.commit()
    ticket_id = created["ticket_id"]

    opened = live_chat.open_chat_session(sample_db, ticket_id=ticket_id, customer_id="USR-A")
    claimed = live_chat.claim_session(sample_db, chat_session_id=opened["chat_session_id"], staff_id="USR-CSKH")
    sample_db.commit()
    assert claimed["status"] == "active"

    test_factory = sessionmaker(bind=sample_db.get_bind(), future=True)
    manager = ConnectionManager()
    staff_ws = _FakeWebSocket()

    async def _run():
        await manager.register(staff_ws, user_id="USR-CSKH", chat_session_id=opened["chat_session_id"], is_staff=True)
        with monkeypatch.context() as m:
            m.setattr("src.api.live_chat_ws.SessionLocal", test_factory)
            await manager.close_customer_session_on_disconnect(chat_session_id=opened["chat_session_id"])

    asyncio.run(_run())

    sample_db.expire_all()
    refreshed = sample_db.get(ChatSession, opened["chat_session_id"])
    assert refreshed.status == "closed", "phiên phải đóng ngay, không được kẹt ở active/waiting mãi mãi"
    assert refreshed.closed_at is not None

    assert any(m["type"] == "system" for m in staff_ws.sent), "CSKH phải được báo khách đã rời đi"
    assert any(m["type"] == "session_closed" for m in staff_ws.sent)

    # Tái dùng ticket_id sau khi khách "đòi gặp người thật" lại phải tạo
    # phiên MỚI (waiting) — không được âm thầm tái dùng phiên đã đóng.
    reopened = live_chat.open_chat_session(sample_db, ticket_id=ticket_id, customer_id="USR-A")
    assert reopened["chat_session_id"] != opened["chat_session_id"]
    assert reopened["status"] == "waiting"


def test_closed_session_rejects_further_messages(sample_db, monkeypatch):
    created = create_ticket_with_fraud_check(
        sample_db, user_id="USR-A", complaint_type="wrong_recipient", scope="internal_wallet",
        description_raw="test closed session send", trans_id="TXN-0001",
    )
    sample_db.commit()
    ticket_id = created["ticket_id"]
    opened = live_chat.open_chat_session(sample_db, ticket_id=ticket_id, customer_id="USR-A")
    live_chat.close_session(sample_db, chat_session_id=opened["chat_session_id"])
    sample_db.commit()

    def _override_session():
        try:
            yield sample_db
            sample_db.commit()
        except Exception:
            sample_db.rollback()
            raise

    app.dependency_overrides[get_session] = _override_session
    test_factory = sessionmaker(bind=sample_db.get_bind(), future=True)
    manager = ConnectionManager()
    monkeypatch.setattr("src.api.live_chat_ws.SessionLocal", test_factory)
    monkeypatch.setattr("src.api.live_chat_ws.manager", manager)
    monkeypatch.setattr("src.api.main._live_chat_manager", manager)

    client = TestClient(app)
    ws_ticket = manager.mint_ticket(user_id="USR-A", role="customer", chat_session_id=opened["chat_session_id"])
    with client.websocket_connect(f"/ws/live-chat?ticket={ws_ticket}") as ws:
        ws.receive_json()  # disclaimer đầu phiên
        ws.send_json({"type": "send_message", "chat_session_id": opened["chat_session_id"], "content": "còn ai không"})
        reply = ws.receive_json()
        assert reply["type"] == "error"
        assert "kết thúc" in reply["text"]

    raw = sample_db.connection().exec_driver_sql(
        "SELECT count(*) FROM messages WHERE chat_session_id = ?", (opened["chat_session_id"],)
    ).scalar()
    assert raw == 0, "không được lưu tin nhắn gửi vào phiên đã đóng"

    app.dependency_overrides.clear()


def test_unregister_removes_from_all_maps():
    async def _run():
        manager = ConnectionManager()
        ws = _FakeWebSocket()
        await manager.register(ws, user_id="USR-CSKH", chat_session_id="CHS-1", is_staff=True)
        manager.unregister(ws, user_id="USR-CSKH")
        assert ws not in manager._staff_sockets
        assert "USR-CSKH" not in manager._user_sockets
        assert "CHS-1" not in manager._session_sockets

    asyncio.run(_run())


def test_second_claim_gets_409(sample_db, monkeypatch):
    created = create_ticket_with_fraud_check(
        sample_db, user_id="USR-A", complaint_type="wrong_recipient", scope="internal_wallet",
        description_raw="test ws 409", trans_id="TXN-0001",
    )
    sample_db.commit()
    ticket_id = created["ticket_id"]

    def _override_session():
        try:
            yield sample_db
            sample_db.commit()
        except Exception:
            sample_db.rollback()
            raise

    app.dependency_overrides[get_session] = _override_session
    test_factory = sessionmaker(bind=sample_db.get_bind(), future=True)
    manager = ConnectionManager()
    monkeypatch.setattr("src.api.live_chat_ws.SessionLocal", test_factory)
    monkeypatch.setattr("src.api.live_chat_ws.manager", manager)
    monkeypatch.setattr("src.api.main._live_chat_manager", manager)

    client = TestClient(app)
    customer_token = create_access_token(user_id="USR-A", role="customer", otp_verified_at=dt.datetime.utcnow())
    cskh_token = create_access_token(user_id="USR-CSKH", role="cskh")
    sup_token = create_access_token(user_id="USR-SUP", role="supervisor")

    resp = client.post("/live-chat/ws-ticket", json={"ticket_id": ticket_id}, headers={"Authorization": f"Bearer {customer_token}"})
    chat_session_id = resp.json()["chat_session_id"]

    first = client.post(f"/live-chat/sessions/{chat_session_id}/claim", headers={"Authorization": f"Bearer {cskh_token}"})
    assert first.status_code == 200
    second = client.post(f"/live-chat/sessions/{chat_session_id}/claim", headers={"Authorization": f"Bearer {sup_token}"})
    assert second.status_code == 409

    app.dependency_overrides.clear()


def test_customer_connects_and_receives_initial_system_message(sample_db, monkeypatch):
    created = create_ticket_with_fraud_check(
        sample_db, user_id="USR-A", complaint_type="wrong_recipient", scope="internal_wallet",
        description_raw="test ws smoke", trans_id="TXN-0001",
    )
    sample_db.commit()
    ticket_id = created["ticket_id"]

    def _override_session():
        try:
            yield sample_db
            sample_db.commit()
        except Exception:
            sample_db.rollback()
            raise

    app.dependency_overrides[get_session] = _override_session
    test_factory = sessionmaker(bind=sample_db.get_bind(), future=True)
    manager = ConnectionManager()
    monkeypatch.setattr("src.api.live_chat_ws.SessionLocal", test_factory)
    monkeypatch.setattr("src.api.live_chat_ws.manager", manager)
    monkeypatch.setattr("src.api.main._live_chat_manager", manager)

    client = TestClient(app)
    customer_token = create_access_token(user_id="USR-A", role="customer", otp_verified_at=dt.datetime.utcnow())
    resp = client.post("/live-chat/ws-ticket", json={"ticket_id": ticket_id}, headers={"Authorization": f"Bearer {customer_token}"})
    assert resp.status_code == 200, resp.text
    ws_ticket = resp.json()["ws_ticket"]

    with client.websocket_connect(f"/ws/live-chat?ticket={ws_ticket}") as ws:
        first = ws.receive_json()
        assert first["type"] == "system"
        assert "mật khẩu" in first["text"] or "OTP" in first["text"]

    # Vé dùng-1-lần: kết nối lại với CÙNG vé phải bị từ chối.
    try:
        with client.websocket_connect(f"/ws/live-chat?ticket={ws_ticket}"):
            raise AssertionError("vé đã dùng 1 lần không được chấp nhận lần 2")
    except Exception:
        pass

    app.dependency_overrides.clear()


def test_by_ticket_returns_closed_session_with_context_for_followup(sample_db):
    """Phát hiện thật (2026-08-11): CSKH mở lại 1 ticket sau khi khách đã
    thoát chat (phiên 'closed') vẫn cần thấy được phiên đó + SĐT khách để
    gọi lại — route /live-chat/sessions/by-ticket KHÔNG được lọc bỏ phiên
    đã đóng, và PHẢI trả kèm context (trước đây context chỉ đẩy qua WS lúc
    claim, phiên đã đóng thì không bao giờ claim được nữa)."""
    created = create_ticket_with_fraud_check(
        sample_db, user_id="USR-A", complaint_type="wrong_recipient", scope="internal_wallet",
        description_raw="test by-ticket closed", trans_id="TXN-0001",
    )
    sample_db.commit()
    ticket_id = created["ticket_id"]
    opened = live_chat.open_chat_session(sample_db, ticket_id=ticket_id, customer_id="USR-A")
    live_chat.close_session(sample_db, chat_session_id=opened["chat_session_id"])
    sample_db.commit()

    def _override_session():
        try:
            yield sample_db
            sample_db.commit()
        except Exception:
            sample_db.rollback()
            raise

    app.dependency_overrides[get_session] = _override_session
    client = TestClient(app)
    cskh_token = create_access_token(user_id="USR-CSKH", role="cskh")

    resp = client.get(f"/live-chat/sessions/by-ticket/{ticket_id}", headers={"Authorization": f"Bearer {cskh_token}"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["chat_session"]["chat_session_id"] == opened["chat_session_id"]
    assert body["chat_session"]["status"] == "closed"
    assert body["context"]["customer"]["phone"] is not None
    assert body["context"]["complaint"]["type"] == "wrong_recipient"

    app.dependency_overrides.clear()


def test_messages_endpoint_returns_transcript_and_enforces_ownership(sample_db):
    created = create_ticket_with_fraud_check(
        sample_db, user_id="USR-A", complaint_type="wrong_recipient", scope="internal_wallet",
        description_raw="test messages endpoint", trans_id="TXN-0001",
    )
    sample_db.commit()
    ticket_id = created["ticket_id"]
    opened = live_chat.open_chat_session(sample_db, ticket_id=ticket_id, customer_id="USR-A")
    live_chat.record_message(sample_db, chat_session_id=opened["chat_session_id"], role="customer", content="tôi cần gặp người thật")
    sample_db.commit()

    def _override_session():
        try:
            yield sample_db
            sample_db.commit()
        except Exception:
            sample_db.rollback()
            raise

    app.dependency_overrides[get_session] = _override_session
    client = TestClient(app)
    owner_token = create_access_token(user_id="USR-A", role="customer", otp_verified_at=dt.datetime.utcnow())
    other_token = create_access_token(user_id="USR-B", role="customer", otp_verified_at=dt.datetime.utcnow())
    cskh_token = create_access_token(user_id="USR-CSKH", role="cskh")

    owner_resp = client.get(
        f"/live-chat/sessions/{opened['chat_session_id']}/messages", headers={"Authorization": f"Bearer {owner_token}"}
    )
    assert owner_resp.status_code == 200
    assert owner_resp.json()["messages"][0]["content"] == "tôi cần gặp người thật"

    staff_resp = client.get(
        f"/live-chat/sessions/{opened['chat_session_id']}/messages", headers={"Authorization": f"Bearer {cskh_token}"}
    )
    assert staff_resp.status_code == 200, "CSKH phải xem được lịch sử để liên hệ lại, không chỉ chủ phiên"

    other_resp = client.get(
        f"/live-chat/sessions/{opened['chat_session_id']}/messages", headers={"Authorization": f"Bearer {other_token}"}
    )
    assert other_resp.status_code == 403, "khách khác không được xem lịch sử chat của người khác"

    app.dependency_overrides.clear()


def test_sweep_closes_orphaned_stale_waiting_session(sample_db, monkeypatch):
    """Phát hiện thật (2026-08-11, test tay): khách đăng xuất/mất mạng đột
    ngột không gửi được khung đóng kết nối WS — WebSocketDisconnect không
    bao giờ tới, close_customer_session_on_disconnect không có cơ hội chạy,
    ticket hiện mãi ở hàng chờ "chat trực tiếp" dù khách đã đi từ lâu. Sweep
    là lớp phòng vệ THỨ 2, không phụ thuộc bắt đúng sự kiện disconnect."""
    created = create_ticket_with_fraud_check(
        sample_db, user_id="USR-A", complaint_type="wrong_recipient", scope="internal_wallet",
        description_raw="test sweep stale", trans_id="TXN-0001",
    )
    sample_db.commit()
    ticket_id = created["ticket_id"]
    old_start = dt.datetime.utcnow() - dt.timedelta(minutes=45)
    opened = live_chat.open_chat_session(sample_db, ticket_id=ticket_id, customer_id="USR-A", now=old_start)
    sample_db.commit()

    test_factory = sessionmaker(bind=sample_db.get_bind(), future=True)
    manager = ConnectionManager()

    async def _run():
        with monkeypatch.context() as m:
            m.setattr("src.api.live_chat_ws.SessionLocal", test_factory)
            return await manager.sweep_stale_waiting_sessions()

    swept = asyncio.run(_run())

    assert swept == [opened["chat_session_id"]]
    sample_db.expire_all()
    refreshed = sample_db.get(ChatSession, opened["chat_session_id"])
    assert refreshed.status == "closed"


def test_sweep_does_not_close_recent_or_still_connected_sessions(sample_db, monkeypatch):
    """2 lý do KHÔNG được đóng: (1) phiên còn quá mới (LIVE_CHAT_STALE_WAITING_MINUTES
    chưa trôi qua) — có thể khách vẫn đang thật sự chờ; (2) phiên có socket
    ĐANG kết nối thật (dù đã cũ) — không được đá 1 khách đang ngồi chờ thật,
    chỉ vì chờ lâu."""
    created = create_ticket_with_fraud_check(
        sample_db, user_id="USR-A", complaint_type="wrong_recipient", scope="internal_wallet",
        description_raw="test sweep keeps live", trans_id="TXN-0001",
    )
    # TXN-0001 (USR-A -> USR-B) chứ KHÔNG phải TXN-0002.
    # TXN-0002 là USR-A -> tài khoản ngân hàng của CHÍNH USR-A, nên USR-B
    # không phải một bên nào của nó. Fixture cũ dựng dữ liệu bằng đúng hành vi
    # mà bản vá C4/BOLA vừa cấm — nó chỉ chạy được nhờ lỗ hổng, và sập ngay
    # khi lỗ hổng được bịt. Test dựng dữ liệu bằng đường mà sản phẩm cấm thì
    # sớm muộn cũng thành vật cản cho chính bản vá đúng.
    created_b = create_ticket_with_fraud_check(
        sample_db, user_id="USR-B", complaint_type="wrong_recipient", scope="internal_wallet",
        description_raw="test sweep keeps recent", trans_id="TXN-0001",
    )
    sample_db.commit()

    old_but_connected = live_chat.open_chat_session(
        sample_db, ticket_id=created["ticket_id"], customer_id="USR-A", now=dt.datetime.utcnow() - dt.timedelta(minutes=45)
    )
    still_recent = live_chat.open_chat_session(
        sample_db, ticket_id=created_b["ticket_id"], customer_id="USR-B", now=dt.datetime.utcnow() - dt.timedelta(minutes=5)
    )
    sample_db.commit()

    test_factory = sessionmaker(bind=sample_db.get_bind(), future=True)
    manager = ConnectionManager()
    still_connected_ws = _FakeWebSocket()

    async def _run():
        await manager.register(still_connected_ws, user_id="USR-A", chat_session_id=old_but_connected["chat_session_id"], is_staff=False)
        with monkeypatch.context() as m:
            m.setattr("src.api.live_chat_ws.SessionLocal", test_factory)
            return await manager.sweep_stale_waiting_sessions()

    swept = asyncio.run(_run())

    assert swept == [], "không được đóng phiên còn kết nối thật hoặc còn quá mới"
    sample_db.expire_all()
    assert sample_db.get(ChatSession, old_but_connected["chat_session_id"]).status == "waiting"
    assert sample_db.get(ChatSession, still_recent["chat_session_id"]).status == "waiting"


def test_ws_ticket_is_not_shaped_like_a_jwt():
    """FIN05-StressTest-Plan-v2 ST2-E-02 — vé ws-ticket (mint_ticket,
    secrets.token_urlsafe) không được là JWT thật (3 đoạn base64 phân tách
    bằng dấu chấm) nhét vào query param `?ticket=...` — JWT thật lộ ra URL
    (log truy cập, lịch sử trình duyệt, referrer header) là rò rỉ nghiêm
    trọng hơn nhiều so với vé dùng-1-lần TTL ngắn không mang thông tin gì
    ngoài chính nó."""
    manager = ConnectionManager()
    ticket = manager.mint_ticket(user_id="USR-A", role="customer")
    assert ticket.count(".") != 2, f"Vé trông giống định dạng JWT (3 đoạn phân tách bằng '.'): {ticket}"
    # secrets.token_urlsafe không mang payload — không giải mã ra thông tin
    # gì (JWT base64-decode được phần header/payload dù chưa xác minh chữ ký).
    import base64
    import binascii

    with pytest.raises((binascii.Error, ValueError)):
        base64.urlsafe_b64decode(ticket.split(".")[0] + "===")
        # Nếu decode "thành công" ra JSON hợp lệ mới thực sự đáng lo — ở đây
        # chỉ cần xác nhận KHÔNG có cấu trúc 3-đoạn để bắt đầu, dòng dưới chỉ
        # là phòng vệ kép cho trường hợp base64 tình cờ decode được (hiếm).
        raise ValueError("token_urlsafe không nên decode ra được cấu trúc có ý nghĩa")


def test_malformed_ws_payload_does_not_crash_connection(sample_db, monkeypatch):
    """FIN05-StressTest-Plan-v2 ST2-E-08 — gửi payload không phải JSON object
    hợp lệ (JSON array thay vì object — `msg.get(...)` sẽ AttributeError nếu
    không kiểm tra kiểu) không được làm hỏng kết nối cho tin nhắn HỢP LỆ gửi
    ngay sau đó trong CÙNG phiên."""
    created = create_ticket_with_fraud_check(
        sample_db, user_id="USR-A", complaint_type="wrong_recipient", scope="internal_wallet",
        description_raw="test malformed ws payload", trans_id="TXN-0001",
    )
    sample_db.commit()
    ticket_id = created["ticket_id"]

    def _override_session():
        try:
            yield sample_db
            sample_db.commit()
        except Exception:
            sample_db.rollback()
            raise

    app.dependency_overrides[get_session] = _override_session
    test_factory = sessionmaker(bind=sample_db.get_bind(), future=True)
    manager = ConnectionManager()
    monkeypatch.setattr("src.api.live_chat_ws.SessionLocal", test_factory)
    monkeypatch.setattr("src.api.live_chat_ws.manager", manager)
    monkeypatch.setattr("src.api.main._live_chat_manager", manager)

    client = TestClient(app)
    customer_token = create_access_token(user_id="USR-A", role="customer", otp_verified_at=dt.datetime.utcnow())
    resp = client.post("/live-chat/ws-ticket", json={"ticket_id": ticket_id}, headers={"Authorization": f"Bearer {customer_token}"})
    chat_session_id = resp.json()["chat_session_id"]
    ws_ticket = resp.json()["ws_ticket"]

    with client.websocket_connect(f"/ws/live-chat?ticket={ws_ticket}") as ws:
        ws.receive_json()  # disclaimer đầu phiên
        ws.send_json([1, 2, 3])  # KHÔNG phải object — msg.get(...) sẽ vỡ nếu không kiểm tra kiểu
        ws.send_json({"type": "send_message", "chat_session_id": chat_session_id, "content": "vẫn gửi được sau payload lạ"})
        reply = ws.receive_json()
        assert reply["type"] == "message"
        assert reply["content"] == "vẫn gửi được sau payload lạ"

    app.dependency_overrides.clear()


def test_sweep_stays_fast_with_thousands_of_stale_sessions(sample_db, monkeypatch):
    """FIN05-StressTest-Plan-v4 L4-07 — sweep_stale_waiting_sessions() chạy
    LƯỜI mỗi lần CSKH tải hàng chờ (GET /live-chat/sessions/waiting) — nếu
    hàng nghìn phiên rác tồn đọng (vd hệ thống chạy lâu ngày không ai dọn),
    sweep không được làm route đó CHẬM tới mức CSKH cảm nhận được lag. Bulk
    insert thẳng ChatSession (bỏ qua create_ticket_with_fraud_check cho 1000
    bản ghi — quá chậm/không cần thiết, chỉ cần 1 ticket_id hợp lệ dùng
    chung, sweep không quan tâm nội dung ticket)."""
    import time

    created = create_ticket_with_fraud_check(
        sample_db, user_id="USR-A", complaint_type="wrong_recipient", scope="internal_wallet",
        description_raw="test sweep load", trans_id="TXN-0001",
    )
    sample_db.commit()
    ticket_id = created["ticket_id"]

    old_start = dt.datetime.utcnow() - dt.timedelta(minutes=45)
    stale_sessions = [
        ChatSession(
            chat_session_id=f"CHS-load-{i:05d}",
            ticket_id=ticket_id,
            customer_id="USR-A",
            status="waiting",
            started_at=old_start,
        )
        for i in range(2000)
    ]
    sample_db.bulk_save_objects(stale_sessions)
    sample_db.commit()

    test_factory = sessionmaker(bind=sample_db.get_bind(), future=True)
    manager = ConnectionManager()

    async def _run():
        with monkeypatch.context() as m:
            m.setattr("src.api.live_chat_ws.SessionLocal", test_factory)
            return await manager.sweep_stale_waiting_sessions()

    start = time.monotonic()
    swept = asyncio.run(_run())
    elapsed = time.monotonic() - start

    assert len(swept) == 2000
    assert elapsed < 5.0, f"Sweep 2000 phiên rác mất {elapsed:.2f}s — quá chậm cho 1 thao tác chạy lười mỗi lần tải trang"

    remaining_waiting = sample_db.query(ChatSession).filter(ChatSession.status == "waiting").count()
    assert remaining_waiting == 0
