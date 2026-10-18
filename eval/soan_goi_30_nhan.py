#!/usr/bin/env python3
"""Soạn gói 30 nhãn cho người chấm — từ KẾT QUẢ ĐÃ CHẠY, không gọi model.

    python eval/soan_goi_30_nhan.py eval/results/llm_judge_run_*_raw.json
    python eval/soan_goi_30_nhan.py <file…> --ca-bien UXQA-003,UXQA-007

Thiết kế đầy đủ + lý do từng quyết định: `eval/GOI-30-NHAN-thiet-ke.md`.

## Vì sao script này KHÔNG sinh hội thoại mới

Nó **tái dùng** kết quả các lượt eval đã chạy. Hai lý do:

1. **Rẻ hơn** — không tốn thêm lượt model nào.
2. **Đúng hơn.** Ta muốn hiệu chuẩn trọng tài trên **chính những lượt đã tạo ra
   các con số đang công bố**, không phải trên một tập mới sinh riêng để chấm.
   Sinh riêng thì ta đo trọng tài trên một phân bố khác với phân bố nó thật sự
   làm việc — và kết quả hiệu chuẩn sẽ không áp được sang các số kia.

## Hai file ra, và vì sao phải là HAI

    goi_30_nhan_NGUOI.md    → gửi người chấm. CHỈ hội thoại + ô trống.
    goi_30_nhan_MAY.json    → phán quyết máy. KHÔNG mở trước khi nhận nhãn về.

Người chấm thấy phán quyết máy trước thì mọi nhãn bị **neo**, đồng thuận cao
**giả**, và ta kết luận "trọng tài đáng tin" từ một phép đo đã bị chính nó
nhiễm. Script **tự kiểm rò rỉ** trước khi ghi (xem `_kiem_ro_ri`) — không dựa
vào việc người soạn nhớ kiểm.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import pathlib
import random
import subprocess
import sys

GOC = pathlib.Path(__file__).resolve().parent.parent
RA_NGUOI = GOC / "eval" / "goi_30_nhan_NGUOI.md"
RA_MAY = GOC / "eval" / "goi_30_nhan_MAY.json"
MOI_TANG = 10

# Chuỗi KHÔNG được xuất hiện trong file người chấm. Danh sách này là cổng chống
# rò rỉ; thêm trường mới vào bản ghi thì thêm khoá vào đây.
CAM_TRONG_FILE_NGUOI = ("passed", "verdict", "judge", "reason", "checks_failed",
                        "severity", "ĐẠT theo máy", "điểm máy",
                        # Metadata transcript của TẦNG C — mang dấu vết PHÂN TÍCH
                        # của tester (ca này thuộc mẫu hỏng nào, gọi mấy tool,
                        # vì sao fallback). Người chấm thấy "F-31 từ chối sai
                        # phạm vi" thì họ không còn chấm mù nữa — họ chấm theo
                        # kết luận của tôi.
                        "mau_hong", "so_tool", "ma_http", "ly_do_fallback",
                        "F-31", "F-32", "F-33", "diễn giải", "từ chối SAI")


def _chay(cmd: list[str]) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=25).stdout.strip()
    except Exception:  # noqa: BLE001
        return "?"


def doc_ban_ghi(duong_dan: list[str]) -> list[dict]:
    """Chuẩn hoá bản ghi từ nhiều dạng file kết quả về một hình dạng."""
    ra = []
    for p in duong_dan:
        d = json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
        if not isinstance(d, list):
            continue
        for x in d:
            hoi = x.get("all_customer_texts") or []
            dap = x.get("all_agent_replies") or ([x["reply"]] if x.get("reply") else [])
            if not dap:
                continue
            # Phán quyết máy: ưu tiên `passed` của TRỌNG TÀI. Nếu file không có
            # (bộ chạy tất định), dùng checks_failed — nhưng ghi rõ NGUỒN, vì
            # hiệu chuẩn trọng tài mà lấy phán quyết của bộ tất định là đo nhầm
            # vật.
            if "passed" in x:
                pq, nguon_pq = str(x["passed"]).lower() in ("true", "1", "dat"), "trong_tai"
            elif "checks_failed" in x:
                pq, nguon_pq = not x.get("checks_failed"), "bo_tat_dinh"
            else:
                continue
            ra.append({
                "id": x.get("case_id") or x.get("source_qa_id") or f"?{len(ra)}",
                "nguon_file": pathlib.Path(p).name,
                "hoi": hoi, "dap": dap,
                "phan_quyet_may": pq, "nguon_phan_quyet": nguon_pq,
                "ly_do_may": x.get("reason", ""),
            })
    return ra


def phan_tang(bg: list[dict], ca_bien: set[str], rnd: random.Random) -> dict[str, list[dict]]:
    """10/10/10 — KHÔNG lấy ngẫu nhiên 30 ca từ toàn bộ.

    Tập mà máy chấm ĐẠT ~90% thì 30 ca ngẫu nhiên ra ~27 ca dễ; đồng thuận sẽ
    cao và con số cao đó chủ yếu nói rằng ca dễ thì ai chấm cũng như nhau.
    Tầng A soi RỘNG TAY, tầng B soi CHẶT TAY — Luật 9 áp cho trọng tài.
    """
    bien = [x for x in bg if x["id"] in ca_bien]
    con_lai = [x for x in bg if x["id"] not in ca_bien]
    dat = [x for x in con_lai if x["phan_quyet_may"]]
    truot = [x for x in con_lai if not x["phan_quyet_may"]]
    rnd.shuffle(dat)
    rnd.shuffle(truot)
    return {"A_may_dat": dat[:MOI_TANG], "B_may_truot": truot[:MOI_TANG],
            "C_bien": bien[:MOI_TANG]}


def _kiem_ro_ri(content_text: str, chon: list[dict]) -> None:
    """Cổng chống rò rỉ — chạy TRƯỚC khi ghi, không dựa vào trí nhớ người soạn."""
    xau = [t for t in CAM_TRONG_FILE_NGUOI if t.lower() in content_text.lower()]
    if xau:
        sys.exit(f"🔴 FILE NGƯỜI CHẤM RÒ PHÁN QUYẾT MÁY: {xau} — DỪNG, không ghi.")
    for x in chon:
        if x["ly_do_may"] and x["ly_do_may"][:40].lower() in content_text.lower():
            sys.exit(f"🔴 RÒ lý do máy của ca {x['id']} — DỪNG, không ghi.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="+", help="file *_raw.json trong eval/results/")
    ap.add_argument("--ca-bien", default="",
                    help="id các ca BIÊN, phẩy ngăn cách (bốn mẫu hỏng — xem thiết kế §4)")
    ap.add_argument("--seed", type=int, default=226)
    a = ap.parse_args()

    duong_dan = [p for m in a.file for p in sorted(glob.glob(m))]
    bg = doc_ban_ghi(duong_dan)
    if not bg:
        sys.exit("🔴 không đọc được bản ghi nào — kiểm lại đường dẫn")

    tu_trong_tai = sum(1 for x in bg if x["nguon_phan_quyet"] == "trong_tai")
    print(f"  đọc {len(bg)} bản ghi từ {len(duong_dan)} file")
    print(f"  phán quyết TRỌNG TÀI: {tu_trong_tai} · bộ tất định: {len(bg) - tu_trong_tai}")
    if tu_trong_tai < 3 * MOI_TANG:
        print(f"  ⚠️  CHỈ {tu_trong_tai} ca có phán quyết TRỌNG TÀI, cần ≥{3 * MOI_TANG}.")
        print("      Hiệu chuẩn trọng tài mà lấy phán quyết của bộ TẤT ĐỊNH là đo nhầm vật.")
        print("      Chạy run_llm_judge_set trên bộ lớn hơn trước khi soạn gói này.")

    rnd = random.Random(a.seed)
    bump = phan_tang(bg, {s.strip() for s in a.ca_bien.split(",") if s.strip()}, rnd)
    for ten, ds in bump.items():
        print(f"  {ten:<14} {len(ds)}/{MOI_TANG} ca" + ("" if len(ds) == MOI_TANG else "   ⚠️ THIẾU"))

    chon = [x for ds in bump.values() for x in ds]
    rnd.shuffle(chon)  # xáo: gom theo tầng là một dạng rò rỉ (người chấm nhận ra khúc toàn ca xấu)

    dong = [
        "# Gói 30 nhãn — bản NGƯỜI CHẤM",
        "",
        "> Chấm **mù**: file này KHÔNG chứa phán quyết của máy, và thứ tự đã xáo.",
        "> Xin đừng tra kết quả máy trước khi chấm xong — thấy trước là mọi nhãn bị neo.",
        "",
        "Mỗi ca điền **ba ô**. `KHÔNG CHẮC` là lựa chọn hợp lệ, không phải né tránh —",
        "ép nhị phân một ca thật sự mơ hồ sẽ biến nó thành một nhãn tuỳ hứng.",
        "",
        "```",
        "ket_luan      : DAT | TRUOT | KHONG_CHAC",
        "ly_do         : một câu (bắt buộc khi TRUOT hoặc KHONG_CHAC)",
        "co_bia_khong  : co | khong      ← hỏi RIÊNG: câu trả lời có thể HỮU ÍCH mà vẫn BỊA",
        "```",
        "",
        "---",
        "",
    ]
    for i, x in enumerate(chon, 1):
        dong.append(f"## Ca {i:02d}  `{x['id']}`\n")
        for j, h in enumerate(x["hoi"]):
            dong.append(f"**Khách:** {h}\n")
            if j < len(x["dap"]):
                dong.append(f"**Agent:** {x['dap'][j]}\n")
        for k in range(len(x["hoi"]), len(x["dap"])):
            dong.append(f"**Agent:** {x['dap'][k]}\n")
        dong += ["```", "ket_luan      : ", "ly_do         : ", "co_bia_khong  : ", "```", "", "---", ""]
    content_text = "\n".join(dong)

    _kiem_ro_ri(content_text, chon)

    h = hashlib.sha256()
    for p in sorted((GOC / "src").rglob("*.py")):
        h.update(p.read_bytes())
    RA_NGUOI.write_text(content_text, encoding="utf-8")
    RA_MAY.write_text(json.dumps({
        "nhan_vat": {
            "he_thong": h.hexdigest()[:12],
            "commit": _chay(["git", "-C", str(GOC), "rev-parse", "--short", "HEAD"]),
            "nguon_file": [pathlib.Path(p).name for p in duong_dan],
            "seed": a.seed,
        },
        "phan_quyet": [{"stt": i, "id": x["id"], "may_dat": x["phan_quyet_may"],
                        "nguon": x["nguon_phan_quyet"], "ly_do": x["ly_do_may"]}
                       for i, x in enumerate(chon, 1)],
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n  ✅ không rò rỉ ({len(CAM_TRONG_FILE_NGUOI)} chuỗi cấm đã kiểm)")
    print(f"  → {RA_NGUOI.relative_to(GOC)}   ← GỬI người chấm")
    print(f"  → {RA_MAY.relative_to(GOC)}   ← GIỮ, không mở trước khi nhận nhãn về")
    print(f"\n  {len(chon)} ca. Đọc kết quả bằng Cohen's kappa + hai chiều sai TÁCH RIÊNG,")
    print("  KHÔNG bằng tỉ lệ trùng thô — xem eval/GOI-30-NHAN-thiet-ke.md §6.")


if __name__ == "__main__":
    main()
