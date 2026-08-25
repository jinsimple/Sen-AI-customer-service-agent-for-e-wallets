"""US-018 — báo cáo vận hành. PRD §12: "Số liệu khớp dữ liệu ticket thật,
không phải ước lượng" — mọi số ở đây tính trực tiếp từ DB tại thời điểm gọi,
không cache, không giá trị mẫu."""
from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models import Complaint, Escalation, Resolution, Ticket


def build_summary(
    session: Session,
    *,
    date_from: dt.datetime | None = None,
    date_to: dt.datetime | None = None,
) -> dict[str, Any]:
    stmt = select(Ticket)
    if date_from is not None:
        stmt = stmt.where(Ticket.created_at >= date_from)
    if date_to is not None:
        stmt = stmt.where(Ticket.created_at <= date_to)
    tickets = session.scalars(stmt).all()
    ticket_ids = {t.ticket_id for t in tickets}
    total_tickets = len(tickets)

    tickets_by_id = {t.ticket_id: t for t in tickets}

    resolutions = (
        session.scalars(select(Resolution).where(Resolution.ticket_id.in_(ticket_ids))).all()
        if ticket_ids
        else []
    )
    # Đề xuất trong bảng resolutions LUÔN do CSKH tạo (propose_resolution KHÔNG
    # nằm trong 5 tool AI được gọi — contracts/agent-tools.yaml — ràng buộc
    # cứng 2, AI không vượt cấp/không tự đề xuất). "% đề xuất AI được duyệt"
    # từng gán nhầm hành động này cho AI; đổi nhãn ở tầng hiển thị, số không đổi.
    decided = [r for r in resolutions if r.status in ("approved", "rejected")]
    approved = [r for r in decided if r.status == "approved"]
    pct_ai_proposal_approved = round(100 * len(approved) / len(decided), 1) if decided else None

    durations_hours = [
        (r.approved_at - tickets_by_id[r.ticket_id].created_at).total_seconds() / 3600
        for r in approved
        if r.approved_at is not None and r.ticket_id in tickets_by_id
    ]
    avg_processing_hours = round(sum(durations_hours) / len(durations_hours), 1) if durations_hours else None

    escalated_ticket_ids = (
        {
            e.ticket_id
            for e in session.scalars(select(Escalation).where(Escalation.ticket_id.in_(ticket_ids))).all()
        }
        if ticket_ids
        else set()
    )
    pct_escalated = round(100 * len(escalated_ticket_ids) / total_tickets, 1) if total_tickets else None

    # Phân bố theo complaint gắn với đúng tập ticket đang xét trong kỳ (join qua complaint_id).
    complaint_ids = {t.complaint_id for t in tickets}
    complaints = (
        session.scalars(select(Complaint).where(Complaint.complaint_id.in_(complaint_ids))).all()
        if complaint_ids
        else []
    )
    by_type: dict[str, int] = {}
    by_scope: dict[str, int] = {}
    for c in complaints:
        by_type[c.type] = by_type.get(c.type, 0) + 1
        by_scope[c.scope] = by_scope.get(c.scope, 0) + 1

    return {
        "date_from": date_from.isoformat() if date_from else None,
        "date_to": date_to.isoformat() if date_to else None,
        "total_tickets": total_tickets,
        # "Thời gian xử lý TB" là CYCLE TIME (tạo vé → sếp duyệt), GỒM CẢ thời
        # gian vé nằm chờ trong hàng đợi — không phải AHT (thời gian NGƯỜI thao
        # tác thật). DB không có mốc "CSKH bắt đầu làm" (không claimed_at/
        # work_started_at nào trên Ticket/Resolution — chỉ có created_at của vé
        # và approved_at của quyết định), nên AHT KHÔNG đo được từ dữ liệu hiện
        # có — trả None + lý do tường minh, KHÔNG suy diễn hay để trống (trống
        # bị đọc thành 0, "chưa đo được" thì không).
        "avg_processing_hours": avg_processing_hours,
        "avg_processing_hours_n": len(durations_hours),
        "aht_hours": None,
        "aht_khong_do_duoc_ly_do": (
            "Chưa đo được — cần mốc thời điểm CSKH BẮT ĐẦU thao tác (vd "
            "claimed_at/work_started_at), hiện DB chỉ có created_at (lúc tạo "
            "vé, gồm cả thời gian nằm chờ) và approved_at (lúc sếp duyệt)."
        ),
        "pct_ai_proposal_approved": pct_ai_proposal_approved,
        "pct_ai_proposal_approved_numerator": len(approved),
        "pct_ai_proposal_approved_n": len(decided),
        "pct_escalated": pct_escalated,
        "pct_escalated_numerator": len(escalated_ticket_ids),
        "pct_escalated_n": total_tickets,
        "by_complaint_type": by_type,
        "by_scope": by_scope,
    }
