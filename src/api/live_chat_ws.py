"""Live chat WebSocket (2026-08-11) — connection-manager + handler in-process.

Không dùng Redis: `Dockerfile` đã có quyết định + lý do sẵn (uvicorn chạy
ĐÚNG 1 worker vì MemorySaver — src/agents/graph.py — giữ state hội thoại AI
trong RAM 1 process, nhiều worker sẽ làm khách mất trí nhớ agent). Cùng lý do
đó áp dụng y hệt cho state live-chat (ai đang kết nối, ai đang nhận ca) — 1
dict Python in-memory là đủ và AN TOÀN cho quy mô hiện tại (~4 CSKH + 2
supervisor / ~50 phiên đồng thời). Nếu sau này scale >1 worker mới cần Redis
pub/sub — đơn giản hoá có chủ đích, không phải thiếu sót.

Giao thức WS tối giản — 1 loại message nhận vào duy nhất (`send_message`):
khách luôn tự động "vào" đúng chat_session_id gắn trong vé lúc kết nối; CSKH
được tự động đăng ký làm participant của 1 phiên NGAY khi claim thành công
qua REST (xem notify_claimed) — không cần thêm round-trip "join_session".
"""
from __future__ import annotations

import datetime as dt
import logging
import secrets
import time
from collections import defaultdict
from typing import Any, Optional

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy import select

from src.config import LIVE_CHAT_STALE_WAITING_MINUTES
from src.db.models import ChatSession
from src.db.session import SessionLocal
from src.services import live_chat
from src.tools.base import ToolError

_WS_TICKET_TTL_SECONDS = 30
_logger = logging.getLogger("fin05.live_chat_ws")


class InMemoryRateLimiter:
    """Sliding-window đơn giản, khoá theo key tuỳ ý — dùng cho cả mint-vé
    (ws-ticket) lẫn giới hạn gửi tin nhắn/giờ. slowapi (HTTP-only decorator)
    không áp dụng được bên trong WS handler, và route ws-ticket cần khoá
    theo user_id chứ không phải IP — mọi khách hiện gọi qua chung 1 container
    frontend (kiến trúc BFF, xem main.py `Limiter(key_func=get_remote_address)`),
    khoá theo IP ở đó thực chất là giới hạn CHUNG cho mọi khách, không phải
    riêng từng người — không lặp lại đặc điểm đó ở route mới này."""

    def __init__(self, *, max_calls: int, window_seconds: float):
        self._max_calls = max_calls
        self._window_seconds = window_seconds
        self._calls: dict[str, list[float]] = defaultdict(list)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        window_start = now - self._window_seconds
        calls = [t for t in self._calls[key] if t >= window_start]
        if len(calls) >= self._max_calls:
            self._calls[key] = calls
            return False
        calls.append(now)
        self._calls[key] = calls
        return True


class ConnectionManager:
    """Singleton module-level (cùng pattern _CHECKPOINTER ở graph.py)."""

    def __init__(self):
        self._tickets: dict[str, dict[str, Any]] = {}
        self._session_sockets: dict[str, set[WebSocket]] = defaultdict(set)
        self._user_sockets: dict[str, set[WebSocket]] = defaultdict(set)
        self._staff_sockets: set[WebSocket] = set()
        self.ws_ticket_limiter = InMemoryRateLimiter(max_calls=5, window_seconds=60)
        self.message_limiter = InMemoryRateLimiter(max_calls=60, window_seconds=3600)

    def mint_ticket(self, *, user_id: str, role: str, chat_session_id: Optional[str] = None) -> str:
        ticket = secrets.token_urlsafe(24)
        self._tickets[ticket] = {
            "user_id": user_id,
            "role": role,
            "chat_session_id": chat_session_id,
            "expires_at": time.monotonic() + _WS_TICKET_TTL_SECONDS,
        }
        return ticket

    def consume_ticket(self, ticket: str) -> Optional[dict[str, Any]]:
        """Dùng 1 lần — xoá NGAY dù thành công hay hết hạn (chống replay)."""
        data = self._tickets.pop(ticket, None)
        if data is None or time.monotonic() > data["expires_at"]:
            return None
        return data

    async def register(self, ws: WebSocket, *, user_id: str, chat_session_id: Optional[str], is_staff: bool) -> None:
        # Phát hiện thật (2026-08-11): 1 user có thể tạo ra kết nối WS "mồ côi"
        # (vd tab cũ không dọn sạch, mất mạng chập chờn không kích hoạt đúng
        # sự kiện disconnect) — nếu không dọn, kết nối cũ vẫn nằm trong
        # _user_sockets/_session_sockets, khiến broadcast gửi tới CẢ 2 nơi
        # (1 nơi client không còn lắng nghe đúng cách), trông như tin nhắn bị
        # lặp/tách. Tối đa 1 kết nối ACTIVE/user tại 1 thời điểm — chủ động
        # đóng kết nối cũ trước khi đăng ký kết nối mới, loại trừ cả lớp bug
        # này bất kể nguyên nhân gốc gây ra kết nối cũ là gì.
        stale = list(self._user_sockets.get(user_id, ()))
        for old_ws in stale:
            self.unregister(old_ws, user_id=user_id)
            try:
                await old_ws.close()
            except Exception:
                pass
        if stale:
            _logger.warning("live_chat_ws_stale_connection_closed", extra={"user_id": user_id, "count": len(stale)})

        self._user_sockets[user_id].add(ws)
        if chat_session_id:
            self._session_sockets[chat_session_id].add(ws)
        if is_staff:
            self._staff_sockets.add(ws)

    def unregister(self, ws: WebSocket, *, user_id: str) -> None:
        self._user_sockets[user_id].discard(ws)
        if not self._user_sockets[user_id]:
            del self._user_sockets[user_id]
        self._staff_sockets.discard(ws)
        for chat_session_id in list(self._session_sockets):
            self._session_sockets[chat_session_id].discard(ws)
            if not self._session_sockets[chat_session_id]:
                del self._session_sockets[chat_session_id]

    async def send_to_session(self, chat_session_id: str, payload: dict[str, Any]) -> None:
        for ws in list(self._session_sockets.get(chat_session_id, ())):
            try:
                await ws.send_json(payload)
            except Exception:
                _logger.warning(
                    "live_chat_ws_send_failed", extra={"chat_session_id": chat_session_id, "payload_type": payload.get("type")}
                )

    async def send_to_user(self, user_id: str, payload: dict[str, Any]) -> None:
        for ws in list(self._user_sockets.get(user_id, ())):
            try:
                await ws.send_json(payload)
            except Exception:
                _logger.warning("live_chat_ws_send_failed", extra={"user_id": user_id, "payload_type": payload.get("type")})

    async def broadcast_to_staff(self, payload: dict[str, Any]) -> None:
        for ws in list(self._staff_sockets):
            try:
                await ws.send_json(payload)
            except Exception:
                _logger.warning("live_chat_ws_send_failed", extra={"broadcast": "staff", "payload_type": payload.get("type")})

    def count_waiting_sessions(self) -> int:
        with SessionLocal() as session:
            return session.query(ChatSession).filter(ChatSession.status == "waiting").count()

    def count_online_staff(self) -> int:
        return len({id(ws) for ws in self._staff_sockets}) or 1  # tránh chia 0

    async def release_staff_sessions(self, *, staff_id: str) -> None:
        """Phát hiện thật (2026-08-11, test tay): CSKH F5/đóng tab KHÔNG bấm
        "Kết thúc chat" — nếu không tự dọn, phiên vẫn 'active'+claimed_by
        CSKH đó MÃI MÃI (mồ côi). Hậu quả kép: (1) khách "đòi gặp nhân viên"
        lại tái dùng ĐÚNG phiên cũ (open_chat_session chỉ tái dùng theo
        ticket_id, không biết CSKH đã rớt kết nối) nên KHÔNG có phiên
        'waiting' mới nào sinh ra, dashboard không có gì để báo; (2) CSKH mở
        lại ticket đó bị kéo thẳng vào chat cũ vì claimed_by vẫn là họ. Gọi
        hàm này ở finally-block lúc WS ngắt kết nối CSKH — tự động trả mọi
        phiên đang active của CSKH đó về hàng chờ, cùng ngữ nghĩa với
        transfer_session() (nút "chuyển ca" thủ công), chỉ khác trigger."""
        with SessionLocal() as db_session:
            stale = db_session.scalars(
                select(ChatSession).where(ChatSession.claimed_by == staff_id, ChatSession.status == "active")
            ).all()
            released_ids = [cs.chat_session_id for cs in stale]
            for cs in stale:
                live_chat.transfer_session(db_session, chat_session_id=cs.chat_session_id)
            db_session.commit()

        for chat_session_id in released_ids:
            await self.send_to_session(
                chat_session_id,
                {"type": "system", "text": "Chuyên viên đã mất kết nối, phiên của bạn được chuyển lại hàng chờ cho chuyên viên khác."},
            )
        if released_ids:
            await self.broadcast_to_staff({"type": "queue_update", "waiting": self.count_waiting_sessions()})

    async def sweep_stale_waiting_sessions(self) -> list[str]:
        """Lớp phòng vệ THỨ 2 (2026-08-11, phát hiện thật: ticket vẫn hiện
        "chờ chat" dù khách đã đăng xuất từ lâu) — dọn dựa trên disconnect
        SẠCH (release_staff_sessions/close_customer_session_on_disconnect)
        không bắt được trường hợp mạng rớt đột ngột/trình duyệt bị kill:
        không gửi được khung đóng kết nối, WebSocketDisconnect không bao giờ
        tới, phiên 'waiting' treo mãi. Gọi lười (lazy) mỗi khi CSKH tải hàng
        chờ — không cần thêm scheduler/cron nào, khớp tinh thần đơn giản đã
        chọn cho toàn bộ tính năng này (xem lý do không dùng Redis ở đầu
        file). CHỈ đóng phiên KHÔNG có socket nào đang thực sự kết nối tới —
        tránh đóng nhầm 1 khách vẫn đang ngồi chờ thật, chỉ là chờ lâu."""
        cutoff = dt.datetime.utcnow() - dt.timedelta(minutes=LIVE_CHAT_STALE_WAITING_MINUTES)
        with SessionLocal() as db_session:
            candidates = db_session.scalars(
                select(ChatSession).where(ChatSession.status == "waiting", ChatSession.started_at < cutoff)
            ).all()
            to_close = [cs.chat_session_id for cs in candidates if not self._session_sockets.get(cs.chat_session_id)]
            for chat_session_id in to_close:
                live_chat.close_session(db_session, chat_session_id=chat_session_id)
            db_session.commit()
        if to_close:
            _logger.warning("live_chat_ws_swept_stale_waiting_sessions", extra={"chat_session_ids": to_close})
        return to_close

    async def close_customer_session_on_disconnect(self, *, chat_session_id: str) -> None:
        """Phát hiện thật (2026-08-11, test tay): khách F5/đóng tab khi đang
        chat — nếu không dọn, ChatSession vẫn 'waiting'/'active' mãi mãi,
        như thể khách còn đó. Đóng NGAY khi khách mất kết nối — lịch sử
        (Message + Ticket.human_handoff_requested vẫn giữ nguyên, không xoá)
        là đủ để CSKH thấy khách đã muốn gặp người thật và liên hệ lại qua
        điện thoại, không cần khách quay lại đúng phiên chat cũ (khách hỏi
        lại người thật lần sau sẽ tạo phiên MỚI, đúng ngữ nghĩa 'đã thoát')."""
        with SessionLocal() as db_session:
            chat_session = db_session.get(ChatSession, chat_session_id)
            if chat_session is None or chat_session.status == "closed":
                return
            live_chat.close_session(db_session, chat_session_id=chat_session_id)
            db_session.commit()

        await self.send_to_session(
            chat_session_id,
            {"type": "system", "text": "Khách đã rời cuộc trò chuyện. Bạn có thể liên hệ lại qua số điện thoại của khách."},
        )
        await self.send_to_session(chat_session_id, {"type": "session_closed", "chat_session_id": chat_session_id})
        await self.broadcast_to_staff({"type": "queue_update", "waiting": self.count_waiting_sessions()})

    async def notify_claimed(self, *, chat_session_id: str, staff_user_id: str, context: dict[str, Any]) -> None:
        """Gọi từ route REST POST /live-chat/sessions/{id}/claim (main.py) sau
        khi claim_session() thành công — đăng ký NGAY socket hiện có của CSKH
        đó làm participant của phiên (không cần round-trip "join_session"
        riêng), đẩy ngữ cảnh AI đã điều tra, và gỡ khỏi hàng chờ hiển thị cho
        các CSKH khác."""
        for ws in list(self._user_sockets.get(staff_user_id, ())):
            self._session_sockets[chat_session_id].add(ws)
        await self.send_to_user(staff_user_id, {"type": "claim_success", "chat_session_id": chat_session_id, "context": context})
        await self.broadcast_to_staff({"type": "session_claimed", "chat_session_id": chat_session_id})
        await self.send_to_session(chat_session_id, {"type": "system", "text": "Chuyên viên CSKH đã tham gia hội thoại."})


manager = ConnectionManager()


async def live_chat_websocket_endpoint(websocket: WebSocket) -> None:
    ticket = websocket.query_params.get("ticket")
    data = manager.consume_ticket(ticket) if ticket else None
    if data is None:
        await websocket.close(code=4401)  # 4401: vé không hợp lệ/hết hạn (custom app code, ngoài dải chuẩn)
        return

    user_id = data["user_id"]
    role = data["role"]
    chat_session_id = data["chat_session_id"]
    is_staff = role in ("cskh", "supervisor")

    await websocket.accept()
    await manager.register(websocket, user_id=user_id, chat_session_id=chat_session_id, is_staff=is_staff)

    if not is_staff and chat_session_id:
        waiting = manager.count_waiting_sessions()
        online_staff = manager.count_online_staff()
        eta_hint = f"Hiện có {waiting} khách đang chờ, {online_staff} chuyên viên trực tuyến." if waiting else "Chuyên viên sẽ tham gia ngay khi rảnh."
        await websocket.send_json(
            {
                "type": "system",
                "text": (
                    "Bạn đang được kết nối với chuyên viên CSKH. "
                    "Lưu ý: chúng tôi KHÔNG BAO GIỜ hỏi mật khẩu hoặc mã OTP giao dịch qua chat. "
                    + eta_hint
                ),
            }
        )
        await manager.broadcast_to_staff({"type": "queue_update", "waiting": manager.count_waiting_sessions()})

    try:
        while True:
            try:
                msg = await websocket.receive_json()
            except ValueError:
                # Payload không phải JSON hợp lệ (khung text lỗi) — bỏ qua
                # khung này, KHÔNG ngắt kết nối, khách/CSKH có thể gửi lại.
                continue
            if not isinstance(msg, dict):
                # Phát hiện thật (FIN05-StressTest-Plan-v2 ST2-E-08): JSON
                # hợp lệ nhưng KHÔNG phải object (vd mảng `[1,2,3]`) làm
                # `msg.get(...)` bên dưới raise AttributeError, crash task
                # của đúng kết nối này (không phải cả server, nhưng vẫn là
                # lỗi không kiểm soát, không nên xảy ra).
                continue
            if msg.get("type") != "send_message":
                continue
            target_session_id = msg.get("chat_session_id") or chat_session_id
            content = (msg.get("content") or "").strip()
            if not target_session_id or not content:
                continue
            if not manager.message_limiter.allow(user_id):
                await websocket.send_json({"type": "error", "text": "Bạn gửi tin nhắn quá nhanh, vui lòng chờ một chút."})
                continue

            with SessionLocal() as db_session:
                try:
                    chat_session = db_session.get(ChatSession, target_session_id)
                    if chat_session is None:
                        continue
                    is_participant = (not is_staff and chat_session.customer_id == user_id) or (
                        is_staff and chat_session.claimed_by == user_id
                    )
                    if not is_participant:
                        await websocket.send_json({"type": "error", "text": "Bạn không có quyền gửi tin nhắn trong phiên này."})
                        continue
                    if chat_session.status == "closed":
                        # Trở nên thực sự xảy ra được sau khi thêm auto-close
                        # lúc ngắt kết nối (release_staff_sessions/
                        # close_customer_session_on_disconnect) — tab còn mở
                        # của phía bên kia (chưa reload) có thể vẫn gửi được
                        # tin nếu không chặn ở đây, dù phiên đã đóng.
                        await websocket.send_json({"type": "error", "text": "Phiên chat này đã kết thúc."})
                        continue
                    saved = live_chat.record_message(
                        db_session,
                        chat_session_id=target_session_id,
                        role="staff" if is_staff else "customer",
                        content=content,
                    )
                    db_session.commit()
                except ToolError:
                    db_session.rollback()
                    continue
            await manager.send_to_session(target_session_id, {"type": "message", **saved})
    except WebSocketDisconnect:
        pass
    finally:
        manager.unregister(websocket, user_id=user_id)
        if is_staff:
            await manager.release_staff_sessions(staff_id=user_id)
        elif chat_session_id:
            await manager.close_customer_session_on_disconnect(chat_session_id=chat_session_id)
