"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export default function TopbarActions({ fullName, role }: { fullName: string; role: string }) {
  const router = useRouter();
  const [theme, setTheme] = useState<"light" | "dark">("light");

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

  function toggleTheme() {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("fin05-theme", next);
  }

  async function logout() {
    await fetch("/api/session", { method: "DELETE" });
    router.push("/login");
    router.refresh();
  }

  const roleLabel = role === "cskh" ? "CSKH" : role === "supervisor" ? "Sếp" : "Khách hàng";

  return (
    <div className="topbar-actions">
      <button className="theme-toggle" onClick={toggleTheme} type="button">
        <svg className="icon icon-sm" viewBox="0 0 24 24">
          {theme === "dark" ? (
            <path d="M12 3v2m0 14v2m9-9h-2M5 12H3m15.36 6.36l-1.42-1.42M7.05 7.05L5.64 5.64m12.72 0l-1.41 1.41M7.05 16.95l-1.41 1.41M12 8a4 4 0 100 8 4 4 0 000-8z" />
          ) : (
            <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z" />
          )}
        </svg>
        {theme === "dark" ? "Chế độ sáng" : "Chế độ tối"}
      </button>
      <span className="who-pill" style={{ cursor: "default" }}>
        {roleLabel} — {fullName}
      </span>
      <button className="theme-toggle" onClick={logout} type="button">
        <svg className="icon icon-sm" viewBox="0 0 24 24">
          <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" />
          <path d="M16 17l5-5-5-5M21 12H9" />
        </svg>
        Đăng xuất
      </button>
    </div>
  );
}
