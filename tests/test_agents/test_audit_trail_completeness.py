"""FIN05-StressTest-Plan-v2 ST2-B-08/B-09 — audit trail `ToolResult`
(src/tools/base.py::record_tool_result, gọi từ MỌI tool trước khi return —
đây là nguồn sự thật duy nhất chống agent bịa số liệu, xem docstring module
đó) và `InvestigationLog` (src/agents/nodes/investigation_log.py — 1 NODE
LangGraph riêng, đọc lại lịch sử message SAU KHI graph chạy xong để ghi log).

PHẠM VI TEST THẬT SỰ Ở ĐÂY: chỉ tầng `ToolResult` — gọi trực tiếp tool qua
`build_customer_tools()` (deterministic, không cần LLM thật, cùng pattern
`tests/test_agents/test_customer_tools.py`).

SỬA LẠI ghi chú cũ (GAP-SEC-002, FIN05_QA_TestCases.jsonl): đánh giá trước
đây cho rằng `InvestigationLog` "phụ thuộc graph LangGraph chạy thật" là
SAI — `write_investigation_logs_for_ticket()` là 1 HÀM THUẦN nhận
`all_messages: list` (message LangChain thô), không tự chạy graph. Test
tầng đó (deterministic, tự dựng AIMessage/ToolMessage, không cần OpenAI) đã
có ở `tests/test_agents/test_investigation_log.py`."""
from __future__ import annotations

from src.agents.tools.customer_tools import build_customer_tools
from src.db.models import ToolResult

_NOW_TS = __import__("datetime").datetime.utcnow().timestamp()


def test_each_tool_call_produces_exactly_one_tool_result_row(sample_db):
    before = sample_db.query(ToolResult).count()

    tools = {t.name: t for t in build_customer_tools(sample_db, user_id="USR-A", otp_verified_at=_NOW_TS)}
    tools["lookup_transaction"].invoke({"trans_id": "TXN-0001"})
    sample_db.commit()

    after_one_call = sample_db.query(ToolResult).count()
    assert after_one_call == before + 1, (
        f"1 lượt gọi lookup_transaction phải sinh ĐÚNG 1 dòng ToolResult, "
        f"trước={before}, sau={after_one_call}"
    )

    tools["get_customer_history"].invoke({})
    sample_db.commit()

    after_two_calls = sample_db.query(ToolResult).count()
    assert after_two_calls == after_one_call + 1, "lượt gọi tool THỨ HAI phải cộng thêm ĐÚNG 1 dòng, không thiếu/trùng"


def test_tool_result_content_hash_matches_stored_payload(sample_db):
    """T4 (Data Brief §6.5, chống bịa số liệu) — `content_hash` phải khớp
    ĐÚNG với `raw_json` đã lưu, để về sau còn đối chiếu được payload chưa bị
    sửa tay/hỏng dữ liệu sau khi ghi. Lấy đúng `tool_result_id` tool vừa trả
    về (KHÔNG sort theo tool_result_id — sinh từ uuid4 hex, không tăng dần
    theo thời gian tạo, sort được sẽ nhặt nhầm dòng)."""
    import hashlib
    import json

    tools = {t.name: t for t in build_customer_tools(sample_db, user_id="USR-A", otp_verified_at=_NOW_TS)}
    payload = tools["lookup_transaction"].invoke({"trans_id": "TXN-0001"})
    sample_db.commit()

    saved = sample_db.get(ToolResult, payload["tool_result_id"])
    assert saved is not None
    expected_hash = hashlib.sha256(
        json.dumps(saved.raw_json, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()
    assert saved.content_hash == expected_hash
