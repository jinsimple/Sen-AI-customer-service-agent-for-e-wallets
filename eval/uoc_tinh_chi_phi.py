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

⚠️ `input_chars` **đã land trong code** (coder, `9d5988c`) nhưng **chưa có
trong bản ghi kết quả nào** — mọi file trong `eval/results/` đều chạy trước đó.
Nên cột thứ hai vẫn in `KHÔNG ĐO ĐƯỢC` cho tới khi có lượt chạy MỚI, và nó
**không** lặng lẽ rơi về token: rơi về token là quay lại đúng cái bẫy công cụ
này sinh ra để tránh.

"Trường đã tồn tại" và "dữ liệu đã có trường đó" là **hai câu hỏi khác nhau** —
cùng họ với `_song()` ≠ `_api_song()`. Script kiểm câu thứ hai, không phải câu
thứ nhất.

## Tỉ lệ KÝ TỰ/TOKEN — phép đo rẻ nhất trả lời một câu đang tin bằng lời

Đo được trên gpt-4o-mini: **2,43 ký tự/token** (13.116 token / 31.937 ký tự).
Nếu Qwen tokenize tiếng Việt gọn hơn thì tỉ lệ này **cao hơn**, và hệ quả kép:
rẻ hơn cho cùng một câu, **và** nhét được nhiều ngữ cảnh hơn trong cùng trần
TPM. Đây là cách **đo** mệnh đề "Qwen hỗ trợ tiếng Việt tốt hơn" thay vì tin
truyền miệng — chỉ cần vài lượt trên **cùng một câu hỏi** ở hai nhà cung cấp.

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


def loi_goi_moi_luot(mau: list[str]) -> tuple[float, int, str]:
    """Đo SỐ LỜI GỌI MODEL trên một lượt chat — từ dữ liệu, không lấy ước chừng.

    Một *lượt chat* của khách KHÔNG phải một lời gọi API: vòng ReAct gọi model
    một lần để quyết định mỗi bước, cộng một lần để viết câu trả lời. Trần
    **RPM** áp trên lời gọi, không trên lượt — nên trần lượt/phút thật có thể
    thấp hơn nhiều so với tính theo TPM.

    ⚠️ Đây là **ƯỚC LƯỢNG CẬN DƯỚI** dùng `tool_calls + 1` làm đại diện. Trường
    thật `so_luot_goi_model` đã có trong `src/agents/graph.py` nhưng **chưa xuất
    hiện trong bản ghi kết quả nào** (đã kiểm: 0/1327). Khi nó có mặt, hàm này
    tự chuyển sang dùng số thật — một lượt có lời gọi không sinh tool call, hoặc
    có retry, sẽ cao hơn ước lượng này.
    """
    that, uoc = [], []
    # (giữ nguyên phần thu thập; hàm trả THÊM p95 ở bản dưới)
    for m in mau:
        for p_ in sorted(glob.glob(m)):
            try:
                d = json.loads(pathlib.Path(p_).read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                continue
            for x in (d if isinstance(d, list) else []):
                u = x.get("usage") or {}
                if isinstance(u, dict) and u.get("so_luot_goi_model"):
                    that.append(u["so_luot_goi_model"])
                elif x.get("tool_calls") is not None:
                    uoc.append(len(x["tool_calls"]) + 1)
    ds, nhan = (that, "ĐO THẬT (so_luot_goi_model)") if that else (
        (uoc, "ước lượng cận dưới (tool_calls + 1)") if uoc else ([1.0], "KHÔNG ĐO ĐƯỢC"))
    ds = sorted(ds)
    return statistics.mean(ds), ds[int(len(ds) * 0.95)], len(ds), nhan


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
    lg_tb, lg_p95, n_lg, nhan_lg = loi_goi_moi_luot(a.nguon)
    vao_p95 = sorted(vao)[int(len(vao) * 0.95)]
    print(f"\n  lời gọi model mỗi lượt: trung bình {lg_tb:.2f} · p95 {lg_p95}"
          f"   ({nhan_lg}, n={n_lg})")
    print(f"  input token mỗi lượt  : trung vị {mau['input_tokens']:,.0f} · p95 {vao_p95:,.0f}")
    print("\n  DUNG LƯỢNG PHẢI ĐỌC Ở ĐUÔI, không ở trung vị: 100 người gõ cùng lúc thì"
          "\n  lượt điều tra nhiều bước mới là thứ làm sập, không phải lượt trung bình.")

    for ten_cot, ltoken, lgoi in (("TRUNG VỊ", mau["input_tokens"], lg_tb),
                                  ("PHÂN VỊ 95", vao_p95, lg_p95)):
        print(f"\n  ── {ten_cot} ──")
        print(f"  {'model':<20}{'lượt/phút':>11}{'theo TPM':>11}{'theo RPM':>11}   CHẶN bởi")
        for ten, g in bg["gia"].items():
            hm = g.get("han_muc") or {}
            t_tpm = hm["tpm"] / ltoken if hm.get("tpm") else None
            t_rpm = hm["rpm"] / lgoi if hm.get("rpm") else None
            co = [v for v in (t_tpm, t_rpm) if v is not None]
            tran = min(co) if co else None
            chan = ("—" if tran is None else
                    ("TPM" if t_rpm is None or (t_tpm is not None and t_tpm <= t_rpm) else "RPM"))
            f = lambda v: "  CHƯA TRA" if v is None else f"{v:>11.1f}"  # noqa: E731
            print(f"  {ten:<20}{('  —' if tran is None else f'{tran:>11.1f}')}"
                  f"{f(t_tpm)}{f(t_rpm)}   {chan}")
    print("\n  Trần công bố = CÁI NHỎ HƠN trong hai cột. Trần áp ở CẤP TÀI KHOẢN GỐC —"
          "\n  mọi key cộng chung, không né được bằng cách tạo thêm key.")

    print("\n  (nhân trung vị × số lượt — KHÔNG phải hoá đơn. Lượt dài hơn trung vị"
          "\n   sẽ đắt hơn; hội thoại nhiều lượt phình theo lịch sử, xem"
          "\n   eval/do_token_latency.py chế độ `don`.)")


if __name__ == "__main__":
    main()
