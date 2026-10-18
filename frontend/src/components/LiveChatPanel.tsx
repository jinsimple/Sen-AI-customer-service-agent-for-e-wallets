"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  claimChatSession,
  closeChatSession,
  getChatSessionByTicket,
  getLiveChatMessages,
  requestLiveChatWsTicket,
  requestStaffWsTicket,
  submitChatCsat,
} from "@/lib/api";
import { useLiveChatSocket, type LiveChatContext, type LiveChatEvent } from "@/lib/useLiveChatSocket";
import { COMPLAINT_TYPE_LABEL, SCOPE_LABEL, labelOf } from "@/lib/types";
import { useI18n } from "@/lib/i18n/client";
import { docLang, translate } from "@/lib/i18n/core";

// Live chat (2026-08-11) — a panel SHARED by both the customer (the /chat page) and
// support/supervisor (the panel inside TicketDetailClient), reusing the EXACT CSS classes already
// used in ChatClient.tsx (.chat-panel/.chat-thread/.bubble-*) — no new classes invented. NO
// financial-action button of any kind here — consistent with the absolute HITL rule (only /approve
// ever writes approved), this panel is ONLY for reading/typing text.

interface LiveChatPanelProps {
  ticketId: string;
  viewerRole: "customer" | "cskh" | "supervisor";
  viewerUserId?: string; // required in practice for staff — used to tell "I claimed this
  // ticket" apart from "someone ELSE claimed it" when reopening the panel (e.g. a supervisor
  // viewing a ticket another support agent is handling — must not be treated as claimedByMe).
}

interface LocalMessage {
  key: string;
  role: "customer" | "staff" | "system";
  content: string;
}

export default function LiveChatPanel({ ticketId, viewerRole, viewerUserId }: LiveChatPanelProps) {
  const { t, lang } = useI18n();
  const isStaff = viewerRole !== "customer";
  const [wsTicket, setWsTicket] = useState<string | null>(null);
  const [chatSessionId, setChatSessionId] = useState<string | null>(null);
  const [claimedByMe, setClaimedByMe] = useState(false);
  const [waitingUnclaimed, setWaitingUnclaimed] = useState(false);
  const [context, setContext] = useState<LiveChatContext | null>(null);
  const [messages, setMessages] = useState<LocalMessage[]>([]);
  const [input, setInput] = useState("");
  const [csatSubmitted, setCsatSubmitted] = useState(false);
  // The BUSINESS status of the session (the server says it's closed), DIFFERENT from `status` in
  // useLiveChatSocket (the WEBSOCKET connection's OWN state) — the two concepts must not be
  // confused: a dropped connection (status="closed") doesn't mean the support agent actually ended
  // the chat session.
  const [sessionClosed, setSessionClosed] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  // A real finding (2026-08-11): after sending, the input box sometimes still shows a leftover
  // fragment of what was just typed even though setInput("") ran (a race between React state and
  // the real DOM input — the exact trigger hasn't been pinned down). Forces React to fully REMOUNT
  // the <input> (changing its key) after every successful send — guaranteed clean regardless of the
  // precise timing cause.
  const [inputResetKey, setInputResetKey] = useState(0);
  const threadRef = useRef<HTMLDivElement>(null);

  const handleEvent = useCallback(
    (event: LiveChatEvent) => {
      if (event.type === "message") {
        // Dedupe by message_id — a second layer of defence: even if the server/connection
        // duplicates and sends the same message more than once (a real finding, 2026-08-11,
        // messages showing up "split apart"), the UI still never shows a duplicate.
        setMessages((prev) => (prev.some((m) => m.key === event.message_id) ? prev : [...prev, { key: event.message_id, role: event.role, content: event.content }]));
      } else if (event.type === "system") {
        setMessages((prev) => [...prev, { key: `sys-${prev.length}-${Date.now()}`, role: "system", content: event.text }]);
      } else if (event.type === "claim_success") {
        setClaimedByMe(true);
        setWaitingUnclaimed(false);
        setChatSessionId(event.chat_session_id);
        setContext(event.context);
      } else if (event.type === "session_claimed" && event.chat_session_id === chatSessionId) {
        setWaitingUnclaimed(false);
      } else if (event.type === "session_closed") {
        setSessionClosed(true);
      } else if (event.type === "error") {
        setMessages((prev) => [...prev, { key: `err-${prev.length}-${Date.now()}`, role: "system", content: event.text }]);
      }
    },
    [chatSessionId]
  );

  const { status, sendMessage } = useLiveChatSocket(wsTicket, handleEvent);

  useEffect(() => {
    threadRef.current?.scrollTo({ top: threadRef.current.scrollHeight });
  }, [messages]);

  // A leave-page warning (2026-08-11, a real finding from manual testing) — F5/closing the tab
  // mid-chat gives the support agent NO warning, the session closes "silently" at the server layer
  // (see release_staff_sessions). Modern browsers (Chrome/Firefox/Safari, since ~2011) don't allow
  // customising the native dialog's CONTENT — you can only control WHETHER a confirmation dialog
  // appears, you can't write your own Vietnamese sentence into it.
  useEffect(() => {
    if (chatSessionId === null || sessionClosed) return;
    if (isStaff && !claimedByMe) return;
    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = "";
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [chatSessionId, sessionClosed, isStaff, claimedByMe]);

  // React StrictMode runs an effect twice on mount to catch missing cleanup — without a guard, that
  // mints 2 ws-tickets + opens 2 WS connections for the SAME mount (a real finding, 2026-08-11: the
  // exact cause of messages getting duplicated/split when sending — 2 connections both active, both
  // receiving the broadcast). Same ref-guard pattern ChatClient.tsx already uses for the greeting
  // effect (around line 168) — the ref survives those 2 mount/unmount cycles (unlike state),
  // blocking it down to exactly one real run.
  const connectStartedRef = useRef(false);

  useEffect(() => {
    if (connectStartedRef.current) return;
    connectStartedRef.current = true;
    let cancelled = false;
    (async () => {
      try {
        if (!isStaff) {
          const res = await requestLiveChatWsTicket(ticketId);
          if (cancelled) return;
          setChatSessionId(res.chat_session_id);
          setWsTicket(res.ws_ticket);
          return;
        }
        const [existing, staffTicket] = await Promise.all([getChatSessionByTicket(ticketId), requestStaffWsTicket()]);
        if (cancelled) return;
        setWsTicket(staffTicket.ws_ticket);
        if (existing.chat_session) {
          setChatSessionId(existing.chat_session.chat_session_id);
          setWaitingUnclaimed(existing.chat_session.status === "waiting" && existing.chat_session.claimed_by === null);
          setClaimedByMe(existing.chat_session.status === "active" && existing.chat_session.claimed_by === viewerUserId);
          // A closed session (the customer hit F5/left —
          // release_staff_sessions/close_customer_session_on_disconnect) still needs to show its
          // HISTORY + the customer's phone number so the support agent can reach back out, not only
          // while waiting/active.
          setSessionClosed(existing.chat_session.status === "closed");
          if (existing.context) setContext(existing.context);
          const history = await getLiveChatMessages(existing.chat_session.chat_session_id);
          if (cancelled) return;
          setMessages((prev) => {
            const seen = new Set(prev.map((m) => m.key));
            const fromHistory = history.messages
              .filter((m) => (m.role === "customer" || m.role === "staff") && !seen.has(m.message_id))
              .map((m) => ({ key: m.message_id, role: m.role as "customer" | "staff", content: m.content }));
            return [...fromHistory, ...prev];
          });
        }
      } catch (e) {
        // Don't let an error opening a chat session (e.g. 403/429/5xx) silently vanish — a real
        // finding, 2026-08-11: the old OTP gate was blocking this route invisibly, so the customer
        // clicked "talk to a human" and saw nothing happen, assuming the feature was broken.
        if (!cancelled) {
          setLoadError(e instanceof Error ? e.message : translate(docLang(), "live.openError"));
        }
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ticketId]);

  const handleClaim = async () => {
    if (!chatSessionId) return;
    try {
      await claimChatSession(chatSessionId);
      // The real result (context/claimedByMe) arrives via the "claim_success" WS push —
      // don't set state directly here, to avoid two sources of truth drifting apart.
    } catch {
      setMessages((prev) => [...prev, { key: `claim-err-${Date.now()}`, role: "system", content: t("live.claimedByOther") }]);
      setWaitingUnclaimed(false);
    }
  };

  // A temporary send lock — a real finding, 2026-08-11: a single Enter press sometimes triggered
  // handleSend several times in a row (suspected to be a duplicated keydown event/duplicate
  // component mount, exact root cause not pinned down), sending a duplicate message even though the
  // user only acted once. A 400ms lock is enough to block near-simultaneous double-fires without
  // blocking genuinely sending several messages in quick succession.
  const sendingRef = useRef(false);

  const handleSend = () => {
    if (!chatSessionId || !input.trim() || sendingRef.current) return;
    sendingRef.current = true;
    window.setTimeout(() => {
      sendingRef.current = false;
    }, 400);
    if (sendMessage(chatSessionId, input.trim())) {
      setInput("");
      setInputResetKey((k) => k + 1);
    }
  };

  const handleCsat = async (score: number) => {
    if (!chatSessionId) return;
    await submitChatCsat(chatSessionId, score);
    setCsatSubmitted(true);
  };

  const handleClose = async () => {
    if (!chatSessionId) return;
    await closeChatSession(chatSessionId);
    setSessionClosed(true);
  };

  const connectionLabel =
    status === "connecting"
      ? t("live.connecting")
      : status === "open"
        ? t("live.connected")
        : status === "closed"
          ? t("live.disconnected")
          : status === "error"
            ? t("live.connError")
            : "";

  if (loadError) {
    return (
      <div className="card">
        <div className="note" style={{ borderColor: "var(--danger)" }}>{loadError}</div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="chat-head">
        <div className="chat-avatar">{isStaff ? "K" : "CS"}</div>
        <div>
          <div className="name">{isStaff ? t("live.withCustomer") : t("live.withAgent")}</div>
          <div className="status">{connectionLabel}</div>
        </div>
      </div>

      {isStaff && context && (
        <div className="bubble-cite" style={{ margin: "8px 0" }}>
          {t("live.aiContext")} {labelOf(COMPLAINT_TYPE_LABEL, context.complaint?.type, lang) ?? context.complaint?.type ?? "—"} ·{" "}
          {labelOf(SCOPE_LABEL, context.complaint?.scope, lang) ?? context.complaint?.scope ?? "—"} · trans_id:{" "}
          {context.complaint?.trans_id ?? t("live.undetermined")}
          {context.customer && (
            <>
              {" · "}
              {context.customer.full_name} · {t("live.phone")} <strong>{context.customer.phone}</strong>
            </>
          )}
        </div>
      )}
      {isStaff && sessionClosed && (
        <div className="note" style={{ marginBottom: 8 }}>
          {t("live.ended")}
        </div>
      )}

      {isStaff && waitingUnclaimed && (
        <button className="btn btn-primary" onClick={handleClaim} style={{ marginBottom: 8 }}>
          {t("live.claim")}
        </button>
      )}

      {isStaff && claimedByMe && !sessionClosed && (
        <button className="btn btn-outline" onClick={handleClose} style={{ marginBottom: 8 }}>
          {t("live.end")}
        </button>
      )}

      <div className="chat-thread" ref={threadRef} style={{ maxHeight: 360 }}>
        {messages.map((m) => {
          if (m.role === "system") {
            return (
              <div className="bubble-row" key={m.key}>
                <div className="bubble-system">{m.content}</div>
              </div>
            );
          }
          const isOwn = (isStaff && m.role === "staff") || (!isStaff && m.role === "customer");
          return (
            <div className={`bubble-row ${isOwn ? "from-user" : "from-bot"}`} key={m.key}>
              <div className={`bubble ${isOwn ? "bubble-user" : "bubble-bot"}`}>{m.content}</div>
            </div>
          );
        })}
      </div>

      {!sessionClosed && (
        <div className="chat-input">
          <input
            key={inputResetKey}
            placeholder={isStaff && !claimedByMe ? t("live.claimToReply") : t("live.typeMessage")}
            value={input}
            disabled={isStaff && !claimedByMe}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              // isComposing/repeat: ignore an Enter that comes from a Vietnamese input method
              // mid-composition (Unikey/OpenKey) or from a held-down repeating key — send EXACTLY
              // once per one real Enter press from the user.
              if (e.key === "Enter" && !e.nativeEvent.isComposing && !e.repeat) handleSend();
            }}
            maxLength={4000}
          />
          <button className="btn btn-primary" onClick={handleSend} disabled={isStaff && !claimedByMe}>
            {t("live.send")}
          </button>
        </div>
      )}

      {!isStaff && sessionClosed && !csatSubmitted && (
        <div style={{ marginTop: 12 }}>
          <div className="status">{t("live.rate")}</div>
          <div style={{ display: "flex", gap: 4, marginTop: 4 }}>
            {[1, 2, 3, 4, 5].map((score) => (
              <span key={score} className="chip" onClick={() => handleCsat(score)}>
                {score}★
              </span>
            ))}
          </div>
        </div>
      )}
      {csatSubmitted && <div className="status" style={{ marginTop: 8 }}>{t("live.thanks")}</div>}
    </div>
  );
}
