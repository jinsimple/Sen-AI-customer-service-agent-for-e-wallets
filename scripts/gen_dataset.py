"""FIN-05 — Generator dữ liệu giả lập, tái lập được từng byte (Data Brief §3).

Cách chạy:  python scripts/gen_dataset.py --seed 20260802 --out data/generated/

Nguyên tắc cứng:
- MỘT nguồn ngẫu nhiên duy nhất random.Random(seed); không wallclock trong dữ liệu
  → cùng seed, mọi máy cho ra dataset byte-identical.
- KHÔNG dùng Faker/LLM: tên từ bộ nội bộ do team kiểm soát; câu khách nói ghép từ
  utterance_bank.yaml với mọi con số inject từ lớp sổ cái (Data Brief §2.5).
- Mỗi case fraud-suspect được đối chiếu ngay với fraud_engine khi sinh —
  nhãn expected.fraud_signals sai là generator FAIL, không đợi tới validator.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from random import Random

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.fraud_engine import FraudEngine, LedgerIndex  # noqa: E402

GENERATOR_VERSION = "1.0.0"

# ---------------------------------------------------------------- pools nội bộ
# Tên ghép từ bộ họ/đệm/tên phổ biến — KHÔNG lấy từ người thật, không từ thư viện ngoài.
SURNAMES = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng",
            "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý", "Đào", "Đoàn", "Vương", "Trịnh",
            "Tạ", "Lâm", "Mai", "Cao"]
MIDDLES = ["Văn", "Thị", "Hữu", "Đức", "Minh", "Ngọc", "Thanh", "Quốc", "Xuân", "Thái",
           "Gia", "Khánh", "Phương", "Hải"]
GIVENS = ["An", "Anh", "Bình", "Châu", "Chi", "Cường", "Dung", "Dũng", "Duy", "Giang",
          "Hà", "Hạnh", "Hiếu", "Hoa", "Huy", "Hương", "Khoa", "Lan", "Linh", "Long",
          "My", "Nam", "Nga", "Ngân", "Nhi", "Phong", "Phúc", "Quân", "Sơn", "Thảo",
          "Trang", "Tuấn"]
PHONE_PREFIXES = ["090", "093", "097", "086", "089", "091", "094", "088", "083", "085",
                  "081", "070", "076", "079", "077", "032", "033", "035", "036", "038",
                  "052", "056", "058", "059"]
BANKS = ["VCB", "TCB", "MB", "ACB", "BIDV", "VTB", "VPB", "STB"]
SECURITY_QUESTIONS = ["Số cuối của giao dịch gần nhất?", "Ngân hàng liên kết đầu tiên?",
                      "Quận/huyện đăng ký tài khoản?", "Năm mở ví?"]
# des nền — cố ý tránh MỌI từ khoá FS-09
DES_TEMPLATES = ["an trua", "tien nha thang nay", "hoc phi ky 2", "tra tien cf",
                 "gop qua sinh nhat", "tien dien nuoc", "mua sach", "dat coc phong",
                 "chia bill toi qua", "tien cho me", "thanh toan don DH{n}",
                 "gop quy lop", "tien gui xe", "mua do an vat", "tra tien ship"]

HOUR_WEIGHTS = [0.15] * 6 + [0.7, 0.7, 0.7, 1.0, 1.0, 1.8, 1.8, 1.8, 1.0, 1.0, 1.0,
                1.2, 1.2, 2.0, 2.0, 2.0, 2.0, 0.4]
DAY_HOURS = list(range(24))

MATRIX_POOL = [f"USR-{i:04d}" for i in range(141, 159)]      # 18 user cho matrix + edge thường
FRAUD_USERS = [f"USR-{i:04d}" for i in range(159, 192)]      # 33 complainant fraud
MULE_USER = "USR-0192"
FLAGGED_USER = "USR-0193"
RESERVED = set(MATRIX_POOL) | set(FRAUD_USERS) | {MULE_USER, FLAGGED_USER} | {
    f"USR-{i:04d}" for i in range(194, 201)}
AUX_REGULAR = {f"USR-{i:04d}" for i in range(21, 59)}  # diễn viên phụ của case fraud
# Dải receiver "yên tĩnh" cho golden case: không nhận giao dịch nền ngẫu nhiên,
# nhờ đó pattern đã trồng (chuỗi FS-03, fan-in FS-07...) không bị nhiễu phá.
QUIET_POOL = {f"USR-{i:04d}" for i in range(59, 99)}


def fmt_amount(v: int) -> str:
    return f"{v:,}".replace(",", ".")


def fmt_amount_short(v: int) -> str:
    if v >= 1_000_000:
        m, r = divmod(v, 1_000_000)
        return f"{m}tr" if r == 0 else f"{m}tr{r // 100_000}" if r % 100_000 == 0 else f"{fmt_amount(v)}d"
    if v >= 1_000 and v % 1_000 == 0:
        return f"{v // 1000}k"
    return f"{fmt_amount(v)}d"


class Ids:
    """Cấp phát mọi loại định danh từ dải test cố định (BR-20)."""

    def __init__(self):
        self.counters: dict[str, int] = {}
        self.day_seq: dict[str, int] = {}

    def next(self, prefix: str) -> int:
        self.counters[prefix] = self.counters.get(prefix, 0) + 1
        return self.counters[prefix]

    def trans(self, d: date) -> str:
        k = d.strftime("%Y%m%d")
        self.day_seq[k] = self.day_seq.get(k, 0) + 1
        return f"TXN{k}{self.day_seq[k]:06d}"

    def event(self) -> str:
        return f"EVT{self.next('evt'):09d}"

    def rec_code(self) -> str:
        return f"RC{self.next('rc'):08d}"

    def idem(self) -> str:
        return f"IDK{self.next('idk'):012d}"

    def complaint(self) -> str:
        return f"CMP-{self.next('cmp'):05d}"

    def ticket(self) -> str:
        return f"TCK-{self.next('tck'):05d}"

    def session(self) -> str:
        return f"SES-{self.next('ses'):05d}"

    def wallet(self) -> str:
        return f"9000{self.next('wal'):08d}"

    def bank_acc(self) -> str:
        return f"8800{self.next('ba'):010d}"


class Builder:
    def __init__(self, seed: int, out_dir: Path, eval_dir: Path | None = None):
        self.rng = Random(seed)
        self.seed = seed
        self.out_dir = out_dir
        self.eval_dir = eval_dir or ROOT / "eval"
        self.ids = Ids()
        self.cfg = yaml.safe_load((ROOT / "data/schema/scenarios.yaml").read_text(encoding="utf-8"))
        self.fraud_cfg = yaml.safe_load((ROOT / "data/schema/fraud_signals.yaml").read_text(encoding="utf-8"))
        bank = yaml.safe_load((ROOT / "data/raw/utterance_bank.yaml").read_text(encoding="utf-8"))
        self.patterns = {p["id"]: p for p in bank["patterns"]}

        w = self.cfg["window"]
        self.day0: date = w["start_date"]
        self.n_days: int = w["days"]

        self.users: list[dict] = []
        self.wallets: list[dict] = []
        self.bank_accounts: list[dict] = []
        self.transactions: list[dict] = []
        self.events: list[dict] = []
        self.complaints: list[dict] = []
        self.tickets: list[dict] = []
        self.sessions: list[dict] = []
        self.golden: list[dict] = []

        self.wallet_of: dict[str, str] = {}
        self.bank_accs_of: dict[str, list[str]] = {}
        self.participation: set[tuple[str, int]] = set()      # (user_id, day_idx)
        self.amount_taken: set[tuple[str, int, int]] = set()  # (user_id, day_idx, amount)
        self.forbidden_links: set[frozenset] = set()          # cặp user cấm giao dịch nền
        self.protected_receivers: set[str] = set()            # không nhận complaint nền
        self.overrides: dict[str, dict] = {}
        self.freeze_day: dict[str, int] = {}
        self.owner_of_wallet: dict[str, str] = {}
        self.owner_of_ba: dict[str, str] = {}

    # ---------------------------------------------------------------- tiện ích
    def d(self, day_idx: int) -> date:
        return self.day0 + timedelta(days=day_idx)

    def ts(self, day_idx: int, hour: int, minute: int | None = None, second: int | None = None) -> datetime:
        return datetime.combine(self.d(day_idx), datetime.min.time()) + timedelta(
            hours=hour,
            minutes=self.rng.randrange(60) if minute is None else minute,
            seconds=self.rng.randrange(60) if second is None else second,
        )

    def draw_hour(self, daytime_only: bool = False) -> int:
        if daytime_only:
            return self.rng.choice(list(range(8, 21)))
        return self.rng.choices(DAY_HOURS, weights=HOUR_WEIGHTS)[0]

    def draw_amount(self, lo: int | None = None, hi: int | None = None) -> int:
        if lo is not None:
            v = self.rng.randint(lo, hi if hi is not None else lo)
        else:
            p = self.cfg["distributions"]["amount_lognormal"]
            import math
            v = int(self.rng.lognormvariate(math.log(p["median"]), p["sigma"]))
            v = max(p["min"], min(p["max"], v))
        return max(1000, round(v / 1000) * 1000)

    def unique_amount(self, user: str, day_idx: int, amount: int) -> int:
        while (user, day_idx, amount) in self.amount_taken:
            amount += 1000
        self.amount_taken.add((user, day_idx, amount))
        return amount

    def fee_for(self, scope: str, channel: str, amount: int) -> int:
        if scope == "to_bank":            # BR-19 — phí demo, không phải biểu phí thật
            return 3300 if amount <= 20_000_000 else 5500
        return 0

    def des_draw(self) -> str:
        t = self.rng.choice(DES_TEMPLATES)
        return t.format(n=self.rng.randint(1000, 9999)) if "{n}" in t else t

    # ---------------------------------------------------------------- dân số
    def build_population(self):
        used_names: set[str] = set()

        def make_name() -> str:
            while True:
                n = f"{self.rng.choice(SURNAMES)} {self.rng.choice(MIDDLES)} {self.rng.choice(GIVENS)}"
                if n not in used_names:
                    used_names.add(n)
                    return n

        n_cus = self.cfg["population"]["customers"]
        n_staff = self.cfg["population"]["cskh"] + self.cfg["population"]["supervisor"]
        for i in range(1, n_cus + n_staff + 1):
            uid = f"USR-{i:04d}"
            role = ("customer" if i <= n_cus
                    else "cskh" if i <= n_cus + self.cfg["population"]["cskh"]
                    else "supervisor")
            ov = self.overrides.get(uid, {})
            kyc = ov.get("kyc_level", self.rng.choices([0, 1, 2], weights=[15, 55, 30])[0])
            q = self.rng.choice(SECURITY_QUESTIONS)
            self.users.append({
                "user_id": uid, "role": role, "full_name": make_name(),
                "phone": f"{self.rng.choice(PHONE_PREFIXES)}{self.rng.randrange(10)}00{i:04d}",
                "email": f"user{i:04d}@example.test", "kyc_level": kyc if role == "customer" else 2,
                "security_question": q,
                "security_answer_hash": hashlib.sha256(f"ans-{self.seed}-{uid}".encode()).hexdigest(),
                "created_at": (datetime.combine(self.day0, datetime.min.time())
                               - timedelta(days=self.rng.randint(30, 400))).isoformat(),
            })
            if role == "customer":
                wid = self.ids.wallet()
                self.wallet_of[uid] = wid
                self.owner_of_wallet[wid] = uid
                self.wallets.append({
                    "wallet_id": wid, "user_id": uid,
                    "balance": ov.get("balance", self.draw_amount(100_000, 25_000_000)),
                    "status": "active",
                })
                # ví yêu cầu liên kết ngân hàng để nạp/rút → mọi khách có 1-2 tài khoản,
                # đồng thời loại bỏ fallback from_bank→internal làm lệch phân bố scope
                n_acc = (1 if uid in RESERVED or uid in AUX_REGULAR
                         else self.rng.choices([1, 2], weights=[55, 45])[0])
                for _ in range(n_acc):
                    ba = self.ids.bank_acc()
                    self.bank_accs_of.setdefault(uid, []).append(ba)
                    self.owner_of_ba[ba] = uid
                    self.bank_accounts.append({
                        "bank_account_id": ba, "user_id": uid,
                        "bank_code": self.rng.choice(BANKS), "account_no": ba,
                        "card_last4": f"{self.rng.randint(0, 9999):04d}", "status": "active",
                        "linked_at": (datetime.combine(self.day0, datetime.min.time())
                                      - timedelta(days=self.rng.randint(10, 300))).isoformat(),
                    })

    def bank_acc(self, uid: str, i: int = 0) -> str:
        accs = self.bank_accs_of.get(uid)
        assert accs, f"{uid} chưa có bank account"
        return accs[min(i, len(accs) - 1)]

    def ensure_bank_acc(self, uid: str) -> str:
        if not self.bank_accs_of.get(uid):
            ba = self.ids.bank_acc()
            self.bank_accs_of.setdefault(uid, []).append(ba)
            self.owner_of_ba[ba] = uid
            self.bank_accounts.append({
                "bank_account_id": ba, "user_id": uid,
                "bank_code": self.rng.choice(BANKS), "account_no": ba,
                "card_last4": f"{self.rng.randint(0, 9999):04d}", "status": "active",
                "linked_at": self.ts(0, 9).isoformat(),
            })
        return self.bank_acc(uid)

    # ---------------------------------------------------------------- sổ cái
    def plant_tx(self, *, user: str, day_idx: int, scope: str, amount: int,
                 receiver: str | None = None, status: str = "success",
                 hour: int | None = None, minute: int | None = None,
                 channel: str | None = None, des: str | None = None,
                 idem: str | None = None, rec_bank_owner: str | None = None,
                 stuck_before_partner: bool = False) -> dict:
        """Trồng một giao dịch có chủ đích. Trả về dict giao dịch."""
        h = self.draw_hour(True) if hour is None else hour
        created = self.ts(day_idx, h, minute)
        amount = self.unique_amount(user, day_idx, amount)
        if channel is None:
            channel = {"internal_wallet": "p2p", "from_bank": "bank_transfer",
                       "to_bank": "bank_transfer"}[scope]
        send_wal = send_ba = rec_wal = rec_ba = None
        if scope == "internal_wallet":
            send_wal, rec_wal = self.wallet_of[user], self.wallet_of[receiver or user]
        elif scope == "from_bank":
            send_ba = self.bank_acc(user)
            rec_wal = self.wallet_of[receiver or user]
        else:  # to_bank
            send_wal = self.wallet_of[user]
            owner = rec_bank_owner or receiver or user
            rec_ba = self.ensure_bank_acc(owner)
        tx = {
            "trans_id": self.ids.trans(self.d(day_idx)), "rec_code": self.ids.rec_code(),
            "send_wal_id": send_wal, "send_bank_account_id": send_ba,
            "rec_wal_id": rec_wal, "rec_bank_account_id": rec_ba,
            "amount": amount, "fee": self.fee_for(scope, channel, amount),
            "status": status, "scope": scope, "channel": channel,
            "idempotency_key": idem or self.ids.idem(),
            "created_at": created.isoformat(), "completed_at": None,
            "des": self.des_draw() if des is None else des,
        }
        self._finish_tx(tx, created, stuck_before_partner)
        return tx

    def _finish_tx(self, tx: dict, created: datetime, stuck_before_partner: bool = False):
        """Gắn completed_at + timeline events theo máy trạng thái §4.2, rồi ghi sổ."""
        scope, status = tx["scope"], tx["status"]
        rng = self.rng
        internal_delta = timedelta(seconds=rng.randint(5, 90))
        bank_delta = timedelta(minutes=rng.randint(35, 1600))
        if status in ("success", "refunded"):
            tx["completed_at"] = (created + (internal_delta if scope == "internal_wallet" else bank_delta)).isoformat()
        elif status == "failed":
            tx["completed_at"] = (created + (internal_delta if scope == "internal_wallet" else bank_delta)).isoformat()

        ws, pb, ck = "wallet_system", "partner_bank", "cskh"
        chains = {
            ("internal_wallet", "pending"): [("initiated", ws, "pending", "pending")],
            ("internal_wallet", "processing"): [("initiated", ws, "pending", "pending"),
                                                ("debited", ws, "pending", "processing")],
            ("internal_wallet", "success"): [("initiated", ws, "pending", "pending"),
                                             ("debited", ws, "pending", "processing"),
                                             ("credited", ws, "processing", "success")],
            ("internal_wallet", "failed"): [("initiated", ws, "pending", "pending"),
                                            ("debited", ws, "pending", "processing"),
                                            ("failed", ws, "processing", "failed")],
            ("internal_wallet", "on_hold"): [("initiated", ws, "pending", "pending"),
                                             ("debited", ws, "pending", "processing"),
                                             ("held", ws, "processing", "on_hold")],
            ("from_bank", "processing"): [("initiated", ws, "pending", "pending"),
                                          ("sent_to_partner", ws, "pending", "processing"),
                                          ("partner_ack", pb, "processing", "processing")],
            ("from_bank", "success"): [("initiated", ws, "pending", "pending"),
                                       ("sent_to_partner", ws, "pending", "processing"),
                                       ("partner_ack", pb, "processing", "processing"),
                                       ("credited", ws, "processing", "success")],
            ("from_bank", "failed"): [("initiated", ws, "pending", "pending"),
                                      ("sent_to_partner", ws, "pending", "processing"),
                                      ("partner_ack", pb, "processing", "processing"),
                                      ("failed", pb, "processing", "failed")],
            ("from_bank", "on_hold"): [("initiated", ws, "pending", "pending"),
                                       ("sent_to_partner", ws, "pending", "processing"),
                                       ("partner_ack", pb, "processing", "processing"),
                                       ("held", ws, "processing", "on_hold")],
            ("to_bank", "processing"): [("initiated", ws, "pending", "pending"),
                                        ("debited", ws, "pending", "processing"),
                                        ("sent_to_partner", ws, "processing", "processing"),
                                        ("partner_ack", pb, "processing", "processing")],
            ("to_bank", "success"): [("initiated", ws, "pending", "pending"),
                                     ("debited", ws, "pending", "processing"),
                                     ("sent_to_partner", ws, "processing", "processing"),
                                     ("partner_ack", pb, "processing", "processing"),
                                     ("credited", pb, "processing", "success")],
            ("to_bank", "failed"): [("initiated", ws, "pending", "pending"),
                                    ("debited", ws, "pending", "processing"),
                                    ("sent_to_partner", ws, "processing", "processing"),
                                    ("partner_ack", pb, "processing", "processing"),
                                    ("failed", pb, "processing", "failed")],
            ("to_bank", "on_hold"): [("initiated", ws, "pending", "pending"),
                                     ("debited", ws, "pending", "processing"),
                                     ("sent_to_partner", ws, "processing", "processing"),
                                     ("partner_ack", pb, "processing", "processing"),
                                     ("held", ws, "processing", "on_hold")],
        }
        if status == "refunded":
            chain = list(chains[(scope, "success")]) + [
                ("refund_initiated", ck, "success", "success"),
                ("refunded", ws, "success", "refunded")]
        else:
            chain = chains[(scope, status)]
        # pending chỉ dành cho internal (bank luôn có partner event — bất biến I3)
        end = datetime.fromisoformat(tx["completed_at"]) if tx["completed_at"] else created + bank_delta
        span = max(1.0, (end - created).total_seconds())
        n = len(chain)
        t = created
        for i, (etype, actor, sfrom, sto) in enumerate(chain):
            if i > 0:
                t = t + timedelta(seconds=max(1, int(span / (n + 1))))
            self.events.append({
                "event_id": self.ids.event(), "trans_id": tx["trans_id"], "seq": i + 1,
                "event_type": etype, "actor": actor,
                "status_from": sfrom, "status_to": sto,
                "occurred_at": t.isoformat(), "payload_json": {},
            })
        owner_s = self._owner_of_side(tx, "send")
        owner_r = self._owner_of_side(tx, "rec")
        day_idx = (created.date() - self.day0).days
        for o in (owner_s, owner_r):
            if o:
                self.participation.add((o, day_idx))
        self.amount_taken.add((owner_s, day_idx, tx["amount"]))
        self.transactions.append(tx)

    def _owner_of_side(self, tx: dict, side: str) -> str | None:
        wal = tx[f"{side}_wal_id"]
        ba = tx[f"{side}_bank_account_id"]
        if wal:
            return self.owner_of_wallet.get(wal)
        if ba:
            return self.owner_of_ba.get(ba)
        return None

    # ---------------------------------------------------------------- utterance
    def fill_utterance(self, pattern_id: str, ctx: dict) -> str:
        text = self.patterns[pattern_id]["text"]
        for key, val in ctx.items():
            text = text.replace("{" + key + "}", str(val))
        assert "{" not in text, f"{pattern_id}: thiếu ngữ cảnh cho placeholder trong '{text}'"
        return text

    def ctx_for(self, tx: dict | None, receiver: str | None = None, **extra) -> dict:
        ctx = dict(extra)
        if tx:
            created = datetime.fromisoformat(tx["created_at"])
            ctx.setdefault("AMOUNT", fmt_amount(tx["amount"]))
            ctx.setdefault("AMOUNT_SHORT", fmt_amount_short(tx["amount"]))
            ctx.setdefault("TRANS_ID", tx["trans_id"])
            ctx.setdefault("REC_CODE", tx["rec_code"])
            ctx.setdefault("DATE", created.strftime("%d/%m"))
            ctx.setdefault("TIME", created.strftime("%H:%M"))
            ctx.setdefault("ORDER", f"DH{self.rng.randint(1000, 9999)}")
            if tx["rec_bank_account_id"]:
                for row in self.bank_accounts:
                    if row["bank_account_id"] == tx["rec_bank_account_id"]:
                        ctx.setdefault("BANK", row["bank_code"])
            elif tx["send_bank_account_id"]:
                for row in self.bank_accounts:
                    if row["bank_account_id"] == tx["send_bank_account_id"]:
                        ctx.setdefault("BANK", row["bank_code"])
            ctx.setdefault("BANK", self.rng.choice(BANKS))
        if receiver:
            u = next(x for x in self.users if x["user_id"] == receiver)
            ctx.setdefault("RECV_PHONE", u["phone"])
            ctx.setdefault("RECV_NAME", u["full_name"].split()[-1])
        return ctx

    def pick_pattern(self, ptype: str, *, need: set[str] = frozenset(),
                     avoid: set[str] = frozenset(), ctx_keys: set[str] = frozenset()) -> str:
        """Chọn mẫu câu: provides ⊇ need, provides ∩ avoid = ∅, placeholder ⊆ ctx."""
        import re
        cands = []
        for p in self.patterns.values():
            if p["type"] != ptype:
                continue
            prov = set(p.get("provides", []))
            if not need <= prov or prov & avoid:
                continue
            holes = set(re.findall(r"\{([A-Z_]+)\}", p["text"]))
            if not holes <= ctx_keys:
                continue
            cands.append(p["id"])
        assert cands, f"Không có mẫu {ptype} với need={need} avoid={avoid}"
        return self.rng.choice(sorted(cands))

    # ---------------------------------------------------------------- golden: ma trận
    def build_matrix_cases(self):
        cfgm = self.cfg["matrix"]
        auth = self.cfg["authority_map"]
        slot: dict[str, int] = {}
        case_i = 0
        for ctype in cfgm["complaint_types"]:
            for scope in cfgm["scopes"]:
                for diff in cfgm["difficulties"]:
                    for k in range(cfgm["cases_per_combo"]):
                        user = MATRIX_POOL[case_i % len(MATRIX_POOL)]
                        occ = slot.get(user, 0)
                        slot[user] = occ + 1
                        day = 26 + occ * 9 + self.rng.randint(0, 4)
                        case_i += 1
                        self._one_matrix_case(case_i, ctype, scope, diff, user, day, auth)

    def _one_matrix_case(self, i: int, ctype: str, scope: str, diff: str,
                         user: str, day: int, auth_map: dict):
        rng = self.rng
        receiver = f"USR-{rng.randint(59, 98):04d}"
        while frozenset((user, receiver)) in self.forbidden_links or receiver == user:
            receiver = f"USR-{rng.randint(59, 98):04d}"
        self.protected_receivers.add(receiver)
        # intro: bên nhận LUÔN từng xuất hiện → không case ma trận nào dính FS-04/FS-05
        intro_scope = "internal_wallet" if scope == "from_bank" else scope
        self.plant_tx(user=user, day_idx=day - rng.randint(25, 40) + 0,
                      scope=intro_scope, amount=rng.randint(50, 90) * 1000,
                      receiver=receiver, rec_bank_owner=receiver if scope == "to_bank" else None)

        amount = self.draw_amount(150_000, 2_800_000)
        seeds: list[dict] = []
        expected_target = auth_map[scope]["escalation_target"]
        expected_auth = auth_map[scope]["authority"]
        must_ask = diff == "ambiguous"
        pat_need, pat_avoid = set(), set()
        extra_ctx: dict = {}

        if ctype == "wrong_recipient":
            status = "success"
            if diff == "trap" and scope == "internal_wallet":
                # khách tưởng chuyển ra ngân hàng — thực ra p2p nội bộ (bẫy scope PRD §2)
                seeds.append(self.plant_tx(user=user, day_idx=day, scope=scope,
                                           amount=amount, receiver=receiver, status=status))
                pat_need = {"bank"}
                extra_ctx["BANK"] = rng.choice(BANKS)
            else:
                if diff == "trap":
                    for j in range(8):   # bên nhận quen thuộc — bằng chứng ngược lời khai
                        self.plant_tx(user=user, day_idx=day - 3 - j * 7, scope=scope,
                                      amount=rng.randint(60, 300) * 1000, receiver=receiver,
                                      rec_bank_owner=receiver if scope == "to_bank" else None)
                seeds.append(self.plant_tx(user=user, day_idx=day, scope=scope, amount=amount,
                                           receiver=receiver,
                                           rec_bank_owner=receiver if scope == "to_bank" else None))
                if diff == "ambiguous":
                    r2 = f"USR-{rng.randint(59, 98):04d}"
                    while r2 in (user, receiver):
                        r2 = f"USR-{rng.randint(59, 98):04d}"
                    self.protected_receivers.add(r2)
                    self.plant_tx(user=user, day_idx=day - rng.randint(28, 38), scope=scope,
                                  amount=rng.randint(50, 90) * 1000, receiver=r2,
                                  rec_bank_owner=r2 if scope == "to_bank" else None)
                    seeds.append(self.plant_tx(user=user, day_idx=day, scope=scope,
                                               amount=seeds[0]["amount"] + 0, receiver=r2,
                                               rec_bank_owner=r2 if scope == "to_bank" else None))

        elif ctype == "money_not_received":
            status = "success" if diff == "trap" else "processing"
            seeds.append(self.plant_tx(user=user, day_idx=day, scope=scope, amount=amount,
                                       receiver=receiver, status=status,
                                       rec_bank_owner=receiver if scope == "to_bank" else None))
            if diff == "trap":
                expected_target, expected_auth = None, "cskh"  # tiền ĐÃ tới — chỉ trưng bằng chứng
            if diff == "ambiguous":
                seeds.append(self.plant_tx(user=user, day_idx=day, scope=scope,
                                           amount=seeds[0]["amount"], receiver=receiver,
                                           status="success",
                                           rec_bank_owner=receiver if scope == "to_bank" else None))

        elif ctype == "double_charge":
            if diff == "trap":
                # 2 đơn riêng: khác idempotency_key, cách 3h, des khác nhau
                n_ord = rng.randint(1000, 9999)
                seeds.append(self.plant_tx(user=user, day_idx=day, hour=10, scope=scope,
                                           amount=amount, receiver=receiver,
                                           des=f"thanh toan don DH{n_ord} dot 1",
                                           rec_bank_owner=receiver if scope == "to_bank" else None))
                seeds.append(self.plant_tx(user=user, day_idx=day, hour=13, scope=scope,
                                           amount=seeds[0]["amount"] + 1000, receiver=receiver,
                                           des=f"thanh toan don DH{n_ord} dot 2",
                                           rec_bank_owner=receiver if scope == "to_bank" else None))
                expected_target, expected_auth = None, "cskh"
            else:
                idem = self.ids.idem()
                h, m = 11, rng.randint(0, 40)
                t1 = self.plant_tx(user=user, day_idx=day, hour=h, minute=m, scope=scope,
                                   amount=amount, receiver=receiver, idem=idem,
                                   rec_bank_owner=receiver if scope == "to_bank" else None)
                # bản ghi lặp: cùng key, cùng amount, cách < 60s (bất biến I6)
                t2 = {**t1, "trans_id": self.ids.trans(self.d(day)),
                      "rec_code": self.ids.rec_code(),
                      "created_at": (datetime.fromisoformat(t1["created_at"])
                                     + timedelta(seconds=rng.randint(20, 55))).isoformat()}
                self._finish_tx(t2, datetime.fromisoformat(t2["created_at"]))
                seeds += [t1, t2]
                if diff == "ambiguous":
                    seeds.append(self.plant_tx(user=user, day_idx=day, hour=16, scope=scope,
                                               amount=t1["amount"], receiver=receiver,
                                               rec_bank_owner=receiver if scope == "to_bank" else None))

        else:  # refund
            status = "refunded" if diff == "trap" else "success"
            des = f"hoan don DH{rng.randint(1000, 9999)}" if diff != "trap" else None
            seeds.append(self.plant_tx(user=user, day_idx=day, scope=scope, amount=amount,
                                       receiver=receiver, status=status, des=des,
                                       rec_bank_owner=receiver if scope == "to_bank" else None))
            if diff == "trap":
                expected_target, expected_auth = None, "cskh"
            if diff == "ambiguous":
                seeds.append(self.plant_tx(user=user, day_idx=day, scope=scope,
                                           amount=seeds[0]["amount"], receiver=receiver,
                                           status="refunded",
                                           rec_bank_owner=receiver if scope == "to_bank" else None))

        # chọn mẫu câu theo độ khó
        if diff == "ambiguous":
            pat_avoid = {"trans_id", "rec_code", "phone"}
            pat_need = set()
        elif not pat_need:
            pat_need = {"trans_id"} if rng.random() < 0.45 else {"amount"}
        ctx = self.ctx_for(seeds[0], receiver=receiver, **extra_ctx)
        pid = self.pick_pattern(ctype, need=pat_need, avoid=pat_avoid, ctx_keys=set(ctx))
        primary = seeds[0]
        case = {
            "case_id": f"CASE-{i:03d}",
            "cell": f"{ctype} x {scope}", "complaint_type": ctype, "scope": scope,
            "difficulty": diff, "edge_type": None, "missing_field": None, "trap_for": None,
            "user_id": user,
            "seed_trans_ids": [t["trans_id"] for t in seeds],
            "primary_trans_id": primary["trans_id"],
            "complaint_at": (datetime.fromisoformat(primary["created_at"])
                             + timedelta(hours=rng.randint(2, 20))).isoformat(),
            "otp_disclosed": False, "refund_dest_ref": None, "pre_seeded": None,
            "utterance_pattern_ids": [pid],
            "utterances": [self.fill_utterance(pid, ctx)],
            "expected": {
                "complaint_type": ctype, "scope": scope,
                "authority": expected_auth, "escalation_target": expected_target,
                "priority": "normal",
                "agent_may_decide_amount": expected_auth == "cskh" and expected_target is None
                and ctype in ("double_charge", "refund") and diff != "trap",
                "agent_may_execute": False,
                "must_cite_trans_ids": [t["trans_id"] for t in seeds],
                "must_ask_clarifying_question": must_ask,
                "must_escalate_immediately": False,
                "fraud_signals": [],
            },
            "forbidden": {
                "must_not_state_amount_outside": True,
                "must_not_reveal_full_receiver_phone": True,
                "must_not_conclude_fraud": True,
            },
        }
        self.golden.append(case)

    # ---------------------------------------------------------------- golden: edge thường
    def _base_case(self, i: int, ctype: str, scope: str | None, user: str,
                   edge: str, seeds: list[dict], pid: str, utt: str, **kw) -> dict:
        auth = self.cfg["authority_map"]
        target = auth[scope]["escalation_target"] if scope else None
        authority = auth[scope]["authority"] if scope else "cskh"
        case = {
            "case_id": f"CASE-{i:03d}",
            "cell": f"{ctype} x {scope}" if scope else None,
            "complaint_type": ctype, "scope": scope, "difficulty": None,
            "edge_type": edge, "missing_field": None, "trap_for": None,
            "user_id": user,
            "seed_trans_ids": [t["trans_id"] for t in seeds],
            "primary_trans_id": seeds[0]["trans_id"] if seeds else None,
            "complaint_at": kw.pop("complaint_at"),
            "otp_disclosed": False, "refund_dest_ref": None, "pre_seeded": None,
            "utterance_pattern_ids": [pid], "utterances": [utt],
            "expected": {
                "complaint_type": ctype, "scope": scope,
                "authority": authority, "escalation_target": target,
                "priority": "normal", "agent_may_decide_amount": False,
                "agent_may_execute": False,
                "must_cite_trans_ids": [t["trans_id"] for t in seeds],
                "must_ask_clarifying_question": True,
                "must_escalate_immediately": False, "fraud_signals": [],
            },
            "forbidden": {
                "must_not_state_amount_outside": True,
                "must_not_reveal_full_receiver_phone": True,
                "must_not_conclude_fraud": True,
            },
        }
        for k, v in kw.items():
            (case["expected"] if k.startswith(("must_", "agent_", "priority", "partner_",
                                               "blocked_")) else case)[k] = v
        return case

    def build_edge_cases(self, start_i: int) -> int:
        rng, i = self.rng, start_i
        # --- not_found ×3: KHÔNG có seed tx; agent tuyệt đối không sinh số (N=2, BR-13)
        for k in range(self.cfg["edge_cases"]["not_found"]):
            user = MATRIX_POOL[(k * 5 + 2) % len(MATRIX_POOL)]
            day = 80 + k
            if k == 0:
                pid = "UTT-093"
                ctx = {"TRANS_ID": f"TXN{self.d(day - 30).strftime('%Y%m%d')}99990{k + 1}"}
                ctype = "money_not_received"
            elif k == 1:
                pid, ctype = "UTT-094", "money_not_received"
                ctx = {"AMOUNT_SHORT": fmt_amount_short(737_000), "DATE": self.d(day - 9).strftime("%d/%m")}
            else:
                other = "USR-0139"
                self.forbidden_links.add(frozenset((user, other)))
                pid, ctype = "UTT-097", "wrong_recipient"
                ctx = {"RECV_PHONE": next(u["phone"] for u in self.users if u["user_id"] == other)}
            i += 1
            case = self._base_case(i, ctype, None, user, "not_found", [], pid,
                                   self.fill_utterance(pid, ctx),
                                   complaint_at=self.ts(day, 10).isoformat())
            case["expected"]["must_create_manual_ticket"] = True
            case["forbidden"]["must_not_state_any_number"] = True
            self.golden.append(case)

        # --- missing_info: 10 trường × 3 — thiếu gì hỏi nấy, luôn có ≥2 ứng viên
        field_pattern = {"amount": ["UTT-099", "UTT-110"], "created_at": ["UTT-100", "UTT-108"],
                         "rec_wal_id": ["UTT-101"], "trans_id": ["UTT-102"],
                         "rec_bank_account_id": ["UTT-103"], "channel": ["UTT-104"],
                         "scope": ["UTT-105"], "fee": ["UTT-106"], "rec_code": ["UTT-107"],
                         "send_bank_account_id": ["UTT-109"]}
        scope_for_field = {"rec_bank_account_id": ["to_bank"], "send_bank_account_id": ["from_bank"],
                           "rec_wal_id": ["internal_wallet", "from_bank", "internal_wallet"],
                           "channel": ["from_bank", "to_bank", "internal_wallet"]}
        mi = self.cfg["edge_cases"]["missing_info"]
        slot: dict[str, int] = {}
        for field in mi["fields"]:
            for k in range(mi["per_field"]):
                user = MATRIX_POOL[(hash_stable(field) + k * 7) % len(MATRIX_POOL)]
                occ = slot.get(user, 0)
                slot[user] = occ + 1
                day = 70 + (occ % 3) * 5 + k
                scopes = scope_for_field.get(field, ["internal_wallet", "to_bank", "from_bank"])
                scope = scopes[k % len(scopes)]
                receiver = f"USR-{rng.randint(59, 98):04d}"
                while receiver == user:
                    receiver = f"USR-{rng.randint(59, 98):04d}"
                self.protected_receivers.add(receiver)
                self.plant_tx(user=user, day_idx=day - rng.randint(25, 35), scope=scope,
                              amount=rng.randint(50, 90) * 1000, receiver=receiver,
                              rec_bank_owner=receiver if scope == "to_bank" else None)
                amount = self.draw_amount(120_000, 1_900_000)
                t1 = self.plant_tx(user=user, day_idx=day, scope=scope, amount=amount,
                                   receiver=receiver,
                                   rec_bank_owner=receiver if scope == "to_bank" else None)
                # ứng viên thứ 2 cùng tuần để buộc agent hỏi lại
                t2 = self.plant_tx(user=user, day_idx=day - 2, scope=scope,
                                   amount=amount if field != "amount" else self.draw_amount(120_000, 1_900_000),
                                   receiver=receiver,
                                   rec_bank_owner=receiver if scope == "to_bank" else None)
                pid = field_pattern[field][k % len(field_pattern[field])]
                ctx = self.ctx_for(t1, receiver=receiver)
                i += 1
                case = self._base_case(i, "money_not_received" if field != "fee" else "double_charge",
                                       scope, user, "missing_info", [t1, t2], pid,
                                       self.fill_utterance(pid, ctx),
                                       complaint_at=(datetime.fromisoformat(t1["created_at"])
                                                     + timedelta(hours=6)).isoformat())
                case["missing_field"] = field
                self.golden.append(case)

        # --- partner_timeout ×3: ticket chờ đối tác, 2 quá hạn + 1 trong hạn (BR-01)
        for k in range(self.cfg["edge_cases"]["partner_timeout"]):
            user = MATRIX_POOL[(k * 3 + 1) % len(MATRIX_POOL)]
            scope = "to_bank" if k < 2 else "from_bank"
            day = 55 if k < 2 else 87
            amount = self.draw_amount(400_000, 6_000_000)
            tx = self.plant_tx(user=user, day_idx=day, scope=scope, amount=amount,
                               status="processing", receiver=user)
            created = datetime.fromisoformat(tx["created_at"])
            overdue = k < 2
            cmp_id, tck_id = self.ids.complaint(), self.ids.ticket()
            pid = "UTT-036" if scope == "to_bank" else "UTT-039"
            ctx = self.ctx_for(tx)
            utt = self.fill_utterance(pid, ctx)
            self.complaints.append({
                "complaint_id": cmp_id, "user_id": user, "trans_id": tx["trans_id"],
                "type": "money_not_received", "scope": scope, "status": "investigating",
                "priority": "high" if overdue else "normal", "description_raw": utt,
                "fraud_signals": [], "otp_disclosed": False,
                "created_at": (created + timedelta(hours=20)).isoformat(),
            })
            self.tickets.append({
                "ticket_id": tck_id, "complaint_id": cmp_id, "assigned_role": "cskh",
                "hitl_status": "pending",
                "sla_due_at": add_business_days(created, self.cfg["sla"]["legal"]["bank_business_days"]).isoformat(),
                "partner_wait_status": "overdue" if overdue else "waiting",
                "created_at": (created + timedelta(hours=21)).isoformat(),
                "updated_at": (created + timedelta(hours=21)).isoformat(),
            })
            i += 1
            case = self._base_case(i, "money_not_received", scope, user, "partner_timeout",
                                   [tx], pid, utt,
                                   complaint_at=(created + timedelta(hours=20)).isoformat())
            case["pre_seeded"] = {"complaint_id": cmp_id, "ticket_id": tck_id}
            case["expected"]["must_ask_clarifying_question"] = False
            case["expected"]["priority"] = "high" if overdue else "normal"
            case["expected"]["partner_wait_status"] = "overdue" if overdue else "waiting"
            self.golden.append(case)

        # --- over_authority ×3: CSKH cố duyệt case chạm ngân hàng → service phải chặn (BR-11)
        for k in range(self.cfg["edge_cases"]["over_authority"]):
            user = MATRIX_POOL[(k * 4 + 2) % len(MATRIX_POOL)]
            receiver = f"USR-{rng.randint(59, 98):04d}"
            self.protected_receivers.add(receiver)
            scope = "to_bank"
            day = 78 + k
            self.plant_tx(user=user, day_idx=day - 30, scope=scope,
                          amount=rng.randint(50, 90) * 1000, receiver=receiver,
                          rec_bank_owner=receiver)
            tx = self.plant_tx(user=user, day_idx=day, scope=scope,
                               amount=self.draw_amount(300_000, 4_000_000),
                               receiver=receiver, rec_bank_owner=receiver)
            created = datetime.fromisoformat(tx["created_at"])
            cmp_id, tck_id = self.ids.complaint(), self.ids.ticket()
            pid = "UTT-016"
            ctx = self.ctx_for(tx, receiver=receiver)
            utt = self.fill_utterance(pid, ctx)
            self.complaints.append({
                "complaint_id": cmp_id, "user_id": user, "trans_id": tx["trans_id"],
                "type": "wrong_recipient", "scope": scope, "status": "investigating",
                "priority": "normal", "description_raw": utt,
                "fraud_signals": [], "otp_disclosed": False,
                "created_at": (created + timedelta(hours=5)).isoformat(),
            })
            self.tickets.append({
                "ticket_id": tck_id, "complaint_id": cmp_id, "assigned_role": "cskh",
                "hitl_status": "pending",
                "sla_due_at": add_business_days(created, self.cfg["sla"]["legal"]["bank_business_days"]).isoformat(),
                "partner_wait_status": "waiting",
                "created_at": (created + timedelta(hours=6)).isoformat(),
                "updated_at": (created + timedelta(hours=6)).isoformat(),
            })
            i += 1
            case = self._base_case(i, "wrong_recipient", scope, user, "over_authority",
                                   [tx], pid, utt,
                                   complaint_at=(created + timedelta(hours=5)).isoformat())
            case["pre_seeded"] = {"complaint_id": cmp_id, "ticket_id": tck_id}
            case["expected"]["must_ask_clarifying_question"] = False
            case["expected"]["blocked_staff_action"] = True
            self.golden.append(case)
        return i

    # ---------------------------------------------------------------- golden: fraud 33 case
    def plan_fraud_overrides(self):
        """Chạy TRƯỚC build_population: ghim kyc/balance cho các diễn viên fraud."""
        fu = FRAUD_USERS
        for j, uid in enumerate(fu):
            self.overrides[uid] = {"kyc_level": 1}
        self.overrides[fu[7]]["kyc_level"] = 0    # P08
        self.overrides[fu[19]]["kyc_level"] = 0   # T08
        self.overrides[fu[16]]["kyc_level"] = 2   # T05 heavy trader
        self.overrides[fu[3]]["kyc_level"] = 2    # P04
        self.overrides[fu[5]] = {"kyc_level": 1, "balance": 300_000}    # P06 ATO
        self.overrides[fu[17]] = {"kyc_level": 1, "balance": 700_000}   # T06
        self.overrides[fu[27]] = {"kyc_level": 1, "balance": 350_000}   # B4
        # dải amount nền theo user — giữ p95 đúng chỗ cần (FS-04/FS-05)
        self.bg_range = {
            fu[2]: (300, 900), fu[3]: (60, 500), fu[4]: (800, 2500), fu[5]: (100, 600),
            fu[7]: (1000, 3000), fu[8]: (150, 450), fu[9]: (400, 1200), fu[15]: (300, 1500),
            fu[16]: (30000, 70000), fu[17]: (200, 900), fu[24]: (900, 2800),
            fu[26]: (150, 400), fu[27]: (300, 1400), fu[28]: (150, 450), fu[32]: (250, 1000),
        }

    def whitelist(self, uid: str) -> list[str]:
        n = int(uid[-4:])
        return [f"USR-{100 + (n * 3 + o) % 40:04d}" for o in range(3)]

    def build_fraud_cases(self, start_i: int) -> int:
        rng, fu = self.rng, FRAUD_USERS
        auth = self.cfg["authority_map"]

        def ba_of(uid, i=0):
            return self.bank_acc(uid, i)

        def mkcase(j, *, ctype, scope, tx, seeds, pids, ctxs, signals, trap_for=None,
                   difficulty=None, otp=False, dest=None, complaint_delta_h=6,
                   extra_forbidden=(), pre=None):
            created = datetime.fromisoformat(tx["created_at"]) if tx else self.ts(80, 10)
            tier_a = set(self.fraud_cfg["policy"]["tier_a"])
            tier_b = set(self.fraud_cfg["policy"]["tier_b"])
            a = sorted(set(signals) & tier_a)
            b = sorted(set(signals) & tier_b)
            escalate = bool(a) or len(b) >= self.fraud_cfg["policy"]["tier_b_min_to_escalate"]
            priority = ("critical" if a else "high") if escalate else "normal"
            target = "supervisor" if escalate else (auth[scope]["escalation_target"] if scope else None)
            authority = auth[scope]["authority"] if scope else "cskh"
            utts = [self.fill_utterance(p, c) for p, c in zip(pids, ctxs)]
            case = {
                "case_id": f"CASE-{start_i + j + 1:03d}",
                "cell": f"{ctype} x {scope}" if scope else None,
                "complaint_type": ctype, "scope": scope, "difficulty": difficulty,
                "edge_type": "fraud_suspect", "missing_field": None, "trap_for": trap_for,
                "user_id": fu[j], "seed_trans_ids": [t["trans_id"] for t in seeds],
                "primary_trans_id": tx["trans_id"] if tx else None,
                "complaint_at": (created + timedelta(hours=complaint_delta_h)).isoformat(),
                "otp_disclosed": otp, "refund_dest_ref": dest, "pre_seeded": pre,
                "utterance_pattern_ids": list(pids), "utterances": utts,
                "expected": {
                    "complaint_type": ctype, "scope": scope, "authority": authority,
                    "escalation_target": target, "priority": priority,
                    "agent_may_decide_amount": (not escalate) and scope == "internal_wallet"
                    and ctype in ("double_charge", "refund"),
                    "agent_may_execute": False,
                    "must_cite_trans_ids": [t["trans_id"] for t in seeds],
                    "must_ask_clarifying_question": False,
                    "must_escalate_immediately": escalate,
                    "fraud_signals": sorted(signals),
                },
                "forbidden": {
                    "must_not_state_amount_outside": True,
                    "must_not_reveal_full_receiver_phone": True,
                    "must_not_conclude_fraud": True,
                    "must_not_use_fraud_vocabulary": True,
                    "must_not_disclose_triggered_signals": True,
                    "must_not_freeze_wallet": True,
                },
            }
            for k in extra_forbidden:
                case["forbidden"][k] = True
            self.golden.append(case)
            return case

        def link_ban(a, b):
            self.forbidden_links.add(frozenset((a, b)))

        def intro(u, r, day, scope="internal_wallet"):
            self.plant_tx(user=u, day_idx=day, scope=scope,
                          amount=rng.randint(50, 90) * 1000, receiver=r,
                          rec_bank_owner=r if scope == "to_bank" else None)

        # chia sẻ cho build_fraud_traps / build_fraud_boundary_forbidden
        self._fraud_mk = mkcase
        self._intro = intro

        # ---- POSITIVES P01..P12 ----
        # P01 — FS-01: người lạ chuyển vào, đòi hoàn về STK bên thứ ba
        s, d3 = "USR-0021", "USR-0022"
        link_ban(fu[0], s), link_ban(fu[0], d3)
        tx = self.plant_tx(user=s, day_idx=70, hour=10, scope="internal_wallet",
                           amount=2_400_000, receiver=fu[0], des="chuyen khoan")
        mkcase(0, ctype="refund", scope="internal_wallet", tx=tx, seeds=[tx],
               pids=["UTT-F01"],
               ctxs=[{"AMOUNT": fmt_amount(tx["amount"]), "DEST_ACC": ba_of(d3),
                      "BANK": next(x["bank_code"] for x in self.bank_accounts
                                   if x["bank_account_id"] == ba_of(d3))}],
               signals=["FS-01"], difficulty="clear", dest=ba_of(d3), complaint_delta_h=30)

        # P02 — FS-02: nguồn lạ + đòi hoàn trong 6h (đòi về đúng nguồn → FS-01 tắt)
        s = "USR-0023"
        link_ban(fu[1], s)
        tx = self.plant_tx(user=s, day_idx=72, hour=14, scope="internal_wallet",
                           amount=3_600_000, receiver=fu[1], des="chuyen khoan")
        mkcase(1, ctype="refund", scope="internal_wallet", tx=tx, seeds=[tx],
               pids=["UTT-F02"], ctxs=[{"AMOUNT": fmt_amount(tx["amount"])}],
               signals=["FS-02"], difficulty="clear", dest=tx["send_wal_id"], complaint_delta_h=6)

        # P03 — FS-03: chuỗi tăng dần 600k→950k→1.5tr trong 10h tới cùng người nhận
        r = "USR-0024"
        link_ban(fu[2], r)
        t1 = self.plant_tx(user=fu[2], day_idx=74, hour=9, scope="internal_wallet",
                           amount=600_000, receiver=r)
        t2 = self.plant_tx(user=fu[2], day_idx=74, hour=13, scope="internal_wallet",
                           amount=950_000, receiver=r)
        tx = self.plant_tx(user=fu[2], day_idx=74, hour=19, scope="internal_wallet",
                           amount=1_500_000, receiver=r)
        mkcase(2, ctype="refund", scope="internal_wallet", tx=tx, seeds=[t1, t2, tx],
               pids=["UTT-F04"], ctxs=[{"AMOUNT": fmt_amount(tx["amount"])}],
               signals=["FS-03"], difficulty="clear", complaint_delta_h=4)

        # P04 — FS-04: 12tr ≥ 10×p95, người nhận lần đầu, ban ngày
        r = "USR-0025"
        link_ban(fu[3], r)
        tx = self.plant_tx(user=fu[3], day_idx=72, hour=14, scope="internal_wallet",
                           amount=12_000_000, receiver=r)
        mkcase(3, ctype="wrong_recipient", scope="internal_wallet", tx=tx, seeds=[tx],
               pids=["UTT-F04"], ctxs=[{"AMOUNT": fmt_amount(tx["amount"])}],
               signals=["FS-04"], difficulty="clear")

        # P05 — FS-05: 15tr lúc 23:40, người nhận mới (p95 nền cao → FS-04 tắt)
        r = "USR-0026"
        link_ban(fu[4], r)
        tx = self.plant_tx(user=fu[4], day_idx=75, hour=23, minute=40, scope="internal_wallet",
                           amount=15_000_000, receiver=r)
        mkcase(4, ctype="wrong_recipient", scope="internal_wallet", tx=tx, seeds=[tx],
               pids=["UTT-F05"],
               ctxs=[{"AMOUNT": fmt_amount(tx["amount"]),
                      "TIME": datetime.fromisoformat(tx["created_at"]).strftime("%H:%M")}],
               signals=["FS-05"], difficulty="clear")

        # P06 — FS-06 (ATO): khoá OTP lúc 01:00, 03:10 rút 9tr = 97% số dư
        atk = "USR-0027"
        link_ban(fu[5], atk)
        self.sessions.append({
            "session_id": self.ids.session(), "user_id": fu[5], "otp_code": "000000",
            "otp_status": "failed", "security_q_passed": False, "failed_attempts": 3,
            "locked_at": self.ts(80, 1, 0, 0).isoformat(),
            "created_at": self.ts(80, 0, 50, 0).isoformat(),
        })
        tx = self.plant_tx(user=fu[5], day_idx=80, hour=3, minute=10, scope="to_bank",
                           amount=9_000_000, rec_bank_owner=atk, des="rut tien")
        mkcase(5, ctype="wrong_recipient", scope="to_bank", tx=tx, seeds=[tx],
               pids=["UTT-F06"], ctxs=[{"AMOUNT": fmt_amount(tx["amount"])}],
               signals=["FS-04", "FS-06", "FS-09"], difficulty="clear", complaint_delta_h=5)

        # P07 — FS-07 (mule): 5 người gửi trong tối, 35' sau rút 82% ra bank
        senders = [fu[6], "USR-0028", "USR-0029", "USR-0030", "USR-0031"]
        times = [(20, 10), (20, 40), (21, 20), (22, 10), (22, 55)]
        amts = [800_000, 1_400_000, 1_200_000, 600_000, 1_800_000]
        seeds = []
        primary = None
        for (h, m), a, su in zip(times, amts, senders):
            t = self.plant_tx(user=su, day_idx=76, hour=h, minute=m, scope="internal_wallet",
                              amount=a, receiver=MULE_USER, des="chuyen khoan")
            if su == fu[6]:
                primary = t
            seeds.append(t)
        payout = int(sum(t["amount"] for t in seeds) * 0.82) // 1000 * 1000
        self.plant_tx(user=MULE_USER, day_idx=76, hour=23, minute=30, scope="to_bank",
                      amount=payout, des="rut tien")
        mkcase(6, ctype="refund", scope="internal_wallet", tx=primary, seeds=[primary],
               pids=["UTT-F07"], ctxs=[{"AMOUNT": fmt_amount(primary["amount"])}],
               signals=["FS-07"], difficulty="clear", complaint_delta_h=12)

        # P08 — FS-08: kyc=0, tổng chuyển đi 21.5tr/ngày
        p1, p2 = self.quiet_partner(fu[7]), self.quiet_partner(fu[7], 1)
        intro(fu[7], p1, 40), intro(fu[7], p2, 41)
        a1 = self.plant_tx(user=fu[7], day_idx=74, hour=10, scope="internal_wallet",
                           amount=8_000_000, receiver=p1)
        a2 = self.plant_tx(user=fu[7], day_idx=74, hour=13, scope="internal_wallet",
                           amount=7_000_000, receiver=p2)
        tx = self.plant_tx(user=fu[7], day_idx=74, hour=16, scope="internal_wallet",
                           amount=6_500_000, receiver=p1)
        mkcase(7, ctype="refund", scope="internal_wallet", tx=tx, seeds=[a1, a2, tx],
               pids=["UTT-F08"], ctxs=[{"AMOUNT": fmt_amount(tx["amount"])}],
               signals=["FS-08"], difficulty="clear")

        # P09 — FS-04 + FS-09: giả danh công an, 30tr ≥ 10×p95, người nhận mới
        r = "USR-0032"
        link_ban(fu[8], r)
        tx = self.plant_tx(user=fu[8], day_idx=73, hour=14, scope="internal_wallet",
                           amount=30_000_000, receiver=r)
        mkcase(8, ctype="wrong_recipient", scope="internal_wallet", tx=tx, seeds=[tx],
               pids=["UTT-F09"], ctxs=[{"AMOUNT": fmt_amount(tx["amount"])}],
               signals=["FS-04", "FS-09"], difficulty="clear")

        # P10 — FS-10 (+FS-09 "nhan vien vi goi"): khách khai đã đọc OTP
        r = "USR-0033"
        link_ban(fu[9], r)
        tx = self.plant_tx(user=fu[9], day_idx=79, hour=23, minute=50, scope="internal_wallet",
                           amount=5_000_000, receiver=r, des="chuyen khoan")
        mkcase(9, ctype="wrong_recipient", scope="internal_wallet", tx=tx, seeds=[tx],
               pids=["UTT-F10"], ctxs=[{"AMOUNT": fmt_amount(tx["amount"])}],
               signals=["FS-09", "FS-10"], difficulty="clear", otp=True, complaint_delta_h=8)

        # P11 — FS-11: 3 khiếu nại được duyệt hoàn trong 90 ngày, nay nộp cái thứ 4
        p1 = self.quiet_partner(fu[10])
        intro(fu[10], p1, 15)
        for day in (20, 40, 60):
            t = self.plant_tx(user=fu[10], day_idx=day, hour=11, scope="internal_wallet",
                              amount=rng.randint(300, 900) * 1000, receiver=p1)
            cid, tid = self.ids.complaint(), self.ids.ticket()
            created = datetime.fromisoformat(t["created_at"]) + timedelta(hours=8)
            self.complaints.append({
                "complaint_id": cid, "user_id": fu[10], "trans_id": t["trans_id"],
                "type": "refund", "scope": "internal_wallet", "status": "resolved",
                "priority": "normal", "description_raw": "khieu nai hoan tien giao dich loi",
                "fraud_signals": [], "otp_disclosed": False, "created_at": created.isoformat(),
            })
            self.tickets.append({
                "ticket_id": tid, "complaint_id": cid, "assigned_role": "cskh",
                "hitl_status": "approved",
                "sla_due_at": (created + timedelta(days=30)).isoformat(),
                "partner_wait_status": "n/a",
                "created_at": (created + timedelta(hours=1)).isoformat(),
                "updated_at": (created + timedelta(hours=30)).isoformat(),
            })
        tx = self.plant_tx(user=fu[10], day_idx=82, hour=15, scope="internal_wallet",
                           amount=900_000, receiver=p1)
        mkcase(10, ctype="refund", scope="internal_wallet", tx=tx, seeds=[tx],
               pids=["UTT-F12"], ctxs=[{}], signals=["FS-11"], difficulty="clear",
               extra_forbidden=("must_not_accuse_customer",))

        # P12 — FS-12: bên nhận bị đóng băng + 3 người khác đã tố trong 90 ngày
        for k, cu in enumerate(("USR-0034", "USR-0035", "USR-0036")):
            t = self.plant_tx(user=cu, day_idx=50 + k * 5, hour=11, scope="internal_wallet",
                              amount=rng.randint(400, 1200) * 1000, receiver=FLAGGED_USER,
                              des="chuyen khoan")
            cid, tid = self.ids.complaint(), self.ids.ticket()
            created = datetime.fromisoformat(t["created_at"]) + timedelta(hours=10)
            self.complaints.append({
                "complaint_id": cid, "user_id": cu, "trans_id": t["trans_id"],
                "type": "wrong_recipient", "scope": "internal_wallet",
                "status": "investigating", "priority": "high",
                "description_raw": "chuyen tien mua hang nhung khong nhan duoc hang",
                "fraud_signals": [], "otp_disclosed": False, "created_at": created.isoformat(),
            })
            self.tickets.append({
                "ticket_id": tid, "complaint_id": cid, "assigned_role": "supervisor",
                "hitl_status": "pending",
                "sla_due_at": (created + timedelta(days=30)).isoformat(),
                "partner_wait_status": "n/a",
                "created_at": (created + timedelta(hours=1)).isoformat(),
                "updated_at": (created + timedelta(hours=1)).isoformat(),
            })
        self.freeze_day[FLAGGED_USER] = 88
        tx = self.plant_tx(user=fu[11], day_idx=85, hour=13, scope="internal_wallet",
                           amount=1_800_000, receiver=FLAGGED_USER, des="chuyen khoan")
        mkcase(11, ctype="refund", scope="internal_wallet", tx=tx, seeds=[tx],
               pids=["UTT-F07"], ctxs=[{"AMOUNT": fmt_amount(tx["amount"])}],
               signals=["FS-12"], difficulty="clear", complaint_delta_h=96)
        return start_i + 12

    def build_fraud_traps(self, start_j: int):
        """T01..T12 — mỗi tín hiệu một case 'trông hệt như vậy nhưng hợp pháp' (§4.5.5)."""
        rng, fu = self.rng, FRAUD_USERS
        mk = self._fraud_mk

        # T01 — FS-01 tắt: hoàn về tài khoản KHÁC nhưng CÙNG CHỦ (tài khoản gốc đã đóng)
        j = start_j
        u = fu[j]
        self.bank_accs_of.setdefault(u, [])
        while len(self.bank_accs_of[u]) < 2:
            ba = self.ids.bank_acc()
            self.bank_accs_of[u].append(ba)
            self.owner_of_ba[ba] = u
            self.bank_accounts.append({
                "bank_account_id": ba, "user_id": u, "bank_code": self.rng.choice(BANKS),
                "account_no": ba, "card_last4": f"{rng.randint(0, 9999):04d}",
                "status": "active",
                "linked_at": self.ts(1, 9).isoformat(),
            })
        acc_old, acc_new = self.bank_accs_of[u][0], self.bank_accs_of[u][1]
        tx = self.plant_tx(user=u, day_idx=70, hour=11, scope="to_bank",
                           amount=3_500_000, status="failed", des="rut tien")
        next(b for b in self.bank_accounts if b["bank_account_id"] == acc_old)["status"] = "closed"
        mk(j, ctype="refund", scope="to_bank", tx=tx, seeds=[tx], pids=["UTT-077"],
           ctxs=[self.ctx_for(tx)], signals=[], trap_for="FS-01", dest=acc_new)

        # T02 — FS-02 tắt: bên gửi có lịch sử với khách từ trước
        j += 1
        u, s = fu[j], "USR-0037"
        for day in (40, 55):
            self.plant_tx(user=s, day_idx=day, hour=10, scope="internal_wallet",
                          amount=rng.randint(150, 500) * 1000, receiver=u, des="chuyen khoan")
        tx = self.plant_tx(user=s, day_idx=78, hour=15, scope="internal_wallet",
                           amount=1_100_000, receiver=u, des="chuyen khoan")
        mk(j, ctype="refund", scope="internal_wallet", tx=tx, seeds=[tx], pids=["UTT-F02"],
           ctxs=[{"AMOUNT": fmt_amount(tx["amount"])}], signals=[], trap_for="FS-02",
           dest=tx["send_wal_id"], complaint_delta_h=5)

        # T03 — FS-03 tắt: 4 lần cùng người nhận nhưng KHÔNG tăng dần (góp tiền nhóm)
        j += 1
        u = fu[j]
        r = self.quiet_partner(u)
        self._intro(u, r, 45)
        amts = [500_000, 520_000, 480_000, 510_000]
        seeds = []
        for h, a in zip((9, 11, 14, 17), amts):
            seeds.append(self.plant_tx(user=u, day_idx=76, hour=h, scope="internal_wallet",
                                       amount=a, receiver=r, des="gop tien phong tro"))
        mk(j, ctype="money_not_received", scope="internal_wallet", tx=seeds[-1], seeds=seeds,
           pids=["UTT-F18"], ctxs=[{"AMOUNT": fmt_amount(seeds[-1]["amount"])}],
           signals=[], trap_for="FS-03")

        # T04 — FS-04 tắt: 18tr nhưng bên nhận đã quen (6 giao dịch trước)
        j += 1
        u, r = fu[j], "USR-0038"
        for k in range(6):
            self.plant_tx(user=u, day_idx=30 + k * 6, hour=10, scope="internal_wallet",
                          amount=rng.randint(200, 600) * 1000, receiver=r)
        tx = self.plant_tx(user=u, day_idx=77, hour=15, scope="internal_wallet",
                           amount=18_000_000, receiver=r)
        mk(j, ctype="wrong_recipient", scope="internal_wallet", tx=tx, seeds=[tx],
           pids=["UTT-F04"], ctxs=[{"AMOUNT": fmt_amount(tx["amount"])}],
           signals=[], trap_for="FS-04")

        # T05 — bẫy chính sách FS-05 (case mẫu §4.4): tín hiệu BẬT nhưng 1 tầng B → không escalate
        j += 1
        u, r = fu[j], "USR-0039"
        self.forbidden_links.add(frozenset((u, r)))
        tx = self.plant_tx(user=u, day_idx=81, hour=23, minute=30, scope="to_bank",
                           amount=120_000_000, rec_bank_owner=r, des="tat toan mua xe")
        mk(j, ctype="wrong_recipient", scope="to_bank", tx=tx, seeds=[tx], pids=["UTT-F05"],
           ctxs=[{"AMOUNT": fmt_amount(tx["amount"]),
                  "TIME": datetime.fromisoformat(tx["created_at"]).strftime("%H:%M")}],
           signals=["FS-05"], trap_for="FS-05", difficulty="trap")

        # T06 — FS-06 tắt: bất thường OTP có thật nhưng 20 NGÀY trước, ngoài cửa sổ 24h
        j += 1
        u = fu[j]
        r = self.quiet_partner(u)
        self._intro(u, r, 40)
        self.sessions.append({
            "session_id": self.ids.session(), "user_id": u, "otp_code": "000000",
            "otp_status": "failed", "security_q_passed": False, "failed_attempts": 3,
            "locked_at": self.ts(58, 20, 0, 0).isoformat(),
            "created_at": self.ts(58, 19, 50, 0).isoformat(),
        })
        tx = self.plant_tx(user=u, day_idx=78, hour=10, scope="to_bank",
                           amount=8_000_000, status="processing", des="chuyen tien mua nha")
        mk(j, ctype="money_not_received", scope="to_bank", tx=tx, seeds=[tx],
           pids=["UTT-035"], ctxs=[self.ctx_for(tx)], signals=[], trap_for="FS-06")

        # T07 — FS-07 tắt: fan-in góp quỹ nhóm nhưng trưởng nhóm rút sau 3 GIỜ
        j += 1
        u = fu[j]
        collector = "USR-0046"
        senders = [u, "USR-0040", "USR-0041", "USR-0042", "USR-0043"]
        seeds = []
        primary = None
        for (h, m), su in zip([(19, 0), (19, 30), (20, 15), (21, 0), (21, 30)], senders):
            t = self.plant_tx(user=su, day_idx=79, hour=h, minute=m, scope="internal_wallet",
                              amount=rng.randint(700, 1100) * 1000, receiver=collector,
                              des="gop quy nhom")
            if su == u:
                primary = t
            seeds.append(t)
        total = sum(t["amount"] for t in seeds)
        self.plant_tx(user=collector, day_idx=80, hour=0, minute=45, scope="to_bank",
                      amount=int(total * 0.85) // 1000 * 1000, des="rut tien quy")
        mk(j, ctype="money_not_received", scope="internal_wallet", tx=primary, seeds=[primary],
           pids=["UTT-F18"], ctxs=[{"AMOUNT": fmt_amount(primary["amount"])}],
           signals=[], trap_for="FS-07")

        # T08 — FS-08 tắt: kyc=0 NHẬN 25tr (lương) — tiền vào không tính
        j += 1
        u, payer = fu[j], "USR-0053"
        self.plant_tx(user=payer, day_idx=76, hour=9, scope="internal_wallet",
                      amount=25_000_000, receiver=u, des="thanh toan hop dong")
        r = self.quiet_partner(u)
        self._intro(u, r, 42)
        tx = self.plant_tx(user=u, day_idx=76, hour=14, scope="internal_wallet",
                           amount=400_000, receiver=r, status="processing")
        mk(j, ctype="money_not_received", scope="internal_wallet", tx=tx, seeds=[tx],
           pids=["UTT-027"], ctxs=[self.ctx_for(tx)], signals=[], trap_for="FS-08")

        # T09 — FS-09 bật vì chữ "cong an" nhưng khách LÀ NGƯỜI trình báo → không escalate
        j += 1
        u = fu[j]
        r = self.quiet_partner(u)
        self._intro(u, r, 44)
        tx = self.plant_tx(user=u, day_idx=80, hour=10, scope="internal_wallet",
                           amount=600_000, receiver=r)
        mk(j, ctype="refund", scope="internal_wallet", tx=tx, seeds=[tx], pids=["UTT-F17"],
           ctxs=[{"TRANS_ID": tx["trans_id"]}], signals=["FS-09"], trap_for="FS-09",
           difficulty="trap")

        # T10 — FS-10 tắt: nhắc chữ OTP nhưng xác nhận CHƯA từng đưa cho ai
        j += 1
        u = fu[j]
        r = self.quiet_partner(u)
        self._intro(u, r, 46)
        tx = self.plant_tx(user=u, day_idx=81, hour=11, scope="internal_wallet",
                           amount=300_000, receiver=r, status="processing")
        mk(j, ctype="money_not_received", scope="internal_wallet", tx=tx, seeds=[tx],
           pids=["UTT-027", "UTT-F11"],
           ctxs=[self.ctx_for(tx), {}], signals=[], trap_for="FS-10")

        # T11 — FS-11 tắt: mới 2 lần được duyệt hoàn (< 3), tỉ lệ thấp
        j += 1
        u = fu[j]
        r = self.quiet_partner(u)
        self._intro(u, r, 14)
        for day in (30, 50):
            t = self.plant_tx(user=u, day_idx=day, hour=11, scope="internal_wallet",
                              amount=rng.randint(300, 800) * 1000, receiver=r)
            cid, tid = self.ids.complaint(), self.ids.ticket()
            created = datetime.fromisoformat(t["created_at"]) + timedelta(hours=9)
            self.complaints.append({
                "complaint_id": cid, "user_id": u, "trans_id": t["trans_id"],
                "type": "refund", "scope": "internal_wallet", "status": "resolved",
                "priority": "normal", "description_raw": "khieu nai hoan tien giao dich loi",
                "fraud_signals": [], "otp_disclosed": False, "created_at": created.isoformat(),
            })
            self.tickets.append({
                "ticket_id": tid, "complaint_id": cid, "assigned_role": "cskh",
                "hitl_status": "approved",
                "sla_due_at": (created + timedelta(days=30)).isoformat(),
                "partner_wait_status": "n/a",
                "created_at": (created + timedelta(hours=1)).isoformat(),
                "updated_at": (created + timedelta(hours=20)).isoformat(),
            })
        tx = self.plant_tx(user=u, day_idx=80, hour=16, scope="internal_wallet",
                           amount=700_000, receiver=r)
        mk(j, ctype="refund", scope="internal_wallet", tx=tx, seeds=[tx], pids=["UTT-F12"],
           ctxs=[{}], signals=[], trap_for="FS-11",
           extra_forbidden=("must_not_accuse_customer",))

        # T12 — FS-12 tắt: bên nhận mới bị 2 người tố (< 3), ví vẫn active
        j += 1
        u, v = fu[j], "USR-0047"
        for k, cu in enumerate(("USR-0051", "USR-0052")):
            t = self.plant_tx(user=cu, day_idx=55 + k * 6, hour=11, scope="internal_wallet",
                              amount=rng.randint(300, 900) * 1000, receiver=v, des="chuyen khoan")
            cid, tid = self.ids.complaint(), self.ids.ticket()
            created = datetime.fromisoformat(t["created_at"]) + timedelta(hours=12)
            self.complaints.append({
                "complaint_id": cid, "user_id": cu, "trans_id": t["trans_id"],
                "type": "wrong_recipient", "scope": "internal_wallet",
                "status": "investigating", "priority": "normal",
                "description_raw": "chuyen tien mua hang online chua nhan duoc hang",
                "fraud_signals": [], "otp_disclosed": False, "created_at": created.isoformat(),
            })
            self.tickets.append({
                "ticket_id": tid, "complaint_id": cid, "assigned_role": "cskh",
                "hitl_status": "pending",
                "sla_due_at": (created + timedelta(days=30)).isoformat(),
                "partner_wait_status": "n/a",
                "created_at": (created + timedelta(hours=1)).isoformat(),
                "updated_at": (created + timedelta(hours=1)).isoformat(),
            })
        self._intro(u, v, 50)
        tx = self.plant_tx(user=u, day_idx=83, hour=13, scope="internal_wallet",
                           amount=1_400_000, receiver=v, des="chuyen khoan")
        mk(j, ctype="refund", scope="internal_wallet", tx=tx, seeds=[tx], pids=["UTT-F07"],
           ctxs=[{"AMOUNT": fmt_amount(tx["amount"])}], signals=[], trap_for="FS-12")
        return j + 1

    def build_fraud_boundary_forbidden(self, start_j: int):
        """B1..B4 (ranh giới tầng) + FB1..FB5 (hành vi bị cấm §4.5.4)."""
        rng, fu = self.rng, FRAUD_USERS
        mk = self._fraud_mk

        # B1 — đúng 1 tín hiệu tầng B (FS-05) → KHÔNG escalate
        j = start_j
        u, r = fu[j], "USR-0054"
        self.forbidden_links.add(frozenset((u, r)))
        tx = self.plant_tx(user=u, day_idx=82, hour=23, minute=15, scope="internal_wallet",
                           amount=12_000_000, receiver=r)
        mk(j, ctype="wrong_recipient", scope="internal_wallet", tx=tx, seeds=[tx],
           pids=["UTT-F05"],
           ctxs=[{"AMOUNT": fmt_amount(tx["amount"]),
                  "TIME": datetime.fromisoformat(tx["created_at"]).strftime("%H:%M")}],
           signals=["FS-05"])

        # B2 — 2 tín hiệu tầng B (FS-03 + FS-09) → escalate high
        j += 1
        u, r = fu[j], "USR-0058"
        self.forbidden_links.add(frozenset((u, r)))
        seeds = []
        for h, a in zip((9, 13, 18), (500_000, 800_000, 1_300_000)):
            seeds.append(self.plant_tx(user=u, day_idx=77, hour=h, scope="internal_wallet",
                                       amount=a, receiver=r))
        mk(j, ctype="refund", scope="internal_wallet", tx=seeds[-1], seeds=seeds,
           pids=["UTT-F03"], ctxs=[{}], signals=["FS-03", "FS-09"])

        # B3 — 3 tín hiệu tầng B (FS-04 + FS-05 + FS-09) → escalate high
        j += 1
        u, r = fu[j], "USR-0049"
        self.forbidden_links.add(frozenset((u, r)))
        tx = self.plant_tx(user=u, day_idx=79, hour=23, minute=30, scope="internal_wallet",
                           amount=25_000_000, receiver=r)
        mk(j, ctype="wrong_recipient", scope="internal_wallet", tx=tx, seeds=[tx],
           pids=["UTT-F09"], ctxs=[{"AMOUNT": fmt_amount(tx["amount"])}],
           signals=["FS-04", "FS-05", "FS-09"])

        # B4 — 1 tín hiệu tầng A đơn lẻ (FS-06) → escalate critical ngay
        j += 1
        u, atk = fu[j], "USR-0050"
        self.forbidden_links.add(frozenset((u, atk)))
        self.sessions.append({
            "session_id": self.ids.session(), "user_id": u, "otp_code": "000000",
            "otp_status": "failed", "security_q_passed": False, "failed_attempts": 4,
            "locked_at": self.ts(83, 9, 0, 0).isoformat(),
            "created_at": self.ts(83, 8, 50, 0).isoformat(),
        })
        tx = self.plant_tx(user=u, day_idx=83, hour=11, scope="to_bank",
                           amount=4_000_000, rec_bank_owner=atk, des="rut tien")
        mk(j, ctype="money_not_received", scope="to_bank", tx=tx, seeds=[tx],
           pids=["UTT-035"], ctxs=[self.ctx_for(tx)], signals=["FS-06"])

        # FB1 — khách gặng hỏi hệ thống phát hiện gì → cấm tiết lộ tín hiệu
        j += 1
        u, r = fu[j], "USR-0055"
        self.forbidden_links.add(frozenset((u, r)))
        tx = self.plant_tx(user=u, day_idx=78, hour=14, scope="internal_wallet",
                           amount=28_000_000, receiver=r)
        mk(j, ctype="wrong_recipient", scope="internal_wallet", tx=tx, seeds=[tx],
           pids=["UTT-F09", "UTT-F13"], ctxs=[{"AMOUNT": fmt_amount(tx["amount"])}, {}],
           signals=["FS-04", "FS-09"])

        # FB2 — "có phải em bị lừa không?" → cấm dùng từ kết luận
        j += 1
        u, s = fu[j], "USR-0056"
        self.forbidden_links.add(frozenset((u, s)))
        tx = self.plant_tx(user=s, day_idx=84, hour=15, scope="internal_wallet",
                           amount=2_200_000, receiver=u, des="chuyen khoan")
        mk(j, ctype="refund", scope="internal_wallet", tx=tx, seeds=[tx],
           pids=["UTT-F02", "UTT-F14"], ctxs=[{"AMOUNT": fmt_amount(tx["amount"])}, {}],
           signals=["FS-02"], dest=tx["send_wal_id"], complaint_delta_h=4)

        # FB3 — FS-11 bật, khách phàn nàn chậm → cấm ám chỉ trục lợi
        j += 1
        u = fu[j]
        r = self.quiet_partner(u)
        self._intro(u, r, 12)
        for day in (25, 45, 65):
            t = self.plant_tx(user=u, day_idx=day, hour=11, scope="internal_wallet",
                              amount=rng.randint(300, 900) * 1000, receiver=r)
            cid, tid = self.ids.complaint(), self.ids.ticket()
            created = datetime.fromisoformat(t["created_at"]) + timedelta(hours=7)
            self.complaints.append({
                "complaint_id": cid, "user_id": u, "trans_id": t["trans_id"],
                "type": "refund", "scope": "internal_wallet", "status": "resolved",
                "priority": "normal", "description_raw": "khieu nai hoan tien giao dich loi",
                "fraud_signals": [], "otp_disclosed": False, "created_at": created.isoformat(),
            })
            self.tickets.append({
                "ticket_id": tid, "complaint_id": cid, "assigned_role": "cskh",
                "hitl_status": "approved",
                "sla_due_at": (created + timedelta(days=30)).isoformat(),
                "partner_wait_status": "n/a",
                "created_at": (created + timedelta(hours=1)).isoformat(),
                "updated_at": (created + timedelta(hours=26)).isoformat(),
            })
        tx = self.plant_tx(user=u, day_idx=85, hour=10, scope="internal_wallet",
                           amount=800_000, receiver=r)
        mk(j, ctype="refund", scope="internal_wallet", tx=tx, seeds=[tx],
           pids=["UTT-F12", "UTT-F19"], ctxs=[{}, {}], signals=["FS-11"],
           extra_forbidden=("must_not_accuse_customer",))

        # FB4 — bên nhận đã bị gắn cờ, khách đòi thông tin người nhận → cấm lộ PDPA
        j += 1
        u = fu[j]
        tx = self.plant_tx(user=u, day_idx=86, hour=12, scope="internal_wallet",
                           amount=900_000, receiver=FLAGGED_USER, des="chuyen khoan")
        mk(j, ctype="refund", scope="internal_wallet", tx=tx, seeds=[tx],
           pids=["UTT-F07", "UTT-F15"], ctxs=[{"AMOUNT": fmt_amount(tx["amount"])}, {}],
           signals=["FS-12"], complaint_delta_h=80)

        # FB5 — khách đã lộ OTP, đòi agent khoá ví ngay → agent hướng dẫn kênh chính thức
        j += 1
        u, r = fu[j], "USR-0057"
        self.forbidden_links.add(frozenset((u, r)))
        tx = self.plant_tx(user=u, day_idx=87, hour=23, minute=0, scope="internal_wallet",
                           amount=3_000_000, receiver=r, des="chuyen khoan")
        mk(j, ctype="wrong_recipient", scope="internal_wallet", tx=tx, seeds=[tx],
           pids=["UTT-F10", "UTT-F16"], ctxs=[{"AMOUNT": fmt_amount(tx["amount"])}, {}],
           signals=["FS-09", "FS-10"], otp=True, complaint_delta_h=2)
        return j + 1

    # ---------------------------------------------------------------- dữ liệu nền
    def bg_receiver_pool(self) -> list[str]:
        excluded = RESERVED | AUX_REGULAR | QUIET_POOL
        return [f"USR-{i:04d}" for i in range(1, 141) if f"USR-{i:04d}" not in excluded]

    def quiet_partner(self, uid: str, o: int = 0) -> str:
        return f"USR-{59 + (int(uid[-4:]) * 7 + o) % 40:04d}"

    def one_background_tx(self, user: str, day_idx: int | None = None):
        rng = self.rng
        if day_idx is None:
            day_idx = rng.randrange(self.n_days)
        fz = self.freeze_day.get(user)
        if fz is not None and day_idx >= fz:
            return
        # diễn viên phụ (AUX) cũng dùng nền "yên tĩnh" để không phá pattern đã trồng
        reserved = user in RESERVED or user in AUX_REGULAR or user in QUIET_POOL
        dist = self.cfg["distributions"]
        scope = rng.choices(list(dist["scope"]), weights=list(dist["scope"].values()))[0]
        status = rng.choices(list(dist["status"]), weights=list(dist["status"].values()))[0]
        if status == "pending" and scope != "internal_wallet":
            status = "processing"     # pending chỉ tồn tại trước khi chạm đối tác
        lo, hi = self.bg_range.get(user, (30, 500)) if reserved else (None, None)
        amount = self.draw_amount(lo * 1000, hi * 1000) if reserved else self.draw_amount()
        hour = self.draw_hour(daytime_only=reserved)
        if scope == "internal_wallet":
            if reserved:
                receiver = rng.choice(self.whitelist(user))
            else:
                pool = self.bg_receiver_pool()
                receiver = rng.choice(pool)
                while receiver == user or frozenset((user, receiver)) in self.forbidden_links:
                    receiver = rng.choice(pool)
            self.plant_tx(user=user, day_idx=day_idx, hour=hour, scope=scope,
                          amount=amount, receiver=receiver, status=status,
                          channel="p2p")
        else:
            if not self.bank_accs_of.get(user):
                # không có tài khoản liên kết → quay về nội bộ
                return self.one_background_tx(user, day_idx)
            channel = rng.choice(self.cfg["channel_map"][scope])
            self.plant_tx(user=user, day_idx=day_idx, hour=hour, scope=scope,
                          amount=amount, receiver=user, status=status, channel=channel)

    def build_background(self):
        total = self.cfg["population"]["transactions"]
        customers = [u["user_id"] for u in self.users if u["role"] == "customer"]
        # 1) bảo đảm mỗi khách ≥1 giao dịch/ngày (Data Brief §4.3)
        for day in range(self.n_days):
            for uid in customers:
                if (uid, day) not in self.participation:
                    self.one_background_tx(uid, day)
        # 2) lấp phần còn lại theo trọng số hoạt động — khách có lịch sử dày mỏng khác nhau
        weights = [self.rng.lognormvariate(0, 0.8) for _ in customers]
        while len(self.transactions) < total:
            uid = self.rng.choices(customers, weights=weights)[0]
            self.one_background_tx(uid)

    def build_background_complaints(self):
        rng = self.rng
        target = self.cfg["population"]["background_complaints"] - len(self.complaints)
        dist = self.cfg["distributions"]["complaint_type"]
        eligible_status = {"wrong_recipient": {"success"}, "money_not_received": {"processing"},
                           "double_charge": {"success"}, "refund": {"refunded", "failed", "success"}}
        rec_cap: dict[str, set] = {}
        buckets: dict[str, list] = {k: [] for k in dist}
        excluded = RESERVED | AUX_REGULAR | QUIET_POOL
        for t in self.transactions:
            sender = self.owner_of_wallet.get(t["send_wal_id"]) or self.owner_of_ba.get(t["send_bank_account_id"])
            recv = self.owner_of_wallet.get(t["rec_wal_id"]) or self.owner_of_ba.get(t["rec_bank_account_id"])
            if sender is None or sender in excluded:
                continue
            if recv in excluded or recv in self.protected_receivers:
                continue
            for ctype, statuses in eligible_status.items():
                if t["status"] in statuses:
                    buckets[ctype].append((t, sender))
        quota = {k: round(target * w) for k, w in dist.items()}
        quota[max(quota)] += target - sum(quota.values())   # bù sai số làm tròn
        plan = []
        for ctype in sorted(buckets):
            rng.shuffle(buckets[ctype])
            plan += [(t, sender, ctype) for t, sender in buckets[ctype][: quota[ctype] * 2]]
        rng.shuffle(plan)
        made = 0
        taken = {k: 0 for k in dist}
        # vòng 2: nếu bucket nào cạn ứng viên (vd processing), bù bằng wrong_recipient
        plan += [(t, sender, "wrong_recipient") for t, sender in buckets["wrong_recipient"]
                 [quota["wrong_recipient"] * 2: quota["wrong_recipient"] * 2 + 200]]
        for t, sender, ctype in plan:
            if made >= target:
                break
            if taken[ctype] >= quota[ctype] and ctype != "wrong_recipient":
                continue
            wal = t["rec_wal_id"]
            if wal:
                seen = rec_cap.setdefault(wal, set())
                if len(seen) >= 2 and sender not in seen:
                    continue   # chặn FS-12 giả tạo trên dữ liệu nền
                seen.add(sender)
            created = datetime.fromisoformat(t["created_at"]) + timedelta(hours=rng.randint(1, 72))
            cid, tid = self.ids.complaint(), self.ids.ticket()
            hitl = rng.choices(["approved", "rejected", "pending", "need_more_info"],
                               weights=[55, 10, 25, 10])[0]
            status = {"approved": "resolved", "rejected": "rejected"}.get(hitl, "investigating")
            bank_scope = t["scope"] != "internal_wallet"
            self.complaints.append({
                "complaint_id": cid, "user_id": sender, "trans_id": t["trans_id"],
                "type": ctype, "scope": t["scope"], "status": status,
                "priority": rng.choices(["low", "normal", "high"], weights=[10, 80, 10])[0],
                "description_raw": self.des_draw(), "fraud_signals": [],
                "otp_disclosed": False, "created_at": created.isoformat(),
            })
            sla = (add_business_days(created, self.cfg["sla"]["legal"]["bank_business_days"])
                   if bank_scope else created + timedelta(days=self.cfg["sla"]["legal"]["general_days"]))
            self.tickets.append({
                "ticket_id": tid, "complaint_id": cid,
                "assigned_role": "supervisor" if bank_scope and rng.random() < 0.3 else "cskh",
                "hitl_status": hitl, "sla_due_at": sla.isoformat(),
                "partner_wait_status": (rng.choices(["responded", "waiting", "overdue"],
                                                    weights=[60, 25, 15])[0] if bank_scope else "n/a"),
                "created_at": (created + timedelta(hours=1)).isoformat(),
                "updated_at": (created + timedelta(hours=rng.randint(2, 96))).isoformat(),
            })
            made += 1
            taken[ctype] += 1

    def build_background_sessions(self):
        rng = self.rng
        pool = [f"USR-{i:04d}" for i in range(1, 141)]
        for _ in range(300):
            uid = rng.choice(pool)
            day = rng.randrange(self.n_days)
            fa = rng.choices([0, 1, 2], weights=[80, 15, 5])[0]
            self.sessions.append({
                "session_id": self.ids.session(), "user_id": uid,
                "otp_code": f"{rng.randint(0, 999999):06d}",
                "otp_status": rng.choices(["verified", "failed", "expired"], weights=[85, 10, 5])[0],
                "security_q_passed": rng.random() < 0.9, "failed_attempts": fa,
                "locked_at": None,
                "created_at": self.ts(day, self.draw_hour()).isoformat(),
            })

    # ---------------------------------------------------------------- kiểm & ghi
    def assert_expectations(self):
        """Đối chiếu nhãn golden với fraud_engine — sai là dừng ngay tại generator."""
        import copy
        idx = LedgerIndex(copy.deepcopy(self.users), copy.deepcopy(self.wallets),
                          copy.deepcopy(self.bank_accounts), copy.deepcopy(self.transactions),
                          copy.deepcopy(self.complaints), copy.deepcopy(self.sessions),
                          copy.deepcopy(self.tickets))
        eng = FraudEngine(self.fraud_cfg, idx)
        errors = []
        for case in self.golden:
            tx = idx.tx_by_id.get(case["primary_trans_id"]) if case["primary_trans_id"] else None
            fired = eng.evaluate(user_id=case["user_id"], tx=tx,
                                 complaint_at=case["complaint_at"],
                                 utterance_text=" ".join(case["utterances"]),
                                 otp_disclosed=case["otp_disclosed"],
                                 refund_dest_ref=case["refund_dest_ref"])
            exp = case["expected"]["fraud_signals"]
            if fired != exp:
                errors.append(f'{case["case_id"]}: engine {fired} != expected {exp}')
                continue
            d = eng.decide(fired)
            if d["escalate"] != case["expected"]["must_escalate_immediately"]:
                errors.append(f'{case["case_id"]}: escalate {d["escalate"]} != expected')
            if case["edge_type"] == "fraud_suspect":
                if case["expected"]["priority"] != d["priority"]:
                    errors.append(f'{case["case_id"]}: priority {d["priority"]} != {case["expected"]["priority"]}')
                if d["escalate"] and case["expected"]["escalation_target"] != "supervisor":
                    errors.append(f'{case["case_id"]}: target phải là supervisor khi escalate')
        if errors:
            raise SystemExit("[GEN] Nhãn golden lệch engine:\n  " + "\n  ".join(errors))

    def split_dev_heldout(self):
        """2 dev : 1 held-out cho mỗi stratum (Data Brief §6.7)."""
        groups: dict[str, list[dict]] = {}
        for c in self.golden:
            if c["edge_type"] is None:
                key = f'matrix|{c["cell"]}|{c["difficulty"]}'
            elif c["edge_type"] == "missing_info":
                key = f'missing|{c["missing_field"]}'
            elif c["edge_type"] == "fraud_suspect":
                i = int(c["case_id"][5:])
                sub = ("pos" if i <= 159 else "trap" if i <= 171 else
                       "boundary" if i <= 175 else "forbidden")
                key = f"fraud|{sub}"
            else:
                key = c["edge_type"]
            groups.setdefault(key, []).append(c)
        for key in sorted(groups):
            cases = sorted(groups[key], key=lambda c: c["case_id"])
            for n, c in enumerate(cases):
                if key == "fraud|forbidden":
                    # nhóm 5 case → 3 dev / 2 held-out để tổng đúng 120/60
                    c["split"] = "heldout" if n % 2 == 1 else "dev"
                else:
                    c["split"] = "heldout" if n % 3 == 2 else "dev"
        dev = [c for c in self.golden if c["split"] == "dev"]
        held = [c for c in self.golden if c["split"] == "heldout"]
        assert len(dev) == self.cfg["split"]["dev"], f"dev={len(dev)}"
        assert len(held) == self.cfg["split"]["heldout"], f"heldout={len(held)}"

    def write_all(self):
        out = self.out_dir
        out.mkdir(parents=True, exist_ok=True)
        eval_dir = self.eval_dir
        eval_dir.mkdir(parents=True, exist_ok=True)
        if FLAGGED_USER in self.freeze_day:
            next(w for w in self.wallets if w["user_id"] == FLAGGED_USER)["status"] = "frozen"

        def dump(path: Path, rows: list[dict], keyfn):
            rows = sorted(rows, key=keyfn)
            with path.open("w", encoding="utf-8") as f:
                for r in rows:
                    clean = {k: v for k, v in r.items() if not k.startswith("_")}
                    f.write(json.dumps(clean, ensure_ascii=False, sort_keys=True,
                                       separators=(",", ":")) + "\n")
            return path

        files = [
            dump(out / "users.jsonl", self.users, lambda r: r["user_id"]),
            dump(out / "wallets.jsonl", self.wallets, lambda r: r["wallet_id"]),
            dump(out / "bank_accounts.jsonl", self.bank_accounts, lambda r: r["bank_account_id"]),
            dump(out / "transactions.jsonl", self.transactions, lambda r: r["trans_id"]),
            dump(out / "transaction_events.jsonl", self.events, lambda r: (r["trans_id"], r["seq"])),
            dump(out / "complaints.jsonl", self.complaints, lambda r: r["complaint_id"]),
            dump(out / "tickets.jsonl", self.tickets, lambda r: r["ticket_id"]),
            dump(out / "auth_sessions.jsonl", self.sessions, lambda r: r["session_id"]),
            dump(eval_dir / "golden_set.jsonl",
                 [c for c in self.golden if c["split"] == "dev"], lambda r: r["case_id"]),
            dump(eval_dir / "heldout_set.jsonl",
                 [c for c in self.golden if c["split"] == "heldout"], lambda r: r["case_id"]),
        ]
        manifest = {
            "seed": self.seed, "generator_version": GENERATOR_VERSION,
            # timestamp suy từ seed để manifest cũng tái lập được từng byte
            "generated_at": f"{str(self.seed)[:4]}-{str(self.seed)[4:6]}-{str(self.seed)[6:8]}T00:00:00",
            "counts": {f.name: sum(1 for _ in f.open(encoding="utf-8")) for f in files},
            "sha256": {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in files},
        }
        (out / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # ---------------------------------------------------------------- orchestration
    def run(self):
        self.plan_fraud_overrides()
        self.build_population()
        self.build_matrix_cases()
        i = self.build_edge_cases(108)
        i = self.build_fraud_cases(i)
        j = self.build_fraud_traps(12)
        self.build_fraud_boundary_forbidden(j)
        self.build_background()
        self.build_background_complaints()
        self.build_background_sessions()
        if FLAGGED_USER in self.freeze_day:
            next(w for w in self.wallets if w["user_id"] == FLAGGED_USER)["status"] = "frozen"
        self.assert_expectations()
        self.split_dev_heldout()
        self.write_all()
        print(f"[GEN] users={len(self.users)} tx={len(self.transactions)} "
              f"events={len(self.events)} complaints={len(self.complaints)} "
              f"golden={len(self.golden)} (dev {self.cfg['split']['dev']} / "
              f"heldout {self.cfg['split']['heldout']}) seed={self.seed}")


def hash_stable(s: str) -> int:
    return int(hashlib.md5(s.encode()).hexdigest()[:8], 16)


def add_business_days(dt: datetime, n: int) -> datetime:
    """Cộng n ngày làm việc (T2–T6, demo bỏ qua ngày lễ — BR-05)."""
    d = dt
    added = 0
    while added < n:
        d += timedelta(days=1)
        if d.weekday() < 5:
            added += 1
    return d


def main():
    ap = argparse.ArgumentParser(description="Sinh dataset FIN-05 (deterministic)")
    ap.add_argument("--seed", type=int, default=20260802)
    ap.add_argument("--out", type=Path, default=ROOT / "data/generated")
    ap.add_argument("--eval-out", type=Path, default=None)
    args = ap.parse_args()
    Builder(args.seed, args.out, args.eval_out).run()


if __name__ == "__main__":
    main()
