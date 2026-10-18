import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import {
  LAST_GATE_COOKIE,
  SESSION_COOKIE,
  sessionCookieMaxAgeSeconds,
  type Gate,
  type Session,
} from "@/lib/session";
import { BACKEND_URL } from "@/lib/server-api";
import { translate } from "@/lib/i18n/core";
import { getLang } from "@/lib/i18n/server";

// Call the backend server-side (no CORS), then set an httpOnly cookie — per Next.js's own
// recommendation: "Cookies should be set on the server to prevent client-side tampering"
// (docs/01-app/02-guides/authentication.md). The JWT the backend issues also lives only in this
// httpOnly cookie — the browser never reads it, only the server-side route handler reuses it (BFF).
// Aug 26 — PO decision: block staff from logging in at /login (the customer gate) and vice versa.
// NOT a security gate — the role still comes 100% from the backend's RESPONSE; `gate` can only make
// a login FAIL FURTHER, never help it succeed (sending the wrong `gate` only gets the sender
// rejected, it can't route around anything). The block happens AFTER the password is verified
// correct — a wrong password teaches an attacker nothing extra; a correct password plus one more
// sentence costs nothing (PO). One and the same error message for every reason this step rejects —
// never reveal the real role on screen.
const wrongGateMessage = async () => translate(await getLang(), "err.wrongGate");

function gateRejects(gate: Gate, role: string) {
  if (gate === "customer") return role !== "customer";
  return role === "customer";
}

export async function POST(req: Request) {
  const { phone, password, gate } = (await req.json()) as { phone: string; password: string; gate: Gate };
  const res = await fetch(`${BACKEND_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ phone, password }),
  });

  if (!res.ok) {
    const loginFailed = translate(await getLang(), "err.loginFailed");
    const body = await res.json().catch(() => ({ detail: loginFailed }));
    return NextResponse.json({ detail: body.detail }, { status: res.status });
  }

  const user = (await res.json()) as {
    user_id: string;
    role: string;
    full_name: string;
    access_token: string;
    refresh_token: string;
  };

  // The password was correct (the backend just confirmed it) — but the wrong gate. Don't establish
  // a session (no cookie set; the tokens the backend just issued die with this request). Return a
  // generic 403 without revealing the real role.
  if (gateRejects(gate, user.role)) {
    return NextResponse.json({ detail: (await wrongGateMessage()) }, { status: 403 });
  }

  const session: Session = { ...user, phone, role: user.role as Session["role"] };

  const store = await cookies();
  store.set(SESSION_COOKIE, JSON.stringify(session), {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    // AUTH5-02/02B — the cookie's lifetime now follows the refresh_token's TTL (7 days for
    // customers, 1 day for internal roles), no longer matching JWT_ACCESS_EXPIRE_MINUTES directly
    // (only 15 minutes) — middleware.ts refreshes the access_token inside this cookie before it
    // expires, so customers aren't logged out after 15 minutes.
    maxAge: sessionCookieMaxAgeSeconds(session.role),
  });

  // The gate-hint cookie — see the comment at LAST_GATE_COOKIE's declaration (lib/session.ts) for
  // why it is NOT httpOnly and is NOT cleared on logout. `gate` here is exactly the parameter the
  // client sent (already passed through gateRejects() above — reaching this line means the gate
  // matches the real role).
  //
  // 🔴 [measured Aug 27] Review + p-226-f0: the original TTL was pinned at a FIXED 30 days — not
  // tied to any real lifecycle (staff refresh_token is only 1 day, customer 7 days). After 1 day,
  // staff are FORCED to log in again regardless of whether the hint cookie is still there — it only
  // PICKS THE GATE, it can't substitute for logging in, so the remaining 29 days of the old
  // constant served no valid use case, just left an extra trace on the workstation. Reuse
  // sessionCookieMaxAgeSeconds(role) — it already exists, already correct per role — so that if the
  // session lifecycle changes tomorrow, the hint cookie follows automatically instead of needing a
  // separately remembered constant kept in sync.
  const gateThat: Gate = gate === "internal" ? "internal" : "customer";
  store.set(LAST_GATE_COOKIE, gateThat, {
    httpOnly: false,
    sameSite: "lax",
    path: "/",
    maxAge: sessionCookieMaxAgeSeconds(session.role),
  });

  // Return to the client WITHOUT access_token/refresh_token — the client only needs to know that
  // login succeeded and which role, to navigate; the tokens stay on the server.
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

  // AUTH5-06 (Auth Flow upgrade, Aug 12, 2026) — logout now ACTUALLY revokes the JWT on the backend
  // (POST /auth/logout), not just clearing the frontend cookie as before (per the finding recorded
  // in tests/test_security/test_jwt_revocation.py). Best-effort — a network error calling the
  // backend must not block clearing the browser's cookie.
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
