# Case Study — designing an AI agent that is not allowed to decide

> This page is written for an engineering reviewer who wants the "why", not just the "what" —
> every claim below links to the actual commit, decision log entry, or test that backs it, so
> you can check it rather than take my word for it.

## The problem

E-wallet customer support has an awkward shape: complaint volume is heavy, frontline agents need
to triage and investigate fast, but the thing they're triaging is other people's money. An LLM
is good at the first half (reading a messy complaint, pulling the right transaction out of a
noisy history, drafting a clear explanation) and categorically unsuited to the second half
(deciding whether to actually move money). The interesting engineering problem wasn't "can an
LLM help with support" — it obviously can — it was: **how do you build a system where that help
is structurally incapable of becoming a decision**, instead of relying on a prompt that says
"please don't"?

## Decision 1 — reject the obvious optimization

The first design let a support agent approve low-value, wallet-to-wallet complaints
themselves — smaller amounts, lower risk, less load on the supervisor. It got reversed. The
project's decision log records why, including the part that matters most: the argument *for*
keeping that shortcut was never wrong on its own terms.

> "To let a support agent self-approve looks more reasonable from a UX/ops angle, so an agent
> *will* propose going back to it. But: (a) 'outside your authority' is defined by **role**, not
> by a monetary threshold — a threshold creates a way around it (split the transaction into
> smaller pieces); (b) one approval path is easier to audit than two; (c) this is a financial
> product being pitched to e-wallet businesses, and an HITL rule with no exceptions is the
> sellable strength."
> — [docs/DECISIONS.md, ADR-002](docs/DECISIONS.md)

That last clause is the one worth sitting with: the easy version of "add nuance later" is exactly
the kind of change that looks like craftsmanship and is actually erosion. The rule became: only a
`supervisor` approves, for **every** transaction scope, no threshold, no exception — enforced as
`INV-01/03/04` and re-checked on every CI run by `tests/test_invariants.py`.

## Decision 2 — a rule the application layer enforces isn't a rule, it's a suggestion

Hard constraint 1 of the project's written constitution ([CLAUDE.md](CLAUDE.md) §2) is that
there is no path for the AI or a support agent to execute a refund themselves. That's easy to
write as an `if` statement in a route handler. It's also easy to accidentally route around: a
hand-written `UPDATE`, a careless migration, a new endpoint that forgets the check. So the same
rule is also a database CHECK constraint:

```sql
(status != 'approved') OR (approved_by IS NOT NULL AND approved_at IS NOT NULL)
```

> "A constraint inside a route's `if` only protects the path that goes through that route. A
> hand-written `UPDATE`, a migration script, a new endpoint that forgets to check — all of them
> get through. A CHECK constraint has no path around it."
> — [docs/DECISIONS.md, ADR-003](docs/DECISIONS.md)

This is the pattern the whole safety design follows: **every rule that must never break lives at
the layer that is hardest to accidentally bypass**, and the thing that makes that credible rather
than a slogan is `tests/test_invariants.py` — it doesn't read the rule from a document, it
introspects the running app (reads `app.routes`, pulls `allowed_roles` out of a decorator's
closure, parses the `CHECK` constraint via an AST) and fails if the code has drifted from
`contracts/`, the project's declared source of truth.

## Decision 3 — the gap that the role check alone didn't close

Role-based access control said: a support agent can *create* a proposal, only a supervisor can
*approve* one. That sounds complete. It wasn't: nothing stopped a supervisor from creating a
proposal and then approving their own. At that point "approval" is just the second click by the
same person, and the audit trail still looks perfectly clean.

> "`POST /tools/propose_resolution` allows **both** `cskh` and `supervisor`, while
> `POST /resolutions/{id}/approve` requires `supervisor` — so a supervisor can walk straight
> through both ends. At that point 'approval' is just the second action by the same person, and
> the entire meaning of the control disappears while every audit record still looks perfect."
> — [docs/DECISIONS.md, ADR-020](docs/DECISIONS.md)

The fix is a second, independent CHECK constraint — maker ≠ checker, enforced even when the
maker and the checker are both allowed to hold the approver role. Three logically equivalent ways
to write the SQL expression were considered and rejected before landing on the final one, for
reasons that are themselves part of the record (`IS DISTINCT FROM` needs a newer SQLite than CI
can guarantee everywhere; the short `!=` form relies on SQL's three-valued NULL logic in a way
that's correct but not obviously so to the next reader). And the ADR states its own limitation
rather than overselling the fix: *at the time it was written, 10 out of 10 existing resolution
rows had `created_by IS NULL`, meaning the constraint protected zero rows retroactively — it only
starts protecting resolutions created through the new code path.* That sentence is in the
decision log on purpose: a security control's existence is not evidence that past data is clean,
and the project had already been burned once by that exact inference ("Nguồn gốc" /
"so khoảng trống" sections of the decision log have more examples).

## Evidence, not just description

The claim "the agent doesn't fabricate numbers" is cheap to assert and expensive to actually
demonstrate, so the project kept dated, unedited transcripts from real runs instead of only
describing the behaviour. One example, reproduced in full in
[`eval/EVAL-EVIDENCE.md`](eval/EVAL-EVIDENCE.md):

- **Input** (a real customer message, informal Vietnamese, no accents): *"minh chuyen 171k cho
  ban hom 1/8 luc 12:47 ma ban bao chua nhan duoc"* ("I sent my friend 171k on Aug 1 at 12:47 and
  they say they haven't received it").
- The agent had to pick the **one correct transaction out of 9** sharing that exact amount,
  disambiguating purely by the timestamp the customer gave.
- Result: correct transaction ID, amount, time and status, in **12.5 seconds**, 1 tool call. The
  same question reproduced the same transaction ID across 2 different days and 2 different
  builds (22.3s and 16.4s respectively).

The write-up doesn't stop at the win. It also records a real defect found in that same
transcript: the PII-masking layer replaced the word *"bạn"* ("you"/"friend") with a `[PERSON]`
placeholder — a false positive, logged as a known finding (measured at roughly 8 out of 20 on a
clean-transcript sample) rather than quietly edited out of the evidence. A report that only shows
the cases that worked isn't evidence, it's marketing; this project's eval docs are written to
survive someone actually reading them.

## What I'd point to if you only have five minutes

1. [`tests/test_invariants.py`](tests/test_invariants.py) — read the file, not just the pass
   count. It introspects the live app rather than re-stating a rule as a second assertion.
2. [`docs/DECISIONS.md`](docs/DECISIONS.md) — 64 ADRs, each with the rejected alternative and why
   it was rejected, not just the final call.
3. [`eval/EVAL-EVIDENCE.md`](eval/EVAL-EVIDENCE.md) — real transcripts, including the ones that
   expose a bug.
4. [`contracts/`](contracts/) — the three YAML files that are the actual source of truth for the
   system's shape; code that drifts from them turns the test suite red before it ships.

## Lessons I'd apply again

- **A rule a human has to remember to check is a rule that will eventually not be checked.**
  Every hard constraint in this project ended up enforced at the layer with the fewest ways
  around it (a database constraint, not an `if`; an introspection test, not a comment saying
  "keep this in sync").
- **The alternative you rejected is worth writing down as carefully as the one you kept.** ADR-002
  isn't interesting because self-approval was obviously a bad idea — it's interesting because it
  wasn't, and the decision log says so instead of pretending the choice was easy.
- **A security fix should say what it doesn't fix.** ADR-020's "protects zero rows retroactively"
  sentence cost nothing to write and prevents a very specific, very plausible future mistake:
  someone reading "there's a constraint for this" and concluding the historical data must
  therefore be clean.
