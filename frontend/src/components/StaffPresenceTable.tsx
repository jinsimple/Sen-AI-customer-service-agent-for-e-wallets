"use client";

import { useEffect, useState } from "react";
import { ApiError, listStaffPresence } from "@/lib/api";
import type { StaffPresenceItem } from "@/lib/types";
import { useI18n } from "@/lib/i18n/client";

// ADR-063 — the "which support agents are online" table plus their ticket counts, viewable by the
// SUPERVISOR ONLY (the /presence/staff route enforces the role at the backend layer — this
// component doesn't check permissions itself, it only displays). Polls at the same 20s cadence as
// the notification bell (POLL_MS) — defined separately in both places ON PURPOSE: this table and
// the bell are two INDEPENDENT concerns (one only the supervisor needs, the other every staff
// member needs); sharing one interval would force two unrelated components to know about each
// other.
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

  // [Sep 4] Default sort the PO decided on: online first, within each group sorted by descending
  // ticket count — whoever is busiest surfaces first for easier workload visibility. Display-only
  // sorting, doesn't change the data/API.
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
