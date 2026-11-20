"""Behavior tests for the trio-workflow skill scripts.

Each test runs a script the way an agent would (a separate Python process) and
checks its exit code, its output and the files it leaves behind.
"""

import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "trio-workflow" / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def run(script, *args, env=None):
    merged = dict(os.environ, **(env or {}))
    merged.pop("TRIO_HEAVY_LOCK", None) if env is None else None
    return subprocess.run([sys.executable, str(SCRIPTS / script), *args], capture_output=True, text=True, encoding="utf-8", env=merged)


class CheckPlanTests(unittest.TestCase):
    def test_complete_english_plan_passes(self):
        result = run("check_plan.py", str(FIXTURES / "good_plan_en.md"))
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("CHECK_PLAN ok", result.stdout)

    def test_complete_chinese_plan_passes(self):
        result = run("check_plan.py", str(FIXTURES / "good_plan_zh.md"))
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_broken_plan_reports_each_problem(self):
        result = run("check_plan.py", str(FIXTURES / "bad_plan.md"))
        self.assertEqual(result.returncode, 1)
        out = result.stdout
        self.assertIn("lacks 'You see'", out)
        self.assertIn("lacks 'Verify, live'", out)
        self.assertIn("'R1 Show the yearly total' lacks 'Invariants'", out)
        self.assertNotIn("'R2 Add a stale-result banner' lacks 'Invariants'", out)
        self.assertIn("decision 'D-1' has no default", out)
        self.assertIn("decision 'D-2' has no default", out)
        self.assertIn("`shared/table.js` is owned by several batches", out)
        self.assertIn("depends on unknown batch 'B7'", out)
        self.assertIn("review-gated requirement 'R2 Add a stale-result banner' lacks 'Prototype'", out)
        self.assertNotIn("'R1 Show the yearly total' lacks 'Prototype'", out)
        self.assertRegex(out, r"CHECK_PLAN \d+ problems")

    def test_missing_sections_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = Path(tmp) / "empty.md"
            plan.write_text("# Plan\n\nNothing here.\n", encoding="utf-8")
            result = run("check_plan.py", str(plan))
        self.assertEqual(result.returncode, 1)
        self.assertIn("no 'requirements' section found", result.stdout)
        self.assertIn("no 'batches' section found", result.stdout)



class ScreenshotSheetTests(unittest.TestCase):
    def test_sheet_marks_each_cell_and_links_images(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "main").mkdir()
            (root / "candidate").mkdir()
            (root / "main" / "results__full.png").write_bytes(b"same")
            (root / "candidate" / "results__full.png").write_bytes(b"same")
            (root / "main" / "results__empty.png").write_bytes(b"old")
            (root / "candidate" / "results__empty.png").write_bytes(b"new")
            (root / "candidate" / "decision__full.png").write_bytes(b"x")
            result = run("screenshot_sheet.py", str(root), "--states", "empty", "full", "narrow")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("pages=2 states=3", result.stdout)
            self.assertIn("missing=3 unchanged=1 changed=1 new=1 removed=0", result.stdout)
            sheet = (root / "index.html").read_text(encoding="utf-8")
        self.assertIn('src="candidate/results__empty.png"', sheet)
        self.assertIn('src="main/results__empty.png"', sheet)
        for tag in ("unchanged", "changed", "new", "missing"):
            self.assertIn(f'<span class="tag">{tag}</span>', sheet)

    def test_missing_folders_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run("screenshot_sheet.py", tmp)
        self.assertEqual(result.returncode, 2)

class LogDecisionTests(unittest.TestCase):
    def test_first_row_writes_header_and_cleans_cells(self):
        with tempfile.TemporaryDirectory() as tmp:
            trail = Path(tmp) / "notes" / "PLAN9_DECISIONS.tsv"
            result = run("log_decision.py", str(trail), "decision", "kept\tthe old\nlayout", "=SUM(A1)", "commit abc123", "-1 issue")
            self.assertEqual(result.returncode, 0, result.stderr)
            rows = trail.read_text(encoding="utf-8").splitlines()
        self.assertEqual(rows[0], "ts\tphase\tdecision\twhy\tevidence\tresult")
        cells = rows[1].split("\t")
        self.assertEqual(len(cells), 6)
        self.assertEqual(cells[1:], ["decision", "kept the old layout", "'=SUM(A1)", "commit abc123", "'-1 issue"])

    def test_rows_append_without_repeating_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            trail = Path(tmp) / "T.tsv"
            run("log_decision.py", str(trail), "start", "new session", "resume", "agent x", "open")
            run("log_decision.py", str(trail), "unit", "batch S1 done", "quick check green", "sha 1", "pass")
            rows = trail.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(rows), 3)
        self.assertEqual(sum(row.startswith("ts\t") for row in rows), 1)

    def test_unknown_phase_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            trail = Path(tmp) / "T.tsv"
            result = run("log_decision.py", str(trail), "misc", "a", "b", "c", "d")
            self.assertEqual(result.returncode, 2)
            self.assertFalse(trail.exists())


class HeavyLockTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.lock = str(Path(self.tmp.name) / "locks" / "heavy-check.lock")

    def tearDown(self):
        self.tmp.cleanup()

    def test_acquire_status_release_cycle(self):
        self.assertEqual(run("heavy_lock.py", "--lock", self.lock, "status").stdout.strip(), "HEAVY_LOCK free")
        taken = run("heavy_lock.py", "--lock", self.lock, "acquire", "--owner", "review-1", "--cmd", "full check")
        self.assertEqual(taken.returncode, 0, taken.stdout)
        record = json.loads(Path(self.lock).read_text(encoding="utf-8"))
        self.assertEqual((record["owner"], record["cmd"]), ("review-1", "full check"))
        self.assertIn("owner=review-1", run("heavy_lock.py", "--lock", self.lock, "status").stdout)
        released = run("heavy_lock.py", "--lock", self.lock, "release", "--owner", "review-1")
        self.assertEqual(released.returncode, 0)
        self.assertFalse(Path(self.lock).exists())

    def test_second_owner_is_refused_without_wait(self):
        run("heavy_lock.py", "--lock", self.lock, "acquire", "--owner", "builder-a", "--cmd", "solver tests")
        busy = run("heavy_lock.py", "--lock", self.lock, "acquire", "--owner", "builder-b", "--cmd", "full check")
        self.assertEqual(busy.returncode, 3)
        self.assertIn("busy owner=builder-a", busy.stdout)

    def test_only_the_holder_can_release(self):
        run("heavy_lock.py", "--lock", self.lock, "acquire", "--owner", "builder-a", "--cmd", "x")
        refused = run("heavy_lock.py", "--lock", self.lock, "release", "--owner", "builder-b")
        self.assertEqual(refused.returncode, 4)
        self.assertTrue(Path(self.lock).exists())

    def test_stale_lock_is_reported_not_removed(self):
        os.makedirs(os.path.dirname(self.lock))
        Path(self.lock).write_text(json.dumps({"owner": "old", "cmd": "x", "host": "h", "started": "2020-01-01T00:00:00+00:00"}), encoding="utf-8")
        status = run("heavy_lock.py", "--lock", self.lock, "status")
        self.assertIn("STALE", status.stdout)
        self.assertTrue(Path(self.lock).exists())

    def test_run_wraps_the_command_and_releases(self):
        result = run("heavy_lock.py", "--lock", self.lock, "run", "--owner", "builder-a", "--", sys.executable, "-c", "import sys; sys.exit(5)")
        self.assertEqual(result.returncode, 5)
        self.assertIn("HEAVY_LOCK released owner=builder-a", result.stdout)
        self.assertFalse(Path(self.lock).exists())

    def test_waiting_owner_gets_the_lock_after_release(self):
        run("heavy_lock.py", "--lock", self.lock, "acquire", "--owner", "builder-a", "--cmd", "x")
        releaser = threading.Timer(1.0, lambda: run("heavy_lock.py", "--lock", self.lock, "release", "--owner", "builder-a"))
        releaser.start()
        started = time.monotonic()
        waited = run("heavy_lock.py", "--lock", self.lock, "--poll", "0.2", "acquire", "--owner", "builder-b", "--cmd", "y", "--wait", "15")
        releaser.join()
        self.assertEqual(waited.returncode, 0, waited.stdout)
        self.assertIn("HEAVY_LOCK acquired owner=builder-b", waited.stdout)
        self.assertLess(time.monotonic() - started, 15)

    def test_lock_path_is_required(self):
        result = run("heavy_lock.py", "status", env={"TRIO_HEAVY_LOCK": ""})
        self.assertEqual(result.returncode, 2)


def _alive(pid):
    if os.name == "nt":
        listing = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True)
        return str(pid) in listing.stdout
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


class HeavyLockIdleTests(unittest.TestCase):
    """A hung command must not hold the lock: `run` stops it after the idle limit."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.lock = str(self.dir / "heavy-check.lock")

    def tearDown(self):
        self.tmp.cleanup()

    def run_locked(self, *options_and_command):
        return run("heavy_lock.py", "--lock", self.lock, "run", "--owner", "builder-a", *options_and_command)

    def test_quiet_command_is_stopped_and_the_lock_released(self):
        started = time.monotonic()
        result = self.run_locked("--idle-minutes", "0.03", "--", sys.executable, "-c", "import time; time.sleep(60)")
        self.assertEqual(result.returncode, 124, result.stdout + result.stderr)
        self.assertIn("HEAVY_LOCK stopped the command after 0.03 min without output", result.stdout)
        self.assertIn("HEAVY_LOCK released owner=builder-a", result.stdout)
        self.assertFalse(Path(self.lock).exists())
        self.assertLess(time.monotonic() - started, 30)

    def test_steady_output_keeps_the_run_alive_and_is_forwarded(self):
        script = "import sys, time\nfor i in range(8):\n    print('tick', i)\n    print('note', i, file=sys.stderr)\n    time.sleep(0.5)\n"
        result = self.run_locked("--idle-minutes", "0.05", "--", sys.executable, "-c", script)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("tick 7", result.stdout)
        self.assertIn("note 7", result.stderr)
        self.assertNotIn("HEAVY_LOCK stopped", result.stdout)

    def test_a_growing_watched_log_counts_as_output(self):
        log = self.dir / "run.log"
        script = f"import time\nfor i in range(8):\n    open({str(log)!r}, 'a').write('line\\n')\n    time.sleep(0.5)\n"
        result = self.run_locked("--idle-minutes", "0.05", "--watch", str(log), "--", sys.executable, "-c", script)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("HEAVY_LOCK stopped", result.stdout)

    def test_the_whole_process_tree_is_stopped(self):
        pid_file = self.dir / "grandchild.pid"
        script = (
            "import subprocess, sys, time\n"
            "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(120)'])\n"
            f"open({str(pid_file)!r}, 'w').write(str(child.pid))\n"
            "time.sleep(120)\n"
        )
        result = self.run_locked("--idle-minutes", "0.05", "--", sys.executable, "-c", script)
        self.assertEqual(result.returncode, 124, result.stdout + result.stderr)
        grandchild = int(pid_file.read_text())
        deadline = time.monotonic() + 10
        while _alive(grandchild) and time.monotonic() < deadline:
            time.sleep(0.2)
        self.assertFalse(_alive(grandchild), f"grandchild {grandchild} still running")

    def test_negative_idle_limit_is_a_usage_error(self):
        result = self.run_locked("--idle-minutes", "-1", "--", sys.executable, "-c", "pass")
        self.assertEqual(result.returncode, 2)
        self.assertFalse(Path(self.lock).exists())


class HeavyLockOwnRunTests(unittest.TestCase):
    """Runs never share the lock, not even with their own owner, and release only their own acquisition."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.lock = str(Path(self.tmp.name) / "heavy-check.lock")

    def tearDown(self):
        self.tmp.cleanup()

    def test_second_run_of_the_same_owner_waits_and_the_first_keeps_the_lock(self):
        first = subprocess.Popen(
            [sys.executable, str(SCRIPTS / "heavy_lock.py"), "--lock", self.lock, "run", "--owner", "builder-a", "--",
             sys.executable, "-c", "import time; time.sleep(4)"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        try:
            deadline = time.monotonic() + 10
            while not Path(self.lock).exists() and time.monotonic() < deadline:
                time.sleep(0.1)
            second = run("heavy_lock.py", "--lock", self.lock, "run", "--owner", "builder-a", "--", sys.executable, "-c", "pass")
            self.assertEqual(second.returncode, 3, second.stdout)
            self.assertIn("same owner", second.stdout)
            self.assertIn("HEAVY_LOCK held owner=builder-a", run("heavy_lock.py", "--lock", self.lock, "status").stdout)
        finally:
            first.communicate(timeout=30)
        self.assertEqual(first.returncode, 0)
        self.assertFalse(Path(self.lock).exists())

    def test_run_leaves_a_manual_hold_of_its_owner_in_place(self):
        run("heavy_lock.py", "--lock", self.lock, "acquire", "--owner", "builder-a", "--cmd", "manual")
        result = run("heavy_lock.py", "--lock", self.lock, "run", "--owner", "builder-a", "--", sys.executable, "-c", "pass")
        self.assertEqual(result.returncode, 3, result.stdout)
        self.assertEqual(json.loads(Path(self.lock).read_text(encoding="utf-8"))["cmd"], "manual")

    def test_run_never_releases_a_later_acquisition_of_the_same_owner(self):
        script = (
            "import json, os\n"
            f"os.remove({self.lock!r})\n"
            f"open({self.lock!r}, 'w').write(json.dumps({{'owner': 'builder-a', 'cmd': 'later', 'token': 'other'}}))\n"
        )
        result = run("heavy_lock.py", "--lock", self.lock, "run", "--owner", "builder-a", "--", sys.executable, "-c", script)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("not released", result.stdout)
        self.assertEqual(json.loads(Path(self.lock).read_text(encoding="utf-8"))["cmd"], "later")


class HeavyLockStepsTests(unittest.TestCase):
    """`run-steps`: the lead runs a worker's heavy steps in order under one hold, each into its own log."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.lock = str(self.dir / "heavy-check.lock")
        self.steps = self.dir / "w07" / "heavy-steps.json"
        self.steps.parent.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def write_steps(self, steps):
        self.steps.write_text(json.dumps({"steps": steps}), encoding="utf-8")

    def run_steps(self, *options):
        return run("heavy_lock.py", "--lock", self.lock, "run-steps", "--owner", "lead", "--steps", str(self.steps), *options)

    def test_steps_run_in_order_under_one_hold_each_into_its_log(self):
        status = [sys.executable, str(SCRIPTS / "heavy_lock.py"), "--lock", self.lock, "status"]
        self.write_steps([
            {"name": "hold", "cmd": status, "log": "logs/hold.log", "expect": ["HEAVY_LOCK held owner=lead"]},
            {"name": "env", "cmd": [sys.executable, "-c", "import os; print('value', os.environ['TRIO_STEP'])"],
             "log": "logs/env.log", "env": {"TRIO_STEP": "42"}, "expect": ["value 42"]},
            {"name": "exit", "cmd": [sys.executable, "-c", "import sys; sys.exit(3)"], "log": "logs/exit.log"},
        ])
        result = self.run_steps()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("STEP 1/3 hold PASS rc=0 expect=ok", result.stdout)
        self.assertIn("STEP 2/3 env PASS", result.stdout)
        self.assertIn("STEP 3/3 exit FAIL rc=3", result.stdout)
        self.assertIn("HEAVY_LOCK steps: 2 passed, 1 failed, 0 not run", result.stdout)
        self.assertIn("value 42", (self.steps.parent / "logs" / "env.log").read_text(encoding="utf-8"))
        self.assertNotIn("value 42", result.stdout)
        self.assertFalse(Path(self.lock).exists())

    def test_missing_expected_line_fails_the_step_and_stop_on_fail_skips_the_rest(self):
        self.write_steps([
            {"name": "quiet", "cmd": [sys.executable, "-c", "print('Ran 3 tests')"], "log": "a.log", "expect": ["OK"]},
            {"name": "later", "cmd": [sys.executable, "-c", "pass"], "log": "b.log"},
        ])
        result = self.run_steps("--stop-on-fail")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("STEP 1/2 quiet FAIL rc=0 expect=missing 'OK'", result.stdout)
        self.assertIn("STEP 2/2 later NOT_RUN", result.stdout)
        self.assertFalse((self.steps.parent / "b.log").exists())

    def test_a_hung_step_is_stopped_and_the_next_step_still_runs(self):
        self.write_steps([
            {"name": "hung", "cmd": [sys.executable, "-c", "import time; time.sleep(60)"], "log": "hung.log", "idle_minutes": 0.03},
            {"name": "next", "cmd": [sys.executable, "-c", "print('done')"], "log": "next.log", "expect": ["done"]},
        ])
        started = time.monotonic()
        result = self.run_steps()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("STEP 1/2 hung FAIL rc=124 idle-stopped", result.stdout)
        self.assertIn("STEP 2/2 next PASS", result.stdout)
        self.assertIn("without output", (self.steps.parent / "hung.log").read_text(encoding="utf-8"))
        self.assertLess(time.monotonic() - started, 30)
        self.assertFalse(Path(self.lock).exists())

    def test_busy_lock_runs_no_step(self):
        run("heavy_lock.py", "--lock", self.lock, "acquire", "--owner", "review-1", "--cmd", "full check")
        self.write_steps([{"name": "one", "cmd": [sys.executable, "-c", "pass"], "log": "one.log"}])
        result = self.run_steps()
        self.assertEqual(result.returncode, 3, result.stdout)
        self.assertFalse((self.steps.parent / "one.log").exists())

    def test_dry_run_checks_the_file_without_a_lock(self):
        self.write_steps([
            {"name": "one", "cmd": [sys.executable, "-c", "pass"], "log": "one.log"},
            {"name": "two", "cmd": [sys.executable, "-c", "pass"], "log": "two.log", "cwd": "."},
        ])
        result = run("heavy_lock.py", "run-steps", "--owner", "w07", "--steps", str(self.steps), "--dry-run", env={"TRIO_HEAVY_LOCK": ""})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("HEAVY_LOCK steps file ok: 2 steps", result.stdout)
        self.assertIn(str(self.steps.parent / "one.log"), result.stdout)
        self.assertFalse((self.steps.parent / "one.log").exists())

    def test_malformed_steps_are_refused_with_each_problem(self):
        self.write_steps([{"name": "one", "command": ["x"], "log": "one.log"}, {"cmd": [], "log": ""}])
        result = self.run_steps("--dry-run")
        self.assertEqual(result.returncode, 2)
        self.assertIn("step 1: unknown keys ['command']", result.stderr)
        self.assertIn("step 1: cmd must be a non-empty list of strings", result.stderr)
        self.assertIn("step 2: needs a name", result.stderr)
        self.assertIn("step 2: needs a log path", result.stderr)


def _codex_row(stamp, used_percent, resets_at, secondary=None):
    limits = {"primary": {"used_percent": used_percent, "window_minutes": 10080, "resets_at": resets_at}, "secondary": secondary}
    return json.dumps({"timestamp": stamp, "type": "event_msg", "payload": {"type": "token_count", "rate_limits": limits}})


class UsageGuardTests(unittest.TestCase):
    """The guard reads Codex's newest rate-limit reading and turns it into FULL / ONE_WORKER / PAUSE."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.day = self.home / "sessions" / "2026" / "11" / "18"
        self.day.mkdir(parents=True)
        self.future = int(time.time()) + 86400

    def tearDown(self):
        self.tmp.cleanup()

    def write_session(self, name, rows, mtime):
        path = self.day / name
        path.write_text("\n".join(rows) + "\n", encoding="utf-8")
        os.utime(path, (mtime, mtime))

    def guard(self, *args):
        return run("usage_guard.py", "--codex-home", str(self.home), *args)

    def test_newest_reading_across_sessions_decides(self):
        now = time.time()
        self.write_session("old.jsonl", [_codex_row("2026-11-18T10:00:00Z", 20.0, self.future)], now - 60)
        self.write_session("new.jsonl", [_codex_row("2026-11-18T09:00:00Z", 10.0, self.future),
                                         _codex_row("2026-11-18T11:00:00Z", 75.0, self.future),
                                         json.dumps({"timestamp": "2026-11-18T11:01:00Z", "type": "response_item"})], now)
        result = self.guard()
        self.assertEqual(result.returncode, 3, result.stdout)
        self.assertIn("USAGE ONE_WORKER: 25% left", result.stdout)

    def test_low_usage_pauses_and_plenty_runs_full(self):
        self.write_session("s.jsonl", [_codex_row("2026-11-18T11:00:00Z", 95.0, self.future)], time.time())
        self.assertEqual(self.guard().returncode, 4)
        self.write_session("s.jsonl", [_codex_row("2026-11-18T12:00:00Z", 40.0, self.future)], time.time())
        full = self.guard()
        self.assertEqual(full.returncode, 0, full.stdout)
        self.assertIn("USAGE FULL: 60% left", full.stdout)

    def test_the_tighter_of_two_windows_counts(self):
        secondary = {"used_percent": 92.0, "window_minutes": 300, "resets_at": self.future}
        self.write_session("s.jsonl", [_codex_row("2026-11-18T11:00:00Z", 10.0, self.future, secondary)], time.time())
        result = self.guard()
        self.assertEqual(result.returncode, 4, result.stdout)
        self.assertIn("8% left in the Codex 300-minute window", result.stdout)

    def test_a_window_that_has_reset_counts_as_full(self):
        self.write_session("s.jsonl", [_codex_row("2026-11-18T11:00:00Z", 99.0, int(time.time()) - 60)], time.time())
        result = self.guard()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("has reset since this reading", result.stdout)

    def test_operator_number_and_missing_reading(self):
        given = self.guard("--left", "8")
        self.assertEqual(given.returncode, 4)
        self.assertIn("given by the operator", given.stdout)
        missing = run("usage_guard.py", "--codex-home", str(self.home / "nowhere"))
        self.assertEqual(missing.returncode, 5)
        self.assertIn("rerun with --left", missing.stdout)

    def test_thresholds_are_validated(self):
        self.assertEqual(self.guard("--left", "50", "--reduce-below", "10", "--pause-below", "20").returncode, 2)
        self.assertEqual(self.guard("--left", "150").returncode, 2)


def _iso(seconds_ago):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - seconds_ago))


def _thread_rows(meta, contexts, last_seconds_ago):
    rows = [json.dumps({"timestamp": _iso(last_seconds_ago + 600), "type": "session_meta", "payload": meta})]
    for i, context in enumerate(contexts):
        ago = last_seconds_ago + 10 * (len(contexts) - 1 - i)
        rows.append(json.dumps({"timestamp": _iso(ago), "type": "token_usage_record",
                                "payload": {"response_id": f"r{i}", "usage": {"input_tokens": context}}}))
    return rows


class UsageGuardThreadTests(unittest.TestCase):
    """--threads lists live Codex threads with their current context, so the lead can retire workers."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.day = self.home / "sessions" / time.strftime("%Y/%m/%d", time.gmtime())
        self.day.mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, rows, mtime=None):
        path = self.day / name
        path.write_text("\n".join(rows) + "\n", encoding="utf-8")
        if mtime is not None:
            os.utime(path, (mtime, mtime))

    def test_live_threads_show_context_calls_and_over_cap(self):
        self.write("lead.jsonl", _thread_rows({"id": "01a1eb6d-0000"}, [30_000, 90_000, 210_000], 60))
        self.write("worker.jsonl", _thread_rows({"id": "x", "agent_path": "/root/w1"}, [30_000, 60_000], 30))
        self.write("near.jsonl", _thread_rows({"id": "y", "agent_path": "/root/w2"}, [130_000], 30))
        result = run("usage_guard.py", "--codex-home", str(self.home), "--left", "80", "--threads")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("THREAD OVER lead 01a1eb6d: context 210k tokens, 3 calls", result.stdout)
        self.assertIn("THREAD NEAR /root/w2: context 130k tokens, 1 calls", result.stdout)
        self.assertIn("THREAD ok   /root/w1: context 60k tokens, 2 calls", result.stdout)
        relaxed = run("usage_guard.py", "--codex-home", str(self.home), "--left", "80", "--threads", "--soft", "0.9")
        self.assertIn("THREAD ok   /root/w2", relaxed.stdout)
        self.assertEqual(run("usage_guard.py", "--left", "80", "--soft", "0").returncode, 2)

    def test_activity_comes_from_the_log_not_the_file_time(self):
        # Windows may leave an open log's modified time at its creation; the last row decides.
        self.write("open.jsonl", _thread_rows({"agent_path": "/root/busy"}, [200_000], 30), mtime=time.time() - 3 * 86400)
        self.write("idle.jsonl", _thread_rows({"agent_path": "/root/idle"}, [40_000], 5 * 3600))
        result = run("usage_guard.py", "--codex-home", str(self.home), "--left", "80", "--threads", "--cap", "250000")
        self.assertIn("THREAD ok   /root/busy: context 200k tokens", result.stdout)
        self.assertNotIn("/root/idle", result.stdout)

    def test_no_live_threads(self):
        result = run("usage_guard.py", "--codex-home", str(self.home), "--left", "80", "--threads")
        self.assertIn("THREADS none active", result.stdout)


if __name__ == "__main__":
    unittest.main()
