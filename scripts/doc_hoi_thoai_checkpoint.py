#!/usr/bin/env python3
"""
doc_hoi_thoai_checkpoint.py — xuất hội thoại đầy đủ của một thread từ PostgresSaver

DỰNG LẠI (P2, giao bởi PO qua p-226-a1, 2026-08-28) — công cụ này từng tồn tại
trong một phiên Claude đã đóng và chết theo phiên đó (không nằm trong scripts/,
không có trong git). Đây là bản dựng lại, không phải ý tưởng mới.

VÌ SAO KHÔNG ĐỌC THẲNG BẢNG `checkpoint_blobs`
-----------------------------------------------
`checkpoint_blobs` lưu channel value đã serialize (dạng nhị phân của
langgraph-checkpoint, không phải JSON thô) — tự parse tay là tái phát minh lại
đúng thứ `langgraph.checkpoint.postgres.PostgresSaver` đã làm, và dễ sai theo
phiên bản serializer. Script này dùng thẳng `PostgresSaver.list()` — cùng lớp
mà `src/agents/graph.py::_build_checkpointer()` dùng để phục vụ agent thật —
nên đọc đúng schema hiện hành mà không cần biết chi tiết định dạng blob.

Lấy checkpoint MỚI NHẤT của thread là đủ: kênh `messages` dùng reducer
`add_messages` của LangGraph, nên checkpoint mới nhất luôn chứa toàn bộ lịch
sử hội thoại từ đầu thread, không chỉ delta của lượt cuối.

CHỈ ĐỌC — không setup(), không ghi gì vào DB.

DÙNG
----
    # Bên trong container đã có DATABASE_URL + langgraph cài sẵn (vd backend):
    python3 scripts/doc_hoi_thoai_checkpoint.py --thread-id "USR-0145:1787651345"

    # Chạy trong container KHÔNG có sẵn file này trên đĩa (không docker cp):
    docker exec -i <container> python3 - --thread-id "USR-0145:1787651345" \\
        < scripts/doc_hoi_thoai_checkpoint.py > hoi_thoai.json

Mặc định in JSON ra stdout (mảng các lượt: thu_tu, vai, noi_dung, tool_calls,
ten_tool, tool_call_id). Dùng --out để ghi ra file thay vì stdout.
"""
from __future__ import annotations

import argparse
import json
import os
import sys


def _doc_conninfo() -> str:
    """DATABASE_URL trong .env là dạng SQLAlchemy (postgresql+psycopg2://).

    psycopg3 (langgraph-checkpoint-postgres dùng) không nhận dạng đó — cùng
    một chỗ vấp mà `src/agents/graph.py::_build_checkpointer():644` đã ghi lại.
    Đổi tiền tố ở đây, KHÔNG bắt người chạy tự truyền biến thứ hai (đúng lý do
    ADR-013 nêu: một biến lệch bản là nguồn của một lớp lỗi âm thầm khác).
    """
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise SystemExit("Thiếu DATABASE_URL trong môi trường — chạy script này "
                          "bên trong container backend (docker exec), không phải host trần.")
    return url.replace("postgresql+psycopg2://", "postgresql://", 1)


def doc_hoi_thoai(thread_id: str) -> list[dict]:
    from langgraph.checkpoint.postgres import PostgresSaver
    from psycopg_pool import ConnectionPool

    pool = ConnectionPool(
        conninfo=_doc_conninfo(),
        min_size=1,
        max_size=1,
        kwargs={"autocommit": True, "prepare_threshold": 0},
        open=True,
    )
    try:
        saver = PostgresSaver(pool)
        config = {"configurable": {"thread_id": thread_id}}
        # limit=1 lấy checkpoint MỚI NHẤT — đủ cho toàn bộ lịch sử, xem docstring module.
        tup = next(saver.list(config, limit=1), None)
        if tup is None:
            raise SystemExit(f"Không có checkpoint nào cho thread_id={thread_id!r} — "
                              "kiểm lại thread_id, hoặc thread thuộc ngăn Postgres khác.")

        messages = tup.checkpoint.get("channel_values", {}).get("messages", [])
        record_row = []
        for thu_tu, msg in enumerate(messages):
            tool_calls = getattr(msg, "tool_calls", None) or []
            record_row.append({
                "thu_tu": thu_tu,
                "vai": getattr(msg, "type", msg.__class__.__name__),
                "noi_dung": msg.content,
                "tool_calls": [
                    {"ten": tc.get("name"), "tham_so": tc.get("args"), "id": tc.get("id")}
                    for tc in tool_calls
                ],
                "ten_tool": getattr(msg, "name", None),
                "tool_call_id": getattr(msg, "tool_call_id", None),
            })
        return record_row
    finally:
        pool.close()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--thread-id", required=True, help='vd "USR-0145:1787651345"')
    ap.add_argument("--out", default=None, help="ghi JSON ra file này thay vì stdout")
    args = ap.parse_args()

    record_row = doc_hoi_thoai(args.thread_id)
    noi_dung_json = json.dumps(record_row, ensure_ascii=False, indent=2)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(noi_dung_json)
        print(f"Đã ghi {len(record_row)} bản ghi vào {args.out}", file=sys.stderr)
    else:
        print(noi_dung_json)
        print(f"--- {len(record_row)} bản ghi ---", file=sys.stderr)


if __name__ == "__main__":
    main()
