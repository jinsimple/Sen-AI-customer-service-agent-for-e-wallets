"use client";

import { forwardRef, useCallback, useEffect, useImperativeHandle, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { claimTicket, listTickets } from "@/lib/api";
import {
  COMPLAINT_TYPE_LABEL,
  HITL_STATUS_LABEL,
  PRIORITY_LABEL,
  SCOPE_LABEL,
  type ComplaintType,
  type HitlStatus,
  type Priority,
  type Scope,
  type TicketPageSize,
  type TicketSummary,
} from "@/lib/types";
import { formatDateTime, formatSlaRemaining } from "@/lib/format";
import type { Role } from "@/lib/session";

// [polish trước quay 04/09] Bảng ticket + bộ lọc dùng CHUNG cho /dashboard
// (CSKH) và /quan-ly-ticket (Sếp) — hai trang trước đó gần như copy-paste
// nguyên khối này (250 dòng), tách ra một nơi để sửa 1 lần không lệch 2 nơi.
//
// 5 tiêu chí complaint_type/scope/priority/status/SLA lọc Ở SERVER (query
// param GET /tickets, kết hợp AND) vì phải đúng trên TOÀN BỘ tập khớp bộ lọc,
// không chỉ trang đang xem. "Chờ đối tác NH"/"Khách yêu cầu người thật" và ô
// tìm theo mã/tên vẫn lọc phía CLIENT, CHỈ trong trang hiện tại — hai tiêu
// chí đó không có tham số server tương ứng (logic partner_wait_status kết
// hợp hitl_status, và human_handoff_requested không nằm trong yêu cầu PO đợt
// này) — nhãn ghi rõ "(trang này)" để không lặp lại lỗi đọc nhầm % Lead bắt
// 20/08 (đếm trên cửa sổ giới hạn rồi tưởng là tổng).
export interface TicketListSectionHandle {
  refresh: () => void;
}

interface TicketListSectionProps {
  role: Role;
  pollMs?: number;
}

const PAGE_SIZES: TicketPageSize[] = [30, 50, 100];

function toIsoOrUndefined(localValue: string): string | undefined {
  if (!localValue) return undefined;
  const d = new Date(localValue);
  return Number.isNaN(d.getTime()) ? undefined : d.toISOString();
}

const TicketListSection = forwardRef<TicketListSectionHandle, TicketListSectionProps>(
  function TicketListSection({ role, pollMs }, ref) {
    const router = useRouter();

    const [complaintType, setComplaintType] = useState<ComplaintType | "">("");
    const [scope, setScope] = useState<Scope | "">("");
    const [priority, setPriority] = useState<Priority | "">("");
    const [hitlStatus, setHitlStatus] = useState<HitlStatus | "">("");
    const [slaAfterLocal, setSlaAfterLocal] = useState("");
    const [slaBeforeLocal, setSlaBeforeLocal] = useState("");

    const [page, setPage] = useState(1);
    const [pageSize, setPageSize] = useState<TicketPageSize>(50);

    const [showPartnerOnly, setShowPartnerOnly] = useState(false);
    const [showHandoffOnly, setShowHandoffOnly] = useState(false);
    const [search, setSearch] = useState("");

    const [tickets, setTickets] = useState<TicketSummary[] | null>(null);
    const [total, setTotal] = useState(0);
    const [error, setError] = useState<string | null>(null);
    const [claiming, setClaiming] = useState<string | null>(null);

    const hasServerFilter = Boolean(complaintType || scope || priority || hitlStatus || slaAfterLocal || slaBeforeLocal);

    const load = useCallback(() => {
      listTickets({
        complaint_type: complaintType || undefined,
        scope: scope || undefined,
        priority: priority || undefined,
        hitl_status: hitlStatus || undefined,
        sla_after: toIsoOrUndefined(slaAfterLocal),
        sla_before: toIsoOrUndefined(slaBeforeLocal),
        page,
        page_size: pageSize,
      })
        .then((res) => {
          setTickets(res.items);
          setTotal(res.total);
        })
        .catch((e) => setError(e.message ?? "Không tải được danh sách ticket"));
    }, [complaintType, scope, priority, hitlStatus, slaAfterLocal, slaBeforeLocal, page, pageSize]);

    useEffect(() => {
      load();
    }, [load]);

    useEffect(() => {
      if (!pollMs) return;
      const id = setInterval(load, pollMs);
      return () => clearInterval(id);
    }, [pollMs, load]);

    useImperativeHandle(ref, () => ({ refresh: load }), [load]);

    // Đổi bộ lọc/kích thước trang → quay về trang 1, tránh đứng ở trang 7
    // trong khi bộ lọc mới chỉ còn 2 trang (offset vượt total, trả mảng rỗng
    // trông như "hết ticket" trong khi chỉ là lệch trang).
    const setFilterAndResetPage = useCallback(<T,>(setter: (v: T) => void) => {
      return (v: T) => {
        setter(v);
        setPage(1);
      };
    }, []);

    const clearFilters = useCallback(() => {
      setComplaintType("");
      setScope("");
      setPriority("");
      setHitlStatus("");
      setSlaAfterLocal("");
      setSlaBeforeLocal("");
      setPage(1);
    }, []);

    const handleClaim = useCallback(
      (ticketId: string, e: React.MouseEvent) => {
        e.stopPropagation();
        setClaiming(ticketId);
        claimTicket(ticketId)
          .then(load)
          .catch((err) => setError(err.message ?? "Không nhận được vé"))
          .finally(() => setClaiming(null));
      },
      [load]
    );

    const filtered = useMemo(() => {
      if (!tickets) return [];
      let list = tickets;
      if (showPartnerOnly)
        list = list.filter(
          (t) =>
            (t.partner_wait_status === "waiting" || t.partner_wait_status === "overdue") &&
            t.hitl_status !== "approved" &&
            t.hitl_status !== "rejected"
        );
      if (showHandoffOnly) list = list.filter((t) => t.human_handoff_requested);
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
    }, [tickets, showPartnerOnly, showHandoffOnly, search]);

    const totalPages = Math.max(1, Math.ceil(total / pageSize));

    return (
      <>
        <div className="card" style={{ marginBottom: 16 }}>
          <div className="card-title">Bộ lọc</div>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "flex-end", marginTop: 10 }}>
            <div>
              <label htmlFor="tls-complaint-type" style={{ display: "block", fontSize: 12, fontWeight: 600, marginBottom: 4 }}>Loại KN</label>
              <select
                id="tls-complaint-type"
                value={complaintType}
                onChange={(e) => setFilterAndResetPage(setComplaintType)(e.target.value as ComplaintType | "")}
              >
                <option value="">Tất cả</option>
                {(Object.keys(COMPLAINT_TYPE_LABEL) as ComplaintType[]).map((k) => (
                  <option key={k} value={k}>{COMPLAINT_TYPE_LABEL[k]}</option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="tls-scope" style={{ display: "block", fontSize: 12, fontWeight: 600, marginBottom: 4 }}>Phạm vi</label>
              <select
                id="tls-scope"
                value={scope}
                onChange={(e) => setFilterAndResetPage(setScope)(e.target.value as Scope | "")}
              >
                <option value="">Tất cả</option>
                {(Object.keys(SCOPE_LABEL) as Scope[]).map((k) => (
                  <option key={k} value={k}>{SCOPE_LABEL[k]}</option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="tls-priority" style={{ display: "block", fontSize: 12, fontWeight: 600, marginBottom: 4 }}>Ưu tiên</label>
              <select
                id="tls-priority"
                value={priority}
                onChange={(e) => setFilterAndResetPage(setPriority)(e.target.value as Priority | "")}
              >
                <option value="">Tất cả</option>
                {(Object.keys(PRIORITY_LABEL) as Priority[]).map((k) => (
                  <option key={k} value={k}>{PRIORITY_LABEL[k]}</option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="tls-hitl-status" style={{ display: "block", fontSize: 12, fontWeight: 600, marginBottom: 4 }}>Trạng thái</label>
              <select
                id="tls-hitl-status"
                value={hitlStatus}
                onChange={(e) => setFilterAndResetPage(setHitlStatus)(e.target.value as HitlStatus | "")}
              >
                <option value="">Tất cả</option>
                {(Object.keys(HITL_STATUS_LABEL) as HitlStatus[]).map((k) => (
                  <option key={k} value={k}>{HITL_STATUS_LABEL[k]}</option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="tls-sla-after" style={{ display: "block", fontSize: 12, fontWeight: 600, marginBottom: 4 }}>SLA từ</label>
              <input
                id="tls-sla-after"
                type="datetime-local"
                value={slaAfterLocal}
                onChange={(e) => setFilterAndResetPage(setSlaAfterLocal)(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="tls-sla-before" style={{ display: "block", fontSize: 12, fontWeight: 600, marginBottom: 4 }}>SLA đến</label>
              <input
                id="tls-sla-before"
                type="datetime-local"
                value={slaBeforeLocal}
                onChange={(e) => setFilterAndResetPage(setSlaBeforeLocal)(e.target.value)}
              />
            </div>
            {hasServerFilter && (
              <span className="btn btn-outline btn-sm" onClick={clearFilters}>
                Xoá bộ lọc
              </span>
            )}
          </div>
        </div>

        <p className="dim" style={{ fontSize: 12, marginBottom: 8 }}>
          Bộ lọc ở trên áp dụng trên TOÀN BỘ ticket khớp ({total} vé). Hai chip và ô tìm bên dưới CHỈ lọc trong trang
          đang xem ({tickets?.length ?? 0} vé).
        </p>
        <div className="filter-bar">
          <span
            className={`filter-chip${showPartnerOnly ? " active" : ""}`}
            onClick={() => setShowPartnerOnly((v) => !v)}
          >
            Chờ đối tác NH (trang này)
          </span>
          <span
            className={`filter-chip${showHandoffOnly ? " active" : ""}`}
            onClick={() => setShowHandoffOnly((v) => !v)}
          >
            Khách yêu cầu người thật (trang này)
          </span>
          <div className="search-box">
            <svg className="icon icon-sm" viewBox="0 0 24 24">
              <circle cx="11" cy="11" r="7" />
              <path d="M21 21l-4-4" />
            </svg>
            <input
              placeholder="Tìm theo mã ticket, mã khiếu nại, tên khách (trang này)..."
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
                  <tr
                    key={t.ticket_id}
                    className={`clickable ${rowClass}`}
                    onClick={() => router.push(`/tickets/${t.ticket_id}`)}
                  >
                    <td className="mono" data-label="Mã ticket">
                      {t.ticket_id}
                      {/* ADR-064(b), PO chốt UX 04/09 — nút CHỈ hiện cho cskh
                          + vé còn trong pool; vé đã claim → badge cho mọi vai. */}
                      {role === "cskh" && t.claimed_by === null ? (
                        <button
                          type="button"
                          className="btn btn-outline btn-sm"
                          style={{ marginLeft: 8 }}
                          disabled={claiming === t.ticket_id}
                          onClick={(e) => handleClaim(t.ticket_id, e)}
                        >
                          {claiming === t.ticket_id ? "Đang nhận…" : "Nhận vé"}
                        </button>
                      ) : t.claimed_by !== null ? (
                        <span className="badge badge-neutral" style={{ marginLeft: 8 }}>
                          Đã nhận
                        </span>
                      ) : null}
                    </td>
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

        <div className="flex between center-y" style={{ marginTop: 12, flexWrap: "wrap", gap: 10 }}>
          <div className="flex center-y" style={{ gap: 8 }}>
            <span
              className="btn btn-outline btn-sm"
              style={page <= 1 ? { opacity: 0.5, pointerEvents: "none" } : undefined}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              ← Trước
            </span>
            <span className="dim" style={{ fontSize: 13 }}>
              Trang {page}/{totalPages} — tổng {total} vé khớp bộ lọc
            </span>
            <span
              className="btn btn-outline btn-sm"
              style={page >= totalPages ? { opacity: 0.5, pointerEvents: "none" } : undefined}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            >
              Sau →
            </span>
          </div>
          <div className="flex center-y" style={{ gap: 6 }}>
            <label htmlFor="tls-page-size" className="dim" style={{ fontSize: 13 }}>Số dòng/trang</label>
            <select
              id="tls-page-size"
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value) as TicketPageSize);
                setPage(1);
              }}
            >
              {PAGE_SIZES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
        </div>
      </>
    );
  }
);

export default TicketListSection;
