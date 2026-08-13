"""GAP-SEC-002 (FIN05_QA_TestCases.jsonl) — `InvestigationLog` (node LangGraph
riêng, src/agents/nodes/investigation_log.py) chưa có test nào chạm tới —
`tests/test_agents/test_audit_trail_completeness.py` chỉ test tầng
`ToolResult`, docstring module đó tự nhận InvestigationLog "phụ thuộc graph
LangGraph chạy thật... phức tạp hơn giá trị mang lại".

PHÁT HIỆN THẬT khi đọc lại `write_investigation_logs_for_ticket`: đây là 1
HÀM THUẦN — nhận `all_messages: list` (list message LangChain thô), KHÔNG tự
chạy graph. Test được TRỰC TIẾP và DETERMINISTIC bằng cách tự dựng
AIMessage/ToolMessage giả lập đúng shape thật, KHÔNG cần gọi OpenAI/LangGraph
thật — đánh giá lại đúng của module gốc là chưa chính xác."""
from __future__ import annotations

import json

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from src.agents.nodes.investigation_log import write_investigation_logs_for_ticket
from src.db.models import InvestigationLog
from src.tools.base import record_tool_result
from src.tools.create_ticket import create_ticket


def _ai_tool_call(name: str, args: dict, call_id: str) -> AIMessage:
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": call_id}])


def _tool_result(call_id: str, payload: dict) -> ToolMessage:
    return ToolMessage(content=json.dumps(payload), tool_call_id=call_id)


def _make_ticket(sample_db, user_id="USR-A") -> str:
    result = create_ticket(
        sample_db,
        user_id=user_id,
        complaint_type="money_not_received",
        scope="internal_wallet",
        description_raw="test",
        trans_id="TXN-0001",
    )
    sample_db.commit()
    return result["ticket_id"]


def test_writes_one_log_row_per_investigation_tool_call_in_order(sample_db):
    ticket_id = _make_ticket(sample_db)

    # tool_result_id=None ở đây (không phải chuỗi bịa) — cột này có FK thật
    # tới tool_results.tool_result_id (models.py), SQLite bật PRAGMA
    # foreign_keys=ON (src/db/session.py) nên 1 id bịa không tồn tại sẽ vỡ
    # constraint. Việc trace ngược đúng ToolResult thật được test riêng ở
    # test_tool_result_id_extracted_correctly_when_a_real_tool_result_exists.
    messages = [
        HumanMessage(content="Tôi bị chuyển nhầm tiền"),
        _ai_tool_call("lookup_transaction", {"trans_id": "TXN-0001"}, "call_1"),
        _tool_result("call_1", {"status": "found"}),
        _ai_tool_call("create_ticket", {"complaint_type": "money_not_received"}, "call_2"),
        _tool_result("call_2", {"ticket_id": ticket_id}),
    ]

    write_investigation_logs_for_ticket(sample_db, ticket_id=ticket_id, all_messages=messages)
    sample_db.commit()

    logs = sample_db.query(InvestigationLog).filter_by(ticket_id=ticket_id).order_by(InvestigationLog.step_no).all()
    assert [lg.tool_called for lg in logs] == ["lookup_transaction", "create_ticket"]
    assert [lg.step_no for lg in logs] == [1, 2]
    assert logs[0].tool_input_json == {"trans_id": "TXN-0001"}
    # created_at tăng dần đúng thứ tự step_no (US-004: CSKH xem lại đúng trình tự thật)
    assert logs[0].created_at < logs[1].created_at


def test_tool_result_id_extracted_correctly_when_a_real_tool_result_exists(sample_db):
    """Xác nhận tool_result_id KHÔNG chỉ đọc suông từ payload — trace được
    ngược lại đúng dòng ToolResult thật (FK thật, không phải chuỗi bịa)."""
    ticket_id = _make_ticket(sample_db)
    real_tool_result_id = record_tool_result(sample_db, "lookup_transaction", {"status": "found"})
    sample_db.commit()

    messages = [
        _ai_tool_call("lookup_transaction", {"trans_id": "TXN-0001"}, "call_1"),
        _tool_result("call_1", {"status": "found", "tool_result_id": real_tool_result_id}),
        _ai_tool_call("create_ticket", {}, "call_2"),
        _tool_result("call_2", {"ticket_id": ticket_id}),
    ]
    write_investigation_logs_for_ticket(sample_db, ticket_id=ticket_id, all_messages=messages)
    sample_db.commit()

    log = sample_db.query(InvestigationLog).filter_by(ticket_id=ticket_id, tool_called="lookup_transaction").one()
    assert log.tool_result_id == real_tool_result_id


def test_scopes_correctly_when_two_tickets_created_in_same_thread(sample_db):
    """Khách tạo 2 ticket trong CÙNG 1 phiên chat — log của ticket THỨ HAI
    không được lẫn tool call thuộc về ticket ĐẦU TIÊN (khoanh vùng lùi từ
    create_ticket liền trước, xem docstring module gốc)."""
    ticket_1 = _make_ticket(sample_db)
    ticket_2 = _make_ticket(sample_db)

    messages = [
        _ai_tool_call("lookup_transaction", {"trans_id": "TXN-0001"}, "call_1"),
        _tool_result("call_1", {"status": "found"}),
        _ai_tool_call("create_ticket", {}, "call_2"),
        _tool_result("call_2", {"ticket_id": ticket_1}),
        _ai_tool_call("get_customer_history", {}, "call_3"),
        _tool_result("call_3", {"status": "ok"}),
        _ai_tool_call("create_ticket", {}, "call_4"),
        _tool_result("call_4", {"ticket_id": ticket_2}),
    ]

    write_investigation_logs_for_ticket(sample_db, ticket_id=ticket_2, all_messages=messages)
    sample_db.commit()

    logs_t2 = sample_db.query(InvestigationLog).filter_by(ticket_id=ticket_2).all()
    assert [lg.tool_called for lg in logs_t2] == ["get_customer_history", "create_ticket"]
    # ticket_1 chưa từng được gọi write_investigation_logs_for_ticket -> đúng 0 dòng
    logs_t1 = sample_db.query(InvestigationLog).filter_by(ticket_id=ticket_1).all()
    assert logs_t1 == []


def test_non_investigation_tool_calls_are_excluded_from_trail(sample_db):
    """request_human_handoff không nằm trong _INVESTIGATION_TOOL_NAMES —
    không được lọt vào investigation trail CSKH xem (trail chỉ nên phản ánh
    quá trình ĐIỀU TRA, không phải mọi tool call agent từng gọi)."""
    ticket_id = _make_ticket(sample_db)

    messages = [
        _ai_tool_call("lookup_transaction", {"trans_id": "TXN-0001"}, "call_1"),
        _tool_result("call_1", {"status": "found"}),
        _ai_tool_call("request_human_handoff", {"reason": "khách muốn gặp người thật"}, "call_2"),
        _tool_result("call_2", {"status": "ok", "ticket_id": "TCK-other"}),
        _ai_tool_call("create_ticket", {}, "call_3"),
        _tool_result("call_3", {"ticket_id": ticket_id}),
    ]
    write_investigation_logs_for_ticket(sample_db, ticket_id=ticket_id, all_messages=messages)
    sample_db.commit()

    logs = sample_db.query(InvestigationLog).filter_by(ticket_id=ticket_id).all()
    assert "request_human_handoff" not in [lg.tool_called for lg in logs]
    assert [lg.tool_called for lg in logs] == ["lookup_transaction", "create_ticket"]


def test_no_matching_create_ticket_call_is_a_silent_no_op(sample_db):
    """ticket_id không khớp bất kỳ kết quả create_ticket nào trong messages
    (vd lỗi logic gọi nhầm ticket_id) — PHẢI im lặng bỏ qua, không raise,
    không ghi log rác (đúng chỉ dẫn docstring: lỗi ghi log phụ không nên làm
    hỏng cả lượt chat đã tạo ticket thành công)."""
    ticket_id = _make_ticket(sample_db)
    messages = [
        _ai_tool_call("lookup_transaction", {"trans_id": "TXN-0001"}, "call_1"),
        _tool_result("call_1", {"status": "found"}),
    ]
    write_investigation_logs_for_ticket(sample_db, ticket_id=ticket_id, all_messages=messages)
    sample_db.commit()

    assert sample_db.query(InvestigationLog).filter_by(ticket_id=ticket_id).count() == 0
