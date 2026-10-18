"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import BannerLechVai from "@/components/BannerLechVai";
import OtpInput from "@/components/OtpInput";
import { ApiError, agentChat, getCustomerHistory, requestLiveChatWsTicket, requestOtp, verifyOtp } from "@/lib/api";
import { COMPLAINT_TYPE_LABEL, labelOf, type ComplaintType, type CustomerHistory } from "@/lib/types";
import { useI18n } from "@/lib/i18n/client";
import { docLang, translate } from "@/lib/i18n/core";
import type { DictKey } from "@/lib/i18n/dict";
import { rich } from "@/lib/i18n/rich";
import { formatDateTime, formatMoney } from "@/lib/format";
import { useLiveChatSocket, type LiveChatEvent } from "@/lib/useLiveChatSocket";

// Complaint.status (different from Ticket.hitl_status) — the current dataset/pipeline only uses
// "investigating"/"resolved", but there's no CHECK constraint enforcing it in the DB, so this falls
// back to the raw original string for an unfamiliar value.
const COMPLAINT_STATUS_LABEL: Record<string, DictKey> = {
  investigating: "chat.cstatus.investigating",
  resolved: "chat.cstatus.resolved",
  rejected: "chat.cstatus.rejected",
};

const COMPLAINT_CHIPS: { value: ComplaintType; label: string; starter: string }[] = [
  { value: "wrong_recipient", label: "Chuyển nhầm", starter: "Tôi bị chuyển nhầm tiền." },
  { value: "money_not_received", label: "Tiền chưa về", starter: "Tôi chuyển tiền mà bên kia chưa nhận được." },
  { value: "double_charge", label: "Trừ tiền 2 lần", starter: "Tôi bị trừ tiền 2 lần cho cùng 1 giao dịch." },
  { value: "refund", label: "Hoàn tiền", starter: "Tôi được duyệt hoàn tiền nhưng chưa thấy tiền về." },
];

// OTP verification is only needed when the agent REALLY touches transaction/account data or creates
// a ticket — a generic policy/fee question doesn't need it.
//
// Finding B2 (phase 2.5) — `create_ticket` being MISSING here is ONE of two independent causes of
// Finding B (an AND condition; patching only one isn't enough — see otpStaleCall below for the
// other half): when this tool fails because the OTP has expired, it doesn't produce a `ticket_id`
// (the creation failed) AND, before this patch, it wasn't in the "sensitive" set either ⟹
// touchedSensitiveData=false ⟹ no OTP re-prompt.
const SENSITIVE_TOOLS = new Set(["lookup_transaction", "get_customer_history", "create_ticket"]);

// Finding B1 (phase 2.5, DECISION B — docs/giao-viec/2026-08-19-gd25-va-finding-ab-otp.md, commit
// 32751c2, decided by the real PO on Aug 19) — an expired OTP NEVER reaches the client as an HTTP
// 403 on the real agent path (only a DIRECT HTTP call to /tools/create_ticket gets a 403, and
// ChatClient never calls that route — see customer_tools.py:632-635: the tool returns
// `{"status":"error",...}` INSIDE a normal 200 response, it never raises). The ONLY way to
// recognise it, given the backend is FROZEN this round: match EXACTLY the constant string the
// backend itself wrote (VERY DIFFERENT from matching a THIRD-PARTY PROVIDER's error body — banned
// in phase 3: this is a literal WE OWN, under version control, pinnable by a guard).
//
// 🔴 Match `_OTP_EXPIRED_ERROR` ONLY (customer_tools.py:600-603) — do NOT match
// `_OTP_REQUIRED_ERROR` (returned at :814·:863·:905, condition `otp_verified_at is None` — the
// customer has NEVER verified). Not an oversight, there's a measured reason: the REQUIRED case only
// happens when `otp_verified_at is None`, meaning `otpVerifiedRef.current` is already FALSE (never
// verified this session) ⟹ the condition `touchedSensitiveData && !otpVerifiedRef.current` below
// FIRES ON ITS OWN, no extra signal needed. The EXPIRED case is the OPPOSITE: already verified once
// so `ref` is TRUE ⟹ that condition does NOT fire — this is the ONE case that needs otpStaleCall.
// Once B2 lands (create_ticket added to SENSITIVE_TOOLS), the REQUIRED case gets covered FOR FREE
// through that exact same path, including for create_ticket.
// ⟹ Also matching REQUIRED wouldn't be slightly redundant — it would be ENTIRELY redundant, and it
// costs a guard-pin test that doesn't cover it (guard ② only checks EXPIRED — see
// ChatClient.pin.test.ts). A WRONG match (REQUIRED included) falls through the touchedSensitiveData
// branch below as normal — it does NOT get silently folded into OTP as UNDETERMINED (Security's
// three-state rule).
//
// 🔴 A DEBT REPAID (Aug 20) — the backend now has a STRUCTURED `loai:"otp_het_tuoi"` field inside
// `_OTP_EXPIRED_ERROR` (customer_tools.py:600-611). Read `loai` FIRST, fall back to a string match
// ONLY when `loai` is absent — NOT a straight replacement: the backend/frontend are TWO SEPARATELY
// BUILT IMAGES, and a mismatched-image window (an older backend image without `loai`, a newer
// frontend image that already dropped the fallback) would make OTP-expiry detection fail SILENTLY —
// the same bug class Finding B just patched, just a contract BETWEEN TWO IMAGES instead of between
// the DB and an image. Remove the fallback branch + `OTP_EXPIRED_MESSAGE` in a LATER round, once
// every image is confirmed to carry `loai`.
const OTP_EXPIRED_LOAI = "otp_het_tuoi";
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
  // crypto.randomUUID() instead of a module-level counter — the counter gets reset to 0 by Next.js
  // Fast Refresh (dev) every time a file is edited while old state (already holding an id like
  // "m1"...) is still around, causing a duplicate React key ("Encountered two children with the
  // same key"). A UUID doesn't depend on module state, so it never collides, even across a hot
  // reload.
  return crypto.randomUUID();
}

// AUTH5-01 (Auth Flow upgrade, 2026-08-12, NIST SP 800-63B-4) — dropped the "security answer" field
// entirely: KBA is no longer an authenticator, an OTP code is the only step-up factor (see
// src/api/main.py::verify_otp). A shared 6-digit OTP input (`OtpInput`, split out Aug 31 for reuse
// in the supervisor-approval flow) — see `@/components/OtpInput.tsx`.

// Bug 12 (real PO, Aug 19, docs/giao-viec/2026-08-19-gd4-po-test-4-loi-ui.md item 12): the V6 OTP
// gate applied to the "Recent transactions" card but MISSED the "Complaint history" card — the same
// bug class "the policy is correct, applied to one branch only" that was patched 3 other times that
// same day (scrub_pii/cong_chi_tieu/_ghi_so). Security + the Lead decided: ONE place defines the
// gate, instead of each card writing its own `!otpVerified ?` check — a future third card inherits
// the gate automatically, with no one needing to remember to copy the pattern correctly.
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
  const { t } = useI18n();
  if (!otpVerified) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        <div className="dim" style={{ fontSize: 12 }}>
          {thongDiepChuaXacThuc}
        </div>
        <button className="btn btn-outline btn-sm" type="button" onClick={onXacThuc}>
          {t("chat.verifyNow")}
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
  // Finding A (phase 2.5 / M-10) — computed UPFRONT from the session at page-render time (the
  // server, page.tsx), 12h per OTP_VIEW_MAX_MINUTES. The "LucTai" ("-at-load-time") in the name is
  // DELIBERATE (Lead/PO-agent): this is a SNAPSHOT taken at render time, NOT a live state — if the
  // page stays open past 12h, this value is STALE, exactly as its name says. It ONLY gates showing
  // the "Recent transactions" card AT PAGE LOAD — it is NOT used to skip the OTP prompt before a
  // sensitive action (that's `otpVerifiedRef`, a different variable for a different purpose: it is
  // correct exactly because it resets on every mount; the "expired WHILE the page stays open" case
  // is Finding B's job — see sendToAgent).
  otpXemConHanLucTai: boolean;
}) {
  // UI-02 — the current session's role does NOT match this screen. Set from the API's 403 response
  // rather than read at render time: the already-open tab never navigates, so the guard route
  // (`proxy.ts`) never runs — the 403 is the ONLY signal.
  const { t, lang } = useI18n();
  const [vaiLech, setVaiLech] = useState<string | null>(null);
  const [history, setHistory] = useState<CustomerHistory | null>(null);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [stage, setStage] = useState<Stage>("greeting");
  const [input, setInput] = useState("");
  const [lastTicket, setLastTicket] = useState<{ ticket_id: string; should_escalate: boolean } | null>(null);
  // Live chat (2026-08-11) — a customer asking for a human (request_human_handoff, CTRL-001)
  // doesn't return ticket_id at the TOP LEVEL of AgentChatResult (only create_ticket does that, see
  // src/agents/graph.py) — it has to be dug out of tool_calls to know which ticket_id to open the
  // live-chat panel for.
  const [liveChatTicketId, setLiveChatTicketId] = useState<string | null>(null);
  // Live chat (2026-08-11, a real finding from manual testing) — support-agent messages are merged
  // DIRECTLY into the same .chat-thread as the AI, with NO separate chat window opened below — the
  // feel must be "the AI handing off to a human within the SAME conversation", not two separate
  // windows.
  const [liveChatWsTicket, setLiveChatWsTicket] = useState<string | null>(null);
  const [liveChatSessionId, setLiveChatSessionId] = useState<string | null>(null);
  const liveChatConnectStartedRef = useRef(false);
  // The ref-guard KEEPS its original purpose (blocking a StrictMode double-invoke, a real reason
  // from 2026-08-11 — the same pattern as greetedRef). `lanThuLai` ("retry count") is a DELIBERATE
  // user-triggered reopening path, not a removal of the ref.
  const [lanThuLai, setLanThuLai] = useState(0);
  const [loiKetNoiChat, setLoiKetNoiChat] = useState(false);
  const threadRef = useRef<HTMLDivElement>(null);
  const greetedRef = useRef(false);
  // Verified once per session — once true, no re-prompting for OTP even if a chip/card/the agent
  // touches sensitive data again later in the same chat session. ALWAYS initialised to `false` —
  // DELIBERATELY, unlike `otpVerified` below (see Finding A/B, phase 2.5). This ref guards the step
  // "ask for OTP BEFORE an about-to-happen sensitive action" (chip/sendToAgent) — a wrong value is
  // CHEAP in the direction of asking once too often (acceptable), whereas pre-setting it to `true`
  // from a value computed at render time could let an action through whose STEP-UP had expired even
  // while the VIEW window was still valid — the source of truth for that case is a live
  // 403/tool-error, not something inferred at mount time (handled by Finding B).
  const otpVerifiedRef = useRef(false);
  // No longer "a state copy of the ref above" (unlike V6/Aug 14) — the two variables are now
  // deliberately separated: the ref (above) guards an about-to-happen action, the state (below)
  // only guards the DISPLAY of the "Recent transactions" card and is ALLOWED to be optimistically
  // initialised from the real session (Finding A) because getting it wrong only affects the UI — at
  // worst the card opens when it shouldn't because otp_verified_at expired 12h ago, while every
  // route that reads real data still checks otp_verified_at on the server itself (INV-10) — nothing
  // leaks through this path.
  const [otpVerified, setOtpVerified] = useState(otpXemConHanLucTai);
  // The message waiting to be sent to the agent AFTER OTP verification finishes — used for the 2
  // entry points that already know for certain they relate to a transaction/ticket FROM THE START
  // (a chip, "Report this transaction"): verification must happen BEFORE calling the agent, not
  // asked for after the agent has already attempted a lookup/ticket creation.
  const pendingStarterRef = useRef<string | null>(null);

  useEffect(() => {
    getCustomerHistory({}).then(setHistory).catch(() => setHistory(null));
    // React StrictMode (dev) runs an effect twice on mount to catch missing cleanup — without a
    // guard, the greeting gets pushed twice. The ref survives those 2 runs (unlike state), so it
    // blocks it down to exactly one.
    if (greetedRef.current) return;
    greetedRef.current = true;
    // The 4 complaint-type chips no longer live here — they duplicated the chip that appears after
    // clicking "Report this transaction" (the right place to pick a problem type, since it's
    // already tied to one specific transaction). Here, the customer typing freely is enough.
    push({
      id: nid(),
      from: "bot",
      // DISC-002 (FIN05_QA_TestCases.jsonl, EU AI Act Art. 50) — spells out "AI assistant" right
      // inside the greeting message itself, not only in the page title/a fixed label outside the
      // chat window (those two exist but don't satisfy the literal "banner/opening statement" the
      // transparency standard requires). The Aug 19 greeting (the morning-of-Aug-19 version,
      // drafted by the PO-agent from a 4-paragraph brief —
      // docs/giao-viec/2026-08-19-gd4-po-test-4-loi-ui.md item 11 — then SHORTENED per the real
      // PO's own direct request later that same day: keeping the required "AI assistant" phrase + a
      // quick entry point, dropping the long-winded explanation of
      // look-up-ability/non-decision-making).
      text: translate(docLang(), "chat.greeting"),
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  // Open the WS ticket + connect IMMEDIATELY on detecting a handoff — a ref-guard blocks a
  // StrictMode double-invoke (the exact cause of messages getting duplicated/split when sending, a
  // real finding, 2026-08-11 — same pattern as greetedRef above).
  useEffect(() => {
    if (!liveChatTicketId || liveChatConnectStartedRef.current) return;
    liveChatConnectStartedRef.current = true;
    requestLiveChatWsTicket(liveChatTicketId)
      .then((res) => {
        setLiveChatSessionId(res.chat_session_id);
        setLiveChatWsTicket(res.ws_ticket);
      })
      .catch(() => {
        // UI-02 — REOPENING THE RETRY DOOR. Before this version, `liveChatConnectStartedRef` was
        // set `true` once and NEVER reset anywhere (grepped the whole repo: exactly 3 lines — the
        // declaration, the check, the set). One attempt, forever. And `.catch` told the customer
        // "please try again" while there was NO path to try again at all: the effect only re-runs
        // when `liveChatTicketId` changes, and it never does.
        //
        // ⚠️ RESETTING THE REF ALONE ISN'T ENOUGH — if the deps don't change, the effect doesn't
        // re-run even once the ref is back to false. `lanThuLai` must be in the deps. A patch that
        // only resets the ref would LOOK correct and have NO effect.
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
        // Echoing the message the CUSTOMER THEMSELVES just sent — the one source of truth is the
        // server; don't echo locally at send time, to avoid showing a duplicate.
        setMessages((prev) => (prev.some((m) => m.id === event.message_id) ? prev : [...prev, { id: event.message_id, from: "user", text: event.content }]));
      }
    } else if (event.type === "system") {
      setMessages((prev) => [...prev, { id: nid(), from: "system", text: event.text }]);
    } else if (event.type === "session_closed") {
      // The live chat session has ended (the support agent clicked "End chat", or the customer just
      // lost their connection and the server closed it on its own — see
      // close_customer_session_on_disconnect) — go back to talking with Sen, instead of letting the
      // customer keep typing into a session that died silently.
      setMessages((prev) => [...prev, { id: nid(), from: "system", text: translate(docLang(), "chat.liveEnded") }]);
      setLiveChatSessionId(null);
      setLiveChatWsTicket(null);
      setLiveChatTicketId(null);
    } else if (event.type === "error") {
      setMessages((prev) => [...prev, { id: nid(), from: "system", text: event.text }]);
    }
  }, []);

  const { status: liveChatStatus, sendMessage: sendLiveChatMessage } = useLiveChatSocket(liveChatWsTicket, handleLiveChatEvent);

  // A leave-page warning while chatting live with a support agent (2026-08-11) — F5/closing the tab
  // DISCONNECTS the WS, and the server closes the session IMMEDIATELY on its own (see
  // close_customer_session_on_disconnect in live_chat_ws.py) — the customer needs to know
  // beforehand that leaving the page now means ending the live chat session on BOTH ends, not just
  // their own screen. Modern browsers don't allow customising the native dialog's content, only
  // turning it on/off.
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

  // The problem-type chip shown after clicking "Report this transaction" — always attaches
  // complaint_type explicitly to the starter message, NEVER sending the agent a message that's just
  // a transaction ID with no stated problem (the agent has created a ticket hastily on an ambiguous
  // message like that before, even with the prompt spelling it out — an LLM doesn't follow
  // instructions with 100% certainty, so it's blocked outright at the UI layer).
  // Calls the REAL /auth/otp/request (the backend now verifies for real, no longer a pure UI gate —
  // see src/auth.py::require_otp_verified) before showing the OTP form. AUTH5-01 (2026-08-12) — no
  // more security question (KBA dropped from the authenticator role), only the OTP code. On failure
  // (network loss...), show an error instead of a fake form.
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
      push({ id: nid(), from: "bot", text: t("chat.otpRequestFailed") });
      setStage("chat");
    }
  }

  function startComplaint(
    c: (typeof COMPLAINT_CHIPS)[number],
    tx: NonNullable<CustomerHistory["recent_transactions"]>[number]
  ) {
    const chipLabel = labelOf(COMPLAINT_TYPE_LABEL, c.value, lang) ?? c.label;
    const label = t("chat.complaintLabel", { label: chipLabel, id: tx.trans_id });
    // Sent to the agent — always Vietnamese (see COMPLAINT_CHIPS).
    const starter = `${c.starter} Giao dịch liên quan: ${tx.trans_id} (${formatMoney(tx.amount, "vi")} lúc ${formatDateTime(tx.created_at, "vi")}).`;
    push({ id: nid(), from: "user", text: label });
    if (otpVerifiedRef.current) {
      void sendToAgent(starter, { echoAsUser: false });
      return;
    }
    push({
      id: nid(),
      from: "bot",
      text: t("chat.needOtpFor", { label: lang === "en" ? chipLabel : chipLabel.toLowerCase() }),
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
            ? { ...m, checking: false, error: e instanceof ApiError ? e.message : t("chat.otpFailed") }
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
      // An entry point that already knows for certain it relates to a transaction (chip/card) —
      // only now actually sends it to the agent, AFTER verification has finished.
      //
      // `vuaXacThucDeGuiLai: true` ("just-verified-resend") — an EXPLICIT flag marking this as a
      // turn that RESENDS a message OTP had blocked (scratchpad/nhap-cong-thu-slot-sau-otp.md item
      // 1). This is EXACTLY ONE resend call, shared by all 3 sources that set `pendingStarterRef`
      // (the startComplaint chip · otpStaleCall mid-conversation · touchedSensitiveData) — no
      // distinction by source, all meaning the same thing: "the customer just finished verifying,
      // this is the message the model needs to process again".
      push({ id: nid(), from: "bot", text: t("chat.otpOkLookup") });
      void sendToAgent(starter, { echoAsUser: false, vuaXacThucDeGuiLai: true });
    } else {
      // A reaction (typing freely, the agent just happened to touch sensitive data) — nothing to
      // resend, just reopen the chat.
      push({ id: nid(), from: "bot", text: t("chat.otpOkContinue") });
      setStage("chat");
    }
  }

  function reportFromRail(tx: NonNullable<CustomerHistory["recent_transactions"]>[number]) {
    // Don't send straight to the agent — clicking this button only tells us which transaction, not
    // yet what the problem is. Ask the customer to pick a problem type first (a chip), then combine
    // it with the transaction info via startComplaint().
    push({
      id: nid(),
      from: "bot",
      text: t("chat.whichProblem", { amount: formatMoney(tx.amount, lang), time: formatDateTime(tx.created_at, lang) }),
      chips: COMPLAINT_CHIPS.map((c) => ({ label: labelOf(COMPLAINT_TYPE_LABEL, c.value, lang) ?? c.label, onClick: () => startComplaint(c, tx) })),
    });
  }

  async function sendToAgent(text: string, opts?: { echoAsUser?: boolean; vuaXacThucDeGuiLai?: boolean }) {
    if (opts?.echoAsUser !== false) push({ id: nid(), from: "user", text });
    setStage("busy");
    try {
      const result = await agentChat({
        message: text,
        vua_xac_thuc_de_gui_lai: opts?.vuaXacThucDeGuiLai,
      });
      push({
        id: nid(),
        from: "bot",
        text: result.reply,
        cite: result.tool_calls.length
          ? t("chat.source", { tools: result.tool_calls.map((c) => c.tool_name).join(" → ") })
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
      // Refresh the "Complaint history" card after EVERY turn that touches a tool (not only right
      // after creating a new ticket) — the agent might just MENTION an already-created ticket again
      // (without returning a ticket_id this turn); the customer still needs to see the real data
      // instead of only hearing the agent describe it in words.
      if (result.tool_calls.length > 0) {
        getCustomerHistory({}).then(setHistory).catch(() => {});
      }

      // ④ (Aug 25) — the DETERMINISTIC OTP GATE already blocked this turn BEFORE it ever touched
      // the model (backend: src/agents/graph.py, DUONG_CAN_OTP). Must be checked BEFORE the two
      // branches below: both of them probe `tool_calls`, but this path calls no tool at all, so
      // `tool_calls` is EMPTY — neither branch fires, and the customer would be left staring at a
      // "please verify" message with nothing to open.
      //
      // Reads the `duong` ("path") KEY, does NOT match the `reply` text — a future change to the
      // backend's wording must not blind the client again (the same reason OTP_EXPIRED_LOAI was
      // created in phase 2.5).
      //
      // 🔴 Do NOT `push(result.reply)` here. Line :501 above already pushed it, UNCONDITIONALLY,
      // for EVERY path — including this one. The original version pushed it a second time, and the
      // customer saw that EXACT SAME bubble appear twice, character for character (PO measured Aug
      // 25: the backend sends 8 sentences → the screen shows 12 bubbles).
      //
      // The anti-impersonation sentence K3 STILL reaches the customer — it's inside `result.reply`,
      // and :501 already pushed it. That worry is valid; it's just already handled above.
      // (`cite` at :501 is `undefined` on this path because `tool_calls` is empty, so the two
      // bubbles would be exactly identical anyway — keeping the first one loses no text.)
      if (result.duong === "can_otp") {
        pendingStarterRef.current = text;
        void beginOtpFlow();
        return;
      }

      // Finding B1 (phase 2.5, Decision B) — the tool just failed because the OTP expired
      // MID-SESSION (`otpVerifiedRef.current` is still `true` from an earlier verification; the
      // backend is now the source of truth). Read `loai` FIRST (newer backend image), fall back to
      // an EXACT match on `message` (an older backend image doesn't carry `loai` yet — see the
      // comment at the OTP_EXPIRED_LOAI/_MESSAGE declaration above). No extra filtering by
      // tool_name needed: both signals can only be produced by 3 tools
      // (lookup_transaction/get_customer_history/create_ticket), which is already narrow enough.
      const otpStaleCall = result.tool_calls.find(
        (c) =>
          c.result.status === "error" &&
          (c.result.loai === OTP_EXPIRED_LOAI || c.result.message === OTP_EXPIRED_MESSAGE)
      );
      if (otpStaleCall) {
        push({
          id: nid(),
          from: "bot",
          text: t("chat.reverifyOtp"),
        });
        pendingStarterRef.current = text;
        void beginOtpFlow();
        return;
      }

      // OTP verification is needed only for touching real transaction/account data
      // (SENSITIVE_TOOLS) or just creating a new ticket — and only asked ONCE per session. A
      // generic policy/fee question (only calling search_policy) doesn't need it.
      const touchedSensitiveData =
        result.tool_calls.some((c) => SENSITIVE_TOOLS.has(c.tool_name)) || !!result.ticket_id;
      if (touchedSensitiveData && !otpVerifiedRef.current) {
        push({
          id: nid(),
          from: "bot",
          text: t("chat.needOtpSensitive"),
        });
        // Bug 1 (real PO, Aug 19): missing this line LOST the question the customer had just asked
        // once verification finished — forcing them to retype it exactly when they were already
        // frustrated. The same `pendingStarterRef` pattern already used in startComplaint() (:392)
        // and otpStaleCall (:488) — submitOtp() resends `text` itself once the OTP is confirmed
        // (otpVerifiedRef=true now, so the tool will be able to run).
        pendingStarterRef.current = text;
        void beginOtpFlow();
        return;
      }
      setStage("chat");
    } catch (e) {
      // A role mismatch = a 403 WITH a string WE OWN (auth.py:306 require_role) — NOT a generic
      // /role/i, which would match any error that happens to contain the word "role". Prefer
      // `status` (a STRONG signal, part of the HTTP contract, already carried by ApiError) over
      // matching text (a WEAK signal) — the same rule already decided for `_DAU_HIEU_HET_HAN_MUC`
      // ("expiry signal"): prefer status_code when available, only fall back to a string when there
      // ISN'T one. status===403 with NO string match ⟹ the THREE-STATE rule still holds: it falls
      // through to the UNDETERMINED branch below (pushing a generic error), ABSOLUTELY never
      // silently folded into "role mismatch" — hiding a real error costs more than losing one
      // nicely worded message. Dumping the literal `"Requires role in ['customer'], current account
      // is cskh"` straight into the chat window is the exact thing the PO saw in the middle of a
      // demo — meaningless to a user and looking like a broken product.
      if (e instanceof ApiError && e.status === 403 && e.message.includes("Cần role thuộc")) {
        const m = /hiện tại là (\w+)/.exec(e.message);
        setVaiLech(m?.[1] ?? "khác");
        setStage("chat");
        return;
      }
      // 27/08 [measured] p-226-f0: a 401 here ONLY ever means "the session has expired" (see the
      // comment at lib/api.ts::dieuHuongKhiHetPhien) — lib/api.ts already redirects to the right
      // gate on its own AND rewrites the message into human-readable copy; this branch just
      // re-shows that same sentence, instead of dumping the raw e.message like the generic branch
      // below (that raw dump is exactly what the PO saw mid-demo: "the chat shows an error").
      if (e instanceof ApiError && e.status === 401) {
        push({ id: nid(), from: "bot", text: e.message });
        setStage("chat");
        return;
      }
      push({
        id: nid(),
        from: "bot",
        text: e instanceof ApiError ? t("chat.errorPrefix", { msg: e.message }) : t("chat.connectError"),
      });
      setStage("chat");
    }
  }

  const liveChatSendingRef = useRef(false);
  // A real finding (2026-08-11): the input box sometimes still has leftover text after sending even
  // though setInput("") ran — forces React to fully remount the <input> (changing its key) after
  // EVERY send (both the AI and live-chat branches) to guarantee it's clean regardless of timing.
  const [inputResetKey, setInputResetKey] = useState(0);

  function handleSend() {
    const text = input.trim();
    if (!text || stage === "otp" || stage === "busy") return;
    // Once a live chat connection is established, EVERY message goes through the support agent, no
    // longer through the AI — the same window, only the "listener" behind it changes.
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
        <span className="eyebrow">{t("chat.eyebrow")}</span>
        <h1>{t("chat.title")}</h1>
        {/* 27/08 — Marketing (p-226-17) đổi: câu cũ là phát biểu TUYỆT ĐỐI,
            cùng hình dạng lỗi vừa vá ở /login, và ĐÃ TỪNG SAI THẬT (ca bot
            báo "đã tạo hồ sơ" trong khi không tạo, mã hồ sơ thuộc khách
            khác). Câu mới nói về QUY TRÌNH (kiểm được, có ca mẫu TCK-DEMO-02)
            thay vì kết quả tuyệt đối; "mọi đề xuất đều có người kiểm" là vế
            DUY NHẤT thật sự tuyệt đối — ép ở CheckConstraint DB, không phải
            hành vi mô hình. Copy nguyên văn marketing, không tự viết lại. */}
        <p className="sub">
          {t("chat.sub")}
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
          {t("chat.liveConnectError")}{" "}
          <button
            type="button"
            onClick={() => {
              setLoiKetNoiChat(false);
              setLanThuLai((n) => n + 1);
            }}
            style={{ background: "none", border: "none", padding: 0, cursor: "pointer", textDecoration: "underline", font: "inherit", color: "inherit", fontWeight: 600 }}
          >
            {t("chat.retry")}
          </button>
        </div>
      )}

      <div className="chat-shell">
        <div className="chat-rail">
          <div className="card">
            <div className="rail-title">{t("chat.recentTx")}</div>
            {/* V6 (hotfix 14/08, PO thật quyết đổi chính sách): chưa xác thực OTP
                thì KHÔNG hiện danh sách giao dịch. Đây là gate ở TẦNG HIỂN THỊ —
                route đọc phía backend giữ nguyên theo contract hiện hành
                (authority-matrix.yaml), OTP vẫn được ép thật trên đường agent
                (INV-10). Muốn ép ở backend thì phải đổi contract → ADR + PO
                duyệt (nợ đã ghi cho đợt sau demo). */}
            <RailCardGatedByOtp
              otpVerified={otpVerified}
              onXacThuc={() => void beginOtpFlow()}
              thongDiepChuaXacThuc={t("chat.otpToSeeTx")}
            >
              {history?.recent_transactions.length === 0 && <div className="dim" style={{ fontSize: 12 }}>{t("chat.noTx")}</div>}
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
                      <span>{tx.direction === "out" ? t("chat.out") : t("chat.in")}</span>
                      <span className="txn-amount">{formatMoney(tx.amount, lang)}</span>
                    </div>
                    <div className="txn-meta">{formatDateTime(tx.created_at, lang)} · {tx.trans_id}</div>
                    <button className="txn-report" onClick={() => reportFromRail(tx)} type="button">
                      <svg className="icon icon-sm" viewBox="0 0 24 24"><path d="M4 4v16l4-4h12V4H4z" /></svg>
                      {t("chat.reportTx")}
                    </button>
                  </div>
                ))}
              </div>
            </RailCardGatedByOtp>
          </div>
          <div className="card">
            <div className="rail-title">{t("chat.complaintHistory")}</div>
            {/* Lỗi 12 (PO thật 19/08, Lead [ĐO]): CÙNG lớp lỗi "chính sách
                đúng, áp thiếu một nhánh" đã vá 3 lần khác trong ngày — cổng
                OTP V6 áp cho thẻ giao dịch nhưng SÓT thẻ này. Dùng CHUNG
                `RailCardGatedByOtp` với thẻ trên, không tự viết `!otpVerified
                ?` riêng — thẻ thứ ba sau này thừa hưởng cổng tự động. */}
            <RailCardGatedByOtp
              otpVerified={otpVerified}
              onXacThuc={() => void beginOtpFlow()}
              thongDiepChuaXacThuc={t("chat.otpToSeeComplaints")}
            >
              {history?.complaints.length === 0 && <div className="dim" style={{ fontSize: 12 }}>{t("chat.noComplaints")}</div>}
              {history?.complaints.map((c) => (
                <div className="hist-item" key={c.complaint_id} style={{ flexDirection: "column", alignItems: "flex-start", gap: 4 }}>
                  <div className="flex between center-y" style={{ width: "100%" }}>
                    <span className="id">{c.complaint_id}</span>
                    <span className="badge badge-neutral">{COMPLAINT_STATUS_LABEL[c.status] ? t(COMPLAINT_STATUS_LABEL[c.status]) : c.status}</span>
                  </div>
                  <div className="dim" style={{ fontSize: 11 }}>
                    {labelOf(COMPLAINT_TYPE_LABEL, c.type, lang)} · {formatDateTime(c.created_at, lang)}
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
              <div className="name">{t("chat.botName")}</div>
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
                          {t("chat.demoOtp", { phone })} <strong>{m.demoOtpCode}</strong>
                        </span>
                      </div>
                      <OtpInput
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
              placeholder={inputEnabled ? t("chat.typeMessage") : t("chat.pickOption")}
              value={input}
              disabled={!inputEnabled}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.nativeEvent.isComposing && !e.repeat) handleSend();
              }}
              // CONSUME-001 — matches AgentChatRequest.message (src/api/schemas.py)
              maxLength={4000}
            />
            <button
              className="icon-btn send"
              disabled={!inputEnabled}
              onClick={handleSend}
              type="button"
              aria-label={t("chat.sendAria")}
            >
              <svg className="icon" viewBox="0 0 24 24"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" /></svg>
            </button>
          </div>
          <div className="chat-disclaimer">
            <svg className="icon icon-sm" viewBox="0 0 24 24"><rect x="4" y="11" width="16" height="9" rx="2" /><path d="M8 11V7a4 4 0 018 0v4" /></svg>
            {t("common.neverAsk")}
          </div>
          {/* Thông báo xử lý dữ liệu — bản demo dùng dữ liệu mô phỏng, nhưng
              người test là NGƯỜI THẬT gõ chữ thật, nên vẫn cần cho họ biết nội
              dung chat được xử lý bởi nhà cung cấp AI nước ngoài. Đây là căn cứ
              pháp lý cơ bản (Luật 91/2025/QH15 + NĐ 356/2025) và thực sự làm giảm lượng PII đi vào —
              đọc rồi thì người ta không gõ số điện thoại thật. Xem ADR-011. */}
          <div className="chat-disclaimer" style={{ paddingTop: 0 }}>
            <svg className="icon icon-sm" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" /><path d="M12 11v5M12 7.5h.01" /></svg>
            {rich(t("chat.demoData"))}
          </div>
        </div>

        <div className="chat-rail" style={{ display: "flex", flexDirection: "column" }}>
          <div className="card">
            <div className="rail-title">{t("chat.statusTitle")}</div>
            {!lastTicket ? (
              <div className="dim" style={{ fontSize: 12 }}>{t("chat.noRequest")}</div>
            ) : (
              <div className="stepper">
                <div className="step">
                  <div className="step-dot done"><svg className="icon icon-sm" viewBox="0 0 24 24"><path d="M20 6L9 17l-5-5" /></svg></div>
                  <div className="step-body"><div className="step-label">{t("chat.stepIntake")}</div></div>
                </div>
                <div className="step">
                  <div className="step-dot done"><svg className="icon icon-sm" viewBox="0 0 24 24"><path d="M20 6L9 17l-5-5" /></svg></div>
                  <div className="step-body"><div className="step-label">{t("chat.stepInvestigate")}</div></div>
                </div>
                <div className="step">
                  <div className="step-dot current" />
                  <div className="step-body">
                    <div className="step-label">{t("chat.stepAwaitAgent")} {lastTicket.should_escalate && <span className="badge badge-critical" style={{ marginLeft: 4 }}>{t("chat.urgent")}</span>}</div>
                    <div className="step-note mono">{lastTicket.ticket_id}</div>
                  </div>
                </div>
                <div className="step"><div className="step-dot pending" /><div className="step-body"><div className="step-label">{t("chat.stepAwaitSupervisor")}</div></div></div>
                <div className="step"><div className="step-dot pending" /><div className="step-body"><div className="step-label">{t("chat.stepDone")}</div></div></div>
              </div>
            )}
          </div>
          {liveChatTicketId && (
            <div className="card" style={{ marginTop: 12 }}>
              <div className="rail-title">{t("chat.liveTitle")}</div>
              <div className="dim" style={{ fontSize: 12 }}>
                {liveChatStatus === "connecting"
                  ? t("live.connecting")
                  : liveChatStatus === "open"
                    ? t("live.connected")
                    : liveChatStatus === "closed"
                      ? t("live.disconnected")
                      : t("live.connError")}
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
