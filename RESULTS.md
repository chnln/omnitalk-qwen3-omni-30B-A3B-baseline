# Results: Qwen3-Omni-30B-A3B on 20 OmniTalk questions

Run `20261109_doc_core`, 2026-11-09. Complete outputs are in [`outputs/20261109_doc_core/`](outputs/20261109_doc_core/).

## Summary

The baseline runs end to end. All 320 requests (20 questions × 8 input conditions × 2 models) finished normally and produced one answer letter each. The job took 21 minutes on two H100 GPUs.

Agreement with the answer key, out of 20. Questions have 4 to 6 options, so picking at random would get about 4 of 20 right.

| Input condition | Instruct | Thinking |
|---|---|---|
| `av_interleaved`: video with interleaved audio | 10 | 10 |
| `av_separate`: video and a separate audio item | 11 | 9 |
| `video_only`: video, no audio | 8 | 11 |
| `frames_audio`: 16 stills and audio | 7 | 9 |
| `frames_only`: 16 stills, no audio | 9 | 7 |
| `audio_only`: audio, no picture | 8 | 4 |
| `subtitles_only`: YouTube captions | 3 | 3 |
| `question_only`: the question alone | 8 | 3 |

**Read these numbers with two limits in mind:**

- **The answer key has not been audited.** Each question's author wrote its answer in the team's annotation document. "Correct" means agreement with that key.
- **There are only 20 questions.** A 95% Wilson interval for 10 of 20 runs from 30% to 70%, and for 3 of 20 from 5% to 36%. Differences of a few questions between conditions are not reliable.

**What the run shows within those limits:**

- **Instruct answers 8 of 20 from the question and options alone.** That is twice the rate of random guessing, and as many as with video alone or audio alone, so the options may give some answers away. Thinking answers 3 of 20 from the question alone, so the rate depends on the model as well as on the questions.
- **Thinking does better with the picture than with the sound.** It gets 11 from video alone and 4 from audio alone. Instruct gets 8 from each.
- **Captions alone are worst for both models** (3 of 20), and for Instruct they do worse than no material at all (8 of 20).
- **Few answers depended on having both modalities.** A question right with interleaved audio and video but wrong with each alone happened twice for each model (`OT-0003` and `OT-0020` for Instruct, `OT-0012` and `OT-0020` for Thinking). The reverse, wrong with both but right with one alone, happened 4 times for Instruct and 5 for Thinking.
- **Interleaving made no visible difference** against a separate audio item (Instruct 10 and 11, Thinking 10 and 9).
- **16 stills with audio came close to video with audio** at about a quarter of the input tokens (Instruct 7 against 10, Thinking 9 against 10; about 7,600 against 29,100 tokens on average).

## Configuration

**Models.** Both from Hugging Face, weights loaded in BF16, audio output not used:

| Model | Hugging Face id | Revision |
|---|---|---|
| `instruct` | `Qwen/Qwen3-Omni-30B-A3B-Instruct` | `26291f793822fb6be9555850f06dfe95f2d7e695` |
| `thinking` | `Qwen/Qwen3-Omni-30B-A3B-Thinking` | `2f443cfc4c54b14a815c0e2bb9a9d6cbcd9a748b` |

**Generation.** The seed is 1234 and `repetition_penalty` is 1.05 for both.

| Model | Temperature | Other | `max_tokens` |
|---|---|---|---|
| `instruct` | 0 (greedy) | | 64 |
| `thinking` | 0.6 | `top_p` 0.95, `top_k` 20 | 8192 |

**Engine.** vLLM 0.33.0 offline inference (`LLM.generate`), tensor parallel size 2, `max_model_len` and `max_num_batched_tokens` 65536 (the model's own limit), `gpu_memory_utilization` 0.85, `mm_processor_cache_gb` 0, requests in batches of 8. Each model ran in its own process.

**Hardware.** Half a GPU node of the Snellius cluster: 2 × NVIDIA H100 (95,830 MiB each), 32 CPU cores, 360 GB of memory.

**Software.** Python 3.12.13, PyTorch 2.14.0 (CUDA 13.0 build), Transformers 5.20.2, qwen-omni-utils 0.0.9, librosa 0.11.0, decord 0.6.0. `requirements.lock.txt` pins all packages and equals `outputs/20261109_doc_core/pip_freeze.txt`.

**Media.** Video decoded with decord at 2 fps up to 240 frames, with `max_pixels` 451,584 (896 × 504) and 16-pixel patches. Four clips are longer than 120 s and reach the frame limit. For `C13`, `C07` and `C05` (129, 135 and 142 s) it lowers the rate to 1.86, 1.77 and 1.69 fps; `C04` (121 s) stays at 1.99 fps. Audio is the clip's own track, mono, 16 kHz. All settings are in `configs/baseline.yaml`.

**Prompt.** [`prompts/mcq_letter_only.txt`](prompts/mcq_letter_only.txt), the same text in every condition; it names the letters of each question's options. Stills are preceded by [`prompts/frame_caption.txt`](prompts/frame_caption.txt) and subtitles by [`prompts/subtitles_block.txt`](prompts/subtitles_block.txt). The full text sent for each request is in the `user_text` and `chat_text` fields of the outputs.

## Inputs

The clips themselves are not in this repository. They are identified by `data/clips_manifest.jsonl` (YouTube id, time window, SHA-256, resolution). The run checked every clip against the SHA-256 before starting.

Twenty questions from the team's annotation document, on 19 clips, 4 to 142 seconds long. `OT-0004` and `OT-0005` share clip `C04`. Options and answers are copied from the document unchanged and are in `data/questions.jsonl`. Questions have 4 to 6 options (3 questions with 4, 12 with 5, 5 with 6). The key letters are B 8 times, D 6, A 3, C 3.

The list favours the questions the benchmark reviewer endorsed most clearly, and covers four question authors. `approval` in the table says how the reviewer treated each one:

- `reviewer_praised` (3): the reviewer called it good
- `reviewer_selected` (9): the reviewer marked it selected or to keep
- `reviewer_written` (3): the reviewer wrote it
- `selected_list` (5): it is on a selected list and the reviewer's comments only refine its annotation

| Question | Clip | Source video | Window (s) | Length (s) | Source size | Frames × decoded size | Approval | Key |
|---|---|---|---|---|---|---|---|---|
| `OT-0001` | C01 | [`BwQ7BaRZGqk`](https://www.youtube.com/watch?v=BwQ7BaRZGqk) | 94.087–203.105 | 109 | 1280×720 | 218 × 896×480 | reviewer_praised | B |
| `OT-0002` | C02 | [`dzX4O9dB17M`](https://www.youtube.com/watch?v=dzX4O9dB17M) | 5.4–28.751 | 23 | 1280×720 | 46 × 896×480 | reviewer_praised | A |
| `OT-0003` | C03 | [`7Gw4BYXpxUM`](https://www.youtube.com/watch?v=7Gw4BYXpxUM) | 118–152 | 34 | 1280×720 | 68 × 896×480 | reviewer_praised | B |
| `OT-0004` | C04 | [`7mzu_UiToiE`](https://www.youtube.com/watch?v=7mzu_UiToiE) | 40.082–160.685 | 121 | 1280×676 | 240 × 896×480 | reviewer_selected | D |
| `OT-0005` | C04 | [`7mzu_UiToiE`](https://www.youtube.com/watch?v=7mzu_UiToiE) | 40.082–160.685 | 121 | 1280×676 | 240 × 896×480 | reviewer_selected | B |
| `OT-0006` | C05 | [`17Drxe_dR8E`](https://www.youtube.com/watch?v=17Drxe_dR8E) | 271.631–413.926 | 142 | 1280×720 | 240 × 896×480 | reviewer_selected | C |
| `OT-0007` | C06 | [`F14Gu6cw86g`](https://www.youtube.com/watch?v=F14Gu6cw86g) | 139.055–248.11 | 109 | 1280×720 | 218 × 896×480 | reviewer_selected | C |
| `OT-0008` | C07 | [`_kAFvpWLb7A`](https://www.youtube.com/watch?v=_kAFvpWLb7A) | 492.081–627.517 | 135 | 1280×720 | 240 × 896×480 | reviewer_selected | D |
| `OT-0009` | C08 | [`_kAFvpWLb7A`](https://www.youtube.com/watch?v=_kAFvpWLb7A) | 321.313–387.079 | 66 | 1280×720 | 130 × 896×480 | reviewer_selected | D |
| `OT-0010` | C09 | [`qNgpeEHdqqA`](https://www.youtube.com/watch?v=qNgpeEHdqqA) | 23.994–45.936 | 22 | 1280×720 | 42 × 896×480 | reviewer_selected | C |
| `OT-0011` | C10 | [`dzX4O9dB17M`](https://www.youtube.com/watch?v=dzX4O9dB17M) | 0–4.3 | 4 | 1280×720 | 8 × 896×480 | reviewer_selected | A |
| `OT-0012` | C11 | [`wfG8gRY3T_4`](https://www.youtube.com/watch?v=wfG8gRY3T_4) | 34.1–38.2 | 4 | 1280×720 | 8 × 896×480 | reviewer_selected | A |
| `OT-0013` | C12 | [`17Drxe_dR8E`](https://www.youtube.com/watch?v=17Drxe_dR8E) | 271–312 | 41 | 1280×720 | 82 × 896×480 | reviewer_written | D |
| `OT-0014` | C13 | [`O3fcjZdPbG8`](https://www.youtube.com/watch?v=O3fcjZdPbG8) | 0–129 | 129 | 1280×720 | 240 × 896×480 | reviewer_written | B |
| `OT-0015` | C14 | [`X4EcUcoo0r4`](https://www.youtube.com/watch?v=X4EcUcoo0r4) | 441–455 | 14 | 1280×720 | 28 × 896×480 | reviewer_written | D |
| `OT-0016` | C15 | [`i28FwwwFiHQ`](https://www.youtube.com/watch?v=i28FwwwFiHQ) | 22.398–85.906 | 64 | 1280×720 | 126 × 896×480 | selected_list | B |
| `OT-0017` | C16 | [`9Ah4tW-k8Ao`](https://www.youtube.com/watch?v=9Ah4tW-k8Ao) | 0–56 | 56 | 960×720 | 110 × 768×576 | selected_list | D |
| `OT-0018` | C17 | [`wXFQ-ibAIIM`](https://www.youtube.com/watch?v=wXFQ-ibAIIM) | 0–68 | 68 | 1280×720 | 136 × 896×480 | selected_list | B |
| `OT-0019` | C18 | [`SNAzY0AleNA`](https://www.youtube.com/watch?v=SNAzY0AleNA) | 5–91 | 86 | 1280×720 | 172 × 896×480 | selected_list | B |
| `OT-0020` | C19 | [`yaSBXuwEZJE`](https://www.youtube.com/watch?v=yaSBXuwEZJE) | 468–508 | 40 | 1280×720 | 80 × 896×480 | selected_list | B |

Question stems:

- `OT-0001`: Why does the man ask for the card back?
- `OT-0002`: At whom does the man yell "shut up"?
- `OT-0003`: Which person-and-response pairing matches the food-ordering exchange?
- `OT-0004`: Why does the woman make a comment about her partner's "massive dumps"?
- `OT-0005`: What does the woman with the camera say is "amazing"?
- `OT-0006`: When the woman says "you use this one", what is she referring to?
- `OT-0007`: Why does the man ask if the woman is hurt?
- `OT-0008`: What does the woman say she would have done herself if the man wasn't there?
- `OT-0009`: What directly prompts the woman to walk outside?
- `OT-0010`: What happens in the video that prompts one of the speakers to exclaim 'boom'?
- `OT-0011`: Who does the speaker think will be better at the game?
- `OT-0012`: Why does the man laugh at the lady's question?
- `OT-0013`: Why does someone in the video ask, “What do you think you're doing?”
- `OT-0014`: Who is the ring in the video actually intended for?
- `OT-0015`: Why did the older woman lower her head?
- `OT-0016`: Who doesn't cook, according to one of the speakers?
- `OT-0017`: Why do the chefs tell Kiki not to take the plate?
- `OT-0018`: Why does someone in the video say, “Be strong”?
- `OT-0019`: Why did the woman in the blue sweater say, “Oh no”?
- `OT-0020`: Why does the boy say “score!”?

Some reviewer suggestions are still open in the document, and the questions are used as they stand there. For example, the reviewer asked for option B of `OT-0001` to be made more specific. Captions are YouTube captions, automatic for 13 clips and manual for 5; `C09` has none, so `subtitles_only` adds no text for `OT-0010`.

**What each condition sent.** Token counts are the range over the 20 questions, from the request's actual token ids.

| Condition | Video | Stills | Audio | Subtitles | Video tokens | Image tokens | Audio tokens | Input tokens in total |
|---|---|---|---|---|---|---|---|---|
| `av_interleaved` | up to 2 fps | | interleaved | | 1,680–50,400 | 0 | 54–1,850 | 1,859–52,369 |
| `av_separate` | up to 2 fps | | separate item | | 1,680–50,400 | 0 | 54–1,850 | 1,859–52,369 |
| `video_only` | up to 2 fps | | | | 1,680–50,400 | 0 | 0 | 1,803–50,558 |
| `frames_audio` | | 16 | separate item | | 0 | 3,360–6,912 | 54–1,850 | 3,625–8,863 |
| `frames_only` | | 16 | | | 0 | 3,360–6,912 | 0 | 3,569–7,256 |
| `audio_only` | | | separate item | | 0 | 0 | 54–1,850 | 177–1,967 |
| `subtitles_only` | | | | yes | 0 | 0 | 0 | 149–715 |
| `question_only` | | | | | 0 | 0 | 0 | 115–194 |

Stills are evenly spaced frames taken from the decoded video, each preceded by its time, such as `Frame at 00:12:`. For the clips of 4 seconds the decoded video has only 8 frames, so 8 stills are sent.

## Outputs

| File | Content |
|---|---|
| [`predictions/<model>__<condition>.jsonl`](outputs/20261109_doc_core/predictions/) | 16 files, 20 records each: full prompt text, raw output, reasoning and answer for Thinking, parsed letter, token counts, stop reason, checks |
| [`scores.md`](outputs/20261109_doc_core/scores.md), [`scores.json`](outputs/20261109_doc_core/scores.json) | Accuracy tables; the JSON adds a breakdown by approval status |
| [`predictions_flat.csv`](outputs/20261109_doc_core/predictions_flat.csv) | One row per request, without long text |
| `meta_instruct.json`, `meta_thinking.json` | Configuration, package versions, GPUs, timing |
| `pip_freeze.txt` | Packages at run time |
| `job.log` | Job log with paths and host names removed |

Field-by-field documentation of the records is in the [README](README.md#outputs).

## Per-question answers

Letter chosen; a check mark means it agrees with the key. The key is in the last column.

**Instruct**

| Question | `av_interleaved` | `av_separate` | `video_only` | `frames_audio` | `frames_only` | `audio_only` | `subtitles_only` | `question_only` | Key |
|---|---|---|---|---|---|---|---|---|---|
| `OT-0001` | E | E | D | E | D | E | E | B ✓ | B |
| `OT-0002` | A ✓ | A ✓ | D | E | E | A ✓ | E | E | A |
| `OT-0003` | B ✓ | B ✓ | D | B ✓ | B ✓ | A | A | B ✓ | B |
| `OT-0004` | A | A | D ✓ | A | D ✓ | D ✓ | A | C | D |
| `OT-0005` | C | C | E | C | F | C | C | F | B |
| `OT-0006` | C ✓ | C ✓ | C ✓ | A | C ✓ | B | E | C ✓ | C |
| `OT-0007` | F | F | C ✓ | F | C ✓ | F | F | B | C |
| `OT-0008` | D ✓ | D ✓ | F | D ✓ | F | D ✓ | C | C | D |
| `OT-0009` | C | C | C | C | B | C | C | B | D |
| `OT-0010` | B | C ✓ | B | C ✓ | B | B | C ✓ | C ✓ | C |
| `OT-0011` | A ✓ | C | A ✓ | C | A ✓ | C | C | B | A |
| `OT-0012` | D | A ✓ | D | D | D | A ✓ | D | A ✓ | A |
| `OT-0013` | D ✓ | D ✓ | D ✓ | D ✓ | D ✓ | D ✓ | D ✓ | D ✓ | D |
| `OT-0014` | B ✓ | B ✓ | B ✓ | B ✓ | B ✓ | B ✓ | B ✓ | B ✓ | B |
| `OT-0015` | A | A | A | A | A | D ✓ | E | A | D |
| `OT-0016` | D | D | D | D | D | C | C | C | B |
| `OT-0017` | D ✓ | D ✓ | D ✓ | D ✓ | D ✓ | D ✓ | B | D ✓ | D |
| `OT-0018` | B ✓ | B ✓ | B ✓ | B ✓ | B ✓ | E | E | E | B |
| `OT-0019` | A | A | A | A | E | A | A | E | B |
| `OT-0020` | B ✓ | B ✓ | D | A | D | A | C | A | B |

**Thinking**

| Question | `av_interleaved` | `av_separate` | `video_only` | `frames_audio` | `frames_only` | `audio_only` | `subtitles_only` | `question_only` | Key |
|---|---|---|---|---|---|---|---|---|---|
| `OT-0001` | E | E | D | E | D | E | E | A | B |
| `OT-0002` | B | C | D | B | D | E | E | E | A |
| `OT-0003` | B ✓ | B ✓ | B ✓ | B ✓ | B ✓ | A | B ✓ | B ✓ | B |
| `OT-0004` | A | A | D ✓ | A | D ✓ | A | A | B | D |
| `OT-0005` | A | C | A | D | D | D | C | F | B |
| `OT-0006` | C ✓ | C ✓ | C ✓ | C ✓ | C ✓ | B | E | B | C |
| `OT-0007` | F | F | C ✓ | F | A | F | D | B | C |
| `OT-0008` | C | F | E | D ✓ | E | C | E | E | D |
| `OT-0009` | B | C | C | C | B | B | C | B | D |
| `OT-0010` | C ✓ | C ✓ | C ✓ | C ✓ | C ✓ | D | A | E | C |
| `OT-0011` | C | C | A ✓ | B | A ✓ | C | C | B | A |
| `OT-0012` | A ✓ | A ✓ | D | D | D | D | D | B | A |
| `OT-0013` | D ✓ | D ✓ | D ✓ | D ✓ | D ✓ | D ✓ | B | D ✓ | D |
| `OT-0014` | B ✓ | B ✓ | B ✓ | B ✓ | A | B ✓ | B ✓ | E | B |
| `OT-0015` | A | A | A | D ✓ | A | D ✓ | D ✓ | E | D |
| `OT-0016` | B ✓ | B ✓ | B ✓ | A | A | C | C | C | B |
| `OT-0017` | D ✓ | D ✓ | F | D ✓ | A | D ✓ | B | D ✓ | D |
| `OT-0018` | B ✓ | B ✓ | B ✓ | B ✓ | B ✓ | E | F | E | B |
| `OT-0019` | A | A | B ✓ | A | E | A | A | E | B |
| `OT-0020` | B ✓ | C | D | D | A | C | C | D | B |

**Things worth noticing**

- `OT-0005` and `OT-0009` are never answered in agreement with the key, by either model in any condition. In `OT-0009` the keyed answer depends on a sound.
- `OT-0003`, `OT-0013` and `OT-0017` are answered correctly from the question alone by both models, so their wording or options may give them away.
- `OT-0020` is the only question both models get right with interleaved audio and video while getting it wrong from audio alone and from video alone.
- `OT-0001`, which the reviewer singled out as a very good question, gets E from both models whenever audio is present (and D from video alone). Instruct's only agreement with the key is from the question alone.

## Checks made during the run

Each request is checked against the token ids vLLM actually produced, and the run stops if a check fails.

- **Modalities.** Every condition had tokens for the modalities it should have and none for those it should not. No request failed this check.
- **Interleaving.** For `av_interleaved`, the position of each audio token was compared with the Hugging Face processor's, by how many audio tokens come before each video token.
  - The largest offset over the 19 clips is 6 tokens (`C07`, 135 s, sampled at 1.77 fps), which equals the limit of 6 tokens (about half a video grid); the next largest are 5 tokens (`C04`), 4 (`C13`) and 3 (`C05`, `C08`).
  - The others are 0 to 2 tokens.
  - The limit dates from the earlier run; it was not changed for this one.
- **Answers.** All 320 outputs stopped normally and parsed as a bare letter that is one of the question's options. All 160 Thinking outputs closed `</think>`. None reached `max_tokens`.

## Time and cost

| Step | Instruct | Thinking |
|---|---|---|
| Decode 19 clips | 24 s | 23 s |
| Load model | 220 s | 356 s |
| Generate 160 requests | 191 s | 390 s |

Generation time is the sum over the 8 conditions, as batches of 8. The whole job took 20 min 38 s, about 132 SBU on the cluster. A 3-question test run before it, including the longest clip, took 10 minutes, about 63 SBU.

## Limitations

- Twenty questions, a single prompt and one seed. Answers can change between runs, especially for Thinking, which samples.
- The answer key was written by the question authors and has not been audited.
- The list was chosen by how strongly the reviewer endorsed the questions, so it is not a random sample of the document.
- The three longest clips are sampled below 2 fps because of the 240-frame limit, and `C07` sits exactly at the interleaving limit.
- Source videos can disappear from YouTube: one question first chosen for this list had to be replaced because its video had been removed.
- `requirements.lock.txt` was exported from the environment that produced these results. It matches the run's `pip_freeze.txt` exactly. A clean install from this file has not been tested separately yet.

## Reproducing this run

See [README.md](README.md). After setup, from the repository root:

```bash
sbatch --partition=<gpu partition> --account=<account> --time=01:45:00 slurm/run_baseline.sbatch core "instruct thinking" 20261109_doc_core
```
