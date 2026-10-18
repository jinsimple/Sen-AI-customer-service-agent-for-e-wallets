"""Hash of the contents of `src/**/*.py` — an identity label for the PRODUCT CODE, not the repo.

WHY IT EXISTS: `build_commit` was proven able to lie in BOTH directions on the same day
(17/08).

    label STILL, code MOVED   fin05-backend-1 reported `7450184` while
                              `graph.py` had been modified via `docker cp`
    label MOVED, code STILL   fin05ttl-backend-1 reported `36d6a1a` — a commit that
                              only touched `docs/`; the image contained nothing of it

⟹ `commit` is NOT a function of `src/`, in either direction. Using it as an image label
uses the WRONG KIND OF IDENTIFIER: it identifies the REPO STATE, whereas what needs
identifying is the PACKAGED CONTENT.

ALGORITHM TAKEN VERBATIM from `eval/measure_quality.py::dau_thuoc()` (field
`he_thong`) — deliberately reused, not rewritten. Two definitions of "which product code"
are two things that will drift apart, silently: the measurement layer and the packaging
layer would talk about two different objects using the same word.

⚠️ BLIND SPOT — stated PRECISELY, because an overstated sentence will be used to explain
away a real alarm, and misexplaining an alarm is the fastest way to get it switched off.

It hashes CONTENT, not paths (exactly like the original in `eval/`) — but
`sorted(rglob("*.py"))` sorts by PATH and then hashes content IN THAT ORDER.
So renaming a file:

    · that SHIFTS its sort position  ->  hash CHANGES     (measured: 6335a5b899e3 -> bdd05b87c4e4
                                                           for src/config.py -> zzz_config.py)
    · that KEEPS its sort position   ->  hash UNCHANGED   (measured: config.py -> configz.py,
                                                           still 6335a5b899e3)

So the blind spot is much narrower than "every rename": it is only a rename that does NOT
shift the ordering. An earlier description in this file overstated it in the weaker
direction — security caught it, and both numbers above are measured, not inferred.

Still not closed: keeping this hash IDENTICAL to the `eval/` version matters more than
closing a rare case, and closing it on one side would create exactly the drift this module
exists to prevent.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

# Same length as the other hash labels in the project, with the HASH METHOD declared
# explicitly — "a hash without its method is not evidence".
HASH_METHOD = "sha256-noi-dung-src-py-da-sap-xep-12"
STAMP_LENGTH = 12


def hash_source(original: Path | str | None = None) -> str:
    """Hash every `*.py` under `original` (default: the `src/` directory containing this file)."""
    original = Path(original) if original is not None else Path(__file__).resolve().parent
    h = hashlib.sha256()
    for f in sorted(original.rglob("*.py")):
        h.update(f.read_bytes())
    return h.hexdigest()[:STAMP_LENGTH]


# Label baked into the image at `docker build`, computed by `hash_source()` itself right
# after `COPY . .` (see Dockerfile). NO such file = not running inside an image built by the
# project's Dockerfile.
STAMP_PATH = Path("/app/.source_hash")


def build_time_stamp() -> str | None:
    """Hash label baked into the image, or None when running outside an image (local dev, tests).

    Distinguishing None (outside an image) from an empty/broken string (inside an image but
    with a bad label) is what lets the startup check FAIL HARD instead of silently skipping —
    see `_declare_source_image_drift` in main.py.
    """
    if not STAMP_PATH.exists():
        return None
    return STAMP_PATH.read_text().strip()
