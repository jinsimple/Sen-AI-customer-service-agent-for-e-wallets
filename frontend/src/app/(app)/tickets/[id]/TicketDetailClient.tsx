"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ApiError,
  escalateTicket,
  getTicketDetail,
  getTicketTranscript,
  lookupTransaction,
  proposeResolution,
  requestMoreInfo,
} from "@/lib/api";
import {
  ACTION_TYPE_LABEL,
  COMPLAINT_TYPE_LABEL,
  labelOf,
  HITL_STATUS_LABEL,
  RESOLUTION_STATUS_LABEL,
  SCOPE_LABEL,
  TOOL_NAME_LABEL,
  TX_STATUS_LABEL,
  type ActionType,
  type LookupTransactionResult,
  type TicketDetail,
  type TicketTranscript,
  type TransactionStatus,
} from "@/lib/types";
import BuocDieuTra from "@/components/BuocDieuTra";
import { useI18n } from "@/lib/i18n/client";
import { rich } from "@/lib/i18n/rich";
import { formatDateTime, formatMoney } from "@/lib/format";
import type { Role } from "@/lib/session";
import LiveChatPanel from "@/components/LiveChatPanel";
import ResolutionApprovalActions from "@/components/ResolutionApprovalActions";

// Danh sách hướng xử lý cho form — nhãn lấy từ ACTION_TYPE_LABEL (nguồn duy
// nhất, chép theo mo_ta của contract). Trước đây đây là bảng nhãn THỨ HAI,
// chữ khác hẳn chỗ hiển thị ("Hoàn về ví" vs "Hoàn tiền về ví").
const ACTION_TYPE_VALUES = Object.keys(ACTION_TYPE_LABEL) as ActionType[];

export default function TicketDetailClient({
  ticketId,
  viewerRole,
  viewerUserId,
}: {
  ticketId: string;
  viewerRole: Role;
  viewerUserId: string;
}) {
  const router = useRouter();
  const { t, lang } = useI18n();
  const backHref = viewerRole === "supervisor" ? "/approve" : "/dashboard";
  const [detail, setDetail] = useState<TicketDetail | null>(null);
  const [transcript, setTranscript] = useState<TicketTranscript | null>(null);
  const [tx, setTx] = useState<LookupTransactionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ kind: "success" | "error"; text: string } | null>(null);

  const [actionType, setActionType] = useState(ACTION_TYPE_VALUES[0]);
  const [rationale, setRationale] = useState("");
  const [amount, setAmount] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [bankReason, setBankReason] = useState("");

  const load = useCallback(async () => {
    setError(null);
    try {
      const d = await getTicketDetail(ticketId);
      setDetail(d);
      // ADR-044 — chỉ gọi khi vé ĐÃ bàn giao (cùng điều kiện LiveChatPanel
      // bên dưới): tính năng ra đời từ đúng nhu cầu "khách xin gặp người
      // thật", vé chưa bao giờ bàn giao không có gì để CSKH cần đọc thêm ở
      // đây — tránh gọi route thừa cho phần lớn vé không liên quan.
      if (d.ticket.human_handoff_requested) {
        getTicketTranscript(ticketId)
          .then(setTranscript)
          .catch(() => setTranscript(null));
      }
      if (d.complaint?.trans_id) {
        const t = await lookupTransaction({ trans_id: d.complaint.trans_id });
        setTx(t);
        // V3.1 (hotfix 14/08): điền sẵn số tiền theo ĐÚNG giao dịch bị khiếu
        // nại, thay vì để ô trống cho người nhập tay. Ô tự do là thứ đã sinh
        // ra đề xuất "hoàn 6 đồng" cho giao dịch 107.000đ — số tiền không truy
        // vết được về giao dịch nào. Vẫn cho sửa (có case hoàn một phần),
        // nhưng backend chặn > số tiền giao dịch (V3.2).
        if ("transaction" in t) setAmount(String(t.transaction.amount));
      } else {
        setTx(null);
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.message : t("td.loadError"));
    }
  }, [ticketId]);

  useEffect(() => {
    void Promise.resolve().then(load);
  }, [load]);

  const citedIds = [
    ...(tx && "tool_result_id" in tx ? [tx.tool_result_id] : []),
    ...(detail?.investigation_logs.map((l) => l.tool_result_id).filter((x): x is string => !!x) ?? []),
  ];

  async function handlePropose(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setMsg(null);
    try {
      await proposeResolution({
        ticket_id: ticketId,
        action_type: actionType,
        rationale,
        amount: amount ? Number(amount) : null,
        cited_tool_result_ids: citedIds,
      });
      setMsg({ kind: "success", text: t("td.submittedOk") });
      setRationale("");
      setAmount("");
      await load();
    } catch (e) {
      setMsg({ kind: "error", text: e instanceof ApiError ? e.message : t("td.submitFailed") });
    } finally {
      setSubmitting(false);
    }
  }

  async function handleRequestMoreInfo() {
    setMsg(null);
    try {
      await requestMoreInfo(ticketId, {});
      setMsg({ kind: "success", text: t("td.needMoreInfoOk") });
      await load();
    } catch (e) {
      setMsg({ kind: "error", text: e instanceof ApiError ? e.message : t("td.actionFailed") });
    }
  }

  async function handleBankEscalate(e: React.FormEvent) {
    e.preventDefault();
    setMsg(null);
    try {
      await escalateTicket({
        ticket_id: ticketId,
        target: "partner_bank",
        reason: bankReason,
      });
      setMsg({ kind: "success", text: t("td.bankRequestOk") });
      setBankReason("");
      await load();
    } catch (e) {
      setMsg({ kind: "error", text: e instanceof ApiError ? e.message : t("td.bankRequestFailed") });
    }
  }

  const backButton = (
    <button
      type="button"
      onClick={() => router.push(backHref)}
      className="btn btn-ghost btn-sm"
      style={{ marginBottom: 14, paddingLeft: 0 }}
    >
      <svg className="icon icon-sm" viewBox="0 0 24 24">
        <path d="M19 12H5M12 19l-7-7 7-7" />
      </svg>
      {t("td.backTo", { where: viewerRole === "supervisor" ? t("td.backToApprove") : t("td.backToQueue") })}
    </button>
  );

  if (error)
    return (
      <>
        {backButton}
        <div className="note" style={{ borderColor: "var(--danger)" }}>{error}</div>
      </>
    );
  if (!detail)
    return (
      <>
        {backButton}
        <div className="dim">{t("common.loading")}</div>
      </>
    );

  const c = detail.complaint;
  const foundTx = tx && "transaction" in tx ? tx.transaction : null;
  // Hotfix 2: chỉ những đề xuất CÒN CHỜ mới có nút quyết định. Đề xuất đã
  // duyệt/từ chối vẫn hiện ở khối "Đề xuất đã trình" bên dưới, không kèm nút.
  const pendingResolutions = detail.resolutions.filter((r) => r.status === "pending_approval");

  return (
    <>
      {backButton}

      <div className="flex between center-y wrap gap-md" style={{ marginBottom: 18 }}>
        <div className="flex gap-md center-y wrap">
          <h2 className="mono" style={{ fontSize: 19 }}>
            {detail.ticket.ticket_id}
          </h2>
          {c && <span className="badge badge-neutral">{labelOf(COMPLAINT_TYPE_LABEL, c.type, lang)}</span>}
          {c && <span className="badge badge-neutral">{labelOf(SCOPE_LABEL, c.scope, lang)}</span>}
          {c?.priority === "critical" && (
            <span className="badge badge-critical">
              <span className="dot dot-pulse" /> {t("td.critical")}
            </span>
          )}
          {detail.ticket.hitl_status === "rejected" ? (
            <span className="badge badge-danger">{labelOf(HITL_STATUS_LABEL, detail.ticket.hitl_status, lang)}</span>
          ) : (
            <span
              className={`status-dot ${
                detail.ticket.hitl_status === "approved"
                  ? "dot-success"
                  : detail.ticket.hitl_status === "need_more_info"
                    ? "dot-info"
                    : ""
              }`}
            >
              {labelOf(HITL_STATUS_LABEL, detail.ticket.hitl_status, lang)}
            </span>
          )}
        </div>
      </div>

      {msg && <div className={`note form-msg ${msg.kind}`} style={{ marginBottom: 18 }}>{msg.text}</div>}

      <div className="grid grid-2" style={{ alignItems: "start" }}>
        <div className="flex-col gap-lg">
          <div className="card">
            <div className="card-title">{t("td.investigationLog")}</div>
            <div className="card-sub" style={{ marginBottom: 14 }}>
              {t("td.investigationLogSub")}
            </div>
            {detail.investigation_logs.length === 0 ? (
              <div className="note">{t("td.noSteps")}</div>
            ) : (
              <div className="trail">
                {detail.investigation_logs.map((log) => (
                  <BuocDieuTra key={log.step_no} log={log} />
                ))}
              </div>
            )}
          </div>

          {c && c.fraud_signals.length > 0 && (
            <div className="card">
              <div
                className="card-title"
                style={{ color: "var(--warning)", display: "flex", alignItems: "center", gap: 7 }}
              >
                <svg className="icon" viewBox="0 0 24 24">
                  <path d="M4 4v16l4-4h12V4H4z" />
                </svg>
                {t("td.routingSignal")}
              </div>
              <div className="flex gap-sm wrap" style={{ marginTop: 10 }}>
                {c.fraud_signals.map((s) => (
                  <span className="badge badge-warning mono" key={s}>
                    {s}
                  </span>
                ))}
              </div>
              <div className="note" style={{ marginTop: 12 }}>
                {rich(t("td.fs06Note"))}
              </div>
            </div>
          )}
        </div>

        <div className="flex-col gap-lg">
          {detail.ticket.human_handoff_requested && (viewerRole === "cskh" || viewerRole === "supervisor") && (
            <LiveChatPanel ticketId={detail.ticket.ticket_id} viewerRole={viewerRole} viewerUserId={viewerUserId} />
          )}

          {/* ADR-044 — hội thoại bot↔khách trước khi bàn giao, để CSKH không
              bắt khách kể lại từ đầu thứ họ đã nói với bot. */}
          {detail.ticket.human_handoff_requested && transcript && (
            <div className="card">
              <div className="card-title">{t("td.conversationTitle")}</div>
              {transcript.transcript === null ? (
                <div className="dim" style={{ fontSize: 13 }}>{transcript.ly_do}</div>
              ) : (
                <>
                  {/* Nghĩa vụ khai (ADR-044, "PII — GIẢI XONG bằng phép đo"):
                      hội thoại ghi TRƯỚC bản vá D' còn giữ nhãn che SAI vĩnh
                      viễn ([PERSON_VN]/[LOCATION] thay từ khách gõ thật, ~12%
                      câu tiếng Việt đời thường bị bóp méo) — KHÔNG vá ngược
                      kho lịch sử, sửa bằng chứng là việc không được làm. */}
                  <div className="note" style={{ fontSize: 11, marginBottom: 10 }}>
                    {t("td.piiFilterNote")}
                  </div>
                  {transcript.handoff_at !== null && transcript.chi_so_bang_giao === null && (
                    <div className="note" style={{ fontSize: 11, marginBottom: 10 }}>
                      {t("td.handoffMismatch", { time: new Date(transcript.handoff_at).toLocaleString(lang === "en" ? "en-GB" : "vi-VN") })}
                    </div>
                  )}
                  <div className="flex-col gap-sm">
                    {transcript.transcript.map((luot, i) => (
                      <div key={i}>
                        <div
                          className="kv-row"
                          style={{ alignItems: "flex-start", opacity: luot.vai === "khach" ? 1 : 0.9 }}
                        >
                          <span className="k" style={{ minWidth: 56 }}>
                            {luot.vai === "khach" ? t("td.customer") : t("td.bot")}
                          </span>
                          <span className="v">
                            {luot.noi_dung}
                            {luot.co_goi_tool && (
                              <span className="badge badge-info mono" style={{ marginLeft: 8, fontSize: 10 }}>
                                {t("td.basedOnLookup")}
                              </span>
                            )}
                          </span>
                        </div>
                        {transcript.chi_so_bang_giao !== null && i === transcript.chi_so_bang_giao && (
                          <div
                            className="dim"
                            style={{ textAlign: "center", fontSize: 11, margin: "10px 0", borderTop: "1px dashed var(--border-strong)", paddingTop: 8 }}
                          >
                            {t("td.handoffMarker")}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          )}

          <div className="card">
            <div className="card-title">{t("td.txInfo")}</div>
            {!c?.trans_id && <div className="dim" style={{ fontSize: 13 }}>{t("td.txNotFound")}</div>}
            {c?.trans_id && !tx && <div className="dim" style={{ fontSize: 13 }}>{t("td.txLoading")}</div>}
            {tx && "status" in tx && tx.status === "not_found" && (
              <div className="dim" style={{ fontSize: 13 }}>{t("td.txNotFoundById", { id: c?.trans_id ?? "" })}</div>
            )}
            {foundTx && (
              <>
                <div className="kv-row"><span className="k">{t("td.txId")}</span><span className="v mono">{foundTx.trans_id}</span></div>
                <div className="kv-row"><span className="k">{t("td.amount")}</span><span className="v mono">{formatMoney(foundTx.amount, lang)}</span></div>
                <div className="kv-row"><span className="k">{t("td.status")}</span><span className="v"><span className="badge badge-info">{labelOf(TX_STATUS_LABEL, foundTx.status as TransactionStatus, lang) ?? foundTx.status}</span></span></div>
                <div className="kv-row">
                  <span className="k">{t("td.recipient")}</span>
                  <span className="v masked">
                    <svg className="icon icon-sm" viewBox="0 0 24 24"><path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z" /><circle cx="12" cy="12" r="3" /></svg>
                    {foundTx.receiver?.full_name ?? "—"} {foundTx.receiver?.phone ?? foundTx.receiver?.account_no ?? ""}
                  </span>
                </div>
                <div className="note" style={{ marginTop: 10, fontSize: 11 }}>
                  {t("td.pdpaMasked")}
                </div>
              </>
            )}
          </div>

          {c && c.scope !== "internal_wallet" && viewerRole === "cskh" && (
            <div className="card">
              <div className="card-title">{t("td.bankInvestigation")}</div>
              <div className="card-sub" style={{ marginBottom: 12 }}>
                {t("td.bankInvestigationSub")}
              </div>
              {detail.escalations.filter((e) => e.target === "partner_bank").length > 0 ? (
                <div className="note">{t("td.bankRequestSent")}</div>
              ) : (
                <form onSubmit={handleBankEscalate}>
                  <div className="field" style={{ marginTop: 0 }}>
                    <label>{t("td.bankReasonLabel")}</label>
                    <input value={bankReason} onChange={(e) => setBankReason(e.target.value)} required />
                  </div>
                  <button className="btn btn-outline btn-sm" style={{ marginTop: 14 }} type="submit">
                    {t("td.sendBankRequest")}
                  </button>
                </form>
              )}
            </div>
          )}

          {viewerRole === "cskh" ? (
            <div className="card">
              <div className="card-title">{t("td.yourActions")}</div>
              <div className="card-sub" style={{ marginBottom: 14 }}>
                {t("td.noSelfApprove")}
              </div>
              <form onSubmit={handlePropose}>
                <div className="field" style={{ marginTop: 0 }}>
                  <label>{t("td.proposedAction")}</label>
                  <select value={actionType} onChange={(e) => setActionType(e.target.value as ActionType)}>
                    {ACTION_TYPE_VALUES.map((value) => (
                      <option key={value} value={value}>{labelOf(ACTION_TYPE_LABEL, value, lang)}</option>
                    ))}
                  </select>
                </div>
                <div className="field">
                  <label>{t("td.amountOptional")}</label>
                  <input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} />
                  {/* V3.2 phần còn lại: backend chỉ chặn được số vô nghĩa (<=0 hoặc
                      vượt số tiền giao dịch). Nó KHÔNG bắt được "6 đồng cho giao
                      dịch 107.000đ" — đúng ca đã xảy ra thật — vì 6 vẫn nằm trong
                      khoảng hợp lệ. Chênh lệch so với giao dịch là hợp lệ (hoàn một
                      phần), nên đây là CẢNH BÁO cho người trình, không phải chặn. */}
                  {foundTx && amount !== "" && Number(amount) !== foundTx.amount && (
                    <div className="dim" style={{ fontSize: 12, marginTop: 6 }}>
                      {t("td.amountMismatch", { amount: formatMoney(foundTx.amount, lang) })}
                    </div>
                  )}
                </div>
                <div className="field">
                  <label>{t("td.rationale")}</label>
                  <textarea rows={2} value={rationale} onChange={(e) => setRationale(e.target.value)} required />
                </div>
                <div className="flex gap-sm wrap" style={{ marginTop: 14 }}>
                  <button className="btn btn-gold" type="submit" disabled={submitting}>
                    {t("td.submitToSupervisor")}
                  </button>
                  <button className="btn btn-outline" type="button" onClick={handleRequestMoreInfo}>
                    {t("td.requestMoreInfo")}
                  </button>
                  <span className="tooltip-wrap" data-tooltip={t("td.outOfAuthority")}>
                    <button className="btn btn-outline" disabled type="button" style={{ borderColor: "var(--border-strong)", color: "var(--text-faint)" }}>
                      {t("td.approveRefund")}
                    </button>
                  </span>
                </div>
              </form>
            </div>
          ) : (
            /* Hotfix 2 (14/08, PO thật quyết): nút duyệt/từ chối chuyển VÀO ĐÂY,
               ngay dưới dấu vết điều tra + thông tin giao dịch. Sáng nay nó nằm ở
               card danh sách /approve — tức mời sếp quyết mà không cần đọc căn cứ,
               ngược với US-005. Đảo lại quyết định V1 sáng nay: đó là lựa chọn phạm
               vi của hotfix 1, không phải ADR, nên PO override được. OTP dynamic
               linking KHÔNG đổi — vẫn xin theo từng resolution.
               Khối này CHỈ render cho supervisor (nhánh else của viewerRole ===
               "cskh"); quyền thật vẫn do backend ép, UI chỉ phản chiếu cho đúng. */
            <div className="card">
              <div className="card-title">{t("td.approvalDecision")}</div>
              {pendingResolutions.length === 0 ? (
                <div className="dim" style={{ fontSize: 13 }}>
                  {t("td.noPending")}
                </div>
              ) : (
                pendingResolutions.map((r) => (
                  <div key={r.resolution_id} style={{ marginTop: 12 }}>
                    <div className="kv-row">
                      <span className="k">{t("td.proposal")}</span>
                      <span className="v">
                        {labelOf(ACTION_TYPE_LABEL, r.action_type, lang)}
                        {r.amount ? ` — ${formatMoney(r.amount, lang)}` : ""}
                      </span>
                    </div>
                    <ResolutionApprovalActions
                      resolutionId={r.resolution_id}
                      onDone={load}
                      onError={(m) => setMsg({ kind: "error", text: m })}
                    />
                  </div>
                ))
              )}
            </div>
          )}

          {detail.resolutions.length > 0 && (
            <div className="card">
              <div className="card-title">{t("td.submittedProposals")}</div>
              {detail.resolutions.map((r) => (
                <div className="kv-row" key={r.resolution_id}>
                  <span className="k">{labelOf(ACTION_TYPE_LABEL, r.action_type, lang)}{r.amount ? ` — ${formatMoney(r.amount, lang)}` : ""}</span>
                  <span className="v"><span className="badge badge-info">{labelOf(RESOLUTION_STATUS_LABEL, r.status, lang)}</span></span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
