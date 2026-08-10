import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { SESSION_COOKIE, type Session } from "@/lib/session";
import { BACKEND_URL } from "@/lib/server-api";

// Gọi backend server-side (không CORS) rồi set cookie httpOnly — theo đúng
// khuyến nghị Next.js: "Cookies should be set on the server to prevent
// client-side tampering" (docs/01-app/02-guides/authentication.md). Token
// JWT backend phát ra cũng chỉ nằm trong cookie httpOnly này — trình duyệt
// không bao giờ đọc được, chỉ route handler server-side dùng lại (BFF).
export async function POST(req: Request) {
  const { phone, role } = await req.json();
  const res = await fetch(`${BACKEND_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ phone, role }),
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
  };
  const session: Session = { ...user, phone, role: user.role as Session["role"] };

  const store = await cookies();
  store.set(SESSION_COOKIE, JSON.stringify(session), {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 8, // 8 giờ — khớp JWT_EXPIRE_MINUTES ở backend
  });

  // Trả về client KHÔNG kèm access_token — client chỉ cần biết đăng nhập
  // xong và role gì để điều hướng, token ở lại phía server.
  const { access_token: _accessToken, ...publicSession } = session;
  return NextResponse.json(publicSession);
}

export async function DELETE() {
  const store = await cookies();
  store.delete(SESSION_COOKIE);
  return NextResponse.json({ ok: true });
}
