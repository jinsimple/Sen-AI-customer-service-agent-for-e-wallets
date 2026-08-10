"""BR-01/BR-02/BR-04/BR-05 — tính `sla_due_at` theo mốc PHÁP LÝ, không bao
giờ theo cam kết dịch vụ nội bộ BR-03 (xem business_rules.md, verified=false
— chưa đối chiếu văn bản gốc, chỉ mở khoá việc build).
"""
from __future__ import annotations

import datetime as dt

from src.config import SLA_LEGAL_BANK_BUSINESS_DAYS, SLA_LEGAL_GENERAL_DAYS


def add_business_days(start: dt.datetime, n_days: int) -> dt.datetime:
    """BR-05: ngày làm việc = T2-T6, bỏ qua ngày lễ VN (bản demo bỏ qua lễ)."""
    current = start
    added = 0
    while added < n_days:
        current += dt.timedelta(days=1)
        if current.weekday() < 5:  # 0=Mon .. 4=Fri
            added += 1
    return current


def compute_sla_due_at(created_at: dt.datetime, scope: str) -> dt.datetime:
    if scope in ("from_bank", "to_bank"):
        # BR-01: giao dịch chạm ngân hàng — trần tra soát 4 ngày làm việc.
        return add_business_days(created_at, SLA_LEGAL_BANK_BUSINESS_DAYS)
    # BR-02: khiếu nại nói chung (nội bộ ví-ví) — trần 30 ngày.
    return created_at + dt.timedelta(days=SLA_LEGAL_GENERAL_DAYS)
