"""ATLAS-001 (FIN05_QA_TestCases.jsonl, MITRE ATLAS Exfiltration/Recon,
2026-08-11) — `lookup_transaction()` dùng chung chỉ che tên/SĐT phía bên kia
(PDPA), KHÔNG chặn toàn bộ record nếu người hỏi không phải 1 bên của giao
dịch. Test THẲNG lớp wrapper `build_customer_tools()` (nơi vá thật —
`_enforce_requester_is_party`, xem src/agents/tools/customer_tools.py) chứ
không phải `_lookup_transaction()` dùng chung — route HTTP thô của CSKH vẫn
cần tra cứu không giới hạn theo user, chỉ tầng khách hàng bị siết.

Deterministic, không cần LLM: gọi thẳng LangChain tool (.invoke) với đúng
tham số agent thật sẽ truyền."""
from __future__ import annotations

import datetime as dt
from concurrent.futures import ThreadPoolExecutor

from src.agents.tools.customer_tools import build_customer_tools

_NOW = dt.datetime.utcnow().timestamp()


def test_stranger_cannot_lookup_others_transaction_by_trans_id(sample_db):
    # USR-CSKH không phải sender/receiver của TXN-0001 (giữa USR-A/USR-B) —
    # không có ví nào trong sample_db, đóng vai "khách lạ" đoán đúng mã.
    tools = {t.name: t for t in build_customer_tools(sample_db, user_id="USR-CSKH", otp_verified_at=_NOW)}
    result = tools["lookup_transaction"].invoke({"trans_id": "TXN-0001"})
    assert result["status"] == "not_found"
    assert "transaction" not in result


def test_stranger_cannot_lookup_others_transaction_by_phone_amount(sample_db):
    # ATLAS-001 mô tả đúng bề mặt này: đoán đúng SĐT người nhận + số tiền của
    # người khác — trước bản vá, vẫn tra ra được (chỉ che tên/SĐT bên kia).
    tools = {t.name: t for t in build_customer_tools(sample_db, user_id="USR-CSKH", otp_verified_at=_NOW)}
    result = tools["lookup_transaction"].invoke({"phone": "0901000002", "amount": 270_000})
    assert result["status"] == "not_found"


def test_owner_can_still_lookup_own_transaction(sample_db):
    # Không phá hành vi đúng hiện có: chính chủ (1 bên thật của giao dịch)
    # vẫn tra được bình thường.
    tools = {t.name: t for t in build_customer_tools(sample_db, user_id="USR-A", otp_verified_at=_NOW)}
    result = tools["lookup_transaction"].invoke({"trans_id": "TXN-0001"})
    assert result["status"] == "found"
    assert result["transaction"]["amount"] == 270_000


def test_wrong_recipient_flow_by_recipient_phone_still_works(sample_db):
    # "Chuyển nhầm" hợp lệ: NGƯỜI GỬI (USR-A) tự nêu SĐT NGƯỜI NHẬN (USR-B,
    # 0901000002) để tra ra giao dịch chính mình đã gửi — vẫn phải tra được,
    # vì USR-A vẫn là 1 bên thật (sender) của TXN-0001. Đây là ca cụ thể
    # _enforce_requester_is_party() phải KHÔNG chặn nhầm.
    tools = {t.name: t for t in build_customer_tools(sample_db, user_id="USR-A", otp_verified_at=_NOW)}
    result = tools["lookup_transaction"].invoke({"phone": "0901000002", "amount": 270_000})
    assert result["status"] == "found"
    assert result["transaction"]["trans_id"] == "TXN-0001"


def test_concurrent_tool_calls_do_not_crash_shared_session(sample_db):
    """Phát hiện thật (2026-08-11, functional_qa_set.jsonl FUNCQA-011-HAPPY):
    LangGraph's ToolNode chạy nhiều tool call trong CÙNG 1 lượt SONG SONG qua
    ThreadPoolExecutor (vd model tra 2 giao dịch nghi trừ 2 lần cùng lúc) —
    nhưng cả 5 tool đóng cứng dùng CHUNG 1 session SQLAlchemy (không
    thread-safe), gây `InvalidRequestError: Session is already flushing`
    khi 2 thread cùng lúc chạm session. `_session_lock` trong
    build_customer_tools() phải serialize hoá việc này — mô phỏng đúng kịch
    bản 2 tool call song song (lookup_transaction ghi tool_result qua
    session.add()+flush()) và xác nhận không crash, cả 2 đều trả kết quả
    đúng."""
    tools = {t.name: t for t in build_customer_tools(sample_db, user_id="USR-A", otp_verified_at=_NOW)}
    lookup = tools["lookup_transaction"]

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(lookup.invoke, {"trans_id": "TXN-0001"}),
            executor.submit(lookup.invoke, {"trans_id": "TXN-0002"}),
        ]
        results = [f.result() for f in futures]  # raise ngay nếu thread nào crash

    assert {r["status"] for r in results} == {"found"}
    assert {r["transaction"]["trans_id"] for r in results} == {"TXN-0001", "TXN-0002"}
