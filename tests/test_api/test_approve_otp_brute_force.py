"""F-12 — OTP duyệt tiền phải có lockout, không brute-force được.

Nguồn đặc tả: `docs/security/review-phase01-ap-that.md` F-12 (mức CAO, security
gọi là phát hiện nặng nhất đợt). Viết từ đặc tả, KHÔNG đọc `src/`.

BẰNG CHỨNG CỦA SECURITY (đo thật trên stack đang chạy): **60 lần gửi mã SAI
liên tiếp, 275 req/s, 0 lần 429**; sau đó challenge vẫn `failed_attempts=0`,
`otp_status='pending'`, `otp_code` còn sống.

ĐỐI XỨNG BỊ GÃY — đây là cốt lõi của phát hiện: đường OTP của **khách**
(`/auth/otp/verify`) có ĐỦ CẢ HAI lớp — rate limit và khoá sau
`OTP_MAX_FAILED_ATTEMPTS` lần sai (xem `tests/test_api/test_otp.py::
test_otp_verify_locks_after_max_failed_attempts`). Đường **duyệt tiền** thì
không có lớp nào. Tức là đường ÍT rủi ro hơn được bảo vệ, đường CHẠM TIỀN thì
để ngỏ.

Đường tấn công: kẻ đã chiếm được phiên supervisor — **đúng kịch bản mà OTP
step-up sinh ra để chặn** — dò 6 chữ số trong cửa sổ 10 phút. Ở tốc độ security
đo được là ~15% mỗi cửa sổ, và xin challenge mới được 10 lần/phút. Vi phạm NIST
800-63B §5.2.2 và làm rỗng nghĩa PSD2 dynamic linking: OTP gắn đúng số tiền
chẳng để làm gì nếu đoán được mã.

Test này viết TRƯỚC bản vá nên sẽ ĐỎ — nó là bài nghiệm thu sẵn cho fix.
"""
from __future__ import annotations

import datetime as dt

import pytest
from fastapi.testclient import TestClient

from src.api.deps import get_session
from src.api.main import app
from src.auth import create_access_token
from src.config import OTP_MAX_FAILED_ATTEMPTS
from src.db.models import AuthSession, Resolution
from src.tools.create_ticket import create_ticket
from src.tools.propose_resolution import propose_resolution

MA_SAI = "000000"


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


def _auth_sep() -> dict:
    token = create_access_token(user_id="USR-SUP", role="supervisor", otp_verified_at=dt.datetime.utcnow())
    return {"Authorization": f"Bearer {token}"}


def _make_resolution(sample_db) -> str:
    ticket = create_ticket(
        sample_db, user_id="USR-A", complaint_type="wrong_recipient", scope="internal_wallet",
        description_raw="test F-12", trans_id="TXN-0001",
    )
    resolution = propose_resolution(
        sample_db, ticket_id=ticket["ticket_id"], action_type="refund_to_wallet",
        rationale="ly do test", amount=92_000, created_by="USR-CSKH",
    )
    return resolution["resolution_id"]


def _xin_challenge(client, resolution_id: str) -> dict:
    resp = client.post(f"/resolutions/{resolution_id}/request-approval-otp", headers=_auth_sep())
    assert resp.status_code == 200, resp.text
    return resp.json()


def _thu_duyet(client, resolution_id: str, session_id: str, otp_code: str):
    return client.post(
        f"/resolutions/{resolution_id}/approve",
        json={"session_id": session_id, "otp_code": otp_code},
        headers=_auth_sep(),
    )


def _challenge(sample_db, session_id: str) -> AuthSession:
    sample_db.expire_all()
    return sample_db.get(AuthSession, session_id)


def test_f12_ma_sai_lam_tang_failed_attempts(client, sample_db):
    """Điều kiện cần đầu tiên: hệ thống phải ĐẾM số lần sai.

    Không đếm thì không có gì để chặn — mọi lớp phòng thủ phía sau đều dựa
    trên con số này. `AuthSession` đã có sẵn cột `failed_attempts` và docstring
    của nó ghi rõ ý định "tái dùng nguyên cơ chế đã có"; ý định nằm trong thiết
    kế mà không nằm trong code thì bằng không.
    """
    rid = _make_resolution(sample_db)
    ch = _xin_challenge(client, rid)

    resp = _thu_duyet(client, rid, ch["session_id"], MA_SAI)
    assert resp.status_code >= 400, f"Mã sai mà duyệt được: {resp.status_code} {resp.text[:200]}"

    sau = _challenge(sample_db, ch["session_id"])
    assert sau.failed_attempts >= 1, (
        f"`failed_attempts` vẫn = {sau.failed_attempts} sau 1 lần gửi mã sai. "
        "Không đếm thì không thể khoá — đây là gốc của F-12."
    )


def test_f12_khoa_sau_nguong_va_khong_tu_mo_lai(client, sample_db):
    """Chạm ngưỡng -> khoá, và khoá phải TUYỆT ĐỐI.

    KHÔNG assert bằng mã HTTP đơn thuần — bài học rút ngay tại file này (bản
    đầu XANH GIẢ): route trả **403 cho cả "mã sai"**, nên `assert status == 403`
    thoả mãn ngay từ lần đoán đầu tiên, trong khi chẳng có cơ chế khoá nào tồn
    tại. Ba lần liên tiếp trong ngày tôi mắc đúng lớp lỗi này (SEC-B, nhóm A
    của `note`, và đây) — dấu hiệu chung: **assertion trùng với trạng thái mặc
    định của hệ thống**.

    Phân biệt bằng thứ chỉ đúng khi khoá THẬT xảy ra: cột `locked_at` trong DB
    chuyển từ NULL sang có giá trị. Đó là dữ kiện không thể vô tình thoả mãn.
    """
    rid = _make_resolution(sample_db)
    ch = _xin_challenge(client, rid)

    assert _challenge(sample_db, ch["session_id"]).locked_at is None, "Challenge mới đã bị khoá sẵn?"

    for lan in range(OTP_MAX_FAILED_ATTEMPTS + 1):
        resp = _thu_duyet(client, rid, ch["session_id"], MA_SAI)
        assert resp.status_code >= 400, f"Lần {lan + 1} mã sai mà duyệt được: {resp.text[:200]}"

    sau = _challenge(sample_db, ch["session_id"])
    assert sau.locked_at is not None, (
        f"Sau {OTP_MAX_FAILED_ATTEMPTS + 1} lần sai, `locked_at` vẫn NULL "
        f"(failed_attempts={sau.failed_attempts}) — challenge KHÔNG hề bị khoá. "
        "403 mà route đang trả chỉ có nghĩa 'mã sai', không phải 'đã khoá'."
    )

    lai = _thu_duyet(client, rid, ch["session_id"], MA_SAI)
    assert lai.status_code == 403, "Khoá tự mở lại — khoá phải chặn tuyệt đối."


def test_f12_da_khoa_thi_ma_dung_cung_khong_duyet_duoc(client, sample_db):
    """Test QUAN TRỌNG NHẤT file này.

    Một cơ chế khoá mà **mã đúng vẫn đi qua được** thì không phải là khoá — kẻ
    tấn công dò tới mã đúng vẫn thắng, và cả `failed_attempts` lẫn `locked_at`
    chỉ là trang trí. Đây đúng là loại "xanh vì lý do sai" nhưng ở tầng thiết
    kế: có đủ cột, có đủ số đếm, mà không chặn gì.
    """
    rid = _make_resolution(sample_db)
    ch = _xin_challenge(client, rid)
    ma_dung = ch["otp_code"]

    for _ in range(OTP_MAX_FAILED_ATTEMPTS + 1):
        _thu_duyet(client, rid, ch["session_id"], MA_SAI)

    resp = _thu_duyet(client, rid, ch["session_id"], ma_dung)
    assert resp.status_code == 403, (
        f"Challenge đã khoá nhưng MÃ ĐÚNG vẫn duyệt được (HTTP {resp.status_code}). "
        "Khoá không có tác dụng gì — kẻ dò ra mã vẫn duyệt được lệnh chạm tiền."
    )

    sample_db.expire_all()
    assert sample_db.get(Resolution, rid).status == "pending_approval", (
        "Resolution đã sang 'approved' qua một challenge bị khoá."
    )


def test_f12_hai_muoi_lan_gui_ma_sai_khong_lot_lan_nao(client, sample_db):
    """Tái hiện thu nhỏ phép đo của security (60 lần, 0 lần bị chặn).

    KHÔNG khẳng định cơ chế nào phải chặn (rate limit hay lockout) — đó là lựa
    chọn triển khai. Chỉ khẳng định điều contract quan tâm: **sau ngưỡng,
    không lần nào còn được xử lý như một lần đoán bình thường**. Nếu 20/20 lần
    đều trả 401 thì hệ thống đang cho dò không giới hạn.
    """
    rid = _make_resolution(sample_db)
    ch = _xin_challenge(client, rid)

    ma_loi = [_thu_duyet(client, rid, ch["session_id"], MA_SAI).status_code for _ in range(20)]
    assert all(m >= 400 for m in ma_loi), f"Có lần mã sai vẫn được duyệt: {ma_loi}"

    # Lại KHÔNG đếm mã HTTP (403 ở đây là "mã sai", không phải "đã khoá" — xem
    # docstring test trên). Bằng chứng duy nhất không thể vô tình thoả mãn:
    # hệ thống đã ĐẾM đủ và đã KHOÁ sau 20 lần dò liên tiếp.
    sau = _challenge(sample_db, ch["session_id"])
    assert sau.failed_attempts >= OTP_MAX_FAILED_ATTEMPTS, (
        f"20 lần dò liên tiếp mà `failed_attempts` chỉ = {sau.failed_attempts}. "
        "Đây chính là phép đo của security: gửi mã sai liên tiếp, không gì đếm lại."
    )
    assert sau.locked_at is not None or 429 in ma_loi, (
        f"20 lần dò liên tiếp: KHÔNG bị khoá (`locked_at` NULL) và KHÔNG lần nào 429. "
        f"Phân bố mã trả về: {ma_loi}. Hệ thống đang cho dò 6 chữ số không giới hạn "
        "trên một lệnh chạm tiền."
    )


def test_f12_dem_sai_khong_lam_doi_trang_thai_resolution(client, sample_db):
    """Mặt còn lại: cơ chế chống brute-force không được gây tác dụng phụ.

    Một bản vá 'chặn cho chắc' mà lỡ đụng vào trạng thái resolution sẽ tạo ra
    lỗi tệ hơn thứ nó vá.
    """
    rid = _make_resolution(sample_db)
    ch = _xin_challenge(client, rid)
    for _ in range(OTP_MAX_FAILED_ATTEMPTS + 2):
        _thu_duyet(client, rid, ch["session_id"], MA_SAI)

    sample_db.expire_all()
    res = sample_db.get(Resolution, rid)
    assert res.status == "pending_approval", f"Trạng thái đổi thành '{res.status}' chỉ vì gõ sai OTP."
    assert res.approved_by is None and res.approved_at is None, "Có dấu vết người duyệt dù chưa ai duyệt."
