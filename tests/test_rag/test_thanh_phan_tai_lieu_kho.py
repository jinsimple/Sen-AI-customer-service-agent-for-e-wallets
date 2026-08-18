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
POSTGRES = os.environ.get("FIN05_POSTGRES_CONTAINER", "fin05-postgres-1")

# Hai file đã THẬT SỰ lọt vào kho phục vụ ngày 16/08 — chặn đích danh, không đoán.
DA_LOT = frozenset({"business_rules", "scenario-candidates-momo-faq"})


def _tim_danh_muc() -> pathlib.Path | None:
    return next((p for p in UNG_VIEN_DANH_MUC if p.exists()), None)


def _kho_dang_song() -> bool:
    r = subprocess.run(
        ["docker", "ps", "-q", "-f", f"name={CONTAINER}"], capture_output=True, text=True
    )
    return bool(r.stdout.strip())


# Mã chạy TRONG container — liệt kê MỌI collection, không gõ cứng tên nào.
#
# 🔴 Bản cũ gõ cứng `get_collection('policy_faq')`. Đo được 18/08 (hộp đen,
# `docker exec` chỉ-đọc, 0 token) — index của `fin05` có BA collection:
#
#     'policy_faq'                            count=0     ← bản cũ soi ĐÚNG cái này
#     'policy_faq__text-embedding-v4'         count=378
#     'policy_faq__text-embedding-3-small'    count=378
#
# Nên suốt thời gian qua ca này KHÔNG đỏ vì "kho rỗng" — nó đỏ vì **soi nhầm
# một collection rỗng trong khi kho thật có 378 chunk**. Câu `pytest.fail` cũ in
# ra KẾT LUẬN ("kho rỗng") thay vì TRIỆU CHỨNG ("collection tên X trả 0
# doc_id"), nên `docs/STATE.md` chép lại và cả đội tin từ 17/08 (Luật H).
#
# Vì sao KHÔNG thay bằng tên mới: gõ `'policy_faq__text-embedding-v4'` là chép
# từ code lần thứ hai, và chết y hệt ngày đổi model nhúng. Tên collection mang
# TÊN MODEL ⟹ nó SẼ đổi.
#
# 🔴 Và vì sao phải kiểm MỌI collection chứ không riêng cái to nhất: hai
# collection cùng giữ 378 chunk là hai kho phục vụ song song. Một cổng rò rỉ bỏ
# sót một collection là một cổng rò rỉ hỏng.
_MA_LIET_KE = """
import glob, json, os, chromadb

# TỰ TÌM index, không gõ cứng path.
#
# 🔴 Vì sao: bản trước gõ cứng '/app/data/rag_index' — thừa kế nguyên văn từ
# chính đầu dò đã hỏng. Đo được 18/08: biến môi trường của container là
# CHROMA_PERSIST_DIR=./data/chroma, tức nó trỏ MỘT PATH KHÁC, và path đó KHÔNG
# có index nào. Nếu sản phẩm có ngày nghe theo biến ấy, một cổng gõ cứng path
# sẽ soi nhầm chỗ y hệt lần trước, chỉ khác một tầng.
#
# Đây là Luật M đúng nghĩa: lần liệt kê đầu cho đúng con số tài liệu đã hứa
# (378), nên không có gì kích hoạt phản xạ soi lại cái path.
duong = sorted({os.path.dirname(f) for f in glob.glob('/app/**/chroma.sqlite3', recursive=True)})
if len(duong) != 1:
    print(json.dumps({'__khong_do_duoc__': 'so index Chroma != 1: ' + repr(duong)}))
else:
    c = chromadb.PersistentClient(path=duong[0])
    ra = {'__duong__': duong[0]}
    for mo_ta in c.list_collections():
        ten = mo_ta.name if hasattr(mo_ta, 'name') else str(mo_ta)
        g = c.get_collection(ten).get(include=['metadatas'])
        ra[ten] = sorted({m.get('doc_id', '?') for m in (g['metadatas'] or [])})
    print(json.dumps(ra))
"""


def _doc_id_moi_collection() -> dict[str, list[str]]:
    """{ten_collection: [doc_id]} cho **mọi** collection trong index.

    Không lọc, không gõ cứng tên. Collection rỗng vẫn xuất hiện với danh sách
    rỗng — cần thế để phân biệt *"không có collection nào"* với *"có nhưng
    rỗng"*, hai triệu chứng khác hẳn nhau.
    """
    r = subprocess.run(
        # PYTHONDONTWRITEBYTECODE: [ĐO] 18/08 — cùng lệnh này không có nó
        # làm `docker diff` tăng +101 dòng (bytecode cache). Nó không hỏng
        # dữ liệu, nhưng nó làm MÙ chính dây báo động cả đội dùng để hỏi
        # "phép đo có chạm vật không". Xác minh Δ=0 trên container thứ ba.
        ["docker", "exec", "-e", "PYTHONDONTWRITEBYTECODE=1", CONTAINER,
         "python", "-c", _MA_LIET_KE],
        capture_output=True, text=True, timeout=120,
    )
    if r.returncode != 0:
        pytest.fail(
            "KHÔNG ĐO ĐƯỢC (không phải 'kho sạch'): không liệt kê được collection "
            f"trong container {CONTAINER} — {(r.stderr or r.stdout)[:300]}"
        )
    ra = json.loads(r.stdout.strip().splitlines()[-1])
    if "__khong_do_duoc__" in ra:
        pytest.fail(
            "KHÔNG ĐO ĐƯỢC (KHÔNG phải 'kho sạch'): " + ra["__khong_do_duoc__"]
            + " — soi một index khi có nhiều index là soi nhầm chỗ, đúng lớp lỗi "
            "vừa vá ngày 18/08."
        )
    ra.pop("__duong__", None)
    return ra


def _ten_theo_doc_id() -> dict[str, str]:
    """`policy_documents.doc_id -> filename`, đọc từ Postgres của ngăn xếp."""
    sql = "SELECT doc_id, filename FROM policy_documents;"
    r = subprocess.run(
        ["docker", "exec", POSTGRES, "sh", "-c",
         f'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At -F "|" -c "{sql}"'],
        capture_output=True, text=True, timeout=120,
    )
    if r.returncode != 0:
        pytest.fail(f"KHÔNG ĐO ĐƯỢC: không đọc được policy_documents — {(r.stderr or r.stdout)[:300]}")
    ten = {}
    for dong in r.stdout.strip().splitlines():
        if "|" in dong:
            d, f = dong.split("|", 1)
            ten[d.strip()] = f.strip()
    return ten


def _tim_lot(
    kho: dict[str, list[str]], ten: dict[str, str], mau_cam: set[str]
) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """LOGIC THUẦN — trả **(lọt, mồ_côi)**, mỗi cái là {collection: {...}}.

    Không chạm container. Tách khỏi phần đọc hạ tầng **có chủ đích**: nhờ nó mà
    cổng này chứng minh được nửa *"KÊU lúc bất thường"* (Luật A) bằng dữ liệu
    bịa, **không ghi một byte nào vào kho đang phục vụ** (Luật I). Xem
    `test_doi_chung_cong_biet_keu_khi_kho_ban`.

    🔴 **Vì sao trả HAI tập chứ không một** — bản đầu của hàm này gộp `doc_id`
    không tra được tên vào chung với "lọt", bằng cách thay nó bằng một nhãn
    `<doc_id không có hàng…>`. Ca đối chứng bắt được ngay: bộ lọc đối chiếu
    `mau_cam` với **chuỗi doc_id**, không với nhãn ⟹ mồ côi **lọt qua im
    lặng**, và một kho có hàng CSDL bị mất sẽ được báo là **SẠCH**.

    Đó đúng là Luật 7 — công cụ đo là lớp không ai canh. Và gộp hai thứ là sai
    cả về nghĩa: *"tài liệu nội bộ đã biết quay lại kho"* và *"có vector mà
    không biết nó là gì"* là hai kết luận khác nhau, đòi hai hành động khác
    nhau. Cái thứ hai là **KHÔNG ĐO ĐƯỢC**, không phải BẨN.
    """
    lot: dict[str, set[str]] = {}
    mo_coi: dict[str, set[str]] = {}
    for col, doc_ids in kho.items():
        for d in doc_ids:
            if d not in ten:
                mo_coi.setdefault(col, set()).add(d)
            elif any(x in ten[d] for x in mau_cam):
                lot.setdefault(col, set()).add(ten[d])
    return lot, mo_coi


def _tai_lieu_trong_kho() -> set[str]:
    """TÊN FILE của tài liệu có vector trong **bất kỳ** collection nào.

    ⚠️ Bản đầu của hàm này đọc `doc_id` từ Chroma rồi đem so với tên file. Mà
    `doc_id` là **băm** (`DOC-b975b2f37aa4`), không phải tên — nên phép so không
    bao giờ khớp và test XANH RỖNG TUẾCH. Nó "chặn" đúng con số không.

    Đây là bẫy assertion-trùng-trạng-thái-mặc-định (PO phê chuẩn 14/08), lần này
    ở dạng khó thấy hơn: hai vế **cùng kiểu dữ liệu** (đều là `set[str]`), chỉ
    khác KHÔNG GIAN TÊN. Không lỗi, không cảnh báo, xanh mượt.
    """
    kho = _doc_id_moi_collection()
    if not kho:
        pytest.fail("KHÔNG ĐO ĐƯỢC: index KHÔNG có collection nào — không có gì để soi")
    tong = {d for ds in kho.values() for d in ds}
    if not tong:
        pytest.fail(
            "KHÔNG ĐO ĐƯỢC (KHÔNG phải 'kho sạch'): mọi collection đều rỗng — "
            + ", ".join(f"{c}={len(ds)}" for c, ds in sorted(kho.items()))
        )
    ten = _ten_theo_doc_id()
    thieu = tong - set(ten)
    assert not thieu, f"index có doc_id không có hàng trong policy_documents: {sorted(thieu)}"
    return {ten[d] for d in tong}


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
    kho = _doc_id_moi_collection()
    if not kho:
        pytest.fail("KHÔNG ĐO ĐƯỢC: index KHÔNG có collection nào — không có gì để soi")
    if not any(kho.values()):
        pytest.fail(
            "KHÔNG ĐO ĐƯỢC (KHÔNG phải 'kho sạch'): mọi collection đều rỗng — "
            + ", ".join(f"{c}={len(ds)}" for c, ds in sorted(kho.items()))
        )

    lot_lai, mo_coi = _tim_lot(kho, _ten_theo_doc_id(), DA_LOT)
    if mo_coi:
        pytest.fail(
            "KHÔNG ĐO ĐƯỢC (KHÔNG phải 'kho sạch'): có vector mang doc_id không "
            "tra được hàng trong `policy_documents` — không biết chúng là tài "
            "liệu gì, nên không khẳng định được kho sạch:\n"
            + "\n".join(f"  {c}: {sorted(t)}" for c, t in sorted(mo_coi.items()))
        )
    assert not lot_lai, (
        "TÀI LIỆU NỘI BỘ QUAY LẠI KHO PHỤC VỤ, theo từng collection:\n"
        + "\n".join(f"  {col}: {sorted(t)}" for col, t in sorted(lot_lai.items()))
        + "\nĐây là hồi quy của sự cố 16/08 (F-KHO-1): bảng số chưa verify + danh "
        "sách kịch bản test được agent trích như chính sách thật."
    )


def test_doi_chung_cong_biet_keu_khi_kho_ban():
    """Nửa **KÊU LÚC BẤT THƯỜNG** của Luật A — nửa mà không ca đối chứng nào thì
    không chứng minh được.

    Chạy trên dữ liệu BỊA, 0 container, 0 token: cổng này vừa đi qua đúng lớp
    lỗi *"xanh vì soi nhầm chỗ"*, nên "xanh" của nó chỉ đọc được khi có một ca
    chứng minh nó biết đỏ.

    🔴 Ca bịa đặt tài liệu bẩn ở **collection THỨ HAI, không phải thứ nhất** —
    đó chính là hình dạng của lỗi thật: index có 3 collection, bản cũ soi đúng
    một cái (và đúng cái rỗng). Một cổng dừng ở collection đầu tiên sẽ XANH ở ca
    này, và đó là điều cần bắt.
    """
    ten = {
        "DOC-sach01": "MoMo_FAQ_Giao_dich.md",
        "DOC-ban01": "business_rules.md",
    }
    kho_ban = {
        "policy_faq__model-a": ["DOC-sach01"],
        "policy_faq__model-b": ["DOC-sach01", "DOC-ban01"],
    }
    lot, mo_coi = _tim_lot(kho_ban, ten, DA_LOT)
    assert lot == {"policy_faq__model-b": {"business_rules.md"}}, (
        f"cổng KHÔNG kêu đúng chỗ khi kho bẩn ở collection thứ hai: {lot}"
    )
    assert mo_coi == {}, f"báo mồ côi oan trên dữ liệu tra được hết: {mo_coi}"

    # Luật 2 — và nó KHÔNG chặn nhầm kho sạch.
    sach, _ = _tim_lot({"policy_faq__model-a": ["DOC-sach01"]}, ten, DA_LOT)
    assert sach == {}, f"cổng kêu oan trên kho sạch: {sach}"

    # TRẠNG THÁI THỨ BA: `doc_id` không tra được tên phải rơi vào rổ RIÊNG,
    # không được im thành "sạch" mà cũng không được kêu thành "bẩn".
    lot_mc, mo_coi_mc = _tim_lot({"c": ["DOC-khong-co-trong-db"]}, ten, DA_LOT)
    assert lot_mc == {}, "mồ côi bị đếm nhầm thành tài liệu nội bộ lọt"
    assert mo_coi_mc == {"c": {"DOC-khong-co-trong-db"}}, (
        f"doc_id không tra được tên bị nuốt mất — kho thủng mà cổng im: {mo_coi_mc}"
    )
