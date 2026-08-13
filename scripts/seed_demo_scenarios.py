#!/usr/bin/env python3
"""Dữ liệu mẫu để bấm thử tay trên UI — KHÔNG phải một phần của
`data/generated/` (pipeline tái lập byte-for-byte, Data Brief §3.3). Script
này ghi thẳng vào DB runtime (`data/app.db`) qua đúng các tool/service thật
(create_ticket_with_fraud_check, propose_resolution, escalate_ticket) — dữ
liệu sinh ra có tool_result_id/investigation_logs thật, không phải mock.

Chạy sau `make db`:
    python scripts/seed_demo_scenarios.py

`make db` (db-reset) sẽ xoá sạch phần này lần chạy tiếp theo — chạy lại
script này mỗi khi cần dữ liệu mẫu để test tay.

Phủ các case:
- Đủ 4 loại khiếu nại × 3 phạm vi giao dịch (12 ticket "pending" cho Dashboard)
- 1 ticket đề xuất pending_approval, phạm vi nội bộ ví (Approve — duyệt trực tiếp)
- 1 ticket đề xuất pending_approval, phạm vi chạm ngân hàng (Approve — tra soát)
- 1 ticket đã duyệt + 1 đã từ chối (Approve — nhật ký HITL)
- 1 ticket escalate tới ngân hàng đối tác (Dashboard — filter "Chờ đối tác NH")
- 1 ticket need_more_info (Dashboard/Ticket detail — trạng thái "cần điều tra thêm")
- 1 ticket not_found (trans_id=None — US-008)
- 1 ticket tín hiệu FS-06 bật, escalate khẩn cấp (Dashboard — filter "Khẩn cấp")
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from scripts.gen_dataset import _PASSWORD_HASHER, SHARED_TEST_PASSWORD
from src.db.models import (
    AuthSession,
    BankAccount,
    InvestigationLog,
    Resolution,
    Ticket,
    Transaction,
    User,
    Wallet,
)
from src.db.session import get_engine
from src.services.complaint_intake import create_ticket_with_fraud_check
from src.tools.base import new_id
from src.tools.escalate_ticket import escalate_ticket
from src.tools.propose_resolution import propose_resolution

COMPLAINT_TYPES = ["wrong_recipient", "money_not_received", "double_charge", "refund"]
SCOPES = ["internal_wallet", "from_bank", "to_bank"]
DESCRIPTIONS = {
    "wrong_recipient": "em chuyen nham sang sdt sai, gio muon lay lai",
    "money_not_received": "da tru tien nhung ben kia chua thay bao ve",
    "double_charge": "bi tru tien 2 lan cho cung 1 giao dich",
    "refund": "da duoc duyet hoan nhung chua thay tien ve vi",
}


def pick_transactions_by_scope(session: Session, scope: str, n: int) -> list[Transaction]:
    stmt = (
        select(Transaction)
        .where(Transaction.scope == scope, Transaction.status == "success")
        .order_by(Transaction.created_at.desc())
        .limit(n)
    )
    return list(session.scalars(stmt))


def owner_user_id(session: Session, tx: Transaction) -> str | None:
    wallet_id = tx.send_wal_id or tx.rec_wal_id
    if not wallet_id:
        return None
    wallet = session.get(Wallet, wallet_id)
    return wallet.user_id if wallet else None


def main() -> None:
    engine = get_engine()
    factory = sessionmaker(bind=engine, future=True)
    session = factory()

    supervisor = session.scalar(select(User).where(User.role == "supervisor"))
    if supervisor is None:
        raise SystemExit("Không tìm thấy user role=supervisor trong DB — chạy `make db` trước.")

    # partner_admin (đối tác ví điện tử — upload chính sách/FAQ, src/rag/):
    # không thuộc pipeline gen_dataset.py tái lập được (Data Brief §5.3, chỉ
    # sinh customer/cskh/supervisor), nên seed thủ công 1 user demo ở đây,
    # idempotent theo SĐT để chạy lại script nhiều lần không lỗi trùng khoá.
    #
    # password_hash — CÙNG mật khẩu test dùng chung với 3 user demo còn lại
    # (scripts/gen_dataset.py::SHARED_TEST_PASSWORD), để 4 role test tay đều
    # dùng 1 mật khẩu duy nhất, dễ nhớ.
    demo_pa_phone = "0900000001"
    demo_pa = session.scalar(select(User).where(User.phone == demo_pa_phone))
    if demo_pa is None:
        session.add(
            User(
                user_id="USR-PA01",
                role="partner_admin",
                full_name="Đối tác ví — Quản trị chính sách",
                phone=demo_pa_phone,
                kyc_level=0,
                password_hash=_PASSWORD_HASHER.hash(SHARED_TEST_PASSWORD),
                created_at=dt.datetime.utcnow(),
            )
        )
        session.commit()
        print(f"Đã tạo user demo partner_admin: USR-PA01 / {demo_pa_phone}")
    elif demo_pa.password_hash is None:
        # Backfill — user demo đã tồn tại TỪ TRƯỚC đợt thêm mật khẩu (2026-08-12).
        demo_pa.password_hash = _PASSWORD_HASHER.hash(SHARED_TEST_PASSWORD)
        session.commit()
        print(f"Đã backfill password_hash cho user demo partner_admin đã có sẵn: {demo_pa_phone}")

    created_tickets: list[str] = []

    # --- 12 ô ma trận: 4 loại khiếu nại × 3 phạm vi (Dashboard) ---------------
    pool = {scope: pick_transactions_by_scope(session, scope, 4) for scope in SCOPES}
    for scope in SCOPES:
        txs = pool[scope]
        for i, ctype in enumerate(COMPLAINT_TYPES):
            tx = txs[i % len(txs)]
            uid = owner_user_id(session, tx)
            if uid is None:
                continue
            result = create_ticket_with_fraud_check(
                session,
                user_id=uid,
                complaint_type=ctype,
                scope=scope,
                description_raw=DESCRIPTIONS[ctype],
                trans_id=tx.trans_id,
            )
            created_tickets.append(result["ticket_id"])
    session.commit()
    print(f"Đã tạo {len(created_tickets)} ticket phủ 4 loại × 3 phạm vi.")

    # --- Ticket đề xuất chờ duyệt — nội bộ ví (Approve: duyệt trực tiếp) -----
    tx = pool["internal_wallet"][0]
    uid = owner_user_id(session, tx)
    r1 = create_ticket_with_fraud_check(
        session, user_id=uid, complaint_type="wrong_recipient", scope="internal_wallet",
        description_raw="chuyen nham 500k, muon hoan lai", trans_id=tx.trans_id,
    )
    p1 = propose_resolution(
        session, ticket_id=r1["ticket_id"], action_type="refund_to_wallet",
        rationale="Khách chuyển nhầm, đã xác minh người nhận đồng ý hoàn — đủ căn cứ hoàn trực tiếp.",
        amount=tx.amount, cited_tool_result_ids=[r1["tool_result_id"]],
    )
    session.commit()
    print(f"Đề xuất chờ duyệt (nội bộ ví): ticket={r1['ticket_id']} resolution={p1['resolution_id']}")

    # --- Ticket đề xuất chờ duyệt — chạm ngân hàng (Approve: tra soát) -------
    tx = pool["to_bank"][1]
    uid = owner_user_id(session, tx)
    r2 = create_ticket_with_fraud_check(
        session, user_id=uid, complaint_type="money_not_received", scope="to_bank",
        description_raw="rut tien ve ngan hang nhung chua thay bao co", trans_id=tx.trans_id,
    )
    p2 = propose_resolution(
        session, ticket_id=r2["ticket_id"], action_type="refund_to_bank",
        rationale="Giao dịch delay đối soát với ngân hàng nhận — đề xuất gửi yêu cầu tra soát.",
        amount=tx.amount, cited_tool_result_ids=[r2["tool_result_id"]],
    )
    session.commit()
    print(f"Đề xuất chờ duyệt (chạm ngân hàng): ticket={r2['ticket_id']} resolution={p2['resolution_id']}")

    # --- 1 ticket đã duyệt + 1 đã từ chối (Approve: nhật ký HITL) -----------
    tx = pool["internal_wallet"][1]
    uid = owner_user_id(session, tx)
    r3 = create_ticket_with_fraud_check(
        session, user_id=uid, complaint_type="double_charge", scope="internal_wallet",
        description_raw="bi tru tien 2 lan", trans_id=tx.trans_id,
    )
    p3 = propose_resolution(
        session, ticket_id=r3["ticket_id"], action_type="ledger_adjustment",
        rationale="Đối chiếu 2 giao dịch cùng idempotency_key — điều chỉnh sổ cái nội bộ.",
        amount=tx.amount, cited_tool_result_ids=[r3["tool_result_id"]],
    )
    res3 = session.get(Resolution, p3["resolution_id"])
    res3.status = "approved"
    res3.approved_by = supervisor.user_id
    res3.approved_at = dt.datetime.utcnow()
    session.commit()
    print(f"Đã duyệt sẵn (audit log): ticket={r3['ticket_id']} resolution={p3['resolution_id']}")

    tx = pool["internal_wallet"][2]
    uid = owner_user_id(session, tx)
    r4 = create_ticket_with_fraud_check(
        session, user_id=uid, complaint_type="refund", scope="internal_wallet",
        description_raw="da duoc duyet hoan nhung chua thay tien", trans_id=tx.trans_id,
    )
    p4 = propose_resolution(
        session, ticket_id=r4["ticket_id"], action_type="refund_to_wallet",
        rationale="Không đủ bằng chứng đối tác đã hoàn — cần xác minh lại trước khi duyệt.",
        amount=tx.amount, cited_tool_result_ids=[r4["tool_result_id"]],
    )
    res4 = session.get(Resolution, p4["resolution_id"])
    res4.status = "rejected"
    session.commit()
    print(f"Đã từ chối sẵn (audit log): ticket={r4['ticket_id']} resolution={p4['resolution_id']}")

    # --- Escalate tới ngân hàng đối tác (Dashboard: "Chờ đối tác NH") -------
    tx = pool["from_bank"][2]
    uid = owner_user_id(session, tx)
    r5 = create_ticket_with_fraud_check(
        session, user_id=uid, complaint_type="money_not_received", scope="from_bank",
        description_raw="nap tien tu ngan hang nhung chua vao vi", trans_id=tx.trans_id,
    )
    escalate_ticket(
        session, ticket_id=r5["ticket_id"], target="partner_bank",
        reason="Giao dịch từ ngân hàng chưa có xác nhận partner_ack sau 4 ngày làm việc.",
        created_by=supervisor.user_id,
    )
    session.commit()
    print(f"Escalate ngân hàng đối tác: ticket={r5['ticket_id']}")

    # --- need_more_info (US-012) ---------------------------------------------
    tx = pool["to_bank"][2]
    uid = owner_user_id(session, tx)
    r6 = create_ticket_with_fraud_check(
        session, user_id=uid, complaint_type="wrong_recipient", scope="to_bank",
        description_raw="chuyen nham so tai khoan ngan hang", trans_id=tx.trans_id,
    )
    ticket6 = session.get(Ticket, r6["ticket_id"])
    ticket6.hitl_status = "need_more_info"
    ticket6.updated_at = dt.datetime.utcnow()
    session.add(InvestigationLog(
        log_id=new_id("LOG"), ticket_id=r6["ticket_id"], step_no=1,
        tool_called="cskh_request_more_info", tool_input_json={"requested_by": "seed_demo"},
        agent_note="Cần khách cung cấp thêm biên lai giao dịch để xác minh số tài khoản đích.",
        created_at=dt.datetime.utcnow(),
    ))
    session.commit()
    print(f"Cần điều tra thêm: ticket={r6['ticket_id']}")

    # --- not_found (US-008) --------------------------------------------------
    any_customer = session.scalar(select(User).where(User.role == "customer"))
    r7 = create_ticket_with_fraud_check(
        session, user_id=any_customer.user_id, complaint_type="money_not_received",
        scope="internal_wallet", description_raw="chuyen 200k hom qua ma khong nho ma GD", trans_id=None,
    )
    session.commit()
    print(f"Not found (cần tra thủ công): ticket={r7['ticket_id']}")

    # --- FS-06: OTP sai nhiều lần + rút gần hết số dư (Dashboard: "Khẩn cấp") -
    fs06_wallet = session.scalar(
        select(Wallet).where(Wallet.status == "active", Wallet.balance > 0).order_by(Wallet.balance.asc())
    )
    fs06_user = session.get(User, fs06_wallet.user_id)
    fs06_bank = session.scalar(select(BankAccount).where(BankAccount.user_id != fs06_wallet.user_id))
    now = dt.datetime.utcnow()
    session.add(AuthSession(
        session_id=new_id("SES"), user_id=fs06_user.user_id, otp_status="failed",
        failed_attempts=4, created_at=now - dt.timedelta(hours=1),
    ))
    session.flush()
    drain_amount = fs06_wallet.balance * 9 + 10_000  # đảm bảo rút ≥90% số dư hiện có
    fs06_tx = Transaction(
        trans_id=f"TXN-DEMO-FS06-{fs06_wallet.wallet_id[-6:]}",
        rec_code=f"RC-DEMO-{fs06_wallet.wallet_id[-6:]}",
        send_wal_id=fs06_wallet.wallet_id,
        rec_bank_account_id=fs06_bank.bank_account_id,
        amount=drain_amount, fee=0, status="success", scope="to_bank", channel="withdrawal",
        idempotency_key=f"IDK-DEMO-{fs06_wallet.wallet_id[-6:]}", created_at=now, completed_at=now,
        des="rut tien gap",
    )
    session.add(fs06_tx)
    session.commit()
    r8 = create_ticket_with_fraud_check(
        session, user_id=fs06_user.user_id, complaint_type="money_not_received", scope="to_bank",
        description_raw="tai khoan bi rut sach tien, em khong lam giao dich nay", trans_id=fs06_tx.trans_id,
    )
    session.commit()
    print(f"FS-06 khẩn cấp: ticket={r8['ticket_id']} should_escalate={r8['should_escalate']}")

    print("\nXong — vào /dashboard hoặc /approve để xem.")


if __name__ == "__main__":
    main()
