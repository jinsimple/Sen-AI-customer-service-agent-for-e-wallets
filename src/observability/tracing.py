"""OpenTelemetry setup — Giai đoạn 1+4 checklist observability. Chọn OTel
(không phải Langfuse) vì đây là chuẩn quốc tế trung lập (CNCF), tự host được
(Jaeger, docker-compose.yml service `jaeger`) — dữ liệu KHÔNG rời khỏi hạ
tầng nội bộ, phù hợp dữ liệu giao dịch/khách hàng của ví điện tử (xem quyết
định 2026-08-10).

`configure_tracing()` PHẢI graceful-degrade khi collector (Jaeger) không sống
— BatchSpanProcessor tự nuốt lỗi export ở background thread theo đúng spec
OTel (xem test_tracing.py::test_tracing_does_not_crash_when_collector_unreachable),
KHÔNG được để thiếu observability backend làm sập tính năng nghiệp vụ chính."""
from __future__ import annotations

import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

_SERVICE_NAME = "fin05-backend"
_SERVICE_VERSION = "0.1.0"

_configured = False


def configure_tracing() -> None:
    """Idempotent. Endpoint đọc từ `OTEL_EXPORTER_OTLP_ENDPOINT` (mặc định
    `localhost:4317` — cổng OTLP gRPC của Jaeger, xem docker-compose.yml)."""
    global _configured
    if _configured:
        return
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317")
    resource = Resource.create({SERVICE_NAME: _SERVICE_NAME, SERVICE_VERSION: _SERVICE_VERSION})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
    # BatchSpanProcessor — gửi theo lô (không fire-and-forget từng span), đúng
    # Giai đoạn 4: tránh overhead network dồn dập khi traffic cao.
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    _configured = True


def get_tracer(name: str):
    return trace.get_tracer(name)


def instrument_fastapi_app(app) -> None:  # noqa: ANN001
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    FastAPIInstrumentor.instrument_app(app)
