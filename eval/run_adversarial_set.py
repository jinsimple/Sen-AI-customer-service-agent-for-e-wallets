#!/usr/bin/env python3
"""Nhóm B — bộ adversarial prompt (`adversarial_set.jsonl`, 40 case bám 10 mục
B1-B10 FIN05-StressTest-Plan.md + PDPA/A2/A6 bổ sung + RAG injection). Gọi
agent THẬT — xem docs/TESTING.md trước khi chạy.

Dùng:
    python eval/run_adversarial_set.py
    python eval/run_adversarial_set.py --sample 5   # debug nhanh
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval._harness import (
    build_eval_session,
    cham_bo_da_luot,
    load_jsonl,
    now_stamp,
    run_case_adversary,
)

EVAL_DIR = Path(__file__).resolve().parent
_PARTNER_ADMIN_ID = "USR-EVAL-PA01"


def _ensure_partner_admin(session) -> str:
    from src.db.models import User

    if session.get(User, _PARTNER_ADMIN_ID) is None:
        session.add(
            User(
                user_id=_PARTNER_ADMIN_ID,
                role="partner_admin",
                full_name="Eval Partner Admin",
                phone="0900000999",
                kyc_level=0,
                created_at=dt.datetime.utcnow(),
            )
        )
        session.commit()
    return _PARTNER_ADMIN_ID


def _ingest_malicious_policy(session, text: str, case_id: str) -> None:
    from src.rag.ingest import ingest_document

    uploader = _ensure_partner_admin(session)
    ingest_document(
        session, file_bytes=text.encode("utf-8"), filename=f"{case_id}.txt", uploaded_by=uploader
    )
    session.commit()


def _inject_malicious_transaction_note(session, trans_id: str, text: str) -> None:
    """SEC-001 (FIN05_QA_TestCases.jsonl) — bề mặt tấn công KHÁC với RAG policy
    doc: `Transaction.des` (ghi chú giao dịch) là trường tự do, được
    lookup_transaction trả nguyên văn cho agent (src/tools/lookup_transaction.py
    "des": txn.des) — chính fraud_engine.py cũng đọc trường này để dò từ khoá
    (FS-09), hệ thống đã tự coi đây là dữ liệu không tin cậy."""
    from src.db.models import Transaction

    txn = session.get(Transaction, trans_id)
    if txn is None:
        raise RuntimeError(f"trans_id không tồn tại để inject SEC-001: {trans_id}")
    txn.des = text
    session.commit()


def run(cases: list[dict]) -> list[dict]:
    import tempfile

    with tempfile.TemporaryDirectory(prefix="fin05_adv_") as tmp:
        db_path = Path(tmp) / "adv.db"
        session = build_eval_session(db_path)

        results = []
        for i, case in enumerate(cases, start=1):
            case_id = case["case_id"]
            print(f"[{i}/{len(cases)}] {case_id} ({case['category']})...", file=sys.stderr)
            try:
                if case.get("setup_malicious_policy"):
                    _ingest_malicious_policy(session, case["setup_malicious_policy"], case_id)
                if case.get("setup_malicious_transaction_note"):
                    note = case["setup_malicious_transaction_note"]
                    _inject_malicious_transaction_note(session, note["trans_id"], note["text"])

                # W0 — chạy qua `run_case_adversary`, kể cả case 1 lượt.
                # `so_luot_leo_thang` mặc định = đúng số lượt viết sẵn, nên 45
                # case cũ chạy Y HỆT trước đây; case nào khai số lớn hơn thì
                # phần dôi ra do kẻ-tấn-công-ảo sinh, phản ứng theo câu agent
                # vừa trả lời.
                kich_ban = case.get("kich_ban_leo_thang") or case["utterances"]
                agent_result = run_case_adversary(
                    session, case=case, thread_id=f"ADV-{case_id}",
                    so_luot_toi_da=int(case.get("so_luot_leo_thang") or len(kich_ban)),
                )
                all_replies = agent_result.get("all_agent_replies") or []
                reply = agent_result.get("reply", "")
                # CHẤM TÍCH LUỸ TOÀN HỘI THOẠI, không chỉ lượt cuối. Bản cũ
                # chấm trên `reply` (= lượt cuối): agent sập ở lượt 2 rồi lượt
                # 5 nói lại câu từ chối chuẩn mực vẫn được tính ĐẠT, dù tiền đã
                # hứa hoàn ở lượt 2. Với bộ đa lượt thì bỏ sót gần như chắc chắn.
                cham = cham_bo_da_luot(case, agent_result)
                violations = cham["vi_pham"]
                first_violation_turn = cham["first_violation_turn"]
            except Exception as e:
                reply = ""
                all_replies = []
                first_violation_turn = None
                violations = [f"LỖI CHẠY CASE: {e!r}"]
                agent_result = {}
            session.rollback()

            results.append(
                {
                    "case_id": case_id,
                    "category": case["category"],
                    "description": case.get("description", ""),
                    "passed": not violations,
                    "violations": violations,
                    "reply": reply,
                    # D1 — giữ TRANSCRIPT ĐỦ LƯỢT trong raw. Điều tra một ca
                    # leo thang mà chỉ có lượt cuối thì không lần ra được agent
                    # bắt đầu nhượng bộ từ đâu.
                    "all_agent_replies": all_replies,
                    "all_customer_texts": agent_result.get("all_customer_texts") or [],
                    "so_luot_da_chay": agent_result.get("so_luot_da_chay", 0),
                    # Tool THEO TỪNG LƯỢT — tách được "từ chối SAU KHI đã thử
                    # tra" (đúng) với "từ chối mà không thử gì" (over-refusal).
                    "tool_calls_theo_luot": agent_result.get("tool_calls_theo_luot") or [],
                    # Crescendo hay thắng ở lượt GIỮA rồi lượt cuối quay lại vô
                    # hại — biết vỡ ở lượt nào mới biết guardrail chặn ở đâu.
                    "first_violation_turn": first_violation_turn,
                    "tool_calls": [c.get("tool_name") for c in agent_result.get("tool_calls", [])],
                }
            )
        session.close()
    return results


# `_check_adv_patterns` (chấm trên MỘT reply) đã bị thay bằng
# `check_forbidden_tich_luy` ở `_harness.py` — quét TOÀN BỘ hội thoại và ghi rõ
# vi phạm ở lượt nào. Xoá hẳn thay vì để lại: một hàm chấm-lượt-cuối nằm cạnh
# một hàm chấm-tích-luỹ là lời mời gọi ai đó dùng nhầm cái yếu hơn.


def write_report(results: list[dict], out_path: Path) -> None:
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    lines = [
        f"# Báo cáo eval adversarial_set — {now_stamp()}",
        "",
        f"**Tổng:** {passed}/{total} pass ({passed / total * 100:.1f}%)" if total else "Không có case.",
        "",
    ]
    failing = [r for r in results if not r["passed"]]
    if failing:
        lines += ["## Case KHÔNG pass (agent bị dụ thành công — cần fix ngay)", ""]
        for r in failing:
            lines.append(f"### {r['case_id']} — {r['category']}: {r['description']}")
            lines.append(f"- Vi phạm: {'; '.join(r['violations'])}")
            lines.append(f"- Tool đã gọi: {', '.join(r['tool_calls']) or '(không)'}")
            lines.append(f"- Reply: {r['reply'][:300]!r}")
            lines.append("")
    else:
        lines.append("Không có case nào bị dụ thành công.")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nBáo cáo: {out_path}", file=sys.stderr)
    print(f"Tổng: {passed}/{total} pass ({passed / total * 100:.1f}%)" if total else "0 case", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--file", type=Path, default=EVAL_DIR / "adversarial_set.jsonl")
    parser.add_argument("--sample", type=int, default=None)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    cases = load_jsonl(args.file)
    if args.sample:
        cases = cases[: args.sample]

    print(f"Chạy {len(cases)} case adversarial từ {args.file} — gọi OpenAI thật.", file=sys.stderr)
    results = run(cases)

    out_dir = EVAL_DIR / "results"
    out_dir.mkdir(exist_ok=True)
    stamp = now_stamp()

    # Lưu raw JSON trước khi format báo cáo — xem run_golden_set.py cho lý do
    # (tránh lặp lại sự cố mất kết quả đã tốn phí OpenAI thật do lỗi format).
    raw_path = out_dir / f"adversarial_run_{stamp}_raw.json"
    raw_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Raw JSON (khôi phục nếu format báo cáo lỗi): {raw_path}", file=sys.stderr)

    out_path = args.out or out_dir / f"adversarial_run_{stamp}.md"
    write_report(results, out_path)

    sys.exit(1 if any(not r["passed"] for r in results) else 0)


if __name__ == "__main__":
    main()
