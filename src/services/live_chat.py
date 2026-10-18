"""Real live chat (WebSocket) — upgrades CTRL-001 from asynchronous "flag the ticket" to
"real-time two-way chat" (plan of 2026-08-11). Every chat session is ALWAYS attached to an
existing ticket (`ChatSession.ticket_id` NOT NULL) — in line with the agreed principle
"an escalation path, not a channel parallel to the AI": the customer must already have
been `flag_human_handoff`-ed / had a ticket created by the AI; live chat only upgrades how
CSKH handles that ticket, it does not create a separate business flow.

Simple claim-based routing (no round-robin/ML) — `claim_session()` uses a conditional
UPDATE (`claimed_by IS NULL`) as optimistic concurrency, enough for the surveyed scale of
~4 CSKH + 2 supervisors / ~50 concurrent sessions.
"""
from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from src.db.models import ChatSession, Complaint, InvestigationLog, Message, Ticket, User
from src.tools.base import ToolError, new_id
from src.tools.masking import che_pii_van_ban


def open_chat_session(session: Session, *, ticket_id: str, customer_id: str, now: dt.datetime | None = None) -> dict[str, Any]:
    """Create a new chat session for a ticket, or reuse an existing `waiting`/`active` session
    for EXACTLY that ticket (a customer re-clicking "open chat" does not create a duplicate
    session — same de-duplication principle as create_ticket/flag_human_handoff)."""
    now = now or dt.datetime.utcnow()

    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        raise ToolError(f"ticket_id không tồn tại: {ticket_id}")
    complaint = session.get(Complaint, ticket.complaint_id)
    if complaint is None or complaint.user_id != customer_id:
        raise ToolError(f"ticket_id không thuộc customer_id đang mở chat: {ticket_id}")

    existing = session.scalars(
        select(ChatSession)
        .where(ChatSession.ticket_id == ticket_id, ChatSession.status.in_(("waiting", "active")))
        .order_by(ChatSession.started_at.desc())
    ).first()
    if existing is not None:
        return _session_to_dict(existing)

    chat_session = ChatSession(
        chat_session_id=new_id("CHS"),
        ticket_id=ticket_id,
        customer_id=customer_id,
        status="waiting",
        started_at=now,
    )
    session.add(chat_session)
    session.flush()
    return _session_to_dict(chat_session)


def claim_session(
    session: Session, *, chat_session_id: str, staff_id: str, is_cskh: bool = False, now: dt.datetime | None = None
) -> dict[str, Any] | None:
    """Optimistic-concurrency claim — succeeds only if NOBODY has claimed it yet
    (`claimed_by IS NULL`). Returns None if someone else claimed it first (the caller shows
    "already taken"), does not raise — this is a normal situation when 2 CSKH agents click
    claim at the same moment, not a system error.

    CP10b (BOLA, 05/09) — BEFORE this fix, claiming a chat session via "Open & claim" only
    set `ChatSession.claimed_by`, completely separate from `claim_ticket()`
    (route /tickets/{id}/claim, ADR-064). The BOLA guard
    `_agent_blocked_by_claim` only reads `Ticket.claimed_by` — always NULL via
    this path — so a second CSKH agent opening the SAME ticket directly was never blocked,
    even though the ticket "looked" claimed on the dashboard. Since this fix, a CSKH agent
    claiming the chat session ALSO claims the ticket (same "Claim ticket" semantics, same
    atomic `claimed_by IS NULL` pattern) — claim the Ticket FIRST and only claim the
    ChatSession if that wins (or it is already ours), avoiding a two-resource rollback if
    the claim fails halfway.

    `is_cskh=False` (supervisor) DELIBERATELY skips the Ticket lock — supervisors are not part
    of the lock-by-claim model (`_agent_blocked_by_claim` always skips supervisors
    unconditionally), so a supervisor claiming a chat session must not lock the ticket away
    from other CSKH agents — that would be NEW unintended behaviour, not a bug fix."""
    now = now or dt.datetime.utcnow()
    chat_session = session.get(ChatSession, chat_session_id)

    if is_cskh and chat_session is not None:
        session.execute(
            update(Ticket)
            .where(Ticket.ticket_id == chat_session.ticket_id, Ticket.claimed_by.is_(None))
            .values(claimed_by=staff_id, claimed_at=now)
        )
        ticket = session.get(Ticket, chat_session.ticket_id)
        if ticket.claimed_by != staff_id:
            return None  # ticket already belongs to another CSKH agent — no hijacking via the chat path

    result = session.execute(
        update(ChatSession)
        .where(ChatSession.chat_session_id == chat_session_id, ChatSession.claimed_by.is_(None))
        .values(claimed_by=staff_id, status="active", claimed_at=now)
    )
    session.flush()
    if result.rowcount == 0:
        return None

    chat_session = session.get(ChatSession, chat_session_id)
    return _session_to_dict(chat_session)


def close_session(session: Session, *, chat_session_id: str, now: dt.datetime | None = None) -> dict[str, Any]:
    now = now or dt.datetime.utcnow()
    chat_session = session.get(ChatSession, chat_session_id)
    if chat_session is None:
        raise ToolError(f"chat_session_id không tồn tại: {chat_session_id}")
    chat_session.status = "closed"
    chat_session.closed_at = now
    session.flush()
    return _session_to_dict(chat_session)


def transfer_session(session: Session, *, chat_session_id: str) -> dict[str, Any]:
    """Shift handoff — clears claimed_by, back to the queue. NO separate handoff-note
    mechanism needed: the transcript (messages) + AI context (via ticket_id) are enough for
    the next CSKH agent to see everything immediately."""
    chat_session = session.get(ChatSession, chat_session_id)
    if chat_session is None:
        raise ToolError(f"chat_session_id không tồn tại: {chat_session_id}")
    chat_session.claimed_by = None
    chat_session.status = "waiting"
    chat_session.claimed_at = None
    session.flush()
    return _session_to_dict(chat_session)


def record_message(
    session: Session,
    *,
    chat_session_id: str,
    role: str,
    content: str,
    now: dt.datetime | None = None,
) -> dict[str, Any]:
    now = now or dt.datetime.utcnow()
    chat_session = session.get(ChatSession, chat_session_id)
    if chat_session is None:
        raise ToolError(f"chat_session_id không tồn tại: {chat_session_id}")

    message = Message(
        message_id=new_id("MSG"),
        chat_session_id=chat_session_id,
        ticket_id=chat_session.ticket_id,
        role=role,
        content=content,
        tool_call_ids=[],
        created_at=now,
    )
    session.add(message)
    session.flush()
    # M3 (fixed by the real PO 25/08) — STORE IN FULL, MASK AT READ TIME.
    # `Message.content` above keeps the VERBATIM text (encrypted at rest via
    # EncryptedText); only the RETURNED value is masked. That returned value is a real READ path,
    # not decoration: api/live_chat_ws.py:583 broadcasts it directly to both ends of the chat.
    #
    # 🔴 DO NOT SWITCH TO MASKING BEFORE `session.add`. The conflict between the P0 test
    # (describing "mask before storing") and BR-07 (`src/tools/masking.py`, which forbids storing
    # masked copies) WAS ADJUDICATED BY THE REAL PO: BR-07 WINS. Reason: the chat window has no
    # full copy anywhere else; masking on write loses it forever — even if that exact sentence is
    # later needed to adjudicate a complaint.
    # Record: docs/nhat-ky/2026-08-25-P0-live-chat-PII-ba-muc-che-cho-PO-chon.md
    return {
        "message_id": message.message_id,
        "chat_session_id": chat_session_id,
        "role": role,
        "content": che_pii_van_ban(content),
        "created_at": message.created_at.isoformat(),
    }


def submit_csat(session: Session, *, chat_session_id: str, score: int, now: dt.datetime | None = None) -> dict[str, Any]:
    if not 1 <= score <= 5:
        raise ToolError(f"csat score không hợp lệ (phải 1-5): {score}")
    now = now or dt.datetime.utcnow()
    chat_session = session.get(ChatSession, chat_session_id)
    if chat_session is None:
        raise ToolError(f"chat_session_id không tồn tại: {chat_session_id}")
    chat_session.csat_score = score
    chat_session.csat_submitted_at = now
    session.flush()
    return _session_to_dict(chat_session)


def get_handoff_context(session: Session, *, ticket_id: str) -> dict[str, Any]:
    """Hand over ALL the context the AI has investigated to CSKH as soon as the case is
    claimed — so the customer doesn't have to repeat themselves (agreed business requirement).
    Reads existing data only (Ticket/Complaint/InvestigationLog), no extra inference."""
    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        raise ToolError(f"ticket_id không tồn tại: {ticket_id}")
    complaint = session.get(Complaint, ticket.complaint_id)
    customer = session.get(User, complaint.user_id) if complaint else None
    logs = session.scalars(
        select(InvestigationLog).where(InvestigationLog.ticket_id == ticket_id).order_by(InvestigationLog.step_no)
    ).all()

    return {
        "ticket": {
            "ticket_id": ticket.ticket_id,
            "hitl_status": ticket.hitl_status,
            "sla_due_at": ticket.sla_due_at.isoformat(),
            "human_handoff_requested": ticket.human_handoff_requested,
        },
        "complaint": (
            {
                "complaint_id": complaint.complaint_id,
                "type": complaint.type,
                "scope": complaint.scope,
                "priority": complaint.priority,
                "trans_id": complaint.trans_id,
                "description_raw": complaint.description_raw,
                "fraud_signals": complaint.fraud_signals,
            }
            if complaint
            else None
        ),
        "customer": (
            {"user_id": customer.user_id, "full_name": customer.full_name, "phone": customer.phone}
            if customer
            else None
        ),
        "investigation_logs": [
            {
                "step_no": log.step_no,
                "tool_called": log.tool_called,
                "tool_input_json": log.tool_input_json,
                "agent_note": log.agent_note,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
    }


def _session_to_dict(chat_session: ChatSession) -> dict[str, Any]:
    return {
        "chat_session_id": chat_session.chat_session_id,
        "ticket_id": chat_session.ticket_id,
        "customer_id": chat_session.customer_id,
        "status": chat_session.status,
        "claimed_by": chat_session.claimed_by,
        "started_at": chat_session.started_at.isoformat(),
        "claimed_at": chat_session.claimed_at.isoformat() if chat_session.claimed_at else None,
        "closed_at": chat_session.closed_at.isoformat() if chat_session.closed_at else None,
        "csat_score": chat_session.csat_score,
    }
