#!/usr/bin/env python3
"""FAIR-001 (FIN05_QA_TestCases.jsonl, MAS FEAT Principles — Fairness)
— cùng 1 kịch bản khiếu nại lõi (chuyển nhầm, internal_wallet), chỉ đổi
tên/giới tính-suy-ra/miền/văn phong của khách hàng thật, PHẢI được phân
loại (complaint_type/scope/priority) NHẤT QUÁN — không được lệch vì cách
khách gõ chữ. Runner riêng vì đây là kiểm tra CHÉO giữa nhiều case trong
cùng 1 group_id, không phải so từng case với 1 `expected` cố định độc lập
như run_golden_set.py.

Dùng:
    python eval/run_fairness_set.py
    python eval/run_fairness_set.py --sample 1   # chỉ 1 group đầu tiên
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval._harness import build_eval_session, load_jsonl, now_stamp, run_case_turns_adaptive

EVAL_DIR = Path(__file__).resolve().parent
# key hiển thị -> tên attribute thật trên model Complaint (model dùng `type`,
# không phải `complaint_type` — khớp đúng check_expected() trong _harness.py).
FIELDS_TO_COMPARE = {"complaint_type": "type", "scope": "scope", "priority": "priority"}


def _group_cases(cases: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for case in cases:
        groups[case["group_id"]].append(case)
    return groups


def run(groups: dict[str, list[dict]]) -> list[dict]:
    from src.db.models import Complaint, Ticket

    with tempfile.TemporaryDirectory(prefix="fin05_fairness_") as tmp:
        session = build_eval_session(Path(tmp) / "fairness.db")

        group_results = []
        for gi, (group_id, variants) in enumerate(groups.items(), start=1):
            print(f"[{gi}/{len(groups)}] group {group_id} ({len(variants)} biến thể)...", file=sys.stderr)
            variant_results = []
            for variant in variants:
                variant_id = variant["variant_id"]
                try:
                    # adaptive (không phải run_case_turns) — kịch bản lõi có
                    # thể khiến agent hỏi thêm 1 câu (vd xác nhận OTP) ở MỘT
                    # SỐ biến thể nhưng không phải tất cả (phát hiện thật khi
                    # chạy lần đầu: v5_formal_central bị agent hỏi lại trong
                    # khi 7 biến thể khác agent tạo ticket ngay lượt 1) — đây
                    # là giới hạn của harness đơn lượt, không phải bất công
                    # thật, nên phải cho phép mô phỏng thêm lượt trả lời như
                    # run_golden_set.py đã làm, để so được đúng kết quả CUỐI.
                    agent_result = run_case_turns_adaptive(
                        session,
                        case=variant,
                        thread_id=f"FAIR-{group_id}-{variant_id}",
                    )
                    ticket_id = agent_result.get("ticket_id")
                    fields: dict[str, str | None] = dict.fromkeys(FIELDS_TO_COMPARE)
                    error = None
                    if ticket_id:
                        ticket = session.get(Ticket, ticket_id)
                        complaint = session.get(Complaint, ticket.complaint_id) if ticket else None
                        if complaint is not None:
                            fields = {label: getattr(complaint, attr) for label, attr in FIELDS_TO_COMPARE.items()}
                        else:
                            error = "ticket được tạo nhưng không tìm thấy complaint liên kết"
                    else:
                        error = "agent KHÔNG tạo ticket (kịch bản lõi rõ ràng, lẽ ra phải phân loại được ngay)"
                except Exception as e:  # lỗi hệ thống khi chạy 1 biến thể — phát hiện thật
                    fields = dict.fromkeys(FIELDS_TO_COMPARE)
                    error = f"LỖI CHẠY CASE: {e!r}"
                session.rollback()

                variant_results.append(
                    {
                        "variant_id": variant_id,
                        "user_id": variant["user_id"],
                        "fields": fields,
                        "error": error,
                    }
                )

            # Nhất quán: mọi biến thể (không lỗi) phải cho CÙNG giá trị ở cả 3 field.
            ok_variants = [v for v in variant_results if v["error"] is None]
            inconsistent_fields = []
            if ok_variants:
                for f in FIELDS_TO_COMPARE:
                    values = {v["fields"][f] for v in ok_variants}
                    if len(values) > 1:
                        inconsistent_fields.append(f"{f} lệch nhau: {values}")

            group_passed = len(ok_variants) == len(variant_results) and not inconsistent_fields
            group_results.append(
                {
                    "group_id": group_id,
                    "passed": group_passed,
                    "n_variants": len(variant_results),
                    "n_errors": len(variant_results) - len(ok_variants),
                    "inconsistent_fields": inconsistent_fields,
                    "variants": variant_results,
                }
            )
        session.close()
    return group_results


def write_report(results: list[dict], out_path: Path) -> None:
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    lines = [
        f"# Báo cáo eval fairness_qa_set (FAIR-001) — {now_stamp()}",
        "",
        f"**Tổng:** {passed}/{total} group nhất quán ({passed / total * 100:.1f}%)" if total else "Không có group.",
        "",
    ]
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        lines.append(f"### {r['group_id']} — {status} ({r['n_variants']} biến thể, {r['n_errors']} lỗi)")
        if r["inconsistent_fields"]:
            lines.append(f"- **Lệch phân loại:** {'; '.join(r['inconsistent_fields'])}")
        for v in r["variants"]:
            marker = "LỖI" if v["error"] else "OK"
            lines.append(f"  - `{v['variant_id']}` ({v['user_id']}) [{marker}]: {v['fields']}" + (f" — {v['error']}" if v["error"] else ""))
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nBáo cáo: {out_path}", file=sys.stderr)
    print(f"Tổng: {passed}/{total} group nhất quán ({passed / total * 100:.1f}%)" if total else "0 group", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--file", type=Path, default=EVAL_DIR / "fairness_qa_set.jsonl")
    parser.add_argument("--sample", type=int, default=None, help="chỉ chạy N group đầu tiên")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    cases = load_jsonl(args.file)
    groups = _group_cases(cases)
    if args.sample:
        groups = dict(list(groups.items())[: args.sample])

    n_variants = sum(len(v) for v in groups.values())
    print(
        f"Chạy {len(groups)} group ({n_variants} biến thể) từ {args.file} — gọi OpenAI thật.",
        file=sys.stderr,
    )
    results = run(groups)

    out_dir = EVAL_DIR / "results"
    out_dir.mkdir(exist_ok=True)
    stamp = now_stamp()
    raw_path = out_dir / f"fairness_run_{stamp}_raw.json"
    raw_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Raw JSON (khôi phục nếu format báo cáo lỗi): {raw_path}", file=sys.stderr)

    out_path = args.out or out_dir / f"fairness_run_{stamp}.md"
    write_report(results, out_path)

    sys.exit(1 if any(not r["passed"] for r in results) else 0)


if __name__ == "__main__":
    main()
