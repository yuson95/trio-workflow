#!/usr/bin/env python3
"""Build a contact sheet (index.html) from page x state screenshots of main and a candidate.

Layout expected under EVIDENCE_DIR:
  main/<page>__<state>.png        screenshots of the main branch (optional)
  candidate/<page>__<state>.png   screenshots of the candidate

The sheet has one row per page and one column per state, with main beside the
candidate. A cell is marked "unchanged" when both files are byte-identical,
"new" when only the candidate has it, "removed" when only main has it, and
"missing" when neither has it. Images are linked, not embedded.

Usage:
  screenshot_sheet.py EVIDENCE_DIR [--states empty full many narrow] [--title TEXT] [--out FILE]
Prints one summary line: SHEET <path> pages=.. states=.. missing=.. unchanged=.. changed=..
"""

import argparse
import filecmp
import html
import os
import sys
from pathlib import Path

SIDES = ("main", "candidate")
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def _collect(root):
    """Map (page, state) -> {side: Path} from the main/ and candidate/ folders."""
    cells = {}
    for side in SIDES:
        folder = root / side
        if not folder.is_dir():
            continue
        for path in sorted(folder.iterdir()):
            if path.suffix.lower() not in IMAGE_SUFFIXES or "__" not in path.stem:
                continue
            page, state = path.stem.split("__", 1)
            cells.setdefault((page, state), {})[side] = path
    return cells


def _status(entry):
    main, candidate = entry.get("main"), entry.get("candidate")
    if main and candidate:
        return "unchanged" if filecmp.cmp(main, candidate, shallow=False) else "changed"
    if candidate:
        return "new"
    if main:
        return "removed"
    return "missing"


def _image(path, out_dir, label):
    relative = os.path.relpath(path, out_dir).replace(os.sep, "/")
    source = html.escape(relative, quote=True)
    return f'<figure><a href="{source}"><img src="{source}" alt="{html.escape(label)}" loading="lazy"></a><figcaption>{html.escape(label)}</figcaption></figure>'


STYLE = """
body{font-family:system-ui,sans-serif;margin:16px;background:Canvas;color:CanvasText}
table{border-collapse:collapse}th,td{border:1px solid GrayText;padding:6px;vertical-align:top}
th{text-align:left;font-weight:500}.pair{display:flex;gap:6px}
figure{margin:0}img{width:260px;height:auto;display:block;border:1px solid GrayText}
figcaption{font-size:12px}.tag{font-size:12px;padding:1px 6px;border:1px solid GrayText;border-radius:8px}
.missing{opacity:.7}
"""


def build(root, states, title, out):
    cells = _collect(root)
    pages = sorted({page for page, _ in cells})
    found_states = sorted({state for _, state in cells})
    ordered = list(states) + [state for state in found_states if state not in states]
    counts = {"missing": 0, "unchanged": 0, "changed": 0, "new": 0, "removed": 0}
    out_dir = out.parent
    rows = []
    for page in pages:
        tds = []
        for state in ordered:
            entry = cells.get((page, state), {})
            status = _status(entry)
            counts[status] += 1
            figures = "".join(_image(entry[side], out_dir, side) for side in SIDES if side in entry)
            tds.append(f'<td class="{status}"><span class="tag">{status}</span><div class="pair">{figures}</div></td>')
        rows.append(f"<tr><th>{html.escape(page)}</th>{''.join(tds)}</tr>")
    head = "".join(f"<th>{html.escape(state)}</th>" for state in ordered)
    summary = ", ".join(f"{name} {value}" for name, value in counts.items())
    document = (
        f"<!doctype html><html><head><meta charset=\"utf-8\"><title>{html.escape(title)}</title><style>{STYLE}</style></head>"
        f"<body><h1>{html.escape(title)}</h1><p>{html.escape(summary)}</p>"
        f"<table><thead><tr><th>page</th>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table></body></html>\n"
    )
    out.write_text(document, encoding="utf-8")
    return pages, ordered, counts


def _utf8_output():
    """Agents read these scripts through pipes; make the bytes UTF-8 on every platform."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def main(argv=None):
    _utf8_output()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("evidence_dir")
    parser.add_argument("--states", nargs="*", default=["empty", "full", "many", "narrow"])
    parser.add_argument("--title", default="Screenshot matrix")
    parser.add_argument("--out")
    args = parser.parse_args(argv)
    root = Path(args.evidence_dir)
    if not (root / "candidate").is_dir() and not (root / "main").is_dir():
        print(f"SHEET needs {root}/candidate or {root}/main", file=sys.stderr)
        return 2
    out = Path(args.out) if args.out else root / "index.html"
    pages, states, counts = build(root, args.states, args.title, out)
    print(f"SHEET {out} pages={len(pages)} states={len(states)} missing={counts['missing']} "
          f"unchanged={counts['unchanged']} changed={counts['changed']} new={counts['new']} removed={counts['removed']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
