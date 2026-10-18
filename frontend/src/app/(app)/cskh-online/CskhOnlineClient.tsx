"use client";

import StaffPresenceTable from "@/components/StaffPresenceTable";
import { useI18n } from "@/lib/i18n/client";

// [Sep 4] Split out of the Approvals page into its own tab — measured by the PO: a crowded roster
// of support agents was cramping the approvals page. The table and the presence/heartbeat mechanism
// are UNCHANGED (StaffPresenceTable.tsx); only its display location moved.
export default function CskhOnlineClient() {
  const { t } = useI18n();
  return (
    <>
      <div className="page-head">
        <span className="eyebrow">{t("eyebrow.supervisor")}</span>
        <h1>{t("cskhOnline.title")}</h1>
        <p className="sub">
          {t("cskhOnline.sub")}
        </p>
      </div>

      <StaffPresenceTable />
    </>
  );
}
