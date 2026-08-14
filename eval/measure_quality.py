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


def dau_thuoc() -> dict[str, str]:
    """Đóng dấu THƯỚC vào file raw — để máy tự canh luật paired eval.

    Luật đã phê chuẩn 14/08: mọi báo cáo đo ghi commit của thước, và một cặp
    paired eval chỉ hợp lệ khi hai nhánh dùng CÙNG thước. Trước đây là quy ước
    người phải nhớ; đóng dấu vào file làm `so_sanh()` tự đối chiếu được.

    ĐO BẰNG BĂM NỘI DUNG, KHÔNG BẰNG COMMIT HEAD — điểm này quan trọng và tôi
    suýt làm sai: nếu lấy `git rev-parse HEAD` thì MỌI commit đều đổi dấu, kể
    cả commit chỉ thêm công cụ báo cáo (như chính commit thêm hàm này), và
    `so_sanh()` sẽ hô "hai thước khác nhau" cho một cặp đo hoàn toàn hợp lệ —
    một báo động giả đủ sức khiến người ta phải chạy lại 40 case vô ích, hoặc
    tệ hơn, khiến họ học cách bỏ qua cảnh báo.

    Chỉ băm thứ THẬT SỰ quyết định điểm số: logic check (`_harness.py`) và bộ
    case (`golden_set.jsonl`). Sửa cách in báo cáo không đổi dấu; sửa một
    check hay một nhãn kỳ vọng thì đổi ngay.

    `commit` vẫn được ghi kèm nhưng chỉ để TRA CỨU, không dùng để so.
    """
    import hashlib
    import subprocess

    h = hashlib.sha256()
    for ten in ("_harness.py", "golden_set.jsonl"):
        f = EVAL_DIR / ten
        h.update(f.read_bytes() if f.exists() else b"")
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5, cwd=EVAL_DIR.parent,
        ).stdout.strip() or "khong-ro"
    except Exception:  # noqa: BLE001
        commit = "khong-ro"
    return {"cham_diem": h.hexdigest()[:12], "commit": commit}


def _tap_check_hong(r: dict) -> set[str]:
    """Rút TẬP HỢP tên check đang hỏng của một case, từ mọi định dạng raw.

    `measure_quality.py` lưu `checks_failed` (danh sách tên); `run_golden_set.py`
    lưu `checks` (danh sách cặp [tên, đạt]). Đọc được cả hai để so sánh chéo
    được giữa hai loại lượt chạy.
    """
    if r.get("checks_failed") is not None:
        hong = set(r.get("checks_failed") or [])
    else:
        hong = {ten for ten, dat in (r.get("checks") or []) if not dat}
    hong |= {f"forbidden:{v}" for v in (r.get("forbidden_violations") or [])}
    if r.get("error"):
        hong.add("LỖI_HỆ_THỐNG")
    return hong


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
        dau = dau_thuoc()  # tính 1 lần cho cả lượt — mọi case cùng một thước
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
                luot_tao_ticket = agent_result.get("luot_tao_ticket")
                error = None
            except Exception as e:  # lỗi khi chạy case là 1 phát hiện thật, không phải lý do bỏ case
                elapsed = time.perf_counter() - t0
                checks = []
                forbidden_violations = [f"LỖI CHẠY CASE: {e!r}"]
                unfounded_amounts = []
                unverified_system_ids = []
                usage = {}
                reply = ""
                # D1: case lỗi giữa chừng vẫn phải giữ lại những gì đã nói được
                # trước khi chết — đó thường là chỗ chứa nguyên nhân.
                all_replies = []
                all_customer_texts = list(case.get("utterances") or [])
                tool_calls = []
                ticket_id = None
                luot_tao_ticket = None
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
                    # D1 — TRANSCRIPT ĐỦ LƯỢT, không chỉ lượt cuối.
                    # `reply` là reply của LƯỢT CUỐI. Hai vai đã vấp đúng chỗ
                    # này: đọc `reply` rồi kết luận "agent không tra cứu gì"
                    # trong khi việc tra cứu xảy ra ở lượt trước và đã bị ghi
                    # đè. Khi phải điều tra một ca hồi quy, thứ cần là toàn bộ
                    # hội thoại — mà lúc đó lượt đo đã chạy xong, không quay
                    # lại lấy được. Nên phải lưu NGAY lúc chạy.
                    "all_agent_replies": all_replies,
                    "all_customer_texts": all_customer_texts,
                    "tool_calls": [c.get("tool_name") for c in tool_calls],
                    "luot_tao_ticket": luot_tao_ticket,
                    "_thuoc": dau,
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


def _nhom_a1() -> set[str]:
    """Case thuộc nhóm A1 — khuyết tật dữ liệu `from_bank`, không phải lỗi agent.

    Nhận diện bằng `scope == "from_bank"` đọc thẳng từ `golden_set.jsonl` chứ
    KHÔNG hardcode danh sách case_id: reseed sắp tới sẽ đổi bộ case, một danh
    sách chép tay sẽ lỗi thời trong im lặng và tiếp tục loại nhầm/bỏ sót.

    Khi dữ liệu `from_bank` được sinh lại đúng contract (ví nhận là ví khách),
    nhóm này KHÔNG còn là "dữ liệu hỏng" nữa — lúc đó phải bỏ tầng lọc này,
    nếu không nó sẽ âm thầm che mất hồi quy thật ở 1/3 ma trận nghiệp vụ.
    Ghi rõ ở đây vì đó là ngày mà hàm này trở nên nguy hiểm.
    """
    f = EVAL_DIR / "golden_set.jsonl"
    if not f.exists():
        return set()
    a1 = set()
    for dong in f.read_text(encoding="utf-8").splitlines():
        if not dong.strip():
            continue
        try:
            d = json.loads(dong)
        except json.JSONDecodeError:
            continue
        if d.get("scope") == "from_bank":
            a1.add(d.get("case_id"))
    return a1


def _mo_ta_thuoc(t: dict | None) -> str:
    """In dấu thước cho người đọc: mã chấm điểm + commit tra cứu."""
    if not t:
        return "KHÔNG ĐÓNG DẤU (file raw cũ)"
    return f"{t.get('cham_diem', '?')} @ {t.get('commit', '?')}"


def so_sanh(truoc_path: Path, sau_path: Path, out_path: Path | None = None) -> int:
    """So sánh TẬP HỢP check hỏng giữa hai lượt đo — trả số ca xấu đi.

    VÌ SAO PHẢI SO TẬP HỢP, KHÔNG SO SỐ ĐẾM: đây chính là thứ đã cứu gói B2.
    Một case có thể hỏng 1 check ở lượt trước và hỏng 1 check ở lượt sau — số
    đếm y hệt, tổng "x/40 pass" y hệt, báo cáo nói "không đổi". Nhưng đó có
    thể là **một lỗi được vá và một lỗi mới sinh ra**. Nhìn bằng số đếm thì
    hai chuyện triệt tiêu nhau và biến mất; nhìn bằng tập hợp thì cả hai hiện
    ra. Một prompt "không làm tệ đi về tổng thể" mà làm hỏng một ô nghiệp vụ
    khác là điều PHẢI thấy trước khi merge.

    Ba nhóm kết quả tách bạch:
      - XẤU ĐI  : check hỏng ở lượt SAU mà lượt TRƯỚC không hỏng → chặn merge
      - TỐT LÊN : check hỏng ở lượt TRƯỚC mà lượt SAU hết hỏng  → giá trị thật
      - LỆCH BỘ : case chỉ có ở một lượt → hai lượt KHÔNG so được, báo ngay
    """
    def _nap(p: Path) -> list[dict]:
        """Nạp file raw, báo lỗi ĐỌC ĐƯỢC thay vì ném traceback.

        Có thật trong repo một file tên `*_raw.json` nhưng nội dung là báo cáo
        Markdown (ai đó trỏ nhầm `--out`) — đã đổi tên 14/08. Công cụ này sẽ
        được dùng lúc gấp, giữa một cổng đo; một traceback JSONDecodeError ở
        đúng lúc đó là thứ tốn thời gian vô ích nhất.
        """
        try:
            du_lieu = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            sys.exit(f"'{p}' không phải JSON hợp lệ ({e}). Cần file *_raw.json do lượt đo sinh ra, không phải báo cáo .md.")
        if not isinstance(du_lieu, list):
            sys.exit(f"'{p}' không phải danh sách kết quả case.")
        return du_lieu

    truoc = _nap(truoc_path)
    sau = _nap(sau_path)
    idx_truoc = {r["case_id"]: r for r in truoc}
    idx_sau = {r["case_id"]: r for r in sau}

    thuoc_truoc = next((r.get("_thuoc") for r in truoc if r.get("_thuoc")), None)
    thuoc_sau = next((r.get("_thuoc") for r in sau if r.get("_thuoc")), None)

    lines = [
        f"# So sánh hai lượt đo — {now_stamp()}",
        "",
        f"- TRƯỚC: `{truoc_path.name}` ({len(truoc)} case) · thước `{_mo_ta_thuoc(thuoc_truoc)}`",
        f"- SAU  : `{sau_path.name}` ({len(sau)} case) · thước `{_mo_ta_thuoc(thuoc_sau)}`",
        "",
    ]

    # --- Cảnh báo chặn: hai nhánh đo bằng hai thước khác nhau ---------------
    if thuoc_truoc and thuoc_sau and thuoc_truoc["cham_diem"] != thuoc_sau["cham_diem"]:
        lines += [
            "> 🔴 **HAI LƯỢT DÙNG HAI THƯỚC KHÁC NHAU** "
            f"(`{thuoc_truoc['cham_diem']}` vs `{thuoc_sau['cham_diem']}`). Chênh lệch dưới đây KHÔNG quy được "
            "cho thay đổi prompt — nó lẫn cả thay đổi của chính bộ chấm. Chạy lại "
            "nhánh TRƯỚC trên thước mới rồi hãy đọc tiếp.",
            "",
        ]
    elif not (thuoc_truoc and thuoc_sau):
        lines += [
            "> ⚠️ Có lượt chưa đóng dấu commit thước (file raw cũ). Không tự đối chiếu "
            "được — người đọc phải tự xác nhận hai lượt cùng thước.",
            "",
        ]

    chi_truoc = sorted(set(idx_truoc) - set(idx_sau))
    chi_sau = sorted(set(idx_sau) - set(idx_truoc))
    if chi_truoc or chi_sau:
        lines += [
            "## 🔴 LỆCH BỘ CASE — hai lượt không so trực tiếp được",
            "",
            f"- Chỉ có ở TRƯỚC ({len(chi_truoc)}): {', '.join(chi_truoc) or '—'}",
            f"- Chỉ có ở SAU ({len(chi_sau)}): {', '.join(chi_sau) or '—'}",
            "",
        ]

    xau_di: list[tuple[str, set[str]]] = []
    tot_len: list[tuple[str, set[str]]] = []
    doi_tap_giu_so_luong: list[str] = []

    for case_id in sorted(set(idx_truoc) & set(idx_sau)):
        h_truoc = _tap_check_hong(idx_truoc[case_id])
        h_sau = _tap_check_hong(idx_sau[case_id])
        moi = h_sau - h_truoc
        het = h_truoc - h_sau
        if moi:
            xau_di.append((case_id, moi))
        if het:
            tot_len.append((case_id, het))
        if moi and het and len(h_truoc) == len(h_sau):
            doi_tap_giu_so_luong.append(case_id)

    lines += [
        "## Tổng kết",
        "",
        f"- **Ca XẤU ĐI: {len(xau_di)}** (có check hỏng MỚI)",
        f"- Ca TỐT LÊN: {len(tot_len)}",
        f"- Ca đổi tập nhưng GIỮ NGUYÊN SỐ LƯỢNG: **{len(doi_tap_giu_so_luong)}** "
        "← nhóm mà so-sánh-bằng-số-đếm sẽ báo 'không đổi'",
        "",
    ]

    if doi_tap_giu_so_luong:
        lines += [
            "> Chính nhóm này là lý do bảng so sánh tồn tại: tổng số case pass không "
            f"đổi, nhưng {len(doi_tap_giu_so_luong)} case đã đổi *bản chất* lỗi.",
            "",
        ]

    if xau_di:
        # TẦNG 1 của quy tắc đọc nhiễu (PO duyệt 14/08): loại ca A1 khỏi nhóm
        # ứng viên tín hiệu TRƯỚC khi giao tập. Ca `from_bank` mang khuyết tật
        # dữ liệu đã biết — bộ sinh gán ví nhận KHÔNG phải của khách, nên
        # KHÔNG cải tiến prompt nào cứu được (xem
        # eval/results/trige_29_case_20260814.md nhóm A1). Trộn chúng vào ứng
        # viên tín hiệu sẽ dẫn tới đọc transcript tìm hồi quy prompt cho một
        # lỗi gốc là dữ liệu — tức sửa đúng thứ không hỏng.
        #
        # Tự động hoá ở đây thay vì bắt người nhớ: người đọc báo cáo lúc đang
        # gấp sẽ không dừng lại tra từng case_id xem nó có scope from_bank không.
        a1 = _nhom_a1()
        tin_hieu = [(c, m) for c, m in xau_di if c not in a1]
        du_lieu_hong = [(c, m) for c, m in xau_di if c in a1]

        lines += [
            "## 🔴 XẤU ĐI — chặn merge cho tới khi giải thích được",
            "",
            f"Tách theo quy tắc đọc nhiễu 3 tầng: **{len(tin_hieu)} ứng viên tín hiệu** · "
            f"{len(du_lieu_hong)} ca thuộc nhóm A1 (khuyết tật dữ liệu `from_bank`).",
            "",
            "### Ứng viên TÍN HIỆU — chỉ nhóm này đáng đọc transcript",
            "",
        ]
        for case_id, moi in tin_hieu:
            lines.append(f"- **{case_id}**: hỏng thêm `{'`, `'.join(sorted(moi))}`")
        if not tin_hieu:
            lines.append("- (không có)")
        lines.append("")

        if du_lieu_hong:
            lines += [
                "### Nhóm A1 — dữ liệu hỏng, KHÔNG phải bằng chứng hồi quy prompt",
                "",
                "> Ca `from_bank` có ví nhận gán sai (không phải ví khách). Xấu đi ổn định "
                "ở nhóm này chứng minh **dữ liệu vẫn hỏng** — thứ đã biết và đã có reseed — "
                "chứ không chứng minh prompt hồi quy. Nếu giao tập chỉ còn ca ở nhóm này, "
                "gate coi như ĐẠT.",
                "",
            ]
            for case_id, moi in du_lieu_hong:
                lines.append(f"- {case_id}: hỏng thêm `{'`, `'.join(sorted(moi))}`")
            lines.append("")

        lines += [
            "> **Tầng 2 và 3** (máy chưa làm thay được): lặp N lượt cùng cấu hình rồi lấy "
            "**GIAO** các tập ứng viên tín hiệu ở trên. Ca xấu ở MỌI lượt = tín hiệu; ca "
            "xấu một lượt = nhiễu temperature. KHÔNG dùng ngưỡng theo số đếm — 14 xấu/18 "
            "tốt có thể là 32 lần flip ngẫu nhiên, mà cũng có thể là 1 hồi quy thật lẫn "
            "trong 31 lần flip; hai tình huống cho cùng một con số.",
            "",
        ]

    if tot_len:
        lines += ["## ✅ TỐT LÊN", ""]
        for case_id, het in tot_len:
            lines.append(f"- {case_id}: hết hỏng `{'`, `'.join(sorted(het))}`")
        lines.append("")

    bia_truoc = {r["case_id"] for r in truoc if r.get("unfounded_amounts")}
    bia_sau = {r["case_id"] for r in sau if r.get("unfounded_amounts")}
    lines += [
        "## Gate bịa số liệu (0% là điều kiện cứng)",
        "",
        f"- TRƯỚC: {len(bia_truoc)} case · SAU: {len(bia_sau)} case",
        f"- Bịa MỚI xuất hiện: {', '.join(sorted(bia_sau - bia_truoc)) or '—'}",
        "",
    ]

    bao_cao = "\n".join(lines)
    if out_path:
        out_path.write_text(bao_cao, encoding="utf-8")
        print(f"Báo cáo so sánh: {out_path}", file=sys.stderr)
    print(bao_cao)
    return len(xau_di)


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
    parser.add_argument(
        "--so-sanh", type=Path, nargs=2, default=None, metavar=("TRUOC_raw.json", "SAU_raw.json"),
        help="So sánh TẬP HỢP check hỏng giữa 2 lượt đo (offline, không gọi LLM). "
             "Thoát mã 1 nếu có ca XẤU ĐI — dùng được làm cổng chặn merge.",
    )
    args = parser.parse_args()

    if args.so_sanh is not None:
        truoc, sau = args.so_sanh
        out = args.out or (EVAL_DIR / "results" / f"so_sanh_{now_stamp()}.md")
        # Thoát khác 0 khi có ca xấu đi: để CI/script gọi được như một cổng,
        # không phải thứ người phải đọc rồi tự nhớ kết luận.
        sys.exit(1 if so_sanh(truoc, sau, out) else 0)

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
