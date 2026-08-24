"""FIN-05 — Engine đánh giá 12 tín hiệu gian lận (Data Brief §4.5).

Nguồn ngưỡng duy nhất: data/schema/fraud_signals.yaml (mọi ngưỡng là
assumption, xem BR-14..BR-16). Engine này được dùng ở 2 chỗ:

1. validate_dataset.py — đối chiếu `expected.fraud_signals` của golden set
   với kết quả tính từ dữ liệu (double-entry: nhãn gán tay phải khớp máy).
2. Tầng service của sản phẩm (tuần 2-3) — tính `complaints.fraud_signals`
   từ dữ liệu thật, KHÔNG để agent tự điền.

Mọi hàm đều thuần (pure): nhận bảng dữ liệu trong bộ nhớ, không chạm DB.
"""

from __future__ import annotations

import unicodedata
from bisect import bisect_left, bisect_right
from datetime import datetime, timedelta
from fractions import Fraction


def _strip_diacritics(text: str) -> str:
    """'Tôi bị lừa đảo' -> 'toi bi lua dao' — so khớp từ khoá không phụ thuộc dấu."""
    text = text.lower().replace("đ", "d")
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def _p95(sorted_amounts: list[int]) -> int:
    """p95 xác định (nearest-rank) trên danh sách ĐÃ sắp xếp tăng dần."""
    n = len(sorted_amounts)
    if n == 0:
        return 0
    return sorted_amounts[min(n - 1, int(round(0.95 * (n - 1))))]


def _dt(value) -> datetime:
    return value if isinstance(value, datetime) else datetime.fromisoformat(value)


class LedgerIndex:
    """Chỉ mục trên các bảng JSONL để engine tra cứu O(log n)."""

    def __init__(self, users, wallets, bank_accounts, transactions, complaints,
                 auth_sessions, tickets):
        self.users = {u["user_id"]: u for u in users}
        self.wallets = {w["wallet_id"]: w for w in wallets}
        self.bank_accounts = {b["bank_account_id"]: b for b in bank_accounts}
        self.wallet_owner = {w["wallet_id"]: w["user_id"] for w in wallets}
        self.bank_owner = {b["bank_account_id"]: b["user_id"] for b in bank_accounts}
        self.tickets_by_complaint = {t["complaint_id"]: t for t in tickets}
        self.tx_by_id = {t["trans_id"]: t for t in transactions}

        self.out_by_user: dict[str, list] = {}
        self.in_by_wallet: dict[str, list] = {}
        self.out_by_wallet: dict[str, list] = {}
        for t in transactions:
            t["_created"] = _dt(t["created_at"])
            sender = self.owner_of_sender(t)
            if sender:
                self.out_by_user.setdefault(sender, []).append(t)
            if t["rec_wal_id"]:
                self.in_by_wallet.setdefault(t["rec_wal_id"], []).append(t)
            if t["send_wal_id"]:
                self.out_by_wallet.setdefault(t["send_wal_id"], []).append(t)
        for lst in self.out_by_user.values():
            lst.sort(key=lambda t: (t["_created"], t["trans_id"]))
        for lst in self.in_by_wallet.values():
            lst.sort(key=lambda t: (t["_created"], t["trans_id"]))
        for lst in self.out_by_wallet.values():
            lst.sort(key=lambda t: (t["_created"], t["trans_id"]))

        self.complaints_by_user: dict[str, list] = {}
        self.complaints_by_rec_wallet: dict[str, list] = {}
        for c in complaints:
            c["_created"] = _dt(c["created_at"])
            self.complaints_by_user.setdefault(c["user_id"], []).append(c)
            tx = self.tx_by_id.get(c["trans_id"]) if c.get("trans_id") else None
            if tx and tx["rec_wal_id"]:
                self.complaints_by_rec_wallet.setdefault(tx["rec_wal_id"], []).append(c)

        self.sessions_by_user: dict[str, list] = {}
        for s in auth_sessions:
            s["_created"] = _dt(s["created_at"])
            self.sessions_by_user.setdefault(s["user_id"], []).append(s)

    # --- helpers định danh 2 bên ---
    def owner_of_sender(self, tx) -> str | None:
        if tx["send_wal_id"]:
            return self.wallet_owner.get(tx["send_wal_id"])
        if tx["send_bank_account_id"]:
            return self.bank_owner.get(tx["send_bank_account_id"])
        return None

    def owner_of_receiver(self, tx) -> str | None:
        if tx["rec_wal_id"]:
            return self.wallet_owner.get(tx["rec_wal_id"])
        if tx["rec_bank_account_id"]:
            return self.bank_owner.get(tx["rec_bank_account_id"])
        return None

    def sender_ref(self, tx) -> str | None:
        return tx["send_wal_id"] or tx["send_bank_account_id"]

    def receiver_ref(self, tx) -> str | None:
        return tx["rec_wal_id"] or tx["rec_bank_account_id"]

    def owner_of_ref(self, ref: str) -> str | None:
        return self.wallet_owner.get(ref) or self.bank_owner.get(ref)

    def out_window(self, user_id: str, start: datetime, end: datetime) -> list:
        """Giao dịch gửi đi của user trong [start, end] (bao cả 2 đầu)."""
        txs = self.out_by_user.get(user_id, [])
        keys = [t["_created"] for t in txs]
        return txs[bisect_left(keys, start): bisect_right(keys, end)]

    def had_link_before(self, user_a: str, user_b: str, before: datetime,
                        within_days: int) -> bool:
        """Hai user có giao dịch với nhau trong within_days trước mốc `before`?"""
        start = before - timedelta(days=within_days)
        for uid, other in ((user_a, user_b), (user_b, user_a)):
            for t in self.out_window(uid, start, before - timedelta(seconds=1)):
                if self.owner_of_receiver(t) == other:
                    return True
        return False

    def receiver_first_time(self, sender_user: str, tx) -> bool:
        """Bên nhận của tx lần đầu xuất hiện với sender (trước thời điểm tx)?"""
        ref = self.receiver_ref(tx)
        for t in self.out_by_user.get(sender_user, []):
            if t["_created"] >= tx["_created"]:
                break
            if self.receiver_ref(t) == ref:
                return False
        return True


class FraudEngine:
    def __init__(self, config: dict, index: LedgerIndex):
        self.cfg = config
        self.idx = index
        self.tier_a = set(config["policy"]["tier_a"])
        self.tier_b = set(config["policy"]["tier_b"])
        kw = config["signals"]["FS-09"]["params"]["keyword_groups"]
        self._keywords = [_strip_diacritics(k) for group in kw.values() for k in group]
        # FS-13 (ADR-048) — hai TẬP RIÊNG, phải khớp CẢ HAI. Giữ tách bạch chứ
        # không gộp thành một danh sách: gộp là mất chính ràng buộc "đồng thời"
        # mà ADR dựng ra để chống bắt oan.
        p13 = config["signals"].get("FS-13", {}).get("params", {})
        self._fs13_nguon = [_strip_diacritics(k) for k in p13.get("nguon_chi_dan", [])]
        self._fs13_kenh = [_strip_diacritics(k) for k in p13.get("kenh_xa_la", [])]

    def _params(self, sid: str) -> dict:
        return self.cfg["signals"][sid]["params"]

    # ------------------------------------------------------------------
    def evaluate(self, *, user_id: str, tx: dict | None, complaint_at: datetime,
                 utterance_text: str, otp_disclosed: bool = False,
                 refund_dest_ref: str | None = None) -> list[str]:
        """Trả về danh sách mã tín hiệu đã bật, sắp xếp theo mã."""
        idx = self.idx
        fired: set[str] = set()
        complaint_at = _dt(complaint_at)

        # FS-10 & FS-09 không cần giao dịch
        if otp_disclosed:
            fired.add("FS-10")
        text = _strip_diacritics(utterance_text or "")
        if tx:
            text += " " + _strip_diacritics(tx.get("des") or "")
        if any(k in text for k in self._keywords):
            fired.add("FS-09")

        # FS-13 — ĐỒNG THỜI ① nguồn chỉ dẫn bên thứ ba VÀ ② kênh xa lạ.
        # `and` chứ không `or`: thiếu ② thì "chồng tôi bảo chuyển" và "shop
        # hướng dẫn chuyển khoản" đều bật, và cả hai đều KHÔNG phải lừa đảo.
        if (self._fs13_nguon and self._fs13_kenh
                and any(k in text for k in self._fs13_nguon)
                and any(k in text for k in self._fs13_kenh)):
            fired.add("FS-13")

        # FS-11 — lịch sử khiếu nại của chính khách
        p11 = self._params("FS-11")
        window_start = complaint_at - timedelta(days=p11["window_days"])
        prior = [c for c in idx.complaints_by_user.get(user_id, [])
                 if window_start <= c["_created"] < complaint_at]
        approved = sum(
            1 for c in prior
            if idx.tickets_by_complaint.get(c["complaint_id"], {}).get("hitl_status") == "approved"
        )
        n_out_90d = len(idx.out_window(user_id, window_start, complaint_at))
        if approved >= p11["min_approved_refunds"] or (
            len(prior) >= p11["ratio_min_complaints"]
            and len(prior) / max(1, n_out_90d) >= p11["complaint_tx_ratio"]
        ):
            fired.add("FS-11")

        if tx is None:
            return sorted(fired)

        tx_at = tx["_created"] if "_created" in tx else _dt(tx["created_at"])
        sender = idx.owner_of_sender(tx)
        receiver = idx.owner_of_receiver(tx)
        is_outbound = sender == user_id
        is_inbound = receiver == user_id

        # FS-01 — đích hoàn khác nguồn gốc, khác chủ
        if refund_dest_ref:
            origin = idx.sender_ref(tx)
            if refund_dest_ref != origin and idx.owner_of_ref(refund_dest_ref) != idx.owner_of_ref(origin):
                fired.add("FS-01")

        # FS-02 — nguồn lạ + đòi hoàn gấp (khiếu nại về giao dịch NHẬN VÀO)
        p02 = self._params("FS-02")
        if is_inbound and sender and sender != user_id:
            no_link = not idx.had_link_before(user_id, sender, tx_at, p02["window_prior_days"])
            fast = (complaint_at - tx_at) <= timedelta(hours=p02["complaint_within_hours"])
            if no_link and fast:
                fired.add("FS-02")

        if is_outbound:
            p03 = self._params("FS-03")
            ref = idx.receiver_ref(tx)
            chain = [t for t in idx.out_window(user_id, tx_at - timedelta(hours=p03["window_hours"]), tx_at)
                     if idx.receiver_ref(t) == ref]
            if len(chain) >= p03["min_chain"] and all(
                chain[i]["amount"] >= p03["growth_factor"] * chain[i - 1]["amount"]
                for i in range(1, len(chain))
            ):
                fired.add("FS-03")

            p04 = self._params("FS-04")
            hist = [t["amount"] for t in idx.out_window(
                user_id, tx_at - timedelta(days=p04["history_days"]), tx_at - timedelta(seconds=1))]
            p95 = _p95(sorted(hist))
            first_time = idx.receiver_first_time(user_id, tx)
            if p95 > 0 and tx["amount"] >= p04["p95_multiplier"] * p95 and first_time:
                fired.add("FS-04")

            p05 = self._params("FS-05")
            hour = tx_at.hour
            if first_time and tx["amount"] >= p05["min_amount"] and (
                hour >= p05["night_start_hour"] or hour < p05["night_end_hour"]
            ):
                fired.add("FS-05")

            # FS-06 — bất thường xác thực + rút gần sạch
            p06 = self._params("FS-06")
            anomaly = any(
                (s["failed_attempts"] >= p06["min_failed_attempts"] or s["locked_at"])
                and tx_at - timedelta(hours=p06["auth_window_hours"]) <= s["_created"] <= tx_at
                for s in idx.sessions_by_user.get(user_id, [])
            )
            if anomaly and tx["send_wal_id"]:
                balance_now = idx.wallets[tx["send_wal_id"]]["balance"]
                pre = balance_now + tx["amount"]
                if pre > 0:
                    # So sánh bằng số nguyên qua Fraction — tránh sai số float của
                    # `(1 - drain_ratio) * pre` (vd (1-0.9)*1_000_000 == 99999.99999999997
                    # trong Python, khiến case rút ĐÚNG 90% số dư bị trượt ngưỡng).
                    ratio = Fraction(p06["drain_ratio"]).limit_denominator(1000)
                    if balance_now * ratio.denominator <= (ratio.denominator - ratio.numerator) * pre:
                        fired.add("FS-06")

            # FS-08 — KYC thấp + tổng CHUYỂN ĐI 24h lớn
            p08 = self._params("FS-08")
            if idx.users[user_id]["kyc_level"] == p08["kyc_level"]:
                day_sum = sum(t["amount"] for t in idx.out_window(
                    user_id, tx_at - timedelta(hours=24), tx_at))
                if day_sum >= p08["daily_outbound_min"]:
                    fired.add("FS-08")

        # FS-07 — fan-in rồi rút ngay (xét trên ví BÊN NHẬN của giao dịch bị khiếu nại).
        # Với mỗi lệnh rút to_bank quanh giao dịch: cụm fan-in = các khoản NHẬN TỪ NGƯỜI KHÁC
        # trong 24h kết thúc ở lần nhận cuối; lần nhận cuối phải cách lệnh rút <= 60'.
        p07 = self._params("FS-07")
        mule_wallet = tx["rec_wal_id"]
        if mule_wallet:
            owner = idx.wallet_owner.get(mule_wallet)
            inbound = [t for t in idx.in_by_wallet.get(mule_wallet, [])
                       if idx.owner_of_sender(t) not in (None, owner)]  # bỏ tự nạp
            payouts = [t for t in idx.out_by_wallet.get(mule_wallet, [])
                       if t["scope"] == "to_bank"
                       and abs((t["_created"] - tx_at).total_seconds()) <= p07["fanin_window_hours"] * 3600]
            for o in payouts:
                before = [t for t in inbound if t["_created"] <= o["_created"]]
                if not before:
                    continue
                last_in = max(t["_created"] for t in before)
                if (o["_created"] - last_in) > timedelta(minutes=p07["payout_within_minutes"]):
                    continue
                cluster = [t for t in before
                           if t["_created"] >= last_in - timedelta(hours=p07["fanin_window_hours"])]
                senders = {idx.owner_of_sender(t) for t in cluster}
                total_in = sum(t["amount"] for t in cluster)
                if (len(senders) >= p07["fanin_min_senders"] and total_in > 0
                        and o["amount"] >= p07["payout_ratio"] * total_in):
                    fired.add("FS-07")
                    break

        # FS-12 — bên nhận đã bị gắn cờ
        p12 = self._params("FS-12")
        if mule_wallet:
            if idx.wallets[mule_wallet]["status"] == "frozen":
                fired.add("FS-12")
            else:
                complainers = {
                    c["user_id"] for c in idx.complaints_by_rec_wallet.get(mule_wallet, [])
                    if c["user_id"] != user_id
                    and complaint_at - timedelta(days=p12["window_days"]) <= c["_created"] < complaint_at
                }
                if len(complainers) >= p12["min_distinct_complainants"]:
                    fired.add("FS-12")

        return sorted(fired)

    # ------------------------------------------------------------------
    def decide(self, fired: list[str]) -> dict:
        """Chính sách 2 tầng §4.5.3 → có escalate không, priority nào."""
        a = sorted(set(fired) & self.tier_a)
        b = sorted(set(fired) & self.tier_b)
        escalate = bool(a) or len(b) >= self.cfg["policy"]["tier_b_min_to_escalate"]
        if a:
            priority = self.cfg["policy"]["priority_tier_a"]
        elif escalate:
            priority = self.cfg["policy"]["priority_tier_b"]
        else:
            priority = "normal"
        return {
            "escalate": escalate,
            "priority": priority,
            "tier_a_fired": a,
            "tier_b_fired": b,
            "escalation_target": self.cfg["policy"]["escalation_target"] if escalate else None,
        }
