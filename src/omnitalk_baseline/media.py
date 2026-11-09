"""Decode a clip once into the tensors every condition shares. Needs the GPU environment."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ClipMedia:
    video: object  # float tensor, frames x channels x height x width, values 0-255
    audio: object  # mono float32 array at 16 kHz, or None when no condition uses audio
    sample_fps: float
    frames: dict  # num_frames -> list of (PIL image, seconds)

    def info(self) -> dict:
        seconds = None if self.audio is None else round(len(self.audio) / 16000, 3)
        return {"video_frames_shape": list(self.video.shape), "sample_fps": round(self.sample_fps, 3), "audio_seconds": seconds}


def decode_clip(path: Path, media_cfg: dict, frame_counts: set[int], with_audio: bool = True) -> ClipMedia:
    import numpy as np
    from qwen_omni_utils import process_mm_info

    # max_frames only matters for clips longer than max_frames / fps seconds, which are then sampled uniformly at a lower rate.
    entry = {"type": "video", "video": str(path), "fps": media_cfg["video_fps"], "max_frames": media_cfg["video_max_frames"],
             "max_pixels": media_cfg["video_max_pixels"]}
    audios, _, videos, video_kwargs = process_mm_info(
        [{"role": "user", "content": [entry]}], use_audio_in_video=with_audio, return_video_kwargs=True,
        image_patch_size=media_cfg["image_patch_size"])
    video, fps = videos[0], float(video_kwargs["fps"][0])
    return ClipMedia(video=video, audio=np.asarray(audios[0], dtype=np.float32) if with_audio else None, sample_fps=fps,
                     frames={n: sample_frames(video, fps, n) for n in frame_counts})


def sample_frames(video, fps: float, count: int) -> list:
    """Evenly spaced stills from the decoded video, at the video's own resolution, with their times in seconds."""
    import numpy as np
    from PIL import Image

    total = video.shape[0]
    indices = np.linspace(0, total - 1, min(count, total)).round().astype(int)
    stills = []
    for index in indices:
        pixels = video[index].clamp(0, 255).permute(1, 2, 0).numpy().astype("uint8")
        stills.append((Image.fromarray(pixels), float(index) / fps))
    return stills
