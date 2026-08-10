"""T1 — vài bất biến cốt lõi trên data/generated/ (Data Brief §6.2).

Đây KHÔNG thay thế scripts/validate_dataset.py (16 nhóm kiểm định đầy đủ,
I1-I10) — chỉ là smoke test nhanh chạy trong `make test`/CI để bắt regression
rõ ràng nhất nếu ai đó sửa generator mà quên chạy validator đầy đủ.
"""
from __future__ import annotations

import json

import pytest

from src.config import DATA_GENERATED_DIR

pytestmark = pytest.mark.skipif(
    not (DATA_GENERATED_DIR / "transactions.jsonl").exists(),
    reason="data/generated/ chưa sinh — chạy `make data` trước",
)


def _read_jsonl(name: str) -> list[dict]:
    path = DATA_GENERATED_DIR / name
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def test_i2_scope_direction_combo():
    for t in _read_jsonl("transactions.jsonl"):
        scope = t["scope"]
        if scope == "internal_wallet":
            assert t["send_wal_id"] and t["rec_wal_id"]
            assert t["send_bank_account_id"] is None and t["rec_bank_account_id"] is None
        elif scope == "from_bank":
            assert t["send_bank_account_id"] and t["rec_wal_id"]
            assert t["send_wal_id"] is None and t["rec_bank_account_id"] is None
        elif scope == "to_bank":
            assert t["send_wal_id"] and t["rec_bank_account_id"]
            assert t["send_bank_account_id"] is None and t["rec_wal_id"] is None
        else:
            pytest.fail(f"scope ngoài enum: {scope}")


def test_i7_amount_is_positive_integer_no_float():
    for t in _read_jsonl("transactions.jsonl"):
        assert isinstance(t["amount"], int)
        assert t["amount"] > 0
        assert isinstance(t["fee"], int)
        assert t["fee"] >= 0


def test_i9_phone_in_controlled_test_range():
    for u in _read_jsonl("users.jsonl"):
        phone = u["phone"]
        assert len(phone) == 10 and phone.isdigit()
        last6 = phone[-6:]
        assert "000000" <= last6 <= "009999"


def test_i10_golden_set_seed_trans_ids_exist_in_transactions():
    trans_ids = {t["trans_id"] for t in _read_jsonl("transactions.jsonl")}
    # golden_set.jsonl nằm ở eval/, không phải data/generated/ — đọc trực tiếp.
    from src.config import EVAL_DIR

    with (EVAL_DIR / "golden_set.jsonl").open(encoding="utf-8") as f:
        golden_cases = [json.loads(line) for line in f if line.strip()]

    missing = []
    for case in golden_cases:
        for seed_id in case.get("seed_trans_ids") or []:
            if seed_id not in trans_ids:
                missing.append((case["case_id"], seed_id))
    assert not missing, f"seed_trans_ids không tồn tại trong transactions.jsonl: {missing[:5]}"
