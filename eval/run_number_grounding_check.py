#!/usr/bin/env python3
"""FIN05-StressTest-Plan-v4 6.1/B-09 — chống bịa số liệu (anti-hallucination),
lớp kiểm tra CÒN THIẾU so với `eval/_harness.py::check_expected`'s "cite_"
checks: check hiện có CHỈ xác nhận trans_id xuất hiện đâu đó trong tool_calls
(agent có gọi đúng tool không) — KHÔNG đối chiếu từng CON SỐ agent phát biểu
bằng lời (trong `reply`) có thật sự khớp với số liệu ToolResult đã trả về hay
không. Đây chính là khoảng trống B-09 chỉ ra: agent có thể gọi ĐÚNG tool,
nhưng khi diễn đạt lại bằng ngôn ngữ tự nhiên vẫn có thể lệch số (làm tròn
sai, nhầm lẫn giữa amount/fee, hoặc bịa hẳn 1 số không có trong tool result).

Gọi agent THẬT (OpenAI thật, tốn phí) — như mọi script khác trong eval/,
KHÔNG chạy tự động trong CI mặc định, chỉ chạy thủ công/nightly.

Dùng:
    python eval/run_number_grounding_check.py
    python eval/run_number_grounding_check.py --sample 3
"""
from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from eval._harness import build_eval_session
from src.agents.graph import run_agent_turn
from src.db.models import Transaction

EVAL_DIR = Path(__file__).resolve().parent

# Số dạng tiền Việt "92.000", "1.234.000", có thể kèm liền "đ"/"VNĐ" không
# cách (vd "167.000đ") — dấu chấm phân cách nghìn, KHÔNG phải dấu thập phân
# (khác định dạng số Anh-Mỹ). CHỈ dùng \b ở ĐẦU pattern, KHÔNG dùng ở cuối —
# phát hiện thật: "đ" là ký tự chữ Unicode (\w khớp cả \w Unicode theo mặc
# định của module `re`), nên \b cuối KHÔNG khớp giữa "0" và "đ" liền nhau
# (2 ký tự \w cạnh nhau không tạo ranh giới) — làm mọi số tiền có "đ" dính
# liền (không cách) bị regex bỏ sót hoàn toàn, không phải do agent bịa số.
_CURRENCY_RE = re.compile(r"\b\d{1,3}(?:\.\d{3})+")


def _extract_currency_numbers(text: str) -> set[int]:
    return {int(m.replace(".", "")) for m in _CURRENCY_RE.findall(text)}


def _pick_cases(session, n: int) -> list[dict]:
    """Chọn N giao dịch thật, amount đủ lớn để định dạng dấu chấm phân cách
    nghìn rõ ràng (tránh amount < 1000, không có dấu chấm để đối chiếu được
    bằng regex trên) — trải trên nhiều user khác nhau, không lặp trans_id."""
    rows = session.execute(
        select(Transaction).where(Transaction.amount >= 10_000).order_by(Transaction.trans_id).limit(500)
    ).scalars().all()
    seen_users: set[str] = set()
    cases = []
    for txn in rows:
        owner_id = (txn.send_wal_id and _wallet_owner(session, txn.send_wal_id)) or _wallet_owner(
            session, txn.rec_wal_id
        )
        if owner_id is None or owner_id in seen_users:
            continue
        seen_users.add(owner_id)
        cases.append({"user_id": owner_id, "trans_id": txn.trans_id, "expected_amount": txn.amount, "fee": txn.fee})
        if len(cases) >= n:
            break
    return cases


def _wallet_owner(session, wallet_id: str | None) -> str | None:
    if wallet_id is None:
        return None
    from src.db.models import Wallet

    w = session.get(Wallet, wallet_id)
    return w.user_id if w else None


def run(n: int) -> int:
    with tempfile.TemporaryDirectory(prefix="fin05_eval_grounding_") as tmp:
        db_path = Path(tmp) / "eval.db"
        session = build_eval_session(db_path)
        cases = _pick_cases(session, n)

        n_pass = 0
        n_fail = 0
        for i, case in enumerate(cases, start=1):
            thread_id = f"grounding-eval-{i}"
            message = f"Giao dịch {case['trans_id']} của tôi là bao nhiêu tiền vậy?"
            result = run_agent_turn(session, user_id=case["user_id"], message=message, thread_id=thread_id)
            session.rollback()  # cô lập side-effect (không có ticket ở case này, nhưng giữ nhất quán pattern harness)

            reply = result.get("reply", "")
            lookup_calls = [c for c in (result.get("tool_calls") or []) if c.get("tool_name") == "lookup_transaction"]
            tool_amounts: set[int] = set()
            for c in lookup_calls:
                r = c.get("result") or {}
                # status=found lồng field thật dưới "transaction" (xem
                # _serialize_transaction, src/tools/lookup_transaction.py) —
                # KHÔNG phẳng ở top-level payload.
                txn = r.get("transaction") or {}
                if isinstance(txn.get("amount"), int):
                    tool_amounts.add(txn["amount"])
                if isinstance(txn.get("fee"), int):
                    tool_amounts.add(txn["fee"])

            mentioned = _extract_currency_numbers(reply)
            # (a) số tiền THẬT phải xuất hiện trong lời đáp — agent không được
            #     né tránh/làm tròn sai con số đã tra được.
            grounded = case["expected_amount"] in mentioned
            # (b) MỌI số dạng tiền agent nhắc tới phải giải thích được bằng 1
            #     ToolResult thật của LƯỢT NÀY (amount hoặc fee) — số nào
            #     không thuộc tập này là số BỊA (không tra được ở đâu ra).
            fabricated = mentioned - tool_amounts

            ok = bool(lookup_calls) and grounded and not fabricated
            status = "PASS" if ok else "FAIL"
            if ok:
                n_pass += 1
            else:
                n_fail += 1
            print(f"[{i}/{len(cases)}] {case['trans_id']} (user={case['user_id']}) -> {status}", file=sys.stderr)
            if not ok:
                print(f"    reply: {reply!r}", file=sys.stderr)
                print(f"    expected_amount={case['expected_amount']} mentioned={mentioned} tool_amounts={tool_amounts}", file=sys.stderr)
                if not lookup_calls:
                    print("    KHÔNG gọi lookup_transaction lượt này — không đánh giá được grounding.", file=sys.stderr)
                if fabricated:
                    print(f"    SỐ BỊA (không khớp bất kỳ ToolResult nào): {fabricated}", file=sys.stderr)

        print(f"\n{n_pass} PASS, {n_fail} FAIL trên {len(cases)} case", file=sys.stderr)
        return 1 if n_fail else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=int, default=5, help="Số case chạy (mặc định 5)")
    args = parser.parse_args()
    sys.exit(run(args.sample))
