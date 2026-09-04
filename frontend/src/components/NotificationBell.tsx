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
import { NOTIFICATION_EVENT_LABEL, type NotificationItem } from "@/lib/types";

// ADR-063 — MVP polling ~20s (WebSocket là đợt nâng cấp sau, KHÔNG làm ở
// đây). Gộp heartbeat presence CÙNG vòng poll unread-count — một chu kỳ,
// hai việc, đúng khuôn thiết kế đã chốt ("poll unread-count gộp cùng vòng
// heartbeat"), không tự ý tách thành 2 interval riêng.
const POLL_MS = 20_000;

function thoiGianTuongDoi(iso: string): string {
  const giay = (Date.now() - new Date(iso).getTime()) / 1000;
  if (giay < 60) return "vừa xong";
  if (giay < 3600) return `${Math.floor(giay / 60)} phút trước`;
  if (giay < 86400) return `${Math.floor(giay / 3600)} giờ trước`;
  return `${Math.floor(giay / 86400)} ngày trước`;
}

export default function NotificationBell() {
  const router = useRouter();
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
        aria-label={unreadCount > 0 ? `${unreadCount} thông báo chưa đọc` : "Thông báo"}
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
            <b>Thông báo</b>
            {unreadCount > 0 && (
              <button type="button" className="notif-mark-all" onClick={() => void onMarkAllRead()}>
                Đánh dấu tất cả đã đọc
              </button>
            )}
          </div>
          {items === null && <div className="notif-empty">Đang tải…</div>}
          {items !== null && items.length === 0 && <div className="notif-empty">Chưa có thông báo nào.</div>}
          {items !== null &&
            items.map((item) => (
              <button
                key={item.notification_id}
                type="button"
                className={`notif-item${item.read_at ? "" : " notif-item-unread"}`}
                onClick={() => void onItemClick(item)}
              >
                <span className="notif-item-label">{NOTIFICATION_EVENT_LABEL[item.event_type]}</span>
                <span className="notif-item-ticket">{item.ticket_id}</span>
                <span className="notif-item-time">{thoiGianTuongDoi(item.created_at)}</span>
              </button>
            ))}
        </div>
      )}
    </div>
  );
}
