"use client";

import { useEffect, useRef, useState } from "react";
import { ApiError, agentChat, getCustomerHistory, requestOtp, verifyOtp } from "@/lib/api";
import { COMPLAINT_TYPE_LABEL, type ComplaintType, type CustomerHistory } from "@/lib/types";
import { formatDateTime, formatMoney } from "@/lib/format";

// Complaint.status (khác Ticket.hitl_status) — trong dataset/pipeline hiện
// tại chỉ dùng "investigating"/"resolved", nhưng không có CHECK constraint
// ràng buộc ở DB nên fallback về đúng chuỗi gốc nếu gặp giá trị lạ.
const COMPLAINT_STATUS_LABEL: Record<string, string> = {
  investigating: "Đang xử lý",
  resolved: "Đã giải quyết",
  rejected: "Đã từ chối",
};

const COMPLAINT_CHIPS: { value: ComplaintType; label: string; starter: string }[] = [
  { value: "wrong_recipient", label: "Chuyển nhầm", starter: "Tôi bị chuyển nhầm tiền." },
  { value: "money_not_received", label: "Tiền chưa về", starter: "Tôi chuyển tiền mà bên kia chưa nhận được." },
  { value: "double_charge", label: "Trừ tiền 2 lần", starter: "Tôi bị trừ tiền 2 lần cho cùng 1 giao dịch." },
  { value: "refund", label: "Hoàn tiền", starter: "Tôi được duyệt hoàn tiền nhưng chưa thấy tiền về." },
];

// OTP chỉ cần xác thực khi agent THỰC SỰ chạm dữ liệu giao dịch/tài khoản
// (2 tool này) hoặc tạo ticket — hỏi chính sách/phí chung chung không cần.
const SENSITIVE_TOOLS = new Set(["lookup_transaction", "get_customer_history"]);

type Msg =
  | { id: string; from: "bot"; text: string; chips?: { label: string; onClick: () => void }[]; cite?: string }
  | { id: string; from: "user"; text: string }
  | {
      id: string;
      from: "otp";
      resolved: boolean;
      securityQuestion: string;
      demoOtpCode: string;
      checking: boolean;
      error: string | null;
    };

type Stage = "greeting" | "otp" | "chat" | "busy";

function nid() {
  // crypto.randomUUID() thay vì bộ đếm cấp module — bộ đếm bị Next.js
  // Fast Refresh (dev) reset về 0 mỗi lần sửa file trong khi state cũ (đã
  // có id "m1"...) vẫn còn, gây trùng key React ("Encountered two children
  // with the same key"). UUID không phụ thuộc trạng thái module nên không
  // bao giờ trùng, kể cả qua hot-reload.
  return crypto.randomUUID();
}

function OtpForm({
  disabled,
  checking,
  error,
  onSubmit,
}: {
  disabled: boolean;
  checking: boolean;
  error: string | null;
  onSubmit: (otpCode: string, securityAnswer: string) => void;
}) {
  // Controlled (không thao tác DOM tay) — bắt buộc để gõ ĐÈ lên ô đã có sẵn
  // số hoạt động đúng: input maxLength=1 chưa được bôi đen thì trình duyệt
  // chặn ký tự mới (đã đạt maxLength), onChange không bắn, không tự nhảy ô.
  // onFocus bôi đen nội dung cũ để gõ đè luôn thay thế được, dù gõ theo thứ
  // tự nào hay quay lại ô đã điền.
  const [digits, setDigits] = useState(["", "", "", "", "", ""]);
  const [answer, setAnswer] = useState("");
  const refs = useRef<Array<HTMLInputElement | null>>([]);

  function handleChange(i: number, value: string) {
    const digit = value.replace(/\D/g, "").slice(-1);
    setDigits((prev) => {
      const next = [...prev];
      next[i] = digit;
      return next;
    });
    if (digit && i < 5) refs.current[i + 1]?.focus();
  }

  function handleKeyDown(i: number, e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Backspace" && !digits[i] && i > 0) {
      refs.current[i - 1]?.focus();
    }
  }

  const canSubmit = !disabled && !checking && digits.every(Boolean) && answer.trim().length > 0;

  return (
    <>
      <div className="otp-row">
        {digits.map((d, i) => (
          <input
            key={i}
            ref={(el) => {
              refs.current[i] = el;
            }}
            className="otp-box"
            inputMode="numeric"
            maxLength={1}
            value={d}
            disabled={disabled || checking}
            onChange={(e) => handleChange(i, e.target.value)}
            onKeyDown={(e) => handleKeyDown(i, e)}
            onFocus={(e) => e.target.select()}
          />
        ))}
      </div>
      <input
        className="otp-answer"
        style={{ marginTop: 8, width: "100%" }}
        placeholder="Câu trả lời bảo mật"
        value={answer}
        disabled={disabled || checking}
        onChange={(e) => setAnswer(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && canSubmit && onSubmit(digits.join(""), answer)}
      />
      {error && (
        <div className="dim" style={{ color: "var(--danger, #d33)", fontSize: 12, marginTop: 6 }}>
          {error}
        </div>
      )}
      {!error && !canSubmit && !checking && (digits.some(Boolean) || answer) && (
        <div className="dim" style={{ fontSize: 12, marginTop: 6 }}>
          {!digits.every(Boolean)
            ? "Nhập đủ 6 số OTP để tiếp tục."
            : "Nhập câu trả lời bảo mật để tiếp tục."}
        </div>
      )}
      <button
        className="btn btn-gold btn-sm"
        style={{ marginTop: 12 }}
        disabled={!canSubmit}
        onClick={() => onSubmit(digits.join(""), answer)}
      >
        {checking ? "Đang xác thực..." : "Xác nhận"}
      </button>
    </>
  );
}

export default function ChatClient({ userId, phone }: { userId: string; phone: string }) {
  const [history, setHistory] = useState<CustomerHistory | null>(null);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [stage, setStage] = useState<Stage>("greeting");
  const [input, setInput] = useState("");
  const [lastTicket, setLastTicket] = useState<{ ticket_id: string; should_escalate: boolean } | null>(null);
  const threadRef = useRef<HTMLDivElement>(null);
  const greetedRef = useRef(false);
  // Xác thực 1 lần/phiên — sau khi true, không hỏi lại OTP dù chip/rail/agent
  // có chạm dữ liệu nhạy cảm thêm lần nữa trong cùng phiên chat.
  const otpVerifiedRef = useRef(false);
  // Tin nhắn đang chờ gửi cho agent SAU KHI xác thực OTP xong — dùng cho 2
  // lối vào đã biết chắc chắn liên quan giao dịch/ticket NGAY TỪ ĐẦU (chip,
  // "Báo lỗi giao dịch này"): phải xác thực TRƯỚC khi gọi agent, không phải
  // sau khi agent đã lỡ tra cứu/tạo ticket rồi mới hỏi.
  const pendingStarterRef = useRef<string | null>(null);

  useEffect(() => {
    getCustomerHistory({}).then(setHistory).catch(() => setHistory(null));
    // React StrictMode (dev) chạy effect 2 lần lúc mount để bắt lỗi thiếu
    // cleanup — không chặn thì lời chào bị đẩy 2 lần. Ref giữ nguyên qua 2
    // lần chạy đó (khác state), nên chặn được đúng 1 lần.
    if (greetedRef.current) return;
    greetedRef.current = true;
    // Không còn chip 4 loại khiếu nại ở đây nữa — trùng lặp với chip hiện ra
    // khi bấm "Báo lỗi giao dịch này" (đúng chỗ cần chọn loại vấn đề, vì đã
    // gắn sẵn với 1 giao dịch cụ thể). Ở đây khách gõ tự do là đủ.
    push({
      id: nid(),
      from: "bot",
      text: "Chào bạn, mình là Sen — mình có thể giúp gì cho bạn hôm nay? Bạn có thể gõ trực tiếp câu hỏi, hoặc bấm \"Báo lỗi giao dịch này\" ở một giao dịch cụ thể bên trái.",
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  useEffect(() => {
    threadRef.current?.scrollTo({ top: threadRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  function push(msg: Msg) {
    setMessages((prev) => [...prev, msg]);
  }

  // Chip chọn loại vấn đề sau khi bấm "Báo lỗi giao dịch này" — luôn ghép rõ
  // complaint_type vào starter, KHÔNG BAO GIỜ gửi cho agent một tin nhắn chỉ
  // có mã giao dịch mà không nói rõ vấn đề gì (agent từng tạo ticket vội khi
  // nhận tin mơ hồ kiểu đó, dù prompt đã dặn rõ — LLM không tuân thủ tuyệt
  // đối 100%, nên chặn hẳn ở tầng UI).
  // Gọi /auth/otp/request THẬT (backend giờ xác thực thật, không còn là gate
  // UI thuần — xem src/auth.py::require_otp_verified) rồi mới hiện form OTP +
  // câu hỏi bảo mật. Thất bại (mất mạng...) thì báo lỗi, không hiện form giả.
  async function beginOtpFlow() {
    try {
      const { security_question, otp_code } = await requestOtp();
      push({
        id: nid(),
        from: "otp",
        resolved: false,
        securityQuestion: security_question,
        demoOtpCode: otp_code,
        checking: false,
        error: null,
      });
      setStage("otp");
    } catch {
      push({ id: nid(), from: "bot", text: "Không xin được mã OTP lúc này, bạn thử lại giúp mình nhé." });
      setStage("chat");
    }
  }

  function startComplaint(
    c: (typeof COMPLAINT_CHIPS)[number],
    tx: NonNullable<CustomerHistory["recent_transactions"]>[number]
  ) {
    const label = `${c.label} — giao dịch ${tx.trans_id}`;
    const starter = `${c.starter} Giao dịch liên quan: ${tx.trans_id} (${formatMoney(tx.amount)} lúc ${formatDateTime(tx.created_at)}).`;
    push({ id: nid(), from: "user", text: label });
    if (otpVerifiedRef.current) {
      void sendToAgent(starter, { echoAsUser: false });
      return;
    }
    push({
      id: nid(),
      from: "bot",
      text: `Mình hiểu bạn đang lo vì ${c.label.toLowerCase()} — để bảo vệ tài khoản của bạn, mình cần xác thực nhanh trước khi tra cứu nhé.`,
    });
    pendingStarterRef.current = starter;
    void beginOtpFlow();
  }

  async function submitOtp(msgId: string, otpCode: string, securityAnswer: string) {
    setMessages((prev) =>
      prev.map((m) => (m.id === msgId && m.from === "otp" ? { ...m, checking: true, error: null } : m))
    );
    try {
      await verifyOtp({ otp_code: otpCode, security_answer: securityAnswer });
    } catch (e) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === msgId && m.from === "otp"
            ? { ...m, checking: false, error: e instanceof ApiError ? e.message : "Xác thực thất bại, thử lại." }
            : m
        )
      );
      return;
    }
    setMessages((prev) => prev.map((m) => (m.id === msgId && m.from === "otp" ? { ...m, resolved: true, checking: false } : m)));
    otpVerifiedRef.current = true;
    const starter = pendingStarterRef.current;
    pendingStarterRef.current = null;
    if (starter) {
      // Lối vào đã biết chắc liên quan giao dịch (chip/rail) — giờ mới thật
      // sự gửi cho agent, SAU KHI đã xác thực xong.
      push({ id: nid(), from: "bot", text: "Xác thực thành công — để mình tra ngay giúp bạn." });
      void sendToAgent(starter, { echoAsUser: false });
    } else {
      // Phản ứng (gõ tự do, agent vừa lỡ chạm dữ liệu nhạy cảm) — không có
      // gì phải gửi lại, chỉ mở lại chat.
      push({ id: nid(), from: "bot", text: "Xác thực thành công — bạn tiếp tục hỏi mình nhé." });
      setStage("chat");
    }
  }

  function reportFromRail(tx: NonNullable<CustomerHistory["recent_transactions"]>[number]) {
    // KHÔNG gửi thẳng cho agent — bấm nút này mới chỉ biết giao dịch nào,
    // chưa biết vấn đề gì. Hỏi khách chọn loại vấn đề trước (chip), rồi mới
    // ghép với thông tin giao dịch qua startComplaint().
    push({
      id: nid(),
      from: "bot",
      text: `Bạn muốn báo vấn đề gì với giao dịch ${formatMoney(tx.amount)} lúc ${formatDateTime(tx.created_at)} này?`,
      chips: COMPLAINT_CHIPS.map((c) => ({ label: c.label, onClick: () => startComplaint(c, tx) })),
    });
  }

  async function sendToAgent(text: string, opts?: { echoAsUser?: boolean }) {
    if (opts?.echoAsUser !== false) push({ id: nid(), from: "user", text });
    setStage("busy");
    try {
      const result = await agentChat({ message: text });
      push({
        id: nid(),
        from: "bot",
        text: result.reply,
        cite: result.tool_calls.length
          ? `nguồn: ${result.tool_calls.map((c) => c.tool_name).join(" → ")}`
          : undefined,
      });
      if (result.ticket_id) {
        setLastTicket({ ticket_id: result.ticket_id, should_escalate: !!result.should_escalate });
      }
      // Làm mới rail "Lịch sử khiếu nại" sau MỌI lượt có chạm tool (không chỉ
      // lúc vừa tạo ticket mới) — agent có thể chỉ NHẮC lại 1 ticket đã tạo
      // trước đó (không trả ticket_id lượt này), khách vẫn cần thấy đúng dữ
      // liệu thật thay vì chỉ nghe agent kể lại bằng lời.
      if (result.tool_calls.length > 0) {
        getCustomerHistory({}).then(setHistory).catch(() => {});
      }

      // Chỉ chạm dữ liệu giao dịch/tài khoản thật (SENSITIVE_TOOLS) hoặc vừa
      // tạo ticket mới cần xác thực OTP — và chỉ hỏi đúng 1 lần/phiên. Câu
      // hỏi chính sách/phí chung chung (chỉ gọi search_policy) không cần.
      const touchedSensitiveData =
        result.tool_calls.some((c) => SENSITIVE_TOOLS.has(c.tool_name)) || !!result.ticket_id;
      if (touchedSensitiveData && !otpVerifiedRef.current) {
        push({
          id: nid(),
          from: "bot",
          text: "Mình vừa cần tra thông tin liên quan tới giao dịch/tài khoản của bạn — xác thực nhanh OTP phiên làm việc để tiếp tục nhé.",
        });
        void beginOtpFlow();
        return;
      }
      setStage("chat");
    } catch (e) {
      push({
        id: nid(),
        from: "bot",
        text: e instanceof ApiError ? `Có lỗi: ${e.message}` : "Có lỗi khi kết nối trợ lý, thử lại giúp mình nhé.",
      });
      setStage("chat");
    }
  }

  function handleSend() {
    const text = input.trim();
    if (!text || stage === "otp" || stage === "busy") return;
    setInput("");
    void sendToAgent(text);
  }

  const inputEnabled = stage === "chat" || stage === "greeting";

  return (
    <>
      <div className="page-head">
        <span className="eyebrow">Chatbot khách hàng · US-002, 003, 006, 007, 008, 009, 010</span>
        <h1>Chatbot AI — luồng khiếu nại lõi</h1>
        <p className="sub">
          AI agent thật (LangGraph + OpenAI) đang chạy — tự tra cứu, phân loại, và tạo ticket dựa trên hội
          thoại tự do. Mọi số liệu bot nói ra đều trích dẫn được từ tool đã gọi.
        </p>
      </div>

      <div className="chat-shell">
        <div className="chat-rail">
          <div className="card">
            <div className="rail-title">Giao dịch gần đây</div>
            {history?.recent_transactions.length === 0 && <div className="dim" style={{ fontSize: 12 }}>Chưa có giao dịch.</div>}
            {history?.recent_transactions.map((tx) => (
              <div className="txn-item" key={tx.trans_id}>
                <div className="txn-top">
                  <span>{tx.direction === "out" ? "Chuyển đi" : "Nhận vào"}</span>
                  <span className="txn-amount">{formatMoney(tx.amount)}</span>
                </div>
                <div className="txn-meta">{formatDateTime(tx.created_at)} · {tx.trans_id}</div>
                <button className="txn-report" onClick={() => reportFromRail(tx)} type="button">
                  <svg className="icon icon-sm" viewBox="0 0 24 24"><path d="M4 4v16l4-4h12V4H4z" /></svg>
                  Báo lỗi giao dịch này
                </button>
              </div>
            ))}
          </div>
          <div className="card">
            <div className="rail-title">Lịch sử khiếu nại của bạn</div>
            {history?.complaints.length === 0 && <div className="dim" style={{ fontSize: 12 }}>Chưa có khiếu nại nào.</div>}
            {history?.complaints.map((c) => (
              <div className="hist-item" key={c.complaint_id} style={{ flexDirection: "column", alignItems: "flex-start", gap: 4 }}>
                <div className="flex between center-y" style={{ width: "100%" }}>
                  <span className="id">{c.complaint_id}</span>
                  <span className="badge badge-neutral">{COMPLAINT_STATUS_LABEL[c.status] ?? c.status}</span>
                </div>
                <div className="dim" style={{ fontSize: 11 }}>
                  {COMPLAINT_TYPE_LABEL[c.type]} · {formatDateTime(c.created_at)}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="chat-panel">
          <div className="chat-head">
            <div className="chat-avatar">S</div>
            <div>
              <div className="name">Sen AI · Trợ lý CSKH</div>
              <div className="status">
                <svg className="icon icon-sm" viewBox="0 0 24 24"><path d="M20 6L9 17l-5-5" /></svg>
                {phone}
              </div>
            </div>
          </div>
          <div className="chat-thread" ref={threadRef}>
            {messages.map((m) => {
              if (m.from === "user") {
                return (
                  <div className="bubble-row from-user" key={m.id}>
                    <div className="bubble bubble-user">{m.text}</div>
                  </div>
                );
              }
              if (m.from === "otp") {
                return (
                  <div className="bubble-row from-bot" key={m.id}>
                    <div className="bubble bubble-bot">
                      <div className="otp-meta">
                        <span>
                          Mã OTP phiên làm việc (mô phỏng — gửi tới {phone}): <strong>{m.demoOtpCode}</strong>
                        </span>
                      </div>
                      <div className="otp-meta" style={{ marginTop: 4 }}>
                        <span>Câu hỏi bảo mật: {m.securityQuestion}</span>
                      </div>
                      <OtpForm
                        disabled={m.resolved}
                        checking={m.checking}
                        error={m.error}
                        onSubmit={(code, answer) => void submitOtp(m.id, code, answer)}
                      />
                    </div>
                  </div>
                );
              }
              return (
                <div className="bubble-row from-bot" key={m.id}>
                  <div className="bubble bubble-bot">
                    {m.text}
                    {m.chips && (
                      <div className="chips">
                        {m.chips.map((c, i) => (
                          <span className="chip" key={i} onClick={c.onClick}>{c.label}</span>
                        ))}
                      </div>
                    )}
                    {m.cite && <div className="bubble-cite">{m.cite}</div>}
                  </div>
                </div>
              );
            })}
            {stage === "busy" && (
              <div className="bubble-row from-bot">
                <div className="typing-dots"><span /><span /><span /></div>
              </div>
            )}
          </div>
          <div className="chat-input">
            <input
              placeholder={inputEnabled ? "Nhập tin nhắn..." : "Chọn một lựa chọn phía trên để tiếp tục"}
              value={input}
              disabled={!inputEnabled}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
            />
            <button
              className="icon-btn send"
              disabled={!inputEnabled}
              onClick={handleSend}
              type="button"
              aria-label="Gửi tin nhắn"
            >
              <svg className="icon" viewBox="0 0 24 24"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" /></svg>
            </button>
          </div>
          <div className="chat-disclaimer">
            <svg className="icon icon-sm" viewBox="0 0 24 24"><rect x="4" y="11" width="16" height="9" rx="2" /><path d="M8 11V7a4 4 0 018 0v4" /></svg>
            Sen không bao giờ hỏi mật khẩu hoặc mã OTP giao dịch thật của bạn qua chat.
          </div>
        </div>

        <div className="chat-rail" style={{ display: "flex", flexDirection: "column" }}>
          <div className="card">
            <div className="rail-title">Trạng thái</div>
            {!lastTicket ? (
              <div className="dim" style={{ fontSize: 12 }}>Chưa có yêu cầu nào trong phiên này.</div>
            ) : (
              <div className="stepper">
                <div className="step">
                  <div className="step-dot done"><svg className="icon icon-sm" viewBox="0 0 24 24"><path d="M20 6L9 17l-5-5" /></svg></div>
                  <div className="step-body"><div className="step-label">Tiếp nhận &amp; xác thực</div></div>
                </div>
                <div className="step">
                  <div className="step-dot done"><svg className="icon icon-sm" viewBox="0 0 24 24"><path d="M20 6L9 17l-5-5" /></svg></div>
                  <div className="step-body"><div className="step-label">Tra cứu &amp; điều tra</div></div>
                </div>
                <div className="step">
                  <div className="step-dot current" />
                  <div className="step-body">
                    <div className="step-label">Chờ CSKH tiếp nhận {lastTicket.should_escalate && <span className="badge badge-critical" style={{ marginLeft: 4 }}>khẩn</span>}</div>
                    <div className="step-note mono">{lastTicket.ticket_id}</div>
                  </div>
                </div>
                <div className="step"><div className="step-dot pending" /><div className="step-body"><div className="step-label">Chờ Sếp phê duyệt</div></div></div>
                <div className="step"><div className="step-dot pending" /><div className="step-body"><div className="step-label">Hoàn tất</div></div></div>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
