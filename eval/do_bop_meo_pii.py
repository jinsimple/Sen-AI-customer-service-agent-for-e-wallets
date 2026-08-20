#!/usr/bin/env python3
"""Đo tỉ lệ bóp méo `scrub_pii(muc_dich="model_input")` trên corpus THẬT
`eval/golden_set.jsonl` (utterances trải phẳng) — ngưỡng PRD §17: ≤ 6%.

Dựng lại phép đo 5,6% (`docs/security/2026-08-19-quyet-dinh-bien-du-lieu-
regex-only-model-input.md:85,90`) thành cổng chạy-lại-được, thay vì một con
số đo một lần rồi mục trong hồ sơ. Mẫu tham khảo: script scratchpad phiên
PO-agent 19/08 (`do_bop_meo_pii.py`, đọc corpus giống hệt, phần "TOÀN CORPUS
— tỉ lệ có bị chèn ÍT NHẤT 1 nhãn" — đúng cơ chế sinh ra 49,2%/12,9%/4,8%/
5,6%). KHÁC bản scratchpad ở chỗ: script này CHỈ đo bản SAU (đang chạy),
không nạp bản pii.py TRƯỚC vá qua importlib — đó là dữ kiện lịch sử một lần,
không phải thứ cần tái lập mỗi lần chạy CI.

Corpus KHÔNG phải "của QA/QC riêng" (cách gọi trong docs/security đã trôi
khỏi vật nó chỉ, PO-agent niêm lại 20/08) — nó CHÍNH LÀ `eval/golden_set.jsonl`,
đếm theo CÂU (utterances trải phẳng, 124), không theo DÒNG (case, 120).
Corpus đổi số câu mà không ai biết thì mọi tỉ lệ % sau đó đổi nghĩa im lặng —
ghim `124` là một assert, không phải một chú thích.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.observability.pii import scrub_pii  # noqa: E402

_MAU_NHAN = re.compile(r"\[[A-Z_]+\]")
_SO_CAU_KY_VONG = 124
_NGUONG_PRD_17 = 6.0  # PRD §17: "bóp méo câu tiếng Việt ≤ 6%"


def _doc_utterances():
    with open(ROOT / "eval" / "golden_set.jsonl", encoding="utf-8") as f:
        for dong in f:
            dong = dong.strip()
            if not dong:
                continue
            d = json.loads(dong)
            for cau in d.get("utterances", []):
                yield d["case_id"], cau


def main() -> int:
    tat_ca = list(_doc_utterances())

    if len(tat_ca) != _SO_CAU_KY_VONG:
        print(
            f"🔴 CORPUS ĐỔI SỐ CÂU: golden_set.jsonl trải phẳng ra {len(tat_ca)} câu, "
            f"kỳ vọng {_SO_CAU_KY_VONG}. Mọi % đo trước đây (49,2%/12,9%/4,8%/5,6%) đứng trên "
            f"mẫu số {_SO_CAU_KY_VONG} — không còn so sánh được với con số mới cho tới khi ai "
            "đó xác nhận lại có ý nghĩa gì.",
            file=sys.stderr,
        )
        return 2

    bi_bop_meo = []
    for case_id, cau in tat_ca:
        ra = scrub_pii(cau, muc_dich="model_input")
        if _MAU_NHAN.search(ra):
            bi_bop_meo.append((case_id, cau, ra))

    tu_so = len(bi_bop_meo)
    mau_so = len(tat_ca)
    ty_le = 100 * tu_so / mau_so

    print(f"Corpus: {mau_so} câu (eval/golden_set.jsonl, utterances trải phẳng)")
    print(f"Bị chèn ÍT NHẤT 1 nhãn [XXX]: {tu_so}/{mau_so} ({ty_le:.1f}%)")
    print(f"Ngưỡng PRD §17: ≤ {_NGUONG_PRD_17:.0f}%")

    if bi_bop_meo:
        print("\nVí dụ (tối đa 5 câu đầu bị bóp méo):")
        for case_id, goc, ra in bi_bop_meo[:5]:
            print(f"  [{case_id}] gốc={goc!r}\n           sau={ra!r}")

    if ty_le > _NGUONG_PRD_17:
        print(
            f"\n🔴 VI PHẠM PRD §17: {tu_so}/{mau_so} = {ty_le:.1f}% > {_NGUONG_PRD_17:.0f}%.",
            file=sys.stderr,
        )
        return 1

    print(f"\n✅ ĐẠT PRD §17 ({ty_le:.1f}% ≤ {_NGUONG_PRD_17:.0f}%).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
