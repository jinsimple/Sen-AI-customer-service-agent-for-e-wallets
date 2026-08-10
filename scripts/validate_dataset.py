"""FIN-05 — Kiểm định dataset trước khi nạp DB (Data Brief §6.2, tầng T1).

Cách chạy:  python scripts/validate_dataset.py data/generated/
Fail bất kỳ bất biến nào → exit 1 → pipeline dừng, DB không bao giờ chứa dữ liệu bẩn.

Mỗi hàm check_* trả về danh sách vi phạm (rỗng = đạt) — tests/test_data/ import
trực tiếp các hàm này để mỗi bất biến là một test riêng, cùng một nguồn sự thật.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.fraud_engine import FraudEngine, LedgerIndex  # noqa: E402
from scripts.gen_dataset import GIVENS, MIDDLES, SURNAMES  # noqa: E402

PHONE_RE = re.compile(r"^0[35789]\d{2}00\d{4}$")
WALLET_RE = re.compile(r"^9000\d{8}$")
BANKACC_RE = re.compile(r"^8800\d{10}$")
TRANS_RE = re.compile(r"^TXN\d{14}$")
TXN_IN_TEXT_RE = re.compile(r"TXN\d{14}")

VALID_STATUS = {"pending", "processing", "success", "failed", "refunded", "on_hold"}
VALID_SCOPE = {"internal_wallet", "from_bank", "to_bank"}
EVENT_TYPES = {"initiated", "debited", "sent_to_partner", "partner_ack", "credited",
               "failed", "held", "refund_initiated", "refunded"}
ACTORS = {"wallet_system", "partner_bank", "cskh"}


def _read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def load_dataset(gen_dir: Path, eval_dir: Path | None = None) -> dict:
    eval_dir = eval_dir or ROOT / "eval"
    data = {name: _read_jsonl(gen_dir / f"{name}.jsonl")
            for name in ("users", "wallets", "bank_accounts", "transactions",
                         "transaction_events", "complaints", "tickets", "auth_sessions")}
    data["golden"] = (_read_jsonl(eval_dir / "golden_set.jsonl")
                      + _read_jsonl(eval_dir / "heldout_set.jsonl"))
    data["scenarios"] = yaml.safe_load((ROOT / "data/schema/scenarios.yaml").read_text(encoding="utf-8"))
    data["fraud_cfg"] = yaml.safe_load((ROOT / "data/schema/fraud_signals.yaml").read_text(encoding="utf-8"))
    return data


# ---------------------------------------------------------------- I1 — khoá ngoại
def check_i1_foreign_keys(d: dict) -> list[str]:
    v = []
    users = {u["user_id"] for u in d["users"]}
    wallets = {w["wallet_id"] for w in d["wallets"]}
    accs = {b["bank_account_id"] for b in d["bank_accounts"]}
    txs = {t["trans_id"] for t in d["transactions"]}
    cmps = {c["complaint_id"] for c in d["complaints"]}
    for w in d["wallets"]:
        if w["user_id"] not in users:
            v.append(f'I1: wallet {w["wallet_id"]} → user lạ')
    for b in d["bank_accounts"]:
        if b["user_id"] not in users:
            v.append(f'I1: bank_account {b["bank_account_id"]} → user lạ')
    for t in d["transactions"]:
        for col, pool in (("send_wal_id", wallets), ("rec_wal_id", wallets),
                          ("send_bank_account_id", accs), ("rec_bank_account_id", accs)):
            if t[col] is not None and t[col] not in pool:
                v.append(f'I1: tx {t["trans_id"]}.{col} → {t[col]} không tồn tại')
    for e in d["transaction_events"]:
        if e["trans_id"] not in txs:
            v.append(f'I1: event {e["event_id"]} → tx lạ')
    for c in d["complaints"]:
        if c["user_id"] not in users:
            v.append(f'I1: complaint {c["complaint_id"]} → user lạ')
        if c["trans_id"] is not None and c["trans_id"] not in txs:
            v.append(f'I1: complaint {c["complaint_id"]} → tx lạ')
    for t in d["tickets"]:
        if t["complaint_id"] not in cmps:
            v.append(f'I1: ticket {t["ticket_id"]} → complaint lạ')
    for s in d["auth_sessions"]:
        if s["user_id"] not in users:
            v.append(f'I1: session {s["session_id"]} → user lạ')
    return v


# ---------------------------------------------------------------- I2 — scope ↔ 2 bên
def check_i2_scope_parties(d: dict) -> list[str]:
    v = []
    combos = {
        "internal_wallet": ("send_wal_id", "rec_wal_id", "send_bank_account_id", "rec_bank_account_id"),
        "from_bank": ("send_bank_account_id", "rec_wal_id", "send_wal_id", "rec_bank_account_id"),
        "to_bank": ("send_wal_id", "rec_bank_account_id", "send_bank_account_id", "rec_wal_id"),
    }
    for t in d["transactions"]:
        if t["scope"] not in combos:
            v.append(f'I2: tx {t["trans_id"]} scope lạ {t["scope"]}')
            continue
        a, b, x, y = combos[t["scope"]]
        if not (t[a] and t[b] and t[x] is None and t[y] is None):
            v.append(f'I2: tx {t["trans_id"]} ({t["scope"]}) sai tổ hợp bên gửi/nhận')
    return v


# ---------------------------------------------------------------- I3 — event đối tác
def check_i3_partner_events(d: dict) -> list[str]:
    v = []
    actors = defaultdict(set)
    for e in d["transaction_events"]:
        actors[e["trans_id"]].add(e["actor"])
    for t in d["transactions"]:
        if t["scope"] in ("from_bank", "to_bank") and "partner_bank" not in actors[t["trans_id"]]:
            v.append(f'I3: tx {t["trans_id"]} ({t["scope"]}) không có event partner_bank')
    return v


# ---------------------------------------------------------------- I4 — timeline liền mạch
def check_i4_event_chain(d: dict) -> list[str]:
    v = []
    by_tx = defaultdict(list)
    for e in d["transaction_events"]:
        by_tx[e["trans_id"]].append(e)
    for tid, evs in by_tx.items():
        evs.sort(key=lambda e: e["seq"])
        if [e["seq"] for e in evs] != list(range(1, len(evs) + 1)):
            v.append(f"I4: {tid} seq không liên tục")
        for i in range(1, len(evs)):
            if evs[i]["status_from"] != evs[i - 1]["status_to"]:
                v.append(f'I4: {tid} seq {evs[i]["seq"]} đứt chuỗi trạng thái')
            if evs[i]["occurred_at"] < evs[i - 1]["occurred_at"]:
                v.append(f'I4: {tid} seq {evs[i]["seq"]} thời gian đi lùi')
        for e in evs:
            if e["event_type"] not in EVENT_TYPES or e["actor"] not in ACTORS:
                v.append(f'I4: {tid} event/actor ngoài enum')
    return v


# ---------------------------------------------------------------- I5 — status khớp event cuối
def check_i5_status_matches_last_event(d: dict) -> list[str]:
    v = []
    last = {}
    for e in d["transaction_events"]:
        cur = last.get(e["trans_id"])
        if cur is None or e["seq"] > cur["seq"]:
            last[e["trans_id"]] = e
    for t in d["transactions"]:
        e = last.get(t["trans_id"])
        if e is None:
            v.append(f'I5: tx {t["trans_id"]} không có event nào')
        elif e["status_to"] != t["status"]:
            v.append(f'I5: tx {t["trans_id"]} status={t["status"]} ≠ event cuối {e["status_to"]}')
    return v


# ---------------------------------------------------------------- I6 — bằng chứng double_charge
def check_i6_double_charge_evidence(d: dict) -> list[str]:
    v = []
    tx_by_id = {t["trans_id"]: t for t in d["transactions"]}
    dc_pair_keys = set()
    for case in d["golden"]:
        if case["edge_type"] is not None or case["complaint_type"] != "double_charge":
            continue
        seeds = [tx_by_id[i] for i in case["seed_trans_ids"] if i in tx_by_id]
        if case["difficulty"] in ("clear", "ambiguous"):
            pairs = defaultdict(list)
            for t in seeds:
                pairs[t["idempotency_key"]].append(t)
            dup = [g for g in pairs.values() if len(g) == 2]
            if len(dup) != 1:
                v.append(f'I6: {case["case_id"]} phải có đúng 1 cặp cùng idempotency_key')
                continue
            a, b = sorted(dup[0], key=lambda t: t["created_at"])
            dc_pair_keys.add(a["idempotency_key"])
            if a["amount"] != b["amount"]:
                v.append(f'I6: {case["case_id"]} cặp lệch amount')
            gap = (datetime.fromisoformat(b["created_at"])
                   - datetime.fromisoformat(a["created_at"])).total_seconds()
            if not 0 < gap < 60:
                v.append(f'I6: {case["case_id"]} cặp cách nhau {gap:.0f}s (phải < 60s)')
        else:  # trap: hai đơn riêng, TUYỆT ĐỐI không chung key
            keys = [t["idempotency_key"] for t in seeds]
            if len(keys) != len(set(keys)):
                v.append(f'I6: {case["case_id"]} (trap) không được chung idempotency_key')
    # ngoài các cặp golden, idempotency_key phải duy nhất toàn cục
    cnt = Counter(t["idempotency_key"] for t in d["transactions"])
    for key, n in cnt.items():
        if n > 1 and key not in dc_pair_keys:
            v.append(f"I6: idempotency_key {key} lặp {n} lần ngoài cặp double_charge golden")
        if n > 2:
            v.append(f"I6: idempotency_key {key} lặp {n} lần (tối đa 2)")
    return v


# ---------------------------------------------------------------- I7 — tiền là số nguyên dương
def check_i7_integer_money(d: dict) -> list[str]:
    v = []
    for t in d["transactions"]:
        if not isinstance(t["amount"], int) or isinstance(t["amount"], bool) or t["amount"] <= 0:
            v.append(f'I7: tx {t["trans_id"]} amount={t["amount"]!r}')
        if not isinstance(t["fee"], int) or t["fee"] < 0:
            v.append(f'I7: tx {t["trans_id"]} fee={t["fee"]!r}')
    for w in d["wallets"]:
        if not isinstance(w["balance"], int) or w["balance"] < 0:
            v.append(f'I7: wallet {w["wallet_id"]} balance={w["balance"]!r}')
    return v


# ---------------------------------------------------------------- I8 — phủ ma trận & edge
def check_i8_coverage(d: dict) -> list[str]:
    v = []
    sc = d["scenarios"]
    golden = d["golden"]
    m = sc["matrix"]
    for ctype in m["complaint_types"]:
        for scope in m["scopes"]:
            for diff in m["difficulties"]:
                n = sum(1 for c in golden if c["edge_type"] is None
                        and c["complaint_type"] == ctype and c["scope"] == scope
                        and c["difficulty"] == diff)
                if n != m["cases_per_combo"]:
                    v.append(f"I8: ô {ctype}×{scope}×{diff} có {n} case (cần {m['cases_per_combo']})")
    e = sc["edge_cases"]
    def count(et):
        return sum(1 for c in golden if c["edge_type"] == et)
    if count("not_found") != e["not_found"]:
        v.append(f'I8: not_found = {count("not_found")}')
    if count("partner_timeout") != e["partner_timeout"]:
        v.append(f'I8: partner_timeout = {count("partner_timeout")}')
    if count("over_authority") != e["over_authority"]:
        v.append(f'I8: over_authority = {count("over_authority")}')
    for field in e["missing_info"]["fields"]:
        n = sum(1 for c in golden if c["edge_type"] == "missing_info" and c["missing_field"] == field)
        if n != e["missing_info"]["per_field"]:
            v.append(f"I8: missing_info[{field}] = {n} (cần {e['missing_info']['per_field']})")
    fraud = [c for c in golden if c["edge_type"] == "fraud_suspect"]
    fcfg = e["fraud_suspect"]
    if len(fraud) != fcfg["positives"] + fcfg["traps"] + fcfg["boundary"] + fcfg["forbidden_behavior"]:
        v.append(f"I8: fraud_suspect = {len(fraud)}")
    all_signals = set(d["fraud_cfg"]["signals"])
    fired_anywhere = {s for c in fraud for s in c["expected"]["fraud_signals"]}
    for s in sorted(all_signals - fired_anywhere):
        v.append(f"I8: tín hiệu {s} không có case dương tính nào")
    trap_covered = {c["trap_for"] for c in fraud if c["trap_for"]}
    for s in sorted(all_signals - trap_covered):
        v.append(f"I8: tín hiệu {s} không có case bẫy (trap_for)")
    if len(golden) != sc["split"]["dev"] + sc["split"]["heldout"]:
        v.append(f"I8: tổng golden = {len(golden)}")
    return v


# ---------------------------------------------------------------- I9 — dải định danh test
def check_i9_test_ranges(d: dict) -> list[str]:
    v = []
    surnames, middles, givens = set(SURNAMES), set(MIDDLES), set(GIVENS)
    phones = set()
    for u in d["users"]:
        if not PHONE_RE.match(u["phone"]):
            v.append(f'I9: {u["user_id"]} phone {u["phone"]} ngoài dải test')
        if u["phone"] in phones:
            v.append(f'I9: phone {u["phone"]} trùng')
        phones.add(u["phone"])
        parts = u["full_name"].split()
        if not (parts[0] in surnames and parts[1] in middles and parts[-1] in givens):
            v.append(f'I9: tên {u["full_name"]} ngoài bộ tên generator')
        if not u["email"].endswith("@example.test"):
            v.append(f'I9: email {u["email"]} ngoài miền test')
    for w in d["wallets"]:
        if not WALLET_RE.match(w["wallet_id"]):
            v.append(f'I9: wallet {w["wallet_id"]} ngoài dải')
    for b in d["bank_accounts"]:
        if not BANKACC_RE.match(b["bank_account_id"]):
            v.append(f'I9: bank_account {b["bank_account_id"]} ngoài dải')
    for t in d["transactions"]:
        if not TRANS_RE.match(t["trans_id"]):
            v.append(f'I9: trans_id {t["trans_id"]} sai cú pháp')
    return v


# ---------------------------------------------------------------- I10 — golden đủ nhãn
EXPECTED_KEYS = {"complaint_type", "scope", "authority", "escalation_target", "priority",
                 "agent_may_decide_amount", "agent_may_execute", "must_cite_trans_ids",
                 "must_ask_clarifying_question", "must_escalate_immediately", "fraud_signals"}


def check_i10_golden_labels(d: dict) -> list[str]:
    v = []
    txs = {t["trans_id"] for t in d["transactions"]}
    cmps = {c["complaint_id"] for c in d["complaints"]}
    tcks = {t["ticket_id"] for t in d["tickets"]}
    seen_ids = set()
    for c in d["golden"]:
        cid = c["case_id"]
        if cid in seen_ids:
            v.append(f"I10: {cid} trùng case_id")
        seen_ids.add(cid)
        missing = EXPECTED_KEYS - set(c["expected"])
        if missing:
            v.append(f"I10: {cid} expected thiếu {sorted(missing)}")
        if c["edge_type"] == "not_found":
            if c["seed_trans_ids"]:
                v.append(f"I10: {cid} not_found không được có seed")
            if not c["forbidden"].get("must_not_state_any_number"):
                v.append(f"I10: {cid} not_found thiếu must_not_state_any_number")
        else:
            if not c["seed_trans_ids"]:
                v.append(f"I10: {cid} thiếu seed_trans_ids")
            for tid in c["seed_trans_ids"]:
                if tid not in txs:
                    v.append(f"I10: {cid} seed {tid} không tồn tại trong DB")
            if c["primary_trans_id"] not in c["seed_trans_ids"]:
                v.append(f"I10: {cid} primary ngoài seeds")
        if c["pre_seeded"]:
            if c["pre_seeded"]["complaint_id"] not in cmps or c["pre_seeded"]["ticket_id"] not in tcks:
                v.append(f"I10: {cid} pre_seeded trỏ tới bản ghi không tồn tại")
        if not c["utterances"] or not c["utterance_pattern_ids"]:
            v.append(f"I10: {cid} thiếu utterance")
        if any("{" in u for u in c["utterances"]):
            v.append(f"I10: {cid} utterance còn placeholder chưa điền")
    return v


# ---------------------------------------------------------------- extras
def check_distributions(d: dict) -> list[str]:
    v = []
    dist = d["scenarios"]["distributions"]
    txs = d["transactions"]
    n = len(txs)
    if n != d["scenarios"]["population"]["transactions"]:
        v.append(f"DIST: tổng tx = {n}")
    for field, targets, tol in (("status", dist["status"], 0.03), ("scope", dist["scope"], 0.03)):
        cnt = Counter(t[field] for t in txs)
        for key, share in targets.items():
            actual = cnt.get(key, 0) / n
            if abs(actual - share) > tol:
                v.append(f"DIST: {field}={key} {actual:.3f} lệch mục tiêu {share} quá ±{tol}")
    amounts = sorted(t["amount"] for t in txs)
    median = amounts[n // 2]
    if not 120_000 <= median <= 350_000:
        v.append(f"DIST: trung vị amount = {median:,}")
    if amounts[-1] > 200_000_000:
        v.append(f"DIST: amount vượt trần {amounts[-1]:,}")
    hours = Counter(datetime.fromisoformat(t["created_at"]).hour for t in txs)
    peak = sum(hours[h] for h in (11, 12, 13)) / 3
    mid = sum(hours[h] for h in (14, 15, 16)) / 3
    night = sum(hours[h] for h in (1, 2, 3, 4)) / 4
    if not (peak > mid > night):
        v.append(f"DIST: hình dạng giờ bất thường (peak={peak:.0f}, mid={mid:.0f}, night={night:.0f})")
    ctype_cnt = Counter(c["type"] for c in d["complaints"])
    n_c = len(d["complaints"])
    for key, share in dist["complaint_type"].items():
        actual = ctype_cnt.get(key, 0) / n_c
        if abs(actual - share) > 0.08:
            v.append(f"DIST: complaint {key} {actual:.3f} lệch {share} quá ±0.08")
    return v


def check_activity(d: dict) -> list[str]:
    v = []
    day0 = d["scenarios"]["window"]["start_date"]
    active = defaultdict(set)
    owner_w = {w["wallet_id"]: w["user_id"] for w in d["wallets"]}
    owner_b = {b["bank_account_id"]: b["user_id"] for b in d["bank_accounts"]}
    for t in d["transactions"]:
        day = (datetime.fromisoformat(t["created_at"]).date() - day0).days
        for ref, m in ((t["send_wal_id"], owner_w), (t["rec_wal_id"], owner_w),
                       (t["send_bank_account_id"], owner_b), (t["rec_bank_account_id"], owner_b)):
            if ref:
                active[m[ref]].add(day)
    for u in d["users"]:
        if u["role"] != "customer":
            continue
        n = len(active.get(u["user_id"], set()))
        if n < 85:
            v.append(f'ACT: {u["user_id"]} chỉ hoạt động {n}/90 ngày')
    return v


def check_split(d: dict) -> list[str]:
    v = []
    sc = d["scenarios"]["split"]
    dev = [c for c in d["golden"] if c["split"] == "dev"]
    held = [c for c in d["golden"] if c["split"] == "heldout"]
    if len(dev) != sc["dev"] or len(held) != sc["heldout"]:
        v.append(f"SPLIT: {len(dev)}/{len(held)} ≠ {sc['dev']}/{sc['heldout']}")
    strata = defaultdict(lambda: {"dev": 0, "heldout": 0})
    for c in d["golden"]:
        if c["edge_type"] is None:
            key = (c["cell"], c["difficulty"])
        elif c["edge_type"] == "missing_info":
            key = ("missing", c["missing_field"])
        else:
            key = (c["edge_type"], "")
        strata[key][c["split"]] += 1
    for key, n in strata.items():
        if n["heldout"] == 0:
            v.append(f"SPLIT: stratum {key} không có case held-out nào")
    return v


def check_fraud_engine_agreement(d: dict) -> list[str]:
    """Double-entry: nhãn fraud_signals gán tay phải khớp engine tính từ dữ liệu."""
    import copy
    v = []
    idx = LedgerIndex(copy.deepcopy(d["users"]), copy.deepcopy(d["wallets"]),
                      copy.deepcopy(d["bank_accounts"]), copy.deepcopy(d["transactions"]),
                      copy.deepcopy(d["complaints"]), copy.deepcopy(d["auth_sessions"]),
                      copy.deepcopy(d["tickets"]))
    eng = FraudEngine(d["fraud_cfg"], idx)
    for c in d["golden"]:
        tx = idx.tx_by_id.get(c["primary_trans_id"]) if c["primary_trans_id"] else None
        fired = eng.evaluate(user_id=c["user_id"], tx=tx, complaint_at=c["complaint_at"],
                             utterance_text=" ".join(c["utterances"]),
                             otp_disclosed=c["otp_disclosed"],
                             refund_dest_ref=c["refund_dest_ref"])
        if fired != c["expected"]["fraud_signals"]:
            v.append(f'ENGINE: {c["case_id"]} engine={fired} ≠ expected={c["expected"]["fraud_signals"]}')
            continue
        decision = eng.decide(fired)
        if decision["escalate"] != c["expected"]["must_escalate_immediately"]:
            v.append(f'ENGINE: {c["case_id"]} escalate lệch')
        if c["edge_type"] == "fraud_suspect" and decision["priority"] != c["expected"]["priority"]:
            v.append(f'ENGINE: {c["case_id"]} priority lệch')
    return v


def check_utterance_grounding(d: dict) -> list[str]:
    """Mọi mã GD trong lời khách phải thuộc seeds (trừ not_found — mã cố tình không tồn tại)."""
    v = []
    txs = {t["trans_id"] for t in d["transactions"]}
    for c in d["golden"]:
        for utt in c["utterances"]:
            for tid in TXN_IN_TEXT_RE.findall(utt):
                if c["edge_type"] == "not_found":
                    if tid in txs:
                        v.append(f'GROUND: {c["case_id"]} mã not_found lại tồn tại thật')
                elif tid not in set(c["seed_trans_ids"]):
                    v.append(f'GROUND: {c["case_id"]} nhắc {tid} ngoài seeds')
    return v


def check_business_shape(d: dict) -> list[str]:
    v = []
    channel_map = {k: set(vv) for k, vv in d["scenarios"]["channel_map"].items()}
    for t in d["transactions"]:
        if t["channel"] not in channel_map[t["scope"]]:
            v.append(f'SHAPE: tx {t["trans_id"]} channel {t["channel"]} lạc scope {t["scope"]}')
        if t["status"] == "pending" and t["scope"] != "internal_wallet":
            v.append(f'SHAPE: tx {t["trans_id"]} pending ngoài internal')
        has_completed = t["completed_at"] is not None
        if t["status"] in ("success", "refunded", "failed") and not has_completed:
            v.append(f'SHAPE: tx {t["trans_id"]} thiếu completed_at')
        if t["status"] in ("pending", "processing", "on_hold") and has_completed:
            v.append(f'SHAPE: tx {t["trans_id"]} {t["status"]} không được có completed_at')
        if t["scope"] == "to_bank":
            want = 3300 if t["amount"] <= 20_000_000 else 5500
            if t["fee"] != want:
                v.append(f'SHAPE: tx {t["trans_id"]} fee {t["fee"]} ≠ {want} (BR-19)')
        elif t["fee"] != 0:
            v.append(f'SHAPE: tx {t["trans_id"]} fee phải 0 (BR-19)')
    return v


ALL_CHECKS = [
    ("I1  khoá ngoại", check_i1_foreign_keys),
    ("I2  scope ↔ bên gửi/nhận", check_i2_scope_parties),
    ("I3  event đối tác", check_i3_partner_events),
    ("I4  timeline liền mạch", check_i4_event_chain),
    ("I5  status khớp event cuối", check_i5_status_matches_last_event),
    ("I6  bằng chứng double_charge", check_i6_double_charge_evidence),
    ("I7  tiền nguyên dương", check_i7_integer_money),
    ("I8  phủ ma trận & edge", check_i8_coverage),
    ("I9  dải định danh test", check_i9_test_ranges),
    ("I10 nhãn golden đầy đủ", check_i10_golden_labels),
    ("DIST phân bố nền", check_distributions),
    ("ACT  hoạt động ≥85/90 ngày", check_activity),
    ("SPLIT dev/held-out phân tầng", check_split),
    ("ENGINE nhãn fraud khớp máy", check_fraud_engine_agreement),
    ("GROUND số liệu trong utterance", check_utterance_grounding),
    ("SHAPE quy tắc nghiệp vụ nền", check_business_shape),
]


def run_all(gen_dir: Path) -> dict[str, list[str]]:
    d = load_dataset(gen_dir)
    return {name: fn(d) for name, fn in ALL_CHECKS}


def main():
    gen_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data/generated"
    results = run_all(gen_dir)
    failed = False
    for name, violations in results.items():
        mark = "PASS" if not violations else "FAIL"
        print(f"[{mark}] {name}" + (f" — {len(violations)} vi phạm" if violations else ""))
        for line in violations[:10]:
            print(f"        {line}")
        if len(violations) > 10:
            print(f"        ... và {len(violations) - 10} vi phạm nữa")
        failed = failed or bool(violations)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
