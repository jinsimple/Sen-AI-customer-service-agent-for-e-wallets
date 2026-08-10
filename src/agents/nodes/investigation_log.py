"""Ghi lại investigation trail thật cho CSKH (US-004) — trước khi có agent,
`investigation_logs` luôn rỗng vì không ai ghi vào bảng này. Khi agent tạo
ticket thành công trong một lượt hội thoại, hàm ở đây duyệt lại lịch sử
message của thread (đã có sẵn qua checkpointer của LangGraph), khoanh đúng
vùng tool-call dẫn tới ticket đó, và ghi thành các dòng InvestigationLog để
CSKH xem lại ở `GET /tickets/{id}` (src/api/main.py)."""
from __future__ import annotations

import datetime as dt
import json

from langchain_core.messages import AIMessage, ToolMessage
from sqlalchemy.orm import Session

from src.db.models import InvestigationLog
from src.tools.base import new_id

# Chỉ 4 tool của agent khách hàng (customer_tools.py) mới đáng ghi vào trail
# — tránh lẫn tool call của một agent khác nếu sau này mở rộng. search_policy
# ở đây để CSKH thấy được căn cứ chính sách agent đã tra trước khi phân loại
# ticket (RAG chính sách/FAQ, src/rag/).
_INVESTIGATION_TOOL_NAMES = {
    "lookup_transaction",
    "get_customer_history",
    "create_ticket",
    "search_policy",
}


def write_investigation_logs_for_ticket(session: Session, *, ticket_id: str, all_messages: list) -> None:
    """Không tìm thấy vùng khớp -> bỏ qua im lặng (lỗi ghi log phụ không nên
    làm hỏng cả lượt chat đã tạo ticket thành công)."""
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

    # Khoanh vùng: tìm lần gọi create_ticket khớp đúng ticket_id vừa tạo,
    # lùi lại tới lần create_ticket liền trước đó (nếu có) làm điểm bắt đầu
    # — đúng cả khi khách đã mở nhiều ticket trong cùng 1 phiên chat.
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
                # step_no tăng dần theo thứ tự thời gian thật (giữ đúng thứ
                # tự khi CSKH xem lại), không phải created_at thật của model
                # call (LangGraph không lưu timestamp riêng cho tool call).
                created_at=now + dt.timedelta(seconds=step_no),
            )
        )
    session.flush()
