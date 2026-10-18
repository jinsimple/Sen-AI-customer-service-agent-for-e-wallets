"""BR-10 · BR-11 · BR-12 — CHECK constraint HITL phải CHẶN THẬT ở tầng DB.

Vì sao cần file này dù `tests/test_invariants.py` đã canh BR-10/BR-11:
INV-07 và INV-14 chỉ đọc `src/db/models.py` bằng AST và khẳng định
*CheckConstraint có tồn tại*. Đó là kiểm tra **sự hiện diện**, không phải
kiểm tra **hiệu lực**. Một constraint viết sai biểu thức (nhầm `OR` thành
`AND`, quên bọc ngoặc, so sánh nhầm cột) vẫn hiện diện đầy đủ và vẫn làm
INV-07/INV-14 xanh mướt — trong khi thực tế nó không chặn gì cả.

Ở đây ta ghi thẳng vào DB rồi đòi database NÉM LỖI. Đây là lớp phòng thủ
cuối cùng của HITL (ràng buộc cứng 1): kể cả khi toàn bộ tầng application bị
lách, database vẫn phải từ chối.

Contract: `contracts/resolution-state-machine.yaml` **v2.2.0**
§resolution.status (`yeu_cau_them` của 2 transition tới `approved`/`rejected`)
+ INV-07/INV-14 + §`invariant_db_maker_checker` (BR-12, ADR-020).

⚠️ BR-12 CHƯA CÓ SỐ INV. BR-10 có INV-07, BR-11 có INV-14, còn BR-12 thì
contract mới chỉ khai `invariant_db_maker_checker` mà chưa thêm mục vào danh
sách `invariants:` — nên `test_invariants.py` KHÔNG canh sự tồn tại của nó.
Nghĩa là hiện chỉ có HIỆU LỰC (file này) mà không có SỰ HIỆN DIỆN: ai xoá
constraint khỏi models.py thì file này đỏ, nhưng bộ ràng-buộc-cứng vẫn xanh —
lệch với cách hai BR anh em được canh. Đã báo PO; sửa contract là việc của họ,
tester không tự thêm INV.
"""
from __future__ import annotations

import datetime as dt

import pytest
from sqlalchemy.exc import IntegrityError

from src.db.models import Resolution
from src.services.complaint_intake import create_ticket_with_fraud_check
from src.tools.propose_resolution import propose_resolution


def _resolution_cho_ticket_moi(sample_db, *, created_by: str | None = "USR-CSKH") -> Resolution:
    """Dựng 1 resolution ở trạng thái `pending_approval` qua đúng đường dịch vụ
    thật (không tự chế bản ghi) — mọi test dưới đây chỉ đổi trạng thái từ đó.

    `created_by` mặc định là **CSKH, không phải supervisor**: mọi test ở đây
    duyệt/từ chối bằng `USR-SUP`, nên để supervisor làm người đề xuất sẽ khiến
    BR-12 chặn và test đỏ vì lý do KHÁC với lý do nó đang kiểm. Ca nào cần thử
    chính BR-12 thì truyền `created_by="USR-SUP"` một cách minh thị.

    `created_by=None` mô phỏng **dòng cũ** (trước migration `b2c3d4e5f6a7`) —
    hợp lệ và cần thiết cho ca 6 của bảng chân trị. Tham số của
    `propose_resolution` là bắt buộc-nhưng-nhận-None, đúng thiết kế: người gọi
    phải RA QUYẾT ĐỊNH minh thị, thay vì lỡ tay sinh thêm dòng NULL mới —
    mỗi dòng NULL mới là một dòng BR-12 không ràng được (F-17)."""
    created = create_ticket_with_fraud_check(
        sample_db, user_id="USR-A", complaint_type="wrong_recipient", scope="internal_wallet",
        description_raw="test check constraint", trans_id="TXN-0001",
    )
    sample_db.commit()
    r = propose_resolution(
        sample_db, ticket_id=created["ticket_id"], action_type="refund_to_wallet",
        rationale="test", amount=270_000, created_by=created_by,
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
    for column, val in day_du.items():
        setattr(res, column, val)

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
    for column, val in day_du.items():
        setattr(res, column, val)

    with pytest.raises(IntegrityError):
        sample_db.commit()
    sample_db.rollback()


# --------------------------------------------------------------------------
# BR-12 (ADR-020) — maker-checker: người đề xuất KHÔNG được tự duyệt
# --------------------------------------------------------------------------


def test_br12_nguoi_de_xuat_khong_duoc_tu_duyet_chinh_minh(sample_db):
    """Ràng buộc cứng 1 ở dạng tinh vi nhất: HITL vẫn có thể bị rỗng nghĩa dù
    mọi cổng đều đúng.

    Cửa mở là CÓ THẬT, không phải giả định: route đề xuất cho phép cả `cskh`
    LẪN `supervisor`, còn route duyệt yêu cầu `supervisor` — nên một supervisor
    đi trọn được cả hai đầu. Khi đó "có người thứ hai xem lại" chỉ còn là một
    thao tác hai bước của cùng một người, mà mọi test quyền hạn vẫn xanh vì
    không ai vượt quyền cả.
    """
    res = _resolution_cho_ticket_moi(sample_db)
    res.created_by = "USR-SUP"
    sample_db.commit()

    res.status = "approved"
    res.approved_by = "USR-SUP"  # ĐÚNG người đã đề xuất
    res.approved_at = dt.datetime.utcnow()

    with pytest.raises(IntegrityError):
        sample_db.commit()
    sample_db.rollback()


def test_br12_nguoi_khac_duyet_thi_ghi_duoc(sample_db):
    """Mặt ngược: BR-12 chỉ được chặn ĐÚNG ca trùng người.

    Thiếu ca này thì một biểu thức viết sai (vd `approved_by = created_by` thay
    vì `!=`, hoặc quên bọc ngoặc) vẫn làm test trên xanh — trong khi nó đang
    chặn mọi lượt duyệt hợp lệ.
    """
    res = _resolution_cho_ticket_moi(sample_db)
    res.created_by = "USR-CSKH"
    sample_db.commit()

    res.status = "approved"
    res.approved_by = "USR-SUP"  # người KHÁC
    res.approved_at = dt.datetime.utcnow()
    sample_db.commit()

    assert sample_db.get(Resolution, res.resolution_id).status == "approved"


def test_br12_created_by_rong_thi_khong_bi_rang(sample_db):
    """Điều kiện NULL không phải kẽ hở — nó là lựa chọn có chủ đích, và phải
    còn hiệu lực để dữ liệu cũ ghi được.

    `created_by` nullable VĨNH VIỄN: resolution tạo trước khi có cột này không
    có cách nào biết ai đề xuất, mà đoán một cái tên vào sổ kiểm toán còn tệ
    hơn để trống. CHECK vô điều kiện sẽ vỡ trên chính các dòng đó.

    ⚠️ ĐỌC KÈM `canh_bao_hieu_luc` của contract: 10/10 resolution hiện có đều
    `created_by IS NULL`, nên **không dòng nào đang bị BR-12 ràng**. Sự TỒN TẠI
    của constraint KHÔNG phải bằng chứng dữ liệu cũ đã sạch — nó chỉ bắt đầu
    bảo vệ từ các resolution tạo qua route mới.
    """
    res = _resolution_cho_ticket_moi(sample_db, created_by=None)
    assert res.created_by is None, "Fixture phải mô phỏng dòng chưa có created_by"

    res.status = "approved"
    res.approved_by = "USR-SUP"
    res.approved_at = dt.datetime.utcnow()
    sample_db.commit()

    assert sample_db.get(Resolution, res.resolution_id).status == "approved"


# --- BR-12 mở rộng sang nhánh TỪ CHỐI (F-18, contract v2.3.0) --------------
#
# Ánh xạ 1-1 với BẢNG CHÂN TRỊ 6 CA của security
# (`docs/security/review-ADR-020-BR-12-maker-checker.md` §6) — cố ý dùng CHUNG
# bộ ca để tester/coder/security đo bằng CÙNG MỘT THƯỚC, không mỗi người một
# cách hiểu:
#
#   1. c=X, chưa duyệt/từ chối  -> cho phép : test_br12_moi_de_xuat_chua_quyet...
#   2. c=X, a=X  TỰ DUYỆT       -> CHẶN     : test_br12_nguoi_de_xuat_khong_duoc_tu_duyet...
#   3. c=X, a=Y  duyệt đúng     -> cho phép : test_br12_nguoi_khac_duyet_thi_ghi_duoc
#   4. c=X, r=X  TỰ TỪ CHỐI     -> CHẶN     : test_br12_nguoi_de_xuat_khong_duoc_tu_tu_choi
#   5. c=X, r=Y  từ chối đúng   -> cho phép : test_br12_nguoi_khac_tu_choi_thi_ghi_duoc
#   6. c=NULL   (dòng cũ)       -> cho phép : test_br12_created_by_rong_thi_khong_bi_rang


def test_br12_moi_de_xuat_chua_quyet_thi_ghi_duoc(sample_db):
    """Ca 1 — trạng thái thường gặp nhất phải không bị vướng gì.

    Một resolution vừa trình, chưa ai duyệt cũng chưa ai từ chối, thì BR-12
    không có gì để nói. Ca này rẻ nhưng cần: biểu thức dạng C có hai nhánh
    `IS NULL`, và chính hai nhánh đó là chỗ dễ viết hỏng nhất — hỏng thì mọi
    đề xuất mới đều bị DB chặn ngay từ lúc trình.
    """
    res = _resolution_cho_ticket_moi(sample_db)
    res.created_by = "USR-CSKH"
    sample_db.commit()

    assert sample_db.get(Resolution, res.resolution_id).status == "pending_approval"


def test_br12_nguoi_de_xuat_khong_duoc_tu_tu_choi(sample_db):
    """Ca 4 — nhánh TỪ CHỐI, phần F-18 vừa mở rộng.

    Vì sao từ chối cũng cần maker-checker dù nó KHÔNG chạm tiền: `reject_reason`
    là đầu vào của vòng học Phase 2. Một người vừa trình vừa tự bác đề xuất của
    chính mình có thể bơm thẳng nhãn `la_tin_hieu_hoc` vào phễu mà không ai
    xem lại — tức là tự tay dạy bộ đo. Ảnh hưởng không nằm ở một giao dịch, nó
    nằm ở chính cái thước dùng để chấm mọi giao dịch sau đó.
    """
    res = _resolution_cho_ticket_moi(sample_db)
    res.created_by = "USR-SUP"
    sample_db.commit()

    res.status = "rejected"
    res.reject_reason = "thieu_can_cu"
    res.rejected_by = "USR-SUP"  # ĐÚNG người đã đề xuất
    res.rejected_at = dt.datetime.utcnow()

    with pytest.raises(IntegrityError):
        sample_db.commit()
    sample_db.rollback()


def test_br12_nguoi_khac_tu_choi_thi_ghi_duoc(sample_db):
    """Ca 5 — mặt ngược của ca 4: chỉ chặn ĐÚNG lúc trùng người.

    Cần vì cùng lý do đã cần ở nhánh duyệt: một biểu thức viết sai (quên nhánh
    `IS NULL`, hoặc so nhầm cột) sẽ chặn luôn mọi lượt từ chối hợp lệ — và khi
    đó sếp không từ chối được đề xuất nào nữa, một sự cố nặng hơn hẳn thứ
    BR-12 định ngăn.
    """
    res = _resolution_cho_ticket_moi(sample_db)
    res.created_by = "USR-CSKH"
    sample_db.commit()

    res.status = "rejected"
    res.reject_reason = "sai_so_lieu"
    res.rejected_by = "USR-SUP"  # người KHÁC
    res.rejected_at = dt.datetime.utcnow()
    sample_db.commit()

    lai = sample_db.get(Resolution, res.resolution_id)
    assert lai.status == "rejected" and lai.rejected_by == "USR-SUP"
