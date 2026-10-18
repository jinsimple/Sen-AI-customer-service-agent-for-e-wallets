"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ApiError, listResolutions } from "@/lib/api";
import { ACTION_TYPE_LABEL, COMPLAINT_TYPE_LABEL, SCOPE_LABEL, labelOf, type ResolutionListItem } from "@/lib/types";
import { useI18n } from "@/lib/i18n/client";
import { formatDateTime, formatMoney } from "@/lib/format";

export default function ApproveClient() {
  const { t, lang } = useI18n();
  const [pending, setPending] = useState<ResolutionListItem[] | null>(null);
  const [history, setHistory] = useState<ResolutionListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    try {
      const [p, all] = await Promise.all([listResolutions("pending_approval"), listResolutions("all")]);
      setPending(p);
      setHistory(all.filter((r) => r.status === "approved" || r.status === "rejected"));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : t("approve.loadError"));
    }
  }

  useEffect(() => {
    // Don't call load() directly — load()'s setState (setError) runs SYNCHRONOUSLY on the first
    // line (before any await), which react-hooks/set-state-in-effect treats as a synchronous
    // setState inside an effect. Push the call out of the current synchronous turn (microtask) —
    // same spirit as the .then()-chain dashboard/page.tsx already uses, while keeping load() as
    // async/await for reuse elsewhere (handleApprove...).
    void Promise.resolve().then(load);
  }, []);

  return (
    <>
      <div className="page-head">
        <span className="eyebrow">{t("eyebrow.supervisor")}</span>
        <h1>{t("approve.title")}</h1>
        <p className="sub">
          {t("approve.sub")}
        </p>
      </div>

      {error && <div className="note" style={{ borderColor: "var(--danger)" }}>{error}</div>}

      <div className="grid grid-2" style={{ alignItems: "start" }}>
        {pending?.length === 0 && <div className="dim">{t("approve.none")}</div>}
        {pending?.map((r) => (
          <div className="card" key={r.resolution_id}>
            <div className="flex between center-y" style={{ marginBottom: 6 }}>
              <Link href={`/tickets/${r.ticket_id}`} className="card-title mono" style={{ fontSize: 15 }}>
                {r.ticket_id}
              </Link>
              <span className="badge badge-neutral">
                {r.scope === "internal_wallet" ? t("approve.internalBadge") : t("approve.bankBadge")}
              </span>
            </div>
            <div className="card-sub">
              {r.complaint_type ? labelOf(COMPLAINT_TYPE_LABEL, r.complaint_type, lang) : "—"}
              {r.scope ? ` · ${labelOf(SCOPE_LABEL, r.scope, lang)}` : ""}
            </div>
            <div className="kv-row" style={{ marginTop: 12 }}>
              <span className="k">{t("approve.proposal")}</span>
              <span className="v">{labelOf(ACTION_TYPE_LABEL, r.action_type, lang)}{r.amount ? ` — ${formatMoney(r.amount, lang)}` : ""}</span>
            </div>
            <div className="kv-row"><span className="k">{t("approve.rationale")}</span><span className="v" style={{ fontWeight: 400 }}>{r.rationale}</span></div>
            <div className="kv-row"><span className="k">{t("approve.submittedAt")}</span><span className="v" style={{ fontWeight: 400 }}>{formatDateTime(r.created_at, lang)}</span></div>

            {r.scope && r.scope !== "internal_wallet" ? (
              <div className="note callout-gold" style={{ marginTop: 12 }}>
                {t("approve.bankNote")}
              </div>
            ) : null}

            {/* Hotfix 2 (14/08): trang này giờ CHỈ là hàng chờ tóm tắt — nút
                duyệt/từ chối đã chuyển vào chi tiết ticket, nơi có dấu vết điều
                tra và thông tin giao dịch. Để nút ở đây là mời sếp quyết mà không
                cần đọc căn cứ, ngược với US-005. */}
            <div className="flex gap-sm wrap" style={{ marginTop: 16 }}>
              <Link className="btn btn-primary" href={`/tickets/${r.ticket_id}`}>
                {t("approve.openDetail")}
              </Link>
            </div>
          </div>
        ))}
      </div>

      <div className="section" style={{ marginTop: 30 }}>
        <div className="section-title">
          {t("approve.logTitle")}
        </div>
        <div className="card">
          <div className="scroll-x">
            <table className="table">
              <thead>
                <tr><th>{t("approve.colTime")}</th><th>{t("approve.colWho")}</th><th>{t("approve.colAction")}</th><th>{t("approve.colTicket")}</th><th>{t("approve.colRationale")}</th></tr>
              </thead>
              <tbody>
                {history?.map((r) => (
                  <tr key={r.resolution_id}>
                    <td className="mono" style={{ fontSize: 12 }}>{r.approved_at ? formatDateTime(r.approved_at, lang) : "—"}</td>
                    <td>{r.approved_by_name ?? "—"}</td>
                    <td>
                      {r.status === "approved" ? (
                        <span className="badge badge-success">{t("approval.approve")}</span>
                      ) : (
                        <span className="badge badge-danger">{t("approval.reject")}</span>
                      )}
                    </td>
                    <td className="mono">
                      <Link href={`/tickets/${r.ticket_id}`}>{r.ticket_id}</Link>
                    </td>
                    <td className="dim" style={{ fontSize: 12 }}>{r.rationale}</td>
                  </tr>
                ))}
                {history?.length === 0 && (
                  <tr><td colSpan={5} className="dim" style={{ textAlign: "center", padding: 20 }}>{t("approve.noActions")}</td></tr>
                )}
              </tbody>
            </table>
          </div>
          <div className="note" style={{ marginTop: 12 }}>
            <svg className="icon" viewBox="0 0 24 24"><rect x="4" y="11" width="16" height="9" rx="2" /><path d="M8 11V7a4 4 0 018 0v4" /></svg>
            <div>{t("approve.logNote")}</div>
          </div>
        </div>
      </div>
    </>
  );
}
