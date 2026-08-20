#!/usr/bin/env python3
"""Kho RAG — in nhãn, kiểm lệch phiên bản, nạp lại.

    python scripts/kho_rag.py nhan      # in nhãn kho (số chunk + băm + phiên bản)
    python scripts/kho_rag.py kiem      # exit 1 nếu kho dựng bằng chuẩn-hoá CŨ
    python scripts/kho_rag.py nap-lai     # xoá + parse lại từ data/raw/ (ưu tiên .docx)
    python scripts/kho_rag.py nap-vector  # GIỮ Postgres, chỉ nhúng lại cho model hiện tại
        [--embed-model M] [--embed-base-url URL] [--embed-api-key-tu TEN_BIEN]
        # nạp kho cho model KHÁC mà KHÔNG đổi cấu hình đang phục vụ

VÌ SAO TỒN TẠI: đòn 2 bỏ dấu ở CẢ HAI vế (index + query). Kho dựng bằng code
cũ + query chạy code mới = LỆCH MỘT VẾ, và ca đó **không có triệu chứng nào** —
search vẫn trả đủ k kết quả, chỉ là kết quả sai. Không lỗi, không log. Đọc text
trong kho cũng không phát hiện được vì thay đổi nằm ở VECTOR, không ở chữ.

Một bước "phải nhớ re-index" mà quên thì im lặng chính là mìn. `kiem` biến nó
thành thứ MÁY kiểm được, và `deploy_home.*` gọi nó tự động.
"""
import hashlib
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# --- TIÊM BIẾN TỪ CLI, PHẢI chạy TRƯỚC mọi `from src...` -------------------
# `src.config` đọc biến môi trường LÚC IMPORT, nên muốn nạp kho cho một model
# khác mà KHÔNG đổi cấu hình đang phục vụ thì phải đặt biến trước import.
#
# Vì sao cần: lật `.env` sang model mới là hệ đang phục vụ chuyển NGAY sang
# collection RỖNG — đúng chế độ hỏng vừa phát hiện ở stack ttl (24 giờ trả
# "không tìm thấy" cho mọi câu, không một tín hiệu). Đường CLI này biến việc
# đổi nhà cung cấp thành thao tác KHÔNG CÓ TRẠNG THÁI TRUNG GIAN HỎNG: nạp
# xong, kiểm xong, rồi mới lật — lật lúc đó là tức thì.
#
# Script này là TIẾN TRÌNH RIÊNG nên biến chỉ sống trong nó, không chạm server.
#
# ⚠️ KHOÁ nhận qua TÊN BIẾN MÔI TRƯỜNG (`--embed-api-key-tu`), KHÔNG nhận giá
# trị trực tiếp: tham số dòng lệnh hiện trong `ps` cho mọi tiến trình trên máy,
# và trong shell history. Truyền khoá qua argv là tự tạo một đường rò mới ngay
# trong công cụ vừa sinh ra để xử một vụ rò khoá.
def _tiem_bien_tu_cli() -> None:
    import os as _os
    import sys as _sys

    cap = {"--embed-model": "EMBEDDING_MODEL", "--embed-base-url": "EMBEDDING_BASE_URL"}
    argv = _sys.argv
    for co, bien in cap.items():
        if co in argv:
            _os.environ[bien] = argv[argv.index(co) + 1]
    if "--embed-api-key-tu" in argv:
        ten = argv[argv.index("--embed-api-key-tu") + 1]
        gt = _os.environ.get(ten)
        if not gt:
            print(f"  Biến {ten} rỗng hoặc không tồn tại — dừng.", file=_sys.stderr)
            raise SystemExit(2)
        _os.environ["EMBEDDING_API_KEY"] = gt


_tiem_bien_tu_cli()


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
        print("            Nếu bạn ĐÃ ở trong container mà vẫn thấy dòng này — kho")
        print("            CHƯA TỪNG được nạp lần nào, chạy: kho_rag.py nap-lai")
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

    ⚠️ CÁCH BĂM PHẢI ĐI KÈM CON SỐ. Đây là băm CHUẨN-HOÁ (md5 của text đã sắp
    xếp), KHÔNG phải băm file thô — hai cách cho hai con số khác nhau trên cùng
    một vật, và so chéo chúng tạo báo động giả. Đã xảy ra HAI LẦN trong một
    ngày: lược đồ tool (chuẩn-hoá vs file-thô) và `.env` (md5 vs sha256, tôi
    kết luận nhầm là file bị sửa loạn xạ trong khi nó đứng yên).

    Bản này băm thứ TẤT ĐỊNH: tập `(chunk_id, text)` ĐÃ SẮP XẾP, đọc từ
    Postgres qua ORM (text đã giải mã, không phải ciphertext — Fernet có IV
    ngẫu nhiên nên băm ciphertext cũng sẽ không tất định).

    ⚠️ Nó băm phía DỮ LIỆU, không băm phía VECTOR. Kho có thể cùng text mà
    khác embedding (đúng ca đòn 2). Vì thế nhãn phải LUÔN đi kèm
    `chuẩn hoá vN` — hai thứ cùng nhau mới định danh được kho.

    ⚠️ KHÔNG băm `chunk_id`. Bản trước có, và tester đo ra nó tạo BÁO ĐỘNG
    RỖNG: `new_id("CHK")` sinh ngẫu nhiên, nên nạp lại CÙNG nguồn CÙNG parser
    vẫn ra băm khác (a3c5c7359337 -> 2209afc2042c) trong khi hai lượt đó cho
    danh sách ca trượt TRÙNG KHÍT 15/14 — tương đương hoàn toàn về đo lường.

    Băm phải trả lời "kho có cùng NỘI DUNG không", không phải "có cùng lượt
    nạp không". Ai cần định danh một lượt nạp thì dùng `nap_lai_luc`.
    """
    with SessionLocal() as s:
        texts = sorted(c.text for c in s.scalars(select(PolicyChunk)).all())
    h = hashlib.md5()
    for text in texts:
        h.update(text.encode())
        h.update(b"\x00")
    return h.hexdigest()[:12]


def nhan() -> None:
    _chan_tu_tao_kho()
    with SessionLocal() as s:
        n = s.query(PolicyChunk).count()
        d = s.query(PolicyDocument).count()
    tt, pb = store.trang_thai_kho()
    print(f"  kho RAG: {n} chunk (Postgres) · {d} doc · băm-chuẩn-hoá(md5,12) {_bam_kho()}")
    print(f"  đường dẫn Chroma: {RAG_INDEX_DIR}")
    print(f"  chuẩn hoá: kho={pb if pb is not None else '(không có dấu)'} · code={store.CHUAN_HOA_VERSION} · trạng thái={tt}")
    print(f"  model embedding: {store.RAG_EMBEDDING_MODEL} · collection {store._ten_collection()}")
    # NHÃN VẬT phải mang tên model nhúng: hai model = hai không gian vector,
    # số đo KHÔNG so chéo được. Thiếu dòng này thì một bảng trước/sau bắc qua
    # hai kho trông y hệt một bảng hợp lệ.


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
    if tt == store.TRANG_THAI_LECH_MODEL:
        print("  [LỆCH MODEL] Kho dựng bằng MODEL EMBEDDING khác với code hiện tại.")
        print("               Vector trong kho vô nghĩa với query mới — search vẫn trả")
        print("               đủ k kết quả, chỉ là kết quả SAI. Không lỗi, không log.")
        print("               Chạy: python scripts/kho_rag.py nap-lai")
        return 1
    if tt == store.TRANG_THAI_LECH:
        print(f"  [LỆCH]  Kho ở phiên bản {pb}, code ở {store.CHUAN_HOA_VERSION}.")
        print("          Chạy: python scripts/kho_rag.py nap-lai")
        return 1
    # Cổng CUỐI, sau mọi cổng khác — vì đây là ca mà mọi cổng khác đều xanh.
    cu, t_nap, t_server = _server_dang_cam_kho_cu()
    if cu:
        _in_canh_bao_kho_cu(t_nap, t_server)
        return 3
    print("  [OK]    Kho khớp phiên bản chuẩn hoá của code, và server đã đọc bản này.")
    return 0


DAU_NAP_LAI = "nap_lai_luc"


def _server_dang_cam_kho_cu() -> tuple[bool, float, float]:
    """Kho có bị nạp lại SAU khi tiến trình phục vụ khởi động không?

    ĐÂY LÀ LỖI ĐÃ CẮN THẬT, và là loại nguy hiểm nhất: mọi đèn đều xanh.
    tester đo `/policy-search` ra 0 kết quả 12 lượt liên tiếp trong khi
    Chroma 378 vector · Postgres 378 chunk · `kiem` xanh. Ba nguồn xác nhận
    "kho ổn" — và cả ba đọc chỗ khác với chỗ sản phẩm đọc.

    CƠ CHẾ: `nap-lai` chạy trong TIẾN TRÌNH RIÊNG (`docker exec python
    scripts/kho_rag.py`) và ghi vào cùng thư mục Chroma mà uvicorn đang mở.
    `chromadb.PersistentClient` không hỗ trợ nhiều tiến trình dùng chung một
    persist dir: `_client` cache ở cấp module trong server giữ segment CŨ —
    segment vừa bị xoá — nên truy vấn trả rỗng. Không lỗi, không log, HTTP 200,
    `status="not_found"`. Khởi động lại server là hết.

    VÌ SAO KHÔNG DÙNG mtime CỦA `chroma.sqlite3`: đã thử, và nó SAI. Chính
    server cũng ghi vào file đó sau khi khởi động (WAL/trang/trạng thái nội
    bộ — cùng lý do khiến băm-theo-file mất tất định, xem `_bam_kho`). Đo thử:
    server lên 08:38:58, mtime kho 08:39:12 -> báo "cũ" trong khi tra hoàn toàn
    tốt. Dấu phải do RIÊNG `nap-lai` đặt, không ai khác chạm.

    VÌ SAO KHÔNG DÙNG canary "hỏi kho một câu" NGAY TRONG SCRIPT NÀY: script
    này cũng là tiến trình riêng. Canary của nó sẽ mở client MỚI, thấy kho mới,
    và báo xanh — đúng lúc server đang trả rỗng. Nó sẽ thành nguồn xác nhận
    sai thứ tư. Muốn hỏi thật thì phải hỏi QUA server, không hỏi cạnh server.
    """
    dau = RAG_INDEX_DIR / DAU_NAP_LAI
    if not dau.exists():
        return False, 0.0, 0.0
    t_nap = dau.stat().st_mtime
    try:
        # mtime của /proc/<pid> trên Linux = lúc tiến trình khởi động. PID 1
        # trong container này là chính uvicorn.
        t_server = os.path.getmtime("/proc/1")
    except OSError:
        return False, t_nap, 0.0
    return t_nap > t_server, t_nap, t_server


def _in_canh_bao_kho_cu(t_nap: float, t_server: float) -> None:
    print(f"  [SERVER CŨ] Kho nạp lại lúc {time.strftime('%H:%M:%S', time.localtime(t_nap))},")
    print(f"              tiến trình phục vụ khởi động lúc {time.strftime('%H:%M:%S', time.localtime(t_server))}.")
    print("              Server đang cầm segment Chroma ĐÃ BỊ XOÁ -> /policy-search")
    print("              trả 0 kết quả, HTTP 200, không lỗi, không log. Im lặng.")
    print("              BẮT BUỘC: docker compose restart backend")



def nap_vector() -> None:
    """Nhúng LẠI các chunk ĐÃ CÓ trong Postgres vào collection của model hiện tại.

    KHÁC `nap-lai` ở chỗ quyết định: `nap-lai` XOÁ sạch `PolicyDocument` rồi
    parse lại từ `data/raw/` -> sinh `chunk_id` MỚI.

    Với thiết kế hai-kho-song-song, làm thế là PHÁ kho kia: Postgres giữ text
    dùng chung, khoá theo `chunk_id`. Sinh id mới -> collection của model cũ
    trỏ vào những id KHÔNG CÒN TỒN TẠI -> `search` vẫn trả đủ k, tất cả bị
    `bo_qua_thieu_chunk` loại, kết quả rỗng. Đúng chế độ hỏng đã tốn một buổi
    hôm qua, lần này do chính ta gây ra.

    Lệnh này GIỮ NGUYÊN Postgres, chỉ tính vector mới cho đúng những chunk đó.
    ⟹ đổi nhà cung cấp nhúng = nạp MỘT LẦN cho model mới, hai kho song song,
    không kho nào phá kho nào, và chuỗi đo của kho cũ không bị cắt.

    MỘT đường nạp cho mọi model (kỷ luật hai-kho đã chốt): không có lệnh riêng
    cho Qwen và lệnh riêng cho OpenAI — cùng lệnh này, khác biến môi trường.
    """
    _chan_tu_tao_kho()
    with SessionLocal() as s:
        rows = [(c.chunk_id, c.doc_id, c.text)
                for c in s.scalars(select(PolicyChunk).order_by(PolicyChunk.chunk_id)).all()]
    if not rows:
        print("  Postgres KHÔNG có chunk nào — chạy `nap-lai` trước, đừng dùng lệnh này.")
        raise SystemExit(1)

    col = store._get_collection()
    if col.count() > 0:
        print(f"  Collection {store._ten_collection()} ĐÃ có {col.count()} vector.")
        print("  KHÔNG ghi đè — xoá tường minh trước nếu thật sự muốn nạp lại.")
        raise SystemExit(1)

    print(f"  nhúng {len(rows)} chunk bằng {store.RAG_EMBEDDING_MODEL} -> {store._ten_collection()}")
    theo_doc: dict[str, list] = {}
    for cid, did, text in rows:
        theo_doc.setdefault(did, []).append((cid, text))
    for did, ds in theo_doc.items():
        store.add_chunks(did, [c for c, _ in ds], [t for _, t in ds])
        print(f"     {did}: {len(ds)} chunk")
    store._dong_dau(col)
    print()
    nhan()


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
                s, file_bytes=f.read_bytes(), filename=f.name, uploaded_by="USR-PA01",
                nguon_nap="script_noi_bo",
            )
            print(f"  nạp: {f.name} -> {doc.doc_id}")
        s.commit()
    # Dấu này CHỈ nap-lai đặt. Nó là thứ duy nhất phân biệt được "kho đổi vì
    # ta nạp lại" với "file kho bị chính server chạm vào khi đọc".
    (RAG_INDEX_DIR / DAU_NAP_LAI).write_text(str(time.time()))
    print()
    nhan()
    print()
    cu, t_nap, t_server = _server_dang_cam_kho_cu()
    if cu:
        _in_canh_bao_kho_cu(t_nap, t_server)
        print("              (nap-lai KHÔNG tự restart: nó chạy BÊN TRONG chính")
        print("               container cần restart, tự giết mình thì không báo")
        print("               cáo lại được. deploy_home.* làm bước này giúp bạn.)")


if __name__ == "__main__":
    lenh = sys.argv[1] if len(sys.argv) > 1 else "nhan"
    if lenh == "nhan":
        nhan()
    elif lenh == "kiem":
        raise SystemExit(kiem())
    elif lenh == "nap-lai":
        nap_lai()
    elif lenh == "nap-vector":
        nap_vector()
    else:
        print(__doc__)
        raise SystemExit(2)
