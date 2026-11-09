# Scores

Accuracy is agreement with the provisional, model-written answer key, not with human gold.

## Per model and condition

| model | condition | correct / n | request errors | unparsed | hit max tokens | predicted letters | mean input tokens | mean output tokens |
|---|---|---|---|---|---|---|---|---|
| instruct | av_interleaved | 4/12 | 0 | 0 | 0 | A:1 B:7 C:3 D:1 | 16395 | 2 |
| instruct | av_separate | 3/12 | 0 | 0 | 0 | A:1 B:7 C:3 D:1 | 16395 | 2 |
| instruct | video_only | 2/12 | 0 | 0 | 0 | B:2 C:7 D:3 | 15732 | 2 |
| instruct | frames_audio | 5/12 | 0 | 0 | 0 | A:1 B:6 C:3 D:2 | 6017 | 2 |
| instruct | frames_only | 5/12 | 0 | 0 | 0 | A:1 B:2 C:6 D:3 | 5354 | 2 |
| instruct | audio_only | 6/12 | 0 | 0 | 0 | A:1 B:5 C:4 D:2 | 797 | 2 |
| instruct | subtitles_only | 3/12 | 0 | 0 | 0 | B:6 C:5 D:1 | 416 | 2 |
| instruct | question_only | 2/12 | 0 | 0 | 0 | A:1 B:3 C:6 D:2 | 134 | 2 |
| thinking | av_interleaved | 5/12 | 0 | 0 | 0 | B:8 C:3 D:1 | 16395 | 314 |
| thinking | av_separate | 5/12 | 0 | 0 | 0 | A:1 B:6 C:5 | 16395 | 277 |
| thinking | video_only | 2/12 | 0 | 0 | 0 | A:2 B:2 C:5 D:3 | 15732 | 265 |
| thinking | frames_audio | 5/12 | 0 | 0 | 0 | A:1 B:6 C:2 D:3 | 6017 | 326 |
| thinking | frames_only | 3/12 | 0 | 0 | 0 | A:2 B:1 C:4 D:5 | 5354 | 321 |
| thinking | audio_only | 5/12 | 0 | 0 | 0 | B:7 C:3 D:2 | 797 | 340 |
| thinking | subtitles_only | 5/12 | 0 | 0 | 0 | B:6 C:4 D:2 | 416 | 2102 |
| thinking | question_only | 2/12 | 0 | 0 | 0 | B:2 C:8 D:2 | 134 | 1739 |

## Per question: instruct

A check mark means the letter agrees with the provisional key; `-` means no letter could be parsed.

| question | av_interleaved | av_separate | video_only | frames_audio | frames_only | audio_only | subtitles_only | question_only |
|---|---|---|---|---|---|---|---|---|
| nan_002-v3 | B | B | D | B | A ✓ | B | B | B |
| R8-58-v2 | B ✓ | B ✓ | C | B ✓ | C | B ✓ | B ✓ | C |
| R8-17-v2 | D | D | C ✓ | D | C ✓ | D | D | C ✓ |
| R7-02-v2 | B | B | B | B | B | B | B | B |
| nan_022-v3 | B | B | D | B | D | A ✓ | B | D |
| R8-30-v2 | C | C | C | C | C | C | C | C |
| R8-31-v2 | C ✓ | C ✓ | C ✓ | C ✓ | C ✓ | C ✓ | C ✓ | C ✓ |
| R8-36-v3 | B | C | B | D ✓ | D ✓ | C | C | B |
| R8-15-v2 | B | B | C | B | C | B | B | C |
| R8-21-v2 | B ✓ | B ✓ | C | B ✓ | B ✓ | B ✓ | C | C |
| R8-35-v2 | C ✓ | B | D | C ✓ | D | C ✓ | C ✓ | D |
| R7-17-v2 | A | A | C | A | C | D ✓ | B | A |

## Per question: thinking

A check mark means the letter agrees with the provisional key; `-` means no letter could be parsed.

| question | av_interleaved | av_separate | video_only | frames_audio | frames_only | audio_only | subtitles_only | question_only |
|---|---|---|---|---|---|---|---|---|
| nan_002-v3 | B | B | A ✓ | B | A ✓ | B | B | D |
| R8-58-v2 | B ✓ | B ✓ | C | B ✓ | C | B ✓ | B ✓ | C |
| R8-17-v2 | C ✓ | C ✓ | D | D | C ✓ | D | D | C ✓ |
| R7-02-v2 | B | C | C | B | B | B | B | B |
| nan_022-v3 | B | B | B | B | D | B | B | B |
| R8-30-v2 | C | C | C | C | C | C | C | C |
| R8-31-v2 | C ✓ | C ✓ | D | C ✓ | D | C ✓ | C ✓ | C ✓ |
| R8-36-v3 | B | B | B | D ✓ | D ✓ | B | C | C |
| R8-15-v2 | B | B | C | B | D | B | B | C |
| R8-21-v2 | B ✓ | B ✓ | C | B ✓ | C | B ✓ | B ✓ | C |
| R8-35-v2 | B | C ✓ | A | A | D | C ✓ | C ✓ | D |
| R7-17-v2 | D ✓ | A | D ✓ | D ✓ | A | D ✓ | D ✓ | C |

## Interleaved audio-video against single modalities

Compares `av_interleaved` with `video_only` and `audio_only`.

| model | questions | right with both, wrong with each alone | wrong with both, right with one alone |
|---|---|---|---|
| instruct | 12 | 0 | 3 |
| thinking | 12 | 1 | 2 |
