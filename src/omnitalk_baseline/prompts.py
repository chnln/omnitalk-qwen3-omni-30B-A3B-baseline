"""Prompt templates. Placeholders are filled with str.replace, so templates may contain literal braces (for example JSON)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Prompts:
    question: str
    subtitles_block: str
    frame_caption: str


def load_prompts(question_file, prompts_dir=None) -> Prompts:
    question_file = Path(question_file)
    prompts_dir = Path(prompts_dir) if prompts_dir else question_file.parent
    read = lambda p: Path(p).read_text(encoding="utf-8").strip()  # noqa: E731
    return Prompts(read(question_file), read(prompts_dir / "subtitles_block.txt"), read(prompts_dir / "frame_caption.txt"))


def format_options(options: dict[str, str]) -> str:
    return "\n".join(f"{letter}. {text}" for letter, text in options.items())


def render_question(template: str, item: dict) -> str:
    return template.replace("{question}", item["question"]).replace("{options}", format_options(item["options"]))


def format_time(seconds: float) -> str:
    whole = int(round(seconds))
    return f"{whole // 60:02d}:{whole % 60:02d}"
