"use client";

import { roleHome, type Role } from "@/lib/session";
import { useI18n } from "@/lib/i18n/client";
import type { DictKey } from "@/lib/i18n/dict";
import { rich } from "@/lib/i18n/rich";

// UI-02 — the WRONG-ROLE banner.
//
// Bug the PO hit during a mentor demo: logging in as a support agent in the SAME browser overwrites
// the customer's session (the BFF architecture deliberately uses ONE session cookie). The
// customer's chat tab is still open; typing again -> `/agent/chat` returns a 403 `"Requires role in
// ['customer'], current account is cskh"` -> that sentence falls straight into the chat window as
// "Error: …" in the middle of the demo.
//
// WHY THE FIX LIVES IN THE CLIENT rather than a guard route: `proxy.ts` DOES block by role
// (`ROLE_PREFIXES`) and redirects correctly — but it only runs on NAVIGATION. The already-open tab
// never navigates; the 403 comes from an API call. The guard route never sees this case.
//
// Does NOT change the session mechanism: one-cookie-one-session is a deliberate BFF design (the
// token never leaves the server, the browser only holds an httpOnly cookie). The patch's job is to
// turn a confusing error into a direction — not to let two roles live in one browser at once.

const TEN_VAI: Record<string, DictKey> = {
  customer: "wrongRole.customer",
  cskh: "wrongRole.cskh",
  supervisor: "wrongRole.supervisor",
  partner_admin: "wrongRole.partner_admin",
};

export default function BannerLechVai({
  vaiHienTai,
  vaiCanCo,
}: {
  vaiHienTai: string;
  vaiCanCo: string;
}) {
  const { t } = useI18n();
  const ten = TEN_VAI[vaiHienTai] ? t(TEN_VAI[vaiHienTai]) : vaiHienTai;
  const tenCan = TEN_VAI[vaiCanCo] ? t(TEN_VAI[vaiCanCo]) : vaiCanCo;
  const ve = roleHome(vaiHienTai as Role);

  return (
    <div
      role="alert"
      style={{
        border: "1px solid var(--warn-border, #d9a441)",
        background: "var(--warn-bg, #fff8e6)",
        color: "var(--warn-fg, #6b4b00)",
        borderRadius: 8,
        padding: "12px 14px",
        margin: "10px 0",
        fontSize: 14,
        lineHeight: 1.6,
      }}
    >
      <strong>{t("wrongRole.loggedInAs", { role: ten })}</strong>
      <div style={{ marginTop: 4 }}>
        {rich(t("wrongRole.thisScreen", { role: tenCan }))}
      </div>
      <div style={{ marginTop: 6 }}>
        {rich(t("wrongRole.incognito"))}
      </div>
      <a href={ve} style={{ display: "inline-block", marginTop: 10, fontWeight: 600 }}>
        {t("wrongRole.back", { role: ten })}
      </a>
    </div>
  );
}
