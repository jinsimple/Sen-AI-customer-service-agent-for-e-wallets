import { NextRequest, NextResponse } from "next/server";
import { parseSessionCookie, roleHome, SESSION_COOKIE, type Role } from "@/lib/session";

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

export function proxy(req: NextRequest) {
  const { pathname } = req.nextUrl;
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api") ||
    pathname.startsWith("/favicon")
  ) {
    return NextResponse.next();
  }

  const session = parseSessionCookie(req.cookies.get(SESSION_COOKIE)?.value);

  if (pathname === "/") {
    return NextResponse.redirect(new URL(homeFor(session?.role), req.url));
  }

  const isPublic = PUBLIC_PATHS.some((p) => pathname.startsWith(p));
  if (isPublic) {
    if (session) return NextResponse.redirect(new URL(roleHome(session.role), req.url));
    return NextResponse.next();
  }

  if (!session) {
    return NextResponse.redirect(new URL("/login", req.url));
  }

  const allowedForRole = ROLE_PREFIXES[session.role];
  const isAllowed = allowedForRole.some((p) => pathname.startsWith(p));
  if (!isAllowed) {
    return NextResponse.redirect(new URL(roleHome(session.role), req.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
