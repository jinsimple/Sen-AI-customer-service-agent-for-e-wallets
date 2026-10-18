"""Chat-turn triage — a BINARY decision: does this turn need the full toolkit?

Behind the `TRIAGE_ENABLED` flag, **OFF by default**. When off, `run_agent_turn` behaves
exactly as it did before this file existed.

═══ WHY RULES, NOT A MODEL ═══════════════════════════════════════════════

`semantic-router` + a local encoder were evaluated. Measured (17/08): greenfield
~609MB, of which `litellm` is **115M** — a gateway to 100+ LLM providers of which we use not
a single line — all to do one thing: **compare the cosine of two vectors**. The current
product image's `site-packages` is **892M**, so ~473M (without semantic-router) would still
be **+53%**. The real PO rejected it.

Pure rules: **0 bytes of dependencies · 0 tokens · 0 models · 0 cold start**. And it is the
ONLY approach that can be evaluated at no cost.

═══ THREE PRINCIPLES ═════════════════════════════════════════════════════

**① AN ALLOWLIST, not a denylist.** Go light ONLY IF **every** token belongs to the closed set
`SMALL_TALK`; a single unknown token ⟹ full.

The two kinds of list fail in **opposite directions**: an incomplete DENYlist ⟹ real
complaints get missed. An incomplete ALLOWlist ⟹ one simple turn is lost, a few extra tokens
spent, **nobody is left behind**. The same principle applied to `DIALABLE` and to secret
masking.

**② NO length clause.** The draft had `DAI_TOI_DA=40` (max length). Measured: removing it
entirely, the 124-sentence negative set **still blocks 124/124**, and the 21 cases that used
to rely on length alone were now blocked by the allowlist — i.e. for **the right reason**. An
arbitrary constant carrying 17% of the cases is something somebody will raise to 60 for a
plausible-sounding reason, and `124/124` would stay green until then.

**③ HAS DIGITS ⟹ full, unconditionally.** Money, transaction IDs, phone numbers, dates and
times — everything worth looking up carries digits. Wrongly routing `"cảm ơn 1000 lần"`
(thanks a thousand times) is accepted; over-blocking is cheaper than missing. This is also
the clause that catches `"mất 500k"` (lost 500k — 8 characters, a complaint) — the case that
kills every "short ⟹ simple" rule.

═══ HARD BOUNDARIES ══════════════════════════════════════════════════════

**This layer does NOT make business decisions.** It only answers *"does this turn need the
full toolkit"*. It must **never** answer the customer on any business matter itself.

**The light path creates NO business records.** If a turn needs to create a record, it is by
definition not a simple turn, and the fact that it took the light path is **proof of
misclassification**. A measurable invariant: `light path ⟹ Δcomplaints = Δtickets = 0`.

**Classify PER TURN, not PER SESSION.** A customer types `"alo"` (hello) and only in the next
message says they lost money — that next message must go full. No state is remembered between
turns.

**Fail safe = when in doubt, go FULL.** Only go light when it can be POSITIVELY confirmed as
simple; everything else — errors, empty messages, unknown tokens — goes full.
"""
from __future__ import annotations

import hashlib
import logging
import re
import unicodedata
from pathlib import Path

_logger = logging.getLogger("fin05.phan_luong")

ROUTE_LIGHT = "nhe"
ROUTE_SLOT_FILL = "thu_slot"
ROUTE_FULL = "day_du"

# Redis signal name (thread_signals.py) marking "has the slot question been asked yet"
# in this conversation — items 5+6 of design 1B: the gate may fire AT MOST ONCE per
# conversation, read/written at the CALLING LAYER (graph.py), not here —
# triage.py is a PURE function (no side effects), in line with the "zero state" principle
# throughout this module.
SIGNAL_1B_SLOT_ASKED = "1b_da_hoi_slot"

# Closed set of small-talk tokens. ONLY extend it when a REAL case appears, never in
# anticipation — every token added is a place a real complaint could slip through.
SMALL_TALK = {
    "alo", "a lô", "alô", "hello", "hi", "hey", "chào", "xin chào", "chao",
    "ê", "e", "ơi", "oi",
    "shop", "chị", "chi", "anh", "em", "bạn", "ban", "ad", "admin", "cskh",
    "bot", "ạ", "a", "nhé", "nhe", "nha", "với", "voi",
    "cảm ơn", "cam on", "cám ơn", "thanks", "thank", "tks", "ok", "oke", "okay",
    "được", "duoc", "rồi", "roi", "vâng", "vang", "ừ", "u", "dạ", "da",
    "tạm biệt", "tam biet", "bye", "goodbye",
    "à", "ừm", "hmm", "haha", "hihi", "^^", ":)", ":d",
}
_PHRASES = sorted((c for c in SMALL_TALK if " " in c), key=len, reverse=True)

_HAS_DIGIT = re.compile(r"\d")
_PUNCTUATION = re.compile(r"[.,!?;:~\-_/\\\"'()\[\]{}…]+")

# Light-path replies. CONSTANTS at the code layer, NOT model-generated — the whole point of
# this path is not calling a model. DELIBERATELY says nothing about any business matter, only
# opens the conversation and invites the customer to describe their issue.
LIGHT_REPLIES = (
    "Dạ mình nghe ạ! Bạn cho mình biết mình có thể hỗ trợ gì cho bạn nhé — "
    "nếu có vấn đề với giao dịch nào, bạn kể giúp mình chi tiết ạ."
)

# ═══ 1B — DETERMINISTIC SLOT-COLLECTION GATE (docs/giao-viec/2026-08-24-luong-chatbot-1A-1B.md) ═══
#
# GROUP B — (i) POSSESSIVE/PERSONAL + TRANSACTION VERB (already happened) + A MINIMAL
# COMPLAINT SIGNAL (added 24/08 after the review caught a false trigger on "tôi chuyển khoản thì
# phí bao nhiêu" — "if I transfer, how much is the fee" — possessive+verb isn't enough; policy
# questions match too), OR
# (ii) "mất"/"bị mất"/"bị trừ" (lost/charged) IMMEDIATELY BEFORE an amount pattern (one
# direction only — PO-agent correction 24/08: both directions would falsely catch "...20k thì
# mất phí gì?" — "is there a fee for 20k?" — since "20k" is only one word away from "mất" in
# the reverse direction).
_POSSESSIVES = ("tôi", "toi", "của tôi", "cua toi", "mình", "minh",
           "tài khoản tôi", "tk tôi", "bên tôi", "ben toi")
_TXN_VERBS = ("chuyển", "chuyen", "bị trừ", "bi tru", "trừ tiền", "tru tien",
               # ③ (24/08) — "nhận"/"nhan" (receive) REMOVED from here: it matches inside
               # "xác nhận" (confirm) (case DOT2-AM-04 = ADV-038 verbatim, "xác nhận
               # cho tôi chắc chắn đi" — confirm it for me for sure), and every real COMPLAINT sense
               # of
               # "nhận" already exists in `_COMPLAINT_SIGNALS` as sufficiently long phrases
               # ("chưa nhận"/"không nhận" — not yet received / didn't receive). Removing it here
               # loses no
               # recognition ability — it only removes one spot of random matching.
               "gửi", "gui", "rút", "rut", "nạp", "nap",
               "thanh toán", "thanh toan")
_LOSS_ANCHORS = ("mất", "mat", "bị mất", "bi mat", "bị trừ", "bi tru")

# 🔴 False trigger caught in review 24/08 (running triage() for real, not by static reading):
# "tôi chuyển khoản thì phí bao nhiêu vậy" (how much is the fee if I transfer) / "tôi cần rút
# tiền, thủ tục thế nào" (I need to withdraw, what's the procedure) — they HAVE
# possessive+transaction verb but are POLICY/PROCEDURE questions, not complaints. The
# PO-approved spec: "policy questions must never trigger the gate". Fixed by TIGHTENING THE
# ENTRY CONDITION (a minimal complaint signal is now mandatory), NOT by listing exception words
# (fee/procedure/regulation...) — an exclusion list is always one word short, while a strict
# entry condition fails in the agreed direction (better to miss than to falsely catch).
# "sao"/"mất" are DELIBERATELY ABSENT even though the old ANCHOR example ("sao mất tiền vậy" —
# why did I lose money) uses them — [MEASURED] the Tester added cases after the first fix:
# "...thì làm sao" (what should I do — a procedure, not a complaint; "sao" matches randomly in
# "làm sao"/"thế nào", very common neutral question phrases) and "...thì mất bao lâu" (how long
# does it take — asking about DURATION, "mất" meaning "take" not "lose money") were both falsely
# caught while these two words were still in the list. A real "mất tiền" is still caught
# separately by GROUP B(ii) (mất adjacent to an amount pattern) — no recognition lost, only
# less ambiguity.
# ③ ("OTP before token" ticket, 24/08) — BARE "bị"/"bi"/"nhầm"/"nham" were REMOVED.
# All four are SUBSTRINGS of far too many non-complaints ("bị" in "bị lừa đảo đúng không" = a
# question; "nhầm" in "Nếu lỡ chuyển nhầm... thì" — "if I accidentally transfer wrongly...
# then" = a policy question). Replaced with SUFFICIENTLY LONG PHRASES — TIGHTENING THE ENTRY
# CONDITION, NOT adding an exclusion list (the rule just above forbids it: an exclusion list is
# always one word short).
#
# [MEASURED] the added phrases were chosen by CONSTRAINTS, not gut feeling — this is the
# smallest set that keeps all three known positive cases:
#   "tôi bị trừ tiền"                                 needs "bị trừ"
#   "mình chuyển nhầm cho người lạ, không nhớ gì cả"  needs "chuyển nhầm"
#   "tôi chuyển nhầm tiền cho người lạ rồi..."        needs "chuyển nhầm"
# ⑨-turn-4 (25/08) — eight phrases SPECIFIC to the wrong-transfer case were SPLIT OUT. Before
# this version they were mixed into `_COMPLAINT_SIGNALS`, and `_group_b()` would match and then
# THROW AWAY which phrase matched, keeping only `True`. The data passed through the function and
# was discarded — it wasn't that it didn't exist. Split out so the calling layer can ask "is
# this a wrong-transfer case" WITHOUT a model, WITHOUT spending tokens.
#
# [MEASURED 25/08, eval corpus, denominator = CLASSIFIED cases] these eight phrases SEPARATE
# CLEANLY:
#   double_charge 0/26 · money_not_received 0/52 · refund 0/35
#   ⟹ outside `wrong_recipient`: 0/113 = 0.00%   (threshold fixed by the PO BEFORE measuring: ≤5%)
#   forward direction: wrong_recipient 19/36 = 52.8%
# 🔴 DECLARED LIMITATION, don't read 0.00% more broadly than it deserves: it says "the eight
# phrases DO NOT appear in other types", NOT "any phrase match means a wrong transfer". 17/36
# wrong-transfer cases contain NONE of the phrases ⟹ ~53% coverage, the rest falls back to the
# old behaviour. DELIBERATE, not an omission. And the corpus is GENERATED DATA — real customers
# write more diversely.
_WRONG_TRANSFER_PHRASES = ("chuyển nhầm", "chuyen nham", "gửi nhầm", "gui nham",
                    "nhầm người", "nham nguoi", "chuyển sai", "chuyen sai")

_COMPLAINT_SIGNALS = ("lỗi", "loi",
                       "bị trừ", "bi tru", "bị mất", "bi mat",
                       *_WRONG_TRANSFER_PHRASES,
                       "chưa nhận", "chua nhan", "không nhận", "khong nhan",
                       "chưa thấy", "chua thay", "không thấy", "khong thay",
                       "chưa tới", "chua toi", "chưa về", "chua ve")

# Caught by the PO-agent 24/08, running the gate on HEAD themselves: "Tôi lo quá, chuyển nhầm
# tiền học phí của con cho người lạ rồi, giúp tôi với." (I'm so worried, I sent my child's
# tuition to a stranger by mistake, please help) — the hardest case the gate could meet. A
# 0-token gate has no ability to reassure, while prompt.py:21 REQUIRES the first sentence to
# reassure before stating lookup results — the deterministic gate would BYPASS exactly that
# rule. Strong emotion signal ⟹ GO day_du (full), let the LLM handle it (it can reassure; a
# deterministic gate cannot) — same spirit as "better to miss than to falsely catch", only on a
# different axis (emotion instead of policy). No "approximate" threshold (e.g. bare "lo"/"sợ"
# — worry/fear — which easily match inside other words) — sufficiently long phrases are used
# so it is NOT ambiguous.
_STRONG_EMOTION_SIGNALS = ("lo quá", "lo qua", "hoảng", "hoang", "sợ quá", "so qua",
                          "gấp lắm", "gap lam", "khẩn cấp", "khan cap",
                          "giúp tôi với", "giup toi voi", "giúp em với", "giup em voi",
                          "giúp mình với", "giup minh voi", "làm sao bây giờ", "lam sao bay gio",
                          "cứu tôi", "cuu toi", "cứu với", "cuu voi")

_re_word = lambda word: re.compile(r"\b" + re.escape(word) + r"\b")  # noqa: E731
_RE_POSSESSIVE = [_re_word(t) for t in _POSSESSIVES]
_RE_TXN_VERBS = [_re_word(t) for t in _TXN_VERBS]
_RE_COMPLAINT_SIGNALS = [_re_word(t) for t in _COMPLAINT_SIGNALS]
_RE_STRONG_EMOTION_SIGNALS = [_re_word(t) for t in _STRONG_EMOTION_SIGNALS]


def _has_strong_emotion(s: str) -> bool:
    return any(p.search(s) for p in _RE_STRONG_EMOTION_SIGNALS)


# Caught in review 24/08: "tôi bị trừ hai trăm bảy mươi nghìn" (I was charged two hundred
# seventy thousand) → thu_slot (slot collection), and the gate asked back "cho mình xin số tiền"
# (please tell me the amount) RIGHT AFTER the customer had just said the amount — in WORDS, not
# digits. `extract_slots()` (item 3.1) DELIBERATELY doesn't parse spelled-out numbers (stated
# clearly in its docstring, not a new hole) — but the NEW consequence: the gate made things
# WORSE than having no gate, because it BLOCKS AHEAD OF the LLM (which can read "hai trăm bảy
# mươi nghìn") with a cruder filter.
#
# CHEAP fix — NO spelled-number parser is built (we don't need the VALUE, only whether "the
# customer may have stated an amount", then DEFER to the LLM, per "better to miss than to
# falsely catch"). Condition: a unit (trăm/nghìn/ngàn/triệu/tỷ — hundred/thousand/million/
# billion) RIGHT NEXT TO a number word (một/hai/.../mười/mươi/lẻ — one/two/.../ten) — same
# "sufficiently long phrase" lesson: the unit MUST be adjacent to a number word; "nghìn" alone
# in "cảm ơn nghìn lần" (thanks a thousand times) doesn't trigger.
#
# 🔴 FIXED 24/08, PO-agent — the first version DELIBERATELY excluded "nửa"/"rưỡi" (half/and a
# half) to avoid conflicting with corpus case S4 ("tôi chuyển nửa triệu hôm qua..." — I sent
# half a million yesterday → thu_slot). The PO-agent re-read S4 and reversed it: the corpus
# ITSELF stated the problem in `vi_sao` (why) ("MISSING although the customer HAD SAID it") and
# then recorded it as the CORRECT expectation — a test case recording WRONG behaviour as the
# standard, born from the 1B spec ("extract by regex" can't read spelled-out Vietnamese), not
# from misreading code. For the customer, "nửa triệu" is the amount they JUST SAID — asking
# again is just as annoying as with "hai trăm bảy mươi nghìn". The settled principle: the
# deterministic gate has NO business judging whether the customer's number is PRECISE enough
# (estimates/rounding/approximations are something the LLM handles better) — it only answers
# "does this sentence show signs that the customer stated an amount?", and if so, DEFERS. The
# Tester fixed S4's `ky_vong` (expectation) + added cases to the corpus.
_NUMBER_WORDS = ("một", "mot", "hai", "ba", "bốn", "bon", "năm", "nam", "sáu", "sau",
              "bảy", "bay", "tám", "tam", "chín", "chin", "mười", "mươi", "muoi", "lẻ", "le",
              "nửa", "nua", "rưỡi", "ruoi")
_NUMBER_WORD_UNITS = ("trăm", "tram", "nghìn", "nghin", "ngàn", "ngan", "triệu", "trieu", "tỷ", "ty")


def _has_spelled_number(s: str) -> bool:
    word = s.split()
    for i, t in enumerate(word):
        if t not in _NUMBER_WORD_UNITS:
            continue
        if (i > 0 and word[i - 1] in _NUMBER_WORDS) or (i + 1 < len(word) and word[i + 1] in _NUMBER_WORDS):
            return True
    return False


# Amount pattern (item 3.1) — ONLY numbers written in digits + an optional unit. Numbers
# written PURELY IN WORDS ("năm trăm nghìn", "nửa triệu" — five hundred thousand, half a
# million) are DELIBERATELY not parsed — stated clearly, no attempt to guess (a separate scope
# if ever needed, not mixed into 1B).
_AMOUNT_RE = re.compile(
    r"\d[\d.,]*\s*(k|nghìn|nghin|ngàn|ngan|tr|triệu|trieu|đ|d|vnd|vnđ)?", re.IGNORECASE
)

# Time-anchor pattern (item 3.2) — absolute dates, clear relative anchors, days of the
# week (assuming the MOST RECENT week). Genuinely vague anchors that don't attach to any phrase
# above (e.g. "dạo này", "gần đây" — lately, recently) DELIBERATELY don't match — the slot is
# treated as MISSING, no inference.
#
# 🔴 FIXED 24/08 (PO-agent, discovered while verifying another fix):
# the previous version listed "mấy hôm trước" (a few days ago) as an example of a
# vague-anchor-deliberately-not-matched — WRONG. That phrase contains "hôm trước" (the other
# day) verbatim (already in the regex), so it HAD IN FACT been matching all along — not a
# regression of any fix. A documentation line contradicting real behaviour — fix the TEXT here,
# KEEP the behaviour (regex unchanged), because the current behaviour is SAFER than the old
# docstring described:
#   matches        ⟹ the gate does NOT ask, defers to the LLM (the LLM can still ask back, more
#                    skilfully, having the whole conversation's context) = one missed chance
#                    to ask, CHEAP
#   doesn't match  ⟹ the gate asks again although the customer HAD given a time direction =
#                    a false catch, exactly what was fixed twice that day (spelled-out
#                    amounts, time of day)
# DO NOT "fix it to match the old docstring" (adding a condition excluding "hôm trước" after
# "mấy") — that would reopen a false-catch case already closed.
#
# 🔴 Caught in review 24/08 (checking a663583, the T0 gate after OTP): this very GATE (and
# R5/1A) TEACHES customers to answer with "sáng/chiều/tối" (morning/afternoon/evening) combined
# with "nay"/"qua" (today/yesterday) (T0's deterministic question: "...or the transaction time
# (today/yesterday, morning/afternoon/evening)..."), but the regex ONLY had "hôm nay"/"hôm qua"
# — customers answering EXACTLY in the format the system taught ("sáng nay" — this morning,
# "tối qua" — last night) were NOT recognised. Same bug family as "1B teaches the customer to
# state the amount, the customer says 'nửa triệu', the gate doesn't recognise it"
# (d9e53ae/2dd5c3e) — a different domain (time instead of amount).
#
# SUFFICIENTLY LONG PHRASES, not bare "nay"/"qua" — the same lesson "sao"/"mất" (1B) paid for:
# "qua" is a substring of "quá" (too), "qua lại" (back and forth), "thông qua" (via); bare
# "nay" is lower risk but the same compound-phrase pattern is kept for consistency and
# readability.
_TIME_RE = re.compile(
    r"\d{1,2}[/-]\d{1,2}([/-]\d{2,4})?"
    r"|ngày\s*\d{1,2}\s*tháng\s*\d{1,2}"
    r"|hôm nay|hom nay|hôm qua|hom qua|hôm kia|hom kia|hôm trước|hom truoc"
    r"|sáng nay|sang nay|chiều nay|chieu nay|tối nay|toi nay"
    r"|sáng qua|sang qua|chiều qua|chieu qua|tối qua|toi qua"
    # 🔴 Đ3 ("OTP before token" ticket ⑦, 24/08) — the two patterns below were MISSING, as
    # measured: T0 asked again for exactly what the customer had just said 2/8 times, and "tuần
    # trước" (last week) / "khoảng 3 giờ chiều" (around 3 pm) were those two cases. Same bug family
    # as the comment block right above (the system TEACHES a format and then can't read it).
    #
    # "tuần trước": a 2-word phrase with no other meaning in Vietnamese ⟹ safe.
    # "2 tuần trước"/"mấy tuần trước" (2/a few weeks ago) match automatically because they CONTAIN
    # the phrase. Lead approved 24/08 after the Coder presented measurements: the three phrases
    # below have EXACTLY the same bug shape as "tuần trước" (all measured = False), the same safety
    # (2-word phrases with no other meaning in Vietnamese). Added in the same round rather than
    # leaving the next round to rediscover them from scratch.
    r"|tuần trước|tuan truoc|tuần rồi|tuan roi"
    r"|tháng trước|thang truoc|tháng rồi|thang roi"
    # "<number> giờ|h + sáng/chiều/tối/trưa/đêm" (o'clock + morning/afternoon/evening/noon/
    # night) — the time of day is MANDATORY; a bare "3 giờ" is not accepted: "3 giờ" alone is also
    # a DURATION ("đợi 3 giờ đồng hồ" — waited 3 hours), not an anchor. The same "sufficiently long
    # phrase" lesson "sao"/"mất" (1B) paid for — better to MISS than to FALSELY CATCH.
    r"|\d{1,2}\s*(giờ|gio|h)\s*(sáng|sang|chiều|chieu|tối|toi|trưa|trua|đêm|dem)\b"
    r"|thứ\s*[2-7]\b|thu\s*[2-7]\b|t[2-7]\b"
    r"|thứ\s*(hai|ba|tư|tu|năm|nam|sáu|sau|bảy|bay)\b|thu\s*(hai|ba|tu|nam|sau|bay)\b",
    re.IGNORECASE,
)

# Code pattern (item 3.3) — NOT mandatory, only recorded if present, does NOT gate
# routing. Transaction ID format confirmed against scripts/gen_dataset.py:135-138 (TXN +
# 8 date digits + 6 sequence digits = 14 digits). Ticket codes MUST match BOTH real shapes:
# `TCK-\d{5}` (scripts/gen_dataset.py:152-153, seed/demo data) AND
# `TCK-[0-9a-f]{12}` (src/tools/base.py::new_id, tickets REALLY created during chat) — the two
# ID generation paths produce different shapes (checked against the real runtime before
# writing, not just reading gen_dataset.py as the original draft quoted) — missing either branch
# means tickets created in the very chat session would never be recognised again.
#
# `\s*` between the prefix and the digits (review 24/08): "TXN 20260810000123" (typed/pasted
# with a space) used to slip through because the regex demanded strict adjacency.
_TXN_CODE = re.compile(r"\bTXN\s*\d{14}\b", re.IGNORECASE)
_TICKET_CODE = re.compile(r"\bTCK-(?:\d{5}|[0-9a-f]{12})\b", re.IGNORECASE)


# ── ③ ROUND 2 · CONDITIONAL FRAME (SENTENCE-MOOD axis) ─────────────────────────────
# Closes DOT2-AM-01 (the policy question "Nếu lỡ chuyển nhầm… thì…" — "If I accidentally
# transfer wrongly… then…").
#
# 🔴 A CLOSED SET, AND TRULY CLOSED. Only conditional conjunctions of Vietnamese grammar — a
# COUNTABLE class of function words, entirely different from topic lists ("phí"/"thủ tục"/
# "quy định"… — fee/procedure/regulation) which the rule above forbids because they are
# "always one word short".
#
# 🔴 "lỡ" is DELIBERATELY ABSENT, even though AM-01 contains it. I DID add it in the round-1
# trial and immediately broke it myself: "lỡ" is an ADVERB ("accidentally"), not a conditional
# conjunction — adding it LOOSENS the closed set, and [MEASURED] it falsely catches two REAL
# complaints:
#     "tôi lỡ chuyển nhầm cho người lạ rồi thì làm sao lấy lại"
#         (I accidentally sent to a stranger, how do I get it back)
#     "tôi lo là chuyển nhầm rồi thì mất luôn à"
#         (I'm worried I sent it wrongly, is it gone?)   (the ASCII "lo " matches "lo là")
# AM-01 is still closed thanks to "nếu" (if) right before it. Don't add it back.
_CONDITIONAL_MARKERS = ("nếu", "neu", "giả sử", "gia su", "trong trường hợp",
                  "trong truong hop")


def _is_conditional_frame(s: str) -> bool:
    """Whether the complaint signal is governed by a CONDITIONAL FRAME.

    Requires ALL THREE, missing one means it doesn't count:
      ① a conditional marker from the CLOSED set `_CONDITIONAL_MARKERS`
      ② a " thì " (then) AFTER that marker — the PAIR is the structure; a lone marker isn't
      ③ that marker comes BEFORE the complaint signal

    🔴 Condition ③ was added in round 3 after I broke my own round-2 version. Without it, a
    conditional clause AFTER the complaint also counts, and [MEASURED] it falsely catches:
        "tôi chuyển nhầm rồi, NẾU không lấy lại được THÌ tôi phải làm sao"
        (I sent it wrongly, IF I can't get it back THEN what do I do)
    — the customer HAS described the event in the main clause; the condition is just an
    accompanying worry.

    ⚠️ LIMITATION MEASURED, NOT FIXED: "nếu vậy thì tôi bị trừ tiền oan à" (so then I was
    wrongly charged?) is excluded (leaning to `day_du`). This sentence is genuinely ambiguous
    — a mid-conversation reaction, and `thu_slot` only fires once per conversation anyway, so
    it almost never gets here. The lean is in the SAFE direction (the LLM handles it).
    Declared rather than adding a fourth rule for one case.
    """
    complaint_position = min(
        (m.start() for p in _RE_COMPLAINT_SIGNALS if (m := p.search(s))), default=None
    )
    if complaint_position is None:
        return False
    for d in _CONDITIONAL_MARKERS:
        i = s.find(d)
        if 0 <= i < complaint_position and " thì " in s[i:]:
            return True
    return False


# ── AM-03 · NO-FIRE LOCK: sentences DEMANDING A THIRD PARTY'S IDENTITY ────────────
# Anchored on NOUNS, NOT on VERBS. The review rejected the request-verb anchor approach
# ("cho tôi xin"/"cho mình biết"/"làm ơn"/"tôi muốn biết"… — give me/let me know/please/I want
# to know) because that is an OPEN set — failing exactly the way the word "mà" failed in the
# 7/7 trial that was rejected.
#
# PII FIELDS are a CLOSED set with an AUTHORITATIVE SOURCE ALREADY: exactly the three things
# `masking.py` masks — full name · phone number · account number. No new concept invented.
#
# Requires BOTH ① a PII field AND ② a third-party marker — regardless of SENTENCE MOOD
# (imperative, question or statement are all caught). "số tài khoản của tôi" (my account
# number) fails ② ⟹ doesn't trigger.
_PII_FIELDS = ("họ tên", "ho ten", "tên đầy đủ", "ten day du", "họ và tên",
               "ho va ten", "tên người", "ten nguoi",
               "số điện thoại", "so dien thoai", "sđt", "sdt",
               "số tài khoản", "so tai khoan", "số tk", "so tk",
               "stk", "thông tin liên hệ", "thong tin lien he")
_THIRD_PARTY_MARKERS = ("người nhận", "nguoi nhan", "người kia", "nguoi kia",
                       "người khác", "nguoi khac", "người ta", "nguoi ta",
                       "người đó", "nguoi do", "người lạ", "nguoi la",
                       "bên nhận", "ben nhan", "chủ tài khoản", "chu tai khoan",
                       "người mà", "nguoi ma", "người tôi", "nguoi toi",
                       "người em", "nguoi em", "người mình", "nguoi minh")


_MARKER_WINDOW = 24  # characters, enough for "của người nhận"/"của chủ tài khoản" (of the recipient/of the account holder)


def _asks_third_party_identity(s: str) -> bool:
    """Does this sentence DEMAND identifying information about SOMEONE ELSE?

    NOT a reclassification — `_group_b` stays as is. This is a NO-FIRE lock:
    a sentence touching a third party's identity must go FULL so that O1–O5 and the
    `masking.py` masking layer run, instead of the 0-token gate returning an off-topic reply.
    """
    for t in _PII_FIELDS:
        i = s.find(t)
        if i < 0:
            continue
        # The marker must come RIGHT AFTER the PII field, within a narrow window — that is how
        # Vietnamese attaches possession ("số điện thoại CỦA NGƯỜI…" — the phone number OF THE
        # PERSON…, "tên NGƯỜI…" — the PERSON's name…).
        # Counting it anywhere would falsely catch "…chuyển nhầm cho NGƯỜI LẠ, không nhớ SỐ TÀI
        # KHOẢN
        # của mình" (…sent to a STRANGER by mistake, don't remember MY ACCOUNT NUMBER): two words
        # close
        # together but NOT belonging together. Near ≠ related.
        # The window counts FROM THE START of the PII field, not the end — because some PII phrases
        # have already SWALLOWED the marker ("tên người" — person's name). Counting from the end,
        # "tên người tôi chuyển nhầm" (the name of the person I sent to) would lose the marker
        # "người tôi" right there.
        after = s[i: i + len(t) + _MARKER_WINDOW]
        if any(c in after for c in _THIRD_PARTY_MARKERS):
            return True
    return False


def _group_b(s: str) -> bool:
    if _is_conditional_frame(s):
        return False
    has_possessive = any(p.search(s) for p in _RE_POSSESSIVE)
    has_verb = any(p.search(s) for p in _RE_TXN_VERBS)
    has_complaint = any(p.search(s) for p in _RE_COMPLAINT_SIGNALS)
    if has_possessive and has_verb and has_complaint:
        return True
    # (ii) one direction: anchor "mất/bị mất/bị trừ" first, then the amount pattern,
    # within a window of ≤2 words RIGHT AFTER the anchor — the reverse direction is not considered.
    word = s.split()
    for anchor in _LOSS_ANCHORS:
        anchor_word_count = len(anchor.split())
        for i, t in enumerate(word):
            if " ".join(word[i : i + anchor_word_count]) != anchor:
                continue
            window = " ".join(word[i + anchor_word_count : i + anchor_word_count + 2])
            if _AMOUNT_RE.search(window):
                return True
    return False


def _normalize_light(s: str) -> str:
    """LIGHT normalisation for slot extraction — ONLY NFC + lowercasing, NO
    `_PUNCTUATION` pass (which `_normalize()` uses for GROUP A/B keyword matching).

    🔴 A REAL BUG caught before reporting: `_normalize()` replaces `/`, `.`, `,`
    with spaces ("26/06" → "26 06", "340.000đ" → "340 000đ") — using it for
    `extract_slots()` meant the date pattern `\\d{1,2}[/-]\\d{1,2}` could NEVER match any
    numeric date, because the `/` was gone before the regex could see it. [MEASURED] running
    the eval/cong_phan_luong.py gate for real on golden_set.jsonl: this bug alone caused most
    of the 47/124 "original negative" cases wrongly reporting `thu_slot` (amount present but
    date reported MISSING although the sentence clearly said "Ngày 26/06"). A separate light
    function for slot extraction, keeping `_normalize()` for keyword matching (GROUP A/B
    behaviour unchanged, only slot-extraction behaviour changed)."""
    return unicodedata.normalize("NFC", s).lower().strip()


def is_wrong_transfer_case(sentence: object) -> bool:
    """Does this sentence show signs of a WRONG-TRANSFER case — deterministic, 0 tokens.

    Used by gate ⑨ (the scam-screening question) so it fires on EXACTLY TURN 4 of the expert
    script, instead of turn 8. See `_WRONG_TRANSFER_PHRASES` for measurements and limits.
    """
    if not isinstance(sentence, str):
        return False
    return any(c in _normalize(sentence) for c in _WRONG_TRANSFER_PHRASES)


def is_personal_complaint(sentence: object) -> bool:
    """Is this sentence a PERSONAL COMPLAINT (GROUP B) — exposes `_group_b` to the calling
    layer, WITHOUT the slot decision.

    Created for the deterministic OTP gate (④, `graph.py`). Separated from `triage()`
    deliberately: `triage()` answers *"which path does this turn take"*; this question
    answers *"does this turn touch personal data"* — two different questions, and merging
    them would force the OTP gate to infer backwards from the `thu_slot`/`day_du` label, which
    changes with slots rather than with personal relevance.

    🔴 INHERITS `_group_b`'s FULL SET OF FALSE CATCHES, measured, declared on the spot:
    [MEASURED 24/08] `bo_ca_am_thu_slot_dot2.json` 2/7 · `bo_ca_ranh_gioi_chinh_sach`
    1/16 · `bo_ca_am_ngan_khong_so` 0/14. Case DOT2-AM-01 (a policy question) is still
    `True` ⟹ it gets blocked by the OTP gate, and that is a **known Q1 violation**, not a
    regression of ④. It closes itself when ③ round 2 (the sentence-mood axis) lands.
    """
    if not isinstance(sentence, str):
        return False
    return _group_b(_normalize(sentence))


def enough_to_narrow(sentence: object) -> bool:
    """Does this sentence already carry enough to NARROW the lookup down to one transaction —
    the slot-collection gate AFTER OTP verification (T0, `graph.py`).

    Exactly ONE of three is enough: a transaction/ticket ID · a time anchor · an amount.

    🔴 CHANGED 25/08 (⑤, "OTP before token" ticket, Q2 decided by the PO). The old name
    `co_ma_giao_dich_hoac_thoi_gian` (has_txn_id_or_time) became WRONG for its behaviour — it
    no longer only checks ID/time. Renamed rather than keeping the old name for convenience: a
    name contradicting behaviour is exactly the bug family just fixed in `9f4d291`.

    TWO changes, in the same direction:
    ① ADD amounts to the recognised set. The gate's question now asks for time + amount (Q2),
      so a customer answering with an AMOUNT must count as having answered. Before this
      version, a customer answering exactly what was asked still got asked again — exactly
      family Đ3 (*the system teaches a format and then can't read it*), just on a different
      axis.
    ② KEEP recognising transaction IDs even though the question NO LONGER mentions them (Q2:
      *drop the txn ID from the question, but still recognise it if the customer volunteers
      it*). Not asking ≠ not reading: a pasted ID is the STRONGEST signal; ignoring it to ask
      again would be obviously foolish.

    A WIDER recognised set ⟹ the gate fires LESS ⟹ leaning to `day_du`. Exactly the "better to
    miss than to falsely catch" direction the module declares — loosening here creates NO new
    false catches, it only reduces asking again for what the customer just said.

    `_has_spelled_number` accompanies `extract_slots()["so_tien"]` to match EXACTLY the
    definition of "the customer stated an amount" that GROUP B(i) uses (line ~449) — without
    it, "nửa triệu" would count as not stated at this gate but stated at the other, i.e. TWO
    definitions of the same thing.
    """
    if not isinstance(sentence, str):
        return False
    s = _normalize_light(sentence)
    if _TXN_CODE.search(s) or _TICKET_CODE.search(s):
        return True
    slot = extract_slots(sentence)
    return slot["thoi_gian"] or slot["so_tien"] or _has_spelled_number(s)


def extract_slots(sentence: object) -> dict[str, bool]:
    """Extract the MANDATORY slots (amount, time) from ONE sentence — NO cross-turn context
    merging (item 5 — merging is the model's job; this layer only reads one sentence at a
    time, per the invariant "classify PER TURN").

    Returns `{"so_tien": bool, "thoi_gian": bool}` (amount, time) — PRESENCE only, no
    extracted values (the real values the customer typed remain intact in the conversation
    history; the model can re-read them on the next turn). `"so_tien"` is the ONLY field used
    to gate/choose the reply template (R1 fixed 24/08 — the gate asks for EXACTLY ONE thing,
    see ASK_MISSING_AMOUNT); `"thoi_gian"` is kept because it is still a meaningful,
    extractable slot, even though NO caller currently consumes it — not deleted, to avoid
    rebuilding the same regex if a later need arises. NEVER raises — non-string input counts
    as missing both (safe: ask or go day_du depending on the caller, no wild guessing)."""
    if not isinstance(sentence, str):
        return {"so_tien": False, "thoi_gian": False}
    s = _normalize_light(sentence)
    return {"so_tien": bool(_AMOUNT_RE.search(s)), "thoi_gian": bool(_TIME_RE.search(s))}


# 🔴 FIXED 24/08 (PO-agent+Lead, after running the real gate exposed an OR/AND
# contradiction — see the discussion history): the ONLY MANDATORY SLOT is the AMOUNT, not the
# pair (amount, time). Basis: expert L3 — "the amount is the STRONGEST search anchor"; with an
# amount, get_customer_history(amount=...) can look it up IMMEDIATELY, and multiple_matches (if
# any) already has its own handling path via the LLM (asking back in the context of the
# candidates) — asking for time FIRST, deterministically, asks for something that may not be
# needed. Time is still EXTRACTED if present (passed along for the model to read), but it is
# NEVER on its own a reason to block/ask. Consequence: the "only time missing" template was
# DELETED — no branch uses it any more.
#
# 🔴 FIXED 24/08, PO-agent — R1 (1A, the CSKH expert's spec, MEASURABLE behaviour):
# "a reply when ≥2 slots are missing contains only ONE information request". `HOI_THIEU_CA_HAI`
# (ask-both, the previous version) asked for THREE things in one message (time + amount +
# transaction ID) — reading it as "not split into two lines, same spirit as R1" was a
# MISREADING: the measurable R1 says "one message, ONE request", not "one message, however many
# requests are bundled". The business spec wins over the token-saving goal when the two clash.
#
# And the settled slot rule (the amount is the ONLY MANDATORY slot; time is never on its own a
# reason to ask) resolves the contradiction itself: the gate has ONLY ONE reason to ask —
# the missing amount — so only ONE template is needed, asking for EXACTLY ONE thing.
# Transaction ID/time are left for the LLM path to ask next under R1 on a later turn if needed.
#
# A DELIBERATE trade-off, not an oversight: asking one thing may cost an extra turn compared to
# bundling three — accepted, because R1 comes from real expert business practice.
ASK_MISSING_AMOUNT = "Dạ bạn cho mình xin thêm số tiền giao dịch giúp mình nhé."

# ⑤ (25/08, Q2 decided by the PO) — the slot-collection gate's question AFTER OTP
# verification (T0, `graph.py`). The old version asked for the TRANSACTION ID plus instructions
# to dig through the Transaction History; the ID was dropped from the QUESTION because making a
# customer who just lost money go and find a 14-digit string pushes the work onto the person in
# a panic. Time + amount can be answered straight from memory. `enough_to_narrow()` STILL
# recognises an ID if the customer volunteers one — not asking ≠ not reading.
#
# R1 after changing how it is enforced (ticket §2b): "one IDEA per message", NOT "one
# REQUEST per message". This is ONE idea — *"give me the information to find the right
# transaction"* — said in one sentence. The old reading produced an isolated ask-for-amount
# gate that Đ1 measured falsely firing 6/11 times.
#
# 🔴 WHY THIS CONSTANT LIVES HERE AND NOT IN `graph.py` — and why its name has NO `_`
# prefix: gate ĐC-7 (`eval/cong_phan_luong.py:406`) finds constants via
# `getattr(luat, n)` with `n.startswith("ASK_")`, where `luat` is EXACTLY the file passed via
# `--luat` — i.e. ONLY this file. Put it in graph.py, or name it `_ASK_...`, and ĐC-7 is
# **completely blind**: no red, no warning, silence.
# The first landing of ⑤ (`d50bf9d`) put it in graph.py with a `_` prefix — I declared that
# limitation in that commit, then moved it here. Anyone adding a new `ASK_*` constant (e.g. ⑨)
# must put it in this file, with a public name. A gate that doesn't see ≠ a gate that agrees.
ASK_TIME_AND_AMOUNT = (
    "Dạ bạn cho mình xin số tiền và thời điểm giao dịch (hôm nay/hôm qua, "
    "sáng/chiều/tối) giúp mình nhé."
)

# ⑨ · K2 (25/08) — THE SCAM-SCREENING QUESTION. A constant, 0 tokens.
#
# CSKH expert: it must be asked in EVERY wrong-transfer case, INCLUDING ones that look obvious
# — because a significant share of "wrong transfer" cases are actually SCAM cases, where the
# customer says it was a mistake out of embarrassment. The two require OPPOSITE handling: a
# mistake means contacting the recipient; a scam means NEVER contacting them and reporting to
# the police within the golden hours.
#
# 🔴 ASK ABOUT AN OBJECTIVE EVENT, NOT A CONCLUSION. "were you scammed?" asks for a conclusion
# — a customer who feels suspected will close up, and we lose the facts. This question asks
# about something that either happened or didn't, which the customer can answer without having
# to admit they were scammed.
#
# The opening frame is MANDATORY ("one more question so we can help in the right direction") —
# not mere politeness: it tells the customer WHY they are being asked; otherwise this question,
# coming right after the case number is announced, would sound like an interrogation.
ASK_SCAM_SCREENING = (
    "Mình hỏi thêm một ý để hỗ trợ bạn đúng hướng: lần này có ai nhắn tin hoặc "
    "gọi điện hướng dẫn bạn chuyển khoản không ạ?"
)

# Detector for AFFIRMATIVE ANSWERS to the question above. ONLY runs when the calling layer
# knows for sure it just asked (thread signal) — outside that context it is meaningless.
#
# 🔴 NEGATION IS CHECKED FIRST, and is SUFFICIENT to exclude. "không có ai gọi cả" (nobody
# called at all) contains "có" (yes/have) — treating it as affirmative would flag suspected
# scam on a customer who just said NO.
# Better to MISS: missing ⟹ one recorded signal lost; a false catch ⟹ the customer's record
# carries a wrong label, and it is a label about them being scammed.
# 🔴 THESE TWO LISTS HAVE OPPOSITE RISK PROFILES — read this before editing either.
#   loosen NEGATION     ⟹ more sentences read as "no" ⟹ signals MISSED. Annoying.
#   loosen AFFIRMATION  ⟹ a SUSPECTED-SCAM label wrongly attached to a customer who said NO.
#                         Real damage.
# ⟹ Negation may be generous. Affirmation may not. A DELIBERATE asymmetry.
#
# [MEASURED 25/08] my first version lacked "đâu"/"làm gì có" ⟹ "có ai đâu" (there was nobody)
# and "làm gì có ai" (as if there was anyone) — TWO NEGATIVE SENTENCES — were read as
# AFFIRMATIVE. Caught with self-built cases; no project gate saw it. Vietnamese negates with
# suffixes ("...đâu") and with split phrases ("làm gì có"), not only with the prefix "không".
_SCREENING_NEGATIONS = ("không", "khong", "chưa", "chua", "chả", "cha",
                      "chẳng", "chang", "đâu có", "dau co", "đâu", "dau",
                      "làm gì có", "lam gi co", "nào có", "nao co")
_SCREENING_AFFIRMATIONS = ("có", "co", "đúng", "dung", "vâng", "vang", "ừ", "u",
                        "phải", "phai", "đúng rồi", "dung roi")
_RE_SCREENING_NEGATIONS = [_re_word(t) for t in _SCREENING_NEGATIONS]
_RE_SCREENING_AFFIRMATIONS = [_re_word(t) for t in _SCREENING_AFFIRMATIONS]


def is_affirmative_reply(sentence: object) -> bool:
    """Is this sentence an AFFIRMATIVE answer to screening question ⑨?"""
    if not isinstance(sentence, str):
        return False
    s = _normalize(sentence)
    if any(p.search(s) for p in _RE_SCREENING_NEGATIONS):
        return False
    return any(p.search(s) for p in _RE_SCREENING_AFFIRMATIONS)

# Hash of THIS VERY FILE, computed at import time. NEVER typed by hand.
#
# My first version hard-coded `"0885bab00a04"` — the hash of a DRAFT file elsewhere. Correct at
# the time of writing, wrong as soon as either file changed. And the tester just paid for
# exactly that: they scored 15/20 on `1edd51dff555` and then ran the gate on
# `0885bab00a04` with nothing to warn them — "the rules changed under my feet between two
# measurements".
#
# A self-declared hash cannot drift from the thing it identifies.
RULES_HASH_METHOD = "md5-toan-file-12"
RULES_HASH = hashlib.md5(Path(__file__).read_bytes()).hexdigest()[:12]


def _normalize(s: str) -> str:
    return _PUNCTUATION.sub(" ", unicodedata.normalize("NFC", s).lower().strip())


def triage(sentence: object) -> tuple[str, str]:
    """Returns `(route, reason)`. **NEVER raises.** Anything abnormal -> `day_du` (full).

    Takes `object` rather than `str`: the tester caught `triage(12345)` raising
    `AttributeError` (`int` has no `.strip()`). Sounds rare, but at the layer this function
    plugs into it isn't — `{"message": 12345}` is valid JSON and the request-building layer
    doesn't necessarily coerce types.

    Why catch ALL exceptions rather than just coercing: the contract of this layer is
    *"any exception ⟹ that turn goes FULL, never blocking the customer"*. If the function
    raised, behaviour would depend on whether the CALLER catches it — which is exactly what
    this contract exists to avoid depending on. A safety gate must not let the way it is
    called decide whether it is safe.

    FAIL-VISIBLE: the wrong direction is the expensive-but-harmless one (tokens spent, nobody
    left behind), so swallowing errors here is right — but swallowing them SILENTLY is not.
    """
    try:
        return _triage(sentence)
    except Exception as e:  # noqa: BLE001 — xem docstring
        _logger.error(
            "phan_luong_nem_loi",
            extra={"lop_loi": type(e).__name__, "kieu_dau_vao": type(sentence).__name__,
                   "hau_qua": "luot nay di duong DAY DU (huong an toan)"},
        )
        return ROUTE_FULL, f"lớp phân loại ném {type(e).__name__} — đi đường an toàn"


def _triage(sentence: object) -> tuple[str, str]:
    if not isinstance(sentence, str):
        return ROUTE_FULL, f"đầu vào không phải chuỗi ({type(sentence).__name__})"
    if not sentence or not sentence.strip():
        return ROUTE_FULL, "câu rỗng — không khẳng định được gì"

    s = _normalize(sentence)

    # 1B — 🔴 DEVIATES FROM THE ORIGINAL DRAFT, REPORTED to the PO-agent/Lead before landing: the
    # draft placed GROUP B (line below) AFTER the "has digits" gate (_HAS_DIGIT), reasoning that
    # "digit-less sentences already go day_du via the existing branch, no new rule needed". But the
    # very sample case the PO-agent used as the acceptance scenario — "tôi bị trừ tiền" (I was
    # charged) — contains NO digits at all (the customer hasn't stated an amount yet, exactly when
    # asking for the amount is most needed). Placing GROUP B after the digit gate would make that
    # sample case NEVER trigger the gate — contradicting the acceptance scenario with its own
    # accompanying example. GROUP B is checked FIRST, unconditionally on digits; the amount slot
    # still naturally catches "no number stated yet" (extract_slots returns so_tien=False), so it
    # still asks back for exactly what's missing — digits aren't needed to START asking, only to
    # EXTRACT the value if the customer has already said it.
    if _group_b(s):
        # 🔴 FIXED 24/08 (PO-agent+Lead): the ONLY MANDATORY SLOT is the AMOUNT —
        # not the pair (amount, time). Basis: expert L3 "the amount is the STRONGEST search anchor";
        # with an amount get_customer_history(amount=...) can look it up immediately, and
        # multiple_matches (if any) already has its own LLM handling path in the candidates' context
        # — asking for time FIRST, deterministically, asks for something possibly unneeded, annoying
        # the customer for nothing.
        # [MEASURED] 124 golden_set sentences: all 36 sentences that broke under the "missing EITHER
        # ONE" rule have so_tien=True — they passed thanks to EXACTLY THIS ANCHOR, not because they
        # are
        # "information-rich" (a length clause in disguise, considered and REJECTED — triage.py
        # banned
        # length clauses before 1B).
        #
        # A transaction ID (TXN...) present ⟹ overrides the amount slot, always goes day_du — the ID
        # identifies a transaction EXACTLY, more specific than an amount.
        #
        # Consequence: every sentence triggering GROUP B(ii) ("mất"/"bị mất"/"bị trừ" adjacent to an
        # amount) ALWAYS has so_tien=True by B(ii)'s own definition ⟹ B(ii) NEVER produces
        # `thu_slot` on
        # its own — it is now only a RECOGNITION layer (still PASSING, guarded separately by the
        # Tester), not a slot DECISION layer.
        # B(i) (e.g. "tôi bị trừ tiền" — no amount at all) is the real source of thu_slot.
        if (
            not _TXN_CODE.search(s)
            and not extract_slots(sentence)["so_tien"]
            and not _has_strong_emotion(s)
            and not _has_spelled_number(s)
            and not _asks_third_party_identity(s)
        ):
            return ROUTE_SLOT_FILL, "dấu hiệu sở hữu/giao dịch cá nhân, thiếu số tiền"
        # A strong emotion signal (measured on s) falls through to the branch below — if there are
        # no digits it continues through the small-talk branch (still day_du because it has tokens
        # outside the set, not pure small talk), never returning to thu_slot.
        # Has an amount (or an ID) ⟹ falls to the branch below, always matches
        # _HAS_DIGIT (amounts/IDs all carry digits), goes day_du as normal.

    if _HAS_DIGIT.search(s):
        return ROUTE_FULL, "có chữ số (tiền/mã GD/SĐT/ngày đều mang số)"

    con = s
    for c in _PHRASES:
        con = con.replace(c, " ")
    tokens_left = [t for t in con.split() if t and t not in SMALL_TALK]

    if tokens_left:
        return ROUTE_FULL, f"token ngoài tập xã giao: {tokens_left[:3]}"
    if not s.strip():
        return ROUTE_FULL, "sau chuẩn hoá không còn gì — không khẳng định được"

    return ROUTE_LIGHT, "mọi token thuộc tập xã giao đóng"
