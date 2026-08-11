"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { listTickets } from "@/lib/api";
import { COMPLAINT_TYPE_LABEL, HITL_STATUS_LABEL, SCOPE_LABEL, type TicketSummary } from "@/lib/types";
import { formatDateTime, formatSlaRemaining } from "@/lib/format";

type FilterKey = "all" | "pending" | "partner" | "critical" | "handoff";

export default function DashboardPage() {
  const router = useRouter();
  const [tickets, setTickets] = useState<TicketSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<FilterKey>("all");
  const [search, setSearch] = useState("");

  useEffect(() => {
    listTickets({ limit: 100 })
      .then(setTickets)
      .catch((e) => setError(e.message ?? "Không tải được hàng chờ"));
  }, []);

  const counts = useMemo(() => {
    if (!tickets) return { all: 0, pending: 0, partner: 0, critical: 0, handoff: 0 };
    return {
      all: tickets.length,
      pending: tickets.filter((t) => t.hitl_status === "pending").length,
      partner: tickets.filter((t) => t.partner_wait_status === "waiting" || t.partner_wait_status === "overdue")
        .length,
      critical: tickets.filter((t) => t.priority === "critical").length,
      handoff: tickets.filter((t) => t.human_handoff_requested).length,
    };
  }, [tickets]);

  const filtered = useMemo(() => {
    if (!tickets) return [];
    let list = tickets;
    if (filter === "pending") list = list.filter((t) => t.hitl_status === "pending");
    if (filter === "partner")
      list = list.filter((t) => t.partner_wait_status === "waiting" || t.partner_wait_status === "overdue");
    if (filter === "critical") list = list.filter((t) => t.priority === "critical");
    if (filter === "handoff") list = list.filter((t) => t.human_handoff_requested);
    if (search.trim()) {
      const q = search.trim().toLowerCase();
      list = list.filter(
        (t) =>
          t.ticket_id.toLowerCase().includes(q) ||
          t.complaint_id.toLowerCase().includes(q) ||
          (t.customer_name ?? "").toLowerCase().includes(q)
      );
    }
    return list;
  }, [tickets, filter, search]);

  return (
    <>
      <div className="page-head">
        <span className="eyebrow">Webapp CSKH · US-011, US-014</span>
        <h1>Hàng chờ ticket</h1>
        <p className="sub">
          Lọc/sắp xếp theo trạng thái và ưu tiên để xử lý đúng case cấp bách trước. Case nghi gian lận
          (tín hiệu FS-06) nổi bật rõ hơn ticket thường.
        </p>
      </div>

      <div className="filter-bar">
        <span className={`filter-chip${filter === "all" ? " active" : ""}`} onClick={() => setFilter("all")}>
          Tất cả ({counts.all})
        </span>
        <span
          className={`filter-chip${filter === "pending" ? " active" : ""}`}
          onClick={() => setFilter("pending")}
        >
          Chờ tiếp nhận ({counts.pending})
        </span>
        <span
          className={`filter-chip${filter === "partner" ? " active" : ""}`}
          onClick={() => setFilter("partner")}
        >
          Chờ đối tác NH ({counts.partner})
        </span>
        <span
          className={`filter-chip${filter === "critical" ? " active" : ""}`}
          style={filter !== "critical" ? { borderColor: "var(--danger)", color: "var(--danger)" } : undefined}
          onClick={() => setFilter("critical")}
        >
          <span className="dot dot-pulse" style={{ background: "var(--danger)" }} />
          Khẩn cấp — nghi gian lận ({counts.critical})
        </span>
        <span
          className={`filter-chip${filter === "handoff" ? " active" : ""}`}
          onClick={() => setFilter("handoff")}
        >
          Khách yêu cầu người thật ({counts.handoff})
        </span>
        <div className="search-box">
          <svg className="icon icon-sm" viewBox="0 0 24 24">
            <circle cx="11" cy="11" r="7" />
            <path d="M21 21l-4-4" />
          </svg>
          <input
            placeholder="Tìm theo mã ticket, mã khiếu nại, tên khách..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {error && <div className="note" style={{ borderColor: "var(--danger)" }}>{error}</div>}

      <div className="card scroll-x" style={{ padding: 0 }}>
        <table className="table">
          <thead>
            <tr>
              <th>Mã ticket</th>
              <th>Khách hàng</th>
              <th>Loại KN</th>
              <th>Phạm vi</th>
              <th>Ưu tiên</th>
              <th>Trạng thái</th>
              <th>SLA</th>
              <th>Cập nhật</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((t) => {
              const sla = formatSlaRemaining(t.sla_due_at);
              const rowClass = t.priority === "critical" ? "row-critical" : sla.overdue ? "row-warning" : "";
              return (
                <tr key={t.ticket_id} className={`clickable ${rowClass}`} onClick={() => router.push(`/tickets/${t.ticket_id}`)}>
                  <td className="mono">{t.ticket_id}</td>
                  <td>
                    {t.customer_name ?? "—"}
                    {t.human_handoff_requested && (
                      <span className="badge badge-warning" style={{ marginLeft: 6 }}>
                        Yêu cầu người thật
                      </span>
                    )}
                  </td>
                  <td>{t.complaint_type ? COMPLAINT_TYPE_LABEL[t.complaint_type] : "—"}</td>
                  <td>
                    <span className="badge badge-neutral">{t.scope ? SCOPE_LABEL[t.scope] : "—"}</span>
                  </td>
                  <td>
                    {t.priority === "critical" ? (
                      <span className="badge badge-critical">
                        <span className="dot dot-pulse" />
                        Khẩn cấp
                      </span>
                    ) : t.priority === "high" ? (
                      <span className="badge badge-warning">Cao</span>
                    ) : (
                      <span className="badge badge-neutral">Bình thường</span>
                    )}
                  </td>
                  <td>
                    <span className="badge badge-warning">{HITL_STATUS_LABEL[t.hitl_status]}</span>
                  </td>
                  <td className="mono" style={{ fontSize: 12 }}>
                    {sla.label}
                  </td>
                  <td className="faint" style={{ fontSize: 12 }}>
                    {formatDateTime(t.created_at)}
                  </td>
                </tr>
              );
            })}
            {tickets && filtered.length === 0 && (
              <tr>
                <td colSpan={8} className="dim" style={{ textAlign: "center", padding: 24 }}>
                  Không có ticket nào khớp bộ lọc.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
