"""Turn raw model output into a chosen letter. An output that does not resolve to one letter stays unparsed and counts as wrong."""
from __future__ import annotations

import re

LETTERS = "ABCD"
_BARE = re.compile(r"^[\s(\[*\"'`]*([A-D])[\s)\]*\"'`.:,]*$")
_EXPLICIT = re.compile(r"\b(?:answer|option|choice)\b[^A-Za-z]{0,12}(?:is\s+)?[(\[*\"'`]*([A-D])\b", re.IGNORECASE)
_LEADING = re.compile(r"^[\s(\[*\"'`]*([A-D])[)\]*\"'`]*\s*[.:)\-]")


def split_thinking(raw: str) -> dict:
    """Separate a Thinking model's reasoning from its answer."""
    if "</think>" in raw:
        thought, answer = raw.split("</think>", 1)
        return {"think_closed": True, "thinking_text": thought.replace("<think>", "").strip(), "answer_text": answer.strip()}
    return {"think_closed": False, "thinking_text": raw.replace("<think>", "").strip(), "answer_text": None}


def parse_letter(text: str | None, options: dict[str, str] | None = None) -> tuple[str | None, str]:
    """Return (letter or None, method)."""
    if not text or not text.strip():
        return None, "empty"
    if m := _BARE.match(text):
        return m.group(1), "bare_letter"
    found = [m.group(1).upper() for m in _EXPLICIT.finditer(text)]
    if found and found[-1] in LETTERS:
        return found[-1], "explicit"
    if m := _LEADING.match(text):
        return m.group(1), "leading_letter"
    if options:
        lowered = text.lower()
        hits = [letter for letter, option in options.items() if option.lower() in lowered]
        if len(hits) == 1:
            return hits[0], "option_text"
    return None, "unparsed"
