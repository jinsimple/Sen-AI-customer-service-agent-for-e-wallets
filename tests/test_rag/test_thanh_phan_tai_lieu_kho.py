"""Kho chính sách CHỈ được chứa tài liệu đã duyệt — F-KHO-1.

## Vì sao có file này

16/08, kho chính sách ĐANG PHỤC VỤ chứa thêm hai file nội bộ:

    business_rules.md               20 chunk   — bảng số CHƯA verify
    scenario-candidates-momo-faq.md 37 chunk   — danh sách kịch bản test

Agent tra `/policy-search` và trích **cả hai như chính sách thật**. Đó là
**ràng buộc cứng 3** (cấm bịa số liệu): một con số trong `business_rules.md`
truy được tới "một kết quả tool có thật", nên mọi lớp truy vết đều báo hợp lệ
— trong khi bản thân tài liệu chưa ai duyệt.

Đường vào **không phải lỗ hổng**: `POST /policy-docs` × 2 dưới `USR-PA01`, tức
**partner_admin dùng đúng cửa của mình** (CLAUDE.md §1: partner_admin CHỈ quản
lý kho chính sách RAG). Không có gì bị lách.

⟹ Chặn theo **đuôi file** (`.docx/.pdf`) chỉ đóng cửa TAI NẠN. Một bản `.docx`
nháp vẫn vào y hệt. Thứ phân biệt "chính sách phục vụ khách" với "ghi chú nội
bộ" là **có ai duyệt hay không**, và điều đó phải nằm trong ĐẶC TẢ.

## Vì sao danh mục KHÔNG nằm trong file này (PO yêu cầu, và tôi tán thành)

Cám dỗ hiển nhiên là viết `assert docs == {"MoMo_FAQ_Giao_dich", "MoMo_ToS"}`.
Làm thế thì lần đổi kho **hợp lệ** tiếp theo test đỏ oan, và người ta sẽ quen
tay sửa test cho xanh — tới lần một file rác thật lọt vào, cái phản xạ đó đã
được huấn luyện xong rồi.

Danh mục phải là **nguồn sự thật ngoài test**. Chưa có ⟹ đó là một thiếu sót
CÓ THẬT, và `test_dac_ta_danh_muc_nguon_ton_tai` dưới đây giữ nó ở trạng thái
đỏ-có-kiểm-soát (`xfail strict`) cho tới khi ai đó viết ra. Khi file danh mục
xuất hiện, test đó **tự XPASS** ⟹ strict biến XPASS thành đỏ ⟹ buộc người kế
tiếp gỡ `xfail` và bật cổng thật lên. Không ai phải nhớ nhắc ai.

## Hai test này chặn hai thứ khác nhau — đừng gộp

    test_dac_ta_...  : ĐẶC TẢ có tồn tại không          (thiếu = chưa chặn được)
    test_kho_chi_...  : KHO có khớp đặc tả không         (lệch = có file lạ)

Gộp lại thì lúc chưa có đặc tả, một kho bẩn sẽ nấp sau đúng cái đỏ đang được
kỳ vọng, và không ai thấy.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess

import pytest

GOC = pathlib.Path(__file__).resolve().parent.parent.parent

# Nơi ĐẶC TẢ sẽ nằm. Nhiều ứng viên vì security/coder chưa chốt chỗ — test chấp
# nhận bất kỳ chỗ nào trong số này, để việc chốt chỗ không bị test cản.
UNG_VIEN_DANH_MUC = (
    GOC / "contracts" / "rag-nguon.yaml",
    GOC / "contracts" / "rag-sources.yaml",
    GOC / "data" / "raw" / "NGUON-DUOC-DUYET.yaml",
)

CONTAINER = os.environ.get("FIN05_BACKEND_CONTAINER", "fin05-backend-1")


def _tim_danh_muc() -> pathlib.Path | None:
    return next((p for p in UNG_VIEN_DANH_MUC if p.exists()), None)


def _kho_dang_song() -> bool:
    r = subprocess.run(
        ["docker", "ps", "-q", "-f", f"name={CONTAINER}"], capture_output=True, text=True
    )
    return bool(r.stdout.strip())


def _doc_id_trong_chroma() -> set[str]:
    """doc_id THỰC SỰ có vector trong index — thứ truy hồi có thể trả về."""
    ma = (
        "import json,chromadb;"
        "c=chromadb.PersistentClient(path='/app/data/rag_index');"
        "col=c.get_collection('policy_faq');"
        "g=col.get(include=['metadatas']);"
        "print(json.dumps(sorted({m.get('doc_id','?') for m in g['metadatas']})))"
    )
    r = subprocess.run(
        ["docker", "exec", CONTAINER, "python", "-c", ma],
        capture_output=True, text=True, timeout=120,
    )
    if r.returncode != 0:
        pytest.fail(f"không đọc được index: {(r.stderr or r.stdout)[:300]}")
    return set(json.loads(r.stdout.strip().splitlines()[-1]))


def _tai_lieu_trong_kho() -> set[str]:
    """TÊN FILE của các tài liệu đang có vector trong index.

    ⚠️ Bản đầu của hàm này đọc `doc_id` từ Chroma rồi đem so với tên file. Mà
    `doc_id` là **băm** (`DOC-b975b2f37aa4`), không phải tên — nên phép so không
    bao giờ khớp và test XANH RỖNG TUẾCH. Nó "chặn" đúng con số không.

    Đây là bẫy assertion-trùng-trạng-thái-mặc-định (PO phê chuẩn 14/08), lần này
    ở dạng khó thấy hơn: hai vế **cùng kiểu dữ liệu** (đều là chuỗi, đều là
    `set[str]`), chỉ khác KHÔNG GIAN TÊN. Không lỗi, không cảnh báo, xanh mượt.

    Tên thật nằm ở `policy_documents.filename`. Ta lấy doc_id từ Chroma (thứ
    truy hồi trả được) rồi tra tên qua Postgres — giao của hai nguồn, để một
    hàng DB còn sót mà không có vector không bị tính là "đang phục vụ".
    """
    doc_ids = _doc_id_trong_chroma()
    if not doc_ids:
        pytest.fail("index KHÔNG có doc_id nào — kho rỗng, mọi khẳng định dưới đây vô nghĩa")
    sql = "SELECT doc_id, filename FROM policy_documents;"
    r = subprocess.run(
        ["docker", "exec", "fin05-postgres-1", "sh", "-c",
         f'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At -F "|" -c "{sql}"'],
        capture_output=True, text=True, timeout=120,
    )
    if r.returncode != 0:
        pytest.fail(f"không đọc được policy_documents: {(r.stderr or r.stdout)[:300]}")
    ten = {}
    for dong in r.stdout.strip().splitlines():
        if "|" in dong:
            d, f = dong.split("|", 1)
            ten[d.strip()] = f.strip()
    thieu = doc_ids - set(ten)
    assert not thieu, f"index có doc_id không có hàng trong policy_documents: {sorted(thieu)}"
    return {ten[d] for d in doc_ids}


@pytest.mark.xfail(
    _tim_danh_muc() is None,
    strict=True,
    reason=(
        "F-KHO-1: CHƯA CÓ đặc tả nào nói tài liệu nào được phép nằm trong kho "
        "chính sách phục vụ khách. Ngày 16/08 hai file nội bộ vào được kho qua "
        "cửa HỢP LỆ của partner_admin và agent trích chúng như chính sách thật. "
        "Chặn đuôi file không đủ — cần danh mục nguồn ĐÃ DUYỆT. "
        f"Đặt một trong: {', '.join(str(p.relative_to(GOC)) for p in UNG_VIEN_DANH_MUC)}"
    ),
)
def test_dac_ta_danh_muc_nguon_ton_tai():
    """Có nguồn sự thật cho câu hỏi 'tài liệu nào được phục vụ khách'."""
    p = _tim_danh_muc()
    assert p is not None, "không tìm thấy danh mục nguồn được duyệt"
    noi_dung = p.read_text(encoding="utf-8").strip()
    assert noi_dung, f"{p.name} tồn tại nhưng RỖNG — một danh mục rỗng chặn được đúng con số không"


@pytest.mark.skipif(
    _tim_danh_muc() is None,
    reason=(
        "chưa có ĐẶC TẢ danh mục nguồn ⟹ chưa có gì để đối chiếu. Đây là thiếu "
        "NĂNG LỰC thật, không phải nối dây sai: test_dac_ta_danh_muc_nguon_ton_tai "
        "đang giữ đúng thiếu sót đó ở trạng thái xfail(strict) và sẽ tự đỏ khi "
        "danh mục xuất hiện. Skip này không bao giờ im lặng được."
    ),
)
@pytest.mark.skipif(not _kho_dang_song(), reason=f"container {CONTAINER} không chạy — chưa có kho để soi")
def test_kho_chi_chua_tai_lieu_duoc_duyet():
    """Kho phục vụ khách KHÔNG chứa tài liệu ngoài danh mục đã duyệt."""
    import yaml  # noqa: PLC0415 — chỉ cần khi đã có danh mục

    p = _tim_danh_muc()
    duyet = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    ten_duyet = {
        str(x.get("ten") if isinstance(x, dict) else x)
        for x in (duyet.get("nguon_duoc_duyet") or duyet.get("sources") or [])
    }
    assert ten_duyet, f"{p.name} không khai được nguồn nào — xem lại khoá 'nguon_duoc_duyet'"

    trong_kho = _tai_lieu_trong_kho()
    la = trong_kho - ten_duyet
    assert not la, (
        f"KHO CHỨA TÀI LIỆU NGOÀI DANH MỤC: {sorted(la)}\n"
        f"  đã duyệt : {sorted(ten_duyet)}\n"
        f"  trong kho: {sorted(trong_kho)}\n"
        "Agent sẽ trích chúng như chính sách thật (ràng buộc cứng 3). "
        "Nếu tài liệu này ĐÚNG là chính sách, thêm nó vào danh mục kèm người "
        "duyệt — đừng sửa test."
    )


@pytest.mark.skipif(not _kho_dang_song(), reason=f"container {CONTAINER} không chạy — chưa có kho để soi")
def test_kho_khong_chua_tai_lieu_noi_bo_da_biet():
    """Cổng CHẶN CỤ THỂ cho đúng hai file đã từng lọt vào — độc lập với đặc tả.

    Test trên chỉ chạy khi đã có danh mục. Trong lúc chưa có, đây là lớp chặn
    tối thiểu: hai file này đã ở trong kho phục vụ thật một lần rồi, nên chặn
    đích danh chúng không phải là đoán — là hồi quy.

    ⚠️ Đây KHÔNG thay được test trên. Nó chặn hai cái tên đã biết; nó **không**
    biết gì về file thứ ba. Xoá nó khi danh mục đặc tả đã bật cổng thật.
    """
    da_lot = {"business_rules", "scenario-candidates-momo-faq"}
    trong_kho = _tai_lieu_trong_kho()
    lot_lai = {t for t in trong_kho if any(x in t for x in da_lot)}
    assert not lot_lai, (
        f"TÀI LIỆU NỘI BỘ QUAY LẠI KHO PHỤC VỤ: {sorted(lot_lai)}\n"
        "Đây là hồi quy của sự cố 16/08 (F-KHO-1): bảng số chưa verify + danh "
        "sách kịch bản test được agent trích như chính sách thật."
    )
