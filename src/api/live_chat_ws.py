"""Live chat WebSocket — connection manager + handler.

The socket is the ONLY thing still held in each process's RAM (the nature of WebSockets —
it can't be moved anywhere); every other piece of state moved to a shared store when
multi-worker was enabled: message fan-out via Redis pub/sub (ADR-015), rate limiting via a
Redis sliding window (Auth Flow round 2026-08-12), and handshake tickets via Redis
TTL+GETDEL (QA-01, QA report 13/08 — tickets in an in-RAM dict made the handshake fail
~3/4 of the time with 4 workers, because REST issued the ticket on worker A and the WS landed
on worker B).

A minimal WS protocol — only 1 inbound message type (`send_message`):
the customer always automatically "joins" the chat_session_id bound into the ticket at connect
time; a CSKH agent is automatically registered as a participant of a session AS SOON AS the
claim succeeds via REST (see notify_claimed) — no extra "join_session" round trip needed.
"""
from __future__ import annotations

import asyncio
import datetime as dt
import json
import logging
import secrets
import time
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
# Tickets MUST live in a shared store (QA-01): minting via REST and consuming via the WS
# handshake have no guarantee of landing on the same worker. If Redis is down, mint/consume
# raise and the handshake fails CLEARLY — deliberately no fallback to RAM, because that fallback
# is exactly the old flaky bug coming back in a harder-to-catch form (same philosophy as
# ADR-013: no silent fallbacks).
_WS_TICKET_KEY = "fin05:ws_ticket:"
# QA-13 — the set of sessions each CSKH agent holds, so a RE-connecting socket reattaches to
# the right sessions. TTL longer than a shift; a closed session is SREM'd immediately (see
# close/release).
_STAFF_SESSIONS_KEY = "fin05:live_chat:staff_sessions:"
_STAFF_SESSIONS_TTL_SECONDS = 12 * 3600
# REVERSE mapping: session -> the CSKH agent holding it. Used at DELIVERY time so it doesn't
# depend on the order of registration events across workers (see _deliver_session_local).
_SESSION_STAFF_KEY = "fin05:live_chat:session_staff:"
# F-14 — the expiry of each worker's in-RAM 'session -> CSKH' cache. 30s:
# short enough that a missed `unclaim` message heals itself before the customer can type a few
# lines, long enough to still be 1 Redis read per session per 30s rather than per message.
_SESSION_STAFF_TTL = 30.0
# Only sweep when above this threshold — cleaning on every read pays for work not yet needed.
# 512 concurrent sessions on ONE worker is already far beyond pilot scale.
_SESSION_STAFF_SWEEP_THRESHOLD = 512
_logger = logging.getLogger("fin05.live_chat_ws")


# Shared pub/sub channel for cross-worker live-chat fan-out (ADR-015).
_PUBSUB_CHANNEL = "fin05:live_chat"
# UNIQUE identifier of this process — used to ignore our own echo when receiving back a
# message we just published (otherwise it would be delivered twice to the local socket: once
# directly, once via pub/sub).
_INSTANCE_ID = secrets.token_hex(8)


async def _subscriber_loop(mgr: ConnectionManager) -> None:
    """Receive messages from OTHER workers and deliver them to this worker's local sockets.

    Runs in the background for the whole process lifetime, started from FastAPI startup.
    Network errors MUST NOT kill the loop — transient Redis drops are normal on cloud
    infrastructure (exactly the keepalive/health_check note captured in the packaging
    playbook); it retries rather than silently stopping fan-out forever.
    """
    while True:
        try:
            pubsub = get_default_client().pubsub(ignore_subscribe_messages=True)
            pubsub.subscribe(_PUBSUB_CHANNEL)
            _logger.info("live_chat_pubsub_subscribed", extra={"instance": _INSTANCE_ID})
            while True:
                # get_message blocks the thread -> pushed to the thread pool so it doesn't choke the
                # event loop (other live-chat routes must still be served).
                msg = await asyncio.to_thread(pubsub.get_message, timeout=1.0)
                if not msg:
                    await asyncio.sleep(0)  # yield the event loop
                    continue
                try:
                    data = json.loads(msg["data"])
                except (TypeError, ValueError):
                    continue
                if data.get("src") == _INSTANCE_ID:
                    continue  # our own echo, already delivered locally
                await mgr._deliver_from_pubsub(
                    data.get("kind", ""), data.get("target"), data.get("payload") or {}
                )
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001
            _logger.warning("live_chat_pubsub_loop_error", extra={"loi": repr(e)})
            await asyncio.sleep(2)


class ConnectionManager:
    """Module-level singleton (same pattern as _CHECKPOINTER in graph.py)."""

    def __init__(self):
        self._session_sockets: dict[str, set[WebSocket]] = defaultdict(set)
        self._user_sockets: dict[str, set[WebSocket]] = defaultdict(set)
        self._staff_sockets: set[WebSocket] = set()
        # Cache "session -> CSKH" to avoid a Redis read per message (QA-13).
        # F-14 — every entry has an EXPIRY. The old version was a dict with no expiry and no cap,
        # only
        # cleared on receiving `unclaim` or on session close. Two failures followed:
        #
        #  * WRONG mappings lived forever. `unclaim` goes over pub/sub — fire-and-forget. A worker
        #    that
        #    just restarted, a Redis blip, or a worker spawned after the message was sent: it never
        # learns
        #    the session changed hands, and keeps pushing the CUSTOMER's messages to the old CSKH
        # agent —
        #    someone no longer entitled to read that session. That is a data leak, not just a
        # routing bug.
        #  * Unbounded growth: every session that ever passed through the worker stayed forever.
        #
        # Redis is the source of truth; this dict only avoids a read per message. Giving it a short
        # expiry means every discrepancy HEALS ITSELF within at most _SESSION_STAFF_TTL seconds,
        # while
        # keeping the original purpose: 1 Redis read per session per 30 seconds, not per message.
        self._session_staff: dict[str, tuple[str, float]] = {}
        # Synchronised via Redis (Auth Flow upgrade 2026-08-12, see
        # src/rate_limit.py) — previously a process-private in-memory dict, losing all state on
        # every
        # backend restart (rate limits silently "reset" after every deploy/restart). Same
        # sliding-window algorithm, only the storage changed — thresholds/semantics unchanged.
        self.ws_ticket_limiter = RedisSlidingWindowLimiter(max_calls=5, window_seconds=60, name="ws_ticket")
        # QA-11: the CSKH/supervisor ticket-issuing path previously had NO limiter at all (measured:
        # 40/40 calls all returned 200, while customers were correctly blocked after 5). The limit
        # is
        # DELIBERATELY wider than for customers, not an incomplete copy: on-shift staff reconnect
        # the WS
        # whenever the network flickers/they switch tabs; capping them at 5/minute would block
        # exactly the
        # people serving customers. 20/minute still stops abuse (bulk ticket-pumping scenarios)
        # without
        # touching the real working rhythm.
        self.staff_ws_ticket_limiter = RedisSlidingWindowLimiter(
            max_calls=20, window_seconds=60, name="ws_ticket_staff"
        )
        self.message_limiter = RedisSlidingWindowLimiter(max_calls=60, window_seconds=3600, name="live_chat_msg")

    def mint_ticket(self, *, user_id: str, role: str, chat_session_id: str | None = None) -> str:
        ticket = secrets.token_urlsafe(24)
        if _WS_TICKET_TTL_SECONDS <= 0:
            # TTL <= 0 means "expire immediately" — nothing is stored (Redis rejects ex<=0), and
            # consume
            # returns None. Preserves the semantics for the TTL tests.
            return ticket
        get_default_client().set(
            _WS_TICKET_KEY + ticket,
            json.dumps({"user_id": user_id, "role": role, "chat_session_id": chat_session_id}),
            ex=_WS_TICKET_TTL_SECONDS,
        )
        return ticket

    def consume_ticket(self, ticket: str) -> dict[str, Any] | None:
        """Single use — GETDEL reads+deletes in ONE atomic command (anti-replay):
        if 2 handshakes race for the same ticket exactly one wins, even when they land on
        2 different workers."""
        raw = get_default_client().getdel(_WS_TICKET_KEY + ticket)
        return json.loads(raw) if raw else None

    async def register(self, ws: WebSocket, *, user_id: str, chat_session_id: str | None, is_staff: bool) -> None:
        # Real finding (2026-08-11): one user can create "orphaned" WS connections
        # (e.g. an old tab not cleaned up, a flaky network that doesn't fire the disconnect event
        # properly) — without cleanup the old connection stays in
        # _user_sockets/_session_sockets, so broadcasts go to BOTH places
        # (one where the client is no longer listening properly), looking like duplicated/split
        # messages. At most 1 ACTIVE connection per user at a time — actively close the old
        # connection
        # before registering the new one, eliminating this whole class of bug regardless of what
        # caused
        # the old connection.
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
            # QA-13 layer 2 — a CSKH agent connecting (or RE-connecting) after claiming a case:
            # staff WS
            # tickets carry no chat_session_id (when requesting the ticket they hadn't claimed
            # anything yet),
            # so relying solely on notify_claimed means one network drop/tab switch leaves the new
            # socket
            # permanently attached to no session — and customer messages silently disappear again. A
            # very
            # real scenario when demoing/working a shift on wifi.
            for cs_id in self._sessions_claimed_by_agent(user_id):
                self._session_sockets[cs_id].add(ws)

    @staticmethod
    def _sessions_claimed_by_agent(staff_id: str) -> list[str]:
        """The sessions this CSKH agent holds, read from REDIS (not the DB, not process RAM): the
        same reason Redis was chosen for the WS ticket store in QA-01 — the state must be
        visible to EVERY worker. A Redis error MUST NOT break the WS connection: this is a
        safety net for reconnects; the main path is still the 'claim' pub/sub. Swallowing the
        error here is deliberate but NOT silent — a warning is logged (ADR-013)."""
        try:
            raw = get_default_client().smembers(_STAFF_SESSIONS_KEY + staff_id)
        except Exception as e:  # noqa: BLE001
            _logger.warning("live_chat_staff_sessions_read_failed", extra={"staff_id": staff_id, "loi": repr(e)})
            return []
        return [s.decode() if isinstance(s, bytes) else str(s) for s in (raw or ())]

    def _forget_agent_session(self, staff_id: str, chat_session_ids: list[str]) -> None:
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

    def _register_agent_session_local(self, chat_session_id: str, staff_user_id: str) -> None:
        """Attach all of that CSKH agent's LOCAL sockets to the session. Called from 2 places: the
        worker handling the REST claim (directly) and every other worker (via pub/sub kind
        'claim') — see QA-13."""
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
    # Cross-worker fan-out via Redis pub/sub (ADR-015)
    #
    # WHY IT IS NEEDED: ConnectionManager holds WebSockets in the RAM of EACH process.
    # Enabling multi-worker (needed to serve 150 concurrent users — see ADR-014) without this layer
    # BREAKS live chat SILENTLY: the customer connects to worker 1, CSKH connects to worker 2, and
    # each side's messages only reach sockets on its own worker — two people sitting in the same
    # chat session with neither seeing the other's messages. No error is raised; messages simply
    # vanish.
    #
    # DESIGN: ALWAYS deliver locally FIRST (the old path, unchanged) and only THEN publish to the
    # other workers, with `_INSTANCE_ID` so the originating worker ignores its own echo. This was
    # chosen over "publish and let the subscriber deliver everything":
    #   - 1 worker (test, dev, CI): behaves exactly as before even when Redis/the subscriber isn't
    #     alive — no "message vanished because the subscriber hadn't started yet" scenario;
    #   - Redis dead: live chat degrades to single-worker scope instead of dying entirely.
    # Trade-off: each message is serialised one extra time. Negligible compared with the risk of
    # losing messages from a waiting customer.
    # ---------------------------------------------------------------

    async def _publish(self, kind: str, target: str | None, payload: dict[str, Any]) -> None:
        """Push to the other workers. A Redis failure MUST NOT break the local path."""
        try:
            from src.redis_client import get_default_client

            get_default_client().publish(
                _PUBSUB_CHANNEL,
                json.dumps(
                    {"src": _INSTANCE_ID, "kind": kind, "target": target, "payload": payload},
                    ensure_ascii=False,
                ),
            )
        except Exception as e:  # noqa: BLE001 — losing cross-worker fan-out beats losing the whole message
            _logger.warning("live_chat_pubsub_publish_failed", extra={"loi": repr(e), "kind": kind})

    async def _deliver_from_pubsub(self, kind: str, target: str | None, payload: dict[str, Any]) -> None:
        """Called from the subscriber loop — ONLY delivers locally, NEVER re-publishes (prevents infinite loops)."""
        if kind == "session" and target:
            await self._deliver_session_local(target, payload)
        elif kind == "user" and target:
            await self._deliver_user_local(target, payload)
        elif kind == "staff":
            await self._deliver_staff_local(payload)
        elif kind == "claim" and target:
            # QA-13 layer 1 — NO delivery, only REGISTRATION: this worker may hold the socket of a
            # CSKH
            # agent who just claimed a case on another worker.
            staff_user_id = str(payload.get("staff_user_id") or "")
            self._session_staff[target] = (staff_user_id, time.monotonic() + _SESSION_STAFF_TTL)
            self._register_agent_session_local(target, staff_user_id)
        elif kind == "unclaim" and target:
            # The session went back to the queue/changed hands — EVERY worker must forget the old
            # mapping, otherwise the customer's messages keep flowing to the old CSKH agent.
            self._session_staff.pop(target, None)

    async def send_to_session(self, chat_session_id: str, payload: dict[str, Any]) -> None:
        await self._deliver_session_local(chat_session_id, payload)
        await self._publish("session", chat_session_id, payload)

    async def _deliver_session_local(self, chat_session_id: str, payload: dict[str, Any]) -> None:
        # QA-13 — the recipient is decided AT DELIVERY TIME, not dependent on whether an earlier
        # registration made it to this worker in time (or at all).
        #
        # Why not rely solely on _session_sockets: that set is filled by 2 events happening on OTHER
        # workers (REST claim, then pub/sub). Measured 13/08: relying on them alone still lost the
        # odd
        # message — every "register first, deliver later" mechanism has a race window and a silent
        # point
        # of failure. The source of truth for "who holds this session" lives in Redis (visible to
        # EVERY
        # worker), so looking it up at delivery time is the shortest path, with no race window.
        targets = {id(ws): ws for ws in self._session_sockets.get(chat_session_id, ())}
        staff_id = self._agent_holds_session(chat_session_id)
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

    def _agent_holds_session(self, chat_session_id: str) -> str | None:
        """The CSKH agent holding the session, read from Redis + cached in RAM with an EXPIRY (1
        read per session per _SESSION_STAFF_TTL seconds on each worker, NOT per message)."""
        remembered = self._session_staff.get(chat_session_id)
        if remembered is not None:
            staff_id_nho, expired = remembered
            if time.monotonic() < expired:
                return staff_id_nho
            # Expired: drop it and re-read Redis. NEVER return the stale value as a "fallback" — the
            # stale value is exactly what causes misrouting.
            self._session_staff.pop(chat_session_id, None)
        self._sweep_expired()
        try:
            raw = get_default_client().get(_SESSION_STAFF_KEY + chat_session_id)
        except Exception as e:  # noqa: BLE001
            _logger.warning("live_chat_session_staff_read_failed", extra={"chat_session_id": chat_session_id, "loi": repr(e)})
            return None
        staff_id = (raw.decode() if isinstance(raw, bytes) else raw) if raw else None
        if staff_id:
            self._session_staff[chat_session_id] = (staff_id, time.monotonic() + _SESSION_STAFF_TTL)
        return staff_id

    def _sweep_expired(self) -> None:
        """Sweep expired entries. Expiry alone does NOT prevent memory growth: an expired entry only
        disappears when someone re-reads that exact session, and nobody reads a closed
        session again. Sweep in batches when above the threshold — cheaper than scanning on
        every read, and the threshold is high enough not to run in normal operation."""
        if len(self._session_staff) <= _SESSION_STAFF_SWEEP_THRESHOLD:
            return
        now_ts = time.monotonic()
        for cs_id in [k for k, (_, expired) in self._session_staff.items() if expired <= now_ts]:
            self._session_staff.pop(cs_id, None)

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
        return len({id(ws) for ws in self._staff_sockets}) or 1  # avoid division by zero

    async def release_staff_sessions(self, *, staff_id: str) -> None:
        """Real finding (2026-08-11, manual test): CSKH pressing F5/closing the tab WITHOUT clicking
        "End chat" — without automatic cleanup, the session stays 'active'+claimed_by that agent
        FOREVER (orphaned). Double consequence: (1) a customer "asking for an agent" again
        reuses EXACTLY the old session (open_chat_session only reuses by ticket_id, unaware the
        agent disconnected) so NO new 'waiting' session appears and the dashboard has nothing to
        show; (2) the agent reopening that ticket is pulled straight into the old chat because
        claimed_by is still them. This function is called in the finally block when a CSKH WS
        disconnects — automatically returning all of that agent's active sessions to the queue,
        with the same semantics as transfer_session() (the manual "hand over shift" button),
        only a different trigger."""
        with SessionLocal() as db_session:
            stale = db_session.scalars(
                select(ChatSession).where(ChatSession.claimed_by == staff_id, ChatSession.status == "active")
            ).all()
            released_ids = [cs.chat_session_id for cs in stale]
            for cs in stale:
                live_chat.transfer_session(db_session, chat_session_id=cs.chat_session_id)
            db_session.commit()

        # QA-13: once the session is back in the queue the old CSKH agent no longer holds it —
        # remove it from the Redis set so a later reconnect doesn't auto-attach to a session someone
        # else
        # is handling.
        self._forget_agent_session(staff_id, released_ids)
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
        """The SECOND line of defence (2026-08-11, real finding: a ticket still showed "waiting for
        chat" long after the customer had logged out) — cleanup based on a CLEAN disconnect
        (release_staff_sessions/close_customer_session_on_disconnect) can't catch sudden network
        loss/a killed browser: no close frame can be sent, WebSocketDisconnect never arrives,
        and the 'waiting' session hangs forever. Called lazily whenever CSKH loads the queue
        — no extra scheduler/cron needed, matching the simplicity chosen for this whole feature
        (see the reasoning at the top of the file). ONLY closes sessions with NO socket actually
        connected — to avoid wrongly closing a customer who is genuinely still waiting, just for
        a long time."""
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
        """Real finding (2026-08-11, manual test): a customer pressing F5/closing the tab mid-chat —
        without cleanup, the ChatSession stays 'waiting'/'active' forever, as if the customer
        were still there. Closed IMMEDIATELY when the customer disconnects — the history
        (Message + Ticket.human_handoff_requested are kept, not deleted) is enough for CSKH to
        see the customer wanted a human and to call them back by phone, without the customer
        needing to return to the exact old chat session (asking for a human again next time
        creates a NEW session, matching the 'left' semantics)."""
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
        """Called from the REST route POST /live-chat/sessions/{id}/claim (main.py) after
        claim_session() succeeds — immediately registers that agent's existing socket as a
        session participant (no separate "join_session" round trip), pushes the AI's
        investigation context, and removes it from the queue shown to other CSKH agents."""
        # QA-13 (measured 13/08: lost 25/60 messages, ALL customer→CSKH, in 5/6 sessions):
        # local registration ONLY takes effect on the worker handling this REST claim. Which worker
        # holds
        # the CSKH agent's WS socket is random (WS tickets in Redis since the QA-01 fix), so 3/4 of
        # the
        # time it is on ANOTHER worker and is never recorded in _session_sockets there ⇒ customer
        # messages
        # published to that worker find no recipient. No exception, no log — the message vanishes.
        # It must
        # be broadcast to EVERY worker to register, in the spirit of ADR-015
        # ("deliver/apply locally first, then publish to other workers").
        self._register_agent_session_local(chat_session_id, staff_user_id)
        await self._publish("claim", chat_session_id, {"staff_user_id": staff_user_id})
        self._session_staff[chat_session_id] = (staff_user_id, time.monotonic() + _SESSION_STAFF_TTL)
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
        await websocket.close(code=4401)  # 4401: invalid/expired ticket (custom app code, outside the standard range)
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
                # Payload is not valid JSON (a malformed text frame) — skip this frame, DO NOT
                # disconnect;
                # the customer/CSKH can resend.
                continue
            if not isinstance(msg, dict):
                # Real finding (FIN05-StressTest-Plan-v2 ST2-E-08): valid JSON that is NOT an object
                # (e.g. an array `[1,2,3]`) made `msg.get(...)` below raise AttributeError, crashing
                # the task
                # for that connection (not the whole server, but still an uncontrolled error that
                # shouldn't
                # happen).
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
                        # Became genuinely possible after auto-close on disconnect was added
                        # (release_staff_sessions/
                        # close_customer_session_on_disconnect) — the other side's still-open tab
                        # (not yet reloaded) could
                        # otherwise still send messages if not blocked here, even though the session
                        # is closed.
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
