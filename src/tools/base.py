"""Shared infrastructure for the 5 tools in PRD §6 / Data Brief §6.3.

Every tool MUST call `record_tool_result` before returning — this is the only way
T4 (no fabricated figures, Data Brief §6.5) has a source of truth to check against:
if the agent states a number, that number must trace back to a `tool_result_id`
produced here. record_tool_result stores exactly WHAT THE TOOL RETURNED TO THE AGENT
(already masked, if applicable) — not the full unmasked version, since the full version
already lives in the source table (BR-07).
"""
from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from sqlalchemy.orm import Session

from src.db.models import ToolResult


class ToolError(Exception):
    """Business error where the tool deliberately refuses (e.g. missing reason, ticket not found).

    Unlike a system error — this is an error the agent MUST be able to handle (report back
    to the customer/staff), not a bug.
    """


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


# Alias kept for backward compatibility with old code importing _new_id.
_new_id = new_id


def record_tool_result(session: Session, tool_name: str, payload: dict[str, Any]) -> str:
    raw_json_str = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    content_hash = hashlib.sha256(raw_json_str.encode("utf-8")).hexdigest()
    tool_result_id = _new_id("TR")
    session.add(
        ToolResult(
            tool_result_id=tool_result_id,
            tool_name=tool_name,
            raw_json=payload,
            content_hash=content_hash,
        )
    )
    session.flush()
    return tool_result_id
