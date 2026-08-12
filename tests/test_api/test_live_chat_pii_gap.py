"""FIN05-StressTest-Plan-v2 ST2-P0-3/E-09 (docs/FIN05-Feature-Inventory-
Security-Review.md §6, dòng "Giới hạn PDPA đã biết") — live-chat KHÔNG chạy
qua bất kỳ bước scrub/mask PII nào trước khi lưu `Message.content`
(src/services/live_chat.py::record_message chỉ mã hoá at-rest qua
EncryptedText, không scrub nội dung). Khác với luồng AI (đã có
`src/observability/pii.py::scrub_pii` cho log/trace, `src/tools/masking.py`
cho dữ liệu bên thứ ba trả về qua tool), CSKH/khách gõ tay SĐT/STK thô vào
live-chat thì lưu nguyên văn — nếu bị lộ (audit log, export dữ liệu, DSAR
PDPA...), số thô hiển thị nguyên vẹn.

Test khẳng định HÀNH VI AN TOÀN MONG MUỐN (nội dung gõ tay chứa PII phải
được che/scrub trước khi lưu) — FAIL NGAY hôm nay, cố tình, không tự sửa
`src/services/live_chat.py::record_message` cùng lúc (quyết định che ở mức
nào — có thể xung đột với nhu cầu CSKH cần SĐT thật để gọi lại khách, xem
ghi chú trong Feature Inventory — là quyết định của PO, không phải quyết
định kỹ thuật đơn thuần)."""
from __future__ import annotations

import pytest

from src.services import live_chat
from src.services.complaint_intake import create_ticket_with_fraud_check


@pytest.mark.security_finding
def test_live_chat_message_containing_raw_phone_number_is_not_masked_before_storage(sample_db):
    ticket_id = create_ticket_with_fraud_check(
        sample_db, user_id="USR-A", complaint_type="wrong_recipient", scope="internal_wallet",
        description_raw="test PII gap", trans_id="TXN-0001",
    )["ticket_id"]
    chat_session = live_chat.open_chat_session(sample_db, ticket_id=ticket_id, customer_id="USR-A")

    raw_phone = "0987654321"
    saved = live_chat.record_message(
        sample_db,
        chat_session_id=chat_session["chat_session_id"],
        role="customer",
        content=f"Bạn liên hệ giúp mình qua số {raw_phone} nhé, số chính chủ luôn.",
    )
    sample_db.commit()

    assert raw_phone not in saved["content"], (
        f"Tin nhắn live-chat lưu nguyên văn số điện thoại thô ({raw_phone}) "
        "không qua bước che/scrub nào — src/services/live_chat.py::"
        "record_message hiện chỉ mã hoá at-rest (EncryptedText), không xử lý "
        "nội dung. Xem docs/FIN05-Feature-Inventory-Security-Review.md §6 — "
        "cần PO quyết định mức che phù hợp (không được che tới mức CSKH mất "
        "khả năng gọi lại khách khi cần) trước khi vá."
    )
