// The "anti-scam" page — content written by Marketing (p-226-17), shipped VERBATIM, never
// re-interpreted. The route is DELIBERATELY always public (see proxy.ts::ALWAYS_PUBLIC_PATHS) — no
// redirect in any direction, even for users who ARE logged in, because this is the page a customer
// opens exactly WHEN they suspect a scam, often mid-login.
//
// 🔴 DO NOT reuse the typography/effects of "/" — Marketing cited "ADR-053"
// (Playfair Display + particles + magnetic CTA) as the reason; [MEASURED] that ADR does NOT exist
// in docs/DECISIONS.md (the latest at the time was ADR-052), and "/" actually uses Inter + a static
// hero, not Playfair/particles/magnetic CTA — reported back to Marketing. BUT the principle stands
// regardless of whether the ADR exists: a page reassuring someone in a panic should be minimal, with
// no effects — applied using EXACTLY the existing token set (Inter, --text/--bg/--danger...), not the
// warm font/colour set of Marketing's draft (which itself used the serif "Source Serif 4" for body
// text — the same Vietnamese-diacritics risk they had just warned me about).
//
// NO link back to "/" anywhere on this page (explicitly specified by Marketing) — inviting someone
// worried about losing money to "see our enterprise solution" would be absurd.
import LanguageToggle from "@/components/LanguageToggle";
import { getT } from "@/lib/i18n/server";
import { rich } from "@/lib/i18n/rich";

export default async function ChoKhachHangPage() {
  const { t } = await getT();
  return (
    <main className="ck-page">
      <div className="ck-wrap">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
          <p className="ck-eyebrow">{t("fc.eyebrow")}</p>
          <LanguageToggle />
        </div>
        <h1 className="ck-h1">{t("fc.h1")}</h1>
        <p className="ck-lead">{t("fc.lead")}</p>
        <p className="ck-lead-strong">{t("fc.leadStrong")}</p>

        <section className="ck-core">
          <h2 className="ck-h2">{t("fc.neverH2")}</h2>
          <p className="ck-lead-strong">{t("common.neverAsk")}</p>
          <ul className="ck-never">
            <li>
              <span className="ck-x" aria-hidden="true">✕</span>
              <span>{rich(t("fc.never1"))}</span>
            </li>
            <li>
              <span className="ck-x" aria-hidden="true">✕</span>
              <span>{rich(t("fc.never2"))}</span>
            </li>
            <li>
              <span className="ck-x" aria-hidden="true">✕</span>
              <span>{rich(t("fc.never3"))}</span>
            </li>
          </ul>
          <p className="ck-core-warn">{rich(t("fc.warn"))}</p>
        </section>

        <section className="ck-section">
          <h2 className="ck-h2">{t("fc.afterH2")}</h2>
          <p>{rich(t("fc.after1"))}</p>
          <p>{rich(t("fc.after2"))}</p>
          <p>{rich(t("fc.after3"))}</p>
          <p>{t("fc.track")}</p>
        </section>

        <section className="ck-section ck-grid-2">
          <div>
            <h3 className="ck-h3">{t("fc.canH3")}</h3>
            <ul className="ck-plain">
              <li>{t("fc.can1")}</li>
              <li>{t("fc.can2")}</li>
              <li>{t("fc.can3")}</li>
              <li>{t("fc.can4")}</li>
            </ul>
          </div>
          <div>
            <h3 className="ck-h3">{t("fc.cantH3")}</h3>
            <ul className="ck-plain">
              <li>{t("fc.cant1")}</li>
              <li>{t("fc.cant2")}</li>
              <li>{t("fc.cant3")}</li>
              <li>{t("fc.cant4")}</li>
            </ul>
          </div>
        </section>

        <section className="ck-section">
          <h2 className="ck-h2">{t("fc.wrongH2")}</h2>
          <p>{t("fc.wrong1")}</p>
          <p>{rich(t("fc.wrong2"))}</p>
        </section>

        <footer className="ck-footer">
          <p>
            <b>{t("fc.footerBrand")}</b>
            <br />
            AI 20K Build Phase Cohort 3 — Vingroup × VinUni
          </p>
          <p className="ck-footer-dim">{t("fc.footerDim")}</p>
        </footer>
      </div>
    </main>
  );
}
