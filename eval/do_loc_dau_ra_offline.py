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

  · CORPUS ÂM TÍNH = 957 câu trả lời THẬT của agent đã lưu trong eval/results/.
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


def nap_luot_that() -> list[dict]:
    """Mọi lượt (reply, câu khách, có thuộc mốc nền không) từ bản ghi đã lưu."""
    luot: list[dict] = []
    for f in sorted((EVAL_DIR / "results").glob("*_raw.json")):
        try:
            ban_ghi = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for r in ban_ghi:
            replies = r.get("all_agent_replies") or []
            khach = r.get("all_customer_texts") or []
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
                luot.append({
                    "case_id": r.get("case_id", "?"),
                    "file": f.name,
                    "luot": i + 1,
                    "reply": rep,
                    "khach": khach[i] if i < len(khach) else "",
                    "phai_khong_chan": phai_khong_chan,
                })
    return luot


def main() -> int:
    from src.agents.output_filter import loc_dau_ra

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

    # CHƯA ĐO ĐƯỢC KHI BẢN GHI CHƯA LƯU PAYLOAD TOOL.
    #
    # Bản ghi eval hiện chỉ lưu TÊN tool, không lưu payload — nên không dựng
    # được `nguon` cho từng lượt. Truyền nguồn rỗng thì mọi câu trả lời có số
    # (tức gần như mọi câu tra cứu) đều bị chặn, và báo cáo sẽ nói "chặn nhầm
    # ~100%" — một hồi quy KHÔNG CÓ THẬT, thuần tuý do bộ đo thiếu dữ liệu.
    # Ngày 15/08 tôi đã một lần suýt để một con số kiểu này chôn mất bản vá
    # đúng; lần này bộ đo tự từ chối thay vì để người đọc phải nhận ra.
    import inspect

    from src.agents.output_filter import loc_dau_ra as _ham

    if "nguon" in inspect.signature(_ham).parameters:
        print("CHƯA ĐO ĐƯỢC: origin-rule đã land nên `loc_dau_ra` đòi `nguon`, mà bản "
              "ghi eval\nchỉ lưu TÊN tool chứ không lưu payload. Truyền nguồn rỗng sẽ "
              "báo một hồi quy\nkhông có thật.\n\nMở khoá bằng cách cho harness lưu "
              "payload tool vào raw (PO đã xếp HOÃN,\nkhông chặn land). Tới lúc đó, "
              "cổng chặn-nhầm đo bằng eval/corpus_origin_rule.jsonl.",
              file=sys.stderr)
        return 2

    luot = nap_luot_that()
    if not luot:
        print("Chưa có lượt nào trong eval/results/ — CHƯA ĐO ĐƯỢC.", file=sys.stderr)
        return 2

    chan_all: list[dict] = []
    chan_phai_khong: list[dict] = []
    nhom_dem: Counter[str] = Counter()
    so_phai_khong = 0

    for i, lt in enumerate(luot):
        if lt["phai_khong_chan"]:
            so_phai_khong += 1
        # thread_id RIÊNG mỗi lượt: bộ đếm mật độ O2 gom theo thread, dùng chung
        # một thread sẽ để lượt trước ảnh hưởng lượt sau và ta không còn đo được
        # từng câu một cách độc lập.
        moi, nhom = loc_dau_ra(
            lt["reply"], tin_nhan_khach=lt["khach"], thread_id=f"OFFLINE-{i}", nguon=""
        )
        if nhom:
            nhom_dem.update(nhom)
        # ĐO ĐƯỢC 15/08: 463/463 lần chặn đều là THAY SẠCH câu, 0 lần che một
        # phần. Nên "bị chặn" ở đây = mất trắng câu trả lời, không phải
        # mất một chi tiết — mức nghiêm trọng cao nhất có thể.
        bi_chan = moi != lt["reply"]
        if bi_chan:
            chan_all.append({**lt, "nhom": nhom})
            if lt["phai_khong_chan"]:
                chan_phai_khong.append({**lt, "nhom": nhom})

    print("=" * 72)
    print("ĐO BỘ LỌC ĐẦU RA O1-O4 — OFFLINE, 0 TPM, TẤT ĐỊNH")
    print("=" * 72)
    print(f"\nCorpus: {len(luot)} lượt trả lời THẬT của agent đã lưu")
    print(f"  trong đó {so_phai_khong} lượt PHẢI KHÔNG ĐƯỢC CHẶN "
          f"(từ ca ĐẠT của mốc nền {HE_THONG_MOC_NEN})")

    print(f"\n── AN TOÀN (tỉ lệ chặn nhầm) {'─' * 40}")
    if so_phai_khong:
        ti_le = len(chan_phai_khong) / so_phai_khong * 100
        print(f"  {len(chan_phai_khong)}/{so_phai_khong} câu HỢP LỆ bị chặn = {ti_le:.1f}%")
    else:
        print("  KHÔNG ĐO ĐƯỢC — chưa có lượt nào thuộc ca ĐẠT của mốc nền.")
    for c in chan_phai_khong[:12]:
        print(f"    ⚠️  {c['case_id']} lượt {c['luot']} · nhóm {c['nhom']}")
        print(f"        {c['reply'][:150]!r}")

    print(f"\n── TỔNG QUAN toàn corpus {'─' * 44}")
    print(f"  {len(chan_all)}/{len(luot)} lượt bị chặn ({len(chan_all)/len(luot)*100:.1f}%)")
    print(f"  Nhóm khớp: {dict(nhom_dem) or 'không nhóm nào'}")

    dau_sau = dau_thuoc()
    if dau_sau != dau_truoc:
        print(f"\n🔴 DẤU LỆCH HAI ĐẦU — LƯỢT ĐO VÔ HIỆU\n"
              f"   trước: {dau_truoc}\n   sau:   {dau_sau}\n"
              f"   Cây làm việc đổi GIỮA lượt đo. Con số trên đo hai vật khác nhau,"
              f" KHÔNG được dùng. Chạy lại khi cây đứng yên.")
        return 3
    print(f"\ndấu khớp hai đầu: he_thong={dau_truoc['he_thong']} commit={dau_truoc['commit']}")

    print("\nLƯU Ý ĐỌC SỐ: đây là tỉ lệ chặn nhầm trên đầu ra THẬT của agent — nó KHÔNG")
    print("nói bộ lọc có bắt được tấn công thật hay không. Hai câu hỏi khác nhau, cần")
    print("hai corpus khác nhau; corpus tấn công phải cũng đến từ nguồn độc lập.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
