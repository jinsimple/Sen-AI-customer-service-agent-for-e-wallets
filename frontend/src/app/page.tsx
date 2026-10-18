import Link from "next/link";
import { redirect } from "next/navigation";
import { getServerSession } from "@/lib/session-server";
import { roleHome } from "@/lib/session";
import LanguageToggle from "@/components/LanguageToggle";
import { getT } from "@/lib/i18n/server";
import { rich } from "@/lib/i18n/rich";

// [MEASURED 2026-10-18] Figures shown in the "countable numbers" strip, counted from the current
// sources — recount whenever contracts/ or eval/ change, don't let them fossilise on a public page:
//   ROUTE_COUNT  = len(routes) in contracts/authority-matrix.yaml
//   EVAL_CASES   = non-empty lines across eval/*.jsonl;  EVAL_SETS = number of those files
const ROUTE_COUNT = 42;
const EVAL_CASES = 420;
const EVAL_SETS = 16;
const COUNTED_ON = "18/10/2026";

const B = { color: "var(--text)" } as const;

// `/` moved here from `/gioi-thieu` (26/08) — designed by the Lead, checked by the review:
// the redirect branch for a logged-in session is kept INTACT (0 auth logic changes); only the
// NO-SESSION branch changed from redirect("/login") to rendering this marketing page.
// proxy.ts handles it identically (matching EXACTLY pathname === "/", NOT via PUBLIC_PATHS — see the
// comment there for why) — this page is the second line of defence (the Next.js docs advise not to
// rely on the proxy alone for auth), in case some path bypasses the proxy.
export default async function Home() {
  const session = await getServerSession();
  if (session) {
    redirect(roleHome(session.role));
  }
  const { t } = await getT();

  // 🔴 The CONTENT below was NOT written by ux-ui — it follows
  // docs/2026-08-26-noi-dung-landing-page.md verbatim (written by the PO-agent, approved by the real
  // PO). Want to change a sentence → ask, don't edit the copy here. Reason: a marketing page is a
  // product claim, and the three hard constraints (the agent never decides · no fabricated figures ·
  // never ask for a transaction OTP) can all be broken by one marketing sentence without touching a
  // line of code.
  return (
    <>
      <nav className="lp-nav">
        <span className="brand">{t("lp.brand")}</span>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <LanguageToggle />
          <Link href="/login" className="btn btn-primary btn-sm">
            {t("lp.login")}
          </Link>
        </div>
      </nav>

      <section className="lp-hero">
        <div className="lp-hero-inner">
          <h1>{t("lp.heroH1")}</h1>
          {/* 27/08 round 3 — Marketing caught it: the PO approved the hero sentence BEFORE the name
              "Sen" existed. Calling the product by two names in the first two lines (nav "Sen ·
              FIN-05", then a hero lead starting "FIN-05...") while every later block says "Sen"
              forces readers to work out they are the same thing — and loses them. Only that one
              word was changed. */}
          <p className="lead">{rich(t("lp.heroLead"))}</p>
          <div className="lp-hero-actions">
            {/* 27/08 — Marketing: "Log in to try it" is a locked door for people without an account.
                It now leads straight into the demo (a one-tap demo customer login on /login), not to
                an empty password field. A secondary "Book a call" button was considered and DROPPED:
                there is no real destination (no published email/calendar), and a button with no
                destination promises a contact channel that doesn't exist. */}
            <Link href="/login" className="btn btn-primary">
              {t("lp.heroCta")}
            </Link>
          </div>
        </div>
      </section>

      {/* 27/08 round 3 — Marketing read the WHOLE page once as a stranger and moved this block ("AI
          plus people") from near the end to RIGHT AFTER THE HERO. The hero's "the decision still
          belongs to a human" reads at first like a LIMITATION ("this AI can't do it all") — the
          explanation of why it is a STRENGTH lives here, and used to come six screens later. Leaving
          it at the end is letting the defence arrive after the verdict. NO specific company is
          named on the public page — names are for the pitch room. */}
      <section className="lp-section">
        <div style={{ maxWidth: 640, margin: "0 auto", textAlign: "center" }}>
          <h2 style={{ marginBottom: 16 }}>{t("lp.triedH2")}</h2>
          <p style={{ color: "var(--text-dim)", fontSize: "var(--fs-16)" }}>{rich(t("lp.tried1"), B)}</p>
          <p style={{ color: "var(--text-dim)", fontSize: "var(--fs-16)", marginTop: 16 }}>{t("lp.tried2")}</p>
          <p style={{ color: "var(--text-dim)", fontSize: "var(--fs-16)", marginTop: 16 }}>{rich(t("lp.tried3"), B)}</p>
        </div>
      </section>

      {/* 27/08 — Marketing (block 02, "the problem — 2 a.m."): the old page jumped from the hero
          straight to the mechanism; buyers don't wake up thinking "I need a four-step flow", they
          wake up to a 2 a.m. case with nobody on duty. DELIBERATELY no specific deadlines (30/05/15
          business days) — the applicable circular wasn't settled yet, so it ships with no number
          that could be wrong. */}
      <section className="lp-section">
        <div style={{ maxWidth: 640, margin: "0 auto", textAlign: "center" }}>
          <h2 style={{ marginBottom: 12 }}>{t("lp.nightH2")}</h2>
          <p style={{ fontStyle: "italic", color: "var(--text-dim)", fontSize: "var(--fs-16)" }}>{t("lp.nightQuote")}</p>
          <p style={{ color: "var(--text-dim)", fontSize: "var(--fs-16)", marginTop: 16 }}>{rich(t("lp.nightBody"), B)}</p>
        </div>
      </section>

      {/* Instead of a partner-logo strip — there are no customers yet, so no logos/testimonials. */}
      <section className="lp-section">
        <div style={{ display: "grid", gap: 28, maxWidth: 720, margin: "0 auto" }}>
          <p style={{ fontSize: "var(--fs-16)", color: "var(--text-dim)", textAlign: "center" }}>{rich(t("lp.p1"), B)}</p>
          <p style={{ fontSize: "var(--fs-16)", color: "var(--text-dim)", textAlign: "center" }}>{rich(t("lp.p2"), B)}</p>
          {/* 27/08 round 2 — Marketing: third person ("the customer's") rather than "your", because
              this page is B2B — the buyer reads it, not a potential victim. A DELIBERATE exception to
              the unified anti-scam sentence on login/chat/for-customers (where the reader CAN be the
              victim) — the same recognisable wording, only the pronoun differs by audience. */}
          <p style={{ fontSize: "var(--fs-16)", color: "var(--text-dim)", textAlign: "center" }}>{rich(t("lp.p3"), B)}</p>
        </div>
      </section>

      <section className="lp-section" id="cach-hoat-dong">
        <h2>{t("lp.flowH2")}</h2>
        <div className="lp-flow">
          <div className="step">
            <b>{t("lp.flow1b")}</b>
            <span>{t("lp.flow1s")}</span>
          </div>
          <span className="arrow">→</span>
          <div className="step">
            <b>{t("lp.flow2b")}</b>
            <span>{t("lp.flow2s")}</span>
          </div>
          <span className="arrow">→</span>
          <div className="step">
            <b>{t("lp.flow3b")}</b>
            <span>{t("lp.flow3s")}</span>
          </div>
          <span className="arrow">→</span>
          <div className="step emphasis">
            <b>{t("lp.flow4b")}</b>
            <span>{t("lp.flow4s")}</span>
          </div>
        </div>

        {/* 27/08 — Marketing (block 04): "the product has already proven those four steps, and
            nobody is using that evidence". The screenshot was taken FOR REAL on current code (real
            customer login 0974000145, through the OTP flow -> reporting a transaction error -> the
            real agent creating a ticket) — not a mock. The whole content area is kept (rail + chat +
            status column); only the header strip (env badge/user name) is cropped. A second capture
            scrolls the chat so the anti-scam warning the agent VOLUNTEERED (nobody asked, including
            "installing a remote-control app") is visible. */}
        <figure style={{ maxWidth: 1120, margin: "40px auto 0" }}>
          <img
            src="/landing/ticket-status-thuc-te.png"
            width={1280}
            height={951}
            alt={t("lp.figAlt")}
            style={{ width: "100%", height: "auto", borderRadius: "var(--radius)", border: "1px solid var(--border)", display: "block" }}
          />
          <figcaption style={{ textAlign: "center", marginTop: 12, fontSize: "var(--fs-14)", color: "var(--text-dim)" }}>
            {t("lp.figCaption")}
          </figcaption>
        </figure>
      </section>

      {/* 27/08 — Marketing (block 05, "the economics"): Brief §3 makes operating cost one of the three
          positioning axes, and the old page had not one line about economics. DELIBERATELY no money
          figures (no sourced agent salary yet) — it describes the SHAPE of the cost curve, not its
          value. The 0.06s/0 tokens vs 8.70s/6,216 tokens pair is THE SAME MESSAGE measured on two
          paths — no denominator to argue about. */}
      <section className="lp-section">
        <div style={{ maxWidth: 720, margin: "0 auto" }}>
          <h2 style={{ textAlign: "center" }}>{t("lp.costH2")}</h2>
          <p style={{ color: "var(--text-dim)", fontSize: "var(--fs-16)", textAlign: "center", marginTop: 16 }}>{rich(t("lp.cost1"), B)}</p>
          <p style={{ color: "var(--text-dim)", fontSize: "var(--fs-16)", textAlign: "center", marginTop: 12 }}>{t("lp.cost2")}</p>
          <h3 style={{ textAlign: "center", marginTop: 32, fontSize: "var(--fs-20)" }}>{t("lp.costH3")}</h3>
          <p style={{ color: "var(--text-dim)", fontSize: "var(--fs-16)", textAlign: "center", marginTop: 16 }}>{rich(t("lp.cost3"), B)}</p>
          <p style={{ color: "var(--text-dim)", fontSize: "var(--fs-16)", textAlign: "center", marginTop: 12 }}>{rich(t("lp.cost4"), B)}</p>
        </div>
      </section>

      <section className="lp-section" style={{ background: "var(--surface-2)", maxWidth: "none" }}>
        <div style={{ maxWidth: 1120, margin: "0 auto" }}>
          <h2>{t("lp.statsH2")}</h2>
          <div className="lp-stat-strip" style={{ marginTop: 40 }}>
            <div className="lp-stat">
              <div className="num">{ROUTE_COUNT}</div>
              <div className="label">{t("lp.statRoutes", { n: ROUTE_COUNT })}</div>
            </div>
            <div className="lp-stat">
              <div className="num">5/5</div>
              <div className="label">{t("lp.statTools")}</div>
            </div>
            <div className="lp-stat">
              <div className="num">{EVAL_CASES}</div>
              <div className="label">{t("lp.statCases", { sets: EVAL_SETS })}</div>
            </div>
            <div className="lp-stat">
              <div className="num">60</div>
              <div className="label">{t("lp.statSealed")}</div>
            </div>
            <div className="lp-stat">
              <div className="num" style={{ color: "var(--navy)" }}>0</div>
              <div className="label">{t("lp.statZero")}</div>
            </div>
          </div>
          <p style={{ textAlign: "center", marginTop: 20, fontSize: "var(--fs-12)", color: "var(--text-faint)" }}>
            {t("lp.statsNote", { date: COUNTED_ON })}
          </p>
        </div>
      </section>

      {/* 27/08 — Marketing (block 08): the old sentence ("third-party details are masked before
          display") wasn't wrong, but it said NOTHING about model inference going through an external
          provider, while /login and ChatClient.tsx ALREADY declared it. The second sentence (the
          self-rotating model pool) is not an excuse — it is a real provider-exit plan. "Designed
          against", NOT "certified" (PO decision 26/08) — no independent audit has happened. */}
      <section className="lp-section">
        <div style={{ maxWidth: 720, margin: "0 auto", textAlign: "center" }}>
          <p style={{ color: "var(--text-dim)", fontSize: "var(--fs-14)" }}>{rich(t("lp.legal1"), B)}</p>
          <p style={{ color: "var(--text-dim)", fontSize: "var(--fs-14)", marginTop: 12 }}>{t("lp.legal2")}</p>
          {/* 27/08 — Marketing cited models.py (PolicyChunk.text = EncryptedText) + store.py
              (documents=chunk_ids — a placeholder, NOT real content). The scope is DELIBERATELY
              narrow: the PARTNER'S POLICY STORE, not customers' transaction data — don't shorten it. */}
          <p style={{ color: "var(--text-dim)", fontSize: "var(--fs-14)", marginTop: 12 }}>{t("lp.legal3")}</p>
        </div>
      </section>

      {/* ONLY links to /login — NEVER to /dang-nhap-noi-bo (staff login) from the public page. */}
      <footer className="lp-footer" style={{ textAlign: "center" }}>
        <div style={{ color: "var(--text)", fontWeight: 700 }}>{t("lp.footerBrand")}</div>
        <div style={{ color: "var(--text-dim)", fontSize: "var(--fs-14)", marginTop: 4 }}>
          AI 20K Build Phase Cohort 3 — Vingroup × VinUni
        </div>
        <Link href="/login" className="btn btn-outline btn-sm" style={{ marginTop: 20, display: "inline-flex" }}>
          {t("lp.footerCta")}
        </Link>
      </footer>
    </>
  );
}
