"""ES-xx emotion signals — SERVICE LAYER, deterministic rules (ADR-022, signed by the PO 15/08).

NOT YET WIRED INTO THE HOT PATH. This file only computes signals; adding `goi_y_handoff`
(handoff suggestion) to the envelope and raising ticket priority is a separate step, done
after the tester finishes the baseline measurement round (a clean before/after pair is
needed).

Three constraints inherited from ADR-022, repeated because they drive the whole design:
  · NO LLM calls. Not a single extra round trip on the hot path.
  · NOT in the prompt. The agent never SAYS it sees the customer is upset
    — that would be the agent asserting a psychological conclusion about a person based on a
    classifier that may be wrong (the spirit of hard constraint 3).
  · NO stored labels. Only numeric counters, in Redis, with a TTL (see thread_signals.py).

THE BIGGEST TRAP IN THIS DOMAIN — BUSINESS VOCABULARY OVERLAPS ANGRY VOCABULARY
------------------------------------------------------------------------------
This is an agent handling FRAUD COMPLAINTS. Phrases like "em bị lừa đảo" (I was scammed),
"bị mất tiền" (lost money), "bị trừ tiền oan" (wrongly charged) are DESCRIPTIONS OF THE CASE
— they appear in almost every legitimate conversation, even when the customer is completely
calm. Putting those words into an anger dictionary would make ES-01 fire on most real cases,
and the signal would lose all meaning: a signal that is always on is not a signal.

So the dictionary here DELIBERATELY contains only language aimed at the SERVICE/STAFF
("what kind of business is this", "irresponsible", "outrageous"), not language describing
the EVENT. This is exactly the bug class the current injection filter suffers from in the
opposite direction — the `tu dong hoan tien` (automatic refund) pattern also blocks real
policy sentences. Same lesson: when attack/anger vocabulary overlaps business vocabulary,
the word list must be chosen by the TARGET being addressed, not by topic.
"""
from __future__ import annotations

import re
import unicodedata

from src.services import thread_signals

# ES-01 threshold N — fixed by the real PO on 15/08 as a WORKING VALUE, to be retuned once
# the tester's multi-turn suite has numbers. Kept here (not scattered through the logic) so
# the next adjustment touches one place only.
ES01_CONSECUTIVE_TURNS = 3

ES01 = "ES-01"
ES02 = "ES-02"


def _strip_diacritics(text: str) -> str:
    """Same approach as `_strip_diacritics` in customer_tools/fraud_engine — match on the
    diacritic-stripped form so it doesn't depend on whether the user typed accents. Lesson
    ADV-041: a pattern written WITH diacritics lets text typed WITHOUT them slip through."""
    text = text.lower().replace("đ", "d")
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


# Language aimed at the SERVICE/STAFF. NO "lua dao" (scam), "mat tien" (lost money),
# "tru tien oan" (wrongly charged)... — those describe the case, see the docstring.
_FRUSTRATION_PATTERNS = [
    r"lam an (kieu gi|nhu the nao|the nay)",
    r"vo trach nhiem",
    r"qua dang",
    r"khong the chap nhan",
    r"te (hai|that)|qua te|chan (that|qua)",
    r"(doi|cho) (gap|noi chuyen voi) (quan ly|nguoi co trach nhiem|cap tren)",
    r"bao nhieu lan (roi|nua)",
    r"(hoi|noi) may lan roi",
    r"lam mat thoi gian",
    r"khong ai (giai quyet|tra loi|xu ly)",
]

# ES-02 — BUSINESS crisis. Fixed by the real PO: does NOT cover psychological distress.
# If you are about to add patterns for that group, stop and read `khong_bao_gom`
# (not included) in contracts/resolution-state-machine.yaml first.
_CRISIS_PATTERNS = [
    r"(bo|xoa|go|khong dung) (vi|app|ung dung) (nay )?(nua|luon)",
    r"dong (tai khoan|vi)",
    r"chuyen sang (vi|app|ngan hang) khac",
    r"(se |sap )?kien",
    r"luat su",
    r"(bao|dang|len) (bao chi|bao|facebook|mang xa hoi|tiktok)",
    r"phan anh len (ngan hang nha nuoc|cong an|bao ve nguoi tieu dung)",
]

_RE_FRUSTRATION = [re.compile(p) for p in _FRUSTRATION_PATTERNS]
_RE_CRISIS = [re.compile(p) for p in _CRISIS_PATTERNS]

# INTENSITY MARKERS (all-caps sentences, "!!!") — CONSIDERED AND DROPPED in v1; recorded
# so a later session doesn't think it was an oversight and add them:
#   · On their own they DO NOT indicate anger. Many people type in all caps out of phone
#     keyboard habit, and older people often use "!!!" as a normal sentence ending. Using them
#     as an independent signal labels people by typing style.
#   · ALONGSIDE a reproach pattern they add no information either: the pattern is already
#     enough to count the turn as strongly negative; intensity only makes the condition
#     stricter without it being clear that stricter is more correct — and "not clear it is
#     more correct" is not enough basis for a routing signal.
# If the tester's multi-turn suite later shows ES-01 firing too early, intensity is the first
# parameter to try — but there must be NUMBERS first, not additions by gut feeling.


def turn_has_frustration(message_text: str) -> bool:
    """Whether ONE turn carries a strongly negative label. NOT ES-01 —
    ES-01 needs ≥N CONSECUTIVE turns, see `evaluate_turn`."""
    if not message_text:
        return False
    clean_text = _strip_diacritics(message_text)
    return any(r.search(clean_text) for r in _RE_FRUSTRATION)


def turn_has_crisis(message_text: str) -> bool:
    """ES-02 fires within ONE turn — threatening to leave/sue/post publicly
    needs no escalation, it is already the peak."""
    if not message_text:
        return False
    return any(r.search(_strip_diacritics(message_text)) for r in _RE_CRISIS)


def evaluate_turn(message_text: str, thread_id: str) -> set[str]:
    """Compute the ES signals for ONE customer turn. Returns the set of active codes.

    This is where the "CONSECUTIVE" semantics of ES-01 are enforced: a turn WITHOUT
    frustration calls `reset()` on the counter. Without that line, what gets counted is
    "total frustrated turns in the conversation" — a customer who gets upset, calms down and
    gets upset again still hits the threshold of 3 while not escalating at all, and ES-01
    loses exactly the meaning of its name.

    NEVER raises: thread_signals already fails open, and this function sits on the chat
    turn's hot path.
    """
    is_enabled: set[str] = set()

    if turn_has_frustration(message_text):
        if thread_signals.bump(ES01, thread_id) >= ES01_CONSECUTIVE_TURNS:
            is_enabled.add(ES01)
    else:
        thread_signals.reset(ES01, thread_id)

    # ES-02 does NOT use the counter: threatening to leave/sue/post publicly is already the peak
    # on the very first turn, no escalation needed. Counting it would force the customer to
    # threaten three times before being heard.
    if turn_has_crisis(message_text):
        is_enabled.add(ES02)

    return is_enabled
