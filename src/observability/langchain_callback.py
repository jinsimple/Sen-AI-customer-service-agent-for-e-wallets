"""Callback handler LangChain -> OTel Span — Giai đoạn 1 checklist
observability: agent là 1 vòng lặp ReAct (LLM sinh -> tool call -> LLM đọc
kết quả -> ...), KHÔNG PHẢI 1 khối "process_request" duy nhất. Mỗi lượt gọi
LLM VÀ mỗi tool call là 1 Span con của span gốc "agent_turn" (mở ở
src/agents/graph.py::run_agent_turn) — nối cây cha-con qua context OTel hiện
hành (KHÔNG tự quản lý parent_id tay), tự đóng đúng nhờ context manager.

Span LLM đánh dấu rõ là "generation" (`gen_ai.*` attributes theo GenAI
Semantic Conventions chuẩn của OTel — KHÔNG tự đặt tên field tuỳ ý, xem
checklist Giai đoạn 4) — khác biệt với span tool thường (không cần
token/cost). Toàn bộ text tự do (prompt/tool input-output) bị `scrub_pii()`
TRƯỚC KHI gắn vào span attribute — scrub PHẢI chạy trước khi rời khỏi
process, không phải sau khi đã gửi lên Jaeger."""
from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import BaseMessage, SystemMessage
from opentelemetry import context as otel_context
from opentelemetry import trace
from opentelemetry.trace import Span, StatusCode

from src.observability.pii import scrub_pii
from src.observability.tracing import get_tracer

_MAX_ATTR_LEN = 1000  # cắt bớt input/output dài — span attribute không phải kho lưu trữ

# Biên an toàn: scrub dư ra một khúc trước khi cắt về _MAX_ATTR_LEN, để một cái
# tên nằm VẮT NGANG mốc 1000 vẫn nằm trọn trong vùng được NER quét. Thiếu biên
# này thì nửa đầu cái tên có thể lọt vào span mà lớp NER không nhận ra (nó chỉ
# thấy một mảnh cụt).
_SCRUB_WINDOW = _MAX_ATTR_LEN + 200


def _truncate(text: str) -> str:
    return text if len(text) <= _MAX_ATTR_LEN else text[:_MAX_ATTR_LEN] + "…(cắt bớt)"


def _scrub_and_truncate(text: str) -> str:
    """CẮT TRƯỚC, SCRUB SAU — không phải ngược lại.

    Thứ tự cũ (scrub toàn bộ rồi mới cắt còn 1.000 ký tự) trả giá NER cho cả
    khúc văn bản chắc chắn bị vứt đi. Chi phí `scrub_pii` tăng theo BẬC HAI
    của độ dài — đo thật trong container (2026-08-14):

        1.200 ký tự →  0,24s        4.000 ký tự →  2,29s
        2.000 ký tự →  0,58s        8.000 ký tự →  8,54s
                       19.800 ký tự → 50,07s

    Callback này chạy cho MỖI lượt gọi LLM (prompt = cả hội thoại) và MỖI tool
    call trong vòng lặp ReAct, nên một lượt chat trả giá đó nhiều lần. Đây mới
    là nguồn latency thật, KHÔNG phải lớp bảo vệ PII của ADR-010 (lớp đó là
    `scrub_pii` trên tin nhắn khách — vài chục ký tự, 0,025s — và
    `_scrub_pii_cho_llm` che theo trường, không dùng NER).

    KHÔNG hạ thấp mức bảo vệ: mọi ký tự THẬT SỰ nằm trong span attribute vẫn đi
    qua đủ pipeline scrub. Phần bị cắt không vào span, nên không có gì rời khỏi
    process mà chưa được che — đúng yêu cầu "scrub trước khi rời process" của
    ADR-010, chỉ bỏ phần tính toán vô ích.
    """
    da_cat = len(text) > _SCRUB_WINDOW
    # GĐ4 (Bảo Mật 19/08): muc_dich="log" — trace/span, registry ĐẦY ĐỦ,
    # hành vi KHÔNG đổi so với trước. Xem docstring src/observability/pii.py.
    scrubbed = scrub_pii(text[:_SCRUB_WINDOW], muc_dich="log") or ""
    if len(scrubbed) > _MAX_ATTR_LEN:
        return scrubbed[:_MAX_ATTR_LEN] + "…(cắt bớt)"
    return scrubbed + "…(cắt bớt)" if da_cat else scrubbed


class OTelTracingCallbackHandler(BaseCallbackHandler):
    """1 instance DÙNG RIÊNG cho ĐÚNG 1 lượt `agent.invoke()` (tạo mới mỗi
    lượt trong run_agent_turn, giống cách build_customer_tools() đã tạo mới
    mỗi request) — `_spans` keyed theo run_id (UUID LangChain tự sinh, duy
    nhất mỗi lượt gọi con), không chia sẻ state giữa các lượt/request khác
    nhau."""

    def __init__(self) -> None:
        self._tracer = get_tracer("fin05.agent")
        self._spans: dict[UUID, tuple[Span, Any]] = {}  # run_id -> (span, otel_context_token)

    def _start_span(self, run_id: UUID, name: str, attributes: dict[str, Any]) -> None:
        span = self._tracer.start_span(name, attributes=attributes)
        ctx = trace.set_span_in_context(span)
        token = otel_context.attach(ctx)
        self._spans[run_id] = (span, token)

    def _end_span(self, run_id: UUID, *, error: BaseException | None = None, extra_attrs: dict[str, Any] | None = None) -> None:
        entry = self._spans.pop(run_id, None)
        if entry is None:
            return
        span, token = entry
        if extra_attrs:
            for k, v in extra_attrs.items():
                span.set_attribute(k, v)
        if error is not None:
            # S-03 — CHUỖI LỖI PHẢI QUA SCRUB, y hệt mọi text khác trong file
            # này (prompt :125, completion :151, tool args :180, tool output
            # :191). Trước bản này đây là NGOẠI LỆ DUY NHẤT giữa bốn tiền lệ
            # nhất quán: `str(error)` và `record_exception` đi thẳng ra backend
            # trace, không qua một lớp che nào.
            #
            # Vì sao chưa từng lộ ra trong test: test dùng SQLite, nó chỉ trả
            # "FOREIGN KEY constraint failed" — không echo tham số. Postgres
            # (bản chạy production) CÓ echo:
            #     DETAIL: Key (phone)=(0912345678) already exists.
            # ⟹ đúng lớp lỗi chỉ hiện ra SAU khi deploy thật, trên môi trường
            # không ai chạy test. Không có ca dương tính hôm nay không có
            # nghĩa là không có lỗ.
            span.set_status(StatusCode.ERROR, _scrub_and_truncate(str(error)))
            # `record_exception` tự dựng attribute `exception.message` +
            # `exception.stacktrace` từ chính object exception — KHÔNG có cách
            # nào chèn scrub vào giữa. Nên ghi TAY một sự kiện tương đương với
            # nội dung đã che, và KHÔNG gọi record_exception nữa: giữ cả hai
            # thì bản đã che chỉ là lớp trang trí cạnh bản thô.
            span.add_event(
                "exception",
                {
                    "exception.type": type(error).__name__,
                    "exception.message": _scrub_and_truncate(str(error)),
                    "exception.escaped": "false",
                },
            )
        span.end()
        otel_context.detach(token)

    # --- LLM generation spans (gen_ai.* — GenAI Semantic Conventions) -----

    def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[BaseMessage]],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        # `serialized["kwargs"]["model_name"]` — KHÔNG phải "model" (phát hiện
        # thật lúc verify trace trên Jaeger: field sai tên khiến span luôn
        # ghi "ChatOpenAI" — tên CLASS — thay vì "gpt-4o-mini" thật).
        model = (serialized.get("kwargs") or {}).get("model_name") or serialized.get("name") or "unknown"
        # CHỈ đưa message KHÔNG PHẢI system prompt vào preview — system prompt
        # là văn bản TĨNH do dev viết (src/agents/prompt.py), không chứa PII
        # khách hàng, và lặp lại y hệt ở MỌI span khiến trace khó đọc. Phát
        # hiện thật lúc verify: scrub PII (đúng, cần thiết cho message THẬT
        # của khách/tool) chạy trên system prompt làm nó vụn thành chuỗi
        # "[NAME]" rải rác, không đọc lại được — hại debug mà không có lợi ích
        # bảo mật nào (system prompt vốn không có PII để che).
        flat = [m for batch in messages for m in batch if not isinstance(m, SystemMessage)]
        prompt_preview = _scrub_and_truncate(" | ".join(m.content if isinstance(m.content, str) else str(m.content) for m in flat))
        self._start_span(
            run_id,
            "gen_ai.generation",
            {
                "gen_ai.system": "openai",
                "gen_ai.request.model": model,
                "gen_ai.operation.name": "chat",
                "gen_ai.prompt.preview": prompt_preview,
            },
        )

    def on_llm_end(self, response: Any, *, run_id: UUID, **kwargs: Any) -> None:
        usage = {}
        try:
            gen = response.generations[0][0]
            msg = getattr(gen, "message", None)
            if msg is not None and getattr(msg, "usage_metadata", None):
                usage = msg.usage_metadata
            elif response.llm_output and "token_usage" in response.llm_output:
                tu = response.llm_output["token_usage"]
                usage = {
                    "input_tokens": tu.get("prompt_tokens", 0),
                    "output_tokens": tu.get("completion_tokens", 0),
                    "total_tokens": tu.get("total_tokens", 0),
                }
            completion_preview = _scrub_and_truncate(getattr(gen, "text", "") or "")
        except (IndexError, AttributeError):
            completion_preview = ""

        self._end_span(
            run_id,
            extra_attrs={
                "gen_ai.usage.input_tokens": usage.get("input_tokens", 0),
                "gen_ai.usage.output_tokens": usage.get("output_tokens", 0),
                "gen_ai.completion.preview": completion_preview,
            },
        )

    def on_llm_error(self, error: BaseException, *, run_id: UUID, **kwargs: Any) -> None:
        self._end_span(run_id, error=error)

    # --- Tool call spans ----------------------------------------------

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        inputs: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        tool_name = serialized.get("name", "unknown_tool")
        args_preview = _scrub_and_truncate(json.dumps(inputs, ensure_ascii=False, default=str) if inputs else input_str)
        self._start_span(run_id, f"tool.{tool_name}", {"tool.name": tool_name, "tool.input.preview": args_preview})

    def on_tool_end(self, output: Any, *, run_id: UUID, **kwargs: Any) -> None:
        # LangGraph bọc kết quả tool thành ToolMessage trước khi gọi callback
        # (khác `.invoke()` gọi tool trực tiếp trả thẳng dict/str) — phát hiện
        # thật lúc verify trace trên Jaeger: thiếu unwrap `.content` khiến
        # preview chỉ hiện repr Pydantic ("content='...' additional_kwargs=...")
        # thay vì JSON đọc được.
        content = getattr(output, "content", output)
        output_str = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False, default=str)
        self._end_span(run_id, extra_attrs={"tool.output.preview": _scrub_and_truncate(output_str)})

    def on_tool_error(self, error: BaseException, *, run_id: UUID, **kwargs: Any) -> None:
        self._end_span(run_id, error=error)
