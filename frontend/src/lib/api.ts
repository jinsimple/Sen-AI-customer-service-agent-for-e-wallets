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

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? JSON.stringify(body);
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
// application/json; multipart cần fetch tự tính boundary từ FormData.
async function uploadFile<T>(path: string, formData: FormData): Promise<T> {
  const res = await fetch(path, { method: "POST", body: formData });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? JSON.stringify(body);
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
