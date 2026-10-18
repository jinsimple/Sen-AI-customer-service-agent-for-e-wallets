// UI-01 — turns the raw JSON payload of one investigation step into readable label/value rows for
// CSKH agents and approving supervisors.
//
// THIS IS A FORMATTING LAYER, NOT AN INTERPRETATION LAYER (hard constraint 3).
// Every displayed value is the ORIGINAL value reformatted — nothing inferred, rounded or summarised.
// Labels come from the STATIC maps below (Vietnamese + English), never generated, never via an LLM.
// The approver must be able to match every number on screen against the raw payload in the expander.

import type { Lang } from "./i18n/core";
import { formatDateTime, formatMoney } from "./format";

// Field labels. A field missing from the map SHOWS ITS RAW NAME (see `nhanCuaField`) — better to
// expose a technical name than to hide data from the approver.
export const FIELD_LABEL: Record<string, string> = {
  // identifiers
  user_id: "Khách hàng",
  trans_id: "Mã giao dịch",
  ticket_id: "Mã hồ sơ",
  complaint_id: "Mã khiếu nại",
  rec_code: "Mã biên lai",
  tool_result_id: "Mã kết quả tra cứu",
  // money + time
  amount: "Số tiền",
  fee: "Phí",
  balance_after: "Số dư sau",
  created_at: "Thời điểm",
  completed_at: "Hoàn tất lúc",
  date_from: "Từ ngày",
  date_to: "Đến ngày",
  days: "Số ngày tra cứu",
  // status / classification
  status: "Trạng thái",
  scope: "Phạm vi",
  type: "Loại khiếu nại",
  complaint_type: "Loại khiếu nại",
  priority: "Mức ưu tiên",
  kyc_level: "Mức xác thực KYC",
  direction: "Chiều giao dịch",
  // parties
  phone: "Số điện thoại",
  full_name: "Họ tên",
  sender: "Người gửi",
  receiver: "Người nhận",
  account_no: "Số tài khoản",
  bank_code: "Ngân hàng",
  wallet_id: "Ví",
  wallets: "Ví của khách",
  balance: "Số dư",
  bank_accounts: "Tài khoản ngân hàng",
  des: "Nội dung chuyển khoản",
  // other
  description_raw: "Mô tả khách cung cấp",
  otp_disclosed: "Khách đã lộ OTP",
  fraud_signals: "Tín hiệu nghi vấn",
  limit_transactions: "Giới hạn số giao dịch",
  query: "Nội dung tra cứu",
  message: "Thông báo",
  results: "Kết quả",
  transaction: "Giao dịch",
  transactions: "Danh sách giao dịch",
  amount_match: "Đối chiếu số tiền",
  candidates: "Các giao dịch trùng khớp",
};

export const FIELD_LABEL_EN: Record<string, string> = {
  user_id: "Customer",
  trans_id: "Transaction ID",
  ticket_id: "Case ID",
  complaint_id: "Complaint ID",
  rec_code: "Receipt code",
  tool_result_id: "Lookup result ID",
  amount: "Amount",
  fee: "Fee",
  balance_after: "Balance after",
  created_at: "Time",
  completed_at: "Completed at",
  date_from: "From",
  date_to: "To",
  days: "Days searched",
  status: "Status",
  scope: "Scope",
  type: "Complaint type",
  complaint_type: "Complaint type",
  priority: "Priority",
  kyc_level: "KYC level",
  direction: "Direction",
  phone: "Phone number",
  full_name: "Full name",
  sender: "Sender",
  receiver: "Recipient",
  account_no: "Account number",
  bank_code: "Bank",
  wallet_id: "Wallet",
  wallets: "Customer's wallets",
  balance: "Balance",
  bank_accounts: "Bank accounts",
  des: "Transfer note",
  description_raw: "Customer's description",
  otp_disclosed: "Customer disclosed an OTP",
  fraud_signals: "Suspicion signals",
  limit_transactions: "Transaction limit",
  query: "Search query",
  message: "Message",
  results: "Results",
  transaction: "Transaction",
  transactions: "Transactions",
  amount_match: "Amount match",
  candidates: "Matching transactions",
};

const TEXT = {
  vi: { notFound: "Không tra được dữ liệu", empty: "(để trống)", none: "(không có)", items: "mục", yes: "Có", no: "Không" },
  en: { notFound: "Data not available", empty: "(empty)", none: "(none)", items: "items", yes: "Yes", no: "No" },
} as const;

export function nhanCuaField(key: string, lang: Lang = "vi"): string {
  return (lang === "en" ? FIELD_LABEL_EN[key] : FIELD_LABEL[key]) ?? key;
}

// Which fields are MONEY — formatted as currency. An explicit list rather than a guess by name:
// guessing "any big number is money" would turn `kyc_level` or `days` into "2đ"/"90đ", i.e. the
// formatting layer inventing meaning it doesn't have.
const FIELD_TIEN = new Set(["amount", "fee", "balance", "balance_after", "amount_vnd", "refund_amount"]);
const FIELD_THOI_GIAN = new Set(["created_at", "completed_at", "date_from", "date_to", "claimed_at", "updated_at"]);

/** One row ready for display. `nhan` (label) may be empty for array elements. */
export type DongHienThi = { nhan: string; giaTri: string; sau: number };

function laChuoiNgay(v: string): boolean {
  // Only recognise unambiguous ISO strings. DON'T use `new Date(v)` to guess, because it swallows
  // strings that aren't dates and yields a wrong date — the formatting layer fabricating data,
  // exactly what hard constraint 3 forbids.
  return /^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}/.test(v);
}

function moTaGiaTri(key: string, v: unknown, lang: Lang): string {
  const tx = TEXT[lang];
  if (v === null || v === undefined) return tx.notFound;
  if (typeof v === "boolean") return v ? tx.yes : tx.no;
  if (typeof v === "number") {
    return FIELD_TIEN.has(key) ? formatMoney(v, lang) : v.toLocaleString(lang === "en" ? "en-US" : "vi-VN");
  }
  if (typeof v === "string") {
    if (v === "") return tx.empty;
    // Values ALREADY MASKED at the data layer (`038***`, `****0001`) are shown AS IS — the display
    // layer must never "prettify" away the masking.
    if (FIELD_THOI_GIAN.has(key) || laChuoiNgay(v)) return formatDateTime(v, lang);
    return v;
  }
  return "";
}

/**
 * Flatten a payload into label/value rows, recursing into nested objects/arrays.
 *
 * `sau` = depth, for the component's indentation. Capped at 3 levels: anything deeper is flattened
 * into one JSON row — readers can't follow a 4-level tree on screen, and the full version stays in
 * the "technical data" expander.
 */
export function traiPayload(v: unknown, sau = 0, key = "", lang: Lang = "vi"): DongHienThi[] {
  const tx = TEXT[lang];
  const label = (k: string) => nhanCuaField(k, lang);
  if (v === null || v === undefined) {
    return [{ nhan: label(key), giaTri: tx.notFound, sau }];
  }
  if (Array.isArray(v)) {
    if (v.length === 0) return [{ nhan: label(key), giaTri: tx.none, sau }];
    if (sau >= 3) return [{ nhan: label(key), giaTri: JSON.stringify(v), sau }];
    const ra: DongHienThi[] = [{ nhan: label(key), giaTri: `${v.length} ${tx.items}`, sau }];
    v.forEach((phanTu, i) => {
      if (typeof phanTu === "object" && phanTu !== null) {
        ra.push({ nhan: `#${i + 1}`, giaTri: "", sau: sau + 1 });
        ra.push(...traiPayload(phanTu, sau + 2, "", lang));
      } else {
        ra.push({ nhan: `#${i + 1}`, giaTri: moTaGiaTri(key, phanTu, lang), sau: sau + 1 });
      }
    });
    return ra;
  }
  if (typeof v === "object") {
    if (sau >= 3) return [{ nhan: label(key), giaTri: JSON.stringify(v), sau }];
    const ra: DongHienThi[] = [];
    if (key) ra.push({ nhan: label(key), giaTri: "", sau });
    for (const [k, giaTri] of Object.entries(v as Record<string, unknown>)) {
      if (typeof giaTri === "object" && giaTri !== null) {
        ra.push(...traiPayload(giaTri, key ? sau + 1 : sau, k, lang));
      } else {
        ra.push({ nhan: label(k), giaTri: moTaGiaTri(k, giaTri, lang), sau: key ? sau + 1 : sau });
      }
    }
    return ra;
  }
  return [{ nhan: label(key), giaTri: moTaGiaTri(key, v, lang), sau }];
}
