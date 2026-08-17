#!/usr/bin/env python3
"""Soi HẠNG của mọi đoạn trong kho cho một truy vấn — CHỈ TRẢ HẠNG, KHÔNG CHẤM.

    python scripts/soi_hang.py --truy-van cauhoi.txt --k 100
    cat cauhoi.txt | python scripts/soi_hang.py --truy-van - --k 100 --ra hang.jsonl

VÌ SAO TỒN TẠI: trần `top_k` của API sản phẩm là 8 (src/api/schemas.py), nên
với bộ đo thì **hạng 9 và hạng 500 cho cùng một số 0** — không phân biệt được
"trượt sát nút" với "chìm sâu". Đó đúng là độ phân giải cần để đọc kết quả
reranker và để biết ca nào đáng cứu bằng cơ chế nào. Script này đi thẳng
index với k lớn; trần 8 của API GIỮ NGUYÊN làm giới hạn an toàn.

RANH GIỚI QUAN TRỌNG NHẤT — yêu cầu của tester, và lý do của họ đúng:
    script này KHÔNG đọc golden_set, KHÔNG so từ khoá, KHÔNG tính Recall/MRR.
    Nó nhận TRUY VẤN, trả ĐOẠN ĐÃ XẾP HẠNG. Việc khớp nhãn thuộc phía tester.

    Nếu một công cụ vừa lấy dữ liệu vừa chấm theo nhãn của người dùng nó, thì
    lần sau **nhãn sai và công cụ sai không phân biệt được** — đúng chuỗi sự
    cố hai ngày qua. Giữ hai vế ở hai phía là cách rẻ nhất để mỗi bên còn soi
    chéo được bên kia.

TRƯỜNG `khoang_cach`, KHÔNG PHẢI `diem`: Chroma trả **L2 bình phương**, NHỎ =
GẦN. Hiệu chuẩn thật (2026-08-16): Chroma báo d=0.900776 · L2²=0.900798 khớp ·
1−cosine=0.450612 không khớp. Đặt tên theo đúng chiều để không ai phải đoán.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from src.config import RAG_EMBEDDING_MODEL  # noqa: E402
from src.db.models import PolicyChunk, PolicyDocument  # noqa: E402
from src.db.session import SessionLocal  # noqa: E402
from src.rag import store  # noqa: E402


def _nhan_kho() -> dict:
    """Nhãn VẬT — không có nó thì không biết mốc trước/sau thuộc cùng kho không.

    Đã cắn một lần: kho đổi 362 -> 419 giữa hai lượt đo của tester mà hai lượt
    ra số trùng nhau, suýt được đọc thành "phép đo lặp lại xác nhận nhau".

    Băm CÙNG CÔNG THỨC với `kho_rag.py::_bam_kho` (băm text đã sắp xếp, KHÔNG
    băm chunk_id) — `new_id("CHK")` ngẫu nhiên nên băm có chunk_id sẽ đổi mỗi
    lần nạp dù nội dung y hệt.
    """
    with SessionLocal() as s:
        texts = sorted(c.text for c in s.scalars(select(PolicyChunk)).all())
        so_doc = s.query(PolicyDocument).count()
    h = hashlib.md5()
    for t in texts:
        h.update(t.encode())
        h.update(b"\x00")
    tt, pb = store.trang_thai_kho()
    return {
        "so_chunk": len(texts),
        "so_doc": so_doc,
        "bam_noi_dung": h.hexdigest()[:12],
        "chuan_hoa": pb,
        "trang_thai": tt,
        "model_embedding": RAG_EMBEDDING_MODEL,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--truy-van", required=True, help="file mỗi dòng một truy vấn, hoặc '-' đọc stdin")
    ap.add_argument("--k", type=int, default=100)
    ap.add_argument("--ra", default=None, help="ghi JSONL ra file; mặc định stdout")
    a = ap.parse_args()

    nguon = sys.stdin if a.truy_van == "-" else open(a.truy_van, encoding="utf-8")
    truy_van = [x.strip() for x in nguon if x.strip()]
    if not truy_van:
        print("KHÔNG có truy vấn nào — dừng, không ghi file rỗng.", file=sys.stderr)
        return 2

    nhan = _nhan_kho()
    # Nhãn ra STDERR: stdout phải là JSONL thuần để `| jq` chạy được. Nhãn vẫn
    # là dòng đầu tiên người chạy nhìn thấy.
    print(json.dumps({"nhan_kho": nhan}, ensure_ascii=False), file=sys.stderr)
    if nhan["trang_thai"] != store.TRANG_THAI_KHOP:
        print(
            f"KHO KHÔNG KHỚP CODE (trạng thái={nhan['trang_thai']}) — số đo sẽ "
            f"thuộc về một kho khác. Chạy `kho_rag.py kiem`.",
            file=sys.stderr,
        )
        return 3

    ra = open(a.ra, "w", encoding="utf-8") if a.ra else sys.stdout
    with SessionLocal() as s:
        ten = {d.doc_id: d.filename for d in s.scalars(select(PolicyDocument)).all()}
        ch = {c.chunk_id: (c.doc_id, c.text) for c in s.scalars(select(PolicyChunk)).all()}

        for q in truy_van:
            # ĐÚNG đường của sản phẩm: `store.search` tự bỏ dấu rồi embed bằng
            # cùng model/base_url mà agent dùng. KHÔNG tự dựng lại phép chuẩn
            # hoá ở đây — lệch một vế thì không có triệu chứng nào, search vẫn
            # trả đủ k, chỉ là kết quả thuộc về một sản phẩm khác.
            hits = store.search(q, k=a.k)
            kq = []
            for i, (cid, d) in enumerate(hits, 1):
                doc_id, text = ch.get(cid, (None, None))
                if text is None:
                    # Chroma trả chunk_id mà Postgres không có = hai nguồn đang
                    # nói về hai kho khác nhau. KHÔNG bỏ qua im lặng (đúng lỗi
                    # `bo_qua_thieu_chunk` đã bắt được): ghi ra để tester thấy.
                    kq.append({"hang": i, "chunk_id": cid, "tai_lieu": None,
                               "khoang_cach": d, "text": None,
                               "canh_bao": "chunk_id KHÔNG có trong Postgres"})
                    continue
                kq.append({
                    "hang": i,
                    "chunk_id": cid,
                    "tai_lieu": ten.get(doc_id),
                    "khoang_cach": d,  # L2 bình phương, NHỎ = GẦN
                    "text": text,
                })
            ra.write(json.dumps(
                {"truy_van": q, "so_doan": len(kq), "don_vi_khoang_cach": "L2_binh_phuong_nho_la_gan",
                 "nhan_kho": nhan["bam_noi_dung"], "ket_qua": kq},
                ensure_ascii=False) + "\n")
    if a.ra:
        ra.close()
        print(f"đã ghi {len(truy_van)} dòng -> {a.ra}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
