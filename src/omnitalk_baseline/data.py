"""Read the question list, clip manifest and subtitles, and check that the clip files are the expected ones."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def read_jsonl(path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_questions(path, subset: str | None = None, question_ids: set[str] | None = None) -> list[dict]:
    rows = read_jsonl(path)
    if subset:
        rows = [r for r in rows if subset in r["subsets"]]
    if question_ids:
        missing = question_ids - {r["question_id"] for r in rows}
        if missing:
            raise ValueError(f"unknown question ids: {sorted(missing)}")
        rows = [r for r in rows if r["question_id"] in question_ids]
    return rows


def load_manifest(path) -> dict[str, dict]:
    return {r["clip_id"]: r for r in read_jsonl(path)}


def sha256_of(path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_clip(entry: dict, clips_dir, verify: bool = True) -> Path:
    """Return the clip path, raising if the file is absent or (when verify is set) not the manifest's file."""
    path = Path(clips_dir) / entry["file"]
    if not path.is_file():
        raise FileNotFoundError(f"clip {entry['clip_id']}: {entry['file']} not found in the clips directory")
    if verify and (found := sha256_of(path)) != entry["sha256"]:
        raise ValueError(f"clip {entry['clip_id']}: sha256 {found[:12]}... does not match the manifest {entry['sha256'][:12]}...")
    return path


def load_subtitles(directory, clip_id: str) -> str:
    """Subtitle lines of a clip, without the '# ...' provenance header."""
    text = (Path(directory) / f"{clip_id}.txt").read_text(encoding="utf-8")
    return "\n".join(line for line in text.splitlines() if line.strip() and not line.startswith("#"))
