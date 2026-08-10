"""T2 — Data Brief §6.3 hàng 1: (a) tra đúng, (b) not_found đúng, (c) nhiều
kết quả trả danh sách, (d) PDPA masking."""
from src.tools.lookup_transaction import lookup_transaction


def test_found_by_trans_id(sample_db):
    r = lookup_transaction(sample_db, trans_id="TXN-0001")
    assert r["status"] == "found"
    assert r["transaction"]["amount"] == 270_000


def test_not_found_does_not_return_approximate_result(sample_db):
    r = lookup_transaction(sample_db, trans_id="TXN-DOES-NOT-EXIST")
    assert r["status"] == "not_found"
    assert "transaction" not in r


def test_multiple_matches_by_phone_amount_returns_list_not_a_pick(sample_db):
    # TXN-0002 và TXN-0003: cùng amount, cùng bên gửi (USR-A / 0901000001).
    r = lookup_transaction(sample_db, phone="0901000001", amount=500_000)
    assert r["status"] == "multiple_matches"
    assert {c["trans_id"] for c in r["candidates"]} == {"TXN-0002", "TXN-0003"}


def test_receiver_pdpa_masked_by_default(sample_db):
    r = lookup_transaction(sample_db, trans_id="TXN-0001")
    receiver = r["transaction"]["receiver"]
    assert receiver["phone"] != "0901000002"
    assert receiver["phone"].startswith("090") and "***" in receiver["phone"]


def test_owner_sees_own_info_unmasked(sample_db):
    r = lookup_transaction(sample_db, trans_id="TXN-0001", requesting_user_id="USR-B")
    receiver = r["transaction"]["receiver"]  # USR-B là receiver, đang tự hỏi
    assert receiver["phone"] == "0901000002"


def test_every_lookup_writes_a_tool_result(sample_db):
    r = lookup_transaction(sample_db, trans_id="TXN-0001")
    assert r["tool_result_id"].startswith("TR-")
