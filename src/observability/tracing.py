"""OpenTelemetry setup — phases 1+4 of the observability checklist. OTel was chosen
(over Langfuse) because it is a vendor-neutral international standard (CNCF) and can be
self-hosted (Jaeger, docker-compose.yml service `jaeger`) — data NEVER leaves the
internal infrastructure, which suits e-wallet transaction/customer data (see the
2026-08-10 decision).

`configure_tracing()` MUST degrade gracefully when the collector (Jaeger) is down
— BatchSpanProcessor swallows export errors on its background thread, as the OTel spec
requires (see test_tracing.py::test_tracing_does_not_crash_when_collector_unreachable).
A missing observability backend must NEVER take down core business features."""
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
    """Idempotent. Endpoint is read from `OTEL_EXPORTER_OTLP_ENDPOINT` (default
    `localhost:4317` — Jaeger's OTLP gRPC port, see docker-compose.yml)."""
    global _configured
    if _configured:
        return
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317")
    resource = Resource.create({SERVICE_NAME: _SERVICE_NAME, SERVICE_VERSION: _SERVICE_VERSION})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
    # BatchSpanProcessor — exports in batches (not fire-and-forget per span), per
    # phase 4: avoids bursts of network overhead under high traffic.
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    _configured = True


def get_tracer(name: str):
    return trace.get_tracer(name)


def instrument_fastapi_app(app) -> None:  # noqa: ANN001
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    FastAPIInstrumentor.instrument_app(app)
