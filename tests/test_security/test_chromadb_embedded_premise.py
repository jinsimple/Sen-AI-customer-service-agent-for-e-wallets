"""Cổng canh TIỀN ĐỀ cho bản ignore CVE `chromadb` (PYSEC-2026-311 +
CVE-2026-45830/CVE-2026-45833/CVE-2026-45831) ở `tests/test_security/
test_dependency_audit.py::_KNOWN_ACCEPTED_VULN_IDS`.

## Vì sao cổng này tồn tại

Lý do ignore (niêm ở `.github/workflows/ci.yml`, bước "Quét CVE gói Python
(C7)"): bốn CVE này CHỈ khai thác được khi chromadb chạy **chế độ máy chủ**
(`HttpClient`, endpoint HTTP `/api/v2/...`) VÀ có `trust_remote_code=true`.
Dự án dùng `PersistentClient` (nhúng trong tiến trình, `src/rag/store.py`),
không có service/port chroma nào trong `docker-compose*.yml`, và
`trust_remote_code` không xuất hiện trong mã. **Không có bản vá** (cột "Fix
Versions" trống cả bốn) nên không thể nâng cấp — an toàn hoàn toàn dựa vào
BA TIỀN ĐỀ này, không dựa vào bản thân gói đã được sửa.

**Test này KHÔNG kiểm CVE.** Nó kiểm ba tiền đề khiến bốn CVE đó vô hại
trong cách triển khai hiện tại. Ai đó đổi sang chế độ máy chủ, hoặc thêm
`trust_remote_code`, hoặc mở port chroma ra ⟹ bốn CVE **thành thật ngay**,
và nếu không có cổng này, dòng ignore vẫn nằm im, `pytest` vẫn xanh, `pip-
audit` vẫn báo "đã ignore có ghi chú" — trong khi bề mặt tấn công đã có
thật. Đúng họ với `Luật P`/`Luật AC` của dự án: một lý lẽ ĐÚNG lúc viết mà
không ai canh lúc nó hết đúng.

## Đọc bằng CẤU TRÚC, không đọc bằng NGHĨA

Ba hàm `_co_...` dưới đây quét VĂN BẢN nguồn (grep/regex), không suy luận
logic nghiệp vụ — đúng ràng buộc tester không đọc `src/` để hiểu, chỉ để
xác nhận một CHUỖI có/không xuất hiện. Mỗi hàm có ca ĐỐI CHỨNG (Luật A) ở
cuối file — chứng minh nó THẬT SỰ bắt được khi tiền đề vi phạm, không chỉ
luôn xanh vì không bao giờ kiểm được gì.
"""
from __future__ import annotations

import re

from src.config import ROOT_DIR

_CVE_LIEN_QUAN = "PYSEC-2026-311, CVE-2026-45830, CVE-2026-45833, CVE-2026-45831"

_DOCKER_COMPOSE_FILES = ("docker-compose.yml", "docker-compose.do.yml", "docker-compose.ttl-test.yml")


def _dung_persistent_client(noi_dung: str) -> bool:
    return "chromadb.PersistentClient(" in noi_dung


def _dung_http_client(noi_dung: str) -> bool:
    return "chromadb.HttpClient(" in noi_dung


def _co_dich_vu_chroma_server(noi_dung: str) -> list[tuple[int, str]]:
    """Tìm dòng khai báo SERVICE/IMAGE tên chroma trong docker-compose —
    KHÔNG bắt oan khai báo VOLUME (`chroma_data:` dưới mục `volumes:`, đang
    có thật và hợp lệ — đó là nơi PersistentClient ghi index xuống đĩa)."""
    vi_pham = []
    for lineno, dong in enumerate(noi_dung.splitlines(), start=1):
        if re.match(r"^\s{2}chroma:\s*$", dong):
            vi_pham.append((lineno, dong))
        elif re.search(r"image:\s*\S*chroma\S*", dong, re.IGNORECASE):
            vi_pham.append((lineno, dong))
    return vi_pham


def _co_trust_remote_code(noi_dung: str) -> bool:
    return "trust_remote_code" in noi_dung


# ============================================================================
# Cổng thật — chạy trên cây làm việc
# ============================================================================


def test_rag_store_dung_che_do_nhung_khong_dung_may_chu():
    noi_dung = (ROOT_DIR / "src" / "rag" / "store.py").read_text(encoding="utf-8")
    assert _dung_persistent_client(noi_dung), (
        "src/rag/store.py KHÔNG còn thấy chromadb.PersistentClient — tiền đề "
        f"'chạy chế độ nhúng' của bản ignore ({_CVE_LIEN_QUAN}) có thể đã đổi. "
        "Xem lại tests/test_security/test_dependency_audit.py::_KNOWN_ACCEPTED_VULN_IDS "
        "trước khi coi các CVE này vẫn được miễn trừ."
    )
    assert not _dung_http_client(noi_dung), (
        "src/rag/store.py giờ dùng chromadb.HttpClient (CHẾ ĐỘ MÁY CHỦ) — "
        f"{_CVE_LIEN_QUAN} KHÔNG còn được miễn trừ, chúng khai thác được đúng ở "
        "chế độ này. Xem lại bản ignore trong test_dependency_audit.py NGAY."
    )


def test_khong_co_dich_vu_chroma_server_trong_docker_compose():
    for ten_file in _DOCKER_COMPOSE_FILES:
        p = ROOT_DIR / ten_file
        if not p.exists():
            continue
        vi_pham = _co_dich_vu_chroma_server(p.read_text(encoding="utf-8"))
        assert not vi_pham, (
            f"{ten_file} có vẻ khai báo DỊCH VỤ/IMAGE chroma "
            f"({', '.join(f'dòng {n}' for n, _ in vi_pham)}) — tiền đề 'không có "
            f"server/port cho chroma' của bản ignore ({_CVE_LIEN_QUAN}) có thể đã "
            "đổi. Xem lại test_dependency_audit.py."
        )


def test_khong_co_trust_remote_code_trong_ma_san_pham():
    """Phạm vi `src/` — ĐÂY mới là nơi một usage thật sẽ nằm nếu tiền đề vỡ.
    Cố ý KHÔNG quét `tests/` — chính file này cần chứa chuỗi
    `trust_remote_code` trong ca đối chứng phía dưới (dữ liệu giả để chứng
    minh bộ dò kêu được), quét cả tests/ sẽ khiến cổng tự bắt oan chính nó."""
    vi_pham = []
    for p in (ROOT_DIR / "src").rglob("*.py"):
        try:
            noi_dung = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if _co_trust_remote_code(noi_dung):
            vi_pham.append(str(p.relative_to(ROOT_DIR)))
    assert not vi_pham, (
        f"Tìm thấy 'trust_remote_code' trong src/ ({', '.join(vi_pham)}) — "
        f"tiền đề 'không có trust_remote_code trong mã sản phẩm' của bản ignore "
        f"({_CVE_LIEN_QUAN}) đã đổi. Xem lại test_dependency_audit.py NGAY — "
        "đây chính là điều kiện khai thác được của các CVE này."
    )


# ============================================================================
# Ca đối chứng (Luật A) — chứng minh cổng THẬT SỰ kêu, không chỉ luôn xanh.
# Chạy trên VĂN BẢN GIẢ, không đụng file thật nào.
# ============================================================================


def test_doi_chung_phat_hien_http_client():
    gia = 'client = chromadb.HttpClient(host="chroma", port=8000)\n'
    assert _dung_http_client(gia), "Hàm dò HttpClient không bắt được ca rõ ràng có HttpClient — cổng mù."
    assert not _dung_persistent_client(gia), "Văn bản giả không có PersistentClient nhưng hàm dò lại báo có."


def test_doi_chung_phat_hien_dich_vu_chroma_trong_compose():
    gia = "services:\n  backend:\n    image: fin05-backend\n  chroma:\n    image: chromadb/chroma:latest\n    ports:\n      - \"8000:8000\"\n"
    vi_pham = _co_dich_vu_chroma_server(gia)
    assert vi_pham, "Hàm dò dịch vụ chroma không bắt được ca rõ ràng có service 'chroma:' — cổng mù."


def test_doi_chung_khong_bat_oan_volume_chroma_data():
    """Ca ÂM bắt buộc (Luật A) — `chroma_data:` dưới `volumes:` là khai báo
    THẬT, hợp lệ, đang tồn tại trong docker-compose.yml. Bắt oan nó thành
    "dịch vụ chroma" sẽ làm cổng này không bao giờ chạy được."""
    gia = "volumes:\n  chroma_data:\n  postgres_data:\n"
    vi_pham = _co_dich_vu_chroma_server(gia)
    assert not vi_pham, f"Bắt OAN khai báo volume chroma_data thành dịch vụ chroma: {vi_pham}"


def test_doi_chung_phat_hien_trust_remote_code():
    gia = "def tai_model():\n    return AutoModel.from_pretrained(ten, trust_remote_code=True)\n"
    assert _co_trust_remote_code(gia), "Hàm dò trust_remote_code không bắt được ca rõ ràng có chuỗi này — cổng mù."
