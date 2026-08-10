// Khớp response thật của src/api/schemas.py + src/api/main.py (backend FastAPI).

export type ComplaintType = "wrong_recipient" | "money_not_received" | "double_charge" | "refund";
export type Scope = "internal_wallet" | "from_bank" | "to_bank";
export type Priority = "low" | "normal" | "high" | "critical";
export type HitlStatus = "pending" | "approved" | "rejected" | "need_more_info";
export type PartnerWaitStatus = "n/a" | "waiting" | "overdue" | "responded";
export type ResolutionStatus = "draft" | "pending_approval" | "approved" | "rejected";

export interface MaskedParty {
  kind: "wallet" | "bank_account";
  wallet_id?: string;
  bank_account_id?: string;
  bank_code?: string;
  account_no?: string;
  phone?: string;
  full_name?: string;
}

export interface TransactionFound {
  status: "found";
  transaction: {
    trans_id: string;
    rec_code: string;
    amount: number;
    fee: number;
    status: string;
    scope: Scope;
    channel: string;
    created_at: string;
    completed_at: string | null;
    des: string | null;
    sender: MaskedParty | null;
    receiver: MaskedParty | null;
  };
  tool_result_id: string;
}

export interface TransactionNotFound {
  status: "not_found";
  tool_result_id: string;
}

export interface TransactionMultiple {
  status: "multiple_matches";
  candidates: unknown[];
  tool_result_id: string;
}

export type LookupTransactionResult = TransactionFound | TransactionNotFound | TransactionMultiple;

export interface CreateTicketResult {
  complaint_id: string;
  ticket_id: string;
  priority: Priority;
  sla_due_at: string;
  should_escalate: boolean;
  escalation_target: string | null;
  tool_result_id: string;
}

export interface TicketSummary {
  ticket_id: string;
  complaint_id: string;
  hitl_status: HitlStatus;
  sla_due_at: string;
  partner_wait_status: PartnerWaitStatus;
  created_at: string;
  complaint_type: ComplaintType | null;
  scope: Scope | null;
  priority: Priority | null;
  fraud_signals: string[];
  customer_name: string | null;
}

export interface TicketDetail {
  ticket: {
    ticket_id: string;
    hitl_status: HitlStatus;
    sla_due_at: string;
    partner_wait_status: PartnerWaitStatus;
  };
  complaint: {
    complaint_id: string;
    user_id: string;
    trans_id: string | null;
    type: ComplaintType;
    scope: Scope;
    priority: Priority;
    description_raw: string;
    fraud_signals: string[];
  } | null;
  resolutions: {
    resolution_id: string;
    action_type: string;
    amount: number | null;
    status: ResolutionStatus;
    rationale: string;
  }[];
  escalations: { escalation_id: string; target: string; reason: string }[];
  investigation_logs: {
    step_no: number;
    tool_called: string;
    tool_input: Record<string, unknown> | null;
    tool_result_id: string | null;
    tool_result: Record<string, unknown> | null;
    agent_note: string | null;
    created_at: string;
  }[];
}

export interface ResolutionListItem {
  resolution_id: string;
  ticket_id: string;
  action_type: string;
  amount: number | null;
  destination_ref: string | null;
  rationale: string;
  cited_tool_result_ids: string[];
  status: ResolutionStatus;
  created_at: string;
  complaint_type: ComplaintType | null;
  scope: Scope | null;
  approved_by_name: string | null;
  approved_at: string | null;
}

export interface ReportSummary {
  date_from: string | null;
  date_to: string | null;
  total_tickets: number;
  avg_processing_hours: number | null;
  pct_ai_proposal_approved: number | null;
  pct_escalated: number | null;
  by_complaint_type: Record<string, number>;
  by_scope: Record<string, number>;
}

export const COMPLAINT_TYPE_LABEL: Record<ComplaintType, string> = {
  wrong_recipient: "Chuyển nhầm",
  money_not_received: "Tiền chưa về",
  double_charge: "Trừ tiền 2 lần",
  refund: "Hoàn tiền",
};

export const SCOPE_LABEL: Record<Scope, string> = {
  internal_wallet: "Nội bộ ví",
  from_bank: "Từ ngân hàng",
  to_bank: "Ra ngân hàng",
};

export interface CustomerHistory {
  user_id: string;
  kyc_level: number;
  wallets: { wallet_id: string; balance: number; status: string }[];
  recent_transactions: {
    trans_id: string;
    amount: number;
    status: string;
    scope: Scope;
    created_at: string;
    direction: "in" | "out";
  }[];
  complaint_count_90d: number;
  complaints: { complaint_id: string; type: ComplaintType; status: string; created_at: string }[];
  tool_result_id: string;
}

export const HITL_STATUS_LABEL: Record<HitlStatus, string> = {
  pending: "Chờ CSKH tiếp nhận",
  approved: "Đã duyệt",
  rejected: "Đã từ chối",
  need_more_info: "Cần điều tra thêm",
};

export interface AgentToolCall {
  tool_name: string;
  args: Record<string, unknown>;
  result: Record<string, unknown>;
}

export interface AgentChatResult {
  reply: string;
  tool_calls: AgentToolCall[];
  ticket_id: string | null;
  should_escalate: boolean | null;
}

export type PolicyDocumentStatus = "processing" | "indexed" | "failed";

export interface PolicyDocument {
  doc_id: string;
  filename: string;
  uploaded_at: string;
  uploaded_by_name: string | null;
  status: PolicyDocumentStatus;
  chunk_count: number;
  error_message: string | null;
}

export interface PolicySearchResultItem {
  text: string;
  source_filename: string;
  doc_id: string;
}

export interface PolicySearchResult {
  status: "found" | "not_found";
  results: PolicySearchResultItem[];
  tool_result_id: string;
}
