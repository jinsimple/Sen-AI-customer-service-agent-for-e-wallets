"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  getUnreadNotificationCount,
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  presenceHeartbeat,
} from "@/lib/api";
import { COMPLAINT_TYPE_LABEL, NOTIFICATION_EVENT_LABEL, PRIORITY_LABEL, SCOPE_LABEL, labelOf, type NotificationItem } from "@/lib/types";
import { useI18n } from "@/lib/i18n/client";
import type { TFn } from "@/lib/i18n/core";
import { formatSlaRemaining } from "@/lib/format";

// ADR-063 — MVP polling ~20s (WebSocket là đợt nâng cấp sau, KHÔNG làm ở
// đây). Gộp heartbeat presence CÙNG vòng poll unread-count — một chu kỳ,
// hai việc, đúng khuôn thiết kế đã chốt ("poll unread-count gộp cùng vòng
// heartbeat"), không tự ý tách thành 2 interval riêng.
const POLL_MS = 20_000;

function thoiGianTuongDoi(iso: string, t: TFn): string {
  const giay = (Date.now() - new Date(iso).getTime()) / 1000;
  if (giay < 60) return t("time.justNow");
  if (giay < 3600) return t("time.minutesAgo", { n: Math.floor(giay / 60) });
  if (giay < 86400) return t("time.hoursAgo", { n: Math.floor(giay / 3600) });
  return t("time.daysAgo", { n: Math.floor(giay / 86400) });
}

export default function NotificationBell() {
  const router = useRouter();
  const { t, lang } = useI18n();
  const [unreadCount, setUnreadCount] = useState(0);
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<NotificationItem[] | null>(null);
  const wrapRef = useRef<HTMLDivElement>(null);

  const refreshUnreadCount = useCallback(() => {
    getUnreadNotificationCount()
      .then((r) => setUnreadCount(r.unread_count))
      .catch(() => {
        // Lỗi mạng lẻ tẻ — KHÔNG hiện lỗi chắn màn cho một badge phụ trợ.
        // Giữ nguyên số cũ, vòng poll sau tự thử lại.
      });
  }, []);

  useEffect(() => {
    refreshUnreadCount();
    const id = setInterval(() => {
      presenceHeartbeat().catch(() => {});
      refreshUnreadCount();
    }, POLL_MS);
    return () => clearInterval(id);
  }, [refreshUnreadCount]);

  useEffect(() => {
    if (!open) return;
    listNotifications()
      .then((r) => setItems(r.items))
      .catch(() => setItems([]));
    function onClickOutside(e: MouseEvent) {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [open]);

  async function onItemClick(item: NotificationItem) {
    setOpen(false);
    if (!item.read_at) {
      // Cập nhật UI NGAY (không đợi round-trip) — đánh dấu đọc thật chạy nền,
      // lỗi mạng ở bước này không nên chặn việc điều hướng tới vé.
      setUnreadCount((n) => Math.max(0, n - 1));
      markNotificationRead(item.notification_id).catch(() => {});
    }
    router.push(`/tickets/${item.ticket_id}`);
  }

  async function onMarkAllRead() {
    setUnreadCount(0);
    setItems((prev) => (prev ? prev.map((i) => ({ ...i, read_at: i.read_at ?? new Date().toISOString() })) : prev));
    try {
      await markAllNotificationsRead();
    } catch {
      // Poll kế tiếp (≤20s) tự chỉnh lại số nếu lệch — không cần retry tay.
    }
  }

  return (
    <div className="user-menu" ref={wrapRef}>
      <button
        type="button"
        className="user-menu-trigger notif-bell-trigger"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={unreadCount > 0 ? t("notif.unreadAria", { n: unreadCount }) : t("notif.title")}
        onClick={() => setOpen((v) => !v)}
      >
        <svg className="icon icon-sm" viewBox="0 0 24 24">
          <path d="M18 8a6 6 0 10-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.73 21a2 2 0 01-3.46 0" />
        </svg>
        {unreadCount > 0 && <span className="notif-badge">{unreadCount > 99 ? "99+" : unreadCount}</span>}
      </button>
      {open && (
        <div className="user-menu-dropdown notif-dropdown" role="menu">
          <div className="notif-dropdown-header">
            <b>{t("notif.title")}</b>
            {unreadCount > 0 && (
              <button type="button" className="notif-mark-all" onClick={() => void onMarkAllRead()}>
                {t("notif.markAll")}
              </button>
            )}
          </div>
          {items === null && <div className="notif-empty">{t("common.loading")}</div>}
          {items !== null && items.length === 0 && <div className="notif-empty">{t("notif.empty")}</div>}
          {items !== null &&
            items.map((item) => (
              <button
                key={item.notification_id}
                type="button"
                className={`notif-item${item.read_at ? "" : " notif-item-unread"}`}
                onClick={() => void onItemClick(item)}
              >
                <span className="notif-item-label">{labelOf(NOTIFICATION_EVENT_LABEL, item.event_type, lang)}</span>
                <span className="notif-item-ticket">{item.ticket_id}</span>
                {/* [polish trước quay 04/09] loại/phạm vi/ưu tiên/SLA — non-PII,
                    join-tại-lúc-đọc (xem GET /notifications, main.py). Có thể
                    null (vé/khiếu nại đã bị xoá giữa lúc tạo noti và lúc đọc —
                    hiếm nhưng KHÔNG loại trừ được) — ẩn cả dòng khi vậy thay vì
                    hiện "—" rối mắt trên một panel vốn đã chật. */}
                {item.complaint_type && (
                  <span className="notif-item-meta" style={{ display: "flex", gap: 6, flexWrap: "wrap", fontSize: 12 }}>
                    <span className="badge badge-neutral">{labelOf(COMPLAINT_TYPE_LABEL, item.complaint_type, lang)}</span>
                    {item.scope && <span className="badge badge-neutral">{labelOf(SCOPE_LABEL, item.scope, lang)}</span>}
                    {item.priority === "critical" ? (
                      <span className="badge badge-critical">{labelOf(PRIORITY_LABEL, item.priority, lang)}</span>
                    ) : item.priority && item.priority !== "normal" ? (
                      <span className="badge badge-warning">{labelOf(PRIORITY_LABEL, item.priority, lang)}</span>
                    ) : null}
                    {item.sla_due_at && (
                      <span className="mono" style={{ color: "var(--text-dim)" }}>
                        {formatSlaRemaining(item.sla_due_at, lang).label}
                      </span>
                    )}
                  </span>
                )}
                <span className="notif-item-time">{thoiGianTuongDoi(item.created_at, t)}</span>
              </button>
            ))}
        </div>
      )}
    </div>
  );
}
