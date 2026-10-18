# English docs index

Most of this project's documentation is in Vietnamese — the product serves Vietnamese e-wallet
customers, and the working team's day-to-day decision log, ADRs, and internal notes were written
in Vietnamese throughout development. This folder is the English-speaking entry point: a map of
where to look and a [glossary](glossary.md) for the terms the rest of the docs use without
translating.

## Where to start

| If you want... | Read |
|---|---|
| The 30-second architecture pitch | [`../../ARCHITECTURE.md`](../../ARCHITECTURE.md) (English) |
| The "why", not just the "what" | [`../../CASE-STUDY.md`](../../CASE-STUDY.md) (English) |
| What the AI agent is actually told to do | [`agent-prompt.md`](agent-prompt.md) — a full English rendering of the live system prompt and all 5 tool docstrings |
| The project's hard constraints and how they're enforced | [`../../CLAUDE.md`](../../CLAUDE.md) — the project's written constitution, loaded into every working session |
| Every structural decision with its reasoning (and the rejected alternatives) | [`../DECISIONS.md`](../DECISIONS.md) — 64 ADRs, Vietnamese, append-only. Worth reading even without Vietnamese: PR/commit references and code excerpts inside each entry are language-independent, and a translator tool handles the prose if you need it |
| The structural "source of truth" the whole system is tested against | [`../../contracts/`](../../contracts/) — 3 YAML files (`authority-matrix.yaml`, `resolution-state-machine.yaml`, `agent-tools.yaml`); their comments are already in English |
| Real evidence from actual runs, not a description of intended behaviour | [`../../eval/EVAL-EVIDENCE.md`](../../eval/EVAL-EVIDENCE.md) |

## Why so much of this repository stays in Vietnamese

A handful of things were deliberately left untranslated rather than converted for an English
audience, because translating them would make the artifact less honest, not more readable:

- **The agent's live system prompt and its replies** — the product's actual customers write in
  Vietnamese; an agent that reasons in English and answers in Vietnamese would be a worse,
  slower, more error-prone product. See [`agent-prompt.md`](agent-prompt.md) for the English
  rendering used for review.
- **The regex/keyword guardrails** (`src/agents/triage.py`, `src/agents/output_filter.py`, the
  PII scrubber) — they match Vietnamese text because that's the language flowing through the
  system.
- **The eval datasets** (`eval/*.jsonl`) — real Vietnamese conversations, used as the actual
  yardstick; translating them would change what's being measured.
- **Already-stored data** — JSON fields, database columns, and Redis key values written before
  this portfolio cleanup keep their original Vietnamese identifiers, because renaming them would
  silently corrupt data already on disk.
- **The decision log and daily working notes** (`docs/DECISIONS.md`, `docs/nhat-ky/`) — a
  historical record of a solo engineer's actual day-to-day calls, written in the moment, in the
  language that moment happened in.

Everything else — code identifiers, comments, and this page's siblings — was translated for this
portfolio edition; see [`../../CLAUDE.md`](../../CLAUDE.md) and the repository's commit history
for the specifics of what changed and why.
