"""Records the real investigation trail for CSKH (US-004) — before the agent existed,
`investigation_logs` was always empty because nothing wrote to it. When the agent
successfully creates a ticket during a conversation turn, the function here walks back
through the thread's message history (already available via LangGraph's checkpointer),
isolates exactly the tool-call span that led to that ticket, and writes it as
InvestigationLog rows for CSKH to review at `GET /tickets/{id}` (src/api/main.py)."""
from __future__ import annotations

import datetime as dt
import json

from langchain_core.messages import AIMessage, ToolMessage
from sqlalchemy.orm import Session

from src.db.models import InvestigationLog
from src.tools.base import new_id

# Only the 4 tools of the customer agent (customer_tools.py) are worth recording in the
# trail — avoids mixing in tool calls from another agent if we expand later. search_policy is
# included so CSKH can see which policy evidence the agent looked up before classifying the
# ticket (policy/FAQ RAG, src/rag/).
_INVESTIGATION_TOOL_NAMES = {
    "lookup_transaction",
    "get_customer_history",
    "create_ticket",
    "search_policy",
}


def write_investigation_logs_for_ticket(session: Session, *, ticket_id: str, all_messages: list) -> None:
    """No matching span found -> skip silently (a failure in this secondary logging must not
    break a chat turn that already created a ticket successfully)."""
    tool_msgs_by_id = {m.tool_call_id: m for m in all_messages if isinstance(m, ToolMessage)}

    pairs: list[tuple[dict, ToolMessage]] = []
    for m in all_messages:
        if not (isinstance(m, AIMessage) and m.tool_calls):
            continue
        for call in m.tool_calls:
            if call["name"] not in _INVESTIGATION_TOOL_NAMES:
                continue
            tm = tool_msgs_by_id.get(call["id"])
            if tm is not None:
                pairs.append((call, tm))

    # Span isolation: find the create_ticket call matching the ticket_id just created,
    # walk back to the previous create_ticket call (if any) as the starting point
    # — correct even when the customer opened several tickets in one chat session.
    end_idx = None
    for i, (call, tm) in enumerate(pairs):
        if call["name"] != "create_ticket":
            continue
        try:
            payload = json.loads(tm.content)
        except (json.JSONDecodeError, TypeError):
            payload = {}
        if payload.get("ticket_id") == ticket_id:
            end_idx = i
    if end_idx is None:
        return

    start_idx = 0
    for i in range(end_idx - 1, -1, -1):
        if pairs[i][0]["name"] == "create_ticket":
            start_idx = i + 1
            break

    now = dt.datetime.utcnow()
    for step_no, (call, tm) in enumerate(pairs[start_idx : end_idx + 1], start=1):
        try:
            payload = json.loads(tm.content)
        except (json.JSONDecodeError, TypeError):
            payload = {"raw": tm.content}
        session.add(
            InvestigationLog(
                log_id=new_id("LOG"),
                ticket_id=ticket_id,
                step_no=step_no,
                tool_called=call["name"],
                tool_input_json=call["args"],
                tool_result_id=payload.get("tool_result_id"),
                agent_note=None,
                # step_no increases in real chronological order (preserving order when CSKH reviews
                # it), not the model call's real created_at
                # (LangGraph does not store a separate timestamp per tool call).
                created_at=now + dt.timedelta(seconds=step_no),
            )
        )
    session.flush()
