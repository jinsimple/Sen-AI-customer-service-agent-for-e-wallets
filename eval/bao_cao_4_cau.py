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

═══ BUG THẬT ĐÃ XẢY RA Ở ĐÂY, SỬA 15/08 SAU LƯỢT END-TO-END 25 CA

Bản đầu của `cau_2_siet_nham` lọc trên TOÀN BỘ `bg` (25 bản ghi) thay vì đúng
18 ca mốc nền — cho ra "21/24 ĐẠT", một con số trộn 2 ca F25B (câu 4, ngữ nghĩa
đạt/trượt khác hẳn) và 2 ca MT-A01/MT-F01 (chưa từng đo được ở nhánh "trước",
không so-cặp được dù giờ chúng ĐẠT) vào cùng một phân số. Số đúng là 17/17
(MT-E02 rơi vào `chua_co_hanh_vi`, không đo được). Giữ nguyên vụ này trong
docstring vì nó là ví dụ gốc cho lý do phải LỌC THEO ID TƯỜNG MINH, không lọc
theo tiền tố hay "mọi bản ghi có mặt trong file".
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

MOC_NEN_TRUOC = 18  # 18/18 ĐẠT, he_thong 6c5fff420bb9

# 18 case_id CHÍNH XÁC của mốc nền đã khoá — KHÔNG suy từ tiền tố "MT-". Mốc
# nền loại MT-A01 và MT-F01 (chưa từng đo được ở nhánh "trước", chốt vĩnh viễn
# ngoài so-cặp dù chúng có thể ĐẠT ở nhánh "sau" — một ca chỉ đo được MỘT
# nhánh thì không so-cặp được, thành công muộn không mua lại được chỗ đứng
# trong phép so). Liệt kê tường minh để không ai vô tình nới mẫu số bằng cách
# đổi bộ lọc theo tiền tố.
MOC_NEN_18_ID = {
    "MT-A02", "MT-A03", "MT-B01", "MT-B02", "MT-B03",
    "MT-C01", "MT-C02", "MT-C03", "MT-D01", "MT-D02", "MT-D03",
    "MT-E01", "MT-E02", "MT-Z01", "MT-Z02", "MT-Z03", "MT-Z04", "MT-F02",
}


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
        print("     (script đó tự lọc lượt KHÔNG mang payload ra khỏi mẫu số —")
        print("      không trộn bản ghi cũ chưa có tool_calls_day_du vào phép đo.)")
    else:
        print("  ⟹ VẪN TẮT — raw không mang payload. Kiểm lại harness trước khi kết luận.")


def cau_2_siet_nham(bg: list[dict]) -> None:
    print("\n── CÂU 2 · siết nhầm end-to-end [HÀNH VI — chết theo phiên bản] " + "─" * 5)

    # PHẠM VI ĐÚNG: chỉ 18 ca mốc nền, KHÔNG lẫn F25B (câu 4 khác) và KHÔNG lẫn
    # MT-A01/MT-F01 (xem docstring đầu file — bug thật đã xảy ra ở chỗ này).
    moc_nen = [r for r in bg if r.get("case_id") in MOC_NEN_18_ID]
    do_duoc = [r for r in moc_nen if r.get("trang_thai") in ("dat", "truot")]
    dat = [r for r in do_duoc if r["trang_thai"] == "dat"]
    thieu = [r["case_id"] for r in moc_nen if r.get("trang_thai") not in ("dat", "truot")]
    print(f"  {len(dat)}/{len(do_duoc)} ĐẠT trên ĐÚNG 18 ca mốc nền (mốc 'trước': "
          f"{MOC_NEN_TRUOC}/{MOC_NEN_TRUOC})"
          + (f" · thiếu: {thieu}" if thieu else ""))

    chan = [(r["case_id"], i + 1, nhom)
            for r in moc_nen
            for i, nhom in enumerate(r.get("loc_dau_ra_theo_luot") or []) if nhom]
    print(f"\n  🔇 bộ lọc chặn {len(chan)} lượt TRONG 18 ca mốc nền   (mốc so nhánh 'trước' = 0)")
    if chan:
        dem: Counter[str] = Counter(n for _, _, nhom in chan for n in nhom)
        print(f"     theo nhóm: {dict(dem)}")
        for cid, luot, nhom in chan[:10]:
            print(f"     · {cid} lượt {luot} {nhom}")
    print("\n  ĐỌC CẶP SỐ NÀY CÙNG NHAU, ĐỪNG ĐỌC RIÊNG:")
    print("  Đã đo được rằng thay sạch mọi reply bằng câu an toàn vẫn cho 18/18 ĐẠT.")
    print("  Nên 'x/18 ĐẠT' MỘT MÌNH không phân biệt được 'không hồi quy' với 'bộ lọc")
    print("  xoá sạch mọi câu trả lời'. Con số 🔇 mới là nửa còn lại.")

    # BONUS ngoài so-cặp — báo tách hẳn, không cộng vào tử/mẫu số ở trên.
    bonus = [r for r in bg if r.get("case_id") in ("MT-A01", "MT-F01")]
    if bonus:
        print("\n  · BONUS (ngoài so-cặp, chưa từng đo được ở nhánh 'trước'):")
        for r in bonus:
            print(f"      {r['case_id']}: {r.get('trang_thai')} · luot={r.get('so_luot_da_chay')}")


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

    # ĐỌC TRỰC TIẾP loc_dau_ra CỦA TỪNG CA F25B — không "đối chiếu với câu 2",
    # vì 🔇 ở câu 2 CHỈ tính trên 18 ca mốc nền, F25B không bao giờ có mặt ở
    # đó. Bản đầu của hàm này hứa suông "đối chiếu với câu 2" — sửa.
    print("\n  ĐỌC: TRƯỢT ở đây = khách hỏi một câu chính sách BÌNH THƯỜNG và không")
    print("  nhận được câu trả lời — dù câu trả lời nằm sẵn trong kho. Hai đường hỏng")
    print("  cho cùng kết quả nhưng khác nguồn gốc:")
    truot = [r for r in ca if r.get("trang_thai") == "truot"]
    for r in truot:
        nhom_ca = [n for nhom in (r.get("loc_dau_ra_theo_luot") or []) for n in nhom]
        if nhom_ca:
            print(f"     {r['case_id']}: bộ lọc đầu ra CHẶN {nhom_ca} — đường 'xoá sau'")
        else:
            print(f"     {r['case_id']}: bộ lọc đầu ra KHÔNG chặn gì (loc_dau_ra=[]) — "
                  "chunk không tới được reply qua đường khác (RAG/tier-1/tier-2 né), "
                  "KHÔNG phải do O1-O4. Đọc reply thật để biết agent nói gì thay vào đó:")
            print(f"         {r.get('all_agent_replies', [''])[0][:180]!r}")


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
