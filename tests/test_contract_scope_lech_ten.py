"""`scope` — contract và CHECK constraint LỆCH cả SỐ LƯỢNG lẫn HỆ TÊN.

## Vì sao lỗ này lọt qua 23 invariant

`tests/test_invariants.py` introspect app đang chạy rồi so với `contracts/` —
và nó bắt được rất nhiều thứ. Nó **không** bắt được cái này, vì hai bên **đặt
tên bằng hai ngôn ngữ**:

    contracts/authority-matrix.yaml   noi_bo_vi · tu_ngan_hang · ra_ngan_hang
    models.py CHECK ck_complaints_scope
                                      internal_wallet · from_bank · to_bank · unknown

Không phép so máy móc nào nối được `noi_bo_vi` với `internal_wallet`. Nên khi
`unknown` được thêm vào CHECK, **không có gì đỏ** — và contract tiếp tục mô tả
một hệ ba giá trị trong khi mã chạy trên bốn.

> **Hai artefact cùng mô tả một thứ nhưng bằng hai hệ tên thì không so được tự
> động — và "không so được" trông y hệt "đã so, khớp".** Cả hai đều im lặng.

Phát hiện ra nó cần một sự cố: 17/08, nhánh fallback ghi `scope="internal_wallet"`
bịa vào bảng bằng chứng
(`eval/FINDING-fallback-bia-scope-17-08.md`). Đi tìm **giá trị đúng để vá** thì
lộ ra rằng giá trị đúng — `unknown` — **không tồn tại trong contract**.

## Bảng nối phải nằm ở CONTRACT, không nằm ở đây

Bảng dưới đây là **chỗ vá tạm**. Nó ở sai chỗ về nguyên tắc: một bảng nối sống
trong test thì test trở thành nguồn sự thật thứ ba, và hiến pháp §3 nói nguồn
sự thật là `contracts/`.

**Cách sửa đúng** (cần quy trình §3: contract → ADR → PO duyệt → `--update` →
bump version → rồi code): mỗi `scope` trong contract khai kèm **giá trị mã**
của nó, ví dụ `noi_bo_vi: {mo_ta: …, gia_tri_ma: internal_wallet}`. Khi đó phép
so là máy móc và bảng nối này biến mất.

Tôi **không** tự sửa contract — đó là vùng của tech-lead sau khi PO duyệt.
"""
from __future__ import annotations

import pathlib
import re

import pytest
import yaml

GOC = pathlib.Path(__file__).resolve().parent.parent

# Bảng nối TẠM. Xem docstring: chỗ đúng của nó là contracts/.
NOI_TEN = {
    "noi_bo_vi": "internal_wallet",
    "tu_ngan_hang": "from_bank",
    "ra_ngan_hang": "to_bank",
}


def _scope_trong_contract() -> set[str]:
    c = yaml.safe_load((GOC / "contracts" / "authority-matrix.yaml").read_text(encoding="utf-8"))
    ra: set[str] = set()

    def di(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "scopes" and isinstance(v, dict):
                                    ra.update(v)
                di(v)
        elif isinstance(o, list):
            for x in o:
                di(x)

    di(c)
    return ra


TEN_CHECK = "ck_complaints_scope"


def _scope_trong_CHECK() -> set[str]:
    """Đọc CHECK constraint qua helper CÓ SẴN của bộ invariant — KHÔNG cần app chạy.

    ## 🔴 Bản đầu của hàm này SAI, và cách nó sai đáng ghi lại

    Tôi viết `re.search(r"scope\\s+IN\\s*\\(([^)]*)\\)", src)` — regex đó bắt
    **lần khớp ĐẦU TIÊN trong file**, hoá ra là CHECK của một bảng khác. Kết
    quả: hàm trả **3** giá trị trong khi `ck_complaints_scope` thật có **4**.

    Hậu quả nếu tôi không chạy thử: test đếm-số-lượng **XANH** (3 = 3) và test
    xfail **XPASS** — tức bộ test báo *"contract và mã đã khớp"* đúng lúc chúng
    lệch. Một finding thật bị chính bộ test của tôi khoá lại.

    > Đo nhầm vật vẫn cho ra một con số **hợp lý**, và một con số hợp lý thì
    > không ai đi kiểm.

    Sửa: dùng `_check_constraints()` của `test_invariants.py` — nó đọc bằng
    **AST** và tra theo **TÊN** constraint, nên không thể ăn nhầm bảng khác.
    Đây cũng là lý do dùng lại thay vì viết mới: bộ invariant đã giải đúng bài
    này rồi.

    Cố ý **không** `docker exec`: một test canh contract phải chạy được trên
    máy CI sạch. Nếu nó chỉ chạy khi có hạ tầng sống thì nó sẽ `skip` im lặng
    đúng lúc cần nhất (Luật 6).
    """
    from tests.test_invariants import _check_constraints

    bt = _check_constraints().get(TEN_CHECK)
    assert bt, (
        f"không tìm thấy CheckConstraint tên {TEN_CHECK!r}. "
        "Đổi tên constraint mà không sửa test này = test canh một vật không còn tồn tại."
    )
    m = re.search(r"IN\s*\(([^)]*)\)", bt)
    assert m, f"{TEN_CHECK} không có dạng 'IN (...)': {bt[:120]}"
    return {x.strip().strip("'\"") for x in m.group(1).split(",") if x.strip()}


@pytest.mark.xfail(
    strict=True,
    reason="CÙNG FINDING MỞ với test dưới — contract khai 3 scope, CHECK có 4. "
    "Đánh dấu xfail để CI không đỏ vì một nợ contract đã biết và đã báo, KHÔNG "
    "phải để giấu nó: strict=True nên khi contract khai đủ, test này XPASS và "
    "buộc người sửa phải quay lại gỡ dấu.",
)
def test_contract_va_CHECK_khai_cung_so_luong_scope():
    """Số lượng phải khớp — phép so RẺ NHẤT, không cần bảng nối.

    Test này KHÔNG phụ thuộc `NOI_TEN`, nên nó vẫn đúng kể cả khi bảng nối sai.
    Đó là lý do nó tách khỏi test dưới: hai mệnh đề, hai đột biến (Luật 16).
    """
    ct, ck = _scope_trong_contract(), _scope_trong_CHECK()
    assert len(ct) == len(ck), (
        f"contract khai {len(ct)} scope {sorted(ct)}\n"
        f"CHECK khai      {len(ck)} scope {sorted(ck)}\n"
        "Hai artefact cùng mô tả một thứ mà số lượng khác nhau."
    )


@pytest.mark.xfail(
    strict=True,
    reason="FINDING MỞ 17/08 — 'unknown' có trong CHECK nhưng KHÔNG khai trong "
    "contracts/authority-matrix.yaml. Đây là giá trị mà mô tả tool create_ticket "
    "BẮT BUỘC dùng khi không tra ra giao dịch, tức nó là giá trị nghiệp vụ thật "
    "chứ không phải giá trị kỹ thuật. Sửa cần quy trình §3 (contract → ADR → PO "
    "duyệt). Khi contract khai đủ, test này CHUYỂN SANG XANH và xfail(strict) sẽ "
    "đỏ — đó là tín hiệu để gỡ dấu xfail, không phải lỗi mới.",
)
def test_moi_gia_tri_trong_CHECK_deu_duoc_contract_khai():
    ct, ck = _scope_trong_contract(), _scope_trong_CHECK()
    da_khai = {NOI_TEN[k] for k in ct if k in NOI_TEN}
    thieu = ck - da_khai
    assert not thieu, (
        f"CHECK cho phép {sorted(thieu)} mà contract KHÔNG khai.\n"
        f"  contract: {sorted(ct)}  → qua bảng nối → {sorted(da_khai)}\n"
        f"  CHECK   : {sorted(ck)}\n"
        "Mã chạy trên một tập giá trị rộng hơn tập contract mô tả."
    )


def test_bang_noi_khong_tu_bia_ra_ten():
    """Bảng nối chỉ được chứa khoá CÓ THẬT ở cả hai phía.

    Không có test này, một khoá gõ sai trong `NOI_TEN` sẽ im lặng làm hai test
    trên đọc sai — và chúng vẫn xanh/đỏ như thường, chỉ là về một vật khác.
    """
    ct, ck = _scope_trong_contract(), _scope_trong_CHECK()
    la = set(NOI_TEN) - ct
    assert not la, f"bảng nối có khoá KHÔNG có trong contract: {sorted(la)}"
    la2 = set(NOI_TEN.values()) - ck
    assert not la2, f"bảng nối trỏ tới giá trị KHÔNG có trong CHECK: {sorted(la2)}"
