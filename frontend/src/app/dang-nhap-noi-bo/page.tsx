"use client";

import { useLoginForm } from "@/lib/useLoginForm";
import EnvBadge from "@/components/EnvBadge";
import LanguageToggle from "@/components/LanguageToggle";
import { useI18n } from "@/lib/i18n/client";
import type { DictKey } from "@/lib/i18n/dict";

// The INTERNAL gate — support agent · supervisor approval · wallet partner. Aug 26 decision: split
// the PAGE from /login (customer), not the MECHANISM — it shares lib/useLoginForm.ts, and the role
// still comes from the server's RESPONSE looked up by phone; there is no role picker here. This
// page is DELIBERATELY not linked from the landing page or `/login` — not real security (the URL is
// still reachable if guessed), just one fewer invitation to a stranger. Tone: utilitarian, terse —
// unlike /login's "welcoming" tone.
//
// 🔴 [measured Aug 26] NO quick login, NO printed demo password, NO list of staff phone numbers —
// even though doing this on /login (customer) is safe (customer accounts exist to be handed to
// strangers), HERE it is a real leak: this route is PUBLIC (PUBLIC_PATHS) + the supervisor-approval
// phone number shown right there + a shared password printed in plain sight ⟹ anyone who opens the
// page can log in as supervisor and approve refunds. Three decisions that are each reasonable on
// their own (the login page must be public · a quick-login button is convenient for demos · a
// shared password is convenient for testing) add up to one open door. The internal page must look
// like an empty login box that reveals nothing about itself (not even a "contact your admin" hint —
// that hint itself confirms "there is a real gate with real accounts behind this"). Staff type
// their own phone number and password — they know it; the page doesn't need to remind them.
// 🔴 A deliberate, narrow EXCEPTION to the ban above (Aug 26) — this does NOT reverse that
// decision. Build-time flag `NEXT_PUBLIC_QUICK_LOGIN`, OFF by default, same pattern as
// `OTP_DEMO_MODE`: Next.js substitutes `NEXT_PUBLIC_*` AT BUILD TIME, so leaving the flag unset
// means the three accounts below don't exist in the bundle sent to the browser — not just hidden in
// the UI. Used for EXACTLY one demo video recording on Sep 1, built on a separate `quay-video` tag,
// never overwriting `latest`. Approved by the real PO via the Lead.
// The real PO synced the `po-demo` database on the night of Sep 1: all three accounts below SHARE
// one password (the support agent's, with an old reversible backup hash) — only the phone number
// differs. Not a system-wide default; it applies only to the `po-demo` environment for the Sep 1
// video shoot.
const MAT_KHAU_QUAY_VIDEO = "Demo@123";
const QUICK_LOGIN_ACCOUNTS: { label: DictKey; phone: string; password: string }[] = [
  { label: "role.cskh", phone: "0353000201", password: MAT_KHAU_QUAY_VIDEO },
  { label: "role.supervisor", phone: "0905000205", password: MAT_KHAU_QUAY_VIDEO },
  { label: "role.partner_admin", phone: "0900000001", password: MAT_KHAU_QUAY_VIDEO },
];

export default function LoginNoiBoPage() {
  const { phone, setPhone, password, setPassword, error, loading, doLogin, handleSubmit } = useLoginForm("internal");
  const { t } = useI18n();

  return (
    <main style={{ maxWidth: 420, margin: "80px auto", padding: "0 20px" }}>
      <div className="card" style={{ padding: 36 }}>
        <div style={{ marginBottom: 14, display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8 }}>
          <EnvBadge />
          <LanguageToggle />
        </div>
        <h3>{t("slogin.title")}</h3>
        <p className="sub">{t("slogin.sub")}</p>

        {process.env.NEXT_PUBLIC_QUICK_LOGIN === "true" && (
          <div style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap" }}>
            {QUICK_LOGIN_ACCOUNTS.map((acc) => (
              <button
                key={acc.phone}
                type="button"
                className="btn btn-primary"
                style={{ flex: "1 1 auto" }}
                disabled={loading}
                onClick={() => doLogin(acc.phone, acc.password)}
              >
                {t(acc.label)}
              </button>
            ))}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className={`field${error ? " field-error" : ""}`}>
            <label>{t("login.phone")}</label>
            <input
              type="tel"
              placeholder="09xx xxx xxx"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              required
            />
          </div>

          <div className={`field${error ? " field-error" : ""}`}>
            <label>{t("login.password")}</label>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            {error && (
              <div className="error-text">
                <svg className="icon icon-sm" viewBox="0 0 24 24">
                  <circle cx="12" cy="12" r="10" />
                  <path d="M12 8v5M12 16h.01" />
                </svg>
                {error}
              </div>
            )}
          </div>

          <button className="btn btn-primary" style={{ width: "100%", justifyContent: "center", marginTop: 20 }} disabled={loading}>
            {loading ? t("login.submitting") : t("login.submit")}
          </button>
        </form>
      </div>
    </main>
  );
}
