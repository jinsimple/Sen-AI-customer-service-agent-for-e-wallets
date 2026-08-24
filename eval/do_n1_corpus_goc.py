#!/usr/bin/env python3
"""ĐO N1 — cổng `thu_slot` bắn bao nhiêu lần trên CORPUS GỐC `eval/*.jsonl`.

    python eval/do_n1_corpus_goc.py [<luat_nen.py>]

Dựng nền để so:  `git show a3bc860:src/agents/phan_luong.py > /tmp/pl_nen.py`

🔴 `heldout_set.jsonl` LOẠI TUYỆT ĐỐI — niêm phong (`CLAUDE.md` §6).

## Nguồn gốc — Coder, 25/08, đợt "OTP trước token"

QA/QC dựng `eval/bo_ca_am_thu_slot_dot2.json` (② trong đợt) là bộ **7 ca
độc lập** dựng TỪ ĐẶC TẢ Đ1 — đúng, nhưng "xanh trên bản dựng lại không
chứng minh gì về corpus gốc" (lớp lỗi đội đã bắt nhiều lần trong dự án này).
Script này đo TRỰC TIẾP trên toàn bộ 14 tệp `eval/*.jsonl` thật đang có —
[ĐO 25/08, QA/QC tái lập ĐỘC LẬP, khớp tuyệt đối]: 409 câu, nền `a3bc860`
bắn 15 lần, HEAD bắn 13 lần. Chỉ đóng được 2 (= ADV-036 + ADV-038).

## 🔴 KHÔNG PHẢI CỔNG PASS/FAIL — luôn `return 0`, và đó là CHỦ Ý

Coder tự cảnh báo lúc bàn giao, và QA/QC giữ nguyên quyết định đó khi nhận
script vào `eval/` (vùng QA/QC, 25/08): **đừng ghim ngưỡng "13" làm điều
kiện đỏ/xanh.** Corpus sẽ lớn lên theo thời gian — một cổng đỏ mỗi khi có
người thêm một câu hợp lệ vào corpus sẽ bị nới ngưỡng theo phản xạ (đúng bài
học `XA_GIAO`/ngân sách token đã lặp lại nhiều lần trong dự án này), và một
ngưỡng bị nới theo phản xạ thì thà không có.

**Cái đáng ghim là MẪU SỐ (409) và DANH SÁCH câu đang bắn oan, không phải
CON SỐ ĐẾM.** Script tự kiểm mẫu số (dòng `if tong != 409`) — bộ bóc câu đã
từng hỏng HAI LẦN trong lúc dựng (7/409 rồi 349/409, mù `utterances` dạng
list rồi mù `query_co_dau`) và cả hai lần đều lệch theo hướng TRẤN AN (mẫu
số nhỏ hơn, tưởng đã đóng hết). Mẫu số khác 409 ⟹ ĐỪNG tin số bắn.

## Danh sách 13 câu đã biết, [ĐO] 25/08 (HEAD lúc đó) — dùng để lọc MỚI/CŨ

Script không tự động diff — người chạy tự đối chiếu output với danh sách
dưới đây. Câu KHÔNG có trong danh sách này mà vẫn bắn ⟹ REGRESSION MỚI,
đáng báo ngay. Câu CÓ trong danh sách mà đã hết bắn ⟹ tốt, cập nhật danh
sách này (đừng lặng lẽ để nó lỗi thời — đúng lỗi ĐANG BỊ SỬA của chính N1).

    Nguyên nhân (Coder phân loại, QA/QC đối chiếu lại bằng mắt, khớp):
      chính sách (2)             — "chính sách xử lý khiếu nại"/"có chính sách gì"
      đã phân loại xong (2-3)    — nhắc lại một phân loại đã có ("đúng là...",
                                    "cho giao dịch...đó")
      khách cần hướng dẫn (1)    — người lớn tuổi, không rành công nghệ
      khiếu nại thật ĐÚNG (3)    — không oan, thật sự thiếu slot bắt buộc
      khác/cần phân loại thêm (5) — chưa xếp dứt khoát vào nhóm nào ở trên

    adversarial_multiturn_set.jsonl × 6, bo_lenh_do.jsonl × 4,
    golden_set.jsonl × 1, golden_set_truy_hoi.jsonl × 1, llm_judge_set.jsonl × 1
"""
from __future__ import annotations

import glob
import importlib.util
import json
import sys

KHOA_CHUOI = ("cau", "input", "message", "text", "prompt", "query_co_dau")
KHOA_LIST = ("utterances", "turns", "luot", "messages")
KHOA_TRONG_DICT = ("cau", "content", "text", "user", "utterance")

MAU_SO_MOC = 409  # [ĐO 25/08] — đổi số này CHỈ khi đã xác nhận corpus THẬT đổi, không phải bộ bóc hỏng


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


def main() -> int:
    moi = nap("src/agents/phan_luong.py", "_luat_head")
    nen = nap(sys.argv[1], "_luat_nen") if len(sys.argv) > 1 else None
    files = [f for f in sorted(glob.glob("eval/*.jsonl")) if "heldout" not in f]
    tong = nen_n = moi_n = 0
    con_ban = []
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
    if nen:
        print(f"  nền  {sys.argv[1]}  → thu_slot {nen_n}")
    print(f"  HEAD → thu_slot {moi_n}   — không phải cổng pass/fail, xem docstring")
    print("  (đối chiếu TAY với danh sách 13 câu đã biết trong docstring — câu MỚI"
          " không có trong danh sách là regression đáng báo ngay)\n")
    for f, c in con_ban:
        print(f"  [{f}] {c[:88]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
