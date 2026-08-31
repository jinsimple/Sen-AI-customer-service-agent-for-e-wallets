"""Bơm lượt khách NGUYÊN VĂN vào các ô `[CHƯA ĐIỀN]` của `goi-cham-NGUOI-v2.md`.

Việc PO thật giao 30/08 (chặn 15 điểm Trải nghiệm + điều kiện hiệu chuẩn heldout).

CÁCH GHÉP — KHÔNG mở `KHOA-doi-chieu.md`, KHÔNG chạy `sinh-goi-cham.py`:
`cases.py` giữ 28 ca THEO ĐÚNG THỨ TỰ GỐC (`goi_30_nhan_NGUOI.md`, KHÔNG xáo),
mỗi ca có `sid` + `agent` (văn bản agent — KHÔNG bị che trong bất kỳ bản nào).
`goi-cham-NGUOI-v2.md` là CÙNG 28 ca đó, chỉ ĐÃ XÁO thứ tự và ĐÃ CHE `khach`.
⟹ so khớp CHÍNH XÁC văn bản `**Agent:**` giữa hai file là đủ để tìm lại đúng
`sid`, KHÔNG cần bảng đối chiếu L-số↔sid — script này thấy sid lúc chạy,
người chấm đọc lại file thì KHÔNG thấy (chỉ thấy lời khách trần trụi).

Utterance thật lấy từ `eval/llm_judge_set.jsonl` (case_id == sid), NGUYÊN VĂN
không rút gọn/diễn giải.

RỦI RO ĐÃ PHÁT HIỆN, XỬ LÝ RÕ RÀNG THAY VÌ ĐOÁN:
- UXQA-005 (ca_cu=11) và UXQA-006 (ca_cu=15) tình cờ có **agent text GIỐNG HỆT
  NHAU** ("Mình xin phép không hỗ trợ được nội dung này vì ngoài phạm vi...").
  Text-match KHÔNG phân biệt được 2 block này thuộc sid nào — CỐ Ý bỏ qua,
  không đoán, in ra danh sách `L##` liên quan để PO/Lead tự quyết cách xử lý.
  ⚠️ [ĐO 30/08, lần chạy đầu SAI]: lần đầu viết script này tôi đoán nhầm cặp
  trùng là (9, 15) — KHÔNG kiểm lại bằng máy, chỉ nhớ từ output rút gọn của
  `Counter`. Hậu quả: ca_cu=9 (agent text THỰC RA khác/không trùng, "Xin lỗi,
  nhưng mình không có thông tin chính xác về đầu tư...") bị loại OAN, còn cặp
  trùng THẬT (11, 15) chỉ loại được 15 — ca_cu=11 lọt qua, khiến CẢ HAI khối
  md có text trùng bị bơm NHẦM cùng một câu (của UXQA-005) dù một trong hai lẽ
  ra phải là câu UXQA-006. Bắt được TRƯỚC khi báo cáo nhờ backup + đối chiếu
  lại bằng tay ngay sau lượt chạy đầu — không phải nhờ code tự kiểm. Bài học:
  đừng suy ra ca_cu từ trí nhớ, luôn in tường minh bằng máy (`by_text` bên
  dưới) trước khi đưa vào set loại trừ.
- UXQA-004 (2 lượt khách, turn0+turn1) xuất hiện 2 lần (ca_cu=10, ca_cu=21).
  Nội dung agent ca_cu=21 khớp rõ với việc trả lời turn1 ("chắc chắn... đúng
  không" ↔ câu hỏi turn1) nên bơm CẢ HAI lượt (đánh số rõ) cho ca_cu=21, và
  chỉ turn0 cho ca_cu=10 (agent hỏi lại loại/phạm vi khiếu nại — khớp phản
  ứng lần đầu). Đây là SUY LUẬN có dẫn chứng, không phải chắc chắn tuyệt đối
  — gắn nhãn ⚠️ để Lead/PO biết đây là ca cần soát lại, KHÔNG lẫn với 18 ca
  còn lại (khớp 1-1 tuyệt đối, không có gì để đoán).

Chạy một lần: `python eval/bo-cham/bom_loi_khach.py`
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))
from cases import CASES  # noqa: E402

MD = GOC / "goi-cham-NGUOI-v2.md"
JUDGE_SET = GOC.parent / "llm_judge_set.jsonl"

PLACEHOLDER = "[CHƯA ĐIỀN — bơm lượt khách từ nguồn eval trước khi chấm ca này]"

# ca_cu tình cờ trùng agent text với ca_cu khác -- KHÔNG được match tự động.
# [ĐO 30/08] Xác nhận bằng máy (KHÔNG suy từ trí nhớ, xem docstring):
# {11: UXQA-005, 15: UXQA-006} trùng agent text. ca_cu=9 (cũng UXQA-005)
# CÓ agent text riêng, KHÔNG trùng ai -- không được đưa vào set này.
CA_CU_MO_HO = {11, 15}
# ca_cu=10/21 cùng sid UXQA-004 (2 lượt) -- xử lý riêng, xem docstring.
CA_CU_UXQA004_TURN0_ONLY = 10
CA_CU_UXQA004_CA_HAI_LUOT = 21


def _doc_utterances() -> dict[str, list[str]]:
    ra: dict[str, list[str]] = {}
    with open(JUDGE_SET, encoding="utf-8") as f:
        for dong in f:
            dong = dong.strip()
            if not dong:
                continue
            d = json.loads(dong)
            ra[d["case_id"]] = d["utterances"]
    return ra


def _kiem_tra_CA_CU_MO_HO() -> None:
    """Xác nhận BẰNG MÁY set loại trừ đúng — không tin trí nhớ (xem docstring
    về lần chạy đầu sai 30/08)."""
    from collections import defaultdict

    theo_text: dict[str, list[int]] = defaultdict(list)
    for ca in CASES:
        if ca["khach"] is None:
            theo_text[ca["agent"].strip()].append(ca["ca_cu"])

    trung_that = set()
    for _text, ca_cu_list in theo_text.items():
        if len(ca_cu_list) > 1:
            trung_that.update(ca_cu_list)

    assert trung_that == CA_CU_MO_HO, (
        f"CA_CU_MO_HO khai {sorted(CA_CU_MO_HO)} nhưng đo bằng máy ra "
        f"{sorted(trung_that)} — DỪNG, sửa hằng số trước khi chạy tiếp."
    )


def _xay_bang_bom(utterances: dict[str, list[str]]) -> dict[int, tuple[str, str]]:
    """ca_cu -> (agent_text_chuan_hoa, van_ban_bom)."""
    bang: dict[int, tuple[str, str]] = {}
    for ca in CASES:
        if ca["khach"] is not None:
            continue
        ca_cu = ca["ca_cu"]
        sid = ca["sid"]
        agent_chuan = ca["agent"].strip()

        if ca_cu in CA_CU_MO_HO:
            continue  # cố ý bỏ qua -- xem docstring

        if sid == "UXQA-004":
            u = utterances["UXQA-004"]
            if ca_cu == CA_CU_UXQA004_TURN0_ONLY:
                bom = u[0]
            elif ca_cu == CA_CU_UXQA004_CA_HAI_LUOT:
                bom = f"(lượt 1) {u[0]}\n\n(lượt 2 -- câu hỏi tiếp theo) {u[1]}"
            else:
                raise AssertionError(f"UXQA-004 xuất hiện ở ca_cu={ca_cu} chưa được xử lý")
        else:
            u = utterances[sid]
            assert len(u) == 1, f"{sid} có {len(u)} lượt, script chỉ xử lý CỨNG 1 lượt trừ UXQA-004"
            bom = u[0]

        bang[ca_cu] = (agent_chuan, bom)
    return bang


def main() -> int:
    _kiem_tra_CA_CU_MO_HO()
    utterances = _doc_utterances()
    bang = _xay_bang_bom(utterances)

    noi_dung = MD.read_text(encoding="utf-8")
    khoi = re.split(r"(?=^## L\d+$)", noi_dung, flags=re.MULTILINE)

    # agent_text_chuan_hoa -> van_ban_bom, để tra theo NỘI DUNG khối trong md
    tra_theo_agent: dict[str, str] = {}
    trung_lap: set[str] = set()
    for _ca_cu, (agent_chuan, bom) in bang.items():
        if agent_chuan in tra_theo_agent:
            trung_lap.add(agent_chuan)
        tra_theo_agent[agent_chuan] = bom
    assert not trung_lap, f"Agent text trùng lặp NGOÀI danh sách CA_CU_MO_HO đã biết: {trung_lap}"

    da_bom = 0
    khong_khop: list[str] = []
    khoi_moi = []
    for k in khoi:
        if PLACEHOLDER not in k:
            khoi_moi.append(k)
            continue

        m = re.search(r"\*\*Agent:\*\*\s*(.*?)\n\n```", k, flags=re.DOTALL)
        if not m:
            khoi_moi.append(k)
            khong_khop.append("(không tách được khối Agent)")
            continue
        agent_text = m.group(1).strip()

        if agent_text in tra_theo_agent:
            bom = tra_theo_agent[agent_text]
            k_moi = k.replace(PLACEHOLDER, bom, 1)
            khoi_moi.append(k_moi)
            da_bom += 1
        else:
            tieu_de = re.match(r"^## (L\d+)", k)
            khong_khop.append(tieu_de.group(1) if tieu_de else "(không rõ L-id)")
            khoi_moi.append(k)

    MD.write_text("".join(khoi_moi), encoding="utf-8")

    con_lai = MD.read_text(encoding="utf-8").count(PLACEHOLDER)
    print(f"Đã bơm: {da_bom}/20")
    print(f"Còn [CHƯA ĐIỀN] (placeholder đầy đủ, KHÔNG tính câu mô tả ở mục hướng dẫn): {con_lai}")
    if khong_khop:
        print("Chưa bơm được (cố ý, xem docstring — KHÔNG đoán):")
        for x in khong_khop:
            print(f"  - {x}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
