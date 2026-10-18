"""Ca đối chứng "bẫy hợp nhất" cho FS-13 — PO giao gấp 25/08, chặn Coder.

> ✅ **0 lượt LLM** — chỉ DB tạm (`sample_db`/`db_session`, cùng fixture các
> file `tests/test_api/*.py` đã dùng). Không cần docker/Redis.

## Nguy cơ, nguyên văn từ PO

`FraudEngine.evaluate()` gọi lại ở lượt sau (sau khi khách trả lời câu sàng
lọc lừa đảo ⑨) với `tx=None` — [ĐO trực tiếp trên `scripts/fraud_engine.py`,
đọc control-flow, KHÔNG đọc điều kiện từng tín hiệu]: dòng `if tx is None:
return sorted(fired)` là **early return VÔ ĐIỀU KIỆN** — khi `tx=None`,
FS-01..08 và FS-12 **không có cách nào bật**, bất kể dữ liệu gì. Nếu hàm nhận
kết quả lượt sau **GÁN ĐÈ** (`complaint.fraud_signals = fired_moi`) thay vì
**HỢP NHẤT** (`union` với tín hiệu cũ), nó sẽ xoá sạch mọi tín hiệu đã bắt
lúc tạo vé — kể cả **FS-06**, tín hiệu DUY NHẤT đang escalate (ràng buộc cứng
5: gắn cờ nghi gian lận ≠ khoá ví, nhưng cờ đó phải SỐNG được để supervisor
thấy).

## Điểm móc — Coder cấp trực tiếp 25/08, CHƯA LAND lúc viết file này

    src/services/complaint_intake.py
    def hop_nhat_tin_hieu_gian_lan(
        session: Session, *, thread_id: str, utterance_text: str,
        them_ma: list[str] | None = None,
    ) -> list[str] | None

Dòng hợp nhất (Coder tự khai, đây là dòng cổng này canh):
    `gop = sorted(set(cu) | set(fired) | set(them_ma or []))`

Gọi với `tx=None, otp_disclosed=False` CỐ Ý bên trong hàm — `otp_disclosed`
truyền `False` KHÔNG được hạ cờ `FS-10` cũ vì union chỉ THÊM, không bao giờ
XOÁ.

🔴 Test này CHƯA CHẠY ĐƯỢC lúc land — hàm chưa tồn tại (`ImportError`), CỐ Ý,
cùng nếp `bo_ca_thu_slot_1b.json`/⑨: land TRƯỚC để Coder cài theo, đỏ ĐÚNG LÝ
DO cho tới khi hàm thật xuất hiện.
"""
from __future__ import annotations

import datetime as dt

import pytest
from sqlalchemy.orm import Session

from src.db.models import Complaint

pytest.importorskip(
    "src.services.complaint_intake",
    reason="hop_nhat_tin_hieu_gian_lan chưa land — xem docstring, đỏ ĐÚNG LÝ DO",
)
from src.services.complaint_intake import merge_fraud_signals  # noqa: E402


def _tao_ve_voi_fs06(session: Session, *, thread_id: str) -> Complaint:
    """Vé đã có sẵn FS-06 (giả lập kết quả `evaluate()` lượt TẠO vé, có `tx`)
    — KHÔNG cần dựng lại toàn bộ FraudEngine/LedgerIndex để trigger FS-06
    thật (đòi auth_session lệch giờ + số dư rút cạn 90%, nặng và không phải
    thứ ca này canh). Ca này canh HÀM HỢP NHẤT, không canh FraudEngine — tách
    hai mối lo, đúng nguyên tắc mỗi cổng chỉ khẳng định MỘT điều."""
    c = Complaint(
        complaint_id=f"CMP-TEST-{thread_id}",
        user_id="USR-A",
        type="wrong_recipient",
        scope="internal_wallet",
        status="investigating",
        priority="critical",  # tier_a (FS-06) -> priority_tier_a: critical, data/schema/fraud_signals.yaml
        description_raw="giao dịch đáng ngờ, đã bắt FS-06 lúc tạo vé",
        fraud_signals=["FS-06"],
        otp_disclosed=False,
        created_at=dt.datetime(2026, 8, 25, 10, 0, 0),
        thread_id=thread_id,
    )
    session.add(c)
    session.flush()
    return c


def test_hop_nhat_giu_nguyen_fs06_khi_goi_lai_voi_tx_none(sample_db: Session):
    """🔴 Ca gấp nhất — union PHẢI giữ FS-06 dù `evaluate()` lượt sau (tx=None)
    tự nó không bao giờ trả lại được FS-06."""
    thread_id = "THREAD-HOP-NHAT-1"
    _tao_ve_voi_fs06(sample_db, thread_id=thread_id)

    merged_items = merge_fraud_signals(
        sample_db, thread_id=thread_id, utterance_text="tôi tự gõ nhầm, không ai hướng dẫn cả"
    )

    assert merged_items is not None, "thread ĐÃ có vé (vừa seed) — không được trả None"
    assert "FS-06" in merged_items, (
        f"MẤT FS-06 sau hợp nhất: {merged_items!r}. Đây đúng lỗ PO cảnh báo — kết quả "
        "evaluate(tx=None) đã GÁN ĐÈ thay vì UNION với complaint.fraud_signals cũ."
    )


def test_hop_nhat_idempotent_goi_hai_lan_khong_phinh_khong_trung(sample_db: Session):
    """Union phải idempotent — gọi lại nhiều lần với CÙNG đầu vào không được
    làm danh sách phình ra hay sinh phần tử trùng."""
    thread_id = "THREAD-HOP-NHAT-2"
    _tao_ve_voi_fs06(sample_db, thread_id=thread_id)

    lan_1 = merge_fraud_signals(
        sample_db, thread_id=thread_id, utterance_text="có người gọi điện hướng dẫn tôi chuyển"
    )
    lan_2 = merge_fraud_signals(
        sample_db, thread_id=thread_id, utterance_text="có người gọi điện hướng dẫn tôi chuyển"
    )
    assert lan_1 == lan_2, (
        f"KHÔNG idempotent: lần 1 = {lan_1!r}, lần 2 = {lan_2!r}. "
        "sorted(set(...)) đúng đặc tả sẽ luôn cho cùng kết quả — lệch nhau "
        "nghĩa là hoặc không dùng set (trùng lặp), hoặc có tác dụng phụ khác."
    )
    assert len(lan_2) == len(set(lan_2)), f"CÓ PHẦN TỬ TRÙNG sau gộp: {lan_2!r}"


def test_hop_nhat_cau_phu_dinh_khong_gan_oan_fs13_va_khong_mat_fs06(sample_db: Session):
    """🔴 Ca Coder tự đề nghị, bắt được CẢ HAI hướng hỏng cùng lúc:
    (a) mất tín hiệu cũ (union hỏng — cùng họ hai ca trên) VÀ
    (b) gắn oan FS-13 lên khách vừa nói KHÔNG (bộ dò khẳng định/phủ định
    hỏng — câu phủ định 'không có ai gọi cả' CHỨA chữ 'có', một bộ dò không
    xét phủ định TRƯỚC sẽ khớp nhầm thành xác nhận)."""
    thread_id = "THREAD-HOP-NHAT-3"
    _tao_ve_voi_fs06(sample_db, thread_id=thread_id)

    merged_items = merge_fraud_signals(
        sample_db, thread_id=thread_id, utterance_text="không có ai gọi cả, tôi tự bấm nhầm thôi"
    )

    assert merged_items is not None
    assert "FS-06" in merged_items, f"MẤT FS-06 ở ca phủ định: {merged_items!r}"
    assert "FS-13" not in merged_items, (
        f"GẮN OAN FS-13 cho câu PHỦ ĐỊNH 'không có ai gọi cả': {merged_items!r}. "
        "Bộ dò khẳng định phải xét phủ định TRƯỚC — câu này chứa chữ 'có' "
        "nhưng đang PHỦ ĐỊNH, không phải xác nhận có người hướng dẫn."
    )


def test_hop_nhat_thread_chua_co_ve_tra_ve_none(sample_db: Session):
    """Biên đã khai trong chữ ký hàm (`-> list[str] | None`) — thread không
    có complaint nào phải trả `None`, KHÔNG phải ném lỗi hay trả `[]` (hai
    trạng thái khác nhau: 'không có gì để hợp nhất' vs 'hợp nhất ra rỗng')."""
    merged_items = merge_fraud_signals(
        sample_db, thread_id="THREAD-KHONG-TON-TAI", utterance_text="câu bất kỳ"
    )
    assert merged_items is None
