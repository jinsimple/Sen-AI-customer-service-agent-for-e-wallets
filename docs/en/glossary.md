# Glossary

Terms you'll hit across the Vietnamese documentation, commit history, and (deliberately
untranslated) data/UI strings, with what they mean in this project specifically.

## Roles

| Term | Means |
|---|---|
| **khách hàng** | Customer. The wallet's end user filing a complaint. |
| **CSKH** (chăm sóc khách hàng) | Support agent. Investigates a complaint, proposes a resolution — **cannot approve one**. |
| **sếp** / **sếp duyệt** | Literally "boss" / "approving boss" — this project's name for the **supervisor** role. The only role that can approve a refund or balance adjustment, for every transaction scope, no exceptions. |
| **đối tác ví** (partner_admin in code) | Wallet partner. Manages the policy/FAQ document library the RAG search draws from. Cannot touch customer data or money. |

## Core noun phrases

| Term | Means |
|---|---|
| **khiếu nại** | Complaint. The thing a customer files. 4 types: `wrong_recipient` (sent to the wrong person), `money_not_received`, `double_charge`, `refund` (plus `other` for a human-handoff request that doesn't fit the other 4). |
| **vé** / **ticket** / **hồ sơ** | Ticket/case. The record created from a complaint, tracked through the support queue and HITL approval flow. |
| **phạm vi** (scope) | Which "rail" the transaction sits on: `internal_wallet` (wallet-to-wallet), `from_bank`, `to_bank`, or `unknown`. |
| **đề xuất** (resolution/proposal) | A support agent's proposed course of action on a ticket (e.g. `refund_to_wallet`), submitted for a supervisor's approval. |
| **duyệt** / **từ chối** | Approve / reject — the supervisor's two decisions on a proposal. |
| **hàng chờ** | Queue. The support-agent-facing list of unclaimed/own tickets. |
| **tra cứu** | Look up. What the agent does via its 5 tools — always a real database/document query, never a model-generated guess. |
| **tín hiệu gian lận** (fraud signal) | A routing signal (e.g. "FS-06") that can raise a ticket's priority. Deliberately never wired to locking a wallet — see hard constraint 5. |

## Mechanisms and acronyms

| Term | Means |
|---|---|
| **HITL** | Human-in-the-loop. The project's absolute rule: no path exists for the AI or a support agent to execute a refund or balance change themselves — only a supervisor, enforced by a database CHECK constraint, not just an `if` in a route handler. |
| **maker-checker** | The rule that the person who *proposes* a resolution can never be the person who *approves* it — enforced even when both people hold a role allowed to approve (see `ADR-020` and `BR-12`). |
| **origin-rule** | The anti-fabrication rule: every figure the agent states must trace back to an actual tool-call result (`tool_results` → `investigation_logs.tool_result_id` → `resolutions.cited_tool_result_ids`). If it can't be traced, the agent must say "I couldn't find that" rather than guess. |
| **step-up OTP** | A second, stricter OTP check required for a consequential action (like a supervisor approving a specific refund), separate from the session OTP used just to enter the app. |
| **BFF** (Backend for Frontend) | The frontend architecture: the browser only ever holds a session cookie; the backend's JWT never leaves the Next.js server. |
| **ADR** (Architecture Decision Record) | An entry in `docs/DECISIONS.md` — append-only, each one stating the decision, the context, and (crucially) why the rejected alternative was rejected. |
| **INV-NN** | An "invariant" ID — a structural rule from `contracts/` that `tests/test_invariants.py` checks against the live app. |
| **BR-NN** | A "business rule" ID from the project's requirements documents, often also enforced as a literal database CHECK constraint. |
| **PDPA** | Vietnam's personal-data-protection framework (Law 91/2025/QH15 + Decree 356/2025), the legal basis for masking third-party transaction details before display. |

## Project / team shorthand

| Term | Means |
|---|---|
| **PO** | Product owner. In this project, the same person as the engineer and architect. |
| **GĐ2.5**, **GĐ3**, etc. | "Phase 2.5", "Phase 3" — internal project phase labels used in commit messages and the decision log. |
| **contracts/** | The three YAML files (`authority-matrix.yaml`, `resolution-state-machine.yaml`, `agent-tools.yaml`) that are the system's declared source of truth; code that drifts from them fails CI. |
| **the invariants / 23 tests** | `tests/test_invariants.py` — the suite that introspects the running app (reads route decorators, parses CHECK constraints via an AST, calls the tool-factory function directly) and compares it against `contracts/`. Red here means the build is broken, by project convention. |
