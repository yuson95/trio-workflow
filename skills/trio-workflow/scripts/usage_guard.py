#!/usr/bin/env python3
"""Tell the builder lead whether usage allows full parallel work, one worker, or a pause.

Agent subscriptions meter usage in windows (a 5-hour window, a weekly window). What is
left when a window resets expires, so holding back never buys more work in a window:
it only moves work later. The guard therefore runs at full speed until a small reserve
(--pause-below, default 3%) that lets the lead stop cleanly: commit wip, update the
handoff and the progress file. The lead runs this before every fan-out and at every
integration, and follows the verdict:

  FULL        run up to the worker cap in 0_RULES
  ONE_WORKER  run one batch at a time; start no parallel batches
  PAUSE       follow builder.md "Pause" now; resume after the reset

ONE_WORKER appears only in a reserve band that a project sets with --reduce-below, for
example to keep quota for a reviewer who shares the window. Near the reset the band is
waived, because what it would keep expires anyway: give --resets-in (hours until the
window resets) and the band does not apply within --near-hours (default 24).

Usage:
  usage_guard.py [--reduce-below PCT] [--pause-below PCT]                 # read Codex's own record
  usage_guard.py --left PCT [--resets-in HOURS] [--reduce-below PCT] [--pause-below PCT]
  usage_guard.py --threads [--cap TOKENS] [--active-minutes MIN]          # also list each live thread

Without --left, the script reads the newest rate-limit reading that Codex writes into
its session logs ($CODEX_HOME/sessions, default ~/.codex/sessions), including the time
each window resets. Other tools keep no such record on disk: take the percent left and
the reset time from the tool's usage page, for the window with the least left.

--threads adds one line per Codex thread active in the last --active-minutes: its agent
path, its current context (the input size of its last call) and its call count. NEAR
marks a context past the soft cap (--soft times --cap, default 80%): the worker finishes
its current unit and ends. OVER marks a context past --cap: it commits wip and ends now
(builder.md rule 8).

Exit codes: 0 FULL, 2 usage error, 3 ONE_WORKER, 4 PAUSE, 5 no reading found.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

FULL, USAGE, ONE_WORKER, PAUSE, UNKNOWN = 0, 2, 3, 4, 5
TAIL_BYTES = 2 * 1024 * 1024
RECENT_DAYS = 7
TIMESTAMP = re.compile(r'"timestamp":\s*"([^"]+)"')


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


def _recent_logs(sessions, now):
    """Session logs started or modified within RECENT_DAYS.

    Codex files a log under sessions/YYYY/MM/DD by the day the thread started, and keeps
    it open while the thread runs. Windows may not update the modified time of a file
    that is still open, so the folder date counts as well as the modified time.
    """
    horizon = now - RECENT_DAYS * 86400
    for path in sessions.rglob("*.jsonl"):
        parts = path.relative_to(sessions).parts
        try:
            started = datetime(int(parts[0]), int(parts[1]), int(parts[2]), tzinfo=timezone.utc).timestamp()
        except (ValueError, IndexError):
            started = 0
        if path.stat().st_mtime >= horizon or started >= horizon - 86400:
            yield path


def _last_timestamp(lines):
    for line in reversed(lines):
        found = TIMESTAMP.search(line[:120])
        if found:
            try:
                return datetime.fromisoformat(found.group(1).replace("Z", "+00:00")).timestamp()
            except ValueError:
                continue
    return None


def newest_codex_reading(codex_home):
    """Return (timestamp, [(name, used_percent, window_minutes, resets_at)]) or None."""
    sessions = Path(codex_home) / "sessions"
    if not sessions.is_dir():
        return None
    best = None
    for path in _recent_logs(sessions, datetime.now(timezone.utc).timestamp()):
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


def live_threads(codex_home, active_minutes, now=None):
    """Return [(label, context_tokens, calls, minutes_since_last_call)] for recently active threads."""
    sessions = Path(codex_home) / "sessions"
    if not sessions.is_dir():
        return []
    now = now or datetime.now(timezone.utc).timestamp()
    found = []
    for path in _recent_logs(sessions, now):
        last_write = _last_timestamp(_tail_lines(path))
        if last_write is None or now - last_write > active_minutes * 60:
            continue
        label, context, calls, last = "lead", None, 0, None
        seen = set()
        with open(path, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if '"session_meta"' in line[:200]:
                    try:
                        meta = json.loads(line).get("payload") or {}
                    except ValueError:
                        meta = {}
                    label = meta.get("agent_path") or f"lead {str(meta.get('id', ''))[:8]}".strip()
                elif '"token_usage_record"' in line[:200]:
                    try:
                        row = json.loads(line)
                    except ValueError:
                        continue
                    payload = row.get("payload") or {}
                    if payload.get("response_id") in seen:
                        continue
                    seen.add(payload.get("response_id"))
                    calls += 1
                    context = (payload.get("usage") or {}).get("input_tokens", context)
                    last = row.get("timestamp", last)
        if context is None:
            continue
        idle = None
        if last:
            idle = (now - datetime.fromisoformat(last.replace("Z", "+00:00")).timestamp()) / 60
        found.append((label, context, calls, idle))
    return sorted(found, key=lambda item: -item[1])


def verdict(left, reduce_below, pause_below, resets_in=None, near_hours=24.0):
    """Return (label, exit code, note). The reserve band is waived within near_hours of the reset."""
    if left < pause_below:
        return "PAUSE", PAUSE, ""
    if left < reduce_below:
        if resets_in is not None and resets_in <= near_hours:
            return "FULL", FULL, f"reserve band waived: the window resets in {resets_in:.1f} h"
        return "ONE_WORKER", ONE_WORKER, ""
    return "FULL", FULL, ""


def main(argv=None):
    _utf8_output()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--left", type=float, help="percent of the usage window left, as the tool shows it")
    parser.add_argument("--resets-in", type=float, help="hours until the window with the least left resets")
    parser.add_argument("--reduce-below", type=float,
                        help="percent left below which only one worker runs (a reserve band; default: none)")
    parser.add_argument("--pause-below", type=float, default=3.0, help="percent left below which the builder pauses")
    parser.add_argument("--near-hours", type=float, default=24.0, help="within this many hours of the reset the reserve band is waived")
    parser.add_argument("--codex-home", default=os.environ.get("CODEX_HOME") or str(Path.home() / ".codex"))
    parser.add_argument("--threads", action="store_true", help="also list each live Codex thread and its context")
    parser.add_argument("--cap", type=int, default=150_000, help="context in tokens above which a thread is marked OVER")
    parser.add_argument("--soft", type=float, default=0.8, help="fraction of --cap above which a thread is marked NEAR")
    parser.add_argument("--active-minutes", type=float, default=120.0, help="threads written to within this many minutes")
    args = parser.parse_args(argv)
    if args.reduce_below is None:
        args.reduce_below = args.pause_below
    if not 0 <= args.pause_below <= args.reduce_below <= 100:
        print("USAGE error: need 0 <= --pause-below <= --reduce-below <= 100")
        return USAGE
    if args.left is not None and not 0 <= args.left <= 100:
        print("USAGE error: --left must be between 0 and 100")
        return USAGE
    if (args.resets_in is not None and args.resets_in < 0) or args.near_hours < 0:
        print("USAGE error: --resets-in and --near-hours must be 0 or more")
        return USAGE
    if not 0 < args.soft <= 1:
        print("USAGE error: --soft must be above 0 and at most 1")
        return USAGE

    code = _usage_line(args)
    if args.threads:
        threads = live_threads(args.codex_home, args.active_minutes)
        if not threads:
            print(f"THREADS none active in the last {args.active_minutes:.0f} min")
        for label, context, calls, idle in threads:
            flag = "OVER" if context > args.cap else "NEAR" if context > args.soft * args.cap else "ok"
            since = f"{idle:.0f} min ago" if idle is not None else "unknown"
            print(f"THREAD {flag:4} {label}: context {context / 1000:.0f}k tokens, {calls} calls, last call {since}")
    return code


def _usage_line(args):
    """Print the usage verdict line and return its exit code."""
    if args.left is not None:
        name, code, note = verdict(args.left, args.reduce_below, args.pause_below, args.resets_in, args.near_hours)
        reset = f"; resets in {args.resets_in:.1f} h" if args.resets_in is not None else ""
        print(f"USAGE {name}: {args.left:.0f}% left (given by the operator{reset})")
        if note:
            print(f"  note: {note}")
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
    resets_in = args.resets_in
    if resets_in is None and resets_at:
        resets_in = max((datetime.fromtimestamp(resets_at, timezone.utc) - now).total_seconds() / 3600, 0.0)
    label, code, note = verdict(left, args.reduce_below, args.pause_below, resets_in, args.near_hours)
    if note:
        notes.append(note)
    age_min = (now - stamp).total_seconds() / 60
    reset = datetime.fromtimestamp(resets_at).strftime("%Y-%m-%d %H:%M") if resets_at else "unknown"
    span = f"{minutes / 1440:.0f}-day" if minutes and minutes >= 1440 else f"{minutes or '?'}-minute"
    print(f"USAGE {label}: {left:.0f}% left in the Codex {span} window (reading {age_min:.0f} min old; resets {reset})")
    for note in notes:
        print(f"  note: {note}")
    return code


if __name__ == "__main__":
    sys.exit(main())
