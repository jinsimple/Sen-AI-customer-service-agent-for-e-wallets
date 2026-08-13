import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { SESSION_COOKIE, sessionCookieMaxAgeSeconds, type Session } from "@/lib/session";
import { BACKEND_URL } from "@/lib/server-api";

// Gọi backend server-side (không CORS) rồi set cookie httpOnly — theo đúng
// khuyến nghị Next.js: "Cookies should be set on the server to prevent
// client-side tampering" (docs/01-app/02-guides/authentication.md). Token
// JWT backend phát ra cũng chỉ nằm trong cookie httpOnly này — trình duyệt
// không bao giờ đọc được, chỉ route handler server-side dùng lại (BFF).
export async function POST(req: Request) {
  const { phone, password } = await req.json();
  const res = await fetch(`${BACKEND_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ phone, password }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Đăng nhập thất bại" }));
    return NextResponse.json({ detail: body.detail }, { status: res.status });
  }

  const user = (await res.json()) as {
    user_id: string;
    role: string;
    full_name: string;
    access_token: string;
    refresh_token: string;
  };
  const session: Session = { ...user, phone, role: user.role as Session["role"] };

  const store = await cookies();
  store.set(SESSION_COOKIE, JSON.stringify(session), {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    // AUTH5-02/02B — cookie sống theo TTL refresh_token (7 ngày khách hàng,
    // 1 ngày role nội bộ), KHÔNG còn khớp trực tiếp JWT_ACCESS_EXPIRE_MINUTES
    // (chỉ 15 phút) — middleware.ts tự làm mới access_token bên trong cookie
    // này trước khi hết hạn, khách không bị đăng xuất sau 15 phút.
    maxAge: sessionCookieMaxAgeSeconds(session.role),
  });

  // Trả về client KHÔNG kèm access_token/refresh_token — client chỉ cần
  // biết đăng nhập xong và role gì để điều hướng, token ở lại phía server.
  const { access_token: _accessToken, refresh_token: _refreshToken, ...publicSession } = session;
  return NextResponse.json(publicSession);
}

export async function DELETE() {
  const store = await cookies();
  const raw = store.get(SESSION_COOKIE)?.value;
  const session = raw ? (() => {
    try {
      return JSON.parse(raw) as Session;
    } catch {
      return null;
    }
  })() : null;

  // AUTH5-06 (đợt nâng cấp Auth Flow 2026-08-12) — đăng xuất giờ THẬT SỰ thu
  // hồi JWT ở backend (POST /auth/logout), không còn CHỈ xoá cookie phía
  // frontend như trước (đúng phát hiện đã ghi trong
  // tests/test_security/test_jwt_revocation.py). Best-effort — lỗi mạng lúc
  // gọi backend không được chặn việc xoá cookie phía trình duyệt.
  if (session?.access_token && session?.refresh_token) {
    try {
      await fetch(`${BACKEND_URL}/auth/logout`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${session.access_token}` },
        body: JSON.stringify({ refresh_token: session.refresh_token }),
        cache: "no-store",
      });
    } catch {
      // best-effort — vẫn xoá cookie phía dưới dù backend không gọi được
    }
  }

  store.delete(SESSION_COOKIE);
  return NextResponse.json({ ok: true });
}
