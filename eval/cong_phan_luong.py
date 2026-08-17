#!/usr/bin/env python3
"""CỔNG cho cờ `PHAN_LUONG_BAT` — chạy lại được, 0 lượt LLM.

    python eval/cong_phan_luong.py --luat <đường dẫn quy_tac_phan_luong.py>

## Vì sao là một LỆNH chứ không phải một lần chạy tay

Cờ này sẽ bật/tắt nhiều lần trong đợt đo. **Mỗi lần bật phải qua cổng**, không
phải chỉ lần đầu — vì thứ đổi giữa hai lần bật (danh sách từ, một ngưỡng, một
mệnh đề bị xoá) chính là thứ không ai nghĩ cần chạy lại.

## Ba nguyên tắc đã đắt tiền, mã hoá thẳng vào đây

**① Kiểm BĂM BỘ CA trước khi chấm.** Chấm một bộ ca đã trôi rồi báo số là báo
về một vật không còn tồn tại. Cổng **từ chối chạy**, không cảnh báo rồi chạy
tiếp.

**② In PHÂN BỐ LÝ DO, không chỉ tỉ lệ** (Luật E). `124/124` từng đạt với
**0 ca** nào chạm mệnh đề chính của thiết kế — một nhánh chưa khai hoả lần nào
là một nhánh **chưa được kiểm**, dù tỉ lệ có là 100%.

**③ Băm khai kèm TÊN THUẬT TOÁN** (Luật 18). `1edd51dff555` và `742df94b195a`
là **cùng một file**, khác thuật toán, và không ai kiểm vì cả hai đều là 12 ký
tự hex.

## 🔴 ĐC-1..5 — CHƯA ĐỦ ĐỊNH NGHĨA, và cổng NỔ thay vì bỏ qua

PO giao *"ĐC-1..5 thành bộ cổng chính thức"*. Tôi tìm trong `docs/` và
**không thấy định nghĩa nào**. Tôi biết chắc hai cái qua tin nhắn:

    ĐC-2  phân loại theo TỪNG LƯỢT, không theo phiên
    ĐC-5  toàn bộ bộ ca âm phải đi đường đầy đủ

Ba cái còn lại tôi **không biết**, và **không đoán** — một cổng có ba mục tôi tự
nghĩ ra là một cổng đo ý kiến của tôi, không đo điều kiện dự án đã chốt.

Cổng dưới đây chạy phần định nghĩa được và **thoát mã 3** ở phần chưa có định
nghĩa. Nó sẽ **không bao giờ báo ĐẠT** cho tới khi ĐC-1/3/4 được viết ra.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import importlib.util
import json
import pathlib
import sys

GOC = pathlib.Path(__file__).resolve().parent.parent
BAM = "sha256[:12] của nội dung tệp (bytes), hoặc của json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True) sau khi bỏ 'bam_nhan' và 'thuat_toan_bam'"


def _bam_tep(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:12]


def _bam_nhan(d: dict) -> str:
    t = {k: v for k, v in d.items() if k not in ("bam_nhan", "thuat_toan_bam")}
    return hashlib.sha256(
        json.dumps(t, ensure_ascii=False, indent=1, sort_keys=True).encode()
    ).hexdigest()[:12]


def _nap_luat(p: pathlib.Path):
    spec = importlib.util.spec_from_file_location("luat", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _nhanh(ly_do: str) -> str:
    l = ly_do.lower()
    if "chữ số" in l:
        return "CHỮ SỐ"
    if "dài" in l:
        return "ĐỘ DÀI"
    if "ngoài tập" in l:
        return "TOKEN NGOÀI TẬP"
    if "xã giao" in l:
        return "mọi token xã giao"
    return f"khác({ly_do[:24]})"


def cham(ten, cau_nhan, phan_luong) -> tuple[bool, str]:
    """Trả (đạt, báo cáo). `cau_nhan` = list[(câu, nhãn kỳ vọng)]."""
    dem = collections.Counter()
    sai = []
    for cau, mong in cau_nhan:
        duong, ly_do = phan_luong(cau)
        dem[_nhanh(ly_do)] += 1
        if duong != mong:
            sai.append((cau, mong, duong, ly_do))
    n = len(cau_nhan)
    d = n - len(sai)
    ra = [f"\n  {ten}: {d}/{n}"]
    ra.append("    phân bố lý do: " + " · ".join(f"{k}={v}" for k, v in dem.most_common()))
    chua_chay = [k for k in ("CHỮ SỐ", "ĐỘ DÀI", "TOKEN NGOÀI TẬP") if dem[k] == 0]
    if chua_chay:
        ra.append(f"    ⚠️  nhánh CHƯA KHAI HOẢ lần nào: {chua_chay} — chưa được kiểm (Luật E)")
    for cau, mong, thuc, ly in sai[:8]:
        ra.append(f"    ✗ {cau!r}  mong {mong} · được {thuc} · vì {ly}")
    return not sai, "\n".join(ra)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--luat", required=True, help="đường dẫn quy_tac_phan_luong.py")
    ap.add_argument("--bo-qua-bam", action="store_true",
                    help="CHỈ để dò lỗi. Cổng thật KHÔNG được dùng cờ này.")
    a = ap.parse_args()

    p_luat = pathlib.Path(a.luat)
    if not p_luat.exists():
        print(f"🔴 không thấy luật: {p_luat}")
        return 2
    print(f"  LUẬT   {p_luat.name} · {p_luat.stat().st_size} byte")
    print(f"         sha256[:12] = {_bam_tep(p_luat)}   md5[:12] = "
          f"{hashlib.md5(p_luat.read_bytes()).hexdigest()[:12]}")
    print(f"  cách băm: {BAM}")
    luat = _nap_luat(p_luat)

    bo = []
    # bộ ca DƯƠNG + ÂM-NGẮN: nhãn nằm trong file JSON đã băm
    for f, ky in (("eval/bo_ca_luot_don.json", "dương 20 ca"),
                  ("eval/bo_ca_am_ngan_khong_so.json", "âm-ngắn 14 ca")):
        p = GOC / f
        if not p.exists():
            print(f"🔴 thiếu bộ ca: {f}")
            return 2
        d = json.loads(p.read_text(encoding="utf-8"))
        thuc, ghi = _bam_nhan(d), d.get("bam_nhan")
        if thuc != ghi and not a.bo_qua_bam:
            print(f"🔴 BỘ CA ĐÃ TRÔI: {f}\n   băm ghi {ghi} ≠ tính lại {thuc}\n"
                  "   TỪ CHỐI CHẤM — số chấm trên bộ ca trôi là số về một vật không còn tồn tại.")
            return 2
        bo.append((f"{ky} [{ghi}]", [(c["cau"], c["ky_vong"]) for c in d["ca"]]))

    # bộ ca ÂM gốc: nhãn ngầm — MỌI câu đều phải đi day_du
    p = GOC / "eval" / "golden_set.jsonl"
    if p.exists():
        cau = []
        for l in p.read_text(encoding="utf-8").splitlines():
            if not l.strip():
                continue
            x = json.loads(l)
            u = x.get("utterances") or ([x["utterance"]] if "utterance" in x else [])
            cau += [(c, "day_du") for c in u if isinstance(c, str) and c.strip()]
        bo.append((f"âm gốc {len(cau)} CÂU [{_bam_tep(p)}]", cau))
        print(f"\n  ⚠️  ĐƠN VỊ ĐẾM: golden_set.jsonl có 120 CA nhưng {len(cau)} CÂU. "
              "Cổng chấm theo CÂU.")

    tat_ca_dat = True
    for ten, cn in bo:
        dat, bc = cham(ten, cn, luat.phan_luong)
        print(bc)
        tat_ca_dat &= dat

    print("\n  ── ĐC-1..5 ─────────────────────────────────────────")
    print("  ĐC-2  phân loại theo TỪNG LƯỢT  → cần dấu `duong` từng lượt, CHƯA CÓ")
    print("  ĐC-5  mọi câu bộ âm đi day_du   → đã chấm ở trên")
    print("  🔴 ĐC-1 · ĐC-3 · ĐC-4 — KHÔNG TÌM THẤY ĐỊNH NGHĨA trong docs/")
    print("     Tôi KHÔNG đoán. Một cổng có ba mục tự nghĩ ra là cổng đo ý kiến")
    print("     của người viết cổng, không đo điều kiện dự án đã chốt.")
    print("\n  ⟹ CỔNG CHƯA ĐẠT — thiếu định nghĩa ĐC-1/3/4. Mã thoát 3.")
    return 3 if tat_ca_dat else 1


if __name__ == "__main__":
    sys.exit(main())
