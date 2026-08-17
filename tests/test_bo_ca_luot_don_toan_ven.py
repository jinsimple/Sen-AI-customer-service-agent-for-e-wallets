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
import pathlib

FILE = pathlib.Path(__file__).resolve().parent.parent / "eval" / "bo_ca_luot_don.json"
BO = json.loads(FILE.read_text(encoding="utf-8"))


def test_bam_nhan_khop_noi_dung():
    """Nhãn BẤT ĐỘNG từ giây công bố băm — test này là thứ thi hành điều đó."""
    d = dict(BO)
    ghi = d.pop("bam_nhan")
    tinh = hashlib.sha256(
        json.dumps(d, ensure_ascii=False, indent=1, sort_keys=True).encode()
    ).hexdigest()[:12]
    assert ghi == tinh, (
        f"băm ghi {ghi} ≠ băm tính lại {tinh}. Bộ ca đã đổi sau khi công bố băm.\n"
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
    hop_le = {"nhe", "day_du"}
    xau = [c["id"] for c in BO["ca"] if c.get("ky_vong") not in hop_le]
    assert not xau, f"ca có nhãn ngoài {hop_le}: {xau}"
    thieu = [c["id"] for c in BO["ca"] if not str(c.get("vi_sao", "")).strip()]
    assert not thieu, f"ca không nêu LÝ DO của nhãn: {thieu} — nhãn không bác được"


def test_id_khong_trung():
    ids = [c["id"] for c in BO["ca"]]
    assert len(ids) == len(set(ids)), f"ID trùng: {sorted({i for i in ids if ids.count(i) > 1})}"
