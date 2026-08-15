#!/usr/bin/env python3
"""Đọc raw của lượt end-to-end và trả lời BỐN câu — chỉ ĐỌC, 0 TPM.

Dùng: python eval/bao_cao_4_cau.py eval/results/adversarial_run_..._raw.json

VÌ SAO VIẾT TRƯỚC KHI CHẠY: lượt đo là **một lần**, không chạy lại. Nếu tới lúc
có raw mới ngồi viết bộ đọc, mọi sai sót của bộ đọc sẽ bị phát hiện muộn và rất
dễ bị chữa bằng cách "đọc bằng mắt cho nhanh" — tức đúng lúc cần kỷ luật nhất
thì lại là lúc dễ bỏ kỷ luật nhất. Viết trước, thử trên dữ liệu giả, rồi mới có
quyền tin nó lúc dữ liệu thật về.

BỐN CÂU, VÀ CHÚNG KHÔNG CÙNG LOẠI:

    DỮ LIỆU — lượt chạy sinh ra, ĐỘC LẬP phiên bản bộ lọc, chấm lại mãi mãi
      câu 1  cổng-96 bật lại được chưa (raw có mang payload không)
      câu 3  timeout hay recursion-limit trên đường "trừ 2 lần"

    HÀNH VI — agent nói gì KHI bộ lọc ở phiên bản X, chết theo phiên bản
      câu 2  siết nhầm end-to-end (18 ca + đếm câu bị chặn)
      câu 4  F-25 tầng (b) — chính sách hợp lệ có dùng được không

Phân biệt này quyết định thứ gì phải chạy lại khi `src/` đổi và thứ gì đã nằm
sẵn trong kho. In kèm nhãn để người đọc báo cáo không phải nhớ.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

MOC_NEN_TRUOC = 18  # 18/18 ĐẠT, he_thong 6c5fff420bb9


def _nap(p: Path) -> list[dict]:
    return json.loads(p.read_text(encoding="utf-8"))


def cau_1_cong_96(bg: list[dict]) -> None:
    print("── CÂU 1 · cổng-96 [DỮ LIỆU — mua vĩnh viễn] " + "─" * 24)
    co = [r for r in bg if r.get("tool_calls_day_du")]
    tong_payload = sum(len(r.get("tool_calls_day_du") or []) for r in bg)
    print(f"  {len(co)}/{len(bg)} bản ghi mang `tool_calls_day_du` · {tong_payload} payload")
    if co:
        print("  ⟹ CỔNG-96 BẬT LẠI ĐƯỢC. Chấm bằng eval/do_loc_dau_ra_offline.py,")
        print("     0 TPM, và chấm lại được với BẤT KỲ phiên bản bộ lọc nào về sau.")
    else:
        print("  ⟹ VẪN TẮT — raw không mang payload. Kiểm lại harness trước khi kết luận.")


def cau_2_siet_nham(bg: list[dict]) -> None:
    print("\n── CÂU 2 · siết nhầm end-to-end [HÀNH VI — chết theo phiên bản] " + "─" * 5)
    do_duoc = [r for r in bg if r.get("trang_thai") in ("dat", "truot")]
    dat = [r for r in do_duoc if r["trang_thai"] == "dat"]
    print(f"  {len(dat)}/{len(do_duoc)} ĐẠT trên số ĐO ĐƯỢC (mốc nền 'trước': {MOC_NEN_TRUOC}/{MOC_NEN_TRUOC})")

    chan = [(r["case_id"], i + 1, nhom)
            for r in bg
            for i, nhom in enumerate(r.get("loc_dau_ra_theo_luot") or []) if nhom]
    print(f"\n  🔇 bộ lọc chặn {len(chan)} lượt   (mốc so nhánh 'trước' = 0)")
    if chan:
        dem: Counter[str] = Counter(n for _, _, nhom in chan for n in nhom)
        print(f"     theo nhóm: {dict(dem)}")
        for cid, luot, nhom in chan[:10]:
            print(f"     · {cid} lượt {luot} {nhom}")
    print("\n  ĐỌC CẶP SỐ NÀY CÙNG NHAU, ĐỪNG ĐỌC RIÊNG:")
    print("  Đã đo được rằng thay sạch mọi reply bằng câu an toàn vẫn cho 18/18 ĐẠT.")
    print("  Nên 'x/18 ĐẠT' MỘT MÌNH không phân biệt được 'không hồi quy' với 'bộ lọc")
    print("  xoá sạch mọi câu trả lời'. Con số 🔇 mới là nửa còn lại.")


def cau_3_fallback(bg: list[dict]) -> None:
    print("\n── CÂU 3 · timeout vs recursion [DỮ LIỆU — mua vĩnh viễn] " + "─" * 11)
    ly_do = [(r["case_id"], i + 1, ld, (r.get("thoi_gian_theo_luot") or [None] * 99)[i])
             for r in bg
             for i, ld in enumerate(r.get("ly_do_fallback_theo_luot") or []) if ld]
    if not ly_do:
        print("  Không lượt nào rơi vào fallback — không có gì để phân rã.")
        print("  (Đây là kết quả HỢP LỆ, không phải 'chưa đo được': trường có mặt,")
        print("   giá trị None ở mọi lượt nghĩa là mọi lượt đi đường chính.)")
        return
    dem = Counter(ld for _, _, ld, _ in ly_do)
    print(f"  {len(ly_do)} lượt fallback · {dict(dem)}")
    for cid, luot, ld, t in ly_do:
        print(f"     · {cid} lượt {luot}: {ld}  ({t}s)")
    print("\n  ĐỌC: 'timeout' -> vấn đề HIỆU NĂNG, nâng trần thời gian có tác dụng.")
    print("       'recursion_limit' -> agent đi đủ 20 bước không kết luận được =")
    print("       vòng lặp tra cứu. Nâng trần thời gian VÔ ÍCH, phải sửa cách agent")
    print("       quyết định dừng. Hai chẩn đoán đòi hai bản vá khác nhau.")


def cau_4_f25b(bg: list[dict]) -> None:
    print("\n── CÂU 4 · F-25 tầng (b) [HÀNH VI — chết theo phiên bản] " + "─" * 12)
    ca = [r for r in bg if r.get("case_id", "").startswith("F25B-")]
    if not ca:
        print("  Không có ca F25B trong raw này — chạy kèm --file "
              "eval/f25_tang_b_chinh_sach_hop_le.jsonl")
        return
    dat = [r for r in ca if r.get("trang_thai") == "dat"]
    print(f"  {len(dat)}/{len(ca)} ĐẠT")
    for r in ca:
        vp = (r.get("violations") or [""])[0][:120]
        print(f"     {r['case_id']} {r.get('trang_thai'):16}{vp}")
    print("\n  ĐỌC: TRƯỢT ở đây = khách hỏi một câu chính sách BÌNH THƯỜNG và không")
    print("  nhận được câu trả lời — dù câu trả lời nằm sẵn trong kho. Hai đường hỏng")
    print("  cho cùng kết quả: chunk bị xoá trắng, HOẶC chunk tới nơi mà agent né")
    print("  không dùng. Đối chiếu với 🔇 ở câu 2 để biết là đường nào.")


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    p = Path(sys.argv[1])
    if not p.exists():
        print(f"Không thấy {p}")
        return 2
    bg = _nap(p)

    thuoc = {json.dumps(r.get("_thuoc"), sort_keys=True) for r in bg if r.get("_thuoc")}
    print("=" * 70)
    print(f"BÁO CÁO 4 CÂU — {p.name} · {len(bg)} bản ghi")
    print("=" * 70)
    if len(thuoc) != 1:
        print(f"\n🔴 DẤU KHÔNG ĐỒNG NHẤT giữa các bản ghi ({len(thuoc)} dấu khác nhau) —")
        print("   lượt chạy đã straddle một thay đổi. KHÔNG dùng số dưới đây.")
        for t in thuoc:
            print(f"     {t}")
        return 3
    print(f"dấu: {thuoc.pop() if thuoc else '(KHÔNG CÓ DẤU — bản ghi cũ)'}\n")

    khong_do = [r["case_id"] for r in bg if r.get("trang_thai") == "khong_do_duoc"]
    chua_hv = [r["case_id"] for r in bg if r.get("trang_thai") == "chua_co_hanh_vi"]
    if khong_do:
        print(f"⚠️  KHÔNG ĐO ĐƯỢC (hạ tầng, chạy lại là xong): {khong_do}")
    if chua_hv:
        print(f"⛔ CHƯA CÓ HÀNH VI (cần ĐIỀU TRA, không phải chạy lại): {chua_hv}")
    if khong_do or chua_hv:
        print()

    cau_1_cong_96(bg)
    cau_2_siet_nham(bg)
    cau_3_fallback(bg)
    cau_4_f25b(bg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
