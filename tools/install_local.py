#!/usr/bin/env python3
"""Copy the trio-workflow skill into each tool's user skill folder, or check or remove those copies.

This is "copy mode": the skill folder is copied to ~/.claude/skills, ~/.codex/skills
or ~/.cursor/skills. Use it when you do not install the plugin through a marketplace.
Never install both ways in one tool, or the tool sees the skill twice.

Usage:
  install_local.py install [--target claude codex cursor]
  install_local.py check   [--target ...]
  install_local.py remove  [--target ...]
"""

import argparse
import filecmp
import shutil
import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "plugins" / "trio-workflow" / "skills" / "trio-workflow"
TARGETS = {
    "claude": Path.home() / ".claude" / "skills" / "trio-workflow",
    "codex": Path.home() / ".codex" / "skills" / "trio-workflow",
    "cursor": Path.home() / ".cursor" / "skills" / "trio-workflow",
}
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc")


def _differences(left, right):
    """Return relative paths that differ between two trees, ignoring caches."""
    comparison = filecmp.dircmp(left, right, ignore=["__pycache__"])
    found = [f"only in source: {name}" for name in comparison.left_only]
    found += [f"only in copy: {name}" for name in comparison.right_only]
    _, mismatch, errors = filecmp.cmpfiles(left, right, comparison.common_files, shallow=False)
    found += [f"differs: {name}" for name in mismatch + errors]
    for name in comparison.common_dirs:
        found += [f"{name}/{item}" for item in _differences(Path(left) / name, Path(right) / name)]
    return found


def _is_link(path):
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def install(target, path):
    if _is_link(path):
        print(f"SKIP {target}: {path} is a link; remove it by hand first")
        return 1
    if path.exists():
        shutil.rmtree(path)
    shutil.copytree(SOURCE, path, ignore=IGNORE)
    print(f"INSTALLED {target}: {path}")
    return 0


def check(target, path):
    if not path.exists():
        print(f"MISSING {target}: {path}")
        return 1
    differences = _differences(SOURCE, path)
    if differences:
        print(f"OUTDATED {target}: {path}")
        for item in differences:
            print(f"  {item}")
        return 1
    print(f"CURRENT {target}: {path}")
    return 0


def remove(target, path):
    if _is_link(path):
        print(f"SKIP {target}: {path} is a link; remove it by hand")
        return 1
    if path.exists():
        shutil.rmtree(path)
        print(f"REMOVED {target}: {path}")
    else:
        print(f"ABSENT {target}: {path}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("action", choices=["install", "check", "remove"])
    parser.add_argument("--target", nargs="+", choices=sorted(TARGETS), default=["claude", "codex"])
    args = parser.parse_args(argv)
    action = {"install": install, "check": check, "remove": remove}[args.action]
    failures = sum(action(target, TARGETS[target]) for target in args.target)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
