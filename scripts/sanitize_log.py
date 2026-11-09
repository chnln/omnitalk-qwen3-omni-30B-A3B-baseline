#!/usr/bin/env python3
"""Copy a job log with absolute cluster paths, usernames and host names replaced, so it can be shared."""
import argparse
import getpass
import re
from pathlib import Path

PATTERNS = [
    (re.compile(r"(/home|/projects|/scratch-shared|/scratch-local|/scratch-node|/gpfs|/sw/arch|/sw|/tmp|/opt)/[^\s'\"),;:]+"), "<path>"),
    (re.compile(r"/Users/[^\s'\"),;:]+"), "<path>"),
    (re.compile(r"\b(?:gcn|tcn|fcn|hcn|srv|int)\d+(?:\.[a-z0-9.\-]+)?\b"), "<host>"),
    (re.compile(r"\bjobid=?\s*\d+\b"), "jobid"),
]


def clean(text: str, usernames: list[str]) -> str:
    for pattern, replacement in PATTERNS:
        text = pattern.sub(replacement, text)
    for name in usernames:
        text = re.sub(rf"\b{re.escape(name)}\b", "<user>", text)
    return text


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("destination", type=Path)
    p.add_argument("--username", action="append", default=[], help="extra names to remove; the current user is always removed")
    args = p.parse_args()
    args.destination.parent.mkdir(parents=True, exist_ok=True)
    args.destination.write_text(clean(args.source.read_text(errors="replace"), [getpass.getuser(), *args.username]), encoding="utf-8")


if __name__ == "__main__":
    main()
