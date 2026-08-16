"""Trích text từ file chính sách/FAQ do partner_admin upload
(POST /policy-docs, src/api/main.py).

Chỉ hỗ trợ .md/.txt/.pdf/.docx — CỐ Ý không hỗ trợ .doc nhị phân cũ (OLE):
không có parser Python thuần an toàn cho định dạng này, ép dùng công cụ hệ
thống (antiword/LibreOffice headless) để mở file người dùng tải lên đi ngược
lại tinh thần "bảo mật RAG cấp cao" của tính năng này. Người upload cần lưu
lại thành .docx trước.

Luôn kiểm magic bytes THẬT trước khi parse — không tin đuôi file client tự
khai, chặn kiểu tấn công đổi đuôi file để né validate.
"""
from __future__ import annotations

import io
import re
import unicodedata

from src.tools.base import ToolError

_PDF_MAGIC = b"%PDF-"
_ZIP_MAGIC = b"PK\x03\x04"  # .docx là 1 file zip (Office Open XML)

_ALLOWED_TEXT_EXTENSIONS = (".md", ".txt")


class UnsupportedDocumentError(ToolError):
    """File không đúng định dạng hỗ trợ hoặc đuôi file không khớp nội dung thật."""


_NGUYEN_AM = set("aeiouy")


def _bo_dau(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _co_nguyen_am(s: str) -> bool:
    return any(c in _NGUYEN_AM for c in _bo_dau(s).lower())


def _ghep_am_tiet_vo(text: str) -> str:
    """Vá lỗi trích xuất PDF chèn khoảng trắng GIỮA một âm tiết tiếng Việt.

    Kho RAG thật chứa `"Giao D ịch"`, `"liên k ết"`, `"th ực"` — khoảng trắng
    do pypdf chèn khi ghép glyph có dấu. Nó phá CẢ HAI tầng truy hồi cùng lúc:
    embedding thấy hai token rác thay vì một từ, và khớp từ khoá trượt hoàn
    toàn. Đo trên kho thật: **414 chỗ** trong 254.196 ký tự.

    LUẬT GHÉP — hai điều kiện ĐỒNG THỜI, và cả hai đều cần:
      (1) mảnh TRƯỚC là cụm PHỤ ÂM THUẦN 1-3 ký tự (không chứa nguyên âm).
          Âm tiết tiếng Việt LUÔN có nguyên âm, nên một token toàn phụ âm
          không bao giờ là một từ hoàn chỉnh — nó chỉ có thể là mảnh vỡ.
      (2) mảnh SAU bắt đầu bằng NGUYÊN ÂM — tức nó là phần VẦN của âm tiết.

    Vì sao cần cả (2), đo mới thấy: chỉ dùng (1) thì ghép nhầm **143 chỗ** viết
    tắt hợp lệ — `NH TMCP` -> `NHTMCP`, `SMS Banking` -> `SMSBanking`,
    `JCB Debit`, `TK ngân`, `x Rộng`. Thêm (2) loại sạch cả 143 mà vẫn giữ
    nguyên 414 ca ghép đúng.

    KHÔNG dùng từ điển: một danh sách từ viết tay sẽ thiếu đúng từ người ta
    sắp gõ (Luật 18/ADR-023). Luật này dựa vào TÍNH CHẤT ÂM VỊ của tiếng Việt,
    không dựa vào việc liệt kê.
    """

    def _thay(m: re.Match[str]) -> str:
        truoc, sau = m.group(1), m.group(2)
        if _co_nguyen_am(truoc):
            return m.group(0)
        dau_sau = _bo_dau(sau)[:1].lower()
        if dau_sau not in _NGUYEN_AM:
            return m.group(0)
        return truoc + sau

    return re.sub(r"\b([A-Za-zĐđ]{1,3}) ([a-zA-ZÀ-ỹĐđ]{1,12})\b", _thay, text)


# DON 3 — LOAI DONG MUC LUC KHOI INDEX.
#
# Phat hien cua tester khi xac minh 41 nhan: muc luc chua NGUYEN VAN 160 cau
# hoi cua tai lieu, va no THANG dap an trong embedding — khach hoi cang giong
# cau that thi cang de trung dong muc luc. Ca RAG-21/22: ca top-3 deu la dong
# "……… so trang". Kho TU CANH TRANH VOI CHINH NO.
#
# LUAT HAI DIEU KIEN, khong phai mot (canh trong kieu F-25 — luat loai phai
# kem ca doi chung, dung loai nham than bai):
#   (1) chuoi >=5 dau cham LIEN TIEP
#   (2) VA ket thuc bang so trang
#
# Do tren kho that (3.896 dong, 2 PDF):
#   khop ca hai dieu kien        263 dong  -> loai, deu la muc luc
#   co "..." nhung KHONG ket so    4 dong  -> GIU, deu la than bai that
#                                             (vd "10.000d,...")
# Chi dieu kien (1) se loai nham 4 dong do. Dieu kien (2) la thu phan biet.
_DONG_MUC_LUC = re.compile(r"\.{5,}\s*\d+\s*$")


def _bo_dong_muc_luc(text: str) -> str:
    """Bo dong muc luc; GIU nguyen moi dong khac va cau truc xuong dong.

    ĐÍNH CHÍNH số đo (commit 0c965a7 ghi SAI, không sửa lịch sử được):
        mốc TRƯỚC  20/35 — KHÔNG phải 19/35. 19/35 có trước khi tester sửa
                   nhãn sai của ca RAG-08 ở 675282e; tôi đo "sau" bằng thước
                   mới nhưng so với mốc "trước" đo bằng thước cũ.
        sau đòn 3  21/35  ⟹ delta ròng +1, không phải +2.

    Trong đó có ca RAG-04 chuyển ĐẠT -> trượt. Đo lại: chunk duy nhất trong
    top-10 khớp từ khoá của ca là một DÒNG TIÊU ĐỀ MỤC LỤC, và nó khớp bằng
    từ khoá yếu `nhận tiền` chứ không phải `50.000.000`. Đáp án thật của FAQ 7
    không có mặt. Tức RAG-04 chưa bao giờ truy hồi đúng — đòn 3 làm lộ một
    PASS GIẢ, không gây hồi quy. Ghi ra thay vì gộp vào delta.

    Hệ quả rộng hơn (tester audit tiếp, PO chốt ở STATE 78ecc79): 9/21 ca đang
    ĐẠT là đạt nhờ từ khoá chung. 60% là GIỚI HẠN TRÊN, cận dưới 34,3%.
    Con số của hàm này chỉ đáng tin tới mức thước chấm đáng tin.
    """
    return "\n".join(d for d in text.split("\n") if not _DONG_MUC_LUC.search(d.strip()))


def _extension(filename: str) -> str:
    idx = filename.rfind(".")
    return filename[idx:].lower() if idx != -1 else ""


def _extract_pdf(content: bytes) -> str:
    from pypdf import PdfReader

    try:
        reader = PdfReader(io.BytesIO(content))
        pages = [page.extract_text() or "" for page in reader.pages]
    except Exception as e:  # pypdf raises nhiều loại lỗi khác nhau tuỳ file hỏng
        raise UnsupportedDocumentError(f"Không đọc được nội dung PDF: {e}") from e
    text = "\n\n".join(p.strip() for p in pages if p.strip())
    if not text.strip():
        raise UnsupportedDocumentError("PDF không có text trích xuất được (có thể là bản scan ảnh)")
    # Vá âm tiết vỡ NGAY TẠI ĐIỂM TRÍCH — trước khi text đi vào chia chunk và
    # embedding. Vá muộn hơn (lúc truy vấn) không cứu được: vector đã sai rồi.
    # Thu tu CO CHU DICH: ghep am tiet vo TRUOC, roi moi bo muc luc.
    # Nguoc lai thi dong muc luc bi tu-vo se khong khop mau va lot vao index.
    return _bo_dong_muc_luc(_ghep_am_tiet_vo(text))


def _hang_bang_thanh_dong(bang) -> list[str]:
    """Mỗi HÀNG bảng -> MỘT dòng tự mô tả, mang theo tên cột.

    Vì sao không nối phẳng: bản PDF của đúng bảng này bị pypdf nghiền thành
    cháo (`NH TMCP Ngoại Thương VCB Tất cả NH TMCP Bản Việt VCCB 2,000,000...`)
    — 23 ngân hàng dính liền một khối, không hàng nào tra riêng được. Đo được:
    tester tìm thấy ~20 đoạn gần-trùng khiến 31,5% kho không bao giờ nổi lên
    top-3, và nhóm đó CHÍNH LÀ bảng này.

    Kèm tên cột vào từng ô để hàng đứng một mình vẫn đọc được: chunk có thể bị
    cắt rời khỏi hàng tiêu đề, lúc đó "VCB · Tất cả" là vô nghĩa còn
    "Tên viết tắt: VCB · Hạn mức: Tất cả" thì không.
    """
    hang = bang.rows
    if not hang:
        return []
    cot = [c.text.strip() for c in hang[0].cells]
    ra: list[str] = []
    for h in hang[1:]:
        o = [c.text.strip() for c in h.cells]
        if not any(o):
            continue
        ra.append(" · ".join(f"{cot[i]}: {v}" if i < len(cot) and cot[i] else v
                             for i, v in enumerate(o) if v))
    return ra


def _extract_docx(content: bytes) -> str:
    """Giữ CẤU TRÚC của DOCX thay vì đổ phẳng.

    Bản trước: `"\\n".join(p.text for p in doc.paragraphs)`. Hai thứ bị vứt:
      1. style heading — mất biên đoạn tự nhiên (239 Heading 3 = ~1 mỗi FAQ,
         và tiêu đề đã mang sẵn tên thực thể: "44. Cách liên kết MoMo với tài
         khoản ngân hàng Việt Nam Phương Đông (OCB)")
      2. `doc.tables` — python-docx KHÔNG đưa ô bảng vào `doc.paragraphs`, nên
         bảng 23 hàng hạn mức ngân hàng trước nay không hề vào kho qua đường
         DOCX. Im lặng, không lỗi.

    Heading được tách bằng DÒNG TRỐNG hai đầu vì `RecursiveCharacterTextSplitter`
    (src/rag/ingest.py) ưu tiên cắt ở `\\n\\n` — đó là cách duy nhất extractor
    tác động được tới biên chunk mà không phải sửa bộ chia.

    TƯƠNG THÍCH NGƯỢC (điều kiện PO cho 4b): file .docx thường — không heading,
    không bảng — cho ra ĐÚNG chuỗi như bản cũ, vì cả hai nhánh mới đều không
    kích hoạt. Đường upload của partner_admin không đổi hành vi.
    """
    from docx import Document
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    try:
        doc = Document(io.BytesIO(content))
    except Exception as e:
        raise UnsupportedDocumentError(f"Không đọc được nội dung DOCX: {e}") from e

    # Duyệt THÂN tài liệu để giữ đúng thứ tự văn bản/bảng xen kẽ —
    # `doc.paragraphs` và `doc.tables` là hai danh sách rời, ghép lại sẽ dồn
    # hết bảng xuống cuối, cắt đứt bảng khỏi đoạn văn giới thiệu nó.
    phan: list[str] = []
    for con in doc.element.body.iterchildren():
        if con.tag.endswith("}p"):
            p = Paragraph(con, doc)
            if not p.text.strip():
                continue
            ten_style = (p.style.name or "") if p.style is not None else ""
            if ten_style.startswith("Heading"):
                phan.append("\n" + p.text.strip())
            else:
                phan.append(p.text.strip())
        elif con.tag.endswith("}tbl"):
            phan.extend(_hang_bang_thanh_dong(Table(con, doc)))

    text = "\n".join(phan).strip()
    if not text.strip():
        raise UnsupportedDocumentError("DOCX không có nội dung text nào")
    return text


def _extract_plain_text(content: bytes) -> str:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as e:
        raise UnsupportedDocumentError(f"File không phải UTF-8 hợp lệ: {e}") from e
    if not text.strip():
        raise UnsupportedDocumentError("File rỗng")
    return text


def extract_text(filename: str, content: bytes) -> str:
    """Điểm vào duy nhất — dispatch theo đuôi file, xác minh magic bytes thật
    trước khi parse, ném UnsupportedDocumentError với thông báo rõ ràng cho
    mọi trường hợp không parse được (agent/API hiển thị lại cho người upload)."""
    ext = _extension(filename)

    if ext in _ALLOWED_TEXT_EXTENSIONS:
        return _extract_plain_text(content)

    if ext == ".pdf":
        if not content.startswith(_PDF_MAGIC):
            raise UnsupportedDocumentError(
                "Đuôi file là .pdf nhưng nội dung không phải PDF thật"
            )
        return _extract_pdf(content)

    if ext == ".docx":
        if not content.startswith(_ZIP_MAGIC):
            raise UnsupportedDocumentError(
                "Đuôi file là .docx nhưng nội dung không phải DOCX thật"
            )
        return _extract_docx(content)

    if ext == ".doc":
        raise UnsupportedDocumentError(
            "Không hỗ trợ .doc (định dạng Word cũ) — vui lòng lưu lại thành .docx rồi upload lại"
        )

    raise UnsupportedDocumentError(
        f"Định dạng '{ext or '(không có đuôi)'}' không được hỗ trợ — chỉ nhận .md/.txt/.pdf/.docx"
    )
