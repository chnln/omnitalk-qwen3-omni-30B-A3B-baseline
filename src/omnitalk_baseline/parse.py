"""Turn raw model output into a chosen letter. An output that does not resolve to one letter stays unparsed and counts as wrong."""
from __future__ import annotations

import re

_BARE = re.compile(r"^[\s(\[*\"'`]*([A-H])[\s)\]*\"'`.:,]*$")
# Letters are matched case-sensitively, and "A" not before a lowercase word, so the article in "a blue cup" is not an answer.
_LETTER = r"[(\[*\"'`]*([B-H]\b|A\b(?!\s+[a-z]))"
_ANSWER_PHRASE = re.compile(r"(?i:\banswer\b)[^A-Za-z]{0,12}(?:(?i:is)\s+)?" + _LETTER)
_OPTION_PHRASE = re.compile(r"(?i:\b(?:option|choice)\b)[^A-Za-z]{0,12}(?:(?i:is)\s+)?" + _LETTER)
_LEADING = re.compile(r"^[\s(\[*\"'`]*([A-H])[)\]*\"'`]*\s*[.:)\-]")


def split_thinking(raw: str) -> dict:
    """Separate a Thinking model's reasoning from its answer."""
    if "</think>" in raw:
        thought, answer = raw.split("</think>", 1)
        return {"think_closed": True, "thinking_text": thought.replace("<think>", "").strip(), "answer_text": answer.strip()}
    return {"think_closed": False, "thinking_text": raw.replace("<think>", "").strip(), "answer_text": None}


def _checked(letter: str, method: str, options: dict[str, str] | None) -> tuple[str | None, str]:
    """A letter that is not one of this question's options cannot be an answer (questions have 4 to 6 options)."""
    return (None, "not_an_option") if options and letter not in options else (letter, method)


def parse_letter(text: str | None, options: dict[str, str] | None = None) -> tuple[str | None, str]:
    """Return (letter or None, method)."""
    if not text or not text.strip():
        return None, "empty"
    if m := _BARE.match(text):
        return _checked(m.group(1), "bare_letter", options)
    if m := _LEADING.match(text):
        return _checked(m.group(1), "leading_letter", options)
    if m := _ANSWER_PHRASE.search(text) or _OPTION_PHRASE.search(text):
        return _checked(m.group(1), "explicit", options)
    if options:
        lowered = text.lower()
        hits = [letter for letter, option in options.items() if option.lower() in lowered]
        if len(hits) == 1:
            return hits[0], "option_text"
    return None, "unparsed"
