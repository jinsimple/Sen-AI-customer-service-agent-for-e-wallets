"""Canh TÍNH TOÀN VẸN của `eval/bo_ca_luot_don.json` — 0 lượt LLM.

Bộ ca này quyết định ngưỡng của lớp định tuyến. Nếu nó lệch khỏi thứ đã băm,
hoặc lời khai trong nó không đúng với nội dung nó, thì mọi con số rút từ nó vô
giá trị — và **không có gì đỏ** để báo.

Đặc biệt canh **đơn vị đếm**: PO đã sửa một lần con số bộ ca ÂM (120 ca nhưng
**124 câu** — router chấm từng câu). Cổng viết `== 120` sẽ bỏ sót 4 câu và
**vẫn xanh**. Con số đúng, tập hợp sai.
"""
from __future__ import annotations

import hashlib
import json

from tests._eval_co_mat import doi_hoi_tep

# Thiếu `eval/` ⟹ SKIP KÈM LÝ DO, không được thành `Interrupted` (xem
# tests/_eval_co_mat.py — trong container `.dockerignore` loại eval/ CÓ CHỦ ĐÍCH).
FILE = doi_hoi_tep("bo_ca_luot_don.json")
BO = json.loads(FILE.read_text(encoding="utf-8"))


def test_bam_nhan_khop_noi_dung():
    """Nhãn BẤT ĐỘNG từ giây công bố băm — test này là thứ thi hành điều đó."""
    write = BO["bam_nhan"]
    # bỏ CẢ HAI khoá — `thuat_toan_bam` cố ý nằm NGOÀI phần được băm, để lời
    # khai thuật toán thêm vào được mà KHÔNG đổi băm đã công bố.
    d = {k: v for k, v in BO.items() if k not in ("bam_nhan", "thuat_toan_bam")}
    tinh = hashlib.sha256(
        json.dumps(d, ensure_ascii=False, indent=1, sort_keys=True).encode()
    ).hexdigest()[:12]
    assert write == tinh, (
        f"băm ghi {write} ≠ băm tính lại {tinh}. Bộ ca đã đổi sau khi công bố băm.\n"
        "Nếu đổi là cố ý: ghi băm cũ vào bam_cu_da_thay rồi băm lại (tiền lệ v4)."
    )


def test_don_vi_dem_dung_nhu_LOI_KHAI():
    """Lời khai '20 ca = 20 câu' phải đúng với nội dung, không chỉ đúng trong văn bản."""
    ca = BO["ca"]
    assert len(ca) == 20, f"khai 20 ca, đếm được {len(ca)}"
    nhieu_cau = [c["id"] for c in ca if len(c["cau"].split("\n")) > 1]
    assert not nhieu_cau, (
        f"ca có nhiều dòng: {nhieu_cau} — lời khai 'mỗi ca đúng MỘT câu' SAI, "
        "và mẫu số của mọi cổng dùng bộ này sẽ lệch."
    )


def test_moi_ca_co_nhan_hop_le_va_KHONG_bo_trong():
    valid = {"nhe", "day_du"}
    xau = [c["id"] for c in BO["ca"] if c.get("ky_vong") not in valid]
    assert not xau, f"ca có nhãn ngoài {valid}: {xau}"
    thieu = [c["id"] for c in BO["ca"] if not str(c.get("vi_sao", "")).strip()]
    assert not thieu, f"ca không nêu LÝ DO của nhãn: {thieu} — nhãn không bác được"


def test_id_khong_trung():
    ids = [c["id"] for c in BO["ca"]]
    assert len(ids) == len(set(ids)), f"ID trùng: {sorted({i for i in ids if ids.count(i) > 1})}"


def test_nhan_CO_DIEU_KIEN_phai_khai_du_dieu_kien_va_nhan_lat():
    """Một nhãn phụ thuộc TÍNH CHẤT CÀI ĐẶT không phải nhãn đặc tả.

    DON-08 được PO phán `nhe`, nhưng chỉ đúng NẾU đường nhẹ được phép hỏi lại và
    không được trả lời nghiệp vụ. Nếu cài đặt không có tính chất đó, nhãn phải
    lật sang `day_du`.

    > **Nhãn như vậy có thể im lặng trở thành SAI khi cài đặt đổi — và bộ ca vẫn
    > xanh.** Nó là `hiện-diện ≠ hiệu-lực` áp cho một cái NHÃN.

    Test này không kiểm được điều kiện (chưa có cài đặt). Nó kiểm thứ kiểm được
    ngay: **điều kiện phải được KHAI, và nhãn-nếu-điều-kiện-sai phải được khai**.
    Thiếu một trong hai, người sau sẽ đọc nhãn như một sự thật vô điều kiện.
    """
    for c in BO["ca"]:
        dk = c.get("🔴_NHAN_CO_DIEU_KIEN")
        if not dk:
            continue
        assert str(dk.get("dieu_kien", "")).strip(), f"{c['id']}: nhãn có điều kiện mà KHÔNG khai điều kiện"
        lat = str(dk.get("nhan_neu_dieu_kien_SAI", "")).strip()
        assert lat, f"{c['id']}: không khai NHÃN LẬT khi điều kiện sai"
        assert lat != c["ky_vong"], (
            f"{c['id']}: nhãn lật ({lat}) trùng nhãn hiện tại ({c['ky_vong']}) — "
            "nếu điều kiện không đổi được nhãn thì nó không phải điều kiện."
        )
        assert c.get("nguon_nhan"), f"{c['id']}: nhãn có điều kiện phải khai NGUỒN (ai phán)"


def test_bam_phai_khai_TEN_THUAT_TOAN():
    """Một chuỗi hex 12 ký tự KHÔNG tự khai nó sinh ra từ đâu.

    17/08: cùng một file 6.305 byte cho `md5 = 1edd51dff555` và
    `sha256 = 742df94b195a`. Hai người đọc hai con số, **nhìn giống hệt nhau**,
    và không ai kiểm — vì cả hai đều là 12 ký tự hex.

    Đây là lần thứ BA trong ngày cùng lớp (`4.862 vs 4.334` · `120 ca vs 124
    câu` · và cái này), và lần này nó **lọt qua chính quy ước đặt ra để chặn
    nó**: quy ước ghi "sha256, 12 ký tự đầu", một bên dùng md5, con số vẫn
    trông hợp lệ.

    > **`1edd51dff555` không phải một băm. `md5:1edd51dff555` mới là.**
    """
    declared = str(BO.get("thuat_toan_bam", "")).strip()
    assert declared, (
        "có `bam_nhan` mà KHÔNG khai thuật toán. Một chuỗi hex không tự khai "
        "nguồn gốc — người sau sẽ băm lại bằng thuật toán khác và thấy lệch, "
        "hoặc tệ hơn: thấy giống rồi tin nhầm."
    )
    assert any(x in declared.lower() for x in ("sha256", "md5", "sha1", "blake")), (
        f"lời khai không nêu TÊN thuật toán: {declared!r}"
    )
    assert "bam_nhan" in declared and "thuat_toan_bam" in declared, (
        "lời khai phải nêu RÕ khoá nào bị loại trước khi băm — thiếu, người "
        "sau không tái lập được con số dù biết thuật toán."
    )
