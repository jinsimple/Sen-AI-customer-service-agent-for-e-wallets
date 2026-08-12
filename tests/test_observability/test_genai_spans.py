"""FIN05-StressTest-Plan-v2 ST2-F-06 (docs/FIN05-Feature-Inventory-Security-
Review.md §8) — span LLM (`OTelTracingCallbackHandler`,
src/observability/langchain_callback.py) phải gắn đủ attribute theo GenAI
Semantic Conventions chuẩn (`gen_ai.system`, `gen_ai.request.model`,
`gen_ai.usage.input_tokens`/`output_tokens`) — regression bảo vệ đúng field
name đã từng sai 1 lần thật (comment trong file: `model_name` chứ không phải
`model`, phát hiện lúc verify trace trên Jaeger, span luôn ghi "ChatOpenAI"
— tên CLASS — thay vì "gpt-4o-mini" thật).

KHÔNG dùng global tracer provider (`trace.get_tracer_provider()`) — module
`src/api/main.py:96` gọi `configure_tracing()` NGAY LÚC IMPORT, và OTel API
chỉ cho set global provider ĐÚNG 1 LẦN (lần gọi sau bị bỏ qua âm thầm) — hầu
hết test khác trong suite đều import `src.api.main` (qua TestClient) TRƯỚC
file này chạy, nên global provider luôn đã bị "khoá" vào bản thật (xuất
OTLP ra Jaeger). Tạo `TracerProvider` RIÊNG + `InMemorySpanExporter` rồi
monkeypatch thẳng `get_tracer` trong module đích — không đụng global API."""
from __future__ import annotations

from uuid import uuid4

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

import src.observability.langchain_callback as callback_module


def _build_isolated_handler(monkeypatch) -> tuple[callback_module.OTelTracingCallbackHandler, InMemorySpanExporter]:
    # tests/conftest.py set OTEL_SDK_DISABLED=true (chống spam lỗi export
    # thật khi chạy suite không có Jaeger sống) — cờ này khiến TracerProvider
    # (kể cả instance tự tạo riêng ở đây, KHÔNG chỉ provider global) luôn
    # trả no-op tracer, span không bao giờ export (phát hiện thật lúc viết
    # test này: 0 span dù code chạy không lỗi). Phải bật lại CHỈ trong scope
    # test này.
    monkeypatch.setenv("OTEL_SDK_DISABLED", "false")
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    isolated_tracer = provider.get_tracer("test.fin05.agent")

    monkeypatch.setattr(callback_module, "get_tracer", lambda name: isolated_tracer)
    handler = callback_module.OTelTracingCallbackHandler()
    return handler, exporter


class _FakeMessage:
    def __init__(self, content: str, usage_metadata: dict | None = None):
        self.content = content
        self.usage_metadata = usage_metadata


class _FakeGeneration:
    def __init__(self, text: str, message):
        self.text = text
        self.message = message


class _FakeLLMResult:
    def __init__(self, generations, llm_output=None):
        self.generations = generations
        self.llm_output = llm_output


def test_llm_generation_span_has_genai_semantic_convention_attributes(monkeypatch):
    from langchain_core.messages import HumanMessage

    handler, exporter = _build_isolated_handler(monkeypatch)
    run_id = uuid4()

    handler.on_chat_model_start(
        {"kwargs": {"model_name": "gpt-4o-mini"}},
        [[HumanMessage(content="khách hỏi giao dịch của tôi")]],
        run_id=run_id,
    )
    result = _FakeLLMResult(
        generations=[[_FakeGeneration("mình đã tra xong", _FakeMessage("mình đã tra xong", {"input_tokens": 42, "output_tokens": 7}))]],
    )
    handler.on_llm_end(result, run_id=run_id)

    spans = exporter.get_finished_spans()
    assert len(spans) == 1, f"Kỳ vọng đúng 1 span generation, có {len(spans)}"
    span = spans[0]

    assert span.name == "gen_ai.generation"
    attrs = dict(span.attributes)
    assert attrs["gen_ai.system"] == "openai"
    assert attrs["gen_ai.request.model"] == "gpt-4o-mini", (
        "Phải đọc serialized['kwargs']['model_name'], KHÔNG phải "
        "serialized['name'] (tên class 'ChatOpenAI') — đúng bug thật đã "
        "từng xảy ra, xem docstring module."
    )
    assert attrs["gen_ai.operation.name"] == "chat"
    assert attrs["gen_ai.usage.input_tokens"] == 42
    assert attrs["gen_ai.usage.output_tokens"] == 7


def test_llm_generation_span_falls_back_to_serialized_name_when_model_name_missing(monkeypatch):
    """Không crash nếu serialized thiếu 'kwargs'/'model_name' (LangChain đổi
    cấu trúc serialized ở version khác) — vẫn ra được 1 giá trị nào đó thay
    vì raise KeyError giữa lượt chat thật của khách."""
    from langchain_core.messages import HumanMessage

    handler, exporter = _build_isolated_handler(monkeypatch)
    run_id = uuid4()

    handler.on_chat_model_start({"name": "ChatOpenAI"}, [[HumanMessage(content="hi")]], run_id=run_id)
    handler.on_llm_end(_FakeLLMResult(generations=[[_FakeGeneration("ok", _FakeMessage("ok"))]]), run_id=run_id)

    spans = exporter.get_finished_spans()
    assert dict(spans[0].attributes)["gen_ai.request.model"] == "ChatOpenAI"
