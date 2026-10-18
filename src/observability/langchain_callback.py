"""LangChain callback handler -> OTel Span — phase 1 of the observability checklist: the
agent is a ReAct loop (LLM generates -> tool call -> LLM reads the result -> ...), NOT a
single "process_request" block. Every LLM call AND every tool call is a child Span of the
root span "agent_turn" (opened in src/agents/graph.py::run_agent_turn) — the parent/child
tree is linked through the current OTel context (NO manual parent_id management), and spans
close correctly via context managers.

LLM spans are clearly marked as "generation" (`gen_ai.*` attributes per the standard OTel
GenAI Semantic Conventions — NO ad-hoc field names, see phase 4 of the checklist) — distinct
from ordinary tool spans (no token/cost needed). All free text (prompt/tool input-output)
goes through `scrub_pii()` BEFORE being attached as a span attribute — scrubbing MUST happen
before leaving the process, not after it has been sent to Jaeger."""
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

_MAX_ATTR_LEN = 1000  # truncate long input/output — span attributes are not a storage system

# Safety margin: scrub a bit beyond _MAX_ATTR_LEN before truncating, so a name straddling
# the 1000 mark still lies entirely within the region NER scans. Without this margin, the
# first half of a name could leak into the span without the NER layer recognising it (it would
# only see a truncated fragment).
_SCRUB_WINDOW = _MAX_ATTR_LEN + 200


def _truncate(text: str) -> str:
    return text if len(text) <= _MAX_ATTR_LEN else text[:_MAX_ATTR_LEN] + "…(cắt bớt)"


def _scrub_and_truncate(text: str) -> str:
    """TRUNCATE FIRST, SCRUB SECOND — not the other way round.

    The old order (scrub everything, then truncate to 1,000 characters) paid NER costs for a
    chunk of text that was certainly going to be thrown away. `scrub_pii` cost grows
    QUADRATICALLY with length — measured in the container (2026-08-14):

        1,200 chars →  0.24s        4,000 chars →  2.29s
        2,000 chars →  0.58s        8,000 chars →  8.54s
                       19,800 chars → 50.07s

    This callback runs for EVERY LLM call (prompt = the whole conversation) and EVERY tool
    call in the ReAct loop, so one chat turn pays that cost many times. This was the real
    source of latency, NOT the PII protection layer of ADR-010 (that layer is `scrub_pii` on
    the customer message — a few dozen characters, 0.025s — and
    `_scrub_pii_for_llm`, which masks by field without NER).

    Protection is NOT reduced: every character that ACTUALLY ends up in a span attribute still
    goes through the full scrub pipeline. The truncated part never enters the span, so nothing
    leaves the process unmasked — exactly ADR-010's "scrub before leaving the process"
    requirement, minus the wasted computation.
    """
    trimmed = len(text) > _SCRUB_WINDOW
    # Phase 4 (Security 19/08): purpose="log" — traces/spans, FULL registry,
    # behaviour UNCHANGED from before. See the src/observability/pii.py docstring.
    scrubbed = scrub_pii(text[:_SCRUB_WINDOW], purpose="log") or ""
    if len(scrubbed) > _MAX_ATTR_LEN:
        return scrubbed[:_MAX_ATTR_LEN] + "…(cắt bớt)"
    return scrubbed + "…(cắt bớt)" if trimmed else scrubbed


class OTelTracingCallbackHandler(BaseCallbackHandler):
    """One instance DEDICATED to EXACTLY one `agent.invoke()` turn (created fresh each turn in
    run_agent_turn, just as build_customer_tools() is created fresh per request) — `_spans`
    is keyed by run_id (a UUID LangChain generates, unique per child call), so no state is
    shared between different turns/requests."""

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
            # S-03 — ERROR STRINGS MUST BE SCRUBBED, exactly like every other text in this file
            # (prompt :125, completion :151, tool args :180, tool output
            # :191). Before this version it was the ONLY EXCEPTION among four consistent precedents:
            # `str(error)` and `record_exception` went straight to the trace backend, through no
            # masking
            # layer at all.
            #
            # Why it never surfaced in tests: tests use SQLite, which only returns
            # "FOREIGN KEY constraint failed" — it doesn't echo parameters. Postgres
            # (the production database) DOES echo them:
            #     DETAIL: Key (phone)=(0912345678) already exists.
            # ⟹ exactly the bug class that only appears AFTER a real deployment, in an environment
            # nobody
            # runs tests against. No positive case today does not mean there is no hole.
            span.set_status(StatusCode.ERROR, _scrub_and_truncate(str(error)))
            # `record_exception` builds the `exception.message` + `exception.stacktrace` attributes
            # itself from the exception object — there is NO way to insert scrubbing in between. So
            # we
            # write an equivalent event BY HAND with masked content, and DO NOT call
            # record_exception any
            # more: keeping both would make the masked version mere decoration next to the raw one.
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
        # `serialized["kwargs"]["model_name"]` — NOT "model" (a real finding while verifying traces
        # in Jaeger: the wrong field name made spans always record "ChatOpenAI" — the CLASS name —
        # instead of the real "gpt-4o-mini").
        model = (serialized.get("kwargs") or {}).get("model_name") or serialized.get("name") or "unknown"
        # ONLY non-system-prompt messages go into the preview — the system prompt
        # is STATIC text written by developers (src/agents/prompt.py), contains no customer PII, and
        # repeats verbatim in EVERY span, making traces hard to read. A real finding while
        # verifying:
        # PII scrubbing (correct and necessary for REAL customer/tool messages) running over the
        # system prompt shredded it into scattered "[NAME]" tokens, unreadable — hurting debugging
        # with no security benefit (the system prompt has no PII to mask).
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
                word = response.llm_output["token_usage"]
                usage = {
                    "input_tokens": word.get("prompt_tokens", 0),
                    "output_tokens": word.get("completion_tokens", 0),
                    "total_tokens": word.get("total_tokens", 0),
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
        # LangGraph wraps tool results into a ToolMessage before invoking the callback
        # (unlike calling a tool directly via `.invoke()`, which returns the dict/str as-is) — a
        # real
        # finding while verifying traces in Jaeger: without unwrapping `.content` the preview only
        # showed the Pydantic repr ("content='...' additional_kwargs=...") instead of readable JSON.
        content = getattr(output, "content", output)
        output_str = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False, default=str)
        self._end_span(run_id, extra_attrs={"tool.output.preview": _scrub_and_truncate(output_str)})

    def on_tool_error(self, error: BaseException, *, run_id: UUID, **kwargs: Any) -> None:
        self._end_span(run_id, error=error)
