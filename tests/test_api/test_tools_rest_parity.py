"""FIN05-StressTest-Plan-v2 ST2-B-14 — so sánh mức kiểm soát route `/tools/*`
(gọi trực tiếp qua REST, dùng bởi CSKH VÀ khách hàng — xem authz matrix,
`/tools/lookup_transaction` = `ALL_ROLES`) với khi AI gọi CÙNG logic qua
function-calling (`build_customer_tools()`).

PHÁT HIỆN THẬT khi viết test này (KHÔNG nằm trong 4 finding P0 đã được
người dùng đồng ý chặn CI — xem docs/FIN05-Feature-Inventory-Security-
Review.md §11 và quyết định 2026-08-11 trong docs/TESTING.md): route
`POST /tools/lookup_transaction` gọi THẲNG `_lookup_transaction` (hàm dùng
chung, src/tools/lookup_transaction.py) — hàm này chỉ che tên/SĐT/số tài
khoản bên thứ ba (BR-06), KHÔNG chặn hẳn record nếu người hỏi không phải 1
bên của giao dịch. `_enforce_requester_is_party` (chặn hẳn) CHỈ được áp
dụng ở lớp wrapper `build_customer_tools()` — dùng cho đường đi qua AI.

Hệ quả: 1 khách hàng (role=customer, JWT hợp lệ CỦA CHÍNH HỌ) gọi TRỰC TIẾP
`POST /tools/lookup_transaction` (bỏ qua AI hoàn toàn) với `trans_id` của
giao dịch KHÔNG liên quan tới họ — vẫn tra ra được amount/fee/status/scope/
channel/mô tả giao dịch (`des`, trường tự do) đầy đủ, chỉ tên/SĐT/STK 2 bên
bị che. Đây là IDOR/BOLA thật qua "đường tắt" REST, đúng đúng lo ngại B-14
đặt ra — không phải so sánh cấu trúc chung chung.

Đánh dấu `xfail(strict=True)` — CHƯA có đồng thuận với người dùng để đưa
vào nhóm chặn CI như 4 finding P0 (họ mới chỉ duyệt CHẶN cho đúng 4 finding
đã liệt kê trước đó) — nhưng vẫn hiện RÕ trong báo cáo test (`xfailed`,
không bị `-m "not security_finding"` ẩn mất), và `strict=True` để nếu ai
vá xong mà quên gỡ `xfail`, CI sẽ tự báo `XPASS` (coi là lỗi) nhắc gỡ."""
from __future__ import annotations

import datetime as dt

import pytest
from fastapi.testclient import TestClient

from src.api.deps import get_session
from src.api.main import app
from src.auth import create_access_token


@pytest.fixture()
def client(sample_db):
    def _override_session():
        try:
            yield sample_db
            sample_db.commit()
        except Exception:
            sample_db.rollback()
            raise

    app.dependency_overrides[get_session] = _override_session
    yield TestClient(app)
    app.dependency_overrides.clear()


def _token(user_id: str, role: str = "customer") -> str:
    return create_access_token(user_id=user_id, role=role, otp_verified_at=dt.datetime.utcnow())


@pytest.mark.xfail(
    strict=True,
    reason=(
        "IDOR thật: POST /tools/lookup_transaction không áp _enforce_requester_is_party "
        "(chỉ có ở build_customer_tools cho đường AI) — khách lạ vẫn tra được "
        "amount/fee/status/des của giao dịch không liên quan. Xem docstring module."
    ),
)
def test_customer_cannot_lookup_unrelated_transaction_via_rest_shortcut(client):
    """TXN-0001 (sample_db) giữa USR-A/USR-B — USR-CSKH (đóng vai 'khách lạ'
    có JWT customer hợp lệ khác) gọi thẳng route REST, không qua AI."""
    stranger_token = _token("USR-CSKH", role="customer")
    resp = client.post(
        "/tools/lookup_transaction",
        json={"trans_id": "TXN-0001"},
        headers={"Authorization": f"Bearer {stranger_token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") == "not_found", (
        f"Khách lạ (không phải 1 bên của TXN-0001) vẫn tra ra được dữ liệu qua "
        f"route REST trực tiếp: {body}"
    )


def test_get_customer_history_rest_route_is_correctly_scoped_to_caller(client):
    """Đối chứng — route NÀY được scope ĐÚNG (user_id lấy từ current_user,
    không nhận qua body), không có cùng lỗ hổng như lookup_transaction. Test
    tích cực để không hiểu nhầm mọi route /tools/* đều có vấn đề."""
    token = _token("USR-A", role="customer")
    resp = client.post("/tools/get_customer_history", json={}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    # Không có tham số user_id nào trong request schema — không cách nào
    # truyền để tra người khác, đúng thiết kế an toàn (đối chiếu schemas.py).
    from src.api.schemas import GetCustomerHistoryRequest

    assert "user_id" not in GetCustomerHistoryRequest.model_fields


# ---------------------------------------------------------------------------
# create_ticket — CÓ 2 đường thật (REST /tools/create_ticket VÀ AI qua
# customer_tools.py::create_ticket), khác lookup_transaction/get_customer_
# history (đã test ở trên). Cả 2 đường CÙNG gọi 1 hàm dùng chung
# (create_ticket_with_fraud_check, src/services/complaint_intake.py) — nên
# khác với lookup_transaction, không có chỗ để 2 đường LỆCH PHA về logic
# nghiệp vụ. Điểm duy nhất có thể lệch là lớp OTP step-up, vì mỗi đường tự
# gác OTP RIÊNG (route dùng FastAPI Depends(require_otp_verified) ở
# src/auth.py, tool AI tự check _otp_fresh() ở customer_tools.py) — 2 chỗ
# viết tay riêng biệt, dễ lệch ngưỡng nếu ai sửa 1 bên quên bên kia.
# ---------------------------------------------------------------------------


def _stale_otp_token(user_id: str, minutes_ago: int) -> str:
    stale = dt.datetime.utcnow() - dt.timedelta(minutes=minutes_ago)
    return create_access_token(user_id=user_id, role="customer", otp_verified_at=stale)


def test_create_ticket_rest_and_ai_both_reject_stale_otp_at_the_same_threshold(client, sample_db):
    """OTP_STEPUP_FRESH_MINUTES = 15 (src/config.py, quyết định AUTH-008) —
    xác nhận CẢ 2 đường cùng từ chối ở > 15 phút, không đường nào lỏng hơn."""
    from src.agents.tools.customer_tools import build_customer_tools
    from src.config import OTP_STEPUP_FRESH_MINUTES

    stale_minutes = OTP_STEPUP_FRESH_MINUTES + 1

    # Đường REST
    stale_token = _stale_otp_token("USR-A", stale_minutes)
    resp = client.post(
        "/tools/create_ticket",
        json={"complaint_type": "money_not_received", "scope": "internal_wallet", "description_raw": "test"},
        headers={"Authorization": f"Bearer {stale_token}"},
    )
    assert resp.status_code == 403, f"REST phải từ chối OTP quá {stale_minutes} phút, được {resp.status_code}"

    # Đường AI — cùng ngưỡng, tự check trong tool wrapper (không qua FastAPI dependency)
    stale_ts = (dt.datetime.utcnow() - dt.timedelta(minutes=stale_minutes)).timestamp()
    tools = {t.name: t for t in build_customer_tools(sample_db, user_id="USR-A", otp_verified_at=stale_ts)}
    ai_result = tools["create_ticket"].invoke(
        {"complaint_type": "money_not_received", "scope": "internal_wallet", "description_raw": "test"}
    )
    assert ai_result.get("status") == "error", f"AI path phải từ chối OTP quá {stale_minutes} phút, được {ai_result}"


def test_create_ticket_rest_and_ai_both_accept_fresh_otp(client, sample_db):
    """Đối chứng — cùng ngưỡng đó, dưới 15 phút CẢ 2 đường đều cho qua (không
    chỉ test hướng từ chối, tránh false-positive nếu ai lỡ chặn cứng luôn)."""
    from src.agents.tools.customer_tools import build_customer_tools

    fresh_token = _stale_otp_token("USR-A", 1)
    resp = client.post(
        "/tools/create_ticket",
        json={"complaint_type": "money_not_received", "scope": "internal_wallet", "description_raw": "test REST"},
        headers={"Authorization": f"Bearer {fresh_token}"},
    )
    assert resp.status_code == 200, resp.text

    fresh_ts = (dt.datetime.utcnow() - dt.timedelta(minutes=1)).timestamp()
    tools = {t.name: t for t in build_customer_tools(sample_db, user_id="USR-A", otp_verified_at=fresh_ts)}
    ai_result = tools["create_ticket"].invoke(
        {"complaint_type": "money_not_received", "scope": "internal_wallet", "description_raw": "test AI"}
    )
    assert ai_result.get("status") != "error", ai_result
    assert "ticket_id" in ai_result


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Phát hiện thật KHÁC (không thuộc 4 finding P0 đã được người dùng "
        "duyệt chặn CI 2026-08-11): create_ticket (CẢ 2 đường REST và AI, "
        "vì cùng gọi chung create_ticket_with_fraud_check ->  "
        "src/tools/create_ticket.py) chỉ kiểm tra trans_id CÓ TỒN TẠI, KHÔNG "
        "kiểm tra trans_id có THUỘC VỀ user_id đang gọi hay không (xem "
        "docstring src/tools/create_ticket.py dòng 3-5, chỉ nêu yêu cầu tồn "
        "tại). Hệ quả: 1 khách hàng có thể tạo ticket khiếu nại tham chiếu "
        "trans_id của MỘT KHÁCH HÀNG KHÁC — không lộ dữ liệu giao dịch (tool "
        "không trả tx detail), nhưng gây nhiễu dữ liệu/CSKH có thể xử lý "
        "nhầm ticket dựa trên giao dịch không thuộc về người khiếu nại. Ảnh "
        "hưởng THẤP HƠN lookup_transaction (không lộ số liệu), nhưng vẫn là "
        "lỗ hổng xác thực quyền sở hữu (BOLA) cần người dùng quyết định có "
        "chặn CI hay chấp nhận rủi ro."
    ),
)
def test_create_ticket_does_not_verify_trans_id_belongs_to_caller(client, sample_db):
    """TXN-0001 (sample_db) thuộc về USR-A — USR-B (khách khác, JWT hợp lệ
    của chính họ) tạo ticket khiếu nại tham chiếu THẲNG trans_id này."""
    fresh_token = _stale_otp_token("USR-B", 1)
    resp = client.post(
        "/tools/create_ticket",
        json={
            "complaint_type": "double_charge",
            "scope": "internal_wallet",
            "description_raw": "Tôi bị trừ tiền 2 lần",
            "trans_id": "TXN-0001",
        },
        headers={"Authorization": f"Bearer {fresh_token}"},
    )
    assert resp.status_code != 200 or resp.json().get("status") == "error", (
        f"USR-B tạo được ticket tham chiếu TXN-0001 (không thuộc về họ) mà không bị chặn: {resp.status_code} {resp.text}"
    )


# ---------------------------------------------------------------------------
# propose_resolution / escalate_ticket — KHÔNG có đường AI để so sánh (đây là
# hành động CHỈ CSKH/Sếp thao tác qua webapp trực tiếp, chưa từng và không
# nên lộ ra cho AI chat khách hàng gọi — xem customer_tools.py dòng 12:
# "KHÔNG có propose_resolution/escalate_ticket — đó là hành động của CSKH,
# không phải AI"). B-14 (v2) hỏi "so REST vs AI" — với 2 tool này câu trả lời
# đúng là "N/A, chỉ có 1 đường REST theo đúng thiết kế". Test dưới đây là
# REGRESSION GUARD giữ đúng bất biến đó — chặn nếu sau này ai vô tình thêm
# nhầm 2 tool này vào bộ công cụ AI khách hàng (rủi ro thật: sẽ cho phép AI
# tự ý duyệt/leo thang case mà không qua HITL con người, vi phạm thẳng
# Brief §7 #1).
# ---------------------------------------------------------------------------


def test_propose_resolution_and_escalate_ticket_are_never_exposed_to_customer_ai(sample_db):
    from src.agents.tools.customer_tools import build_customer_tools

    tool_names = {t.name for t in build_customer_tools(sample_db, user_id="USR-A", otp_verified_at=None)}
    assert "propose_resolution" not in tool_names
    assert "escalate_ticket" not in tool_names
