"""FIN05-StressTest-Plan-v2 ST2-B-06 — `request_human_handoff` là tool DUY
NHẤT trong `build_customer_tools()` KHÔNG kiểm `_otp_fresh(...)` trong thân
hàm (đối chiếu trực tiếp `src/agents/tools/customer_tools.py` — khác
`lookup_transaction`/`create_ticket`). Đây là quyết định thiết kế CÓ CHỦ ĐÍCH
(docstring tool: "KHÔNG cần OTP — đây là routing request, không phải thao
tác chạm dữ liệu tài khoản"), và `src/api/main.py::live_chat_ws_ticket` từng
sửa lỗi thật vì gác nhầm OTP ở route mở phiên chat sau khi handoff (xem
comment tại đó, phát hiện 2026-08-11). Test này là regression CHẶN ai đó
"vá nhầm" thêm OTP vào request_human_handoff sau này — không phải kiểm tra
tính năng mới."""
from __future__ import annotations

from src.agents.tools.customer_tools import build_customer_tools
from src.services.complaint_intake import create_ticket_with_fraud_check


def test_request_human_handoff_succeeds_without_any_otp_verification(sample_db):
    tools = {t.name: t for t in build_customer_tools(sample_db, user_id="USR-A", otp_verified_at=None)}
    result = tools["request_human_handoff"].invoke({"reason": "Khách muốn nói chuyện với người thật"})

    assert result.get("status") != "error", (
        f"request_human_handoff PHẢI thành công dù otp_verified_at=None (đây "
        f"là routing request, không phải thao tác dữ liệu) — nhưng nhận: {result}"
    )
    assert "ticket_id" in result


def test_request_human_handoff_reuses_existing_ticket_for_same_issue(sample_db):
    """Không tạo hồ sơ trùng khi hội thoại ĐÃ tạo ticket cho đúng vấn đề —
    đúng docstring tool (`ticket_id` truyền lại tránh trùng)."""
    created = create_ticket_with_fraud_check(
        sample_db, user_id="USR-A", complaint_type="wrong_recipient", scope="internal_wallet",
        description_raw="test handoff reuse", trans_id="TXN-0001",
    )
    sample_db.commit()

    tools = {t.name: t for t in build_customer_tools(sample_db, user_id="USR-A", otp_verified_at=None)}
    result = tools["request_human_handoff"].invoke(
        {"reason": "Muốn nói chuyện trực tiếp về vấn đề đã báo", "ticket_id": created["ticket_id"]}
    )

    assert result["ticket_id"] == created["ticket_id"]
