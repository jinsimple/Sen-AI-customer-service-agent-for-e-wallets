"use client";

import StaffPresenceTable from "@/components/StaffPresenceTable";
import { useI18n } from "@/lib/i18n/client";

// [04/09] Tách khỏi trang Phê duyệt sang tab riêng — PO đo thật: đông CSKH
// làm bảng chật chỗ trang duyệt. Bảng + cơ chế presence/heartbeat giữ
// NGUYÊN (StaffPresenceTable.tsx), đây chỉ đổi CHỖ hiển thị.
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
