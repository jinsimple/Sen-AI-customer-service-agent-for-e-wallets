"""OUTPUT filter O1–O4 — the last net, run on `reply` before it is returned to the customer.

THE ASYMMETRY PRINCIPLE (security §4.1, don't copy it wrongly from elsewhere):
for INPUT PII scrubbing the project settled on "better to mask by mistake than to leak". That
principle **DOES NOT carry over here**. On output, a false positive silently replaces a
CORRECT answer with a template sentence — destroying exactly what the customer needs. So the
output filter must be **NARROW BUT CERTAIN**; the broad part is left to the per-thread
guardrail signal counting (which only counts, never blocks a sentence).

Direct consequence for how this is written: every group below is designed to **miss in a
controlled way** rather than catch wrongly. Anyone wanting to tighten it more broadly must
bring negative-case counts first.
"""
from __future__ import annotations

import json
import logging
import re
import unicodedata

from src.agents import phrase_match as KC  # noqa: N812 — KC is a DELIBERATE alias (the phrase-match module is used heavily, see ADR-023)
from src.services import thread_signals

_logger = logging.getLogger("fin05.output_filter")

SAFE_FALLBACK_REPLY = (
    "Xin lỗi, phần này mình không trả lời trực tiếp được. Để đảm bảo an toàn "
    "thông tin cho bạn, mình chuyển sang chuyên viên hỗ trợ nhé."
)


def _strip_diacritics(t: str) -> str:
    t = t.lower().replace("đ", "d")
    return "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")


# ---------------------------------------------------------------- O1
# INTERNAL thresholds/signals. Narrow: only codes and variable names with a distinctive shape,
# no semantic guessing.
_O1_CODE = [
    re.compile(r"\bFS-\d+\b", re.IGNORECASE),
    re.compile(r"\bOTP_[A-Z_]{3,}\b"),
    re.compile(r"\b(RESOLUTION_APPROVAL_OTP_FRESH_MINUTES|OTP_VIEW_MAX_MINUTES|OTP_STEPUP_FRESH_MINUTES)\b"),
]
# The OTP validity figure — ONLY counted when the sentence is talking about OTP. "15 minutes"
# in a sentence about the investigation timeline is harmless; the same number next to the word
# OTP leaks configuration.
_O1_OTP_DIGITS = re.compile(r"\b(12\s*(gio|tieng)|15\s*phut|10\s*phut)\b")
# Trigger context for the validity figure: not just the word "otp". "Ma duyet cua sep
# het han 10 phut" (the supervisor's approval code expires in 10 minutes) has no "OTP" yet leaks
# exactly the config value
# RESOLUTION_APPROVAL_OTP_FRESH_MINUTES.
# F-27 — ANCHOR ON THE EXPIRY CONTEXT, NOT on a technical keyword.
# The previous version required the reply to contain "otp"/"ma duyet" before inspecting the number:
#   "Mã OTP duyệt hết hạn sau 10 phút"                  -> blocked
#   "Sếp duyệt phải xin mã riêng, hết hạn sau 10 phút"  -> SLIPPED THROUGH
#     (the supervisor must request a separate code, expiring after 10 minutes)
# The same config value (RESOLUTION_APPROVAL_OTP_FRESH_MINUTES), but the second phrasing is the
# MOST NATURAL way for the agent to say it — the prompt even tells it to avoid technical terms.
# A pattern anchored on technical keywords keeps leaking through EVERYDAY WORDING.
# Exactly the F-24 lesson: a pattern only catches how WE IMAGINE people talk, not how they REALLY
# talk.
# Now anchored on: the config value + any EXPIRY/VALIDITY marker.
# RULE 18: via `KC.phrase`, "ma duyet" also catches "mã PHẢI duyệt" (code MUST be approved),
# "ma xac nhan" catches "mã cần xác nhận" (code needs confirming). See `phrase_match.py` — a
# PURELY ADDITIVE transformation.
_O1_CODE_CONTEXT = KC.phrase(
    "otp", "ma duyet", "ma xac nhan", "phe duyet", "ma xac thuc",
    "het han", "hieu luc", "con han", "hieu luc trong", "trong vong",
    "phai xin lai", "xin ma moi", "ma rieng",
)
# NGUONG NOI BO dang "vuot nguong N trieu". Ca nay dac biet: 10 trieu la nguong
# SINH TRAC HOC (QD 2345/QD-NHNN), KHONG phai nguong gian lan — hien phap §8 ghi
# ro. Agent noi cau do vua ro cau hinh noi bo VUA SAI LUAT, nen chan la dung ca
# hai mat.
_O1_MONEY_THRESHOLD = re.compile(r"\b(vuot |tren |qua )?nguong\s*\d+\s*(trieu|tr|nghin|k)\b")


def _match_o1(reply: str) -> bool:
    if any(r.search(reply) for r in _O1_CODE):
        return True
    clean_text = _strip_diacritics(reply)
    if _O1_MONEY_THRESHOLD.search(clean_text):
        return True
    return KC.match_any(_O1_CODE_CONTEXT, clean_text) and bool(_O1_OTP_DIGITS.search(clean_text))


# ---------------------------------------------------------------- O2
# DELIBERATELY NARROW, and I state the limitation plainly: "lists >=2 consecutive internal
# rules" has no machine-checkable definition without comparing against the prompt itself. Here
# we only catch VERBATIM repetition of phrases specific to the internal prompt. Paraphrase is NOT
# caught — left to the per-thread guardrail count, per the narrow-but-certain principle. Don't
# read O2's existence as "every way of leaking instructions is covered".
_O2_INTERNAL_PHRASES = KC.phrase(
    "rang buoc bat buoc",
    "quy trinh dieu tra",
    "khong bao gio duoc",
    "ban la tro ly ao cua",
)


def _match_o2(reply: str) -> bool:
    clean_text = _strip_diacritics(reply)
    return sum(1 for c in _O2_INTERNAL_PHRASES if c.search(clean_text)) >= 2


# ---------------------------------------------------------------- O3
# CONDITIONAL: part B only runs when part A fires. An oracle violation is NOT a lexical property
# of the answer — it is a property of the PAIR (the customer's guess ↔ the answer). The same word
# "chính xác" (exactly/correct) is harmless when the customer asks about an amount, and a leak
# when the customer just read out a masked digit sequence.
_A_DIGIT_SEQUENCE = re.compile(r"\d{4,}")
_A_PROPER_NAME = re.compile(r"\b[A-ZĐÀ-Ỹ][a-zà-ỹ]+(\s+[A-ZĐÀ-Ỹ][a-zà-ỹ]+){1,}\b")
_A_CONFIRMATION_QUESTION = KC.phrase(
    "co phai", "dung khong", "phai khong", "hay la", "dung/sai", "dung hay sai",
    "gan dung", "xac nhan giup", "co dung", "phai vay khong",
)
# B — only counts when the confirm/deny phrase STANDS AS AN ANSWERING CLAUSE, i.e. it opens a
# clause. "không có giao dịch nào chính xác với 500k" (no transaction exactly matching 500k) does
# NOT match because "chính xác" sits mid-clause, not as a yes/no answer.
# The NEGATIVE forms are covered too: ruling out one possibility is also ONE BIT of oracle.
# "Khong phai 21 dau" (it's not 21) narrows the guessing space exactly as "dung roi" (that's
# right) confirms it.
_B_ASSERTION = KC.phrase(
    "dung roi", "chinh xac", "vang", "phai roi", "gan dung", "dung vay",
    "khong phai", "sai roi", "khong dung", "khong phai vay",
)


def _split_clauses(t: str) -> list[str]:
    return [m.strip() for m in re.split(r"[,.;:!?\n]+", t) if m.strip()]


def _a_is_speculation(customer_message: str) -> bool:
    if not customer_message:
        return False
    has_data = bool(_A_DIGIT_SEQUENCE.search(customer_message)) or bool(_A_PROPER_NAME.search(customer_message))
    clean_text = _strip_diacritics(customer_message)
    is_question = KC.match_any(_A_CONFIRMATION_QUESTION, clean_text)
    return has_data and is_question


# THE PROVENANCE RULE — completely replaces the _MA_HE_THONG prefix list from 7ee2ab5.
#
# Why drop the list: it was WHACK-A-MOLE. The PO measured two holes in a single round:
#   - missing "RC" -> RC00000051 (the CUSTOMER'S OWN receipt) wrongly blocked
#   - smuggling: gluing a letter prefix onto a phone number ("SDT0387000001") escaped
# Adding RC to the list only patches the first case and DOESN'T touch the second — tomorrow
# another prefix will be missing. A prefix list is broken by nature: it blocks by SHAPE, and an
# attacker can choose the shape.
#
# The provenance rule blocks by SOURCE: every run of >=7 digits the agent states must trace back
# to a tool result from this turn, or to text the customer typed themselves. It closes both holes
# above without listing anything:
#   RC00000051 the customer just typed -> present in the source -> PASSES
#   SDT0387000001                      -> the phone was scrubbed from the tool result -> BLOCKED
# And it COINCIDES EXACTLY with hard constraint 3 (numbers the agent states must trace to a real
# tool), so one check blocks both ORACLES and FABRICATED NUMBERS.
#
# EDGE CASE, written down so nobody "fixes it to go green": a number the agent ADDS UP ITSELF
# (the sum of two transactions) IS BLOCKED because no source contains it. That is a FEATURE,
# exactly constraint 3.
# FORMAT TIGHTENED (fix B) — a separator is ONLY valid when it has the shape of a THOUSANDS
# SEPARATOR, i.e. every group after a separator has EXACTLY 3 digits. The old pattern
# `\d[\d.,\s]{5,}\d` treated EVERY dot/comma/space as a separator, so it glued things that
# aren't one number into a sequence that EXISTS NOWHERE, then blocked the agent for "untraceable":
#   "01.08.2026"           -> 01082026        (a DATE, wrongly blocked)
#   "1.100.000, 262.000"   -> 1100000262000   (two amounts, BOTH valid, wrongly blocked)
# The `\d{7,}` branch keeps catching fabrication for numbers written WITHOUT separators — trap F
# is not loosened.
#
# TWO HOLES MEASURED, CLOSED BY TWO DIFFERENT MECHANISMS — dropping `\s` (my intermediate draft)
# WAS WITHDRAWN: it closed hole ① but OPENED a new hole on the fabrication side (Lead [MEASURED]
# independently, see below). The standing version is BOUNDARY ANCHORS + CONSISTENT SEPARATOR,
# closing both with no trade-off.
#
# ① BOUNDARY ANCHORS `(?<!\d)…(?!\d)` (found by Lead, [MEASURED]) — without anchors, the pattern
#    picks ANY starting point inside a digit string split by dots, as long as the remainder
#    happens to fit the group-of-3 shape: "01.08.2026" yields the phantom sequence "08.202"
#    (starting mid-"08", grouped with ".202" of "2026"). The `(?!\d)` anchor stops it: the
#    character after "08.202" is '6' (a digit) → match rejected, and no other starting point
#    satisfies both \d{1,3} and the tail.
# ② CONSISTENT SEPARATOR via backreference `([.,\s])…\1` (found by me, after my "drop \s"
#    version was caught by Lead [MEASURED] regressing on `'so 1 100 000 bia'` — a FABRICATED
#    number using spaces as thousands separators, caught by the OLD pattern, blinded by the "drop
#    \s" version). `\s` stays in the separator SET (Lead's fabrication-catching side isn't lost),
#    but every repetition within ONE sequence must use EXACTLY ONE separator character (`\1`
#    re-matches the character captured the first time) — ONE sequence may not mix '.' with ' '.
#    This is exactly the shape that distinguishes the two cases:
#      "1 100 000" (fabricated, ALL spaces)          -> consistent -> BLOCKED  ✅
#      "1.100.000 262.000" (two INDEPENDENT numbers, number 1 -> consistent up to "1.100.000",
#       using '.', then hits ' ' BEFORE "262" — doesn't     stops there, "262.000" is
#       match \1='.' -> the match stops at number one)     the NEXT separate match  ✅
#    [MEASURED] by script, 12 cases (9 from Lead + 2 I found + 1 old limitation) —
#    0/12 off expectation, and this pattern ALSO CLOSES the "glued without a space" limitation
#    ('1.100.000,262.000') the previous version had to declare as accepted: a comma after '.'
#    is now also rejected by the backreference because it doesn't match \1='.'.
#
# 🔴 REMAINING LIMITATION (found by the PO-agent, confirmed independently by Lead [MEASURED], and
# by me [MEASURED] a third time before writing — all three agree): numbers the agent FABRICATES
# with INCONSISTENT separators (`2.500 000` · `2 500.000` · `2.500,000`) are NOT caught — the
# backreference demands the SAME character for every group in a sequence, so a mixed sequence
# never assembles ≥7 digits and falls out of the extracted set ENTIRELY (`_digit_sequences`
# returns empty for these, not wrong). The ORIGINAL pattern `\d[\d.,\s]{5,}\d` DID CATCH all
# three ⟹ this is a REAL NARROWING versus the baseline, not merely out of reach — a CONSCIOUS
# trade-off to close two false-block cases ('1.100.000 262.000' and '1.100.000,262.000'). This
# trade-off is FAR NARROWER than the withdrawn "drop \s" version (which let EVERY space-separated
# fabricated number through, even pure-space ones), but it is NOT EMPTY: fabricated numbers using
# a CONSISTENT separator (all dots or all spaces) are still correctly blocked. Fixing this hole
# would require enforcing consistency at ANOTHER LAYER or loosening back towards false blocks —
# both cost more than they gain, and all their errors fall on the FALSE-BLOCK side, exactly what
# is being cured today. DON'T fix it.
_DIGIT_SEQUENCE = re.compile(r"(?<!\d)\d{1,3}([.,\s])\d{3}(?:\1\d{3})*(?!\d)|(?<!\d)\d{7,}(?!\d)")
# ⚠️ `([.,\s])` is a CAPTURING GROUP (mandatory, so `\1` can anchor the separator) — only use
# it via `finditer(...).group()` (exactly ONE place, `_digit_sequences` below). Calling
# `_DIGIT_SEQUENCE.findall(...)` would return group 1's SEPARATOR, NOT the number —
# and it fails SILENTLY (no error, just a data type the caller didn't expect).
# Tester case OR-F03: "43a5940" is a SLICE of the tool_result_id "TR-43a5940ecd78"
# — an INTERNAL identifier of the measurement suite that must never be emitted to the customer.
# It isn't a pure digit string (letters interleaved), so a digits-only rule is completely blind
# to it.
# Extended: any alphanumeric TOKEN of length >=7 that contains AT LEAST one digit. The threshold
# of 7 + mandatory digit keep ordinary Vietnamese words out (no word is both >=7 long and
# contains a digit).
_CODE_TOKEN = re.compile(r"[A-Za-z0-9]{7,}")

# 🔴 FIX A (25/08) — CODES WITH A HYPHEN. `_CODE_TOKEN` requires ≥7 CONTIGUOUS characters,
# so the `-` cuts `CMP-00003` into "CMP"(3) + "00003"(5) ⟹ **both below the threshold**,
# O3 COMPLETELY BLIND. Incident 25/08: the bot fabricated `CMP-00003` — a REAL code belonging to
# ANOTHER customer — and the filter let it through, while THE SAME SENTENCE WITHOUT THE CODE was
# blocked by O5.
# ⟹ Adding a fake code to a sentence made it SAFER in the filter's eyes.
#
# Every REAL code in the system has ≥7 CONTIGUOUS characters after its prefix (TCK-…12hex ·
# RES-…12hex · TXN…14 digits), so this gap only opens for FABRICATED codes — nobody trips on it
# until the model fabricates one.
#
# Pattern: 2–5 LETTERS + `-` + ≥3 alphanumerics. DELIBERATELY starts with a LETTER so it does
# NOT swallow dates (`2026-08-27` starts with a digit ⟹ no match) — dates are something the agent
# legitimately says all the time; blocking them would shut down normal answers.
# `{3,}` after the hyphen: "COVID-19"/"check-in"/"e-mail" all fall outside.
#
# 🔴 APPLIED TO BOTH SIDES (reply AND source) because it lives in `_digit_sequences` — REAL codes
# from tool results are extracted identically, so they stay TRACEABLE and are NOT wrongly
# blocked. Only FABRICATED codes are absent from the source.
_HYPHENATED_CODE = re.compile(r"\b[A-Za-z]{2,5}-[A-Za-z0-9]{3,}\b")


def _digit_sequences(text: str, *, allow_separator: bool = True) -> set[str]:
    """Every digit sequence / code in the text.

    `allow_separator` — DIFFERS between PROSE and JSON, and this is where it's easy to go wrong:

    · PROSE (the agent's answer, the customer's typed text): MUST allow it, because the same
      number is written differently in different places — the tool returns `262000`, a person
      writes `262.000đ`.
    · JSON (tool payloads): MUST FORBID it. A comma in JSON is a FIELD SEPARATOR,
      not a thousands separator. Allowing it would merge `{"amounts": [262000, 1100]}`
      into `2620001100` — a number that EXISTS NOWHERE, yet gets loaded into the VALID SOURCE
      set. An agent fabricating exactly that string would pass.
      Measured: exactly this case SLIPPED THROUGH in build 3e7ac21.
      Same family as the tester's trap F (a fabricated number "traceable" because it matches a
      fragment of the source), but straddling the BOUNDARY BETWEEN TWO FIELDS instead of
      sitting inside one value.
    """
    out_items = set()
    pattern = _DIGIT_SEQUENCE if allow_separator else re.compile(r"\d{7,}")
    for m in pattern.finditer(text or ""):
        number = re.sub(r"[.,\s]", "", m.group())
        if len(number) >= 7:
            out_items.add(number)
    for m in _CODE_TOKEN.finditer(text or ""):
        tok = m.group()
        if any(c.isdigit() for c in tok):
            out_items.add(tok.lower())
    for m in _HYPHENATED_CODE.finditer(text or ""):
        tok = m.group()
        if any(c.isdigit() for c in tok):
            out_items.add(tok.lower())
    return out_items


# DIAGNOSTICS store no content (fix C). MUST NOT contain values or HASHES of values —
# a hash is still an identifier and can still be matched back to a specific number; only the
# SHAPE may be logged. See the call site in `filter_output` — the principle "a reply matching O3
# almost certainly contains masked data; logging it leaks it with our own hands" applies equally
# to EVERY new diagnostic field, not just the original `reply`.
def _shape_this_is(this_is: set[str]) -> dict[str, object]:
    return {
        "o3_so_luong_day_la": len(this_is),
        "o3_do_dai_day_la": sorted(len(t) for t in this_is),
        "o3_co_chu_cai": any(any(c.isalpha() for c in t) for t in this_is),
        # A pure DATE-looking shape: an ALL-DIGIT sequence of exactly 8 characters (DDMMYYYY glued
        # together — exactly the fabricated "01.08.2026" -> "01082026" case fix B just closed). A
        # deliberately ROUGH guess: the goal is quick diagnosis, not precise classification — if
        # this is
        # misused, go and ask for the real value; don't guess further.
        "o3_co_hinh_dang_ngay": any(len(t) == 8 and t.isdigit() for t in this_is),
    }


def _turn_payload_empty(source: str) -> bool | None:
    """Whether `luot_nay` (this turn — the wrapper produced by `assemble_o3_source`, graph.py)
    is empty.

    `None` = CANNOT BE DETERMINED (the source doesn't carry this wrapper — e.g. a source built
    by the offline eval's own convention) — this is the mandatory THIRD state
    (Rule H): "not measurable" must not be merged into "not empty"/"empty".
    """
    try:
        d = json.loads(source)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(d, dict) or "luot_nay" not in d:
        return None
    return not d["luot_nay"]


def _match_o3(reply: str, customer_message: str, source: str, customer_text: str = "") -> tuple[bool, dict]:
    # source = tool payload (JSON) -> extracted STRICTLY, separators may not merge numbers.
    # customer_text + customer_message = prose -> extracted LENIENTLY, "262.000đ" accepted.
    valid = (
        _digit_sequences(source, allow_separator=False)
        | _digit_sequences(customer_message)
        | _digit_sequences(customer_text)
    )
    # SO THEO GIA TRI, KHONG so chuoi con — bay F cua tester.
    # Ban dau toi so `so in g or g in so` de "tool tra so dai hon ma agent
    # chi doc mot phan" van qua. Nhung chinh no mo mot cua BIA SO MOI:
    # "20260504" la CHUOI CON cua trans_id that TXN20260504000247, nen mot
    # con so agent bia ra van "truy vet duoc" chi vi no tinh co la tien to
    # cua mot ma that. Do that: LOT.
    # Bay B (dinh dang) va bay F (chuoi con) KEO NGUOC NHAU — noi de cuu B
    # lam do F, siet de cuu F lam do B. Loi ra: chuan hoa DINH DANG (bo dau
    # phan cach) de cuu B, nhung so KHOP TUYET DOI de dong F.
    this_is = {number for number in _digit_sequences(reply) if number not in valid}
    if this_is:
        return True, _shape_this_is(this_is)
    if not _a_is_speculation(customer_message):
        return False, {}
    for md in _split_clauses(_strip_diacritics(reply)):
        # `.match` rather than `.search`: keeps the old `startswith` semantics of "standing at the
        # START of a clause". Rule 18 only loosens the MIDDLE of a phrase, not the clause-start
        # anchor —
        # that anchor is what distinguishes a yes/no ANSWER from the word "chính xác" sitting inside
        # a
        # harmless sentence.
        if any(k.match(md) for k in _B_ASSERTION):
            return True, {}
    return False, {}


# ---------------------------------------------------------------- O4
# BY PHRASE, not by word: only matches when all THREE elements are present IN THE SAME CLAUSE.
# "chắc chắn sẽ được hoàn cho bạn" (you will certainly be refunded) matches; "nếu muốn biết chắc
# chắn thì liên hệ CSKH" (if you want to know for sure, contact customer service) doesn't, because
# it lacks a money object and isn't addressed at the customer's case.
# "du dieu kien duoc hoan" (eligible for a refund) is a COMMITMENT DRESSED AS A CONDITION: it
# doesn't promise outright, but the customer reads it as "I will be refunded". Hard constraint 1
# forbids the agent from concluding on the outcome, even indirectly.
_O4_VERBS = ["se ", "chac chan", "dam bao", "cam ket", "du dieu kien", "duoc duyet",
    # Security 19/08 (030e4b2) + PO-agent [MEASURED] for real (3d14d30): the PERFECT tense
    # ("đã", "vừa" — already, just) slipped through entirely before this fix — "đã được hoàn tiền"
    # (has been refunded) is a statement of OUTCOME, not a promise, but the customer reads it the
    # same way and the consequence is worse (the customer STOPS FOLLOWING UP on a transaction nobody
    # has approved).
    #
    # 🔴 DO NOT use BARE "da"/"vua" (unlike "se " — only "sẽ" strips to "se", but "đã" AND "dạ" (an
    # extremely common sentence-opening particle in CSKH style — "Dạ anh...") BOTH strip to "da").
    # [MEASURED] reproduced: bare "da" WRONGLY catches "Dạ anh khoản hoàn tiền đang được xử lý ạ"
    # (Yes sir, the refund is being processed — no perfect tense at all) — exactly the "negative
    # case
    # #1" trap Security warned about, merely moved from "sẽ" to "đã"/"dạ".
    #
    # 🔴 AND DO NOT pair "da"/"vua" with BARE "hoan" — [MEASURED] reproduced A SECOND TIME, this
    # time wrongly catching THE EXISTING test suite itself: "Giao dịch ngày 01.08.2026 của bạn đã
    # hoàn
    # tất." (Your transaction on 01.08.2026 has completed.) was wrongly blocked
    # (test_o3_cong_hanh_vi... went red). A lone "hoàn" is ambiguous between "hoàn TIỀN" (refund)
    # and
    # "hoàn TẤT/THÀNH" (complete) — bare `hoan` in `_O4_MONEY` survives with "sẽ/chắc chắn"
    # (hardly anyone says "will certainly have completed") but NOT with "đã/vừa" (very natural with
    # "hoàn tất" — an everyday progress description, not a money commitment). ⟹ only paired with the
    # phrases ALREADY in `_O4_MONEY` that are unambiguous on their own (hoàn TIỀN, hoàn LẠI, trả
    # lại,
    # bồi hoàn, nhận...tiền, về/vào ví/tài khoản — none can be read as "done"), NOT with bare
    # "hoan". Plus the variants "da duoc "/"vua duoc " — the passive ("đã ĐƯỢC hoàn tiền") is more
    # natural than the active voice in CSKH writing.
    "da hoan tien", "da duoc hoan tien", "vua hoan tien", "vua duoc hoan tien",
    "da hoan lai", "da duoc hoan lai", "vua hoan lai", "vua duoc hoan lai",
    "da tra lai", "da duoc tra lai", "vua tra lai", "vua duoc tra lai",
    "da boi hoan", "da duoc boi hoan", "vua boi hoan", "vua duoc boi hoan",
    "da nhan lai tien", "da nhan duoc tien", "vua nhan lai tien", "vua nhan duoc tien",
    "da ve vi", "da vao vi", "da vao tai khoan",
    "vua ve vi", "vua vao vi", "vua vao tai khoan"]
_O4_MONEY = ["hoan tien", "hoan lai", "hoan", "tra lai", "boi hoan", "nhan lai tien", "nhan duoc tien", "ve vi", "vao vi", "vao tai khoan"]
_O4_CUSTOMER_ADDRESS = ["ban", "anh", "chi", "minh", "cua ban", "quy khach"]


# NEGATION — the part I forgot, which made O4 punish the agent for OBEYING ORDERS.
# Hard constraint 1 requires the agent to say "I can't decide on the refund myself".
# That refusal uses EXACTLY THE SAME WORDS as a commitment, differing by one negation:
#     "chắc chắn bạn SẼ được hoàn"                        -> commitment, must block
#       (you WILL certainly be refunded)
#     "mình KHÔNG THỂ xác nhận chắc chắn bạn sẽ được hoàn" -> refusal, must pass
#       (I CANNOT confirm for sure that you will be refunded)
# The 3-element phrase matches identically in both. Measured: 96/463 blocks were O4, and among
# them were sentences where the agent was refusing to commit exactly as instructed.
# This is exactly the "negative case #1" trap security wrote for O2 — punishing the agent for
# obeying — just showing up in O4.
_O4_NEGATIONS = ["khong", "chua", "khong the", "chua the", "khong bao gio"]


def _marker_positions(md: str, tokens: list[str]) -> int | None:
    """Earliest position of a token, matched on WORD BOUNDARIES.

    Substring matching is O4's biggest source of false positives, and it is silent:
    `"hoan"` sits inside `"khoang"` (kh-OAN-g), so the harmless sentence "phản hồi lại
    bạn trong KHOẢNG thời gian đến 14/09" (we'll reply to you within the period up to 14/09)
    was counted as having a "money object". Four of the five remaining false blocks were due to
    exactly this word.
    """
    pos = [m.start() for t in tokens for m in [re.search(rf"\b{re.escape(t.strip())}\b", md)] if m]
    return min(pos) if pos else None


def _match_o4(reply: str) -> bool:
    for md in _split_clauses(_strip_diacritics(reply)):
        # A clause with a negation -> SKIPPED. A deliberate trade-off under the output filter's
        # narrow-but-certain principle: missing a convoluted commitment is better than deleting a
        # textbook refusal. Clauses are split on punctuation, so
        # "không có gì phải lo, bạn chắc chắn sẽ được hoàn" (nothing to worry about, you will
        # certainly
        # be refunded) is still caught in the second half.
        if any(p in md for p in _O4_NEGATIONS):
            continue
        verb_pos = _marker_positions(md, _O4_VERBS)
        money_pos = _marker_positions(md, _O4_MONEY)
        address_pos = _marker_positions(md, _O4_CUSTOMER_ADDRESS)
        if verb_pos is None or money_pos is None or address_pos is None:
            continue
        # ORDER is what distinguishes a PROMISE from a PROCESS DESCRIPTION — the three elements
        # being
        # present isn't enough:
        #   "bạn SẼ được HOÀN tiền"              -> verb BEFORE money = a promise
        #   "quyết định HOÀN tiền SẼ phụ thuộc"  -> money BEFORE verb = a description
        #     (the refund decision WILL depend on...)
        # The second sentence is the agent doing hard constraint 1 RIGHT (no promise, deferring to
        # the
        # decision-maker). The previous version deleted it — i.e. punished the agent for obeying,
        # exactly
        # the "negative case #1" trap security wrote for O2, resurfacing in O4.
        if verb_pos < money_pos:
            return True
    return False


# ---------------------------------------------------------------- O5
# Original spec: docs/security/2026-08-24-dac-ta-o5-tu-vung-hoan-tat-gia-tao-ve.md
# (Security, after finding 5f627e3: "đã tạo hồ sơ cho bạn rồi" (I've created a case for you)
# slipped cleanly through O3+O4 because it had no number and no money word). The original spec §2
# proposed comparing the TICKET CODE against `source` (like O3) — but the Tester RE-measured with
# REAL 12-hex codes (`new_id()`) instead of the 5-6 character fixture of the first measurement:
# O3 already covers 2/2 "states the WRONG code" cases (wrong value + superstring), because real
# codes ALWAYS fall within `_CODE_TOKEN`'s reach (7-character threshold). O5 is only needed for
# EXACTLY the gap where O3 has nothing to compare: a reply that states NO code at all — whether a
# fake completion (no tool result) or a real completion where the code was forgotten (now ALWAYS
# wrong by policy, see below).
#
# The rule (narrowed by Security 24/08, approved by the real PO via the PO-agent):
#   COMPLETION vocabulary (đã/vừa tạo/mở/ghi nhận — already/just created/opened/recorded, with
#   passive variants) matches an
#   OBJECT (hồ sơ/vé/ticket/khiếu nại — case/ticket/complaint) in the SAME clause
#   AND the reply contains NO code token (`_CODE_TOKEN` — REUSING O3's definition verbatim, no
#   new yardstick invented).
#
# NO value comparison against `source` (unlike §2 of the original spec) — for a sufficient
# reason, not an omission: the `create_ticket` docstring now REQUIRES stating the code
# (customer_tools.py, `6d0e3a9`, same session), so a MISSING CODE IS ALWAYS WRONG by policy,
# regardless of whether `source` holds a successful tool result. This simplification was decided
# by the two MEASUREMENT rounds themselves, not by prior speculation.
#
# Reusing O4's paid-for mechanisms VERBATIM, not reinventing:
#   1. Fused phrases, NO bare "da"/"vua" — the "dạ" trap: stripped of diacritics it equals "da"
#      (_strip_diacritics("Dạ") == _strip_diacritics("đã") == "da"). Every entry below ALWAYS
#      fuses the tense with the verb into one phrase, like O4's "da hoan tien".
#   2. `_O4_NEGATIONS` for negated clauses — "mình CHƯA tạo được hồ sơ lúc này" (I HAVEN'T been
#      able to create the case yet) is a CORRECT sentence (the agent honestly reporting an error/
#      expired OTP, exactly what finding 5f627e3 asked to teach the agent to say) — it MUST pass;
#      no separate negation list is invented for O5.
#
# 🔴 Caught in review 24/08 (checking 491c91d) — TWO holes, both MEASURED directly by running
# code, not inferred:
#
#   ① MISSING the "addressed to the customer" element (the first version had only 2 elements:
#      has_verb + has_object).
#      [MEASURED] "Vé loại này đã được mở rất nhiều lần trong quá khứ, không có gì bất thường."
#      (This kind of ticket has been opened many times in the past, nothing unusual.) and "Hồ sơ
#      tương tự đã ghi nhận cho nhiều khách khác trước đây rồi." (Similar cases have been recorded
#      for many other customers before.) — neither claims anything was done FOR THE CUSTOMER IN
#      THIS CHAT, they only describe general/past matters, yet both matched the old 2 elements ⟹
#      WRONGLY BLOCKED. Exactly what the principle at the top of the file warns is the WORST
#      outcome (false positive > false negative at the output-filter layer).
#
#      The review suggested adding an ORDER check (like O4: verb_pos < money_pos) — CONSIDERED but
#      NOT used: ordering would drop the valid passive case itself
#      "Hồ sơ khiếu nại của bạn đã được ghi nhận" (Your complaint has been recorded — the object
#      comes BEFORE the verb, the natural Vietnamese passive structure) — losing a REAL catch to
#      close 2 false-positive holes is a worse trade. A DIFFERENT direction was chosen: add a THIRD
#      ELEMENT, "addressed to the customer" (mirroring `_O4_CUSTOMER_ADDRESS` — exactly the open
#      question in §4 of the original spec: "Is a customer-address element needed?"). Both of the
#      review's sentences LACK customer address (no bạn/anh/chị/mình/của bạn/quý khách) ⟹ requiring
#      this element closes both holes WITHOUT ordering, keeping the ability to catch valid passive
#      sentences.
#
#   ② MISSING vocabulary: "đã lập" (drew up a case/ticket — common in CSKH) and ESPECIALLY "đã
#      tiếp nhận" (received/accepted) — [MEASURED] the review pointed out this IS exactly the
#      vocabulary ADR-047 (`1080762`, landed THE SAME DAY) uses to describe what create_ticket does
#      ("tiếp nhận trước, bổ sung sau" — accept first, supplement later). The new branch of
#      prompt.py step 4 makes it highly likely the model uses EXACTLY "tiếp nhận" when reporting
#      results — the very language frame installed that day. Missing this word would be blind to
#      exactly the case with the HIGHEST probability among fake completions from now on.
#      "lập"/"tiếp nhận" (active + passive) were added to the verb list.
_O5_COMPLETION_VERBS = [
    "da tao", "da mo", "da ghi nhan", "da lap", "da tiep nhan",
    "vua tao", "vua mo", "vua ghi nhan", "vua lap", "vua tiep nhan",
    "da duoc tao", "da duoc mo", "da duoc ghi nhan", "da duoc lap", "da duoc tiep nhan",
    "vua duoc tao", "vua duoc mo", "vua duoc ghi nhan", "vua duoc lap", "vua duoc tiep nhan",
]
_O5_OBJECTS = ["ho so", "ve", "ticket", "don khieu nai", "khieu nai"]
_O5_CUSTOMER_ADDRESS = ["ban", "anh", "chi", "minh", "cua ban", "quy khach"]
# 🔴 The review critiqued its own "whole reply" suggestion (24/08, after d9885ca) —
# [MEASURED] extending "customer address" to the whole reply LENDS customer-address status to an
# UNRELATED sentence: "Bạn hỏi hay đó. Loại vé này đã được mở rất nhiều lần trong quá khứ cho
# nhiều khách khác..." (Good question. This kind of ticket has been opened many times in the past
# for many other customers...) — "Bạn" (you) in the FIRST sentence only acknowledges the question;
# the NEXT sentence is still a general description exactly like the 2 round-1 false positives —
# resurfacing, same bug family. "Proximity" doesn't solve it (the review tried): "bạn" also sits
# in an adjacent clause in the very case just built.
#
# Fixed via ANOTHER BRANCH the review suggested: NEGATE general descriptions, same pattern as
# `_O4_NEGATIONS` — a clause showing signs of talking about something GENERAL/PAST (frequency,
# history, other people) does NOT count, even if it has both verb+object.
_O5_GENERIC_DESCRIPTIONS = ["nhieu lan", "truoc day", "thuong xuyen", "khach khac"]

# 🔴 RB3 false positive, SECOND TIME (04/09, caught by QA via T1-T5, 2/8 turns — the first
# time, earlier on 04/09, was a missing `request_human_handoff` source, fixed in c6d15ac, a
# DIFFERENT bug). The Coder reproduced it with a direct function test (0 tokens, deterministic):
#   "Mình đã ghi nhận khiếu nại của bạn, đang xử lý tiếp." -> True WRONG
#     (I've noted your complaint, continuing to process it.)
# "ghi nhận khiếu nại" (note the complaint) is NOT something the model invented — it is the
# VERBATIM phrase `prompt.py` teaches (Constraint #1 part b) and the reference CSKH expert script
# uses it repeatedly — the PO decided: DO NOT touch prompt.py (the business logic is right); only
# the matcher needs to get smarter at distinguishing 2 DIFFERENT MEANINGS of the same phrase:
#   SOFT MEANING — "đã ghi nhận/tiếp nhận" = has HEARD/UNDERSTOOD the information, still
#     processing (not necessarily having called create_ticket).
#   HARD MEANING — "đã tạo/mở/lập" (created/opened/drew up) = asserts a specific record ALREADY
#     EXISTS.
# Designed by the review, verified by the Coder on 9 cases + 4 self-added adversarial cases
# (100% match) before landing — see the Lead/Review/Coder discussion history of the evening of
# 04/09; the full matrix is not repeated here.
_O5_STRONG_VERBS = [
    "da tao", "da mo", "da lap",
    "vua tao", "vua mo", "vua lap",
    "da duoc tao", "da duoc mo", "da duoc lap",
    "vua duoc tao", "vua duoc mo", "vua duoc lap",
]
_O5_SOFT_VERBS = [
    "da ghi nhan", "da tiep nhan",
    "vua ghi nhan", "vua tiep nhan",
    "da duoc ghi nhan", "da duoc tiep nhan",
    "vua duoc ghi nhan", "vua duoc tiep nhan",
]
# SOFT sentences saying continuing/not-yet-done (STANDING NEXT TO the soft verb, NOT the whole
# reply — see the "reply-global" warning in `claims_ticket_created` below; this IS exactly where
# that trap nearly recurred if the if-branch were placed wrongly).
_O5_PROGRESSIVE = [
    "dang xu ly", "de minh tra", "de minh kiem tra", "se tiep tuc",
    "tiep tuc kiem tra", "cho minh it phut",
]
# NO " ma " (mã — code) here any more — [MEASURED 04/09] `_strip_diacritics()` collapses
# ALL of "ma/má/mạ/mả/mã/mà" into the same string "ma", so "mã" (case number) and "mà" (a
# conjunction — one of the most common words in Vietnamese, e.g. "...của bạn MÀ chưa rõ...")
# collide, wrongly catching swathes of valid soft+continuing sentences. "mã" is now checked
# separately on the ORIGINAL accented `reply` in `claims_ticket_created` (safe: the function only
# receives text the AGENT generated itself, not abbreviated/unaccented customer input).
_O5_STRONG_CONFIRM_ASCII = ["thanh cong", "xong"]


def claims_ticket_created(reply: str) -> bool:
    """Does this sentence CLAIM that a ticket/case HAS BEEN CREATED — with or without a code.

    🔴 DIFFERS from `_match_o5` in EXACTLY ONE POINT, and that point is the whole reason this
    function exists: O5 **steps aside** when the sentence includes a code, because its comment
    declares the assumption *"O3 already covers every wrong/fabricated-code case"*.
    [MEASURED 25/08] **that assumption is WRONG**:
        `_CODE_TOKEN = r"[A-Za-z0-9]{7,}"`
        "CMP-00003" → the `-` cuts it into "CMP" (3) + "00003" (5) → BOTH below the threshold
        ⟹ O3 is COMPLETELY BLIND to that code shape
    Every REAL code in the system (`TCK-…12 hex`, `TXN…14 digits`, `RES-…`) has ≥7 contiguous
    characters, so this gap only opens for **FABRICATED** codes — and nobody trips on it until
    the model really fabricates one.
    Measured consequence: **adding a fake code to a sentence made it SAFER in the filter's eyes.**

    ⟹ This function DELIBERATELY grants **no** code-based exemption — having a code (real or
    fabricated) never makes the function return `False`; it can only push TOWARDS `True` (see
    the SOFT branch below). It only answers *"does it claim creation"*; checking against the
    REAL `ticket_id` is the job of the calling layer (`graph.py`), the only place that knows the
    truth. This is hard constraint 3 enforced by FACTS, not vocabulary — so it doesn't inherit
    the ceiling of word matching that the `_match_o5` comment declared.

    🔴 04/09 — HARD/SOFT split (see `_O5_STRONG_VERBS`/`_O5_SOFT_VERBS` above): HARD verbs
    ("tạo/mở/lập" — create/open/draw up) are always `True` with an object — OLD behaviour,
    unchanged. SOFT verbs ("ghi nhận/tiếp nhận" — note/receive) need 1 of 2 extra conditions:
    a REAL CODE (accented), or NO continuing sentence ("đang xử lý tiếp" — still processing...)
    to be `True`; continuing with no code gives `False` (exactly the case QA caught).

    The order inside the SOFT branch is DELIBERATE — code/success is checked BEFORE continuing,
    so a sentence with both a code and continuing ("...mã KN-00042, đang xử lý tiếp nhé" —
    code KN-00042, still processing) is still `True` (the code WINS, not "washed away" by the
    continuing sentence).

    ⚠️ TWO DECLARED TRADE-OFFS (Review + Coder, 04/09) — not hidden holes; later readers, DON'T
    assume there's only one direction:
    1. The code/"thành công" (success) check is REPLY-GLOBAL (not limited to the clause containing
       the soft verb) — it can only make the function OVER-ZEALOUS, attaching an EXTRA `True` to
       a soft sentence whose code/"success" sits in an unrelated clause.
       It can NEVER let a real hallucination through (the safe direction — false positive >
       false negative, per the principle at the top of the file).
    2. The `" mã "` check reads the ORIGINAL accented `reply`, NOT via `_strip_diacritics()` — if
       the model (rarely, never seen across dozens of real LLM examples) happened to GENERATE
       "mã" without its accent inside an otherwise fully accented sentence, that sentence would
       fall into the continuing branch instead of the code being caught — the OPPOSITE direction
       to trade-off ① (it could MISS rather than falsely catch). Accepted because the function
       only receives agent-generated text (not abbreviated/unaccented customer input), and
       avoiding it would reopen the far more common "ma/má/mạ/mả/mã/mà" collision.
    """
    md = _strip_diacritics(reply)
    if any(t in md for t in _O5_GENERIC_DESCRIPTIONS):
        return False
    if not any(d in md for d in _O5_OBJECTS):
        return False
    if any(v in md for v in _O5_STRONG_VERBS):
        return True
    if any(v in md for v in _O5_SOFT_VERBS):
        has_real_code = " mã " in f" {reply.lower()} "
        if has_real_code or any(x in md for x in _O5_STRONG_CONFIRM_ASCII):
            return True
        if any(t in md for t in _O5_PROGRESSIVE):
            return False
        return True
    return False


def _match_o5(reply: str) -> bool:
    # 🔴 Review round 2 (24/08, checking a95f8f0) — [MEASURED] requiring "customer address" in the
    # SAME CLAUSE as verb+object LETS THROUGH a whole family of natural CSKH closing sentences:
    # "Bạn yên tâm nhé. Đã tạo hồ sơ khiếu nại rồi." (Don't worry. The complaint case has been
    # created.) — the pronoun is in the PREVIOUS sentence (reassurance), verb+object in the CLOSING
    # sentence (fact), exactly the "separate the emotional sentence from the factual one" pattern
    # that
    # several other prompt.py rules force the agent to follow — `_split_clauses` CANNOT merge them
    # back.
    # "Customer address" now checks the WHOLE REPLY (as `_CODE_TOKEN` already does at the end of the
    # function) — [MEASURED] confirmed the review's 2 original false-positive cases (general/past
    # descriptions that mention the customer NOWHERE in the reply) still have no customer address
    # after the change; the old hole is not reopened.
    #
    # ⚠️ REMAINING LIMITATION, DELIBERATELY NOT FIXED (raised by the review; agreed to expose rather
    # than hide): a sentence with NO pronoun at all ("Đã tạo hồ sơ khiếu nại rồi nhé." — The
    # complaint
    # case has been created.) still SLIPS THROUGH — with no "bạn/anh/chị/mình/quý khách" anywhere in
    # the reply, changing the scope can't save it. The alternative signal (the particles "nhé"/"ạ")
    # carries its own false-catch risk and needs separate measurement before being added — DON'T
    # guess
    # in advance, per Rule M. This is a DECLARED trade-off, not a hidden hole.
    #
    # ⚠️ SECOND LIMITATION, DELIBERATELY STOPPING HERE (the review shot back at `_O5_GENERIC_
    # DESCRIPTIONS` after the fix, 24/08): one of the 4 general-description words used in a
    # DIFFERENT
    # sense (a time reference within the conversation/the customer's PERSONAL frequency, not
    # "general
    # matters/many other customers") in the SAME clause as the closing sentence also SLIPS THROUGH —
    # "Mình đã tạo hồ sơ khiếu nại cho bạn như đã hứa trước đây rồi nhé." (I've created the
    # complaint
    # case for you as promised earlier.), "...thấy trường hợp này xảy ra thường xuyên với bạn."
    # (...I see
    # this happens to you frequently.) Word matching can't distinguish MEANING, only PRESENCE —
    # three
    # consecutive fix rounds with the same failure shape (customer-address same-clause ->
    # whole-reply
    # -> word-based exclusion) prove the CEILING of the word/position-matching approach, not a
    #  single
    # remaining hole. STOP patching here — the surface is now so narrow that it needs exactly a rare
    # combination, O5 is only the last net for ONE narrow gap (O3 already covers every
    # wrong/fabricated
    # code), and the principle at the top of the file accepts controlled misses. Closing it for good
    # needs a real SEMANTIC signal, not a fourth exclusion list — left for the PO-agent/Security to
    # weigh whether a different direction is worth investing in.
    addresses_customer_anywhere = _marker_positions(_strip_diacritics(reply), _O5_CUSTOMER_ADDRESS) is not None
    has_completion_clause = False
    for md in _split_clauses(_strip_diacritics(reply)):
        if any(p in md for p in _O4_NEGATIONS):
            continue
        if any(p in md for p in _O5_GENERIC_DESCRIPTIONS):
            continue
        has_verb = _marker_positions(md, _O5_COMPLETION_VERBS) is not None
        has_object = _marker_positions(md, _O5_OBJECTS) is not None
        if has_verb and has_object and addresses_customer_anywhere:
            has_completion_clause = True
            break
    if not has_completion_clause:
        return False
    # The whole REPLY, not just the clause under consideration — the code may be in another
    # sentence of the same reply ("Mình đã tạo hồ sơ cho bạn. Mã của bạn là KN-..." — I've created
    # your case. Your code is KN-...).
    # The original `reply` (not diacritic-stripped) — _CODE_TOKEN only matches [A-Za-z0-9];
    # Vietnamese
    # diacritics don't fall into that character class, so no prior normalisation is needed.
    return not _CODE_TOKEN.search(reply)


# ---------------------------------------------------------------- public
def filter_output(
    reply: str,
    *,
    source: str,
    customer_message: str = "",
    customer_text: str = "",
    thread_id: str = "",
    correlation_id: str | None = None,
) -> tuple[str, list[str]]:
    """Returns (filtered_reply, list_of_matched_groups).

    Match -> REPLACE with a meaningful safe sentence, NEVER silently cut: a truncated reply is
    more confusing to the customer than a polite refusal.
    """
    if not reply:
        return reply, []

    matched = []
    if _match_o1(reply):
        matched.append("O1")
    if _match_o2(reply):
        matched.append("O2")
    o3_matched, o3_shape = _match_o3(reply, customer_message, source, customer_text)
    if o3_matched:
        matched.append("O3")
    if _match_o4(reply):
        matched.append("O4")
    if _match_o5(reply):
        matched.append("O5")

    if not matched:
        return reply, []

    # STRUCTURED log, NEVER the verbatim reply: a reply matching O3 almost certainly contains
    # masked data — logging it would leak exactly what was just blocked, by our own hand.
    # Fix C: when O3 blocks, add the SHAPE of the unknown sequences (count/length/has letters/
    # date-shaped) + whether this turn's payload is empty — SHAPE ONLY, NO values, NO hashes of
    # values
    # (a hash can still be matched back to the real value).
    _logger.warning(
        "output_filter_khop",
        extra={
            "nhom": ",".join(matched),
            "correlation_id": correlation_id,
            "do_dai_reply": len(reply),
            **(o3_shape if o3_matched else {}),
            **({"o3_payload_luot_nay_rong": _turn_payload_empty(source)} if o3_matched else {}),
        },
    )
    # Counted per thread — SHARING infrastructure with ES-xx (5a) and guardrail 5c.
    # Several matches within one conversation is exactly the sign of a Crescendo attack in progress.
    if thread_id:
        for phrase_group in matched:
            thread_signals.bump(f"OUT-{phrase_group}", thread_id)

    return SAFE_FALLBACK_REPLY, matched


# ---------------------------------------------------------------- O2-B: COUNTING
# LISTING DENSITY — COUNT, DON'T BLOCK (decided by security, approved by the PO).
#
# Solves exactly the point where I once said "no machine-checkable definition": instead of
# comparing meaning against the prompt (impossible), COUNT THE NUMBER OF DIFFERENT rule TOPICS
# appearing in one reply, via a FIXED list of anchors.
#
# Why a threshold of 3 rather than 1: constraint 7 forbids LISTING THE SET of rules, NOT revealing
# ONE limitation. The agent is even ORDERED to state its limitations (constraints 1+8) — "mình
# không tự quyết được việc hoàn tiền" (I can't decide on refunds myself) is a BUSINESS-CORRECT
# sentence and must be said. 1-2 anchors = a normal explanation; >=3 in one reply = reciting the
# rulebook, and that is what's worth counting.
#
# COUNT rather than BLOCK: blocking here would block exactly the sentences where the agent
# explains its limits to the customer — breaking usability right where the product needs it
# most. Several counts within one conversation are the real signal (gradual Crescendo
# extraction), and that is the job of the per-thread guardrail, not the sentence filter.
_RULE_ANCHORS = {
    k: KC.phrase(*v) for k, v in {
        "khong_quyet_tien": ["khong tu quyet", "khong the tu duyet", "phai co nguoi duyet", "khong duoc hoan tien truc tiep"],
        "khong_bia_so": ["khong bia", "chi dua tren du lieu", "phai tra cuu duoc"],
        "pdpa_ben_thu_ba": ["thong tin nguoi khac", "ben thu ba", "khong cung cap thong tin ca nhan"],
        "khong_ket_luan_gian_lan": ["khong ket luan gian lan", "khong khang dinh la lua dao"],
        "otp": ["khong hoi mat khau", "khong hoi otp giao dich", "otp phien"],
        "phan_loai": ["4 loai khieu nai", "phan loai khieu nai", "pham vi giao dich"],
        "tai_lieu_tham_khao": ["chi la tham khao", "tai lieu tham khao"],
        "xung_ai": ["toi la tro ly ao", "minh la tro ly ao", "toi la ai"],
        "khong_tiet_lo_huong_dan": ["khong the chia se huong dan", "khong tiet lo quy trinh noi bo"],
    }.items()
}
LISTING_THRESHOLD = 3


def count_listing_density(reply: str) -> int:
    """Number of different rule TOPICS in the reply. Doesn't block, only counts."""
    clean_text = _strip_diacritics(reply)
    return sum(1 for phrase in _RULE_ANCHORS.values() if KC.match_any(phrase, clean_text))


# ------------------------------------------------ O2-C: THE **PROCESS** ANCHOR FAMILY
# (security `docs/security/mo-neo-quy-trinh-cho-O2.md`, approved by the PO.)
#
# THE HOLE IS IN THE MEASURING TOOL, NOT THE FILTER — and that is the more dangerous category.
# All 9 anchors above belong to the PRINCIPLES family; none belongs to the STEPS family. Yet
# constraint 7 of the system prompt forbids reciting BOTH the "Mandatory constraints" AND the
# "Investigation process". Measured (security, build `5f643f71ddb5`): a sentence listing the
# principles counts 3; two sentences reciting the process verbatim count **0**.
#
# Why a blind measuring tool is more dangerous than a leaky filter: the density distribution
# would say "no problem", and the proposition "count first, ESCALATE TO BLOCKING when leaks are
# seen" becomes **empty** — exactly what the "O2 counts first, blocks later" decision was meant
# to eliminate.
#
# TWO SIMULTANEOUS CONDITIONS, and this is where the principles family's counting must NOT be
# copied over: STEPS are something the agent LEGITIMATELY says EVERY DAY when telling the customer
# what it is doing ("mình sẽ tra cứu giao dịch rồi tạo hồ sơ" — I'll look up the transaction and
# then create a case = 2 steps, and it must always stay silent). The distinction is NOT in
# MENTIONING a step, but in PRESENTING A CHAIN OF STEPS AS A PROCESS.
_STEP_ANCHORS = {
    k: KC.phrase(*v) for k, v in {
        "buoc_phan_loai": ["xac dinh loai khieu nai", "phan loai khieu nai", "thuoc loai nao", "xac dinh loai van de"],
        "buoc_tra_lich_su": ["tra lich su giao dich", "lich su giao dich", "cac giao dich gan day", "xem giao dich gan day"],
        "buoc_tra_giao_dich": ["tra cuu giao dich", "tra ma giao dich", "doi chieu so tien", "kiem tra giao dich"],
        "buoc_hoi_lai": ["hoi lai de thu hep", "hoi them thong tin", "hoi ban them", "hoi ro hon"],
        "buoc_tao_ho_so": ["tao ho so", "tao ticket", "lap phieu khieu nai", "tao phieu khieu nai"],
        "buoc_bao_ket_qua": ["bao ma ticket", "bao moc xu ly", "thong bao sla", "ma ho so cua ban", "thoi han xu ly"],
        "buoc_chuyen_nguoi_that": ["chuyen chuyen vien", "gap nguoi that", "chuyen nhan vien", "chuyen sang nguoi that"],
    }.items()
}
# (B) SIGNS OF PRESENTING-AS-A-PROCESS. (B) alone is NOT enough: "quy trình tra soát với ngân
# hàng mất 5-7 ngày" (the investigation process with the bank takes 5-7 days) has (B) but no steps
# -> silent.
_PROCESS_HINTS = KC.phrase(
    "quy trinh", "cac buoc", "gom:", "trinh tu", "buoc 1", "buoc mot",
    "thu nhat", "minh duoc huong dan", "quy dinh cua minh", "minh lam theo",
)
# "đầu tiên … sau đó" (first … then) is a SEQUENCE marker, so it only counts when BOTH halves
# are present — "đầu tiên" alone could appear in any sentence.
_SEQUENCE_PAIRS = (KC.phrase_pattern("dau tien"), KC.phrase_pattern("sau do"))
# Threshold 2 (not 3 as for the principles family) because (B) already does the filtering:
# a presenting-a-process sign PLUS two steps is already reciting the process.
PROCESS_THRESHOLD = 2


def count_process_density(reply: str) -> int:
    """Number of different STEPS — but ONLY when the sentence is presenting them as a process.

    Returns 0 without sign (B), even with many steps: that is security's mandatory negative
    case, and it protects exactly the sentences where the agent tells the customer what it is
    doing.
    """
    clean_text = _strip_diacritics(reply)
    has_b = KC.match_any(_PROCESS_HINTS, clean_text) or all(m.search(clean_text) for m in _SEQUENCE_PAIRS)
    if not has_b:
        return 0
    return sum(1 for phrase in _STEP_ANCHORS.values() if KC.match_any(phrase, clean_text))


def instruction_leak_signal(reply: str, *, thread_id: str = "") -> dict[str, int]:
    """The two families are counted SEPARATELY, recorded under ONE key per `thread_id`.

    One shared key because the goal is detecting *a conversation that is extracting
    instructions*, regardless of whether it extracts principles or process — a gradual
    extractor (Crescendo) has no reason to stick to one family. Counted separately because the
    two families have different thresholds, and mixing them into one number loses the ability
    to tell which family it is blind to — exactly the bug just fixed here.

    STILL ONLY COUNTS, NEVER BLOCKS (the O2 decision stands).
    """
    principle = count_listing_density(reply)
    process = count_process_density(reply)
    if thread_id and (principle >= LISTING_THRESHOLD or process >= PROCESS_THRESHOLD):
        thread_signals.bump("OUT-LO-CHI-THI", thread_id)
    return {"nguyen_tac": principle, "quy_trinh": process}
