"""Input conditions: what the model receives for one question.

A condition only says which modalities are present and how. `build_message` and `build_multi_modal_data`
turn a condition plus a decoded clip into the chat message and vLLM's multi_modal_data.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .prompts import Prompts, format_time, render_question


@dataclass(frozen=True)
class Condition:
    name: str
    visual: str  # video | frames | none
    audio: str  # interleaved | separate | none
    subtitles: bool = False
    num_frames: int | None = None

    def __post_init__(self):
        if self.visual not in ("video", "frames", "none") or self.audio not in ("interleaved", "separate", "none"):
            raise ValueError(f"{self.name}: unknown visual or audio mode ({self.visual}, {self.audio})")
        if self.audio == "interleaved" and self.visual != "video":
            raise ValueError(f"{self.name}: interleaved audio needs visual: video")
        if (self.visual == "frames") != (self.num_frames is not None):
            raise ValueError(f"{self.name}: num_frames goes with visual: frames")

    @property
    def expected(self) -> dict[str, bool]:
        """Which modalities must, and must not, reach the model."""
        return {"video": self.visual == "video", "image": self.visual == "frames", "audio": self.audio != "none"}


def load_conditions(config: dict) -> dict[str, Condition]:
    return {name: Condition(name=name, **spec) for name, spec in config["conditions"].items()}


def build_message(cond: Condition, item: dict, media, prompts: Prompts, subtitles: str | None) -> tuple[list[dict], str]:
    """Return the chat message and the plain text the model reads.

    Media entries carry placeholders only: the chat template needs their type, and the data goes through multi_modal_data.
    """
    content: list[dict[str, Any]] = []
    texts: list[str] = []
    if cond.visual == "video":
        content.append({"type": "video", "video": "clip"})
    elif cond.visual == "frames":
        for _, seconds in media.frames[cond.num_frames]:
            caption = prompts.frame_caption.replace("{time}", format_time(seconds))
            content.append({"type": "text", "text": caption})
            content.append({"type": "image", "image": "frame"})
            texts.append(caption)
    if cond.audio == "separate":
        content.append({"type": "audio", "audio": "clip"})
    if cond.subtitles:
        if subtitles is None:
            raise ValueError(f"{item['question_id']}: condition {cond.name} needs subtitles")
        block = prompts.subtitles_block.replace("{subtitles}", subtitles)
        content.append({"type": "text", "text": block})
        texts.append(block)
    question = render_question(prompts.question, item)
    content.append({"type": "text", "text": question})
    texts.append(question)
    return [{"role": "user", "content": content}], "\n\n".join(texts)


def build_multi_modal_data(cond: Condition, media, sample_rate: int) -> tuple[dict, dict]:
    """Return vLLM's multi_modal_data and mm_processor_kwargs for this condition."""
    data: dict[str, Any] = {}
    if cond.visual == "video":
        data["video"] = media.video
    elif cond.visual == "frames":
        data["image"] = [image for image, _ in media.frames[cond.num_frames]]
    if cond.audio != "none":
        data["audio"] = (media.audio, sample_rate)
    kwargs: dict[str, Any] = {}
    if cond.visual == "video":
        # The processor otherwise assumes fps=1.0, which stretches the temporal ids and misaligns interleaved audio.
        kwargs["fps"] = media.sample_fps
    if cond.visual == "video" or cond.audio != "none":
        kwargs["use_audio_in_video"] = cond.audio == "interleaved"
    return data, kwargs
