"use client";

import { useCallback, useEffect, useRef, useState } from "react";

// Live chat (2026-08-11) — a WebSocket connection DIRECTLY to Caddy -> backend (route
// /ws/live-chat, see the Caddyfile) using a single-use ticket minted through the BFF
// (lib/api.ts::requestLiveChatWsTicket/requestStaffWsTicket) — NOT through the BFF for the WS
// connection itself (the browser can't attach an Authorization header to `new WebSocket()`, and a
// real JWT must never go into a query param). The URL uses the SAME origin as the current page
// (window.location.host) — Caddy serves both the frontend and /ws/live-chat under 1 domain, so the
// browser doesn't need to, and must not, know the real backend address (keeping the BFF invariant
// intact).

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
  // "connecting" is a DERIVED value (no setState inside the effect — to avoid a cascading render,
  // see react-hooks/set-state-in-effect): "idle" while a wsTicket already exists means a connection
  // is in the process of opening.
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
