"""Trục ĐỐI CHỨNG cho `resolutions.note`: căn cứ từ chối có SỐNG SÓT không.

⚠️ FILE NÀY CỐ Ý TÁCH KHỎI `test_reject_note_doi_khang.py`. Đừng gộp.

## Vì sao phải là một file riêng, và vì sao "assert chặt hơn" KHÔNG phải cách vá

Bộ `test_reject_note_doi_khang.py` (13 ca, đang xanh) hỏi **"PII có vắng mặt
không"** — dạng `assert sdt not in note_trong_db`. Security đo được scrub `note`
**chặn nhầm 8/20 = 40%** trên ghi chú KHÔNG hề có PII: nó xoá đúng **căn cứ từ
chối** (`"từ chối theo chính sách"` → `"từ chối [PERSON]"`).

Bộ 13 ca đó **vẫn xanh** khi điều này xảy ra. Không phải vì nó viết ẩu — mà vì:

> **Assert dạng `X not in db` LUÔN XANH khi nội dung bị xoá quá tay.**
> Xoá càng mạnh thì test càng xanh. Một bộ test chỉ hỏi *"PII có vắng mặt
> không"* **KHÔNG THỂ** phát hiện over-scrub, chạy bao nhiêu ca cũng vậy.
> *(security rút, PO-agent ratify thành luật dự án 15/08.)*

Luật này **không nói bộ kia sai — nó nói bộ kia ĐO SAI THỨ.** Hệ quả thao tác,
và đây là điểm dễ làm hỏng nhất: cách vá **không phải "assert chặt hơn"** mà là
**thêm một câu hỏi KHÁC LOẠI**. Chặt hơn theo cùng một trục chỉ làm bản vá
chặt-tay-nhất thắng nhanh hơn.

Hai trục, hai file, hai chiều hỏng ngược nhau:

| File | Câu hỏi | Chiều hỏng nó bắt |
|---|---|---|
| `test_reject_note_doi_khang.py` | PII có vắng mặt không? | scrub **quá lỏng** — dữ liệu cá nhân vào sổ kiểm toán |
| **file này** | nội dung hợp lệ có sống sót không? | scrub **quá tay** — mất căn cứ của một phán quyết HITL |

Nhét chung một file là mời một lần sửa làm hỏng cả hai — chính vì bản vá làm
một trục xanh hơn thì trục kia đỏ, và người sửa vội sẽ nới đúng cái vừa cản họ.

## Vì sao mất căn cứ từ chối là thiệt hại THẬT, không phải chuyện thẩm mỹ

`resolutions.note` là **trường ẩn duy nhất nơi văn bản tự do nhân viên gõ đi vào
bản ghi kiểm toán** (ADR-024). Nó tồn tại để trả lời câu *"vì sao hồ sơ này bị
từ chối"*. Một note bị scrub thành `"từ chối [PERSON]"` vẫn **có mặt đầy đủ**
trong sổ, vẫn qua mọi ràng buộc DB, và **không còn trả lời được câu hỏi nó sinh
ra để trả lời** — đúng dạng *hiện diện ≠ hiệu lực* ở tầng dữ liệu.

## NGƯỠNG: 0/20. Không phải "thấp hơn".

Một ghi chú KHÔNG chứa PII thì không có gì hợp pháp để scrub cả — nên bất kỳ
thay đổi nào cũng là thay đổi thừa. Ngưỡng "thấp hơn 8" sẽ hợp thức hoá một
mức mất mát tuỳ tiện.

## TRẠNG THÁI: CỔNG SỐNG — 8/20 tại `he_thong c110a1a8eff7`

Đo 15/08 qua ĐƯỜNG GHI THẬT (POST `/resolutions/{id}/reject` → đọc thẳng DB),
dấu kẹp hai đầu khớp. Danh sách 8 ca **trùng khớp 8/8** với phép đo độc lập của
security (họ gọi thẳng hàm scrub, `he_thong fd16681d8088`) ⟹ finding là **tính
chất của hệ thống**, không phải hiện vật của một cách đo (Luật 16: hai dẫn xuất
bằng hai PHƯƠNG PHÁP khác nhau).

## VÌ SAO 8 CA DÙNG `xfail(strict=True)` CHỨ KHÔNG PHẢI MARKER `security_finding`

PO-agent ban đầu chốt gắn `security_finding`. Tôi **đo thử trước khi gắn** và nó
có một lỗ — báo lại kèm số, họ quyết cuối:

```
JOB security-findings-gate  (pytest tests/ -m security_finding)
    20 ca đối chứng CHẠY          (8 failed · 12 passed)
    test_reject_note_doi_khang.py DESELECTED  (nó không mang marker)
    test_cam_chay_le_...          DESELECTED  (nó cũng không mang marker)
```

⟹ Trong đúng cái job đó, trục đối chứng **chạy MỘT MÌNH**, và **chính cái cổng
cấm-chạy-lẻ cũng bị cùng bộ lọc bịt miệng**. Một bản vá "không scrub gì cả" sẽ
cho **20/20 xanh** ở job này mà không còn gì bắt được — đúng kịch bản mà cổng
kia sinh ra để chặn, chỉ khác là nay nó bị vô hiệu bởi một marker.

`xfail(strict=True)` giữ được cả ba mục tiêu của PO-agent mà không mở lỗ đó:
  - KHÔNG làm `lint-and-test` đỏ (tránh tái diễn hình dạng F-CI-2)
  - KHÔNG cần job CI mới, KHÔNG chờ coder
  - 20 ca **ở lại cùng phiên** với bộ ca có PII ⟹ cặp đối chứng còn nguyên
Và thêm một tính chất marker không có: **vá xong thì XPASS tự báo lỗi**, buộc gỡ
marker. Yêu cầu "khi B1/B2 land thì gỡ" thành CƠ CHẾ thay vì lời nhắc.

Đánh dấu theo `ket_qua_goc` của corpus (nhãn ĐÃ GHI NHẬN, không phải tôi chạy
suite rồi chép ra): nên MỌI đổi hành vi đều đỏ — vá được thì XPASS, hồi quy ở 12
ca đang qua thì FAIL. Hai chiều đều có người canh.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.deps import get_session
from src.api.main import app
from src.auth import create_access_token
from src.db.models import Resolution
from src.tools.create_ticket import create_ticket
from src.tools.propose_resolution import propose_resolution

BO_CA_CO_PII = "test_reject_note_doi_khang.py"

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture()
def client(sample_db):
    """Bản sao fixture `client` của `test_reject_note_doi_khang.py`.

    KHÔNG import chéo từ file test kia: fixture ở đó là CỤC BỘ (không nằm ở
    `conftest.py`), nên file này không thấy nó — phát hiện thật khi dựng khung,
    lượt chạy đầu ra `ERROR at setup ... fixture 'client' not found`.

    Đáng ghi lại vì nó là một cái bẫy nhỏ đúng họ với cả ngày hôm nay: một file
    test mới trông như đã sẵn sàng, và thứ chặn nó không phải logic mà là **dây
    nối** — nếu khung này chỉ được dựng vào lúc corpus tới, ta sẽ vấp đúng lỗi
    đó đúng lúc đang vội.
    """
    def _override_session():
        try:
            yield sample_db
            sample_db.commit()
        except Exception:
            sample_db.rollback()
            raise

    app.dependency_overrides[get_session] = _override_session
    yield TestClient(app)
    app.dependency_overrides.clear()

# Corpus do SECURITY xuất — ĐÚNG 20 câu đã dùng đo 8/20, kèm đánh dấu 8 câu bị
# chặn nhầm ở lần đo gốc.
#
# VÌ SAO KHÔNG TỰ SOẠN 20 CA (tester đã hỏi và dừng chờ): nếu tôi soạn bộ khác,
# con số của tôi và con số 8/20 của security **đo hai vật khác nhau** và không
# ai ghép cặp được — không nói được "đã cải thiện" hay "chưa". Cùng lý do một
# cặp before/after phải dùng CÙNG thước (Luật 4).
CORPUS = REPO / "docs" / "security" / "corpus-ghi-chu-sach-20-ca.jsonl"
CORPUS_UNG_VIEN = [CORPUS]

# Trường của corpus (security trích BẰNG AST từ script đo gốc, không chép tay —
# nên đây đúng là 20 câu đã cho ra 8/20, không phải một bộ tương tự):
#   id · cau · ky_vong · ket_qua_goc · sau_scrub_goc
#
# `ket_qua_goc` là NHÃN TẠI `he_thong fd16681d8088`, không phải sự thật vĩnh
# viễn. Cây đã trôi từ lúc đó. Bộ đo này KHÔNG đọc `ket_qua_goc` để chấm — nó
# đo lại từ đầu và đóng dấu riêng. Cột gốc chỉ để ĐỐI CHIẾU thủ công khi cần
# biết một ca đã đổi hành vi hay chưa; ghi đè nó là mất mốc so sánh.
TRUONG_CAU = "cau"

SO_CA_THEO_DAC_TA = 20


def _tim_corpus() -> Path | None:
    for p in CORPUS_UNG_VIEN:
        if p.exists():
            return p
    return None


def _nap_corpus(p: Path) -> list[dict]:
    out_items = []
    for number, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            out_items.append(json.loads(line))
        except json.JSONDecodeError as e:
            raise AssertionError(
                f"{p.name} dòng {number} không phải JSON hợp lệ: {e}. Corpus hỏng là "
                "lỗi PHẢI ĐỎ — không được lặng lẽ bỏ qua dòng rồi đo trên mẫu số nhỏ hơn."
            ) from e
    return out_items


def _auth(role: str, user_id: str) -> dict:
    token = create_access_token(
        user_id=user_id, role=role, otp_verified_at=dt.datetime.utcnow()
    )
    return {"Authorization": f"Bearer {token}"}


def _make_resolution(sample_db) -> tuple[str, str]:
    ticket = create_ticket(
        sample_db, user_id="USR-A", complaint_type="wrong_recipient",
        scope="internal_wallet", description_raw="do toan ven note",
        trans_id="TXN-0001",
    )
    resolution = propose_resolution(
        sample_db, ticket_id=ticket["ticket_id"], action_type="refund_to_wallet",
        rationale="ly do test", amount=92_000, created_by="USR-CSKH",
    )
    return ticket["ticket_id"], resolution["resolution_id"]


def _tu_choi(client, resolution_id: str, *, note: str):
    return client.post(
        f"/resolutions/{resolution_id}/reject",
        json={"reason": "khac", "note": note},
        headers=_auth("supervisor", "USR-SUP"),
    )


_CHUA_CO_FIELD = object()


def _note_trong_db(sample_db, resolution_id: str) -> str:
    """ĐỌC THẲNG DB, không đọc qua response API.

    Đọc qua API không phân biệt được "đã che khi ghi" với "ghi thô rồi che lúc
    trả về" — và bản thô nằm trong DB là đã hỏng: nó có trong mọi bản sao lưu,
    mọi truy vấn vận hành, mọi lần ai đó mở pgAdmin. Cùng lý do bộ che-PII đọc
    thẳng DB.
    """
    sample_db.expire_all()
    res = sample_db.get(Resolution, resolution_id)
    val = getattr(res, "note", _CHUA_CO_FIELD)
    assert val is not _CHUA_CO_FIELD, (
        "`Resolution.note` chưa tồn tại — chưa đo được, KHÔNG phải đạt."
    )
    return val or ""


# ===========================================================================
# CỔNG GHÉP LIÊN-FILE — CẤM CHẠY LẺ TRỤC ĐỐI CHỨNG
# ===========================================================================


def test_cam_chay_le_phai_kem_bo_ca_co_pii(request):
    """Trục này chạy MỘT MÌNH là vô nghĩa — và tệ hơn: nó gây hiểu nhầm.

    Một bản vá **"không scrub gì cả"** đạt **0/20 hoàn hảo** ở file này. Nếu ai
    chạy riêng nó rồi báo "0/20, xong", họ vừa nghiệm thu một bản vá đã gỡ bỏ
    toàn bộ lớp che PII — đúng chiều hỏng mà `test_reject_note_doi_khang.py`
    sinh ra để canh.

    Đây là "ca đối chứng bắt buộc" (Luật 2) ở tầng FILE thay vì tầng ca: hai bộ
    kéo về hai phía ngược nhau, nên điểm cân chỉ thấy được khi chạy CÙNG.

    Cơ chế thay vì lời dặn (PO-agent yêu cầu, cùng tinh thần xfail-strict): test
    này đọc danh sách test ĐÃ THU của phiên chạy và ĐỎ nếu bộ ca có PII vắng
    mặt. Một dòng dặn trong docstring sẽ bị bỏ qua đúng vào lúc ai đó chạy vội
    `pytest <file này>` để xem con số.
    """
    tried = {i.nodeid for i in request.session.items}
    co_bo_pii = any(BO_CA_CO_PII in nid for nid in tried)
    assert co_bo_pii, (
        f"Trục đối chứng đang chạy MÀ KHÔNG có `{BO_CA_CO_PII}` trong cùng phiên.\n"
        "0/20 ở đây KHÔNG chứng minh gì cả — một bản vá gỡ sạch scrub cũng đạt "
        "0/20. Chạy cùng:\n"
        f"    pytest tests/test_api/{BO_CA_CO_PII} {Path(__file__).name}\n"
        "hoặc đơn giản `pytest tests/`."
    )


# ===========================================================================
# TỰ ÁP LUẬT 6 LÊN CHÍNH FILE NÀY — skip phải TỰ CHỨNG MINH lý do là THẬT
# ===========================================================================
# Hôm nay đội mất hai ngày vì hai bộ test skip trong im lặng với một dòng lý do
# trông rất hợp lý (`tests/CHUAN-VIET-TEST.md` Luật 6). File này skip khi chưa
# có corpus — một lý do CHÍNH ĐÁNG (năng lực chưa tồn tại, không phải dây nối
# sai). Nhưng "chính đáng" không miễn cho nó khỏi phải chứng minh.


def test_ly_do_skip_phai_that():
    """Chạy LUÔN, không bao giờ skip. Canh chính cơ chế skip của file này.

    Hai chiều đều phải đúng:
      - báo "chưa có corpus" thì corpus phải THẬT SỰ không tồn tại ở mọi đường
        ứng viên (nếu có mà không thấy ⟹ đường dẫn sai, và đó là BUG của bộ
        test đội lốt điều kiện môi trường — đúng ca F-CI-3)
      - corpus tồn tại thì phải nạp được và ĐỦ 20 ca (có file mà rỗng/thiếu ca
        là tệ nhất: nó làm `parametrize` sinh 0 test và cả file xanh trong im
        lặng — pytest KHÔNG báo gì khi parametrize trên danh sách rỗng)
    """
    p = _tim_corpus()
    if p is None:
        for candidate in CORPUS_UNG_VIEN:
            assert not candidate.exists(), (
                f"MÂU THUẪN: {candidate} TỒN TẠI nhưng bộ dò báo không có corpus. "
                "Đường dẫn sai — bug của bộ test, không phải thiếu dữ liệu."
            )
        pytest.skip(
            "Corpus 20 ca ghi chú sạch CHƯA TỒN TẠI — security đang xuất ra file "
            f"(chờ ở: {' hoặc '.join(str(x.relative_to(REPO)) for x in CORPUS_UNG_VIEN)}). "
            "Đây là 'CHƯA ĐO ĐƯỢC', KHÔNG phải 'đạt'."
        )

    ca = _nap_corpus(p)
    assert len(ca) == SO_CA_THEO_DAC_TA, (
        f"{p.name} có {len(ca)} ca, đặc tả nói {SO_CA_THEO_DAC_TA}. Mẫu số lệch thì "
        "con số của tôi không ghép cặp được với 8/20 của security."
    )
    thieu_truong = [c for c in ca if TRUONG_CAU not in c]
    assert not thieu_truong, f"{len(thieu_truong)} ca thiếu trường `{TRUONG_CAU}`."

    # Mọi ca trong corpus phải là ca KHÔNG ĐƯỢC ĐỔI. Một ca `ky_vong` khác lọt
    # vào đây sẽ được chấm bằng bất biến sai — và vì nó nằm trong file đối
    # chứng nên không ai nghi ngờ.
    sai_ky_vong = [c["id"] for c in ca if c.get("ky_vong") != "khong_doi"]
    assert not sai_ky_vong, (
        f"Ca không phải `khong_doi` lọt vào corpus đối chứng: {sai_ky_vong}"
    )


# ===========================================================================
# TRỤC ĐO — cắm corpus vào là chạy
# ===========================================================================


def _ca_corpus() -> list:
    """Nạp corpus cho `parametrize`. Trả về 1 ca giữ chỗ khi chưa có corpus.

    ⚠️ KHÔNG trả về danh sách rỗng: `parametrize([])` làm pytest **im lặng bỏ
    qua** cả test, không skip, không báo — nó chỉ biến mất khỏi report. Đó đúng
    là dạng "test có mà chưa từng chạy" mà Luật 6 sinh ra để chặn, và nó còn
    kín hơn `skip` vì `skip` ít nhất còn hiện một dòng.
    """
    p = _tim_corpus()
    if p is None:
        return [pytest.param(None, id="chua-co-corpus")]

    out_items = []
    for i, c in enumerate(_nap_corpus(p)):
        marks = []
        if c.get("ket_qua_goc") == "chan_nham":
            marks.append(
                pytest.mark.xfail(
                    strict=True,
                    reason=(
                        f"S-01 (CHƯA VÁ) — {c.get('id')} là 1 trong 8 ca over-scrub đã "
                        "ghi nhận. ĐỪNG SỬA CHO XANH: khi B1/B2 land, strict=True tự "
                        "báo XPASS = lỗi, buộc gỡ marker và biến ca này thành "
                        "regression-gate thường trú. Đó là bước CÓ CHỦ ĐÍCH, không "
                        "phải dọn dẹp."
                    ),
                )
            )
        out_items.append(pytest.param(c, id=c.get("id", f"ca-{i}"), marks=marks))
    return out_items


@pytest.mark.parametrize("ca", _ca_corpus())
def test_ghi_chu_sach_phai_song_sot_nguyen_van(ca, client, sample_db):
    """Ghi chú KHÔNG chứa PII phải vào DB **NGUYÊN VĂN**, không sót một ký tự.

    VÌ SAO SO KHỚP TUYỆT ĐỐI chứ không "chứa từ khoá căn cứ": một assert dạng
    `"chính sách" in note_db` sẽ XANH cho `"từ chối [PERSON] theo chính sách"` —
    tức vẫn xanh trong khi tên đã bị xoá nhầm. Cùng bẫy `1b` (`CHUAN-VIET-TEST.md`):
    assertion khớp đúng cái chuỗi mà trạng thái hỏng vô tình còn giữ lại.

    Nếu về sau có CHUẨN HOÁ hợp lệ (vd cắt khoảng trắng thừa), nới assert này
    **kèm lý do dẫn nguồn** — đừng nới vì nó đang cản.
    """
    if ca is None:
        pytest.skip(
            "Chưa có corpus — xem `test_ly_do_skip_phai_that` để biết lý do này "
            "có thật hay là bug đường dẫn. CHƯA ĐO ĐƯỢC, không phải đạt."
        )

    gui = ca[TRUONG_CAU]
    _, resolution_id = _make_resolution(sample_db)
    resp = _tu_choi(client, resolution_id, note=gui)
    assert resp.status_code == 200, (
        f"Route từ chối trả {resp.status_code} — request chết TRƯỚC tầng cần đo. "
        "Xanh/đỏ ở đây đều vô nghĩa nếu note chưa từng tới điểm ghi (Luật 1)."
    )

    trong_db = _note_trong_db(sample_db, resolution_id)
    assert trong_db == gui, (
        f"[{ca.get('id')}] Ghi chú KHÔNG có PII bị ĐỔI khi ghi vào sổ kiểm toán.\n"
        f"  gửi đi : {gui!r}\n"
        f"  trong DB: {trong_db!r}\n"
        "Đây là over-scrub: mất căn cứ của một phán quyết HITL. Ngưỡng là 0/20 — "
        "đừng nới assert, đừng sửa corpus."
    )
