"""Live chat (2026-08-11) — mirror test_complaint_intake.py style. Dùng
sample_db (tests/conftest.py: USR-A/USR-B khách hàng, USR-CSKH/USR-SUP nhân
viên, TXN-0001 giữa USR-A/USR-B) — tạo 1 ticket thật qua
create_ticket_with_fraud_check() trước khi test live_chat.py, không tự chế
Ticket/Complaint tay (giữ đúng bất biến FK/CHECK constraint thật)."""
from __future__ import annotations

import pytest

from src.services import live_chat
from src.services.complaint_intake import create_ticket_with_fraud_check
from src.tools.base import ToolError


def _make_ticket(sample_db, *, user_id: str = "USR-A") -> str:
    created = create_ticket_with_fraud_check(
        sample_db,
        user_id=user_id,
        complaint_type="wrong_recipient",
        scope="internal_wallet",
        description_raw="test live chat",
        trans_id="TXN-0001",
    )
    return created["ticket_id"]


def test_open_chat_session_creates_waiting_session(sample_db):
    ticket_id = _make_ticket(sample_db)
    result = live_chat.open_chat_session(sample_db, ticket_id=ticket_id, customer_id="USR-A")
    assert result["status"] == "waiting"
    assert result["ticket_id"] == ticket_id
    assert result["claimed_by"] is None


def test_open_chat_session_reuses_existing_waiting_session(sample_db):
    """Khách bấm lại nút mở chat không tạo phiên trùng cho CÙNG 1 ticket."""
    ticket_id = _make_ticket(sample_db)
    first = live_chat.open_chat_session(sample_db, ticket_id=ticket_id, customer_id="USR-A")
    second = live_chat.open_chat_session(sample_db, ticket_id=ticket_id, customer_id="USR-A")
    assert first["chat_session_id"] == second["chat_session_id"]


def test_open_chat_session_rejects_ticket_not_owned_by_customer(sample_db):
    ticket_id = _make_ticket(sample_db, user_id="USR-A")
    with pytest.raises(ToolError):
        live_chat.open_chat_session(sample_db, ticket_id=ticket_id, customer_id="USR-B")


def test_claim_session_race_second_claim_is_noop(sample_db):
    """2 CSKH cùng bấm nhận 1 phiên — chỉ người ĐẦU TIÊN thành công, người
    sau nhận None (không phải lỗi hệ thống, không raise)."""
    ticket_id = _make_ticket(sample_db)
    chat_session = live_chat.open_chat_session(sample_db, ticket_id=ticket_id, customer_id="USR-A")
    chat_session_id = chat_session["chat_session_id"]

    first_claim = live_chat.claim_session(sample_db, chat_session_id=chat_session_id, staff_id="USR-CSKH")
    second_claim = live_chat.claim_session(sample_db, chat_session_id=chat_session_id, staff_id="USR-SUP")

    assert first_claim is not None
    assert first_claim["claimed_by"] == "USR-CSKH"
    assert first_claim["status"] == "active"
    assert second_claim is None


def test_record_message_persists_and_encrypts_at_rest(sample_db, tmp_path):
    """M3 (`d8e4ff9`, niêm `992e382`) — LƯU ĐỦ, CHE Ở TẦNG ĐỌC. TRƯỚC bản vá
    này, `saved["content"]` (giá trị trả về — đường đọc) mang đúng nguyên văn
    khách gõ; giờ nó PHẢI đã che PII. Bản LƯU (đọc lại qua ORM, giải mã)
    PHẢI vẫn giữ nguyên văn — che ở lúc lưu là mất vĩnh viễn, BR-07 cấm.
    """
    ticket_id = _make_ticket(sample_db)
    chat_session = live_chat.open_chat_session(sample_db, ticket_id=ticket_id, customer_id="USR-A")
    saved = live_chat.record_message(
        sample_db, chat_session_id=chat_session["chat_session_id"], role="customer", content="số điện thoại của tôi là 0901000001"
    )
    sample_db.commit()

    # Đường đọc (giá trị trả về — WS broadcast thẳng nó) PHẢI đã che.
    assert "0901000001" not in saved["content"], (
        f"Giá trị trả về của record_message vẫn mang SĐT thô: {saved['content']!r} — "
        "đây là ĐƯỜNG ĐỌC (WS broadcast dùng thẳng giá trị này), phải che theo M3."
    )

    # Bản lưu PHẢI vẫn đủ — đọc lại qua ORM (tự giải mã), không phải giá trị
    # trả về của lượt ghi. Mất vế này thì SĐT khách gõ biến mất vĩnh viễn,
    # kể cả khi sau này cần đúng câu ấy để phân xử một khiếu nại (BR-07).
    from src.db.models import Message

    reloaded = sample_db.get(Message, saved["message_id"])
    assert reloaded.content == "số điện thoại của tôi là 0901000001", (
        f"Bản lưu KHÔNG còn nguyên văn: {reloaded.content!r} — M3 chọn vì lưu đủ, "
        "che ở tầng đọc. Nếu bản lưu cũng bị che, ta đã mất vĩnh viễn nguyên văn "
        "khách gõ (BR-07 cấm lưu bản đã che)."
    )

    # Đọc THẲNG bytes thô qua raw connection (bỏ qua tầng ORM tự giải mã) —
    # xác nhận content KHÔNG nằm plaintext trong DB, cùng kỹ thuật đã dùng
    # để xác nhận EncryptedText hoạt động cho PolicyChunk.text. Vẫn phải
    # đúng dù nội dung lưu giờ là NGUYÊN VĂN (mã hoá at-rest là lớp riêng,
    # không liên quan tới việc có che PII hay không).
    raw = sample_db.connection().exec_driver_sql(
        "SELECT content FROM messages WHERE message_id = ?", (saved["message_id"],)
    ).scalar()
    assert "0901000001" not in raw


def test_record_message_masks_phone_and_bank_account_but_keeps_amount(sample_db):
    """① ĐƯỜNG ĐỌC (M3, `d8e4ff9`) — giá trị trả về của record_message (đúng
    thứ WS broadcast thẳng, `live_chat_ws.py:583`) phải che SĐT + STK, NHƯNG
    KHÔNG được ăn mất số tiền — đây chính là lý do M3 (che lúc lưu, giữ đủ)
    được chọn thay M1 (che lúc lưu): số tiền là dữ kiện khiếu nại tài chính,
    ăn mất nó khi che là hỏng đúng thứ quan trọng nhất trong câu."""
    ticket_id = _make_ticket(sample_db)
    chat_session = live_chat.open_chat_session(sample_db, ticket_id=ticket_id, customer_id="USR-A")
    saved = live_chat.record_message(
        sample_db,
        chat_session_id=chat_session["chat_session_id"],
        role="customer",
        content="Gọi mình 0987654321 nhé, STK 88000000000001. Mình chuyển 1500000000 đồng.",
    )
    sample_db.commit()

    content_text = saved["content"]
    assert "0987654321" not in content_text, f"SĐT thô vẫn còn trong đường đọc: {content_text!r}"
    assert content_text.startswith("Gọi mình 098") and content_text[content_text.index("098") + 3] == "*", (
        f"SĐT phải che dạng giữ 3 đầu — không thấy mẫu che ngay sau '098': {content_text!r}"
    )
    assert content_text.count("4321") >= 1 and "4321." not in content_text.split("STK")[0], (
        f"SĐT phải giữ 4 số cuối '4321' sau khi che: {content_text!r}"
    )
    assert "88000000000001" not in content_text, f"STK thô vẫn còn trong đường đọc: {content_text!r}"
    assert "0001" in content_text, f"STK phải giữ 4 số cuối '0001' sau khi che: {content_text!r}"
    assert "1500000000 đồng" in content_text, (
        f"Số tiền BỊ ĂN MẤT khi che — đúng lỗi M3 được chọn để tránh: {content_text!r}"
    )


def test_record_message_full_content_survives_intact_in_storage(sample_db):
    """② BẢN LƯU VẪN ĐỦ (điều kiện bắt buộc PO đặt cho M3, `992e382`) —
    KHÔNG đủ để chỉ chấm đường đọc bị che; phải khẳng định riêng bản lưu
    (đọc lại qua ORM, giải mã, KHÔNG phải giá trị trả về của lượt ghi) giữ
    NGUYÊN VẸN cả SĐT lẫn STK. Thiếu ca này thì việc sửa test không phân
    biệt được với đi vòng qua cổng — có thể "sửa cho xanh" bằng cách che
    luôn cả bản lưu, mất vĩnh viễn dữ liệu cần cho phân xử khiếu nại sau
    này (BR-07 cấm chính điều đó)."""
    from src.db.models import Message

    ticket_id = _make_ticket(sample_db)
    chat_session = live_chat.open_chat_session(sample_db, ticket_id=ticket_id, customer_id="USR-A")
    cau_goc = "Gọi mình 0987654321 nhé, STK 88000000000001. Mình chuyển 1500000000 đồng."
    saved = live_chat.record_message(
        sample_db, chat_session_id=chat_session["chat_session_id"], role="customer", content=cau_goc
    )
    sample_db.commit()

    reloaded = sample_db.get(Message, saved["message_id"])
    assert reloaded.content == cau_goc, (
        f"Bản lưu không còn nguyên văn — SĐT/STK có thể đã bị che vĩnh viễn "
        f"trước khi lưu (đúng điều BR-07 cấm): lưu {reloaded.content!r}, gốc {cau_goc!r}"
    )


def test_submit_csat_rejects_out_of_range_score(sample_db):
    ticket_id = _make_ticket(sample_db)
    chat_session = live_chat.open_chat_session(sample_db, ticket_id=ticket_id, customer_id="USR-A")
    with pytest.raises(ToolError):
        live_chat.submit_csat(sample_db, chat_session_id=chat_session["chat_session_id"], score=6)


def test_get_handoff_context_includes_ticket_and_complaint(sample_db):
    ticket_id = _make_ticket(sample_db)
    context = live_chat.get_handoff_context(sample_db, ticket_id=ticket_id)
    assert context["ticket"]["ticket_id"] == ticket_id
    assert context["complaint"]["type"] == "wrong_recipient"
    assert context["customer"]["user_id"] == "USR-A"
