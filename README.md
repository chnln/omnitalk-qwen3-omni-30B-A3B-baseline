# OmniTalk baseline: Qwen3-Omni-30B-A3B

A runnable baseline for OmniTalk, a benchmark of multiple-choice questions about short video clips of people interacting. A question is meant to need speech and what is visible (or audible beyond speech) to be understood together.

This repository runs `Qwen/Qwen3-Omni-30B-A3B-Instruct` and `-Thinking` with [vLLM](https://github.com/vllm-project/vllm) offline inference, under several input conditions (audio and video interleaved, video without audio, video split into frames, and so on), and scores the answers.

Results of the reference run, with its configuration, inputs and outputs: **[RESULTS.md](RESULTS.md)**.

## Contents

| Path | What it holds |
|---|---|
| `configs/baseline.yaml` | Models, sampling, engine settings, media settings, and the input conditions |
| `prompts/` | Prompt templates |
| `data/questions.jsonl` | The questions, options and answer key, with how each question was reviewed |
| `data/clips_manifest.jsonl` | Which clip each question uses: source video, time window, SHA-256, resolution |
| `data/subtitles/` | YouTube captions for the subtitle conditions |
| `data/clips/` | Put the clips here (not tracked by Git) |
| `scripts/run_baseline.py` | Run one model over the questions |
| `scripts/score_run.py` | Score a finished run |
| `scripts/verify_clips.py` | Check clip files against the manifest |
| `scripts/sanitize_log.py` | Strip paths and host names from a job log before sharing it |
| `slurm/` | Job scripts and a template for site-specific settings |
| `src/omnitalk_baseline/` | The library the scripts use |
| `tests/` | Tests that need no GPU, weights or clips |
| `outputs/` | Complete outputs of the runs in RESULTS.md |

## Requirements

- Linux, x86_64, Python 3.12
- Two GPUs with about 93 GiB each. The reference run used 2 × NVIDIA H100, 32 CPU cores and 360 GB of memory. vLLM reserves 85% of each GPU
- `ffmpeg` on `PATH`, used to read the audio track of an mp4
- About 130 GB of disk for the two checkpoints

## Setup

**1. Environment.** `requirements.lock.txt` pins all 216 packages of the environment behind RESULTS.md (vLLM 0.33.0, PyTorch 2.14.0 with CUDA 13, Transformers 5.20.2, qwen-omni-utils 0.0.9, librosa 0.11.0).

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.lock.txt
```

On a SLURM cluster, `sbatch --partition=<cpu or build partition> --account=<account> slurm/build_env.sbatch /path/to/new/venv` does the same in a job. It needs no GPU.

**2. Weights.** Download the two checkpoints into your Hugging Face cache. The config pins the revisions used for RESULTS.md; the snapshot downloaded must match them, or change `revision:` in the config.

```bash
hf download Qwen/Qwen3-Omni-30B-A3B-Instruct --revision 26291f793822fb6be9555850f06dfe95f2d7e695
hf download Qwen/Qwen3-Omni-30B-A3B-Thinking --revision 2f443cfc4c54b14a815c0e2bb9a9d6cbcd9a748b
```

**3. Clips.** The clips are not distributed here. See [Inputs](#inputs) for how to obtain or replace them, and put them in `data/clips/`, or set `OMNITALK_CLIPS_DIR`. Then check them:

```bash
.venv/bin/python scripts/verify_clips.py
```

**4. Site settings.** For SLURM:

```bash
cp slurm/site.env.example slurm/site.env   # then edit; this file stays out of Git
```

## Running

**On SLURM.** Run from the repository root with your own partition and account. Partition and account deliberately do not appear in the job script.

```bash
sbatch --partition=<gpu partition> --account=<account> --time=00:45:00 slurm/run_baseline.sbatch smoke instruct smoke_run
sbatch --partition=<gpu partition> --account=<account> slurm/run_baseline.sbatch
```

The arguments are, in order: the subset (`smoke` has 3 questions, `core` has 20; default `core`), a quoted space-separated list of keys under `models:` (default `"instruct thinking"`), the run id that names the output directory, and comma-separated conditions (default all). Each model loads once, which takes about 4 to 8 minutes; the 160 requests per model then take about 3 to 7 minutes.

**Without SLURM.** Run from the repository root, with the variables from `slurm/site.env` exported:

```bash
.venv/bin/python scripts/run_baseline.py --model instruct --subset smoke --output-dir outputs/my_run
.venv/bin/python scripts/score_run.py --run outputs/my_run
```

**Tests** (no GPU needed):

```bash
uv run --no-project --python 3.12 --with pytest --with pyyaml python -m pytest -q
```

## Input conditions

Each condition sends the same question text and differs only in the material around it.

| Condition | Video or frames | Audio | Subtitles |
|---|---|---|---|
| `av_interleaved` | video at 2 fps | interleaved with the video grids | no |
| `av_separate` | video at 2 fps | one separate audio item | no |
| `video_only` | video at 2 fps | none | no |
| `frames_audio` | 16 evenly spaced stills, each after a `Frame at mm:ss:` caption | one separate audio item | no |
| `frames_only` | as above | none | no |
| `audio_only` | none | one audio item | no |
| `subtitles_only` | none | none | yes |
| `question_only` | none | none | no |

`av_interleaved` is the primary condition. In an earlier pilot on this model, interleaving was what made timing in the audio match the frames.

Video is sampled at 2 fps up to 240 frames (`video_max_frames`), at most 896 x 504 pixels. A clip longer than 120 s is sampled evenly at the lower rate that gives 240 frames. Four of the 19 clips are longer than 120 s; the three longest (129, 135 and 142 s) are sampled at 1.69 to 1.86 fps.

The run checks each request's actual token ids before accepting it. It stops with exit code 3 if a modality that should be absent reached the model, or if interleaved audio sits more than half a video grid from the Hugging Face processor's position. A request that produced no output is left out of the scores, and the run then exits with code 4.

## Inputs

**Questions** (`data/questions.jsonl`, one JSON object per line):

```json
{"question_id": "OT-0012", "clip_id": "C11",
 "question": "Why does the man laugh at the lady's question?",
 "options": {"A": "It was a joke", "B": "It was a dumb question", "C": "He is gloating", "D": "He is proud of his achievement", "E": "He feels nervous"},
 "answer": "A", "answer_status": "author_key", "approval": "reviewer_selected", "subsets": ["smoke", "core"]}
```

Questions have 4 to 6 options. The prompt names the letters each question allows.

The 20 questions come from the team's shared annotation document, and `question_id` is a neutral id. They are the ones the benchmark reviewer endorsed most clearly, and they cover four question authors. `approval` says what the reviewer did:

| `approval` | Meaning | Questions |
|---|---|---|
| `reviewer_praised` | The reviewer called the question good | 3 |
| `reviewer_selected` | The reviewer marked it selected or to keep | 9 |
| `reviewer_written` | The reviewer wrote it | 3 |
| `selected_list` | It is on a selected list and the reviewer's comments only refine its annotation | 5 |

Wording and options are copied from the document unchanged. The key (`answer_status: author_key`) is the answer each question's author wrote; it has not been audited independently. Some reviewer suggestions are still open in the document, for example making one option of OT-0001 more specific. Treat scores as agreement with this key.

**Clips** (`data/clips_manifest.jsonl`) identify the input video without including it:

```json
{"clip_id": "C11", "file": "C11.mp4",
 "source": {"platform": "youtube", "video_id": "wfG8gRY3T_4", "url": "...", "title": "...", "channel": "...", "start_seconds": 34.1, "end_seconds": 38.2},
 "sha256": "...", "size_bytes": 770607, "caption_kind": "auto", "duration_s": 4.104, "width": 1280, "height": 720, "video_codec": "h264", "video_fps": 29.97,
 "has_audio": true, "audio_codec": "aac", "audio_sample_rate": 48000, "audio_channels": 2}
```

Clips are short cuts of public videos; redistribution rights are unconfirmed, so they stay out of this repository. To rebuild them, take `source.video_id`, `start_seconds` and `end_seconds`. Files you cut yourself will not match `sha256` byte for byte; use `--no-verify-clips` for them, and record that your input differs.

**Subtitles** (`data/subtitles/<clip_id>.txt`) are the YouTube captions in the clip window, with times relative to the clip start. `caption_kind` in the manifest says whether they are `auto`-generated or `manual`. Clip C09 has no captions, so its subtitle file is empty and `subtitles_only` gives that question no extra text. Captions can be wrong.

## Outputs

Each run writes to `outputs/<run_id>/`:

| File | Content |
|---|---|
| `predictions/<model>__<condition>.jsonl` | One record per question: see below |
| `meta_<model>.json` | Model, revision, sampling, engine and media settings, package versions, GPUs, load and decode times, wall time per condition |
| `pip_freeze.txt` | Installed packages at run time |
| `scores.md` | Tables: accuracy, letter distribution, per-question answers |
| `scores.json` | The same in structured form, with a breakdown by `approval` |
| `predictions_flat.csv` | One row per question and condition, without long text |
| `job.log` | Job log with paths and host names removed |

A prediction record holds:

| Field | Meaning |
|---|---|
| `question_id`, `clip_id`, `model`, `hf_id`, `condition` | What was run |
| `user_text`, `chat_text` | The text the model read, and the full chat prompt with media placeholders |
| `sampling` | Generation parameters |
| `media` | Decoded video shape, sampling rate, audio length |
| `prompt_tokens`, `modality_tokens` | Input tokens in total and per modality |
| `interleaving` | For `av_interleaved`, the comparison with the Hugging Face processor |
| `output_text` | Raw model output |
| `thinking_text`, `answer_text`, `think_closed` | For Thinking, the reasoning and the answer after `</think>` |
| `parsed_letter`, `parse_method` | The letter read from the answer; `null` if none could be read |
| `answer`, `answer_status`, `correct` | The answer key and whether the answer agrees with it. Unparsed counts as wrong |
| `output_tokens`, `finish_reason`, `hit_max_tokens` | Length and stop reason |
| `timing`, `error` | Wall time of the batch the request ran in, and any error |

## Extending

**Add a condition.** Add a line to `conditions:` in `configs/baseline.yaml`, for example 32 frames with audio:

```yaml
frames32_audio: {visual: frames, num_frames: 32, audio: separate, subtitles: false}
```

A new way of combining inputs (for example a different frame layout) goes in `src/omnitalk_baseline/conditions.py`, and `expected` must say which modalities should arrive.

**Add a prompt.** Copy a file in `prompts/`, set `prompt_file:` in the config. Templates use `{question}`, `{options}` and `{letters}` (the letters this question allows, such as `A, B, C, D, or E`), filled with plain replacement, so JSON in a prompt is safe.

**Add questions or clips.** Add rows to the two JSONL files in the same format, the clip to the clips directory, and a subtitle file if a condition uses subtitles. Put questions in a subset with `subsets`.

**Add a model.** Add an entry under `models:`. vLLM must support it, and `src/omnitalk_baseline/engine.py` and `media.py` assume the Qwen3-Omni processor and placeholders. Another model family needs a change there.

## Notes from getting this to run

- vLLM starts its workers with `spawn`, so the engine must be built inside `main()`, and `VLLM_WORKER_MULTIPROC_METHOD=spawn` must be set.
- Pass `fps` to the processor. Otherwise it assumes 1.0 while the video was sampled at 2.0, which misaligns interleaved audio.
- Pin `librosa==0.11.0`. Version 1.0 no longer reads the audio object `qwen-omni-utils` passes for audio in video.
- Do not format prompts with `str.format`; prompts that contain braces then fail.
- `max_model_len` cannot exceed the model's `max_position_embeddings` (65536). At 896 x 504 and 2 fps, video costs about 441 tokens per second, so long clips need `video_max_frames`.
