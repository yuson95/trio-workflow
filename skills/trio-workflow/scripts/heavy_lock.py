#!/usr/bin/env python3
"""Machine-wide lock so only one heavy check runs at a time across agent sessions.

Heavy checks (full test suites, solver runs, browser suites, timing runs) give
flaky results when they overlap. Every session on the machine takes this lock
before a heavy run. The lock is a JSON file created atomically; a stale lock is
reported, never removed automatically, because its holder may still be running.

`run` also guards against a hung command holding the lock: after --idle-minutes
(default 30) without output on stdout or stderr, and without growth of any
--watch file, it stops the command's whole process tree, releases the lock and
exits 124. Python children run unbuffered so their progress counts as output.
--idle-minutes 0 turns the guard off.

Usage:
  heavy_lock.py --lock PATH status
  heavy_lock.py --lock PATH acquire --owner NAME --cmd TEXT [--wait SECONDS]
  heavy_lock.py --lock PATH release --owner NAME
  heavy_lock.py --lock PATH run --owner NAME [--wait SECONDS] [--idle-minutes N]
                [--watch FILE ...] -- COMMAND [ARGS...]

The lock path can also come from the TRIO_HEAVY_LOCK environment variable.
Exit codes: 0 ok, 2 usage error, 3 busy (wait expired), 4 held by another owner,
124 run stopped after the idle limit; otherwise `run` returns the command's code.
"""

import argparse
import json
import os
import signal
import socket
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone

BUSY, NOT_OWNER, USAGE, IDLE_STOPPED = 3, 4, 2, 124


def _now():
    return datetime.now(timezone.utc)


def _read(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        return None
    except (OSError, ValueError):
        # A lock that exists but cannot be parsed still blocks; report it as unknown.
        return {"owner": "unknown", "cmd": "unreadable lock file", "started": None}


def _age_hours(info):
    started = info.get("started") if info else None
    if not started:
        return None
    try:
        return (_now() - datetime.fromisoformat(started)).total_seconds() / 3600
    except ValueError:
        return None


def _describe(info, stale_hours):
    age = _age_hours(info)
    age_text = "unknown" if age is None else f"{age:.2f}h"
    stale = age is not None and age > stale_hours
    text = f"owner={info.get('owner')} cmd={info.get('cmd')!r} host={info.get('host')} age={age_text}"
    if stale:
        text += " STALE (report it; do not delete it without the operator)"
    return text


def _try_create(path, owner, cmd):
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    record = {"owner": owner, "cmd": cmd, "host": socket.gethostname(), "pid": os.getppid(), "started": _now().isoformat()}
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return False
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(record, handle)
    return True


def acquire(path, owner, cmd, wait, poll, stale_hours):
    deadline = time.monotonic() + max(wait, 0)
    announced = False
    while True:
        if _try_create(path, owner, cmd):
            print(f"HEAVY_LOCK acquired owner={owner} cmd={cmd!r}")
            return 0
        info = _read(path)
        if info is None:
            continue  # Released between our attempt and the read; try again at once.
        if info.get("owner") == owner:
            print(f"HEAVY_LOCK already held by this owner: {_describe(info, stale_hours)}")
            return 0
        if not announced:
            print(f"HEAVY_LOCK busy {_describe(info, stale_hours)}")
            announced = True
        if time.monotonic() >= deadline:
            print("HEAVY_LOCK wait expired; run later or report the holder")
            return BUSY
        time.sleep(min(poll, max(deadline - time.monotonic(), 0.05)))


def release(path, owner):
    info = _read(path)
    if info is None:
        print("HEAVY_LOCK not held")
        return 0
    if info.get("owner") != owner:
        print(f"HEAVY_LOCK held by another owner, not released: owner={info.get('owner')}")
        return NOT_OWNER
    os.remove(path)
    print(f"HEAVY_LOCK released owner={owner}")
    return 0


def status(path, stale_hours):
    info = _read(path)
    print("HEAVY_LOCK free" if info is None else f"HEAVY_LOCK held {_describe(info, stale_hours)}")
    return 0


def _forward(source, target, activity):
    """Copy a child's output to our own stream and stamp the time of each chunk."""
    out = getattr(target, "buffer", target)
    while True:
        chunk = os.read(source.fileno(), 4096)
        if not chunk:
            return
        activity[0] = time.monotonic()
        out.write(chunk)
        out.flush()


def _watch_sizes(paths):
    sizes = []
    for path in paths:
        try:
            stat = os.stat(path)
            sizes.append((stat.st_size, stat.st_mtime_ns))
        except OSError:
            sizes.append(None)
    return sizes


def _stop_tree(process):
    """Stop the command and everything it started; a hung browser is usually a grandchild."""
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(process.pid)], capture_output=True)
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
    try:
        process.wait(timeout=30)
    except subprocess.TimeoutExpired:
        process.kill()


def _run_watched(command, idle_minutes, watch):
    env = dict(os.environ)
    env.setdefault("PYTHONUNBUFFERED", "1")
    options = {"start_new_session": True} if os.name != "nt" else {}
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, **options)
    activity = [time.monotonic()]
    readers = [
        threading.Thread(target=_forward, args=(process.stdout, sys.stdout, activity), daemon=True),
        threading.Thread(target=_forward, args=(process.stderr, sys.stderr, activity), daemon=True),
    ]
    for reader in readers:
        reader.start()
    limit = idle_minutes * 60
    sizes = _watch_sizes(watch)
    while process.poll() is None:
        time.sleep(min(1.0, max(limit / 10, 0.05)))
        current = _watch_sizes(watch)
        if current != sizes:
            sizes = current
            activity[0] = time.monotonic()
        if time.monotonic() - activity[0] > limit:
            _stop_tree(process)
            print(
                f"HEAVY_LOCK stopped the command after {idle_minutes:g} min without output; "
                "process tree killed, lock released. Record the run as NOT_RUN and find what hung.",
                flush=True,
            )
            return IDLE_STOPPED
    for reader in readers:
        reader.join(timeout=5)
    return process.returncode


def run(path, owner, wait, poll, stale_hours, command, idle_minutes=30.0, watch=()):
    if not command:
        print("HEAVY_LOCK run needs a command after --", file=sys.stderr)
        return USAGE
    if idle_minutes < 0:
        print("HEAVY_LOCK --idle-minutes must be 0 (off) or more", file=sys.stderr)
        return USAGE
    code = acquire(path, owner, " ".join(command), wait, poll, stale_hours)
    if code != 0:
        return code
    try:
        if idle_minutes == 0:
            return subprocess.call(command)
        return _run_watched(command, idle_minutes, list(watch))
    finally:
        release(path, owner)


def _utf8_output():
    """Agents read these scripts through pipes; make the bytes UTF-8 on every platform."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def main(argv=None):
    _utf8_output()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--lock", default=os.environ.get("TRIO_HEAVY_LOCK"), help="lock file path (or TRIO_HEAVY_LOCK)")
    parser.add_argument("--stale-hours", type=float, default=3.0)
    parser.add_argument("--poll", type=float, default=10.0, help="seconds between checks while waiting")
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("status")
    take = sub.add_parser("acquire")
    take.add_argument("--owner", required=True)
    take.add_argument("--cmd", required=True)
    take.add_argument("--wait", type=float, default=0.0)
    give = sub.add_parser("release")
    give.add_argument("--owner", required=True)
    wrap = sub.add_parser("run")
    wrap.add_argument("--owner", required=True)
    wrap.add_argument("--wait", type=float, default=0.0)
    wrap.add_argument("--idle-minutes", type=float, default=30.0, help="stop after this long without output; 0 turns it off")
    wrap.add_argument("--watch", action="append", default=[], help="a log file whose growth counts as output (repeatable)")
    wrap.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    if not args.lock:
        print("HEAVY_LOCK needs --lock PATH or TRIO_HEAVY_LOCK", file=sys.stderr)
        return USAGE
    if args.action == "status":
        return status(args.lock, args.stale_hours)
    if args.action == "acquire":
        return acquire(args.lock, args.owner, args.cmd, args.wait, args.poll, args.stale_hours)
    if args.action == "release":
        return release(args.lock, args.owner)
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    return run(args.lock, args.owner, args.wait, args.poll, args.stale_hours, command, args.idle_minutes, args.watch)


if __name__ == "__main__":
    sys.exit(main())
