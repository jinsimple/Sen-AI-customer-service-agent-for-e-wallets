import { NextRequest, NextResponse } from "next/server";
import { parseSessionCookie, roleHome, sessionCookieMaxAgeSeconds, SESSION_COOKIE, type Role, type Session } from "@/lib/session";

// US-001 AC: "khách hàng không vào được dashboard CSKH kể cả sửa URL trực
// tiếp" — chặn ở proxy (Next.js 16 đổi tên từ middleware, chức năng như cũ),
// không chỉ ẩn UI. Đây là optimistic check (chỉ đọc cookie, không gọi DB) —
// đủ cho demo vì không có dữ liệu nhạy cảm nào trả trực tiếp từ proxy.
const ROLE_PREFIXES: Record<Role, string[]> = {
  customer: ["/chat"],
  cskh: ["/dashboard", "/tickets", "/policy-lookup"],
  supervisor: ["/approve", "/report", "/tickets"],
  partner_admin: ["/knowledge"],
};

const PUBLIC_PATHS = ["/login"];

function homeFor(role: Role | undefined) {
  return role ? roleHome(role) : "/login";
}

// AUTH5-02 (đợt nâng cấp Auth Flow, 2026-08-12) — access_token giờ chỉ sống
// 15 phút (JWT_ACCESS_EXPIRE_MINUTES, src/config.py). Nếu không có gì chủ
// động làm mới, MỌI request sau 15 phút sẽ 401 và người dùng bị đăng xuất
// giữa chừng — không chấp nhận được cho 1 phiên demo/UAT thật. `proxy.ts` là
// file DUY NHẤT được phép theo quy ước Next.js 16 (không thể thêm
// middleware.ts riêng) nên logic làm mới token GỘP CHUNG vào đây, chạy
// TRƯỚC logic redirect theo role — áp dụng cho CẢ page lẫn route /api/* (BFF
// đọc access_token từ cookie), không loại trừ /api như nhánh redirect bên
// dưới. Docs Next.js cảnh báo proxy "không dùng cho slow data fetching/
// session management đầy đủ" — ở đây CHỈ gọi fetch khi token gần hết hạn
// (không phải mọi request), chấp nhận đánh đổi vì kiến trúc BFF của dự án
// không có chỗ nào khác chạy được trước ~30 route handler mà không sửa lại
// từng route.
const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8010";
const REFRESH_MARGIN_SECONDS = 120;

function decodeJwtExp(token: string): number | null {
  // Đọc payload JWT KHÔNG verify chữ ký — chỉ dùng làm gợi ý "có nên chủ
  // động refresh không", KHÔNG dùng để xác thực/gác quyền (việc đó luôn do
  // backend làm lại bằng chữ ký thật). Sai/rỗng thì coi như "không rõ hạn",
  // để request đi tiếp bình thường, backend tự trả 401 nếu token thật sự hỏng.
  try {
    const payloadB64Url = token.split(".")[1];
    if (!payloadB64Url) return null;
    const payloadB64 = payloadB64Url.replace(/-/g, "+").replace(/_/g, "/");
    const json = atob(payloadB64);
    const payload = JSON.parse(json) as { exp?: number };
    return typeof payload.exp === "number" ? payload.exp : null;
  } catch {
    return null;
  }
}

async function refreshSessionIfNeeded(req: NextRequest, session: Session | null): Promise<Session | null> {
  if (!session) return null;
  const exp = decodeJwtExp(session.access_token);
  const nowSeconds = Date.now() / 1000;
  if (exp !== null && exp - nowSeconds > REFRESH_MARGIN_SECONDS) return session; // còn tươi

  try {
    const res = await fetch(`${BACKEND_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: session.refresh_token }),
    });
    if (!res.ok) return exp !== null && exp <= nowSeconds ? null : session; // refresh fail + token cũ cũng hết hạn -> coi như đăng xuất
    const refreshed = (await res.json()) as { access_token: string; refresh_token: string };
    return { ...session, access_token: refreshed.access_token, refresh_token: refreshed.refresh_token };
  } catch {
    // Backend/mạng lỗi — giữ session cũ, để route handler tự 401 nếu token
    // thật sự đã hết hạn (không giả vờ đã refresh xong).
    return session;
  }
}

export async function proxy(req: NextRequest) {
  const { pathname } = req.nextUrl;
  if (pathname.startsWith("/_next") || pathname.startsWith("/favicon")) {
    return NextResponse.next();
  }

  const originalSession = parseSessionCookie(req.cookies.get(SESSION_COOKIE)?.value);
  const session = await refreshSessionIfNeeded(req, originalSession);
  const sessionChanged = session?.access_token !== originalSession?.access_token;

  function withRefreshedCookie(res: NextResponse): NextResponse {
    if (session && sessionChanged) {
      res.cookies.set(SESSION_COOKIE, JSON.stringify(session), {
        httpOnly: true,
        sameSite: "lax",
        path: "/",
        maxAge: sessionCookieMaxAgeSeconds(session.role),
      });
    } else if (!session && originalSession) {
      res.cookies.delete(SESSION_COOKIE);
    }
    return res;
  }

  // /api/* — route handler BFF tự đọc cookie + tự trả unauthorized(), không
  // cần logic redirect theo role ở đây (đó là cho page). Vẫn phải áp dụng
  // withRefreshedCookie() để route handler thấy access_token ĐÃ được làm mới.
  if (pathname.startsWith("/api")) {
    return withRefreshedCookie(NextResponse.next());
  }

  if (pathname === "/") {
    return withRefreshedCookie(NextResponse.redirect(new URL(homeFor(session?.role), req.url)));
  }

  const isPublic = PUBLIC_PATHS.some((p) => pathname.startsWith(p));
  if (isPublic) {
    if (session) return withRefreshedCookie(NextResponse.redirect(new URL(roleHome(session.role), req.url)));
    return withRefreshedCookie(NextResponse.next());
  }

  if (!session) {
    return withRefreshedCookie(NextResponse.redirect(new URL("/login", req.url)));
  }

  const allowedForRole = ROLE_PREFIXES[session.role];
  const isAllowed = allowedForRole.some((p) => pathname.startsWith(p));
  if (!isAllowed) {
    return withRefreshedCookie(NextResponse.redirect(new URL(roleHome(session.role), req.url)));
  }

  return withRefreshedCookie(NextResponse.next());
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
