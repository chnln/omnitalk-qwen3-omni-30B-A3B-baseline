"""vLLM offline engine and the checks on what actually reached the model. Needs the GPU environment."""
from __future__ import annotations

import time
import traceback

PAD_TOKENS = {"video": "<|video_pad|>", "audio": "<|audio_pad|>", "image": "<|image_pad|>"}
# vLLM and Hugging Face can place an audio token one position apart: vLLM pads audio to a multiple of the 160-sample hop,
# and with non-integer frame rates the two round a grid's time differently. Audio has 13 tokens per second, so 2 tokens is 0.15 s.
AUDIO_OFFSET_TOLERANCE = 2


def load_engine(model_cfg: dict, engine_cfg: dict, mm_limits: dict, seed: int):
    """Return (llm, processor, pad token ids). Call from inside main(): vLLM starts its tensor-parallel workers with spawn."""
    from transformers import Qwen3OmniMoeProcessor
    from vllm import LLM

    llm = LLM(model=model_cfg["hf_id"], revision=model_cfg["revision"], limit_mm_per_prompt=mm_limits, seed=seed, **engine_cfg)
    processor = Qwen3OmniMoeProcessor.from_pretrained(model_cfg["hf_id"], revision=model_cfg["revision"])
    pad_ids = {kind: processor.tokenizer.convert_tokens_to_ids(token) for kind, token in PAD_TOKENS.items()}
    return llm, processor, pad_ids


def modality_token_counts(ids: list[int], pad_ids: dict[str, int]) -> dict[str, int]:
    return {kind: sum(1 for t in ids if t == pad) for kind, pad in pad_ids.items()}


def modality_violations(counts: dict[str, int], expected: dict[str, bool]) -> list[str]:
    """Names of modalities whose presence in the prompt contradicts the condition."""
    return [f"{kind}: {counts[kind]} tokens, expected {'some' if want else 'none'}"
            for kind, want in expected.items() if (counts[kind] > 0) != want]


def pad_runs(ids: list[int], pad_ids: set[int]) -> list[list[int]]:
    """Consecutive runs of pad tokens as [token, length]."""
    runs: list[list[int]] = []
    for token in ids:
        if token in pad_ids:
            if runs and runs[-1][0] == token:
                runs[-1][1] += 1
            else:
                runs.append([token, 1])
    return runs


def _audio_tokens_before_video_tokens(runs: list[list[int]], audio_pad: int) -> list[int]:
    """For each video token, how many audio tokens come before it."""
    before, audio = [], 0
    for token, length in runs:
        if token == audio_pad:
            audio += length
        else:
            before.extend([audio] * length)
    return before


def compare_interleaving(vllm_ids: list[int], reference_ids: list[int], video_pad: int, audio_pad: int) -> dict:
    """Measure how far vLLM's interleaved audio sits from the Hugging Face processor's, in audio tokens."""
    ours, theirs = pad_runs(vllm_ids, {video_pad, audio_pad}), pad_runs(reference_ids, {video_pad, audio_pad})
    ours_before, theirs_before = _audio_tokens_before_video_tokens(ours, audio_pad), _audio_tokens_before_video_tokens(theirs, audio_pad)
    audio_delta = sum(n for t, n in ours if t == audio_pad) - sum(n for t, n in theirs if t == audio_pad)
    same_video = len(ours_before) == len(theirs_before)
    offset = max((abs(a - b) for a, b in zip(ours_before, theirs_before)), default=0)
    return {"identical": ours == theirs, "ok": same_video and offset <= AUDIO_OFFSET_TOLERANCE and abs(audio_delta) <= AUDIO_OFFSET_TOLERANCE,
            "same_video_tokens": same_video, "audio_token_delta": audio_delta, "max_audio_offset_tokens": offset,
            "n_runs": len(ours), "n_audio_runs": sum(1 for t, _ in ours if t == audio_pad)}


def reference_input_ids(processor, chat: str, media) -> list[int]:
    """The token ids the Hugging Face processor produces for an interleaved clip."""
    batch = processor(text=chat, audio=[media.audio], videos=[media.video], return_tensors="pt", padding=True,
                      use_audio_in_video=True, fps=media.sample_fps)
    return batch["input_ids"][0].tolist()


def generate(llm, requests: list[dict], sampling_params: list):
    """Run a batch, falling back to one request at a time if the batch fails.

    Returns (output or None, batch wall seconds, batch size, error text or None) per request.
    """
    start = time.time()
    try:
        outputs = llm.generate(requests, sampling_params=sampling_params, use_tqdm=False)
        wall = time.time() - start
        return [(o, wall, len(requests), None) for o in outputs]
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        print(f"batch of {len(requests)} failed; retrying one request at a time", flush=True)
    results = []
    for request, params in zip(requests, sampling_params):
        start = time.time()
        try:
            output = llm.generate([request], sampling_params=params, use_tqdm=False)[0]
            results.append((output, time.time() - start, 1, None))
        except Exception as error:  # noqa: BLE001
            traceback.print_exc()
            results.append((None, time.time() - start, 1, repr(error)[:1000]))
    return results
