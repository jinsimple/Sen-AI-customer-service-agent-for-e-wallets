"""LangGraph agent for the core complaint flow (PRD §6) — the single entry point
`run_agent_turn()`, called from `POST /agent/chat` (src/api/main.py).

API note: `langgraph.prebuilt.create_react_agent` is deprecated in the installed
langgraph 1.2.10/langchain 1.3.14 — `langchain.agents.create_agent` is used instead
(the prompt parameter is named `system_prompt`, not `prompt`)."""
from __future__ import annotations

import datetime as dt
import json
import logging
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from typing import Any

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.errors import GraphRecursionError
from openai import (
    APIError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
)
from opentelemetry.trace import Status, StatusCode
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.agents import llm_pool
from src.agents.nodes.investigation_log import write_investigation_logs_for_ticket
from src.agents.output_filter import claims_ticket_created, filter_output, instruction_leak_signal
from src.agents.triage import (
    RULES_HASH,
    ROUTE_FULL,
    ROUTE_LIGHT,
    ROUTE_SLOT_FILL,
    ASK_SCAM_SCREENING,
    ASK_MISSING_AMOUNT,
    ASK_TIME_AND_AMOUNT,
    SIGNAL_1B_SLOT_ASKED,
    LIGHT_REPLIES,
    enough_to_narrow,
    is_wrong_transfer_case,
    is_personal_complaint,
    is_affirmative_reply,
    triage,
)
from src.agents.prompt import hash_prompt_template, build_system_prompt
from src.agents.tools.customer_tools import TurnGuard, _otp_fresh, build_customer_tools
from src.config import (
    AGENT_TURN_TIMEOUT_SECONDS,
    OTP_GATE_GROUP_B_ENABLED,
    T0_GATE_ENABLED,
    DATABASE_URL,
    DB_KIND,
    OTHER_SUPPORT_CHANNELS,
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MAX_TOKENS,
    LLM_MODEL,
    OPENAI_MAX_RETRIES,
    OPENAI_TIMEOUT_SECONDS,
    OTP_VIEW_MAX_MINUTES,
    TRIAGE_ENABLED,
    REASONING_ENABLED,
)
from src.egress_gate import (
    spend_gate,
    record_unreadable_spend,
    shared_http_client,
    is_blocked,
)
from src.build_stamp import HASH_METHOD, build_time_stamp
from src.db.models import Complaint, Ticket, User
from src.observability.langchain_callback import OTelTracingCallbackHandler
from src.observability.pii import scrub_pii
from src.observability.usage_ledger import record_usage
from src.observability.tracing import get_tracer
from src.services.complaint_intake import flag_human_handoff, merge_fraud_signals
from src.services.emotion_signals import evaluate_turn
from src.services.thread_signals import reset as clear_signal
from src.services.thread_signals import read_value, store_value
from src.services.thread_signals import read_or_unknown as read_signal
from src.services.thread_signals import bump as incr_signal
from src.tools.base import ToolError

_tracer = get_tracer("fin05.agent")
_logger = logging.getLogger("fin05.agents.graph")

# CONSUME-002 (FIN05_QA_TestCases.jsonl, OWASP LLM10:2025 Unbounded
# Consumption) — the real default of the installed langgraph (verified directly in
# `langgraph._internal._config.DEFAULT_RECURSION_LIMIT`) is 10007 steps, effectively equivalent
# to NO limit (the OpenAI budget/timeout would be exhausted long before reaching it if the agent
# got stuck in a loop of ambiguous tool calls). 20 is enough for a few real ReAct rounds (LLM
# reasoning + interleaved tool calls), far lower to stop infinite loops.
_AGENT_RECURSION_LIMIT = 20


class EmptyReplyError(RuntimeError):
    """The model returned empty content because it HIT THE TOKEN CAP — OUR configuration error.

    A dedicated class so the measurement suite can tell it apart from every other error.
    Swallowing it into an empty answer would make the yardstick record "the model answered
    poorly" for an infrastructure error of our own — miscounting our mistake as the provider's.
    """

# The JSON schemas of the 5 tools sent with EVERY model call — a constant, measured 2026-08-16.
# Update when adding/removing tools. See the explanation where `usage["input_chars"]` is built.
_CHARS_TOOL_SCHEMA = 6773

# Number of tools bound in the most recent agent build in this process. Written by the
# REQUEST-BUILDING layer, not the decision layer — see the comment where it is assigned.
_TOOLS_SENT_COUNT = 0

# Whether reasoning was ON in the most recent model build — read back from the model object,
# not from config. See the comment where it is assigned.
_REASONING_SENT = True

# ═══ SLOT-COLLECTION GATE AFTER MID-CONVERSATION OTP VERIFICATION ═══════════════
# (scratchpad/nhap-cong-thu-slot-sau-otp.md, Lead 24/08, proposed by the real PO,
# all 4 items approved by the PO-agent)
#
# THE PROBLEM: after the customer verifies OTP mid-conversation, the frontend AUTOMATICALLY
# RE-SENDS the message that was blocked (ChatClient.tsx::submitOtp() -> pendingStarterRef).
# `5e8deb6` taught the model to CALL the tool AGAIN instead of repeating an old conclusion from
# memory — a SYMPTOM fix, kept as a SAFETY NET (if the model ignores the rule, the net still
# holds when the resend already has enough slots). This gate REMOVES ENTIRELY the situation of
# relying on the model "remembering correctly": it asks for the missing slot via a DETERMINISTIC
# mechanism first, then calls the model EXACTLY ONCE with complete data.
#
# A SEPARATE KEY, NEVER shared with `SIGNAL_1B_SLOT_ASKED` — the Lead pushed back on the frame
# the PO-agent initially leaned towards ("reset the S7 marker = a fresh starting point"):
# resetting the S7 KEY ITSELF would let 1B fire A SECOND TIME in the same conversation on a later
# turn UNRELATED to this gate — exactly what S7 (1B's once-per-conversation limit) exists to
# forbid. The key below is COMPLETELY INDEPENDENT of 1B; don't "optimise" by merging the two keys
# even though their names sound alike.
_SIGNAL_OTP_RESEND_ASKED = "otp_resend_da_hoi"

# ⑭ (25/08) — SERVER-SIDE EVIDENCE that this thread WAS once blocked by the OTP gate.
# COMPLETELY DIFFERENT from `_SIGNAL_OTP_RESEND_ASKED` above (that one records "T0 HAS ALREADY
# ASKED"). Two keys, two different questions — don't merge them even though the names sound close.
_SIGNAL_OTP_BLOCKED = "da_bi_otp_chan"

# ⑨ — "the scam-screening question has already been asked in this thread". Once per conversation.
_SIGNAL_SCREENING_ASKED = "da_hoi_sang_loc"
# ⑨-turn-4 — two TURN-LOCATING signals. Kept separate because they answer two different
# questions: "is this thread a wrong-transfer case" and "has the transaction been found yet".
# Merging them loses the ability to fire on EXACTLY THE RIGHT TURN.
_SIGNAL_WRONG_TRANSFER_CASE = "ca_chuyen_nham"
_SIGNAL_TXN_FOUND = "da_tra_duoc_gd"

# GATE item 4 (04/09, the PO fixed fail-closed) — TWO NEW signals, completely different from
# the three above: those three are keyed per THREAD (once per conversation), the two below are
# keyed per TRANS_ID (once per TRANSACTION) — exactly the PO's requirement "each separate
# wrong-transfer case must be screened separately", not once for the whole thread.
#
# `_SIGNAL_TRANS_ID_PENDING_SCREENING` (keyed per THREAD, the value is the trans_id STRING, using
# `store_value`/`read_value`): "which transaction was the question fired on turn N ABOUT" — a
# mandatory bridge, because the turn firing the question (⑨, which knows the trans_id) and the
# turn receiving the answer (PIECE 4, which only has the customer's free text and doesn't
# naturally know which transaction it answers) are TWO DIFFERENT TURNS.
_SIGNAL_TRANS_ID_PENDING_SCREENING = "trans_id_cho_sang_loc"
# `_SIGNAL_SCREENING_DONE` (keyed per TRANS_ID, a counter — using
# `incr_signal`/`read_signal`): "this transaction HAS been asked AND HAS received a screening
# answer" — `create_ticket` (customer_tools.py) reads this signal via EXACTLY the `trans_id` about
# to get a ticket, to decide whether to allow or block. NEVER deleted:
# unlike `_SIGNAL_SCREENING_ASKED` (deleted after each question-answer round so it can be asked
# again for a LATER case), this signal must live FOREVER for that exact trans_id —
# a transaction only needs screening EXACTLY ONCE; asking again breaks things in a different way
# (the customer being asked repeatedly a question they already answered).
_SIGNAL_SCREENING_DONE = "sang_loc_xong"

# ADR-057 (docs/DECISIONS.md, 01/09) — EARLY HANDOFF for the "expensive tier".
# Counts TURNS (not a once-only condition like ⑨) — incremented on every turn still in the state
# "expensive tier, transaction not yet identified", read back at the gate applied below (near
# CTC1). Placed NEXT TO, NOT MERGED with, the ⑨ signals above — the two signal sets answer two
# different questions.
_SIGNAL_ESCALATION_TURNS = "luot_tang_dat"
# 🔴 N IS PROVISIONAL, on WEAK grounds (ADR-057 itself declares: the number comes from ONE
# measurement run, and the noise was shown to be large — 22/75 cases changed results when re-run
# on the same code, see ADR-056).
# CHANGING N = changing EXACTLY this constant — don't scatter the number 2 elsewhere.
_ESCALATION_HANDOFF_TURNS = 2
# The "expensive tier" — refund + wrong_recipient, the weakest of the 4 complaint types
# (14.0%/17.1% versus 26.7%/38.1%), and the money is ALREADY IN SOMEONE ELSE'S HANDS —
# a mistake here leaves the customer waiting for something that never comes, unlike the other 2
# types (a later turn can still correct it). The enum values match the CheckConstraint
# `ck_complaints_type` (src/db/models.py) — no other names invented.
_ESCALATING_COMPLAINT_TYPES = frozenset({"refund", "wrong_recipient"})
ROUTE_OTP_RESEND_SLOT_FILL = "otp_resend_thu_slot"
ROUTE_NEEDS_OTP = "can_otp"
FS13_HANDOFF_ROUTE = "fs13_ban_giao"

# The replacement reply when the hard-constraint-3 gate catches a claim with no real ticket.
# 🔴 NO promises, NO codes stated, and it TRUTHFULLY says the case wasn't created — fabricating
# reassurance here would repeat exactly the error just blocked. It only points to a step the
# customer CAN take, so they don't sit waiting for a case that doesn't exist.
_TICKET_NOT_CREATED_REPLY = (
    "Mình xin lỗi — hồ sơ khiếu nại CHƯA được tạo, mình báo thật để bạn không "
    "chờ nhầm. Bạn nhắn lại giúp mình để tạo lại, hoặc mình chuyển bạn sang "
    "chuyên viên hỗ trợ trực tiếp nhé."
)


def _gate_reply_before_lookup(outcome: dict[str, Any]) -> str:
    """The DETERMINISTIC reply replacing a turn blocked by the CTC1 gate (see where it is applied
    below) — built directly from the REAL result of `get_customer_history`, not handed to the
    model to rephrase (the same rule as ADR-048 applied to ⑧/⑨/_TICKET_NOT_CREATED_REPLY:
    one deterministic line is safer than betting on the model obeying the prompt).

    Lists at most the 5 most recent transactions — this is the CHATTING CUSTOMER'S OWN DATA
    (OTP-verified so this tool could run), not third-party PII, so no masking under BR-07 is
    needed.

    🔴 Caught by the PO (reading the diff before this function first ran): prompt.py:21
    REQUIRES the first sentence when about to state lookup results to open with "Mình
    hiểu..."/"Mình biết..." (I understand.../I know...), NEVER opening with the looked-up facts
    like "Mình đã tra cứu..." (I've looked up...). The first version of this function violated
    that almost verbatim — no automated gate caught it (grepping _harness.py/output_filter.py
    shows no such rule), so it was a quality regression slipping past every measurement with
    nobody knowing. The opener "Mình hiểu bạn đang sốt ruột." (I understand you're anxious.) is
    applied to BOTH branches — the empty branch needs it most, since that is where the customer
    is most likely to feel let down."""
    txn = outcome.get("recent_transactions") or []
    if not txn:
        return (
            "Mình hiểu bạn đang sốt ruột. Mình đã tra lịch sử giao dịch gần đây của "
            "bạn nhưng chưa thấy giao dịch nào trong 90 ngày qua. Bạn cho mình mã "
            "giao dịch, số điện thoại người nhận, hoặc số tiền + thời điểm cụ thể để "
            "mình tra kỹ hơn nhé."
        )
    line = []
    for t in txn[:5]:
        amount_value = f"{t['amount']:,}".replace(",", ".") + "đ" if t.get("amount") is not None else "?"
        direction = "chuyển đi" if t.get("direction") == "out" else "nhận vào"
        moment = (t.get("created_at") or "")[:16].replace("T", " ")
        line.append(f"- {t.get('trans_id', '?')}: {amount_value} ({direction}) lúc {moment}")
    items = "\n".join(line)
    return (
        "Mình hiểu bạn đang sốt ruột. Mình đã tra lịch sử giao dịch gần đây của "
        f"bạn, thấy:\n{items}\n\n"
        "Bạn cho mình biết đây có phải giao dịch bạn đang hỏi không (hoặc gửi mã "
        "giao dịch cụ thể nếu không có trong danh sách) để mình tra tiếp nhé."
    )


# The target slot is a TRANSACTION ID OR A TIME ANCHOR — UNLIKE 1B (where the amount is the
# mandatory slot). Reason: 1B applies to the FIRST turn, when nothing is known; this gate applies
# at the point where the customer has described enough for the model to decide to call a tool
# (that is why the tool ran and was blocked by OTP) — what's missing is what helps the tool NARROW
# it down to one result, exactly the role of an ID/date (the amount is most likely ALREADY in the
# sentence, since it is the detail customers tend to mention first).

# ── ⑧ · K3 — TWO ANTI-IMPERSONATION SENTENCES ─────────────────────────────────────
# The "OTP before token" ticket ⑧. Constants, 0 tokens, NOT handed to the model to phrase —
# the same rule as ADR-048 ("one DETERMINISTIC line inserted after the tool returns; don't bet
# safety on the model obeying").
#
# 🔴 K3 measured: the project enforces very strictly that the bot NEVER asks for a transaction
# OTP, but nowhere forced the bot to TELL THE CUSTOMER it will never ask. For a customer who has
# just been scammed once, when a fake CSKH agent calls a second time, the only thing protecting
# them is having HEARD this sentence from the real CSKH.
#
# ⚠️ FORM OF ADDRESS CHANGED from the ticket's verbatim text — declared so nobody thinks it was
# miscopied: the ticket wrote "chị" (older sister/ma'am) because it quoted the expert script
# directly (the customer in the script is a woman). This constant fires for EVERY customer, and
# the system DOES NOT know the customer's gender (`customer_name` is deliberately not sent to the
# LLM, PII-OK below). "bạn"/"mình" (you/I) are used — exactly the form of address every other
# constant in this module uses. Content, clause order and insertion point are kept 100% as in
# the ticket.
#
# 🔴 INSERTED AFTER `filter_output()`, DELIBERATELY — not out of convenience.
#
# [MEASURED 24/08] running `filter_output()` directly on BOTH constants: **both PASS**, no O
# group matches. In other words, today moving the insertion point before the filter would NOT
# break anything — I wrote the opposite in the draft, the measurement refuted it, and the
# measurement is kept rather than the argument.
#
# Still inserted AFTER, for a different and more durable reason:
#   ① These two sentences are OUR text, already reviewed, containing NO digits — having the
#     filter check them is spending effort checking something known to be correct.
#   ② The safety margin is THIN in a real direction: the second sentence contains "sẽ" (will —
#     already in `_O4_VERBS`) in the same clause as "lấy lại tiền" (get the money back). It
#     doesn't match ONLY because `_O4_MONEY` currently lacks the phrase "lấy lại tiền" (it has
#     "nhận lại tiền"). Adding exactly one phrase to `_O4_MONEY` — something O4 could perfectly
#     well do later — would make this safety fix delete itself, SILENTLY, with no gate going red.
# ⟹ Inserting after the filter makes ② impossible, rather than guarding against it forever.
SESSION_OTP_WARNING = (
    "Mình nói rõ để bạn yên tâm: đây là mã xác thực phiên hỗ trợ, không phải "
    "mã OTP giao dịch — mình không bao giờ hỏi mã OTP giao dịch hay mật khẩu "
    "ví của bạn."
)
# 🔴 TWO FORMS ADDED 25/08 (found by the review, ranked "do it now" by the PO). The first
# version had only THREE nets (OTP · password · money transfer). It lacked **processing/
# verification fees** and **installing a remote-control app** — the two most common scams on
# Vietnamese e-wallets.
#
# Why missing EXACTLY those two is the most dangerous: **we ourselves had just set the stage for
# them.** The bot had just told someone who SUSPECTS A SCAM that *"a specialist will contact you"*
# — the customer is now WAITING for a call and can't tell real from fake.
#   · "pay a 50k verification fee and I'll push the refund through right away"  ← the customer
#     IS WAITING for a refund, the amount is SMALL ⟹ the lowest psychological barrier
#   · "install this app so I can get into your phone to help"                  ← the customer
#     IS HOPING for help
# The three existing scams all ask the customer to do something that ALREADY SOUNDS suspicious.
# These two sound COMPLETELY REASONABLE in exactly the context we had just created.
#
# Merged into ONE sentence, not split into lines: customers don't read long warnings — and an
# unread warning fails exactly like no warning.
# The final clause ("even if they say it's to get your money back") neutralises exactly THE
# PRETEXT all five scams borrow, rather than listing a sixth scam.
WARNING_NOBODY_WILL_CALL = (
    "Một lưu ý để bạn giữ an toàn: sẽ không có ai từ ví gọi điện yêu cầu bạn "
    "chuyển tiền, nộp phí xử lý, cài ứng dụng điều khiển từ xa, hay cung cấp "
    "mật khẩu và mã OTP — kể cả khi họ nói là để lấy lại tiền cho bạn."
)

# ④ · the deterministic OTP gate's sentence. The anti-impersonation sentence ⑧ (K3) is
# pre-joined — THIS is the "turn 1" the ticket refers to: the first point where the customer is
# asked to verify. Joined directly in the constant rather than via `_add_impersonation_warning()`:
# this path does NOT go through the filter, so there is no "insert after" point, and hard-joining
# makes it obvious when reading.
_NEEDS_OTP_VERIFICATION = (
    "Dạ để tra cứu giao dịch của bạn thì mình cần bạn xác thực OTP phiên làm "
    "việc trước nhé.\n\n" + SESSION_OTP_WARNING
)

# ① (narrowed by the real PO 25/08) — the customer CONFIRMS someone was guiding them through the
# transfer. The PO verbatim: *"no need to go deep, just SAY A SPECIALIST WILL CONTACT YOU, that's
# enough."*
#
# Two things, no more:
#   ① STOP the wrong-transfer advice path — achieved by NOT calling the model this turn.
#      Forbidding it in words still lets the model say it; not running it means it can't.
#   ② say a specialist will contact them + hand over to a human.
#
# 🔴 THE K3 SENTENCE JOINED HERE IS MANDATORY, NOT DECORATION. We have just told someone who
# SUSPECTS A SCAM that "someone will contact you" — exactly the line a scammer needs for a second
# call ("I'm from the complaints department"). Saying someone will call without this sentence is
# clearing the way for the second round of the scam ourselves.
_FS13_HANDOFF = (
    "Cảm ơn bạn đã cho mình biết. Trường hợp này mình chuyển ngay cho chuyên "
    "viên hỗ trợ xử lý trực tiếp, sẽ có người liên hệ lại với bạn.\n\n"
    + WARNING_NOBODY_WILL_CALL
)

# Anchor recognising "this sentence is already in the model's reply" — avoids saying it twice.
# A SUFFICIENTLY LONG and SPECIFIC phrase is chosen (the 1B "sao"/"mất" lesson): a bare "OTP"
# would also match sentences where the model is explaining something else.
_ALREADY_WARNED_ANCHOR = (
    "không bao giờ hỏi mã otp giao dịch",
    "không có ai từ ví gọi điện",
)


def _add_impersonation_warning(reply: str, *, has_otp_error: bool, ticket_id: str | None) -> str:
    """Append the anti-impersonation sentence to the END of `reply` — a PURE function, easy to test.

    `has_otp_error`: whether any tool this turn was blocked by the OTP gate (the customer is at
    exactly the moment they are asked to verify — the ticket's "turn 1" insertion point).
    `ticket_id`: whether there is a case ID to report (the "turn 8" insertion point).

    NOT inserted if the model already said it itself — saying it twice makes the warning look
    like machine-pasted text, and customers learn to ignore it.
    """
    if not isinstance(reply, str):
        return reply
    low = reply.lower()
    extra_items: list[str] = []
    if has_otp_error and _ALREADY_WARNED_ANCHOR[0] not in low:
        extra_items.append(SESSION_OTP_WARNING)
    if ticket_id is not None and _ALREADY_WARNED_ANCHOR[1] not in low:
        extra_items.append(WARNING_NOBODY_WILL_CALL)
    if not extra_items:
        return reply
    return (reply.rstrip() + "\n\n" + "\n\n".join(extra_items)).strip()


# The MEASURED size of the tool schemas at the most recent build — replacing a hand-typed constant.
_CHARS_TOOL_SCHEMA_REAL = _CHARS_TOOL_SCHEMA

def _retry_wait_seconds(err: Exception) -> float | None:
    """Moi so giay nha cung cap BAO, khong tu doan.

    OpenAI tra nguyen van "Please try again in 1.381s" trong than loi. Doc
    dung so do de noi voi khach, thay vi bia mot con so nghe hop ly — cung
    tinh than rang buoc cung 3: con so noi ra phai co nguon.

    Khong tra duoc thi tra None, va cau tra loi noi "sau it giay" thay vi mot
    con so gia.
    """
    m = re.search(r"try again in ([0-9.]+)s", str(err))
    return float(m.group(1)) if m else None


# ═══ Classifying PROVIDER errors ═══════════════════════════════════════════
#
# `APIError` is the EXACT boundary of this family: every provider error inherits from it
# (inheritance tree checked on the running openai==3.0.0: 401/403/400/404/
# 429/5xx go through APIStatusError, timeouts/network drops through APIConnectionError, both
# under APIError), and NONE of our own errors fall into it. Catching more broadly
# (`Exception`) would swallow our own bugs as "system busy".
#
# WHY IT IS NEEDED: before this version `except` was locked to EXACTLY ONE NAME — `RateLimitError`.
# But what needs handling is not a name, it is the STATE "the provider won't serve this turn".
# 429 is only one of the ways they refuse; the other 6 classes fell straight out as a bare HTTP
# 500. The tester observed it on the real path when the Qwen quota ran out mid-session: timeout ->
# 200 + a fallback ticket, but 403 -> 500, no ticket, nothing at all.
#
# ⚠️ NEVER wire this family into the fallback-CREATE-TICKET branch below. The reason already held
# for 429 (see the comment on that branch), and is STRONGER for 401/403: an exhausted quota is a
# GLOBAL failure hitting every customer at once ⟹ creating tickets would mean one ticket per online
# customer. In the 150-user session that would be 150 ghost tickets in one minute, for complaints
# that DON'T EXIST — diluting exactly the queue where "AI gave up" tickets need to be visible.

# Four classes that NO NUMBER OF CUSTOMER RETRIES will clear — a human must handle them.
# 400/404 are OUR errors (wrong model/parameters), not provider incidents;
# grouped here because from the customer's side they look identical: waiting won't fix them.
_ERRORS_NEEDING_INTERVENTION = (
    AuthenticationError,      # 401 wrong key / just rotated / expired
    PermissionDeniedError,    # 403 quota exhausted OR insufficient permission
    BadRequestError,          # 400 our error
    NotFoundError,            # 404 our error
)

# "Out of money" markers in the message body. DELIBERATELY used for ONE log field only,
# never for anything the customer sees:
#   DashScope's `403 free quota exhausted` is the SAME PermissionDeniedError CLASS as a
#   wrong-permission 403. Separating the two requires string comparison -> fragile per provider,
#   and it breaks SILENTLY when they change their wording.
#   Rule: a FRAGILE distinction may only drive CHEAP consequences. A mistake here costs one
#   mislabelled log field (exposing itself as soon as an operator looks). If it drove "what the
#   customer sees", one wording change = customers get a 500.
_QUOTA_EXHAUSTED_HINTS = ("quota", "exhaust", "insufficient", "balance", "arrear", "unpurchased")


def _describe_provider_error(err: APIError, *, model: str = LLM_MODEL) -> dict[str, object]:
    """Fields for incident forensics. Contains NO raw message body.

    The raw body may carry keys or internal identifiers; we only extract a boolean flag from
    it. Enough for an operator to know "out of money or wrong key", not enough to leak anything
    into the log.

    `model`: the model BEING TRIED when this error happened (phase 3 — the rotation passes it
    explicitly). Defaults to `LLM_MODEL` only so old non-rotating callers don't break.
    """
    body = (str(getattr(err, "message", "") or str(err))).lower()
    # `is_blocked(err)`: OUR OWN block (spending cap/allow flag,
    # `src/egress_gate.py`) is wrapped by the SDK into `APIConnectionError` — it is NOT in
    # `_ERRORS_NEEDING_INTERVENTION` (that tuple only classifies PROVIDER errors). Without this
    # clause, a turn WE blocked ourselves would wrongly get "busy, please message again in a few
    # minutes" (wrong — the cap resets at 00:00 UTC, possibly hours away) and would NOT be pointed
    # to
    # `OTHER_SUPPORT_CHANNELS` — exactly the trap the two comments on the reply branch below
    # describe, just from a different error source. `is_blocked()` already exists to bridge exactly
    # this spot (it reads `__cause__`, not `isinstance` on `APIConnectionError` — real network
    # errors
    # are also `APIConnectionError`; merging them would recreate the very Rule H bug `is_blocked()`
    # exists to avoid).
    _self_blocked = is_blocked(err)
    return {
        "lop_loi": type(err).__name__,
        "ma_trang_thai": getattr(err, "status_code", None),
        # Phase 3 — an ASSUMPTION, not an invariant: every model in LLM_MODEL_POOL shares the SAME
        # `LLM_BASE_URL` (true for today's deepseek pool, the same DashScope account). If the pool
        # later
        # gets a model with a DIFFERENT base_url, this field will be wrong in exactly the way just
        # fixed
        # for `model` — forensics with the RIGHT model BUT the WRONG provider. Written down so
        # whoever
        # adds a different-base_url model knows to fix THIS SPOT rather than rediscovering it.
        "nha_cung_cap": LLM_BASE_URL or "openai",
        "model": model,
        "can_can_thiep": isinstance(err, _ERRORS_NEEDING_INTERVENTION) or _self_blocked,
        # Keep the SOURCE separate from the CONSEQUENCE — "needs intervention" groups provider
        # errors
        # together with self-blocking because the customer sees the same sentence, but the on-call
        # engineer
        # must be able to tell "provider quota exhausted" from "OUR OWN cap is blocking" without
        # guessing
        # from `lop_loi=APIConnectionError` (error class).
        "tu_chan": _self_blocked,
        "co_dau_hieu_het_han_muc": any(d in body for d in _QUOTA_EXHAUSTED_HINTS),
        # The provider's `request_id`: EXACTLY what their support team asks for when we dispute a
        # bill/quota — without it forensics with them is impossible (security ④). Not a secret, not
        # PII.
        # ONLY used in internal records, NEVER shown to customers.
        "request_id_ncc": getattr(err, "request_id", None),
    }


def _write_ledger(res: dict, thread_id: str | None, user_id: str) -> None:
    """Write ONE usage-ledger line for EVERY exit path of `run_agent_turn`.

    Put in one function because of a lesson just paid for: my first version attached
    `record_usage` right before the final `return` — and EVERY fallback path (429 · provider
    error · timeout · recursion) `return`s EARLY, never reaching it. The ledger was missing
    exactly the FAILED turns, i.e. it under-counted turns and read as "fewer turns than reality"
    rather than as a visible gap.

    The same shape as this morning's `flag_human_handoff` case: a correct mechanism, attached in
    exactly the place it was conceived, and nobody went looking for the second spot of the same
    class. Here the "second spot" was four other `return`s.

    `ly_do_fallback` (fallback reason) is taken FROM the returned dict itself, not rebuilt — two
    sources would drift, and drift silently.
    """
    u = res.get("usage") or {}
    # Phase 3 — the minimal spending cap (876a240). Called UNCONDITIONALLY — the function skips
    # itself when `total_tokens is None` (the "unreadable" fallback path), so placing it HERE
    # (running
    # on ALL 5 exit paths) is exactly that function's own design, not a separate phase-3 choice. It
    # does
    # NOT add embedding calls — see the spend_gate() docstring.
    spend_gate(u.get("total_tokens"))
    # Lead measured 19/08: the `token_khong_doc_duoc` (token unreadable) flag is WRITTEN to
    # usage.jsonl but nobody READS it — state written but never watched has the same effect as not
    # writing it. Counted separately (TURNS, not tokens — tokens are exactly what couldn't be read)
    # so
    # the cap's blind spot becomes a readable number.
    if u.get("token_khong_doc_duoc"):
        record_unreadable_spend()
    record_usage({
        "ts": dt.datetime.utcnow().isoformat() + "Z",
        "thread_id": thread_id or user_id,
        # Phase 3 (876a240) — the model that REALLY answered/was being tried this turn, READ FROM
        # `res` (every return path of run_agent_turn declares this field itself), NOT the global
        # constant
        # `LLM_MODEL`. After rotation, the answering model may DIFFER from the pinned model — a
        # constant
        # here would record the wrong model ON THE VERY FIRST ROTATED TURN, and this ledger is the
        # "evidence for invoice reconciliation" (PO 876a240) — a mistake here means total blindness
        # when
        # reconciliation is needed.
        "model": res.get("model"),
        "models_da_thu": res.get("models_da_thu"),
        # WHERE IT WAS MEASURED. The tester had to rule out the ttl stack indirectly because "no
        # record
        # captured the URL of the measured turn" — the same family as security's timestamp issue. A
        # number
        # that doesn't declare WHERE IT WAS MEASURED will need investigating all over again next
        # time.
        "base_url": LLM_BASE_URL or "openai",
        # WHICH OBJECT produced this number — WITH the hash method, because a 12-hex string doesn't
        # declare its own origin. On 17/08 a whole round was lost because I compared md5 with
        # someone
        # else's sha256 and concluded ".env changed 4 times". This ledger is re-read months later —
        # the
        # worst place to drop labels.
        "bam_ma_nguon": build_time_stamp(),
        "cach_bam": HASH_METHOD,
        "so_luot_goi_model": u.get("so_luot_goi_model"),
        "input_tokens": u.get("input_tokens"),
        "output_tokens": u.get("output_tokens"),
        # Review measured 19/08: this field NEVER made it into `usage.jsonl`
        # — it existed in `res["usage"]["total_tokens"]` (used for `spend_gate`) but was never
        # listed in the
        # dict passed to `record_usage`, in ANY version (not an old/new schema issue — my original
        # claim
        # was WRONG, the review corrected it). Without this line the "reconciliation evidence"
        # ledger has no
        # way to reveal a turn touched by the None-vs-0 guard (:1318).
        "total_tokens": u.get("total_tokens"),
        "token_khong_doc_duoc": u.get("token_khong_doc_duoc"),
        "cached_input_tokens": u.get("cached_input_tokens"),
        "reasoning_tokens": u.get("reasoning_tokens"),
        "input_chars": u.get("input_chars"),
        # 🔴 UNIT: counted for **THIS TURN**, NOT the whole conversation. The source is
        # `tool_calls_out`, built from `turn_messages = all_messages[prev_len:]`
        # — only the part AFTER the checkpoint slice. A conversation "looked up on turn N, recounted
        # on
        # turn N+1" gives `1` then `0`, and **both are CORRECT**.
        # [MEASURED 25/08] three sessions all read this field as a PER-CONVERSATION number and lost
        # several
        # rounds over a contradiction that didn't exist. The field isn't wrong, isn't missing, isn't
        # silent
        # — it just **DOESN'T DECLARE ITS UNIT**.
        #
        # 🔴 READ TOGETHER — why not to build an invariant between these two fields:
        # `so_tool_call` (tool-call count) and `so_luot_goi_model` (model-call count) are derived
        # from **THE
        # SAME `turn_messages`**. An invariant tying them together (e.g.
        # `so_luot_goi_model == so_tool_call + 1`) **DOES NOT check two sources** —
        # it checks two ways of deriving from ONE list. A list missing items ⟹ both drop together ⟹
        # the
        # relation **STILL HOLDS**, and the invariant stays silent exactly when it should shout. The
        # same
        # family as `if tm is None: continue` (orphaned calls, fixed in `466c59a`): the mechanism
        # isn't
        # wrong, it just DOESN'T SEE what has fallen out.
        "so_tool_call": len(res.get("tool_calls") or []),
        "ly_do_fallback": res.get("ly_do_fallback"),
        # Three SYMPTOM fields, always present (None on normal turns) — a missing key and a null key
        # are read differently by every analysis tool, and "missing key" would be read as "never
        # failed".
        "lop_loi_ncc": (res.get("trieu_chung") or {}).get("lop_loi_ncc"),
        "ma_trang_thai_ncc": (res.get("trieu_chung") or {}).get("ma_trang_thai_ncc"),
        "giay_da_troi": (res.get("trieu_chung") or {}).get("giay_da_troi"),
        "duong": res.get("duong"),
        "so_tool_schema_gui": u.get("so_tool_schema_gui"),
        # The REAL STATE of the turn, not the config flag value — without this field, R2 and R3
        # lines in
        # the ledger CAN'T be distinguished when re-read months later, and the ledger exists to be
        # re-read
        # months later.
        "suy_luan_gui": u.get("suy_luan_gui"),
        "co_ticket": bool(res.get("ticket_id")),
    })


def _fallback_reason(err: Exception) -> str:
    """Classify why the turn fell back. Returns a string, never None.

    The default branch `"khac"` (other) is DELIBERATE even though it never fires today (there is
    exactly one `except` leading to fallback). It exists for the DAY someone adds a third fallback
    path and forgets to declare it: the tester gets an odd value that is visible immediately,
    instead of a gap they would misread as "a normal turn".

    NOTE for report readers: 429 overload CURRENTLY masquerades as `"timeout"` —
    sleeping per `retry_after` eats into the AGENT_TURN_TIMEOUT_SECONDS budget, so a
    self-recovering error shows up as a timeout. Separating it needs a `"qua_tai"` (overload)
    value and catching RateLimitError at this layer — a separate job, already in the pilot
    backlog, NOT done in this commit.
    """
    if isinstance(err, FutureTimeoutError):
        return "timeout"
    if isinstance(err, GraphRecursionError):
        return "recursion_limit"
    return "khac"


def _error_symptom(err: BaseException | None) -> dict[str, object]:
    """The SYMPTOM of the error, separated from the CONCLUSION about it (Rule H).

    Why it is needed, with a real case: the ledger recorded
    `ly_do_fallback = "nha_cung_cap_can_can_thiep"` (provider needs intervention).
    That is a CONCLUSION — it says *what must be done*, not *what the provider answered*. Totally
    different incidents (`401` wrong key · `403` quota exhausted · `404` wrong model name) all
    pour into one label, and handling those three cases is COMPLETELY DIFFERENT — one needs a
    top-up, one a key fix, one a config fix.
    An on-call engineer reading the ledger can't tell them apart and will try all three.

    ⟹ The status code goes INTO THE LEDGER, next to the conclusion, not replacing it. Two
    fields, two questions: *"what did the provider say"* and *"who must do what"*.

    🔴 `None` here means **UNREADABLE** (the error carries no status code —
    timeouts, loops), NOT "code 0". The same convention as `input_tokens`.
    """
    if err is None:
        return {"lop_loi_ncc": None, "ma_trang_thai_ncc": None}
    code = getattr(err, "status_code", None)
    return {
        "lop_loi_ncc": type(err).__name__,
        # coerced to int or None — some SDKs return strings, and a string slipping into the ledger
        # would make every `>= 500` filter silently return empty instead of erroring.
        "ma_trang_thai_ncc": int(code) if isinstance(code, (int, str)) and str(code).isdigit() else None,
    }


_TICKET_CREATING_TOOLS = ("create_ticket", "request_human_handoff")


def _has_ticket_proposal(turn_messages: list) -> tuple[bool, bool]:
    """RB3 false positive, THIRD TIME (05/09, QA reproduced 2/2 times) — the customer asked
    "chưa nhận được tiền" (money not received), the turn ONLY called `lookup_transaction`, and the
    model summarised the result and then ASKED the customer before creating a case ("...được
    không ạ?" — is that OK?) — it had NOT proposed creating a ticket this turn at all.
    `claims_ticket_created()` still returned `True` because of exactly its DECLARED RISK
    DIRECTION (code/"success" checked REPLY-GLOBALLY, see that function's docstring): "Mã giao
    dịch" (a transaction ID, not a ticket code) + "đã ghi nhận" (recorded — saying the MONEY
    TRANSFER was recorded, not a case) fell exactly into the 2 pieces of the SOFT branch, though
    neither piece was about actually CREATING A CASE.

    A PURE function, separated so it can be tested WITHOUT calling the LLM (same pattern as
    `write_investigation_logs_for_ticket`,
    tests/test_agents/test_investigation_log.py — the function takes `all_messages` directly and
    doesn't run the graph itself) — it receives `turn_messages` (raw LangChain messages of the
    current turn) and returns 2 flags:
      - `called_tool`: whether this turn called ANY tool (of any kind).
      - `has_ticket_proposal`: whether, among them, there is a `create_ticket`/
        `request_human_handoff` — READING RAW `AIMessage.tool_calls`,
        INCLUDING ORPHANED calls (with no `ToolMessage` reply). The review on
        05/09 re-checked the original case of 25/08 (MT-Z01) and confirmed it ACTUALLY DID have an
        orphaned `create_ticket` in the raw tool_calls — the old comment in the
        `request_human_handoff` branch (above, in `run_agent_turn`) wrongly declared it as
        "0 tool_call" and has been corrected in place. Reading raw rather than
        `tool_calls_out` (which filters out orphans) is a MANDATORY SAFETY CONDITION —
        reading `tool_calls_out` would make case MT-Z01 no longer satisfy the condition
        "intends to create a ticket", reopening exactly the hard-constraint-#3 hole RB3 was
        created to close.
    """
    called_tool = False
    has_ticket_proposal = False
    for m in turn_messages:
        if not (isinstance(m, AIMessage) and m.tool_calls):
            continue
        for call in m.tool_calls:
            called_tool = True
            if call["name"] in _TICKET_CREATING_TOOLS:
                has_ticket_proposal = True
    return called_tool, has_ticket_proposal


def _raw_reply_for_eval(raw_reply: str, matched_group: list[str]) -> dict:
    """The sentence BEFORE FILTERING — only when the flag is on, only when something was blocked.

    Why the tester needs it: `loc_dau_ra=["O3"]` says the filter DID block, but not whether it
    blocked CORRECTLY or over-tightened. Without being able to read what was swallowed, every
    blocked case "passes" according to the grader (the safe sentence violates no invariant), and
    the "after" run looks better than the "before" run while the filter may be over-blocking en
    masse — a confound in the favourable direction, the most dangerous kind.

    Why NOT on by default: this sentence is exactly what the filter exists to keep from getting
    out. Shipping it in the production envelope would reopen the very door just closed, and it
    would flow on into logs/traces/third parties. Fail-closed: without the environment variable,
    it is NOT returned.
    """
    if os.environ.get("FIN05_EVAL_KEEP_RAW_REPLY") != "1" or not matched_group:
        return {}
    return {"reply_truoc_loc": raw_reply}


def _raise_priority_by_emotion(session: Session, *, ticket_id: str) -> None:
    """ES fires -> raise `complaints.priority`, CAPPED AT `high`. ONLY RAISES.

    NEVER up to `critical`: that level belongs to FS-06 (suspected fraud). Letting frustration
    climb to the same level as suspected fraud would ruin EXACTLY the most important queue —
    on-call staff could no longer tell "urgent because of money risk" from "urgent because the
    customer is angry", and they'd lose trust in the critical label itself.

    NEVER LOWERS: ES switching off on a later turn doesn't mean the problem got lighter. Lowering
    it would erase the trace of a time the customer was strained, which CSKH need to see when
    opening the case.
    """
    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        return
    complaint = session.get(Complaint, ticket.complaint_id)
    if complaint is None or complaint.priority in ("high", "critical"):
        return
    complaint.priority = "high"
    session.flush()


def _build_checkpointer():
    """Where the agent's conversation memory is stored — an ARCHITECTURAL decision, not just a
    technical one.

    BEFORE 2026-08-13: `MemorySaver()` kept every conversation in the RAM of ONE process.
    Consequences lasting throughout the project:
      - The backend HAD TO run exactly 1 worker (stated in the Dockerfile). A 10-vCPU machine
        could only use 1 — wasting 90% of capacity, with 150 concurrent users sharing a single
        event loop.
      - Restarting the backend = EVERY customer losing their context mid-conversation. For the
        150-user test session, one deploy/crash would ruin the whole session.

    PostgresSaver moves state out of the process (the 12-Factor "stateless processes" principle),
    opening the way to multi-worker AND letting conversations survive restarts.

    A DELIBERATE, NON-SILENT FALLBACK: tests run on SQLite (conftest creates a separate temporary
    engine per test) — PostgresSaver can't run there. Falling back to MemorySaver when the DB
    isn't Postgres is RIGHT for tests, but it must LOG clearly, not repeat the DATABASE_URL lesson
    (ADR-013): a silent fallback once quietly split the system into two databases.

    🔴 A RACE under multi-worker on an EMPTY DB [MEASURED by DevOps 20/08]: this function re-runs
    in EVERY process importing `graph` — i.e. EVERY uvicorn worker (a module-level singleton, not
    run once for the whole app). `saver.setup()` below is ONLY idempotent when sequential; N
    workers calling CREATE TABLE for the first time together (nobody sees the table existing yet)
    hit `UniqueViolation` on `pg_type` (Postgres registers a row type for every new table).
    Required: the entrypoint must "warm up" the schema ONCE, SEQUENTIALLY, BEFORE spawning any
    worker — e.g. `python -c "import src.agents.graph as g; g.close_checkpointer()"` right after
    `alembic upgrade head`. After that step, `saver.setup()` in each worker really is a no-op (the
    schema exists, no CREATE left to race over) — EXACTLY as the "idempotent" comment on the
    `saver.setup()` line below says, but only when this warm-up step comes first, not as an
    inherent property.

    See ADR-014.
    """
    if DB_KIND != "postgresql":
        _logger.warning(
            "checkpointer_in_memory",
            extra={"db_kind": DB_KIND, "ly_do": "DB không phải Postgres — hội thoại "
                   "chỉ nằm trong RAM, mất khi restart, KHÔNG chạy được multi-worker. "
                   "Bình thường với test/SQLite; nếu thấy dòng này ở production là SAI."},
        )
        return MemorySaver()

    from langgraph.checkpoint.postgres import PostgresSaver
    from psycopg_pool import ConnectionPool

    # DATABASE_URL in SQLAlchemy form (postgresql+psycopg2://) — the psycopg3 used by langgraph
    # needs the standard form (postgresql://). Converted here rather than making operators declare 2
    # variables that can easily drift.
    conninfo = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql://", 1)
    pool = ConnectionPool(
        conninfo=conninfo,
        max_size=_CHECKPOINT_POOL_MAX,
        # autocommit is MANDATORY: PostgresSaver manages its own transactions; letting psycopg open
        # implicit transactions holds locks and hangs when several workers write.
        kwargs={"autocommit": True, "prepare_threshold": 0},
        open=True,
    )
    saver = PostgresSaver(pool)
    saver.setup()  # idempotent ONLY when the entrypoint has warmed up the schema first — see this function's docstring
    global _CHECKPOINT_POOL
    _CHECKPOINT_POOL = pool  # keep a reference so it can be closed cleanly at shutdown
    _logger.info("checkpointer_postgres", extra={"pool_max": _CHECKPOINT_POOL_MAX})
    return saver


def close_checkpointer() -> None:
    """Close the checkpointer's pool — called from FastAPI shutdown (src/api/main.py).

    psycopg's ConnectionPool runs background threads; without an explicit close the interpreter
    raises `PythonFinalizationError: cannot join thread at interpreter shutdown` on exit (really
    encountered while verifying). For a long-running server this error only dirties the shutdown
    log, but graceful shutdown is a mandatory item of the production packaging checklist — and an
    unclosed pool keeps Postgres connections until the TCP timeout, eating into max_connections
    during continuous deploys.
    """
    global _CHECKPOINT_POOL
    if _CHECKPOINT_POOL is not None:
        try:
            _CHECKPOINT_POOL.close()
            _logger.info("checkpointer_pool_closed")
        except Exception as e:  # noqa: BLE001 — shutdown must not raise errors outward
            _logger.warning("checkpointer_pool_close_failed", extra={"loi": repr(e)})
        finally:
            _CHECKPOINT_POOL = None


# A separate pool for the checkpointer, SEPARATE from SQLAlchemy's pool: the two have
# different access rhythms (checkpoints write on every ReAct step, the ORM reads/writes business
# data) and sharing would make them congest each other. Total connections = workers x (ORM pool +
# this pool) must stay below Postgres's max_connections (default 100).
_CHECKPOINT_POOL_MAX = int(os.environ.get("CHECKPOINT_POOL_MAX", "5"))
_CHECKPOINT_POOL = None  # assigned in _build_checkpointer(), closed in close_checkpointer()

# Module-level singleton: the agent is rebuilt per request (session/tools bound to that
# request), but the checkpointer is one shared instance so conversation history continues across
# requests with the same thread_id.
_CHECKPOINTER = _build_checkpointer()


def read_handoff_transcript(thread_id: str) -> dict[str, object] | None:
    """ADR-044 — reads the bot↔customer conversation of ONE thread for the route
    `GET /tickets/{ticket_id}/transcript` (src/api/main.py). Read via
    `checkpointer.get_tuple()` — NEVER parsing the `checkpoint_*` tables directly
    (a LangGraph implementation detail that changes between versions, ADR-044
    item 5).

    Returns `None` when the thread_id has NO checkpoint — the route above interprets that as
    "couldn't look it up" with a reason; this function does NOT invent a reason itself
    (clear separation of responsibility: this function only reads, the route decides the
    message).

    PII: checkpoints store the SCRUBBED version (`HumanMessage` built from `scrub_pii(...,
    purpose="model_input")` at :790) — this function does NOT scrub again, per ADR-044 item
    "PII — SOLVED by measurement". WRONG masking labels (e.g. `[PERSON_VN]` replacing words the
    customer really typed, before fix D') remain intact in OLD checkpoints — the route/UI must
    declare this itself; this function doesn't retroactively edit evidence.

    Returns `{"luot": [...], "chi_so_bang_giao": int | None}` (turns, handoff index).
      - `luot`: each turn is `vai` (role: "khach"/"bot" — customer/bot) + `noi_dung` (content) +
        `co_goi_tool` (whether the bot called a tool right before generating this reply or it is
        just plain talk — CSKH need to tell which replies are based on real data).
      - `chi_so_bang_giao`: the (0-based) index of the LAST turn "above the line" — i.e. the bot
        turn confirming RIGHT AFTER the `request_human_handoff` tool ran. The UI draws the divider
        right after this turn. `None` if the conversation has NO `request_human_handoff` call
        (the transcript is readable but there was never a handoff — e.g. CSKH opened the ticket
        themselves, not at the customer's request). `handoff_at` (the DB timestamp) is NOT used
        to infer this position — there is no per-message timestamp to match against; using the
        very EVENT that produced the handoff (the tool call) is more precise than an indirect
        timestamp comparison.

        TWO special cases both give `chi_so_bang_giao=None` even though `handoff_at` (DB) has a
        value — the route/UI handle them THE SAME WAY (showing a note instead of a divider), but
        the CAUSES differ; don't merge them when reading/re-explaining:

        (a) DECLARED 19/08 (found by the PO-agent, not a bug): the ticket came from the
            timeout/abandoned-turn branch — `flag_human_handoff(...)` called DIRECTLY,
            NOT via the `request_human_handoff` tool the LLM calls. The transcript has NO
            `ToolMessage` of that name anywhere — self-consistent, not a single trace of the
            handoff in the conversation.

        (b) DECLARED 20/08 (found by the review while checking the whole chain): the
            `request_human_handoff` tool WAS REALLY called by the LLM (the `ToolMessage` is
            present in the checkpoint), but it is the LAST message — the turn was cut off
            (timeout/error) right after the tool finished, BEFORE the model could generate a
            confirming `AIMessage` with content. The loop below ends with the flag
            `just_called_handoff=True` still pending, never assigned to `chi_so_bang_giao`
            because there is no bot turn after it to receive it.
            DIFFERENT from case (a) in that there IS REAL EVIDENCE the tool ran, but that
            evidence can never be attached to a displayed turn (`co_goi_tool` only attaches to
            the next AIMessage — there is none here) — CSKH see no badge for exactly this call,
            even when EARLIER turns in the same conversation have badges for other tools. Not
            "fixed" by guessing the divider position — that would replace an honest gap with a
            guess."""
    tuple_ = _CHECKPOINTER.get_tuple({"configurable": {"thread_id": thread_id}})
    if tuple_ is None:
        return None
    messages = (tuple_.checkpoint.get("channel_values") or {}).get("messages") or []

    turn: list[dict[str, object]] = []
    has_tool_from_prev_turn = False
    just_called_handoff = False
    handoff_index: int | None = None
    for m in messages:
        if isinstance(m, ToolMessage):
            has_tool_from_prev_turn = True
            if m.name == "request_human_handoff":
                just_called_handoff = True
            continue
        if isinstance(m, HumanMessage):
            turn.append({"vai": "khach", "noi_dung": str(m.content), "co_goi_tool": False})
            has_tool_from_prev_turn = False
        elif isinstance(m, AIMessage):
            content_text = str(m.content or "")
            if not content_text.strip():
                # An AIMessage with empty content (carrying only tool_calls, no speech yet) — not a
                # conversation TURN, skipped. The flag has_tool_from_prev_turn was already set to
                # True in the
                # ToolMessage branch above when that tool finished executing.
                continue
            turn.append({"vai": "bot", "noi_dung": content_text, "co_goi_tool": has_tool_from_prev_turn})
            has_tool_from_prev_turn = False
            if just_called_handoff:
                handoff_index = len(turn) - 1
                just_called_handoff = False
    return {"luot": turn, "chi_so_bang_giao": handoff_index}

# Sentinel — distinguishes "otp_verified_at not passed" (backward compat: treated as JUST
# verified, used by the eval harness/existing tests that assume "the customer verified OTP before
# entering the chat") from "None really passed" (the real current_user has NEVER verified —
# /agent/chat always passes it explicitly, see src/api/main.py).
# "now" is computed at CALL time (not at module load) to avoid time drift if the test suite runs
# for a long time.
_ALWAYS_FRESH = object()


# ---------------------------------------------------------------- O3 source
# Tool ERROR branches are excluded from the source (Security's condition Đ1,
# docs/security/2026-08-18-dinh-hang-ban-va-A-o3-toolmessage-lich-su.md §3):
# the error branch echoes verbatim the PARAMETERS THE MODEL SET ITSELF (e.g.
# `create_ticket.py:42 "complaint_type không hợp lệ: {complaint_type}"` — invalid complaint_type),
# so a code/number the agent FABRICATED on turn N-1, rejected by the tool and echoed into the
# ToolMessage — if that branch got into the source, then turn N repeating that same fabricated
# code would be treated by O3 as "traced to a tool", granting a permanent pass to a FAKE number.
#
# It USED TO BE an allow-list `status in {found, not_found, multiple_matches}` —
# WITHDRAWN, because the premise was wrong: Lead [MEASURED] 3/5 tools (get_customer_history ·
# create_ticket · request_human_handoff) have NO TOP-LEVEL `status` key on the SUCCESS path
# (status is nested inside each element, or doesn't exist). The allow-list taken literally would
# strip the success payloads of ALL THREE tools from the source —
# and `get_customer_history` is exactly the tool behind the verification query "show my recent
# transactions", so the fix would NOT cure the very case it was built to cure.
# `contracts/agent-tools.yaml:65,94,106` also declares `output.status` for ALL THREE of those tools
# (`get_customer_history`/`create_ticket`/`request_human_handoff`) which the runtime DOESN'T emit —
# the old allow-list trusted the project's source of truth exactly, and that source DRIFTED from
# the runtime. Nobody conjured the wrong premise out of thin air: this is the ADR-027 class of
# blindness — the `test_invariants` checker compares DECLARATIONS with DECLARATIONS (contract ↔
# CHECK constraint/route) and has never compared the contract with the REAL PAYLOAD at runtime.
#
# The deny-list `status == "error"` — this predicate is ANCHORED IN OBSERVABLE BEHAVIOUR,
# NOT IN THE CONTRACT (the lesson just paid for above).
#
# [MEASURED] 19/08, `grep -rn '"status": "error"' src/agents/tools/customer_tools.py`
# → 9 error-return points (`:597 :601 :637 :819 :840 :873 :919 :947 :997`), 0 success payloads
# carrying this key. `:637` is the REUSED constant `_STOP_LOOP_INSTRUCTION`, returned at `:777`
# (the livelock stop instruction) — not an inline `return {...}`, so it slipped past THREE earlier
# independent scans (Review, Lead, me) that all counted 8: all three scanned for the shape
# `return {...}`, not the shape of a constant.
#
# That number is a SNAPSHOT and WILL DRIFT again when a 6th tool or a new error branch appears
# (Rule N: a COUNTED number must come with its counting method; Rule P: a stale number must be
# sealed, not a permanent anchor). What keeps this property true GOING FORWARD is QA/QC case ⑩
# (guarding that every real error-return path carries `status:"error"`) — NOT this comment.
_TOOL_ERROR_STATUS = "error"

# Tools whose HISTORICAL results are gathered into the source. Declared EXPLICITLY in exactly
# one place so that narrowing the scope later is a one-line edit, not a re-read of the loop:
# Security weighed the axis "does the payload echo parameters the model set itself" and showed the
# error branch is a laundering channel for fabricated numbers (closed by the allow-list above),
# but if that axis is re-weighed for WRITE tools, the line below is where to change it.
HISTORY_TOOLS = frozenset({
    "lookup_transaction",
    "get_customer_history",
    "create_ticket",
    "request_human_handoff",
    "search_policy",
})


def assemble_o3_source(all_messages: list, tool_calls_out: list[dict]) -> str:
    """Assembles the SOURCE channel (JSON) for O3's provenance rule.

    TWO parts, and the boundary between them is deliberate:

    · `tool_calls_out` — tool results of THIS TURN, keeping the old shape
      (including `args`).
    · tool results of EARLIER TURNS in the same conversation — ONLY the `result` part,
      **not** `args`. Hard constraint 3 requires every number the agent states to trace back to a
      REAL tool result; `args` are parameters THE MODEL SET ITSELF, not something the system
      returned. Gathering them would let the model grant itself evidence across turns — exactly
      the laundering door Đ1 closed, just through a different field.

    `AIMessage`s are NOT gathered: the agent's words are not a valid source; gathering them would
    make O3 certify its own output.

    Why the history part is needed (fix A): the old source channel only loaded the current
    turn's payload, so a turn where the agent answered from memory (without calling the tool
    again) made every code/number looked up on earlier turns "untraceable" -> O3 blocked WRONGLY.
    Hard constraint 3 says "a real tool result", NOT "from this turn".
    """
    history: list[dict] = []
    for m in all_messages:
        if not isinstance(m, ToolMessage):
            continue
        if getattr(m, "name", None) not in HISTORY_TOOLS:
            continue
        try:
            payload = json.loads(m.content)
        except (json.JSONDecodeError, TypeError, ValueError):
            continue  # unparseable -> NOT a source (fail-closed)
        if not isinstance(payload, dict):
            continue
        if payload.get("status") == _TOOL_ERROR_STATUS:
            continue
        history.append(payload)
    return json.dumps(
        {"luot_nay": tool_calls_out, "luot_truoc": history},
        ensure_ascii=False,
        default=str,
    )


def _build_agent(
    session: Session,
    *,
    user_id: str,
    customer_name: str,
    otp_verified_at: float | None,
    guard: TurnGuard | None = None,
    # ADR-044 — the EFFECTIVE thread_id of this turn (with `or user_id` already applied by the
    # caller, see run_agent_turn), threaded down to build_customer_tools so the create_ticket tool
    # writes it into Complaint.thread_id at CREATION. None = old callers (tests/eval) don't pass it
    # —
    # Complaint.thread_id is NULL, exactly the "PERMANENTLY NULLABLE" design of migration
    # a8b9c0d1e2f3, not an error.
    thread_id: str | None = None,
    # Phase 3 (876a240) — the MODEL name for this turn, NOT a global constant.
    # The default `LLM_MODEL` keeps the old behaviour UNCHANGED for every caller that doesn't pass
    # it
    # (existing tests/eval). The rotation lives INLINE in `run_agent_turn` (not a separate function
    # `_chay_luot_voi_xoay` — that name was once announced to QA/QC in a message on 19/08 and then
    # NOT
    # implemented that way; the correction was reported to Lead/QA/QC the same day), passing each
    # element of `LLM_MODEL_POOL` explicitly — this is the SPY POINT QA/QC use to simulate quota
    # errors
    # without spending real tokens (patching by the `model` value received to tell which call it
    # is).
    model: str = LLM_MODEL,
):
    chat_model = ChatOpenAI(
        # LLM_* fallback ve OPENAI_* (src/config.py) -> khong dat gi thi hanh vi
        # y het truoc. `base_url=None` la mac dinh cua SDK, khong phai mot gia
        # tri dac biet can xu ly rieng.
        #
        # `http_client` DUNG CHUNG voi duong embedding (src/rag/store.py) —
        # xem src/egress_gate.py. Day la noi DUY NHAT moi loi goi ra nha cung
        # cap di qua, nen no la cho duy nhat co cho chot chan + bo dem. Dat o
        # tang nay con thay ca luot SDK TU RETRY (max_retries duoi day): dem o
        # tang tren SDK ghi 1 cho 3 lan ban ra day.
        http_client=shared_http_client(),
        model=model,
        temperature=0.2,
        api_key=LLM_API_KEY,
        # Phase 3: every model in LLM_MODEL_POOL shares the SAME base_url/api_key —
        # the same DashScope account, not changing the data-leaves-our-infrastructure boundary
        # (confirmed by
        # Security for the deepseek pool). Switching providers BETWEEN models within ONE pool is
        # outside the
        # scope of phase 3.
        base_url=LLM_BASE_URL,
        # Only passed when SET — `max_tokens=None` and "not passed" differ in some clients. See
        # LLM_MAX_TOKENS in config.py.
        **({"max_tokens": LLM_MAX_TOKENS} if LLM_MAX_TOKENS else {}),
        timeout=OPENAI_TIMEOUT_SECONDS,
        max_retries=OPENAI_MAX_RETRIES,
        # T3 · only PASSED when OFF. Passing nothing when on = exactly the old behaviour, not
        # "passing enable_thinking=True" (the two differ at some providers, and we have no reason to
        # experiment).
        **({} if REASONING_ENABLED else {"extra_body": {"enable_thinking": False}}),
    )
    # Read BACK from the object just built, NOT from the config variable again: if the parameter
    # name were wrong, `extra_body` wouldn't stick to the model while the config variable would
    # still
    # say "off". Observe the artefact, don't trust the declaration — the same principle as the
    # `duong`
    # (route) marker and `so_tool_schema_gui` (tool schemas sent).
    global _REASONING_SENT
    _REASONING_SENT = not bool((getattr(chat_model, "extra_body", None) or {}).get("enable_thinking") is False)
    tools = build_customer_tools(
        session, user_id=user_id, otp_verified_at=otp_verified_at, guard=guard, thread_id=thread_id
    )
    # The number of tool schemas REALLY bound to the call. Taken from the list just built, NOT
    # typed by hand — `_CHARS_TOOL_SCHEMA = 6773` above is a constant someone has to remember to
    # update,
    # and we're not adding a second one of that kind.
    #
    # This field comes from a DIFFERENT mechanism than the triage decision, so the two can't lie at
    # the
    # same time: a `duong` marker stuck at "day_du" (full) while this number = 0 is a self-exposing
    # contradiction, and vice versa.
    global _TOOLS_SENT_COUNT, _CHARS_TOOL_SCHEMA_REAL
    _TOOLS_SENT_COUNT = len(tools)
    # Schema size MEASURED FROM THE SCHEMA ITSELF, not typed by hand. `_CHARS_TOOL_SCHEMA
    # = 6773` above comes with the comment "update when adding/removing tools" — a number SOMEONE
    # MUST
    # REMEMBER to update, i.e. it will break silently on the day a sixth tool arrives.
    # Real payload measured 17/08: 6,773 characters — the constant is RIGHT today, and right thanks
    # to
    # a person, not a mechanism.
    try:
        from langchain_core.utils.function_calling import convert_to_openai_tool
        _CHARS_TOOL_SCHEMA_REAL = len(json.dumps(
            [convert_to_openai_tool(t) for t in tools], ensure_ascii=False))
    except Exception:  # noqa: BLE001 — a broken measurement must not kill the chat turn
        _CHARS_TOOL_SCHEMA_REAL = _CHARS_TOOL_SCHEMA
    # customer_name is NOT passed — the customer's real name must not leave the system for the LLM
    # (ADR-010). The parameter is kept in the signature so old callers don't break.
    system_prompt = build_system_prompt(current_time=dt.datetime.utcnow())
    return create_agent(chat_model, tools, system_prompt=system_prompt, checkpointer=_CHECKPOINTER)


def run_agent_turn(
    session: Session,
    *,
    user_id: str,
    message: str,
    thread_id: str | None = None,
    otp_verified_at: float | None = _ALWAYS_FRESH,
    vua_xac_thuc_de_gui_lai: bool = False,
) -> dict[str, Any]:
    """`otp_verified_at`: the timestamp (epoch seconds) of the most recent OTP+security-question
    verification (src/auth.py) — passed for REAL from current_user.otp_verified_at in
    /agent/chat (src/api/main.py); may be None if the customer has NEVER verified.
    Not passing this parameter (default `_ALWAYS_FRESH`) means treating it as JUST verified —
    so as NOT to break the existing eval/golden_set.jsonl + adversarial_set: those cases assume
    "the customer verified OTP before entering the chat" (exactly the opening sentence of the
    system prompt) and aren't testing the OTP flow —
    the real OTP flow is tested separately in tests/test_api/test_otp.py +
    frontend/e2e/auth.spec.ts.

    `vua_xac_thuc_de_gui_lai` (just verified, re-sending): an EXPLICIT flag from the frontend (NOT
    inferred from timestamps) signalling that this turn is ChatClient.tsx::submitOtp()
    AUTOMATICALLY RE-SENDING a message previously blocked by OTP (`pendingStarterRef`) — see the
    post-OTP slot-collection gate just below. The `False` default keeps the old behaviour intact
    for every other caller (eval/golden_set, tests, every normal chat turn)."""
    if otp_verified_at is _ALWAYS_FRESH:
        otp_verified_at = dt.datetime.utcnow().timestamp()

    user = session.get(User, user_id)
    if user is None:
        raise ToolError(f"user_id không tồn tại: {user_id}")

    # Reset at the start of EVERY turn: these two variables are module-level globals (written in
    # `_build_agent`). Without resetting, an early `return` happening BEFORE the agent is built
    # would
    # report the PREVIOUS TURN's values — a plausible and wrong number.
    # `None` here is DELIBERATE: it says "agent not built yet", completely different from `0`
    # meaning
    # "built, no tools sent".
    global _TOOLS_SENT_COUNT, _CHARS_TOOL_SCHEMA_REAL
    _TOOLS_SENT_COUNT = None
    _CHARS_TOOL_SCHEMA_REAL = None

    # ── ⑭ · A CLIENT FLAG MUST HAVE SERVER-SIDE EVIDENCE ────────────────────────────
    # 🔴 A MEASURED HOLE (found by the review, reproduced by the PO via direct API calls,
    # re-confirmed
    # by the Coder by reading the code): `vua_xac_thuc_de_gui_lai` is a flag DECLARED BY THE CLIENT,
    # and ALL THREE deterministic gates used it as "True ⟹ SKIP".
    #     :928  T0   True ⟹ enters T0, and a sentence with any digit falls straight through to the
    # model
    #     :986  ④    `and not vua_xac_thuc_de_gui_lai`  ⟹ skipped
    #     :1035 T1   `if not vua_xac_thuc_de_gui_lai`   ⟹ skipped
    # ⟹ ONE flag switched off ALL THREE. Any client (curl/Postman) with a valid JWT but NO OTP,
    # setting
    # the flag=true on every request, went straight into a full model turn.
    #
    # ✅ NO data leaks — the tool layer reads `otp_verified_at` from the JWT, not this flag. Hard
    #    constraint 4 is NOT breached.
    # 🔴 BUT this is exactly the 49,700–71,600-token scenario ④ was created to eliminate. And it is
    #    NOT just cost: the system's real ceiling is TPM (STATE §6.⓵), and TPM is a SHARED quota —
    # one
    #    abusive client eats into EVERY other customer's share. That is AVAILABILITY, not the bill.
    #
    # The fix: the flag only takes effect when the server ITSELF KNOWS this thread was once blocked.
    # Reusing `thread_signals` (no second mechanism built).
    #
    # 🔴 THE SAFE DIRECTION: `read_signal` is `read_or_unknown` — a Redis error returns None. `None`
    # and
    # `0` BOTH count as NO evidence ⟹ the flag is ignored ⟹ the deterministic gates run normally. It
    # errs on the CHEAP side, not the expensive one. A Redis failure makes the customer get asked
    # one
    # more turn (annoying), it does NOT open the gate for anyone.
    #
    # Why the per-thread key SURVIVES verification: `/auth/otp/verify` re-issues the token KEEPING
    # the
    # original `iat` (src/auth.py::create_access_token) precisely so that `thread_id = user_id:iat`
    # doesn't change mid-conversation.
    _evidence_tid = thread_id or user_id
    _has_block_evidence = read_signal(_SIGNAL_OTP_BLOCKED, _evidence_tid) not in (None, 0)
    if vua_xac_thuc_de_gui_lai and not _has_block_evidence:
        _logger.info(
            "agent_turn_co_resend_khong_co_bang_chung",
            extra={"user_id": user_id, "thread_id": _evidence_tid},
        )
    vua_xac_thuc_de_gui_lai = vua_xac_thuc_de_gui_lai and _has_block_evidence

    # ── ⑨ + PIECE 4 · COLLECTING THE SCREENING ANSWER ───────────────────────────────
    # The PREVIOUS turn asked the screening question (thread signal). This turn is the answer.
    #
    # This is the piece NOBODY COSTED in the original ticket: before this version
    # `engine.evaluate()` was called EXACTLY ONCE, with `description_raw` at ticket creation. Even
    # if
    # FS-13 existed, it could only catch customers self-reporting it in their very first description
    # —
    # and a customer calling what happened a "wrong transfer" would never reach it. The signal only
    # fired when we no longer needed it.
    #
    # TWO sources, merged:
    #   ① `is_affirmative_reply` — the customer says YES. That IS the FS-13 semantics,
    #      inferred from the QUESTION-ANSWER CONTEXT, with no keyword needed in the answer.
    #   ② `engine.evaluate()` on that same sentence — catching richer answers
    #      ("có, người ta gọi điện bảo em chuyển" — yes, someone called and told me to transfer) and
    #      FS-09 too.
    #
    # The signal is DELETED after processing: one question, one collection. Without deleting it
    # every
    # later turn would re-run a DB query with an unchanged result.
    # Does NOT block the turn: this is RECORDING, not a gate. If it fails, the turn still runs.
    _slot_tid_try = thread_id or user_id
    if read_signal(_SIGNAL_SCREENING_ASKED, _slot_tid_try) not in (None, 0):
        try:
            _merge = merge_fraud_signals(
                session,
                thread_id=_slot_tid_try,
                utterance_text=message,
                add_code=["FS-13"] if is_affirmative_reply(message) else None,
            )
            # 🔴 DELETED AFTER A SUCCESSFUL MERGE, not before (caught by the review, fixed by the
            # PO).
            # The first version deleted it BEFORE the `try` — if the merge raised, the turn still
            # ran (right)
            # but the statement "someone guided me through the transfer" was LOST FOREVER, with no
            # turn ever
            # retrying. Exactly the asymmetry rule written in the affirmation detector, in a
            # different domain:
            #   delete AFTER  ⟹ a failed merge means asking the customer once more.   Annoying.
            #   delete BEFORE ⟹ a failed merge LOSES a scam-victim statement.         Real damage.
            #
            # NO endless asking loop: the ASK gate requires signal == 0, and the signal only returns
            # to 0 once
            # the merge is DONE. Signal still 1 ⟹ no re-asking, just retrying the merge each turn.
            # Retries are
            # bounded by the number of turns the customer keeps chatting, not a loop within one
            # turn.
            clear_signal(_SIGNAL_SCREENING_ASKED, _slot_tid_try)
            # GATE item 4 — marks EXACTLY the transaction whose question-answer round just completed
            # as
            # "screened", keyed per trans_id (not per thread) — read back in `create_ticket`
            # (customer_tools.py) before allowing a ticket.
            # Marked UNCONDITIONALLY here (whether the customer answers "yes" or "no", screening IS
            # DONE for
            # this transaction — the content of the answer only affects `_merge`/FS-13, not whether
            # it has
            # been asked and answered).
            # No trans_id could be stored (Redis failed exactly when ⑨ wrote it, or the rare case
            # where ⑨
            # hadn't written yet) → NOTHING is marked — fail-closed, exactly as the PO decided: the
            # gate in
            # create_ticket treats it as NOT screened and blocks until there is real evidence.
            _just_asked_trans_id = read_value(_SIGNAL_TRANS_ID_PENDING_SCREENING, _slot_tid_try)
            if _just_asked_trans_id:
                incr_signal(_SIGNAL_SCREENING_DONE, _just_asked_trans_id)
            _logger.info(
                "agent_turn_thu_sang_loc_lua_dao",
                extra={"user_id": user_id, "thread_id": _slot_tid_try,
                       "tin_hieu_sau_gop": _merge, "trans_id_sang_loc": _just_asked_trans_id},
            )
            # ① — FS-13 fires ⟹ STOP THE TURN, don't call the model. Handoff happens at the SERVICE
            # LAYER
            # (`flag_human_handoff`), NOT through an AI tool — per hard constraint 2: escalation is
            # never
            # triggered by the AI itself.
            if _merge is not None and "FS-13" in _merge:
                _account = None
                try:
                    _account = flag_human_handoff(
                        session, user_id=user_id,
                        reason="Khách xác nhận có người hướng dẫn chuyển khoản "
                               "(FS-13) — cần chuyên viên liên hệ trực tiếp.",
                        thread_id=_slot_tid_try,
                    ).get("ticket_id")
                except Exception:  # noqa: BLE001
                    _logger.exception(
                        "agent_turn_fs13_ban_giao_loi",
                        extra={"user_id": user_id, "thread_id": _slot_tid_try},
                    )
                _res_fs13 = {
                    "reply": _FS13_HANDOFF,
                    "tool_calls": [], "ticket_id": _account, "should_escalate": False,
                    "model": None, "models_da_thu": [],
                    "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0,
                              "cached_input_tokens": 0, "reasoning_tokens": 0,
                              "input_chars": 0, "so_luot_goi_model": 0,
                              "so_tool_schema_gui": 0, "chars_tool_schema_moi_luot": 0,
                              "suy_luan_gui": None},
                    "loc_dau_ra": [],
                    "tin_hieu_lo_chi_thi": {"nguyen_tac": 0, "quy_trinh": 0},
                    "goi_y_handoff": True,
                    "ly_do_fallback": None,
                    "duong": FS13_HANDOFF_ROUTE,
                }
                _write_ledger(_res_fs13, thread_id, user_id)
                return _res_fs13
        except Exception:  # noqa: BLE001 — recording MUST NOT break the chat turn
            _logger.exception(
                "agent_turn_thu_sang_loc_loi",
                extra={"user_id": user_id, "thread_id": _slot_tid_try},
            )

    # ── T0 · SLOT-COLLECTION GATE AFTER OTP VERIFICATION ───────────────────────────────
    # Runs BEFORE triage() (1B), independently of `TRIAGE_ENABLED` — the decision here, "what to
    # call
    # the model with", is entirely different from 1B's decision "which toolkit does this turn need".
    # When this flag is on, this turn does NOT go through 1B's nhe/thu_slot/day_du (light/slot/full)
    # — a post-OTP resend is always a real complaint (that is why the tool was blocked by OTP),
    # never
    # valid for ROUTE_LIGHT or for 1B asking for the amount again under a different slot.
    # 🔴 Đ4 ("OTP before token" ticket ⑦) — this gate now has its OWN SWITCH
    # `T0_GATE_ENABLED` (ON by default, see src/config.py). Before the fix, switching off
    # `TRIAGE_ENABLED` to fight a fire still left T0 running, with NO signal saying so.
    # How to recognise it in the ledger: `duong=otp_resend_thu_slot` ⟹ T0 handled this turn.
    if T0_GATE_ENABLED and vua_xac_thuc_de_gui_lai:
        _effective_tid_otp = thread_id or user_id
        if read_signal(_SIGNAL_OTP_RESEND_ASKED, _effective_tid_otp) == 0 and not enough_to_narrow(message):
            incr_signal(_SIGNAL_OTP_RESEND_ASKED, _effective_tid_otp)
            _logger.info(
                "agent_turn_otp_resend_thu_slot",
                extra={"user_id": user_id, "thread_id": _effective_tid_otp},
            )
            _res_otp_resend = {
                "reply": ASK_TIME_AND_AMOUNT,
                "tool_calls": [],
                "ticket_id": None,
                "should_escalate": False,
                # Same principle as ROUTE_LIGHT/ROUTE_SLOT_FILL — no model is called, so None/0 is
                # the TRUTH,
                # not "unreadable".
                "model": None,
                "models_da_thu": [],
                "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0,
                          "cached_input_tokens": 0, "reasoning_tokens": 0,
                          "input_chars": 0, "so_luot_goi_model": 0,
                          "so_tool_schema_gui": 0,
                          "chars_tool_schema_moi_luot": 0,
                          "suy_luan_gui": None},
                "loc_dau_ra": [],
                "tin_hieu_lo_chi_thi": {"nguyen_tac": 0, "quy_trinh": 0},
                "goi_y_handoff": False,
                "ly_do_fallback": None,
                "duong": ROUTE_OTP_RESEND_SLOT_FILL,
            }
            _write_ledger(_res_otp_resend, thread_id, user_id)
            return _res_otp_resend
        # Eligible (has an ID/time) OR already asked on an earlier resend turn in this conversation
        # (the
        # customer verified OTP several times) — the signal is NOT incremented (only in the asking
        # branch
        # above), and the turn falls straight through to the full model flow below with the VERBATIM
        # `message`, skipping 1B.

    # ── ④ · DETERMINISTIC OTP GATE FOR GROUP B ────────────────────────────────────
    # The invariant of this round: NO turn spends tokens before OTP verification is complete.
    # A personal-complaint turn whose OTP isn't fresh WILL CERTAINLY be blocked by the tool layer —
    # calling the model for it means paying to rediscover a fact this layer already knows.
    # [MEASURED, self-declared in customer_tools.py:620-629] such a turn costs 8 tool calls · 46
    # seconds · 49,700–71,600 tokens, and the ledger records `total_tokens = 0`.
    #
    # Q1 (decided by the PO): applies ONLY to GROUP B. Policy questions are NOT blocked —
    # `search_policy` is already exempt from OTP.
    #
    # 🔴 NOT A SECURITY LAYER — see the comment on `OTP_GATE_GROUP_B_ENABLED` in
    # src/config.py. Uses the VIEW threshold (12h), DELIBERATELY as loose as the tool layer, not
    # stricter. Removing the lock in the tool because "this gate exists" would open hard constraint
    # 4.
    #
    # Placed AFTER T0 (post-OTP resend turns are already verified and don't land here) and BEFORE T1
    # — any later and the thing we meant to save would already be spent.
    #
    # 🔴 AM-01 still has `nhom_b=True` for now ⟹ one class of policy questions gets blocked. This is
    # an ALREADY-TRACKED hole of GROUP B flowing downstream, NOT a regression caused by ④; it closes
    # itself when ③ round 2 (the sentence-mood axis) lands. Lead approved landing first, 25/08.
    if (
        OTP_GATE_GROUP_B_ENABLED
        and not vua_xac_thuc_de_gui_lai
        # REUSES the tool layer's `_otp_fresh` — NO second definition of "fresh" is written. Two
        # definitions of the same thing will drift, and drift silently (the same reason
        # `hash_source` vs
        # `BUILD_COMMIT` exist).
        # This gate blocks ⟹ the tool would block too: one source, impossible to drift.
        and not _otp_fresh(otp_verified_at, OTP_VIEW_MAX_MINUTES)
        and is_personal_complaint(message)
    ):
        _logger.info(
            "agent_turn_can_otp",
            extra={"user_id": user_id, "thread_id": thread_id or user_id,
                   "bam_luat": RULES_HASH},
        )
        _res_needs_otp = {
            "reply": _NEEDS_OTP_VERIFICATION,
            # 🔴 THE CONTRACT WITH THE CLIENT (Lead approved 25/08): the client opens the OTP dialog
            # on
            # `duong === "can_otp"` (route: needs OTP), NOT on the Vietnamese wording of `reply`.
            # Before ④,
            # both OTP-triggering paths in ChatClient.tsx read `tool_calls`/`ticket_id` — and every
            # 0-token
            # path returns those empty, so adding this gate without adding the key would lead
            # customers into a
            # dead end.
            "tool_calls": [],
            "ticket_id": None,
            "should_escalate": False,
            "model": None,
            "models_da_thu": [],
            "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0,
                      "cached_input_tokens": 0, "reasoning_tokens": 0,
                      "input_chars": 0, "so_luot_goi_model": 0,
                      "so_tool_schema_gui": 0,
                      "chars_tool_schema_moi_luot": 0,
                      "suy_luan_gui": None},
            "loc_dau_ra": [],
            "tin_hieu_lo_chi_thi": {"nguyen_tac": 0, "quy_trinh": 0},
            "goi_y_handoff": False,
            "ly_do_fallback": None,
            "duong": ROUTE_NEEDS_OTP,
        }
        # ⑭ — record the EVIDENCE: this thread was really blocked by the OTP gate just now. Only on
        # the
        # next turn may the client set `vua_xac_thuc_de_gui_lai`.
        incr_signal(_SIGNAL_OTP_BLOCKED, thread_id or user_id)
        _write_ledger(_res_needs_otp, thread_id, user_id)
        return _res_needs_otp

    # ── T1 · TRIAGE ─────────────────────────────────────────────────────────────────
    # Behind a flag, OFF BY DEFAULT. When off, this function behaves exactly as before this branch
    # existed.
    #
    # The light path RETURNS IMMEDIATELY, touching NO model, NO tool, writing NO business record.
    # That
    # is its whole point: cheaper than any cheap model, because there is no model.
    #
    # Placed AFTER loading `user` (the user must really exist) and BEFORE everything else —
    # any later and what we meant to save would already be spent.
    if not vua_xac_thuc_de_gui_lai and TRIAGE_ENABLED:
        _route, _route_reason = triage(message)
        if _route == ROUTE_LIGHT:
            _logger.info(
                "agent_turn_duong_nhe",
                extra={"user_id": user_id, "thread_id": thread_id or user_id,
                       "ly_do": _route_reason, "bam_luat": RULES_HASH},
            )
            _res_light = {
                "reply": LIGHT_REPLIES,
                "tool_calls": [],
                "ticket_id": None,
                "should_escalate": False,
                # Phase 3 — the light path calls NO model (routing happens before touching the LLM)
                # ⟹ None/empty is the TRUTH, not "unreadable".
                "model": None,
                "models_da_thu": [],
                "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0,
                          "cached_input_tokens": 0, "reasoning_tokens": 0,
                          "input_chars": 0, "so_luot_goi_model": 0,
                          # Two COUNTING fields at the same level as `so_luot_goi_model`.
                          # The tester fell into the two-level trap: `.get()` on a missing key
                          # returns None, exactly like an
                          # existing key holding None.
                          # `duong` (route) STAYS top-level — it is a LABEL, not a measurement.
                          "so_tool_schema_gui": 0,
                          "chars_tool_schema_moi_luot": 0,
                          "suy_luan_gui": None},
                "loc_dau_ra": [],
                "tin_hieu_lo_chi_thi": {"nguyen_tac": 0, "quy_trinh": 0},
                "goi_y_handoff": False,
                "ly_do_fallback": None,
                # A marker written by THIS LAYER, from what it REALLY sends (nothing).
                # `so_tool_schema_gui` comes from a DIFFERENT mechanism than the triage decision, so
                # a single
                # failure point can't fake both: a marker stuck at "day_du" while this number = 0 is
                # a
                # self-exposing contradiction.
                "duong": ROUTE_LIGHT,
            }
            _write_ledger(_res_light, thread_id, user_id)
            return _res_light

        elif _route == ROUTE_SLOT_FILL:
            # 1B — the deterministic slot-collection gate (docs/giao-viec/2026-08-24-luong-
            # chatbot-1A-1B.md). The "has it been asked yet" state lives in this CALLING LAYER
            # (Redis,
            # thread_signals.py) — triage.py is a PURE function with no side effects. At most ONE
            # ask per
            # conversation (item 5): once asked, there is NO early return here any more; it falls
            # straight
            # through to the full path below like a normal day_du turn — MERGING the original
            # account + the
            # customer's answer is the job of the model reading the conversation history; this
            # deterministic
            # layer cannot merge cross-turn context (exactly the invariant "classify PER TURN").
            #
            # 🔴 Caught in review 24/08: uses `read_or_unknown()` (NOT `doc()`) — `== 0` is ONLY true
            # when
            # Redis confirms "really not asked yet". A Redis error returns `None`, and `None == 0`
            # is `False`
            # ⟹ does NOT fire, falls to day_du — exactly this module's safe direction ("when in
            # doubt, go
            # FULL"). Using plain `doc()` (merging errors into 0) would make a dead Redis ⟹ the gate
            # treat
            # every turn as the first ⟹ fire repeatedly.
            _effective_tid = thread_id or user_id
            if read_signal(SIGNAL_1B_SLOT_ASKED, _effective_tid) == 0:
                incr_signal(SIGNAL_1B_SLOT_ASKED, _effective_tid)
                # R1 (1A) fixed 24/08: the gate asks for EXACTLY ONE thing — the amount is the only
                # mandatory slot (see the ASK_MISSING_AMOUNT comment), so extract_slots(message) is
                # no longer
                # needed here to choose a template.
                _reply_slot = ASK_MISSING_AMOUNT
                _logger.info(
                    "agent_turn_duong_thu_slot",
                    extra={"user_id": user_id, "thread_id": _effective_tid,
                           "ly_do": _route_reason, "bam_luat": RULES_HASH},
                )
                _res_slot = {
                    "reply": _reply_slot,
                    "tool_calls": [],
                    "ticket_id": None,
                    "should_escalate": False,
                    # Same principle as ROUTE_LIGHT — no model is called, so None/0 is the TRUTH,
                    # not
                    # "unreadable".
                    "model": None,
                    "models_da_thu": [],
                    "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0,
                              "cached_input_tokens": 0, "reasoning_tokens": 0,
                              "input_chars": 0, "so_luot_goi_model": 0,
                              "so_tool_schema_gui": 0,
                              "chars_tool_schema_moi_luot": 0,
                              "suy_luan_gui": None},
                    "loc_dau_ra": [],
                    "tin_hieu_lo_chi_thi": {"nguyen_tac": 0, "quy_trinh": 0},
                    "goi_y_handoff": False,
                    "ly_do_fallback": None,
                    # 🔴 A SEPARATE label, NOT sharing "nhe" (light) — without it the gate's firing
                    # frequency per
                    # turn can't be counted in usage.jsonl, and the token-reduction forecast (1B.5)
                    # can't be verified
                    # (PO-agent request, item 1 of the 1B draft).
                    "duong": ROUTE_SLOT_FILL,
                }
                _write_ledger(_res_slot, thread_id, user_id)
                return _res_slot

    # ES-xx (ADR-022) — computed BEFORE calling the agent, on the customer's message, at the
    # SERVICE LAYER. No LLM call, nothing goes into the prompt, no extra step.
    #
    # Placed HERE rather than after the reply exists, deliberately: computing it afterwards would
    # still
    # honour "not in the prompt", but would lose the ability to raise the suggestion ON the current
    # turn — and the whole value of ES is moving frustrated people to a human EARLY, not one turn
    # later.
    #
    # DELIBERATELY NOT putting the emotion label into the prompt: the agent would SAY that
    # perception
    # out loud, i.e. assert a psychological conclusion about a person based on a classifier that may
    # be
    # wrong — against the spirit of hard constraint 3 (everything the agent asserts must trace to
    # real
    # data; an inferred emotion is not real data).
    emotion_signal = evaluate_turn(message, thread_id or user_id)

    # 1 guard PER turn (not global) — hands the `session` over between the main thread and the
    # background thread when the turn is abandoned on timeout, see TurnGuard (QA-12).
    guard = TurnGuard()
    agent = _build_agent(
        session, user_id=user_id, customer_name=None, otp_verified_at=otp_verified_at, guard=guard,  # PII-OK: deliberately passing None, not sending the full name to the LLM
        thread_id=thread_id or user_id,
    )
    # thread_id defaults to user_id (real behaviour, unchanged). eval/_harness.py passes a
    # separate thread_id per case to isolate conversation memory (the module-level checkpointer is
    # shared — without isolation, several cases with the same user_id in one eval run would continue
    # each other's conversations).
    config = {"configurable": {"thread_id": thread_id or user_id}}

    # `agent` above is ONLY for reading state before the turn — it doesn't depend on any model
    # (a checkpoint is conversation history, not an artefact of a specific model) so it does NOT
    # need
    # rebuilding per rotation below.
    state_before = agent.get_state(config)
    prev_len = len(state_before.values.get("messages", [])) if state_before.values else 0

    # Phase 3 (876a240) — MODEL POOL + ROTATION. `models_da_thu` (models tried) lists EVERY model
    # tried in this turn in order (including rejected attempts) — providers bill FAILED attempts
    # too,
    # and the "invoice reconciliation evidence" (876a240) must record them all, not just the final
    # answering model.
    tried_models: list[str] = []
    trying_model = llm_pool.turn_start_model()

    # Root span "agent_turn" — one chat turn is a multi-step ReAct loop (LLM generation +
    # interleaved
    # tool calls), NOT a single block (phase 1 of the observability checklist).
    # `callbacks=[handler]`
    # (NOT `.configurable`) creates a child span for EACH LLM/tool round inside, linking the
    # parent/child tree automatically through the current OTel context (the root span is active).
    with _tracer.start_as_current_span("agent_turn") as root_span:
        root_span.set_attribute("fin05.user_id", user_id)
        root_span.set_attribute("fin05.thread_id", thread_id or user_id)
        root_span.set_attribute("fin05.otp_verified", otp_verified_at is not None)

        # Phase 3 — THE ROTATION LOOP. Wraps build-agent + invoke, NOT the three existing except
        # branches below: the rotatable branch (an APIError carrying a quota-exhausted signal, with
        # OTHER
        # models STILL in the pool) is handled HERE and then `continue`s; every NON-rotatable branch
        # (429 ·
        # non-quota errors · pool exhausted · timeout/recursion) is `raise`d INTACT out of the loop
        # for the
        # THREE existing excepts to handle EXACTLY as before phase 3 — no behaviour change for those
        # cases,
        # only ADDING a new turn-off before reaching them.
        answering_model: str | None = None
        try:
            while True:
                agent = _build_agent(
                    session, user_id=user_id, customer_name=None,  # PII-OK: always None, the full name never leaves the system (ADR-010)
                    otp_verified_at=otp_verified_at, guard=guard, model=trying_model,
                    thread_id=thread_id or user_id,
                )
                tried_models.append(trying_model)

                def _invoke():
                    return agent.invoke(
                        # Phase 4 (Security 19/08): purpose="model_input" — the NARROW registry
                        # (D'), not loading
                        # Spacy/Date/generic Phone. See the src/observability/pii.py docstring.
                        {"messages": [HumanMessage(content=scrub_pii(message, purpose="model_input") or message)]},
                        config={
                            **config,
                            "callbacks": [OTelTracingCallbackHandler()],
                            "recursion_limit": _AGENT_RECURSION_LIMIT,
                        },
                    )

                # AGENT_TURN_TIMEOUT_SECONDS — OPENAI_TIMEOUT_SECONDS only caps EACH individual
                # OpenAI call;
                # one /agent/chat turn may need MANY calls interleaved with tools (ReAct), so the
                # total time can
                # still go far beyond (measured: 70s for one request) unless capped SEPARATELY here.
                # Runs in a
                # separate thread so `.result(timeout=...)` returns a controlled error to the client
                # in time.
                # DELIBERATELY NOT using `with ThreadPoolExecutor(...) as executor:` — `__exit__`
                # calls
                # `shutdown(wait=True)` by default, i.e. BLOCKS until the unfinished thread
                # completes before leaving
                # the `with`, wiping out the timeout's effect entirely. `shutdown(wait=False)` on
                # timeout: it can't
                # cancel the OpenAI call still running underneath (Python can't kill threads), but
                # it returns
                # control to the client IMMEDIATELY, without waiting. A NEW executor per attempt —
                # reusing an
                # executor after it has been `shutdown` is an error.
                executor = ThreadPoolExecutor(max_workers=1)
                # A timestamp so the ledger can answer "how long did this turn RUN before failing".
                # Without it the `timeout` label is an UNVERIFIABLE claim: a turn giving up
                # instantly and a turn
                # running the full 45 seconds look identical in the ledger. With it,
                # `giay_da_troi ≈ AGENT_TURN_TIMEOUT_SECONDS` (seconds elapsed) is evidence the
                # label is RIGHT, and
                # `0.4 seconds` is evidence it is WRONG.
                _turn_started_at = time.monotonic()
                try:
                    result = executor.submit(_invoke).result(timeout=AGENT_TURN_TIMEOUT_SECONDS)
                    answering_model = trying_model
                    break
                except RateLimitError:
                    # 429 NEVER rotates — it is transient congestion, not "out of tokens" (PO
                    # constraint 876a240).
                    # Raised intact for the outer except RateLimitError to handle exactly as before
                    # phase 3.
                    raise
                except APIError as e:
                    executor.shutdown(wait=False)
                    description = _describe_provider_error(e, model=trying_model)
                    # PO constraint 876a240: prefer `status_code` when the provider DOES return one
                    # — 403 is always
                    # treated as quota regardless of wording, NOT relying purely on fragile string
                    # matching
                    # (`co_dau_hieu_het_han_muc` — has quota-exhausted hint, see the warning where
                    # it is declared).
                    # Strings are only relied on when there is NO status_code — some transport
                    # errors carry no status
                    # code.
                    is_quota = description["ma_trang_thai"] == 403 or (
                        description["ma_trang_thai"] is None and bool(description["co_dau_hieu_het_han_muc"])
                    )
                    if not is_quota:
                        raise  # non-quota error — NO rotation, the old path
                    llm_pool.mark_exhausted(trying_model)
                    next_model = llm_pool.turn_start_model(tried=set(tried_models))
                    if next_model is None:
                        # POOL FULLY EXHAUSTED — the last quota error is raised INTACT for the outer
                        # except APIError.
                        # That IS the existing "needs intervention" message (no time promises, only
                        # pointing to another
                        # channel) — a fully exhausted pool is by nature "the provider keeps
                        # refusing"; no second
                        # message/mechanism is needed.
                        raise
                    trying_model = next_model
                    continue
                # GraphRecursionError/FutureTimeoutError: no except at THIS LAYER catches them —
                # they propagate
                # straight to the outer try, the old behaviour (no rotation on timeout/recursion).
        except RateLimitError as e:
            # 429 provider overload. BEFORE THIS VERSION it wasn't in the `except` tuple below -> it
            # fell
            # straight out as HTTP 500, and the customer received `{"detail":"Internal Server
            # Error"}` while
            # OpenAI had clearly said "try again in 1.381s". Measured: the tester reproduces it by
            # running
            # `--lap 3`.
            #
            # A SEPARATE BRANCH, NOT shared with timeout/recursion below — they differ in the MOST
            # IMPORTANT
            # way: that branch CREATES A TICKET handing over to a human, right for when the agent
            # gives up. 429
            # isn't that: it is transient congestion that clears in a few seconds. Creating tickets
            # for it would
            # dump a handful of ghost tickets on CSKH every peak minute for complaints that DON'T
            # EXIST — and
            # the customer still wouldn't have an answer.
            #
            # No sleep-and-retry here: the `openai` SDK already retried OPENAI_MAX_RETRIES times
            # following the
            # provider's `Retry-After` BEFORE raising up to here. Sleeping more at this layer would
            # only eat
            # into the AGENT_TURN_TIMEOUT_SECONDS budget and turn the 429 into a timeout — exactly
            # the confusion
            # `_fallback_reason` warns about.
            executor.shutdown(wait=False)
            # CORRECTION of commit 8a30238 (its message is easy to misread; history can't be
            # edited): the
            # phrase "no ghost tickets" there describes what THIS branch avoids doing, NOT a bug
            # that once
            # happened and was then blocked. Before the fix, 429 fell straight out as a 500 and
            # never touched
            # the fallback branch -> it never created any ticket via that path.
            #
            # ⚠️ BUT there is a REAL ghost-ticket path this branch does NOT close: when the SDK
            # sleeps per
            # `Retry-After` and the TOTAL exceeds AGENT_TURN_TIMEOUT_SECONDS, we get
            # FutureTimeoutError rather
            # than RateLimitError -> it falls to the branch below -> THAT branch DOES create a
            # ticket. So a slow
            # enough 429 still spawns tickets as before. Logged as F-33b.
            #
            # WHOEVER OPENS F-33b: plugging it here is plugging the WRONG SPOT. The spot to fix is
            # the timeout
            # branch, or the relationship OPENAI_MAX_RETRIES x AGENT_TURN_TIMEOUT_SECONDS. And F-33c
            # (storing
            # `ly_do_fallback` in the record) is the precondition for answering "does 429 spawn
            # tickets" with
            # ONE query — it can't be answered today, because the 15 fallback complaints in the DB
            # share ONE
            # reason text for both timeout and recursion.
            seconds = _retry_wait_seconds(e)
            _logger.warning(
                "agent_turn_qua_tai",
                extra={
                    "user_id": user_id,
                    "thread_id": thread_id or user_id,
                    "retry_after_giay": seconds,
                    "so_lan_sdk_da_thu": OPENAI_MAX_RETRIES,
                },
            )
            root_span.set_attribute("fin05.qua_tai", True)
            advice = f" sau khoảng {seconds:.0f} giây" if seconds else " sau ít giây"
            _res = {
                "reply": (
                    "Xin lỗi bạn, hệ thống đang bận nên mình chưa xử lý kịp. "
                    f"Bạn nhắn lại giúp mình{advice} nhé — tin nhắn của bạn "
                    "chưa bị mất gì cả."
                ),
                "tool_calls": [],
                # Phase 3 — 429 does NOT rotate (PO constraint), so trying_model here is ALWAYS the
                # ONLY model
                # tried this turn.
                "model": trying_model,
                "models_da_thu": list(tried_models),
                "ticket_id": None,
                "should_escalate": False,
                "usage": {
                    # `None` = UNREADABLE, entirely different from `0` = NONE.
                    # On this branch the request WAS SENT but no call RETURNED ⟹ `so_luot_goi_model
                    # = 0` is the TRUTH.
                    # But whether the provider bills a rejected/abandoned request is something we
                    # CAN'T check from
                    # inside the system ⟹ tokens are None.
                    # Putting 0 there would assert something we don't know.
                    "input_tokens": None,
                    "output_tokens": None,
                    "total_tokens": None,
                    "cached_input_tokens": None,
                    "so_luot_goi_model": 0,
                    "so_tool_schema_gui": _TOOLS_SENT_COUNT,
                    "chars_tool_schema_moi_luot": _CHARS_TOOL_SCHEMA_REAL,
                    "suy_luan_gui": _REASONING_SENT,
                },
                "loc_dau_ra": [],
                "tin_hieu_lo_chi_thi": {"nguyen_tac": 0, "quy_trinh": 0},
                "goi_y_handoff": False,
                "ly_do_fallback": "qua_tai",
                # The CONCLUSION above, the SYMPTOM here — neither can replace the other.
                "trieu_chung": {**_error_symptom(e), "giay_da_troi": round(time.monotonic() - _turn_started_at, 2)},
                "duong": ROUTE_FULL,
            }
            _write_ledger(_res, thread_id, user_id)
            return _res
            executor.shutdown(wait=True)  # the thread really had finished when .result() returned; wait=True costs nothing extra
        except APIError as e:
            # Every REMAINING way the provider can refuse. `RateLimitError` is already caught above
            # — it is
            # a CHILD of APIError, so the order of these two branches can NOT be swapped: reversed,
            # the 429
            # would be swallowed here and lose the specific `retry_after` message the provider
            # clearly gave.
            #
            # TWO INDEPENDENT AXES, not two ends of one axis:
            #   CUSTOMER axis    — soft 8/8, never a bare 500. Even for 400/404
            #                      (our bug): the customer doesn't deserve a 500 for our bug.
            #   OPERATIONS axis  — the noise level is set separately. error for cases needing a
            # human,
            #                      warning for cases that clear themselves.
            # Merging the two axes produces BOTH errors: loud means the customer gets a 500 (exactly
            # today's
            # case), quiet means operations never learn the key is wrong.
            executor.shutdown(wait=False)
            description = _describe_provider_error(e, model=trying_model)
            intervention = bool(description["can_can_thiep"])
            # TWO SEPARATE EVENT NAMES, not one name with a classification field. Reason (security
            # ①):
            # with separate names, `grep` finds them today, and the day someone attaches a real
            # alert, it
            # attaches to the name — no code change. One shared name + a filter field forces whoever
            # builds the
            # alert to know that field exists.
            ten_su_kien = (
                "agent_turn_ncc_can_can_thiep" if intervention else "agent_turn_ncc_thoang_qua"
            )
            write = _logger.error if intervention else _logger.warning
            write(
                ten_su_kien,
                extra={
                    "user_id": user_id,
                    # correlation_id: links the incident to the NUMBER OF SESSIONS affected without
                    # storing any
                    # content (security ④).
                    "thread_id": thread_id or user_id,
                    **description,
                },
            )
            # The SECOND machine-readable surface, and the ONLY one queryable today: the Jaeger
            # span.
            # Already wired, no new route needed (a new route = a contract change), and no
            # operational state
            # exposed on the public `/health` — `lop_loi_cuoi="AuthenticationError"` (last error
            # class) on an
            # unauthenticated endpoint would tell outsiders our key is broken.
            root_span.set_attribute("fin05.su_kien", ten_su_kien)
            root_span.set_attribute("fin05.loi_nha_cung_cap", str(description["lop_loi"]))
            root_span.set_attribute("fin05.can_can_thiep", intervention)
            root_span.set_attribute("fin05.het_han_muc", bool(description["co_dau_hieu_het_han_muc"]))
            root_span.set_attribute("fin05.tu_chan", bool(description["tu_chan"]))
            if intervention:
                # A RED span, not just a tagged span. Jaeger filters on `error=true` by default; a
                # custom tag
                # would require the on-call engineer to know its name in advance.
                root_span.set_status(Status(StatusCode.ERROR, ten_su_kien))
                root_span.record_exception(e)

            # TWO DIFFERENT SENTENCES, differing exactly where there are consequences. Merging them
            # would
            # tell the customer "try again in a few minutes" when the truth is "out of money, no
            # number of
            # retries will fix it".
            #
            # Three things BOTH sentences deliberately DON'T say:
            #  · not "access not yet granted" — the agent once said that and then asked for a
            # transaction ID,
            #    sending the customer off on a pointless task (observation ⑤).
            #  · not "recorded"/"CSKH will contact you" — this branch creates NO ticket. Promising a
            # record
            #    that doesn't exist is the worst kind of fabrication: the customer SITS WAITING for
            # a call that
            #    never comes.
            #  · no error code, no provider name — useless to the customer, and it exposes
            # infrastructure.
            #
            # The strings are CONSTANTS at the code layer, NOT model-generated: we only get here
            # because the
            # model just failed; asking it to write the apology would depend on exactly what just
            # broke.
            # The NEEDS-INTERVENTION group: NO time promises (retrying may not help for hours) AND
            # it must
            # point to another channel.
            # This is security's CONDITION ③, not optional: we deliberately don't record this turn,
            # and the
            # cost of losing track is NOT uniform — losing a customer asking about fees costs ≈ 0,
            # losing a
            # customer about to REPORT FRAUD costs a lot and is time-sensitive. We can't tell them
            # apart
            # because the agent failed BEFORE classifying. The path to a human is the only remaining
            # measure —
            # it turns "we lost track of the customer" into "the customer still has a way forward".
            reply = (
                "Xin lỗi bạn, hệ thống đang gặp sự cố kỹ thuật nên tạm thời "
                "chưa xử lý được yêu cầu này. Nếu việc của bạn cần xử lý ngay, "
                f"bạn liên hệ {OTHER_SUPPORT_CHANNELS} giúp mình nhé."
                if intervention else
                "Xin lỗi bạn, hệ thống đang bận nên mình chưa xử lý kịp. "
                "Bạn nhắn lại giúp mình sau ít phút nhé — tin nhắn của bạn "
                "chưa bị mất gì cả."
            )
            _res = {
                "reply": reply,
                "tool_calls": [],
                # Phase 3 — this branch is ALSO the destination for "pool fully exhausted" (every
                # model in
                # LLM_MODEL_POOL marked exhausted within this turn). `models_da_thu` then contains
                # EVERY model
                # tried, not just the last — exactly the "reconciliation evidence" requirement
                # (876a240).
                "model": None,  # NO model answered successfully on this branch
                "models_da_thu": list(tried_models),
                "ticket_id": None,          # DELIBERATE: see the comment on _ERRORS_NEEDING_INTERVENTION
                "should_escalate": False,
                "usage": {
                    # `None` = UNREADABLE, entirely different from `0` = NONE.
                    # On this branch the request WAS SENT but no call RETURNED ⟹ `so_luot_goi_model
                    # = 0` is the TRUTH.
                    # But whether the provider bills a rejected/abandoned request is something we
                    # CAN'T check from
                    # inside the system ⟹ tokens are None.
                    # Putting 0 there would assert something we don't know.
                    "input_tokens": None,
                    "output_tokens": None,
                    "total_tokens": None,
                    "cached_input_tokens": None,
                    "so_luot_goi_model": 0,
                    "so_tool_schema_gui": _TOOLS_SENT_COUNT,
                    "chars_tool_schema_moi_luot": _CHARS_TOOL_SCHEMA_REAL,
                    "suy_luan_gui": _REASONING_SENT,
                },
                "loc_dau_ra": [],
                "tin_hieu_lo_chi_thi": {"nguyen_tac": 0, "quy_trinh": 0},
                "goi_y_handoff": False,
                # Two SEPARATE values, not merged: the operational question "does this incident
                # clear itself
                # or need a human" must be answerable with one query.
                "ly_do_fallback": (
                    "nha_cung_cap_can_can_thiep" if intervention else "nha_cung_cap_thoang_qua"
                ),
                # 🔴 The two labels above are CONCLUSIONS ("who must do what"). They merge
                # `401` wrong key · `403` quota exhausted · `404` wrong model name into ONE string —
                # three
                # incidents needing three completely different fixes.
                # The status code accompanies them here so the ledger can answer the second
                # question:
                # "what did the provider say". The two old labels are KEPT because tests assert them
                # — renaming is
                # something that has to go through the tester.
                "trieu_chung": {**_error_symptom(e), "giay_da_troi": round(time.monotonic() - _turn_started_at, 2)},
                "duong": ROUTE_FULL,
            }
            _write_ledger(_res, thread_id, user_id)
            return _res
        except (GraphRecursionError, FutureTimeoutError) as e:
            # wait=False is always safe here: if the thread has finished (the GraphRecursionError
            # branch)
            # it returns immediately; if not (a real timeout) it doesn't wait, exactly as intended.
            executor.shutdown(wait=False)
            # The ReAct loop exceeded _AGENT_RECURSION_LIMIT OR the total time ceiling (this really
            # happens — not theory, see case CONSUME-002) — the error must NOT fall out as a 500;
            # hand over to a
            # human entirely instead of hanging indefinitely/crashing. root_span still records
            # correctly (the
            # context manager closes even on exceptions), there are just no child spans for the
            # failed turn.
            is_timeout = isinstance(e, FutureTimeoutError)
            _logger.warning(
                "agent_turn_timeout" if is_timeout else "agent_recursion_limit_reached",
                extra={"user_id": user_id, "thread_id": thread_id or user_id},
            )
            root_span.set_attribute("fin05.recursion_limit_reached", not is_timeout)
            root_span.set_attribute("fin05.turn_timeout", is_timeout)
            # Hand the session back to this thread BEFORE writing (QA-12). Set the flag first, then
            # take
            # the lock: any in-flight tool call finishes before releasing the lock, and every tool
            # call AFTER
            # that sees the flag and refuses to touch the DB — the abandoned background thread can
            # no longer
            # create a second ticket for the same chat turn (measured: 4/4 cases used to create
            # ghost tickets).
            #
            # Written with THE INJECTED `session` itself, no second session opened:
            # opening a second connection to the same DB while the first holds an unfinished write
            # transaction is what causes "database is locked" (QA-12) — and it is unnecessary,
            # because once
            # the lock is acquired this session is completely safe. Using the injected session is
            # also what
            # preserves QA-10: the ticket always lands in exactly the DB the caller specified.
            guard.abandoned.set()
            with guard.lock:
                handoff = flag_human_handoff(
                    session,
                    user_id=user_id,
                    reason="Hệ thống AI gặp khó khăn khi xử lý yêu cầu này (vòng lặp tra cứu không ra kết quả rõ ràng) — cần chuyên viên hỗ trợ trực tiếp.",
                    thread_id=thread_id or user_id,
                )
                # Explicit commit: the customer was just told this ticket ID, so it MUST really
                # exist,
                # regardless of whether the caller commits (the eval harness rolls back between
                # cases) — reporting
                # an untraceable ticket ID is fabricating data, hard constraint #3.
                session.commit()
            _res = {
                "reply": "Mình chưa tra được yêu cầu này, để mình chuyển cho chuyên viên hỗ trợ trực tiếp nhé — mã ticket của bạn là "
                + handoff["ticket_id"]
                + ".",
                # Phase 3 — timeout/recursion do NOT rotate (PO constraint), so EXACTLY ONE model
                # was tried
                # this turn.
                "model": trying_model,
                "models_da_thu": list(tried_models),
                # `None`, NOT `[]`. This fixes a lie told by the data: `[]` means "no tool was
                # called", while
                # on this branch we DON'T KNOW — `_invoke` raised, so there is no
                # `result["messages"]` to read.
                # Recovering it from the checkpointer would mean reading while the background thread
                # is still
                # writing, exactly the race that caused QA-12; not worth it.
                # Before this fix the tester read `[]` as a real observation and nearly concluded
                # "the agent called
                # no tools" for cases that had run tools.
                # `null` = "couldn't be recovered", entirely different from `[]` = "none".
                "tool_calls": None,
                "ticket_id": handoff["ticket_id"],
                "should_escalate": False,
                # These four zeros mean "NOT MEASURABLE", not "measured as 0" —
                # `_invoke` raised AFTER the model may already have run and spent real tokens. The
                # same kind of
                # distinction `tool_calls: None` above deliberately keeps. Not yet changed to None
                # because a
                # consumer sums them directly; but anyone building cost tests/dashboards on this
                # field must know:
                # fallback turns SILENTLY under-report money spent, and an assertion `usage == 0`
                # would be green in
                # BOTH senses.
                "usage": {
                    # `None` = UNREADABLE, entirely different from `0` = NONE.
                    # On this branch the request WAS SENT but no call RETURNED ⟹ `so_luot_goi_model
                    # = 0` is the TRUTH.
                    # But whether the provider bills a rejected/abandoned request is something we
                    # CAN'T check from
                    # inside the system ⟹ tokens are None.
                    # Putting 0 there would assert something we don't know.
                    "input_tokens": None,
                    "output_tokens": None,
                    "total_tokens": None,
                    "cached_input_tokens": None,
                    "so_luot_goi_model": 0,
                    "so_tool_schema_gui": _TOOLS_SENT_COUNT,
                    "chars_tool_schema_moi_luot": _CHARS_TOOL_SCHEMA_REAL,
                    "suy_luan_gui": _REASONING_SENT,
                },
                # A fallback sentence written by US, not by the LLM -> no filtering needed.
                "loc_dau_ra": [],
                "tin_hieu_lo_chi_thi": {"nguyen_tac": 0, "quy_trinh": 0},
                # A turn that falls back must still carry the signal: a frustrated customer hitting
                # a system
                # error is exactly when a human is MOST needed.
                "goi_y_handoff": bool(emotion_signal),
                # THE DEFINITIVE POSITIVE MARKER of a fallback. The tester uses exactly this field
                # to exclude
                # cases from paired comparisons, so it carries part of the definition of the
                # measurement's
                # exclusion set — it must NOT be set by mistake on the normal path.
                # Previously they had to recognise it by a string signature in `reply`, which could
                # drift after a
                # single wording edit.
                "ly_do_fallback": _fallback_reason(e),
                # `giay_da_troi` (seconds elapsed) is what makes the `timeout` label VERIFIABLE
                # instead of
                # something to take on trust. Without it, "timeout" is just the name of a code
                # branch.
                "trieu_chung": {**_error_symptom(e), "giay_da_troi": round(time.monotonic() - _turn_started_at, 2)},
                "duong": ROUTE_FULL,
            }
            _write_ledger(_res, thread_id, user_id)
            return _res
    all_messages = result["messages"]
    turn_messages = all_messages[prev_len:]

    reply = ""
    stop_reason = None
    for m in reversed(turn_messages):
        if isinstance(m, AIMessage) and not m.tool_calls:
            reply = m.content
            stop_reason = (getattr(m, "response_metadata", None) or {}).get("finish_reason")
            break

    # SHOUT when the model returns EMPTY content. Before this version `reply` received "" and went
    # straight to the customer: a blank screen, HTTP 200, no error, no log.
    # The cause: a reasoning model spends its whole token cap on thinking and has no room left to
    # generate content. Not fixable by guessing the cap — fixed by making the silent branch SHOUT,
    # and
    # only then knowing whether the cap needs tuning.
    if not str(reply).strip():
        _logger.warning(
            "agent_reply_rong",
            extra={
                "user_id": user_id,
                "thread_id": thread_id or user_id,
                "model": answering_model,
                "so_message_luot_nay": len(turn_messages),
                "finish_reason": stop_reason,
                "ghi_chu": "Content rỗng nhưng KHÔNG phải do hết trần — chưa rõ nguyên nhân.",
            },
        )

    tool_msgs_by_id = {m.tool_call_id: m for m in turn_messages if isinstance(m, ToolMessage)}
    tool_calls_out: list[dict] = []
    ticket_id = None
    should_escalate = None
    has_otp_error_in_turn = False
    orphan_call_count = 0

    for m in turn_messages:
        if not (isinstance(m, AIMessage) and m.tool_calls):
            continue
        for call in m.tool_calls:
            tm = tool_msgs_by_id.get(call["id"])
            if tm is None:
                # 🔴 ORPHANED CALLS — the model emits a `tool_call` with NO resulting `ToolMessage`.
                # The
                # previous version `continue`d silently ⟹ it left NO trace, `so_tool_call=0`,
                # **exactly like
                # "the model proposed nothing"**. Two completely different states wearing the same
                # shell —
                # exactly the bug family the project has named many times.
                orphan_call_count += 1
                _logger.warning(
                    "agent_tool_call_mo_coi",
                    extra={"user_id": user_id, "thread_id": thread_id or user_id,
                           "tool_name": call["name"]},
                )
                continue
            try:
                payload = json.loads(tm.content)
            except (json.JSONDecodeError, TypeError):
                payload = {"raw": tm.content}
            tool_calls_out.append({"tool_name": call["name"], "args": call["args"], "result": payload})
            if call["name"] == "create_ticket" and "ticket_id" in payload:
                ticket_id = payload["ticket_id"]
                should_escalate = payload.get("should_escalate")
                # 🔴 DON'T REBUILD `loai_khieu_nai` (complaint type) HERE. The previous version
                # pulled
                # `complaint_type` out of `args` at this spot for ⑨ to use; ⑨ MOVED ITS HOOK on
                # 25/08 to two thread
                # signals (`is_wrong_transfer_case` + `_SIGNAL_TXN_FOUND`, see the ⑨ · K2 block
                # below) so the
                # screening question lands on TURN 4 instead of turn 8. The variable here became a
                # corpse —
                # nobody reads it, but the old comment still described a mechanism that had moved,
                # i.e. it
                # ACTIVELY pointed later readers the wrong way.
                # (If `complaint_type` is needed for SOMETHING ELSE: it is in `args`,
                # NOT in `result` — create_ticket.py:110-118 deliberately doesn't return it.)

            # RB3 false positive (04/09, found by QA, 2/2 E2E cases): this loop used to read
            # ticket_id ONLY
            # from create_ticket — every SUCCESSFUL request_human_handoff (creating a new ticket OR
            # reusing an
            # old one, see flag_human_handoff returning {"ticket_id":...}) was treated as "no real
            # ticket yet",
            # and RB3 (the block just below, ~line 2172) overwrote the CORRECT answer with
            # _TICKET_NOT_CREATED_REPLY. NOT merged into the create_ticket branch above —
            # request_human_handoff has NO should_escalate (a different payload shape); merging
            # would read a
            # non-existent field. This branch does NOT loosen the RB3 condition
            # (`ticket_id is None and claims_ticket_created(...)` stays as is) — it only adds one
            # VALID source
            # for ticket_id to be non-None when the real tool has succeeded.
            #
            # 🔴 CORRECTION 05/09 (the review re-checked; the old line was WRONG): case
            # MT-Z01 was NOT "0 tool_call" — that turn's RAW `AIMessage.tool_calls` DID contain
            # `create_ticket`, but as an ORPHANED call (no `ToolMessage` reply, see
            # `orphan_call_count` in the
            # loop above), so it did NOT get into `tool_calls_out`/this branch — that is why the
            # measurement at
            # the time said `so_tool_call=0` (counted on the filtered `tool_calls_out`), not that
            # the model
            # called no tool at all. `ticket_id` is still None as before (a payload that doesn't
            # exist can't be
            # read), but RB3 now fires via the RAW signal `has_ticket_proposal`
            # (see the RB3 gate below), not via "no AIMessage carrying tool_calls" as the old line
            # wrongly
            # claimed.
            if call["name"] == "request_human_handoff" and "ticket_id" in payload:
                ticket_id = payload["ticket_id"]

            # ⑧ · the "turn 1" insertion point — whether any tool this turn was blocked by the OTP
            # GATE.
            # Reads the RETURN VALUE, doesn't catch exceptions: the two OTP errors
            # `return` a dict, they do NOT raise (customer_tools.py:596-613) —
            # the same trap `_STOP_LOOP_INSTRUCTION` recorded there.
            # Matches on `loai` (kind) FIRST (structured, built in phase 2.5 so the client doesn't
            # depend on
            # wording), and only then on the Vietnamese anchor for the
            # `_OTP_REQUIRED_ERROR` branch — a branch that DELIBERATELY has no `loai` (see the
            # comment there),
            # so the string anchor is the ONLY path left.
            if isinstance(payload, dict) and payload.get("status") == "error":
                if payload.get("loai") == "otp_het_tuoi" or "xác thực" in str(payload.get("message", "")):
                    has_otp_error_in_turn = True

    if ticket_id is not None:
        write_investigation_logs_for_ticket(session, ticket_id=ticket_id, all_messages=all_messages)
        if emotion_signal:
            _raise_priority_by_emotion(session, ticket_id=ticket_id)

    # Accumulated token usage of THIS TURN (every model call inside, including intermediate
    # tool-calling rounds) — used to measure real cost (eval/measure_quality.py),
    # NOT affecting the old contract (only new keys added, no existing key changed).
    # T1 — `cached_tokens` is the ONLY thing telling whether prompt caching works.
    # Before this version nobody knew whether the cache hit 0% or 50%; inferring from OpenAI's docs
    # can't replace measurement (and that inference was wrong once: the HH:MM timestamp sat at
    # character 233/16,082, making the stable prefix only ~68 tokens, far below the 1024 threshold —
    # the cache certainly hit 0%).
    # `input_chars` — a quantity that is INVARIANT ACROSS TOKENIZERS.
    #
    # Why it is needed: two providers' tokens are NOT comparable (different tokenizers, Vietnamese
    # being where they diverge most), so the T1->T3 measurement chain would BREAK as soon as the
    # model
    # changes. Characters don't change.
    #
    # ⚠️ EXACTLY WHAT IS COUNTED, DECLARED HERE so it doesn't become a "partial metric that looks
    # like
    # an invariant quantity":
    #     YES   system prompt (15,094 characters) + every message of each model call,
    #           accumulated across ReAct steps — exactly the variable part
    #     NO    the JSON schemas of the 5 tools = 6,773 characters, CONSTANT per call
    #
    # The missing part is a MEASURED constant, not an unknown: anyone needing the absolute total
    # adds
    # `6773 × so_luot_goi_model`. The number is written here instead of being silently omitted — a
    # named gap can be subtracted, an unnamed one can't.
    usage = {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "cached_input_tokens": 0,
        "reasoning_tokens": 0,
        "input_chars": 0,
        # COUNTS CALLS THAT **RETURNED**, not calls emitted — it only increments when an
        # `AIMessage` has `usage_metadata`, i.e. only when the provider has answered.
        # Declared here because the field name doesn't say so, and a field that doesn't declare what
        # it
        # counts makes EVERY value ambiguous, even the correct ones.
        "so_luot_goi_model": 0,
        # THREE token states, NOT two (Lead measured 19/08: 4 turns DID call the model yet tokens
        # recorded 0 — "called, the provider reported no number", NOT "0 cost"). `False` = every
        # call in
        # this turn had a valid number; `True` = AT LEAST one model call answered without
        # total_tokens —
        # spend_gate() reads this flag to NOT silently add 0.
        "token_khong_doc_duoc": False,
        "chars_tool_schema_moi_luot": _CHARS_TOOL_SCHEMA_REAL,
        "so_tool_schema_gui": _TOOLS_SENT_COUNT,
        "suy_luan_gui": _REASONING_SENT,
        # The INSTRUCTION identity of this turn. The rendered prompt changes every minute (it
        # contains
        # the date/time), so "the same prompt" across two measurement runs is an ASSUMPTION rather
        # than a
        # fact — unless the TEMPLATE hash is compared. Returned ready-made so nobody has to remember
        # to
        # record it, and so a before/after pair straddling two different templates GETS EXPOSED.
        "bam_mau_prompt": hash_prompt_template(),
    }
    _system_prompt_chars = len(build_system_prompt(current_time=dt.datetime.utcnow()))
    for m in turn_messages:
        meta = isinstance(m, AIMessage) and getattr(m, "usage_metadata", None)
        if meta:
            # Each AIMessage with usage_metadata = ONE model call. That call's input is the system
            # prompt +
            # every message BEFORE it. Rebuilt from `all_messages` rather than intercepting at the
            # model layer:
            # intercepting would be more precise, but would require patching the library — not worth
            # it for a
            # measurement metric.
            j = all_messages.index(m)
            usage["so_luot_goi_model"] += 1
            usage["input_chars"] += _system_prompt_chars + sum(
                len(str(getattr(x, "content", "") or "")) for x in all_messages[:j]
            )
            for k in ("input_tokens", "output_tokens", "total_tokens"):
                usage[k] += meta.get(k, 0) or 0
            # The model HAS answered (we are in the truthy `meta` branch) but reported no
            # total_tokens ->
            # "unreadable", not a real "0 cost". THIS flag preserves the third state, while the `or
            # 0` sum above
            # stays as is (Lead: don't change the loop, it would break turns over a ledger-write
            # error).
            if not meta.get("total_tokens"):
                usage["token_khong_doc_duoc"] = True
            # LangChain gathers provider details into `input_token_details`; OpenAI puts the cached
            # part
            # under the key `cache_read`. Read defensively because key names are the provider's
            # contract, not
            # ours.
            # A reasoning model's THINKING tokens live in `output_token_details`,
            # NOT `input_token_details`. They are counted in `output_tokens` so the bill isn't wrong
            # — but
            # without separating them nobody knows how much money is being paid for the part
            # customers never
            # read.
            usage["reasoning_tokens"] += (meta.get("output_token_details") or {}).get("reasoning", 0) or 0
            detail = meta.get("input_token_details") or {}
            usage["cached_input_tokens"] += detail.get("cache_read", 0) or 0

    # Lead measured 19/08: `meta.get(k, 0) or 0` above squashes "unreadable" into 0
    # RIGHT INSIDE the loop — but `spend_gate()` (graph._write_ledger) was already correct for this
    # case; its `None` path just could never be reached because usage is initialised to 0, not None
    # (graph.py:1242). Fixed HERE, after the loop, WITHOUT changing `spend_gate`: if the model HAS
    # answered (so_luot_goi_model > 0) and the token total is still 0 after summing every call —
    # meaning NO call reported a number, not "0 cost" — return `None` so it lands in the existing
    # `cong_chi_tieu_bo_qua_khong_biet` (spend gate skipped, unknown) branch instead of being
    # swallowed
    # by `spend_gate`'s silent `tokens <= 0` branch.
    if usage["so_luot_goi_model"] > 0 and usage["total_tokens"] == 0:
        usage["input_tokens"] = None
        usage["output_tokens"] = None
        usage["total_tokens"] = None

    # 🔴 Two LIMITATIONS the Lead declared 19/08 — both are CHOICES, not omissions:
    #
    # ① The "PARTIALLY known" case (several calls per turn — the shape rotation produces):
    #    model A reports 20,000 tokens, model B (rotated to) reports nothing. The guard above only
    # fires
    #    when the TOTAL = 0 — here the total = 20,000 ≠ 0, the guard stays silent, and B's share
    # NEVER
    #    enters the cap. A DELIBERATE trade-off: counting the known part beats dropping the whole
    # turn.
    #    The `token_khong_doc_duoc` flag (per call, see above) still goes `True`, so it is still
    #    TRACEABLE via the `unreadable_count_today()` counter — the missing part just can't be
    #    accumulated into the money figure, because there is no number to add.
    #
    # ② The "KNOWN NOTHING but SOME fields reported" case: a real test measured
    #    `{"input_tokens":120,"output_tokens":0,"total_tokens":0}` — ALL THREE fields become `None`,
    #    including `input_tokens=120` that the provider DID report. This is the REVERSE direction of
    # the
    #    bug just fixed (turning KNOWN into UNKNOWN), accepted DELIBERATELY: a half-reported
    #    usage_metadata block is hard to trust as a whole, and keeping input_tokens alone wouldn't
    # help
    #    `spend_gate()` (it needs total_tokens) — not an omission.
    #
    # Both are acceptable for the "minimal cap" (PO 876a240) as small errors that are DECLARED and
    # TRACEABLE (the `khong_doc_duoc` counter) — not a reason to build more mechanisms.

    # TWO COMPLETELY DIFFERENT empty cases, deliberately not merged:
    #   empty + finish_reason="length" -> the model spent the whole token cap on hidden thinking,
    # with
    #       no room left for content. This is OUR CONFIGURATION failure, fixable via LLM_MAX_TOKENS.
    #       It must BLOW UP: letting it through would make the measurement suite record an
    #       infrastructure error of ours as "the model answered poorly" (Rule 1c).
    #   empty for another reason -> unknown. Warn, don't guess, don't swallow.
    if not str(reply).strip() and stop_reason == "length":
        _logger.error(
            "agent_reply_rong_het_tran",
            extra={
                "user_id": user_id,
                "model": answering_model,
                "finish_reason": stop_reason,
                "reasoning_tokens": usage["reasoning_tokens"],
                "output_tokens": usage["output_tokens"],
                "llm_max_tokens": LLM_MAX_TOKENS,
            },
        )
        raise EmptyReplyError(
            f"Model {answering_model} tra noi dung RONG voi finish_reason=length — "
            f"tran token bi phan suy nghi an het ({usage['reasoning_tokens']}/"
            f"{usage['output_tokens']} token dau ra la reasoning). "
            f"Nang LLM_MAX_TOKENS (hien {LLM_MAX_TOKENS})."
        )

    # THE TRACEABILITY SOURCE for O3's provenance rule: every code/digit sequence of >=7 characters
    # the agent states must be present in one of these two places — otherwise where did it come
    # from?
    #   · tool results of this turn AND of earlier turns (`assemble_o3_source`)
    #   · everything the CUSTOMER typed in the conversation — not just the current turn, because the
    #     customer may read out a receipt code on turn 1 and the agent repeat it on turn 3
    # This is hard constraint 3 written as an executable check.
    # TWO SEPARATE SOURCE CHANNELS — not merged into one string. Tool payloads are JSON, so commas
    # in
    # them are FIELD SEPARATORS; customer text is prose, so commas/dots are thousands separators.
    # Merging and extracting with one rule would certainly misread one of the two channels — and
    # misreading the JSON channel produces numbers that DON'T EXIST into the valid source set.
    tool_source = assemble_o3_source(all_messages, tool_calls_out)
    customer_text = " ".join(
        m.content for m in all_messages if isinstance(m, HumanMessage) and isinstance(m.content, str)
    )
    filtered_reply, matched_group = filter_output(
        reply,
        source=tool_source,
        customer_text=customer_text,
        customer_message=message,
        thread_id=thread_id or user_id,
    )
    # O2 COUNT-FIRST-BLOCK-LATER (security, docs/security/mo-neo-quy-trinh-cho-O2.md,
    # approved by the PO) — RUNS ON THE ORIGINAL `reply`, not `filtered_reply`. Listing density is a
    # signal about the agent's BEHAVIOUR (whether it is reciting the rulebook), independent of
    # whether
    # O1-O4 blocked that sentence — mixing the two would blind the density distribution to exactly
    # the
    # sentences O3/O4 replaced with SAFE_FALLBACK_REPLY.
    #
    # Before this version the function had NO call site on the real path (only tests/ and eval/) —
    # the
    # proposition "count first, escalate to blocking when leaks are seen" was empty in production
    # until
    # now. Returned via the ENVELOPE (not only written to Redis) for the same reason as the three
    # diagnostic fields below: eval calls the graph directly and Redis is per-process fakeredis, so
    # a
    # counter written only to Redis would be invisible to whoever is measuring.
    # ⑭ — the SECOND evidence-producing path: this turn the model ran and a TOOL was blocked by the
    # OTP
    # gate. Covers the case where ④ didn't fire (e.g. a sentence outside GROUP B where the model
    # still
    # decided to call a tool) — without this branch, the customer's legitimate resend flow would be
    # wrongly blocked by ⑭ itself.
    if has_otp_error_in_turn:
        incr_signal(_SIGNAL_OTP_BLOCKED, thread_id or user_id)

    # ── 🔴 HARD-CONSTRAINT-3 GATE · A CLAIMED TICKET MUST BE A REAL TICKET ───────────
    # Incident 25/08, during a scripted run: the bot said *"Đã tạo hồ sơ khiếu nại thành công với mã
    # CMP-00003"* (the complaint case was created successfully with code CMP-00003) while **0 rows**
    # were
    # created — and `CMP-00003` was a REAL code of ANOTHER customer. The bot stole nothing; it made
    # up a
    # short string that happened to be someone else's key, so every PII-masking layer was
    # irrelevant.
    #
    # [MEASURED] that turn did NOT fail: so_luot_goi_model=1 · ly_do_fallback=null ·
    # so_tool_call=0. The model was just STORYTELLING in a normal turn.
    #
    # [MEASURED] why it slipped through: O5 STEPS ASIDE when the sentence includes a code (its
    # comment
    # declares the assumption *"O3 already covers every fabricated-code case"*), while O3 is BLIND
    # to
    # `CMP-00003` (the `-` cuts it below the 7-contiguous-character threshold). The gap sits EXACTLY
    # BETWEEN the two gates — neither gate is broken; the DIVISION OF LABOUR between them is.
    # ⟹ **Adding a fake code to a sentence made it SAFER in the filter's eyes.**
    #
    # 🔴 THIS GATE DOES NOT MATCH VOCABULARY TO GUESS TRUE/FALSE — it compares the claim against this
    # turn's REAL `ticket_id`. That is why it doesn't inherit the ceiling of word matching that
    # `_match_o5` declared after three rounds of fixes.
    # Placed BEFORE every insertion point (⑧/⑨) so the replacement sentence doesn't carry the false
    # claim along.
    #
    # 🔴 THIRD TIME (05/09) — QA reproduced 2/2 times: the customer asked "chưa nhận được tiền"
    # (money not
    # received), the turn ONLY called `lookup_transaction` (status "success" on the system side),
    # and
    # the model summarised the result and then ASKED the customer before creating a case ("...được
    # không ạ?" — is that OK?) — it had NOT proposed creating a ticket this turn at all.
    # `claims_ticket_created()` still returned `True` because of exactly the RISK DIRECTION DECLARED
    # there (code/"success" checked REPLY-GLOBALLY): "Mã giao dịch" (a transaction ID, not a ticket
    # code) + "đã ghi nhận" (talking about the MONEY TRANSFER being recorded, not a case) fell
    # exactly
    # into the 2 pieces of the SOFT branch, though neither piece was about actually CREATING A CASE.
    #
    # Fixed with a STRUCTURAL GATE (suggested by the review, preferred over a third vocabulary patch
    # —
    # for fear of spawning a 4th branch): `claims_ticket_created()` is only asked when THIS TURN
    # really
    # intends to create a ticket (`create_ticket`/`request_human_handoff` appears in the RAW
    # `AIMessage.tool_calls` — including ORPHANED calls, see the loop above). A turn ONLY calling
    # other
    # tools (lookup/history/policy...) cannot possibly be "claiming a created ticket" in the sense
    # hard
    # constraint #3 targets — even if the wording happens to match the vocabulary. A turn calling NO
    # tool at all (`_has_tool_call_this_turn=False`, pure hallucination) is STILL caught — no
    # loosening
    # in that direction, only narrowing exactly the direction that just exposed a false positive.
    #
    # ⚠️ A DECLARED TRADE-OFF: in theory, a turn calling a DIFFERENT tool (e.g. lookup) and THEN
    # independently fabricating "I've also created a ticket" in the same reply would NO LONGER be
    # caught
    # by this gate. Accepted because ALL THREE real false positives that night fit exactly the
    # pattern
    # "called another tool, didn't propose creating a ticket" — NOBODY has measured a
    # hallucination-with-another-tool case yet — and MT-Z01 (the original case that gave birth to
    # RB3),
    # re-checked by the review, STILL has an orphaned `create_ticket` in its raw tool_calls, so it
    # is
    # still correctly caught by the new gate.
    _has_tool_call_this_turn, _has_ticket_proposal_this_turn = _has_ticket_proposal(turn_messages)
    _only_non_ticket_tools = _has_tool_call_this_turn and not _has_ticket_proposal_this_turn
    if ticket_id is None and not _only_non_ticket_tools and claims_ticket_created(filtered_reply):
        _logger.error(
            "agent_khai_tao_ve_khong_co_ve",
            extra={"user_id": user_id, "thread_id": thread_id or user_id,
                   "so_goi_mo_coi": orphan_call_count, "model": answering_model},
        )
        matched_group = list(matched_group) + ["RB3"]
        filtered_reply = _TICKET_NOT_CREATED_REPLY

    # ── 🔴 FORCED-LOOKUP-FIRST GATE (CTC1) ──────────────────────────────────────────
    # Measured by the PO: prompt.py already instructs it 3 times, in caps, with a WRONG example as
    # the
    # villain (lines 15, 17-18, 41 — "call get_customer_history IMMEDIATELY on the first message if
    # there's no transaction ID/phone, DON'T ask the customer first") — the model still skipped it
    # in
    # 29/180 cases. INSTRUCTING via the prompt has run out of room; the move is to ENFORCE it at the
    # code layer, the same principle as the deterministic gates above
    # (_TICKET_NOT_CREATED_REPLY/⑧/⑨).
    #
    # The condition has ONLY two parts, deliberately simple (the first version also required the
    # sentence to contain an amount/recipient name/time anchor — WITHDRAWN, because measured on the
    # real target group, 12/29 customers only described the PROBLEM ("charged twice", "tapped the
    # wrong
    # recipient in my contacts") and gave no identifying details at all — the narrow condition
    # missed
    # 41%. get_customer_history needs nothing more from the customer and can be called right away
    # with
    # just the user_id, so there is no good reason NOT to call it on the first complaint message):
    #   prev_len == 0        — the FIRST message of this thread (already computed at the start of
    #                           run_agent_turn, reused, not guessed).
    #   not tool_calls_out   — the agent hasn't called any tool this turn.
    #
    # ① SAFE WHEN UNSURE: called through EXACTLY the tool wrapper the LLM uses
    # (build_customer_tools()["get_customer_history"].invoke(...)), NOT the raw function in
    # src/tools/get_customer_history.py — inheriting INTACT the OTP-freshness check
    # (OTP_VIEW_MAX_MINUTES) + PII masking of the real LLM path. So this gate CANNOT violate
    # Constraint
    # #4 itself even with a bug here: with an expired/missing OTP the tool returns `status:
    # "error"`,
    # and the branch below treats it as UNSURE and skips — NEVER inventing an answer from data it
    # doesn't have.
    #
    # ② RECORDED IN THE MEASUREMENT RESULT, not just logged: exactly one element is added to
    # `tool_calls_out` (the same {"tool_name","args","result"} shape as a real tool call — because
    # it
    # IS a real tool call, only differing in who decided to make it) and a "CTC1" code to
    # `matched_group` — both already flow straight into `_res_final["tool_calls"]`/
    # `_res_final["loc_dau_ra"]` below, with nothing else to change there.
    #
    # ④ DOES NOT touch create_ticket: this branch has exactly ONE tool call
    # (get_customer_history), and no branch leads to another tool — it can't accidentally hasten
    # case
    # creation.
    if prev_len == 0 and not tool_calls_out:
        try:
            _gate_tools = {
                t.name: t for t in build_customer_tools(
                    session, user_id=user_id, otp_verified_at=otp_verified_at,
                    guard=guard, thread_id=thread_id or user_id,
                )
            }
            _gate_args = {"days": 90, "limit_transactions": 20}
            _result_gate = _gate_tools["get_customer_history"].invoke(_gate_args)
        except Exception:  # noqa: BLE001 — ① when unsure, don't block; an error in the
            # gate must never break a chat turn that already has a valid reply from the model.
            _logger.exception(
                "cong_tra_truoc_loi_khi_goi_tool",
                extra={"user_id": user_id, "thread_id": thread_id or user_id},
            )
            _result_gate = None
        if isinstance(_result_gate, dict) and _result_gate.get("status") != _TOOL_ERROR_STATUS:
            tool_calls_out = list(tool_calls_out) + [{
                "tool_name": "get_customer_history",
                "args": _gate_args,
                "result": _result_gate,
            }]
            matched_group = list(matched_group) + ["CTC1"]
            filtered_reply = _gate_reply_before_lookup(_result_gate)

    # ── 🔴 ADR-057 · EARLY HANDOFF for the "expensive tier" (CD1) ────────────────────
    # 🔴 THE BOUNDARY (read before editing): this is a DETERMINISTIC rule at the SERVICE LAYER — the
    # AI
    # decides NOTHING; it still only investigates and answers as before. This branch may do EXACTLY
    # ONE
    # thing: raise the handoff-suggestion flag (`goi_y_handoff`, which already exists — ES-xx; the
    # frontend renders a "talk to a human" button itself; the system only SUGGESTS). NEVER call
    # create_ticket/request_human_handoff, never change should_escalate itself
    # (reserved for FS-06 — test_fraud_policy_chi_dinh_tuyen_khong_phan_quyet).
    # Teaching the AI "hand off when it finds things hard" would be the AI ESCALATING ITSELF,
    # violating
    # hard constraint #2 — this does NOT do that: the condition reads directly from the DB
    # (Complaint.type/trans_id); the model is not asked to interpret what "hard" means.
    #
    # The condition — machine-readable, no model cooperation needed:
    #   complaint_type ∈ {refund, wrong_recipient}   (the expensive tier, see ADR-057)
    #   AND turns spent in this state ≥ N             (_ESCALATION_HANDOFF_TURNS)
    #   AND the transaction is not yet identified     (Complaint.trans_id IS NULL)
    #
    # The Complaint is LOOKED UP VIA `thread_id`, not via the local `ticket_id` variable above —
    # `ticket_id` is only non-None if THIS TURN just created a ticket; an unfinished expensive-tier
    # complaint was usually created on an EARLIER turn.
    _hit_tid = thread_id or user_id
    _complaint_hit = session.scalars(
        select(Complaint)
        .where(Complaint.thread_id == _hit_tid)
        .order_by(Complaint.created_at.desc())
        .limit(1)
    ).first()
    needs_escalation_handoff = False
    if (
        _complaint_hit is not None
        and _complaint_hit.type in _ESCALATING_COMPLAINT_TYPES
        and _complaint_hit.trans_id is None
    ):
        _turn_hit = incr_signal(_SIGNAL_ESCALATION_TURNS, _hit_tid)
        if _turn_hit >= _ESCALATION_HANDOFF_TURNS:
            needs_escalation_handoff = True
            matched_group = list(matched_group) + ["CD1"]

    # ⑧ · K3 — inserted AFTER the filter. See the comment on `_add_impersonation_warning` for why it
    # must NOT be moved earlier.
    filtered_reply = _add_impersonation_warning(
        filtered_reply, has_otp_error=has_otp_error_in_turn, ticket_id=ticket_id
    )

    # ⑨ · K2 — THE SCAM-SCREENING QUESTION, deterministic, 0 tokens.
    # The firing condition is READ AT THIS LAYER, not left to the model: the ticket just created has
    # `complaint_type == "wrong_recipient"`, and the thread has never been asked.
    # The expert requires it in EVERY wrong-transfer case — including obvious-looking ones, because
    # the obvious ones are exactly the ones that get skipped.
    # Inserted AFTER the filter, for the same reason as ⑧ (see the comment on
    # `_add_impersonation_warning`).
    # 🔴 HOOK MOVED 25/08 — the first version fired on `ticket_id is not None`, i.e. it could only
    # fire
    # AFTER `create_ticket` returned. In the expert script the ticket is created between turns 7 and
    # 8
    # ⟹ the screening question appeared on TURN 8, while the expert places it on TURN 4. A 4-turn
    # gap, and in exactly the dangerous direction: the customer had already heard ALL the
    # wrong-transfer advice on turns 5-6 before being asked whether they were scammed.
    # I chose the spot that was EASY TO MEASURE (`create_ticket` is the only place the code layer
    # knows
    # `complaint_type` for sure), not the RIGHT TURN. Ticket ⑨ says "ask in EVERY wrong-transfer
    # case"
    # — it says WHETHER to ask, not WHERE; the 5 spec axes also score "was it asked", so no gate
    # caught
    # the 4-turn error.
    #
    # 🔴 THE TURN-8 BRANCH WAS DROPPED ENTIRELY, not kept alongside (the PO's hard condition): asking
    # the
    # customer the same question TWICE breaks things in another way, and it WOULD SLIP PAST every
    # existing gate since they all score "was it asked".
    #
    # LOCATING TURN 4: read the signals of EARLIER turns first, then write this turn's signal (order
    # matters). The turn that finds the transaction only WRITES the signal; the following turn asks
    # ⟹ exactly turn 4, not turn 3.
    _slot_tid = thread_id or user_id
    if is_wrong_transfer_case(message):
        incr_signal(_SIGNAL_WRONG_TRANSFER_CASE, _slot_tid)
    _already_found = read_signal(_SIGNAL_TXN_FOUND, _slot_tid) not in (None, 0)
    if (
        _already_found
        and read_signal(_SIGNAL_WRONG_TRANSFER_CASE, _slot_tid) not in (None, 0)
        and read_signal(_SIGNAL_SCREENING_ASKED, _slot_tid) == 0
    ):
        incr_signal(_SIGNAL_SCREENING_ASKED, _slot_tid)
        filtered_reply = (filtered_reply.rstrip() + "\n\n" + ASK_SCAM_SCREENING).strip()
    # Written AFTER the check above — writing first would make the found-it turn satisfy the
    # condition itself and the question would land on turn 3 (in the same message as the 5-fact
    # read-back), also breaking R1 "one idea per message".
    if not _already_found:
        _found_results = next(
            (
                c["result"] for c in tool_calls_out
                if c.get("tool_name") == "lookup_transaction"
                and isinstance(c.get("result"), dict)
                and c["result"].get("status") == "found"
            ),
            None,
        )
        if _found_results is not None:
            incr_signal(_SIGNAL_TXN_FOUND, _slot_tid)
            # GATE item 4 — store the trans_id AS SOON AS it is known, so the asking turn (⑨ above,
            # the
            # same turn or the next) and the answer-receiving turn (PIECE 4, at the start of this
            # function)
            # match EXACTLY the same transaction. Overwriting an old trans_id when the thread has a
            # SECOND
            # wrong-transfer case found BEFORE the first finished its question-answer round is
            # acceptable: ⑨
            # only asks ONE question per turn (R1), so this situation is rare, and the overwritten
            # case can
            # still look itself up again (`_already_found` is already 1, `lookup_transaction` isn't
            # called
            # again) — no transaction is lost; at worst a screening answer gets attributed to the
            # other case
            # once, and it corrects itself on that case's next asking turn.
            _newly_found_trans_id = _found_results.get("trans_id")
            if _newly_found_trans_id:
                store_value(_SIGNAL_TRANS_ID_PENDING_SCREENING, _slot_tid, _newly_found_trans_id)
    instruction_leak_result = instruction_leak_signal(reply, thread_id=thread_id or user_id)
    _res_final = {
        "reply": filtered_reply,
        "tool_calls": tool_calls_out,
        # Phase 3 (876a240) — the model that REALLY ANSWERED (not the constant LLM_MODEL) + EVERY
        # model
        # tried this turn in order, including attempts the provider rejected (providers bill FAILED
        # attempts
        # too — the "invoice reconciliation evidence" must record them all, not just the final
        # model).
        "model": answering_model,
        "models_da_thu": list(tried_models),
        "ticket_id": ticket_id,
        "should_escalate": should_escalate,
        "usage": usage,
        # FOUR DIAGNOSTIC fields (`tin_hieu_lo_chi_thi` — instruction-leak signal — added in Rule
        # 18).
        # Not a convenience: eval produces NOT A SINGLE log line (the runner calls the graph
        # directly,
        # logging_config is never initialised) and Redis is per-process fakeredis — so the filter's
        # logs +
        # counters are INVISIBLE to whoever is measuring. Without them O1/O3/O4 all produce the same
        # identical safe sentence, exactly the "two states wearing one shell" family; and before
        # Rule 18,
        # listing density was even worse — not just invisible but NEVER computed on the real path.
        "loc_dau_ra": matched_group,
        "tin_hieu_lo_chi_thi": instruction_leak_result,
        # ES-xx -> the FRONTEND renders a "talk to a human" button. It does NOT call
        # request_human_handoff itself: the decision to talk to a human belongs to the CUSTOMER
        # (CTRL-001 / ISO-IEC 25059); the system only SUGGESTS.
        # ADR-057 (CD1) ORs into EXACTLY this existing flag — no new flag, no new path, just ONE
        # more reason
        # for the system to suggest a human.
        "goi_y_handoff": bool(emotion_signal) or needs_escalation_handoff,
        "duong": ROUTE_FULL,
        "ly_do_fallback": None,  # EXPLICITLY null, NOT a missing key — a missing key
        # can't be distinguished from "an old version without this field".
        **_raw_reply_for_eval(reply, matched_group),
    }
    _write_ledger(_res_final, thread_id, user_id)
    return _res_final
