#!/usr/bin/env python3
"""Create a project's handoff directory from the trio templates.

Writes 00_START_HERE.md, 00_FLOW.md, 0_RULES.md and PROMPTS.md (plus an empty
batch-notes/ folder) with the project's names filled in. Existing files are
never overwritten; they are reported as KEPT, so the script is safe to rerun.

Usage:
  bootstrap_handoff.py --dir PATH --project NAME --reviewer AGENT --builder AGENT
                       [--lang en|zh] [--same-family yes|no] [--delivery local|pr]
                       [--lock PATH] [--service TEXT] [--skill-dir PATH]
Prints one line per file and a summary line: BOOTSTRAP <dir> wrote=N kept=M
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
TEMPLATES = SKILL_DIR / "templates"
FILES = ("00_START_HERE.md", "00_FLOW.md", "0_RULES.md", "PROMPTS.md")
PLACEHOLDER = re.compile(r"\{\{([a-z_]+)\}\}")


def fill(text, values, name):
    def replace(match):
        key = match.group(1)
        if key not in values:
            raise KeyError(f"template {name} uses unknown placeholder {{{{{key}}}}}")
        return values[key]
    return PLACEHOLDER.sub(replace, text)


def bootstrap(args):
    target = Path(args.dir)
    target.mkdir(parents=True, exist_ok=True)
    (target / "batch-notes").mkdir(exist_ok=True)
    values = {
        "project": args.project,
        "reviewer": args.reviewer,
        "builder": args.builder,
        "same_family": args.same_family,
        "delivery": args.delivery,
        "lock": args.lock or str(target / ".locks" / "heavy-check.lock"),
        "service": args.service,
        "skill_dir": args.skill_dir or str(SKILL_DIR),
        "date": date.today().isoformat(),
    }
    wrote = kept = 0
    for name in FILES:
        destination = target / name
        if destination.exists():
            print(f"KEPT  {destination}")
            kept += 1
            continue
        text = (TEMPLATES / args.lang / name).read_text(encoding="utf-8")
        destination.write_text(fill(text, values, f"{args.lang}/{name}"), encoding="utf-8", newline="\n")
        print(f"WROTE {destination}")
        wrote += 1
    print(f"BOOTSTRAP {target} wrote={wrote} kept={kept}")
    return 0


def _utf8_output():
    """Agents read these scripts through pipes; make the bytes UTF-8 on every platform."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def main(argv=None):
    _utf8_output()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dir", required=True, help="handoff directory to create or complete")
    parser.add_argument("--project", required=True)
    parser.add_argument("--reviewer", required=True, help="agent or tool playing the reviewer")
    parser.add_argument("--builder", required=True, help="agent or tool playing the builder")
    parser.add_argument("--lang", choices=["en", "zh"], default="en")
    parser.add_argument("--same-family", choices=["yes", "no"], default="no")
    parser.add_argument("--delivery", choices=["local", "pr"], default="local")
    parser.add_argument("--lock", help="heavy-check lock file (default: <dir>/.locks/heavy-check.lock)")
    parser.add_argument("--service", default="none", help="the operator's running service, e.g. 'port 8766'")
    parser.add_argument("--skill-dir", help="where agents find the skill (default: this skill's folder)")
    args = parser.parse_args(argv)
    try:
        return bootstrap(args)
    except KeyError as error:
        print(f"BOOTSTRAP failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
