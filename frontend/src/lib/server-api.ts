import "server-only";
import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { parseSessionCookie, SESSION_COOKIE, sessionCookieMaxAgeSeconds, type Session } from "@/lib/session";
import { translate } from "@/lib/i18n/core";
import { getLang } from "@/lib/i18n/server";

/**
 * The layer that calls the REAL FastAPI — only ever imported from a Route Handler
 * (`app/api/**\/route.ts`), never from a Client Component. This is the linchpin of the BFF (Backend
 * for Frontend) architecture: the browser never calls FastAPI directly or knows its address/token —
 * every request goes through a Next.js server-side route handler, which reads the token from the
 * httpOnly cookie before attaching `Authorization: Bearer` when calling the real backend.
 *
 * `BACKEND_URL` deliberately has NO `NEXT_PUBLIC_` prefix — a variable without that prefix is never
 * bundled by Next.js into what's sent to the browser, meaning client-side JS can never learn the
 * real backend address, narrowing the attack surface compared with the earlier design that had to
 * expose `NEXT_PUBLIC_API_BASE`.
 */
export const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8010";

export class ServerApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

// 65s — a bit wider than the browser-side timeout (60s, see lib/api.ts) so that, under normal
// conditions, a real timeout error always surfaces from the browser side first (a more meaningful
// message for the customer); the timeout here is only a server-side resource safety net (so a
// connection/handler doesn't hang forever if the backend itself is truly stuck) — UX-01
// (FIN05-QA-Test-Report.md), the same root cause as BUG-01.
const BACKEND_FETCH_TIMEOUT_MS = 65_000;

// ---------------------------------------------------------------------------
// SESSION REFRESH — LIVES HERE, NOT IN `proxy.ts`
//
// `proxy.ts` CAN still call `/auth/refresh` (confirmed on the backend) but the cookie it sets with
// `NextResponse.cookies.set()` NEVER leaves the server — measured for real: 0 `set-cookie` headers
// on EITHER the page path or `/api`, while the control case `/api/session` (using `cookies()` from
// `next/headers`) produces exactly 1 header. Same source across three images, same Node v20.20.2 +
// Next 16.3.0, and the code matches the installed Next version's official docs point for point — so
// this is NOT a fixable configuration mistake, it's a corner with no documented answer.
//
// Consequence of the new token never reaching the browser: the next request carries the OLD,
// ALREADY-ROTATED refresh token -> AUTH5-03 treats it as stolen -> `revoke_family` -> THE WHOLE
// SESSION DIES, including the token pair that was just issued. The system shoots itself in the
// foot.
//
// So: use the PATH ALREADY PROVEN TO WORK — `cookies()` from `next/headers` inside a route handler.
// And place it in `backendFetch()`, because this is the ONE CHOKE POINT every BFF call passes
// through: "easy to miss a route" is solved by STRUCTURE, not by the carefulness of whoever edits
// this next.
const _dangRefresh = new Map<string, Promise<Session | null>>();

/**
 * Single-flight keyed by refresh token.
 *
 * MANDATORY, not an optimisation: a refresh token is USE-ONCE, and a second call reusing it
 * triggers `revoke_family` (auth.py:146-155) — meaning two parallel calls don't just waste work,
 * they KILL THE SESSION. One page render firing several `backendFetch` calls in parallel is normal,
 * so without this lock we'd reproduce the exact bug just fixed, only at a new layer.
 *
 * ⚠️ KNOWN LIMITATION: the Map lives at MODULE scope, so it only covers ONE Node process. Multiple
 * frontend replicas, or multiple browser tabs (two JS contexts that can't see each other), can
 * still refresh in parallel. Full coverage needs a shared lock (Redis). Noted here so the next
 * scaling pass doesn't assume this is fully solved.
 */
async function _lamMoiPhien(cu: Session): Promise<Session | null> {
  const dangCo = _dangRefresh.get(cu.refresh_token);
  if (dangCo) return dangCo;

  const viec = (async (): Promise<Session | null> => {
    try {
      const res = await fetch(`${BACKEND_URL}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: cu.refresh_token }),
        cache: "no-store",
      });
      // 27/08 [measured] p-226-f0: when the refresh_token has also failed (expired/revoked), this
      // function returns null BUT the dead session cookie stays sitting in the browser — proxy.ts
      // only checks the cookie's SHAPE, not its validity, so it still treats the user as "logged
      // in" and lets them through. Every backend call after that 401s again → tries to refresh
      // again → fails again, a LOOP with no way out on its own — only clicking Logout (the ONLY
      // other place that calls store.delete) escapes it. Delete the cookie RIGHT HERE so the loop
      // has nothing left to repeat.
      //
      // 🔴 [measured 27/08] p-226-8b (Review): delete ONLY when the backend REALLY rejects the
      // refresh_token (401) — `!res.ok` is broader than intended, also catching 429
      // (`/auth/refresh` is rate-limited at 30/minute, main.py — multiple tabs/parallel BFF
      // requests can all trigger it) and 5xx (an uncaught exception in rotate_refresh_token during
      // a brief Redis hiccup). Both are "the network/backend is temporarily broken", not "the token
      // was rejected" — deleting the cookie in those two cases DESTROYS A STILL-LIVE SESSION,
      // exactly the kind of regression this patch set out to avoid, just pointed the other way
      // (before: keeping a dead cookie too long; now, if left unfixed: deleting a live cookie too
      // eagerly).
      if (res.status === 401) {
        (await cookies()).delete(SESSION_COOKIE);
        return null;
      }
      if (!res.ok) {
        return null;
      }
      const moi = (await res.json()) as { access_token: string; refresh_token: string };
      const phien: Session = { ...cu, access_token: moi.access_token, refresh_token: moi.refresh_token };
      // THIS is the egress path that has been proven to work — `cookies()` from `next/headers`, the
      // same way `/api/session` does it. Do NOT use `NextResponse.cookies.set()`.
      const store = await cookies();
      store.set(SESSION_COOKIE, JSON.stringify(phien), {
        httpOnly: true,
        sameSite: "lax",
        path: "/",
        maxAge: sessionCookieMaxAgeSeconds(phien.role),
      });
      return phien;
    } catch {
      // The network/backend is broken (NOT the refresh_token being rejected — that's the !res.ok
      // branch above) — don't delete the cookie here: the session may still be valid, the backend
      // is just temporarily unreachable. Return null so the caller throws the original 401 error
      // rather than retrying with a token that might not even exist anymore.
      return null;
    } finally {
      _dangRefresh.delete(cu.refresh_token);
    }
  })();

  _dangRefresh.set(cu.refresh_token, viec);
  return viec;
}

type InitCoCo = RequestInit & { __daThuLai?: boolean };

export async function backendFetch<T>(
  path: string,
  token: string,
  init?: InitCoCo
): Promise<T> {
  // FormData (file upload, see app/api/policy-docs/route.ts) — don't set Content-Type:
  // application/json here yourself, so fetch/undici computes the correct multipart boundary on its
  // own. Forcing JSON onto a FormData body would stop FastAPI from parsing it.
  const isFormData = init?.body instanceof FormData;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), BACKEND_FETCH_TIMEOUT_MS);
  let res: Response;
  try {
    res = await fetch(`${BACKEND_URL}${path}`, {
      ...init,
      // A proxy for financial data/per-user login sessions — must never be cached. Next.js (even a
      // Route Handler, even a GET method) still caches a fetch by default through the "HMR cache"
      // during `next dev`, EVEN WITH no-store set at the route level (see
      // node_modules/next/dist/docs/.../fetch.md, Troubleshooting section) — a real finding: right
      // after a supervisor's approval succeeded (the POST succeeded, the backend had already
      // changed the status), the immediately following GET /api/resolutions still returned the old
      // record, and the card never disappeared from the queue even though the backend was correct.
      // Setting no-store explicitly here (the single fetch call point to the real backend) so it
      // doesn't depend on the default configuration.
      cache: "no-store",
      headers: {
        ...(isFormData ? {} : { "Content-Type": "application/json" }),
        Authorization: `Bearer ${token}`,
        ...(init?.headers ?? {}),
      },
      signal: controller.signal,
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ServerApiError(504, translate(await getLang(), "err.backendTimeout"));
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      // FastAPI (an HTTPException) returns {"detail": "..."}, but slowapi (a 429 rate limit, see
      // src/api/main.py) returns {"error": "..."} — missing this branch makes the error fall
      // through to JSON.stringify(body) and show raw JSON verbatim to the customer (a real finding:
      // hitting "Confirm" on an OTP repeatedly triggers the rate limit, and the screen showed
      // {"error":"Rate limit exceeded: ..."} instead of an understandable message).
      // For a 422 validation error specifically, FastAPI returns `detail` as an ARRAY of objects
      // [{loc, msg, type}...] — passing it straight into Error(message) gets coerced to the string
      // "[object Object]" on the customer's screen (QA-05, minutes dated Aug 13, caught at both
      // /api/otp/verify and /api/resolutions/.../approve).
      if (Array.isArray(body.detail)) {
        const lang = await getLang();
        const invalid = translate(lang, "err.invalid");
        detail = body.detail
          .map((d: { loc?: unknown[]; msg?: string }) => {
            const field = Array.isArray(d.loc) ? d.loc.slice(1).join(".") : "";
            return field ? `${field}: ${d.msg ?? invalid}` : d.msg ?? invalid;
          })
          .join("; ");
        detail = translate(lang, "err.invalidPayload", { detail });
      } else {
        detail = body.detail ?? body.error ?? JSON.stringify(body);
      }
    } catch {
      // giữ statusText nếu body không phải JSON
    }
    // 401 -> try refreshing EXACTLY ONCE, then retry the call. 401 ONLY (an expired token), NOT
    // applied to 403 (the wrong role — refreshing can't change the role, so retrying is pointless
    // and only clutters the logs).
    if (res.status === 401 && !init?.__daThuLai) {
      const cu = parseSessionCookie((await cookies()).get(SESSION_COOKIE)?.value);
      if (cu) {
        const moi = await _lamMoiPhien(cu);
        if (moi) {
          return backendFetch<T>(path, moi.access_token, { ...init, __daThuLai: true });
        }
      }
    }
    throw new ServerApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

/**
 * Used in the catch block of every proxy route handler — turns a backend error (401/403/400/404...)
 * into the matching response for the client, instead of leaking a generic 500 traceback.
 */
export function proxyErrorResponse(e: unknown): NextResponse {
  if (e instanceof ServerApiError) {
    return NextResponse.json({ detail: e.message }, { status: e.status });
  }
  throw e;
}

/**
 * A function, not a constant — every call must construct a new Response. A Response can only be
 * read/sent once; sharing one instance across concurrent requests fails in a way that's hard to
 * track down.
 */
export async function unauthorized(): Promise<NextResponse> {
  return NextResponse.json({ detail: translate(await getLang(), "err.notLoggedIn") }, { status: 401 });
}
