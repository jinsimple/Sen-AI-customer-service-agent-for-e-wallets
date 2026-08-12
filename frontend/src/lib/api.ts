"use client";

import type {
  AgentChatResult,
  CustomerHistory,
  LookupTransactionResult,
  PolicyDocument,
  PolicySearchResult,
  ReportSummary,
  ResolutionListItem,
  TicketDetail,
  TicketSummary,
} from "@/lib/types";
import type { LiveChatContext } from "@/lib/useLiveChatSocket";

// Client Component gọi các route nội bộ /api/* (BFF, xem frontend/src/app/api/)
// — KHÔNG bao giờ gọi thẳng FastAPI. Route nội bộ đọc JWT từ cookie httpOnly
// phía server rồi mới gọi backend thật, nên trình duyệt không cần và không
// được biết địa chỉ/token của FastAPI.

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

// Timeout mặc định 60s — UX-01 (FIN05-QA-Test-Report.md): mọi hành động
// async (gửi chat, duyệt case...) phải có trần thời gian rõ ràng, KHÔNG bao
// giờ treo vô hạn (cùng gốc với BUG-01 ở trang login, nhưng request() này là
// điểm dùng chung cho agentChat/approveResolution/... nên sửa 1 chỗ áp dụng
// hết). 60s (không phải 10s như login) vì agentChat gọi LLM thật, đã đo thực
// tế có lượt cần 15-20s+ khi tải cao — timeout phải đủ rộng để không huỷ
// nhầm request đang chạy đúng, chỉ chặn trường hợp treo thật sự.
const DEFAULT_TIMEOUT_MS = 60_000;

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
      throw new ApiError(0, `Máy chủ phản hồi quá lâu (>${Math.round(timeoutMs / 1000)}s) — thử lại giúp mình nhé.`);
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      // Phòng vệ đúp: BFF (server-api.ts::backendFetch) đã chuẩn hoá lỗi 429
      // rate-limit về {"detail": ...}, nhưng vẫn giữ nhánh {"error": ...} ở
      // đây phòng trường hợp lỗi đến từ route Next.js khác chưa qua chuẩn
      // hoá đó — tránh lặp lại đúng bug đã tìm thấy (hiện JSON thô cho khách).
      detail = body.detail ?? body.error ?? JSON.stringify(body);
    } catch {
      // giữ statusText nếu body không phải JSON
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

// Upload file — KHÔNG dùng request() vì hàm đó luôn ép Content-Type:
// application/json; multipart cần fetch tự tính boundary từ FormData. Vẫn áp
// timeout riêng — file lớn/mạng chậm cũng không được treo vô hạn (UX-01).
async function uploadFile<T>(path: string, formData: FormData): Promise<T> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);
  let res: Response;
  try {
    res = await fetch(path, { method: "POST", body: formData, signal: controller.signal });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiError(0, `Máy chủ phản hồi quá lâu (>${Math.round(DEFAULT_TIMEOUT_MS / 1000)}s) — thử lại giúp mình nhé.`);
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      // Phòng vệ đúp: BFF (server-api.ts::backendFetch) đã chuẩn hoá lỗi 429
      // rate-limit về {"detail": ...}, nhưng vẫn giữ nhánh {"error": ...} ở
      // đây phòng trường hợp lỗi đến từ route Next.js khác chưa qua chuẩn
      // hoá đó — tránh lặp lại đúng bug đã tìm thấy (hiện JSON thô cho khách).
      detail = body.detail ?? body.error ?? JSON.stringify(body);
    } catch {
      // giữ statusText nếu body không phải JSON
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// /tools/* — agent/khách gọi để điều tra
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
// /agent/chat — AI agent thật (LangGraph), chỉ phục vụ role=customer
// ---------------------------------------------------------------------------

export function agentChat(params: { message: string }) {
  return post<AgentChatResult>("/api/agent-chat", params);
}

// ---------------------------------------------------------------------------
// /auth/otp/* — OTP phiên làm việc + câu hỏi bảo mật THẬT ở backend (src/
// auth.py::require_otp_verified). verifyOtp() không trả access_token về đây
// — route /api/otp/verify tự cập nhật cookie httpOnly server-side.
// ---------------------------------------------------------------------------

export function requestOtp() {
  return post<{ security_question: string; otp_code: string; note: string }>("/api/otp/request");
}

export function verifyOtp(params: { otp_code: string; security_answer: string }) {
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
// /tickets* — đọc, dùng cho UI CSKH/sếp
// ---------------------------------------------------------------------------

export function listTickets(params?: { hitl_status?: string; limit?: number }) {
  const qs = new URLSearchParams();
  if (params?.hitl_status) qs.set("hitl_status", params.hitl_status);
  if (params?.limit) qs.set("limit", String(params.limit));
  const suffix = qs.toString() ? `?${qs}` : "";
  return get<TicketSummary[]>(`/api/tickets${suffix}`);
}

export function getTicketDetail(ticketId: string) {
  return get<TicketDetail>(`/api/tickets/${ticketId}`);
}

export function requestMoreInfo(ticketId: string, params: { note?: string }) {
  return post<{ ticket_id: string; hitl_status: string }>(
    `/api/tickets/${ticketId}/request-more-info`,
    params
  );
}

// ---------------------------------------------------------------------------
// /resolutions — hàng chờ phê duyệt cho Sếp
// ---------------------------------------------------------------------------

export function listResolutions(status: string = "pending_approval") {
  return get<ResolutionListItem[]>(`/api/resolutions?status=${encodeURIComponent(status)}`);
}

export function approveResolution(resolutionId: string) {
  return post<{ resolution_id: string; status: string; approved_by: string }>(
    `/api/resolutions/${resolutionId}/approve`
  );
}

export function rejectResolution(resolutionId: string) {
  return post<{ resolution_id: string; status: string }>(`/api/resolutions/${resolutionId}/reject`);
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
// /policy-docs, /policy-search — RAG chính sách/FAQ (partner_admin quản lý,
// CSKH tra cứu, agent khách hàng dùng qua tool search_policy phía backend)
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

// ---------------------------------------------------------------------------
// /live-chat — chat 2 chiều thời gian thực với CSKH (2026-08-11), nâng cấp
// CTRL-001 (ticket-flag bất đồng bộ) lên WebSocket thật. Vé (ws_ticket) mint
// qua route BFF này rồi dùng để mở kết nối `new WebSocket(...)` TRỰC TIẾP
// (không qua BFF — xem useLiveChatSocket.ts) tới Caddy -> backend.
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
  // context (2026-08-11) — trả kèm LUÔN, kể cả phiên đã 'closed', để CSKH mở
  // lại ticket sau khi khách đã thoát chat vẫn thấy SĐT để liên hệ lại
  // (trước đây context chỉ đẩy qua WS lúc claim, phiên đã đóng không claim
  // được nữa nên không bao giờ nhận được).
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
