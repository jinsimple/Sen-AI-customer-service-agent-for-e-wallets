"""T2 — Data Brief §6.3 hàng 2: gọi bằng user_id của khách A KHÔNG BAO GIỜ
trả về dữ liệu khách B."""
import pytest

from src.tools.base import ToolError
from src.tools.get_customer_history import get_customer_history


def test_returns_only_own_wallet(sample_db):
    r = get_customer_history(sample_db, user_id="USR-A", days=3650)
    assert [w["wallet_id"] for w in r["wallets"]] == ["900000000001"]


def test_never_leaks_other_customer_wallet(sample_db):
    r_a = get_customer_history(sample_db, user_id="USR-A", days=3650)
    r_b = get_customer_history(sample_db, user_id="USR-B", days=3650)
    wallets_a = {w["wallet_id"] for w in r_a["wallets"]}
    wallets_b = {w["wallet_id"] for w in r_b["wallets"]}
    assert wallets_a.isdisjoint(wallets_b)


def test_unknown_user_id_raises(sample_db):
    with pytest.raises(ToolError):
        get_customer_history(sample_db, user_id="USR-NOPE")


def test_amount_match_found_includes_scope(sample_db):
    """Phát hiện thật (2026-08-11, functional_qa_set.jsonl): nhánh
    amount_match.status="found" trước đây chỉ trả trans_id, thiếu scope —
    agent phải TỰ ĐOÁN scope khi tạo ticket qua đường này (khác đường
    lookup_transaction luôn có đủ scope), gây sai lệch scope không phải do
    lỗi suy luận của agent mà do tool thiếu dữ liệu. TXN-0001 (sample_db):
    270_000đ, internal_wallet, USR-A là sender."""
    r = get_customer_history(sample_db, user_id="USR-A", days=3650, amount=270_000)
    assert r["amount_match"]["status"] == "found"
    assert r["amount_match"]["trans_id"] == "TXN-0001"
    assert r["amount_match"]["scope"] == "internal_wallet"
    assert r["amount_match"]["direction"] == "out"
