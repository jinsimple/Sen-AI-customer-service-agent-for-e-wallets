#!/usr/bin/env python3
"""Đo drift chất lượng "thực tế" trên agent FIN-05 THẬT (OpenAI thật, tốn phí)
— lấy cảm hứng từ câu hỏi "bạn biết agent chậm/đắt/bịa khi nào? Khi user phàn
nàn — cách tệ nhất và đắt nhất để phát hiện vấn đề". Đo 3 chỉ số đúng tinh
thần đó thay vì đợi user report:

    1. Latency (p50/p95 giây/lượt, giây/case)
    2. Cost (ước lượng theo giá OPENAI_MODEL, xem _PRICE_PER_1M_TOKENS)
    3. "Bịa số liệu" — heuristic: số tiền (chuỗi >=4 chữ số) xuất hiện trong
       reply nhưng KHÔNG có trong tool_calls (dữ liệu tool thật đã tra) lẫn
       utterances (số khách tự cung cấp) -> cờ nghi vấn để người xem lại, KHÔNG
       phải oracle NLU hoàn hảo (giống check_forbidden ở _harness.py).

VÁ QA-03 (biên bản QA 13/08): mã định danh hệ thống trong reply (TCK-/RES-/
CHS-...) chứa chuỗi số dài — đường fallback-timeout trả mã ticket mà KHÔNG có
tool_call ghi lại, làm heuristic cũ cờ nhầm chính mã ticket THẬT thành "bịa"
(7/7 cờ của cả baseline lẫn run 13/08 đều là loại này, đã đối chiếu DB).
Giờ tách 3 lớp, không gộp:
    - `unfounded_amounts`      — số KHÔNG thuộc ID hệ thống nào: nghi bịa thật.
    - (loại thẳng)             — số thuộc ID hệ thống ĐÃ XÁC MINH tồn tại
                                 (result.ticket_id hoặc tra thấy trong DB phiên đo).
    - `unverified_system_ids`  — số thuộc ID hệ thống KHÔNG xác minh được:
                                 vẫn hiện ra cho người xem, không âm thầm bỏ.

Dùng:
    python eval/measure_quality.py                    # 24 case mẫu (stratified theo cell), golden_set
    python eval/measure_quality.py --n 40              # tuỳ chỉnh cỡ mẫu
    python eval/measure_quality.py --file eval/adversarial_set.jsonl --n 15
    python eval/measure_quality.py --rescore eval/results/<run>_raw.json
        # chấm LẠI offline một file raw đã lưu bằng thước mới — không gọi LLM,
        # không tốn phí; ID hệ thống trong chế độ này chỉ phân loại được là
        # "chưa đối chiếu DB" (DB tạm của run gốc đã bị xoá).

Giá OPENAI_MODEL là ƯỚC LƯỢNG (hardcode theo giá công bố tại thời điểm viết,
không phải số hoá đơn thật) — chỉ để có cảm nhận thứ tự độ lớn (order of
magnitude), KHÔNG dùng để đối chiếu billing thật.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval._harness import (
    build_eval_session,
    check_expected,
    check_forbidden,
    load_jsonl,
    now_stamp,
    run_case_turns_adaptive,
)
from src.config import OPENAI_MODEL

EVAL_DIR = Path(__file__).resolve().parent

# USD/1M token, ước lượng tại thời điểm viết (2026-08-10) — KHÔNG phải giá
# billing thật, chỉ để có thứ tự độ lớn. Cập nhật nếu OpenAI đổi giá.
_PRICE_PER_1M_TOKENS: dict[str, tuple[float, float]] = {
    "gpt-4o-mini": (0.150, 0.600),  # (input, output)
    "gpt-4o": (2.50, 10.00),
}

# Số tiền VND thường >=4 chữ số (>=1.000đ) — lọc bớt false positive từ hằng số
# chính sách 1-3 chữ số (vd "48 giờ", "30 ngày", "4 ngày làm việc") vốn không
# phải "số liệu giao dịch" cần grounding vào tool result.
_AMOUNT_RE = re.compile(r"\d{1,3}(?:[.,]\d{3})+|\d{4,}")

# Mã định danh hệ thống xuất hiện trong reply (vd "mã ticket của bạn là
# TCK-38750618ef4b") — phần hex chứa chuỗi số dài, KHÔNG phải số tiền.
_SYSTEM_ID_RE = re.compile(r"\b(?:TCK|RES|CHS|SES|TR|MSG)-[0-9A-Za-z]{4,}\b")


def _digits_only(s: str) -> str:
    return re.sub(r"\D", "", s)


def _extract_amount_digit_runs(text: str) -> set[str]:
    return {_digits_only(m.group()) for m in _AMOUNT_RE.finditer(text)}


def _grounding_digit_runs(tool_calls: list[dict], utterances: list[str]) -> set[str]:
    blob = json.dumps(tool_calls, ensure_ascii=False) + " " + " ".join(utterances)
    return _extract_amount_digit_runs(blob)


def split_unfounded_amounts(
    reply: str,
    tool_calls: list[dict],
    utterances: list[str],
    verified_ids: set[str] | None = None,
) -> tuple[list[str], list[str]]:
    """Phân loại chuỗi số trong `reply` không khớp dữ liệu tool/lời khách:

    Trả `(suspects, unverified_system_ids)`:
    - `suspects`: số KHÔNG nằm trong bất kỳ ID hệ thống nào của reply — ứng
      viên bịa thật, cần người xem lại (vẫn không phải oracle).
    - `unverified_system_ids`: số nằm trong một ID hệ thống của reply nhưng ID
      đó KHÔNG có trong `verified_ids` — hiện ra minh bạch thay vì âm thầm bỏ
      (một mã TCK bịa hoàn toàn vẫn phải nhìn thấy được).
    Số nằm trong ID hệ thống ĐÃ xác minh (`verified_ids`) bị loại hẳn — đó là
    mã thật hệ thống sinh ra, không phải agent bịa (gốc QA-03)."""
    verified_ids = verified_ids or set()
    reply_amounts = _extract_amount_digit_runs(reply)
    grounded = _grounding_digit_runs(tool_calls, utterances)
    reply_ids = _SYSTEM_ID_RE.findall(reply)
    suspects: list[str] = []
    unverified: list[str] = []
    for a in sorted(reply_amounts - grounded):
        owner = next((tok for tok in reply_ids if a in _digits_only(tok)), None)
        if owner is None:
            suspects.append(a)
        elif owner not in verified_ids:
            unverified.append(f"{a} (trong {owner})")
    return suspects, unverified


def _verify_reply_system_ids(session, reply: str, result: dict) -> set[str]:
    """Xác minh các ID hệ thống trong reply: khớp `result.ticket_id` (payload
    có cấu trúc từ agent — kể cả đường fallback) hoặc tra thấy trong DB phiên
    đo. Import model tại chỗ để chế độ --rescore chạy được không cần src/DB."""
    from src.db.models import ChatSession, Resolution, Ticket

    lookup = {"TCK": Ticket, "RES": Resolution, "CHS": ChatSession}
    verified: set[str] = set()
    for tok in set(_SYSTEM_ID_RE.findall(reply)):
        if tok == result.get("ticket_id"):
            verified.add(tok)
            continue
        model = lookup.get(tok.split("-", 1)[0])
        if model is not None and session.get(model, tok) is not None:
            verified.add(tok)
    return verified


def _sample_stratified_by_cell(cases: list[dict], n: int) -> list[dict]:
    """Lấy mẫu rải đều theo `cell` (ma trận 4 loại × 3 phạm vi) nếu case có
    field đó (golden_set), ngược lại lấy N case đầu — KHÔNG random để tái lập
    được kết quả giữa các lần chạy (đúng cách run_golden_set.py --sample đã
    làm cho mục đích debug nhanh, tái dùng lại tinh thần đó)."""
    if n >= len(cases):
        return cases
    if not any(c.get("cell") for c in cases):
        return cases[:n]
    by_cell: dict[str, list[dict]] = {}
    for c in cases:
        by_cell.setdefault(c.get("cell") or "(none)", []).append(c)
    sampled: list[dict] = []
    cell_keys = sorted(by_cell)
    i = 0
    while len(sampled) < n:
        cell = cell_keys[i % len(cell_keys)]
        bucket = by_cell[cell]
        if bucket:
            sampled.append(bucket.pop(0))
        i += 1
        if all(not v for v in by_cell.values()):
            break
    return sampled


def run(cases: list[dict]) -> list[dict]:
    with tempfile.TemporaryDirectory(prefix="fin05_quality_") as tmp:
        db_path = Path(tmp) / "quality.db"
        session = build_eval_session(db_path)

        results = []
        for i, case in enumerate(cases, start=1):
            case_id = case.get("case_id", f"CASE-{i}")
            print(f"[{i}/{len(cases)}] {case_id}...", file=sys.stderr)
            t0 = time.perf_counter()
            try:
                agent_result = run_case_turns_adaptive(session, case=case, thread_id=f"QUALITY-{case_id}")
                elapsed = time.perf_counter() - t0
                reply = agent_result.get("reply", "")
                all_replies = agent_result.get("all_agent_replies") or [reply]
                all_customer_texts = agent_result.get("all_customer_texts") or case.get("utterances") or []
                tool_calls = agent_result.get("tool_calls") or []
                usage = agent_result.get("usage") or {}

                checks = check_expected(session, agent_result, case.get("expected") or {})
                forbidden_violations = []
                for r in all_replies:
                    forbidden_violations.extend(
                        check_forbidden(r, case.get("forbidden"), utterances=all_customer_texts)
                    )
                unfounded_amounts = []
                unverified_system_ids = []
                for r in all_replies:
                    verified = _verify_reply_system_ids(session, r, agent_result)
                    suspects, unverified = split_unfounded_amounts(
                        r, tool_calls, all_customer_texts, verified_ids=verified
                    )
                    unfounded_amounts.extend(suspects)
                    unverified_system_ids.extend(unverified)

                ticket_id = agent_result.get("ticket_id")
                error = None
            except Exception as e:  # lỗi khi chạy case là 1 phát hiện thật, không phải lý do bỏ case
                elapsed = time.perf_counter() - t0
                checks = []
                forbidden_violations = [f"LỖI CHẠY CASE: {e!r}"]
                unfounded_amounts = []
                unverified_system_ids = []
                usage = {}
                reply = ""
                ticket_id = None
                error = repr(e)
            session.rollback()

            results.append(
                {
                    "case_id": case_id,
                    "elapsed_seconds": round(elapsed, 3),
                    "usage": usage,
                    "checks_failed": [name for name, ok in checks if not ok],
                    "forbidden_violations": forbidden_violations,
                    "unfounded_amounts": unfounded_amounts,
                    "unverified_system_ids": unverified_system_ids,
                    "ticket_id": ticket_id,
                    "reply": reply,
                    "error": error,
                }
            )
        session.close()
    return results


def write_report(results: list[dict], out_path: Path) -> None:
    total = len(results)
    latencies = [r["elapsed_seconds"] for r in results if r["error"] is None]
    input_price, output_price = _PRICE_PER_1M_TOKENS.get(OPENAI_MODEL, (0.0, 0.0))
    costs = []
    for r in results:
        u = r.get("usage") or {}
        cost = (u.get("input_tokens", 0) / 1e6) * input_price + (u.get("output_tokens", 0) / 1e6) * output_price
        r["cost_usd_estimate"] = round(cost, 6)
        costs.append(cost)

    hallucinated = [r for r in results if r["unfounded_amounts"]]
    errored = [r for r in results if r["error"] is not None]
    quality_failed = [r for r in results if r["checks_failed"] or r["forbidden_violations"]]

    def _pctl(data: list[float], p: float) -> float:
        if not data:
            return 0.0
        s = sorted(data)
        idx = min(len(s) - 1, int(round(p * (len(s) - 1))))
        return s[idx]

    lines = [
        f"# Đo drift chất lượng agent (thực tế, OpenAI thật) — {now_stamp()}",
        "",
        f"Model: `{OPENAI_MODEL}` — {total} case.",
        "",
        "## 1. Latency",
        "",
        f"- p50: {_pctl(latencies, 0.5):.2f}s | p95: {_pctl(latencies, 0.95):.2f}s | max: {max(latencies, default=0):.2f}s",
        f"- Trung bình: {statistics.fmean(latencies):.2f}s/case" if latencies else "- (không có case chạy thành công)",
        "",
        "## 2. Cost (ước lượng, KHÔNG phải billing thật)",
        "",
        f"- Tổng: ${sum(costs):.4f} cho {total} case | Trung bình: ${statistics.fmean(costs):.5f}/case" if costs else "- (không có dữ liệu)",
        f"- Giá dùng để ước lượng: input ${input_price}/1M token, output ${output_price}/1M token ({OPENAI_MODEL})",
        "",
        "## 3. Bịa số liệu (ứng viên, cần người xem lại — không phải oracle)",
        "",
        f"- {len(hallucinated)}/{total} case có ít nhất 1 số tiền trong reply KHÔNG khớp dữ liệu tool/lời khách"
        f" ({len(hallucinated) / total * 100:.1f}%)" if total else "- (không có case)",
        f"- {sum(1 for r in results if r.get('unverified_system_ids'))}/{total} case có số nằm trong ID hệ thống"
        " CHƯA đối chiếu được DB (xem chi tiết — không tính vào tỉ lệ bịa, không âm thầm bỏ)",
        "",
        "## 4. Lỗi hệ thống / vi phạm chất lượng khác",
        "",
        f"- Case lỗi khi chạy: {len(errored)}/{total}",
        f"- Case sai lệch checks/forbidden pattern (không tính bịa số liệu riêng ở mục 3): {len(quality_failed)}/{total}",
        "",
    ]

    if hallucinated:
        lines += ["## Chi tiết case bị flag bịa số liệu", ""]
        for r in hallucinated:
            lines.append(f"### {r['case_id']}")
            lines.append(f"- Số nghi vấn: {', '.join(r['unfounded_amounts'])}")
            lines.append(f"- Reply: {r['reply'][:300]!r}")
            lines.append("")

    sysid_cases = [r for r in results if r.get("unverified_system_ids")]
    if sysid_cases:
        lines += ["## Số trong ID hệ thống CHƯA đối chiếu DB (minh bạch, không tính vào mục 3)", ""]
        for r in sysid_cases:
            lines.append(f"- {r['case_id']}: {', '.join(r['unverified_system_ids'])}")
        lines.append("")

    if errored:
        lines += ["## Chi tiết case lỗi hệ thống", ""]
        for r in errored:
            lines.append(f"- {r['case_id']}: {r['error']}")
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nBáo cáo: {out_path}", file=sys.stderr)
    print(
        f"Latency p50={_pctl(latencies, 0.5):.2f}s p95={_pctl(latencies, 0.95):.2f}s | "
        f"Cost tổng=${sum(costs):.4f} | Bịa số liệu={len(hallucinated)}/{total} "
        f"({(len(hallucinated) / total * 100) if total else 0:.1f}%)",
        file=sys.stderr,
    )


def rescore(raw_path: Path) -> None:
    """Chấm LẠI một file raw đã lưu bằng thước QA-03 — offline, không gọi LLM.

    File raw cũ không lưu tool_calls nên KHÔNG tính lại grounding từ đầu —
    chỉ PHÂN LOẠI LẠI các số đã bị cờ: số nằm trong một ID hệ thống của chính
    reply đó chuyển sang `unverified_system_ids` (DB tạm của run gốc đã xoá,
    không đối chiếu tồn tại được — người xem tự đối chiếu DB thật nếu cần);
    số còn lại giữ nguyên là nghi bịa thật."""
    results = json.loads(raw_path.read_text(encoding="utf-8"))
    for r in results:
        reply_ids = _SYSTEM_ID_RE.findall(r.get("reply") or "")
        suspects: list[str] = []
        unverified: list[str] = []
        for a in r.get("unfounded_amounts") or []:
            owner = next((tok for tok in reply_ids if a in _digits_only(tok)), None)
            if owner is None:
                suspects.append(a)
            else:
                unverified.append(f"{a} (trong {owner})")
        r["unfounded_amounts"] = suspects
        r["unverified_system_ids"] = (r.get("unverified_system_ids") or []) + unverified

    out_json = raw_path.with_name(raw_path.stem + "_rescored.json")
    out_json.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md = raw_path.with_name(raw_path.stem + "_rescored.md")
    write_report(results, out_md)
    print(f"Rescore JSON: {out_json}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--file", type=Path, default=EVAL_DIR / "golden_set.jsonl")
    parser.add_argument("--n", type=int, default=24, help="Cỡ mẫu (stratified theo cell nếu có)")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument(
        "--rescore", type=Path, default=None,
        help="Chấm lại offline một file *_raw.json đã lưu bằng thước QA-03 (không gọi LLM, không tốn phí)",
    )
    args = parser.parse_args()

    if args.rescore is not None:
        rescore(args.rescore)
        return

    all_cases = load_jsonl(args.file)
    cases = _sample_stratified_by_cell(all_cases, args.n)

    print(f"Chạy {len(cases)}/{len(all_cases)} case từ {args.file} — mỗi case gọi OpenAI thật.", file=sys.stderr)
    results = run(cases)

    out_dir = EVAL_DIR / "results"
    out_dir.mkdir(exist_ok=True)
    stamp = now_stamp()

    raw_path = out_dir / f"quality_run_{stamp}_raw.json"
    raw_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Raw JSON: {raw_path}", file=sys.stderr)

    out_path = args.out or out_dir / f"quality_run_{stamp}.md"
    write_report(results, out_path)


if __name__ == "__main__":
    main()
