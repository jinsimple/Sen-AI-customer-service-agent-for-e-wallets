"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ApiError,
  escalateTicket,
  getTicketDetail,
  lookupTransaction,
  proposeResolution,
  requestMoreInfo,
} from "@/lib/api";
import {
  COMPLAINT_TYPE_LABEL,
  HITL_STATUS_LABEL,
  SCOPE_LABEL,
  type LookupTransactionResult,
  type TicketDetail,
} from "@/lib/types";
import { formatDateTime, formatMoney } from "@/lib/format";
import type { Role } from "@/lib/session";
import LiveChatPanel from "@/components/LiveChatPanel";

const ACTION_TYPES = [
  { value: "refund_to_wallet", label: "Hoàn về ví" },
  { value: "refund_to_bank", label: "Hoàn về ngân hàng" },
  { value: "ledger_adjustment", label: "Điều chỉnh sổ cái nội bộ" },
  { value: "no_action", label: "Không cần xử lý" },
  { value: "manual_review", label: "Cần xem xét thủ công" },
];

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
  const backHref = viewerRole === "supervisor" ? "/approve" : "/dashboard";
  const [detail, setDetail] = useState<TicketDetail | null>(null);
  const [tx, setTx] = useState<LookupTransactionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ kind: "success" | "error"; text: string } | null>(null);

  const [actionType, setActionType] = useState(ACTION_TYPES[0].value);
  const [rationale, setRationale] = useState("");
  const [amount, setAmount] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [bankReason, setBankReason] = useState("");

  const load = useCallback(async () => {
    setError(null);
    try {
      const d = await getTicketDetail(ticketId);
      setDetail(d);
      if (d.complaint?.trans_id) {
        const t = await lookupTransaction({ trans_id: d.complaint.trans_id });
        setTx(t);
      } else {
        setTx(null);
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Không tải được ticket");
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
      setMsg({ kind: "success", text: "Đã trình sếp — chờ phê duyệt." });
      setRationale("");
      setAmount("");
      await load();
    } catch (e) {
      setMsg({ kind: "error", text: e instanceof ApiError ? e.message : "Trình sếp thất bại" });
    } finally {
      setSubmitting(false);
    }
  }

  async function handleRequestMoreInfo() {
    setMsg(null);
    try {
      await requestMoreInfo(ticketId, {});
      setMsg({ kind: "success", text: "Đã chuyển ticket sang trạng thái cần điều tra thêm." });
      await load();
    } catch (e) {
      setMsg({ kind: "error", text: e instanceof ApiError ? e.message : "Thao tác thất bại" });
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
      setMsg({ kind: "success", text: "Đã gửi yêu cầu tra soát tới ngân hàng đối tác." });
      setBankReason("");
      await load();
    } catch (e) {
      setMsg({ kind: "error", text: e instanceof ApiError ? e.message : "Gửi yêu cầu thất bại" });
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
      Quay lại {viewerRole === "supervisor" ? "Phê duyệt" : "Hàng chờ"}
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
        <div className="dim">Đang tải…</div>
      </>
    );

  const c = detail.complaint;
  const foundTx = tx && "transaction" in tx ? tx.transaction : null;

  return (
    <>
      {backButton}

      <div className="flex between center-y wrap gap-md" style={{ marginBottom: 18 }}>
        <div className="flex gap-md center-y wrap">
          <h2 className="mono" style={{ fontSize: 19 }}>
            {detail.ticket.ticket_id}
          </h2>
          {c && <span className="badge badge-neutral">{COMPLAINT_TYPE_LABEL[c.type]}</span>}
          {c && <span className="badge badge-neutral">{SCOPE_LABEL[c.scope]}</span>}
          {c?.priority === "critical" && (
            <span className="badge badge-critical">
              <span className="dot dot-pulse" /> Khẩn cấp
            </span>
          )}
          <span className="badge badge-warning">{HITL_STATUS_LABEL[detail.ticket.hitl_status]}</span>
        </div>
      </div>

      {msg && <div className={`note form-msg ${msg.kind}`} style={{ marginBottom: 18 }}>{msg.text}</div>}

      <div className="grid grid-2" style={{ alignItems: "start" }}>
        <div className="flex-col gap-lg">
          <div className="card">
            <div className="card-title">Investigation trail</div>
            <div className="card-sub" style={{ marginBottom: 14 }}>
              Mỗi bước: tool đã gọi, input, kết quả, ghi chú AI, thời gian.
            </div>
            {detail.investigation_logs.length === 0 ? (
              <div className="note">
                Chưa có bước điều tra nào được ghi nhận cho ticket này — AI agent chưa xử lý case này
                (agent đang được xây, xem FIN05-Backend-Handoff.md §4.2).
              </div>
            ) : (
              <div className="trail">
                {detail.investigation_logs.map((log) => (
                  <div className="trail-step" key={log.step_no}>
                    <span className="trail-tool">{log.tool_called}()</span>
                    <div className="trail-io">
                      {"input: " + JSON.stringify(log.tool_input)}
                      {"\nkết quả: " + JSON.stringify(log.tool_result)}
                    </div>
                    {log.agent_note && <div className="trail-note">{log.agent_note}</div>}
                    <div className="trail-time">{formatDateTime(log.created_at)}</div>
                  </div>
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
                Tín hiệu định tuyến — KHÔNG PHẢI kết luận gian lận
              </div>
              <div className="flex gap-sm wrap" style={{ marginTop: 10 }}>
                {c.fraud_signals.map((s) => (
                  <span className="badge badge-warning mono" key={s}>
                    {s}
                  </span>
                ))}
              </div>
              <div className="note" style={{ marginTop: 12 }}>
                <b>FS-06</b> (rút sạch sau bất thường xác thực) kích hoạt escalate ngay khi bật — phạm vi
                MVP chỉ dùng tín hiệu này (PRD §5). Gắn cờ <b>không</b> tự động khoá ví.
              </div>
            </div>
          )}
        </div>

        <div className="flex-col gap-lg">
          {detail.ticket.human_handoff_requested && (viewerRole === "cskh" || viewerRole === "supervisor") && (
            <LiveChatPanel ticketId={detail.ticket.ticket_id} viewerRole={viewerRole} viewerUserId={viewerUserId} />
          )}
          <div className="card">
            <div className="card-title">Thông tin giao dịch</div>
            {!c?.trans_id && <div className="dim" style={{ fontSize: 13 }}>Khách không tra ra được giao dịch (case not_found).</div>}
            {c?.trans_id && !tx && <div className="dim" style={{ fontSize: 13 }}>Đang tra cứu…</div>}
            {tx && "status" in tx && tx.status === "not_found" && (
              <div className="dim" style={{ fontSize: 13 }}>Không tìm thấy giao dịch {c?.trans_id}.</div>
            )}
            {foundTx && (
              <>
                <div className="kv-row"><span className="k">Mã giao dịch</span><span className="v mono">{foundTx.trans_id}</span></div>
                <div className="kv-row"><span className="k">Số tiền</span><span className="v mono">{formatMoney(foundTx.amount)}</span></div>
                <div className="kv-row"><span className="k">Trạng thái</span><span className="v"><span className="badge badge-info">{foundTx.status}</span></span></div>
                <div className="kv-row">
                  <span className="k">Người nhận</span>
                  <span className="v masked">
                    <svg className="icon icon-sm" viewBox="0 0 24 24"><path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z" /><circle cx="12" cy="12" r="3" /></svg>
                    {foundTx.receiver?.full_name ?? "—"} {foundTx.receiver?.phone ?? foundTx.receiver?.account_no ?? ""}
                  </span>
                </div>
                <div className="note" style={{ marginTop: 10, fontSize: 11 }}>
                  Đã che một phần theo PDPA (NĐ 13/2023/NĐ-CP) — US-016.
                </div>
              </>
            )}
          </div>

          {c && c.scope !== "internal_wallet" && viewerRole === "cskh" && (
            <div className="card">
              <div className="card-title">Tra soát ngân hàng đối tác</div>
              <div className="card-sub" style={{ marginBottom: 12 }}>
                Case chạm ngân hàng — chỉ có nút tạo yêu cầu tra soát, không có nút duyệt hoàn tiền trực tiếp.
              </div>
              {detail.escalations.filter((e) => e.target === "partner_bank").length > 0 ? (
                <div className="note">Đã gửi yêu cầu tra soát — xem trạng thái ở SLA/partner_wait_status.</div>
              ) : (
                <form onSubmit={handleBankEscalate}>
                  <div className="field" style={{ marginTop: 0 }}>
                    <label>Lý do tra soát</label>
                    <input value={bankReason} onChange={(e) => setBankReason(e.target.value)} required />
                  </div>
                  <button className="btn btn-outline btn-sm" style={{ marginTop: 14 }} type="submit">
                    Gửi yêu cầu tra soát
                  </button>
                </form>
              )}
            </div>
          )}

          {viewerRole === "cskh" ? (
            <div className="card">
              <div className="card-title">Hành động của bạn (CSKH)</div>
              <div className="card-sub" style={{ marginBottom: 14 }}>
                Không có đường nào để tự duyệt hoàn tiền (US-012, US-015).
              </div>
              <form onSubmit={handlePropose}>
                <div className="field" style={{ marginTop: 0 }}>
                  <label>Hướng xử lý đề xuất</label>
                  <select value={actionType} onChange={(e) => setActionType(e.target.value)}>
                    {ACTION_TYPES.map((a) => (
                      <option key={a.value} value={a.value}>{a.label}</option>
                    ))}
                  </select>
                </div>
                <div className="field">
                  <label>Số tiền (nếu có)</label>
                  <input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} />
                </div>
                <div className="field">
                  <label>Căn cứ</label>
                  <textarea rows={2} value={rationale} onChange={(e) => setRationale(e.target.value)} required />
                </div>
                <div className="flex gap-sm wrap" style={{ marginTop: 14 }}>
                  <button className="btn btn-gold" type="submit" disabled={submitting}>
                    Trình sếp
                  </button>
                  <button className="btn btn-outline" type="button" onClick={handleRequestMoreInfo}>
                    Yêu cầu điều tra thêm
                  </button>
                  <span className="tooltip-wrap" data-tooltip="Ngoài thẩm quyền của bạn — chỉ Sếp mới có quyền duyệt hoàn tiền (US-015).">
                    <button className="btn btn-outline" disabled type="button" style={{ borderColor: "var(--border-strong)", color: "var(--text-faint)" }}>
                      Duyệt hoàn tiền
                    </button>
                  </span>
                </div>
              </form>
            </div>
          ) : (
            <div className="note">
              Bạn đang xem với vai trò Sếp — phê duyệt/từ chối đề xuất thực hiện ở trang <b>Phê duyệt</b>,
              không thao tác trực tiếp ở đây.
            </div>
          )}

          {detail.resolutions.length > 0 && (
            <div className="card">
              <div className="card-title">Đề xuất đã trình</div>
              {detail.resolutions.map((r) => (
                <div className="kv-row" key={r.resolution_id}>
                  <span className="k">{r.action_type}{r.amount ? ` — ${formatMoney(r.amount)}` : ""}</span>
                  <span className="v"><span className="badge badge-info">{r.status}</span></span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
