"""Nhóm C — tự động hoá ma trận phân quyền (C2 BOLA/BFLA, OWASP API Top 10)
đã verify tay bằng curl trong scripts/verify_security.sh — giữ nguyên script
đó cho việc chạy tay, suite này chạy trong CI mỗi PR.

Chỉ kiểm ĐÚNG lớp uỷ quyền (401 không token / 403 sai role) — KHÔNG gọi tới
business logic thật cho case "role đúng" ở các route tốn phí/side-effect
(agent/chat gọi OpenAI thật, create_ticket ghi DB thật...) để giữ suite nhanh
và rẻ. Route GET thuần đọc, không side-effect/không LLM thì test luôn cả case
role đúng (200 hoặc 404 — cả 2 đều là "qua được cổng phân quyền").

`test_no_untested_route_missing_from_matrix` tự đối chiếu với `app.routes` —
route mới thêm vào src/api/main.py mà quên khai báo ở đây sẽ FAIL rõ ràng,
tránh suite lạc hậu âm thầm.
"""
from __future__ import annotations

from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient

from src.api.deps import get_session
from src.api.main import app
from src.auth import create_access_token

ALL_ROLES = {"customer", "cskh", "supervisor", "partner_admin"}


@dataclass
class RouteCheck:
    method: str
    path_template: str  # phải khớp NGUYÊN VĂN route.path của FastAPI (đối chiếu app.routes)
    concrete_path: str  # path thật gửi trong test (thay {id} bằng giá trị giả không tồn tại)
    allowed_roles: set[str]
    body: dict | None = None
    is_multipart: bool = False
    safe_success_check: bool = False  # True: route GET thuần đọc, test luôn case role đúng


ROUTES: list[RouteCheck] = [
    RouteCheck("POST", "/auth/otp/request", "/auth/otp/request", {"customer"}, body={}),
    RouteCheck(
        "POST", "/auth/otp/verify", "/auth/otp/verify", {"customer"},
        body={"otp_code": "000000", "security_answer": "wrong"},
    ),
    RouteCheck("POST", "/tools/lookup_transaction", "/tools/lookup_transaction", ALL_ROLES, body={"trans_id": "TXN-NOPE"}),
    RouteCheck("POST", "/tools/get_customer_history", "/tools/get_customer_history", {"customer"}, body={}),
    RouteCheck(
        "POST", "/tools/create_ticket", "/tools/create_ticket", {"customer"},
        body={"complaint_type": "wrong_recipient", "scope": "internal_wallet", "description_raw": "test"},
    ),
    RouteCheck(
        "POST", "/tools/propose_resolution", "/tools/propose_resolution", {"cskh", "supervisor"},
        body={"ticket_id": "TCK-NOPE", "action_type": "no_action", "rationale": "test"},
    ),
    RouteCheck(
        "POST", "/tools/escalate_ticket", "/tools/escalate_ticket", {"cskh", "supervisor"},
        body={"ticket_id": "TCK-NOPE", "target": "partner_bank", "reason": "test"},
    ),
    RouteCheck("POST", "/agent/chat", "/agent/chat", {"customer"}, body={"message": "test"}),
    RouteCheck("GET", "/tickets", "/tickets", {"cskh", "supervisor"}, safe_success_check=True),
    RouteCheck("GET", "/tickets/{ticket_id}", "/tickets/TCK-NOPE", {"cskh", "supervisor"}, safe_success_check=True),
    RouteCheck("POST", "/resolutions/{resolution_id}/approve", "/resolutions/RES-NOPE/approve", {"supervisor"}),
    RouteCheck("POST", "/resolutions/{resolution_id}/reject", "/resolutions/RES-NOPE/reject", {"supervisor"}),
    RouteCheck("GET", "/resolutions", "/resolutions", {"cskh", "supervisor"}, safe_success_check=True),
    RouteCheck(
        "POST", "/tickets/{ticket_id}/request-more-info", "/tickets/TCK-NOPE/request-more-info",
        {"cskh", "supervisor"}, body={},
    ),
    RouteCheck("GET", "/reports/summary", "/reports/summary", {"cskh", "supervisor"}, safe_success_check=True),
    RouteCheck("POST", "/policy-docs", "/policy-docs", {"partner_admin"}, is_multipart=True),
    RouteCheck("GET", "/policy-docs", "/policy-docs", {"partner_admin"}, safe_success_check=True),
    RouteCheck("DELETE", "/policy-docs/{doc_id}", "/policy-docs/DOC-NOPE", {"partner_admin"}),
    RouteCheck("POST", "/policy-search", "/policy-search", {"cskh", "supervisor"}, body={"query": "test"}),
]

# Route công khai (không cần token), ngoài phạm vi phân quyền nghiệp vụ, hoặc
# do FastAPI tự sinh (Swagger/OpenAPI) — loại khỏi yêu cầu "phải có trong ROUTES".
PUBLIC_ROUTES = {
    ("POST", "/auth/login"),
    ("GET", "/health"),
    ("GET", "/openapi.json"),
    ("GET", "/docs"),
    ("GET", "/docs/oauth2-redirect"),
    ("GET", "/redoc"),
}


@pytest.fixture()
def client(sample_db):
    def _override_session():
        # Phải commit/rollback ĐÚNG như get_session() thật (src/api/deps.py)
        # — xem ghi chú tương tự ở tests/test_api/test_otp.py (bug thật tìm
        # được 2026-08-10: fixture chỉ yield không commit/rollback che mất 1
        # lỗi rollback thật trong verify_otp()).
        try:
            yield sample_db
            sample_db.commit()
        except Exception:
            sample_db.rollback()
            raise

    app.dependency_overrides[get_session] = _override_session
    yield TestClient(app)
    app.dependency_overrides.clear()


def _auth_headers(role: str, user_id: str = "USR-TEST") -> dict:
    token = create_access_token(user_id=user_id, role=role)
    return {"Authorization": f"Bearer {token}"}


def _send(client: TestClient, route: RouteCheck, headers: dict | None = None):
    kwargs = {"headers": headers} if headers else {}
    if route.method == "GET":
        return client.get(route.concrete_path, **kwargs)
    if route.method == "DELETE":
        return client.delete(route.concrete_path, **kwargs)
    if route.is_multipart:
        return client.post(route.concrete_path, files={"file": ("t.txt", b"noi dung test", "text/plain")}, **kwargs)
    return client.request(route.method, route.concrete_path, json=route.body, **kwargs)


def test_no_untested_route_missing_from_matrix():
    """Route mới thêm vào main.py mà quên khai báo ở ROUTES sẽ FAIL ở đây —
    chặn suite lạc hậu âm thầm khi thêm endpoint mới."""
    tested = {(r.method, r.path_template) for r in ROUTES}
    missing = []
    for route in app.routes:
        methods = getattr(route, "methods", None)
        path = getattr(route, "path", None)
        if not methods or not path:
            continue
        for method in methods:
            if method in ("HEAD", "OPTIONS"):
                continue
            key = (method, path)
            if key in PUBLIC_ROUTES or key in tested:
                continue
            missing.append(key)
    assert not missing, f"Route chưa có trong ma trận test_authz_matrix: {missing}"


@pytest.mark.parametrize("route", ROUTES, ids=lambda r: f"{r.method} {r.path_template}")
def test_no_token_returns_401(client, route: RouteCheck):
    resp = _send(client, route, headers=None)
    assert resp.status_code == 401, f"{route.method} {route.path_template} không token phải 401, được {resp.status_code}"


@pytest.mark.parametrize("route", ROUTES, ids=lambda r: f"{r.method} {r.path_template}")
def test_wrong_role_returns_403(client, route: RouteCheck):
    disallowed = ALL_ROLES - route.allowed_roles
    for role in disallowed:
        resp = _send(client, route, headers=_auth_headers(role))
        assert resp.status_code == 403, (
            f"{route.method} {route.path_template} với role sai '{role}' phải 403, được {resp.status_code}: {resp.text[:200]}"
        )


@pytest.mark.parametrize("route", [r for r in ROUTES if r.safe_success_check], ids=lambda r: f"{r.method} {r.path_template}")
def test_correct_role_not_blocked_by_authz(client, route: RouteCheck):
    """Chỉ áp dụng cho GET thuần đọc, không side-effect/không gọi LLM — role
    đúng phải QUA ĐƯỢC cổng phân quyền (không phải 401/403). 200 hoặc 404 (case
    ticket_id giả không tồn tại) đều hợp lệ — điều cần xác nhận là không bị
    chặn NHẦM ở tầng uỷ quyền."""
    for role in route.allowed_roles:
        resp = _send(client, route, headers=_auth_headers(role))
        assert resp.status_code not in (401, 403), (
            f"{route.method} {route.path_template} với role ĐÚNG '{role}' bị chặn nhầm: {resp.status_code}"
        )


def test_fake_token_returns_401(client):
    resp = client.get("/tickets", headers={"Authorization": "Bearer eyFake.Not.AJwt"})
    assert resp.status_code == 401


def test_wrong_scheme_returns_401(client):
    resp = client.get("/tickets", headers={"Authorization": "Basic dXNlcjpwYXNz"})
    assert resp.status_code == 401
