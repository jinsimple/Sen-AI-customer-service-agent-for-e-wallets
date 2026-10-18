import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { getServerSession } from "@/lib/session-server";
import { backendFetch, proxyErrorResponse, unauthorized } from "@/lib/server-api";
import { SESSION_COOKIE, sessionCookieMaxAgeSeconds, type Session } from "@/lib/session";

// The backend issues a NEW JWT (otp_verified=true) once verification succeeds — the httpOnly cookie
// must be UPDATED here (the route handler, not a Server Component — see the cookies() docs:
// "Setting cookies is not supported during Server Component rendering"). The client NEVER sees the
// new access_token, only {ok:true} — the same BFF rule applied to the whole session.
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

    // AUTH5-02 — verify_otp also issues a NEW refresh_token (a new family, see
    // src/api/main.py::verify_otp) — both fields must be updated, not just access_token as before.
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
