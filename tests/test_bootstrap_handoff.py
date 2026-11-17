"""Behavior tests for scripts/bootstrap_handoff.py."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins" / "trio-workflow" / "skills" / "trio-workflow" / "scripts" / "bootstrap_handoff.py"
FILES = ("00_START_HERE.md", "00_FLOW.md", "0_RULES.md", "PROMPTS.md")


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, encoding="utf-8")


class BootstrapHandoffTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name) / "handoff"

    def tearDown(self):
        self.tmp.cleanup()

    def bootstrap(self, *extra):
        return run("--dir", str(self.dir), "--project", "Solar Atlas", "--reviewer", "Claude Code", "--builder", "Codex", *extra)

    def test_english_files_are_written_and_filled(self):
        result = self.bootstrap("--delivery", "pr", "--service", "port 8766")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("wrote=4 kept=0", result.stdout)
        self.assertTrue((self.dir / "batch-notes").is_dir())
        for name in FILES:
            text = (self.dir / name).read_text(encoding="utf-8")
            self.assertNotIn("{{", text, name)
            self.assertIn("Solar Atlas", text, name)
        rules = (self.dir / "0_RULES.md").read_text(encoding="utf-8")
        self.assertIn("Reviewer = Claude Code; Builder = Codex", rules)
        self.assertIn("Delivery: pr", rules)
        self.assertIn("port 8766", rules)
        self.assertIn("heavy-check.lock", rules)

    def test_chinese_templates_are_used_with_lang_zh(self):
        result = self.bootstrap("--lang", "zh")
        self.assertEqual(result.returncode, 0, result.stderr)
        start = (self.dir / "00_START_HERE.md").read_text(encoding="utf-8")
        self.assertIn("从这里开始 · Solar Atlas", start)
        self.assertIn("审查者 | Claude Code", start)

    def test_existing_files_are_kept_not_overwritten(self):
        self.dir.mkdir(parents=True)
        (self.dir / "00_FLOW.md").write_text("my own flow\n", encoding="utf-8")
        result = self.bootstrap()
        self.assertIn("wrote=3 kept=1", result.stdout)
        self.assertEqual((self.dir / "00_FLOW.md").read_text(encoding="utf-8"), "my own flow\n")
        again = self.bootstrap()
        self.assertIn("wrote=0 kept=4", again.stdout)

    def test_required_arguments_are_enforced(self):
        result = run("--dir", str(self.dir), "--project", "X")
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.dir.exists())


if __name__ == "__main__":
    unittest.main()
