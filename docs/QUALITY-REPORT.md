# Quality report

This report states what the repository can prove. Every number below has a source file. Items the repository cannot prove are marked `[CHƯA XÁC MINH]`. It is a draft built from the repo; the author's own quality report can replace or extend it.

## 1. How quality is checked

| Layer | What it checks | Where | Size |
|---|---|---|---|
| Structural invariants | The five hard constraints against the **running app**: roles per route, CHECK constraints, tool names | `tests/test_invariants.py`, `contracts/` | 23 tests |
| Backend tests | Units, security, integration | `tests/` | 598 test functions in 111 files |
| Frontend E2E | Real UI, asserting on the rendered DOM | `frontend/e2e/` | 38 Playwright specs |
| Agent evaluation | Behaviour of the agent on labelled scenarios | `eval/*.jsonl`, `eval/run_*.py` | 360 cases in 15 non-sealed sets, plus a 60-case held-out set (see §4) |
| Manual evidence | Verbatim transcripts from real runs, including defects | `eval/EVAL-EVIDENCE.md` | 7 cases (Aug 16) |

Test counts: `git grep -hE '^\s*(async )?def test_' -- tests | wc -l` (598); `ls frontend/e2e/*.spec.ts | wc -l` (38). Evaluation counts: `grep -c .` on each file in `eval/`, held-out excluded.

### Models used in evaluation

- **Agent under test:** `qwen3.8-flash` through DashScope (the model of record for the Aug 31 benchmark).
- **Judge and attacker simulator:** OpenAI `gpt-4o-mini`, pinned in `src/config.py` and overridable with `EVAL_JUDGE_MODEL`.
- The judge is a different model from the agent on purpose, so changing the agent does not move the yardstick (comments in `src/config.py`).
- Rule-based checks run first, the LLM judge only where a rule cannot grade (`eval/_llm_judge.py`, 14 judge cases).

## 2. Benchmark of Aug 31, 2026 (recorded in the repo)

Source: [`eval/results/benchmark-31aug/README.md`](../eval/results/benchmark-31aug/README.md). One model (`qwen3.8-flash`), one code hash (`9c17c5684c9a`), one day, 246 cases, 0 cases lost to infrastructure. Cost for the whole day: 12,104,482 tokens over 1,467 model calls (including failed turns).

| Set | Cases passed completely | Individual checks passed |
|---|---|---|
| Golden (120 cases) | 32 (26.7%) | 319 / 462 (69.0%) |
| Held-out (60 cases) | 14 (23.3%) | 158 / 236 (66.9%) |
| Gap | −3.4 points | −2.1 points |
| Adversarial (46 single-turn + 20 multi-turn) | 60 / 66 passed by the checker | 4 of the 6 failures were checker false alarms, 2 were real defects |

How to read these numbers:

- The gap between golden and held-out is within the sampling error of 60 cases, so the benchmark shows **no sign of overfitting to the golden set**.
- "Completely passed" is strict: every check of a case must pass. The 26.7% was recorded at code hash `9c17c5684c9a`; later changes (for example the forced-lookup gate of ADR-056, dated after the run) are not reflected. It is not the current pass rate. `[CHƯA XÁC MINH: post-fix re-run]`
- The adversarial checker matches strings and is blind to negation. The repo's own wording is: *"no violation found among flagged cases, after reading by hand"*. It does **not** support the claim "safe on 66 adversarial cases". Only 20 of the 60 cases the checker passed were read by hand.
- `khong_tao_ticket_hop_le` is a rate of **correct** behaviour, not of failure.
- The held-out set was used in this run, and the benchmark README calls it spent for future overfitting checks. Treat it as consumed.

## 3. Retrieval (policy RAG) baseline

Source: [`eval/results/rag_context_precision_recall_baseline.json`](../eval/results/rag_context_precision_recall_baseline.json), measured on Sep 5, 2026 against the live `/policy-search` route, 34 cases. Method: deterministic text-overlap context precision and recall, no LLM, precision de-duplicated by unique content. The formulas are borrowed from RAGAS; the RAGAS library was not run.

| Axis | Cases | Mean precision | Mean recall |
|---|---|---|---|
| R1 | 4 | 0.250 | 0.500 |
| R2 | 3 | 0.528 | 0.833 |
| R3 | 3 | 0.347 | 0.500 |
| P1 / P2 / P3 | 3 each | 1.000 | n/a |
| S1 | 3 | 0.306 | 0.833 |
| F1 | 3 | 0.000 | n/a |
| T1 | 3 | 0.528 | 0.833 |
| V1 | 3 | 0.500 | 1.000 |
| U1 | 3 | 0.778 | 1.000 |

The axis codes are the case groups of `eval/rag_policy_set.jsonl`; their descriptions are not repeated in this file. `[CHƯA XÁC MINH: plain-language name of each axis]`. These are baseline values, reported as measured, and several are low. The abstention gate of ADR-061 (cross-encoder reranker, fails closed) was added to improve precision on out-of-scope questions.

## 4. Held-out set, honestly

`eval/heldout_set.jsonl` has 60 cases. The project notes describe it as sealed and run once. ADR-059 and the Aug 31 benchmark README show it ran in the Aug 31 benchmark and was then treated as spent. This report did not open the file. A new unseen set would be needed for a fresh overfitting check. `[CHƯA XÁC MINH]`

## 5. Safety properties and how they are checked

| Property | Check |
|---|---|
| Only a supervisor can approve | Role matrix compared against the real routes (invariants); DB constraint (INV-07) |
| Proposer cannot approve own proposal | DB constraint, INV-15 |
| Figures trace to tool results | Output filter with origin-rule; corpus `eval/corpus_origin_rule.jsonl` (14 cases) |
| PII masked before the LLM | `tests/test_security/` |
| Fraud flag never locks a wallet | No code path connects them; constraint 5 in `CLAUDE.md` |
| The system never moves money | No code in `src/` changes a balance or locks a wallet (grep-verified, Oct 19) |

## 6. Latency and cost

| Measurement | Value | Source |
|---|---|---|
| Greeting on the deterministic fast path | 0 tokens, 0.01–0.06 s | `scripts/BAN-GIAO-coder-2026-08-17.md` |
| Same greeting through the full model path | 6,216 input tokens, 8.7 s | same file, single request |
| Median tokens per conversation and latency per turn | `[CHƯA XÁC MINH]` | not in the repo; the 246-case size matches the Aug 31 run |

## 7. Known gaps

- No post-fix full re-run of golden and adversarial sets is recorded in the repo.
- No LLM-based RAGAS metrics; only the deterministic baseline above.
- No LangSmith dataset or evaluator in the repo (tracing is disabled on purpose). The Results table in the README is empty until a re-run is exported.
- `create_ticket` two-step confirmation (ADR-051) is now implemented at tool level and covered by offline tests, but the prompt changed with it and no live-model re-run exists yet; the contract's `return_direct` string output is not implemented.
- The model alias `qwen3.8-flash` has no date pin, so the Aug 31 numbers may not be reproducible later (ADR-059).
- All data is synthetic; there are no real-user conversations.
