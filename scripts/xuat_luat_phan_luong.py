#!/usr/bin/env python3
"""Xuất bản chạy-được của luật phân luồng cho tester chấm — SINH TỪ `src/`.

    python scripts/xuat_luat_phan_luong.py --ra <duong_dan>.py

VÌ SAO TỒN TẠI: tester **không đọc `src/`** (hiến pháp §4), nên họ cần một file
chạy được. Nhưng hai bản sao chép tay thì **lệch**, và nó đã lệch thật:

    tester chấm 15/20 trên  md5 1edd51dff555
    cổng của họ chạy trên   md5 0885bab00a04   (tôi đã gỡ DAI_TOI_DA giữa chừng)

Không có gì báo đỏ. Tester gọi đúng tên nó: *"luật đổi dưới chân tôi giữa hai
lần đo"*. Lần đó chưa hại vì R1 chưa chạy; xen giữa R1 và R2 thì phép so chết
mà không ai thấy.

⟹ Bản xuất **sinh từ `src/agents/phan_luong.py`**, không gõ lại. Một nguồn, một
dẫn xuất. File xuất tự mang băm của **cả hai** để không ai phải đoán.

CỐ Ý KHÔNG làm bản xuất thành `import src.agents.phan_luong`: nếu tester chạy
được import đó thì họ đang chạy `src/` đang có trên đĩa, và **hai lần chạy cách
nhau một commit sẽ là hai vật khác nhau mà không lộ ra**. File tĩnh + băm thì lộ.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent / "src" / "agents" / "phan_luong.py"

# Cắt từ hằng số đầu tiên tới hết — bỏ phần import và docstring module, thêm
# lại phần chạy được. Mốc cắt là MỘT dòng cố định; nếu nó biến mất thì script
# DỪNG chứ không đoán (mất mốc = bản xuất có thể thiếu một mệnh đề, và một luật
# thiếu mệnh đề vẫn chạy được, vẫn cho ra số, chỉ là sai).
MOC = 'DUONG_NHE = "nhe"'

DAU = '''#!/usr/bin/env python3
"""SINH TỰ ĐỘNG bởi scripts/xuat_luat_phan_luong.py — ĐỪNG SỬA TAY.

Sửa tay ở đây là tạo lại đúng sự cố hai-băm mà file này sinh ra để chống.
Nguồn: src/agents/phan_luong.py

    bam_nguon = {bam_nguon}   (md5-toan-file-12 của src/agents/phan_luong.py)
    bam_ban_xuat: in ra khi chạy
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import sys
import unicodedata
from pathlib import Path

_logger = logging.getLogger("fin05.phan_luong")
BAM_NGUON = "{bam_nguon}"

'''

DUOI = '''

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vao", required=True)
    ap.add_argument("--truong", default="cau")
    ap.add_argument("--mong-doi", default=None, choices=["nhe", "day_du"])
    a = ap.parse_args()

    ban_xuat = hashlib.md5(Path(__file__).read_bytes()).hexdigest()[:12]
    print(f"  bam_nguon={BAM_NGUON} · bam_ban_xuat={ban_xuat} (md5-toan-file-12)",
          file=sys.stderr)

    f = sys.stdin if a.vao == "-" else open(a.vao, encoding="utf-8")
    n = dat = 0
    truot = []
    for dong in f:
        dong = dong.strip()
        if not dong:
            continue
        d = json.loads(dong)
        cau = d.get(a.truong)
        if cau is None:
            print(f"THIẾU trường {a.truong!r} — dừng. Khoá có: {sorted(d)}", file=sys.stderr)
            return 2
        qd, ly_do = phan_luong(cau)
        n += 1
        if a.mong_doi:
            ok = qd == a.mong_doi
            dat += ok
            if not ok:
                truot.append((d.get("case_id") or d.get("id") or n, cau, qd, ly_do))
        else:
            print(json.dumps({"cau": cau, "duong": qd, "ly_do": ly_do}, ensure_ascii=False))

    if a.mong_doi:
        print(f"  {dat}/{n} ĐẠT (mong đợi tất cả = {a.mong_doi!r})")
        for cid, cau, qd, ly in truot:
            print(f"    TRƯỢT [{cid}] {cau[:52]!r} -> {qd} · {ly}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ra", required=True)
    a = ap.parse_args()

    goc = GOC.read_text(encoding="utf-8")
    if MOC not in goc:
        print(f"KHÔNG tìm thấy mốc cắt {MOC!r} trong {GOC} — luật đã đổi cấu trúc. "
              f"DỪNG, không đoán: một bản xuất thiếu mệnh đề vẫn chạy và vẫn cho ra số.",
              file=sys.stderr)
        return 2

    bam_nguon = hashlib.md5(GOC.read_bytes()).hexdigest()[:12]
    than = goc[goc.index(MOC):]
    # `BAM_LUAT` trong src tự băm CHÍNH file src; trong bản xuất nó sẽ băm nhầm
    # bản xuất. Gỡ hẳn để không có hai thứ cùng tên nói hai chuyện.
    than = "\n".join(d for d in than.splitlines()
                     if not d.startswith(("BAM_LUAT", "CACH_BAM_LUAT")))

    ra = Path(a.ra)
    ra.write_text(DAU.format(bam_nguon=bam_nguon) + than + DUOI, encoding="utf-8")
    bam_xuat = hashlib.md5(ra.read_bytes()).hexdigest()[:12]
    print(f"  {GOC.name} (md5 {bam_nguon})  ->  {ra}  (md5 {bam_xuat})")
    print("  cách băm: md5-toan-file-12 · đưa CẢ HAI cho tester")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
