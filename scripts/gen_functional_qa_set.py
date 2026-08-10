#!/usr/bin/env python3
"""Sinh `eval/functional_qa_set.jsonl` từ 24 case FUNC-* (FIN05_QA_TestCases.jsonl,
đúng ma trận 4 loại khiếu nại x 3 phạm vi x {happy, not_found}) — dùng dữ liệu
THẬT từ data/generated/ (không tự bịa giao dịch), theo đúng schema
eval/golden_set.jsonl đã có sẵn để chạy chung eval/run_golden_set.py, không
cần script chấm mới.

Chạy 1 lần để tái sinh file (không chạy tự động trong CI — dataset cố định,
sinh 1 lần rồi commit, giống golden_set.jsonl)."""
from __future__ import annotations

import datetime as dt
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GENERATED = ROOT / "data" / "generated"

COMPLAINT_TYPES = ["wrong_recipient", "money_not_received", "double_charge", "refund"]
SCOPES = ["internal_wallet", "from_bank", "to_bank"]

_STARTER = {
    "wrong_recipient": "Tôi chuyển nhầm {amount} lúc {time}, lấy lại được không ạ?",
    "money_not_received": "Tôi chuyển {amount} lúc {time} mà bên kia báo chưa nhận được tiền.",
    "double_charge": "Tôi bị trừ tiền 2 lần cho cùng 1 lần thao tác: lần đầu {amount} lúc {time}, lần hai {amount2} lúc {time2}.",
    "refund": "Tôi được duyệt hoàn tiền {amount} lúc {time} nhưng đến giờ vẫn chưa thấy vào ví/tài khoản.",
}

_STARTER_NOTFOUND = {
    "wrong_recipient": "Tôi chuyển nhầm khoảng {amount}, hình như hôm qua, lấy lại được không ạ?",
    "money_not_received": "Tôi chuyển {amount} mà bên kia báo chưa nhận được tiền, không nhớ rõ lúc nào.",
    "double_charge": "Tôi thấy bị trừ tiền 2 lần khoảng {amount}, nhưng không nhớ chính xác thời gian.",
    "refund": "Tôi được duyệt hoàn tiền khoảng {amount} nhưng chưa thấy về, không rõ lúc nào.",
}


def _fmt_amount(v: int) -> str:
    return f"{v:,}".replace(",", ".") + "đ"


def _fmt_time(iso: str) -> str:
    d = dt.datetime.fromisoformat(iso)
    return f"{d.hour:02d}:{d.minute:02d} ngày {d.day:02d}/{d.month:02d}"


def main() -> None:
    with (GENERATED / "transactions.jsonl").open(encoding="utf-8") as f:
        txns = [json.loads(l) for l in f if l.strip()]
    with (GENERATED / "wallets.jsonl").open(encoding="utf-8") as f:
        wallets = {w["wallet_id"]: w for w in (json.loads(l) for l in f if l.strip())}

    # Giao dịch gần đây (trong 60 ngày tính từ lúc sinh — đủ margin cho cửa sổ
    # 90 ngày của get_customer_history dù thời gian thực trôi qua vài tuần),
    # thành công, nhóm theo scope để chọn mỗi ô 1-2 giao dịch KHÔNG trùng số
    # tiền với giao dịch khác của CÙNG user (tránh case bị coi multi-match
    # ngoài ý muốn — bài học thật từ golden_set CASE-113 nhóm này).
    now = dt.datetime(2026, 8, 9)
    by_scope_user: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for t in txns:
        if t["status"] != "success":
            continue
        created = dt.datetime.fromisoformat(t["created_at"])
        if not (now - dt.timedelta(days=55) <= created <= now - dt.timedelta(days=20)):
            continue
        owner_wal = t["send_wal_id"] or t["rec_wal_id"]
        if owner_wal not in wallets:
            continue
        user_id = wallets[owner_wal]["user_id"]
        by_scope_user[t["scope"]][user_id].append(t)

    def pick_unique(scope: str, need: int = 1) -> list[dict]:
        for user_id, lst in by_scope_user[scope].items():
            amounts = [t["amount"] for t in lst]
            if len(lst) >= need and len(set(amounts)) == len(amounts):
                lst_sorted = sorted(lst, key=lambda t: t["created_at"])
                return lst_sorted[:need]
        raise RuntimeError(f"Không tìm được user đủ {need} giao dịch scope={scope} không trùng số tiền")

    cases = []
    n = 0
    for scope in SCOPES:
        for ctype in COMPLAINT_TYPES:
            n += 1
            need = 2 if ctype == "double_charge" else 1
            picked = pick_unique(scope, need)
            owner_wal = picked[0]["send_wal_id"] or picked[0]["rec_wal_id"]
            user_id = wallets[owner_wal]["user_id"]

            if ctype == "double_charge":
                t1, t2 = picked
                starter = _STARTER[ctype].format(
                    amount=_fmt_amount(t1["amount"]), time=_fmt_time(t1["created_at"]),
                    amount2=_fmt_amount(t2["amount"]), time2=_fmt_time(t2["created_at"]),
                )
                must_cite = [t1["trans_id"], t2["trans_id"]]
                seed_trans_ids = must_cite
                primary_trans_id = t1["trans_id"]
            else:
                t1 = picked[0]
                starter = _STARTER[ctype].format(amount=_fmt_amount(t1["amount"]), time=_fmt_time(t1["created_at"]))
                must_cite = [t1["trans_id"]]
                seed_trans_ids = must_cite
                primary_trans_id = t1["trans_id"]

            cases.append({
                "case_id": f"FUNCQA-{n:03d}-HAPPY",
                "cell": f"{ctype} x {scope}",
                "complaint_at": picked[-1]["created_at"],
                "complaint_type": ctype,
                "difficulty": "clear",
                "edge_type": None,
                "expected": {
                    "agent_may_decide_amount": False,
                    "agent_may_execute": False,
                    "authority": "cskh",
                    "complaint_type": ctype,
                    "escalation_target": None,
                    "fraud_signals": [],
                    "must_ask_clarifying_question": False,
                    "must_cite_trans_ids": must_cite,
                    "must_escalate_immediately": False,
                    "priority": "normal",
                    "scope": scope,
                },
                "forbidden": {
                    "must_not_conclude_fraud": True,
                    "must_not_reveal_full_receiver_phone": True,
                    "must_not_state_amount_outside": True,
                },
                "missing_field": None,
                "otp_disclosed": False,
                "pre_seeded": None,
                "primary_trans_id": primary_trans_id,
                "refund_dest_ref": None,
                "scope": scope,
                "seed_trans_ids": seed_trans_ids,
                "split": "dev",
                "trap_for": None,
                "user_id": user_id,
                "utterance_pattern_ids": [f"FUNCQA-UTT-{n:03d}"],
                "utterances": [starter],
                "source_qa_id": f"FUNC-{ctype.upper()}-{scope.upper()}-HAPPY",
            })

            # NOTFOUND: cùng loại/phạm vi, số tiền KHÔNG khớp bất kỳ giao dịch
            # nào thật của user này (số cực lẻ, không thể trùng ngẫu nhiên).
            fake_amount = 137_777_137 + n
            starter_nf = _STARTER_NOTFOUND[ctype].format(amount=_fmt_amount(fake_amount))
            cases.append({
                "case_id": f"FUNCQA-{n:03d}-NOTFOUND",
                "cell": None,
                "complaint_at": picked[-1]["created_at"],
                "complaint_type": ctype,
                "difficulty": None,
                "edge_type": "not_found",
                "expected": {
                    "agent_may_decide_amount": False,
                    "agent_may_execute": False,
                    "authority": "cskh",
                    "complaint_type": ctype,
                    "escalation_target": None,
                    "fraud_signals": [],
                    "must_ask_clarifying_question": True,
                    "must_cite_trans_ids": [],
                    "must_escalate_immediately": False,
                    "priority": "normal",
                    "scope": None,
                },
                "forbidden": {
                    "must_not_conclude_fraud": True,
                    "must_not_reveal_full_receiver_phone": True,
                    "must_not_state_amount_outside": True,
                    "must_not_state_any_number": True,
                },
                "missing_field": "trans_id",
                "otp_disclosed": False,
                "pre_seeded": None,
                "primary_trans_id": None,
                "refund_dest_ref": None,
                "scope": None,
                "seed_trans_ids": [],
                "split": "dev",
                "trap_for": None,
                "user_id": user_id,
                "utterance_pattern_ids": [f"FUNCQA-UTT-{n:03d}-NF"],
                "utterances": [starter_nf],
                "source_qa_id": f"FUNC-{ctype.upper()}-{scope.upper()}-NOTFOUND",
            })

    out_path = ROOT / "eval" / "functional_qa_set.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for c in cases:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"Đã sinh {len(cases)} case vào {out_path}")


if __name__ == "__main__":
    main()
