/**
 * No real password (see src/api/schemas.py::LoginRequest on the backend) — the dataset has no
 * password column; Brief §7 only requires a session OTP + a security question for sensitive
 * actions, not a real login system.
 *
 * `access_token` (a JWT signed by the backend, src/auth.py) is the thing that actually proves
 * identity — this cookie is httpOnly, unreadable by browser-side JS; only Next.js's server-side
 * route handler (BFF, see lib/server-api.ts) reads it to attach `Authorization: Bearer` when
 * calling FastAPI. The browser never calls FastAPI directly or sees this token.
 */
export type Role = "customer" | "cskh" | "supervisor" | "partner_admin";

export interface Session {
  user_id: string;
  role: Role;
  full_name: string;
  phone: string;
  access_token: string;
  // AUTH5-02/02C (Auth Flow upgrade, 2026-08-12) — access_token is now short-lived (15 minutes,
  // JWT_ACCESS_EXPIRE_MINUTES), so it MUST travel with a refresh_token so middleware.ts can refresh
  // it automatically without forcing repeated logins. Shares the same httpOnly cookie as
  // access_token (not a separate cookie — this BFF architecture has only one server-side session
  // read/write point; splitting off a second cookie adds no real security, since browser JS already
  // can't read this cookie anyway, it only adds another place to keep in sync).
  refresh_token: string;
}

export const SESSION_COOKIE = "fin05_session";

// Aug 27 — PO reported: staff whose session expired (or who got logged out) always get redirected
// to /login (the customer gate) — a real DEAD END, since each gate ONLY ACCEPTS its own role
// (route.ts::gateRejects), and the public "/" page has no path leading to /dang-nhap-noi-bo. Unlike
// the Logout button (which knows `role` right at the moment it's clicked, see TopbarActions.tsx) —
// proxy.ts/layout.tsx, on hitting a broken session (cookie missing/expired/revoked), has NO role
// left to look up, because the role lived inside that very dead cookie.
//
// This hint cookie stores the GATE (not the specific role — no need to know support agent vs.
// supervisor, just "which gate this browser last logged in through") to use as a FALLBACK once the
// session can no longer be read. NOT sensitive (identifies no one, only says which gate), so it is
// NOT httpOnly — `lib/api.ts` (the client, running in the browser) also needs to read it to know
// which gate to redirect to when an API call returns 401 mid-session (the refresh has also failed,
// see server-api.ts::_lamMoiPhien) — proxy.ts can't catch this case in time, because the (dead)
// session cookie still looks shaped validly at the moment of page navigation.
//
// 🔴 [measured Aug 27] Review (p-226-8b): the original TTL was pinned at a FIXED 30 days — not tied
// to any real lifecycle (staff refresh_token is only 1 day, customer 7 days; past that, staff are
// FORCED to log in again regardless of whether the hint cookie is still there, since it only PICKS
// A GATE and can't substitute for logging in). Reuse `sessionCookieMaxAgeSeconds(role)`
// (route.ts::POST) — it already exists, already correct per role — instead of pinning a separate
// constant that has to be remembered and kept in sync every time the session lifecycle changes.
// Written in route.ts::POST on every successful login, READ in proxy.ts when !session and in
// lib/api.ts on a mid-session 401 — NOT cleared on logout (intentional: staff who close their
// machine and come back still land on the right internal gate even before logging in, within the
// session's own valid lifetime).
export type Gate = "customer" | "internal";
export const LAST_GATE_COOKIE = "fin05_last_gate";

export function loginPathForGate(gate: string | undefined): string {
  return gate === "internal" ? "/dang-nhap-noi-bo" : "/login";
}

// AUTH5-02B — an internal role is higher-risk if its refresh_token is stolen (touches many
// customers' data), so its cookie TTL is far shorter than a customer's — MUST match
// JWT_REFRESH_EXPIRE_DAYS_CUSTOMER/STAFF in src/config.py (backend).
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
