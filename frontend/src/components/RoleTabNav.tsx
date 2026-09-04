"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Role } from "@/lib/session";

const TABS: Record<Role, { href: string; label: string }[]> = {
  customer: [{ href: "/chat", label: "Trợ lý AI" }],
  cskh: [
    { href: "/dashboard", label: "Hàng chờ" },
    // /tickets/[id] không có mục riêng — vào từ hàng chờ
    { href: "/policy-lookup", label: "Tra cứu chính sách" },
    { href: "/report", label: "Báo cáo vận hành" },
  ],
  supervisor: [
    { href: "/approve", label: "Phê duyệt" },
    // [04/09] Tách khỏi trang Phê duyệt — PO đo thật đông CSKH làm bảng
    // chật trang duyệt. Bảng/cơ chế presence giữ nguyên, chỉ đổi chỗ.
    { href: "/cskh-online", label: "CSKH online" },
    // ADR-064 (b) — Sếp cần xem TẤT CẢ ticket (không riêng hàng chờ duyệt)
    // để quản lý. `GET /tickets` vốn đã trả toàn bộ cho supervisor, đây chỉ
    // là lối vào UI, không đổi quyền/contract.
    { href: "/quan-ly-ticket", label: "Quản lý ticket" },
    { href: "/report", label: "Báo cáo vận hành" },
    // Sếp cũng cần tra chính sách khi quyết định — backend /policy-search đã
    // mở cho supervisor sẵn trong authority-matrix, chỉ thiếu lối vào ở nav.
    { href: "/policy-lookup", label: "Tra cứu chính sách" },
  ],
  partner_admin: [{ href: "/knowledge", label: "Chính sách & FAQ" }],
};

const GROUP_LABEL: Record<Role, string> = {
  customer: "Khách hàng",
  cskh: "CSKH",
  supervisor: "Sếp",
  partner_admin: "Đối tác ví",
};

export default function RoleTabNav({ role }: { role: Role }) {
  const pathname = usePathname();
  // 26/08 — chuẩn ngành: một hàng chỉ có ĐÚNG MỘT tab không phải điều hướng,
  // nó là một nhãn chiếm trọn một hàng khung. customer/partner_admin chỉ có
  // 1 màn nên KHÔNG render hàng này — cskh/supervisor (nhiều tab) giữ nguyên.
  // `?? []` phòng TABS[role] undefined (vai lạ) làm nổ .length ở layout —
  // vỡ TOÀN TRANG thay vì chỉ ẩn tab, dù hôm nay vai luôn là 1-trong-4 giá
  // trị hợp lệ từ session đã lọc.
  const tabs = TABS[role] ?? [];
  if (tabs.length <= 1) return null;
  return (
    <nav className="tabnav">
      <div className="tabgroup">
        <span className="tabgroup-label">{GROUP_LABEL[role]}</span>
        {tabs.map((tab) => (
          <Link
            key={tab.href}
            href={tab.href}
            className={`tab-btn${pathname.startsWith(tab.href) ? " active" : ""}`}
          >
            {tab.label}
          </Link>
        ))}
      </div>
    </nav>
  );
}
