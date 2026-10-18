#!/usr/bin/env python3
"""Bản đồ PHỦ của kho RAG — tài liệu nguồn có bao nhiêu phần thật sự vào được kho.

    python eval/do_phu_kho.py                 # cả hai tài liệu
    python eval/do_phu_kho.py --tai-lieu ToS  # một tài liệu

## Câu hỏi nó trả lời, và câu hỏi nó KHÔNG trả lời

TRẢ LỜI: *"đoạn X của tài liệu nguồn có nằm trong kho không"* — tức phần NẠP.
KHÔNG TRẢ LỜI: *"truy hồi có lấy được nó ra khi khách hỏi không"* — phần TRUY
HỒI, đó là việc của `benchmark.py`.

Phân biệt này là toàn bộ lý do file này tồn tại. Ngày 16/08 bộ ca ToS đạt 2/8
và có hai cách đọc hoàn toàn khác nhau:

    "ToS chưa vào kho đủ"    -> lỗi NẠP,      chữa bằng parser/chunker, rẻ
    "ToS vào đủ mà không ra" -> lỗi TRUY HỒI, chữa bằng cơ chế tìm, đắt

Đoán sai hướng thì mất một vòng. Đo ra **96,1% ToS có trong kho, mục 19 phủ
11/11** trong khi đúng các câu hỏi mục 19 lại trượt ⟹ lỗi TRUY HỒI, không phải
lỗi nạp. Một phép đo 2 phút, 0 lượt LLM, chặn được một đòn đi sai hướng.

## Vì sao KHÔNG chỉ tra trong tập chunk đã khảo sát

Bản đầu của phép đo này chỉ tra trong tập chunk gom được từ một đợt quét
(340/378). Kết quả: mục 15 "không thấy" ⟹ tôi **báo nhầm là kho thiếu**. Sự
thật là khảo sát thiếu, không phải kho thiếu.

⟹ Đoạn nào không thấy trong tập đã gom thì **HỎI THẲNG kho bằng chính đoạn
đó** trước khi kết luận vắng. "Không tìm thấy bằng cách A" không phải "không
tồn tại" — bốn lần trong một ngày, cùng một họ lỗi.

## Vì sao lát cắt nằm ở 1/4 đoạn, không phải đầu đoạn

Đầu đoạn hay bị bộ chia dùng làm ranh giới chunk, nên một lát lấy từ đầu đoạn
dễ bị cắt đôi và báo "vắng" oan. Lấy ở 1/4 thì nằm gọn trong thân.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import unicodedata
import warnings
import zipfile
from xml.etree import ElementTree as ET

warnings.filterwarnings("ignore")

GOC = pathlib.Path(__file__).resolve().parent.parent
RA = GOC / "eval" / "phu_kho.json"
BASE = "https://localhost"
NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
TAI_LIEU = {
    "FAQ": GOC / "data" / "raw" / "MoMo_FAQ_Giao_dich.docx",
    "ToS": GOC / "data" / "raw" / "MoMo_ToS.docx",
}
NGAN_NHAT = 40  # đoạn ngắn hơn thế là gạch đầu dòng/tiêu đề, không đủ đặc trưng để tra

# Đoạn KHÔNG được tính vào mẫu số: đòn 3 CỐ Ý loại chúng khỏi kho.
# Tính vào thì phủ FAQ ra 81,0% — nghe như mất 19% nội dung, trong khi 153 trong
# 287 đoạn "vắng" là thứ ta chủ động vứt. Mẫu số sạch: 90,1%.
# Một mẫu số bẩn không sai ở phép chia; nó sai ở chỗ trả lời một câu hỏi khác
# với câu ta đang hỏi.
MUC_LUC = re.compile(r"^\d{1,3}\.\s.*\d{1,3}\s*$")   # dòng mục lục: kết bằng SỐ TRANG
RAC_URL = re.compile(r"https?://|cdn-cgi|email-protection")


def dang_bi_loai_co_y(p: str) -> bool:
    t = re.sub(r"\s+", " ", p).strip()
    return bool(MUC_LUC.match(t) or RAC_URL.search(t))


def strip_diacritics(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s.replace("đ", "d").replace("Đ", "D").lower())


def doan_cua(f: pathlib.Path) -> list[str]:
    x = ET.fromstring(zipfile.ZipFile(f).read("word/document.xml"))
    return [
        t
        for t in (
            "".join(n.text or "" for n in p.iter(NS + "t")).strip() for p in x.iter(NS + "p")
        )
        if t
    ]


def lat_dac_trung(p: str) -> str:
    t = re.sub(r"\s+", " ", p).strip()
    return t[len(t) // 4 : len(t) // 4 + 55] if len(t) >= 80 else t


def do_mot(ten: str, f: pathlib.Path, c) -> dict:
    paras = doan_cua(f)
    # gom sẵn một tập chunk để đỡ phải hỏi từng đoạn: quét bằng chính các đoạn dài
    goi = [re.sub(r"\s+", " ", p)[:300] for p in paras if len(re.sub(r"\s+", "", p)) >= 120]
    da_gom: set[str] = set()
    for i, q in enumerate(goi[::3]):  # 1/3 là đủ để phủ rộng, phần còn lại hỏi lẻ
        r = c.post(f"{BASE}/api/policy-search", json={"query": q})
        if r.status_code == 200:
            da_gom.update(y.get("text", "") for y in (r.json().get("results") or []))
        if i % 40 == 0:
            print(f"   …gom {i}/{len(goi[::3])} · {len(da_gom)} chunk", flush=True)
    gom = strip_diacritics(" ||| ".join(da_gom))

    muc, hien, hoi_le = "0", {}, 0
    for i, p in enumerate(paras):
        m = re.match(r"^(\d{1,3})\.\s+\D", p)
        if m and len(p) < 90:
            muc = m.group(1)
        if len(re.sub(r"\s+", "", p)) < NGAN_NHAT or dang_bi_loai_co_y(p):
            continue
        lat = lat_dac_trung(p)
        co = strip_diacritics(lat) in gom
        if not co:  # CHƯA THẤY != VẮNG — hỏi thẳng kho bằng chính đoạn đó
            hoi_le += 1
            r = c.post(f"{BASE}/api/policy-search", json={"query": re.sub(r"\s+", " ", p)[:300]})
            if r.status_code == 200:
                doan = " ".join(y.get("text", "") for y in (r.json().get("results") or []))
                co = strip_diacritics(lat) in strip_diacritics(doan)
        o = hien.setdefault(muc, {"co": 0, "tong": 0, "thieu": []})
        o["co"] += co
        o["tong"] += 1
        if not co:
            o["thieu"].append(i)
    tc = sum(o["co"] for o in hien.values())
    tt = sum(o["tong"] for o in hien.values())
    print(f"   {ten}: {tc}/{tt} = {tc / tt * 100:.1f}%  (hỏi lẻ {hoi_le} lượt)")
    return {"theo_muc": hien, "co": tc, "tong": tt, "so_doan_nguon": len(paras)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tai-lieu", choices=[*TAI_LIEU, "tat-ca"], default="tat-ca")
    a = ap.parse_args()

    import httpx

    c = httpx.Client(verify=False, timeout=60)
    c.post(f"{BASE}/api/session", json={"phone": "0353000201", "password": "Demo@123"}).raise_for_status()
    if not (c.post(f"{BASE}/api/policy-search", json={"query": "hạn mức"}).json().get("results")):
        raise SystemExit("🔴 kho KHÔNG trả lời được (canary rỗng) — DỪNG, xem benchmark.py::canary_kho")

    ket = {}
    for ten, f in TAI_LIEU.items():
        if a.tai_lieu in (ten, "tat-ca"):
            print(f"── {ten} ──")
            ket[ten] = do_mot(ten, f, c)
    c.close()

    ket["_nhan"] = {
        "bam_ket_qua": hashlib.sha256(
            json.dumps(ket, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()[:12]
    }
    RA.write_text(json.dumps(ket, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n→ {RA.relative_to(GOC)} · băm kết quả {ket['_nhan']['bam_ket_qua']}")
    for ten in (t for t in TAI_LIEU if t in ket):
        o = ket[ten]
        xau = {k: v for k, v in o["theo_muc"].items() if v["co"] < v["tong"]}
        print(f"  {ten}: {o['co']}/{o['tong']} = {o['co'] / o['tong'] * 100:.1f}%"
              f" · mục chưa đủ: {sorted(xau, key=lambda s: int(s)) or 'không có'}")


if __name__ == "__main__":
    main()
