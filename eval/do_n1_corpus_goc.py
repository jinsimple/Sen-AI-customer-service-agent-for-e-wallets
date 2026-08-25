#!/usr/bin/env python3
"""ĐO N1 — cổng `thu_slot` bắn bao nhiêu lần trên CORPUS GỐC `eval/*.jsonl`.

    python eval/do_n1_corpus_goc.py [--luat <phan_luong.py>] [--nen <phan_luong.py>]

`--luat` mặc định bản thật trong repo (`src/agents/phan_luong.py`) — trỏ vào
bản KHÁC (cũ/đột biến/ngoài repo) để bất kỳ vai nào cũng kiểm chéo được cả
hai vế của Luật A (cổng có KÊU đúng lúc không) **mà không cần sửa
`eval/n1_bao_oan_da_biet.json`** (vùng ghi QA/QC) — [PO 25/08] đề xuất sau
khi tự thấy giới hạn: chỉ chạy được vế IM (`exit 0`), không dựng được ca
phá vì sẽ phải chạm vùng ghi người khác.

Dựng nền để so:  `git show a3bc860:src/agents/phan_luong.py > /tmp/pl_nen.py`
rồi `--nen /tmp/pl_nen.py`.

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

## 🔴 TRỤC KHÔNG ĐO — [PO 25/08, phát hiện qua `--luat` trên bản đột biến]

Cổng này CHỈ bắt DƯƠNG TÍNH GIẢ (câu không nên bắn mà bắn). Nó **MÙ HOÀN
TOÀN** với ÂM TÍNH GIẢ — một bản vá làm `phan_luong()` **không bao giờ**
trả `thu_slot` cho câu nào (giết sạch cổng `thu_slot`) sẽ cho corpus gốc
**0 dương tính giả**, và N1 báo `exit 0` — "đạt", trong khi cổng đã chết.
Phép thử Luật R: *"nếu ai xoá `DOT2-DUONG-01` (ca dương duy nhất còn lại),
cái gì kêu?"* → **N1 vẫn xanh.**

**Cổng bù trục này:** `eval/bo_ca_am_thu_slot_dot2.json` (chạy qua
`eval/cong_ca_am_thu_slot_dot2.py`) — case `DOT2-DUONG-01` là ca DƯƠNG duy
nhất, kỳ vọng `thu_slot`. Cổng đó bắt đúng khi `phan_luong()` bị giết sạch
(đã tự kiểm 25/08). Hai cổng BÙ NHAU theo hai chiều của Luật A — không cổng
nào một mình đủ để nói "cổng `thu_slot` đang hoạt động đúng".

Cũng KHÔNG phân biệt "bắn OAN" với "bắn ĐÚNG nhưng không phải oan" — xem
field `bat_oan` trong `n1_bao_oan_da_biet.json` (phân loại thủ công, không
phải phép đo tự động của chính script này).
"""
from __future__ import annotations

import argparse
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
    ap = argparse.ArgumentParser()
    # `--luat` — [PO 25/08] gỡ đúng nút "vai khác không kiểm chéo được vế KÊU của
    # Luật A vì phải chạm eval/n1_bao_oan_da_biet.json (vùng ghi QA/QC)". Trỏ
    # `--luat` vào một bản phan_luong.py cũ/đột biến NGOÀI repo là dựng được ca
    # phá mà không cần sửa file nào trong vùng của QA/QC — cùng khuôn
    # `cong_ca_am_thu_slot_dot2.py` đã dùng cho ②.
    ap.add_argument("--luat", default="src/agents/phan_luong.py",
                     help="đường dẫn phan_luong.py coi là HEAD/hiện hành (mặc định: bản thật trong repo)")
    ap.add_argument("--nen", default=None,
                     help="đường dẫn phan_luong.py NỀN để so token (tuỳ chọn, không tham gia diff regression)")
    a = ap.parse_args()

    moi = nap(a.luat, "_luat_head")
    nen = nap(a.nen, "_luat_nen") if a.nen else None
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
        print(f"  nền  {a.nen}  → thu_slot {nen_n}")
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
    # bat_oan: True = bắn OAN thật · False = bắn ĐÚNG (khớp ngoại lệ ĐC-5, vd
    # NP-2/CASE-041) · None = chưa xác định. [PO 25/08] "13 câu bắn" KHÔNG
    # đồng nghĩa "13 câu bắn OAN" — số này tự thân KHÔNG đo được sự khác biệt
    # đó, đây là phân loại THỦ CÔNG đính kèm, không phải phép đo.
    bat_oan = {(c["tep"], c["cau"]): c.get("bat_oan") for c in da_biet_raw["ca"]}

    hien_tai = set(con_ban)
    moi_regression = sorted(hien_tai - da_biet)
    da_dong = sorted(da_biet - hien_tai)

    dem_oan = dem_dung = dem_chua_ro = dem_moi = 0
    for f, c in con_ban:
        key = (f, c)
        if key not in da_biet:
            danh_dau, dem_moi = "🆕 MỚI (chưa phân loại)", dem_moi + 1
        else:
            v = bat_oan.get(key)
            if v is True:
                danh_dau, dem_oan = "  (đã biết, OAN)", dem_oan + 1
            elif v is False:
                danh_dau, dem_dung = "  (đã biết, ĐÚNG — không phải oan)", dem_dung + 1
            else:
                danh_dau, dem_chua_ro = "  (đã biết, chưa rõ oan/đúng)", dem_chua_ro + 1
        print(f"  {danh_dau} [{f}] {c[:88]}")

    print(f"\n  Trong {len(con_ban)} câu bắn `thu_slot`: {dem_oan} OAN thật · {dem_dung} ĐÚNG "
          f"(không phải oan) · {dem_chua_ro} chưa phân loại · {dem_moi} mới ngoài danh sách.")

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
