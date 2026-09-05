"use client";

import TicketListSection from "@/components/TicketListSection";

// ADR-064 (b — Sếp thấy TẤT CẢ, không đổi phạm vi quyền hiện có) — tách khỏi
// /dashboard (CSKH) thay vì tái dùng thẳng: trang đó còn WS chờ chat trực
// tiếp/nhận live-chat — việc VẬN HÀNH của CSKH, không phải việc QUẢN LÝ của
// Sếp. Bảng+bộ lọc+phân trang dùng chung qua TicketListSection (04/09).
export default function QuanLyTicketClient() {
  return (
    <>
      <div className="page-head">
        <span className="eyebrow">Webapp Sếp</span>
        <h1>Quản lý ticket</h1>
        <p className="sub">Toàn bộ ticket trong hệ thống, không riêng ca đang chờ duyệt — để nắm bức tranh chung.</p>
      </div>

      <TicketListSection role="supervisor" />
    </>
  );
}
