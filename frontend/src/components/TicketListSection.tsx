"use client";

import { forwardRef, useCallback, useEffect, useImperativeHandle, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { claimTicket, listTickets } from "@/lib/api";
import {
  COMPLAINT_TYPE_LABEL,
  HITL_STATUS_LABEL,
  PRIORITY_LABEL,
  SCOPE_LABEL,
  labelOf,
  type ComplaintType,
  type HitlStatus,
  type Priority,
  type Scope,
  type TicketPageSize,
  type TicketSummary,
} from "@/lib/types";
import { formatDateTime, formatSlaRemaining } from "@/lib/format";
import { useI18n } from "@/lib/i18n/client";
import type { Role } from "@/lib/session";

// [polish before the Sep 4 shoot] The ticket table + filters shared by /dashboard (support) and
// /quan-ly-ticket (supervisor) — the two pages had previously almost copy-pasted this whole block
// (250 lines); split out into one place so a fix doesn't drift between the two.
//
// The 5 criteria complaint_type/scope/priority/status/SLA filter ON THE SERVER (query params to GET
// /tickets, combined with AND) because they must hold over the WHOLE matching set, not just the
// page being viewed. "Awaiting bank partner"/"Customer asked for a human" and the ID/name search
// box still filter on the CLIENT, ONLY within the current page — those two criteria have no
// corresponding server parameter (partner_wait_status combines with hitl_status in logic, and
// human_handoff_requested wasn't part of this round's PO ask) — the label spells out "(this page)"
// so it doesn't repeat the misreading the Lead caught on Aug 20 (counting over a limited window and
// mistaking it for the total).
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
    const { t: tr, lang } = useI18n();

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
        .catch((e) => setError(e.message ?? tr("tls.loadError")));
    }, [complaintType, scope, priority, hitlStatus, slaAfterLocal, slaBeforeLocal, page, pageSize, tr]);

    useEffect(() => {
      load();
    }, [load]);

    useEffect(() => {
      if (!pollMs) return;
      const id = setInterval(load, pollMs);
      return () => clearInterval(id);
    }, [pollMs, load]);

    useImperativeHandle(ref, () => ({ refresh: load }), [load]);

    // Changing a filter/page size → jump back to page 1, to avoid being stuck on page 7 while the
    // new filter only leaves 2 pages (offset past the total, returning an empty array that looks
    // like "no more tickets" when it's really just a stale page).
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
          .catch((err) => setError(err.message ?? tr("tls.claimError")))
          .finally(() => setClaiming(null));
      },
      [load]
    );

    // [polish before the Sep 4 shoot] Row number is global across pagination (PO decision: page 2,
    // page_size 50 → rows 51-100, NOT repeating 1-50) — the index is computed from the POSITION
    // WITHIN THE FETCHED PAGE (`tickets`), not from `filtered` (the 2 page-scoped chips + the
    // search box below must not make the row number "jump around" continuously; the correct meaning
    // is "which row is this within THIS PAGE", not "which row among what's left after filtering
    // further in the browser").
    const sttTheoTicketId = useMemo(() => {
      const m = new Map<string, number>();
      (tickets ?? []).forEach((t, i) => m.set(t.ticket_id, (page - 1) * pageSize + i + 1));
      return m;
    }, [tickets, page, pageSize]);

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
        <div className="card tls-filter-panel" style={{ marginBottom: 16 }}>
          <div className="card-title">{tr("tls.filters")}</div>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "flex-end", marginTop: 10 }}>
            <div>
              <label htmlFor="tls-complaint-type" style={{ display: "block", fontSize: 12, fontWeight: 600, marginBottom: 4 }}>{tr("tls.type")}</label>
              <select
                id="tls-complaint-type"
                value={complaintType}
                onChange={(e) => setFilterAndResetPage(setComplaintType)(e.target.value as ComplaintType | "")}
              >
                <option value="">{tr("tls.all")}</option>
                {(Object.keys(COMPLAINT_TYPE_LABEL) as ComplaintType[]).map((k) => (
                  <option key={k} value={k}>{labelOf(COMPLAINT_TYPE_LABEL, k, lang)}</option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="tls-scope" style={{ display: "block", fontSize: 12, fontWeight: 600, marginBottom: 4 }}>{tr("tls.scope")}</label>
              <select
                id="tls-scope"
                value={scope}
                onChange={(e) => setFilterAndResetPage(setScope)(e.target.value as Scope | "")}
              >
                <option value="">{tr("tls.all")}</option>
                {(Object.keys(SCOPE_LABEL) as Scope[]).map((k) => (
                  <option key={k} value={k}>{labelOf(SCOPE_LABEL, k, lang)}</option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="tls-priority" style={{ display: "block", fontSize: 12, fontWeight: 600, marginBottom: 4 }}>{tr("tls.priority")}</label>
              <select
                id="tls-priority"
                value={priority}
                onChange={(e) => setFilterAndResetPage(setPriority)(e.target.value as Priority | "")}
              >
                <option value="">{tr("tls.all")}</option>
                {(Object.keys(PRIORITY_LABEL) as Priority[]).map((k) => (
                  <option key={k} value={k}>{labelOf(PRIORITY_LABEL, k, lang)}</option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="tls-hitl-status" style={{ display: "block", fontSize: 12, fontWeight: 600, marginBottom: 4 }}>{tr("tls.status")}</label>
              <select
                id="tls-hitl-status"
                value={hitlStatus}
                onChange={(e) => setFilterAndResetPage(setHitlStatus)(e.target.value as HitlStatus | "")}
              >
                <option value="">{tr("tls.all")}</option>
                {(Object.keys(HITL_STATUS_LABEL) as HitlStatus[]).map((k) => (
                  <option key={k} value={k}>{labelOf(HITL_STATUS_LABEL, k, lang)}</option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="tls-sla-after" style={{ display: "block", fontSize: 12, fontWeight: 600, marginBottom: 4 }}>{tr("tls.slaFrom")}</label>
              <input
                id="tls-sla-after"
                type="datetime-local"
                value={slaAfterLocal}
                onChange={(e) => setFilterAndResetPage(setSlaAfterLocal)(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="tls-sla-before" style={{ display: "block", fontSize: 12, fontWeight: 600, marginBottom: 4 }}>{tr("tls.slaTo")}</label>
              <input
                id="tls-sla-before"
                type="datetime-local"
                value={slaBeforeLocal}
                onChange={(e) => setFilterAndResetPage(setSlaBeforeLocal)(e.target.value)}
              />
            </div>
            {hasServerFilter && (
              <span className="btn-clear-filter" onClick={clearFilters}>
                {tr("tls.clearFilters")}
              </span>
            )}
          </div>
        </div>

        <p className="dim" style={{ fontSize: 12, marginBottom: 8 }}>
          {tr("tls.filterNote", { total, page: tickets?.length ?? 0 })}
        </p>
        <div className="filter-bar">
          <span
            className={`filter-chip${showPartnerOnly ? " active" : ""}`}
            onClick={() => setShowPartnerOnly((v) => !v)}
          >
            {tr("tls.chipPartner")}
          </span>
          <span
            className={`filter-chip${showHandoffOnly ? " active" : ""}`}
            onClick={() => setShowHandoffOnly((v) => !v)}
          >
            {tr("tls.chipHandoff")}
          </span>
          <div className="search-box">
            <svg className="icon icon-sm" viewBox="0 0 24 24">
              <circle cx="11" cy="11" r="7" />
              <path d="M21 21l-4-4" />
            </svg>
            <input
              placeholder={tr("tls.searchPlaceholder")}
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
                <th>{tr("tls.colNo")}</th>
                <th>{tr("tls.colTicket")}</th>
                <th>{tr("tls.colCustomer")}</th>
                <th>{tr("tls.type")}</th>
                <th>{tr("tls.scope")}</th>
                <th>{tr("tls.priority")}</th>
                <th>{tr("tls.status")}</th>
                <th>SLA</th>
                <th>{tr("tls.colUpdated")}</th>
                <th>{tr("tls.colActions")}</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((t) => {
                const sla = formatSlaRemaining(t.sla_due_at, lang);
                const rowClass = t.priority === "critical" ? "row-critical" : sla.overdue ? "row-warning" : "";
                return (
                  <tr
                    key={t.ticket_id}
                    className={`clickable ${rowClass}`}
                    onClick={() => router.push(`/tickets/${t.ticket_id}`)}
                  >
                    <td className="tls-stt" data-label={tr("tls.colNo")}>{sttTheoTicketId.get(t.ticket_id)}</td>
                    <td className="mono" data-label={tr("tls.colTicket")}>{t.ticket_id}</td>
                    <td className="tls-col-khach" data-label={tr("tls.colCustomer")}>
                      <span className="tls-ten" title={t.customer_name ?? "—"}>{t.customer_name ?? "—"}</span>
                      {t.human_handoff_requested && <span className="badge badge-warning">{tr("tls.handoffBadge")}</span>}
                    </td>
                    <td className="tls-col-loai-kn" data-label={tr("tls.type")} title={t.complaint_type ? labelOf(COMPLAINT_TYPE_LABEL, t.complaint_type, lang) : "—"}>
                      {t.complaint_type ? labelOf(COMPLAINT_TYPE_LABEL, t.complaint_type, lang) : "—"}
                    </td>
                    <td className="tls-nowrap" data-label={tr("tls.scope")}>
                      <span className="badge badge-neutral">{t.scope ? labelOf(SCOPE_LABEL, t.scope, lang) : "—"}</span>
                    </td>
                    <td className="tls-nowrap" data-label={tr("tls.priority")}>
                      {t.priority === "critical" ? (
                        <span className="badge badge-critical">
                          <span className="dot dot-pulse" />
                          {labelOf(PRIORITY_LABEL, "critical", lang)}
                        </span>
                      ) : t.priority === "high" ? (
                        <span className="status-dot dot-warning">{labelOf(PRIORITY_LABEL, "high", lang)}</span>
                      ) : (
                        <span className="status-dot">{labelOf(PRIORITY_LABEL, "normal", lang)}</span>
                      )}
                    </td>
                    <td className="tls-nowrap" data-label={tr("tls.status")}>
                      {t.hitl_status === "rejected" ? (
                        <span className="badge badge-danger">{labelOf(HITL_STATUS_LABEL, t.hitl_status, lang)}</span>
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
                          {labelOf(HITL_STATUS_LABEL, t.hitl_status, lang)}
                        </span>
                      )}
                    </td>
                    <td className="mono tls-nowrap" style={{ fontSize: 12 }} data-label="SLA">
                      {sla.label}
                    </td>
                    <td className="faint tls-nowrap" style={{ fontSize: 12 }} data-label={tr("tls.colUpdated")}>
                      {formatDateTime(t.created_at, lang)}
                    </td>
                    <td className="tls-col-thao-tac" data-label={tr("tls.colActions")}>
                      {/* ADR-064(b), PO chốt UX 04/09 — nút CHỈ hiện cho cskh +
                          vé còn trong pool; vé đã claim → badge cho mọi vai.
                          [polish 04/09, PO bắt ragged] tách khỏi ô Mã ticket —
                          cột riêng để độ dài mã KHÔNG còn quyết định nút có
                          rớt dòng hay không. */}
                      {role === "cskh" && t.claimed_by === null ? (
                        <button
                          type="button"
                          className="btn btn-outline btn-sm"
                          disabled={claiming === t.ticket_id}
                          onClick={(e) => handleClaim(t.ticket_id, e)}
                        >
                          {claiming === t.ticket_id ? tr("tls.claiming") : tr("tls.claim")}
                        </button>
                      ) : t.claimed_by !== null ? (
                        <span className="badge badge-neutral">{tr("tls.claimed")}</span>
                      ) : null}
                    </td>
                  </tr>
                );
              })}
              {tickets && filtered.length === 0 && (
                <tr>
                  <td colSpan={10} className="dim" style={{ textAlign: "center", padding: 24 }}>
                    {tr("tls.noMatch")}
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
              {tr("tls.prev")}
            </span>
            <span className="dim" style={{ fontSize: 13 }}>
              {tr("tls.pageInfo", { page, pages: totalPages, total })}
            </span>
            <span
              className="btn btn-outline btn-sm"
              style={page >= totalPages ? { opacity: 0.5, pointerEvents: "none" } : undefined}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            >
              {tr("tls.next")}
            </span>
          </div>
          <div className="flex center-y" style={{ gap: 6 }}>
            <label htmlFor="tls-page-size" className="dim" style={{ fontSize: 13 }}>{tr("tls.pageSize")}</label>
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
