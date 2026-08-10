"""US-018 — báo cáo vận hành. PRD §12: "Số liệu khớp dữ liệu ticket thật,
không phải ước lượng" — mọi số ở đây tính trực tiếp từ DB tại thời điểm gọi,
không cache, không giá trị mẫu."""
from __future__ import annotations

import datetime as dt
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models import Complaint, Escalation, Resolution, Ticket


def build_summary(
    session: Session,
    *,
    date_from: Optional[dt.datetime] = None,
    date_to: Optional[dt.datetime] = None,
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
        "avg_processing_hours": avg_processing_hours,
        "pct_ai_proposal_approved": pct_ai_proposal_approved,
        "pct_escalated": pct_escalated,
        "by_complaint_type": by_type,
        "by_scope": by_scope,
    }
