"""FIN05-StressTest-Plan-v4 S4-01/S4-02/S4-03 — test TRỰC TIẾP
`compute_sla_due_at`/`add_business_days` (src/tools/sla.py), không qua
tạo ticket (chỉ chạm gián tiếp qua test khác, không kiểm số ngày tính RA
có đúng không).

PHÁT HIỆN THẬT lúc viết file này (khác giả định trong FIN05-StressTest-
Plan-v4 §4 S4-02 — tài liệu đó liệt kê "4 loại: NH 4 ngày, chung 30 ngày,
phản hồi đầu 48h, nghi gian lận 7 ngày"): `src/config.py` CÓ định nghĩa
`SLA_SERVICE_FIRST_RESPONSE_HOURS=48` và `SLA_SERVICE_FRAUD_BUSINESS_DAYS=7`
nhưng grep toàn bộ `src/` xác nhận **0 nơi nào import/dùng 2 hằng số này**
— `compute_sla_due_at` CHỈ implement 2 trong 4 loại (ngân hàng 4 ngày làm
việc, chung 30 ngày). Đây là CẤU HÌNH CHẾT (dead config)/tính năng CHƯA
hoàn thiện, không phải chỉ thiếu test — 2 test dưới cùng ghi nhận rõ finding
này thay vì viết test giả định hành vi không tồn tại."""
from __future__ import annotations

import datetime as dt

import pytest

from src.config import (
    SLA_LEGAL_BANK_BUSINESS_DAYS,
    SLA_LEGAL_GENERAL_DAYS,
    SLA_SERVICE_FIRST_RESPONSE_HOURS,
    SLA_SERVICE_FRAUD_BUSINESS_DAYS,
)
from src.tools.sla import add_business_days, compute_sla_due_at


def test_add_business_days_skips_weekend():
    """S4-01 — tạo Thứ Sáu (2026-08-14) + 1 ngày làm việc phải nhảy qua
    Thứ Bảy/Chủ Nhật, ra đúng Thứ Hai (2026-08-17), không phải Thứ Bảy."""
    friday = dt.datetime(2026, 8, 14, 10, 0)  # xác nhận đúng là Thứ Sáu
    assert friday.weekday() == 4
    result = add_business_days(friday, 1)
    assert result.date() == dt.date(2026, 8, 17)
    assert result.weekday() == 0  # Thứ Hai


def test_add_business_days_starting_on_weekend():
    """Case biên (S4-03 tinh thần) — bắt đầu tính TỪ Thứ Bảy, vẫn phải đếm
    đúng ngày làm việc, không tính nhầm Thứ Bảy là 1 ngày làm việc."""
    saturday = dt.datetime(2026, 8, 15, 10, 0)
    assert saturday.weekday() == 5
    result = add_business_days(saturday, 4)
    # CN(16) không tính, T2(17) T3(18) T4(19) T5(20) = 4 ngày làm việc
    assert result.date() == dt.date(2026, 8, 20)


@pytest.mark.parametrize("scope", ["from_bank", "to_bank"])
def test_bank_scope_uses_legal_business_days_threshold(scope):
    """S4-02 — giao dịch chạm ngân hàng dùng đúng SLA_LEGAL_BANK_BUSINESS_DAYS
    (4 ngày làm việc, không phải ngày lịch thường)."""
    created_at = dt.datetime(2026, 8, 10, 9, 0)  # Thứ Hai
    due = compute_sla_due_at(created_at, scope)
    expected = add_business_days(created_at, SLA_LEGAL_BANK_BUSINESS_DAYS)
    assert due == expected
    assert due.weekday() < 5, "Hạn SLA rơi vào cuối tuần — add_business_days phải luôn trả về ngày làm việc"


def test_internal_wallet_scope_uses_calendar_days_threshold():
    """S4-02 — khiếu nại nội bộ ví-ví dùng SLA_LEGAL_GENERAL_DAYS (30 ngày
    LỊCH, không phải ngày làm việc — khác hẳn nhánh ngân hàng)."""
    created_at = dt.datetime(2026, 8, 10, 9, 0)
    due = compute_sla_due_at(created_at, "internal_wallet")
    assert due == created_at + dt.timedelta(days=SLA_LEGAL_GENERAL_DAYS)


def test_sla_due_at_created_just_before_midnight_does_not_lose_a_day():
    """S4-03 — case biên tạo ticket ngay TRƯỚC nửa đêm: hạn SLA phải cách
    đúng số ngày theo GIỜ, không bị timezone/rounding làm lệch 1 ngày."""
    created_at = dt.datetime(2026, 8, 10, 23, 59, 0)
    due = compute_sla_due_at(created_at, "internal_wallet")
    assert (due - created_at) == dt.timedelta(days=SLA_LEGAL_GENERAL_DAYS)


def test_service_sla_constants_are_not_wired_into_compute_sla_due_at():
    """Ghi nhận finding CẤU HÌNH CHẾT (xem docstring module) — nếu ai đó sau
    này wire 2 hằng số này vào compute_sla_due_at (đúng việc NÊN làm), test
    này sẽ FAIL và cần được viết lại thành test hành vi thật, không phải
    xoá đi — đây là tín hiệu TỐT nếu fail."""
    import inspect

    from src.tools import sla as sla_module

    source = inspect.getsource(sla_module)
    assert "SLA_SERVICE_FIRST_RESPONSE_HOURS" not in source, (
        "SLA_SERVICE_FIRST_RESPONSE_HOURS (48h phản hồi đầu) giờ ĐÃ được dùng "
        "trong sla.py — cập nhật test này thành test hành vi thật (không chỉ "
        "test 'chưa dùng'), xem docs/FIN05-StressTest-Plan-v4-QA-Backlog.md S4-02."
    )
    assert "SLA_SERVICE_FRAUD_BUSINESS_DAYS" not in source, (
        "SLA_SERVICE_FRAUD_BUSINESS_DAYS (7 ngày nghi gian lận) giờ ĐÃ được "
        "dùng trong sla.py — cập nhật test này thành test hành vi thật."
    )
    # Giữ tham chiếu 2 hằng số ở đây (import ở đầu file) — để khi ai đó XOÁ
    # hẳn khỏi config.py (dọn dead config thay vì wire vào), ruff F401 sẽ tự
    # báo unused import, nhắc quay lại xoá cả test này.
    assert SLA_SERVICE_FIRST_RESPONSE_HOURS == 48
    assert SLA_SERVICE_FRAUD_BUSINESS_DAYS == 7
