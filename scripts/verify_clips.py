#!/usr/bin/env python3
"""Check that the clips in a directory are the exact files the manifest describes."""
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from omnitalk_baseline.data import load_manifest, resolve_clip  # noqa: E402


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", type=Path, default=ROOT / "data/clips_manifest.jsonl")
    p.add_argument("--clips-dir", type=Path, default=Path(os.environ.get("OMNITALK_CLIPS_DIR", ROOT / "data/clips")))
    args = p.parse_args()
    failures = 0
    for clip_id, entry in load_manifest(args.manifest).items():
        try:
            resolve_clip(entry, args.clips_dir)
            print(f"ok   {clip_id}")
        except (OSError, ValueError) as error:
            failures += 1
            print(f"FAIL {error}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
