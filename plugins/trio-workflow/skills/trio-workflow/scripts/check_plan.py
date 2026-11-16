#!/usr/bin/env python3
"""Check a trio plan file for the structure reviewers rely on.

Checks:
  1. Every requirement block (### <ID> ... under the requirements section) has
     a type, a "You see" line, unit and live verification, and a review gate;
     a review-gated requirement (gate other than "none") also needs a prototype.
  2. Every decision row has a default.
  3. In the batches table, no file is owned by two batches unless it is listed
     as append-only, and every dependency names a batch that exists.

English labels and the Chinese labels below are both recognized, so a plan
written in either language passes.

Usage:
  check_plan.py PLAN.md [PLAN.md ...]
Prints one line per problem and a summary line; exits 1 when problems exist.
"""

import re
import sys

LABELS = {
    "type": ("Type", "类型"),
    "you_see": ("You see", "你会看到"),
    "unit": ("Verify, unit", "单元验证"),
    "live": ("Verify, live", "实际操作验证"),
    "gate": ("Review gate", "走查"),
}
SECTION_REQUIREMENTS = ("requirements", "需求")
SECTION_DECISIONS = ("decisions", "决定", "待决")
SECTION_BATCHES = ("batches", "批次")
OWNED_HEADERS = ("owned files", "独占文件", "归属文件")
DEPENDS_HEADERS = ("depends on", "依赖")
APPEND_ONLY_MARKERS = ("append-only", "追加型")
EMPTY_DEFAULTS = {"", "-", "—", "tbd", "?", "待定"}
PROTOTYPE = ("Prototype", "原型")
GATE_VALUE = re.compile(r"(?:Review gate|走查)\s*\**\s*[:：]\s*(.*)")
NO_GATE = {"none", "no", "-", "—", "无", "不需要", "否"}
BACKTICK = re.compile(r"`([^`]+)`")


def _sections(lines):
    """Yield (title, start, end) for every '## ' section."""
    marks = [(i, line[3:].strip()) for i, line in enumerate(lines) if line.startswith("## ")]
    for index, (start, title) in enumerate(marks):
        end = marks[index + 1][0] if index + 1 < len(marks) else len(lines)
        yield title, start, end


def _matches(title, keys):
    lowered = title.lower()
    return any(key in lowered for key in keys)


def _table_rows(lines, start, end):
    """Return (header_cells, [(line_no, cells)]) for the first table in a range."""
    header, rows = None, []
    for number in range(start, end):
        line = lines[number].strip()
        if not line.startswith("|"):
            if header is not None and rows:
                break
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if header is None:
            header = cells
        elif all(set(cell) <= set("-: ") for cell in cells):
            continue
        else:
            rows.append((number + 1, cells))
    return header, rows


def _column(header, keys):
    for index, cell in enumerate(header or []):
        if _matches(cell, keys):
            return index
    return None


def _has_label(body, aliases):
    """True when a line of the block starts with one of the labels, optionally as a bullet or in bold."""
    return any(re.search(r"(^|\n)\s*[-*]?\s*(\*\*)?" + re.escape(alias), body) for alias in aliases)


def check_requirements(lines, start, end, problems):
    blocks = [i for i in range(start, end) if lines[i].startswith("### ")]
    if not blocks:
        problems.append((start + 1, "requirements section has no '### <ID> ...' blocks"))
    for position, first in enumerate(blocks):
        last = blocks[position + 1] if position + 1 < len(blocks) else end
        body = "\n".join(lines[first:last])
        name = lines[first][4:].strip()
        for key, aliases in LABELS.items():
            if not _has_label(body, aliases):
                problems.append((first + 1, f"requirement '{name}' lacks '{aliases[0]}' / '{aliases[1]}'"))
        gate = GATE_VALUE.search(body)  # a gate other than "none" means the operator will judge the result
        gated = gate is not None and gate.group(1).strip().strip("*`").strip().lower() not in NO_GATE
        if gated and not _has_label(body, PROTOTYPE):
            problems.append((first + 1, f"review-gated requirement '{name}' lacks 'Prototype' / '原型'"))


def check_decisions(lines, start, end, problems):
    header, rows = _table_rows(lines, start, end)
    column = _column(header, ("default", "默认"))
    if header is None or column is None:
        return
    for number, cells in rows:
        value = cells[column].strip().lower() if column < len(cells) else ""
        if value in EMPTY_DEFAULTS:
            problems.append((number, f"decision '{cells[0]}' has no default"))


def check_batches(lines, start, end, problems):
    header, rows = _table_rows(lines, start, end)
    owned_col, depends_col = _column(header, OWNED_HEADERS), _column(header, DEPENDS_HEADERS)
    if header is None or owned_col is None:
        problems.append((start + 1, "batches section has no table with an owned-files column"))
        return
    append_only = set()
    for number in range(start, end):
        if any(marker in lines[number].lower() for marker in APPEND_ONLY_MARKERS):
            append_only.update(BACKTICK.findall(lines[number]))
    batches = {cells[0] for _, cells in rows if cells}
    owners = {}
    for number, cells in rows:
        batch = cells[0]
        for path in BACKTICK.findall(cells[owned_col] if owned_col < len(cells) else ""):
            owners.setdefault(path, []).append((batch, number))
        if depends_col is not None and depends_col < len(cells):
            for token in re.split(r"[,;，、\s]+", cells[depends_col]):
                token = token.strip()
                if token and token.lower() not in {"none", "-", "—", "无"} and token not in batches:
                    problems.append((number, f"batch '{batch}' depends on unknown batch '{token}'"))
    for path, holders in sorted(owners.items()):
        if len(holders) > 1 and path not in append_only:
            names = ", ".join(batch for batch, _ in holders)
            problems.append((holders[1][1], f"file `{path}` is owned by several batches ({names}); give it one owner or mark it append-only"))


def check(path):
    with open(path, encoding="utf-8") as handle:
        lines = handle.read().splitlines()
    problems = []
    seen = set()
    for title, start, end in _sections(lines):
        if _matches(title, SECTION_REQUIREMENTS) and "requirements" not in seen:
            seen.add("requirements")
            check_requirements(lines, start, end, problems)
        elif _matches(title, SECTION_DECISIONS):
            check_decisions(lines, start, end, problems)
        elif _matches(title, SECTION_BATCHES) and "batches" not in seen:
            seen.add("batches")
            check_batches(lines, start, end, problems)
    for needed in ("requirements", "batches"):
        if needed not in seen:
            problems.append((1, f"no '{needed}' section found"))
    return problems


def _utf8_output():
    """Agents read these scripts through pipes; make the bytes UTF-8 on every platform."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def main(argv=None):
    _utf8_output()
    paths = sys.argv[1:] if argv is None else argv
    if not paths:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    total = 0
    for path in paths:
        for line, message in check(path):
            print(f"PLAN {path}:{line}: {message}")
            total += 1
    print("CHECK_PLAN ok" if total == 0 else f"CHECK_PLAN {total} problems")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
