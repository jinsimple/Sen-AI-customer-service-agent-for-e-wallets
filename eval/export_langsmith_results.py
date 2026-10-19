#!/usr/bin/env python3
"""Export LangSmith experiment results into the README "Results" markdown table.

STATUS: written, NOT RUN. The repository keeps LangSmith tracing OFF on purpose
(src/config.py, F-30: prompts must not leave the system), and it contains no LangSmith
dataset or evaluator. Turn LangSmith on deliberately, run the suites, then use this script.

What it does (read-only against LangSmith, writes one local markdown file):
  1. Reads LANGSMITH_API_KEY from the environment (never from a file, never logged).
  2. Lists the experiments (projects) attached to each dataset named in --datasets.
  3. For every experiment, reads its run count, start date and the mean of one feedback key
     (--pass-key, default "pass", expected to be 0/1 per case).
  4. Prints a markdown table  | Suite | Cases | Pass rate | Date | Judge model |.

Safety rules baked in:
  * Anything whose name contains "heldout" / "held-out" / "held_out" is SKIPPED and the skip is
    logged. The held-out set is never exported or summarised here.
  * Nothing is invented: a value LangSmith does not return is written as "[CHƯA XÁC MINH]".
  * Every step is logged to stderr (what is read, what is found, what is skipped, and why).

Usage:
  export LANGSMITH_API_KEY=...            # a read-only key is enough
  python eval/export_langsmith_results.py \\
      --datasets fin05-golden fin05-adversarial fin05-rag-policy \\
      --pass-key pass --out docs/results-table.md

The "Judge model" column is taken from the experiment's metadata key `judge_model`. Tag your
experiments with it when you run them (client.evaluate(..., metadata={"judge_model": "..."})).
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime

UNKNOWN = "[CHƯA XÁC MINH]"
HELDOUT_MARKERS = ("heldout", "held-out", "held_out")

log = logging.getLogger("export_langsmith")


def _is_heldout(name: str | None) -> bool:
    lowered = (name or "").lower()
    return any(marker in lowered for marker in HELDOUT_MARKERS)


def _fmt_date(value) -> str:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    return UNKNOWN


def _pass_rate(project, pass_key: str) -> str:
    """Mean of feedback `pass_key` as a percentage, from the project's feedback stats."""
    stats = getattr(project, "feedback_stats", None) or {}
    entry = stats.get(pass_key)
    if not entry:
        log.warning("    no feedback stats for key %r on experiment %r (available keys: %s)",
                    pass_key, project.name, sorted(stats) or "none")
        return UNKNOWN
    mean = entry.get("avg")
    if mean is None:
        log.warning("    feedback key %r has no 'avg' on experiment %r", pass_key, project.name)
        return UNKNOWN
    return f"{mean * 100:.1f}%"


def _judge_model(project) -> str:
    metadata = getattr(project, "extra", None) or {}
    metadata = metadata.get("metadata", {}) if isinstance(metadata, dict) else {}
    value = metadata.get("judge_model")
    if not value:
        log.warning("    experiment %r has no metadata key 'judge_model'", project.name)
        return UNKNOWN
    return str(value)


def collect_rows(client, datasets: list[str], pass_key: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for dataset in datasets:
        log.info("dataset %r", dataset)
        if _is_heldout(dataset):
            log.warning("  SKIPPED dataset %r: held-out sets are never exported", dataset)
            continue
        try:
            projects = list(client.list_projects(reference_dataset_name=dataset))
        except Exception as exc:  # network, auth, unknown dataset
            log.error("  cannot list experiments for %r: %s", dataset, exc)
            continue
        log.info("  found %d experiment(s)", len(projects))
        for project in projects:
            if _is_heldout(project.name):
                log.warning("  SKIPPED experiment %r: held-out marker in name", project.name)
                continue
            log.info("  experiment %r (runs=%s, started=%s)",
                     project.name, getattr(project, "run_count", None), getattr(project, "start_time", None))
            cases = getattr(project, "run_count", None)
            rows.append([
                f"{dataset} / {project.name}",
                str(cases) if cases is not None else UNKNOWN,
                _pass_rate(project, pass_key),
                _fmt_date(getattr(project, "start_time", None)),
                _judge_model(project),
            ])
    return rows


def render_table(rows: list[list[str]]) -> str:
    header = "| Suite | Cases | Pass rate | Date | Judge model |\n|---|---|---|---|---|\n"
    body = "\n".join("| " + " | ".join(row) + " |" for row in rows)
    return header + body + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--datasets", nargs="+", required=True, help="LangSmith dataset names to export")
    parser.add_argument("--pass-key", default="pass", help="feedback key holding 0/1 per case")
    parser.add_argument("--out", default="-", help="output markdown file, '-' for stdout")
    parser.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s", stream=sys.stderr)

    api_key = os.environ.get("LANGSMITH_API_KEY")
    if not api_key:
        log.error("LANGSMITH_API_KEY is not set; nothing was read. Aborting.")
        return 2
    log.info("LANGSMITH_API_KEY is set (value not logged)")

    try:
        from langsmith import Client
    except ImportError:
        log.error("the 'langsmith' package is not installed (pip install langsmith). Aborting.")
        return 2

    client = Client(api_key=api_key)
    rows = collect_rows(client, args.datasets, args.pass_key)
    if not rows:
        log.error("no experiments collected; output not written")
        return 1

    table = render_table(rows)
    if args.out == "-":
        print(table)
    else:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(table)
        log.info("wrote %d row(s) to %s", len(rows), args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
