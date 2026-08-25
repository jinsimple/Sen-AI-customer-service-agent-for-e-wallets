"""Nhóm identity/AUTH-* — OTP phiên làm việc + câu hỏi bảo mật THẬT ở backend
(Brief §7 #4, src/auth.py::require_otp_verified). TRƯỚC bản vá: OTP chỉ là
gate UI mô phỏng ở frontend, backend không kiểm tra gì — gọi thẳng agent/API
bằng JWT hợp lệ vẫn lấy được dữ liệu nhạy cảm không cần xác thực (phát hiện
thật khi đối chiếu bộ QA test FIN05_QA_TestCases.jsonl, nhóm AUTH-*).

Phạm vi gác OTP thật sự (quyết định sau khi phát hiện xung đột UX lúc build
Playwright — xem src/api/main.py comment tại lookup_transaction):
- `/tools/create_ticket` — gác ở TẦNG HTTP, không có lý do hợp lệ nào để bỏ
  qua (tạo ticket luôn là hành động tài chính/khiếu nại thật).
- `/tools/lookup_transaction`, `/tools/get_customer_history` — KHÔNG gác ở
  tầng HTTP (route còn phục vụ CSKH tra cứu khi xử lý ticket, và rail "Giao
  dịch gần đây" của khách hàng cần hiện ngay lúc vào trang, trước khi có cơ
  hội xác thực OTP). Gác ở TẦNG AGENT thay vào đó — build_customer_tools()
  (customer_tools.py) tự chặn khi otp_verified_at=None/quá hạn, đây mới là
  đường đi thật của 1 cuộc điều tra khiếu nại qua chat (US-002).

AUTH-005/007/008 (quyết định 2026-08-10, xem docs/TESTING.md): 2 ngưỡng "còn
tươi" khác nhau theo mức rủi ro — OTP_VIEW_MAX_MINUTES (12h) cho thao tác chỉ
xem, OTP_STEPUP_FRESH_MINUTES (15 phút) cho create_ticket. Test hạn dùng token
dựng SẴN với otp_verified_at LÙI VỀ QUÁ KHỨ thay vì chờ thời gian thật trôi
qua (không thể chờ 15 phút/12 giờ thật trong CI)."""
from __future__ import annotations

import datetime as dt

import jwt
import pytest
from fastapi.testclient import TestClient

from src.agents.tools.customer_tools import build_customer_tools
from src.api.deps import get_session
from src.api.main import app
from src.auth import create_access_token
from src.config import (
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
    OTP_MAX_FAILED_ATTEMPTS,
    OTP_STEPUP_FRESH_MINUTES,
    OTP_VIEW_MAX_MINUTES,
)


@pytest.fixture()
def client(sample_db):
    def _override_session():
        # Phải commit/rollback ĐÚNG như get_session() thật (src/api/deps.py)
        # — phát hiện thật (2026-08-10): fixture cũ chỉ `yield sample_db`
        # không commit/rollback, làm test PASS NHẦM dù verify_otp() có bug
        # thật (failed_attempts += 1 rồi raise HTTPException bị get_session()
        # thật rollback cuốn ngược — khoá sau N lần sai KHÔNG BAO GIỜ xảy ra
        # qua HTTP thật, phát hiện lúc test tay qua UI, không phải qua CI).
        try:
            yield sample_db
            sample_db.commit()
        except Exception:
            sample_db.rollback()
            raise

    app.dependency_overrides[get_session] = _override_session
    # slowapi Limiter là singleton module-level (src/api/main.py::limiter) —
    # state rate-limit sống SUỐT phiên pytest nếu không reset (cùng phát hiện
    # thật đã ghi ở tests/test_api/test_auth_login.py) — thêm
    # test_otp_request_rate_limited_per_user (AUTH5-05E, đợt nâng cấp Auth
    # Flow 2026-08-12) gọi /auth/otp/request 11 lần làm lộ ra gap này ở CHÍNH
    # file test này (trước đó mỗi test chỉ gọi 1-2 lần, chưa đủ cộng dồn chạm
    # ngưỡng 10/phút).
    app.state.limiter.reset()
    yield TestClient(app)
    app.state.limiter.reset()
    app.dependency_overrides.clear()


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _login_token() -> str:
    return create_access_token(user_id="USR-A", role="customer")


def test_create_ticket_blocked_without_otp(client):
    resp = client.post(
        "/tools/create_ticket",
        headers=_auth(_login_token()),
        json={"complaint_type": "wrong_recipient", "scope": "internal_wallet", "description_raw": "test"},
    )
    assert resp.status_code == 403
    assert "OTP" in resp.json()["detail"]


def test_lookup_transaction_and_history_not_blocked_by_http_gate(client):
    """KHÔNG gác OTP ở tầng HTTP cho 2 route này (xem docstring module) — vẫn
    phải qua được dù chưa xác thực OTP, agent tự gác ở tầng riêng."""
    token = _login_token()
    resp = client.post("/tools/lookup_transaction", headers=_auth(token), json={"trans_id": "TXN-NOPE"})
    assert resp.status_code != 403
    resp = client.post("/tools/get_customer_history", headers=_auth(token), json={})
    assert resp.status_code != 403


def test_agent_tools_blocked_when_otp_not_verified(sample_db):
    """Đường đi THẬT của 1 cuộc điều tra qua chat (US-002) — agent tự chặn
    tool nhạy cảm khi otp_verified_at=None, không phụ thuộc route HTTP nào."""
    tools = build_customer_tools(sample_db, user_id="USR-A", otp_verified_at=None)
    by_name = {t.name: t for t in tools}

    lookup_result = by_name["lookup_transaction"].invoke({"trans_id": "TXN-0001"})
    assert lookup_result["status"] == "error"
    assert "OTP" in lookup_result["message"]

    history_result = by_name["get_customer_history"].invoke({})
    assert history_result["status"] == "error"

    ticket_result = by_name["create_ticket"].invoke(
        {"complaint_type": "wrong_recipient", "scope": "internal_wallet", "description_raw": "test"}
    )
    assert ticket_result["status"] == "error"


def test_agent_tools_allowed_when_otp_verified(sample_db):
    tools = build_customer_tools(sample_db, user_id="USR-A", otp_verified_at=dt.datetime.utcnow().timestamp())
    by_name = {t.name: t for t in tools}
    result = by_name["lookup_transaction"].invoke({"trans_id": "TXN-0001"})
    assert result.get("status") != "error" or "OTP" not in result.get("message", "")


# ---------------------------------------------------------------------------
# AUTH-007/008 — ngưỡng "còn tươi" khác nhau theo mức rủi ro thao tác.
# ---------------------------------------------------------------------------


def test_view_tools_allowed_within_12h_but_stepup_action_needs_fresher_otp(sample_db):
    """AUTH-008: create_ticket cần xác thực TƯƠI HƠN thao tác chỉ xem. Dựng
    otp_verified_at ở 30 phút trước — quá hạn step-up (15 phút) nhưng còn
    trong hạn xem (12h)."""
    verified_30min_ago = (dt.datetime.utcnow() - dt.timedelta(minutes=30)).timestamp()
    tools = build_customer_tools(sample_db, user_id="USR-A", otp_verified_at=verified_30min_ago)
    by_name = {t.name: t for t in tools}

    lookup_result = by_name["lookup_transaction"].invoke({"trans_id": "TXN-0001"})
    assert lookup_result.get("status") != "error" or "OTP" not in lookup_result.get("message", "")

    ticket_result = by_name["create_ticket"].invoke(
        {"complaint_type": "wrong_recipient", "scope": "internal_wallet", "description_raw": "test"}
    )
    assert ticket_result["status"] == "error"
    assert "hạn" in ticket_result["message"] or "OTP" in ticket_result["message"]


def test_nguong_otp_khop_loi_hua_prd_17():
    """PRD §17 (FIN05-PRD.md) — ngưỡng cứng: OTP xem ≤12h · OTP hành động ≤15p.

    Test biên bên dưới (`+1`/`-1` phút quanh hằng số) canh MÁY CÓ THI HÀNH hằng
    số hiện tại không — chúng đỏ được nếu enforcement gãy, nhưng KHÔNG đỏ nếu
    ai đổi chính hằng số (test biên khi đó chuyển sang canh SỐ MỚI một cách im
    lặng). Ca này canh CON SỐ, độc lập với ca biên — đổi hằng số làm ĐÚNG ca
    này đỏ, đúng chỗ hai loại gate bổ khuyết nhau."""
    assert OTP_VIEW_MAX_MINUTES == 720, (
        f"OTP_VIEW_MAX_MINUTES={OTP_VIEW_MAX_MINUTES} lệch ngưỡng PRD §17 "
        "'OTP xem dữ liệu ≤ 12 giờ' (720 phút)."
    )
    assert OTP_STEPUP_FRESH_MINUTES == 15, (
        f"OTP_STEPUP_FRESH_MINUTES={OTP_STEPUP_FRESH_MINUTES} lệch ngưỡng PRD §17 "
        "'OTP hành động có hậu quả ≤ 15 phút'."
    )


def test_view_tools_blocked_after_12h_absolute_max(sample_db):
    """AUTH-007: quá OTP_VIEW_MAX_MINUTES (12h) — kể cả thao tác chỉ xem cũng
    phải xác thực OTP lại (NIST 800-63B AAL2 reauth mốc tuyệt đối)."""
    verified_too_long_ago = (
        dt.datetime.utcnow() - dt.timedelta(minutes=OTP_VIEW_MAX_MINUTES + 1)
    ).timestamp()
    tools = build_customer_tools(sample_db, user_id="USR-A", otp_verified_at=verified_too_long_ago)
    by_name = {t.name: t for t in tools}

    lookup_result = by_name["lookup_transaction"].invoke({"trans_id": "TXN-0001"})
    assert lookup_result["status"] == "error"


def test_stepup_action_allowed_when_within_fresh_window(sample_db):
    verified_just_now = (
        dt.datetime.utcnow() - dt.timedelta(minutes=OTP_STEPUP_FRESH_MINUTES - 1)
    ).timestamp()
    tools = build_customer_tools(sample_db, user_id="USR-A", otp_verified_at=verified_just_now)
    by_name = {t.name: t for t in tools}
    ticket_result = by_name["create_ticket"].invoke(
        {"complaint_type": "wrong_recipient", "scope": "internal_wallet", "description_raw": "test"}
    )
    assert ticket_result.get("status") != "error" or "hạn" not in ticket_result.get("message", "")


def test_http_create_ticket_gate_rejects_stale_otp_beyond_stepup_window(client):
    """require_otp_verified (src/auth.py, gắn ở /tools/create_ticket) cũng
    phải áp đúng ngưỡng step-up 15 phút, không phải chỉ tầng agent."""
    stale_at = dt.datetime.utcnow() - dt.timedelta(minutes=OTP_STEPUP_FRESH_MINUTES + 1)
    stale_token = create_access_token(user_id="USR-A", role="customer", otp_verified_at=stale_at)
    resp = client.post(
        "/tools/create_ticket",
        headers=_auth(stale_token),
        json={"complaint_type": "wrong_recipient", "scope": "internal_wallet", "description_raw": "test"},
    )
    assert resp.status_code == 403
    assert "OTP" in resp.json()["detail"]


def test_otp_request_returns_code_and_question(client):
    resp = client.post("/auth/otp/request", headers=_auth(_login_token()))
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["otp_code"]) == 6
    assert "security_question" in body


def test_otp_request_rate_limited_per_user(client):
    """AUTH5-05E — khoá theo user_id (không chỉ IP), chặn brute-force mã OTP
    nhắm 1 user cụ thể kể cả khi kẻ tấn công đổi IP liên tục."""
    login_token = _login_token()
    for _ in range(10):
        resp = client.post("/auth/otp/request", headers=_auth(login_token))
        assert resp.status_code == 200
    blocked = client.post("/auth/otp/request", headers=_auth(login_token))
    assert blocked.status_code == 429


def test_otp_verify_wrong_code_increments_failed_attempts(client):
    login_token = _login_token()
    session_id = client.post("/auth/otp/request", headers=_auth(login_token)).json()["session_id"]
    resp = client.post(
        "/auth/otp/verify",
        headers=_auth(login_token),
        json={"session_id": session_id, "otp_code": "000000"},
    )
    assert resp.status_code == 401


def test_otp_verify_locks_after_max_failed_attempts(client):
    login_token = _login_token()
    session_id = client.post("/auth/otp/request", headers=_auth(login_token)).json()["session_id"]
    for _ in range(OTP_MAX_FAILED_ATTEMPTS - 1):
        resp = client.post(
            "/auth/otp/verify", headers=_auth(login_token), json={"session_id": session_id, "otp_code": "000000"}
        )
        assert resp.status_code == 401
    # Lần cuối chạm ngưỡng -> khoá (403), không phải 401 sai bình thường nữa.
    resp = client.post(
        "/auth/otp/verify", headers=_auth(login_token), json={"session_id": session_id, "otp_code": "000000"}
    )
    assert resp.status_code == 403
    assert "khoá" in resp.json()["detail"]

    # Đã khoá -> gọi lại lần nữa vẫn phải bị chặn (403), không quay lại 401
    # "sai bình thường" — khoá phải chặn TUYỆT ĐỐI, không tự mở lại.
    resp = client.post(
        "/auth/otp/verify",
        headers=_auth(login_token),
        json={"session_id": session_id, "otp_code": "000000"},
    )
    assert resp.status_code == 403


def test_otp_verify_correct_then_create_ticket_succeeds(client):
    login_token = _login_token()
    otp_resp = client.post("/auth/otp/request", headers=_auth(login_token))
    session_id = otp_resp.json()["session_id"]
    otp_code = otp_resp.json()["otp_code"]

    verify_resp = client.post(
        "/auth/otp/verify",
        headers=_auth(login_token),
        json={"session_id": session_id, "otp_code": otp_code},
    )
    assert verify_resp.status_code == 200
    new_token = verify_resp.json()["access_token"]
    assert verify_resp.json()["otp_verified"] is True

    resp = client.post(
        "/tools/create_ticket",
        headers=_auth(new_token),
        json={"complaint_type": "wrong_recipient", "scope": "internal_wallet", "description_raw": "test"},
    )
    # Không còn bị OTP chặn nữa — 200 hoặc lỗi nghiệp vụ khác, tuyệt đối
    # KHÔNG phải 403 do thiếu OTP.
    assert resp.status_code != 403


def test_otp_verify_session_id_must_belong_to_caller(client):
    """Vá race condition 2026-08-13 — session_id là khoá tra cứu chính, nhưng
    vẫn phải xác nhận đúng chủ sở hữu, không cho verify hộ session của người
    khác dù đoán trúng session_id (không phải bí mật, chỉ là khoá chính)."""
    victim_token = create_access_token(user_id="USR-B", role="customer")
    victim_session = client.post("/auth/otp/request", headers=_auth(victim_token)).json()
    attacker_token = _login_token()  # USR-A
    resp = client.post(
        "/auth/otp/verify",
        headers=_auth(attacker_token),
        json={"session_id": victim_session["session_id"], "otp_code": victim_session["otp_code"]},
    )
    assert resp.status_code == 400


def test_otp_verify_preserves_original_iat_for_thread_continuity(client):
    """thread_id hội thoại = user_id:iat (src/agents/graph.py) — cấp lại JWT
    lúc verify OTP KHÔNG được đổi iat, nếu không sẽ làm agent "quên" ngữ cảnh
    đã nói với khách trước khi xác thực xong trong CÙNG 1 phiên chat."""
    login_token = _login_token()
    original_iat = jwt.decode(login_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])["iat"]

    otp_resp = client.post("/auth/otp/request", headers=_auth(login_token)).json()
    verify_resp = client.post(
        "/auth/otp/verify",
        headers=_auth(login_token),
        json={"session_id": otp_resp["session_id"], "otp_code": otp_resp["otp_code"]},
    )
    new_token = verify_resp.json()["access_token"]
    new_iat = jwt.decode(new_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])["iat"]
    assert new_iat == original_iat


# ---------------------------------------------------------------------------
# Đối chứng khoá hành vi — token CŨ (trước verify) vẫn PHẢI bị chặn sau khi
# MỘT token khác (mới, cùng user) đã xác thực OTP thành công.
#
# Bối cảnh (24/08): PO thật tự tìm ra bug Ở FRONTEND — ChatClient.tsx gọi
# `await verifyOtp(...)` rồi VỨT kết quả, không lưu access_token MỚI, khiến
# mọi tin nhắn sau đó vẫn mang token CŨ (chưa xác thực) dù giao diện vừa báo
# "Xác thực thành công". Ca này KHÔNG vá frontend (ngoài vùng ghi tests/) —
# nó KHOÁ đúng hành vi backend đang có, để không ai "sửa" backend cho dễ
# (vd chuyển otp_verified thành cờ dùng chung theo user_id, thay vì đọc riêng
# từ CHÍNH token trình lên) mà vô tình mở toang cổng OTP cho MỌI token cũ của
# user đó — sẽ che mất bug thật thay vì lộ ra, và biến bug frontend thành lỗ
# hổng bảo mật thật (token cũ lộ ra ngoài vẫn dùng được sau khi chủ tài khoản
# xác thực OTP một lần bằng thiết bị khác).
#
# 🔴 KHÔNG viết qua /agent/chat như PO-agent đề xuất ban đầu: lookup_transaction/
# get_customer_history chỉ gác Ở TẦNG AGENT (build_customer_tools, xem docstring
# đầu file), tức phải có một lượt LangGraph THẬT gọi tool đó mới quan sát được
# — test_gd2_tool_calls_khong_null.py đã tự khai KHÔNG có tiền lệ dựng fake
# agent trả về trạng thái tool-call thành công đầy đủ ("KHÔNG đoán hình dạng
# state cần thiết — để SKIP kèm lý do"), và việc đó tốn LLM thật nếu không
# fake. /tools/create_ticket là route DUY NHẤT gác OTP Ở TẦNG HTTP (cùng
# docstring đầu file) — dùng route này để khoá đúng NGUYÊN TẮC (otp_verified_at
# đọc từ CHÍNH token trình lên, không phải trạng thái dùng chung theo user_id)
# bằng cơ chế THẬT, 0 token, đã có tiền lệ trực tiếp ở
# test_otp_verify_correct_then_create_ticket_succeeds ngay phía trên.
def test_token_cu_van_bi_chan_sau_khi_token_khac_cung_user_da_xac_thuc(client):
    login_token = _login_token()  # "token cũ" — CHƯA từng qua otp/verify
    otp_resp = client.post("/auth/otp/request", headers=_auth(login_token)).json()
    verify_resp = client.post(
        "/auth/otp/verify",
        headers=_auth(login_token),
        json={"session_id": otp_resp["session_id"], "otp_code": otp_resp["otp_code"]},
    )
    assert verify_resp.json()["otp_verified"] is True
    new_token = verify_resp.json()["access_token"]  # "token mới" — cùng user, đã xác thực

    # Đối chứng DƯƠNG trước — token MỚI phải dùng được (nếu vế này tự đỏ, ca
    # dưới không chứng minh được gì, đúng khuôn test_otp_verify_correct_then_create_ticket_succeeds).
    resp_new = client.post(
        "/tools/create_ticket",
        headers=_auth(new_token),
        json={"complaint_type": "wrong_recipient", "scope": "internal_wallet", "description_raw": "test"},
    )
    assert resp_new.status_code != 403, (
        f"Token MỚI (vừa otp/verify xong) vẫn bị 403 — vế đối chứng dương tự hỏng, "
        f"không dùng được để khẳng định gì về token cũ: {resp_new.text[:200]}"
    )

    # Ca CHÍNH — token CŨ, dùng NGAY SAU KHI token mới (cùng user_id) vừa xác
    # thực xong, PHẢI VẪN bị chặn. Nếu ca này đỏ (token cũ bỗng dùng được),
    # nghĩa là otp_verified đã trở thành trạng thái DÙNG CHUNG theo user_id
    # thay vì đọc riêng từ token — đúng lỗ PO-agent lo backend có thể vô tình
    # mở ra nếu "sửa" sai chỗ.
    resp_old = client.post(
        "/tools/create_ticket",
        headers=_auth(login_token),
        json={"complaint_type": "wrong_recipient", "scope": "internal_wallet", "description_raw": "test"},
    )
    assert resp_old.status_code == 403, (
        f"Token CŨ (chưa từng otp/verify) LẠI dùng được create_ticket ngay sau khi "
        f"token KHÁC của CÙNG user vừa xác thực OTP — otp_verified_at có vẻ đã thành "
        f"trạng thái dùng chung theo user_id thay vì đọc riêng từ từng token. "
        f"HTTP {resp_old.status_code}: {resp_old.text[:200]}"
    )
    assert "OTP" in resp_old.json()["detail"]
