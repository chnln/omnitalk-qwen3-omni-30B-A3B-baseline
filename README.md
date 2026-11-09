# OmniTalk baseline: Qwen3-Omni-30B-A3B

A runnable baseline for OmniTalk, a benchmark of multiple-choice questions about short video clips of people interacting. A question is meant to need speech and what is visible (or audible beyond speech) to be understood together.

This repository runs `Qwen/Qwen3-Omni-30B-A3B-Instruct` and `-Thinking` with [vLLM](https://github.com/vllm-project/vllm) offline inference, under several input conditions (audio and video interleaved, video without audio, video split into frames, and so on), and scores the answers.

Results of the reference run, with its configuration, inputs and outputs: **[RESULTS.md](RESULTS.md)**.

## Contents

| Path | What it holds |
|---|---|
| `configs/baseline.yaml` | Models, sampling, engine settings, media settings, and the input conditions |
| `prompts/` | Prompt templates |
| `data/questions.jsonl` | The questions, options and provisional answers |
| `data/clips_manifest.jsonl` | Which clip each question uses: source video, time window, SHA-256, resolution |
| `data/subtitles/` | Auto-generated subtitles for the subtitle conditions |
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
- About 186 GiB of GPU memory across two GPUs. The reference run used 2 × NVIDIA H100 (93 GiB each), 32 CPU cores, one half node
- `ffmpeg` on `PATH`, used to read the audio track of an mp4
- About 130 GB of disk for the two checkpoints

## Setup

**1. Environment.** `requirements.lock.txt` pins all 216 packages of the environment behind RESULTS.md (vLLM 0.33.0, PyTorch 2.14.0 with CUDA 13, Transformers 5.20.2, qwen-omni-utils 0.0.9, librosa 0.11.0).

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.lock.txt
```

On a SLURM cluster, `slurm/build_env.sbatch` does the same in a job. Compiling and installing need no GPU.

**2. Weights.** Download the two checkpoints into your Hugging Face cache. The config pins the revisions used for RESULTS.md; the snapshot downloaded must match them, or change `revision:` in the config.

```bash
huggingface-cli download Qwen/Qwen3-Omni-30B-A3B-Instruct --revision 26291f793822fb6be9555850f06dfe95f2d7e695
huggingface-cli download Qwen/Qwen3-Omni-30B-A3B-Thinking --revision 2f443cfc4c54b14a815c0e2bb9a9d6cbcd9a748b
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
SUBSET=smoke MODELS=instruct RUN_ID=smoke sbatch --partition=<gpu partition> --account=<account> --time=00:45:00 slurm/run_baseline.sbatch
sbatch --partition=<gpu partition> --account=<account> slurm/run_baseline.sbatch
```

`SUBSET` selects questions (`smoke` has 3, `core` has 12). `MODELS` is a space-separated list of keys under `models:`. `CONDITIONS` limits conditions (comma-separated). `RUN_ID` names the output directory. Each model loads once, which takes about 5 to 13 minutes; the 96 requests per model then take a few minutes.

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

The run checks each request's actual token ids before accepting it. It stops with exit code 3 if a modality that should be absent reached the model, or if the interleaving pattern differs from the Hugging Face processor's.

## Inputs

**Questions** (`data/questions.jsonl`, one JSON object per line):

```json
{"question_id": "R8-17-v2", "clip_id": "R8-17",
 "question": "What prompts the man in the blue shirt to say 'Oops'?",
 "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
 "answer": "C", "answer_status": "provisional", "question_review": "accepted_by_author",
 "relation": "complementary", "target": "prompt_or_cause", "subsets": ["smoke", "core"]}
```

`relation` says how the modalities relate (`complementary` or `contradictory`). `target` is what the question asks about (referent, intention, execution, and so on).

Answers are `provisional`: a model wrote them while listening to the clip, and no person has verified them. Treat scores as agreement with this key.

**Clips** (`data/clips_manifest.jsonl`) identify the input video without including it:

```json
{"clip_id": "R8-17", "file": "R8-17.mp4",
 "source": {"platform": "youtube", "video_id": "a-e3kdPKEcU", "url": "...", "title": "...", "start_seconds": 85.0, "end_seconds": 128.0},
 "sha256": "...", "size_bytes": 2637891, "duration_s": 43.0, "width": 240, "height": 426, "video_codec": "h264", "video_fps": 30.0,
 "has_audio": true, "audio_codec": "aac", "audio_sample_rate": 48000, "audio_channels": 2}
```

Clips are short cuts of public videos; redistribution rights are unconfirmed, so they stay out of this repository. To rebuild them, take `source.video_id`, `start_seconds` and `end_seconds`. Files you cut yourself will not match `sha256` byte for byte; use `--no-verify-clips` for them, and record that your input differs.

**Subtitles** (`data/subtitles/<clip_id>.txt`) are YouTube auto-captions in the clip window, with times relative to the clip start. They can be wrong.

## Outputs

Each run writes to `outputs/<run_id>/`:

| File | Content |
|---|---|
| `predictions/<model>__<condition>.jsonl` | One record per question: see below |
| `meta_<model>.json` | Model, revision, sampling, engine and media settings, package versions, GPUs, load and decode times, wall time per condition |
| `pip_freeze.txt` | Installed packages at run time |
| `scores.md` | Tables: accuracy, letter distribution, per-question answers |
| `scores.json` | The same in structured form, with breakdowns by relation and target |
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
| `answer`, `answer_status`, `correct` | The provisional key and whether the answer agrees with it. Unparsed counts as wrong |
| `output_tokens`, `finish_reason`, `hit_max_tokens` | Length and stop reason |
| `timing`, `error` | Wall time of the batch the request ran in, and any error |

## Extending

**Add a condition.** Add a line to `conditions:` in `configs/baseline.yaml`, for example 32 frames with audio:

```yaml
frames32_audio: {visual: frames, num_frames: 32, audio: separate, subtitles: false}
```

A new way of combining inputs (for example a different frame layout) goes in `src/omnitalk_baseline/conditions.py`, and `expected` must say which modalities should arrive.

**Add a prompt.** Copy a file in `prompts/`, set `prompt_file:` in the config. Templates use `{question}` and `{options}`, filled with plain replacement, so JSON in a prompt is safe.

**Add questions or clips.** Add rows to the two JSONL files in the same format, the clip to the clips directory, and a subtitle file if a condition uses subtitles. Put questions in a subset with `subsets`.

**Add a model.** Add an entry under `models:`. vLLM must support it, and `src/omnitalk_baseline/engine.py` and `media.py` assume the Qwen3-Omni processor and placeholders. Another model family needs a change there.

## Notes from getting this to run

- vLLM starts its workers with `spawn`, so the engine must be built inside `main()`, and `VLLM_WORKER_MULTIPROC_METHOD=spawn` must be set.
- Pass `fps` to the processor. Otherwise it assumes 1.0 while the video was sampled at 2.0, which misaligns interleaved audio.
- Pin `librosa==0.11.0`. Version 1.0 no longer reads the audio object `qwen-omni-utils` passes for audio in video.
- Do not format prompts with `str.format`; prompts that contain braces then fail.
