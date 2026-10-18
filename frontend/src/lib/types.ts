// Matches the real response shape of src/api/schemas.py + src/api/main.py (the FastAPI backend).

// "other" (CTRL-001, 2026-08-11) — the customer asks for a human without a description matching one
// of the 4 specific transaction-complaint types.
export type ComplaintType = "wrong_recipient" | "money_not_received" | "double_charge" | "refund" | "other";
// "unknown" — VALID_SCOPES (create_ticket.py) allows it; the customer couldn't be determined after
// CLARIFY_QUESTION_MAX_ROUNDS + 1 scope question (2026-08-11). Missing this branch used to make
// SCOPE_LABEL[scope] return `undefined`, rendering the badge EMPTY (no console error, just silently
// missing text) — caught by inspecting a screenshot of the notification panel during the Sep 4
// polish, not a NEW bug from this round.
export type Scope = "internal_wallet" | "from_bank" | "to_bank" | "unknown";
export type Priority = "low" | "normal" | "high" | "critical";
export type HitlStatus = "pending" | "approved" | "rejected" | "need_more_info";
export type PartnerWaitStatus = "n/a" | "waiting" | "overdue" | "responded";
export type ResolutionStatus = "draft" | "pending_approval" | "approved" | "rejected";
// Matches the CHECK constraint ck_resolutions_action_type + the resolution-state-machine.yaml
// contract. A union (not a string) so the label table below is forced to cover every value —
// missing one is a build-time error.
export type ActionType =
  | "refund_to_wallet"
  | "refund_to_bank"
  | "ledger_adjustment"
  | "no_action"
  | "manual_review";
// The six values REALLY present in the transactions table (counted from the DB, Aug 14).
export type TransactionStatus =
  | "success"
  | "processing"
  | "pending"
  | "failed"
  | "refunded"
  | "on_hold";

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
  human_handoff_requested: boolean;
  // ADR-064(b) — null = still in the pool (support agents see the "Claim" button). A value: for a
  // support agent it is ALWAYS themselves (the backend already filters), for a supervisor it can be
  // anyone (that route doesn't filter).
  claimed_by: string | null;
}

// [polish before the Sep 4 shoot] GET /tickets switched from a bare array to real pagination —
// `total` is the total number of tickets MATCHING the current filter (not the system-wide total),
// used to compute the page count.
export interface TicketPageResponse {
  items: TicketSummary[];
  total: number;
  page: number;
  page_size: number;
}

export type TicketPageSize = 30 | 50 | 100;

export interface TicketListFilters {
  hitl_status?: HitlStatus;
  complaint_type?: ComplaintType;
  scope?: Scope;
  priority?: Priority;
  sla_before?: string;
  sla_after?: string;
}

export interface TicketDetail {
  ticket: {
    ticket_id: string;
    hitl_status: HitlStatus;
    sla_due_at: string;
    partner_wait_status: PartnerWaitStatus;
    human_handoff_requested: boolean;
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
    action_type: ActionType;
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

// ADR-044 — GET /tickets/{ticket_id}/transcript. `transcript`/`chi_so_bang_giao` travel TOGETHER:
// null when it can't be looked up (with a `ly_do`), an array when it can. The UI uses
// `chi_so_bang_giao` to draw the divider RIGHT AFTER that turn (0-based, null = the conversation
// never called request_human_handoff — no divider).
export interface TicketTranscript {
  transcript: { vai: "khach" | "bot"; noi_dung: string; co_goi_tool: boolean }[] | null;
  ly_do: string | null;
  handoff_at: string | null;
  chi_so_bang_giao: number | null;
}

export interface ResolutionListItem {
  resolution_id: string;
  ticket_id: string;
  action_type: ActionType;
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

// B1-B3 (Aug 20) — every % MUST come with its denominator (n): "0.4%" on a denominator of 3 states
// nothing; the viewer has no way to know unless they see n. AHT (actual HUMAN handling time) is
// DIFFERENT from avg_processing_hours (cycle time, which includes waiting time) — the DB has no
// "work started" timestamp yet, so `aht_hours` is always null, with an explicit reason attached
// instead of being left blank (a blank gets read as 0).
export interface ReportSummary {
  date_from: string | null;
  date_to: string | null;
  total_tickets: number;
  avg_processing_hours: number | null;
  avg_processing_hours_n: number;
  aht_hours: number | null;
  aht_khong_do_duoc_ly_do: string;
  pct_ai_proposal_approved: number | null;
  pct_ai_proposal_approved_numerator: number;
  pct_ai_proposal_approved_n: number;
  pct_escalated: number | null;
  pct_escalated_numerator: number;
  pct_escalated_n: number;
  by_complaint_type: Record<string, number>;
  by_scope: Record<string, number>;
}

export const COMPLAINT_TYPE_LABEL: Record<ComplaintType, string> = {
  wrong_recipient: "Chuyển nhầm",
  money_not_received: "Tiền chưa về",
  double_charge: "Trừ tiền 2 lần",
  refund: "Hoàn tiền",
  other: "Khác (yêu cầu hỗ trợ chung)",
};

export const SCOPE_LABEL: Record<Scope, string> = {
  internal_wallet: "Nội bộ ví",
  from_bank: "Từ ngân hàng",
  to_bank: "Ra ngân hàng",
  unknown: "Chưa xác định",
};

export const PRIORITY_LABEL: Record<Priority, string> = {
  low: "Thấp",
  normal: "Bình thường",
  high: "Cao",
  critical: "Khẩn cấp",
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

// Display labels (Aug 14). THREE PRINCIPLES, don't break them:
//  - Translate ONLY at the display layer. Values sent/received over the API and stored in the DB
//    stay the original English strings — guarded by a CHECK constraint + INV-12.
//  - `action_type`/`status` labels are copied from `mo_ta` in
//    contracts/resolution-state-machine.yaml, never made up.
//  - `Record<Union, string>` is deliberate: adding a new value to the union while forgetting its
//    label is a TypeScript build-time error, not a silent UI bug.
export const RESOLUTION_STATUS_LABEL: Record<ResolutionStatus, string> = {
  draft: "Nháp — chưa trình",
  // The opening clause of the contract's `mo_ta` ("Submitted, awaiting supervisor approval. A
  // MANDATORY GATE before any money-touching action.") — shortened to fit a badge, not a label
  // invented from scratch.
  pending_approval: "Chờ sếp duyệt",
  approved: "Sếp đã duyệt",
  rejected: "Sếp từ chối",
};

export const ACTION_TYPE_LABEL: Record<ActionType, string> = {
  refund_to_wallet: "Hoàn tiền về ví",
  refund_to_bank: "Hoàn tiền về tài khoản ngân hàng",
  ledger_adjustment: "Điều chỉnh sổ cái",
  no_action: "Không hành động (khiếu nại không có cơ sở)",
  manual_review: "Cần người xem xét thủ công thêm",
};

// A transaction status NOT in the contract — the labels below are the tech lead's proposal, pending
// PO approval before merging in round 2. The six values come from REAL data in the DB, not from
// memory: success · processing · failed · refunded · pending · on_hold.
export const TX_STATUS_LABEL: Record<TransactionStatus, string> = {
  success: "Thành công",
  processing: "Đang xử lý",
  pending: "Chờ xử lý",
  failed: "Thất bại",
  refunded: "Đã hoàn tiền",
  on_hold: "Đang tạm giữ",
};

// Tool names in the Investigation trail. `Record<string, string>` (NOT a union) is deliberate: the
// tool list is decided by the backend (contracts/agent-tools.yaml); a new tool shows up and the
// trail still displays its raw technical name instead of breaking the build or rendering empty —
// call sites use `?? log.tool_called`.
export const TOOL_NAME_LABEL: Record<string, string> = {
  lookup_transaction: "Tra cứu giao dịch",
  get_customer_history: "Tra cứu lịch sử khách",
  create_ticket: "Tạo hồ sơ khiếu nại",
  search_policy: "Tra cứu chính sách",
  request_human_handoff: "Yêu cầu gặp nhân viên",
  propose_resolution: "Đề xuất hướng xử lý",
  escalate_ticket: "Chuyển cấp xử lý",
};

// ADR-019 — labels taken exactly from `mo_ta` in contract v2.1.0, never invented. Order: the 4
// values with `la_tin_hieu_hoc=true` (a fault of the proposal) come first, then the non-fault group
// — so the supervisor sees the most commonly used group at the top.
export type RejectReason =
  | "sai_so_lieu"
  | "sai_phan_loai"
  | "thieu_can_cu"
  | "sai_chinh_sach"
  | "trung_case"
  | "khach_rut"
  | "khac";

export const REJECT_REASON_LABEL: Record<RejectReason, string> = {
  sai_so_lieu: "Sai số liệu (số tiền/mã giao dịch/thời điểm không khớp)",
  sai_phan_loai: "Sai phân loại (loại khiếu nại hoặc phạm vi giao dịch)",
  thieu_can_cu: "Thiếu căn cứ, không thể bổ sung",
  sai_chinh_sach: "Trái quy định/chính sách hiện hành",
  trung_case: "Trùng — đã xử lý ở ticket khác",
  khach_rut: "Khách rút khiếu nại",
  khac: "Lý do khác",
};

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
  // ④ (Aug 25) — the LABEL for which path a turn took, written by the backend
  // (src/agents/graph.py). The client ONLY reads the "can_otp" value: the deterministic OTP gate
  // blocked this turn before it ever reached the model.
  //
  // 🔴 WHY THIS KEY MUST EXIST, instead of reading the `reply` text: both OTP-dialog triggers
  // already in ChatClient.tsx probe `tool_calls`/`ticket_id` — and EVERY 0-token backend path
  // returns `tool_calls: []`, `ticket_id: null`. Without this key, the customer reads "please
  // verify" and nothing opens: a dead end. The same reason `loai:"otp_het_tuoi"` ("otp-expired")
  // was created in phase 2.5 — the client must never recognise state by matching a Vietnamese
  // string whose wording could change.
  //
  // Optional: older backend images don't send this field yet.
  duong?: string | null;
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
  // ADR-065 (Sep 5) — used to build the "View full text" deep-link.
  chunk_id: string;
}

// ADR-065 — GET /policy-doc/{doc_id}. `highlight` is null when the highlight position couldn't be
// determined (wrong/non-matching chunk_id, or the document has no full_text yet) — the frontend
// still shows the full text, just without highlighting/scrolling; this is not an error.
export interface PolicyDocFullText {
  doc_id: string;
  filename: string;
  full_text: string | null;
  highlight: { start: number; end: number } | null;
}

export interface PolicySearchResult {
  status: "found" | "not_found";
  results: PolicySearchResultItem[];
  tool_result_id: string;
}

// ADR-063 — the notification bell. Content is ONLY event_type + ticket_id — NO amounts/PII/phone
// numbers (hard constraint #3 + PDPA, enforced at both the backend layer and this type).
export type NotificationEventType = "ve_moi" | "cho_duyet" | "da_duyet" | "da_tu_choi";

// [polish before the Sep 4 shoot] 4 added fields — joined AT READ TIME from the existing
// Ticket/Complaint (NOT a snapshot taken at fan-out time, because priority can change AFTER the
// notification was created — e.g. `_nang_uu_tien_theo_cam_xuc` (sentiment-based
// re-prioritisation)). Still non-PII only, the same hard constraint #3 as the comment above.
export interface NotificationItem {
  notification_id: string;
  event_type: NotificationEventType;
  ticket_id: string;
  created_at: string;
  read_at: string | null;
  complaint_type: ComplaintType | null;
  scope: Scope | null;
  priority: Priority | null;
  sla_due_at: string | null;
}

export const NOTIFICATION_EVENT_LABEL: Record<NotificationEventType, string> = {
  ve_moi: "Vé mới",
  cho_duyet: "Đề xuất chờ duyệt",
  da_duyet: "Đề xuất đã được duyệt",
  da_tu_choi: "Đề xuất đã bị từ chối",
};

export interface StaffPresenceItem {
  user_id: string;
  full_name: string;
  online: boolean;
  so_ve_dang_xu_ly: number;
}

// ── English display labels (portfolio edition) ────────────────────────────────────────────────────
// Same rule as above: display layer only, wire values stay as they are. `Record<Union, string>` so a
// missing English label is a build error. Look-ups go through `labelOf(MAP, key, lang)`, which finds
// the English twin by the identity of the Vietnamese map.
export const COMPLAINT_TYPE_LABEL_EN: Record<ComplaintType, string> = {
  wrong_recipient: "Wrong recipient",
  money_not_received: "Money not received",
  double_charge: "Charged twice",
  refund: "Refund",
  other: "Other (general support request)",
};

export const SCOPE_LABEL_EN: Record<Scope, string> = {
  internal_wallet: "Wallet-to-wallet",
  from_bank: "From bank",
  to_bank: "To bank",
  unknown: "Not determined",
};

export const PRIORITY_LABEL_EN: Record<Priority, string> = {
  low: "Low",
  normal: "Normal",
  high: "High",
  critical: "Critical",
};

export const RESOLUTION_STATUS_LABEL_EN: Record<ResolutionStatus, string> = {
  draft: "Draft — not submitted",
  pending_approval: "Awaiting supervisor",
  approved: "Approved by supervisor",
  rejected: "Rejected by supervisor",
};

export const ACTION_TYPE_LABEL_EN: Record<ActionType, string> = {
  refund_to_wallet: "Refund to wallet",
  refund_to_bank: "Refund to bank account",
  ledger_adjustment: "Ledger adjustment",
  no_action: "No action (complaint unfounded)",
  manual_review: "Needs further manual review",
};

export const TX_STATUS_LABEL_EN: Record<TransactionStatus, string> = {
  success: "Successful",
  processing: "Processing",
  pending: "Pending",
  failed: "Failed",
  refunded: "Refunded",
  on_hold: "On hold",
};

export const TOOL_NAME_LABEL_EN: Record<string, string> = {
  lookup_transaction: "Look up transaction",
  get_customer_history: "Look up customer history",
  create_ticket: "Create complaint case",
  search_policy: "Search policy",
  request_human_handoff: "Request a human agent",
  propose_resolution: "Propose resolution",
  escalate_ticket: "Escalate case",
};

export const REJECT_REASON_LABEL_EN: Record<RejectReason, string> = {
  sai_so_lieu: "Wrong figures (amount/transaction ID/time don't match)",
  sai_phan_loai: "Wrong classification (complaint type or transaction scope)",
  thieu_can_cu: "Insufficient evidence, cannot be supplemented",
  sai_chinh_sach: "Contrary to current rules/policy",
  trung_case: "Duplicate — handled in another ticket",
  khach_rut: "Customer withdrew the complaint",
  khac: "Other reason",
};

export const HITL_STATUS_LABEL_EN: Record<HitlStatus, string> = {
  pending: "Awaiting support agent",
  approved: "Approved",
  rejected: "Rejected",
  need_more_info: "Needs more investigation",
};

export const NOTIFICATION_EVENT_LABEL_EN: Record<NotificationEventType, string> = {
  ve_moi: "New ticket",
  cho_duyet: "Proposal awaiting approval",
  da_duyet: "Proposal approved",
  da_tu_choi: "Proposal rejected",
};

const EN_TWIN = new Map<object, Record<string, string>>([
  [COMPLAINT_TYPE_LABEL, COMPLAINT_TYPE_LABEL_EN],
  [SCOPE_LABEL, SCOPE_LABEL_EN],
  [PRIORITY_LABEL, PRIORITY_LABEL_EN],
  [RESOLUTION_STATUS_LABEL, RESOLUTION_STATUS_LABEL_EN],
  [ACTION_TYPE_LABEL, ACTION_TYPE_LABEL_EN],
  [TX_STATUS_LABEL, TX_STATUS_LABEL_EN],
  [TOOL_NAME_LABEL, TOOL_NAME_LABEL_EN],
  [REJECT_REASON_LABEL, REJECT_REASON_LABEL_EN],
  [HITL_STATUS_LABEL, HITL_STATUS_LABEL_EN],
  [NOTIFICATION_EVENT_LABEL, NOTIFICATION_EVENT_LABEL_EN],
]);

/** Display label for `key` in `lang`. Returns undefined for unknown keys so callers keep their
 *  existing `?? rawValue` fallbacks. */
export function labelOf<K extends string>(
  map: Record<K, string>,
  key: K | string | null | undefined,
  lang: "vi" | "en" = "vi",
): string | undefined {
  if (key == null) return undefined;
  const src = lang === "en" ? EN_TWIN.get(map) ?? map : map;
  return (src as Record<string, string>)[key];
}
