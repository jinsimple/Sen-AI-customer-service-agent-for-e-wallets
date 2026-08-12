#!/usr/bin/env python3
"""Nhóm case `check_type: llm_judge` từ FIN05_QA_TestCases.jsonl (chủ yếu
`ux_tone`) — KHÔNG kiểm được bằng regex/đối chiếu field DB (giọng văn, đồng
cảm, thuật ngữ kỹ thuật rò rỉ...), chấm bằng `eval/_llm_judge.py`. Đúng
khuyến nghị chính README bộ QA: "deterministic trước, LLM-judge sau, chỉ dùng
khi không assert được bằng code".

Dùng:
    python eval/run_llm_judge_set.py
    python eval/run_llm_judge_set.py --sample 1
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval._harness import build_eval_session, load_jsonl, now_stamp, run_case_turns
from eval._llm_judge import llm_judge

EVAL_DIR = Path(__file__).resolve().parent


def _run_one(session, case: dict) -> dict:
    thread_id = f"UXQA-{case['case_id']}"
    if case.get("setup") == "tool_error":
        from src.tools.base import ToolError

        with patch(
            "src.agents.tools.customer_tools._lookup_transaction",
            side_effect=ToolError("Đối tác ngân hàng phản hồi chậm (timeout), chưa tra được trạng thái giao dịch."),
        ):
            result = run_case_turns(
                session, user_id=case["user_id"], utterances=case["utterances"], thread_id=thread_id
            )
    elif case.get("setup") == "rag_empty":
        # GAP-AGENT-RAG-001 — RAG rỗng ở TẦNG AGENT thật (khác
        # tests/test_rag/test_search_empty_index.py, vốn chỉ test hàm
        # search_policy_text() thuần, không qua LLM thật). Chroma dùng chung
        # 1 index thật trên đĩa (không tách riêng theo eval session như DB
        # SQLite tạm) — nên KHÔNG thể tạo "kho rỗng thật" chỉ bằng cách seed
        # ít dữ liệu, phải patch thẳng store.search() để mô phỏng đúng tình
        # huống collection rỗng/không có chunk nào khớp, rồi để AGENT THẬT
        # (không mock LLM) tự quyết định trả lời gì — đây mới là điều B-09/
        # grounding thật sự cần verify: LLM có tự bịa chính sách khi không
        # có gì để trích dẫn hay không.
        from src.rag import store as rag_store

        with patch.object(rag_store, "search", return_value=[]):
            result = run_case_turns(
                session, user_id=case["user_id"], utterances=case["utterances"], thread_id=thread_id
            )
    else:
        result = run_case_turns(session, user_id=case["user_id"], utterances=case["utterances"], thread_id=thread_id)
    return result


def run(cases: list[dict]) -> list[dict]:
    with tempfile.TemporaryDirectory(prefix="fin05_uxqa_") as tmp:
        db_path = Path(tmp) / "uxqa.db"
        session = build_eval_session(db_path)

        results = []
        for i, case in enumerate(cases, start=1):
            case_id = case["case_id"]
            print(f"[{i}/{len(cases)}] {case_id} ({case['source_qa_id']})...", file=sys.stderr)
            try:
                agent_result = _run_one(session, case)
                reply = agent_result.get("reply", "")
                verdict = llm_judge(
                    reply=reply,
                    expected_output_contains=case["expected_output_contains"],
                    forbidden_output_contains=case["forbidden_output_contains"],
                    context=case.get("context", ""),
                )
            except Exception as e:  # lỗi hệ thống khi chạy case — phát hiện thật, không sập cả batch
                reply = ""
                verdict = {"pass": False, "reason": f"LỖI CHẠY CASE: {e!r}"}
            session.rollback()

            results.append(
                {
                    "case_id": case_id,
                    "source_qa_id": case["source_qa_id"],
                    "passed": verdict["pass"],
                    "reason": verdict["reason"],
                    "reply": reply,
                }
            )
        session.close()
    return results


def write_report(results: list[dict], out_path: Path) -> None:
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    lines = [
        f"# Báo cáo eval llm_judge_set — {now_stamp()}",
        "",
        f"**Tổng:** {passed}/{total} pass ({passed / total * 100:.1f}%)" if total else "Không có case.",
        "",
    ]
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        lines.append(f"### {r['case_id']} ({r['source_qa_id']}) — {status}")
        lines.append(f"- Lý do giám khảo: {r['reason']}")
        lines.append(f"- Reply: {r['reply'][:300]!r}")
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nBáo cáo: {out_path}", file=sys.stderr)
    print(f"Tổng: {passed}/{total} pass ({passed / total * 100:.1f}%)" if total else "0 case", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--file", type=Path, default=EVAL_DIR / "llm_judge_set.jsonl")
    parser.add_argument("--sample", type=int, default=None)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    cases = load_jsonl(args.file)
    if args.sample:
        cases = cases[: args.sample]

    print(f"Chạy {len(cases)} case llm_judge từ {args.file} — gọi OpenAI thật (2 lần/case: agent + giám khảo).", file=sys.stderr)
    results = run(cases)

    out_dir = EVAL_DIR / "results"
    out_dir.mkdir(exist_ok=True)
    stamp = now_stamp()
    raw_path = out_dir / f"llm_judge_run_{stamp}_raw.json"
    raw_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    out_path = args.out or out_dir / f"llm_judge_run_{stamp}.md"
    write_report(results, out_path)

    sys.exit(1 if any(not r["passed"] for r in results) else 0)


if __name__ == "__main__":
    main()
