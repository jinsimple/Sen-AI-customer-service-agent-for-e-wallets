"""Tool 1/5 — `lookup_transaction` (PRD §6, Data Brief §6.3 row 1).

Required tests (T2):
  (a) exact lookup by transaction ID / phone + amount + time range
  (b) no result -> "not_found", NEVER an approximate result
  (c) several matching results -> return the list so the agent asks back, NEVER pick one
  (d) PDPA: the counterparty's phone/name is partially masked
"""
from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models import BankAccount, Transaction, User, Wallet
from src.tools.base import record_tool_result
from src.tools.masking import mask_account_no, mask_full_name, mask_phone


def _party_info(
    session: Session,
    *,
    wallet_id: str | None,
    bank_account_id: str | None,
    requesting_user_id: str | None,
) -> dict[str, Any]:
    """Return one side of a transaction (wallet or bank account), PDPA-masked unless the
    owner is the one asking (BR-06). `requesting_user_id=None` (unknown requester) ->
    always mask; this is the safe default."""
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


def _serialize_transaction(session: Session, txn: Transaction, requesting_user_id: str | None) -> dict[str, Any]:
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


def is_party_to_transaction(session: Session, txn: Transaction, user_id: str) -> bool:
    """ADR-021 — is `user_id` ONE PARTY to transaction `txn`?

    The definition covers BOTH wallets AND bank accounts. The old version (ATLAS-001) only
    compared `wallet_id`, missing half the data model: per CHECK
    `ck_transactions_scope_direction_i2`, `from_bank` has a bank account as the SENDER and
    `to_bank` has a bank account as the RECEIVER. For a top-up, the bank account holder is a
    party in the proper business sense — returning "not found" to them is wrong, regardless
    of how the seed data looks.

    THIS IS THE ONLY DEFINITION. Every place that needs to ask "who may see this
    transaction" must call this function rather than re-comparing — two definitions of the
    same concept are the seed of drift (the guard-drift lesson, see ADR-021).
    """
    my_wallet = set(session.scalars(select(Wallet.wallet_id).where(Wallet.user_id == user_id)))
    if txn.send_wal_id in my_wallet or txn.rec_wal_id in my_wallet:
        return True
    my_account = set(
        session.scalars(select(BankAccount.bank_account_id).where(BankAccount.user_id == user_id))
    )
    return txn.send_bank_account_id in my_account or txn.rec_bank_account_id in my_account


def lookup_transaction(
    session: Session,
    *,
    trans_id: str | None = None,
    rec_code: str | None = None,
    phone: str | None = None,
    amount: int | None = None,
    date_from: dt.datetime | None = None,
    date_to: dt.datetime | None = None,
    requesting_user_id: str | None = None,
    only_callers_transactions: bool = False,
) -> dict[str, Any]:
    """Look up a transaction. Priority: `trans_id` > `rec_code` > (`phone` + `amount` [+ date range]).

    Returns exactly ONE of three shapes — the agent must handle all three, never guess:
      {"status": "found", "transaction": {...}}
      {"status": "not_found"}
      {"status": "multiple_matches", "candidates": [{...summary...}, ...]}
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
        # The contract requires `status='error'`, NOT a crash. Previously this raised
        # ValueError -> `_handle_tool_error` (main.py) doesn't catch ValueError ->
        # HTTP 500 shown to the user. The AI path wasn't affected because customer_tools blocks it
        # first, but the REST route was.
        return {
            "status": "error",
            "message": "lookup_transaction cần trans_id, hoặc rec_code, hoặc (phone + amount)",
        }

    # === Ownership filter (C4/BOLA) — AT THE LIST LEVEL, NOT THE RESULT LEVEL ===
    # Placing it here rather than wrapping each result shape is deliberate: all three shapes
    # (found/not_found/multiple_matches) are DERIVED from `matches`, so filtering in one place
    # covers everything and no shape can be missed. The old fix only wrapped the `found` branch,
    # so the phone+amount lookup still returned `multiple_matches` with other people's
    # trans_ids — enough to reconstruct a profile FROM A PHONE NUMBER ALONE.
    # A fully filtered list naturally becomes `not_found`: it doesn't even reveal that "a matching
    # transaction exists", consistent with the PDPA principle used throughout the project.
    if only_callers_transactions and requesting_user_id:
        matches = [m for m in matches if is_party_to_transaction(session, m, requesting_user_id)]

    if len(matches) == 0:
        result = {"status": "not_found"}
    elif len(matches) == 1:
        result = {"status": "found", "transaction": _serialize_transaction(session, matches[0], requesting_user_id)}
    else:
        # (c) several matching results -> return the list, NEVER pick one on the agent's behalf.
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
