#!/usr/bin/env python3
"""Kho RAG — in nhãn, kiểm lệch phiên bản, nạp lại.

    python scripts/kho_rag.py nhan      # in nhãn kho (số chunk + băm + phiên bản)
    python scripts/kho_rag.py kiem      # exit 1 nếu kho dựng bằng chuẩn-hoá CŨ
    python scripts/kho_rag.py nap-lai   # xoá + nạp lại từ data/raw/ (ưu tiên .docx)

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

from sqlalchemy import select  # noqa: E402

from src.config import RAG_INDEX_DIR  # noqa: E402
from src.db.models import PolicyChunk, PolicyDocument  # noqa: E402
from src.db.session import SessionLocal  # noqa: E402
from src.rag import store  # noqa: E402
from src.rag.ingest import delete_document, ingest_document  # noqa: E402

THU_MUC_NGUON = Path(__file__).resolve().parent.parent / "data" / "raw"


def _chon_nguon() -> list[Path]:
    """Cùng một tài liệu có cả .docx lẫn .pdf -> LẤY .docx. (Đòn 4a)

    Đo được, thước đối xứng — lấy từ điển bên này soi bên kia để không bên nào
    tự chứng minh mình sạch:

        soi PDF  bằng từ điển DOCX : 115 chữ vỡ · thiếu 17 câu
        soi DOCX bằng từ điển PDF  :   0 chữ vỡ · thiếu  9 câu

    DOCX sạch tuyệt đối VÀ đủ hơn — không có mặt nào PDF hơn, nên đây không
    phải đánh đổi. PDF nhiều ký tự hơn (169k so 162k) chỉ vì lặp header/footer
    và mục lục, không phải vì nhiều nội dung hơn.

    Đòn 1 (`_ghep_am_tiet_vo`) GIỮ NGUYÊN trong pipeline — nó vẫn là đường duy
    nhất cho nguồn chỉ-có-PDF, và nó có thật hiệu lực: 215 chỗ vỡ kiểu
    `xác th ực` bị nó ghép lại hết. Cái nó KHÔNG bắt là lớp thứ hai
    (`ho ặc`, `kho ản` — vế trái có nguyên âm), 131 lần/52 dạng; đòn 4 tránh
    lớp đó bằng cách không đi qua PDF chứ không phải bằng cách vá thêm.

    ⚠️ CỐ Ý chỉ nhận .docx/.pdf — KHÔNG nhận .md/.txt, dù `parsers.py` đọc
    được cả hai. `data/raw/` còn `scenario-candidates-momo-faq.md` và
    `business_rules.md`: vật liệu kịch bản test và quy tắc nội bộ, CHƯA BAO
    GIỜ nằm trong kho (bản trước glob đúng `*.pdf`). Nới đuôi file ở đây sẽ
    âm thầm đẩy giàn giáo test vào kho chính sách, và agent sẽ trích dẫn nó
    như chính sách thật — đúng thứ ràng buộc cứng 3 cấm. Đòn 4 là ĐỔI NGUỒN
    của cùng một bộ tài liệu, không phải mở rộng bộ tài liệu.
    """
    tat_ca = sorted(p for p in THU_MUC_NGUON.iterdir()
                    if p.suffix.lower() in (".docx", ".pdf"))
    co_docx = {p.stem for p in tat_ca if p.suffix.lower() == ".docx"}
    return [p for p in tat_ca if not (p.suffix.lower() == ".pdf" and p.stem in co_docx)]


def _chan_tu_tao_kho() -> None:
    """DỪNG nếu kho không tồn tại ở đường đang trỏ — KHÔNG để Chroma tự tạo.

    Lỗi tester bắt (nặng hơn "đọc nhầm đường"): công cụ chạy trên HOST mở
    `PersistentClient` vào `<repo>/data/rag_index` — đường KHÔNG tồn tại vì kho
    thật nằm trong Docker volume `fin05_chroma_data`, chỉ container thấy.
    Chroma **tự tạo một store RỖNG** ở đó, rồi công cụ báo "kho trống".

    ⟹ Nó không chỉ đọc nhầm chỗ — **nó chế ra bằng chứng cho kết luận sai của
    chính nó**. Chạy lần hai sẽ thấy một store "thật" (do lần một đẻ ra) và mọi
    dấu hiệu đều nhất quán. Dạng công-cụ-sai khó bắt nhất: nó tự làm cho mình
    đúng.

    LUẬT: một công cụ ĐI KIỂM không bao giờ được phép TẠO RA thứ nó đang kiểm.
    """
    if not (RAG_INDEX_DIR / "chroma.sqlite3").exists():
        print(f"  [SAI CHỖ] Không có kho Chroma ở {RAG_INDEX_DIR}")
        print("            Kho thật nằm trong Docker volume `fin05_chroma_data`,")
        print("            CHỈ container thấy. Chạy trong container:")
        print("              docker exec fin05-backend-1 python scripts/kho_rag.py kiem")
        print("            (DỪNG ở đây thay vì mở — mở là Chroma tự đẻ một kho rỗng")
        print("             rồi công cụ báo 'kho trống', tự chế bằng chứng cho mình.)")
        raise SystemExit(2)


def _bam_kho() -> str:
    """Băm NỘI DUNG kho, tất định.

    Bản trước băm FILE trong thư mục Chroma — và tester đo ra nó KHÔNG TẤT
    ĐỊNH: ba lần đọc liên tiếp trên kho không đổi cho ba giá trị khác nhau.
    Đúng thôi: `chroma.sqlite3` là SQLite, nó ghi WAL / đổi trang / cập nhật
    trạng thái nội bộ ở MỖI LẦN MỞ, kể cả khi chỉ đọc. Băm một file đang sống
    thì băm cả tiếng ồn của nó.

    Hệ quả của bản trước nặng hơn "một con số xấu": mọi suy luận
    "băm khác ⟹ kho đổi" thành vô hiệu THEO CẢ HAI CHIỀU. (Re-index vẫn là
    thật — bằng chứng là probe 0/8→5/8, không phải băm.)

    Bản này băm thứ TẤT ĐỊNH: tập `(chunk_id, text)` ĐÃ SẮP XẾP, đọc từ
    Postgres qua ORM (text đã giải mã, không phải ciphertext — Fernet có IV
    ngẫu nhiên nên băm ciphertext cũng sẽ không tất định).

    ⚠️ Nó băm phía DỮ LIỆU, không băm phía VECTOR. Kho có thể cùng text mà
    khác embedding (đúng ca đòn 2). Vì thế nhãn phải LUÔN đi kèm
    `chuẩn hoá vN` — hai thứ cùng nhau mới định danh được kho.
    """
    with SessionLocal() as s:
        rows = sorted(
            (c.chunk_id, c.text) for c in s.scalars(select(PolicyChunk)).all()
        )
    h = hashlib.md5()
    for cid, text in rows:
        h.update(cid.encode())
        h.update(b"\x00")
        h.update(text.encode())
        h.update(b"\x00")
    return h.hexdigest()[:12]


def nhan() -> None:
    _chan_tu_tao_kho()
    with SessionLocal() as s:
        n = s.query(PolicyChunk).count()
        d = s.query(PolicyDocument).count()
    tt, pb = store.trang_thai_kho()
    print(f"  kho RAG: {n} chunk (Postgres) · {d} doc · băm-nội-dung {_bam_kho()}")
    print(f"  đường dẫn Chroma: {RAG_INDEX_DIR}")
    print(f"  chuẩn hoá: kho={pb if pb is not None else '(không có dấu)'} · code={store.CHUAN_HOA_VERSION} · trạng thái={tt}")


def kiem() -> int:
    nhan()
    tt, pb = store.trang_thai_kho()
    with SessionLocal() as s:
        n_pg = s.query(PolicyChunk).count()
    # ĐỐI CHIẾU HAI NGUỒN. Postgres nói có chunk mà Chroma nói trống = KHÔNG
    # PHẢI "kho trống", mà là ĐANG ĐỌC HAI KHO KHÁC NHAU. Bản trước in cả hai
    # số cạnh nhau ("418 chunk" rồi "kho chưa có chunk nào") mà không đối
    # chiếu — người đọc phải tự nhận ra mâu thuẫn. Giờ máy nhận ra.
    if tt == store.TRANG_THAI_TRONG and n_pg > 0:
        print(f"  [MÂU THUẪN] Postgres có {n_pg} chunk nhưng Chroma ở {RAG_INDEX_DIR} trống.")
        print("              Hai nguồn không cùng nói về một kho — KHÔNG kết luận gì.")
        print("              Gần như chắc chắn đang chạy sai nơi (host vs container).")
        return 2
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
    # nap-lai CÓ QUYỀN tạo kho (đó là việc của nó), nhưng chỉ khi thư mục
    # đích thuộc container — kiểm bằng sự tồn tại của thư mục cha.
    if not RAG_INDEX_DIR.parent.exists():
        print(f"  [SAI CHỖ] {RAG_INDEX_DIR.parent} không tồn tại — chạy trong container.")
        raise SystemExit(2)
    nguon = _chon_nguon()
    if not nguon:
        print(f"  KHÔNG có tài liệu nào trong {THU_MUC_NGUON} — dừng, không xoá kho hiện có.")
        raise SystemExit(1)
    bo_qua = sorted(p.name for p in THU_MUC_NGUON.iterdir()
                    if p.suffix.lower() == ".pdf" and p not in nguon)
    if bo_qua:
        print(f"  bỏ qua (có bản .docx sạch hơn): {', '.join(bo_qua)}")
    with SessionLocal() as s:
        for d in s.query(PolicyDocument).all():
            print(f"  xoá: {d.filename}")
            delete_document(s, d.doc_id)
        s.commit()
        for f in nguon:
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
