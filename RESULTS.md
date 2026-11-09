# Results: Qwen3-Omni-30B-A3B on 12 OmniTalk questions

Run `20261109_core`, 2026-11-09. Complete outputs are in [`outputs/20261109_core/`](outputs/20261109_core/).

## Summary

The baseline runs end to end. All 192 requests (12 questions × 8 input conditions × 2 models) finished normally and produced one answer letter each. The job took 16 minutes on two H100 GPUs.

Agreement with the provisional answer key, out of 12. Chance is 3 of 12.

| Input condition | Instruct | Thinking |
|---|---|---|
| `av_interleaved`: video with interleaved audio | 4 | 5 |
| `av_separate`: video and a separate audio item | 3 | 5 |
| `video_only`: video, no audio | 2 | 2 |
| `frames_audio`: 16 stills and audio | 5 | 5 |
| `frames_only`: 16 stills, no audio | 5 | 3 |
| `audio_only`: audio, no picture | 6 | 5 |
| `subtitles_only`: auto-generated subtitles | 3 | 5 |
| `question_only`: the question alone | 2 | 2 |

**Read these numbers with two limits in mind:**

- **The answer key is provisional.** A model (Gemini, listening to each clip) wrote the answers. No person has verified them. "Correct" means agreement with that key.
- **There are only 12 questions.** A 95% Wilson interval for 2 of 12 runs from 5% to 45%, and for 6 of 12 from 25% to 75%. No two conditions in the table are reliably different.

**What the run shows within those limits:**

- **Adding the picture to the sound did not help.** Instruct agrees with the key more often from audio alone (6) than from interleaved audio and video (4). Thinking is level (5 and 5).
- **Few answers depended on having both modalities.** A question right with audio and video but wrong with each alone happened 0 times for Instruct and once for Thinking (`R8-17-v2`). Wrong with both but right with one alone happened 3 times for Instruct and 2 for Thinking.
- **Interleaving made no visible difference** against a separate audio item for this task (Instruct 4 and 3, Thinking 5 and 5).
- **16 stills did about as well as 2 fps video** when audio was included, at roughly a third of the input tokens (about 6,000 against 16,400 on average).
- **Questions built on a mismatch between modalities were harder.** With interleaved input, the 5 `contradictory` questions scored 1 of 5 for both models, and the 7 `complementary` ones 3 of 7 (Instruct) and 4 of 7 (Thinking).

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

**Engine.** vLLM 0.33.0 offline inference (`LLM.generate`), tensor parallel size 2, `max_model_len` and `max_num_batched_tokens` 49152, `gpu_memory_utilization` 0.85, `mm_processor_cache_gb` 0, requests in batches of 8. Each model ran in its own process.

**Hardware.** Half a GPU node of the Snellius cluster: 2 × NVIDIA H100 (95,830 MiB each), 32 CPU cores, 360 GB of memory.

**Software.** Python 3.12.13, PyTorch 2.14.0 (CUDA 13.0 build), Transformers 5.20.2, qwen-omni-utils 0.0.9, librosa 0.11.0, decord 0.6.0. `requirements.lock.txt` pins all packages and equals `outputs/20261109_core/pip_freeze.txt`.

**Media.** Video decoded with decord at 2 fps, with `max_pixels` 451,584 (896 × 504) and 16-pixel patches. Audio is the clip's own track, mono, 16 kHz. All settings are in `configs/baseline.yaml`.

**Prompt.** [`prompts/mcq_letter_only.txt`](prompts/mcq_letter_only.txt), the same text in every condition. Stills are preceded by [`prompts/frame_caption.txt`](prompts/frame_caption.txt) and subtitles by [`prompts/subtitles_block.txt`](prompts/subtitles_block.txt). The full text sent for each request is in the `user_text` and `chat_text` fields of the outputs.

## Inputs

The clips themselves are not in this repository. They are identified by `data/clips_manifest.jsonl` (YouTube id, time window, SHA-256, resolution). The run checked every clip against the SHA-256 before starting.

Twelve questions from the OmniTalk drafts, one per clip, 28 to 80 seconds long. Options and answers are in `data/questions.jsonl`. Correct letters are balanced: A, B, C and D three times each.

| Question | Clip | Source video | Window (s) | Length (s) | Source size | Frames × decoded size | Relation | Target | Key |
|---|---|---|---|---|---|---|---|---|---|
| `nan_002-v3` | LR-02 | [`Gehr1AgEF20`](https://www.youtube.com/watch?v=Gehr1AgEF20) | 639–703 | 64 | 854×480 | 128 × 864×480 | complementary | referent | A |
| `R8-58-v2` | R8-58 | [`RNe3uKe7Lm8`](https://www.youtube.com/watch?v=RNe3uKe7Lm8) | 730–775 | 45 | 854×480 | 88 × 864×480 | complementary | intention | B |
| `R8-17-v2` | R8-17 | [`a-e3kdPKEcU`](https://www.youtube.com/watch?v=a-e3kdPKEcU) | 85–128 | 43 | 240×426 | 86 × 288×512 | complementary | prompt_or_cause | C |
| `R7-02-v2` | R7-02 | [`l5Kzc2OBDJE`](https://www.youtube.com/watch?v=l5Kzc2OBDJE) | 805–860 | 55 | 854×480 | 110 × 864×480 | contradictory | prompt_or_cause | D |
| `nan_022-v3` | LR-22 | [`HWHkbeEqaYM`](https://www.youtube.com/watch?v=HWHkbeEqaYM) | 154–182 | 28 | 854×480 | 54 × 864×480 | complementary | prompt_or_cause | A |
| `R8-30-v2` | R8-30 | [`JXfJNFod9wk`](https://www.youtube.com/watch?v=JXfJNFod9wk) | 346–378 | 32 | 854×480 | 64 × 864×480 | contradictory | execution | B |
| `R8-31-v2` | R8-31 | [`b5AufL0DeK0`](https://www.youtube.com/watch?v=b5AufL0DeK0) | 700–742 | 42 | 640×360 | 84 × 640×352 | complementary | belief | C |
| `R8-36-v3` | R8-36 | [`D1W7hKOEY3g`](https://www.youtube.com/watch?v=D1W7hKOEY3g) | 107–157 | 50 | 270×480 | 100 × 288×512 | contradictory | intention | D |
| `R8-15-v2` | R8-15 | [`N482JKTdqkU`](https://www.youtube.com/watch?v=N482JKTdqkU) | 235–305 | 70 | 854×480 | 140 × 864×480 | contradictory | intention | A |
| `R8-21-v2` | R8-21 | [`oiItZVzXjKM`](https://www.youtube.com/watch?v=oiItZVzXjKM) | 115–195 | 80 | 640×360 | 158 × 640×352 | contradictory | stance | B |
| `R8-35-v2` | R8-35 | [`vm_3VykE_A8`](https://www.youtube.com/watch?v=vm_3VykE_A8) | 468–504 | 36 | 854×480 | 72 × 864×480 | complementary | addressee | C |
| `R7-17-v2` | R7-17 | [`ckP9ywG-B_U`](https://www.youtube.com/watch?v=ckP9ywG-B_U) | 145–210 | 65 | 640×360 | 130 × 640×352 | complementary | referent | D |

Question stems:

- `nan_002-v3`: When the seated man asks "Did I tell you to do that?", what does "that" refer to?
- `R8-58-v2`: When the man asks "Or do I go like this?", what is he proposing?
- `R8-17-v2`: What prompts the man in the blue shirt to say 'Oops'?
- `R7-02-v2`: What prompts the person filming to shout 'Oh!' near the stove?
- `nan_022-v3`: What directly prompts the driver of the red car to shout "Oh, you pillock!"?
- `R8-30-v2`: How is the child's request for blue carried out?
- `R8-31-v2`: When the man says 'It's the mirror image', what is he explaining?
- `R8-36-v3`: Why does the child take a bowl after the adult says 'Those are clean'?
- `R8-15-v2`: Why does the older woman step away from the kitchen island?
- `R8-21-v2`: When the speaker off camera says 'That's great, AJ. Good for you, honey!', what attitude is being expressed?
- `R8-35-v2`: Who or what is the man addressing when he says, "Shut up"?
- `R7-17-v2`: When someone asks "Wait, take that off?", what does "that" refer to?

The first three questions were accepted in an author review of the question wording; the other nine have not been reviewed. Subtitles are YouTube auto-captions, except for one hand-added line in R8-17 ("Oops. Daddy did that wrong."), because the caption cue fell after the end of the shortened clip.

**What each condition sent.** Token counts are the range over the 12 questions, from the request's actual token ids.

| Condition | Video | Stills | Audio | Subtitles | Video tokens | Image tokens | Audio tokens | Input tokens in total |
|---|---|---|---|---|---|---|---|---|
| `av_interleaved` | 2 fps | | interleaved | | 6,192–28,350 | 0 | 365–1,040 | 6,892–29,392 |
| `av_separate` | 2 fps | | separate item | | 6,192–28,350 | 0 | 365–1,040 | 6,892–29,392 |
| `video_only` | 2 fps | | | | 6,192–28,350 | 0 | 0 | 6,330–28,479 |
| `frames_audio` | | 16 | separate item | | 0 | 2,304–6,480 | 365–1,040 | 3,178–7,696 |
| `frames_only` | | 16 | | | 0 | 2,304–6,480 | 0 | 2,608–6,800 |
| `audio_only` | | | separate item | | 0 | 0 | 365–1,040 | 511–1,181 |
| `subtitles_only` | | | | yes | 0 | 0 | 0 | 211–718 |
| `question_only` | | | | | 0 | 0 | 0 | 122–145 |

Stills are evenly spaced frames taken from the decoded video, each preceded by its time, such as `Frame at 00:12:`. Portrait clips are enlarged slightly by the model's image processing (240×426 to 288×512).

## Outputs

| File | Content |
|---|---|
| [`predictions/<model>__<condition>.jsonl`](outputs/20261109_core/predictions/) | 16 files, 12 records each: full prompt text, raw output, reasoning and answer for Thinking, parsed letter, token counts, stop reason, checks |
| [`scores.md`](outputs/20261109_core/scores.md), [`scores.json`](outputs/20261109_core/scores.json) | Accuracy tables; the JSON adds breakdowns by relation, target and review status |
| [`predictions_flat.csv`](outputs/20261109_core/predictions_flat.csv) | One row per request, without long text |
| `meta_instruct.json`, `meta_thinking.json` | Configuration, package versions, GPUs, timing |
| `pip_freeze.txt` | Packages at run time |
| `job.log` | Job log with paths and host names removed |

Field-by-field documentation of the records is in the [README](README.md#outputs).

## Per-question answers

Letter chosen; a check mark means it agrees with the provisional key. The key is in the last column.

**Instruct**

| Question | `av_interleaved` | `av_separate` | `video_only` | `frames_audio` | `frames_only` | `audio_only` | `subtitles_only` | `question_only` | Key |
|---|---|---|---|---|---|---|---|---|---|
| `nan_002-v3` | B | B | D | B | A ✓ | B | B | B | A |
| `R8-58-v2` | B ✓ | B ✓ | C | B ✓ | C | B ✓ | B ✓ | C | B |
| `R8-17-v2` | D | D | C ✓ | D | C ✓ | D | D | C ✓ | C |
| `R7-02-v2` | B | B | B | B | B | B | B | B | D |
| `nan_022-v3` | B | B | D | B | D | A ✓ | B | D | A |
| `R8-30-v2` | C | C | C | C | C | C | C | C | B |
| `R8-31-v2` | C ✓ | C ✓ | C ✓ | C ✓ | C ✓ | C ✓ | C ✓ | C ✓ | C |
| `R8-36-v3` | B | C | B | D ✓ | D ✓ | C | C | B | D |
| `R8-15-v2` | B | B | C | B | C | B | B | C | A |
| `R8-21-v2` | B ✓ | B ✓ | C | B ✓ | B ✓ | B ✓ | C | C | B |
| `R8-35-v2` | C ✓ | B | D | C ✓ | D | C ✓ | C ✓ | D | C |
| `R7-17-v2` | A | A | C | A | C | D ✓ | B | A | D |

**Thinking**

| Question | `av_interleaved` | `av_separate` | `video_only` | `frames_audio` | `frames_only` | `audio_only` | `subtitles_only` | `question_only` | Key |
|---|---|---|---|---|---|---|---|---|---|
| `nan_002-v3` | B | B | A ✓ | B | A ✓ | B | B | D | A |
| `R8-58-v2` | B ✓ | B ✓ | C | B ✓ | C | B ✓ | B ✓ | C | B |
| `R8-17-v2` | C ✓ | C ✓ | D | D | C ✓ | D | D | C ✓ | C |
| `R7-02-v2` | B | C | C | B | B | B | B | B | D |
| `nan_022-v3` | B | B | B | B | D | B | B | B | A |
| `R8-30-v2` | C | C | C | C | C | C | C | C | B |
| `R8-31-v2` | C ✓ | C ✓ | D | C ✓ | D | C ✓ | C ✓ | C ✓ | C |
| `R8-36-v3` | B | B | B | D ✓ | D ✓ | B | C | C | D |
| `R8-15-v2` | B | B | C | B | D | B | B | C | A |
| `R8-21-v2` | B ✓ | B ✓ | C | B ✓ | C | B ✓ | B ✓ | C | B |
| `R8-35-v2` | B | C ✓ | A | A | D | C ✓ | C ✓ | D | C |
| `R7-17-v2` | D ✓ | A | D ✓ | D ✓ | A | D ✓ | D ✓ | C | D |

**Things worth noticing**

- `R8-31-v2` is answered correctly from the question alone by both models, so the question text or options may give it away.
- `R8-30-v2` gets C ("dipped into blue dye", the literal request) in all 16 runs, while the key is purple. This question tests whether speech was carried out as asked.
- With audio present, models lean to B: Instruct 7 of 12 and Thinking 8 of 12 in `av_interleaved`. The key is balanced, so this bias cannot raise the score.

**Reasoning, from Thinking's output (not checked against the video):** in `nan_002-v3`, with interleaved input, the reasoning quotes the seated man's speech with times close to the auto-captions, follows the repeated "turn the chili peppers", and picks B without using the visible action that the key relies on. In `R8-17-v2` the same condition cites both speech and picture and picks the keyed answer. The questions in this set are designed so that speech alone can mislead. The first example fits that pattern, but two examples show no more than that.

## Checks made during the run

Each request is checked against the token ids vLLM actually produced, and the run stops if a check fails.

- **Modalities.** Every condition had tokens for the modalities it should have and none for those it should not. For example, `video_only` had 0 audio tokens in all 24 of its requests. No request failed this check.
- **Interleaving.** For `av_interleaved`, the position of each audio token was compared with the Hugging Face processor's, by how many audio tokens come before each video token.
  - 7 clips had an offset of 0 tokens, 4 clips 1 token, and R8-21 (80 s) 3 tokens, about 0.23 s.
  - Offsets above 0 appear only for clips with a source frame rate of 23.976 or 29.97 fps. Clips at 25 or 30 fps have an offset of 0.
  - The limit is 6 tokens, about half a video grid. An earlier limit of 2 tokens, set before any data existed, stopped the job on R8-21; it was then raised to this value and the run was repeated.
- **Answers.** All 192 outputs stopped normally and parsed as a single letter. All 96 Thinking outputs closed `</think>`. None reached `max_tokens`.

## Time and cost

| Step | Instruct | Thinking |
|---|---|---|
| Decode 12 clips | 17 s | 14 s |
| Load model | 246 s | 371 s |
| Generate 96 requests | 85 s | 205 s |

Generation time is the sum over the 8 conditions, as batches of 8. The whole job took 16 min 13 s, 104 SBU on the cluster. Two earlier attempts cost another 95 SBU: both stopped at the interleaving check described above.

## Limitations

- Twelve questions, a single prompt and one seed. Answers can change between runs, especially for Thinking, which samples.
- The answer key has not been verified by a person. The model that wrote it heard the audio; the key may be wrong in places.
- The questions were screened using other models' single-modality tests, so this is not a random sample of the question drafts.
- Results use the source video's frame rate and low resolution as they are (up to 864×480 after decoding).
- `requirements.lock.txt` was exported from the environment that produced these results. It matches the run's `pip_freeze.txt` exactly. A clean install from this file has not been tested separately yet.

## Reproducing this run

See [README.md](README.md). After setup, from the repository root:

```bash
sbatch --partition=<gpu partition> --account=<account> --time=01:30:00 slurm/run_baseline.sbatch core "instruct thinking" 20261109_core
```
