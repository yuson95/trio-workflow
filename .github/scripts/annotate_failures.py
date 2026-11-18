#!/usr/bin/env python3
"""Turn unittest failures into GitHub Actions error annotations.

Job logs need a signed-in browser, but a check run's annotations are public, so
anyone (or any agent) can read why CI failed from the API. Usage:

  python .github/scripts/annotate_failures.py <unittest output file>
"""

import sys
from pathlib import Path

SEPARATOR = "=" * 70


def blocks(text):
    """Yield (title, body) for each FAIL or ERROR block in unittest's verbose output."""
    for chunk in text.split(SEPARATOR)[1:]:
        lines = chunk.strip("\n").splitlines()
        if not lines or not lines[0].startswith(("FAIL:", "ERROR:")):
            continue
        body = [line for line in lines[1:] if not set(line) <= {"-"}]
        tail = "\n".join(body).split("\nRan ")[0].strip()
        yield lines[0], tail[-3000:]


def escape(value):
    return value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def escape_property(value):
    return escape(value).replace(":", "%3A").replace(",", "%2C")


def main(argv):
    text = Path(argv[1]).read_text(encoding="utf-8", errors="replace")
    found = list(blocks(text))
    for title, body in found:
        print(f"::error title={escape_property(title)}::{escape(body)}")
    if not found:
        print(f"::error title=tests failed::{escape(text[-3000:])}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
