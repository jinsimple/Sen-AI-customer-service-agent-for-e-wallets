"""BR-10 · BR-11 — CHECK constraint HITL phải CHẶN THẬT ở tầng DB.

Vì sao cần file này dù `tests/test_invariants.py` đã canh BR-10/BR-11:
INV-07 và INV-14 chỉ đọc `src/db/models.py` bằng AST và khẳng định
*CheckConstraint có tồn tại*. Đó là kiểm tra **sự hiện diện**, không phải
kiểm tra **hiệu lực**. Một constraint viết sai biểu thức (nhầm `OR` thành
`AND`, quên bọc ngoặc, so sánh nhầm cột) vẫn hiện diện đầy đủ và vẫn làm
INV-07/INV-14 xanh mướt — trong khi thực tế nó không chặn gì cả.

Ở đây ta ghi thẳng vào DB rồi đòi database NÉM LỖI. Đây là lớp phòng thủ
cuối cùng của HITL (ràng buộc cứng 1): kể cả khi toàn bộ tầng application bị
lách, database vẫn phải từ chối.

Contract: `contracts/resolution-state-machine.yaml` v2.1.0 §resolution.status
(`yeu_cau_them` của 2 transition tới `approved`/`rejected`) + INV-07/INV-14.
"""
from __future__ import annotations

import datetime as dt

import pytest
from sqlalchemy.exc import IntegrityError

from src.db.models import Resolution
from src.services.complaint_intake import create_ticket_with_fraud_check
from src.tools.propose_resolution import propose_resolution


def _resolution_cho_ticket_moi(sample_db) -> Resolution:
    """Dựng 1 resolution ở trạng thái `pending_approval` qua đúng đường dịch vụ
    thật (không tự chế bản ghi) — mọi test dưới đây chỉ đổi trạng thái từ đó."""
    created = create_ticket_with_fraud_check(
        sample_db, user_id="USR-A", complaint_type="wrong_recipient", scope="internal_wallet",
        description_raw="test check constraint", trans_id="TXN-0001",
    )
    sample_db.commit()
    r = propose_resolution(
        sample_db, ticket_id=created["ticket_id"], action_type="refund_to_wallet",
        rationale="test", amount=270_000,
    )
    sample_db.commit()
    return sample_db.get(Resolution, r["resolution_id"])


# --------------------------------------------------------------------------
# BR-11 (INV-14, ADR-019) — từ chối phải có lý do + người + thời điểm
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thieu",
    ["reject_reason", "rejected_by", "rejected_at"],
    ids=["thieu_ly_do", "thieu_nguoi_tu_choi", "thieu_thoi_diem"],
)
def test_br11_rejected_thieu_bat_ky_truong_nao_deu_bi_db_chan(sample_db, thieu):
    """Thiếu BẤT KỲ trường nào trong 3 → DB phải ném IntegrityError.

    Kiểm từng trường riêng (không gộp 1 test "thiếu hết") vì lỗi thật hay gặp
    là constraint chỉ ép 1-2 trường: gộp lại thì test vẫn xanh nhờ trường được
    ép, còn trường bị bỏ sót không ai biết.
    """
    day_du = {
        "reject_reason": "sai_so_lieu",
        "rejected_by": "USR-SUP",
        "rejected_at": dt.datetime.utcnow(),
    }
    day_du[thieu] = None

    res = _resolution_cho_ticket_moi(sample_db)
    res.status = "rejected"
    for cot, gia_tri in day_du.items():
        setattr(res, cot, gia_tri)

    with pytest.raises(IntegrityError):
        sample_db.commit()
    sample_db.rollback()


def test_br11_rejected_du_ca_ba_truong_thi_ghi_duoc(sample_db):
    """Mặt còn lại của cùng một ràng buộc: đường HỢP LỆ phải chạy được.

    Thiếu test này thì một constraint viết quá chặt (chặn cả trường hợp đúng)
    vẫn làm mọi test "phải bị chặn" ở trên xanh — tức là ta chỉ chứng minh
    được nó chặn, chưa chứng minh được nó không chặn nhầm.
    """
    res = _resolution_cho_ticket_moi(sample_db)
    res.status = "rejected"
    res.reject_reason = "thieu_can_cu"
    res.rejected_by = "USR-SUP"
    res.rejected_at = dt.datetime.utcnow()
    sample_db.commit()

    lai = sample_db.get(Resolution, res.resolution_id)
    assert lai.status == "rejected"
    assert lai.reject_reason == "thieu_can_cu"


def test_br11_reject_reason_ngoai_taxonomy_bi_chan(sample_db):
    """Lý do từ chối phải thuộc enum — chuỗi tự do sẽ phá vòng học Phase 2.

    `la_tin_hieu_hoc` được tra theo TÊN lý do; một giá trị lạ không tra được
    cờ nào, nên case đó hoặc biến mất khỏi bộ ứng viên eval, hoặc lọt vào như
    mẫu không phân loại được. Cả hai đều làm hỏng thước đo.
    """
    res = _resolution_cho_ticket_moi(sample_db)
    res.status = "rejected"
    res.reject_reason = "sep_khong_thich"  # không có trong taxonomy ADR-019
    res.rejected_by = "USR-SUP"
    res.rejected_at = dt.datetime.utcnow()

    with pytest.raises(IntegrityError):
        sample_db.commit()
    sample_db.rollback()


# --------------------------------------------------------------------------
# BR-10 (INV-07) — đối xứng, trước nay CHƯA có test hiệu lực nào
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "thieu", ["approved_by", "approved_at"], ids=["thieu_nguoi_duyet", "thieu_thoi_diem"]
)
def test_br10_approved_thieu_nguoi_duyet_bi_db_chan(sample_db, thieu):
    """Ràng buộc cứng 1 (HITL tuyệt đối) ở tầng thấp nhất của hệ thống.

    Đây là câu trả lời cho câu hỏi kiểm toán "nếu ai đó UPDATE thẳng vào DB
    thì sao": database phải tự từ chối tạo ra một lệnh chạm tiền đã duyệt mà
    không có người duyệt.
    """
    day_du = {"approved_by": "USR-SUP", "approved_at": dt.datetime.utcnow()}
    day_du[thieu] = None

    res = _resolution_cho_ticket_moi(sample_db)
    res.status = "approved"
    for cot, gia_tri in day_du.items():
        setattr(res, cot, gia_tri)

    with pytest.raises(IntegrityError):
        sample_db.commit()
    sample_db.rollback()
