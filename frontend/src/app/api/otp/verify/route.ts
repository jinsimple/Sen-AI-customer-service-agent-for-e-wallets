import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { getServerSession } from "@/lib/session-server";
import { backendFetch, proxyErrorResponse, unauthorized } from "@/lib/server-api";
import { SESSION_COOKIE, type Session } from "@/lib/session";

// Backend cấp JWT MỚI (otp_verified=true) sau khi xác thực đúng — cookie
// httpOnly phải được CẬP NHẬT ở đây (route handler, không phải Server
// Component — xem docs cookies() "Setting cookies is not supported during
// Server Component rendering"). Client KHÔNG BAO GIỜ thấy access_token mới,
// chỉ nhận {ok:true} — đúng nguyên tắc BFF đã áp dụng cho toàn bộ session.
export async function POST(req: Request) {
  const session = await getServerSession();
  if (!session) return unauthorized();

  const { otp_code, security_answer } = await req.json();
  try {
    const data = await backendFetch<{ access_token: string; otp_verified: boolean }>(
      "/auth/otp/verify",
      session.access_token,
      { method: "POST", body: JSON.stringify({ otp_code, security_answer }) }
    );

    const updated: Session = { ...session, access_token: data.access_token };
    const store = await cookies();
    store.set(SESSION_COOKIE, JSON.stringify(updated), {
      httpOnly: true,
      sameSite: "lax",
      path: "/",
      maxAge: 60 * 60 * 8,
    });

    return NextResponse.json({ ok: true, otp_verified: data.otp_verified });
  } catch (e) {
    return proxyErrorResponse(e);
  }
}
