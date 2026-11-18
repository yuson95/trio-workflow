#!/usr/bin/env python3
"""Tell the builder lead whether usage allows full parallel work, one worker, or a pause.

Agent subscriptions meter usage in windows (Codex, for example, a weekly window).
Parallel workers with large contexts can spend a whole window in an afternoon, and
a builder cut off mid-edit leaves a broken tree. The lead runs this before every
fan-out and at every integration, and follows the verdict:

  FULL        run up to the worker cap in 0_RULES
  ONE_WORKER  run one batch at a time; start no parallel batches
  PAUSE       follow builder.md "Pause" now

Usage:
  usage_guard.py [--reduce-below PCT] [--pause-below PCT]              # read Codex's own record
  usage_guard.py --left PCT [--reduce-below PCT] [--pause-below PCT]   # a number the operator gave

Without --left, the script reads the newest rate-limit reading that Codex writes into
its session logs ($CODEX_HOME/sessions, default ~/.codex/sessions). Other tools keep
no such record on disk: ask the operator for the number shown in the tool's usage page.

Exit codes: 0 FULL, 2 usage error, 3 ONE_WORKER, 4 PAUSE, 5 no reading found.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

FULL, USAGE, ONE_WORKER, PAUSE, UNKNOWN = 0, 2, 3, 4, 5
TAIL_BYTES = 4 * 1024 * 1024
NEWEST_FILES = 8


def _utf8_output():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def _tail_lines(path):
    """Return the complete lines in the last TAIL_BYTES of a file."""
    with open(path, "rb") as handle:
        handle.seek(0, os.SEEK_END)
        size = handle.tell()
        handle.seek(max(0, size - TAIL_BYTES))
        data = handle.read()
    lines = data.decode("utf-8", errors="replace").splitlines()
    return lines if size <= TAIL_BYTES else lines[1:]


def newest_codex_reading(codex_home):
    """Return (timestamp, [(name, used_percent, window_minutes, resets_at)]) or None."""
    sessions = Path(codex_home) / "sessions"
    if not sessions.is_dir():
        return None
    files = sorted(sessions.rglob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)[:NEWEST_FILES]
    best = None
    for path in files:
        for line in reversed(_tail_lines(path)):
            if '"rate_limits"' not in line:
                continue
            try:
                row = json.loads(line)
            except ValueError:
                continue
            limits = (row.get("payload") or {}).get("rate_limits") or {}
            windows = []
            for name in ("primary", "secondary"):
                window = limits.get(name) or {}
                if "used_percent" in window:
                    windows.append((name, float(window["used_percent"]), window.get("window_minutes"), window.get("resets_at")))
            if windows:
                stamp = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
                if best is None or stamp > best[0]:
                    best = (stamp, windows)
                break
    return best


def verdict(left, reduce_below, pause_below):
    if left < pause_below:
        return "PAUSE", PAUSE
    if left < reduce_below:
        return "ONE_WORKER", ONE_WORKER
    return "FULL", FULL


def main(argv=None):
    _utf8_output()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--left", type=float, help="percent of the usage window left, as the tool shows it")
    parser.add_argument("--reduce-below", type=float, default=30.0, help="percent left below which only one worker runs")
    parser.add_argument("--pause-below", type=float, default=10.0, help="percent left below which the builder pauses")
    parser.add_argument("--codex-home", default=os.environ.get("CODEX_HOME") or str(Path.home() / ".codex"))
    args = parser.parse_args(argv)
    if not 0 <= args.pause_below <= args.reduce_below <= 100:
        print("USAGE error: need 0 <= --pause-below <= --reduce-below <= 100")
        return USAGE

    if args.left is not None:
        if not 0 <= args.left <= 100:
            print("USAGE error: --left must be between 0 and 100")
            return USAGE
        name, code = verdict(args.left, args.reduce_below, args.pause_below)
        print(f"USAGE {name}: {args.left:.0f}% left (given by the operator)")
        return code

    reading = newest_codex_reading(args.codex_home)
    if reading is None:
        print(f"USAGE UNKNOWN: no rate-limit reading under {Path(args.codex_home) / 'sessions'}; "
              "ask the operator for the percent left and rerun with --left")
        return UNKNOWN
    stamp, windows = reading
    now = datetime.now(timezone.utc)
    worst = None
    notes = []
    for name, used, minutes, resets_at in windows:
        left = 100.0 - used
        if resets_at and datetime.fromtimestamp(resets_at, timezone.utc) <= now:
            notes.append(f"{name} window has reset since this reading")
            left = 100.0
        if worst is None or left < worst[1]:
            worst = (name, left, minutes, resets_at)
    name, left, minutes, resets_at = worst
    label, code = verdict(left, args.reduce_below, args.pause_below)
    age_min = (now - stamp).total_seconds() / 60
    reset = datetime.fromtimestamp(resets_at).strftime("%Y-%m-%d %H:%M") if resets_at else "unknown"
    span = f"{minutes / 1440:.0f}-day" if minutes and minutes >= 1440 else f"{minutes or '?'}-minute"
    print(f"USAGE {label}: {left:.0f}% left in the Codex {span} window (reading {age_min:.0f} min old; resets {reset})")
    for note in notes:
        print(f"  note: {note}")
    return code


if __name__ == "__main__":
    sys.exit(main())
