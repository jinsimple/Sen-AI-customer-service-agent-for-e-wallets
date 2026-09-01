"""AUTH5-01/01C (đợt nâng cấp Auth Flow, 2026-08-12, NIST SP 800-63B-4) —
VIẾT LẠI theo đúng ghi chú tự để lại trong bản gốc của file này ("nếu dòng
self-check FAIL nghĩa là code đã đổi... cập nhật lại 2 test theo thuật toán
mới thay vì chỉnh test cho pass lại").

Quyết định THẬT (PO chốt qua AskUserQuestion, 2026-08-12) khác hướng tài liệu
gốc giả định (chỉ nâng hash bcrypt/argon2): câu hỏi bảo mật (KBA) BỊ BỎ HẲN
khỏi vai trò xác thực — `POST /auth/otp/verify` giờ CHỈ kiểm mã OTP, không
còn so khớp `security_answer_hash` (xem src/api/main.py::verify_otp). Đây là
bản vá MẠNH HƠN "chỉ nâng hash" mà AUTH5-01 gốc đề xuất — loại bỏ hẳn class
lỗ hổng, không chỉ giảm nhẹ. `security_answer_hash` vẫn nâng lên argon2id có
salt (AUTH5-01C) như vệ sinh bảo mật cho dữ liệu vẫn lưu (hỗ trợ CSKH nhận
diện khách qua hotline), dù không còn gate route nào.

Không còn `@pytest.mark.security_finding` — đây là hành vi ĐÚNG đã implement,
không phải finding chờ vá."""
from __future__ import annotations

import pytest
from argon2 import PasswordHasher
from fastapi.testclient import TestClient

from src.api.deps import get_session
from src.api.main import app
from src.auth import create_access_token
from src.config import DATASET_SEED


def test_security_answer_hash_differs_across_calls_for_same_input():
    """argon2id tự sinh salt ngẫu nhiên mỗi lần .hash(), kể cả cùng input —
    2 lần hash CÙNG 1 câu trả lời phải ra 2 giá trị KHÁC nhau (khác SHA-256
    trần trước đây, luôn xác định/deterministic)."""
    hasher = PasswordHasher()
    same_answer = "Nguyễn Thị Bình"

    first = hasher.hash(same_answer)
    second = hasher.hash(same_answer)

    assert first != second
    # Cả 2 vẫn phải verify đúng lại được câu trả lời gốc — không chỉ khác
    # nhau ngẫu nhiên vô nghĩa.
    hasher.verify(first, same_answer)
    hasher.verify(second, same_answer)


def test_security_answer_hash_format_is_not_a_raw_fixed_length_digest():
    """Định dạng lưu thật (scripts/gen_dataset.py) phải tự mô tả thuật toán +
    salt nhúng sẵn (argon2 bắt đầu '$argon2'), không phải hex digest cố định
    64 ký tự (đặc trưng SHA-256 trần không salt)."""
    hasher = PasswordHasher()
    stored_hash = hasher.hash(f"ans-{DATASET_SEED}-USR-DEMO-0001")

    assert stored_hash.startswith("$argon2"), f"security_answer_hash phải là argon2id, được: {stored_hash[:20]}..."
    assert len(stored_hash) != 64, "vẫn có hình dạng hex digest cố định — chưa thật sự đổi thuật toán"


def test_gen_dataset_formula_stays_in_sync_with_new_hasher():
    """Test 'khoá' — đọc TRỰC TIẾP source, xác nhận scripts/gen_dataset.py
    thật sự dùng PasswordHasher (argon2id), không lặng lẽ quay lại sha256."""
    from src.config import ROOT_DIR

    gen_dataset_src = (ROOT_DIR / "scripts" / "gen_dataset.py").read_text(encoding="utf-8")
    assert "_PASSWORD_HASHER.hash(f\"ans-{self.seed}-{uid}\")" in gen_dataset_src, (
        "Công thức sinh security_answer_hash ở scripts/gen_dataset.py đã đổi — "
        "cập nhật lại test này theo thuật toán mới."
    )
    assert "hashlib.sha256(f\"ans-{self.seed}-{uid}\"" not in gen_dataset_src, (
        "security_answer_hash vẫn còn dùng SHA-256 trần — nâng cấp AUTH5-01C chưa hoàn tất."
    )


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
    app.state.limiter.reset()
    yield TestClient(app)
    app.state.limiter.reset()
    app.dependency_overrides.clear()


def test_verify_otp_no_longer_gates_on_security_answer(client, sample_db):
    """AUTH5-01 THẬT (không phải finding nữa) — /auth/otp/verify chấp nhận
    request THIẾU security_answer hoàn toàn (schema OtpVerifyRequest đã bỏ
    field này) miễn otp_code đúng. Trước bản vá: request này bị 422 (thiếu
    field bắt buộc) hoặc 401 (answer sai) — giờ phải 200."""
    from src.db.models import AuthSession
    from src.tools.base import new_id

    session_id = new_id("SES")
    sample_db.add(
        AuthSession(
            session_id=session_id,
            user_id="USR-A",
            otp_code="123456",
            otp_status="pending",
            security_q_passed=False,
            failed_attempts=0,
        )
    )
    sample_db.commit()

    token = create_access_token(user_id="USR-A", role="customer")
    resp = client.post(
        "/auth/otp/verify",
        json={"session_id": session_id, "otp_code": "123456"},  # KHÔNG có security_answer
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["otp_verified"] is True


def test_verify_otp_rejects_correct_otp_alone_is_still_gated_by_otp_itself(client, sample_db):
    """Đối chứng: KHÔNG phải mọi request đều qua — otp_code SAI vẫn bị từ
    chối (400 — lỗi PHÍA NGƯỜI GỌI, ĐÍNH CHÍNH 27/08: xem
    tests/test_api/test_otp.py::test_otp_verify_wrong_code_increments_failed_attempts,
    401 trước đây làm phiên còn sống bị đối xử như đã chết), chứng minh OTP
    vẫn là gate THẬT, chỉ có câu hỏi bảo mật là bị bỏ, không phải bỏ luôn
    toàn bộ xác thực."""
    from src.db.models import AuthSession
    from src.tools.base import new_id

    session_id = new_id("SES")
    sample_db.add(
        AuthSession(
            session_id=session_id,
            user_id="USR-A",
            otp_code="123456",
            otp_status="pending",
            security_q_passed=False,
            failed_attempts=0,
        )
    )
    sample_db.commit()

    token = create_access_token(user_id="USR-A", role="customer")
    resp = client.post(
        "/auth/otp/verify",
        json={"session_id": session_id, "otp_code": "000000"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
