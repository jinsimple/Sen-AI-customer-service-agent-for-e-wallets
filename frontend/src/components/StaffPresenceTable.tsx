"use client";

import { useEffect, useState } from "react";
import { ApiError, listStaffPresence } from "@/lib/api";
import type { StaffPresenceItem } from "@/lib/types";
import { useI18n } from "@/lib/i18n/client";

// ADR-063 — bảng "CSKH nào đang online" + số vé đang xử lý, CHỈ Sếp xem
// (route /presence/staff ép role ở tầng backend — component này không tự
// kiểm quyền, chỉ hiển thị). Poll cùng nhịp 20s với chuông (POLL_MS) — hai
// nơi định nghĩa riêng CÓ CHỦ ĐÍCH: bảng này và chuông là 2 mối quan tâm
// độc lập (một cái Sếp mới cần, một cái mọi nhân viên cần), gộp interval
// dùng chung sẽ ép hai component không liên quan phải biết về nhau.
const POLL_MS = 20_000;

export default function StaffPresenceTable() {
  const { t } = useI18n();
  const [items, setItems] = useState<StaffPresenceItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let huy = false;
    function tai() {
      listStaffPresence()
        .then((r) => {
          if (!huy) setItems(r.items);
        })
        .catch((e) => {
          if (!huy) setError(e instanceof ApiError ? e.message : t("presence.loadError"));
        });
    }
    tai();
    const id = setInterval(tai, POLL_MS);
    return () => {
      huy = true;
      clearInterval(id);
    };
  }, [t]);

  if (error) return <div className="note" style={{ borderColor: "var(--danger)" }}>{error}</div>;

  // [04/09] Sắp xếp mặc định PO chốt: online lên đầu, trong mỗi nhóm xếp
  // theo số vé đang xử lý giảm dần — ai đông việc nổi lên trước để dễ nhìn
  // phân bổ. Chỉ sắp xếp hiển thị, không đổi dữ liệu/API.
  const sapXep = items === null ? null : [...items].sort((a, b) => {
    if (a.online !== b.online) return a.online ? -1 : 1;
    return b.so_ve_dang_xu_ly - a.so_ve_dang_xu_ly;
  });

  return (
    <div className="card" style={{ marginBottom: 20 }}>
      <div className="card-title" style={{ marginBottom: 10 }}>{t("presence.title")}</div>
      {items === null && <div className="dim">{t("common.loading")}</div>}
      {items !== null && items.length === 0 && <div className="dim">{t("presence.empty")}</div>}
      {items !== null && items.length > 0 && (
        <table className="table">
          <thead>
            <tr>
              <th>{t("presence.colStaff")}</th>
              <th>{t("presence.colStatus")}</th>
              <th>{t("presence.colTickets")}</th>
            </tr>
          </thead>
          <tbody>
            {sapXep!.map((it) => (
              <tr key={it.user_id}>
                <td>{it.full_name}</td>
                <td>
                  <span className={`badge ${it.online ? "badge-success" : "badge-neutral"}`}>
                    {it.online ? t("presence.online") : t("presence.offline")}
                  </span>
                </td>
                <td>{it.so_ve_dang_xu_ly}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
