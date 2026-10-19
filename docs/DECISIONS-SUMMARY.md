# Decisions summary — the ten calls that shaped Sen

The full decision log is [DECISIONS.md](DECISIONS.md) (64 ADRs, Vietnamese, append-only). This page summarises ten of them in English: context, decision, trade-off. It is a reading aid. Where wording matters, the ADR is the source of truth.

Each entry also answers the interview question "what did you decide, and what did it cost?"

---

## 1. ADR-001 — The AI has no role of its own

- **Context.** The permission system needed an answer to "what is the AI allowed to do?"
- **Decision.** Nothing special. The agent runs inside the customer's session and calls tools with the customer's own `user_id`. It has every limit of the `customer` role and no more.
- **Trade-off.** A separate `ai_agent` role would have created a second permission table to keep in sync and a new attack surface. Without it, blocking the customer role *is* blocking the AI: one layer of defence instead of two. The cost is that the agent can never be granted a convenient extra power.
- **Enforced by.** `contracts/authority-matrix.yaml` has no `ai_agent` column; the invariant test that checks "no money-touching route is open to `customer`" is also a test of the AI.

## 2. ADR-002 — The supervisor approves every scope, with no threshold

- **Context.** The first design let support agents self-approve small wallet-to-wallet cases to relieve the supervisor.
- **Decision.** Removed. Only `supervisor` approves, for every transaction scope and amount.
- **Trade-off.** Self-approval looks better for operations and UX, and an agent will propose it again. It was rejected because (a) "out of authority" is defined by role, not by amount, since a threshold invites splitting a transaction into smaller ones; (b) one approval path is easier to audit than two; (c) a human-in-the-loop rule with no exceptions is the strength worth showing a wallet company. The cost is more load on the supervisor.
- **Enforced by.** Invariants INV-01/03/04; `cskh` is `deny` on every money-touching route.

## 3. ADR-003 — Enforce human approval in the database, not only in the application

- **Context.** A rule inside a route's `if` protects only that route.
- **Decision.** Add a `CHECK` constraint: a resolution cannot be `approved` without an approver and an approval time.
- **Trade-off.** A hand-written `UPDATE`, a careless migration or a new endpoint that forgets the check can all bypass application code. A constraint has no path around it. The cost is that violations surface as database errors unless the route also checks first.
- **Enforced by.** Constraint on `resolutions`; invariant INV-07 checks that the constraint still exists.

## 4. ADR-010 — No identifying customer data leaves the system for the LLM

- **Context.** A review found the customer's real name and phone number inside the payload sent to the model provider. The masking code existed but only ran for logs.
- **Decision.** Close both ends: remove the customer name from the system prompt (the agent says "quý khách"), mask name, phone and account number in every tool result, and scrub the customer's own typed text before it becomes a message.
- **Trade-off.** The fix lives in the agent's wrapper, not in the lookup tool itself, because the support-agent path legitimately needs the full data and never leaves the system. Masking costs some context (the model cannot use a name) and produces false positives; one is documented in `eval/EVAL-EVIDENCE.md`.
- **Enforced by.** `scrub_pii` in the agent layer; `tests/test_security/`.

## 5. ADR-020 — Maker-checker: the proposer cannot approve their own proposal

- **Context.** Roles said "support creates, supervisor approves". But a supervisor was also allowed to *create* a proposal, so one person could do both steps and the audit trail would still look perfect.
- **Decision.** A second `CHECK` constraint (`created_by` must differ from `approved_by` and from `rejected_by`), plus the same check in the route so users get a clear 403 instead of a database error.
- **Trade-off.** The SQL is deliberately long: shorter forms rely on three-valued NULL logic or on `IS DISTINCT FROM`, which needs a newer SQLite than CI can guarantee. The ADR states its own limit: when written, all 10 existing resolutions had `created_by` NULL, so the constraint protected no old row.
- **Enforced by.** `ck_resolutions_maker_checker_br12`; invariant INV-15 proves the constraint still exists, not just that behaviour works today.

## 6. ADR-022 — Emotion signals route to a human; they never reach the LLM

- **Context.** Empathy was enforced only through the prompt. Nothing told the system a customer was escalating, so there was no early path to a person.
- **Decision.** Distress signals (ES-xx) are computed in the service layer, before the graph runs, never by the model. They do two things only: show the customer a "talk to a person" button, and raise ticket priority. They never escalate to the supervisor.
- **Trade-off.** The agent never states a psychological conclusion about a customer, and a wrong signal is cheap (the customer ignores a button). The cost is a less "intelligent" feel than a model that reads mood.
- **Enforced by.** Modelled like the fraud signal FS-06; hard constraint 2 (no escalation by the AI).

## 7. ADR-043 (with ADR-058/059) — The infrastructure rotates models; the code does not know model names

- **Context.** Earlier, the model name was pinned by date because a drifting alias makes every A/B measurement meaningless. The product owner then asked for the opposite: the service must never stop because a free quota ran out during demo and test.
- **Decision.** The model pool comes from `LLM_MODEL_POOL`. Rotation is automatic and silent, triggered only by a quota-exhausted error class (never by a `429`), capped at the pool size per turn, with exhausted models marked in Redis with a TTL used as back-off.
- **Trade-off.** Availability over reproducibility. ADR-059 later admitted that the 31 Aug benchmark ran on `qwen3.8-flash`, an alias with no date, and that the "pinned names only" guard promised by ADR-043 was never coded. The ADR corrects the record instead of editing the earlier one and lists the fix as open debt.
- **Enforced by.** `src/agents/llm_pool.py`; the judge model is pinned separately in `src/config.py` so the yardstick does not move when the agent's model does.

## 8. ADR-051 (with ADR-049) — Ticket creation in two steps: approved, not yet implemented

- **Context.** The agent sometimes said "I created a ticket" when it had not, or created one too early on a vague message.
- **Decision.** ADR-049 detects "the customer asked for a ticket" deterministically. ADR-051 splits `create_ticket` into two calls: first return a six-field summary built in code from the model's own arguments, then create the ticket only after the customer confirms. Both were approved by the product owner on Aug 25.
- **Trade-off.** One extra turn for the customer, in exchange for nothing being created before they agree and a summary the model cannot embellish. It tightens the human-in-the-loop rule.
- **Status, stated plainly.** The decision and the contract (`contracts/agent-tools.yaml` v2.2.0, input `xac_nhan`) exist. The `create_ticket` tool in `src/agents/tools/customer_tools.py` has no such parameter, and the invariant suite only compares tool *names*, so it cannot see the gap. The contract file itself warns about this hole. What does run today is the output filter that checks "ticket created" claims against the database and swaps in a fixed reply when none exists. `[CHƯA XÁC MINH]` whether the two-step flow was dropped or is pending.

## 9. ADR-056 — Move a rule from the prompt into code

- **Context.** In 180 golden and held-out cases, the agent chose to call no lookup tool in 29 first complaint messages. It asked the customer for details it could have looked up. The prompt already said "call the tool immediately" three times, in capitals, with a counter-example.
- **Decision.** If the first message of a complaint flow gets a reply with no tool call, block it and replace it with a fixed sentence built from a real `get_customer_history` result. The condition has two parts only: re-measuring showed 12 of the 29 cases had no amount, name or time, so copying the prompt's wording into code would have missed 41%.
- **Trade-off.** The decision log's own summary: *"told in a prompt, followed about 84% of the time; forced in code, 100%."* Limits: block only when sure; log every firing into the measurement results; force the lookup only, never speed up `create_ticket`; the invariant suite must stay green.
- **Enforced by.** Service-layer gate in `src/agents/graph.py`; measured in the golden, adversarial and control groups.

## 10. ADR-061 — Policy search must be able to say "I don't know"

- **Context.** `search_policy` returned `found` for garbage or off-topic questions, with real policy chunks in the wrong context, which breaks "never fabricate". A single embedding-distance threshold failed on three measurements: a near-miss ("interbank fee") scored inside the range of true matches.
- **Decision.** Two independent layers: filter by `scope` at chunk level (one FAQ document mixes many topics), and an abstention gate using a cross-encoder reranker that encodes query and chunk together. No LLM grader, in line with the project's rule of deterministic guardrails.
- **Trade-off.** An extra sidecar service and CPU latency, in exchange for no extra LLM tokens. The gate fails closed: if the reranker is down, the answer is `not_found`. The cross-encoder model must be measured on real Vietnamese before it is chosen.
- **Enforced by.** `rerank_service/`, `src/rag/`, the policy-RAG eval set.
