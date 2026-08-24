#!/usr/bin/env python3
"""Cổng PRESENCE — "câu trả lời có đủ thứ BẮT BUỘC không", chiều mà dự án
CHƯA TỪNG canh (mọi bộ lọc O1-O4 + `forbidden`/`forbidden_reply_patterns` chỉ
hỏi "có chứa thứ CẤM không"). Nguồn yêu cầu: PO thật hỏi qua PO-agon 20/08.

Đo trên `eval/golden_set.jsonl` (schema `expected`), CHỈ hai trục có tín hiệu
THẬT trong corpus — không tự vẽ thêm quy tắc mặc định cho phần corpus không
nói gì (xem "MẪU SỐ" bên dưới, in ra mỗi lần chạy, không chỉ trong tài liệu):

  ① MÃ VÉ    — 50/120 ca có cờ rõ (`must_create_manual_ticket` ·
               `must_ask_clarifying_question` · `must_offer_before_creating_ticket`)
  ② CĂN CỨ   — 118/120 ca có `must_cite_trans_ids` (2 ca rỗng ĐÚNG vì cả hai
               `must_ask_clarifying_question=true` — chưa tra ra thì không có
               gì để trích, tự giải thích chính nó)

70 ca còn lại của ① KHÔNG có cờ nào — corpus không nói ca đó có cần vé hay
không, và không nguồn nào khác (PRD/US) định nghĩa được quy tắc mặc định.
KHÔNG tính vào mẫu số, KHÔNG suy đoán. Vẽ một quy tắc mặc định vào đó là vẽ
giả định vào dữ liệu, không phải đọc dữ liệu.

⛔ ③ BƯỚC TIẾP THEO · ④ TRẠNG THÁI — CHƯA KIỂM ĐƯỢC, khai ngay tại đây (không
phải một tài liệu riêng, để không ai quên đi tra):
  ③ không trường nào trong `expected`/`forbidden` mã hoá nội dung "bước tiếp
    theo"; không văn bản nào trong docs/contracts định nghĩa cụm từ chuẩn.
    Dựng regex đoán cụm từ = nhóm (b) (cổng-canh-cơ-chế-giả-vờ-canh-lời-hứa).
  ④ `contracts/resolution-state-machine.yaml` có state THẬT (draft/
    pending_approval/approved/rejected, hitl_status, partner_wait_status)
    nhưng đó là MÃ NỘI BỘ DB, không phải câu tiếng Việt agent nói với khách.
    Ánh xạ mã→câu (nếu có) nằm trong prompt — ngoài vùng đọc được của tester.
    Một nguồn TỒN TẠI không có nghĩa nó là nguồn CHO CÂU HỎI NÀY.

Cách dùng:
  python eval/do_cong_presence.py              # chỉ tự kiểm (0 token, xem SELF-TEST)
  python eval/do_cong_presence.py --file eval/results/<raw>.json
                                                # chấm transcript THẬT đã có sẵn
                                                # (KHÔNG tự gọi LLM — không chi
                                                # thêm ngân sách; nếu chưa có
                                                # transcript mới, phải nói rõ
                                                # transcript đó cũ bao nhiêu)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_MAU_TICKET = re.compile(r"\bTCK-[A-Za-z0-9]+\b")


def _tai_golden_set() -> dict[str, dict]:
    ca_theo_id = {}
    with open(ROOT / "eval" / "golden_set.jsonl", encoding="utf-8") as f:
        for dong in f:
            dong = dong.strip()
            if not dong:
                continue
            d = json.loads(dong)
            ca_theo_id[d["case_id"]] = d
    return ca_theo_id


def cham_co_mat(case: dict, reply: str) -> dict:
    """Chấm MỘT ca trên HAI trục có tín hiệu thật. Trả None cho trục không
    áp dụng được (không phải FAIL — là 'không có gì để chấm')."""
    exp = case.get("expected") or {}
    ket_qua: dict = {"case_id": case["case_id"], "ma_ve": None, "can_cu": None}

    # ── ① MÃ VÉ — chỉ chấm khi có cờ rõ, ưu tiên must_create_manual_ticket
    # (dương tính cụ thể) trước hai cờ "chưa nên có vé" ──
    co_ve = bool(_MAU_TICKET.search(reply))
    if exp.get("must_create_manual_ticket") is True:
        ket_qua["ma_ve"] = {
            "ap_dung": "must_create_manual_ticket",
            "dat": co_ve,
            "ly_do": None if co_ve else "Kỳ vọng có mã vé (TCK-...), reply không có.",
        }
    elif exp.get("must_ask_clarifying_question") is True or exp.get("must_offer_before_creating_ticket") is True:
        nguon = "must_ask_clarifying_question" if exp.get("must_ask_clarifying_question") else "must_offer_before_creating_ticket"
        ket_qua["ma_ve"] = {
            "ap_dung": nguon,
            "dat": not co_ve,
            "ly_do": None if not co_ve else "Kỳ vọng CHƯA có mã vé (cần hỏi lại/xác nhận trước), reply đã có.",
        }
    # else: không cờ nào -> giữ None, không chấm (70 ca "mờ")

    # ── ② CĂN CỨ — khớp CHUỖI mã giao dịch, không khớp câu chữ ──
    can_cu_can = exp.get("must_cite_trans_ids") or []
    if can_cu_can:
        thieu = [t for t in can_cu_can if t not in reply]
        ket_qua["can_cu"] = {
            "can": can_cu_can,
            "dat": not thieu,
            "thieu": thieu,
        }
    # else: rỗng (2 ca must_ask_clarifying_question) -> giữ None, không chấm

    return ket_qua


def _in_mau_so(ca_theo_id: dict) -> None:
    tong = len(ca_theo_id)
    co_co_ve = sum(
        1
        for c in ca_theo_id.values()
        if (c.get("expected") or {}).get("must_create_manual_ticket") is True
        or (c.get("expected") or {}).get("must_ask_clarifying_question") is True
        or (c.get("expected") or {}).get("must_offer_before_creating_ticket") is True
    )
    co_can_cu = sum(1 for c in ca_theo_id.values() if (c.get("expected") or {}).get("must_cite_trans_ids"))
    print("MẪU SỐ THẬT (khai trước khi đọc bất kỳ số nào dưới đây):")
    print(f"  ① mã vé : phủ {co_co_ve}/{tong} ca — {tong - co_co_ve} ca còn lại KHÔNG có tín hiệu, KHÔNG chấm.")
    print(f"  ② căn cứ: phủ {co_can_cu}/{tong} ca — {tong - co_can_cu} ca rỗng ĐÚNG (chưa tra ra thì không có gì trích).")
    print(f"  ③ bước tiếp theo · ④ trạng thái: 0/{tong} — CHƯA KIỂM ĐƯỢC, xem docstring đầu file vì sao.")


def _tu_kiem_do_duoc_thieu_ve() -> bool:
    ca = {
        "case_id": "TU-KIEM-①",
        "expected": {"must_create_manual_ticket": True},
    }
    reply_thieu = "Mình đã ghi nhận phản ánh của bạn, bộ phận liên quan sẽ xử lý."
    kq = cham_co_mat(ca, reply_thieu)
    return kq["ma_ve"] is not None and kq["ma_ve"]["dat"] is False


def _tu_kiem_do_duoc_thieu_can_cu() -> bool:
    ca = {
        "case_id": "TU-KIEM-②",
        "expected": {"must_cite_trans_ids": ["TXN20260101000099"]},
    }
    reply_thieu = "Mình đã kiểm tra và ghi nhận phản ánh của anh, bộ phận liên quan sẽ xử lý."
    kq = cham_co_mat(ca, reply_thieu)
    return kq["can_cu"] is not None and kq["can_cu"]["dat"] is False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--file", type=Path, default=None,
        help="transcript raw JSON đã có sẵn (list các dict có case_id + reply). "
        "KHÔNG tự gọi LLM — không cung cấp thì chỉ chạy tự kiểm (0 token).",
    )
    args = parser.parse_args()

    print("── TỰ KIỂM (Luật A — cổng phải ĐỎ được, 0 token, câu dựng sẵn) ──")
    dat_1 = _tu_kiem_do_duoc_thieu_ve()
    dat_2 = _tu_kiem_do_duoc_thieu_can_cu()
    print(f"  ① bắt đúng câu THIẾU mã vé: {'ĐẠT' if dat_1 else '🔴 KHÔNG BẮT ĐƯỢC — cổng hỏng'}")
    print(f"  ② bắt đúng câu THIẾU căn cứ: {'ĐẠT' if dat_2 else '🔴 KHÔNG BẮT ĐƯỢC — cổng hỏng'}")
    if not (dat_1 and dat_2):
        print("\n🔴 Tự kiểm thất bại — cổng chỉ biết IM, không được tin. Dừng ở đây.", file=sys.stderr)
        return 2

    ca_theo_id = _tai_golden_set()
    print()
    _in_mau_so(ca_theo_id)

    if args.file is None:
        print(
            "\nKhông có `--file` — CHƯA chấm transcript thật nào. Cổng đã CHỨNG MINH nó "
            "bắt được câu thiếu (tự kiểm ở trên), nhưng chưa áp lên bản đang chạy. Chấm "
            "thật cần một transcript golden_set MỚI (120 ca thật) — đó là một lượt tốn "
            "ngân sách riêng, không phải việc script này tự làm."
        )
        return 0

    with open(args.file, encoding="utf-8") as f:
        transcript = json.load(f)
    reply_theo_id = {t["case_id"]: t.get("reply", "") for t in transcript if t.get("case_id") in ca_theo_id}

    print(f"\n── CHẤM TRÊN {args.file} ({len(reply_theo_id)}/{len(ca_theo_id)} ca khớp case_id) ──")

    vi_pham = []
    dat_1_dem = thieu_1 = dat_2_dem = thieu_2 = 0
    for case_id, case in ca_theo_id.items():
        reply = reply_theo_id.get(case_id)
        if reply is None:
            continue
        kq = cham_co_mat(case, reply)
        if kq["ma_ve"] is not None:
            if kq["ma_ve"]["dat"]:
                dat_1_dem += 1
            else:
                thieu_1 += 1
                vi_pham.append(f"  [① {case_id}] {kq['ma_ve']['ly_do']}")
        if kq["can_cu"] is not None:
            if kq["can_cu"]["dat"]:
                dat_2_dem += 1
            else:
                thieu_2 += 1
                vi_pham.append(f"  [② {case_id}] thiếu trích: {kq['can_cu']['thieu']}")

    print(f"  ① mã vé : {dat_1_dem} đạt · {thieu_1} thiếu (trên {dat_1_dem + thieu_1} ca có chấm)")
    print(f"  ② căn cứ: {dat_2_dem} đạt · {thieu_2} thiếu (trên {dat_2_dem + thieu_2} ca có chấm)")

    if vi_pham:
        print("\nVI PHẠM:")
        print("\n".join(vi_pham))
        return 1

    print("\n✅ Không vi phạm nào trên phần corpus có tín hiệu.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
