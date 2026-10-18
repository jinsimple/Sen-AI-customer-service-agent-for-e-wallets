import "server-only";
import { cookies } from "next/headers";
import { parseSessionCookie, SESSION_COOKIE, type Session } from "@/lib/session";

export async function getServerSession(): Promise<Session | null> {
  const store = await cookies();
  return parseSessionCookie(store.get(SESSION_COOKIE)?.value);
}

// M-10 (logged Aug 14) / Finding A, phase 2.5 — an F5 after OTP was already verified locked the
// "Recent transactions" rail even though the OTP was still valid: ChatClient.tsx initialised
// `otpVerified` with `useState(false)`, INDEPENDENT of the real session, so EVERY mount (F5, a new
// tab) was treated as unverified — even when `otp_verified_at` in the JWT still had 12 hours left.
//
// MUST match `OTP_VIEW_MAX_MINUTES` on the backend (src/config.py) — THIS IS A DELIBERATE COPY, the
// same pattern `sessionCookieMaxAgeSeconds` in session.ts already uses for
// JWT_REFRESH_EXPIRE_DAYS_*. The phase-2.5 backend is FROZEN, so there's no way to read this
// threshold from one shared source — a mismatch between the two sides only causes a WRONG UI
// DISPLAY FOR A FEW SECONDS (the rail opening/locking incorrectly), NOT A SECURITY HOLE: every
// route that reads real data still checks otp_verified_at itself on the server (INV-10); this value
// ONLY decides what the UI shows, never who can read what.
const OTP_VIEW_MAX_MINUTES = 12 * 60;

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const segment = token.split(".")[1];
    if (!segment) return null;
    return JSON.parse(Buffer.from(segment, "base64url").toString("utf8"));
  } catch {
    // A broken/unreadable JWT -> treated as having NO otp_verified_at, without throwing an error
    // that breaks the whole chat page over a value that only affects display.
    return null;
  }
}

// Return a boolean/expiry timestamp, NEVER the raw JWT claim, out of this function — the caller
// (page.tsx) is only allowed to pass an ALREADY-DERIVED value on to the client, never the
// `access_token` or the raw claim object.
export function getOtpXemConHan(session: Session): boolean {
  const claims = decodeJwtPayload(session.access_token);
  const otpVerifiedAt = claims?.otp_verified_at;
  if (typeof otpVerifiedAt !== "number") return false;
  // `Date.now()` is correct because the backend AND frontend both run with TZ=UTC in Docker
  // ([measured] Lead, Aug 19). NOT unconditionally true: `otp-forge.ts` (Aug 11) recorded
  // `utcnow().timestamp()` drifting by a timezone offset when the backend runs DIRECTLY on the host
  // (e.g. `make run`) — the 12h window would shrink by exactly that offset, SILENTLY, with no error
  // firing. This comparison is only correct when both sides stand on UTC.
  const ageMinutes = (Date.now() / 1000 - otpVerifiedAt) / 60;
  return ageMinutes <= OTP_VIEW_MAX_MINUTES;
}
