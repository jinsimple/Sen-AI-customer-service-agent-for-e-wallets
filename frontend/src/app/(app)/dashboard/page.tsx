"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { listTickets, listWaitingChatSessions, requestStaffWsTicket } from "@/lib/api";
import { COMPLAINT_TYPE_LABEL, HITL_STATUS_LABEL, SCOPE_LABEL, type TicketSummary } from "@/lib/types";
import { formatDateTime, formatSlaRemaining } from "@/lib/format";
import { useLiveChatSocket, type LiveChatEvent } from "@/lib/useLiveChatSocket";

interface WaitingChatSession {
  chat_session_id: string;
  ticket_id: string;
  customer_id: string;
  started_at: string;
}

type FilterKey = "all" | "pending" | "partner" | "critical" | "handoff";

export default function DashboardPage() {
  const router = useRouter();
  const [tickets, setTickets] = useState<TicketSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<FilterKey>("all");
  const [search, setSearch] = useState("");
  const [waitingChats, setWaitingChats] = useState<WaitingChatSession[]>([]);

  const loadTickets = useCallback(() => {
    listTickets({ limit: 100 })
      .then(setTickets)
      .catch((e) => setError(e.message ?? "Không tải được hàng chờ"));
  }, []);

  useEffect(() => {
    loadTickets();
  }, [loadTickets]);

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
      loadTickets();
    }, 60_000);
    return () => clearInterval(interval);
  }, [loadWaitingChats, loadTickets]);

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
        // `tickets` chỉ fetch ĐÚNG MỘT LẦN lúc mount (useEffect deps rỗng).
        // Mà chip "Khách yêu cầu người thật (N)" lại đếm từ `tickets`, nên
        // khách bấm "gặp người thật" xong thì CSKH đang mở sẵn dashboard KHÔNG
        // bao giờ thấy số đếm nhúc nhích — đứng yên tới khi reload cả trang.
        // Poll 60s bên dưới cũng chỉ chạm `waitingChats`, không cứu được.
        loadTickets();
      }
    },
    [loadWaitingChats, loadTickets]
  );

  useLiveChatSocket(staffWsTicket, handleDashboardWsEvent);

  const counts = useMemo(() => {
    if (!tickets) return { all: 0, pending: 0, partner: 0, critical: 0, handoff: 0 };
    return {
      all: tickets.length,
      pending: tickets.filter((t) => t.hitl_status === "pending").length,
      partner: tickets.filter(
        (t) =>
          (t.partner_wait_status === "waiting" || t.partner_wait_status === "overdue") &&
          t.hitl_status !== "approved" &&
          t.hitl_status !== "rejected"
      ).length,
      critical: tickets.filter((t) => t.priority === "critical").length,
      handoff: tickets.filter((t) => t.human_handoff_requested).length,
    };
  }, [tickets]);

  const filtered = useMemo(() => {
    if (!tickets) return [];
    let list = tickets;
    if (filter === "pending") list = list.filter((t) => t.hitl_status === "pending");
    if (filter === "partner")
      // Vé đã DUYỆT/TỪ CHỐI coi như đã kết thúc — không còn "chờ" gì nữa dù
      // partner_wait_status chưa/không được cập nhật lại. Bug thật 03/09:
      // hai vé "Đã duyệt" vẫn lọt vào tab này vì điều kiện cũ chỉ nhìn
      // partner_wait_status, bỏ qua hitl_status.
      list = list.filter(
        (t) =>
          (t.partner_wait_status === "waiting" || t.partner_wait_status === "overdue") &&
          t.hitl_status !== "approved" &&
          t.hitl_status !== "rejected"
      );
    if (filter === "critical") list = list.filter((t) => t.priority === "critical");
    if (filter === "handoff") list = list.filter((t) => t.human_handoff_requested);
    if (search.trim()) {
      const q = search.trim().toLowerCase();
      list = list.filter(
        (t) =>
          t.ticket_id.toLowerCase().includes(q) ||
          t.complaint_id.toLowerCase().includes(q) ||
          (t.customer_name ?? "").toLowerCase().includes(q)
      );
    }
    return list;
  }, [tickets, filter, search]);

  return (
    <>
      <div className="page-head">
        <span className="eyebrow">Webapp CSKH</span>
        <h1>Hàng chờ ticket</h1>
        <p className="sub">
          Lọc/sắp xếp theo trạng thái và ưu tiên để xử lý đúng case cấp bách trước. Case nghi gian lận
          (tín hiệu FS-06) nổi bật rõ hơn ticket thường.
        </p>
      </div>

      {waitingChats.length > 0 && (
        <div className="card" style={{ marginBottom: 18, borderColor: "var(--warning)" }}>
          <div className="card-title" style={{ display: "flex", alignItems: "center", gap: 7 }}>
            <span className="dot dot-pulse" style={{ background: "var(--warning)" }} />
            Khách đang chờ chat trực tiếp ({waitingChats.length})
          </div>
          <div className="flex-col gap-sm" style={{ marginTop: 10 }}>
            {waitingChats.map((s) => (
              <div key={s.chat_session_id} className="flex between center-y">
                <span className="mono" style={{ fontSize: 13 }}>{s.ticket_id}</span>
                <span className="faint" style={{ fontSize: 12 }}>Chờ từ {formatDateTime(s.started_at)}</span>
                <span className="btn btn-primary" onClick={() => router.push(`/tickets/${s.ticket_id}`)}>
                  Mở &amp; nhận
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Lead đo 20/08: listTickets({limit:100}) là 100 vé MỚI NHẤT, không phải
          tổng — 60/100 handoff trong cửa sổ này đọc nhầm thành 60% trong khi
          thật (786 vé) là 113/786=14,4%. Một dòng khai chung cho mọi chip
          dưới đây thay vì sửa từng nhãn — đúng vì mọi chip cùng đếm trên
          CÙNG mảng `tickets` (cửa sổ 100), không riêng "Tất cả". */}
      <p className="dim" style={{ fontSize: 12, marginBottom: 8 }}>
        Số đếm dưới đây tính trên 100 vé MỚI NHẤT, không phải tổng toàn hệ thống.
      </p>
      <div className="filter-bar">
        <span className={`filter-chip${filter === "all" ? " active" : ""}`} onClick={() => setFilter("all")}>
          Tất cả ({counts.all}/100 vé mới nhất)
        </span>
        <span
          className={`filter-chip${filter === "pending" ? " active" : ""}`}
          onClick={() => setFilter("pending")}
        >
          Chờ tiếp nhận ({counts.pending})
        </span>
        <span
          className={`filter-chip${filter === "partner" ? " active" : ""}`}
          onClick={() => setFilter("partner")}
        >
          Chờ đối tác NH ({counts.partner})
        </span>
        <span
          className={`filter-chip${filter === "critical" ? " active" : ""}`}
          style={filter !== "critical" ? { borderColor: "var(--danger)", color: "var(--danger)" } : undefined}
          onClick={() => setFilter("critical")}
        >
          <span className="dot dot-pulse" style={{ background: "var(--danger)" }} />
          Khẩn cấp — nghi gian lận ({counts.critical})
        </span>
        <span
          className={`filter-chip${filter === "handoff" ? " active" : ""}`}
          onClick={() => setFilter("handoff")}
        >
          Khách yêu cầu người thật ({counts.handoff}/100 vé mới nhất)
        </span>
        <div className="search-box">
          <svg className="icon icon-sm" viewBox="0 0 24 24">
            <circle cx="11" cy="11" r="7" />
            <path d="M21 21l-4-4" />
          </svg>
          <input
            placeholder="Tìm theo mã ticket, mã khiếu nại, tên khách..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {error && <div className="note" style={{ borderColor: "var(--danger)" }}>{error}</div>}

      <div className="card scroll-x" style={{ padding: 0 }}>
        <table className="table table-cards-mobile">
          <thead>
            <tr>
              <th>Mã ticket</th>
              <th>Khách hàng</th>
              <th>Loại KN</th>
              <th>Phạm vi</th>
              <th>Ưu tiên</th>
              <th>Trạng thái</th>
              <th>SLA</th>
              <th>Cập nhật</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((t) => {
              const sla = formatSlaRemaining(t.sla_due_at);
              const rowClass = t.priority === "critical" ? "row-critical" : sla.overdue ? "row-warning" : "";
              return (
                <tr key={t.ticket_id} className={`clickable ${rowClass}`} onClick={() => router.push(`/tickets/${t.ticket_id}`)}>
                  <td className="mono" data-label="Mã ticket">{t.ticket_id}</td>
                  <td data-label="Khách hàng">
                    {t.customer_name ?? "—"}
                    {t.human_handoff_requested && (
                      <span className="badge badge-warning" style={{ marginLeft: 6 }}>
                        Yêu cầu người thật
                      </span>
                    )}
                  </td>
                  <td data-label="Loại KN">{t.complaint_type ? COMPLAINT_TYPE_LABEL[t.complaint_type] : "—"}</td>
                  <td data-label="Phạm vi">
                    <span className="badge badge-neutral">{t.scope ? SCOPE_LABEL[t.scope] : "—"}</span>
                  </td>
                  <td data-label="Ưu tiên">
                    {t.priority === "critical" ? (
                      <span className="badge badge-critical">
                        <span className="dot dot-pulse" />
                        Khẩn cấp
                      </span>
                    ) : t.priority === "high" ? (
                      <span className="status-dot dot-warning">Cao</span>
                    ) : (
                      <span className="status-dot">Bình thường</span>
                    )}
                  </td>
                  <td data-label="Trạng thái">
                    {t.hitl_status === "rejected" ? (
                      <span className="badge badge-danger">{HITL_STATUS_LABEL[t.hitl_status]}</span>
                    ) : (
                      <span
                        className={`status-dot ${
                          t.hitl_status === "approved"
                            ? "dot-success"
                            : t.hitl_status === "need_more_info"
                              ? "dot-info"
                              : ""
                        }`}
                      >
                        {HITL_STATUS_LABEL[t.hitl_status]}
                      </span>
                    )}
                  </td>
                  <td className="mono" style={{ fontSize: 12 }} data-label="SLA">
                    {sla.label}
                  </td>
                  <td className="faint" style={{ fontSize: 12 }} data-label="Cập nhật">
                    {formatDateTime(t.created_at)}
                  </td>
                </tr>
              );
            })}
            {tickets && filtered.length === 0 && (
              <tr>
                <td colSpan={8} className="dim" style={{ textAlign: "center", padding: 24 }}>
                  Không có ticket nào khớp bộ lọc.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
