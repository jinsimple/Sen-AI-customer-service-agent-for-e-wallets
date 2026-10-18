"use client";

import type {
  AgentChatResult,
  CustomerHistory,
  LookupTransactionResult,
  NotificationItem,
  PolicyDocFullText,
  PolicyDocument,
  PolicySearchResult,
  RejectReason,
  ReportSummary,
  ResolutionListItem,
  StaffPresenceItem,
  TicketDetail,
  TicketListFilters,
  TicketPageResponse,
  TicketPageSize,
  TicketTranscript,
} from "@/lib/types";
import type { LiveChatContext } from "@/lib/useLiveChatSocket";
import { LAST_GATE_COOKIE, loginPathForGate } from "@/lib/session";
import { docLang, translate } from "@/lib/i18n/core";

// A Client Component calls the internal /api/* routes (BFF, see frontend/src/app/api/) — NEVER
// FastAPI directly. The internal route reads the JWT from the server-side httpOnly cookie before
// calling the real backend, so the browser doesn't need to, and must not, know FastAPI's
// address/token.

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

// Default timeout 60s — UX-01 (FIN05-QA-Test-Report.md): every async action (sending a chat
// message, approving a case...) must have a clear time cap, NEVER hang forever (same root cause as
// BUG-01 on the login page, but this request() is the shared choke point for
// agentChat/approveResolution/..., so fixing it once covers all of them). 60s (not 10s like login)
// because agentChat calls a real LLM, and turns measured in practice have taken 15-20s+ under load
// — the timeout must be generous enough not to cancel a request that's running correctly, only to
// catch a genuine hang.
const DEFAULT_TIMEOUT_MS = 60_000;

// 27/08 [measured] p-226-f0: a 401 from the BFF (server-api.ts::backendFetch, AFTER it already
// tried refreshing the token and that also failed) MOSTLY means "the session is no longer valid" —
// NEVER used for a business-logic error shaped as a 200 payload (an expired/missing OTP lives
// INSIDE /api/agent-chat, see ChatClient.tsx::OTP_EXPIRED_LOAI — it has never been an HTTP 401
// status). Safe to redirect STRAIGHT to the right gate instead of leaving every page to catch the
// raw error and show it verbatim to the customer (the exact root cause the PO reported: "chatting
// with the chat bot shows an error — logging out and back in fixes it", because nothing used to
// clean up a dead cookie or redirect on its own; only the Logout button did that).
//
// ✅ [27/08] AN EXCEPTION THAT DISAPPEARED AT THE ROOT, not one handled more cleanly.
// `/auth/otp/verify` used to return 401 for a WRONG OTP CODE — going through the same
// `backendFetch`, it stayed 401 after a refresh (the refresh SUCCEEDED because the token was still
// alive; the new OTP code was what was wrong) ⟹ a customer who mistyped six digits got kicked to
// /login, losing an otherwise-live session. There was no structured field to key off, so the first
// patch had to MATCH THE STRING — against the project's own stated principle in ChatClient.tsx
// ("prefer status, a STRONG signal that's part of the HTTP contract, over matching wording"). The
// backend now returns 400 for that case (main.py, "Incorrect OTP code") ⟹ 401 again has EXACTLY ONE
// meaning across every route: the session can no longer be used.
// 🔴 DON'T add another exception here. If a new route returns 401 for an error that is NOT "the
// session died", fix THAT ROUTE — don't teach this function another special case. An exception at
// this layer is cheap to write and expensive forever after: it turns a read-and-understand rule
// into a look-it-up-in-a-list rule.

function dieuHuongKhiHetPhien() {
  if (typeof document === "undefined") return;
  const match = document.cookie.match(new RegExp(`(?:^|; )${LAST_GATE_COOKIE}=([^;]*)`));
  const goiY = match ? decodeURIComponent(match[1]) : undefined;
  window.location.href = loginPathForGate(goiY);
}

const phienHetHanMessage = () => translate(docLang(), "err.sessionExpired");

async function request<T>(path: string, init?: RequestInit & { timeoutMs?: number }): Promise<T> {
  const { timeoutMs = DEFAULT_TIMEOUT_MS, ...fetchInit } = init ?? {};
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  let res: Response;
  try {
    res = await fetch(path, {
      ...fetchInit,
      headers: { "Content-Type": "application/json", ...(fetchInit.headers ?? {}) },
      signal: controller.signal,
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiError(0, translate(docLang(), "err.timeout", { s: Math.round(timeoutMs / 1000) }));
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      // Double defence: the BFF (server-api.ts::backendFetch) already normalises a 429 rate-limit
      // error into {"detail": ...}, but the {"error": ...} branch is kept here in case an error
      // arrives from a different Next.js route that hasn't gone through that normalisation — to
      // avoid repeating exactly the bug already found (showing raw JSON to the customer).
      detail = body.detail ?? body.error ?? JSON.stringify(body);
    } catch {
      // giữ statusText nếu body không phải JSON
    }
    if (res.status === 401) {
      dieuHuongKhiHetPhien();
      throw new ApiError(401, phienHetHanMessage());
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

function get<T>(path: string): Promise<T> {
  return request<T>(path, { method: "GET" });
}

function post<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined });
}

function del<T>(path: string): Promise<T> {
  return request<T>(path, { method: "DELETE" });
}

// File upload — doesn't use request() because that function always forces Content-Type:
// application/json; multipart needs fetch to compute its own boundary from FormData. Still applies
// its own timeout — a large file/slow network must not hang forever either (UX-01).
async function uploadFile<T>(path: string, formData: FormData): Promise<T> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);
  let res: Response;
  try {
    res = await fetch(path, { method: "POST", body: formData, signal: controller.signal });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiError(0, translate(docLang(), "err.timeout", { s: Math.round(DEFAULT_TIMEOUT_MS / 1000) }));
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      // Double defence: the BFF (server-api.ts::backendFetch) already normalises a 429 rate-limit
      // error into {"detail": ...}, but the {"error": ...} branch is kept here in case an error
      // arrives from a different Next.js route that hasn't gone through that normalisation — to
      // avoid repeating exactly the bug already found (showing raw JSON to the customer).
      detail = body.detail ?? body.error ?? JSON.stringify(body);
    } catch {
      // giữ statusText nếu body không phải JSON
    }
    if (res.status === 401) {
      dieuHuongKhiHetPhien();
      throw new ApiError(401, phienHetHanMessage());
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// /tools/* — called by the agent/customer for investigation
// ---------------------------------------------------------------------------

export function lookupTransaction(params: {
  trans_id?: string;
  rec_code?: string;
  phone?: string;
  amount?: number;
}) {
  return post<LookupTransactionResult>("/api/tools/lookup-transaction", params);
}

export function getCustomerHistory(params: { days?: number; limit_transactions?: number }) {
  return post<CustomerHistory>("/api/tools/customer-history", params);
}

// ---------------------------------------------------------------------------
// /agent/chat — the real AI agent (LangGraph), serves role=customer only
// ---------------------------------------------------------------------------

export function agentChat(params: { message: string; vua_xac_thuc_de_gui_lai?: boolean }) {
  return post<AgentChatResult>("/api/agent-chat", params);
}

// ---------------------------------------------------------------------------
// /auth/otp/* — the session OTP + the REAL security question on the backend
// (src/auth.py::require_otp_verified). verifyOtp() doesn't return access_token here — the
// /api/otp/verify route updates the httpOnly cookie server-side on its own.
// ---------------------------------------------------------------------------

export function requestOtp() {
  return post<{ session_id: string; security_question: string; otp_code: string; note: string }>(
    "/api/otp/request"
  );
}

export function verifyOtp(params: { session_id: string; otp_code: string }) {
  return post<{ ok: true; otp_verified: boolean }>("/api/otp/verify", params);
}

export function proposeResolution(params: {
  ticket_id: string;
  action_type: string;
  rationale: string;
  amount?: number | null;
  destination_ref?: string | null;
  cited_tool_result_ids?: string[];
}) {
  return post<{ resolution_id: string; status: string; tool_result_id: string }>(
    "/api/tools/propose-resolution",
    params
  );
}

export function escalateTicket(params: { ticket_id: string; target: string; reason: string }) {
  return post<{ escalation_id: string; tool_result_id: string }>(
    "/api/tools/escalate-ticket",
    params
  );
}

// ---------------------------------------------------------------------------
// /tickets* — reads, used by the support/supervisor UI
// ---------------------------------------------------------------------------

// [polish before the Sep 4 shoot] The old `limit` was dropped on the backend (see main.py) — real
// pagination replaces it. `page_size` is capped at 30/50/100 per the PO's decision, no arbitrary
// number accepted (the backend 422s if it's wrong, but blocking it at the type here is cheaper).
export function listTickets(
  params?: TicketListFilters & { page?: number; page_size?: TicketPageSize }
) {
  const qs = new URLSearchParams();
  if (params?.hitl_status) qs.set("hitl_status", params.hitl_status);
  if (params?.complaint_type) qs.set("complaint_type", params.complaint_type);
  if (params?.scope) qs.set("scope", params.scope);
  if (params?.priority) qs.set("priority", params.priority);
  if (params?.sla_before) qs.set("sla_before", params.sla_before);
  if (params?.sla_after) qs.set("sla_after", params.sla_after);
  qs.set("page", String(params?.page ?? 1));
  qs.set("page_size", String(params?.page_size ?? 50));
  return get<TicketPageResponse>(`/api/tickets?${qs}`);
}

export function getTicketDetail(ticketId: string) {
  return get<TicketDetail>(`/api/tickets/${ticketId}`);
}

// ADR-044 — a support agent reads the bot↔customer conversation of the ticket they're handling.
export function getTicketTranscript(ticketId: string) {
  return get<TicketTranscript>(`/api/tickets/${ticketId}/transcript`);
}

// ADR-064(b) — an active "Claim ticket", support agent ONLY (the backend 403s for any other role).
export function claimTicket(ticketId: string) {
  return post<{ ticket_id: string; claimed_by: string; claimed_at: string }>(
    `/api/tickets/${ticketId}/claim`,
    {}
  );
}

export function requestMoreInfo(ticketId: string, params: { note?: string }) {
  return post<{ ticket_id: string; hitl_status: string }>(
    `/api/tickets/${ticketId}/request-more-info`,
    params
  );
}

// ---------------------------------------------------------------------------
// /resolutions — the supervisor's approval queue
// ---------------------------------------------------------------------------

export function listResolutions(status: string = "pending_approval") {
  return get<ResolutionListItem[]>(`/api/resolutions?status=${encodeURIComponent(status)}`);
}

// AUTH5-04 (Auth Flow upgrade, 2026-08-12) — the supervisor must request a SEPARATE OTP for this
// exact resolution_id first, then approveResolution() becomes possible (bound to the exact amount
// at the moment it was requested — changing the amount afterwards forces requesting it again).
export function requestResolutionApprovalOtp(resolutionId: string) {
  return post<{ session_id: string; resolution_id: string; otp_code: string; note: string }>(
    `/api/resolutions/${resolutionId}/request-approval-otp`
  );
}

export function approveResolution(resolutionId: string, sessionId: string, otpCode: string) {
  return post<{ resolution_id: string; status: string; approved_by: string }>(
    `/api/resolutions/${resolutionId}/approve`,
    { session_id: sessionId, otp_code: otpCode }
  );
}

export function rejectResolution(resolutionId: string, reason: RejectReason) {
  // ADR-019 — `reason` is required; the backend enforces it at BOTH the schema and the CHECK
  // constraint.
  return post<{ resolution_id: string; status: string; reject_reason: string; rejected_by: string }>(
    `/api/resolutions/${resolutionId}/reject`,
    { reason }
  );
}

// ---------------------------------------------------------------------------
// /reports
// ---------------------------------------------------------------------------

export function getReportSummary(params?: { date_from?: string; date_to?: string }) {
  const qs = new URLSearchParams();
  if (params?.date_from) qs.set("date_from", params.date_from);
  if (params?.date_to) qs.set("date_to", params.date_to);
  const suffix = qs.toString() ? `?${qs}` : "";
  return get<ReportSummary>(`/api/reports-summary${suffix}`);
}

// ---------------------------------------------------------------------------
// /policy-docs, /policy-search — the policy/FAQ RAG (managed by partner_admin, looked up by support
// agents, used by the customer agent via the backend's search_policy tool)
// ---------------------------------------------------------------------------

export function listPolicyDocs() {
  return get<PolicyDocument[]>("/api/policy-docs");
}

export function uploadPolicyDoc(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return uploadFile<PolicyDocument>("/api/policy-docs", formData);
}

export function deletePolicyDoc(docId: string) {
  return del<{ doc_id: string; status: string }>(`/api/policy-docs/${docId}`);
}

export function searchPolicy(query: string) {
  return post<PolicySearchResult>("/api/policy-search", { query });
}

// ADR-065 (Sep 5) — the deep-link that reads the full text for one /policy-search result.
export function getPolicyDoc(docId: string, chunkId?: string) {
  const qs = chunkId ? `?chunk_id=${encodeURIComponent(chunkId)}` : "";
  return get<PolicyDocFullText>(`/api/policy-doc/${docId}${qs}`);
}

// ---------------------------------------------------------------------------
// /live-chat — real-time two-way chat with a support agent (2026-08-11), upgrading CTRL-001 (an
// asynchronous ticket flag) to a real WebSocket. A ticket (ws_ticket) is minted through this BFF
// route, then used to open a `new WebSocket(...)` connection DIRECTLY (not through the BFF — see
// useLiveChatSocket.ts) to Caddy -> backend.
// ---------------------------------------------------------------------------

export function requestLiveChatWsTicket(ticketId: string) {
  return post<{ ws_ticket: string; chat_session_id: string }>("/api/live-chat/ws-ticket", { ticket_id: ticketId });
}

export function requestStaffWsTicket() {
  return post<{ ws_ticket: string }>("/api/live-chat/staff-ws-ticket");
}

export function listWaitingChatSessions() {
  return get<{ sessions: { chat_session_id: string; ticket_id: string; customer_id: string; started_at: string }[] }>(
    "/api/live-chat/sessions/waiting"
  );
}

export function getChatSessionByTicket(ticketId: string) {
  // context (2026-08-11) — ALWAYS returned, even for a 'closed' session, so a support agent
  // reopening a ticket after the customer has left the chat still sees the phone number to reach
  // back out (previously, context was only pushed over the WS at claim time; a closed session can
  // no longer be claimed, so it would never be received).
  return get<{
    chat_session: { chat_session_id: string; status: string; claimed_by: string | null } | null;
    context: LiveChatContext | null;
  }>(`/api/live-chat/sessions/by-ticket/${ticketId}`);
}

export function getLiveChatMessages(chatSessionId: string) {
  return get<{ messages: { message_id: string; role: string; content: string; created_at: string }[] }>(
    `/api/live-chat/sessions/${chatSessionId}/messages`
  );
}

export function claimChatSession(chatSessionId: string) {
  return post<{ chat_session_id: string; ticket_id: string; status: string; claimed_by: string | null }>(
    `/api/live-chat/sessions/${chatSessionId}/claim`
  );
}

export function closeChatSession(chatSessionId: string) {
  return post<{ chat_session_id: string; status: string }>(`/api/live-chat/sessions/${chatSessionId}/close`);
}

export function submitChatCsat(chatSessionId: string, score: number) {
  return post<{ chat_session_id: string; csat_score: number | null }>(
    `/api/live-chat/sessions/${chatSessionId}/csat`,
    { score }
  );
}

// ADR-063 — the notification bell.
export function listNotifications() {
  return get<{ items: NotificationItem[] }>("/api/notifications");
}

export function getUnreadNotificationCount() {
  return get<{ unread_count: number }>("/api/notifications/unread-count");
}

export function markNotificationRead(notificationId: string) {
  return post<{ notification_id: string; read: boolean }>(`/api/notifications/${notificationId}/read`);
}

export function markAllNotificationsRead() {
  return post<{ marked_read: number }>("/api/notifications/read-all");
}

export function presenceHeartbeat() {
  return post<{ status: string }>("/api/presence/heartbeat");
}

export function listStaffPresence() {
  return get<{ items: StaffPresenceItem[] }>("/api/presence/staff");
}
