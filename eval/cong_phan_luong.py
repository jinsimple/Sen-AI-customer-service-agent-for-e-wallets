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
    dg = ly_do.lower()
    if "chữ số" in l:
        return "CHỮ SỐ"
    if "dài" in l:
        return "ĐỘ DÀI"
    if "ngoài tập" in l:
        return "TOKEN NGOÀI TẬP"
    if "xã giao" in l:
        return "mọi token xã giao"
    return f"khác({ly_do[:24]})"


def _nhanh_luat_CO(nguon: str) -> set[str]:
    """Nhánh nào luật THỰC SỰ có — đọc từ nguồn, không từ danh sách tôi nhớ.

    🔴 Bản đầu dùng một danh sách CỨNG ba nhánh, nên sau khi `DAI_TOI_DA` bị
    XOÁ nó vẫn cảnh báo *"ĐỘ DÀI chưa khai hoả"* ở cả ba bộ ca. Cảnh báo về một
    nhánh KHÔNG CÒN TỒN TẠI là nhiễu — và nhiễu dạy người đọc bỏ qua cảnh báo,
    tức nó phá đúng thứ Luật E dựng ra.
    """
    co = set()
    if "CO_CHU_SO" in nguon:
        co.add("CHỮ SỐ")
    if "DAI_TOI_DA" in nguon:
        co.add("ĐỘ DÀI")
    if "XA_GIAO" in nguon:
        co.add("TOKEN NGOÀI TẬP")
    return co


def cham(ten, cau_nhan, phan_luong, nhanh_co=None) -> tuple[bool, str]:
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
    chua_chay = sorted(k for k in (nhanh_co or set()) if dem[k] == 0)
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
        for dg in p.read_text(encoding="utf-8").splitlines():
            if not l.strip():
                continue
            x = json.loads(l)
            u = x.get("utterances") or ([x["utterance"]] if "utterance" in x else [])
            cau += [(c, "day_du") for c in u if isinstance(c, str) and c.strip()]
        bo.append((f"âm gốc {len(cau)} CÂU [{_bam_tep(p)}]", cau))
        print(f"\n  ⚠️  ĐƠN VỊ ĐẾM: golden_set.jsonl có 120 CA nhưng {len(cau)} CÂU. "
              "Cổng chấm theo CÂU.")

    nhanh_co = _nhanh_luat_CO(p_luat.read_text(encoding="utf-8"))
    print(f"  nhánh luật CÓ: {sorted(nhanh_co)}")
    tat_ca_dat = True
    for ten, cn in bo:
        dat, bc = cham(ten, cn, luat.phan_luong, nhanh_co)
        print(bc)
        tat_ca_dat &= dat

    print("\n  ── ĐC-1..5 ── nguồn: docs/giao-viec/2026-08-17-dinh-nghia-cong-DC-phan-luong.md")
    print(f"     sha256[:12] = {_bam_tep(GOC / 'docs/giao-viec/2026-08-17-dinh-nghia-cong-DC-phan-luong.md')}")
    dc = {}

    # ĐC-1 — xã giao thuần PHẢI đi nhẹ. Vế "kêu thật lúc bất thường".
    # 🔴 DÂN SỐ: ĐC-1 nói "câu xã giao THUẦN (kiểu 'alo')" — KHÔNG phải mọi ca
    # nhãn `nhe`. Bản đầu của tôi lấy cả 10 ca nhãn nhe (gồm 'cho mình hỏi cái
    # này với') rồi báo 5/10 — đo sai DÂN SỐ, đúng lớp lỗi golden_set-không-có-
    # lượt-đơn. Dân số đúng là nhóm ① chào hỏi, phân nhóm tôi đặt TỪ ĐẶC TẢ
    # trước khi thấy luật.
    _d = json.loads((GOC / "eval/bo_ca_luot_don.json").read_text(encoding="utf-8"))
    xa_giao = [c["cau"] for c in _d["ca"] if c["nhom"].startswith("①")]
    sai1 = [c for c in xa_giao if luat.phan_luong(c)[0] != "nhe"]
    dc["ĐC-1"] = (not sai1, f"{len(xa_giao)-len(sai1)}/{len(xa_giao)} câu xã giao đi nhẹ"
                  + (f" · TRƯỢT: {sai1[:3]}" if sai1 else ""))

    # ĐC-3 — ném lỗi / đầu vào bất thường ⟹ ĐẦY ĐỦ, KHÔNG được nổ ra ngoài.
    # fail-open VỀ PHÍA ĐẮT TIỀN: lỗi của lớp tiết kiệm không bao giờ thành lỗi của khách.
    quai = [("", "chuỗi rỗng"), ("   ", "toàn khoảng trắng"), ("\n\t", "toàn ký tự trắng"),
            ("\x00\x01", "byte điều khiển"), ("😀🔥", "chỉ emoji"),
            ("a" * 5000, "5000 ký tự"), ("﷽" * 50, "ký tự hợp âm"),
            (None, "None"), (12345, "số nguyên"), ([], "list rỗng")]
    hong3 = []
    for v, ten in quai:
        try:
            d, _ = luat.phan_luong(v)
            if d != "day_du":
                hong3.append(f"{ten} → {d} (phải day_du)")
        except Exception as e:
            hong3.append(f"{ten} → NÉM {type(e).__name__} (phải nuốt và trả day_du)")
    dc["ĐC-3"] = (not hong3, f"{len(quai)-len(hong3)}/{len(quai)} đầu vào bất thường → day_du"
                  + ("\n         🔴 " + "\n         🔴 ".join(hong3) if hong3 else ""))

    # ĐC-4 — câu lạ / không phân định được ⟹ ĐẦY ĐỦ.
    la = ["asdkjhasd", "xin chào ạaaaa bqzxk", "test test 123 abc xyz",
          "ủa gì vậy trời", "hmm thế à ừ nhỉ sao lại thế được nhỉ"]
    sai4 = [c for c in la if luat.phan_luong(c)[0] != "day_du"]
    dc["ĐC-4"] = (not sai4, f"{len(la)-len(sai4)}/{len(la)} câu lạ → day_du"
                  + (f" · LỌT: {sai4}" if sai4 else ""))

    # 🔴 DÂN SỐ: ĐC-5 nói "mọi câu của BỘ ÂM" — bản đầu tôi dùng `tat_ca_dat`
    # gộp CẢ bộ dương, nên 5 ca dương trượt (đúng theo thiết kế, chúng lệch phía
    # an toàn) kéo ĐC-5 xuống đỏ. Đo sai dân số lần thứ HAI trong cùng một hàm.
    dat_am = all(luat.phan_luong(c)[0] == "day_du"
                 for ten, cn in bo if "âm" in ten for c, _ in cn)
    n_am = sum(len(cn) for ten, cn in bo if "âm" in ten)
    dc["ĐC-5"] = (dat_am, f"mọi câu của {n_am} CÂU bộ ÂM đi day_du (KHÔNG gồm bộ dương)")

    for k in ("ĐC-1", "ĐC-3", "ĐC-4", "ĐC-5"):
        ok, mo = dc[k]
        print(f"  {'✅' if ok else '🔴'} {k}  {mo}")

    # RÀNG BUỘC ĐỌC ①: ĐC-1 và ĐC-5 chỉ có nghĩa khi ĐỨNG CÙNG NHAU
    if dc["ĐC-1"][0] != dc["ĐC-5"][0]:
        print("  ⚠️  ĐC-1 và ĐC-5 KHÔNG cùng trạng thái — mỗi cái một mình bị một")
        print("      router suy biến qua mặt (không-làm-gì ↔ cho-tất-qua).")

    print("\n  ── CHƯA CHẠY ĐƯỢC (cần hệ thống, không phải luật thuần) ──")
    print("  ĐC-2  phân loại theo TỪNG LƯỢT — luật này KHÔNG có trạng thái nên ở")
    print("        tầng luật nó đạt HIỂN NHIÊN. Phép thử THẬT phải qua hệ thống,")
    print("        nơi có thể có cache/phiên. Đạt ở đây KHÔNG có nghĩa gì.")
    print("  Δ     đường nhẹ: không LLM · không trả lời nghiệp vụ · không bản ghi")
    print("        → tests/test_bat_bien_dinh_tuyen_duong_nhe.py, chờ dấu `duong`")

    het = all(v[0] for v in dc.values())
    if not het:
        print("\n  ⟹ 🔴 CỔNG ĐỎ.")
        return 1
    print("\n  ⟹ ✅ phần LUẬT THUẦN đạt. CHƯA ĐẠT TOÀN PHẦN: ĐC-2 và Δ cần hệ thống.")
    return 3


if __name__ == "__main__":
    sys.exit(main())
