#!/usr/bin/env python3
"""Nhóm A — đối chiếu agent thật với `golden_set.jsonl`/`heldout_set.jsonl`
(FIN05-StressTest-Plan.md mục 3, A8). Gọi agent THẬT (OpenAI thật, tốn phí) —
xem docs/TESTING.md trước khi chạy full trên CI/production.

Dùng:
    python eval/run_golden_set.py                          # golden_set, full 120 case
    python eval/run_golden_set.py --file eval/heldout_set.jsonl   # heldout, CHỈ CHẠY THỦ CÔNG
    python eval/run_golden_set.py --sample 12               # debug nhanh, không dùng trên CI

Thang nghiêm trọng (mục 7 FIN05-StressTest-Plan.md), xếp theo vi phạm NẶNG
NHẤT phát hiện được trong 1 case:
    Blocker  — vi phạm `forbidden` (bịa số liệu/PDPA/lộ tín hiệu/gian lận...)
               hoặc trích dẫn tool_result sai (A3 chống bịa số liệu)
    Critical — sai tín hiệu FS-06 (escalate nhầm/bỏ sót case cần escalate)
    High     — sai complaint_type/scope/priority/logic tạo ticket
    (không có vi phạm nào) — Pass
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval._harness import (
    build_eval_session,
    cau_hinh_dinh_tuyen_luc_chay,
    check_expected,
    check_forbidden,
    load_jsonl,
    now_stamp,
    run_case_turns_adaptive,
)

EVAL_DIR = Path(__file__).resolve().parent


def _severity_for_case(violations: list[str], checks: list[tuple[str, bool]]) -> str:
    if violations or any(name.startswith("cite_") and not ok for name, ok in checks):
        return "Blocker"
    if any(name == "fraud_signal_fs06" and not ok for name, ok in checks):
        return "Critical"
    if any(not ok for _, ok in checks):
        return "High"
    return "Pass"


def _customer_phone(session, user_id: str) -> str | None:
    from src.db.models import User

    user = session.get(User, user_id)
    return user.phone if user else None


def run(cases: list[dict]) -> list[dict]:
    with tempfile.TemporaryDirectory(prefix="fin05_eval_") as tmp:
        db_path = Path(tmp) / "eval.db"
        session = build_eval_session(db_path)

        results = []
        for i, case in enumerate(cases, start=1):
            case_id = case["case_id"]
            print(f"[{i}/{len(cases)}] {case_id} ({case['cell']})...", file=sys.stderr)
            try:
                agent_result = run_case_turns_adaptive(session, case=case, thread_id=f"EVAL-{case_id}")
                reply = agent_result.get("reply", "")
                checks = check_expected(session, agent_result, case.get("expected") or {})
                # Quét forbidden trên TOÀN BỘ lượt trả lời (kể cả lượt mô
                # phỏng thêm), không chỉ lượt cuối — 1 câu vi phạm ở giữa hội
                # thoại vẫn là vi phạm thật dù lượt cuối agent chốt đúng.
                all_replies = agent_result.get("all_agent_replies") or [reply]
                all_customer_texts = agent_result.get("all_customer_texts") or case.get("utterances")
                own_phone = _customer_phone(session, case["user_id"])
                violations = []
                seen = set()
                for r in all_replies:
                    for v in check_forbidden(
                        r, case.get("forbidden"), utterances=all_customer_texts, customer_own_phone=own_phone
                    ):
                        if v not in seen:
                            seen.add(v)
                            violations.append(v)
                severity = _severity_for_case(violations, checks)
            except Exception as e:  # lỗi hệ thống khi chạy case — tự nó là 1 phát hiện, không được để sập cả batch
                checks = []
                violations = [f"LỖI CHẠY CASE: {e!r}"]
                severity = "Blocker"
                reply = ""
                agent_result = {}
            session.rollback()  # mỗi case độc lập — không để side-effect case này ảnh hưởng case sau

            results.append(
                {
                    "case_id": case_id,
                    "cell": case["cell"],
                    "difficulty": case.get("difficulty"),
                    "edge_type": case.get("edge_type"),
                    "severity": severity,
                    "checks": checks,
                    "violations": violations,
                    "reply": reply,
                    "all_agent_replies": agent_result.get("all_agent_replies") or [reply],
                    "all_customer_texts": agent_result.get("all_customer_texts") or case.get("utterances"),
                    "tool_calls": [c.get("tool_name") for c in agent_result.get("tool_calls", [])],
                    "extra_turns_used": agent_result.get("extra_turns_used", 0),
                    # ĐƯỜNG ĐỊNH TUYẾN mỗi lượt (`nhe`/`thu_slot`/`day_du`) — ①
                    # đợt "OTP trước token" 24/08, đóng Đ2 cùng
                    # `cau_hinh_dinh_tuyen_luc_chay()` ở header báo cáo.
                    "duong_theo_luot": agent_result.get("duong_theo_luot") or [],
                }
            )
        session.close()
    return results


def write_report(results: list[dict], out_path: Path) -> None:
    total = len(results)
    passed = sum(1 for r in results if r["severity"] == "Pass")
    by_cell = defaultdict(lambda: [0, 0])
    by_difficulty = defaultdict(lambda: [0, 0])
    by_severity = Counter(r["severity"] for r in results)
    # ① — phân bố ĐƯỜNG ĐỊNH TUYẾN toàn corpus (đếm LƯỢT, không đếm CA — một
    # ca nhiều lượt có thể đổi đường giữa chừng). `None` = bản `run_agent_turn`
    # đang chạy chưa trả khoá `duong` (bản cũ hơn hạng mục ①).
    duong_dem = Counter(
        d for r in results for d in (r.get("duong_theo_luot") or [None])
    )

    for r in results:
        by_cell[r["cell"] or "(edge case, ngoài ma trận)"][1] += 1
        by_difficulty[r.get("difficulty") or "(không gắn nhãn)"][1] += 1
        if r["severity"] == "Pass":
            by_cell[r["cell"] or "(edge case, ngoài ma trận)"][0] += 1
            by_difficulty[r.get("difficulty") or "(không gắn nhãn)"][0] += 1

    extra_turn_cases = [r for r in results if r.get("extra_turns_used")]

    lines = [
        f"# Báo cáo eval golden_set — {now_stamp()}",
        "",
        "> ⚠️ **Đường eval dùng sentinel `_ALWAYS_FRESH`** (`run_agent_turn`, "
        "`graph.py`) — OTP phiên LUÔN được coi là vừa xác thực xong. Không ca "
        "nào ở đây đo được hành vi khi OTP thiếu/hết hạn; trục đó chỉ đo được "
        "bằng chạy thật (`fin05do`/production) — xem finding A2 24/08.",
        "> ⚠️ **Harness gọi thẳng `run_agent_turn()` trong tiến trình** — JWT/"
        "rate-limit/audit-log KHÔNG nằm trên đường đo này. Kết luận về các "
        "tầng đó từ kết quả eval là kết luận SAI CHỖ ĐO; xem "
        "`tests/test_api/` cho bộ test có đi qua các tầng đó.",
        f"> 🚦 **{cau_hinh_dinh_tuyen_luc_chay()}.** Đóng Đ2 (24/08) — trước hạng "
        "mục này, không báo cáo eval nào từng in giá trị đang chạy, nên eval và "
        "sản phẩm có thể đã chạy hai cấu hình khác nhau mà không ai biết.",
        "> 🚦 **Phân bố đường định tuyến toàn corpus (đếm LƯỢT):** "
        + " · ".join(f"`{k}`={v}" for k, v in duong_dem.most_common()),
        "",
        f"**Tổng:** {passed}/{total} pass ({passed / total * 100:.1f}%)" if total else "Không có case nào.",
        f"**Cần mô phỏng thêm lượt hội thoại (Hướng 1 — xem eval/_harness.py::run_case_turns_adaptive):** "
        f"{len(extra_turn_cases)}/{total} case (trung bình "
        f"{sum(r['extra_turns_used'] for r in extra_turn_cases) / len(extra_turn_cases):.1f} lượt thêm)"
        if extra_turn_cases else "**Không case nào cần mô phỏng thêm lượt** (mọi case hoàn tất đúng kịch bản gốc).",
        "",
        "## Theo mức nghiêm trọng",
        "",
        "| Mức | Số case |",
        "|---|---|",
    ]
    for sev in ("Blocker", "Critical", "High", "Pass"):
        lines.append(f"| {sev} | {by_severity.get(sev, 0)} |")

    lines += ["", "## Theo ô ma trận (4 loại × 3 phạm vi)", "", "| Ô | Pass/Tổng |", "|---|---|"]
    for cell, (p, t) in sorted(by_cell.items()):
        lines.append(f"| {cell} | {p}/{t} |")

    lines += ["", "## Theo độ khó", "", "| Độ khó | Pass/Tổng |", "|---|---|"]
    for diff, (p, t) in sorted(by_difficulty.items()):
        lines.append(f"| {diff} | {p}/{t} |")

    # ① — bảng ĐẦY ĐỦ mọi case, kể cả case PASS. Không có bảng này thì một ca
    # "xanh vì đi thu_slot, chưa từng chạm model/O1-O5" trông giống hệt một ca
    # xanh thật trên báo cáo — đúng lỗ Đ1 mô tả (2 ca adversarial ADV-036/
    # ADV-038 "xanh" nhưng lớp phòng thủ chưa từng chạy).
    lines += ["", "## Đường định tuyến mỗi ca (`duong`, đọc được không cần mở code)", "",
              "| Case | Đường đi từng lượt | Có chạm model? |", "|---|---|---|"]
    for r in results:
        dtl = r.get("duong_theo_luot") or []
        cham_model = "có" if any(d == "day_du" for d in dtl) else ("KHÔNG — toàn nhe/thu_slot" if dtl else "?")
        lines.append(f"| {r['case_id']} | {', '.join(str(d) for d in dtl) or '(rỗng)'} | {cham_model} |")

    failing = [r for r in results if r["severity"] != "Pass"]
    if failing:
        lines += ["", "## Chi tiết case KHÔNG pass", ""]
        for r in sorted(failing, key=lambda x: {"Blocker": 0, "Critical": 1, "High": 2}[x["severity"]]):
            lines.append(f"### {r['case_id']} — {r['severity']} ({r['cell']}, {r.get('difficulty')})")
            failed_checks = [name for name, ok in r["checks"] if not ok]
            if failed_checks:
                lines.append(f"- Sai lệch: {', '.join(failed_checks)}")
            if r["violations"]:
                lines.append(f"- Vi phạm forbidden: {'; '.join(r['violations'])}")
            lines.append(f"- Tool đã gọi: {', '.join(r['tool_calls']) or '(không)'}")
            if r.get("extra_turns_used"):
                lines.append(f"- Đã mô phỏng thêm {r['extra_turns_used']} lượt hội thoại, vẫn không đạt")
            all_replies = r.get("all_agent_replies") or [r["reply"]]
            if r["violations"] and len(all_replies) > 1:
                # Vi phạm có thể nằm ở lượt GIỮA hội thoại (đã mô phỏng thêm),
                # không phải lượt cuối — hiện đủ toàn bộ hội thoại để audit tay
                # (Hướng 2) xác định đúng lượt nào chứa câu vi phạm.
                lines.append("- Toàn bộ hội thoại (để xác định đúng lượt vi phạm):")
                all_customer = r.get("all_customer_texts") or []
                for idx, agent_reply in enumerate(all_replies):
                    customer_text = all_customer[idx] if idx < len(all_customer) else "(?)"
                    lines.append(f"  - Khách (lượt {idx + 1}): {customer_text[:200]!r}")
                    lines.append(f"  - Agent (lượt {idx + 1}): {agent_reply[:300]!r}")
            else:
                lines.append(f"- Reply: {r['reply'][:300]!r}")
            lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nBáo cáo: {out_path}", file=sys.stderr)
    print(f"Tổng: {passed}/{total} pass ({passed / total * 100:.1f}%)" if total else "0 case", file=sys.stderr)
    # `by_severity` là Counter dựng TỪ results ⟹ khoá vắng nghĩa là ĐẾM ĐƯỢC 0,
    # đúng nghĩa. `.get(sev, 0)` ở đây KHÔNG phải mặc-định-im-lặng.
    #
    # Nhưng có một trường hợp thật mà nó nói dối: **không có result nào**, hoặc
    # có result mà `severity` rỗng/None. Khi đó bảng in `Blocker=0` từ ZERO DỮ
    # LIỆU — và "0 Blocker" với "chưa đo được" trông giống hệt nhau trên slide.
    thieu_sev = [r for r in results if not r.get("severity")]
    if not results or thieu_sev:
        print(f"🔴 KHÔNG ĐỌC ĐƯỢC dòng severity dưới đây: "
              f"{len(results)} result, {len(thieu_sev)} thiếu trường `severity`. "
              "Số 0 ở đây là ZERO DỮ LIỆU, không phải KHÔNG CÓ LỖI.", file=sys.stderr)
    print(f"Blocker={by_severity.get('Blocker', 0)} Critical={by_severity.get('Critical', 0)} "
          f"High={by_severity.get('High', 0)}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--file", type=Path, default=EVAL_DIR / "golden_set.jsonl")
    parser.add_argument("--sample", type=int, default=None, help="Chỉ chạy N case đầu (debug, KHÔNG dùng trên CI)")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    cases = load_jsonl(args.file)
    if args.sample:
        # 1 case/ô ma trận cho smoke test nhanh — không random để tái lập được
        seen_cells = set()
        sampled = []
        for c in cases:
            if c["cell"] not in seen_cells:
                sampled.append(c)
                seen_cells.add(c["cell"])
            if len(sampled) >= args.sample:
                break
        cases = sampled

    print(f"🚦 {cau_hinh_dinh_tuyen_luc_chay()}", file=sys.stderr)
    print(f"Chạy {len(cases)} case từ {args.file} — mỗi case gọi OpenAI thật.", file=sys.stderr)
    results = run(cases)

    out_dir = EVAL_DIR / "results"
    out_dir.mkdir(exist_ok=True)
    stamp = now_stamp()

    # Lưu raw JSON NGAY sau khi chạy xong, TRƯỚC khi format báo cáo markdown —
    # mỗi case vừa tốn tiền gọi OpenAI thật, không được để 1 lỗi format báo
    # cáo (vd sort() gặp None) làm mất toàn bộ kết quả đã tốn phí thu được.
    raw_path = out_dir / f"golden_run_{stamp}_raw.json"
    raw_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Raw JSON (khôi phục nếu format báo cáo lỗi): {raw_path}", file=sys.stderr)

    out_path = args.out or out_dir / f"golden_run_{stamp}.md"
    write_report(results, out_path)

    blocker_or_critical = sum(1 for r in results if r["severity"] in ("Blocker", "Critical"))
    sys.exit(1 if blocker_or_critical > 0 else 0)


if __name__ == "__main__":
    main()
