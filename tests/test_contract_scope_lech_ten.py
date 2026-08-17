"""`scope` — contract ↔ CHECK constraint, so bằng MÁY qua `gia_tri_ma`.

## Bảng nối tạm đã bị XOÁ, và đó là kết quả mong muốn

Bản 17/08 sáng của file này mang một **bảng nối viết tay** (`noi_bo_vi` →
`internal_wallet`…) vì hai artefact đặt tên bằng **hai ngôn ngữ**:

    contracts/authority-matrix.yaml   noi_bo_vi · tu_ngan_hang · ra_ngan_hang
    ck_complaints_scope   internal_wallet · from_bank · to_bank · unknown

Không phép so máy móc nào nối được hai hệ tên đó. Nên khi `unknown` được thêm
vào CHECK (11/08), **không có gì đỏ** — và nó **sống sáu ngày ngoài mọi tài
liệu**. Đó cũng là lý do `flag_human_handoff` ghi cứng `internal_wallet` mà
không cổng nào kêu.

> **Hai artefact cùng mô tả một thứ nhưng bằng hai hệ tên thì không so được tự
> động — và "không so được" trông y hệt "đã so, khớp".** Cả hai đều im lặng.

Bản cũ đã ghi rằng bảng nối đó **ở sai chỗ về nguyên tắc**: một bảng nối sống
trong test biến test thành **nguồn sự thật thứ ba**, trong khi hiến pháp §3 nói
nguồn sự thật là `contracts/`. Cách sửa đúng — mỗi scope khai kèm `gia_tri_ma`
— nay đã vào contract (ADR-029 mục 4, PO thật duyệt, `b831a9e`).

**Bảng nối biến mất khỏi file này.** Đó là dấu hiệu bản vá đúng chỗ: nó không
thêm một lớp, nó **gỡ** một lớp.

## 🔴 HAI CHECK KHÁC NHAU LÀ ĐÚNG — đừng "sửa cho đều"

    complaints    scope IN ('internal_wallet','from_bank','to_bank','unknown')
    transactions  scope IN ('internal_wallet','from_bank','to_bank')

`transactions` **luôn biết** phạm vi thật của nó nên `unknown` vô nghĩa ở đó.
Contract nói được điều này qua `rang_buoc_db: ck_complaints_scope` — **chỉ**
`khong_ro` mang trường đó.

⟹ So **theo TÊN RÀNG BUỘC**, không so *"mọi scope phải có mặt trong mọi bảng"*.
Cách thứ hai đỏ vĩnh viễn và **đỏ sai** — và một cổng đỏ sai sẽ bị ai đó tắt.
"""
from __future__ import annotations

import pathlib
import re

import yaml

GOC = pathlib.Path(__file__).resolve().parent.parent
CHECK_COMPLAINTS = "ck_complaints_scope"
CHECK_TRANSACTIONS = "ck_transactions_scope"


def _scopes_contract() -> dict[str, dict]:
    c = yaml.safe_load((GOC / "contracts" / "authority-matrix.yaml").read_text(encoding="utf-8"))

    def di(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "scopes" and isinstance(v, dict):
                    return v
                r = di(v)
                if r:
                    return r
        elif isinstance(o, list):
            for x in o:
                r = di(x)
                if r:
                    return r
        return None

    s = di(c)
    assert s, "không tìm thấy khoá `scopes` trong authority-matrix.yaml"
    return s


def _gia_tri_trong_CHECK(ten: str) -> set[str]:
    """Đọc CHECK theo TÊN, qua helper AST có sẵn của bộ invariant.

    Tra theo **danh tính**, không theo **vị trí**. Bản đầu của hàm này dùng
    `re.search(r"scope IN (...)")` — nó bắt lần khớp **đầu tiên trong file**,
    hoá ra là CHECK của một bảng khác, và trả **3** giá trị thay vì 4. Nếu tôi
    không chạy thử, bộ test đã báo *"contract và mã đã khớp"* **đúng lúc chúng
    lệch**.
    """
    from tests.test_invariants import _check_constraints

    bt = _check_constraints().get(ten)
    assert bt, f"không tìm thấy CheckConstraint tên {ten!r}"
    m = re.search(r"IN\s*\(([^)]*)\)", bt)
    assert m, f"{ten} không có dạng 'IN (...)': {bt[:120]}"
    return {x.strip().strip("'\"") for x in m.group(1).split(",") if x.strip()}


def test_moi_scope_contract_khai_du_gia_tri_ma():
    """Thiếu `gia_tri_ma` thì mọi phép so bên dưới quay về đoán mò."""
    thieu = [k for k, v in _scopes_contract().items()
             if not isinstance(v, dict) or not str(v.get("gia_tri_ma", "")).strip()]
    assert not thieu, (
        f"scope thiếu `gia_tri_ma`: {thieu}\n"
        "Thiếu trường này thì contract và CHECK lại là hai hệ tên không nối được, "
        "và ta quay lại đúng chỗ `unknown` sống sáu ngày ngoài tài liệu."
    )


def test_contract_va_CHECK_khai_CUNG_MOT_TAP():
    """🔴 Phép so chính — máy đọc, không bảng nối viết tay."""
    ct = {v["gia_tri_ma"] for v in _scopes_contract().values()}
    ck = _gia_tri_trong_CHECK(CHECK_COMPLAINTS)
    assert ct == ck, (
        f"contract khai {sorted(ct)}\n{CHECK_COMPLAINTS} cho phép {sorted(ck)}\n"
        f"  chỉ contract: {sorted(ct - ck)}  ·  chỉ CHECK: {sorted(ck - ct)}\n"
        "Mã và tài liệu đang mô tả hai tập giá trị khác nhau."
    )


def test_scope_gan_rang_buoc_RIENG_thi_chi_o_bang_do():
    """`khong_ro` khai `rang_buoc_db: ck_complaints_scope` ⟹ CHỈ hợp lệ ở đó.

    Đây là vế chống *"sửa cho đều"*: `transactions` **cố ý** không có `unknown`,
    và một cổng ngây thơ đòi mọi scope có mặt ở mọi bảng sẽ đỏ vĩnh viễn — rồi
    bị tắt. Test này khoá đúng ý định đó lại bằng máy, thay vì để nó sống trong
    một câu chú thích không ai chạy.
    """
    rieng = {v["gia_tri_ma"]: v["rang_buoc_db"]
             for v in _scopes_contract().values() if v.get("rang_buoc_db")}
    assert rieng, "không scope nào khai `rang_buoc_db` — nếu đúng vậy, xoá test này"
    khac = _gia_tri_trong_CHECK(CHECK_TRANSACTIONS)
    for gt, ten in rieng.items():
        assert ten == CHECK_COMPLAINTS, f"`{gt}` khai ràng buộc lạ: {ten}"
        assert gt not in khac, (
            f"`{gt}` khai CHỈ hợp lệ ở {ten}, nhưng nó CÓ trong {CHECK_TRANSACTIONS}. "
            "Contract và CHECK bất đồng về PHẠM VI của giá trị, không chỉ về tập giá trị."
        )


def test_scope_KHONG_gan_rang_buoc_thi_co_o_CA_HAI_bang():
    """Vế đối chứng của test trên (Luật 2) — chứng minh nó không chặn bừa.

    Ba scope **không** khai `rang_buoc_db` phải có mặt ở **cả hai** CHECK. Thiếu
    ca này, một `rang_buoc_db` gõ nhầm vào cả bốn scope vẫn làm test trên xanh,
    và ta mất khả năng phân biệt *"cố ý chỉ ở một bảng"* với *"lỡ thiếu ở bảng
    kia"*.
    """
    chung = {v["gia_tri_ma"] for v in _scopes_contract().values() if not v.get("rang_buoc_db")}
    assert chung, "mọi scope đều khai rang_buoc_db — bất thường, đọc lại contract"
    for ten in (CHECK_COMPLAINTS, CHECK_TRANSACTIONS):
        thieu = chung - _gia_tri_trong_CHECK(ten)
        assert not thieu, f"scope dùng chung {sorted(thieu)} VẮNG ở {ten}"
