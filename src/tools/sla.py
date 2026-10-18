"""BR-01/BR-02/BR-04/BR-05 — compute `sla_due_at` from the LEGAL deadline, never
from the internal service commitment BR-03 (see business_rules.md, verified=false
— not yet checked against the original regulation; only unblocks the build).
"""
from __future__ import annotations

import datetime as dt

from src.config import SLA_LEGAL_BANK_BUSINESS_DAYS, SLA_LEGAL_GENERAL_DAYS


def add_business_days(start: dt.datetime, n_days: int) -> dt.datetime:
    """BR-05: business days = Mon-Fri, Vietnamese public holidays ignored (demo build skips holidays)."""
    current = start
    added = 0
    while added < n_days:
        current += dt.timedelta(days=1)
        if current.weekday() < 5:  # 0=Mon .. 4=Fri
            added += 1
    return current


def compute_sla_due_at(created_at: dt.datetime, scope: str) -> dt.datetime:
    if scope in ("from_bank", "to_bank"):
        # BR-01: bank-touching transactions — investigation ceiling of 4 business days.
        return add_business_days(created_at, SLA_LEGAL_BANK_BUSINESS_DAYS)
    # BR-02: general complaints (internal wallet-to-wallet) — 30-day ceiling.
    return created_at + dt.timedelta(days=SLA_LEGAL_GENERAL_DAYS)
