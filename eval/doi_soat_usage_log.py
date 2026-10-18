#!/usr/bin/env python3
"""ĐỐI SOÁT `usage.jsonl` — cổng phát hiện lượt đã tốn tiền mà KHÔNG có bản
ghi (lỗ quan sát), cùng bất biến `so_luot_goi_model = so_tool_call + 1`.

    python eval/doi_soat_usage_log.py --container <tên container backend>

🔴 `--container` BẮT BUỘC, KHÔNG có mặc định — đợt "OTP trước token" đã một
lần cả đội đo nhầm ngăn xếp (`fin05-po-test` build từ scratchpad phiên khác,
không mang mã đợt đang đo). Một cổng có mặc định là một cổng mời người sau
đoán bừa ngăn nào.

## Nguồn gốc — phát hiện 25/08, buổi tốn phí "OTP trước token"

Đối chiếu tay hai nguồn độc lập trong lúc đo mẫu số lưu lượng thật: đếm
thread trong bảng `checkpoints` (LangGraph PostgresSaver, bằng chứng hội
thoại ĐÃ XẢY RA) so với thread trong `usage.jsonl` (bằng chứng TA ĐÃ GHI).
Lệch 41% (7/17 thread) — bắt được CHỈ VÌ tình cờ có cả hai nguồn trong tay
lúc đang đo việc khác. Gốc: backend bị kernel OOM-kill giữa lượt xử lý (máy
chạy quá nhiều ngăn xếp cùng lúc) — lượt đã gọi LLM xong (tốn tiền) nhưng
chưa kịp ghi sổ trước khi tiến trình chết.

**Không có cổng này, một cuốn sổ thiếu 41% trông Y HỆT một cuốn sổ đầy đủ.**
Đây là thước đo ĐỘ TIN của mọi con số token dự án từng công bố — thiếu nó,
mọi báo cáo chi phí là một cận dưới mà không ai biết cận dưới bao nhiêu.

## Hai phép kiểm, ĐỘC LẬP, không gộp

1. **Đối soát nguồn** — `thread` có trong `checkpoints` mà KHÔNG có dòng nào
   trong `usage.jsonl` ⟹ lượt đã tốn tiền, mất bản ghi. In đủ DANH SÁCH
   thread_id, không chỉ đếm.
2. **Bất biến `so_luot_goi_model = so_tool_call + 1`** — CHỈ áp cho dòng có
   `so_luot_goi_model > 0` (dòng model THẬT SỰ chạy; dòng cổng tất định như
   `can_otp`/`thu_slot`/`otp_resend_thu_slot` đúng đắn mang cả hai = 0, KHÔNG
   thuộc phạm vi bất biến này). Vi phạm là cảnh báo sớm cho lớp bug "tool
   call bị đánh rơi ở khâu nối, im lặng".

## Chạy TỪ HOST, qua `docker exec` — không phải trong container

`docker exec … pytest` cho eval/ ra 0 ca chạy vì `.dockerignore` loại thư
mục này khỏi ảnh — hiện ra như "0 failed", một cái còi đã tắt. Script này tự
nó gọi `docker exec` ra ngoài, không cần chạy trong ảnh.
"""
from __future__ import annotations

import argparse
import json
import subprocess

_MA = r'''
import json, os
from sqlalchemy import create_engine, text

eng = create_engine(os.environ["DATABASE_URL"])
with eng.connect() as c:
    rows = c.execute(text("SELECT DISTINCT thread_id FROM checkpoints")).fetchall()
threads_that = {r[0] for r in rows}


def _co_ai_message(thread_id: str) -> str:
    """Phân loại một thread KHÔNG có dòng usage.jsonl — [PO 25/08, đính chính]
    "không có dòng sổ" KHÔNG đồng nghĩa "mất bản ghi": nếu agent CHƯA TỪNG
    trả lời (chỉ có câu khách, chưa tốn tiền) thì việc không có dòng sổ là
    ĐÚNG, không phải lỗ quan sát. Trả 'mat_that' / 'binh_thuong' / 'chua_ro'.
    """
    from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
    with eng.connect() as c:
        row = c.execute(
            text("SELECT blob FROM checkpoint_blobs WHERE thread_id=:t AND channel='messages' "
                 "ORDER BY version DESC LIMIT 1"),
            {"t": thread_id},
        ).fetchone()
    if not row or not row[0]:
        return "chua_ro"
    try:
        obj = JsonPlusSerializer().loads_typed(("msgpack", bytes(row[0])))
        co_ai = any(type(m).__name__ == "AIMessage" for m in obj)
        return "mat_that" if co_ai else "binh_thuong"
    except Exception:
        return "chua_ro"

threads_so = set()
dong_vi_pham_bat_bien = []
tong_dong = 0
try:
    with open("/app/logs/usage.jsonl", encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            tong_dong = lineno
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            threads_so.add(d.get("thread_id"))
            goi_model = d.get("so_luot_goi_model") or 0
            tool_call = d.get("so_tool_call") or 0
            if goi_model > 0 and goi_model != tool_call + 1:
                dong_vi_pham_bat_bien.append(
                    {"dong": lineno, "thread_id": d.get("thread_id"),
                     "so_luot_goi_model": goi_model, "so_tool_call": tool_call}
                )
except FileNotFoundError:
    print(json.dumps({"loi": "khong_thay_usage_jsonl"}))
    raise SystemExit(0)

ung_vien = sorted(threads_that - threads_so)
mat_that, binh_thuong, chua_ro = [], [], []
for t in ung_vien:
    loai = _co_ai_message(t)
    {"mat_that": mat_that, "binh_thuong": binh_thuong, "chua_ro": chua_ro}[loai].append(t)

print(json.dumps({
    "tong_thread_that": len(threads_that),
    "tong_thread_co_log": len(threads_so & threads_that),
    "thread_mat_that": mat_that,
    "thread_binh_thuong_khong_tinh": binh_thuong,
    "thread_chua_ro": chua_ro,
    "tong_dong_usage": tong_dong,
    "vi_pham_bat_bien": dong_vi_pham_bat_bien,
}, ensure_ascii=False))
'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--container", required=True, help="tên container backend (vd fin05-dot-otp-backend-1) — KHÔNG có mặc định, cố ý")
    a = ap.parse_args()

    r = subprocess.run(
        ["docker", "exec", a.container, "python", "-c", _MA],
        capture_output=True, text=True, timeout=60,
    )
    if r.returncode != 0:
        print(f"🔴 Không chạy được trong container {a.container!r}: {(r.stderr or r.stdout)[-1000:]}")
        return 2

    dong_cuoi = [dong for dong in r.stdout.strip().splitlines() if dong.strip()]
    if not dong_cuoi:
        print(f"🔴 Container {a.container!r} không trả về gì — kiểm tên container đúng chưa.")
        return 2
    try:
        outcome = json.loads(dong_cuoi[-1])
    except json.JSONDecodeError:
        print(f"🔴 Không đọc được JSON kết quả:\n{r.stdout}")
        return 2

    if outcome.get("loi") == "khong_thay_usage_jsonl":
        print(f"🔴 Không thấy /app/logs/usage.jsonl trong container {a.container!r}.")
        return 2

    print(f"Container: {a.container}")
    print(f"Thread THẬT (checkpoints): {outcome['tong_thread_that']}")
    print(f"Thread CÓ log (usage.jsonl): {outcome['tong_thread_co_log']}")
    print(f"Tổng dòng usage.jsonl: {outcome['tong_dong_usage']}")

    # [PO 25/08, đính chính] "không có dòng sổ" ≠ "mất bản ghi" — một thread
    # mà agent CHƯA TỪNG trả lời (chỉ có câu khách) đúng đắn không có dòng
    # sổ, đếm nó vào "mất" là báo động giả DO CHÍNH CỔNG SINH RA. Phân loại
    # bằng cách giải mã checkpoint (có AIMessage hay không) trước khi báo.
    mat = outcome["thread_mat_that"]
    binh_thuong = outcome["thread_binh_thuong_khong_tinh"]
    chua_ro = outcome["thread_chua_ro"]
    ok = True
    if mat:
        ok = False
        ti_le = len(mat) / outcome["tong_thread_that"] * 100 if outcome["tong_thread_that"] else 0
        print(f"\n🔴 {len(mat)} LƯỢT ĐÃ TỐN TIỀN MÀ KHÔNG CÓ BẢN GHI ({ti_le:.0f}% tổng thread"
              f" — CHỈ tính thread CÓ AIMessage, đã loại thread agent chưa từng chạy):")
        for t in mat:
            print(f"   {t}")
    else:
        print("\n✅ Không có thread nào MẤT THẬT (có AIMessage mà không có dòng sổ).")
    if binh_thuong:
        print(f"  ({len(binh_thuong)} thread không có dòng sổ NHƯNG agent chưa từng trả lời "
              f"— BÌNH THƯỜNG, không tính là mất: {', '.join(binh_thuong)})")
    if chua_ro:
        print(f"  🟡 {len(chua_ro)} thread CHƯA RÕ (blob rỗng/giải mã lỗi, không gộp vào mất "
              f"lẫn bình thường — cần xem tay): {', '.join(chua_ro)}")

    vp = outcome["vi_pham_bat_bien"]
    if vp:
        ok = False
        print(f"\n🔴 {len(vp)} DÒNG VI PHẠM BẤT BIẾN so_luot_goi_model = so_tool_call + 1:")
        for v in vp:
            print(f"   dòng {v['dong']} ({v['thread_id']}): goi_model={v['so_luot_goi_model']} "
                  f"tool_call={v['so_tool_call']} (mong {v['so_tool_call'] + 1})")
    else:
        print("✅ Bất biến so_luot_goi_model = so_tool_call + 1 khít trên mọi dòng model đã chạy.")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
