"""Usage ledger — records the tokens of EVERY turn into JSONL on a volume, to have a BASELINE.

WHY IT EXISTS (measured 17/08): grepping for usage across the logs of all three stacks
returned **0 lines**, and no table stored tokens. Usage lived only in process stdout, and
`docker logs` is PER-CONTAINER — every recreate wipes it. That afternoon alone I recreated
6 times in two hours.

⟹ Today the project **cannot answer** "how much are we spending, and where". Worse for the
token-saving effort: **there is no baseline to prove a cut actually worked** — after a cut
there is nothing to compare against, and "optimised" becomes an unverifiable claim.

Same family as F-33c: numbers that get produced and then vanish.

## Why JSONL on a volume, NOT a new DB table

Measured before choosing, not chosen by habit:

    write /app/logs/... -> recreate -> still readable          ✅ (actually tried)
    container stdout    -> recreate -> old container log LOST  ✅ (actually tried)

`logs_data:/app/logs` is a **named volume** (docker-compose.yml); it survives recreate
and `down` (lost only on `down -v`).

A new DB table would also work, but it drags in a migration + `models.py`, while the JSONL
path gives us a baseline **today** instead of queueing behind three pending ADRs. This is a
MEASUREMENT tool, not business data — it needs no join with `tickets`, no integrity
constraints, and should not sit on the product's write path.

## Limitations, declared up front

· lost on `docker compose down -v` (same fate as `postgres_data`)
· one ledger per stack, never merged
· cannot be joined with business records — `thread_id` is the only link
· NEVER records conversation content. Only counts and labels.
"""
from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path

_logger = logging.getLogger("fin05.usage")

LEDGER_PATH = Path(os.environ.get("USAGE_LEDGER_FILE", "/app/logs/usage.jsonl"))

# Writes from many workers/threads into the same file: each line is one short `write`
# (< PIPE_BUF), so POSIX append is already atomic per line. This lock only prevents
# interleaving between threads WITHIN one process.
_key = threading.Lock()
_already_warned = False


def record_usage(record_row: dict, route: Path | None = None) -> None:
    """Write one line. NEVER break a chat turn because of a ledger-write error.

    Swallowing the error here is correct — a broken measurement ledger must not cost the
    customer their answer. But swallowing it SILENTLY is not: warn ONCE (not every turn —
    that is exactly the alarm that cries wolf and gets switched off), and an empty ledger
    exposes itself as soon as someone reads it.

    `route` — 18/08: lets ONE write function serve SEVERAL ledgers. The second ledger is
    `egress_ledger.jsonl` (`src/egress_gate.py`).

    🔴 SEVERAL LEDGERS, ONE WRITER — these are two separate decisions, don't merge them:

    · **Several ledgers** because `usage.jsonl` is *one line per CHAT TURN* (18 fields,
      with `thread_id`/`ly_do_fallback`/`duong`) while the egress ledger is *one line per
      HTTP REQUEST*. Different GRAIN, different POPULATION. Mixing them makes `wc -l`
      return a number that is **neither the turn count nor the request count** — and it
      **looks valid**. Exactly the "mixed population" trap (STATE §8) the project already
      paid for with `4%` (13/370) and `so_luot_goi_model = 0`.

    · **One writer** because this function carries two properties that are hard to get
      right twice: *never break a turn because of a ledger error*, and *warn ONCE instead
      of every turn*. A second writer would be two definitions of the same thing — they
      will drift, and drift silently.
    """
    global _already_warned
    dest = route or LEDGER_PATH
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record_row, ensure_ascii=False)
        with _key, dest.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as e:  # noqa: BLE001 — xem docstring
        if not _already_warned:
            _already_warned = True
            _logger.error(
                "khong_ghi_duoc_so_usage",
                extra={"duong": str(dest), "loi": type(e).__name__,
                       "hau_qua": "mat moc nen cho moi phep so truoc/sau"},
            )
