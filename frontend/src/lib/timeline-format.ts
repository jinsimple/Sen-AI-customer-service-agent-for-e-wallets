// UI-01 — biến payload JSON thô của một bước điều tra thành nhãn-giá-trị đọc
// được cho CSKH và sếp duyệt.
//
// ĐÂY LÀ LỚP ĐỊNH DẠNG, KHÔNG PHẢI LỚP DIỄN GIẢI (ràng buộc cứng 3).
// Mọi giá trị hiển thị là giá trị GỐC được format lại — không suy ra, không
// làm tròn, không tóm tắt. Nhãn tiếng Việt lấy từ map TĨNH dưới đây, không
// sinh động, không gọi LLM. Người duyệt phải đối chiếu được từng con số trên
// màn hình với payload gốc trong expander.

import { formatDateTime, formatMoney } from "./format";

// Nhãn field. Thiếu field nào thì HIỂN THỊ TÊN GỐC (xem `nhanCuaField`) —
// thà lộ tên kỹ thuật còn hơn giấu dữ liệu khỏi người duyệt.
export const FIELD_LABEL: Record<string, string> = {
  // định danh
  user_id: "Khách hàng",
  trans_id: "Mã giao dịch",
  ticket_id: "Mã hồ sơ",
  complaint_id: "Mã khiếu nại",
  rec_code: "Mã biên lai",
  tool_result_id: "Mã kết quả tra cứu",
  // tiền + thời gian
  amount: "Số tiền",
  fee: "Phí",
  balance_after: "Số dư sau",
  created_at: "Thời điểm",
  completed_at: "Hoàn tất lúc",
  date_from: "Từ ngày",
  date_to: "Đến ngày",
  days: "Số ngày tra cứu",
  // trạng thái / phân loại
  status: "Trạng thái",
  scope: "Phạm vi",
  type: "Loại khiếu nại",
  complaint_type: "Loại khiếu nại",
  priority: "Mức ưu tiên",
  kyc_level: "Mức xác thực KYC",
  direction: "Chiều giao dịch",
  // các bên
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
  // khác
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

export function nhanCuaField(key: string): string {
  return FIELD_LABEL[key] ?? key;
}

// Field nào là TIỀN — format theo kiểu VN. Danh sách tường minh chứ không đoán
// theo tên: đoán "cứ số lớn là tiền" sẽ biến `kyc_level` hay `days` thành
// "2đ"/"90đ", tức lớp định dạng bịa ra ngữ nghĩa nó không có.
const FIELD_TIEN = new Set(["amount", "fee", "balance", "balance_after", "amount_vnd", "refund_amount"]);
const FIELD_THOI_GIAN = new Set(["created_at", "completed_at", "date_from", "date_to", "claimed_at", "updated_at"]);

const NHAN_BOOLEAN: Record<string, string> = { true: "Có", false: "Không" };

/** Một dòng đã sẵn sàng hiển thị. `nhan` có thể rỗng cho phần tử mảng. */
export type DongHienThi = { nhan: string; giaTri: string; sau: number };

function laChuoiNgay(v: string): boolean {
  // Chỉ nhận dạng ISO rõ ràng. KHÔNG dùng `new Date(v)` để đoán, vì nó nuốt
  // cả những chuỗi không phải ngày và cho ra một ngày sai — lớp định dạng bịa
  // dữ liệu, đúng thứ ràng buộc cứng 3 cấm.
  return /^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}/.test(v);
}

function moTaGiaTri(key: string, v: unknown): string {
  if (v === null || v === undefined) return "Không tra được dữ liệu";
  if (typeof v === "boolean") return NHAN_BOOLEAN[String(v)];
  if (typeof v === "number") {
    return FIELD_TIEN.has(key) ? formatMoney(v) : v.toLocaleString("vi-VN");
  }
  if (typeof v === "string") {
    if (v === "") return "(để trống)";
    // Giá trị ĐÃ CHE ở tầng dữ liệu (`038***`, `****0001`) hiển thị NGUYÊN
    // TRẠNG — lớp hiển thị không được "làm đẹp" mất dấu che.
    if (FIELD_THOI_GIAN.has(key) || laChuoiNgay(v)) return formatDateTime(v);
    return v;
  }
  return "";
}

/**
 * Trải payload thành danh sách dòng nhãn-giá-trị, đệ quy cho object/mảng lồng.
 *
 * `sau` = độ sâu, để component thụt lề. Chặn ở 3 tầng: sâu hơn thì trải phẳng
 * thành một dòng JSON — người đọc không theo nổi cây 4 tầng trên màn hình, và
 * bản đầy đủ vẫn nằm nguyên trong expander "dữ liệu kỹ thuật".
 */
export function traiPayload(v: unknown, sau = 0, key = ""): DongHienThi[] {
  if (v === null || v === undefined) {
    return [{ nhan: nhanCuaField(key), giaTri: "Không tra được dữ liệu", sau }];
  }
  if (Array.isArray(v)) {
    if (v.length === 0) return [{ nhan: nhanCuaField(key), giaTri: "(không có)", sau }];
    if (sau >= 3) return [{ nhan: nhanCuaField(key), giaTri: JSON.stringify(v), sau }];
    const ra: DongHienThi[] = [{ nhan: nhanCuaField(key), giaTri: `${v.length} mục`, sau }];
    v.forEach((phanTu, i) => {
      if (typeof phanTu === "object" && phanTu !== null) {
        ra.push({ nhan: `#${i + 1}`, giaTri: "", sau: sau + 1 });
        ra.push(...traiPayload(phanTu, sau + 2));
      } else {
        ra.push({ nhan: `#${i + 1}`, giaTri: moTaGiaTri(key, phanTu), sau: sau + 1 });
      }
    });
    return ra;
  }
  if (typeof v === "object") {
    if (sau >= 3) return [{ nhan: nhanCuaField(key), giaTri: JSON.stringify(v), sau }];
    const ra: DongHienThi[] = [];
    if (key) ra.push({ nhan: nhanCuaField(key), giaTri: "", sau });
    for (const [k, giaTri] of Object.entries(v as Record<string, unknown>)) {
      if (typeof giaTri === "object" && giaTri !== null) {
        ra.push(...traiPayload(giaTri, key ? sau + 1 : sau, k));
      } else {
        ra.push({ nhan: nhanCuaField(k), giaTri: moTaGiaTri(k, giaTri), sau: key ? sau + 1 : sau });
      }
    }
    return ra;
  }
  return [{ nhan: nhanCuaField(key), giaTri: moTaGiaTri(key, v), sau }];
}
