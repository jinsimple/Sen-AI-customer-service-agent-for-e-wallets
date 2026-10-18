"""US-018 — operational report. PRD §12: "Figures match real ticket data, not
estimates" — every number here is computed directly from the DB at call time,
no cache, no sample values."""
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
    # Proposals in the resolutions table are ALWAYS created by CSKH (propose_resolution
    # is NOT one of the 5 tools the AI may call — contracts/agent-tools.yaml — hard
    # constraint 2: the AI never escalates itself / never proposes on its own). "% of AI
    # proposals approved" once misattributed this action to the AI; the label was fixed at the
    # display layer, the number is unchanged.
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

    # Distribution by complaint, tied to exactly the set of tickets in scope for the period (joined
    # via complaint_id).
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
        # "Average handling time" is CYCLE TIME (ticket created → supervisor approval),
        # INCLUDING time the ticket sat in the queue — not AHT (actual HUMAN handling time).
        # The DB has no "CSKH started working" timestamp (no claimed_at/
        # work_started_at on Ticket/Resolution — only the ticket's created_at
        # and the decision's approved_at), so AHT CANNOT be measured from current data
        # — return None + an explicit reason, NEVER infer it or leave it blank (blank is
        # read as 0; "not measurable yet" is not).
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
