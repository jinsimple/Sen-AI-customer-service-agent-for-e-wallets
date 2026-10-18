# FIN-05 — AI Agent for E-Wallet Customer Support

> *[Bản tiếng Việt / Vietnamese version →](README.vi.md)*

> An AI agent that helps e-wallet customer-support teams handle transaction complaints:
> **it investigates through tools, classifies the complaint, and proposes an evidence-backed
> resolution — and it never decides anything itself.** Every money-touching action goes through
> human approval (HITL), every figure the agent states traces back to a real tool call, and both
> rules are enforced at the database layer and guarded by 23 automated invariant tests.

**Author:** Đào Ngọc Bích — sole engineer, product owner, and architect · **Mentor:** Đặng Hải
Lộc · **Domain input:** informal feedback from domain advisors in the Vietnamese e-wallet
industry (no formal partnership) · **Origin:** built solo end-to-end for AI 20K Build Phase
(Cohort 3), later cleaned up into this public portfolio edition

**Live demo:** https://app.adaptivealgo.uk *(home server + Cloudflare Tunnel — see the
[deployment notes](docs/giao-viec/2026-08-15-chay-that-tai-nha-windows-tunnel.md), in Vietnamese)*

---

## Architecture in 30 seconds

An LLM — **a pool of 4 models the system rotates through automatically** (`qwen3.8-plus` plus
three `deepseek` variants, via DashScope, see ADR-043) — is orchestrated with **LangGraph**
(ReAct, 5 tools that query a real database) · policy RAG runs on **ChromaDB** (verbatim excerpts
with a source citation, never an AI summary) · **every safety layer is a deterministic rule
outside the model**: PII is masked before anything reaches the LLM (Presidio + spaCy NER), the
agent is blocked from fabricating numbers (an origin-rule — every figure must trace back to a
tool result), prompt-injection defences (spotlighting + a trust-tier system), and maker-checker
separation enforced by a database CHECK constraint. Details: [ARCHITECTURE.md](ARCHITECTURE.md).

## Key features (verified by real runs, not just described)

**Investigation & conversation**
- The agent investigates a complaint through **5 tools backed by a real database**, classifies
  it (4 complaint types × 3 transaction scopes), and proposes a resolution — **it never decides**.
  Approval is a human's job (the supervisor).
- **Anti-fabrication (origin-rule):** every amount/status the agent states must trace back to a
  tool result; a transaction ID that doesn't exist gets a flat *"I couldn't find that"*, never a
  made-up answer.
- **Automatic handoff to a human:** `request_human_handoff` opens a live chat and creates/
  escalates a ticket.

**Policy lookup (RAG)** — ADR-061/062/065
- Returns **verbatim excerpts with a source citation**, never an AI summary; scoped filtering +
  cross-encoder reranking (a sidecar service, **fails closed** to `not_found` if the sidecar is
  down).
- Handles **both short keywords** ("withdrawal fee", "refund") **and full sentences**; irrelevant/
  garbage input ("zzzqwx", "what's the weather") correctly returns *"not found"* (precision is
  preserved, not forced to answer something).
- **"View full text" deep link** (ADR-065): clicking a result opens the full document in a new
  tab, **auto-scrolled and highlighted** to the matched excerpt.

**Support queue & role-scoped access** — ADR-063/064
- **New-ticket notification bell** — fanned out to whichever support agents are currently
  online, with the complaint type · scope · priority · SLA attached; paired with a **"who's
  online" table** for the supervisor.
- A support agent **only sees unclaimed tickets plus their own**; an active, idempotent **"Claim"**
  button. A supervisor sees **everything** (an ID-based access attempt on someone else's ticket
  gets a 404, not a 403 — it doesn't even reveal the ticket exists).
- Ticket table: **real pagination** (30/50/100 rows) + a **genuine server-side AND filter** across
  5 criteria (a real SQL WHERE clause) + a row-number column.

**Safety — deterministic rules outside the model**
- HITL: only a supervisor can approve a refund/balance adjustment, for **every** transaction
  scope (enforced by a database CHECK constraint).
- PII is masked before reaching the LLM · step-up OTP for consequential actions · flagging
  suspected fraud is **never** wired directly to locking a wallet.
- A guardrail blocks the AI from falsely claiming *"ticket created"* — it only fires when a turn
  genuinely intended to create one.

## Running it locally

### Option 1 — Docker (the full stack, close to production)

```bash
git clone <your-fork-url> && cd FIN05-portfolio
cp .env.example .env        # fill in OPENAI_API_KEY + generate 2 secrets (see table below)
docker compose up -d        # backend + frontend + postgres + redis + caddy + jaeger
# wait ~1 minute, check with: docker ps → backend should be "healthy"
# open https://localhost (self-signed cert — accept the browser warning)
```

### Option 2 — Dev mode (backend/frontend run separately, hot-reload)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
make db          # generates data + builds the schema + seeds it (60k transactions, 200 customers)
make demo-data   # sample scenarios for the Dashboard/Approve screens

make run         # FastAPI backend on :8010

cd frontend && npm install && npm run dev   # Next.js frontend on :3000
```

## Environment variables

The app **fails fast if a required secret is missing** — there's no `changeme`-style default.

| Variable | Required | Notes |
|---|---|---|
| `JWT_SECRET_KEY` | ✅ | Generate with `openssl rand -hex 32` |
| `FIELD_ENCRYPTION_KEY` | ✅ | A Fernet key, generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. ⚠️ Encrypts chat transcripts/account numbers/complaint descriptions at rest — **lose the key and that data is gone for good**; moving to a new machine means carrying it over unchanged. |
| `REDIS_URL` | ✅ | `redis://localhost:6379/0` · tests/CI use `fake://ci` (fakeredis, no real Redis needed) |
| `OPENAI_API_KEY` | ✅ (to run the agent) | |
| `DATABASE_URL` | — | Defaults to SQLite for dev; Docker uses Postgres (already set in the compose file) |
| `LLM_MODEL_POOL` | — | **The pool of models the infrastructure rotates through** when one runs out of quota (ADR-043). Comma-separated list. If unset, only `LLM_MODEL` is used, with no rotation |
| `LLM_MODEL` | — | The chat model currently in use. **This is the real operational variable** |
| `APP_ENV` | `production` | 🔴 Defaults **fail-safe**: if unset, `/docs`, `/openapi.json`, and `/redoc` are all DISABLED. Set to `development` to re-enable them while working locally |
| `OPENAI_MODEL` | `gpt-4o-mini` | Now only the **final fallback** for `LLM_MODEL` |
| `JWT_ACCESS_EXPIRE_MINUTES` | — | Defaults to 15 |
| `CLOUDFLARE_TUNNEL_TOKEN` | only the `home` profile | For a home-server deploy; fails fast in `scripts/deploy_home.*` |
| `AI_LOG_SERVER` / `AI_LOG_API_KEY` | — | Submits an AI-usage log to the cohort's grading server (a pre-push hook) — **not relevant outside the original cohort program; safe to leave unset** |
| `SSL_CERT_FILE` | — | ⚠️ **Machine-specific** (a certifi path from the original Mac) — do NOT carry this over to another machine |

## Demo accounts (shared password `Demo@123`)

| Role | Phone | Sees |
|---|---|---|
| Customer | `0974000145` | AI assistant chat, live chat with a human |
| Support agent | `0353000201` | Ticket queue, investigation timeline — **no approval button** |
| Supervisor | `0905000205` | Approvals + per-proposal step-up OTP |
| Wallet partner | `0900000001` | Manages the RAG policy library — can't touch money or customer data |

> To use two roles on the same machine: the customer role in a normal window, the staff role in
> a **private/incognito window** (one browser = one login session).

## Example conversations (verified against real runs — see
[eval/EVAL-EVIDENCE.md](eval/EVAL-EVIDENCE.md))

The product's customers are Vietnamese, so the agent converses in Vietnamese — these are real
logged conversations, kept as-is with an English gloss of what happened:

```text
minh chuyen 171k cho ban hom 1/8 luc 12:47 ma ban bao chua nhan duoc
("I sent my friend 171k on Aug 1 at 12:47 and they say they haven't received it")
→ finds the 1 correct transaction among 9 with the same amount, disambiguated by timestamp

kiem tra giup gd TXN20260623999901, toi chuyen ma khong thay trong lich su
("please check transaction TXN20260623999901, I sent it but don't see it in my history")
→ the ID doesn't exist: the agent says plainly "I couldn't find that", fabricating nothing

Trừ một lần đã xót, đây trừ tận hai lần 852k, quá đáng thật.
("Getting charged once already hurt, and now I've been charged 852k TWICE — that's too much.")
→ acknowledges the frustration first, then lists the 2 matching transactions 37 seconds apart

dung roi, 2 giao dich 852.000d luc 11:31 ngay 30/06 do, tao ho so giup minh
("yes, those two 852,000₫ transactions at 11:31 on June 30, please file a complaint for me")
→ creates a ticket into the support queue; the agent only PROPOSES — approval is a human's job

cho tôi gặp người thật
("let me talk to a real person")
→ calls request_human_handoff, creates/escalates a ticket and opens a live-chat channel
```

## Testing

```bash
pytest tests/test_invariants.py -v        # the 5 hard constraints, 23 tests — introspects the real running app
python scripts/check_contracts.py         # detects drift against contracts/
pytest tests/ -m "not security_finding"   # the full backend suite (**109 files · 598 test functions**, measured Oct 18)
python eval/run_golden_set.py             # business-scenario cases (calls the real LLM)
python eval/run_adversarial_set.py        # adversarial/attack cases
```

Frontend E2E: **38 Playwright specs** (`frontend/e2e/`) — run against the real UI, asserting on
the rendered DOM.

CI (GitHub Actions, `.github/workflows/ci.yml`) — **14 jobs**: invariants · contract-drift ·
lint+test · appsec · security-findings-gate · migration-chain · …

🔴 **A note on the CI badge, so a red run isn't misread as a broken build:**
- **8 jobs run for real**, on a self-hosted runner.
- **6 `ubuntu-latest` jobs don't run at all** — the cohort GitHub org's shared-runner billing is
  blocked. The tell: `runner_name` is **empty**, `steps = 0`, and it fails in **0 seconds**. They
  render identically red to an actual failing test, which is misleading if you only look at the
  color.
- **`security-findings-gate` is red by design** — it stays red for as long as a P0 security
  finding is open, as an intentional reminder, not a bug.
- Occasional transient infra blips (a network drop during `pip install`, a port clash on a
  shared runner).

## Structure & further reading

```
contracts/        ← SOURCE OF TRUTH: 42 routes × role · the HITL state machine · the 5 AI tools
src/agents/       ← the LangGraph agent + its 5 tools + guardrails (spotlighting, O1-O4, origin-rule)
src/api/          ← FastAPI (BFF-first, rate-limited, step-up OTP)
frontend/         ← Next.js (BFF pattern — the browser never holds the backend's JWT)
tests/            ← 109 test files + tests/test_invariants.py (red = the build is broken)
eval/             ← golden/adversarial/heldout sets + evidence from real runs
docs/DECISIONS.md ← 64 ADRs — every decision with its reasoning and why the alternatives were rejected
docs/STATE.md     ← the project's living status, updated at the end of every working session
```

Further reading: [docs/en/](docs/en/) (English index + glossary) ·
[CASE-STUDY.md](CASE-STUDY.md) · [ARCHITECTURE.md](ARCHITECTURE.md) ·
[README.vi.md](README.vi.md) (original Vietnamese README, more detail on the product itself)

## About this repository

This is a personal portfolio edition of a project originally built solo for **AI 20K Build
Phase, Cohort 3** (Vingroup × VinUni), where I held both the product-owner and engineering-lead
roles and coordinated a team of role-specialised Claude Code sessions (tech-lead · tester ·
security · DevOps · critic · PO-agent) against a shared written constitution
([CLAUDE.md](CLAUDE.md)). The commit history here is real and unedited; identifiers, comments,
and this front-door documentation were translated to English and a few names were anonymised for
a public audience, but the code, tests, and decisions themselves are untouched.

## License

MIT
