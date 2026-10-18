"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { listWaitingChatSessions, requestStaffWsTicket } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import { useI18n } from "@/lib/i18n/client";
import { useLiveChatSocket, type LiveChatEvent } from "@/lib/useLiveChatSocket";
import type { Role } from "@/lib/session";
import TicketListSection, { type TicketListSectionHandle } from "@/components/TicketListSection";

interface WaitingChatSession {
  chat_session_id: string;
  ticket_id: string;
  customer_id: string;
  started_at: string;
}

// ADR-064(b) — trang này giờ cho CẢ cskh lẫn supervisor xem (Sếp dùng qua
// /quan-ly-ticket, route đó tái dùng /dashboard trước 04/09 — hiện đã tách
// riêng, nhưng /dashboard vẫn mở cho supervisor theo proxy.ts). `role` BẮT
// BUỘC truyền từ page.tsx (server, đọc session thật) — không đoán bằng dữ
// liệu ticket (vd "có claimed_by là cskh") vì Sếp cũng thấy y hệt field đó.
//
// [polish trước quay 04/09] Bảng ticket + bộ lọc + phân trang chuyển vào
// TicketListSection dùng chung với /quan-ly-ticket — trang này giữ lại phần
// RIÊNG của CSKH: banner khách chờ chat trực tiếp + WS staff ticket.
export default function DashboardClient({ role }: { role: Role }) {
  const router = useRouter();
  const { t, lang } = useI18n();
  const [waitingChats, setWaitingChats] = useState<WaitingChatSession[]>([]);
  const ticketSectionRef = useRef<TicketListSectionHandle>(null);

  const loadWaitingChats = useCallback(() => {
    listWaitingChatSessions()
      .then((res) => setWaitingChats(res.sessions))
      .catch(() => {});
  }, []);

  useEffect(() => {
    loadWaitingChats();
    // Poll 60s làm lưới an toàn (vd WS mất kết nối tạm thời) — cập nhật
    // TỨC THỜI thật sự đến từ WS bên dưới (queue_update), không phải từ đây.
    // Lưới này phải phủ CẢ HAI nguồn: trước bản vá BUGREPRO-001 nó chỉ nạp
    // lại waitingChats, nên khi WS rớt thì bảng ticket + mọi chip đếm đứng
    // yên vô thời hạn mà không có dấu hiệu gì cho CSKH biết.
    const interval = setInterval(() => {
      loadWaitingChats();
      ticketSectionRef.current?.refresh();
    }, 60_000);
    return () => clearInterval(interval);
  }, [loadWaitingChats]);

  // Live chat (2026-08-11, phát hiện thật qua test tay) — CSKH đang đứng ở
  // Dashboard PHẢI thấy ticket chờ mới ngay khi khách bấm "gặp người thật",
  // không phải đợi refresh/poll — mở 1 kết nối WS staff riêng cho trang này
  // (KHÁC kết nối trong LiveChatPanel, vốn chỉ mở SAU KHI đã vào 1 ticket cụ
  // thể) chỉ để lắng nghe broadcast "queue_update" rồi fetch lại danh sách.
  const [staffWsTicket, setStaffWsTicket] = useState<string | null>(null);
  const wsConnectStartedRef = useRef(false);

  useEffect(() => {
    if (wsConnectStartedRef.current) return;
    wsConnectStartedRef.current = true;
    requestStaffWsTicket()
      .then((res) => setStaffWsTicket(res.ws_ticket))
      .catch(() => {});
  }, []);

  const handleDashboardWsEvent = useCallback(
    (event: LiveChatEvent) => {
      if (event.type === "queue_update" || event.type === "session_claimed") {
        loadWaitingChats();
        // BUGREPRO-001/002 (QA/QC test tay 12/08/2026, xác nhận lại bằng đọc
        // code 13/08) — TRƯỚC bản vá này chỉ `waitingChats` được nạp lại, còn
        // bảng ticket chỉ fetch ĐÚNG MỘT LẦN lúc mount. Mà chip "Khách yêu
        // cầu người thật" lại đếm từ đó, nên khách bấm "gặp người thật" xong
        // thì CSKH đang mở sẵn dashboard KHÔNG bao giờ thấy số đếm nhúc
        // nhích — đứng yên tới khi reload cả trang. Poll 60s cũng chỉ chạm
        // waitingChats, không cứu được — refresh() bên dưới mới cứu.
        ticketSectionRef.current?.refresh();
      }
    },
    [loadWaitingChats]
  );

  useLiveChatSocket(staffWsTicket, handleDashboardWsEvent);

  return (
    <>
      <div className="page-head">
        <span className="eyebrow">{t("eyebrow.cskh")}</span>
        <h1>{t("queue.title")}</h1>
        <p className="sub">
          {t("queue.sub")}
        </p>
      </div>

      {waitingChats.length > 0 && (
        <div className="card" style={{ marginBottom: 18, borderColor: "var(--warning)" }}>
          <div className="card-title" style={{ display: "flex", alignItems: "center", gap: 7 }}>
            <span className="dot dot-pulse" style={{ background: "var(--warning)" }} />
            {t("queue.waitingChats", { n: waitingChats.length })}
          </div>
          <div className="flex-col gap-sm" style={{ marginTop: 10 }}>
            {waitingChats.map((s) => (
              <div key={s.chat_session_id} className="flex between center-y">
                <span className="mono" style={{ fontSize: 13 }}>{s.ticket_id}</span>
                <span className="faint" style={{ fontSize: 12 }}>{t("queue.waitingSince", { time: formatDateTime(s.started_at, lang) })}</span>
                <span className="btn btn-primary" onClick={() => router.push(`/tickets/${s.ticket_id}`)}>
                  {t("queue.openClaim")}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* pollMs KHÔNG truyền ở đây — interval 60s phía trên đã gọi
          ticketSectionRef.refresh() cùng lúc với loadWaitingChats(), tránh 2
          bộ đếm 60s độc lập chạy chồng lên nhau. */}
      <TicketListSection ref={ticketSectionRef} role={role} />
    </>
  );
}
