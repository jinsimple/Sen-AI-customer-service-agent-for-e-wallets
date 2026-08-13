import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { getServerSession } from "@/lib/session-server";
import { backendFetch, proxyErrorResponse, unauthorized } from "@/lib/server-api";
import { SESSION_COOKIE, sessionCookieMaxAgeSeconds, type Session } from "@/lib/session";

// Backend cấp JWT MỚI (otp_verified=true) sau khi xác thực đúng — cookie
// httpOnly phải được CẬP NHẬT ở đây (route handler, không phải Server
// Component — xem docs cookies() "Setting cookies is not supported during
// Server Component rendering"). Client KHÔNG BAO GIỜ thấy access_token mới,
// chỉ nhận {ok:true} — đúng nguyên tắc BFF đã áp dụng cho toàn bộ session.
export async function POST(req: Request) {
  const session = await getServerSession();
  if (!session) return unauthorized();

  const { session_id, otp_code } = await req.json();
  try {
    const data = await backendFetch<{ access_token: string; refresh_token: string; otp_verified: boolean }>(
      "/auth/otp/verify",
      session.access_token,
      { method: "POST", body: JSON.stringify({ session_id, otp_code }) }
    );

    // AUTH5-02 — verify_otp cũng cấp refresh_token MỚI (family mới, xem
    // src/api/main.py::verify_otp) — phải cập nhật cả 2 field, không chỉ
    // access_token như trước.
    const updated: Session = { ...session, access_token: data.access_token, refresh_token: data.refresh_token };
    const store = await cookies();
    store.set(SESSION_COOKIE, JSON.stringify(updated), {
      httpOnly: true,
      sameSite: "lax",
      path: "/",
      maxAge: sessionCookieMaxAgeSeconds(updated.role),
    });

    return NextResponse.json({ ok: true, otp_verified: data.otp_verified });
  } catch (e) {
    return proxyErrorResponse(e);
  }
}
