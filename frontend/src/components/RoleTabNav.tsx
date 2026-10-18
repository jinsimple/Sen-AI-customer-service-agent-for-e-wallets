"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Role } from "@/lib/session";
import { useI18n } from "@/lib/i18n/client";
import type { DictKey } from "@/lib/i18n/dict";

const TABS: Record<Role, { href: string; label: DictKey }[]> = {
  customer: [{ href: "/chat", label: "nav.chat" }],
  cskh: [
    { href: "/dashboard", label: "nav.queue" },
    // /tickets/[id] has no tab of its own — reached from the queue
    { href: "/policy-lookup", label: "nav.policyLookup" },
    { href: "/report", label: "nav.report" },
  ],
  supervisor: [
    { href: "/approve", label: "nav.approve" },
    // [Sep 4] Split out of the Approvals page — measured by the PO: a crowded roster of support
    // agents was cramping the approvals page. The table/presence mechanism is unchanged, only its
    // location moved.
    { href: "/cskh-online", label: "nav.agentsOnline" },
    // ADR-064 (b) — the supervisor needs to see ALL tickets (not just the approval queue) to
    // manage. `GET /tickets` already returns everything for a supervisor; this is just a UI entry
    // point, no change to permissions/contract.
    { href: "/quan-ly-ticket", label: "nav.ticketAdmin" },
    { href: "/report", label: "nav.report" },
    // The supervisor also needs to look up policy when deciding — the backend /policy-search is
    // already open to supervisors in the authority-matrix, only the nav entry point was missing.
    { href: "/policy-lookup", label: "nav.policyLookup" },
  ],
  partner_admin: [{ href: "/knowledge", label: "nav.knowledge" }],
};

const GROUP_LABEL: Record<Role, DictKey> = {
  customer: "role.customer",
  cskh: "role.cskh",
  supervisor: "role.supervisor",
  partner_admin: "role.partner_admin",
};

// [polish before the Sep 4 shoot] Caught by the PO from a screenshot: landing on `/tickets/{id}`
// from Queue/Ticket management/Approvals lit up NO tab — that page has no href of its own in TABS
// (noted since Aug 26: "reached from the queue", accepted at the time, now the PO wants it fixed).
// A support agent has only 1 way into a ticket (Queue), so it can point there directly; a
// supervisor has 2 ways (Ticket management/Approvals), so it must REMEMBER the MOST RECENT entry
// point — using sessionStorage (not state/a URL param, since router.push and next/link are both
// used from 4 different places leading here; fixing it once in the nav component is cheaper than
// fixing every call site), written EVERY TIME the page is standing on one of that role's own tabs,
// and read back while on `/tickets/`. Cold start (opening a ticket link directly, having never
// visited a tab this session) → no tab lights up, same as the old behaviour, no worse than before.
const NHO_TAB_KEY = (role: Role) => `fin05_tab_gan_nhat:${role}`;

export default function RoleTabNav({ role }: { role: Role }) {
  const pathname = usePathname();
  const { t } = useI18n();
  const tabs = TABS[role] ?? [];
  const isTicketDetail = pathname.startsWith("/tickets/");

  const [tabGanNhat, setTabGanNhat] = useState<string | null>(null);
  useEffect(() => {
    const matched = tabs.find((t) => pathname.startsWith(t.href));
    if (matched) {
      // Writing to sessionStorage (an external system) — no setState needed on this branch, because
      // `active` below is already computed correctly via `pathname.startsWith` directly, and
      // doesn't depend on tabGanNhat while STANDING ON a real tab.
      sessionStorage.setItem(NHO_TAB_KEY(role), matched.href);
    } else if (isTicketDetail) {
      // The ONE branch that needs to read state back from an external system (sessionStorage) —
      // exactly the "subscribe to an update from an external system" pattern an effect exists for,
      // and doesn't count toward the setState-in-effect calls to avoid.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setTabGanNhat(sessionStorage.getItem(NHO_TAB_KEY(role)));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pathname, role]);

  // Aug 26 — industry convention: a row holds EXACTLY ONE non-navigating tab as a label that fills
  // the whole row. customer/partner_admin have only 1 screen, so this row is NOT rendered for them
  // — cskh/supervisor (multiple tabs) keep it as is. `?? []` guards against TABS[role] being
  // undefined (an unknown role), which would blow up `.length` in the layout — breaking the WHOLE
  // PAGE instead of just hiding a tab, even though today the role is always one of 4 valid values
  // from an already-filtered session.
  if (tabs.length <= 1) return null;
  return (
    <nav className="tabnav">
      <div className="tabgroup">
        <span className="tabgroup-label">{t(GROUP_LABEL[role])}</span>
        {tabs.map((tab) => {
          const active = pathname.startsWith(tab.href) || (isTicketDetail && tabGanNhat === tab.href);
          return (
            <Link key={tab.href} href={tab.href} className={`tab-btn${active ? " active" : ""}`}>
              {t(tab.label)}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
