"""🔴 NIÊM 31/08 22:xx — DỰNG CHO TÌNH HUỐNG BỘ MÔ PHỎNG HỎNG 31/08, KHÔNG CÒN
ÁP DỤNG SAU KHI CÓ KHOÁ OPENAI. Nguyên nhân thật hoá ra là THIẾU 1 BIẾN MÔI
TRƯỜNG (khoá OpenAI), không phải hồi quy code/dữ liệu golden_set — PO cấp
khoá, chạy lại 5 ca trượt đêm qua trên CÙNG ảnh: 5/5 Pass, extra_turns 1-2
(không còn 0), create_ticket có ở cả 5 ca. Bộ mô phỏng thêm lượt hoạt động
bình thường trở lại — 3 nhóm ①②③ ở đây không còn cần thiết cho lượt đo tiếp
theo. Giữ nguyên file này (không xoá, không sửa đè — Luật P, CLAUDE.md §7b),
dùng lại nếu tình huống dụng cụ đo hỏng lặp lại lần khác; lượt 120 ca thật
sắp chạy dùng `eval/bang_theo_check_120ca.py` (không cần lọc nhóm nữa).

═══ NỘI DUNG GỐC (31/08, lúc bộ mô phỏng còn hỏng) ═══

Tách `golden_ket_qua_tung_ca.jsonl` thành 3 NHÓM theo `reply` THẬT (đọc văn
bản, không suy đoán qua tín hiệu gián tiếp), rồi tính bảng TỪNG PHÉP KIỂM CHỈ
trên nhóm ① — vì bộ mô phỏng thêm lượt (khách gật/gọi lại) đã CHẾT (hồi quy hạ
tầng đo 14-25/08, không phải lỗi sản phẩm), mọi ca bị cắt giữa chừng đều
"trượt" các check cần lượt sau dù agent làm đúng.

    ①  hội thoại TRỌN VẸN         mọi phép kiểm ĐO ĐƯỢC, tính bình thường
    ②  cắt vì agent hỏi XÁC NHẬN  ADR-051 thì 1 (tóm tắt + hỏi khách gật) —
                                  KHÔNG ĐO ĐƯỢC (lỗi DỤNG CỤ ĐO)
    ③  cắt vì agent hỏi LÀM RÕ    thiếu dữ kiện (mã GD/SĐT/số tiền...) —
                                  KHÔNG ĐO ĐƯỢC (lỗi DỤNG CỤ ĐO)

🔴 NHÓM ③ KHÔNG PHẢI LỖI. Agent nói "chưa tìm thấy, cho thêm thông tin" là
hành vi ĐÚNG theo Ràng buộc cứng #3 (cấm bịa số liệu — thiếu dữ kiện thì phải
hỏi, không được đoán). Xếp nhóm này thành "trượt" là báo cáo sai theo hướng
XẤU ĐI, không phải gian lận nâng điểm — nhưng vẫn là báo cáo sai, phải sửa.

LỊCH SỬ (giữ lại, không xoá — xem lý do ở CLAUDE.md §7b "Luật P"):
    30/08  bản đầu: phân loại theo CA (Y/Z/Z+Y/?), dựa 4 điều kiện gián tiếp
           (tên check + tool_calls + regex câu hỏi + extra_turns_used).
    31/08  PO tự đọc `reply` của CASE-010/064/011 — hoá ra KHÔNG khớp dấu
           hiệu Z (không hỏi xác nhận, mà hỏi mã giao dịch — hình dạng khác
           hẳn). Bộ 4-điều-kiện đúng đắn từ chối gán Z (xếp "?"), nhưng đó
           lộ ra vấn đề LỚN HƠN: bộ mô phỏng chết ảnh hưởng CẢ câu hỏi làm
           rõ, không chỉ câu hỏi xác nhận ADR-051 — ước 14/15 ca bị cắt.
           ⟹ Đổi hẳn từ "phân loại ca trượt" sang "tách nhóm đo-được", tính
           bảng riêng cho từng nhóm thay vì cố nhét một ca vào Y/Z.

NGUỒN
-----
- ADR-051 (`docs/DECISIONS.md`): `create_ticket` hai thì — thì 1
  (`xac_nhan=false`) KHÔNG tạo gì, trả tóm tắt + hỏi khách xác nhận; thì 2
  tạo thật sau khi khách gật. Bộ mô phỏng phải tự gật + gọi lại mới đo được
  thì 2 — phần này đã chết.
- Ràng buộc cứng #3 (CLAUDE.md): cấm bịa số liệu — không đủ dữ kiện phải nói
  rõ "không tra được"/hỏi thêm, đúng hành vi nhóm ③.

QUY TẮC TÁCH NHÓM — đọc `reply` thật, thứ tự ưu tiên ② trước ③:
    ②  regex `_MAU_XAC_NHAN` khớp — cụm "có đồng ý"/"đồng ý"/"bạn có"/
       "xác nhận" trong ~60 ký tự trước "tạo (hồ sơ|vé|ticket)" v.v.
       Tự kiểm bằng 8/15 ca thật (CASE-001/002/019/028/037/046/055/091).
    ③  KHÔNG khớp ② NHƯNG có "?" hoặc "được không:" trong ~350 ký tự cuối —
       bắt được cả biến thể câu hỏi kết bằng dấu ":" rồi liệt kê gạch đầu
       dòng thay vì dấu "?" (CASE-011 thật — câu hỏi không có "?" nào cả).
       Tự kiểm bằng 6/15 ca thật (CASE-010/011/064/082/100/109).
    ①  còn lại — 1/15 ca thật (CASE-073, đã tạo ticket xong trong 1 lượt).

Giới hạn CHƯA khắc phục hết, nói thẳng: đây là heuristic đọc văn bản, không
phải máy hiểu ngôn ngữ. Một câu hỏi làm rõ phrasing khác hẳn 6 ca đã thấy
(không "?", không "được không:") vẫn có thể lọt vào nhóm ① sai — khi golden
đủ 120 ca, RÀ LẠI danh sách ① xem có ca nào đáng ngờ (vd severity != Pass mà
vẫn rơi vào ① — nên soát tay).

Chạy:
    python eval/phan_loai_truot_adr051.py --ket-qua <file> [--ra <file .jsonl>]
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

# Cụm dấu hiệu câu hỏi XÁC NHẬN thì-1 ADR-051 — mở rộng dần khi thấy biến thể
# THẬT, không đoán trước cho lỏng.
_MAU_XAC_NHAN = re.compile(
    r"(có đồng ý|đồng ý|có muốn|bạn có|xác nhận).{0,60}"
    r"(tạo (hồ sơ|vé|ticket)|mở (hồ sơ|vé)|tiến hành tạo)",
    re.IGNORECASE,
)

# Dấu hiệu "còn đang chờ khách trả lời thêm" — dấu hỏi thường gặp, cộng biến
# thể kết bằng ":" rồi liệt kê gạch đầu dòng (CASE-011 thật, không có "?" nào).
_MAU_CHO_TIEP = re.compile(r"(\?|được không\s*:)", re.IGNORECASE)

_DO_DAI_DUOI = 350  # ký tự cuối `reply` được xét cho _MAU_CHO_TIEP


def nhom_hoi_thoai(record: dict) -> str:
    """Trả '①' | '②' | '③' — đọc `reply` thật, không dùng tín hiệu gián tiếp
    (tên check, tool_calls, extra_turns_used) để quyết định nhóm."""
    reply = (record.get("reply") or "").strip()
    if _MAU_XAC_NHAN.search(reply):
        return "②"
    if _MAU_CHO_TIEP.search(reply[-_DO_DAI_DUOI:]):
        return "③"
    return "①"


_MAU_CITE_TXN = re.compile(r"^cite_TXN")


def _gom_ten_check(ten: str) -> str:
    """Bó mọi `cite_TXN<mã cụ thể>` (tên khác nhau mỗi ca) vào MỘT hàng
    chung — nếu không, bảng sẽ có một hàng cite_TXN... riêng cho MỖI mã giao
    dịch khác nhau, không đọc được."""
    if _MAU_CITE_TXN.match(ten):
        return "cite_TXN... (trích dẫn mã GD — Ràng buộc cứng #3)"
    return ten


def gom_theo_check(records: list[dict]) -> dict[str, list[int]]:
    """Trả {tên_bó: [đạt, tổng]} — CHỈ gộp trên các record truyền vào (gọi
    hàm này với `records` đã lọc nhóm ①, không tự lọc bên trong)."""
    table_rows: dict[str, list[int]] = {}
    for d in records:
        for item in d.get("checks", []):
            if not isinstance(item, list) or len(item) != 2:
                continue
            ten, val = item
            bo = _gom_ten_check(str(ten))
            if bo not in table_rows:
                table_rows[bo] = [0, 0]
            table_rows[bo][1] += 1
            if val is True:
                table_rows[bo][0] += 1
    return table_rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ket-qua", required=True, type=Path)
    ap.add_argument("--ra", type=Path, default=None)
    args = ap.parse_args()

    records = []
    with open(args.outcome, encoding="utf-8") as f:
        for dong in f:
            dong = dong.strip()
            if dong:
                records.append(json.loads(dong))

    theo_nhom: dict[str, list[dict]] = {"①": [], "②": [], "③": []}
    for d in records:
        theo_nhom[nhom_hoi_thoai(d)].append(d)

    print(f"Tổng: {len(records)} ca")
    print(f"  ① trọn vẹn (đo được)      : {len(theo_nhom['①'])}")
    print(f"  ② cắt — hỏi XÁC NHẬN      : {len(theo_nhom['②'])}   [KHÔNG ĐO ĐƯỢC — dụng cụ đo]")
    print(f"  ③ cắt — hỏi LÀM RÕ        : {len(theo_nhom['③'])}   [KHÔNG ĐO ĐƯỢC — dụng cụ đo, KHÔNG PHẢI LỖI]")

    print(f"\nTỪNG PHÉP KIỂM — CHỈ tính trên nhóm ① (n={len(theo_nhom['①'])} ca):")
    bang_check = gom_theo_check(theo_nhom["①"])
    if not bang_check:
        print("  (nhóm ① rỗng — chưa có ca nào đo được trong lượt này)")
    for ten, (dat, tong_ck) in bang_check.items():
        print(f"  {ten:55s} {dat}/{tong_ck}")

    if theo_nhom["②"]:
        print(f"\n② Cắt vì XÁC NHẬN ({len(theo_nhom['②'])} ca) — chờ Coder vá mô phỏng để đo lại:")
        print(f"  {[d['case_id'] for d in theo_nhom['②']]}")
    if theo_nhom["③"]:
        print(f"\n③ Cắt vì LÀM RÕ ({len(theo_nhom['③'])} ca) — hành vi ĐÚNG, không phải lỗi:")
        print(f"  {[d['case_id'] for d in theo_nhom['③']]}")

    dem_severity: dict[str, int] = {}
    for d in records:
        sv = d.get("severity", "?")
        dem_severity[sv] = dem_severity.get(sv, 0) + 1
    print(f"\nCon số GỘP theo severity (CŨ, tham khảo) — {dict(dem_severity)}")
    print(
        "🔴 KHÔNG dùng con số severity gộp này để báo cáo pass-rate — nó tính "
        "cả ca nhóm ②③ (dụng cụ đo dừng giữa chừng, không phải sản phẩm). "
        "Dùng bảng TỪNG PHÉP KIỂM trên nhóm ① ở trên."
    )

    if args.ra:
        args.ra.parent.mkdir(parents=True, exist_ok=True)
        with open(args.ra, "w", encoding="utf-8") as f:
            for d in records:
                f.write(json.dumps({"case_id": d["case_id"], "severity": d.get("severity"), "nhom": nhom_hoi_thoai(d)}, ensure_ascii=False) + "\n")
        print(f"\nGhi chi tiết: {args.ra}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
