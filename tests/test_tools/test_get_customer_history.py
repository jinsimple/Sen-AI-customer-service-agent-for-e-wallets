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
