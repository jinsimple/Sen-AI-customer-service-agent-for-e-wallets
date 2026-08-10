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
}

export const SESSION_COOKIE = "fin05_session";

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
      ["customer", "cskh", "supervisor", "partner_admin"].includes(parsed.role)
    ) {
      return parsed as Session;
    }
  } catch {
    // cookie hỏng/bị sửa tay — coi như chưa đăng nhập
  }
  return null;
}
