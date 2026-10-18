"use client";

import TicketListSection from "@/components/TicketListSection";
import { useI18n } from "@/lib/i18n/client";

// ADR-064 (b — the supervisor sees EVERYTHING, no change to the existing permission scope) — split
// out of /dashboard (support) instead of reusing it directly: that page also carries the WS
// connection for live chat requests/claims — an OPERATIONAL concern for support, not a MANAGEMENT
// concern for the supervisor. Table + filters + pagination are shared through TicketListSection
// (Sep 4).
export default function QuanLyTicketClient() {
  const { t } = useI18n();
  return (
    <>
      <div className="page-head">
        <span className="eyebrow">{t("eyebrow.supervisor")}</span>
        <h1>{t("ticketMgmt.title")}</h1>
        <p className="sub">{t("ticketMgmt.sub")}</p>
      </div>

      <TicketListSection role="supervisor" />
    </>
  );
}
