"""PII scrubbing — MUST run BEFORE data is logged or sent to the trace backend (Jaeger)
— phase 3 of the observability checklist. Applies to all free text that may contain PII
before it goes into a JSON log or span attribute: customer messages, agent replies,
tool args/results.

🔴 TWO EXPLICIT REGISTRIES, not one filter-afterwards registry (Security phase 4,
19/08; review anchor: read together with docs/security/2026-08-19-gd4-dinh-hang-scrub-
pii-model-input.md + docs/giao-viec/2026-08-19-gd4-po-test-4-loi-ui.md).
`scrub_pii()` takes a MANDATORY `purpose` parameter (no default):

  - `"model_input"` — data GOING OUT to the LLM provider (`graph.py:787`).
    NARROW registry: does NOT load SpacyRecognizer/DateRecognizer/PhoneRecognizer
    (generic)/MedicalLicenseRecognizer — keeps only VN_PHONE_NUMBER/VN_ID_NUMBER
    (hand-written regex) + underthesea PERSON_VN + the rest of the Presidio catalog
    (Email/Iban/Crypto/Ip/Url/MacAddress). QA/QC measured a 124-sentence corpus
    (golden_set.jsonl, 19/08): the distortion rate went from 50.0% → 5.6% after dropping
    those three recognizers — the generic PhoneRecognizer matches ANY phone-like DIGIT STRING
    (unlike the narrow VN_PHONE_NUMBER), DateRecognizer matches YYYYMMDD, which collides
    with the internal transaction ID format (`TXN20260810...`), and Spacy guesses
    PERSON/LOCATION/ORGANIZATION from context — all three were the main sources of
    distortion, not rare edge cases.
  - `"log"` — EVERYWHERE else (trace/span attributes, the `resolutions.note` typed by CSKH).
    FULL registry, kept EXACTLY as originally designed — over-redaction here is an
    ESTABLISHED POLICY (see "REAL FINDINGS" below), NOT loosened by the decision above.

WHY TWO SEPARATE REGISTRIES (built separately, not load-everything-then-filter-results):
the two holes fixed on the same day (Spacy forgetting to apply `_plausible_person_span`,
MEDICAL_LICENSE slipping into the registry) both had the same shape: "forgot to filter for
one particular branch". A registry that NEVER LOADS the extra recognizers in the first place
has nothing to forget to filter later — removing that kind of risk at the root instead of
adding yet another runtime check (just as easy to forget as the previous two).

"Tuần" (decision (b), Security + Lead 19/08): STILL kept in the NER stoplist even though it
IS a valid real Vietnamese personal name — it is used as a time word ("tuần sau" = next week,
"tuần trước" = last week) far more often than as a proper name in e-wallet customer-service
contexts. This is a DECLARED TRADE-OFF, not a bug: a customer named "Tuần" saying
"Mình là Tuần" (I'm Tuần) will NOT be masked (see `_WORDS_MISTAKEN_FOR_NAMES` for the
check you must ask yourself before adding a new word to that list).

**Microsoft Presidio** (`presidio-analyzer`) is the main engine — decided 2026-08-10,
replacing the earlier decision (calling spaCy directly): the product's customer PII detection
will expand to more PII types over time (card numbers, IBAN, crypto wallets, IP...), and
Presidio ships a recognizer catalog for those — adding a new PII type later just means
registering one more `PatternRecognizer`, instead of hand-writing a regex scan for each.
Presidio itself uses spaCy as its internal NLP engine (still the `xx_ent_wiki_sm` model
verified earlier), and comes with EmailRecognizer/PhoneRecognizer/IbanRecognizer/
CryptoRecognizer/IpRecognizer/UrlRecognizer/DateRecognizer — no need to hand-write those
"future" types any more.

ONLY `presidio-analyzer` (detection) is used, NOT `presidio-anonymizer` (masking/replacement)
— the real reason, found during installation: `presidio-anonymizer` pins
`cryptography<49.0.0`, DOWNGRADING to a version with 3 known CVEs (PYSEC-2026-3552/3553/
3554), while the project uses `cryptography>=50.0.0` for field encryption at rest
(`src/db/crypto_types.py`). Doing the character replacement ourselves (already present and
carefully verified) is far cheaper than accepting a known vulnerability in the core crypto
library — not worth it.

A hand-written `PatternRecognizer` is still kept for Vietnamese phone/ID-card/old-ID/bank
account numbers (Presidio has no dedicated recognizer for Vietnamese formats) — registered
TOGETHER in one `AnalyzerEngine` with the built-in recognizers, not as 2 separate tiers as
in the previous design.

**Vietnamese personal-name NER (decision 2026-08-11, after finding a real gap in the
previous version):** the `SpacyRecognizer` inside Presidio uses a small multilingual model
(`xx_ent_wiki_sm`) — NOT specialised for Vietnamese, missing many Vietnamese names (concrete
case: "Anh Lê Hoàng Nam..." — see the history of tests/test_observability/test_pii.py). A
`_VietnameseNameRecognizer` (a hand-written `EntityRecognizer` calling `underthesea.ner()`)
was added as a COMPLEMENT to `SpacyRecognizer`, NOT a replacement — the 2 recognizers run in
parallel and results are merged via the existing `_merge_overlapping`. underthesea catches
cases spaCy misses, but a REAL FINDING during verification: it labels B-PER (wrongly) on a
few strings that aren't names — prefixed numeric transaction IDs (`TXN20260810000123`) and
all-caps abbreviations (`CCCD`). These 2 false-positive kinds are filtered with simple rules,
not a hard-coded prefix list (real Vietnamese names contain no digits and are not all caps)
— see `_plausible_person_span()`.

REAL FINDINGS during verification (see tests/test_observability/test_pii.py) — recorded
honestly, without sugar-coating:
  - `SpacyRecognizer` quite often assigns the WRONG entity type to personal names (LOCATION/
    ORGANIZATION instead of PERSON). Since the goal is MASKING (not classification), the
    scrubber masks using EXACTLY the type Presidio returns (without forcing PERSON) —
    over-redaction accepted, not loosened to reduce false positives, per the phase-3
    checklist principle.
  - underthesea still misses some names (case "Trần Thị Bích" — but that case IS caught
    separately by `SpacyRecognizer`, so the merged pipeline still masks it correctly; a
    concrete example of why BOTH recognizers are kept rather than one replacing the other).
    No case where both recognizers miss has been recorded so far — if one appears, update
    this note rather than silently leaving it.
  - Graceful degradation: missing `presidio-analyzer`/`underthesea` (not installed) or an NER
    model failing to load → falls back to ONLY the Vietnamese regex layer (hand-written
    basic phone/ID/email) instead of crashing the app. A failure loading
    `_VietnameseNameRecognizer` alone does not bring down the whole `AnalyzerEngine` —
    `SpacyRecognizer` + the rest of the Presidio catalog keep working normally.
"""
from __future__ import annotations

import functools
import logging
import re
from typing import Literal

_logger = logging.getLogger("fin05.observability.pii")

# "model_input" = NARROW registry (D'), data going out to the LLM provider.
# "log" = FULL registry, everywhere else (trace/span, resolutions.note).
ScrubPurpose = Literal["model_input", "log"]

# --- Regex fallback (NO Presidio needed) — used when presidio-analyzer isn't installed /
# fails to load; keeps the 3 most clearly structured PII types at minimum. ---------------
_FALLBACK_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_FALLBACK_PHONE_RE = re.compile(r"(?<![\w-])(?:\+84|0)\d{9}(?!\d)")
_FALLBACK_ID_RE = re.compile(r"(?<![\w-])\d{9,19}(?!\d)")


def scrub_regex(text: str) -> str:
    """Regex layer only — used in tests specifically to PROVE why the NER layer is needed
    (free-form personal names will SLIP through this layer), and as a fallback when Presidio
    is unavailable. DO NOT use directly for real logs (use `scrub_pii`)."""
    out = _FALLBACK_EMAIL_RE.sub("[EMAIL]", text)
    out = _FALLBACK_PHONE_RE.sub("[PHONE]", out)
    out = _FALLBACK_ID_RE.sub("[ID_NUMBER]", out)
    return out


# Vietnamese phone/ID-card/old-ID/bank account numbers — Presidio has no dedicated
# recognizer for Vietnamese formats, so they are registered into the shared registry. Same
# pattern verified in the previous version (internal IDs with letter prefixes like
# TXN.../TCK... are left unmasked — they are lookup codes, not PII).
#
# Upper bound 14 -> 19 (ADR-024, measured while building scrub-at-write for
# `resolutions.note`): "thẻ 9704123456789012" (card, 16 digits) slipped through the 14-digit
# version intact — no Presidio recognizer catches card numbers that don't follow the
# international Luhn/BIN format. 19 is the maximum card-number length under ISO/IEC 7812;
# Vietnamese bank account numbers (up to 14 digits) stay within the old range, so behaviour
# is unchanged for them.
_VN_PHONE_REGEX = r"(?<![\w-])(?:\+84|0)\d{9}(?!\d)"
_VN_ID_REGEX = r"(?<![\w-])\d{9,19}(?!\d)"

# "Free" NER labels — the entity type is guessed from CONTEXT (SpacyRecognizer/
# underthesea), unlike NON-NER labels matched by structured REGEX (VN_PHONE_NUMBER/
# VN_ID_NUMBER/EMAIL_ADDRESS/IBAN_CODE/...). Only THIS group may have
# `_plausible_person_span` applied (Security 19/08) — "MISC" is a spaCy label Presidio
# hasn't mapped (the warning "Entity MISC is not mapped..." has been seen in the logs); it is
# still an NER guess, not a structural match, so it belongs in this group.
_FREE_NER_LABELS = {"PERSON", "LOCATION", "ORGANIZATION", "PERSON_VN", "MISC"}


# Vietnamese personal pronouns + forms of address — NOT personal names, even if NER labels
# them B-PER. Real finding 2026-08-13 while measuring scrubbing on customer messages:
# "tôi chuyển 5tr cho số 09..." (I transferred 5M to number 09...) became "[PERSON] chuyển ..."
# and the agent lost the subject of the sentence. This is a CLOSED list (Vietnamese pronouns
# are a finite set that doesn't grow), unlike the general rule in _plausible_person_span.
_PRONOUNS_NOT_NAMES = {
    "tôi", "tui", "mình", "em", "anh", "chị", "cô", "chú", "bác", "ông", "bà",
    "con", "cháu", "bạn", "cậu", "tớ", "ta", "họ", "nó", "ai",
}


def _trim_pronouns(text: str, start: int, end: int, label: str) -> tuple[int, int, str] | None:
    """Trim extra pronouns/verbs at BOTH ENDS of a PERSON span; return None if empty.

    WHY IT IS NEEDED (measured 2026-08-13 on customer messages):
    Vietnamese NER labels MULTI-WORD PHRASES, not exactly the name: "tôi bị" (I got)
    -> PERSON, "anh bị trừ" (you got charged) -> PERSON, "chị" (sister/you) -> ORGANIZATION.
    Masking the whole phrase strips the sentence of its subject ("[PERSON] charged twice") —
    the agent can no longer tell who did what. Filtering by exact string match DOESN'T work
    because the span is "tôi bị", not "tôi".

    Trimming rather than dropping the whole span preserves both directions: "anh Huy" ->
    still masks "Huy" (the real name) but gives "anh" back to the sentence.

    Applies ONLY to person labels — never touches phone/ID/email (those are hard PII, there
    is no trimming them).
    """
    if "PERSON" not in label.upper() and "ORGANIZATION" not in label.upper():
        return (start, end, label)

    span = text[start:end]
    # Trim from the start
    while True:
        m = re.match(r"^\s*(\w+)", span)
        if not m or m.group(1).lower() not in _PRONOUNS_NOT_NAMES:
            break
        start += m.end()
        span = text[start:end]
    # Trim from the end: drop the last token if it is a pronoun or a common connector
    while True:
        m = re.search(r"(\w+)\s*$", span)
        if not m or m.group(1).lower() not in _PRONOUNS_NOT_NAMES | _COMMON_CONNECTORS:
            break
        end -= len(span) - m.start()
        span = text[start:end]

    span = text[start:end].strip()
    if not span or span.lower() in _PRONOUNS_NOT_NAMES | _COMMON_CONNECTORS:
        return None
    # Re-align the boundaries after stripping
    left_offset = len(text[start:end]) - len(text[start:end].lstrip())
    return (start + left_offset, start + left_offset + len(span), label)


# Verbs/connectors that NER often wrongly merges into personal-name spans in complaint sentences.
_COMMON_CONNECTORS = {"bị", "trừ", "là", "cho", "của", "đã", "được", "vừa", "chuyển", "nhận"}


# ORDINARY Vietnamese words (not pronouns) that NER has wrongly labelled as a person/
# organisation — real finding 19/08 (the real PO testing scenario A): "Mã giao dịch..."
# (Transaction ID...) was labelled B-PER, and the agent received "[PERSON_VN] giao dịch...",
# losing the subject. 🔴 AN OPEN LIST — unlike `_PRONOUNS_NOT_NAMES` (pronouns are a FINITE set
# that can be fully enumerated): "words NER commonly mistakes" is NOT finite; new cases beyond
# "mã" will keep appearing. Find a new case -> ADD IT HERE, don't silently skip it (the same
# commitment written for _PRONOUNS_NOT_NAMES above, restated clearly by Security 19/08 in
# docs/security/2026-08-19-gd4-dinh-hang-scrub-pii-model-input.md).
# UPDATE 19/08 (afternoon): PO-agent [MEASURED] "Giao dịch bị treo mấy ngày rồi" (the
# transaction has been stuck for days) -> "ngày" (day) labelled LOCATION — a sentence with NO
# code, NO number, NO name, proving this is not limited to "transaction ID" but is NER
# distorting everyday Vietnamese words in general. Coder measured further and found "tuần"
# (week, capitalised at sentence start) also labelled PERSON — BOTH added, per the commitment
# above. QA/QC is building a corpus measuring before/after rates on golden_set.jsonl — new
# cases from it will be added here.
#
# 🔴 GATE before adding a NEW word to this list (Security + Lead 19/08, after discovering that
# "tuần" IS ALSO a valid Vietnamese personal name, not just a time word): ask yourself "could
# this word plausibly be a real Vietnamese name?" — if YES, this is a TRADE-OFF (losing the
# ability to mask a rare name in exchange for not distorting a common word), NOT free. Adding
# the word is still RIGHT if its use as an ordinary word >> its use as a proper name in
# e-wallet customer-service contexts (exactly the case for "mã"/"ngày"/"tuần") — but the
# trade-off MUST be declared right on the line adding the word, not added silently as a
# harmless fix.
_WORDS_MISTAKEN_FOR_NAMES = {"mã", "ngày", "tuần"}


def _plausible_person_span(span: str) -> bool:
    """Filters REAL false positives found while verifying underthesea.ner() on the project's
    data: internal transaction/ticket IDs (e.g. `TXN20260810000123`, new_id() prefix +
    digits, see src/tools/base.py::new_id) and all-caps abbreviations (e.g. `CCCD`) are
    sometimes wrongly labelled B-PER. Real Vietnamese names contain NO digits and are NOT
    written in all caps — a general rule, not a hard-coded ID prefix list (no update needed
    when a new ID prefix appears).

    Security 19/08 (df186c0): previously this function was ONLY applied to `underthesea.ner()`
    (`_underthesea_person_spans` below) — Presidio's `SpacyRecognizer` ran UNFILTERED, so
    "TXN...352" labelled LOCATION/MISC slipped through intact as `[LOCATION]`. `scrub_pii()`
    now applies this function to EVERY recognizer returning a FREE NER label (see
    `_FREE_NER_LABELS`), not just underthesea — THIS CORRECTS A FUNDAMENTALLY WRONG
    DESCRIPTION, it is not a loosening: the rule only drops spans that WERE NEVER PII (digits/
    all caps/pronouns/common words), and doesn't touch the decision to "mask with exactly the
    type Presidio returns even if the TYPE may be wrong" for REAL PII."""
    if any(ch.isdigit() for ch in span):
        return False
    if span.isupper():
        return False
    clean_text = span.strip().lower()
    if clean_text in _PRONOUNS_NOT_NAMES:
        return False
    if clean_text in _WORDS_MISTAKEN_FOR_NAMES:
        return False
    return True


def _underthesea_person_spans(text: str) -> list[tuple[int, int, str]]:
    """underthesea.ner() returns tokens (possibly multi-word, e.g. 'Lê Hoàng Nam')
    as SUBSTRINGS of the original text (no word segmentation with '_') — character offsets
    are mapped back with a sequential cursor (`str.find` from the position after the previous
    token), in the order the tokens are returned. Tokens not found are skipped (shouldn't
    happen in practice, but safer than computing a wrong offset)."""
    from underthesea import ner as underthesea_ner

    spans: list[tuple[int, int, str]] = []
    cursor = 0
    for token, _pos, _chunk, ner_tag in underthesea_ner(text):
        idx = text.find(token, cursor)
        if idx == -1:
            continue
        end = idx + len(token)
        if ner_tag in ("B-PER", "I-PER") and _plausible_person_span(token):
            spans.append((idx, end, "PERSON_VN"))
        cursor = end
    return spans


class _VietnameseNameRecognizer:
    """A hand-written `presidio_analyzer.EntityRecognizer` wrapping `underthesea.ner()` —
    a specialised Vietnamese NER layer COMPLEMENTING `SpacyRecognizer` (multilingual,
    see the module docstring), not replacing it. Registered separately, outside the main
    try/except of `_load_analyzer()` — a missing `underthesea`/load failure MUST NOT bring
    down the whole AnalyzerEngine (SpacyRecognizer + the rest of the catalog remain)."""

    def __new__(cls):
        from presidio_analyzer import EntityRecognizer, RecognizerResult

        class _Impl(EntityRecognizer):
            def load(self) -> None:  # underthesea lazy-loads its model internally
                pass

            def analyze(self, text, entities, nlp_artifacts=None):
                return [
                    RecognizerResult(entity_type="PERSON_VN", start=start, end=end, score=0.75)
                    for start, end, _label in _underthesea_person_spans(text)
                ]

        return _Impl(supported_entities=["PERSON_VN"], supported_language="vi", name="VietnameseNameRecognizer")


# Recognizers excluded ONLY FROM THE model_input PATH — they guess PII from CONTEXT (Spacy)
# or match GENERIC DIGIT STRINGS that easily collide with internal transaction IDs (Date:
# YYYYMMDD ~ TXN20260810...; Phone: any phone-like digit string, UNLIKE the narrow
# hand-written VN_PHONE_NUMBER below). The log/trace path does NOT exclude these recognizers —
# over-redaction in logs is an ESTABLISHED POLICY (see the module docstring), not an oversight
# of forgetting to apply the same list.
_EXCLUDE_FROM_MODEL_INPUT = ("SpacyRecognizer", "DateRecognizer", "PhoneRecognizer")


def _build_registry(nlp_engine, *, is_model_input: bool):
    """ONE configuration source for BOTH registries (model_input/log) — the
    `is_model_input` parameter controls which recognizers are NOT loaded, rather than two
    functions copying the same recognizer list twice (Security 19/08: load-everything-then-
    filter-results was where the filtering got forgotten; with a single configuration source
    there are no copies to drift apart)."""
    from presidio_analyzer import Pattern, PatternRecognizer, RecognizerRegistry

    registry = RecognizerRegistry(supported_languages=["vi"])
    # Presidio's built-in catalog for "vi" — Email/Phone/Iban/Crypto/Ip/
    # Url/Date/MedicalLicense/MacAddress + SpacyRecognizer (NER for person/
    # organisation/location names) — this is exactly the "more PII types in the future" part that
    # needs no hand-written regex per type.
    registry.load_predefined_recognizers(languages=["vi"], nlp_engine=nlp_engine)
    # Security 19/08 (QA/QC measured the golden_set.jsonl corpus: 49.2% of turns distorted):
    # `MEDICAL_LICENSE` is defined IN DIGITS — the existing shape filter ("has digits ⟹ not PII")
    # applied to it would CANCEL ITSELF OUT; there is no way to fix it with a shape filter.
    # In a Vietnamese e-wallet customer-service context, customers mentioning a US medical
    # licence number ≈ 0 — the recognizer only produced false positives on transaction IDs/account
    # numbers. Removed UNIFORMLY from both log/trace and model-input (unlike the decision to keep
    # Spacy PERSON/LOCATION — here there is NO real PII behind it to trade off when removing it).
    registry.remove_recognizer("MedicalLicenseRecognizer")
    if is_model_input:
        for name_text in _EXCLUDE_FROM_MODEL_INPUT:
            registry.remove_recognizer(name_text)
    registry.add_recognizer(
        PatternRecognizer(
            supported_entity="VN_PHONE_NUMBER",
            supported_language="vi",
            patterns=[Pattern(name="vn_phone", regex=_VN_PHONE_REGEX, score=0.9)],
        )
    )
    registry.add_recognizer(
        PatternRecognizer(
            supported_entity="VN_ID_NUMBER",
            supported_language="vi",
            patterns=[Pattern(name="vn_id", regex=_VN_ID_REGEX, score=0.6)],
        )
    )
    try:
        registry.add_recognizer(_VietnameseNameRecognizer())
    except Exception as e:  # underthesea missing — does NOT bring down the whole analyzer
        _logger.warning(
            "pii_underthesea_unavailable_spacy_only",
            extra={"error": repr(e), "la_model_input": is_model_input},
        )
    return registry


def _build_nlp_engine():
    from presidio_analyzer.nlp_engine import NlpEngineProvider

    return NlpEngineProvider(
        nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "vi", "model_name": "xx_ent_wiki_sm"}],
        }
    ).create_engine()


@functools.lru_cache(maxsize=1)
def _load_analyzer_model_input():
    """Lazy singleton — NARROW registry for the SEND-TO-MODEL path (`graph.py:787`).
    `_EXCLUDE_FROM_MODEL_INPUT` (see the constant) is NOT loaded at build time at all, rather
    than loaded-then-filtered on every call. Returns None if presidio-analyzer/spaCy/the model
    isn't ready — MUST degrade gracefully to the regex fallback, never crash the app.
    """
    try:
        nlp_engine = _build_nlp_engine()
        registry = _build_registry(nlp_engine, is_model_input=True)
        from presidio_analyzer import AnalyzerEngine

        return AnalyzerEngine(nlp_engine=nlp_engine, registry=registry, supported_languages=["vi"])
    except Exception as e:  # presidio-analyzer missing, spaCy missing, or model missing
        _logger.warning("pii_presidio_unavailable_fallback_regex_only", extra={"error": repr(e), "muc_dich": "model_input"})
        return None


@functools.lru_cache(maxsize=1)
def _load_analyzer_log():
    """Lazy singleton — FULL registry for the LOG/TRACE path (every call site other than
    `graph.py:787`) — keeps EVERY recognizer including Spacy/Date/Phone
    (except MedicalLicense, removed uniformly from both paths — see `_build_registry`).
    Returns None if presidio-analyzer/spaCy/the model isn't ready — degrades gracefully to
    the regex fallback."""
    try:
        nlp_engine = _build_nlp_engine()
        registry = _build_registry(nlp_engine, is_model_input=False)
        from presidio_analyzer import AnalyzerEngine

        return AnalyzerEngine(nlp_engine=nlp_engine, registry=registry, supported_languages=["vi"])
    except Exception as e:
        _logger.warning("pii_presidio_unavailable_fallback_regex_only", extra={"error": repr(e), "muc_dich": "log"})
        return None


def _merge_overlapping(spans: list[tuple[int, int, str]]) -> list[tuple[int, int, str]]:
    """Presidio may return several recognizers DUPLICATING/OVERLAPPING one character region
    (e.g. EMAIL_ADDRESS overlapping URL on the domain part) — merged into one block to avoid
    processing twice on top of each other, which would corrupt offsets during replacement.
    Type labels are merged (safer than picking one type) — per the principle "better to mask
    by mistake than to leak"."""
    if not spans:
        return []
    spans = sorted(spans, key=lambda s: s[0])
    merged = [spans[0]]
    for start, end, label in spans[1:]:
        last_start, last_end, last_label = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end), f"{last_label}/{label}" if label not in last_label else last_label)
        else:
            merged.append((start, end, label))
    return merged


def scrub_pii(text: str | None, *, purpose: ScrubPurpose) -> str | None:
    """USE THIS FUNCTION for every log/span attribute OR outgoing text that may contain
    customer/agent PII. Presidio (when available) or the regex fallback (see the module
    docstring).

    `purpose` is MANDATORY, with NO default — the two holes fixed on 19/08 (Spacy forgetting
    the filter, MEDICAL_LICENSE slipping into the registry) were both "forgot to choose the
    right branch"; a mandatory parameter forces every NEW call site to ask that question, and
    nobody can accidentally land in the wrong branch by forgetting to pass it.
      - `"model_input"`: data GOING OUT to the LLM provider — NARROW registry (D',
        see the module docstring).
      - `"log"`: everywhere else (trace/span, `resolutions.note`) — FULL registry,
        behaviour UNCHANGED from before phase 4."""
    if not text:
        return text

    analyzer = _load_analyzer_model_input() if purpose == "model_input" else _load_analyzer_log()
    if analyzer is None:
        return scrub_regex(text)

    results = analyzer.analyze(text=text, language="vi")
    if not results:
        return text

    raw_spans = [(r.start, r.end, r.entity_type) for r in results]
    # Security 19/08 (df186c0): `_plausible_person_span` is applied to EVERY recognizer
    # returning a FREE NER label (context-guessed — PERSON/LOCATION/ORGANIZATION/
    # MISC from SpacyRecognizer, PERSON_VN from underthesea), not just underthesea as before.
    # DELIBERATELY NOT applied to NON-NER labels (VN_PHONE_NUMBER/
    # VN_ID_NUMBER/EMAIL_ADDRESS/IBAN_CODE/...): those recognizers match by structured
    # REGEX — digits/capitals are their CORRECT signal, not noise as with NER. Applying it to this
    # group by mistake would disable the very recognizers protecting real PII (all-digit phone
    # numbers/ID cards).
    raw_spans = [
        (start, end, label)
        for start, end, label in raw_spans
        if label not in _FREE_NER_LABELS or _plausible_person_span(text[start:end])
    ]
    raw_spans = [s for s in (_trim_pronouns(text, *s) for s in raw_spans) if s]
    if not raw_spans:
        return text

    spans = _merge_overlapping(raw_spans)
    chars = list(text)
    for start, end, label in sorted(spans, key=lambda s: s[0], reverse=True):
        chars[start:end] = list(f"[{label}]")
    return "".join(chars)
