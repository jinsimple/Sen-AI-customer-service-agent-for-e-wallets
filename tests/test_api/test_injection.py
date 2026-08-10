"""Nhóm C3 — input độc hại vào các trường tự do (OWASP ASVS input validation).

SQLAlchemy ORM đã tham số hoá query sẵn nên rủi ro SQL injection thấp — các
test dưới đây là BẰNG CHỨNG xác nhận điều đó bằng thực nghiệm, không phải giả
định suông. API trả JSON (không phải HTML) nên rủi ro XSS thật sự nằm ở tầng
frontend render (React tự escape mặc định) — test ở đây xác nhận API lưu/trả
payload NGUYÊN VĂN dạng dữ liệu thô, không "thực thi"/biến dạng gì cả.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.api.deps import get_session
from src.api.main import app
from src.auth import create_access_token
from src.db.models import User

SQLI_PAYLOADS = [
    "'; DROP TABLE tickets; --",
    "' OR '1'='1",
    "1; DELETE FROM users WHERE '1'='1'; --",
]
XSS_PAYLOADS = [
    "<script>alert('xss')</script>",
    "<img src=x onerror=alert(1)>",
]


@pytest.fixture()
def client(sample_db):
    def _override_session():
        yield sample_db

    app.dependency_overrides[get_session] = _override_session
    yield TestClient(app)
    app.dependency_overrides.clear()


def _auth(role: str, user_id: str) -> dict:
    token = create_access_token(user_id=user_id, role=role)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize("payload", SQLI_PAYLOADS + XSS_PAYLOADS)
def test_create_ticket_description_injection_is_inert(client, sample_db, payload):
    resp = client.post(
        "/tools/create_ticket",
        headers=_auth("customer", "USR-A"),
        json={
            "complaint_type": "wrong_recipient",
            "scope": "internal_wallet",
            "description_raw": payload,
            "trans_id": "TXN-0001",
        },
    )
    assert resp.status_code in (200, 400), (
        f"payload gây lỗi hệ thống thay vì xử lý sạch (200 tạo được/400 validation từ chối hợp lệ, "
        f"không được 500): {resp.status_code} {resp.text[:200]}"
    )

    if resp.status_code == 200:
        ticket_id = resp.json()["ticket_id"]
        detail = client.get(f"/tickets/{ticket_id}", headers=_auth("cskh", "USR-CSKH"))
        assert detail.status_code == 200
        # Lưu/trả về NGUYÊN VĂN — không bị "thực thi" hay biến dạng thành gì khác.
        assert detail.json()["complaint"]["description_raw"] == payload

    # Bằng chứng thực nghiệm: bảng users vẫn còn nguyên dù payload gõ y hệt
    # lệnh DROP/DELETE — SQL injection không có tác dụng qua ORM tham số hoá.
    assert sample_db.query(User).count() > 0


@pytest.mark.parametrize("payload", SQLI_PAYLOADS)
def test_policy_search_query_injection_no_crash(client, payload, monkeypatch):
    # search_policy_text gọi OpenAI embeddings thật (src/rag/store.py) — không
    # liên quan tới thứ đang kiểm ở đây (injection vào query string), mock lại
    # đúng theo pattern tests/test_rag/test_ingest.py để test chạy được không
    # cần OPENAI_API_KEY thật.
    monkeypatch.setattr("src.rag.search.store.search", lambda query, k: [])
    resp = client.post("/policy-search", headers=_auth("cskh", "USR-CSKH"), json={"query": payload})
    assert resp.status_code == 200
    assert resp.json()["status"] in ("found", "not_found")


def test_request_more_info_note_injection_no_crash(client):
    # Ticket không tồn tại — chỉ xác nhận input độc hại không gây lỗi hệ
    # thống khác thường (500) so với input sạch, vẫn 404 đúng logic nghiệp vụ.
    resp = client.post(
        "/tickets/TCK-KHONG-TON-TAI/request-more-info",
        headers=_auth("cskh", "USR-CSKH"),
        json={"note": "'; DROP TABLE tickets; --<script>alert(1)</script>"},
    )
    assert resp.status_code == 404


def test_policy_doc_upload_path_traversal_filename_is_safe(client, sample_db):
    admin = User(
        user_id="USR-PA-TEST", role="partner_admin", full_name="Test PA", phone="0900000001", kyc_level=0,
    )
    from datetime import datetime

    admin.created_at = datetime(2026, 1, 1)
    sample_db.add(admin)
    sample_db.commit()

    resp = client.post(
        "/policy-docs",
        headers=_auth("partner_admin", "USR-PA-TEST"),
        files={"file": ("../../../../etc/passwd.txt", b"noi dung test khong lien quan", "text/plain")},
    )
    # Không được 500 (crash) — hoặc parse như file .txt thường (200), hoặc từ
    # chối định dạng (400) — tên file độc hại không được phép ảnh hưởng tới
    # đường dẫn ghi file thật (ingest_document chỉ dùng filename để hiển thị/
    # lưu DB, không dùng làm đường dẫn ghi đĩa trực tiếp).
    assert resp.status_code in (200, 400)
