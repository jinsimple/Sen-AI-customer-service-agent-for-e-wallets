"""Tool 2/5 — `get_customer_history` (PRD §6, Data Brief §6.3 hàng 2).

Test bắt buộc: gọi bằng `user_id` của khách A KHÔNG BAO GIỜ trả về dữ liệu
khách B — test phân quyền, không chỉ test chức năng (đây là chỗ một agent
bị dụ "cho tôi xem lịch sử của X" bằng số điện thoại đoán mò dễ rò rỉ nhất).
Mọi query trong hàm này lọc CHẶT theo đúng `user_id` truyền vào — không có
đường nào để tham số khác (vd `phone`) mở rộng sang user khác.
"""
from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models import Complaint, Transaction, User, Wallet
from src.observability.logging_config import get_logger
from src.tools.base import ToolError, record_tool_result

_logger = get_logger("fin05.tools.get_customer_history")


def get_customer_history(
    session: Session,
    *,
    user_id: str,
    days: int = 90,
    limit_transactions: int = 20,
    amount: int | None = None,
) -> dict[str, Any]:
    """`amount`: lọc gần đúng theo số tiền khách mô tả (sai số ±2%, đủ bù làm
    tròn "270k"/"270.000đ") — dùng khi khách chỉ mô tả mơ hồ (số tiền + thời
    gian gần đúng, không có mã giao dịch). KHÔNG có filter này, khách hàng
    hoạt động nhiều (dataset thật: trung vị ~232 giao dịch/user) sẽ dễ bị
    giao dịch cũ đẩy khỏi top `limit_transactions` dù vẫn còn trong `days`
    ngày — phát hiện thật qua eval/run_golden_set.py (agent không tự tìm ra
    giao dịch, phải hỏi lại dù đã có đủ mô tả).

    Có `amount` → kết quả kèm thêm `amount_match` (status found/multiple_matches/
    not_found, giống hệt pattern của lookup_transaction) — TÍN HIỆU CẤU TRÚC rõ
    ràng để agent rẽ nhánh, không phải để agent tự đọc danh sách rồi suy luận có
    mơ hồ hay không. Lý do đổi từ chỉ dựa vào hướng dẫn trong prompt: thực nghiệm
    qua eval/run_golden_set.py cho thấy hướng dẫn prompt đơn thuần ("nếu có nhiều
    khớp thì hỏi lại") KHÔNG được tuân theo ổn định ở quy mô lớn (chuẩn ngành —
    xem OpenAI agent safety guide: "design workflows so ambiguous data never
    directly drives agent behavior", nên đẩy phát hiện mơ hồ xuống tầng tool,
    không chỉ dựa vào lời văn)."""
    # Hàm này KHÔNG nhận correlation_id — log vẫn tự gắn được đúng correlation_id
    # + user_id của request đang xử lý qua contextvars (src/observability/
    # context.py), chứng minh cơ chế "gắn 1 lần ở entry point, hàm con tự thừa
    # hưởng" hoạt động đúng ngay cả ở tầng sâu nhất (tool), không cần sửa chữ
    # ký hàm để truyền tay.
    _logger.info("get_customer_history_called", extra={"days": days, "has_amount": amount is not None})

    user = session.get(User, user_id)
    if user is None:
        raise ToolError(f"user_id không tồn tại: {user_id}")

    wallets = list(session.scalars(select(Wallet).where(Wallet.user_id == user_id)))
    wallet_ids = [w.wallet_id for w in wallets]

    since = dt.datetime.utcnow() - dt.timedelta(days=days)
    txn_stmt = select(Transaction).where(
        Transaction.created_at >= since,
        (Transaction.send_wal_id.in_(wallet_ids)) | (Transaction.rec_wal_id.in_(wallet_ids)),
    )
    amount_match: dict[str, Any] | None = None
    if amount is not None:
        tolerance = max(round(amount * 0.02), 1)
        amount_stmt = txn_stmt.where(Transaction.amount.between(amount - tolerance, amount + tolerance))
        # KHÔNG áp limit_transactions ở đây — amount đã tự thu hẹp kết quả rồi,
        # giới hạn thêm sẽ làm mất đúng những ứng viên cần liệt kê đủ để agent
        # hỏi lại (giống lookup_transaction không giới hạn số candidates trả về).
        amount_matches = list(session.scalars(amount_stmt.order_by(Transaction.created_at.desc()))) if wallet_ids else []
        if len(amount_matches) == 0:
            amount_match = {"status": "not_found"}
        elif len(amount_matches) == 1:
            # scope PHẢI có ở đây (không chỉ trans_id) — thiếu trường này khiến
            # agent phải tự đoán scope khi tạo ticket qua nhánh amount_match=found
            # (khác nhánh multiple_matches bên dưới vốn đã có sẵn scope cho từng
            # candidate). Phát hiện thật qua functional_qa_set.jsonl: các case
            # money_not_received/double_charge tra ra giao dịch qua amount_match
            # (không qua lookup_transaction) đều bị lệch scope vì thiếu dữ liệu
            # này, không phải lỗi suy luận của agent.
            match = amount_matches[0]
            amount_match = {
                "status": "found",
                "trans_id": match.trans_id,
                "scope": match.scope,
                "amount": match.amount,
                "created_at": match.created_at.isoformat() if match.created_at else None,
                "direction": "out" if match.send_wal_id in wallet_ids else "in",
            }
        else:
            amount_match = {
                "status": "multiple_matches",
                "candidates": [
                    {
                        "trans_id": t.trans_id,
                        "amount": t.amount,
                        "created_at": t.created_at.isoformat() if t.created_at else None,
                        "scope": t.scope,
                        "direction": "out" if t.send_wal_id in wallet_ids else "in",
                    }
                    for t in amount_matches
                ],
            }
        txn_stmt = amount_stmt
    txn_stmt = txn_stmt.order_by(Transaction.created_at.desc()).limit(limit_transactions)
    transactions = list(session.scalars(txn_stmt)) if wallet_ids else []

    complaints = list(
        session.scalars(
            select(Complaint).where(Complaint.user_id == user_id).order_by(Complaint.created_at.desc())
        )
    )

    result = {
        "user_id": user_id,
        "kyc_level": user.kyc_level,
        "wallets": [{"wallet_id": w.wallet_id, "balance": w.balance, "status": w.status} for w in wallets],
        **({"amount_match": amount_match} if amount_match is not None else {}),
        "recent_transactions": [
            {
                "trans_id": t.trans_id,
                "amount": t.amount,
                "status": t.status,
                "scope": t.scope,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "direction": "out" if t.send_wal_id in wallet_ids else "in",
            }
            for t in transactions
        ],
        "complaint_count_90d": len(
            [c for c in complaints if c.created_at and c.created_at >= since]
        ),
        "complaints": [
            {
                "complaint_id": c.complaint_id,
                "type": c.type,
                "status": c.status,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in complaints
        ],
    }

    tool_result_id = record_tool_result(session, "get_customer_history", result)
    return {**result, "tool_result_id": tool_result_id}
