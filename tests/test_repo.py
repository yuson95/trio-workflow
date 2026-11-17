"""Repository self-checks: the things reviewed by hand before every release.

Versions agree, marketplaces point at real plugins, links resolve, the skill
stays small, nothing in the skill is orphaned, and both template languages
carry the same files and placeholders.
"""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "trio-workflow"
SKILL = PLUGIN / "skills" / "trio-workflow"
MANIFESTS = [PLUGIN / ".claude-plugin" / "plugin.json", PLUGIN / ".codex-plugin" / "plugin.json",
             PLUGIN / ".cursor-plugin" / "plugin.json", PLUGIN / "plugin.json"]
LINK = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")
PLACEHOLDER = re.compile(r"\{\{([a-z_]+)\}\}")
DESCRIPTION_LIMIT = 450
SKILL_LINE_LIMIT = 110


def markdown_files():
    return [p for p in ROOT.rglob("*.md") if ".git" not in p.parts]


class RepoTests(unittest.TestCase):
    def test_all_manifests_share_the_changelog_version(self):
        versions = {str(m.relative_to(ROOT)): json.loads(m.read_text(encoding="utf-8"))["version"] for m in MANIFESTS}
        self.assertEqual(len(set(versions.values())), 1, versions)
        top = re.search(r"^## (\d+\.\d+\.\d+)", (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"), re.M)
        self.assertIsNotNone(top, "CHANGELOG.md has no version heading")
        self.assertEqual(top.group(1), next(iter(versions.values())), "CHANGELOG's newest version differs from the manifests")

    def test_marketplaces_point_at_real_plugins(self):
        claude = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        codex = json.loads((ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(claude["name"], "trio")
        self.assertEqual(codex["name"], "trio")
        claude_source = ROOT / claude["plugins"][0]["source"]
        codex_source = ROOT / codex["plugins"][0]["source"]["path"]
        self.assertTrue((claude_source / ".claude-plugin" / "plugin.json").is_file())
        self.assertTrue((codex_source / ".codex-plugin" / "plugin.json").is_file())

    def test_relative_markdown_links_resolve(self):
        broken = []
        for md in markdown_files():
            for target in LINK.findall(md.read_text(encoding="utf-8")):
                if "://" in target or target.startswith("mailto:"):
                    continue
                if not (md.parent / target).exists():
                    broken.append(f"{md.relative_to(ROOT)} -> {target}")
        self.assertEqual(broken, [])

    def test_skill_stays_small(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        front = re.match(r"---\n(.*?)\n---\n", text, re.S)
        self.assertIsNotNone(front, "SKILL.md needs YAML front matter")
        self.assertIn("name: trio-workflow", front.group(1))
        description = re.search(r"^description: (.*)$", front.group(1), re.M).group(1)
        self.assertLessEqual(len(description), DESCRIPTION_LIMIT, "the always-loaded description grew; trim it")
        self.assertLessEqual(len(text.splitlines()), SKILL_LINE_LIMIT, "SKILL.md grew; move detail into a branch file")

    def test_every_branch_file_and_script_is_reachable_from_skill_md(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        orphans = [p.name for p in SKILL.glob("*.md") if p.name != "SKILL.md" and f"]({p.name})" not in text]
        unlisted = [p.name for p in (SKILL / "scripts").glob("*.py") if p.name not in text]
        self.assertEqual(orphans, [], "branch files not linked from SKILL.md")
        self.assertEqual(unlisted, [], "scripts not listed in SKILL.md")

    def test_template_languages_match(self):
        en, zh = SKILL / "templates" / "en", SKILL / "templates" / "zh"
        self.assertEqual(sorted(p.name for p in en.glob("*.md")), sorted(p.name for p in zh.glob("*.md")))
        for name in (p.name for p in en.glob("*.md")):
            en_keys = set(PLACEHOLDER.findall((en / name).read_text(encoding="utf-8")))
            zh_keys = set(PLACEHOLDER.findall((zh / name).read_text(encoding="utf-8")))
            self.assertEqual(en_keys, zh_keys, f"placeholders differ in {name}")

    def test_license_ships_with_the_plugin(self):
        self.assertEqual((ROOT / "LICENSE").read_text(encoding="utf-8"), (PLUGIN / "LICENSE").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
