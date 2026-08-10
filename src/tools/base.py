"""Hạ tầng dùng chung cho 5 tool ở PRD §6 / Data Brief §6.3.

Mọi tool PHẢI gọi `record_tool_result` trước khi return — đây là cách duy
nhất để T4 (chống bịa số liệu, Data Brief §6.5) có một nguồn sự thật để đối
chiếu: nếu agent nói ra một con số, con số đó phải truy được về một
`tool_result_id` sinh từ đây. record_tool_result lưu đúng NHỮNG GÌ TOOL TRẢ
VỀ CHO AGENT (đã masking nếu có) — không lưu bản đầy đủ chưa che, vì bản
đầy đủ đã có sẵn trong bảng gốc (BR-07).
"""
from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from sqlalchemy.orm import Session

from src.db.models import ToolResult


class ToolError(Exception):
    """Lỗi nghiệp vụ do tool chủ động từ chối (vd thiếu reason, ticket không tồn tại).

    Khác với lỗi hệ thống — đây là lỗi mà agent PHẢI xử lý được (báo lại
    khách/nhân viên), không phải bug.
    """


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


# Alias giữ tương thích ngược cho code cũ import _new_id.
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
