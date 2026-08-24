#!/usr/bin/env python3
"""CỔNG ĐỐI CHỨNG ÂM cho `thu_slot` — đợt "OTP trước token", hạng mục ② (24/08).

    python eval/cong_ca_am_thu_slot_dot2.py --luat <đường dẫn phan_luong.py>

Nguồn đặc tả: `docs/giao-viec/2026-08-24-dot-otp-truoc-token.md` §3 Đ1 + §4.
Bộ ca: `eval/bo_ca_am_thu_slot_dot2.json`.

Tự chứa, không phụ thuộc `eval/cong_phan_luong.py` — bộ ca này CHỦ Ý phải
ĐỎ trên HEAD hiện tại (đo hành vi bắn oan trước khi vá), khác mục đích của
cổng chính (đo hồi quy trên luật đã vá). Gộp chung sẽ làm cổng chính đỏ vì
lý do không phải của nó.

Ba nguyên tắc mượn lại từ `cong_phan_luong.py` (đã đắt tiền, không phát
minh lại): kiểm băm bộ ca trước khi chấm · cảnh báo khi `--luat` đang dirty
(không chặn, chỉ tự khai thân phận) · in đủ TÊN TỪNG CA sai, không chỉ đếm.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pathlib
import subprocess
import sys

GOC = pathlib.Path(__file__).resolve().parent.parent


def _dang_dirty(p: pathlib.Path) -> bool:
    try:
        r = subprocess.run(
            ["git", "status", "--porcelain", "--", str(p.resolve())],
            capture_output=True, text=True, cwd=GOC, timeout=10,
        )
    except Exception:  # noqa: BLE001
        return False
    return bool(r.stdout.strip())


def _bam_nhan(d: dict) -> str:
    t = {k: v for k, v in d.items() if k not in ("bam_nhan", "thuat_toan_bam")}
    return hashlib.sha256(
        json.dumps(t, ensure_ascii=False, indent=1, sort_keys=True).encode()
    ).hexdigest()[:12]


def _nap_luat(p: pathlib.Path):
    spec = importlib.util.spec_from_file_location("luat_dot2", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--luat", required=True, help="đường dẫn phan_luong.py (khuyên dùng bản ĐÃ COMMIT)")
    ap.add_argument("--bo-qua-bam", action="store_true", help="CHỈ để dò lỗi lúc soạn bộ ca")
    a = ap.parse_args()

    p_luat = pathlib.Path(a.luat)
    if not p_luat.exists():
        print(f"🔴 không thấy luật: {p_luat}")
        return 2
    dirty = _dang_dirty(p_luat)
    if dirty:
        print(f"  ⚠️  ĐANG ĐO BẢN CHƯA CHỐT — {p_luat} có sửa đổi CHƯA COMMIT.")
        print("      Kết quả KHÔNG dùng để tick CHECKLIST/báo cáo — chỉ hợp lệ để tự dò lúc dev.")
    print(f"  LUẬT   {p_luat} · sha256[:12]={hashlib.sha256(p_luat.read_bytes()).hexdigest()[:12]}")
    luat = _nap_luat(p_luat)

    p_ca = GOC / "eval" / "bo_ca_am_thu_slot_dot2.json"
    d = json.loads(p_ca.read_text(encoding="utf-8"))
    thuc, ghi = _bam_nhan(d), d.get("bam_nhan")
    if thuc != ghi and not a.bo_qua_bam:
        print(f"🔴 BỘ CA ĐÃ TRÔI: băm ghi {ghi} ≠ tính lại {thuc} — TỪ CHỐI CHẤM.")
        return 2
    print(f"  BỘ CA  {p_ca.name} · {len(d['ca'])} ca [{ghi}]")

    sai = []
    for c in d["ca"]:
        duong, ly_do, *_ = luat.phan_luong(c["cau"])
        ok = duong == c["ky_vong"]
        trang = "✅" if ok else "🔴"
        print(f"  {trang} {c['id']:16s} [{c['truc']}]")
        print(f"       câu:    {c['cau']!r}")
        print(f"       mong:   {c['ky_vong']}  ·  thực: {duong}  ·  lý_do: {ly_do}")
        if not ok:
            sai.append(c["id"])

    n = len(d["ca"])
    print(f"\n  ⟹ {n - len(sai)}/{n} khớp kỳ vọng.")
    if sai:
        print(f"  🔴 ĐỎ — {len(sai)} ca: {', '.join(sai)}")
    else:
        print("  ✅ XANH — không ca nào lệch kỳ vọng.")
    if dirty:
        print("  ⚠️  Nhắc lại: bản luật vừa chấm ĐANG DIRTY, số trên KHÔNG dùng để tick/báo cáo.")
        return 4
    return 1 if sai else 0


if __name__ == "__main__":
    sys.exit(main())
