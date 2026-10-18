"""RB3 false-positive LẦN BA (05/09, QA tái lập 2/2 lần ở bước TRA CỨU) —
test hàm THUẦN `_co_de_xuat_tao_ve` (src/agents/graph.py), tách riêng khỏi
`run_agent_turn` để không cần gọi LLM (cùng khuôn
tests/test_agents/test_investigation_log.py — dựng AIMessage/ToolMessage
đúng shape thật, KHÔNG chạy graph).

Bối cảnh thật: khách hỏi "chưa nhận được tiền", lượt CHỈ gọi
`lookup_transaction`, model tóm tắt kết quả rồi HỎI Ý khách trước khi tạo hồ
sơ ("...được không ạ?"). `khai_da_tao_ve(reply)` cho câu này vẫn `True`
(đúng — xem test_rb3_khai_da_tao_ve.py, ca `mem_de_nghi_hoi_y_lookup_step`)
vì "Mã giao dịch" (mã GD) + "đã ghi nhận" (tiền, không phải hồ sơ) rơi đúng
2 mảnh ghép nhánh MỀM. Cổng CẤU TRÚC (đọc TỪ HÀM NÀY) là lớp bảo vệ THỰC SỰ
ngăn RB3 kích nhầm ở bước tra cứu — không sửa matcher.

Đỏ-trước/xanh-sau CẢ HAI CHIỀU (PO chốt 05/09): giữ ca dương-tính-đúng
(MT-Z01 — orphaned create_ticket vẫn phải kích được) VÀ thêm ca âm-tính
(lookup-step fallback không kích)."""
from __future__ import annotations

import json

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from src.agents.graph import _has_ticket_proposal


def _ai_tool_call(name: str, args: dict, call_id: str) -> AIMessage:
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": call_id}])


def _tool_result(call_id: str, payload: dict) -> ToolMessage:
    return ToolMessage(content=json.dumps(payload), tool_call_id=call_id)


def test_luot_chi_lookup_khong_tinh_la_de_xuat_tao_ve():
    """Ca THẬT 05/09 — lookup_transaction THÀNH CÔNG, KHÔNG có create_ticket/
    request_human_handoff nào — đây chính là điều kiện phải KHÔNG kích RB3."""
    messages = [
        HumanMessage(content="Tôi chuyển tiền mà người nhận báo chưa thấy, kiểm tra giúp tôi"),
        _ai_tool_call("lookup_transaction", {"trans_id": "TXN20260728000108"}, "call_1"),
        _tool_result("call_1", {"status": "found", "transaction": {"trans_id": "TXN20260728000108"}}),
    ]
    called_tool, has_ticket_proposal = _has_ticket_proposal(messages)
    assert called_tool is True
    assert has_ticket_proposal is False


def test_orphaned_create_ticket_van_tinh_la_de_xuat_tao_ve_mt_z01():
    """Ca gốc 25/08 (MT-Z01) — Review 05/09 đối chiếu lại xác nhận
    `AIMessage.tool_calls` THÔ CÓ `create_ticket`, nhưng MỒ CÔI (không có
    ToolMessage phản hồi). Đây là điều kiện BẮT BUỘC vẫn phải tính là "có đề
    xuất tạo vé" — đọc RAW, không đọc tool_calls_out đã lọc bỏ mồ côi."""
    messages = [
        HumanMessage(content="Chuyển nhầm tiền cho người lạ"),
        _ai_tool_call("create_ticket", {"complaint_type": "wrong_recipient"}, "call_orphan"),
        # KHÔNG có ToolMessage nào cho call_orphan — đúng dạng mồ côi thật.
    ]
    called_tool, has_ticket_proposal = _has_ticket_proposal(messages)
    assert called_tool is True
    assert has_ticket_proposal is True


def test_request_human_handoff_orphan_cung_tinh_la_de_xuat_tao_ve():
    messages = [
        HumanMessage(content="Cho tôi gặp người thật"),
        _ai_tool_call("request_human_handoff", {}, "call_2"),
    ]
    called_tool, has_ticket_proposal = _has_ticket_proposal(messages)
    assert called_tool is True
    assert has_ticket_proposal is True


def test_khong_goi_tool_nao_khong_duoc_mien_tru():
    """Hallucination THUẦN, zero tool_call — KHÔNG được coi là 'chỉ tool
    không liên quan', vì `co_goi_tool=False` — cổng RB3 ở graph.py vẫn phải
    đánh giá `khai_da_tao_ve()` bình thường cho ca này (không nới lỏng
    hướng này, chỉ thu hẹp đúng hướng vừa lộ false-positive)."""
    messages = [
        HumanMessage(content="Tôi bị chuyển nhầm tiền"),
        AIMessage(content="Đã tạo hồ sơ khiếu nại thành công với mã CMP-00003.", tool_calls=[]),
    ]
    called_tool, has_ticket_proposal = _has_ticket_proposal(messages)
    assert called_tool is False
    assert has_ticket_proposal is False


def test_ket_hop_lookup_va_create_ticket_cung_luot():
    """Lượt có CẢ lookup_transaction lẫn create_ticket (thứ tự nghiệp vụ
    bình thường: tra trước, tạo sau) — vẫn phải tính đúng là CÓ đề xuất tạo
    vé, không bị 'rửa' bởi tool khác đứng cùng lượt."""
    messages = [
        HumanMessage(content="Xác nhận đúng giao dịch rồi, tạo hồ sơ giúp tôi"),
        _ai_tool_call("lookup_transaction", {"trans_id": "TXN-0001"}, "call_1"),
        _tool_result("call_1", {"status": "found"}),
        _ai_tool_call("create_ticket", {"complaint_type": "wrong_recipient"}, "call_2"),
        _tool_result("call_2", {"ticket_id": "TCK-abc123"}),
    ]
    called_tool, has_ticket_proposal = _has_ticket_proposal(messages)
    assert called_tool is True
    assert has_ticket_proposal is True
