"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { listTickets } from "@/lib/api";
import { COMPLAINT_TYPE_LABEL, HITL_STATUS_LABEL, SCOPE_LABEL, type TicketSummary } from "@/lib/types";
import { formatDateTime, formatSlaRemaining } from "@/lib/format";

// ADR-064 (b — Sếp thấy TẤT CẢ, không đổi phạm vi quyền hiện có) — tách khỏi
// /dashboard (CSKH) thay vì tái dùng thẳng: trang đó còn WS chờ chat trực
// tiếp/nhận live-chat — việc VẬN HÀNH của CSKH, không phải việc QUẢN LÝ của
// Sếp. Bảng+bộ lọc dùng lại đúng khuôn (đã chứng minh ổn ở dashboard).
type FilterKey = "all" | "pending" | "partner" | "critical" | "handoff";

// [04/09] limit cao hơn hẳn /dashboard (100) — trang đó ĐÃ có ghi chú "không
// phải tổng" (Lead bắt 20/08, đọc nhầm % vì cửa sổ 100 vé). Trang này đúng
// nghĩa "Sếp xem TẤT CẢ" theo yêu cầu PO, nên phải THẬT là tất cả trong quy
// mô hiện tại (654 ticket đo được 04/09), không lặp lại cùng lỗi đọc nhầm.
const GIOI_HAN_TICKET = 1000;

export default function QuanLyTicketClient() {
  const router = useRouter();
  const [tickets, setTickets] = useState<TicketSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<FilterKey>("all");
  const [search, setSearch] = useState("");

  const loadTickets = useCallback(() => {
    listTickets({ limit: GIOI_HAN_TICKET })
      .then(setTickets)
      .catch((e) => setError(e.message ?? "Không tải được danh sách ticket"));
  }, []);

  useEffect(() => {
    loadTickets();
  }, [loadTickets]);

  const counts = useMemo(() => {
    if (!tickets) return { all: 0, pending: 0, partner: 0, critical: 0, handoff: 0 };
    return {
      all: tickets.length,
      pending: tickets.filter((t) => t.hitl_status === "pending").length,
      partner: tickets.filter(
        (t) =>
          (t.partner_wait_status === "waiting" || t.partner_wait_status === "overdue") &&
          t.hitl_status !== "approved" &&
          t.hitl_status !== "rejected"
      ).length,
      critical: tickets.filter((t) => t.priority === "critical").length,
      handoff: tickets.filter((t) => t.human_handoff_requested).length,
    };
  }, [tickets]);

  const filtered = useMemo(() => {
    if (!tickets) return [];
    let list = tickets;
    if (filter === "pending") list = list.filter((t) => t.hitl_status === "pending");
    if (filter === "partner")
      list = list.filter(
        (t) =>
          (t.partner_wait_status === "waiting" || t.partner_wait_status === "overdue") &&
          t.hitl_status !== "approved" &&
          t.hitl_status !== "rejected"
      );
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
        <span className="eyebrow">Webapp Sếp</span>
        <h1>Quản lý ticket</h1>
        <p className="sub">Toàn bộ ticket trong hệ thống, không riêng ca đang chờ duyệt — để nắm bức tranh chung.</p>
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
        <table className="table table-cards-mobile">
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
                  <td className="mono" data-label="Mã ticket">{t.ticket_id}</td>
                  <td data-label="Khách hàng">
                    {t.customer_name ?? "—"}
                    {t.human_handoff_requested && (
                      <span className="badge badge-warning" style={{ marginLeft: 6 }}>
                        Yêu cầu người thật
                      </span>
                    )}
                  </td>
                  <td data-label="Loại KN">{t.complaint_type ? COMPLAINT_TYPE_LABEL[t.complaint_type] : "—"}</td>
                  <td data-label="Phạm vi">
                    <span className="badge badge-neutral">{t.scope ? SCOPE_LABEL[t.scope] : "—"}</span>
                  </td>
                  <td data-label="Ưu tiên">
                    {t.priority === "critical" ? (
                      <span className="badge badge-critical">
                        <span className="dot dot-pulse" />
                        Khẩn cấp
                      </span>
                    ) : t.priority === "high" ? (
                      <span className="status-dot dot-warning">Cao</span>
                    ) : (
                      <span className="status-dot">Bình thường</span>
                    )}
                  </td>
                  <td data-label="Trạng thái">
                    {t.hitl_status === "rejected" ? (
                      <span className="badge badge-danger">{HITL_STATUS_LABEL[t.hitl_status]}</span>
                    ) : (
                      <span
                        className={`status-dot ${
                          t.hitl_status === "approved"
                            ? "dot-success"
                            : t.hitl_status === "need_more_info"
                              ? "dot-info"
                              : ""
                        }`}
                      >
                        {HITL_STATUS_LABEL[t.hitl_status]}
                      </span>
                    )}
                  </td>
                  <td className="mono" style={{ fontSize: 12 }} data-label="SLA">
                    {sla.label}
                  </td>
                  <td className="faint" style={{ fontSize: 12 }} data-label="Cập nhật">
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
