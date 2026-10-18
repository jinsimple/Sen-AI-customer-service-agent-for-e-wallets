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

// Live chat (2026-08-11) — panel dùng CHUNG cho cả khách hàng (trang /chat)
// và CSKH/sếp (panel trong TicketDetailClient), tái dùng NGUYÊN class CSS đã
// có ở ChatClient.tsx (.chat-panel/.chat-thread/.bubble-*) — không tự chế
// class mới. KHÔNG có bất kỳ nút thao tác tài chính nào ở đây — nhất quán
// nguyên tắc HITL tuyệt đối (chỉ /approve mới ghi approved), panel này CHỈ
// xem/gõ chữ.

interface LiveChatPanelProps {
  ticketId: string;
  viewerRole: "customer" | "cskh" | "supervisor";
  viewerUserId?: string; // bắt buộc thực tế cho staff — dùng phân biệt "tôi
  // đã nhận ca này" với "người KHÁC đã nhận" khi mở lại panel (vd supervisor
  // xem 1 ticket CSKH khác đang xử lý — không được coi là claimedByMe).
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
  // Trạng thái NGHIỆP VỤ của phiên (server nói đã đóng), KHÁC với `status`
  // của useLiveChatSocket (trạng thái CHÍNH kết nối WebSocket) — 2 khái
  // niệm không được lẫn: mất mạng (status="closed") không có nghĩa CSKH đã
  // kết thúc phiên chat thật.
  const [sessionClosed, setSessionClosed] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  // Phát hiện thật (2026-08-11): sau khi gửi, ô nhập đôi khi còn sót lại
  // 1 phần chữ vừa gõ dù setInput("") đã chạy (đua giữa state React và DOM
  // input thật — chưa xác định chính xác trigger). Buộc React REMOUNT hẳn
  // <input> (đổi key) sau mỗi lần gửi thành công — chắc chắn sạch bất kể
  // nguyên nhân timing chính xác là gì.
  const [inputResetKey, setInputResetKey] = useState(0);
  const threadRef = useRef<HTMLDivElement>(null);

  const handleEvent = useCallback(
    (event: LiveChatEvent) => {
      if (event.type === "message") {
        // Dedupe theo message_id — phòng vệ 2 lớp: dù server/kết nối trùng
        // có gửi cùng 1 tin nhắn nhiều lần (phát hiện thật 2026-08-11, tin
        // nhắn hiện tượng "bị tách chữ"), UI vẫn không hiện trùng.
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

  // Cảnh báo rời trang (2026-08-11, phát hiện thật qua test tay) — F5/đóng
  // tab khi đang chat KHÔNG có gì báo trước cho CSKH, phiên tự đóng "âm
  // thầm" ở tầng server (xem release_staff_sessions). Trình duyệt hiện đại
  // (Chrome/Firefox/Safari, từ ~2011) không cho tuỳ biến NỘI DUNG hộp thoại
  // native — chỉ điều khiển được việc CÓ hiện hộp thoại xác nhận hay không,
  // không viết được câu tiếng Việt riêng vào đó.
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

  // React StrictMode chạy effect 2 lần lúc mount để bắt lỗi thiếu cleanup —
  // không chặn thì mint 2 ws-ticket + mở 2 kết nối WS cho CÙNG 1 lượt mount
  // (phát hiện thật 2026-08-11: đúng nguyên nhân tin nhắn bị lặp/tách khi
  // gửi — 2 kết nối cùng active, cùng nhận broadcast). Cùng pattern ref-guard
  // ChatClient.tsx đã dùng cho effect chào hỏi (dòng ~168) — ref sống sót
  // qua 2 lần mount/unmount đó (khác state), chặn được đúng 1 lần thật.
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
          // Phiên đã đóng (khách F5/thoát — release_staff_sessions/
          // close_customer_session_on_disconnect) vẫn phải hiện được LỊCH SỬ
          // + SĐT khách để CSKH liên hệ lại, không chỉ khi còn waiting/active.
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
        // Không để lỗi mở phiên chat (vd 403/429/5xx) rơi mất âm thầm — phát
        // hiện thật 2026-08-11: OTP-gate cũ chặn ngầm route này, khách bấm
        // "gặp người thật" xong không thấy gì xảy ra, tưởng tính năng hỏng.
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
      // Kết quả thật (context/claimedByMe) tới qua push WS "claim_success",
      // không set state trực tiếp ở đây — tránh 2 nguồn sự thật lệch nhau.
    } catch {
      setMessages((prev) => [...prev, { key: `claim-err-${Date.now()}`, role: "system", content: t("live.claimedByOther") }]);
      setWaitingUnclaimed(false);
    }
  };

  // Khoá gửi tạm thời — phát hiện thật 2026-08-11: 1 lần Enter đôi khi kích
  // hoạt handleSend nhiều lần liên tiếp (nghi do sự kiện keydown lặp/component
  // mount trùng chưa xác định được gốc rễ chính xác), gây gửi trùng tin nhắn
  // dù người dùng chỉ thao tác 1 lần. Khoá 400ms là đủ ngăn double-fire sát
  // nhau mà không cản trở gửi nhiều tin nhắn thật liên tục.
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
              // isComposing/repeat: bỏ qua Enter đến từ bộ gõ tiếng Việt đang
              // soạn thảo (Unikey/OpenKey) hoặc phím giữ lặp — chỉ gửi đúng 1
              // lần cho 1 lần bấm Enter thật của người dùng.
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
