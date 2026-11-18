"""Repository self-checks: the things reviewed by hand before every release.

The repository is one plain skill, its version matches the changelog, links
resolve, the skill stays small, nothing in the skill is orphaned, and both
template languages carry the same files and placeholders.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "trio-workflow"
LINK = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")
PLACEHOLDER = re.compile(r"\{\{([a-z_]+)\}\}")
DESCRIPTION_LIMIT = 450
SKILL_LINE_LIMIT = 110


def markdown_files():
    return [p for p in ROOT.rglob("*.md") if ".git" not in p.parts]


class RepoTests(unittest.TestCase):
    def test_skill_version_matches_the_changelog(self):
        front = re.match(r"---\n(.*?)\n---\n", (SKILL / "SKILL.md").read_text(encoding="utf-8"), re.S).group(1)
        version = re.search(r'^  version: "(\d+\.\d+\.\d+)"$', front, re.M)
        self.assertIsNotNone(version, "SKILL.md needs metadata.version")
        top = re.search(r"^## (\d+\.\d+\.\d+)", (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"), re.M)
        self.assertIsNotNone(top, "CHANGELOG.md has no version heading")
        self.assertEqual(top.group(1), version.group(1), "CHANGELOG's newest version differs from SKILL.md")

    def test_repository_holds_exactly_one_skill_and_no_plugin_wrapper(self):
        # Skill installers such as `npx skills` discover every SKILL.md, so a stray one would install twice.
        skill_files = [p.relative_to(ROOT).as_posix() for p in ROOT.rglob("SKILL.md") if ".git" not in p.parts]
        self.assertEqual(skill_files, ["skills/trio-workflow/SKILL.md"])
        wrappers = [p.relative_to(ROOT).as_posix() for pattern in ("plugin.json", "marketplace.json")
                    for p in ROOT.rglob(pattern) if ".git" not in p.parts]
        self.assertEqual(wrappers, [], "trio ships as a plain skill with one install path")

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

    def test_license_ships_with_the_skill(self):
        # Installers copy only the skill folder, so the MIT notice must live inside it.
        self.assertEqual((ROOT / "LICENSE").read_text(encoding="utf-8"), (SKILL / "LICENSE").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
