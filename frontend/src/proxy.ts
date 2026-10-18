import { NextRequest, NextResponse } from "next/server";
import {
  LAST_GATE_COOKIE,
  loginPathForGate,
  parseSessionCookie,
  roleHome,
  sessionCookieMaxAgeSeconds,
  SESSION_COOKIE,
  type Role,
  type Session,
} from "@/lib/session";

// US-001 AC: "a customer can't reach the support dashboard even by editing the URL directly" —
// blocked at the proxy (Next.js 16's renamed middleware, same function), not just hidden in the UI.
// This is an optimistic check (it only reads the cookie, no DB call) — enough for a demo, since no
// sensitive data is ever returned directly from the proxy.
const ROLE_PREFIXES: Record<Role, string[]> = {
  customer: ["/chat"],
  // /report: the contract allows it (GET /reports/summary roles [cskh, supervisor]) but the
  // frontend is stricter — a support agent gets kicked to /dashboard. This is the SECOND occurrence
  // of the same bug class "the frontend guard is narrower than the contract" (the first: supervisor
  // + /policy-lookup, d0baf35). The tester is writing a test that scans the whole role×route matrix
  // so a third occurrence gets caught by a machine.
  // /policy-doc: the "View full text" deep-link from /policy-lookup (ADR-065, Sep 5) — opened via a
  // link, with NO nav tab of its own, same pattern as /tickets/{id}. The SIXTH occurrence of the
  // same bug class "a new route forgot to declare itself here" if missed (5 earlier ones:
  // /policy-lookup, /dashboard, /report, /cskh-online, /quan-ly-ticket) — declared RIGHT AWAY when
  // the route is added, instead of waiting for someone to click something broken.
  cskh: ["/dashboard", "/tickets", "/policy-lookup", "/policy-doc", "/report"],
  // /policy-lookup: a supervisor also needs to look up policy when deciding on an approval. Without
  // this prefix, the proxy redirects straight to roleHome() = /approve, so clicking the tab looks
  // like a broken tab (QA measured this, Aug 14). The backend already allows it — authority-matrix:
  // POST /policy-search roles [cskh, supervisor].
  // /dashboard: a supervisor can view the support queue under the current contract (GET /tickets:
  // cskh, supervisor). This is the THIRD occurrence of the same bug class "the frontend guard is
  // narrower than the contract" — the tester's role×route matrix scanner is what will catch a
  // fourth occurrence.
  // /cskh-online: a new tab split off from /approve (Sep 4) — missing this prefix here would be the
  // FOURTH occurrence of the bug class "a new route is missing from the proxy's own allowlist" (a
  // different branch from the contract-backend one, which has already happened 3 times:
  // /policy-lookup, /dashboard, /report). The route calls no API beyond /presence/staff (already
  // allowed for a supervisor in the authority-matrix).
  // /quan-ly-ticket (ADR-064 b): a NEW tab split off from /approve following the same pattern as
  // /cskh-online — the FIFTH repeat of exactly the "a new route forgot to declare itself here" bug
  // class if missed (4 earlier ones: /policy-lookup, /dashboard, /report, /cskh-online). The route
  // opens no new API — /quan-ly-ticket only calls the GET /tickets already allowed for a supervisor
  // in the authority-matrix.
  supervisor: [
    "/approve", "/cskh-online", "/quan-ly-ticket", "/report", "/tickets",
    "/policy-lookup", "/policy-doc", "/dashboard",
  ],
  partner_admin: ["/knowledge"],
};

// Aug 26 — the landing page was moved from /gioi-thieu BACK to "/" (Lead's design, reviewed). "/"
// is NOT in this array — it has its own EXACT-match branch further down (`pathname === "/"`),
// DELIBERATELY kept out of PUBLIC_PATHS because the matcher here is `khopTienTo` (prefix + a "/"
// boundary), and "/" plus a boundary would match EVERY path — folding it in here would throw
// /dashboard, /approve... wide open. /dang-nhap-noi-bo stays here: a genuinely public route (the
// internal login page), not the landing page.
const PUBLIC_PATHS = ["/login", "/dang-nhap-noi-bo"];

// Review (p-226-8b, Aug 26): a raw `startsWith` matches by CHARACTER PREFIX, not by segment
// boundary — "/dashboard".startsWith also matches "/dashboard-admin". The two places that use it
// (PUBLIC_PATHS below AND ROLE_PREFIXES) share the same shape of bug: whoever names a new route
// sharing a prefix with an already-allowed route accidentally opens up or escalates permissions,
// with no other change needed. One boundary-aware match function (exact OR prefix + "/") closes
// both spots at once, instead of relying on memory to avoid it.
function khopTienTo(pathname: string, prefix: string) {
  return pathname === prefix || pathname.startsWith(prefix + "/");
}

// Aug 27 — Marketing built /cho-khach-hang: an "anti-scam" page (confirming "does Sen ever ask for
// an OTP code?"). This is a THIRD, different group from PUBLIC_PATHS in nature — PUBLIC_PATHS
// redirects an ALREADY-logged-in user to roleHome (correct for /login), while this page must be
// readable even while a customer is CURRENTLY logging in and panicking, with no redirect in EITHER
// direction. It isn't folded into PUBLIC_PATHS as an exception — behaviour that's different in
// nature belongs in a different group, not a branching flag inside the old one.
const ALWAYS_PUBLIC_PATHS = ["/cho-khach-hang"];

// AUTH5-02 (Auth Flow upgrade, 2026-08-12) — access_token now lives only 15 minutes
// (JWT_ACCESS_EXPIRE_MINUTES, src/config.py). Without something actively refreshing it, EVERY
// request after 15 minutes 401s and the user gets logged out mid-session — not acceptable for a
// real demo/UAT session. `proxy.ts` is the ONE file Next.js 16's convention allows (a separate
// middleware.ts can't be added), so the token-refresh logic is FOLDED IN HERE, running BEFORE the
// role-redirect logic — applied to BOTH pages and /api/* routes (the BFF reads access_token from
// the cookie), with no /api exclusion unlike the redirect branch below. Next.js's docs warn that
// proxy "shouldn't be used for slow data fetching/full session management" — here it ONLY calls
// fetch when the token is close to expiring (not on every request); accepted as a trade-off because
// this project's BFF architecture has nowhere else that runs before ~30 route handlers without
// editing every route individually.
const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8010";
const REFRESH_MARGIN_SECONDS = 120;

// 27/08 [measured] p-226-dc: adding real images to the landing page (`/landing/*.png`) surfaced
// that file (AND every file already in `public/` beforehand — this measured even Next's own default
// `/next.svg`, `/file.svg`) getting redirected to /login for a customer who is NOT logged in — the
// matcher only excludes `_next/*`/favicon, not the rest of `public/`. The bug was ALREADY THERE
// BEFOREHAND, not caused by the new images — the new images were just the first request to hit this
// exact bug class.
//
// 🔴 [measured Aug 27] Review (p-226-8b): the FIRST patch used a regex on the FILE EXTENSION —
// WRONG, because it tests the pathname without telling apart "a real static file in public/" from
// "an App Router route with a DYNAMIC segment whose parameter value happens to match the
// extension". Specifically: `/tickets/[id]` (only cskh/supervisor may enter, per ROLE_PREFIXES) — a
// customer calling `/tickets/x.json` would match the `.json` extension regex on the VERY FIRST
// LINE, skipping the role check below entirely, and get the page shell RENDERED (the real data
// stays safe because the backend checks the role itself separately — but this still contradicts the
// literal US-001 AC at the top of the file: blocked at the proxy, not just hidden in the UI). A
// file extension is NOT a safe invariant once the system has dynamic routes — an ALLOWLIST OF REAL
// PATHS is, because it doesn't infer from the SHAPE of a string (whether it has a dot) but from the
// LIST of asset files that actually exist. Switched to using `khopTienTo` (already in place, the
// same mechanism as PUBLIC_PATHS/ALWAYS_PUBLIC_PATHS below) on the exact real static-asset
// directories — `public/` in this project barely changes, and the cost of remembering one extra
// line when adding a new asset folder is FAR LOWER than the risk of a file-extension regex
// reopening the US-001 gap.
const STATIC_ASSET_PATHS = ["/landing", "/file.svg", "/vercel.svg", "/next.svg", "/globe.svg", "/window.svg"];

export async function proxy(req: NextRequest) {
  const { pathname } = req.nextUrl;
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/favicon") ||
    STATIC_ASSET_PATHS.some((p) => khopTienTo(pathname, p))
  ) {
    return NextResponse.next();
  }

  // SESSION REFRESH MOVED OUT OF HERE -> `lib/server-api.ts::backendFetch`.
  //
  // Why removed rather than fixed: proxy CAN still call `/auth/refresh` (confirmed on the backend,
  // layer-0 confirms the rotation succeeded) but the cookie it sets with
  // `NextResponse.cookies.set()` NEVER leaves the server — 0 `set-cookie` headers on EITHER the
  // page path or `/api`, while the control case `/api/session` (using `cookies()` from
  // next/headers) produces exactly 1 header.
  //
  // Consequence of leaving it here: the token is rotated on the server, the browser never learns
  // it, the next request carries the OLD, ALREADY-ROTATED refresh token -> AUTH5-03 -> the whole
  // family is revoked -> the session dies. A "refresh" mechanism that kills the session every time
  // it runs.
  //
  // Ruled out: a UI-01 regression · wrong file location · wrong export name · wrong code pattern
  // (all three match the Next 16.3.0 docs point for point) · dependency drift (all three images
  // share Node v20.20.2 + Next 16.3.0 + an empty manifest). Not a fixable configuration mistake —
  // so moved to the path PROVEN TO EGRESS CORRECTLY.
  const session = parseSessionCookie(req.cookies.get(SESSION_COOKIE)?.value);

  // The request header is ALREADY PATCHED — so a route handler running WITHIN THIS SAME request
  // reads the new access_token, not just the browser receiving it on the next turn.
  //
  // THIS IS A BUG, NOT AN OPTIMISATION. The previous version had a comment saying "Still need to
  // apply withRefreshedCookie() so the route handler sees the REFRESHED access_token" — correctly
  // stating the INTENT that the code failed to achieve: `res.cookies.set()` sets a cookie on the
  // RESPONSE (the path back to the browser), while a route handler reads a cookie from the REQUEST,
  // which still holds the old token. A reviewer reading that comment would nod along.
  //
  // The measured consequence: right after the token expired, the FIRST request still 401s even
  // though the refresh succeeded within that very request; only the second request gets 200. Mild
  // when the user just clicks again — FATAL when a UI layer tries exactly once
  // (`liveChatConnectStartedRef`, the PO's demo case).

  // /api/* — the BFF route handler reads the cookie itself and returns unauthorized() itself, no
  // need for role-redirect logic here (that's for a page).
  //
  // TWO halves, and missing either one breaks it halfway:
  //   `NextResponse.next()` -> a route handler WITHIN this request
  //       sees the new token (this half was PREVIOUSLY MISSING)
  //   `withRefreshedCookie(...)` -> the browser gets the new token for
  //       SUBSEQUENT requests
  if (pathname.startsWith("/api")) {
    return NextResponse.next();
  }

  if (ALWAYS_PUBLIC_PATHS.some((p) => khopTienTo(pathname, p))) {
    return NextResponse.next();
  }

  // An EXACT-match branch, DELIBERATELY kept apart from PUBLIC_PATHS (see the comment at that
  // array's declaration) — "/" is now the public landing page, no longer pure authentication logic.
  // With a session -> still goes to the role's home screen, NO CHANGE from before (0 change to the
  // auth surface for an already-logged-in user). Without a session -> CHANGED: let it render (the
  // marketing page at app/page.tsx), no longer redirecting to "/login".
  if (pathname === "/") {
    if (session) return NextResponse.redirect(new URL(roleHome(session.role), req.url));
    return NextResponse.next();
  }

  const isPublic = PUBLIC_PATHS.some((p) => khopTienTo(pathname, p));
  if (isPublic) {
    if (session) return NextResponse.redirect(new URL(roleHome(session.role), req.url));
    return NextResponse.next();
  }

  if (!session) {
    // Aug 27 — PO reported: staff whose session expired always got sent to /login (the customer
    // gate), a DEAD END because that gate rejects internal roles. Having no `session` here means
    // there's no role left to look up (the session cookie is lost/broken) — use the gate-hint
    // cookie (LAST_GATE_COOKIE, written at login, outliving the real session) as a fallback instead
    // of always defaulting to /login. See lib/session.ts.
    const goiY = req.cookies.get(LAST_GATE_COOKIE)?.value;
    return NextResponse.redirect(new URL(loginPathForGate(goiY), req.url));
  }

  const allowedForRole = ROLE_PREFIXES[session.role];
  const isAllowed = allowedForRole.some((p) => khopTienTo(pathname, p));
  if (!isAllowed) {
    return NextResponse.redirect(new URL(roleHome(session.role), req.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
