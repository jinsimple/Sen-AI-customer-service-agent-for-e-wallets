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
