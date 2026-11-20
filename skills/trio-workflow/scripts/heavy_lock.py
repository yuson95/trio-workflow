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

`run` and `run-steps` never share the lock, not even with their own owner: a
second run waits like any other session, and each run releases only the
acquisition it made. To keep the lock across several commands, list them in a
steps file and use `run-steps`.

`run-steps` runs the steps of a JSON file in order under one acquisition. A
worker writes the file and checks it with --dry-run; the lead runs it. Each step
writes its output to its own log and prints one summary line. The file is a list
of steps, or {"steps": [...]}. Each step has:
  name   short label (required)
  cmd    the command as a list of strings (required)
  log    the step's log file (required)
  cwd    working directory (optional)
  env    extra environment variables, {"NAME": "value"} (optional)
  expect lines the log must contain for the step to pass (optional)
  idle_minutes, watch   as for `run` (optional)
Relative paths resolve against the steps file's folder.

Usage:
  heavy_lock.py --lock PATH status
  heavy_lock.py --lock PATH acquire --owner NAME --cmd TEXT [--wait SECONDS]
  heavy_lock.py --lock PATH release --owner NAME
  heavy_lock.py --lock PATH run --owner NAME [--wait SECONDS] [--idle-minutes N]
                [--watch FILE ...] -- COMMAND [ARGS...]
  heavy_lock.py --lock PATH run-steps --owner NAME --steps FILE [--wait SECONDS]
                [--stop-on-fail] [--dry-run]

The lock path can also come from the TRIO_HEAVY_LOCK environment variable.
Exit codes: 0 ok, 2 usage error, 3 busy (wait expired), 4 held by another owner,
124 run stopped after the idle limit; otherwise `run` returns the command's code.
`run-steps` returns 0 when every step passed and 1 otherwise.
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
import uuid
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
    """Create the lock file atomically; return the new acquisition's token, or None if the lock is taken."""
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    token = uuid.uuid4().hex
    record = {
        "owner": owner,
        "cmd": cmd,
        "host": socket.gethostname(),
        "pid": os.getpid(),
        "parent_pid": os.getppid(),
        "token": token,
        "started": _now().isoformat(),
    }
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return None
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(record, handle)
    return token


def _acquire(path, owner, cmd, wait, poll, stale_hours, share_with_owner):
    """Return (exit code, token). The token is None when an earlier acquisition of this owner is reused."""
    deadline = time.monotonic() + max(wait, 0)
    announced = False
    while True:
        token = _try_create(path, owner, cmd)
        if token:
            print(f"HEAVY_LOCK acquired owner={owner} cmd={cmd!r}")
            return 0, token
        info = _read(path)
        if info is None:
            continue  # Released between our attempt and the read; try again at once.
        same_owner = info.get("owner") == owner
        if same_owner and share_with_owner:
            print(f"HEAVY_LOCK already held by this owner: {_describe(info, stale_hours)}")
            return 0, None
        if not announced:
            note = " (same owner: runs never share the lock; put several commands in one run-steps file)" if same_owner else ""
            print(f"HEAVY_LOCK busy {_describe(info, stale_hours)}{note}")
            announced = True
        if time.monotonic() >= deadline:
            print("HEAVY_LOCK wait expired; run later or report the holder")
            return BUSY, None
        time.sleep(min(poll, max(deadline - time.monotonic(), 0.05)))


def acquire(path, owner, cmd, wait, poll, stale_hours):
    return _acquire(path, owner, cmd, wait, poll, stale_hours, share_with_owner=True)[0]


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


def _release_token(path, owner, token):
    """Release only the acquisition this run made; never a lock someone took after it."""
    info = _read(path)
    if info is None:
        print("HEAVY_LOCK not held")
        return 0
    if info.get("token") != token:
        print(f"HEAVY_LOCK not released: it now belongs to another acquisition (owner={info.get('owner')})")
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


def _run_watched(command, idle_minutes, watch, out=None, err=None, cwd=None, extra_env=None):
    """Run the command, forwarding its output; return (exit code, stopped for idleness)."""
    env = dict(os.environ)
    env.setdefault("PYTHONUNBUFFERED", "1")
    env.update(extra_env or {})
    options = {"start_new_session": True} if os.name != "nt" else {}
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, cwd=cwd, **options)
    activity = [time.monotonic()]
    readers = [
        threading.Thread(target=_forward, args=(process.stdout, out or sys.stdout, activity), daemon=True),
        threading.Thread(target=_forward, args=(process.stderr, err or sys.stderr, activity), daemon=True),
    ]
    for reader in readers:
        reader.start()
    limit = idle_minutes * 60 if idle_minutes > 0 else float("inf")
    sizes = _watch_sizes(watch)
    while process.poll() is None:
        time.sleep(min(1.0, max(limit / 10, 0.05)))
        current = _watch_sizes(watch)
        if current != sizes:
            sizes = current
            activity[0] = time.monotonic()
        if time.monotonic() - activity[0] > limit:
            _stop_tree(process)
            return IDLE_STOPPED, True
    for reader in readers:
        reader.join(timeout=5)
    return process.returncode, False


def _idle_message(idle_minutes):
    return (
        f"HEAVY_LOCK stopped the command after {idle_minutes:g} min without output; "
        "process tree killed, lock released. Record the run as NOT_RUN and find what hung."
    )


def run(path, owner, wait, poll, stale_hours, command, idle_minutes=30.0, watch=()):
    if not command:
        print("HEAVY_LOCK run needs a command after --", file=sys.stderr)
        return USAGE
    if idle_minutes < 0:
        print("HEAVY_LOCK --idle-minutes must be 0 (off) or more", file=sys.stderr)
        return USAGE
    code, token = _acquire(path, owner, " ".join(command), wait, poll, stale_hours, share_with_owner=False)
    if code != 0:
        return code
    try:
        if idle_minutes == 0:
            return subprocess.call(command)
        code, stopped = _run_watched(command, idle_minutes, list(watch))
        if stopped:
            print(_idle_message(idle_minutes), flush=True)
        return code
    finally:
        _release_token(path, owner, token)


STEP_KEYS = {"name", "cmd", "log", "cwd", "env", "expect", "idle_minutes", "watch"}


def _is_strings(value):
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def load_steps(steps_file, default_idle):
    """Read and validate a steps file; return (steps, problems). Paths come back absolute."""
    try:
        with open(steps_file, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError) as error:
        return [], [f"cannot read {steps_file}: {error}"]
    raw = data.get("steps") if isinstance(data, dict) else data
    if not isinstance(raw, list) or not raw:
        return [], ['the file must hold a non-empty list of steps, or {"steps": [...]}']
    base = os.path.dirname(os.path.abspath(steps_file))

    def resolve(value):
        return value if os.path.isabs(value) else os.path.normpath(os.path.join(base, value))

    steps, problems = [], []
    for number, item in enumerate(raw, 1):
        where = f"step {number}"
        if not isinstance(item, dict):
            problems.append(f"{where}: not an object")
            continue
        found = []
        unknown = sorted(set(item) - STEP_KEYS)
        if unknown:
            found.append(f"unknown keys {unknown}")
        if not isinstance(item.get("name"), str) or not item.get("name"):
            found.append("needs a name")
        if not _is_strings(item.get("cmd")) or not item.get("cmd"):
            found.append("cmd must be a non-empty list of strings")
        if not isinstance(item.get("log"), str) or not item.get("log"):
            found.append("needs a log path")
        if "cwd" in item and not isinstance(item["cwd"], str):
            found.append("cwd must be a string")
        env = item.get("env", {})
        if not isinstance(env, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in env.items()):
            found.append("env must map names to strings")
        if not _is_strings(item.get("expect", [])):
            found.append("expect must be a list of strings")
        if not _is_strings(item.get("watch", [])):
            found.append("watch must be a list of strings")
        idle = item.get("idle_minutes", default_idle)
        if isinstance(idle, bool) or not isinstance(idle, (int, float)) or idle < 0:
            found.append("idle_minutes must be 0 (off) or more")
        if found:
            problems.extend(f"{where}: {problem}" for problem in found)
            continue
        steps.append({
            "name": item["name"],
            "cmd": item["cmd"],
            "log": resolve(item["log"]),
            "cwd": resolve(item["cwd"]) if "cwd" in item else None,
            "env": env,
            "expect": item.get("expect", []),
            "idle_minutes": float(idle),
            "watch": [resolve(path) for path in item.get("watch", [])],
        })
    return steps, problems


def _run_step(step):
    """Run one step into its log; return (passed, summary text)."""
    os.makedirs(os.path.dirname(step["log"]), exist_ok=True)
    started = time.monotonic()
    try:
        with open(step["log"], "wb") as log:
            code, stopped = _run_watched(step["cmd"], step["idle_minutes"], step["watch"], log, log, step["cwd"], step["env"])
            if stopped:
                log.write(("\n" + _idle_message(step["idle_minutes"]) + "\n").encode("utf-8"))
    except OSError as error:
        return False, f"NOT_RUN ({error})"
    seconds = time.monotonic() - started
    with open(step["log"], encoding="utf-8", errors="replace") as handle:
        text = handle.read()
    missing = [line for line in step["expect"] if line not in text]
    expect = "expect=ok" if not missing else f"expect=missing {missing[0]!r}"
    state = "idle-stopped " if stopped else ""
    return code == 0 and not missing, f"rc={code} {state}{expect} {seconds:.0f}s log={step['log']}"


def run_steps(path, owner, wait, poll, stale_hours, steps_file, stop_on_fail=False, dry_run=False):
    steps, problems = load_steps(steps_file, 30.0)
    if problems:
        for problem in problems:
            print(f"HEAVY_LOCK steps file: {problem}", file=sys.stderr)
        return USAGE
    total = len(steps)
    if dry_run:
        for number, step in enumerate(steps, 1):
            print(f"STEP {number}/{total} {step['name']} cmd={' '.join(step['cmd'])!r} log={step['log']}")
        print(f"HEAVY_LOCK steps file ok: {total} steps")
        return 0
    code, token = _acquire(path, owner, f"run-steps {steps_file}", wait, poll, stale_hours, share_with_owner=False)
    if code != 0:
        return code
    passed = failed = 0
    try:
        for number, step in enumerate(steps, 1):
            if stop_on_fail and failed:
                print(f"STEP {number}/{total} {step['name']} NOT_RUN (an earlier step failed)", flush=True)
                continue
            ok, summary = _run_step(step)
            passed, failed = passed + ok, failed + (not ok)
            print(f"STEP {number}/{total} {step['name']} {'PASS' if ok else 'FAIL'} {summary}", flush=True)
        print(f"HEAVY_LOCK steps: {passed} passed, {failed} failed, {total - passed - failed} not run")
        return 0 if passed == total else 1
    finally:
        _release_token(path, owner, token)


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
    queue = sub.add_parser("run-steps")
    queue.add_argument("--owner", required=True)
    queue.add_argument("--steps", required=True, help="JSON steps file (see the module help)")
    queue.add_argument("--wait", type=float, default=0.0)
    queue.add_argument("--stop-on-fail", action="store_true", help="skip the remaining steps after a failed one")
    queue.add_argument("--dry-run", action="store_true", help="check the file and list the steps; take no lock")
    args = parser.parse_args(argv)
    if args.action == "run-steps" and args.dry_run:
        return run_steps(args.lock, args.owner, 0, args.poll, args.stale_hours, args.steps, dry_run=True)
    if not args.lock:
        print("HEAVY_LOCK needs --lock PATH or TRIO_HEAVY_LOCK", file=sys.stderr)
        return USAGE
    if args.action == "status":
        return status(args.lock, args.stale_hours)
    if args.action == "acquire":
        return acquire(args.lock, args.owner, args.cmd, args.wait, args.poll, args.stale_hours)
    if args.action == "release":
        return release(args.lock, args.owner)
    if args.action == "run-steps":
        return run_steps(args.lock, args.owner, args.wait, args.poll, args.stale_hours, args.steps, args.stop_on_fail)
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    return run(args.lock, args.owner, args.wait, args.poll, args.stale_hours, command, args.idle_minutes, args.watch)


if __name__ == "__main__":
    sys.exit(main())
