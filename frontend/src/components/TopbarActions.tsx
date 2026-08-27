"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import EnvBadge from "./EnvBadge";

// 26/08 — chuẩn ngành: gom nút theme + viên tên (who-pill, trông như nút
// nhưng KHÔNG bấm được) + nút đăng xuất thành MỘT nút người dùng có menu thả
// xuống. EnvBadge KHÔNG đụng — cố ý nổi bật nhất thanh đầu (ADR-009), không
// cào bằng chung nhóm "tiện ích".
//
// Đăng xuất tách khỏi nhóm trên bằng đường kẻ + màu --danger — trước đó nó
// dùng CHUNG class "theme-toggle" với nút đổi theme, trông giống hệt nhau dù
// hậu quả khác hẳn (một cái đổi màu nền, một cái KẾT THÚC PHIÊN LÀM VIỆC).

// Quy ước gọi tên người Việt: gọi bằng TÊN (từ cuối), không bằng HỌ — "chị
// Anh", không phải "chị Hồ". Phòng tên rỗng/một từ/khoảng trắng thừa vì đây
// là chữ hiện ở MỌI màn của MỌI vai, không được phép vỡ.
function chuCaiTenGoi(fullName: string): string {
  const parts = fullName.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  return parts[parts.length - 1][0]?.toUpperCase() ?? "?";
}

export default function TopbarActions({ fullName, role }: { fullName: string; role: string }) {
  const router = useRouter();
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const itemRefs = useRef<(HTMLButtonElement | null)[]>([]);

  useEffect(() => {
    void Promise.resolve().then(() => {
      const saved = (typeof window !== "undefined" && localStorage.getItem("fin05-theme")) as
        | "light"
        | "dark"
        | null;
      if (saved) {
        setTheme(saved);
        document.documentElement.setAttribute("data-theme", saved);
      }
    });
  }, []);

  useEffect(() => {
    if (!open) return;
    itemRefs.current[0]?.focus();
    function onClickOutside(e: MouseEvent) {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [open]);

  function toggleTheme() {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("fin05-theme", next);
  }

  // 27/08 — PO báo: đăng xuất LUÔN đá về /login (cổng khách), kể cả với
  // nhân viên. Vì gate là mỗi cổng CHỈ CHẤP NHẬN đúng vai của mình
  // (useLoginForm.ts, server so gate với role và TỪ CHỐI nếu lệch — xem
  // route.ts::gateRejects), nhân viên bị đá sang /login là NGÕ CỤT: không tự
  // đăng nhập lại được ở đó, và trang công khai "/" cũng không có đường nào
  // dẫn tới /dang-nhap-noi-bo. Component này đã nhận `role` sẵn (dùng cho
  // roleLabel ngay dưới) — chỉ là chỗ điều hướng không tra nó trước khi đó.
  const loginPath = role === "customer" ? "/login" : "/dang-nhap-noi-bo";

  async function logout() {
    await fetch("/api/session", { method: "DELETE" });
    router.push(loginPath);
    router.refresh();
  }

  const roleLabel = role === "cskh" ? "CSKH" : role === "supervisor" ? "Sếp" : role === "partner_admin" ? "Đối tác ví" : "Khách hàng";
  const items = itemRefs.current;

  function onTriggerKeyDown(e: React.KeyboardEvent) {
    if (e.key === "ArrowDown" || e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      setOpen(true);
    }
  }

  function onMenuKeyDown(e: React.KeyboardEvent<HTMLButtonElement>, idx: number) {
    if (e.key === "Escape") {
      e.preventDefault();
      setOpen(false);
      triggerRef.current?.focus();
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      items[(idx + 1) % items.length]?.focus();
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      items[(idx - 1 + items.length) % items.length]?.focus();
    } else if (e.key === "Tab") {
      setOpen(false);
    }
  }

  return (
    <div className="topbar-actions">
      {/* Nhãn môi trường đứng ĐẦU TIÊN, trước mọi thứ khác — nếu 2 cửa sổ
          hiện 2 nhãn khác nhau thì biết ngay đang lệch stack. Xem ADR-009. */}
      <EnvBadge compact />
      <div className="user-menu" ref={wrapRef}>
        <button
          ref={triggerRef}
          type="button"
          className="user-menu-trigger"
          aria-haspopup="menu"
          aria-expanded={open}
          onClick={() => setOpen((v) => !v)}
          onKeyDown={onTriggerKeyDown}
        >
          <span className="user-menu-avatar">{chuCaiTenGoi(fullName)}</span>
          <span className="user-menu-name">{fullName}</span>
          <svg className="icon icon-sm" viewBox="0 0 24 24">
            <path d="M6 9l6 6 6-6" />
          </svg>
        </button>
        {open && (
          <div className="user-menu-dropdown" role="menu">
            <div className="user-menu-header">
              <b>{roleLabel}</b>
              <span>{fullName}</span>
            </div>
            <button
              ref={(el) => {
                itemRefs.current[0] = el;
              }}
              type="button"
              role="menuitem"
              className="user-menu-item"
              onClick={() => toggleTheme()}
              onKeyDown={(e) => onMenuKeyDown(e, 0)}
            >
              <svg className="icon icon-sm" viewBox="0 0 24 24">
                {theme === "dark" ? (
                  <path d="M12 3v2m0 14v2m9-9h-2M5 12H3m15.36 6.36l-1.42-1.42M7.05 7.05L5.64 5.64m12.72 0l-1.41 1.41M7.05 16.95l-1.41 1.41M12 8a4 4 0 100 8 4 4 0 000-8z" />
                ) : (
                  <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z" />
                )}
              </svg>
              {theme === "dark" ? "Chế độ sáng" : "Chế độ tối"}
            </button>
            <div className="user-menu-divider" />
            <button
              ref={(el) => {
                itemRefs.current[1] = el;
              }}
              type="button"
              role="menuitem"
              className="user-menu-item user-menu-item-danger"
              onClick={() => void logout()}
              onKeyDown={(e) => onMenuKeyDown(e, 1)}
            >
              <svg className="icon icon-sm" viewBox="0 0 24 24">
                <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" />
                <path d="M16 17l5-5-5-5M21 12H9" />
              </svg>
              Đăng xuất
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
