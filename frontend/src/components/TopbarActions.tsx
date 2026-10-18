"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import EnvBadge from "./EnvBadge";
import NotificationBell from "./NotificationBell";
import LanguageToggle from "./LanguageToggle";
import { useI18n } from "@/lib/i18n/client";

// Aug 26 — industry convention: merge the theme button + the name pill (who-pill, which looked like
// a button but was NOT clickable) + the logout button into ONE user menu button with a dropdown.
// EnvBadge is left untouched — deliberately the most prominent thing in the topbar (ADR-009), not
// lumped into a generic "utilities" group.
//
// Logout is set apart from the group above by a divider + the --danger colour — it used to SHARE
// the "theme-toggle" class with the theme-switch button, looking identical despite very different
// consequences (one changes a background colour, the other ENDS THE WORKING SESSION).

// Vietnamese naming convention: address people by their GIVEN name (the last word), not their
// family name — "chị Anh", not "chị Hồ". Guards against an empty/one-word/extra-whitespace name
// because this text appears on EVERY screen for EVERY role and must never break.
function chuCaiTenGoi(fullName: string): string {
  const parts = fullName.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  return parts[parts.length - 1][0]?.toUpperCase() ?? "?";
}

export default function TopbarActions({ fullName, role }: { fullName: string; role: string }) {
  const router = useRouter();
  const { t } = useI18n();
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

  // Aug 27 — PO reported: logout ALWAYS redirects to /login (the customer gate), even for staff.
  // Because each gate ONLY ACCEPTS its own role (useLoginForm.ts; the server compares the gate to
  // the role and REJECTS on a mismatch — see route.ts::gateRejects), staff being sent to /login is
  // a DEAD END: they can't log back in there, and the public "/" page has no path leading to
  // /dang-nhap-noi-bo either. This component already receives `role` (used for roleLabel right
  // below) — the navigation here simply wasn't reading it beforehand.
  const loginPath = role === "customer" ? "/login" : "/dang-nhap-noi-bo";

  async function logout() {
    await fetch("/api/session", { method: "DELETE" });
    router.push(loginPath);
    router.refresh();
  }

  const roleLabel =
    role === "cskh" ? t("role.cskh") : role === "supervisor" ? t("role.supervisor") : role === "partner_admin" ? t("role.partner_admin") : t("role.customer");
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
      <LanguageToggle />
      {/* ADR-063 — CHỈ cskh/supervisor có vé để nhận thông báo (customer/
          partner_admin không nằm trong luồng chuông). Đặt TRƯỚC user-menu
          — "trên-trái cạnh tên nhân viên" đúng brief. */}
      {(role === "cskh" || role === "supervisor") && <NotificationBell />}
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
              {theme === "dark" ? t("menu.lightMode") : t("menu.darkMode")}
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
              {t("menu.logout")}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
