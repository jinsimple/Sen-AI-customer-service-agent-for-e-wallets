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
  return (
    <nav className="tabnav">
      <div className="tabgroup">
        <span className="tabgroup-label">{GROUP_LABEL[role]}</span>
        {TABS[role].map((tab) => (
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
