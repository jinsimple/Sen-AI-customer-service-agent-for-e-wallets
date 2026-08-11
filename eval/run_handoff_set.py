#!/usr/bin/env python3
"""CTRL-001 (FIN05_QA_TestCases.jsonl, ISO/IEC 25059 "user controllability")
— khách yêu cầu người thật -> agent phải gọi request_human_handoff NGAY, và
ticket thật phải có `human_handoff_requested=True` trong DB (deterministic,
không chỉ dựa vào lời văn). Runner riêng (không dùng run_golden_set.py) vì
kịch bản này không phải ma trận 4 loại×3 phạm vi và không cần
simulate_customer_reply() (agent phải hành động ngay trong lượt đó, không
hỏi thêm) — dùng thẳng run_case_turns() (không phải run_case_turns_adaptive).

Dùng:
    python eval/run_handoff_set.py
    python eval/run_handoff_set.py --sample 1
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval._harness import build_eval_session, load_jsonl, now_stamp, run_case_turns
from eval._llm_judge import llm_judge

EVAL_DIR = Path(__file__).resolve().parent


def run(cases: list[dict]) -> list[dict]:
    from src.db.models import Ticket

    with tempfile.TemporaryDirectory(prefix="fin05_handoff_") as tmp:
        session = build_eval_session(Path(tmp) / "handoff.db")

        results = []
        for i, case in enumerate(cases, start=1):
            case_id = case["case_id"]
            print(f"[{i}/{len(cases)}] {case_id}...", file=sys.stderr)
            ticket_id = None
            try:
                agent_result = run_case_turns(
                    session, user_id=case["user_id"], utterances=case["utterances"], thread_id=f"HANDOFF-{case_id}"
                )
                handoff_calls = [
                    c for c in agent_result.get("tool_calls", []) if c.get("tool_name") == "request_human_handoff"
                ]
                called_tool = bool(handoff_calls)
                ticket_flagged = False
                if handoff_calls:
                    ticket_id = handoff_calls[-1].get("result", {}).get("ticket_id")
                    if ticket_id:
                        ticket = session.get(Ticket, ticket_id)
                        ticket_flagged = bool(ticket and ticket.human_handoff_requested)

                reply = agent_result.get("reply", "")
                verdict = llm_judge(
                    reply=reply,
                    expected_output_contains=case["expected_output_contains"],
                    forbidden_output_contains=case["forbidden_output_contains"],
                    context=case.get("context", ""),
                )
                passed = called_tool and ticket_flagged and verdict["pass"]
                reason_parts = []
                if not called_tool:
                    reason_parts.append("KHÔNG gọi tool request_human_handoff")
                if called_tool and not ticket_flagged:
                    reason_parts.append("ticket không có human_handoff_requested=True trong DB")
                if not verdict["pass"]:
                    reason_parts.append(f"giám khảo: {verdict['reason']}")
            except Exception as e:  # lỗi hệ thống khi chạy case — phát hiện thật, không sập cả batch
                passed = False
                reply = ""
                reason_parts = [f"LỖI CHẠY CASE: {e!r}"]
            session.rollback()

            results.append(
                {
                    "case_id": case_id,
                    "passed": passed,
                    "reason": "; ".join(reason_parts) or "OK",
                    "ticket_id": ticket_id,
                    "reply": reply,
                }
            )
        session.close()
    return results


def write_report(results: list[dict], out_path: Path) -> None:
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    lines = [
        f"# Báo cáo eval handoff_qa_set — {now_stamp()}",
        "",
        f"**Tổng:** {passed}/{total} pass ({passed / total * 100:.1f}%)" if total else "Không có case.",
        "",
    ]
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        lines.append(f"### {r['case_id']} — {status}")
        lines.append(f"- Lý do: {r['reason']}")
        lines.append(f"- ticket_id: {r['ticket_id']}")
        lines.append(f"- Reply: {r['reply'][:300]!r}")
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nBáo cáo: {out_path}", file=sys.stderr)
    print(f"Tổng: {passed}/{total} pass ({passed / total * 100:.1f}%)" if total else "0 case", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--file", type=Path, default=EVAL_DIR / "handoff_qa_set.jsonl")
    parser.add_argument("--sample", type=int, default=None)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    cases = load_jsonl(args.file)
    if args.sample:
        cases = cases[: args.sample]

    print(f"Chạy {len(cases)} case handoff từ {args.file} — gọi OpenAI thật (2 lần/case: agent + giám khảo).", file=sys.stderr)
    results = run(cases)

    out_dir = EVAL_DIR / "results"
    out_dir.mkdir(exist_ok=True)
    stamp = now_stamp()
    raw_path = out_dir / f"handoff_run_{stamp}_raw.json"
    raw_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Raw JSON (khôi phục nếu format báo cáo lỗi): {raw_path}", file=sys.stderr)

    out_path = args.out or out_dir / f"handoff_run_{stamp}.md"
    write_report(results, out_path)

    sys.exit(1 if any(not r["passed"] for r in results) else 0)


if __name__ == "__main__":
    main()
