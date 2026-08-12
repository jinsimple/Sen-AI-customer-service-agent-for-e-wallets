"""FIN05-StressTest-Plan-v4 6.2 — RAG trả về RỖNG (chưa có tài liệu chính
sách nào được upload, hoặc index Chroma có chunk_id đã lệch pha với DB —
tài liệu vừa bị xoá nhưng index chưa kịp đồng bộ, xem comment
src/rag/search.py dòng 37-39) — agent KHÔNG được tự suy đoán chính sách khi
không có gì để trích dẫn (chỉ dẫn rõ trong docstring search_policy,
customer_tools.py dòng 383-384).

Test ở TẦNG DETERMINISTIC (monkeypatch `store.search`, không gọi Chroma/
OpenAI thật) — giống pattern `tests/test_services/test_fault_tolerance.py`.
Hành vi ngôn ngữ tự nhiên của agent khi rỗng (agent có thực sự NÓI đúng "chưa
có thông tin" hay không) là 1 case eval riêng, không nằm trong phạm vi test
nhanh này."""
from __future__ import annotations

from src.agents.tools.customer_tools import build_customer_tools
from src.db.models import ToolResult
from src.rag import search as search_module


def test_search_policy_text_returns_not_found_when_chroma_index_is_fully_empty(sample_db, monkeypatch):
    monkeypatch.setattr(search_module.store, "search", lambda query, k: [])

    payload = search_module.search_policy_text(sample_db, query="phí rút tiền là bao nhiêu")

    assert payload["status"] == "not_found"
    assert payload["results"] == []
    assert "tool_result_id" in payload


def test_search_policy_text_returns_not_found_when_index_has_stale_chunk_ids(sample_db, monkeypatch):
    """Chroma trả về chunk_id NHƯNG bảng policy_chunks không còn dòng nào
    khớp (tài liệu vừa bị xoá, index background job chưa kịp đồng bộ) —
    PHẢI graceful-degrade về not_found, KHÔNG crash/KeyError."""
    monkeypatch.setattr(
        search_module.store, "search", lambda query, k: [("CHUNK-does-not-exist-anymore", 0.12)]
    )

    payload = search_module.search_policy_text(sample_db, query="chính sách hoàn tiền")

    assert payload["status"] == "not_found"
    assert payload["results"] == []


def test_search_policy_text_records_exactly_one_tool_result_even_when_empty(sample_db, monkeypatch):
    """Rỗng vẫn phải đi qua record_tool_result — audit trail (B-08/B-09)
    không được bỏ qua chỉ vì không có kết quả, CSKH vẫn cần thấy AI ĐÃ tra
    (và không ra gì) thay vì không có dấu vết nào."""
    monkeypatch.setattr(search_module.store, "search", lambda query, k: [])
    before = sample_db.query(ToolResult).count()

    search_module.search_policy_text(sample_db, query="ưu đãi tháng này")

    after = sample_db.query(ToolResult).count()
    assert after == before + 1


def test_search_policy_ai_tool_does_not_require_otp_and_handles_empty_index(sample_db, monkeypatch):
    """search_policy KHÔNG nằm trong SENSITIVE_TOOLS (chính sách/phí chung
    chung, không chạm dữ liệu tài khoản) — regression guard giữ đúng bất
    biến đó (khác lookup_transaction/get_customer_history/create_ticket,
    đều có OTP gate), đồng thời xác nhận đường AI (không chỉ hàm dùng chung)
    cũng xử lý đúng lúc rỗng."""
    monkeypatch.setattr(search_module.store, "search", lambda query, k: [])

    tools = {t.name: t for t in build_customer_tools(sample_db, user_id="USR-A", otp_verified_at=None)}
    result = tools["search_policy"].invoke({"query": "phí chuyển tiền liên ngân hàng"})

    assert result["status"] == "not_found"
    assert result != {
        "status": "error",
        "message": "Khách chưa xác thực OTP phiên làm việc + câu hỏi bảo mật — yêu cầu khách hoàn tất xác thực trong ứng dụng trước khi tiếp tục thao tác này.",
    }
