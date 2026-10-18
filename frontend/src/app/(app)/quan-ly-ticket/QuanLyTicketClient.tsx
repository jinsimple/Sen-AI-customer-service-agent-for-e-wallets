"use client";

import TicketListSection from "@/components/TicketListSection";
import { useI18n } from "@/lib/i18n/client";

// ADR-064 (b — Sếp thấy TẤT CẢ, không đổi phạm vi quyền hiện có) — tách khỏi
// /dashboard (CSKH) thay vì tái dùng thẳng: trang đó còn WS chờ chat trực
// tiếp/nhận live-chat — việc VẬN HÀNH của CSKH, không phải việc QUẢN LÝ của
// Sếp. Bảng+bộ lọc+phân trang dùng chung qua TicketListSection (04/09).
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
