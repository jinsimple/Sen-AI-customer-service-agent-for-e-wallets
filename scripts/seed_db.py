#!/usr/bin/env python3
"""FIN-05 — nạp data/generated/*.jsonl vào DB.

Chỉ nạp 8 bảng dữ liệu nền (users, wallets, bank_accounts, transactions,
transaction_events, complaints, tickets, auth_sessions). KHÔNG nạp
tool_results/investigation_logs/resolutions/escalations/messages — 5 bảng
đó sinh ra lúc runtime khi agent/CSKH thao tác, không phải dữ liệu nền
(Data Brief §4.2). golden_set.jsonl / heldout_set.jsonl cũng KHÔNG nạp vào
DB — đó là input của eval harness (T3-T5), không phải dữ liệu ứng dụng.

Idempotent theo cách đơn giản nhất có thể đúng: mỗi bảng được XOÁ SẠCH rồi
NẠP LẠI trong một transaction — chạy `make db-seed` hai lần cho ra đúng
cùng số dòng, không nhân đôi (yêu cầu §5.3). Thứ tự xoá là NGƯỢC thứ tự
nạp để không vi phạm khoá ngoại (PRAGMA foreign_keys=ON, xem
src/db/session.py).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import Session

from src.config import DATA_GENERATED_DIR
from src.db.models import (
    AuthSession,
    BankAccount,
    Base,
    Complaint,
    Ticket,
    Transaction,
    TransactionEvent,
    User,
    Wallet,
)
from src.db.session import get_engine, session_scope


def _parse_dt(value: Any) -> dt.datetime | None:
    if value is None:
        return None
    return dt.datetime.fromisoformat(value)


def _row_users(r: dict) -> dict:
    r = dict(r)
    r["created_at"] = _parse_dt(r["created_at"])
    return r


def _row_wallets(r: dict) -> dict:
    return dict(r)


def _row_bank_accounts(r: dict) -> dict:
    r = dict(r)
    r["linked_at"] = _parse_dt(r["linked_at"])
    return r


def _row_transactions(r: dict) -> dict:
    r = dict(r)
    r["created_at"] = _parse_dt(r["created_at"])
    r["completed_at"] = _parse_dt(r.get("completed_at"))
    return r


def _row_transaction_events(r: dict) -> dict:
    r = dict(r)
    r["occurred_at"] = _parse_dt(r["occurred_at"])
    return r


def _row_complaints(r: dict) -> dict:
    r = dict(r)
    r["created_at"] = _parse_dt(r["created_at"])
    r.setdefault("fraud_signals", [])
    return r


def _row_tickets(r: dict) -> dict:
    r = dict(r)
    r["created_at"] = _parse_dt(r["created_at"])
    r["updated_at"] = _parse_dt(r["updated_at"])
    r["sla_due_at"] = _parse_dt(r["sla_due_at"])
    return r


def _row_auth_sessions(r: dict) -> dict:
    r = dict(r)
    r["created_at"] = _parse_dt(r.get("created_at")) or dt.datetime.utcnow()
    r["locked_at"] = _parse_dt(r.get("locked_at"))
    return r


# Thứ tự NẠP — cha trước con, theo đúng FK trong models.py.
TABLES: list[tuple[str, Any, Callable[[dict], dict]]] = [
    ("users.jsonl", User, _row_users),
    ("wallets.jsonl", Wallet, _row_wallets),
    ("bank_accounts.jsonl", BankAccount, _row_bank_accounts),
    ("transactions.jsonl", Transaction, _row_transactions),
    ("transaction_events.jsonl", TransactionEvent, _row_transaction_events),
    ("complaints.jsonl", Complaint, _row_complaints),
    ("tickets.jsonl", Ticket, _row_tickets),
    ("auth_sessions.jsonl", AuthSession, _row_auth_sessions),
]


def _read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def seed(session: Session, data_dir: Path = DATA_GENERATED_DIR, batch_size: int = 2000) -> dict[str, int]:
    counts: dict[str, int] = {}

    # Xoá theo thứ tự NGƯỢC (con trước cha) để không vỡ FK.
    for filename, model, _ in reversed(TABLES):
        session.query(model).delete()

    for filename, model, row_fn in TABLES:
        path = data_dir / filename
        if not path.exists():
            raise FileNotFoundError(
                f"Thiếu {path} — chạy `make data` trước, hoặc kiểm tra DATA_GENERATED_DIR"
            )
        raw_rows = _read_jsonl(path)
        mapped = [row_fn(r) for r in raw_rows]
        for i in range(0, len(mapped), batch_size):
            session.bulk_insert_mappings(model, mapped[i : i + batch_size])
        counts[filename] = len(mapped)

    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir", type=Path, default=DATA_GENERATED_DIR, help="Thư mục chứa *.jsonl nạp vào DB"
    )
    parser.add_argument(
        "--database-url", type=str, default=None, help="Override DATABASE_URL (mặc định lấy từ src/config.py)"
    )
    args = parser.parse_args()

    engine = get_engine(args.database_url)
    from sqlalchemy.orm import sessionmaker

    factory = sessionmaker(bind=engine, future=True)

    with session_scope(factory) as session:
        counts = seed(session, data_dir=args.data_dir)

    print("Nạp xong:")
    for filename, n in counts.items():
        print(f"  {filename:<28} {n:>8} dòng")


if __name__ == "__main__":
    main()
