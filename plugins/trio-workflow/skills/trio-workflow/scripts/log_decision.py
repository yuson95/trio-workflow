#!/usr/bin/env python3
"""Append one row to a plan's decision trail (<KEY>_DECISIONS.tsv).

The trail is append-only: a wrong row is superseded by a new row, never edited.
Cells are kept to one line, and cells that a spreadsheet would read as a
formula are prefixed with a single quote.

Usage:
  log_decision.py FILE PHASE DECISION WHY EVIDENCE RESULT
"""

import os
import sys
from datetime import datetime, timezone

HEADER = ["ts", "phase", "decision", "why", "evidence", "result"]
PHASES = {"start", "opening", "kickoff", "unit", "integrate", "decision", "retry", "violation", "blocker", "stop", "fix", "pause"}
FORMULA_STARTS = ("=", "+", "-", "@")


def clean(cell):
    text = " ".join(str(cell).replace("\t", " ").splitlines()).strip()
    return "'" + text if text.startswith(FORMULA_STARTS) else text


def append(path, phase, decision, why, evidence, result):
    if phase not in PHASES:
        raise ValueError(f"unknown phase {phase!r}; use one of {', '.join(sorted(PHASES))}")
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    needs_header = not os.path.exists(path) or os.path.getsize(path) == 0
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    row = [stamp, phase] + [clean(cell) for cell in (decision, why, evidence, result)]
    with open(path, "a", encoding="utf-8", newline="\n") as handle:
        if needs_header:
            handle.write("\t".join(HEADER) + "\n")
        handle.write("\t".join(row) + "\n")


def _utf8_output():
    """Agents read these scripts through pipes; make the bytes UTF-8 on every platform."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def main(argv=None):
    _utf8_output()
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 6:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        append(*args)
    except ValueError as error:
        print(f"DECISION not logged: {error}", file=sys.stderr)
        return 2
    print(f"DECISION logged phase={args[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
