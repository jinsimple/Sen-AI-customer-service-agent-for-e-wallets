"""Canh chính lớp cô lập Redis của `conftest.py` — bản vá 17/08.

## Vì sao một bản vá cần test canh, dù đã nghiệm thu ba chiều

Ngày 17/08 fixture `_flush_redis_between_tests` trong `conftest.py` được phát
hiện đã gọi `flushdb()` lên **Redis THẬT** của ngăn xếp `fin05-*`: đo được
`cmdstat_flushdb calls=437`, `DBSIZE` về 0, cuốn sạch phiên đăng nhập của mọi
người đang dùng. Nguyên nhân: docstring nói *"fakeredis trong test"* nhưng đó
là **giả định**, không phải ràng buộc — `flushdb()` gọi vào bất cứ client nào
`get_default_client()` trả về, và `docker exec <backend> pytest` thì `REDIS_URL`
là Redis thật.

Bản vá có hai lớp và **đã nghiệm thu ba chiều bằng tay**, gồm cả chính ca gây
hại (chạy trong container: 23/23 xanh, `flushdb` giữ nguyên 437). Nhưng nghiệm
thu bằng tay **không sống sót qua thời gian**:

> Người gỡ lớp bảo vệ sẽ **không thấy gì đỏ** — vì lỗi này không biểu hiện trên
> máy người gỡ. Nó biểu hiện trên Redis của **người bên cạnh**, ở một thời điểm
> không ai nối lại được với lệnh đã gây ra nó.

Đó chính là lý do nó chạy 437 lần mà không ai phát hiện: **người gây ra không
thấy hậu quả, người chịu hậu quả không thấy nguyên nhân.** Test dưới đây là thứ
duy nhất đứng giữa hai đầu đó.

## Ba test, ba mệnh đề độc lập

    lớp 1 CÓ HIỆU LỰC   — REDIS_URL bị ÉP về fake:// trước mọi import
    lớp 1 CÓ TÁC DỤNG   — client toàn cục thực sự là fakeredis, không chỉ biến đúng
    lớp 2 BẮT ĐƯỢC      — cổng nhận diện được một client THẬT

Test thứ hai không thừa: biến môi trường đúng mà client vẫn thật là hoàn toàn
có thể (conftest bị nạp sau module đầu tiên chạm `src.config`). Kiểm biến là
kiểm **ý định**; kiểm client là kiểm **kết quả**.
"""
from __future__ import annotations

import os

import pytest

from tests.conftest import _redis_la_gia


def test_lop1_ep_duoc_REDIS_URL_ve_ban_gia():
    """`REDIS_URL` phải là `fake://` bất kể môi trường vào là gì.

    Đây là mệnh đề mà `setdefault` KHÔNG bảo đảm: trong container biến đã có
    giá trị thật, `setdefault` im lặng nhường cho nó — đúng ca đã gây hại.
    """
    url = os.environ.get("REDIS_URL", "")
    assert url.startswith("fake://"), (
        f"REDIS_URL = {url!r} — KHÔNG phải bản giả.\n"
        "Lớp ép ở đầu tests/conftest.py đã bị gỡ hoặc đổi thành setdefault.\n"
        "Hậu quả: fixture autouse _flush_redis_between_tests sẽ gọi flushdb()\n"
        "lên Redis THẬT nếu ai chạy pytest trong container (đã xảy ra 17/08,\n"
        "flushdb calls=437, cuốn sạch phiên của mọi người dùng ngăn xếp đó)."
    )


def test_lop1_co_TAC_DUNG_client_toan_cuc_that_su_la_gia():
    """Biến đúng chưa đủ — client TOÀN CỤC phải thực sự là fakeredis.

    Kiểm qua đúng cửa mà fixture dùng (`get_default_client`), không qua một
    đường khác — đo trên vật sẽ bị `flushdb()`, không đo trên vật tương tự nó.
    """
    from src.redis_client import get_default_client

    mod = type(get_default_client()).__module__
    assert "fakeredis" in mod, (
        f"client toàn cục là {mod} — KHÔNG phải fakeredis.\n"
        "REDIS_URL có thể đúng nhưng conftest được nạp SAU module đầu tiên\n"
        "chạm src.config, nên client đã dựng xong từ giá trị cũ."
    )
    la_gia, mo_ta = _redis_la_gia()
    assert la_gia, f"cổng không nhận ra client này là giả: {mo_ta}"


def test_lop2_cong_BAT_DUOC_mot_client_that(monkeypatch):
    """Cổng phải NHẬN RA client thật — nếu không nó là cổng rỗng.

    Đây là vế Luật 2: đã chứng minh cổng không chặn nhầm (hai test trên xanh),
    giờ phải chứng minh nó **chặn thật**. Một cổng luôn trả "an toàn" thì xanh
    trong mọi trường hợp và không canh gì cả.

    Dựng client thật GIẢ ĐỊNH bằng monkeypatch, KHÔNG nối vào Redis nào —
    test canh cổng thì không được tự mình mở đúng cái cửa nó đang canh.
    """
    import tests.conftest as ct

    class _ClientThat:  # module = "tests.test_co_lap_redis_cua_conftest"
        pass

    monkeypatch.setenv("REDIS_URL", "redis://redis:6379/0")
    monkeypatch.setattr(ct, "get_default_client", lambda: _ClientThat())

    la_gia, mo_ta = ct._redis_la_gia()
    assert not la_gia, (
        f"🔴 CỔNG RỖNG — nó coi một client THẬT là bản giả: {mo_ta}\n"
        "Cổng này là lớp cuối chặn flushdb() lên Redis production."
    )
    assert "redis://redis:6379/0" in mo_ta, (
        f"cổng không nêu được REDIS_URL trong thông báo: {mo_ta!r} — "
        "người gặp lỗi sẽ không biết nó đang nói về Redis nào."
    )
