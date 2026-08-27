/**
 * Không có mật khẩu thật (xem src/api/schemas.py::LoginRequest ở backend) —
 * dataset không có cột password, Brief §7 chỉ yêu cầu OTP phiên + câu hỏi
 * bảo mật cho thao tác nhạy cảm, không phải hạ tầng đăng nhập thật.
 *
 * `access_token` (JWT do backend ký, src/auth.py) mới là thứ chứng minh
 * danh tính — cookie này httpOnly, JS phía trình duyệt không đọc được, chỉ
 * route handler server-side của Next.js (BFF, xem lib/server-api.ts) đọc để
 * gắn `Authorization: Bearer` khi gọi FastAPI. Trình duyệt không bao giờ
 * gọi thẳng FastAPI hay thấy token này.
 */
export type Role = "customer" | "cskh" | "supervisor" | "partner_admin";

export interface Session {
  user_id: string;
  role: Role;
  full_name: string;
  phone: string;
  access_token: string;
  // AUTH5-02/02C (đợt nâng cấp Auth Flow 2026-08-12) — access_token giờ
  // ngắn hạn (15 phút, JWT_ACCESS_EXPIRE_MINUTES) nên PHẢI đi kèm
  // refresh_token để middleware.ts tự làm mới mà không bắt đăng nhập lại
  // liên tục. Cùng cookie httpOnly với access_token (không tách cookie
  // riêng — kiến trúc BFF ở đây chỉ có 1 điểm ghi/đọc session phía server,
  // tách thêm 1 cookie thứ 2 không tăng thêm bảo mật thật vì JS trình
  // duyệt vốn đã không đọc được cookie này, chỉ tăng chỗ phải đồng bộ).
  refresh_token: string;
}

export const SESSION_COOKIE = "fin05_session";

// 27/08 — PO báo: nhân viên hết phiên (hoặc bị đăng xuất) luôn bị đá về
// /login (cổng khách) — NGÕ CỤT thật, vì mỗi cổng CHỈ chấp nhận đúng vai của
// mình (route.ts::gateRejects), và trang công khai "/" không có đường nào
// dẫn tới /dang-nhap-noi-bo. Khác với nút Đăng xuất (biết `role` ngay lúc
// bấm, xem TopbarActions.tsx) — proxy.ts/layout.tsx gặp session đã hỏng
// (cookie thiếu/hết hạn/bị revoke) thì KHÔNG CÒN vai nào để tra, vì vai nằm
// trong chính cookie đã chết đó.
//
// Cookie gợi ý này lưu GATE (không phải role cụ thể — không cần biết CSKH
// hay Sếp, chỉ cần biết "trình duyệt này lần trước đăng nhập ở cổng nào") để
// dùng LÀM DỰ PHÒNG khi session không đọc được nữa. KHÔNG nhạy cảm (không
// định danh ai, chỉ nói cổng nào) nên KHÔNG httpOnly — `lib/api.ts` (client,
// chạy trong trình duyệt) cũng cần đọc được nó để biết đá về cổng nào khi
// một lời gọi API 401 giữa phiên (refresh cũng đã hỏng, xem
// server-api.ts::_lamMoiPhien) — proxy.ts không kịp thấy ca này vì cookie
// phiên (đã chết) vẫn còn hình dạng hợp lệ lúc điều hướng trang. Sống dài
// hơn hẳn session thật (30 ngày) để còn đó SAU KHI session đã hết hạn, đúng
// lúc cần dùng tới. Ghi ở route.ts::POST mỗi lần đăng nhập thành công, ĐỌC ở
// proxy.ts khi !session và ở lib/api.ts khi 401 giữa phiên — KHÔNG xoá khi
// đăng xuất (dụng ý: nhân viên đóng máy rồi quay lại vẫn về đúng cổng nội bộ
// dù chưa đăng nhập).
export type Gate = "customer" | "internal";
export const LAST_GATE_COOKIE = "fin05_last_gate";
export const LAST_GATE_COOKIE_MAX_AGE_SECONDS = 30 * 24 * 60 * 60;

export function loginPathForGate(gate: string | undefined): string {
  return gate === "internal" ? "/dang-nhap-noi-bo" : "/login";
}

// AUTH5-02B — role nội bộ rủi ro cao hơn nếu refresh_token bị đánh cắp
// (chạm dữ liệu nhiều khách), TTL cookie ngắn hơn hẳn khách hàng — PHẢI
// khớp JWT_REFRESH_EXPIRE_DAYS_CUSTOMER/STAFF ở src/config.py (backend).
export function sessionCookieMaxAgeSeconds(role: Role): number {
  const days = role === "customer" ? 7 : 1;
  return days * 24 * 60 * 60;
}

export function roleHome(role: Role): string {
  if (role === "customer") return "/chat";
  if (role === "cskh") return "/dashboard";
  if (role === "partner_admin") return "/knowledge";
  return "/approve";
}

export function parseSessionCookie(raw: string | undefined): Session | null {
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw);
    if (
      parsed &&
      typeof parsed.user_id === "string" &&
      typeof parsed.role === "string" &&
      typeof parsed.access_token === "string" &&
      typeof parsed.refresh_token === "string" &&
      ["customer", "cskh", "supervisor", "partner_admin"].includes(parsed.role)
    ) {
      return parsed as Session;
    }
  } catch {
    // cookie hỏng/bị sửa tay — coi như chưa đăng nhập
  }
  return null;
}
