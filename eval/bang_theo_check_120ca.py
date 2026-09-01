"""Bảng TỪNG PHÉP KIỂM cho lượt golden(120) thật — sau khi PO cấp khoá OpenAI
31/08 và xác nhận bộ mô phỏng thêm lượt hoạt động lại bình thường (5/5 ca thử
lại: Pass, extra_turns 1-2, create_ticket có đủ). Không còn cần lọc nhóm
①②③ như `eval/phan_loai_truot_adr051.py` (dựng cho tình huống mô phỏng hỏng
31/08, đã NIÊM — xem docstring file đó) — mọi `checks` trong file kết quả giờ
đáng tin trên TOÀN BỘ ca, gộp thẳng theo tên phép kiểm.

🔴 SỬA 01/09 (câu cũ đọc ngược nghĩa — xem feedback_dieu_kien_nam_trong_cau):
bản CŨ LOẠI TRỪ 2 phép kiểm `khong_tao_ticket_hop_le` và `de_nghi_truoc_khi_tao_ticket`
khỏi bảng (gắn nhãn "KHÔNG ĐO ĐƯỢC", lý do: bộ mô phỏng thêm lượt hỏng 31/08).
Bản NÀY GIỮ CẢ HAI, không loại trừ nữa — lý do loại trừ cũ không còn áp dụng.
Cả hai vẫn cần đọc cẩn thận (xem nhãn cảnh báo ngay cạnh số trong bảng in ra):
tên `khong_tao_ticket_hop_le` NÓI NGƯỢC — True nghĩa là "KHÔNG tạo hồ sơ mới
ĐÚNG", không phải "tạo hồ sơ hợp lệ"; `de_nghi_truoc_khi_tao_ticket` chỉ đo
gián tiếp trên rất ít mẫu (n thường ~4), tỉ lệ cao trên mẫu nhỏ không nói
được nhiều.

Chạy:
    python eval/bang_theo_check_120ca.py --ket-qua <golden_ket_qua_tung_ca.jsonl> [--ra <file .jsonl>]
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

_MAU_LOI_HA_TANG = re.compile(r"LỖI CHẠY CASE", re.IGNORECASE)


def _co_loi_ha_tang(record: dict) -> bool:
    """True nếu ca này là LỖI HẠ TẦNG (container/hạn mức chết giữa chừng),
    không phải sản phẩm sai — nhận diện qua chuỗi "LỖI CHẠY CASE" trong
    `violations`, KHÔNG dùng severity=="Blocker" (một ca Blocker THẬT do sản
    phẩm sai vẫn phải giữ lại, không được lọc nhầm theo severity)."""
    for v in record.get("violations", []):
        if _MAU_LOI_HA_TANG.search(str(v)):
            return True
    return False


_MAU_CITE_TXN = re.compile(r"^cite_TXN")


def _gom_ten_check(ten: str) -> str:
    """Bó mọi `cite_TXN<mã cụ thể>` (tên khác nhau mỗi ca) vào MỘT hàng
    chung — nếu không, bảng sẽ có một hàng riêng cho MỖI mã giao dịch."""
    if _MAU_CITE_TXN.match(ten):
        return "cite_TXN... (trích dẫn mã GD — Ràng buộc cứng #3)"
    return ten


def gom_theo_check(records: list[dict]) -> dict[str, list[int]]:
    """Trả {tên_bó: [đạt, tổng]} — gộp TOÀN BỘ file theo tên phép kiểm."""
    bang: dict[str, list[int]] = {}
    for d in records:
        for item in d.get("checks", []):
            if not isinstance(item, list) or len(item) != 2:
                continue
            ten, gia_tri = item
            bo = _gom_ten_check(str(ten))
            if bo not in bang:
                bang[bo] = [0, 0]
            bang[bo][1] += 1
            if gia_tri is True:
                bang[bo][0] += 1
    return bang


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ket-qua", required=True, type=Path)
    ap.add_argument("--ra", type=Path, default=None)
    args = ap.parse_args()

    tat_ca = []
    with open(args.ket_qua, encoding="utf-8") as f:
        for dong in f:
            dong = dong.strip()
            if dong:
                tat_ca.append(json.loads(dong))

    loi_ha_tang = [d for d in tat_ca if _co_loi_ha_tang(d)]
    records = [d for d in tat_ca if not _co_loi_ha_tang(d)]

    print(f"Tổng file: {len(tat_ca)} ca — LỖI HẠ TẦNG (loại khỏi tính toán): {len(loi_ha_tang)} — CÒN LẠI: {len(records)}")
    if loi_ha_tang:
        print(f"  case_id lỗi hạ tầng: {[d['case_id'] for d in loi_ha_tang]}")
    if not records:
        print("🔴 KHÔNG còn ca nào sau khi lọc lỗi hạ tầng — dừng, không có gì để tính.")
        return 1

    # KHỐI LƯỢNG: đo có-xảy-ra (dùng lượt thêm hay không) — KHÔNG nói gì về
    # đúng/sai. Tách riêng khỏi CHẤT LƯỢNG bên dưới theo quyết định PO 01/09
    # (ca Klarna, điều ②) — đêm 31/08 cổng CTC1 từng đẩy "có tra cứu" 22/29 →
    # 29/29 trong khi "trả lời đúng" 3 → 6 nằm trong nhiễu; hai loại số lẫn
    # trong một bảng suýt bị đọc thành cùng một bằng chứng.
    print("KHỐI LƯỢNG (n = " + str(len(records)) + " ca):")
    print("  🔴 Chỉ số khối lượng KHÔNG được dùng làm bằng chứng cải thiện.")
    dem_extra_turns: dict[int, int] = {}
    for d in records:
        et = d.get("extra_turns_used")
        dem_extra_turns[et] = dem_extra_turns.get(et, 0) + 1
    print(f"  Phân bố extra_turns_used: {dict(sorted(dem_extra_turns.items(), key=lambda x: (x[0] is None, x[0])))}")
    if dem_extra_turns.get(0, 0) == len(records) and len(records) > 3:
        print(
            "  🔴 CẢNH BÁO: TOÀN BỘ ca có extra_turns_used=0 — đúng dấu hiệu mô phỏng "
            "thêm lượt lại chết (xem eval/phan_loai_truot_adr051.py, tình huống 31/08). "
            "DỪNG, kiểm lại khoá OpenAI/hạ tầng trước khi tin bảng dưới đây."
        )

    # Nhãn cảnh báo gắn NGAY CẠNH số — đọc rời số khỏi cảnh báo là y hệt cái
    # bẫy "câu điều kiện rụng khỏi câu" đã gặp nhiều lần (xem docstring đầu file).
    _CANH_BAO_CANH_TEN = {
        "khong_tao_ticket_hop_le": "🔴 TÊN NGƯỢC — True = KHÔNG tạo hồ sơ là ĐÚNG, không phải \"tạo hợp lệ\"",
        "de_nghi_truoc_khi_tao_ticket": "🔴 n RẤT NHỎ (~4) — tỉ lệ cao trên mẫu này gần như không nói gì",
    }
    print(f"\nCHẤT LƯỢNG (n = {len(records)} ca):")
    bang_check = gom_theo_check(records)
    for ten, (dat, tong_ck) in bang_check.items():
        canh_bao = _CANH_BAO_CANH_TEN.get(ten, "")
        dong = f"  {ten:55s} {dat}/{tong_ck}"
        print(f"{dong}  {canh_bao}" if canh_bao else dong)

    dem_severity: dict[str, int] = {}
    for d in records:
        sv = d.get("severity", "?")
        dem_severity[sv] = dem_severity.get(sv, 0) + 1
    print(f"\nTheo severity (thành phần bộ đề — input, không phải kết quả đo): {dict(dem_severity)}")

    if args.ra:
        args.ra.parent.mkdir(parents=True, exist_ok=True)
        with open(args.ra, "w", encoding="utf-8") as f:
            json.dump(
                {"tong": len(records), "theo_check": bang_check, "theo_severity": dem_severity},
                f,
                ensure_ascii=False,
                indent=1,
            )
        print(f"\nGhi chi tiết: {args.ra}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
