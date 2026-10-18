// Khớp response thật của src/api/schemas.py + src/api/main.py (backend FastAPI).

// "other" (CTRL-001, 2026-08-11) — khách yêu cầu gặp người thật không kèm
// mô tả khớp 1 trong 4 loại khiếu nại giao dịch cụ thể.
export type ComplaintType = "wrong_recipient" | "money_not_received" | "double_charge" | "refund" | "other";
// "unknown" — VALID_SCOPES (create_ticket.py) cho phép, khách không xác
// định được sau CLARIFY_QUESTION_MAX_ROUNDS + 1 câu hỏi phạm vi (2026-08-11).
// Thiếu nhánh này trước đây khiến SCOPE_LABEL[scope] trả `undefined`, badge
// render RỖNG (không lỗi console, chỉ im lặng mất chữ) — bắt được khi soi
// ảnh chụp panel thông báo đợt polish 04/09, không phải lỗi MỚI của đợt này.
export type Scope = "internal_wallet" | "from_bank" | "to_bank" | "unknown";
export type Priority = "low" | "normal" | "high" | "critical";
export type HitlStatus = "pending" | "approved" | "rejected" | "need_more_info";
export type PartnerWaitStatus = "n/a" | "waiting" | "overdue" | "responded";
export type ResolutionStatus = "draft" | "pending_approval" | "approved" | "rejected";
// Khớp CHECK constraint ck_resolutions_action_type + contract
// resolution-state-machine.yaml. Là union (không phải string) để bảng nhãn
// bên dưới bắt buộc phủ đủ — thiếu một giá trị là lỗi lúc build.
export type ActionType =
  | "refund_to_wallet"
  | "refund_to_bank"
  | "ledger_adjustment"
  | "no_action"
  | "manual_review";
// Sáu giá trị đang có THẬT trong bảng transactions (đếm từ DB 14/08).
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
  // ADR-064(b) — null = còn trong pool (CSKH thấy nút "Nhận vé"). Có giá
  // trị: với cskh LUÔN là chính mình (backend đã lọc), với supervisor có
  // thể là bất kỳ ai (route đó không lọc).
  claimed_by: string | null;
}

// [polish trước quay 04/09] GET /tickets đổi từ mảng trần sang trang có phân
// trang thật — `total` là tổng số vé KHỚP BỘ LỌC hiện tại (không phải tổng
// toàn hệ thống), dùng để tính số trang.
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

// ADR-044 — GET /tickets/{ticket_id}/transcript. `transcript`/`chi_so_bang_giao`
// đi CÙNG NHAU: null khi không tra được (kèm `ly_do`), mảng khi có. UI dùng
// `chi_so_bang_giao` để vẽ vạch phân cách NGAY SAU lượt đó (0-based, null =
// hội thoại chưa từng gọi request_human_handoff — không có vạch).
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

// B1-B3 (20/08) — mọi % PHẢI đi kèm mẫu số (n): "0,4%" trên mẫu số 3 không
// phát biểu được gì, người xem không có cách nào biết trừ khi thấy n. AHT
// (thời gian NGƯỜI thao tác) KHÁC avg_processing_hours (cycle time, gồm cả
// thời gian nằm chờ) — DB chưa có mốc bắt đầu thao tác nên `aht_hours` luôn
// null, kèm lý do tường minh thay vì để trống (trống bị đọc thành 0).
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

// Nhãn hiển thị (14/08). BA NGUYÊN TẮC, đừng phá:
//  - CHỈ dịch ở tầng hiển thị. Giá trị gửi/nhận qua API và lưu DB vẫn là
//    chuỗi tiếng Anh gốc — chúng bị CHECK constraint + INV-12 canh.
//  - Nhãn của `action_type`/`status` chép theo `mo_ta` trong
//    contracts/resolution-state-machine.yaml, KHÔNG tự sáng tác.
//  - `Record<Union, string>` cố ý: thêm giá trị mới vào union mà quên nhãn
//    là TypeScript báo lỗi lúc build, không phải lỗi âm thầm trên UI.
export const RESOLUTION_STATUS_LABEL: Record<ResolutionStatus, string> = {
  draft: "Nháp — chưa trình",
  // mệnh đề đầu của mo_ta trong contract ("Đã gửi, chờ sếp duyệt. CỔNG
  // BẮT BUỘC trước mọi hành động tiền.") — rút ngắn cho vừa badge, không
  // phải nhãn tự đặt.
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

// Trạng thái giao dịch KHÔNG có trong contract — nhãn dưới đây do tech-lead
// đề xuất, chờ PO duyệt trước khi merge đợt 2. Sáu giá trị lấy từ dữ liệu
// THẬT trong DB, không phải từ trí nhớ: success · processing · failed ·
// refunded · pending · on_hold.
export const TX_STATUS_LABEL: Record<TransactionStatus, string> = {
  success: "Thành công",
  processing: "Đang xử lý",
  pending: "Chờ xử lý",
  failed: "Thất bại",
  refunded: "Đã hoàn tiền",
  on_hold: "Đang tạm giữ",
};

// Tên tool trong Investigation trail. Record<string, string> (KHÔNG phải
// union) có chủ đích: danh sách tool do backend quyết (contracts/
// agent-tools.yaml), tool mới xuất hiện thì trail vẫn hiện tên kỹ thuật gốc
// thay vì vỡ build hay hiện rỗng — nơi gọi dùng `?? log.tool_called`.
export const TOOL_NAME_LABEL: Record<string, string> = {
  lookup_transaction: "Tra cứu giao dịch",
  get_customer_history: "Tra cứu lịch sử khách",
  create_ticket: "Tạo hồ sơ khiếu nại",
  search_policy: "Tra cứu chính sách",
  request_human_handoff: "Yêu cầu gặp nhân viên",
  propose_resolution: "Đề xuất hướng xử lý",
  escalate_ticket: "Chuyển cấp xử lý",
};

// ADR-019 — nhãn lấy đúng theo `mo_ta` trong contract v2.1.0, KHÔNG sáng tác.
// Thứ tự: 4 giá trị `la_tin_hieu_hoc=true` (lỗi của đề xuất) trước, rồi tới
// nhóm không phải lỗi — để sếp thấy nhóm hay dùng nhất lên đầu.
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
  // ④ (25/08) — NHÃN đường đi của lượt, do backend ghi (src/agents/graph.py).
  // Client CHỈ đọc giá trị "can_otp": cổng OTP tất định đã chặn lượt này trước
  // khi chạm model.
  //
  // 🔴 VÌ SAO PHẢI CÓ KHOÁ NÀY, không đọc câu chữ `reply`: hai đường kích hộp
  // thoại OTP sẵn có ở ChatClient.tsx đều dò trong `tool_calls`/`ticket_id` —
  // mà MỌI đường 0-token của backend đều trả `tool_calls: []`, `ticket_id: null`.
  // Thiếu khoá này thì khách đọc "xác thực nhé" rồi không có gì mở ra: ngõ cụt.
  // Cùng lý do `loai:"otp_het_tuoi"` ra đời ở GĐ2.5 — client không được nhận
  // diện trạng thái bằng chuỗi tiếng Việt có thể sửa văn phong.
  //
  // Optional: các ảnh backend cũ chưa gửi trường này.
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
  // ADR-065 (05/09) — dùng dựng link deep-link "Xem toàn văn".
  chunk_id: string;
}

// ADR-065 — GET /policy-doc/{doc_id}. `highlight` null khi không xác định
// được vị trí tô sáng (chunk_id sai/không khớp/tài liệu chưa có full_text) —
// FE vẫn hiện toàn văn, chỉ không tô sáng/cuộn, không phải lỗi.
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

// ADR-063 — Chuông thông báo. Nội dung CHỈ event_type + ticket_id — KHÔNG số
// tiền/PII/SĐT (ràng buộc cứng #3 + PDPA, ép ở cả tầng backend lẫn type này).
export type NotificationEventType = "ve_moi" | "cho_duyet" | "da_duyet" | "da_tu_choi";

// [polish trước quay 04/09] 4 trường thêm — join-tại-lúc-đọc từ Ticket/
// Complaint hiện có (KHÔNG snapshot lúc fan-out, vì ưu tiên có thể đổi SAU
// khi noti đã tạo — vd `_nang_uu_tien_theo_cam_xuc`). Vẫn chỉ non-PII, cùng
// ràng buộc cứng #3 như comment trên.
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
