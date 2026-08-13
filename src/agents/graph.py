"""LangGraph agent cho luồng khiếu nại lõi (PRD §6) — entrypoint duy nhất
`run_agent_turn()`, gọi từ `POST /agent/chat` (src/api/main.py).

Lưu ý API: `langgraph.prebuilt.create_react_agent` đã deprecated ở bản
langgraph 1.2.10/langchain 1.3.14 đang cài — dùng `langchain.agents.create_agent`
thay thế (tham số prompt tên là `system_prompt`, không phải `prompt`)."""
from __future__ import annotations

import datetime as dt
import json
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Any

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.errors import GraphRecursionError
from sqlalchemy.orm import Session

from src.agents.nodes.investigation_log import write_investigation_logs_for_ticket
from src.agents.prompt import build_system_prompt
from src.agents.tools.customer_tools import build_customer_tools
from src.config import (
    AGENT_TURN_TIMEOUT_SECONDS,
    OPENAI_API_KEY,
    OPENAI_MAX_RETRIES,
    OPENAI_MODEL,
    OPENAI_TIMEOUT_SECONDS,
)
from src.db.models import User
from src.db.session import SessionLocal
from src.observability.langchain_callback import OTelTracingCallbackHandler
from src.observability.tracing import get_tracer
from src.services.complaint_intake import flag_human_handoff
from src.tools.base import ToolError

_tracer = get_tracer("fin05.agent")
_logger = logging.getLogger("fin05.agents.graph")

# CONSUME-002 (FIN05_QA_TestCases.jsonl, OWASP LLM10:2025 Unbounded
# Consumption) — mặc định thật của langgraph đang cài (xác nhận trực tiếp
# `langgraph._internal._config.DEFAULT_RECURSION_LIMIT`) là 10007 bước, thực
# chất tương đương KHÔNG có giới hạn (đốt hết ngân sách OpenAI/timeout rất
# lâu trước khi chạm ngưỡng đó nếu agent kẹt vòng lặp gọi tool mơ hồ liên
# tục). 20 đủ cho vài vòng ReAct thật (LLM suy luận + gọi tool xen kẽ), thấp
# hơn nhiều để chặn lặp vô hạn.
_AGENT_RECURSION_LIMIT = 20

# Singleton module-level: agent được build lại mỗi request (session/tools
# gắn với request đó), nhưng checkpointer dùng chung 1 instance nên lịch sử
# hội thoại nối tiếp được qua nhiều request cùng thread_id=user_id. Mất khi
# restart process — chấp nhận được, khớp US-010 "không giữ ngữ cảnh xuyên
# phiên đăng nhập khác nhau" (Brief).
_CHECKPOINTER = MemorySaver()

# Sentinel — phân biệt "không truyền otp_verified_at" (backward-compat: coi như
# vừa xác thực XONG, dùng bởi eval harness/test hiện có vốn giả định "khách đã
# xác thực OTP trước khi vào chat") với "truyền None thật" (current_user thật
# CHƯA TỪNG xác thực — /agent/chat luôn truyền tường minh, xem src/api/main.py).
# Tính "now" lúc GỌI HÀM (không phải lúc module nạp) để không lệch thời gian
# nếu test suite chạy lâu.
_ALWAYS_FRESH = object()


def _build_agent(session: Session, *, user_id: str, customer_name: str, otp_verified_at: float | None):
    model = ChatOpenAI(
        model=OPENAI_MODEL,
        temperature=0.2,
        api_key=OPENAI_API_KEY,
        timeout=OPENAI_TIMEOUT_SECONDS,
        max_retries=OPENAI_MAX_RETRIES,
    )
    tools = build_customer_tools(session, user_id=user_id, otp_verified_at=otp_verified_at)
    system_prompt = build_system_prompt(current_time=dt.datetime.utcnow(), customer_name=customer_name)
    return create_agent(model, tools, system_prompt=system_prompt, checkpointer=_CHECKPOINTER)


def run_agent_turn(
    session: Session,
    *,
    user_id: str,
    message: str,
    thread_id: str | None = None,
    otp_verified_at: float | None = _ALWAYS_FRESH,
) -> dict[str, Any]:
    """`otp_verified_at`: timestamp (epoch giây) lúc xác thực OTP+câu hỏi bảo
    mật gần nhất (src/auth.py) — truyền THẬT từ current_user.otp_verified_at ở
    /agent/chat (src/api/main.py), có thể là None nếu khách CHƯA TỪNG xác thực.
    Không truyền tham số này (mặc định `_ALWAYS_FRESH`) nghĩa là coi như vừa
    xác thực XONG — để KHÔNG phá vỡ eval/golden_set.jsonl + adversarial_set
    hiện có: các case đó vốn giả định "khách đã xác thực OTP trước khi vào
    chat" (đúng câu mở đầu system prompt), không phải kiểm tra luồng OTP —
    luồng OTP thật được test riêng ở tests/test_api/test_otp.py +
    frontend/e2e/auth.spec.ts."""
    if otp_verified_at is _ALWAYS_FRESH:
        otp_verified_at = dt.datetime.utcnow().timestamp()

    user = session.get(User, user_id)
    if user is None:
        raise ToolError(f"user_id không tồn tại: {user_id}")

    agent = _build_agent(
        session, user_id=user_id, customer_name=user.full_name, otp_verified_at=otp_verified_at
    )
    # thread_id mặc định = user_id (hành vi thật, không đổi). eval/_harness.py
    # truyền thread_id riêng biệt mỗi case để cô lập bộ nhớ hội thoại
    # (checkpointer module-level dùng chung — nếu không cô lập, nhiều case
    # cùng user_id trong 1 lần chạy eval sẽ nối tiếp hội thoại của nhau).
    config = {"configurable": {"thread_id": thread_id or user_id}}

    state_before = agent.get_state(config)
    prev_len = len(state_before.values.get("messages", [])) if state_before.values else 0

    # Span gốc "agent_turn" — 1 lượt chat là 1 vòng lặp ReAct nhiều bước (LLM
    # generation + tool call xen kẽ), KHÔNG PHẢI 1 khối duy nhất (Giai đoạn 1
    # checklist observability). `callbacks=[handler]` (KHÔNG dùng
    # `.configurable`) tạo span con cho MỖI vòng gọi LLM/tool bên trong, tự
    # nối cây cha-con qua context OTel hiện hành (span gốc đang active).
    with _tracer.start_as_current_span("agent_turn") as root_span:
        root_span.set_attribute("fin05.user_id", user_id)
        root_span.set_attribute("fin05.thread_id", thread_id or user_id)
        root_span.set_attribute("fin05.otp_verified", otp_verified_at is not None)
        def _invoke():
            return agent.invoke(
                {"messages": [HumanMessage(content=message)]},
                config={
                    **config,
                    "callbacks": [OTelTracingCallbackHandler()],
                    "recursion_limit": _AGENT_RECURSION_LIMIT,
                },
            )

        # AGENT_TURN_TIMEOUT_SECONDS — OPENAI_TIMEOUT_SECONDS chỉ chặn TỪNG
        # lượt gọi OpenAI riêng lẻ; 1 lượt /agent/chat có thể cần NHIỀU lượt
        # gọi xen kẽ với tool (ReAct), nên tổng thời gian vẫn có thể vượt xa
        # (đo thật: 70s cho 1 request) nếu không chặn RIÊNG ở đây. Chạy trong
        # thread riêng để `.result(timeout=...)` trả lỗi có kiểm soát cho
        # client kịp lúc. CỐ Ý KHÔNG dùng `with ThreadPoolExecutor(...) as
        # executor:` — `__exit__` mặc định gọi `shutdown(wait=True)`, tức
        # BLOCK tới khi thread dở xong mới thoát `with`, xoá sạch tác dụng
        # của timeout. `shutdown(wait=False)` khi timeout: không huỷ được
        # lượt gọi OpenAI đang chạy dở bên dưới (Python không kill thread
        # được), nhưng trả quyền điều khiển lại cho client NGAY, không đợi.
        executor = ThreadPoolExecutor(max_workers=1)
        try:
            result = executor.submit(_invoke).result(timeout=AGENT_TURN_TIMEOUT_SECONDS)
            executor.shutdown(wait=True)  # thread thật sự đã xong lúc .result() trả về, wait=True không tốn gì thêm
        except (GraphRecursionError, FutureTimeoutError) as e:
            # wait=False luôn an toàn ở đây: nếu thread đã xong (nhánh
            # GraphRecursionError) thì trả về ngay lập tức; nếu chưa (nhánh
            # timeout thật) thì không chờ, đúng mục đích.
            executor.shutdown(wait=False)
            # Vòng lặp ReAct vượt quá _AGENT_RECURSION_LIMIT HOẶC vượt trần
            # thời gian tổng (thật sự xảy ra — không phải lý thuyết, xem case
            # CONSUME-002) — KHÔNG để lỗi rơi ra ngoài thành 500, chuyển hẳn
            # cho người xử lý thay vì treo vô thời hạn/crash. root_span vẫn
            # ghi nhận đúng (context manager tự đóng dù có exception), chỉ
            # không có span con của lượt hỏng.
            is_timeout = isinstance(e, FutureTimeoutError)
            _logger.warning(
                "agent_turn_timeout" if is_timeout else "agent_recursion_limit_reached",
                extra={"user_id": user_id, "thread_id": thread_id or user_id},
            )
            root_span.set_attribute("fin05.recursion_limit_reached", not is_timeout)
            root_span.set_attribute("fin05.turn_timeout", is_timeout)
            if is_timeout:
                # KHÔNG dùng `session` dùng chung ở đây — thread nền (_invoke)
                # vẫn có thể đang chạy dở, cầm session đó cho 1 tool call
                # (SQLAlchemy Session không an toàn khi 2 thread cùng đụng
                # 1 lúc, khác nhánh GraphRecursionError bên dưới — nhánh đó
                # invoke() đã CHẮC CHẮN trả về xong, không còn thread nào
                # khác đụng session). Mở session RIÊNG, tự commit/đóng.
                with SessionLocal() as timeout_session:
                    handoff = flag_human_handoff(
                        timeout_session,
                        user_id=user_id,
                        reason="Hệ thống AI gặp khó khăn khi xử lý yêu cầu này (vòng lặp tra cứu không ra kết quả rõ ràng) — cần chuyên viên hỗ trợ trực tiếp.",
                    )
                    timeout_session.commit()
            else:
                handoff = flag_human_handoff(
                    session,
                    user_id=user_id,
                    reason="Hệ thống AI gặp khó khăn khi xử lý yêu cầu này (vòng lặp tra cứu không ra kết quả rõ ràng) — cần chuyên viên hỗ trợ trực tiếp.",
                )
            return {
                "reply": "Mình chưa tra được yêu cầu này, để mình chuyển cho chuyên viên hỗ trợ trực tiếp nhé — mã ticket của bạn là "
                + handoff["ticket_id"]
                + ".",
                "tool_calls": [],
                "ticket_id": handoff["ticket_id"],
                "should_escalate": False,
                "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            }
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

    # Token usage cộng dồn của LƯỢT NÀY (mọi vòng gọi model bên trong, kể cả
    # vòng gọi tool trung gian) — dùng để đo cost thật (eval/measure_quality.py),
    # KHÔNG ảnh hưởng contract cũ (chỉ thêm key mới, không đổi key sẵn có).
    usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    for m in turn_messages:
        meta = isinstance(m, AIMessage) and getattr(m, "usage_metadata", None)
        if meta:
            for k in usage:
                usage[k] += meta.get(k, 0) or 0

    return {
        "reply": reply,
        "tool_calls": tool_calls_out,
        "ticket_id": ticket_id,
        "should_escalate": should_escalate,
        "usage": usage,
    }
