"""Nhóm C3 — input độc hại vào các trường tự do (OWASP ASVS input validation).

SQLAlchemy ORM đã tham số hoá query sẵn nên rủi ro SQL injection thấp — các
test dưới đây là BẰNG CHỨNG xác nhận điều đó bằng thực nghiệm, không phải giả
định suông. API trả JSON (không phải HTML) nên rủi ro XSS thật sự nằm ở tầng
frontend render (React tự escape mặc định) — test ở đây xác nhận API lưu/trả
payload NGUYÊN VĂN dạng dữ liệu thô, không "thực thi"/biến dạng gì cả.
"""
from __future__ import annotations

import datetime as dt
import os.path
import pathlib

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from src.api.deps import get_session
from src.api.main import app
from src.auth import create_access_token
from src.db.models import User
from tests._ton_tien import duoc_phep_ton_tien, reason_text

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
        # Phải commit/rollback ĐÚNG như get_session() thật (src/api/deps.py)
        # — phát hiện thật (2026-08-10): fixture cũ chỉ `yield sample_db`
        # không commit/rollback, làm lộ SAI 1 bug thật (route mutate rồi
        # raise HTTPException, get_session() thật rollback cuốn ngược mutate
        # đó — src/api/main.py::verify_otp, failed_attempts không bao giờ
        # thật sự tăng qua HTTP) vì test đọc state trong cùng 1 session còn
        # nguyên trong bộ nhớ dù backend thật đã rollback mất.
        try:
            yield sample_db
            sample_db.commit()
        except Exception:
            sample_db.rollback()
            raise

    app.dependency_overrides[get_session] = _override_session
    yield TestClient(app)
    app.dependency_overrides.clear()


def _auth(role: str, user_id: str) -> dict:
    # otp_verified_at=vừa xác thực xong — các test injection ở đây kiểm input
    # độc hại, không phải luồng OTP (đã có tests/test_api/test_otp.py riêng).
    token = create_access_token(user_id=user_id, role=role, otp_verified_at=dt.datetime.utcnow())
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


# --------------------------------------------------------------------------
# Path traversal — mốc để kiểm HIỆU QUẢ, không chỉ mã trạng thái
# --------------------------------------------------------------------------

_GOC_REPO = pathlib.Path(__file__).resolve().parents[2]
# Payload nhắm `../../../../etc/passwd.txt` — bốn mức lên. Lấy dư một mức để
# không phải đoán đúng thư mục kho nằm sâu bao nhiêu.
_TO_TIEN = [_GOC_REPO, *list(_GOC_REPO.parents)[:5]]
_MOC_THOAT = [t / "etc" / "passwd.txt" for t in _TO_TIEN] + [t / "passwd.txt" for t in _TO_TIEN]


def _ten_tai_lieu(sample_db) -> set[str]:
    """Tên tệp ĐÃ LƯU, đọc thẳng bằng SQL trên `policy_documents`.

    Đọc bằng SQL chứ không qua model để ca này viết được từ ĐẶC TẢ: tên bảng và
    tên cột lấy từ `tests/test_migrations/test_migration_chain.py` và
    `tests/test_rag/test_thanh_phan_tai_lieu_kho.py:113`, không từ `src/`.
    """
    sample_db.expire_all()
    return {row_item[0] for row_item in sample_db.execute(text("SELECT filename FROM policy_documents;"))}


def _tao_partner_admin(sample_db) -> None:
    admin = User(
        user_id="USR-PA-TEST", role="partner_admin", full_name="Test PA", phone="0900000001", kyc_level=0,
    )
    admin.created_at = dt.datetime(2026, 1, 1)
    sample_db.add(admin)
    sample_db.commit()


def _nap(client, ten_tep: str, content_text: bytes = b"noi dung test khong lien quan"):
    return client.post(
        "/policy-docs",
        headers=_auth("partner_admin", "USR-PA-TEST"),
        files={"file": (ten_tep, content_text, "text/plain")},
    )


# 🔴 CỔNG CHI PHÍ — chỉ hai ca dưới đây, KHÔNG gắn cả file.
#
# Đo được 18/08 (tester): `POST /policy-docs` → ingest → **OpenAI
# /v1/embeddings THẬT**. Bằng chứng: `httpx` log `POST https://api.openai.com
# /v1/embeddings "HTTP/1.1 200 OK"` + `fin05.rag policy_doc_nap chunk_count:1`.
# Quét toàn bộ `tests/` với khoá giả cả hai nhà cung cấp (620/620 ca, kèm đối
# chứng dương): đây là **lời gọi duy nhất** rời khỏi máy trong cả suite, và nó
# **không qua `_ton_tien` lẫn `_dong_bang`**. `CLAUDE.md §7` in sẵn
# `pytest tests/` ⟹ người mới sẽ gõ nó và trả tiền mà không định.
#
# Vì sao gắn ĐÚNG HAI CA chứ không cả file (Luật J): 10 ca appsec còn lại
# (SQLi/XSS) đang canh đúng và **không tốn một xu**. Bịt một cổng bằng cách tắt
# một cổng khác là đổi ngang, không phải vá.
#
# 🔴 CÁI GIÁ, ghi ra để không ai phải tự phát hiện: mặc định TẮT nghĩa là cổng
# path-traversal **không chạy trong `pytest tests/` lẫn CI**. Đây là bản vá
# TẠM. Bản vá thật là một tầng nhúng giả ở `tests/` để hai ca này chạy 0 đồng —
# cần tech-lead chỉ ĐIỂM NỐI (tester không đọc `src/`).
_CONG_CHI_PHI = pytest.mark.skipif(
    not duoc_phep_ton_tien(),
    reason=reason_text(60, "2 lời gọi OpenAI /v1/embeddings qua POST /policy-docs"),
)


@_CONG_CHI_PHI
def test_policy_doc_upload_path_traversal_khong_ghi_tep_ra_ngoai_repo(client, sample_db):
    """Nửa HIỆU QUẢ TRÊN ĐĨA của ca traversal.

    Bản cũ (`..._filename_is_safe`) chỉ assert `status_code in (200, 400)` —
    tức nó kiểm "không crash", một tính chất THẬT nhưng **thuộc trục khác với
    trục tên nó hứa**. Nó đỏ suốt vì một `KeyError` trong logging, rồi xanh khi
    lỗi đó được vá, và trong CẢ HAI trạng thái nó chưa từng kiểm path traversal
    (`eval/QUET-TEN-HUA-KHAC-ASSERTION.md`, 17/08).

    🔴 Vì sao BẮT BUỘC có nửa đối chứng dương ở đầu: nếu `/policy-docs` không
    để lại dấu vết quan sát được nào, assertion "không tệp nào thoát ra" sẽ
    XANH VĨNH VIỄN — xanh vì KHÔNG CÓ GÌ XẢY RA, chứ không phải vì an toàn
    (Luật 1). Xanh kiểu đó trông y hệt xanh thật.

    🔴 PHẠM VI ca này chứng minh — khai ra để người sau không trích quá: nó
    chứng minh không có tệp mới nào ở **12 đích thoát cụ thể** mà payload nhắm
    tới. Nó KHÔNG chứng minh "không tệp nào ghi ra ngoài thư mục kho" ở dạng
    tổng quát — một tệp thoát khỏi thư mục kho nhưng vẫn NẰM TRONG cây repo sẽ
    không bị phép này bắt.
    """
    _tao_partner_admin(sample_db)

    resp_lanh = _nap(client, "chinh-sach-hoan-tien.txt", b"noi dung chinh sach lanh")
    assert resp_lanh.status_code == 200, (
        f"KHÔNG ĐO ĐƯỢC (không phải TRƯỢT): tệp .txt LÀNH bị từ chối "
        f"({resp_lanh.status_code}) — kênh quan sát chết, phần tấn công bên dưới "
        f"sẽ xanh mà không chứng minh gì. Body: {resp_lanh.text[:200]}"
    )
    ten_sau_doi_chung = _ten_tai_lieu(sample_db)
    assert any("chinh-sach-hoan-tien" in t for t in ten_sau_doi_chung), (
        f"KHÔNG ĐO ĐƯỢC: nạp lành trả 200 nhưng `policy_documents` không có hàng "
        f"nào mang tên đó ({sorted(ten_sau_doi_chung)}) — ta đang soi nhầm chỗ."
    )

    thoat_tu_truoc = {m for m in _MOC_THOAT if m.exists()}
    resp = _nap(client, "../../../../etc/passwd.txt")
    # Không được 500 (crash) — hoặc parse như .txt thường (200), hoặc từ chối
    # định dạng (400). Đây là assertion CŨ, giữ nguyên: nó có giá trị thật,
    # chỉ là nó không phải thứ tên ca hứa.
    assert resp.status_code in (200, 400), f"HTTP {resp.status_code}: {resp.text[:200]}"

    thoat_moi = sorted(str(m) for m in _MOC_THOAT if m.exists() and m not in thoat_tu_truoc)
    assert not thoat_moi, f"🔴 TRAVERSAL THẬT: tệp được ghi RA NGOÀI cây repo: {thoat_moi}"


@_CONG_CHI_PHI
@pytest.mark.xfail(
    strict=True,
    reason=(
        "FINDING 18/08 (tester, chưa có đồng thuận về mức độ ⟹ CỐ Ý không gắn "
        "`security_finding`): `policy_documents.filename` lưu NGUYÊN VĂN "
        "'../../../../etc/passwd.txt'. Chưa phải lỗ hổng hôm nay — cột này "
        "không được dùng làm đường ghi đĩa — nhưng nó là TIỀN ĐỀ của lỗ hổng "
        "ngày bất kỳ ai nối nó vào một đường ghi. `strict=True` để khi ai đó "
        "giam tên lại, CI báo XPASS và không ai kịp quên gỡ nhãn."
    ),
)
def test_policy_doc_upload_ten_tep_da_luu_phai_bi_giam(client, sample_db):
    """Nửa HIỆU QUẢ TRONG CSDL — phần thật sự mang đúng tên ca gốc.

    Tách khỏi ca trên **có chủ đích**: nửa trên đang canh được và phải ở lại
    cổng chính màu xanh; gộp chung rồi gắn nhãn thì cả hai nửa cùng bị ẩn khỏi
    `lint-and-test`, tức bản vá làm IM một phép kiểm đang chạy tốt (Luật J).
    """
    _tao_partner_admin(sample_db)
    before = _ten_tai_lieu(sample_db)

    resp = _nap(client, "../../../../etc/passwd.txt")
    assert resp.status_code in (200, 400), f"HTTP {resp.status_code}: {resp.text[:200]}"

    new_name = _ten_tai_lieu(sample_db) - before
    if resp.status_code == 200:
        assert len(new_name) == 1, (
            f"nạp trả 200 nhưng số hàng mới trong `policy_documents` là "
            f"{len(new_name)}, chờ đúng 1: {sorted(new_name)} — KHÔNG ĐO ĐƯỢC"
        )
    assert new_name, "KHÔNG ĐO ĐƯỢC: không có hàng mới nào để soi tên"
    for name_text in new_name:
        assert name_text == os.path.basename(name_text) and ".." not in name_text, (
            f"🔴 tên tệp KHÔNG bị giam, lưu nguyên văn {name_text!r} trong "
            "`policy_documents`. 200/400 không nói gì về điều này — đây là trục "
            "mà tên ca gốc hứa."
        )
