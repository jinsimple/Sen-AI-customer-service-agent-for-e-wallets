#!/usr/bin/env python3
"""Ước tính CHI PHÍ theo TIỀN — từ số token đã đo, không đoán.

    python eval/uoc_tinh_chi_phi.py                       # dùng số đo mới nhất
    python eval/uoc_tinh_chi_phi.py --nguon eval/results/*_raw.json

## Vì sao tiền chứ không phải token

Token của hai nhà cung cấp **không cùng đơn vị** — tokenizer khác nhau, và
tiếng Việt là chỗ chúng lệch nhau nhiều nhất. `15.400 token` của model A và
`15.400 token` của model B **không phải cùng một lượng văn bản**. So token giữa
hai model là so hai thứ khác nhau bằng một con số trông giống nhau.

Tiền thì cùng đơn vị. Nhưng tiền/lượt vẫn còn một cái bẫy (xem dưới).

## Cái bẫy còn lại: `$/lượt` KHÔNG phải `$/cùng một lượng việc`

Nếu model A tokenize tiếng Việt tệ hơn (nhiều token hơn cho cùng câu), nó sẽ
đắt hơn ở `$/lượt` **dù giá trên token rẻ hơn**. Muốn so công bằng phải chia
cho một đại lượng **bất biến qua tokenizer**: số **KÝ TỰ** vào.

    $/lượt           trả lời "chạy bộ đo này tốn bao nhiêu"      ← luôn tính được
    $/1000 ký tự vào trả lời "model nào rẻ hơn cho CÙNG việc"    ← cần `input_chars`

⚠️ **`input_chars` CHƯA có trong `usage`** (đã kiểm 17/08: envelope chỉ có
`input_tokens · output_tokens · total_tokens · cached_input_tokens`). Coder
đang thêm. Tới lúc đó, trục thứ hai in `KHÔNG ĐO ĐƯỢC` — **không** lặng lẽ rơi
về token, vì rơi về token là quay lại đúng cái bẫy công cụ này sinh ra để tránh.

## Bảng giá là DỮ LIỆU, và là một loại NHÃN VẬT

`eval/gia_tien.json`, không hardcode. Giá đổi theo tháng; một bảng giá cũ làm
mọi con số tiền sai **mà không ai biết** — nên nó mang `ngay_tra` + `nguon`, và
script **cảnh báo khi quá hạn**. Cùng lý do mỗi lượt chấm phải in `he_thong`:
số không có nhãn thì không biết nó nói về cái gì.
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import pathlib
import statistics

GOC = pathlib.Path(__file__).resolve().parent.parent
BANG_GIA = GOC / "eval" / "gia_tien.json"
DO_TOKEN = GOC / "eval" / "do_token_latency.json"


def doc_bang_gia() -> dict:
    d = json.loads(BANG_GIA.read_text(encoding="utf-8"))
    han = int(d.get("_canh_bao_sau_ngay", 30))
    hom_nay = dt.date.today()
    cu = []
    for ten, g in d["gia"].items():
        tuoi = (hom_nay - dt.date.fromisoformat(g["ngay_tra"])).days
        if tuoi > han:
            cu.append(f"{ten} ({tuoi} ngày)")
    if cu:
        print(f"  ⚠️  BẢNG GIÁ QUÁ {han} NGÀY: {', '.join(cu)}")
        print("      Giá cũ ⟹ mọi con số dưới đây sai mà không có triệu chứng nào."
              " Tra lại trước khi dùng để quyết định.")
    return d


def gom_usage(mau: list[str]) -> list[dict]:
    """Gom mọi bản ghi có `usage` từ các file kết quả đã chạy."""
    ra = []
    for m in mau:
        for p in sorted(glob.glob(m)):
            try:
                d = json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                continue
            muc = d if isinstance(d, list) else d.get("ket", [])
            for x in muc:
                for u in ([x["usage"]] if isinstance(x.get("usage"), dict)
                          else [l.get("usage") for l in (x.get("luot") or [])
                                if isinstance(l, dict)]):
                    if isinstance(u, dict) and u.get("input_tokens"):
                        ra.append(u)
                # bộ đo token của tôi lưu phẳng, không lồng trong `usage`
                for l in (x.get("luot") or []):
                    if isinstance(l, dict) and l.get("vao"):
                        ra.append({"input_tokens": l["vao"], "output_tokens": l.get("ra") or 0,
                                   "cached_input_tokens": l.get("cache") or 0,
                                   "input_chars": l.get("ky_tu_vao")})
    return ra


def tien_mot_luot(u: dict, g: dict) -> float:
    vao = u.get("input_tokens") or 0
    cached = u.get("cached_input_tokens") or 0
    ra = u.get("output_tokens") or 0
    # Phần cached tính giá riêng NẾU nhà cung cấp công bố; không công bố thì
    # tính giá thường — KHÔNG giả định là rẻ hơn. Giả định có lợi cho một bên
    # trong bảng so sánh là cách nhanh nhất để bảng so sánh vô dụng.
    gia_cached = g.get("vao_cached")
    if gia_cached is None:
        return (vao * g["vao"] + ra * g["ra"]) / 1e6
    return ((vao - cached) * g["vao"] + cached * gia_cached + ra * g["ra"]) / 1e6


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nguon", nargs="*", default=[str(DO_TOKEN)])
    a = ap.parse_args()

    bg = doc_bang_gia()
    us = gom_usage(a.nguon)
    if not us:
        raise SystemExit("🔴 không tìm thấy bản ghi `usage` nào — kiểm lại --nguon")

    vao = [u["input_tokens"] for u in us]
    ra = [u.get("output_tokens") or 0 for u in us]
    co_chars = [u.get("input_chars") for u in us if u.get("input_chars")]

    print("=" * 74)
    print("ƯỚC TÍNH CHI PHÍ — từ số ĐÃ ĐO")
    print("=" * 74)
    print(f"  {len(us)} lượt đo · input trung vị {statistics.median(vao):,.0f} token"
          f" · output trung vị {statistics.median(ra):,.0f}")
    print(f"  nguồn: {', '.join(pathlib.Path(p).name for m in a.nguon for p in sorted(glob.glob(m)))[:90]}")

    mau = {"input_tokens": statistics.median(vao),
           "output_tokens": statistics.median(ra),
           "cached_input_tokens": statistics.median([u.get("cached_input_tokens") or 0 for u in us])}

    print(f"\n{'model':<16}{'$/lượt':>10}{'$/1000 ký tự vào':>20}   ghi chú")
    print("-" * 74)
    for ten, g in bg["gia"].items():
        t = tien_mot_luot(mau, g)
        if co_chars:
            kt = statistics.median(co_chars)
            cot2 = f"{t / kt * 1000:>19.5f}"
        else:
            cot2 = f"{'KHÔNG ĐO ĐƯỢC':>19}"
        note = "" if g.get("vao_cached") is not None else "chưa công bố giá cached"
        print(f"{ten:<16}{t:>10.5f}{cot2}   {note}")

    if not co_chars:
        print("\n  ⚠️  `input_chars` CHƯA có trong `usage` — cột thứ hai KHÔNG tính được.")
        print("      Đây là cột DUY NHẤT so được hai model trên CÙNG một lượng văn bản;")
        print("      cột `$/lượt` bên trái thiên vị model nào tokenize tiếng Việt gọn hơn.")
        print("      Đừng đọc bảng trên thành 'model nào rẻ hơn' — nó mới trả lời")
        print("      'chạy bộ đo này trên model nào tốn bao nhiêu'.")

    print(f"\n{'bộ đo':<24}{'lượt':>6}" + "".join(f"{t:>13}" for t in bg["gia"]))
    print("-" * 74)
    for ten, b in bg["bo_do"].items():
        d = "".join(f"{tien_mot_luot(mau, g) * b['so_luot']:>13.3f}" for g in bg["gia"].values())
        print(f"{ten:<24}{b['so_luot']:>6}{d}")
    print("\n  (nhân trung vị × số lượt — KHÔNG phải hoá đơn. Lượt dài hơn trung vị"
          "\n   sẽ đắt hơn; hội thoại nhiều lượt phình theo lịch sử, xem"
          "\n   eval/do_token_latency.py chế độ `don`.)")


if __name__ == "__main__":
    main()
