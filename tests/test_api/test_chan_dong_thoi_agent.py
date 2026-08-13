"""Chặn đồng thời cho /agent/chat — hỏng có kiểm soát thay vì hỏng hỗn loạn.

VÌ SAO CÓ FILE NÀY (ADR-012)
----------------------------
`@limiter.limit("20/minute")` KHÔNG chặn được kịch bản 150 người cùng bấm gửi
trong 1 giây: mỗi người chỉ gọi đúng 1 lần, không ai vượt rate limit nào cả.
Nhưng 150 lượt agent chạy song song sẽ:
  (a) vét sạch threadpool 40 luồng của Starlette — FIN-05 chạy ĐÚNG 1 worker
      (bắt buộc vì MemorySaver giữ hội thoại trong RAM per-process), nên mọi
      người dùng chia chung một event loop duy nhất;
  (b) bắn đồng loạt vào OpenAI và ăn bão 429 — đo thật 2026-08-13: 1 lượt chat
      ~15.136 token, hạn mức 200.000 TPM => trần ~13 lượt/phút cho TOÀN hệ thống.

Bộ test này canh HAI CHIỀU:
  - vượt hạn -> từ chối NGAY với thông báo đọc được + Retry-After (không treo,
    không 500 trần trụi);
  - slot PHẢI được trả lại kể cả khi request lỗi — quên trả thì sau vài lỗi hệ
    thống tự bóp cổ mình với 0 request đang chạy.
"""

from __future__ import annotations

import pytest

from src.rate_limit import RedisConcurrencyLimiter


@pytest.fixture(autouse=True)
def _redis_sach():
    """Mỗi test bắt đầu với Redis sạch — fakeredis dùng chung giữa các test."""
    from src.redis_client import get_default_client

    get_default_client().flushall()
    yield


def test_cho_qua_dung_so_slot_roi_tu_choi():
    lim = RedisConcurrencyLimiter(max_concurrent=3, ttl_seconds=60, name="t1")
    tokens = [lim.acquire() for _ in range(3)]
    assert all(tokens), "3 slot đầu phải được cấp"
    assert lim.acquire() is None, "Slot thứ 4 phải bị từ chối khi max=3"
    assert lim.in_flight() == 3


def test_tra_slot_thi_cho_nguoi_tiep_theo_vao():
    lim = RedisConcurrencyLimiter(max_concurrent=2, ttl_seconds=60, name="t2")
    a, b = lim.acquire(), lim.acquire()
    assert lim.acquire() is None
    lim.release(a)
    assert lim.acquire() is not None, "Trả slot xong phải có chỗ cho người mới"
    lim.release(b)


def test_slot_tu_het_han_khi_process_chet_giua_chung():
    """LƯỚI AN TOÀN bắt buộc: process bị SIGKILL/OOM không kịp trả slot.

    Không có TTL thì hệ thống tự khoá VĨNH VIỄN với 0 request đang chạy —
    hỏng kiểu tệ nhất vì nhìn bên ngoài như hệ thống vẫn sống.
    """
    import time

    lim = RedisConcurrencyLimiter(max_concurrent=1, ttl_seconds=0.3, name="t3")
    assert lim.acquire() is not None
    assert lim.acquire() is None, "Đang đầy thì phải từ chối"
    time.sleep(0.5)
    assert lim.acquire() is not None, (
        "Slot quá hạn KHÔNG được tự thu hồi — process chết giữa chừng sẽ khoá "
        "hệ thống vĩnh viễn."
    )


def test_release_none_khong_no():
    """acquire() trả None (bị từ chối) thì release(None) phải im lặng bỏ qua."""
    lim = RedisConcurrencyLimiter(max_concurrent=1, ttl_seconds=60, name="t4")
    lim.release(None)  # không được ném exception


def test_dem_doc_lap_giua_cac_ten_khac_nhau():
    """Limiter của agent_chat không được ăn lẫn slot của tác vụ khác."""
    a = RedisConcurrencyLimiter(max_concurrent=1, ttl_seconds=60, name="agent")
    b = RedisConcurrencyLimiter(max_concurrent=1, ttl_seconds=60, name="khac")
    assert a.acquire() is not None
    assert b.acquire() is not None, "2 limiter khác tên phải đếm độc lập"
    assert a.acquire() is None


# ===========================================================================
# Đường HTTP THẬT — canh route /agent/chat, không chỉ canh class limiter
# ===========================================================================

@pytest.fixture
def client(sample_db, monkeypatch):
    from fastapi.testclient import TestClient

    from src.api import main as main_module
    from src.api.deps import get_session
    from src.api.main import app

    def _override_session():
        try:
            yield sample_db
        except Exception:
            sample_db.rollback()
            raise

    app.dependency_overrides[get_session] = _override_session
    app.state.limiter.reset()
    yield TestClient(app), main_module
    app.state.limiter.reset()
    app.dependency_overrides.clear()


def _token_khach():
    import datetime as dt

    from src.auth import create_access_token

    return create_access_token(
        user_id="USR-A", role="customer", iat=dt.datetime.utcnow(),
        otp_verified_at=dt.datetime.utcnow(),
    )


def test_het_slot_tra_503_co_thong_bao_doc_duoc(client, monkeypatch):
    """Quá tải phải báo rõ + Retry-After, KHÔNG treo và KHÔNG 500 trần trụi."""
    tc, main_module = client
    # Ép limiter đầy: max=0 => mọi request đều bị từ chối.
    monkeypatch.setattr(
        main_module, "_agent_turn_limiter",
        RedisConcurrencyLimiter(max_concurrent=0, ttl_seconds=60, name="agent_full"),
    )
    r = tc.post("/agent/chat", json={"message": "xin chào"},
                headers={"Authorization": f"Bearer {_token_khach()}"})

    assert r.status_code == 503, f"Phải trả 503 khi quá tải, nhận {r.status_code}"
    assert r.headers.get("Retry-After"), "Thiếu Retry-After — client không biết chờ bao lâu"
    chi_tiet = r.json().get("detail", "")
    assert "thử lại" in chi_tiet.lower(), (
        f"Thông báo phải hướng dẫn được người dùng, nhận: {chi_tiet!r}"
    )


def test_slot_duoc_tra_lai_ke_ca_khi_request_loi(client, monkeypatch):
    """finally BẮT BUỘC — thoát bằng exception mà không trả slot thì sau vài
    lỗi hệ thống tự khoá với 0 request đang chạy."""
    tc, main_module = client
    lim = RedisConcurrencyLimiter(max_concurrent=2, ttl_seconds=60, name="agent_err")
    monkeypatch.setattr(main_module, "_agent_turn_limiter", lim)

    def _no_ra_loi(*a, **kw):
        raise RuntimeError("lỗi giả lập bên trong agent")

    monkeypatch.setattr(main_module, "run_agent_turn", _no_ra_loi)

    for _ in range(3):
        try:
            tc.post("/agent/chat", json={"message": "xin chào"},
                    headers={"Authorization": f"Bearer {_token_khach()}"})
        except RuntimeError:
            pass  # TestClient ném lại exception của server — không sao, đang test slot

    assert lim.in_flight() == 0, (
        f"Còn {lim.in_flight()} slot chưa trả sau khi request lỗi — thiếu finally, "
        "hệ thống sẽ tự bóp cổ mình sau vài lỗi."
    )
