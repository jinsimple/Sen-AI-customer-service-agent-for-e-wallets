"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import BannerLechVai from "@/components/BannerLechVai";
import { ApiError, agentChat, getCustomerHistory, requestLiveChatWsTicket, requestOtp, verifyOtp } from "@/lib/api";
import { COMPLAINT_TYPE_LABEL, type ComplaintType, type CustomerHistory } from "@/lib/types";
import { formatDateTime, formatMoney } from "@/lib/format";
import { useLiveChatSocket, type LiveChatEvent } from "@/lib/useLiveChatSocket";

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
// hoặc tạo ticket — hỏi chính sách/phí chung chung không cần.
//
// Finding B2 (GĐ2.5) — `create_ticket` THIẾU ở đây là MỘT trong hai nguyên
// nhân độc lập của Finding B (phép AND, vá một cái không đủ — xem
// otpStaleCall bên dưới cho nửa còn lại): khi tool này hỏng vì OTP hết tươi,
// nó không tạo `ticket_id` (tạo thất bại) VÀ trước bản vá này không có mặt
// trong tập "nhạy cảm" ⟹ touchedSensitiveData=false ⟹ không hỏi lại OTP.
const SENSITIVE_TOOLS = new Set(["lookup_transaction", "get_customer_history", "create_ticket"]);

// Finding B1 (GĐ2.5, QUYẾT ĐỊNH B — docs/giao-viec/2026-08-19-gd25-va-finding-ab-otp.md,
// commit 32751c2, PO thật chốt 19/08) — OTP hết tươi KHÔNG BAO GIỜ tới client
// dưới dạng HTTP 403 trên đường agent thật (chỉ route HTTP /tools/create_ticket
// TRỰC TIẾP mới 403, và ChatClient không gọi route đó — xem
// customer_tools.py:632-635: tool trả `{"status":"error",...}` TRONG một
// response 200 bình thường, KHÔNG raise). Cách nhận diện DUY NHẤT trong ràng
// buộc backend ĐÓNG BĂNG đợt này: khớp CHÍNH XÁC chuỗi hằng số backend tự
// viết ra (KHÁC hẳn khớp thân lỗi NHÀ CUNG CẤP — thứ đã cấm ở GĐ3: đây là
// literal TA SỞ HỮU, dưới quản lý phiên bản, ghim được bằng cổng).
//
// 🔴 CHỈ khớp `_OTP_EXPIRED_ERROR` (customer_tools.py:600-603) — KHÔNG khớp
// `_OTP_REQUIRED_ERROR` (trả ở :814·:863·:905, điều kiện `otp_verified_at is
// None` — khách CHƯA TỪNG xác thực). Không phải thiếu sót, có lý do đo được:
// ca REQUIRED chỉ xảy ra khi `otp_verified_at is None`, tức `otpVerifiedRef.
// current` đang là FALSE (chưa từng xác thực trong phiên) ⟹ điều kiện
// `touchedSensitiveData && !otpVerifiedRef.current` bên dưới TỰ BẮN, không
// cần tín hiệu gì thêm. Ca EXPIRED thì NGƯỢC LẠI: đã xác thực một lần nên
// `ref` là TRUE ⟹ điều kiện đó KHÔNG bắn — đây là ca DUY NHẤT cần otpStaleCall.
// Sau khi B2 (SENSITIVE_TOOLS thêm create_ticket) land, ca REQUIRED được phủ
// MIỄN PHÍ qua đúng con đường đó, kể cả cho create_ticket.
// ⟹ Khớp thêm REQUIRED không thừa MỘT CHÚT — nó THỪA HOÀN TOÀN, và trả giá
// bằng một chuỗi cổng ghim không phủ (cổng ② chỉ so đúng EXPIRED — xem
// ChatClient.pin.test.ts). Khớp SAI (kể cả REQUIRED) rơi qua nhánh
// touchedSensitiveData bên dưới như bình thường — KHÔNG RÕ không bị gộp
// ngầm vào OTP (điều khoản ba-trạng-thái của Bảo Mật).
//
// Nợ có hạn, có chuyến (khai trong Quyết định B): giải pháp (ii) này đi cùng
// đợt backend GĐ3 (đằng nào cũng gỡ băng cho bể model xoay) sẽ đổi sang field
// `loai` có cấu trúc, cổng ghim tháo bỏ khi đó — KHÔNG phải "tạm thời vĩnh viễn".
const OTP_EXPIRED_MESSAGE =
  "Lần xác thực OTP gần nhất đã quá hạn cho thao tác này — yêu cầu khách xác thực OTP lại trước khi tiếp tục.";

type Msg =
  | { id: string; from: "bot"; text: string; chips?: { label: string; onClick: () => void }[]; cite?: string }
  | { id: string; from: "user"; text: string }
  | { id: string; from: "staff"; text: string }
  | { id: string; from: "system"; text: string }
  | {
      id: string;
      from: "otp";
      resolved: boolean;
      sessionId: string;
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
  onSubmit: (otpCode: string) => void;
}) {
  // Controlled (không thao tác DOM tay) — bắt buộc để gõ ĐÈ lên ô đã có sẵn
  // số hoạt động đúng: input maxLength=1 chưa được bôi đen thì trình duyệt
  // chặn ký tự mới (đã đạt maxLength), onChange không bắn, không tự nhảy ô.
  // onFocus bôi đen nội dung cũ để gõ đè luôn thay thế được, dù gõ theo thứ
  // tự nào hay quay lại ô đã điền.
  //
  // AUTH5-01 (đợt nâng cấp Auth Flow 2026-08-12, NIST SP 800-63B-4) — bỏ
  // hẳn ô "câu trả lời bảo mật": KBA không còn là authenticator, mã OTP là
  // yếu tố step-up duy nhất (xem src/api/main.py::verify_otp).
  const [digits, setDigits] = useState(["", "", "", "", "", ""]);
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
    if (e.key === "Enter" && canSubmit) onSubmit(digits.join(""));
  }

  const canSubmit = !disabled && !checking && digits.every(Boolean);

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
      {error && (
        <div className="dim" style={{ color: "var(--danger, #d33)", fontSize: 12, marginTop: 6 }}>
          {error}
        </div>
      )}
      {!error && !canSubmit && !checking && digits.some(Boolean) && (
        <div className="dim" style={{ fontSize: 12, marginTop: 6 }}>
          Nhập đủ 6 số OTP để tiếp tục.
        </div>
      )}
      <button
        className="btn btn-gold btn-sm"
        style={{ marginTop: 12 }}
        disabled={!canSubmit}
        onClick={() => onSubmit(digits.join(""))}
      >
        {checking ? "Đang xác thực..." : "Xác nhận"}
      </button>
    </>
  );
}

// Lỗi 12 (PO thật 19/08, docs/giao-viec/2026-08-19-gd4-po-test-4-loi-ui.md
// mục 12): cổng OTP V6 áp cho thẻ "Giao dịch gần đây" nhưng SÓT thẻ "Lịch
// sử khiếu nại" — cùng lớp lỗi "chính sách đúng, áp thiếu một nhánh" đã vá
// 3 lần khác trong ngày (scrub_pii/cong_chi_tieu/_ghi_so). Bảo Mật + Lead
// chốt: MỘT nơi định nghĩa cổng, không phải mỗi thẻ tự viết `!otpVerified ?`
// riêng — thẻ thứ ba sau này thừa hưởng cổng tự động, không cần ai nhớ copy
// đúng pattern.
function RailCardGatedByOtp({
  otpVerified,
  onXacThuc,
  thongDiepChuaXacThuc,
  children,
}: {
  otpVerified: boolean;
  onXacThuc: () => void;
  thongDiepChuaXacThuc: string;
  children: React.ReactNode;
}) {
  if (!otpVerified) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        <div className="dim" style={{ fontSize: 12 }}>
          {thongDiepChuaXacThuc}
        </div>
        <button className="btn btn-outline btn-sm" type="button" onClick={onXacThuc}>
          Xác thực ngay
        </button>
      </div>
    );
  }
  return <>{children}</>;
}

export default function ChatClient({
  userId,
  phone,
  otpXemConHanLucTai,
}: {
  userId: string;
  phone: string;
  // Finding A (GĐ2.5 / M-10) — tính SẴN từ phiên lúc render trang (server,
  // page.tsx), 12h theo OTP_VIEW_MAX_MINUTES. Tên có "LucTai" CÓ CHỦ ĐÍCH
  // (Lead/PO-agent): đây là ẢNH CHỤP tại thời điểm render, KHÔNG PHẢI trạng
  // thái sống — nếu trang mở lâu quá 12h thì giá trị này CŨ, đúng như tên nó
  // nói. CHỈ gate hiển thị rail "Giao dịch gần đây" lúc TẢI TRANG — KHÔNG
  // dùng để bỏ qua bước hỏi OTP trước thao tác nhạy cảm (đó là
  // `otpVerifiedRef`, khác biến, khác mục đích: nó đúng khi CÒN reset mỗi
  // lần mount, phần "hết tươi TRONG KHI đang mở trang" là việc của Finding B
  // — xem sendToAgent).
  otpXemConHanLucTai: boolean;
}) {
  // UI-02 — vai của phiên hiện tại KHÔNG khớp màn này. Đặt từ phản hồi 403 của
  // API chứ không đọc lúc render: tab đang mở không điều hướng lần nào, nên
  // guard route (`proxy.ts`) không bao giờ chạy — 403 là tín hiệu DUY NHẤT.
  const [vaiLech, setVaiLech] = useState<string | null>(null);
  const [history, setHistory] = useState<CustomerHistory | null>(null);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [stage, setStage] = useState<Stage>("greeting");
  const [input, setInput] = useState("");
  const [lastTicket, setLastTicket] = useState<{ ticket_id: string; should_escalate: boolean } | null>(null);
  // Live chat (2026-08-11) — khách yêu cầu người thật (request_human_handoff,
  // CTRL-001) không trả ticket_id ở TOP LEVEL của AgentChatResult (chỉ
  // create_ticket làm vậy, xem src/agents/graph.py) — phải tự dò trong
  // tool_calls để biết đúng ticket_id cần mở panel chat trực tiếp.
  const [liveChatTicketId, setLiveChatTicketId] = useState<string | null>(null);
  // Live chat (2026-08-11, phản hồi thật từ test tay) — tin nhắn CSKH gộp
  // THẲNG vào cùng .chat-thread với AI, KHÔNG mở 1 khung chat riêng biệt bên
  // dưới — cảm giác phải là "AI bàn giao cho người thật trong CÙNG 1 cuộc
  // trò chuyện", không phải 2 cửa sổ tách rời.
  const [liveChatWsTicket, setLiveChatWsTicket] = useState<string | null>(null);
  const [liveChatSessionId, setLiveChatSessionId] = useState<string | null>(null);
  const liveChatConnectStartedRef = useRef(false);
  // Ref-guard GIỮ NGUYÊN mục đích gốc (chặn StrictMode double-invoke, lý do
  // thật từ 2026-08-11 — cùng pattern greetedRef). `lanThuLai` là đường mở lại
  // CÓ CHỦ Ý của người dùng, không phải gỡ bỏ ref.
  const [lanThuLai, setLanThuLai] = useState(0);
  const [loiKetNoiChat, setLoiKetNoiChat] = useState(false);
  const threadRef = useRef<HTMLDivElement>(null);
  const greetedRef = useRef(false);
  // Xác thực 1 lần/phiên — sau khi true, không hỏi lại OTP dù chip/rail/agent
  // có chạm dữ liệu nhạy cảm thêm lần nữa trong cùng phiên chat. LUÔN khởi
  // tạo `false` — CỐ Ý, khác `otpVerified` bên dưới (xem Finding A/B GĐ2.5).
  // Ref này gác bước "hỏi OTP TRƯỚC một thao tác nhạy cảm sắp làm" (chip/
  // sendToAgent) — sai lệch RẺ theo hướng hỏi thừa (chấp nhận được), trong khi
  // pre-set nó `true` từ một giá trị tính lúc render có thể làm lọt một thao
  // tác đã hết tươi STEP-UP dù còn tươi VIEW — nguồn sự thật cho ca đó là 403/
  // tool-error SỐNG, không phải suy ra lúc mount (Finding B xử lý).
  const otpVerifiedRef = useRef(false);
  // KHÔNG còn là "bản STATE của ref trên" (khác V6/14-08) — hai biến này nay
  // tách bạch chủ đích: ref (trên) gác thao tác SẮP làm, state (dưới) chỉ gác
  // HIỂN THỊ rail "Giao dịch gần đây" và ĐƯỢC PHÉP khởi tạo lạc quan từ phiên
  // thật (Finding A) vì hậu quả sai chỉ là UI — rail cùng lắm mở nhầm khi
  // otp_verified_at đã hết hạn 12h, còn mọi route đọc dữ liệu thật vẫn tự
  // kiểm otp_verified_at ở server (INV-10), không có gì rò qua ngả này.
  const [otpVerified, setOtpVerified] = useState(otpXemConHanLucTai);
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
      // DISC-002 (FIN05_QA_TestCases.jsonl, EU AI Act Art.50) — nêu rõ "trợ
      // lý AI" ngay trong chính tin nhắn chào, không chỉ ở tiêu đề trang/
      // nhãn cố định bên ngoài khung chat (2 chỗ đó có sẵn nhưng không đủ
      // theo đúng nghĩa "banner/câu mở đầu" mà chuẩn minh bạch yêu cầu).
      // Câu chào 19/08 (PO thật yêu cầu đổi, PO-agent soạn — docs/giao-viec/
      // 2026-08-19-gd4-po-test-4-loi-ui.md mục 11): đặt phạm vi bằng giọng
      // tự tin ("chỉ làm một việc, nhưng làm kỹ" — chặn so sánh nhầm loại
      // với ChatGPT/Claude), tách rõ tra-được/không-quyết, và biến HITL
      // (ràng buộc cứng 1) thành cam kết bảo vệ thay vì điểm yếu ("quy định
      // về tiền của bạn, không phải giới hạn của máy"). `\n\n` giữ đúng cấu
      // trúc 4 đoạn của bản gốc — bubble chưa có `white-space: pre-line`
      // nên hiện xuống dòng gộp thành khoảng trắng đơn, không phải lỗi.
      text: "Chào bạn, mình là Sen — trợ lý AI của ví. Mình chỉ làm một việc, nhưng làm kỹ: điều tra khiếu nại giao dịch của chính bạn.\n\nMình tra được — giao dịch cụ thể (số tiền · trạng thái · thời điểm), lịch sử ví, và quy định áp dụng cho trường hợp của bạn. Mọi con số mình nói đều lấy từ hệ thống và có ghi nguồn ngay dưới câu trả lời.\n\nMình không quyết — hoàn tiền hay điều chỉnh số dư phải do chuyên viên CSKH xác minh rồi người có thẩm quyền phê duyệt. Đây là quy định về tiền của bạn, không phải giới hạn của máy.\n\nBạn cứ kể bằng lời thường, không cần nhớ mã giao dịch. Hoặc bấm \"Báo lỗi giao dịch này\" ở một giao dịch cụ thể bên trái.",
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  // Mở vé WS + kết nối NGAY khi phát hiện handoff — ref-guard chặn
  // StrictMode double-invoke (đúng nguyên nhân đã gây tin nhắn lặp/tách khi
  // gửi, phát hiện thật 2026-08-11 — cùng pattern với greetedRef ở trên).
  useEffect(() => {
    if (!liveChatTicketId || liveChatConnectStartedRef.current) return;
    liveChatConnectStartedRef.current = true;
    requestLiveChatWsTicket(liveChatTicketId)
      .then((res) => {
        setLiveChatSessionId(res.chat_session_id);
        setLiveChatWsTicket(res.ws_ticket);
      })
      .catch(() => {
        // UI-02 — MỞ LẠI CỬA THỬ LẠI. Trước bản này `liveChatConnectStartedRef`
        // set `true` một lần và KHÔNG BAO GIỜ reset ở đâu (grep toàn repo: đúng
        // 3 dòng — khai báo, kiểm, set). Một lần thử, vĩnh viễn. Và `.catch`
        // lại bảo khách "thử lại giúp mình nhé" trong khi KHÔNG TỒN TẠI đường
        // nào để thử lại: effect chỉ chạy lại khi `liveChatTicketId` đổi, mà
        // nó không đổi.
        //
        // ⚠️ RESET REF MỘT MÌNH KHÔNG ĐỦ — deps không đổi thì effect không chạy
        // lại dù ref đã về false. Phải có `lanThuLai` trong deps. Một bản vá
        // chỉ reset ref sẽ TRÔNG đúng và KHÔNG có hiệu lực.
        liveChatConnectStartedRef.current = false;
        setLoiKetNoiChat(true);
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [liveChatTicketId, lanThuLai]);

  const handleLiveChatEvent = useCallback((event: LiveChatEvent) => {
    if (event.type === "message") {
      if (event.role === "staff") {
        setMessages((prev) => (prev.some((m) => m.id === event.message_id) ? prev : [...prev, { id: event.message_id, from: "staff", text: event.content }]));
      } else {
        // Echo tin nhắn CHÍNH KHÁCH vừa gửi — nguồn sự thật duy nhất là
        // server, không echo cục bộ lúc gửi để tránh hiện trùng.
        setMessages((prev) => (prev.some((m) => m.id === event.message_id) ? prev : [...prev, { id: event.message_id, from: "user", text: event.content }]));
      }
    } else if (event.type === "system") {
      setMessages((prev) => [...prev, { id: nid(), from: "system", text: event.text }]);
    } else if (event.type === "session_closed") {
      // Phiên chat trực tiếp đã kết thúc (CSKH bấm "Kết thúc chat", hoặc
      // chính khách vừa mất kết nối rồi phía server tự đóng — xem
      // close_customer_session_on_disconnect) — quay lại nói chuyện với Sen,
      // KHÔNG để khách gõ tiếp vào 1 phiên đã chết trong im lặng.
      setMessages((prev) => [...prev, { id: nid(), from: "system", text: "Phiên chat trực tiếp đã kết thúc. Bạn có thể tiếp tục hỏi Sen." }]);
      setLiveChatSessionId(null);
      setLiveChatWsTicket(null);
      setLiveChatTicketId(null);
    } else if (event.type === "error") {
      setMessages((prev) => [...prev, { id: nid(), from: "system", text: event.text }]);
    }
  }, []);

  const { status: liveChatStatus, sendMessage: sendLiveChatMessage } = useLiveChatSocket(liveChatWsTicket, handleLiveChatEvent);

  // Cảnh báo rời trang khi đang chat trực tiếp với CSKH (2026-08-11) — F5/
  // đóng tab NGẮT kết nối WS, phía server tự đóng phiên NGAY (xem
  // close_customer_session_on_disconnect trong live_chat_ws.py) — khách cần
  // biết trước rằng rời trang lúc này nghĩa là kết thúc phiên chat trực
  // tiếp ở CẢ 2 đầu, không chỉ riêng màn hình của họ. Trình duyệt hiện đại
  // không cho tuỳ biến nội dung hộp thoại native, chỉ bật/tắt được nó.
  useEffect(() => {
    if (!liveChatSessionId || liveChatStatus !== "open") return;
    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = "";
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [liveChatSessionId, liveChatStatus]);

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
  // UI thuần — xem src/auth.py::require_otp_verified) rồi mới hiện form OTP.
  // AUTH5-01 (2026-08-12) — không còn hỏi câu hỏi bảo mật (KBA bỏ khỏi vai
  // trò authenticator), chỉ mã OTP. Thất bại (mất mạng...) thì báo lỗi,
  // không hiện form giả.
  async function beginOtpFlow() {
    try {
      const { session_id, otp_code } = await requestOtp();
      push({
        id: nid(),
        from: "otp",
        resolved: false,
        sessionId: session_id,
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

  async function submitOtp(msgId: string, sessionId: string, otpCode: string) {
    setMessages((prev) =>
      prev.map((m) => (m.id === msgId && m.from === "otp" ? { ...m, checking: true, error: null } : m))
    );
    try {
      await verifyOtp({ session_id: sessionId, otp_code: otpCode });
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
    setOtpVerified(true);
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
      const handoffCall = result.tool_calls.find((c) => c.tool_name === "request_human_handoff");
      const handoffTicketId = handoffCall?.result?.ticket_id;
      if (typeof handoffTicketId === "string") {
        setLiveChatTicketId(handoffTicketId);
        if (!result.ticket_id) {
          setLastTicket({ ticket_id: handoffTicketId, should_escalate: false });
        }
      }
      // Làm mới rail "Lịch sử khiếu nại" sau MỌI lượt có chạm tool (không chỉ
      // lúc vừa tạo ticket mới) — agent có thể chỉ NHẮC lại 1 ticket đã tạo
      // trước đó (không trả ticket_id lượt này), khách vẫn cần thấy đúng dữ
      // liệu thật thay vì chỉ nghe agent kể lại bằng lời.
      if (result.tool_calls.length > 0) {
        getCustomerHistory({}).then(setHistory).catch(() => {});
      }

      // Finding B1 (GĐ2.5, Quyết định B) — tool vừa hỏng vì OTP ĐÃ hết tươi
      // GIỮA phiên (`otpVerifiedRef.current` vẫn `true` từ lần xác thực
      // trước, backend mới là nguồn sự thật). Khớp CHÍNH XÁC message — không
      // lọc thêm theo tool_name: message này chỉ 3 tool (lookup_transaction/
      // get_customer_history/create_ticket) có thể sinh ra nên đã đủ hẹp.
      const otpStaleCall = result.tool_calls.find(
        (c) => c.result.status === "error" && c.result.message === OTP_EXPIRED_MESSAGE
      );
      if (otpStaleCall) {
        push({
          id: nid(),
          from: "bot",
          text: "Để tiếp tục thao tác này, mình cần bạn xác thực lại OTP phiên làm việc nhé.",
        });
        pendingStarterRef.current = text;
        void beginOtpFlow();
        return;
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
        // Lỗi 1 (PO thật 19/08): thiếu dòng này làm câu khách vừa hỏi bị MẤT
        // sau khi xác thực xong — bắt gõ lại đúng lúc khách đang bực. Cùng
        // khuôn `pendingStarterRef` đã dùng ở startComplaint() (:392) và
        // otpStaleCall (:488) — submitOtp() tự gửi lại `text` sau khi OTP
        // xanh (giờ otpVerifiedRef=true nên tool sẽ chạy được).
        pendingStarterRef.current = text;
        void beginOtpFlow();
        return;
      }
      setStage("chat");
    } catch (e) {
      // 403 kèm chữ "role" = lệch vai, KHÔNG phải lỗi trợ lý. Đổ nguyên văn
      // `"Cần role thuộc ['customer'], tài khoản hiện tại là cskh"` vào khung
      // chat là thứ PO đọc thấy giữa buổi demo — vô nghĩa với người dùng và
      // trông như sản phẩm hỏng.
      if (e instanceof ApiError && e.status === 403 && /role/i.test(e.message)) {
        const m = /hiện tại là (\w+)/.exec(e.message);
        setVaiLech(m?.[1] ?? "khác");
        setStage("chat");
        return;
      }
      push({
        id: nid(),
        from: "bot",
        text: e instanceof ApiError ? `Có lỗi: ${e.message}` : "Có lỗi khi kết nối trợ lý, thử lại giúp mình nhé.",
      });
      setStage("chat");
    }
  }

  const liveChatSendingRef = useRef(false);
  // Phát hiện thật (2026-08-11): ô nhập đôi khi còn sót chữ sau khi gửi dù
  // setInput("") đã chạy — buộc React remount hẳn <input> (đổi key) sau MỖI
  // lần gửi (cả 2 nhánh AI/live-chat) để chắc chắn sạch bất kể timing.
  const [inputResetKey, setInputResetKey] = useState(0);

  function handleSend() {
    const text = input.trim();
    if (!text || stage === "otp" || stage === "busy") return;
    // Sau khi đã kết nối chat trực tiếp, MỌI tin nhắn đi qua CSKH, không qua
    // AI nữa — cùng cửa sổ, chỉ đổi "người nghe" phía sau.
    if (liveChatSessionId) {
      if (liveChatSendingRef.current) return;
      liveChatSendingRef.current = true;
      window.setTimeout(() => {
        liveChatSendingRef.current = false;
      }, 400);
      if (sendLiveChatMessage(liveChatSessionId, text)) {
        setInput("");
        setInputResetKey((k) => k + 1);
      }
      return;
    }
    setInput("");
    setInputResetKey((k) => k + 1);
    void sendToAgent(text);
  }

  const inputEnabled = (stage === "chat" || stage === "greeting") && !(liveChatTicketId && !liveChatSessionId);

  return (
    <>
      <div className="page-head">
        <span className="eyebrow">Trợ lý AI cho khách hàng</span>
        <h1>Trợ lý AI</h1>
        <p className="sub">
          Trợ lý AI — mọi con số đều được tra cứu từ hệ thống thật, không tự suy đoán.
        </p>
      </div>

      {/* UI-02 — băng lệch vai. Đặt TRÊN CÙNG, ngoài khung chat: lỗi vai không
          phải một tin nhắn của trợ lý, và nhét nó vào dòng hội thoại chính là
          thứ PO đọc thấy giữa buổi demo ("Có lỗi: Cần role thuộc..."). */}
      {vaiLech && <BannerLechVai vaiHienTai={vaiLech} vaiCanCo="customer" />}

      {/* UI-02 — ĐƯỜNG THỬ LẠI THẬT. Bản trước `.catch` chỉ đẩy một dòng chữ
          "thử lại giúp mình nhé" vào khung chat — trong khi KHÔNG TỒN TẠI
          đường nào để thử lại (ref-guard đã bật, deps không đổi). Nút này
          tăng `lanThuLai` -> effect chạy lại thật. */}
      {loiKetNoiChat && (
        <div role="alert" className="note" style={{ margin: "10px 0" }}>
          Không mở được kết nối chat trực tiếp.{" "}
          <button
            type="button"
            onClick={() => {
              setLoiKetNoiChat(false);
              setLanThuLai((n) => n + 1);
            }}
            style={{ background: "none", border: "none", padding: 0, cursor: "pointer", textDecoration: "underline", font: "inherit", color: "inherit", fontWeight: 600 }}
          >
            Thử lại
          </button>
        </div>
      )}

      <div className="chat-shell">
        <div className="chat-rail">
          <div className="card">
            <div className="rail-title">Giao dịch gần đây</div>
            {/* V6 (hotfix 14/08, PO thật quyết đổi chính sách): chưa xác thực OTP
                thì KHÔNG hiện danh sách giao dịch. Đây là gate ở TẦNG HIỂN THỊ —
                route đọc phía backend giữ nguyên theo contract hiện hành
                (authority-matrix.yaml), OTP vẫn được ép thật trên đường agent
                (INV-10). Muốn ép ở backend thì phải đổi contract → ADR + PO
                duyệt (nợ đã ghi cho đợt sau demo). */}
            <RailCardGatedByOtp
              otpVerified={otpVerified}
              onXacThuc={() => void beginOtpFlow()}
              thongDiepChuaXacThuc="Xác thực OTP để xem giao dịch gần đây"
            >
              {history?.recent_transactions.length === 0 && <div className="dim" style={{ fontSize: 12 }}>Chưa có giao dịch.</div>}
              {/* PO thật 19/08 (mục 12): rail là MỘT cột — danh sách giao dịch
                  nở đầy sau OTP đẩy thẻ "Lịch sử khiếu nại" trôi khỏi màn
                  hình. Cuộn nội bộ thay vì đảo thứ tự 2 thẻ (đơn giản hơn, ít
                  rủi ro phá layout khác — Lead chốt sau khi xác nhận không có
                  phiên ux-ui nào đang hoạt động để hỏi). 280px là ước lượng
                  đầu — đủ ~3-4 giao dịch, CHƯA đo/tinh chỉnh trên màn hình
                  thật, chỉnh lại nếu QA/QC thấy cụt/thừa. */}
              <div style={{ maxHeight: 280, overflowY: "auto" }}>
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
            </RailCardGatedByOtp>
          </div>
          <div className="card">
            <div className="rail-title">Lịch sử khiếu nại của bạn</div>
            {/* Lỗi 12 (PO thật 19/08, Lead [ĐO]): CÙNG lớp lỗi "chính sách
                đúng, áp thiếu một nhánh" đã vá 3 lần khác trong ngày — cổng
                OTP V6 áp cho thẻ giao dịch nhưng SÓT thẻ này. Dùng CHUNG
                `RailCardGatedByOtp` với thẻ trên, không tự viết `!otpVerified
                ?` riêng — thẻ thứ ba sau này thừa hưởng cổng tự động. */}
            <RailCardGatedByOtp
              otpVerified={otpVerified}
              onXacThuc={() => void beginOtpFlow()}
              thongDiepChuaXacThuc="Xác thực OTP để xem lịch sử khiếu nại"
            >
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
            </RailCardGatedByOtp>
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
              if (m.from === "staff") {
                return (
                  <div className="bubble-row from-bot" key={m.id}>
                    <div className="bubble bubble-bot">{m.text}</div>
                  </div>
                );
              }
              if (m.from === "system") {
                return (
                  <div className="bubble-row" key={m.id}>
                    <div className="bubble-system">{m.text}</div>
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
                      <OtpForm
                        disabled={m.resolved}
                        checking={m.checking}
                        error={m.error}
                        onSubmit={(code) => void submitOtp(m.id, m.sessionId, code)}
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
              key={inputResetKey}
              placeholder={inputEnabled ? "Nhập tin nhắn..." : "Chọn một lựa chọn phía trên để tiếp tục"}
              value={input}
              disabled={!inputEnabled}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.nativeEvent.isComposing && !e.repeat) handleSend();
              }}
              // CONSUME-001 — khớp AgentChatRequest.message (src/api/schemas.py)
              maxLength={4000}
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
          {/* Thông báo xử lý dữ liệu — bản demo dùng dữ liệu mô phỏng, nhưng
              người test là NGƯỜI THẬT gõ chữ thật, nên vẫn cần cho họ biết nội
              dung chat được xử lý bởi nhà cung cấp AI nước ngoài. Đây là căn cứ
              pháp lý cơ bản (NĐ 13/2023) và thực sự làm giảm lượng PII đi vào —
              đọc rồi thì người ta không gõ số điện thoại thật. Xem ADR-011. */}
          <div className="chat-disclaimer" style={{ paddingTop: 0 }}>
            <svg className="icon icon-sm" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" /><path d="M12 11v5M12 7.5h.01" /></svg>
            Bản demo dùng dữ liệu mô phỏng — vui lòng <strong>không nhập thông tin cá nhân thật</strong>.
            Nội dung chat được xử lý bởi AI của nhà cung cấp nước ngoài.
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
          {liveChatTicketId && (
            <div className="card" style={{ marginTop: 12 }}>
              <div className="rail-title">Chat trực tiếp CSKH</div>
              <div className="dim" style={{ fontSize: 12 }}>
                {liveChatStatus === "connecting" ? "Đang kết nối..." : liveChatStatus === "open" ? "Đã kết nối" : liveChatStatus === "closed" ? "Mất kết nối" : "Lỗi kết nối"}
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
