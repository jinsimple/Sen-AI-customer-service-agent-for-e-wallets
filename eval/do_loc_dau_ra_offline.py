#!/usr/bin/env python3
"""Đo bộ lọc đầu ra O1-O4 OFFLINE — 0 TPM, tất định, chạy lại bao nhiêu lần cũng ra một kết quả.

VÌ SAO ĐO OFFLINE THAY VÌ CHỜ LƯỢT END-TO-END:
Bộ lọc là một TẤM LƯỚI. Chứng minh lưới hoạt động thì ném thẳng vật đáng bắt
vào lưới, không phải chờ diễn viên nhào lộn ngã đúng chỗ. Lượt end-to-end tốn
TPM và chỉ trả lời câu khác hẳn ("agent CÓ rò không"), không trả lời câu này
("bộ lọc CÓ bắt không, và có bắt nhầm không").

NGUỒN DỮ LIỆU — CỐ Ý ĐỘC LẬP VỚI TÁC GIẢ BỘ LỌC:
Một bộ lọc bắt đúng những chuỗi tác giả nó nghĩ ra sẽ xanh 100% và không chứng
minh được gì về chuỗi tác giả không nghĩ tới. Đó chính là lý do hiến pháp cấm
tester đọc `src/`. Nên corpus ở đây KHÔNG lấy từ scratchpad của coder:

  · CORPUS ÂM TÍNH = câu trả lời THẬT của agent đã lưu trong eval/results/.
    Đầu ra thật của mô hình, không ai curate, sinh ra TRƯỚC khi bộ lọc tồn tại.
    Trong đó nhóm từ 18 ca mốc nền đều ĐẠT ⇒ đều là câu HỢP LỆ ⇒ **không câu
    nào được phép bị chặn**. Đây là mẫu mạnh hơn hẳn vài câu đối chứng chọn
    tay: nó cho ra một CON SỐ ĐO ĐƯỢC chứ không phải một lời hứa.

GHÉP ĐÚNG CẶP reply ↔ lượt khách:
`loc_dau_ra` nhận `tin_nhan_khach` vì O3 ĐÁNG LẼ chỉ bật khi lượt khách có dãy
số + câu hỏi xác nhận. Script này ghép reply[i] với câu khách[i] đúng như lúc
chạy thật, để không làm nhẹ tội bộ lọc.

ĐO ĐƯỢC 15/08: cổng đó KHÔNG GIỮ — O3 chặn y hệt nhau với câu khách bình
thường, câu khách đúng phổ O3, và câu khách RỖNG. Tức O3 quyết định chỉ dựa
trên reply. Giữ việc ghép cặp lại vì nó đúng về nguyên tắc và vì cổng này có
thể được vá.

CHỈ ĐO TRÊN LƯỢT MANG PAYLOAD (từ khi origin-rule land, `nguon` bắt buộc):
`nguon_tu_payload()` ráp `tool_calls_day_du` của case thành chuỗi `nguon`. Đây
là QUY ƯỚC CỦA TÔI, chưa đối chiếu với đường sản xuất thật — nếu lệch, con số
dưới đây không nói thay cho đường chạy thật, phải hỏi coder xác nhận. Lượt nào
KHÔNG mang payload (bản ghi cũ trước 15/08) bị loại khỏi mẫu số, không trộn
vào — nguồn rỗng của chúng sẽ báo chặn nhầm không có thật.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval.measure_quality import dau_thuoc

EVAL_DIR = Path(__file__).resolve().parent
HE_THONG_MOC_NEN = "6c5fff420bb9"


def nguon_tu_payload(tool_calls_day_du: list[dict]) -> str:
    """Ráp payload tool thành chuỗi `nguon` cho `loc_dau_ra`.

    QUY ƯỚC CỦA TÔI, CHƯA ĐỐI CHIẾU VỚI ĐƯỜNG SẢN XUẤT THẬT — mỗi kết quả tool
    tự json.dumps() rồi nối bằng "\n". Coder từng vá một lỗ "dấu phẩy trong
    payload đẻ ra số nguồn không tồn tại" (commit 20b8332, "hai-kênh"); nếu
    đường sản xuất ráp KHÁC quy ước này, con số script trả về không nói thay
    cho đường chạy thật — phải hỏi coder xác nhận trước khi dùng làm căn cứ.

    XẤP XỈ: dùng TOÀN BỘ payload của case cho MỌI lượt trong case đó, vì raw
    chỉ lưu tool_calls_day_du gộp cả hội thoại, không tách theo từng lượt.
    Xấp xỉ này lệch về hướng AN TOÀN cho phép đo (nhiều nguồn hơn ⇒ ít bị
    chặn-nhầm-vì-thiếu-dữ-liệu hơn), không phải hướng nguy hiểm.
    """
    return "\n".join(
        json.dumps(tc["result"], ensure_ascii=False)
        for tc in tool_calls_day_du if tc.get("result")
    )


def nap_luot_that() -> list[dict]:
    """Mọi lượt (reply, câu khách, nguồn, có thuộc mốc nền không) từ bản ghi
    đã lưu."""
    turn: list[dict] = []
    for f in sorted((EVAL_DIR / "results").glob("*_raw.json")):
        try:
            record_row = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for r in record_row:
            replies = r.get("all_agent_replies") or []
            khach = r.get("all_customer_texts") or []
            source = nguon_tu_payload(r.get("tool_calls_day_du") or [])
            # "PHẢI KHÔNG ĐƯỢC CHẶN" = câu đến từ ca ĐẠT trong mốc nền. Ca ĐẠT
            # nghĩa là toàn hội thoại không vi phạm bất biến nào ⇒ mọi câu trong
            # đó đều hợp lệ. Đây là nhóm mà một lần chặn = một lần chặn nhầm,
            # không cần tranh luận thêm.
            phai_khong_chan = (
                r.get("_thuoc", {}).get("he_thong") == HE_THONG_MOC_NEN
                and r.get("trang_thai") == "dat"
            )
            for i, rep in enumerate(replies):
                if not (rep or "").strip():
                    continue
                turn.append({
                    "case_id": r.get("case_id", "?"),
                    "file": f.name,
                    "luot": i + 1,
                    "reply": rep,
                    "khach": khach[i] if i < len(khach) else "",
                    "nguon": source,
                    "co_payload": bool(source),
                    "phai_khong_chan": phai_khong_chan,
                })
    return turn


def main() -> int:
    from src.agents.output_filter import filter_output

    # ĐÓNG DẤU HAI ĐẦU — Luật 4, và bài học đắt nhất ngày 15/08.
    #
    # Tôi dựng cả cơ chế dấu thước cho lượt end-to-end rồi chạy phép đo offline
    # này KHÔNG dấu gì cả. Ba lượt chạy cho 27/96 -> 5/96 -> 0/96; tôi kết luận
    # "phép đo không tái lập, harness hỏng" và RÚT LẠI một finding ĐÚNG. Sự
    # thật: coder đang vá O3/O4 giữa các lượt chạy, ba con số là ba trạng thái
    # code khác nhau — tất cả đều đúng.
    #
    # Một dòng dấu này đã đủ để tôi thấy ngay, thay vì đi dựng một cơ chế
    # "trạng thái tích luỹ" không hề tồn tại rồi tự nhận lỗi mình không mắc.
    # BÀI HỌC: kỷ luật đo phải phủ MỌI phép đo, không chỉ phép đo đắt tiền.
    # Phép đo rẻ là phép đo hay chạy nhất, nên cũng là phép đo hay straddle
    # một thay đổi nhất.
    dau_truoc = dau_thuoc()
    print(f"dấu TRƯỚC: {json.dumps(dau_truoc, ensure_ascii=False)}", file=sys.stderr)

    luot_tho = nap_luot_that()
    if not luot_tho:
        print("Chưa có lượt nào trong eval/results/ — CHƯA ĐO ĐƯỢC.", file=sys.stderr)
        return 2

    # CHỈ ĐO TRÊN LƯỢT THẬT SỰ MANG PAYLOAD.
    #
    # Bản trước của guard này kiểm CHỮ KÝ HÀM (`"nguon" in inspect.signature`)
    # thay vì kiểm DỮ LIỆU THẬT — nên nó báo "CHƯA ĐO ĐƯỢC" một cách VÔ ĐIỀU
    # KIỆN ngay cả sau khi harness đã lưu payload thật (15/08, sau lượt
    # end-to-end 25 ca: 20/25 bản ghi CÓ tool_calls_day_du, nhưng script vẫn
    # từ chối đo vì guard chỉ nhìn signature). Sửa: lọc theo `co_payload` của
    # TỪNG LƯỢT, không suy từ chữ ký hàm.
    turn = [lt for lt in luot_tho if lt["co_payload"]]
    khong_payload = len(luot_tho) - len(turn)
    if not turn:
        print(f"CHƯA ĐO ĐƯỢC: {len(luot_tho)} lượt trong eval/results/ nhưng KHÔNG lượt "
              "nào mang payload\n(tool_calls_day_du). Cần một lượt chạy MỚI sau khi "
              "harness lưu payload — các bản ghi\ncũ hơn 15/08 sẽ mãi mãi không có "
              "trường này.", file=sys.stderr)
        return 2
    if khong_payload:
        print(f"BỎ QUA {khong_payload}/{len(luot_tho)} lượt không mang payload "
              "(bản ghi cũ, trước khi harness lưu tool_calls_day_du) — không trộn "
              "chúng vào mẫu số, vì nguồn rỗng của chúng sẽ báo chặn nhầm không có "
              "thật.", file=sys.stderr)

    chan_all: list[dict] = []
    chan_phai_khong: list[dict] = []
    nhom_dem: Counter[str] = Counter()
    so_phai_khong = 0

    for i, lt in enumerate(turn):
        if lt["phai_khong_chan"]:
            so_phai_khong += 1
        # thread_id RIÊNG mỗi lượt: bộ đếm mật độ O2 gom theo thread, dùng chung
        # một thread sẽ để lượt trước ảnh hưởng lượt sau và ta không còn đo được
        # từng câu một cách độc lập.
        moi, nhom = filter_output(
            lt["reply"], customer_message=lt["khach"], thread_id=f"OFFLINE-{i}",
            source=lt["nguon"],
        )
        if nhom:
            nhom_dem.update(nhom)
        bi_chan = moi != lt["reply"]
        if bi_chan:
            chan_all.append({**lt, "nhom": nhom})
            if lt["phai_khong_chan"]:
                chan_phai_khong.append({**lt, "nhom": nhom})

    print("=" * 72)
    print("ĐO BỘ LỌC ĐẦU RA O1-O4 — OFFLINE, 0 TPM, TẤT ĐỊNH")
    print("=" * 72)
    print(f"\nCorpus ĐO ĐƯỢC: {len(turn)}/{len(luot_tho)} lượt (loại {khong_payload} "
          "lượt không mang payload)")
    print(f"  trong đó {so_phai_khong} lượt PHẢI KHÔNG ĐƯỢC CHẶN "
          f"(từ ca ĐẠT của mốc nền {HE_THONG_MOC_NEN})")

    print(f"\n── AN TOÀN (tỉ lệ chặn nhầm) {'─' * 40}")
    if so_phai_khong:
        ti_le = len(chan_phai_khong) / so_phai_khong * 100
        print(f"  {len(chan_phai_khong)}/{so_phai_khong} câu HỢP LỆ bị chặn = {ti_le:.1f}%")
    else:
        print("  KHÔNG ĐO ĐƯỢC — chưa có lượt nào thuộc ca ĐẠT của mốc nền mang payload.")
    for c in chan_phai_khong[:12]:
        print(f"    ⚠️  {c['case_id']} lượt {c['luot']} · nhóm {c['nhom']}")
        print(f"        {c['reply'][:150]!r}")

    print(f"\n── TỔNG QUAN corpus đo được {'─' * 38}")
    print(f"  {len(chan_all)}/{len(turn)} lượt bị chặn ({len(chan_all)/len(turn)*100:.1f}%)")
    print(f"  Nhóm khớp: {dict(nhom_dem) or 'không nhóm nào'}")

    trailing_marker = dau_thuoc()
    if trailing_marker != dau_truoc:
        print(f"\n🔴 DẤU LỆCH HAI ĐẦU — LƯỢT ĐO VÔ HIỆU\n"
              f"   trước: {dau_truoc}\n   sau:   {trailing_marker}\n"
              f"   Cây làm việc đổi GIỮA lượt đo. Con số trên đo hai vật khác nhau,"
              f" KHÔNG được dùng. Chạy lại khi cây đứng yên.")
        return 3
    print(f"\ndấu khớp hai đầu: he_thong={dau_truoc['he_thong']} commit={dau_truoc['commit']}")

    print("\nLƯU Ý ĐỌC SỐ: đây là tỉ lệ chặn nhầm trên đầu ra THẬT của agent — nó KHÔNG")
    print("nói bộ lọc có bắt được tấn công thật hay không. Hai câu hỏi khác nhau, cần")
    print("hai corpus khác nhau; corpus tấn công phải cũng đến từ nguồn độc lập.")
    print("CỔNG BÙ trục HIỆU QUẢ (bắt tấn công thật): eval/do_corpus_o_group.py")
    print("— [khảo sát QA/QC 25/08] hai cổng đo hai chiều khác nhau của CÙNG bộ lọc")
    print("O1-O4, không cổng nào một mình đủ để nói bộ lọc đang hoạt động đúng.")
    print("\nQUY ƯỚC RÁP `nguon` (json.dumps từng kết quả, nối \\n) CHƯA ĐỐI CHIẾU VỚI")
    print("ĐƯỜNG SẢN XUẤT THẬT — coder cần xác nhận trước khi dùng con số này làm căn cứ.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
