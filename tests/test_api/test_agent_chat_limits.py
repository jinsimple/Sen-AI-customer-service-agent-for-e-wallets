"""CONSUME-001/002 (FIN05_QA_TestCases.jsonl, OWASP LLM10:2025 Unbounded
Consumption) — chặn 2 dạng "tốn tài nguyên vô hạn": input quá dài
(CONSUME-001, `AgentChatRequest.message` giới hạn 4000 ký tự — pure
Pydantic, không cần DB/LLM) và vòng lặp tool gọi mơ hồ liên tục
(CONSUME-002, `run_agent_turn()` phải bắt `GraphRecursionError` và chuyển
người xử lý thay vì crash/lặp vô hạn — mock hẳn tầng agent, không gọi
OpenAI thật)."""
from __future__ import annotations

import pytest
from langgraph.errors import GraphRecursionError
from pydantic import ValidationError

from src.api.schemas import AgentChatRequest
from src.db.models import Ticket

# ---------------------------------------------------------------------------
# CONSUME-001 — input quá dài bị Pydantic từ chối trước khi tới agent.
# ---------------------------------------------------------------------------


def test_agent_chat_request_accepts_message_at_limit():
    req = AgentChatRequest(message="a" * 4000)
    assert len(req.message) == 4000


def test_agent_chat_request_rejects_message_over_limit():
    with pytest.raises(ValidationError):
        AgentChatRequest(message="a" * 4001)


# ---------------------------------------------------------------------------
# CONSUME-002 — GraphRecursionError (vòng lặp ReAct vượt _AGENT_RECURSION_LIMIT)
# phải được bắt gọn: không crash 500, không lặp vô hạn, tạo ticket handoff
# thật (human_handoff_requested=True) thay vì để khách chờ vô thời hạn.
# ---------------------------------------------------------------------------


class _RecursionLimitCapturingAgent:
    """Bắt CHÍNH XÁC giá trị `recursion_limit` được truyền vào `.invoke()` —
    2 test CONSUME-002 bên dưới chỉ verify HÀNH VI khi GraphRecursionError
    xảy ra (agent luôn raise ngay), KHÔNG verify _AGENT_RECURSION_LIMIT
    (src/agents/graph.py) có thật sự được thread đúng vào config LangGraph
    hay không — 1 dòng gõ sai/xoá nhầm ở đó sẽ không bị bất kỳ test nào ở
    trên bắt được vì chúng không đọc `config`. FIN05-StressTest-Plan-v4 6.2
    ("recursion limit exact-threshold test") — verify WIRING bằng cách bắt
    tham số thật, KHÔNG gọi agent thật lặp đủ 20 vòng (tốn kém, không xác
    định được, và không mang lại giá trị hơn so với verify wiring)."""

    class _State:
        values: dict = {}

    def __init__(self):
        self.last_config: dict | None = None

    def get_state(self, config):
        return self._State()

    def invoke(self, *a, **kw):
        self.last_config = kw.get("config")
        return {"messages": []}


def test_run_agent_turn_threads_configured_recursion_limit_into_langgraph_config(sample_db, monkeypatch):
    import src.agents.graph as graph_module

    agent = _RecursionLimitCapturingAgent()

    def _fake_build_agent(session, *, user_id, customer_name, otp_verified_at, guard=None, model=None):
        return agent

    monkeypatch.setattr(graph_module, "_build_agent", _fake_build_agent)

    graph_module.run_agent_turn(sample_db, user_id="USR-A", message="test")

    assert agent.last_config is not None, "agent.invoke() không được gọi hoặc không truyền config"
    assert agent.last_config.get("recursion_limit") == graph_module._AGENT_RECURSION_LIMIT == 20


class _RecursionBoomAgent:
    """Giả lập agent LangGraph kẹt vòng lặp — get_state() cần cho
    run_agent_turn() tính prev_len TRƯỚC khi gọi invoke()."""

    class _State:
        values: dict = {}

    def get_state(self, config):
        return self._State()

    def invoke(self, *a, **kw):
        raise GraphRecursionError("giả lập vượt quá recursion_limit — vòng lặp tool mơ hồ liên tục")


def test_run_agent_turn_handles_recursion_limit_gracefully(sample_db, monkeypatch):
    import src.agents.graph as graph_module

    def _fake_build_agent(session, *, user_id, customer_name, otp_verified_at, guard=None, model=None):
        return _RecursionBoomAgent()

    monkeypatch.setattr(graph_module, "_build_agent", _fake_build_agent)

    result = graph_module.run_agent_turn(
        sample_db, user_id="USR-A", message="tôi bị chuyển nhầm tiền nhưng không nhớ gì cả"
    )

    # Không crash (không raise ra ngoài), có ticket thật để CSKH nhận diện —
    # KHÔNG bịa số liệu/ngụ ý đã tra ra kết quả.
    assert result["ticket_id"] is not None

    # `is None`, KHÔNG phải `== []`. Đây từng là một test XANH ĐANG BẢO VỆ MỘT
    # LỜI NÓI DỐI: nhánh fallback ném lỗi trước khi đọc được `result["messages"]`,
    # nên hệ thống KHÔNG BIẾT agent đã gọi tool nào. `[]` khẳng định "không tool
    # nào được gọi" — một điều không ai quan sát được. Phân biệt ba trạng thái:
    #     []    -> quan sát thật: agent không gọi tool nào
    #     [...] -> quan sát thật: đây là danh sách
    #     None  -> KHÔNG KHÔI PHỤC ĐƯỢC (nhánh fallback)
    # Tôi đã đo được hậu quả của việc lẫn hai cái đầu: 4/5 bản ghi có tool_calls
    # rỗng KHÔNG hề đi qua fallback, nên `[]` không suy ngược ra fallback được.
    assert result["tool_calls"] is None
    assert "chuyển" in result["reply"].lower() or "chuyên viên" in result["reply"].lower()

    ticket = sample_db.get(Ticket, result["ticket_id"])
    assert ticket is not None
    assert ticket.human_handoff_requested is True


def test_run_agent_turn_recursion_limit_creates_only_one_ticket(sample_db, monkeypatch):
    """Không để lại nhiều ticket mồ côi nếu (giả định) hàm bị gọi lại — kiểm
    tra đơn giản: đúng 1 ticket được tạo cho đúng 1 lần recursion error."""
    import src.agents.graph as graph_module

    def _fake_build_agent(session, *, user_id, customer_name, otp_verified_at, guard=None, model=None):
        return _RecursionBoomAgent()

    monkeypatch.setattr(graph_module, "_build_agent", _fake_build_agent)

    before = sample_db.query(Ticket).count()
    graph_module.run_agent_turn(sample_db, user_id="USR-A", message="test")
    after = sample_db.query(Ticket).count()
    assert after == before + 1
