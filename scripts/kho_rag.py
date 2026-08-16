#!/usr/bin/env python3
"""Kho RAG — in nhãn, kiểm lệch phiên bản, nạp lại.

    python scripts/kho_rag.py nhan      # in nhãn kho (số chunk + băm + phiên bản)
    python scripts/kho_rag.py kiem      # exit 1 nếu kho dựng bằng chuẩn-hoá CŨ
    python scripts/kho_rag.py nap-lai   # xoá + nạp lại từ data/raw/*.pdf

VÌ SAO TỒN TẠI: đòn 2 bỏ dấu ở CẢ HAI vế (index + query). Kho dựng bằng code
cũ + query chạy code mới = LỆCH MỘT VẾ, và ca đó **không có triệu chứng nào** —
search vẫn trả đủ k kết quả, chỉ là kết quả sai. Không lỗi, không log. Đọc text
trong kho cũng không phát hiện được vì thay đổi nằm ở VECTOR, không ở chữ.

Một bước "phải nhớ re-index" mà quên thì im lặng chính là mìn. `kiem` biến nó
thành thứ MÁY kiểm được, và `deploy_home.*` gọi nó tự động.
"""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import RAG_INDEX_DIR  # noqa: E402
from src.db.models import PolicyChunk, PolicyDocument  # noqa: E402
from src.db.session import SessionLocal  # noqa: E402
from src.rag import store  # noqa: E402
from src.rag.ingest import delete_document, ingest_document  # noqa: E402

THU_MUC_PDF = Path(__file__).resolve().parent.parent / "data" / "raw"


def _bam_kho() -> str:
    h = hashlib.md5()
    for p in sorted(RAG_INDEX_DIR.rglob("*")):
        if p.is_file():
            h.update(hashlib.md5(p.read_bytes()).hexdigest().encode())
    return h.hexdigest()[:12]


def nhan() -> None:
    with SessionLocal() as s:
        n = s.query(PolicyChunk).count()
        d = s.query(PolicyDocument).count()
    tt, pb = store.trang_thai_kho()
    print(f"  kho RAG: {n} chunk · {d} doc · băm {_bam_kho()}")
    print(f"  đường dẫn Chroma: {RAG_INDEX_DIR}")
    print(f"  chuẩn hoá: kho={pb if pb is not None else '(không có dấu)'} · code={store.CHUAN_HOA_VERSION} · trạng thái={tt}")


def kiem() -> int:
    nhan()
    tt, pb = store.trang_thai_kho()
    if tt == store.TRANG_THAI_TRONG:
        print("  [TRỐNG] Kho chưa có chunk nào — chạy `nap-lai`.")
        return 1
    if tt == store.TRANG_THAI_KHONG_DAU:
        print("  [CŨ]    Kho CÓ nội dung nhưng KHÔNG có dấu phiên bản — dựng trước đòn 2.")
        print("          Index còn dấu tiếng Việt, query đã bỏ dấu ⟹ LỆCH MỘT VẾ.")
        print("          Search vẫn trả đủ k kết quả, chỉ là KẾT QUẢ SAI. Không triệu chứng.")
        print("          Chạy: python scripts/kho_rag.py nap-lai")
        return 1
    if tt == store.TRANG_THAI_LECH:
        print(f"  [LỆCH]  Kho ở phiên bản {pb}, code ở {store.CHUAN_HOA_VERSION}.")
        print("          Chạy: python scripts/kho_rag.py nap-lai")
        return 1
    print("  [OK]    Kho khớp phiên bản chuẩn hoá của code.")
    return 0


def nap_lai() -> None:
    pdfs = sorted(THU_MUC_PDF.glob("*.pdf"))
    if not pdfs:
        print(f"  KHÔNG có PDF nào trong {THU_MUC_PDF} — dừng, không xoá kho hiện có.")
        raise SystemExit(1)
    with SessionLocal() as s:
        for d in s.query(PolicyDocument).all():
            print(f"  xoá: {d.filename}")
            delete_document(s, d.doc_id)
        s.commit()
        for f in pdfs:
            doc = ingest_document(
                s, file_bytes=f.read_bytes(), filename=f.name, uploaded_by="USR-PA01"
            )
            print(f"  nạp: {f.name} -> {doc.doc_id}")
        s.commit()
    print()
    nhan()


if __name__ == "__main__":
    lenh = sys.argv[1] if len(sys.argv) > 1 else "nhan"
    if lenh == "nhan":
        nhan()
    elif lenh == "kiem":
        raise SystemExit(kiem())
    elif lenh == "nap-lai":
        nap_lai()
    else:
        print(__doc__)
        raise SystemExit(2)
