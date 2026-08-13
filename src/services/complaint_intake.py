"""Nối `scripts/fraud_engine.py` (script thuần, không chạm DB) vào tool
`create_ticket` (§4.1 FIN05-Backend-Handoff.md).

Data Brief §4.2: `complaints.fraud_signals` "do tầng service tính từ dữ
liệu, không phải do agent tự điền" — đây là tầng service đó. Tool
`create_ticket` giữ mỏng, không tự tính tín hiệu; nơi DUY NHẤT chuyển dữ
liệu từ DB (SQLAlchemy rows) sang định dạng `LedgerIndex` (list[dict] như
JSONL) mà `fraud_engine.py` cần là ở đây.

Dùng `FraudEngine.evaluate()` để tính TOÀN BỘ tín hiệu (tái dùng nguyên
engine đã qua 16 nhóm kiểm định dataset, không viết lại — mã khác ngoài
FS-06 vẫn được lưu vào `complaints.fraud_signals`, dữ liệu thừa không sao).
Quyết định escalate/priority sau đó do `src.tools.fraud_policy.evaluate_escalation()`
quyết — phạm vi MVP chỉ `FS-06` (PRD §5). KHÔNG dùng `FraudEngine.decide()`
— đó là chính sách 2 tầng cũ của dataset gốc, chỉ còn dùng nội bộ ở
`scripts/validate_dataset.py` để tự kiểm định dataset, không áp cho sản phẩm.
"""
from __future__ import annotations

import datetime as dt
from functools import lru_cache
from typing import Any

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from scripts.fraud_engine import FraudEngine, LedgerIndex
from src.config import DATA_SCHEMA_DIR
from src.db.models import AuthSession, BankAccount, Complaint, Ticket, Transaction, User, Wallet
from src.tools.create_ticket import create_ticket as _create_ticket


@lru_cache(maxsize=1)
def _load_fraud_config() -> dict:
    path = DATA_SCHEMA_DIR / "fraud_signals.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _rows_as_dicts(session: Session, model: Any) -> list[dict]:
    cols = model.__table__.columns.keys()
    return [{c: getattr(row, c) for c in cols} for row in session.scalars(select(model))]


def _build_engine(session: Session) -> FraudEngine:
    """Nạp toàn bộ dữ liệu nền hiện có trong DB thành LedgerIndex. Quy mô demo
    (60k transactions, vài trăm dòng các bảng khác) nên nạp lại mỗi lần gọi
    là đủ nhanh — không cần cache, tránh rủi ro đọc dữ liệu cũ sau khi có
    ticket/complaint mới."""
    idx = LedgerIndex(
        _rows_as_dicts(session, User),
        _rows_as_dicts(session, Wallet),
        _rows_as_dicts(session, BankAccount),
        _rows_as_dicts(session, Transaction),
        _rows_as_dicts(session, Complaint),
        _rows_as_dicts(session, AuthSession),
        _rows_as_dicts(session, Ticket),
    )
    return FraudEngine(_load_fraud_config(), idx)


def create_ticket_with_fraud_check(
    session: Session,
    *,
    user_id: str,
    complaint_type: str,
    scope: str,
    description_raw: str,
    trans_id: str | None = None,
    otp_disclosed: bool = False,
    now: dt.datetime | None = None,
) -> dict[str, Any]:
    """Tính tín hiệu gian lận từ dữ liệu DB rồi tạo ticket — thay vì để agent
    tự truyền `fraud_signals` tay (rủi ro agent quên/bịa tín hiệu). Đây là
    entrypoint agent/API nên gọi thay cho `create_ticket` trực tiếp khi
    `trans_id` có giá trị; case not_found (`trans_id=None`) vẫn tính được
    FS-09/FS-10/FS-11 (không cần giao dịch) rồi mới tạo ticket.
    """
    now = now or dt.datetime.utcnow()

    engine = _build_engine(session)
    # QUAN TRỌNG: lấy tx từ engine.idx.tx_by_id (không tự query Transaction
    # riêng) — LedgerIndex gắn khoá "_created" ngay trên object trong lúc
    # dựng chỉ mục; evaluate()/receiver_first_time() đọc "_created" từ chính
    # object đó, dựng dict tách rời sẽ thiếu khoá này và vỡ KeyError.
    tx_dict = engine.idx.tx_by_id.get(trans_id) if trans_id is not None else None

    fired = engine.evaluate(
        user_id=user_id,
        tx=tx_dict,
        complaint_at=now,
        utterance_text=description_raw,
        otp_disclosed=otp_disclosed,
        refund_dest_ref=None,  # chưa xác định ở bước tạo ticket, chỉ có tại propose_resolution
    )

    return _create_ticket(
        session,
        user_id=user_id,
        complaint_type=complaint_type,
        scope=scope,
        description_raw=description_raw,
        trans_id=trans_id,
        otp_disclosed=otp_disclosed,
        fraud_signals=fired,
        now=now,
    )


def flag_human_handoff(
    session: Session,
    *,
    user_id: str,
    reason: str,
    ticket_id: str | None = None,
    now: dt.datetime | None = None,
) -> dict[str, Any]:
    """CTRL-001 (FIN05_QA_TestCases.jsonl, 2026-08-11) — khách chủ động yêu
    cầu gặp người thật (ISO/IEC 25059 'user controllability'). Kiến trúc
    CSKH vẫn bất đồng bộ (dashboard, không phải live chat) — hàm này tạo/
    đánh dấu 1 Ticket THẬT với `human_handoff_requested=True` để CSKH thấy
    và ưu tiên xử lý, KHÔNG giả vờ có người đang chat trực tiếp ngay lúc này.

    `ticket_id`: nếu agent ĐÃ tạo ticket cho đúng vấn đề đang nói trong hội
    thoại này (tránh tạo trùng, cùng nguyên tắc đã áp dụng cho create_ticket)
    — chỉ set cờ lên ticket đó, PHẢI thuộc đúng `user_id` (chặn agent bị dụ
    flag nhầm ticket của người khác qua tham số này).
    Không có `ticket_id` — tạo ticket MỚI, complaint_type='other' (khách yêu
    cầu người thật không nhất thiết mô tả 1 trong 4 loại khiếu nại cụ thể).
    """
    now = now or dt.datetime.utcnow()

    if ticket_id is not None:
        ticket = session.get(Ticket, ticket_id)
        if ticket is None:
            raise ValueError(f"ticket_id không tồn tại: {ticket_id}")
        complaint = session.get(Complaint, ticket.complaint_id)
        if complaint is None or complaint.user_id != user_id:
            raise ValueError(f"ticket_id không thuộc user_id đang chat: {ticket_id}")
        ticket.human_handoff_requested = True
        ticket.updated_at = now
        session.flush()
        return {"ticket_id": ticket.ticket_id, "human_handoff_requested": True, "created_new_ticket": False}

    created = create_ticket_with_fraud_check(
        session,
        user_id=user_id,
        complaint_type="other",
        scope="internal_wallet",
        description_raw=reason,
        trans_id=None,
        now=now,
    )
    ticket = session.get(Ticket, created["ticket_id"])
    ticket.human_handoff_requested = True
    session.flush()
    return {**created, "human_handoff_requested": True, "created_new_ticket": True}
