#!/usr/bin/env python3
"""Rà CƠ HỌC nhãn của một bộ ca — không đọc nội dung để hiểu.

    python eval/ra_nhan_co_hoc.py eval/golden_set_truy_hoi.jsonl
    python eval/ra_nhan_co_hoc.py eval/heldout_set.jsonl --ra bao_cao.md --chi-tom-tat

## Vì sao tồn tại

`eval/heldout_set.jsonl` **chỉ được bắn MỘT LẦN** cho con số công bố. Nhưng nhãn
của nó viết **trước** khi ta phát hiện sáu lớp lỗi thước trong tuần:

    bo_dau() không gộp khoảng trắng   → cụm dài vắt qua xuống dòng = TRƯỢT GIẢ
    từ khoá CHUNG                     → khớp chunk bên cạnh = PASS GIẢ
    chuỗi không sống qua trích PDF    → nhãn chết, trông như sản phẩm kém
    mẫu số đếm cả thứ đã cố ý vứt     → phủ 81% thay vì 87,4%
    doc_id là BĂM, không phải tên     → so hai không gian tên, xanh rỗng tuếch
    chuỗi lỏng (≥6 chunk chứa)        → đạt nhờ khớp nhầm

Nếu heldout dính cùng lớp lỗi, ta phát hiện **đúng lúc bắn phát duy nhất**, và
không có phát thứ hai.

## 🔴 Ràng buộc chống nhiễm bẩn — đọc trước khi chạy

Bộ heldout mất **tính độc lập** thì con số của nó vô giá trị, kể cả khi nhãn
đúng. Nên script này thiết kế để **người chạy đọc càng ít nội dung càng tốt**:

- `--chi-tom-tat` in **CHỈ số đếm**, chi tiết ghi ra file cho vai khác xử lý.
- Không in `query`, không in đáp án, không in ca ĐẠT — chỉ ca **hỏng**, và chỉ
  **chuỗi nhãn** của nó.
- Script **không sửa gì**. Nó không có đường ghi vào bộ ca.

**Được làm:** kiểm chuỗi nhãn có sống qua chuẩn hoá · có trong kho · có đặc
trưng · định dạng nhất quán.
**KHÔNG được làm:** sửa ca theo nội dung · chọn/loại ca · chỉnh thước theo
những gì thấy trong heldout.

Người rà **không nên** là người sẽ bắn phát heldout, nếu tránh được. Nếu không
tránh được thì `--chi-tom-tat` giữ mức tiếp xúc ở **số đếm**, và phần chi tiết
phải do vai khác đọc.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import unicodedata

GOC = pathlib.Path(__file__).resolve().parent.parent
BASE = "https://localhost"


def bo_dau(s: str) -> str:
    """Y HỆT `benchmark.bo_dau` — kể cả gộp khoảng trắng.

    Phải giống hệt, không phải "tương đương": rà bằng một chuẩn hoá KHÁC chuẩn
    hoá lúc chấm thì ta đang rà một bộ nhãn không phải bộ sẽ được dùng.
    """
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s.replace("đ", "d").replace("Đ", "D").lower())


def dac_trung(s: str) -> bool:
    """Luật chuỗi đặc trưng: có SỐ · hoặc VIẾT HOA · hoặc cụm ≥3 từ."""
    return bool(re.search(r"\d", s)) or s.isupper() or len(s.split()) >= 3


def lay_nhan(x: dict) -> list[str]:
    """Mọi trường có thể chứa chuỗi nhãn, không đoán tên trường."""
    ra = []
    for k in ("tu_khoa_dac_trung", "tu_khoa_dap_an", "expected", "expected_output_contains",
              "tu_khoa", "keywords"):
        v = x.get(k)
        if isinstance(v, str):
            ra.append(v)
        elif isinstance(v, list):
            ra += [t for t in v if isinstance(t, str)]
    return ra


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("bo_ca")
    ap.add_argument("--ra", default=None, help="ghi báo cáo CHI TIẾT ra file (cho vai khác đọc)")
    ap.add_argument("--chi-tom-tat", action="store_true",
                    help="chỉ in SỐ ĐẾM ra màn hình — giữ mức tiếp xúc nội dung ở tối thiểu")
    ap.add_argument("--khong-tra-kho", action="store_true", help="bỏ bước tra kho (offline)")
    a = ap.parse_args()

    p = pathlib.Path(a.bo_ca)
    ca = [json.loads(dg) for dg in p.read_text(encoding="utf-8").splitlines() if dg.strip()]

    kho = ""
    if not a.khong_tra_kho:
        try:
            import httpx

            c = httpx.Client(verify=False, timeout=60)
            c.post(f"{BASE}/api/session", json={"phone": "0353000201", "password": "Demo@123"})
            # Gom kho bằng CHÍNH nhãn — không gửi query của bộ ca đi đâu cả.
            gom = set()
            for x in ca:
                for s in lay_nhan(x)[:1]:
                    r = c.post(f"{BASE}/api/policy-search", json={"query": s, "top_k": 8})
                    if r.status_code == 200:
                        gom.update(y.get("text", "") for y in (r.json().get("results") or []))
            c.close()
            kho = bo_dau(" ||| ".join(gom))
        except Exception as e:  # noqa: BLE001
            print(f"  ⚠️  không tra được kho ({type(e).__name__}) — bỏ qua cửa 'có trong kho'")

    dem = {"tong": len(ca), "am_ban_bo_qua": 0, "khong_co_nhan": 0, "khong_dac_trung": 0,
           "vo_khi_chuan_hoa": 0, "nghi_khong_trong_kho": 0, "ok": 0}
    chi_tiet = []
    for x in ca:
        cid = x.get("id") or x.get("case_id") or "?"
        # Ca ÂM BẢN đúng ra KHÔNG có nhãn — kỳ vọng là "không có trong kho".
        # Đếm nó thành lỗi là dương tính giả, và trên một bộ chỉ-bắn-một-lần thì
        # nhiễu còn tệ hơn im lặng: người đọc báo cáo sẽ đi sửa thứ không hỏng.
        if str(x.get("ky_vong", "")).startswith("khong_co"):
            dem["am_ban_bo_qua"] += 1
            continue
        nhan = lay_nhan(x)
        if not nhan:
            dem["khong_co_nhan"] += 1
            chi_tiet.append((cid, "KHÔNG CÓ TRƯỜNG NHÃN NÀO", ""))
            continue
        loi = []
        if not any(dac_trung(s) for s in nhan):
            dem["khong_dac_trung"] += 1
            loi.append("không chuỗi nào ĐẶC TRƯNG (thiếu số/viết-hoa/cụm≥3 từ)")
        # "vỡ khi chuẩn hoá": chuỗi chứa khoảng trắng thừa hoặc xuống dòng ⟹ sau
        # khi gộp nó KHÁC chính nó, tức nhãn viết ra đã không khớp được với text
        # đã chuẩn hoá. Đây đúng lớp lỗi `bo_dau` không gộp \s+.
        if any(bo_dau(s) != bo_dau(re.sub(r"\s+", " ", s.strip())) for s in nhan):
            dem["vo_khi_chuan_hoa"] += 1
            loi.append("chuỗi đổi hình sau chuẩn hoá")
        # ⚠️ PHÉP DÒ YẾU, cố ý gọi là "NGHI" chứ không phải "lỗi": tra bằng chính
        # chuỗi nhãn thì truy vấn ngắn embed kém, và chuỗi CÓ THẬT trong kho vẫn
        # không ra (đã trả giá: `PCI DSS` — 15 ca bị tôi nghi oan, kiểm lại
        # 15/15 đều có thật). "Không tìm thấy bằng cách A" != "không tồn tại".
        if kho and not any(bo_dau(s) in kho for s in nhan):
            dem["nghi_khong_trong_kho"] += 1
            loi.append("NGHI không có trong kho — phép dò YẾU, phải kiểm lại bằng "
                       "đường độc lập trước khi sửa nhãn")
        if loi:
            chi_tiet.append((cid, " · ".join(loi), " | ".join(repr(s) for s in nhan)))
        else:
            dem["ok"] += 1

    print(f"\n  RÀ CƠ HỌC — {p.name}")
    print(f"  {'-' * 56}")
    for k, v in dem.items():
        print(f"  {k:<24} {v:>4}")
    hong = dem["tong"] - dem["ok"] - dem["am_ban_bo_qua"]
    print(f"\n  ⟹ {hong}/{dem['tong']} ca có ít nhất một lỗi cơ học")

    if a.ra:
        r = pathlib.Path(a.ra)
        r.write_text(
            f"# Rà cơ học nhãn — {p.name}\n\n"
            f"> Sinh bởi `eval/ra_nhan_co_hoc.py`. **Chỉ lỗi CƠ HỌC**, không đọc nội dung.\n"
            f"> Người rà không sửa: báo dạng [ca → lỗi → cách sửa] để vai khác quyết.\n\n"
            + "\n".join(f"- `{c}` — {dg}\n  - nhãn: {n}" for c, dg, n in chi_tiet) + "\n",
            encoding="utf-8")
        print(f"  → chi tiết ghi ra {r} ({len(chi_tiet)} ca) — KHÔNG in ra đây")
    elif not a.chi_tom_tat:
        for c, dg, n in chi_tiet:
            print(f"    {c:<12} {dg}\n                 {n[:100]}")
    else:
        print("  (chi tiết KHÔNG in — dùng --ra để ghi ra file cho vai khác đọc)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
