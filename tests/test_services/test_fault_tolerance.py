"""Nhóm D4/D5 — mô phỏng lỗi hệ thống ngoài (tool bên ngoài chậm/lỗi, DB mất
kết nối, OpenAI lỗi) bằng `monkeypatch` — nhanh, xác định, không cần dựng hạ
tầng chaos (Toxiproxy) thật. Kiểm agent xử lý graceful: không bịa số liệu
thay thế, không để lộ traceback nội bộ, DB rollback sạch (không ticket dở
dang) khi lỗi xảy ra giữa chừng.
"""
from __future__ import annotations

import datetime as dt

import pytest

from src.agents.tools.customer_tools import build_customer_tools
from src.db.models import Complaint, Ticket
from src.services.complaint_intake import create_ticket_with_fraud_check
from src.tools.base import ToolError

_FRESH_OTP = dt.datetime.utcnow().timestamp()  # test D4/D5 kiểm lỗi hệ thống
# ngoài, không phải luồng OTP (đã có tests/test_api/test_otp.py riêng) — cần
# khách "đã xác thực" để không bị chặn OTP che lấp lỗi đang test.

# ---------------------------------------------------------------------------
# D4 — tool bên ngoài (lookup_transaction/get_customer_history) lỗi/timeout.
# Wrapper trong customer_tools.py hiện chỉ bắt ToolError — test này xác nhận
# rõ điều đó (và phát hiện nếu lỗi hệ thống khác lọt qua, không bị bịa im lặng).
# ---------------------------------------------------------------------------


def test_lookup_transaction_tool_error_returns_graceful_dict(sample_db, monkeypatch):
    tools = build_customer_tools(sample_db, user_id="USR-A", otp_verified_at=_FRESH_OTP)
    lookup = next(t for t in tools if t.name == "lookup_transaction")

    def _raise_tool_error(*args, **kwargs):
        raise ToolError("giả lập ngân hàng đối tác timeout")

    monkeypatch.setattr("src.agents.tools.customer_tools._lookup_transaction", _raise_tool_error)
    result = lookup.invoke({"trans_id": "TXN-0001"})

    # Trả về dict lỗi rõ ràng cho LLM tự diễn đạt lại, KHÔNG raise làm sập cả
    # lượt chat, KHÔNG có số liệu bịa nào trong kết quả.
    assert result["status"] == "error"
    assert "timeout" in result["message"].lower() or "giả lập" in result["message"]


def test_lookup_transaction_unexpected_exception_is_not_silently_swallowed(sample_db, monkeypatch):
    """Lỗi hệ thống KHÔNG PHẢI ToolError (vd TimeoutError/ConnectionError thật
    từ 1 dependency ngoài) — xác nhận hành vi THẬT của wrapper (không bắt được
    ToolError khác nhóm), để biết rõ giới hạn thay vì giả định đã xử lý hết."""
    tools = build_customer_tools(sample_db, user_id="USR-A", otp_verified_at=_FRESH_OTP)
    lookup = next(t for t in tools if t.name == "lookup_transaction")

    def _raise_connection_error(*args, **kwargs):
        raise ConnectionError("ngân hàng đối tác mất kết nối")

    monkeypatch.setattr("src.agents.tools.customer_tools._lookup_transaction", _raise_connection_error)

    # Ghi nhận hành vi thật: wrapper chỉ bắt ToolError (xem customer_tools.py)
    # — lỗi hệ thống khác (ConnectionError...) sẽ propagate lên trên, KHÔNG bị
    # nuốt âm thầm thành 1 kết quả trông như hợp lệ. Đây là hành vi AN TOÀN
    # (thà lộ lỗi rõ ràng còn hơn agent bịa tiếp) nhưng đồng nghĩa tầng gọi
    # (run_agent_turn/route FastAPI) phải tự chịu trách nhiệm không lộ
    # traceback cho khách — xem test_agent_chat_route_does_not_leak_traceback.
    with pytest.raises(ConnectionError):
        lookup.invoke({"trans_id": "TXN-0001"})


# ---------------------------------------------------------------------------
# D5 — dependency failure: OpenAI API lỗi giữa lượt chat.
# ---------------------------------------------------------------------------


def test_run_agent_turn_propagates_openai_error_without_partial_ticket(sample_db, monkeypatch):
    """OpenAI API lỗi (rate limit/500) giữa lượt chat — không được để lại
    ticket/complaint dở dang trong DB (agent chưa kịp gọi create_ticket)."""
    import src.agents.graph as graph_module

    class _BoomModel:
        def bind_tools(self, *a, **kw):
            return self

        def invoke(self, *a, **kw):
            raise RuntimeError("giả lập OpenAI API lỗi 500")

    def _boom_build_agent(session, *, user_id, customer_name, otp_verified_at, guard=None):
        raise RuntimeError("giả lập OpenAI API lỗi 500")

    monkeypatch.setattr(graph_module, "_build_agent", _boom_build_agent)

    before = sample_db.query(Ticket).count()
    with pytest.raises(RuntimeError):
        graph_module.run_agent_turn(sample_db, user_id="USR-A", message="tôi bị chuyển nhầm tiền")
    sample_db.rollback()  # mô phỏng đúng hành vi get_session() thật (src/api/deps.py) khi exception raise

    after = sample_db.query(Ticket).count()
    assert after == before, "Lỗi OpenAI giữa chừng không được để lại ticket dở dang"


# ---------------------------------------------------------------------------
# D5 — DB lỗi giữa chừng khi đang tạo ticket — rollback sạch, không complaint
# mồ côi (complaint có mà ticket không, hoặc ngược lại).
# ---------------------------------------------------------------------------


def test_create_ticket_db_error_mid_transaction_rolls_back_cleanly(sample_db, monkeypatch):
    complaints_before = sample_db.query(Complaint).count()
    tickets_before = sample_db.query(Ticket).count()

    original_add = sample_db.add
    call_count = {"n": 0}

    def _add_then_boom(obj):
        call_count["n"] += 1
        original_add(obj)
        # Ticket luôn được add SAU Complaint (complaint_intake.py) — cho nổ
        # đúng lúc chuẩn bị add Ticket để mô phỏng DB chết giữa 2 bước ghi.
        if isinstance(obj, Ticket):
            raise RuntimeError("giả lập DB mất kết nối giữa transaction")

    monkeypatch.setattr(sample_db, "add", _add_then_boom)

    with pytest.raises(RuntimeError):
        create_ticket_with_fraud_check(
            sample_db,
            user_id="USR-A",
            complaint_type="wrong_recipient",
            scope="internal_wallet",
            description_raw="test fault tolerance",
            trans_id="TXN-0001",
        )
    sample_db.rollback()

    # Không để lại Complaint mồ côi (không có Ticket đi kèm) — get_session()
    # thật (src/api/deps.py) rollback toàn bộ request khi exception raise,
    # test này xác nhận đúng invariant đó ở tầng service.
    assert sample_db.query(Complaint).count() == complaints_before
    assert sample_db.query(Ticket).count() == tickets_before


# ---------------------------------------------------------------------------
# AGENT_TURN_TIMEOUT_SECONDS (đo đạc + vá 2026-08-13) — 1 lượt /agent/chat có
# thể cần nhiều lượt gọi OpenAI xen kẽ tool (ReAct), đo thật thấy 1 request
# tốn tới 70s dưới tải đồng thời (nhiều lượt LLM thật dồn dập trong stress
# test). OPENAI_TIMEOUT_SECONDS chỉ chặn TỪNG lượt gọi OpenAI riêng lẻ —
# test này xác nhận có 1 trần TỔNG THẬT SỰ áp dụng cho agent.invoke().
# ---------------------------------------------------------------------------


def test_run_agent_turn_times_out_gracefully_instead_of_hanging(sample_db, monkeypatch):
    """agent.invoke() "treo" lâu hơn AGENT_TURN_TIMEOUT_SECONDS -> run_agent_turn
    phải TRẢ VỀ (không đợi hết) với reply handoff người thật, không hang vô
    thời hạn, không rơi thành 500."""
    import time

    import src.agents.graph as graph_module

    monkeypatch.setattr(graph_module, "AGENT_TURN_TIMEOUT_SECONDS", 0.3)
    # QA-10 (13/08): KHÔNG monkeypatch SessionLocal nữa — bản vá làm nhánh
    # timeout mở session mới trên ĐÚNG engine được tiêm. Monkeypatch cũ chính
    # là thứ che mất lỗ hổng: test xanh trong khi chạy thật (eval harness,
    # không monkeypatch) ticket rơi vào DB mặc định của app. Assert cuối hàm
    # giờ là lưới hồi quy thật cho QA-10 — bỏ DI đi là nó đỏ ngay.

    class _HangingModel:
        def bind_tools(self, *a, **kw):
            return self

        def invoke(self, *a, **kw):
            time.sleep(2.0)  # > AGENT_TURN_TIMEOUT_SECONDS (0.3s) đã monkeypatch ở trên
            raise AssertionError("không được chạy tới đây — .result(timeout=...) đã trả lỗi trước")

    class _FakeAgent:
        def get_state(self, config):
            from types import SimpleNamespace

            return SimpleNamespace(values={})

        def invoke(self, *a, **kw):
            return _HangingModel().invoke()

    def _fake_build_agent(session, *, user_id, customer_name, otp_verified_at, guard=None, model=None):
        return _FakeAgent()

    monkeypatch.setattr(graph_module, "_build_agent", _fake_build_agent)

    tickets_before = sample_db.query(Ticket).count()
    start = time.monotonic()
    result = graph_module.run_agent_turn(sample_db, user_id="USR-A", message="tôi bị chuyển nhầm tiền")
    elapsed = time.monotonic() - start

    assert elapsed < 1.5, (
        f"run_agent_turn phải trả về ngay sau AGENT_TURN_TIMEOUT_SECONDS (0.3s), "
        f"không đợi hết .invoke() giả lập (2s) — mất {elapsed:.2f}s, cho thấy timeout không có tác dụng"
    )
    assert "chuyên viên hỗ trợ trực tiếp" in result["reply"]
    assert result["ticket_id"]

    # QA-10: ticket handoff ghi qua session RIÊNG (thread-safe) nhưng trên
    # ĐÚNG engine được tiêm — nên sample_db phải thấy được sau commit. Nếu
    # nhánh timeout quay lại dùng DB mặc định của app, count không tăng và
    # test đỏ.
    sample_db.expire_all()
    assert sample_db.query(Ticket).count() == tickets_before + 1
