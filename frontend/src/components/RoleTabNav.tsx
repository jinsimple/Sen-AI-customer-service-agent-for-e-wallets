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
    // /tickets/[id] không có mục riêng — vào từ hàng chờ
    { href: "/policy-lookup", label: "nav.policyLookup" },
    { href: "/report", label: "nav.report" },
  ],
  supervisor: [
    { href: "/approve", label: "nav.approve" },
    // [04/09] Tách khỏi trang Phê duyệt — PO đo thật đông CSKH làm bảng
    // chật trang duyệt. Bảng/cơ chế presence giữ nguyên, chỉ đổi chỗ.
    { href: "/cskh-online", label: "nav.agentsOnline" },
    // ADR-064 (b) — Sếp cần xem TẤT CẢ ticket (không riêng hàng chờ duyệt)
    // để quản lý. `GET /tickets` vốn đã trả toàn bộ cho supervisor, đây chỉ
    // là lối vào UI, không đổi quyền/contract.
    { href: "/quan-ly-ticket", label: "nav.ticketAdmin" },
    { href: "/report", label: "nav.report" },
    // Sếp cũng cần tra chính sách khi quyết định — backend /policy-search đã
    // mở cho supervisor sẵn trong authority-matrix, chỉ thiếu lối vào ở nav.
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

// [polish trước quay 04/09] PO bắt qua ảnh chụp: vào `/tickets/{id}` từ Hàng
// chờ/Quản lý ticket/Phê duyệt thì KHÔNG tab nào sáng — trang đó không có
// href riêng trong TABS (khai từ 26/08: "vào từ hàng chờ", chấp nhận lúc đó,
// nay PO muốn sửa). CSKH chỉ có 1 lối vào ticket (Hàng chờ) nên trỏ thẳng;
// Sếp có 2 lối (Quản lý ticket/Phê duyệt) nên phải NHỚ lối vào GẦN NHẤT —
// dùng sessionStorage (không phải state/URL param, vì cả router.push lẫn
// next/link ở 4 nơi khác nhau đều dẫn vào đây, sửa tận gốc ở component nav
// rẻ hơn sửa từng call site) ghi MỖI LẦN trang đứng đúng trên 1 tab của
// chính vai đó, đọc lại khi đang ở `/tickets/`. Cold start (mở thẳng link vé
// chưa từng ghé tab nào trong phiên) → không tab nào sáng, giữ nguyên hành
// vi cũ, không tệ hơn trước.
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
      // Ghi ra sessionStorage (hệ thống ngoài) — không cần setState ở nhánh
      // này, vì `active` bên dưới đã tính đúng qua `pathname.startsWith`
      // trực tiếp, không phụ thuộc tabGanNhat khi đang ĐỨNG TRÊN một tab thật.
      sessionStorage.setItem(NHO_TAB_KEY(role), matched.href);
    } else if (isTicketDetail) {
      // Nhánh DUY NHẤT cần đọc lại state từ hệ thống ngoài (sessionStorage) —
      // đúng khuôn "subscribe cập nhật từ external system" mà effect sinh ra
      // để làm, không tính vào tổng lời gọi setState-trong-effect cần tránh.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setTabGanNhat(sessionStorage.getItem(NHO_TAB_KEY(role)));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pathname, role]);

  // 26/08 — chuẩn ngành: một hàng chỉ có ĐÚNG MỘT tab không phải điều hướng,
  // nó là một nhãn chiếm trọn một hàng khung. customer/partner_admin chỉ có
  // 1 màn nên KHÔNG render hàng này — cskh/supervisor (nhiều tab) giữ nguyên.
  // `?? []` phòng TABS[role] undefined (vai lạ) làm nổ .length ở layout —
  // vỡ TOÀN TRANG thay vì chỉ ẩn tab, dù hôm nay vai luôn là 1-trong-4 giá
  // trị hợp lệ từ session đã lọc.
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
