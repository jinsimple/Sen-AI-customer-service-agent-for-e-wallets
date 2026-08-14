"""Live chat WebSocket — connection-manager + handler.

Socket là thứ DUY NHẤT còn nằm trong RAM từng process (bản chất WebSocket —
không chuyển đi đâu được); mọi state khác đã ra store dùng chung khi bật
multi-worker: fan-out tin nhắn qua Redis pub/sub (ADR-015), rate-limit qua
Redis sliding window (đợt Auth Flow 2026-08-12), và vé handshake qua Redis
TTL+GETDEL (QA-01, biên bản QA 13/08 — vé trong dict RAM làm handshake fail
~3/4 số lần với 4 worker vì REST cấp vé ở worker A, WS rơi vào worker B).

Giao thức WS tối giản — 1 loại message nhận vào duy nhất (`send_message`):
khách luôn tự động "vào" đúng chat_session_id gắn trong vé lúc kết nối; CSKH
được tự động đăng ký làm participant của 1 phiên NGAY khi claim thành công
qua REST (xem notify_claimed) — không cần thêm round-trip "join_session".
"""
from __future__ import annotations

import asyncio
import datetime as dt
import json
import logging
import secrets
from collections import defaultdict
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy import select

from src.config import LIVE_CHAT_STALE_WAITING_MINUTES
from src.db.models import ChatSession
from src.db.session import SessionLocal
from src.rate_limit import RedisSlidingWindowLimiter
from src.redis_client import get_default_client
from src.services import live_chat
from src.tools.base import ToolError

_WS_TICKET_TTL_SECONDS = 30
# Vé PHẢI nằm ở store dùng chung (QA-01): mint qua REST và consume qua WS
# handshake không có gì bảo đảm rơi vào cùng worker. Redis rớt thì mint/consume
# ném lỗi và handshake fail RÕ RÀNG — cố ý không fallback về RAM, vì fallback
# đó chính là bug chập chờn cũ quay lại dưới dạng khó bắt hơn (cùng triết lý
# ADR-013: không fallback im lặng).
_WS_TICKET_KEY = "fin05:ws_ticket:"
# QA-13 — tập phiên mà mỗi CSKH đang giữ, để socket nối LẠI tự gắn lại đúng
# phiên. TTL rộng hơn một ca trực; phiên đóng thì SREM ngay (xem close/release).
_STAFF_SESSIONS_KEY = "fin05:live_chat:staff_sessions:"
_STAFF_SESSIONS_TTL_SECONDS = 12 * 3600
# Ánh xạ NGƯỢC: phiên -> CSKH đang giữ. Dùng lúc GIAO TIN để không phụ thuộc
# thứ tự các sự kiện đăng ký giữa các worker (xem _deliver_session_local).
_SESSION_STAFF_KEY = "fin05:live_chat:session_staff:"
_logger = logging.getLogger("fin05.live_chat_ws")


# Kênh pub/sub dùng chung cho fan-out live-chat liên worker (ADR-015).
_PUBSUB_CHANNEL = "fin05:live_chat"
# Định danh DUY NHẤT của process này — dùng để bỏ qua tiếng vọng của chính
# mình khi nhận lại thông điệp vừa publish (nếu không sẽ giao 2 lần cho socket
# local: 1 lần trực tiếp, 1 lần qua pub/sub).
_INSTANCE_ID = secrets.token_hex(8)


async def _vong_lap_subscriber(mgr: ConnectionManager) -> None:
    """Nhận thông điệp từ worker KHÁC rồi giao cho socket local của worker này.

    Chạy nền suốt vòng đời process, khởi động từ FastAPI startup. Lỗi mạng
    KHÔNG được làm chết vòng lặp — Redis rớt tạm thời là chuyện thường trên
    hạ tầng cloud (đúng ghi chú keepalive/health_check đã đúc kết trong
    playbook đóng gói), tự thử lại thay vì im lặng dừng fan-out vĩnh viễn.
    """
    while True:
        try:
            pubsub = get_default_client().pubsub(ignore_subscribe_messages=True)
            pubsub.subscribe(_PUBSUB_CHANNEL)
            _logger.info("live_chat_pubsub_subscribed", extra={"instance": _INSTANCE_ID})
            while True:
                # get_message chặn luồng -> đẩy sang thread pool để không chẹn
                # event loop (route live-chat khác vẫn phải phục vụ được).
                msg = await asyncio.to_thread(pubsub.get_message, timeout=1.0)
                if not msg:
                    await asyncio.sleep(0)  # nhường event loop
                    continue
                try:
                    data = json.loads(msg["data"])
                except (TypeError, ValueError):
                    continue
                if data.get("src") == _INSTANCE_ID:
                    continue  # tiếng vọng của chính mình, đã giao local rồi
                await mgr._giao_tu_pubsub(
                    data.get("kind", ""), data.get("target"), data.get("payload") or {}
                )
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001
            _logger.warning("live_chat_pubsub_loop_error", extra={"loi": repr(e)})
            await asyncio.sleep(2)


class ConnectionManager:
    """Singleton module-level (cùng pattern _CHECKPOINTER ở graph.py)."""

    def __init__(self):
        self._session_sockets: dict[str, set[WebSocket]] = defaultdict(set)
        self._user_sockets: dict[str, set[WebSocket]] = defaultdict(set)
        self._staff_sockets: set[WebSocket] = set()
        # Nhớ tạm "phiên -> CSKH" để khỏi đọc Redis mỗi tin nhắn (QA-13).
        self._session_staff: dict[str, str] = {}
        # Đồng bộ Redis (đợt nâng cấp Auth Flow 2026-08-12, xem
        # src/rate_limit.py) — trước đây in-memory dict riêng của process,
        # mất sạch state mỗi lần restart backend (rate-limit "reset" âm thầm
        # sau mọi lần deploy/restart). Cùng thuật toán sliding window, chỉ
        # đổi nơi lưu — không đổi ngưỡng/ngữ nghĩa.
        self.ws_ticket_limiter = RedisSlidingWindowLimiter(max_calls=5, window_seconds=60, name="ws_ticket")
        # QA-11: đường cấp vé của CSKH/sếp trước đây KHÔNG gắn limiter nào (đo
        # thật: 40/40 lần đều 200, trong khi khách bị chặn đúng sau 5). Hạn mức
        # rộng hơn khách CÓ CHỦ ĐÍCH, không phải sao chép thiếu: nhân viên trực
        # ca nối lại WS mỗi lần mạng chập chờn/đổi tab, khoá họ ở mức 5 lần/phút
        # là chặn đúng người đang phục vụ khách. 20/phút vẫn chặn được lạm dụng
        # (kịch bản bơm vé hàng loạt) mà không đụng nhịp làm việc thật.
        self.staff_ws_ticket_limiter = RedisSlidingWindowLimiter(
            max_calls=20, window_seconds=60, name="ws_ticket_staff"
        )
        self.message_limiter = RedisSlidingWindowLimiter(max_calls=60, window_seconds=3600, name="live_chat_msg")

    def mint_ticket(self, *, user_id: str, role: str, chat_session_id: str | None = None) -> str:
        ticket = secrets.token_urlsafe(24)
        if _WS_TICKET_TTL_SECONDS <= 0:
            # TTL <= 0 nghĩa là "hết hạn ngay" — không lưu gì (Redis từ chối
            # ex<=0), consume sẽ trả None. Giữ ngữ nghĩa cho test canh TTL.
            return ticket
        get_default_client().set(
            _WS_TICKET_KEY + ticket,
            json.dumps({"user_id": user_id, "role": role, "chat_session_id": chat_session_id}),
            ex=_WS_TICKET_TTL_SECONDS,
        )
        return ticket

    def consume_ticket(self, ticket: str) -> dict[str, Any] | None:
        """Dùng 1 lần — GETDEL đọc+xoá trong MỘT lệnh atomic (chống replay):
        2 handshake tranh nhau cùng 1 vé thì đúng 1 bên nhận được, kể cả khi
        chúng rơi vào 2 worker khác nhau."""
        raw = get_default_client().getdel(_WS_TICKET_KEY + ticket)
        return json.loads(raw) if raw else None

    async def register(self, ws: WebSocket, *, user_id: str, chat_session_id: str | None, is_staff: bool) -> None:
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
            # QA-13 lớp 2 — CSKH nối (hoặc NỐI LẠI) sau khi đã nhận ca: vé WS
            # của nhân viên không mang chat_session_id (lúc xin vé họ chưa
            # nhận ca nào), nên nếu chỉ dựa vào notify_claimed thì một lần
            # rớt mạng/đổi tab là socket mới vĩnh viễn không thuộc phiên nào
            # — tin của khách lại biến mất im lặng. Kịch bản rất thật khi
            # demo/trực ca trên wifi.
            for cs_id in self._phien_da_nhan_cua_cskh(user_id):
                self._session_sockets[cs_id].add(ws)

    @staticmethod
    def _phien_da_nhan_cua_cskh(staff_id: str) -> list[str]:
        """Các phiên CSKH này đang giữ, đọc từ REDIS (không phải DB, không phải
        RAM process): cùng lý do đã chọn Redis cho kho vé WS ở QA-01 — trạng
        thái phải nhìn thấy được từ MỌI worker. Lỗi Redis KHÔNG được làm hỏng
        kết nối WS: đây là lưới an toàn cho lần nối lại, đường chính vẫn là
        pub/sub 'claim'. Nuốt lỗi ở đây là có chủ đích nhưng KHÔNG im lặng —
        có log cảnh báo (ADR-013)."""
        try:
            raw = get_default_client().smembers(_STAFF_SESSIONS_KEY + staff_id)
        except Exception as e:  # noqa: BLE001
            _logger.warning("live_chat_staff_sessions_read_failed", extra={"staff_id": staff_id, "loi": repr(e)})
            return []
        return [s.decode() if isinstance(s, bytes) else str(s) for s in (raw or ())]

    def _quen_phien_cua_cskh(self, staff_id: str, chat_session_ids: list[str]) -> None:
        if not chat_session_ids:
            return
        for cs_id in chat_session_ids:
            self._session_staff.pop(cs_id, None)
        try:
            client = get_default_client()
            client.srem(_STAFF_SESSIONS_KEY + staff_id, *chat_session_ids)
            client.delete(*[_SESSION_STAFF_KEY + cs for cs in chat_session_ids])
        except Exception as e:  # noqa: BLE001
            _logger.warning("live_chat_staff_sessions_srem_failed", extra={"staff_id": staff_id, "loi": repr(e)})

    def _dang_ky_cskh_vao_phien_local(self, chat_session_id: str, staff_user_id: str) -> None:
        """Gắn mọi socket LOCAL của CSKH đó vào phiên. Gọi ở 2 nơi: worker xử
        lý REST claim (trực tiếp) và mọi worker khác (qua pub/sub kind
        'claim') — xem QA-13."""
        for ws in list(self._user_sockets.get(staff_user_id, ())):
            self._session_sockets[chat_session_id].add(ws)

    def unregister(self, ws: WebSocket, *, user_id: str) -> None:
        self._user_sockets[user_id].discard(ws)
        if not self._user_sockets[user_id]:
            del self._user_sockets[user_id]
        self._staff_sockets.discard(ws)
        for chat_session_id in list(self._session_sockets):
            self._session_sockets[chat_session_id].discard(ws)
            if not self._session_sockets[chat_session_id]:
                del self._session_sockets[chat_session_id]

    # ---------------------------------------------------------------
    # Fan-out liên worker qua Redis pub/sub (ADR-015)
    #
    # VÌ SAO CẦN: ConnectionManager giữ WebSocket trong RAM của TỪNG process.
    # Bật multi-worker (cần thiết để phục vụ 150 người đồng thời — xem ADR-014)
    # mà không có lớp này thì live-chat VỠ ÂM THẦM: khách nối vào worker 1,
    # CSKH nối vào worker 2, mỗi bên gửi tin chỉ tới được socket của chính
    # worker mình — hai người ngồi trong cùng một phiên chat mà không ai thấy
    # tin nhắn của ai. Không có lỗi nào được ném ra, chỉ là tin nhắn biến mất.
    #
    # THIẾT KẾ: LUÔN giao local TRƯỚC (đường cũ, không đổi) rồi MỚI publish cho
    # các worker khác, kèm `_INSTANCE_ID` để worker gốc bỏ qua tiếng vọng của
    # chính mình. Chọn cách này thay vì "publish rồi để subscriber giao tất":
    #   - 1 worker (test, dev, CI): chạy đúng y như trước kể cả khi Redis/
    #     subscriber không sống — không có kịch bản "tin nhắn biến mất vì
    #     subscriber chưa kịp chạy";
    #   - Redis chết: live-chat suy giảm về phạm vi 1 worker thay vì chết hẳn.
    # Đánh đổi: mỗi tin bị serialize thêm 1 lần. Không đáng kể so với rủi ro
    # mất tin nhắn của khách đang chờ.
    # ---------------------------------------------------------------

    async def _publish(self, kind: str, target: str | None, payload: dict[str, Any]) -> None:
        """Đẩy sang các worker khác. Redis hỏng KHÔNG được làm hỏng đường local."""
        try:
            from src.redis_client import get_default_client

            get_default_client().publish(
                _PUBSUB_CHANNEL,
                json.dumps(
                    {"src": _INSTANCE_ID, "kind": kind, "target": target, "payload": payload},
                    ensure_ascii=False,
                ),
            )
        except Exception as e:  # noqa: BLE001 — mất fan-out liên worker còn hơn mất cả tin nhắn
            _logger.warning("live_chat_pubsub_publish_failed", extra={"loi": repr(e), "kind": kind})

    async def _giao_tu_pubsub(self, kind: str, target: str | None, payload: dict[str, Any]) -> None:
        """Gọi từ vòng lặp subscriber — CHỈ giao local, KHÔNG publish lại (chống lặp vô hạn)."""
        if kind == "session" and target:
            await self._deliver_session_local(target, payload)
        elif kind == "user" and target:
            await self._deliver_user_local(target, payload)
        elif kind == "staff":
            await self._deliver_staff_local(payload)
        elif kind == "claim" and target:
            # QA-13 lớp 1 — KHÔNG giao tin, chỉ ĐĂNG KÝ: worker này có thể
            # đang giữ socket của CSKH vừa nhận ca ở worker khác.
            staff_user_id = str(payload.get("staff_user_id") or "")
            self._session_staff[target] = staff_user_id
            self._dang_ky_cskh_vao_phien_local(target, staff_user_id)
        elif kind == "unclaim" and target:
            # Phiên đã trả về hàng chờ/đổi người giữ — MỌI worker phải quên
            # ánh xạ cũ, nếu không tin của khách vẫn chảy tới CSKH cũ.
            self._session_staff.pop(target, None)

    async def send_to_session(self, chat_session_id: str, payload: dict[str, Any]) -> None:
        await self._deliver_session_local(chat_session_id, payload)
        await self._publish("session", chat_session_id, payload)

    async def _deliver_session_local(self, chat_session_id: str, payload: dict[str, Any]) -> None:
        # QA-13 — người nhận được quyết định LÚC GIAO TIN, không phụ thuộc vào
        # việc đăng ký trước đó có kịp/có tới worker này hay không.
        #
        # Vì sao không chỉ dựa vào _session_sockets: tập đó được điền bởi 2 sự
        # kiện xảy ra ở worker KHÁC (REST claim, rồi pub/sub). Đo thật 13/08
        # cho thấy chỉ dựa vào chúng vẫn mất tin lẻ tẻ — mọi cơ chế "đăng ký
        # trước, giao sau" đều có cửa sổ đua và điểm hỏng im lặng. Nguồn sự
        # thật "ai đang giữ phiên này" nằm ở Redis (thấy được từ MỌI worker),
        # nên tra thẳng lúc giao là đường ngắn nhất, không cửa sổ đua.
        targets = {id(ws): ws for ws in self._session_sockets.get(chat_session_id, ())}
        staff_id = self._cskh_dang_giu_phien(chat_session_id)
        if staff_id:
            for ws in self._user_sockets.get(staff_id, ()):
                targets.setdefault(id(ws), ws)
        for ws in list(targets.values()):
            try:
                await ws.send_json(payload)
            except Exception:
                _logger.warning(
                    "live_chat_ws_send_failed", extra={"chat_session_id": chat_session_id, "payload_type": payload.get("type")}
                )

    def _cskh_dang_giu_phien(self, chat_session_id: str) -> str | None:
        """CSKH đang giữ phiên, đọc từ Redis + nhớ lại trong RAM (1 lần đọc cho
        mỗi phiên trên mỗi worker, KHÔNG phải mỗi tin nhắn)."""
        if chat_session_id in self._session_staff:
            return self._session_staff[chat_session_id]
        try:
            raw = get_default_client().get(_SESSION_STAFF_KEY + chat_session_id)
        except Exception as e:  # noqa: BLE001
            _logger.warning("live_chat_session_staff_read_failed", extra={"chat_session_id": chat_session_id, "loi": repr(e)})
            return None
        staff_id = (raw.decode() if isinstance(raw, bytes) else raw) if raw else None
        if staff_id:
            self._session_staff[chat_session_id] = staff_id
        return staff_id

    async def send_to_user(self, user_id: str, payload: dict[str, Any]) -> None:
        await self._deliver_user_local(user_id, payload)
        await self._publish("user", user_id, payload)

    async def _deliver_user_local(self, user_id: str, payload: dict[str, Any]) -> None:
        for ws in list(self._user_sockets.get(user_id, ())):
            try:
                await ws.send_json(payload)
            except Exception:
                _logger.warning("live_chat_ws_send_failed", extra={"user_id": user_id, "payload_type": payload.get("type")})

    async def broadcast_to_staff(self, payload: dict[str, Any]) -> None:
        await self._deliver_staff_local(payload)
        await self._publish("staff", None, payload)

    async def _deliver_staff_local(self, payload: dict[str, Any]) -> None:
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

        # QA-13: phiên đã trả về hàng chờ thì CSKH cũ không còn giữ nữa — dọn
        # khỏi tập Redis để lần nối lại sau không tự gắn vào phiên người khác
        # đang xử lý.
        self._quen_phien_cua_cskh(staff_id, released_ids)
        for cs_id in released_ids:
            await self._publish("unclaim", cs_id, {})

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
        # QA-13 (đo 13/08: mất 25/60 tin, TOÀN BỘ chiều khách→CSKH, 5/6 phiên):
        # đăng ký local CHỈ có tác dụng trên worker xử lý REST claim này. Socket
        # WS của CSKH nằm ở worker nào là ngẫu nhiên (vé WS trong Redis từ bản
        # vá QA-01), nên 3/4 trường hợp nó nằm ở worker KHÁC và không bao giờ
        # được ghi vào _session_sockets ở đó ⇒ tin của khách publish tới worker
        # đó không tìm thấy người nhận. Không exception, không log — tin biến
        # mất. Phải phát cho MỌI worker cùng đăng ký, đúng tinh thần ADR-015
        # ("giao/áp local trước, rồi publish cho worker khác").
        self._dang_ky_cskh_vao_phien_local(chat_session_id, staff_user_id)
        await self._publish("claim", chat_session_id, {"staff_user_id": staff_user_id})
        self._session_staff[chat_session_id] = staff_user_id
        try:
            client = get_default_client()
            client.sadd(_STAFF_SESSIONS_KEY + staff_user_id, chat_session_id)
            client.expire(_STAFF_SESSIONS_KEY + staff_user_id, _STAFF_SESSIONS_TTL_SECONDS)
            client.set(_SESSION_STAFF_KEY + chat_session_id, staff_user_id, ex=_STAFF_SESSIONS_TTL_SECONDS)
        except Exception as e:  # noqa: BLE001
            _logger.warning("live_chat_staff_sessions_write_failed", extra={"staff_id": staff_user_id, "loi": repr(e)})
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
