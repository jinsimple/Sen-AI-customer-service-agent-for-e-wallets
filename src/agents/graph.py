"""LangGraph agent cho luồng khiếu nại lõi (PRD §6) — entrypoint duy nhất
`run_agent_turn()`, gọi từ `POST /agent/chat` (src/api/main.py).

Lưu ý API: `langgraph.prebuilt.create_react_agent` đã deprecated ở bản
langgraph 1.2.10/langchain 1.3.14 đang cài — dùng `langchain.agents.create_agent`
thay thế (tham số prompt tên là `system_prompt`, không phải `prompt`)."""
from __future__ import annotations

import datetime as dt
import json
from typing import Any

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from sqlalchemy.orm import Session

from src.agents.nodes.investigation_log import write_investigation_logs_for_ticket
from src.agents.prompt import build_system_prompt
from src.agents.tools.customer_tools import build_customer_tools
from src.config import OPENAI_API_KEY, OPENAI_MODEL
from src.db.models import User
from src.tools.base import ToolError

# Singleton module-level: agent được build lại mỗi request (session/tools
# gắn với request đó), nhưng checkpointer dùng chung 1 instance nên lịch sử
# hội thoại nối tiếp được qua nhiều request cùng thread_id=user_id. Mất khi
# restart process — chấp nhận được, khớp US-010 "không giữ ngữ cảnh xuyên
# phiên đăng nhập khác nhau" (Brief).
_CHECKPOINTER = MemorySaver()


def _build_agent(session: Session, *, user_id: str, customer_name: str):
    model = ChatOpenAI(model=OPENAI_MODEL, temperature=0.2, api_key=OPENAI_API_KEY)
    tools = build_customer_tools(session, user_id=user_id)
    system_prompt = build_system_prompt(current_time=dt.datetime.utcnow(), customer_name=customer_name)
    return create_agent(model, tools, system_prompt=system_prompt, checkpointer=_CHECKPOINTER)


def run_agent_turn(session: Session, *, user_id: str, message: str, thread_id: str | None = None) -> dict[str, Any]:
    user = session.get(User, user_id)
    if user is None:
        raise ToolError(f"user_id không tồn tại: {user_id}")

    agent = _build_agent(session, user_id=user_id, customer_name=user.full_name)
    # thread_id mặc định = user_id (hành vi thật, không đổi). eval/_harness.py
    # truyền thread_id riêng biệt mỗi case để cô lập bộ nhớ hội thoại
    # (checkpointer module-level dùng chung — nếu không cô lập, nhiều case
    # cùng user_id trong 1 lần chạy eval sẽ nối tiếp hội thoại của nhau).
    config = {"configurable": {"thread_id": thread_id or user_id}}

    state_before = agent.get_state(config)
    prev_len = len(state_before.values.get("messages", [])) if state_before.values else 0

    result = agent.invoke({"messages": [HumanMessage(content=message)]}, config=config)
    all_messages = result["messages"]
    turn_messages = all_messages[prev_len:]

    reply = ""
    for m in reversed(turn_messages):
        if isinstance(m, AIMessage) and not m.tool_calls:
            reply = m.content
            break

    tool_msgs_by_id = {m.tool_call_id: m for m in turn_messages if isinstance(m, ToolMessage)}
    tool_calls_out: list[dict] = []
    ticket_id = None
    should_escalate = None

    for m in turn_messages:
        if not (isinstance(m, AIMessage) and m.tool_calls):
            continue
        for call in m.tool_calls:
            tm = tool_msgs_by_id.get(call["id"])
            if tm is None:
                continue
            try:
                payload = json.loads(tm.content)
            except (json.JSONDecodeError, TypeError):
                payload = {"raw": tm.content}
            tool_calls_out.append({"tool_name": call["name"], "args": call["args"], "result": payload})
            if call["name"] == "create_ticket" and "ticket_id" in payload:
                ticket_id = payload["ticket_id"]
                should_escalate = payload.get("should_escalate")

    if ticket_id is not None:
        write_investigation_logs_for_ticket(session, ticket_id=ticket_id, all_messages=all_messages)

    return {
        "reply": reply,
        "tool_calls": tool_calls_out,
        "ticket_id": ticket_id,
        "should_escalate": should_escalate,
    }
