"""Tool 1/5 — `lookup_transaction` (PRD §6, Data Brief §6.3 hàng 1).

Test bắt buộc (T2):
  (a) tra đúng bằng mã GD / SĐT+số tiền+khoảng thời gian
  (b) không có kết quả -> "not_found", KHÔNG trả kết quả gần đúng
  (c) nhiều kết quả trùng khớp -> trả danh sách để agent hỏi lại, KHÔNG tự chọn
  (d) PDPA: SĐT/tên bên nhận bị che một phần
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models import BankAccount, Transaction, User, Wallet
from src.tools.base import record_tool_result
from src.tools.masking import mask_account_no, mask_full_name, mask_phone


def _party_info(
    session: Session,
    *,
    wallet_id: Optional[str],
    bank_account_id: Optional[str],
    requesting_user_id: Optional[str],
) -> dict[str, Any]:
    """Trả thông tin một phía giao dịch (ví hoặc TK ngân hàng), che PDPA nếu
    không phải chính chủ đang hỏi (BR-06). `requesting_user_id=None` (không rõ
    ai đang hỏi) -> luôn che, đây là lựa chọn an toàn mặc định."""
    if wallet_id is not None:
        wallet = session.get(Wallet, wallet_id)
        if wallet is None:
            return {"kind": "wallet", "wallet_id": wallet_id, "user_id": None}
        user = session.get(User, wallet.user_id)
        is_owner = requesting_user_id is not None and requesting_user_id == wallet.user_id
        return {
            "kind": "wallet",
            "wallet_id": wallet_id,
            "phone": user.phone if is_owner else mask_phone(user.phone),
            "full_name": user.full_name if is_owner else mask_full_name(user.full_name),
        }
    if bank_account_id is not None:
        acct = session.get(BankAccount, bank_account_id)
        if acct is None:
            return {"kind": "bank_account", "bank_account_id": bank_account_id, "user_id": None}
        user = session.get(User, acct.user_id)
        is_owner = requesting_user_id is not None and requesting_user_id == acct.user_id
        return {
            "kind": "bank_account",
            "bank_code": acct.bank_code,
            "account_no": acct.account_no if is_owner else mask_account_no(acct.account_no),
            "full_name": user.full_name if is_owner else mask_full_name(user.full_name),
        }
    return {"kind": "none"}


def _serialize_transaction(session: Session, txn: Transaction, requesting_user_id: Optional[str]) -> dict[str, Any]:
    return {
        "trans_id": txn.trans_id,
        "rec_code": txn.rec_code,
        "amount": txn.amount,
        "fee": txn.fee,
        "status": txn.status,
        "scope": txn.scope,
        "channel": txn.channel,
        "created_at": txn.created_at.isoformat() if txn.created_at else None,
        "completed_at": txn.completed_at.isoformat() if txn.completed_at else None,
        "des": txn.des,
        "sender": _party_info(
            session,
            wallet_id=txn.send_wal_id,
            bank_account_id=txn.send_bank_account_id,
            requesting_user_id=requesting_user_id,
        ),
        "receiver": _party_info(
            session,
            wallet_id=txn.rec_wal_id,
            bank_account_id=txn.rec_bank_account_id,
            requesting_user_id=requesting_user_id,
        ),
    }


def lookup_transaction(
    session: Session,
    *,
    trans_id: Optional[str] = None,
    rec_code: Optional[str] = None,
    phone: Optional[str] = None,
    amount: Optional[int] = None,
    date_from: Optional[dt.datetime] = None,
    date_to: Optional[dt.datetime] = None,
    requesting_user_id: Optional[str] = None,
) -> dict[str, Any]:
    """Tra cứu giao dịch. Ưu tiên `trans_id` > `rec_code` > (`phone` + `amount` [+ khoảng ngày]).

    Trả về đúng MỘT trong ba dạng — agent phải xử lý cả ba, không được đoán:
      {"status": "found", "transaction": {...}}
      {"status": "not_found"}
      {"status": "multiple_matches", "candidates": [{...tóm tắt...}, ...]}
    """
    matches: list[Transaction] = []

    if trans_id:
        txn = session.get(Transaction, trans_id)
        matches = [txn] if txn else []
    elif rec_code:
        matches = list(session.scalars(select(Transaction).where(Transaction.rec_code == rec_code)))
    elif phone and amount is not None:
        user = session.scalars(select(User).where(User.phone == phone)).first()
        if user is None:
            matches = []
        else:
            wallet = session.scalars(select(Wallet).where(Wallet.user_id == user.user_id)).first()
            if wallet is None:
                matches = []
            else:
                stmt = select(Transaction).where(
                    Transaction.amount == amount,
                    (Transaction.send_wal_id == wallet.wallet_id) | (Transaction.rec_wal_id == wallet.wallet_id),
                )
                if date_from is not None:
                    stmt = stmt.where(Transaction.created_at >= date_from)
                if date_to is not None:
                    stmt = stmt.where(Transaction.created_at <= date_to)
                matches = list(session.scalars(stmt))
    else:
        raise ValueError(
            "lookup_transaction cần trans_id, hoặc rec_code, hoặc (phone + amount)"
        )

    if len(matches) == 0:
        result = {"status": "not_found"}
    elif len(matches) == 1:
        result = {"status": "found", "transaction": _serialize_transaction(session, matches[0], requesting_user_id)}
    else:
        # (c) nhiều kết quả trùng khớp -> trả danh sách, KHÔNG tự chọn hộ agent.
        result = {
            "status": "multiple_matches",
            "candidates": [
                {
                    "trans_id": m.trans_id,
                    "amount": m.amount,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                    "scope": m.scope,
                    "status": m.status,
                }
                for m in matches
            ],
        }

    tool_result_id = record_tool_result(session, "lookup_transaction", result)
    return {**result, "tool_result_id": tool_result_id}
