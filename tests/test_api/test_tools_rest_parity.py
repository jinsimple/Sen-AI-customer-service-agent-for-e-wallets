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

TRẠNG THÁI 15/08 — CẢ HAI LỖ HỔNG ĐÃ VÁ, KHÔNG CÒN `xfail` NÀO TRONG FILE.

Lịch sử để lại vì nó chứng minh cơ chế hoạt động: hai test dưới đây từng mang
`xfail(strict=True)` — cố ý KHÔNG gắn `security_finding` (chưa có đồng thuận
chặn CI), nhưng vẫn hiện rõ trong báo cáo dưới dạng `xfailed` thay vì bị ẩn.
`strict=True` là phần quan trọng: khi coder vá xong, CI tự báo **XPASS** —
"test này lẽ ra phải hỏng mà lại chạy được" — nên không ai kịp quên gỡ nhãn.
Đó chính là cách hai lỗ này được đóng: máy nhắc, không phải người nhớ.

Nay cả hai là test hồi quy thường. Mở lại lỗ hổng là ĐỎ ngay, không núp được
dưới nhãn xfail nữa."""
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


def test_customer_cannot_lookup_unrelated_transaction_via_rest_shortcut(client):
    """C4/BOLA — ĐÃ VÁ 15/08, gỡ `xfail(strict=True)` thành test thường.

    Lịch sử: `POST /tools/lookup_transaction` từng KHÔNG áp
    `_enforce_requester_is_party` (chốt chặn đó chỉ có ở `build_customer_tools`
    cho đường AI), nên khách lạ tra thẳng REST vẫn thấy amount/fee/status/des
    của giao dịch không liên quan. Đúng ca "hai đường vào cùng một dữ liệu,
    chỉ một đường có gác".

    `strict=True` đã làm đúng việc của nó: coder vá xong, CI báo **XPASS** —
    tức "test này lẽ ra phải hỏng mà lại chạy được" — nên không ai kịp quên gỡ.

    Từ đây nó là test hồi quy thường: mở lại lỗ hổng là ĐỎ ngay, không còn núp
    dưới nhãn xfail.

    TXN-0001 (sample_db) giữa USR-A/USR-B — USR-CSKH đóng vai 'khách lạ' có
    JWT customer hợp lệ khác, gọi thẳng route REST, không qua AI.
    """
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


def test_create_ticket_does_not_verify_trans_id_belongs_to_caller(client, sample_db):
    """C4/BOLA đường `create_ticket` — người lạ không được mở hồ sơ trên giao
    dịch của người khác.

    ⚠️ BẢN CŨ CỦA TEST NÀY KHÔNG CANH THỨ NÓ TUYÊN BỐ (sửa 15/08).
    Docstring cũ viết *"TXN-0001 thuộc về USR-A — USR-B (khách khác)"*. Sai:
    tra `tests/conftest.py` thì TXN-0001 là `900000000001` (USR-A) →
    `900000000002` (**USR-B**), tức **USR-B là BÊN NHẬN hợp pháp**. Một bên
    của giao dịch mở hồ sơ khiếu nại về chính giao dịch đó là hành vi ĐÚNG,
    không phải BOLA. Test vì vậy không chứng minh được lỗ hổng nào — nó chỉ
    khẳng định hệ thống chặn một việc lẽ ra phải cho phép.

    Đúng lớp lỗi đã thành luật của dự án: **assertion trùng với thứ hệ thống
    vốn làm, nên không kiểm được gì**. Ở đây còn tệ hơn một bậc — nếu bản vá
    C4 làm đúng (cho phép bên nhận), test này sẽ đỏ và tố cáo oan bản vá đúng.

    Nay dùng NGƯỜI LẠ THẬT: USR-CSKH mang JWT vai `customer`, không phải bên
    gửi cũng không phải bên nhận của TXN-0001 — cùng chuẩn "khách lạ" mà
    `test_customer_cannot_lookup_unrelated_transaction_via_rest_shortcut` dùng.
    """
    fresh_token = _stale_otp_token("USR-CSKH", 1)
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
        f"Khách lạ (USR-CSKH, không phải bên nào của TXN-0001) tạo được ticket "
        f"tham chiếu giao dịch này mà không bị chặn: {resp.status_code} {resp.text}"
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


def test_create_ticket_van_cho_phep_ben_nhan_hop_phap_mo_ho_so(client, sample_db):
    """Ca ĐỐI CHỨNG của test trên — bản vá C4 không được chặn nhầm người có quyền.

    TXN-0001 là `900000000001` (USR-A) → `900000000002` (USR-B). **USR-B là bên
    NHẬN**, nên họ mở hồ sơ khiếu nại về chính giao dịch đó là hoàn toàn hợp lệ
    (khách báo "tiền chưa về" thì đúng là bên nhận đi khiếu nại).

    Vì sao ca này bắt buộc phải có: thiếu nó, một bản vá "chặn cho chắc" — ví
    dụ chỉ cho BÊN GỬI mở hồ sơ — vẫn làm test chặn-người-lạ xanh mướt, trong
    khi sản phẩm vừa cấm mất một nửa số khách hàng có quyền khiếu nại thật.
    Đây cũng chính là bản chất lỗi của bản CŨ test kia: nó nhầm USR-B thành
    người lạ, nên nếu bản vá làm ĐÚNG thì nó lại tố cáo oan.
    """
    token = _stale_otp_token("USR-B", 1)
    resp = client.post(
        "/tools/create_ticket",
        json={
            "complaint_type": "money_not_received",
            "scope": "internal_wallet",
            "description_raw": "Bên gửi báo đã chuyển nhưng ví tôi chưa nhận được.",
            "trans_id": "TXN-0001",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, (
        f"BÊN NHẬN hợp pháp của TXN-0001 bị chặn không mở được hồ sơ: "
        f"{resp.status_code} {resp.text[:200]}"
    )
    assert resp.json().get("ticket_id"), resp.text
