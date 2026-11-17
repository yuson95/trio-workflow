"""Behavior tests for tools/install_local.py (copy-mode installs).

Each test points the user's home directory at a temporary folder, runs the
installer the way a person would, and checks the files it leaves behind.
"""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "tools" / "install_local.py"


def run(home, *args):
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home))
    return subprocess.run([sys.executable, str(INSTALLER), *args], capture_output=True, text=True, encoding="utf-8", env=env)


class InstallLocalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.target = self.home / ".codex" / "skills" / "trio-workflow"

    def tearDown(self):
        self.tmp.cleanup()

    def test_install_then_check_reports_current(self):
        installed = run(self.home, "install", "--target", "codex")
        self.assertEqual(installed.returncode, 0, installed.stdout + installed.stderr)
        self.assertTrue((self.target / "SKILL.md").is_file())
        self.assertTrue((self.target / "scripts" / "check_plan.py").is_file())
        self.assertFalse(any(self.target.rglob("__pycache__")))
        checked = run(self.home, "check", "--target", "codex")
        self.assertEqual(checked.returncode, 0)
        self.assertIn("CURRENT codex", checked.stdout)

    def test_check_finds_edited_and_missing_copies(self):
        self.assertIn("MISSING codex", run(self.home, "check", "--target", "codex").stdout)
        run(self.home, "install", "--target", "codex")
        (self.target / "SKILL.md").write_text("edited by hand\n", encoding="utf-8")
        checked = run(self.home, "check", "--target", "codex")
        self.assertEqual(checked.returncode, 1)
        self.assertIn("OUTDATED codex", checked.stdout)
        self.assertIn("differs: SKILL.md", checked.stdout)

    def test_reinstall_replaces_stale_files_and_remove_cleans_up(self):
        run(self.home, "install", "--target", "codex")
        (self.target / "stale.md").write_text("left over\n", encoding="utf-8")
        run(self.home, "install", "--target", "codex")
        self.assertFalse((self.target / "stale.md").exists())
        removed = run(self.home, "remove", "--target", "codex")
        self.assertEqual(removed.returncode, 0)
        self.assertIn("REMOVED codex", removed.stdout)
        self.assertFalse(self.target.exists())
        self.assertIn("ABSENT codex", run(self.home, "remove", "--target", "codex").stdout)


if __name__ == "__main__":
    unittest.main()
