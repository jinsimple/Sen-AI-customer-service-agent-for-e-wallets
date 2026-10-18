"""Vietnamese PHRASE matching that TOLERATES INSERTED FUNCTION WORDS — fixes a WHOLE CLASS
of bugs, rather than patching case by case.

Three bugs of the same family before this file existed (security 2fc55b0 named it on the
third occurrence, and it really is one family):

    F-24  the injection pattern allowed exactly ONE modifier word
          -> "ignore ALL PREVIOUS instructions", the MOST common injection, slipped through
    F-27  O1 required the literal word "OTP"
          -> "the supervisor must request a separate code, expiring after 10 minutes"
             slipped through, even though it leaked the exact config value
             RESOLUTION_APPROVAL_OTP_FRESH_MINUTES
    O2    the anchor required an ADJACENT phrase
          -> "mình cũng KHÔNG ĐƯỢC kết luận gian lận" ("I am also NOT ALLOWED to conclude
             fraud") counted 0, despite carrying exactly the anchor's meaning

Same shape every time: **the pattern matches how WE IMAGINE people talk, and misses how
PEOPLE ACTUALLY talk.** And the key point, the one that makes this a class bug rather than
three stray ones: inserting function words between components is **ordinary Vietnamese
grammar**, not an evasion trick. "không kết luận" -> "không ĐƯỢC kết luận" -> "cũng
KHÔNG BAO GIỜ kết luận" ("don't conclude" -> "not ALLOWED to conclude" -> "also NEVER
conclude"). Ordinary writers insert these words naturally. So an adjacency-requiring
pattern is wrong on **the normal case**, not only the attack case — it both misses
attackers and mis-measures real customers.

DESIGN PROPERTY — PURELY ADDITIVE, provable rather than hoped for:
with 0 function words, `_GAP` reduces to `\\s*`, so the new pattern matches EVERYTHING the
old pattern (substring match with exactly one space) matched, plus the inserted-word and
run-together variants. Consequence for reviewers: Rule 18 **cannot cause extra misses**, but
**can cause extra blocks** — so every place it is applied on a BLOCKING path must come with
negative-case counts.

DELIBERATELY EXCLUDED: group O4 (`_O4_VERBS/_O4_MONEY/_O4_CUSTOMER_ADDRESS`). O4 matches on
ORDERED word boundaries and is the group with the most false blocks historically — 4/5 of
the remaining false blocks in the previous round came from a single word ("hoan" inside
"khoang"). Loosening there loosens the thinnest spot. This is a decision, not an oversight.
"""
from __future__ import annotations

import re

# Function words allowed to be inserted — written WITHOUT DIACRITICS because every caller
# compares on diacritic-stripped strings. The list is DELIBERATELY SHORT and contains only
# function words: a false positive would require the phrase's CONTENT words to appear in the
# right order separated only by these words — at which point the sentence already carries
# the phrase's meaning.
#
# DO NOT add content words here. "hoan"/"toan" ("hoàn toàn", "completely") were excluded on
# purpose: "hoan" is an O4 MONEY token; making it a function word would open a bridge between
# two unrelated clauses.
FILLER_WORDS = (
    "duoc", "phai", "se", "cung", "nen", "can", "luon", "van",
    "bao", "gio", "he", "the", "tuyet", "doi", "da", "dang",
)
# SECOND FAMILY — quantifiers / determiners. Separated from function words because they
# insert in different places ("bỏ qua TOÀN BỘ ràng buộc" — "ignore ALL constraints" — rather
# than "không ĐƯỢC kết luận"), but it is the same class bug: F-24 had to hand-list
# `(moi |tat ca |cac |nhung |truoc do |o tren )*` — and **missed "toàn bộ"** ("entire"), so
# "bỏ qua toàn bộ hướng dẫn" ("ignore the entire instructions") did NOT match in build
# 5f643f71. A perfect illustration of why hand-listing loses: every list misses exactly the
# word someone is about to type.
MODIFIER_WORDS = (
    "moi", "tat", "ca", "toan", "bo", "cac", "nhung", "truoc", "do",
    "o", "tren", "phia", "ben", "het", "sach",
)
# Ceiling of 4 tokens between two components: enough for "cũng không bao giờ" (3) and
# "tất cả các" / "toàn bộ các" (3); any higher and the two components are so far apart that
# they are no longer one phrase.
MAX_FILLER_WORDS = 4

# `\s*` rather than `\s+`: run-together strings ("bo qua" -> "boqua") are exactly what the
# second comparison pass of `_match_pattern` (customer_tools) exists to catch, and there the
# pattern goes through `.replace(" ", "")`, so every LITERAL space disappears. `_GAP` contains
# no literal space -> it survives that replace and still matches correctly.
GAP = (
    r"\s*(?:(?:" + "|".join(FILLER_WORDS + MODIFIER_WORDS) + r")\s*){0,"
    + str(MAX_FILLER_WORDS) + r"}"
)


def phrase_pattern(phrase: str) -> re.Pattern[str]:
    """One PHRASE (words separated by spaces) -> a regex that tolerates inserted function words.

    Use for PLAIN-TEXT phrase lists. For hand-written regexes with groups/alternation,
    don't call this — insert `GAP` directly at the right join point in the pattern, because
    mechanically replacing every space would also hit spaces inside alternation groups.
    """
    return re.compile(GAP.join(re.escape(t) for t in phrase.split()))


def phrase(*cac_cum: str) -> tuple[re.Pattern[str], ...]:
    return tuple(phrase_pattern(c) for c in cac_cum)


def match_any(pattern: tuple[re.Pattern[str], ...], text: str) -> bool:
    return any(m.search(text) for m in pattern)
