"use client";

import { useCallback, useEffect, useRef, useState } from "react";

// Live chat (2026-08-11) — kết nối WebSocket TRỰC TIẾP tới Caddy -> backend
// (route /ws/live-chat, xem Caddyfile) bằng vé dùng-1-lần mint qua BFF
// (lib/api.ts::requestLiveChatWsTicket/requestStaffWsTicket) — KHÔNG qua
// BFF cho chính kết nối WS (browser không gắn được Authorization header vào
// `new WebSocket()`, và JWT thật không bao giờ nhét vào query param). URL
// dùng CÙNG origin với trang hiện tại (window.location.host) — Caddy phục
// vụ cả frontend lẫn /ws/live-chat dưới 1 domain, trình duyệt không cần và
// không được biết địa chỉ backend thật (giữ nguyên bất biến BFF).

export interface LiveChatContext {
  ticket: { ticket_id: string; hitl_status: string; sla_due_at: string; human_handoff_requested: boolean };
  complaint: {
    complaint_id: string;
    type: string;
    scope: string;
    priority: string;
    trans_id: string | null;
    description_raw: string;
    fraud_signals: string[];
  } | null;
  customer: { user_id: string; full_name: string; phone: string } | null;
  investigation_logs: {
    step_no: number;
    tool_called: string;
    tool_input_json: unknown;
    agent_note: string | null;
    created_at: string;
  }[];
}

export type LiveChatEvent =
  | { type: "message"; message_id: string; chat_session_id: string; role: "customer" | "staff"; content: string; created_at: string }
  | { type: "system"; text: string }
  | { type: "queue_update"; waiting: number }
  | { type: "claim_success"; chat_session_id: string; context: LiveChatContext }
  | { type: "session_claimed"; chat_session_id: string }
  | { type: "session_closed"; chat_session_id: string }
  | { type: "error"; text: string };

export type LiveChatStatus = "idle" | "connecting" | "open" | "closed" | "error";

export function useLiveChatSocket(wsTicket: string | null, onEvent: (event: LiveChatEvent) => void) {
  // "connecting" là giá trị SUY RA (không setState trong effect — tránh
  // cascading render, xem react-hooks/set-state-in-effect): còn "idle" mà đã
  // có wsTicket nghĩa là đang trong quá trình mở kết nối.
  const [rawStatus, setRawStatus] = useState<Exclude<LiveChatStatus, "connecting">>("idle");
  const status: LiveChatStatus = wsTicket && rawStatus === "idle" ? "connecting" : rawStatus;
  const wsRef = useRef<WebSocket | null>(null);
  const onEventRef = useRef(onEvent);
  useEffect(() => {
    onEventRef.current = onEvent;
  }, [onEvent]);

  useEffect(() => {
    if (!wsTicket) return;
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const url = `${protocol}//${window.location.host}/ws/live-chat?ticket=${encodeURIComponent(wsTicket)}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setRawStatus("open");
    ws.onclose = () => setRawStatus("closed");
    ws.onerror = () => setRawStatus("error");
    ws.onmessage = (evt) => {
      try {
        onEventRef.current(JSON.parse(evt.data) as LiveChatEvent);
      } catch {
        // bỏ qua message không phải JSON hợp lệ — không nên xảy ra với
        // server tự viết, nhưng không để 1 frame lỗi làm crash cả kết nối.
      }
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [wsTicket]);

  const sendMessage = useCallback((chatSessionId: string, content: string): boolean => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) return false;
    wsRef.current.send(JSON.stringify({ type: "send_message", chat_session_id: chatSessionId, content }));
    return true;
  }, []);

  return { status, sendMessage };
}
