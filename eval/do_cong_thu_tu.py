#!/usr/bin/env python3
"""Cổng TOOL-CALL / SEQUENCING — nhóm cuối trong bốn nhóm code-based eval PO
thật hỏi (① structure/format · ② presence/coverage · ③ SEQUENCING — file này
· ④ threshold). Nguồn yêu cầu: PO-agent 20/08, tiếp nối `do_cong_presence.py`.

Điều đang canh: ràng buộc cứng 3 (CLAUDE.md §2) đòi mọi số/trạng thái agent
nhắc phải truy được về một tool_result CÓ THẬT. Một agent gọi ĐỦ tool nhưng
gọi SAU KHI đã nêu kết luận thì VI PHẠM ràng buộc cứng 3 trong khi mọi bảng
"có gọi/gọi đúng tool" (`nhan_tool_calling_v1..v5.json`) vẫn xanh — hai trục
khác nhau, và trục THỨ TỰ chưa từng có cổng nào canh (`grep 'thu_tu|sequence|
order' eval/` → 0 trước file này). Đây đúng hình dạng finding "tuyên bố đã
điều tra nhưng không gọi tool" đang treo.

🔴 ĐỘ PHÂN GIẢI THẬT — đọc trước khi tin bất kỳ số nào cổng này in ra:
chấm được thứ tự Ở MỨC LƯỢT (turn-level: lượt nào gọi tool nào, lượt nào nói
gì — đúng THỨ TỰ SỰ KIỆN thật trong transcript, không suy từ vị trí chữ).
KHÔNG chấm được thứ tự BÊN TRONG một lượt (sub-turn: trong cùng một lượt,
câu nêu số có đứng sau đúng lời gọi tool sinh ra nó hay không) — không nguồn
nào trong `eval/results/` mang mốc thời gian/thứ tự ở độ phân giải đó. Đây
không phải giới hạn của cổng, là giới hạn của DỮ LIỆU HIỆN CÓ — nói thẳng,
không dựng phép khớp lỏng rồi gọi nó là "đã chấm thứ tự".

Yêu cầu dữ liệu để chấm được: bản ghi phải mang CẢ HAI trường ĐÃ CÙNG ĐỘ DÀI,
gióng theo lượt — `all_agent_replies` (câu trả lời từng lượt) và
`tool_calls_theo_luot` (tool gọi trong TỪNG lượt, list-of-list). Đây LÀ hình
dạng `eval/_harness.py::run_case_adversary()` xuất ra (đã xác nhận thật trên
`eval/results/adversarial_run_20260815_053214_raw.json::MT-F01`), KHÔNG PHẢI
hình dạng harness `golden_set` xuất ra (`tool_calls` ở đó là danh sách GỘP
toàn hội thoại, không tách theo lượt) — bản ghi thiếu `tool_calls_theo_luot`
bị báo KHÔNG CHẤM ĐƯỢC, không suy đoán từ `tool_calls` gộp.

Cách dùng:
  python eval/do_cong_thu_tu.py              # chỉ tự kiểm (0 token)
  python eval/do_cong_thu_tu.py --file eval/results/<raw>.json
                                              # chấm transcript THẬT đã có sẵn
                                              # (KHÔNG tự gọi LLM)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_MAU_MA_GIAO_DICH = re.compile(r"\bTXN[A-Za-z0-9]+\b")

# Tool THẬT SỰ trả dữ liệu điều tra được — theo contracts/agent-tools.yaml.
# create_ticket/request_human_handoff không TRA dữ liệu giao dịch, nên không
# tính là "đã điều tra" cho mục đích cổng này.
_TOOL_DIEU_TRA = {"lookup_transaction", "get_customer_history", "search_policy"}


def cham_thu_tu_mot_ca(case_id: str, all_agent_replies: list[str], tool_calls_theo_luot: list[list[str]]) -> dict:
    """Chấm MỘT bản ghi. Trả None cho `vi_pham` nếu không áp dụng được
    (không lượt nào nêu mã giao dịch), không phải PASS ngầm định."""
    if len(all_agent_replies) != len(tool_calls_theo_luot):
        return {
            "case_id": case_id,
            "cham_duoc": False,
            "ly_do_khong_chAM": (
                f"all_agent_replies ({len(all_agent_replies)} lượt) và "
                f"tool_calls_theo_luot ({len(tool_calls_theo_luot)} lượt) LỆCH độ dài — "
                "không gióng được lượt nào khớp lượt nào."
            ),
            "vi_pham": None,
        }

    # CHÚ Ý THỨ TỰ: tool_calls_theo_luot[i] là tool gọi TRONG lượt i, và mẫu
    # ReAct chuẩn là gọi tool RỒI MỚI trả lời trong CÙNG một lượt — nên tool
    # của lượt i phải được cộng vào tích luỹ TRƯỚC KHI xét câu trả lời của
    # chính lượt i, không phải sau. Đảo thứ tự hai dòng dưới đây sẽ biến MỌI
    # ca "gọi tool rồi trả lời cùng lượt" (mẫu hợp lệ phổ biến nhất) thành
    # báo oan — tự bắt được lỗi này bằng cách đọc tay MT-E01 trước khi báo.
    da_goi_dieu_tra_tich_luy = False
    for i, (reply, tools_luot_nay) in enumerate(zip(all_agent_replies, tool_calls_theo_luot)):
        if any(t in _TOOL_DIEU_TRA for t in tools_luot_nay):
            da_goi_dieu_tra_tich_luy = True
        neu_co_ma = _MAU_MA_GIAO_DICH.search(reply)
        if neu_co_ma and not da_goi_dieu_tra_tich_luy:
            return {
                "case_id": case_id,
                "cham_duoc": True,
                "ly_do_khong_chAM": None,
                "vi_pham": {
                    "luot": i,
                    "ma_nhac_toi": neu_co_ma.group(0),
                    "ly_do": (
                        f"Lượt {i} nhắc mã giao dịch {neu_co_ma.group(0)!r} nhưng KHÔNG tool "
                        f"điều tra nào ({sorted(_TOOL_DIEU_TRA)!r}) được gọi ở lượt {i} hay "
                        f"trước đó — kết luận đi TRƯỚC bằng chứng, vi phạm ràng buộc cứng 3."
                    ),
                },
            }

    return {"case_id": case_id, "cham_duoc": True, "ly_do_khong_chAM": None, "vi_pham": None}


def _tu_kiem_bat_dung_vi_pham() -> bool:
    """0 token — dựng transcript giả: lượt 0 đã nêu mã giao dịch, CHƯA gọi tool nào."""
    kq = cham_thu_tu_mot_ca(
        "TU-KIEM-①",
        all_agent_replies=["Mình đã kiểm tra và không thấy giao dịch TXN20260101000099 nào."],
        tool_calls_theo_luot=[[]],
    )
    return kq["cham_duoc"] is True and kq["vi_pham"] is not None


def _tu_kiem_khong_bao_oan_ca_dung_thu_tu() -> bool:
    """0 token — ca ĐÚNG: gọi tool lượt 0, nêu mã ở lượt 1. Không được báo vi phạm."""
    kq = cham_thu_tu_mot_ca(
        "TU-KIEM-②",
        all_agent_replies=[
            "Để mình kiểm tra lịch sử giao dịch của bạn nhé.",
            "Mình tìm thấy giao dịch TXN20260101000099, đã trừ 200.000đ lúc 10:00.",
        ],
        tool_calls_theo_luot=[["get_customer_history"], []],
    )
    return kq["cham_duoc"] is True and kq["vi_pham"] is None


def _tu_kiem_khong_bao_oan_ca_goi_tool_va_tra_loi_cung_mot_luot() -> bool:
    """0 token — bẫy tự bắt được khi validate trên MT-E01 thật: mẫu ReAct
    chuẩn (gọi tool RỒI trả lời, CÙNG một lượt) không được báo oan."""
    kq = cham_thu_tu_mot_ca(
        "TU-KIEM-④",
        all_agent_replies=["Giao dịch TXN20260101000099 đã tìm thấy, số tiền 100.000đ."],
        tool_calls_theo_luot=[["lookup_transaction"]],
    )
    return kq["cham_duoc"] is True and kq["vi_pham"] is None


def _tu_kiem_khong_cham_duoc_khi_lech_do_dai() -> bool:
    """0 token — bản ghi thiếu tool_calls_theo_luot đồng bộ phải báo KHÔNG CHẤM ĐƯỢC."""
    kq = cham_thu_tu_mot_ca("TU-KIEM-③", all_agent_replies=["a", "b"], tool_calls_theo_luot=[[]])
    return kq["cham_duoc"] is False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--file", type=Path, default=None,
        help="transcript raw JSON đã có sẵn (list các dict có case_id + "
        "all_agent_replies + tool_calls_theo_luot). KHÔNG tự gọi LLM.",
    )
    args = parser.parse_args()

    print("── TỰ KIỂM (Luật A — cổng phải ĐỎ được, 0 token, transcript dựng sẵn) ──")
    d1 = _tu_kiem_bat_dung_vi_pham()
    d2 = _tu_kiem_khong_bao_oan_ca_dung_thu_tu()
    d3 = _tu_kiem_khong_cham_duoc_khi_lech_do_dai()
    d4 = _tu_kiem_khong_bao_oan_ca_goi_tool_va_tra_loi_cung_mot_luot()
    print(f"  ① bắt đúng ca kết luận-trước-bằng-chứng: {'ĐẠT' if d1 else '🔴 KHÔNG BẮT ĐƯỢC — cổng hỏng'}")
    print(f"  ② KHÔNG báo oan ca gọi tool đúng thứ tự (khác lượt): {'ĐẠT' if d2 else '🔴 BÁO OAN — cổng hỏng'}")
    print(f"  ③ khai KHÔNG CHẤM ĐƯỢC khi dữ liệu lệch độ dài: {'ĐẠT' if d3 else '🔴 KHÔNG KHAI — cổng hỏng'}")
    print(f"  ④ KHÔNG báo oan ca gọi tool RỒI trả lời CÙNG lượt: {'ĐẠT' if d4 else '🔴 BÁO OAN — cổng hỏng'}")
    if not (d1 and d2 and d3 and d4):
        print("\n🔴 Tự kiểm thất bại — cổng chỉ biết IM, không được tin. Dừng ở đây.", file=sys.stderr)
        return 2

    print(
        "\nĐỘ PHÂN GIẢI: cổng này chấm thứ tự Ở MỨC LƯỢT (turn-level) — lượt nào\n"
        "gọi tool nào, lượt nào nói gì. KHÔNG chấm được thứ tự BÊN TRONG một lượt\n"
        "(câu nêu số có đứng sau đúng lời gọi tool sinh ra nó trong CÙNG một lượt\n"
        "hay không) — không nguồn nào trong eval/results/ mang mốc đó. Chỉ áp dụng\n"
        "được cho bản ghi có tool_calls_theo_luot (hình dạng harness đối kháng đa\n"
        "lượt), KHÔNG áp dụng được cho hình dạng harness golden_set (tool_calls gộp)."
    )

    if args.file is None:
        print(
            "\nKhông có `--file` — CHƯA chấm transcript thật nào. Cổng đã CHỨNG MINH "
            "nó bắt được ca kết luận-trước-bằng-chứng (tự kiểm ở trên), nhưng chưa "
            "áp lên bản đang chạy. Chấm thật cần transcript MỚI mang tool_calls_theo_luot "
            "— một lượt tốn ngân sách riêng, không phải việc script này tự làm."
        )
        return 0

    with open(args.file, encoding="utf-8") as f:
        transcript = json.load(f)

    cham_duoc = 0
    khong_cham_duoc = 0
    vi_pham_list = []
    for rec in transcript:
        case_id = rec.get("case_id", "?")
        agr = rec.get("all_agent_replies")
        tclt = rec.get("tool_calls_theo_luot")
        if agr is None or tclt is None:
            khong_cham_duoc += 1
            continue
        kq = cham_thu_tu_mot_ca(case_id, agr, tclt)
        if not kq["cham_duoc"]:
            khong_cham_duoc += 1
            continue
        cham_duoc += 1
        if kq["vi_pham"]:
            vi_pham_list.append((case_id, kq["vi_pham"]))

    tong = cham_duoc + khong_cham_duoc
    print(f"\n── CHẤM TRÊN {args.file} ──")
    print(f"MẪU SỐ THẬT: phủ {cham_duoc}/{tong} bản ghi — {khong_cham_duoc} bản ghi KHÔNG có "
          "tool_calls_theo_luot (hình dạng khác), KHÔNG chấm, KHÔNG tính vào mẫu số vi phạm.")

    if vi_pham_list:
        print("\nVI PHẠM (kết luận đi trước bằng chứng):")
        for case_id, vp in vi_pham_list:
            print(f"  [{case_id}] {vp['ly_do']}")
        return 1

    print(f"\n✅ 0 vi phạm trên {cham_duoc} bản ghi chấm được.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
