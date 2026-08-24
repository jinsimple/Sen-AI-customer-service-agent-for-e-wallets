#!/usr/bin/env python3
"""ĐO N1 — cổng `thu_slot` bắn bao nhiêu lần trên CORPUS GỐC `eval/*.jsonl`.

    python eval/do_n1_corpus_goc.py [<luat_nen.py>]

Dựng nền để so:  `git show a3bc860:src/agents/phan_luong.py > /tmp/pl_nen.py`

🔴 `heldout_set.jsonl` LOẠI TUYỆT ĐỐI — niêm phong (`CLAUDE.md` §6).

## Nguồn gốc — Coder, 25/08, đợt "OTP trước token"

QA/QC dựng `eval/bo_ca_am_thu_slot_dot2.json` (② trong đợt) là bộ **7 ca
độc lập** dựng TỪ ĐẶC TẢ Đ1 — đúng, nhưng "xanh trên bản dựng lại không
chứng minh gì về corpus gốc" (lớp lỗi đội đã bắt nhiều lần trong dự án này).
Coder viết script này, đo TRỰC TIẾP trên toàn bộ 14 tệp `eval/*.jsonl` thật
đang có — [ĐO 25/08, QA/QC tái lập ĐỘC LẬP, khớp tuyệt đối]: 409 câu, nền
`a3bc860` bắn 15 lần, HEAD bắn 13 lần. Chỉ đóng được 2 (= ADV-036 + ADV-038).

## Mẫu số GHIM, không phải số đếm — nguyên văn lời Coder, không diễn rộng

> *"đừng ghim ngưỡng 13 — nó sẽ đỏ ngay khi ai đó thêm một ca vào corpus, và
> người sau sẽ hạ ngưỡng thay vì đọc. Cái đáng ghim là mẫu số 409 và DANH
> SÁCH 13 câu."*

Bộ bóc câu đã hỏng HAI LẦN lúc Coder dựng (7/409 rồi 349/409, mù
`utterances` dạng list rồi mù `query_co_dau`) — cả hai lần lệch theo hướng
TRẤN AN (mẫu số nhỏ hơn, tưởng đã đóng hết). Mẫu số khác 409 ⟹ ĐỪNG tin số
bắn — script tự kiểm bằng `MAU_SO_MOC`.

## 🔴 ĐÍNH CHÍNH 25/08 — quyết định `return 0` vô điều kiện là của QA/QC, KHÔNG PHẢI Coder

Bản đầu của file này (do QA/QC viết khi nhận vào `eval/`) ghi nhầm "giữ
nguyên quyết định của Coder: luôn `return 0`". **Sai** — Coder chỉ nói câu
trích ở trên (đừng ghim SỐ ĐẾM), và tự nhận xét thêm:

> *"ghim DANH SÁCH ... là một cổng pass/fail hợp lệ, và nó bắt được đúng
> thứ ta vừa suýt bỏ lỡ ... `return 0` vô điều kiện thì không ai bị đánh
> thức khi điều đó xảy ra lần nữa."*

QA/QC đã tự diễn rộng thành "không cổng hoá" rồi gán nhầm cho Coder —
Coder chưa hề loại phương án cổng-theo-danh-sách. Sửa lại: **cổng hoá theo
DANH SÁCH (không phải số đếm) là quyết định của QA/QC, 25/08, sau khi
Coder chỉ ra chỗ sai.**

## Cách cổng hoạt động — so DANH SÁCH, không so SỐ

`eval/n1_bao_oan_da_biet.json` ghim 13 câu đã biết (kèm tệp nguồn, băm
`bam_nhan`). Mỗi lần chạy:
- Câu bắn `thu_slot` mà KHÔNG có trong danh sách ⟹ **REGRESSION MỚI**,
  thoát mã khác 0.
- Câu CÓ trong danh sách mà HẾT bắn ⟹ in ra để người chạy tự cập nhật danh
  sách (xoá phần tử, tính lại `bam_nhan`) — không tự động xoá, tránh một
  script tự sửa "vật chứng" của chính nó.
- Mẫu số khác `MAU_SO_MOC` (409) ⟹ thoát mã khác 0, không tin số bắn.
"""
from __future__ import annotations

import glob
import hashlib
import importlib.util
import json
import pathlib
import sys

KHOA_CHUOI = ("cau", "input", "message", "text", "prompt", "query_co_dau")
KHOA_LIST = ("utterances", "turns", "luot", "messages")
KHOA_TRONG_DICT = ("cau", "content", "text", "user", "utterance")

MAU_SO_MOC = 409  # [ĐO 25/08] — đổi số này CHỈ khi đã xác nhận corpus THẬT đổi, không phải bộ bóc hỏng
GOC = pathlib.Path(__file__).resolve().parent.parent
FILE_DA_BIET = GOC / "eval" / "n1_bao_oan_da_biet.json"


def nap(duong_dan, ten):
    sp = importlib.util.spec_from_file_location(ten, duong_dan)
    m = importlib.util.module_from_spec(sp)
    sys.modules[ten] = m
    sp.loader.exec_module(m)
    return m


def cau_trong(d):
    out = []
    for k in KHOA_CHUOI:
        v = d.get(k)
        if isinstance(v, str) and v.strip():
            out.append(v)
    for k in KHOA_LIST:
        v = d.get(k)
        if not isinstance(v, list):
            continue
        for x in v:
            if isinstance(x, str) and x.strip():
                out.append(x)
            elif isinstance(x, dict):
                for kk in KHOA_TRONG_DICT:
                    if isinstance(x.get(kk), str) and x[kk].strip():
                        out.append(x[kk])
                        break
    return out


def _bam_nhan(d: dict) -> str:
    t = {k: v for k, v in d.items() if k not in ("bam_nhan", "thuat_toan_bam")}
    return hashlib.sha256(
        json.dumps(t, ensure_ascii=False, indent=1, sort_keys=True).encode()
    ).hexdigest()[:12]


def main() -> int:
    moi = nap("src/agents/phan_luong.py", "_luat_head")
    nen = nap(sys.argv[1], "_luat_nen") if len(sys.argv) > 1 else None
    files = [f for f in sorted(glob.glob("eval/*.jsonl")) if "heldout" not in f]
    tong = nen_n = moi_n = 0
    con_ban: list[tuple[str, str]] = []
    for f in files:
        for line in open(f, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            for c in cau_trong(d):
                tong += 1
                if nen and nen.phan_luong(c)[0] == "thu_slot":
                    nen_n += 1
                if moi.phan_luong(c)[0] == "thu_slot":
                    moi_n += 1
                    con_ban.append((f.split("/")[-1], c))

    print(f"MẪU SỐ {tong} câu / {len(files)} tệp   (heldout LOẠI — niêm phong)")
    if tong != MAU_SO_MOC:
        print(f"  🔴 MẪU SỐ KHÁC {MAU_SO_MOC} (mốc 25/08) — bộ bóc đã lệch, ĐỪNG dùng kết quả.")
        return 2
    if nen:
        print(f"  nền  {sys.argv[1]}  → thu_slot {nen_n}")
    print(f"  HEAD → thu_slot {moi_n}\n")

    if not FILE_DA_BIET.exists():
        print(f"🔴 thiếu {FILE_DA_BIET} — không so được với danh sách đã ghim.")
        return 2
    da_biet_raw = json.loads(FILE_DA_BIET.read_text(encoding="utf-8"))
    bam_thuc, bam_ghi = _bam_nhan(da_biet_raw), da_biet_raw.get("bam_nhan")
    if bam_thuc != bam_ghi:
        print(f"🔴 {FILE_DA_BIET.name} ĐÃ TRÔI: băm ghi {bam_ghi} ≠ tính lại {bam_thuc} — TỪ CHỐI SO.")
        return 2
    da_biet = {(c["tep"], c["cau"]) for c in da_biet_raw["ca"]}

    hien_tai = set(con_ban)
    moi_regression = sorted(hien_tai - da_biet)
    da_dong = sorted(da_biet - hien_tai)

    for f, c in con_ban:
        danh_dau = "🆕 MỚI" if (f, c) not in da_biet else "  (đã biết)"
        print(f"  {danh_dau} [{f}] {c[:88]}")

    if da_dong:
        print(f"\n  ✅ {len(da_dong)} câu trong danh sách đã ghim KHÔNG còn bắn — cập nhật "
              f"{FILE_DA_BIET.name} (xoá phần tử, tính lại bam_nhan):")
        for f, c in da_dong:
            print(f"     [{f}] {c[:88]}")

    if moi_regression:
        print(f"\n🔴 REGRESSION MỚI — {len(moi_regression)} câu bắn `thu_slot` mà KHÔNG có trong "
              f"{FILE_DA_BIET.name}:")
        for f, c in moi_regression:
            print(f"     [{f}] {c[:88]}")
        return 1

    print("\n✅ Không có regression mới ngoài danh sách đã ghim.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
