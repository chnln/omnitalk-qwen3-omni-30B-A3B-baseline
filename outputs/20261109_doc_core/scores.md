# Scores

Accuracy is agreement with the answer key written by the question authors (`answer_status`: `author_key`), which has not been audited independently.

## Per model and condition

| model | condition | correct / n | request errors | unparsed | hit max tokens | predicted letters | mean input tokens | mean output tokens |
|---|---|---|---|---|---|---|---|---|
| instruct | av_interleaved | 10/20 | 0 | 0 | 0 | A:5 B:5 C:3 D:5 E:1 F:1 | 29138 | 2 |
| instruct | av_separate | 11/20 | 0 | 0 | 0 | A:5 B:4 C:5 D:4 E:1 F:1 | 29138 | 2 |
| instruct | video_only | 8/20 | 0 | 0 | 0 | A:3 B:3 C:3 D:9 E:1 F:1 | 28233 | 2 |
| instruct | frames_audio | 7/20 | 0 | 0 | 0 | A:5 B:3 C:4 D:5 E:2 F:1 | 7607 | 2 |
| instruct | frames_only | 9/20 | 0 | 0 | 0 | A:2 B:5 C:2 D:7 E:2 F:2 | 6703 | 2 |
| instruct | audio_only | 8/20 | 0 | 0 | 0 | A:5 B:3 C:4 D:5 E:2 F:1 | 1046 | 2 |
| instruct | subtitles_only | 3/20 | 0 | 0 | 0 | A:3 B:2 C:7 D:2 E:5 F:1 | 424 | 2 |
| instruct | question_only | 8/20 | 0 | 0 | 0 | A:3 B:6 C:5 D:2 E:3 F:1 | 142 | 2 |
| thinking | av_interleaved | 10/20 | 0 | 0 | 0 | A:5 B:7 C:4 D:2 E:1 F:1 | 29138 | 343 |
| thinking | av_separate | 9/20 | 0 | 0 | 0 | A:4 B:4 C:7 D:2 E:1 F:2 | 29138 | 295 |
| thinking | video_only | 11/20 | 0 | 0 | 0 | A:3 B:5 C:4 D:6 E:1 F:1 | 28233 | 304 |
| thinking | frames_audio | 9/20 | 0 | 0 | 0 | A:3 B:5 C:3 D:7 E:1 F:1 | 7607 | 328 |
| thinking | frames_only | 7/20 | 0 | 0 | 0 | A:7 B:3 C:2 D:6 E:2 | 6703 | 300 |
| thinking | audio_only | 4/20 | 0 | 0 | 0 | A:3 B:3 C:4 D:6 E:3 F:1 | 1046 | 343 |
| thinking | subtitles_only | 3/20 | 0 | 0 | 0 | A:3 B:4 C:5 D:3 E:4 F:1 | 424 | 2704 |
| thinking | question_only | 3/20 | 0 | 0 | 0 | A:1 B:7 C:1 D:3 E:7 F:1 | 142 | 1940 |

## Per question: instruct

A check mark means the letter agrees with the answer key; `-` means no letter could be parsed.

| question | av_interleaved | av_separate | video_only | frames_audio | frames_only | audio_only | subtitles_only | question_only |
|---|---|---|---|---|---|---|---|---|
| OT-0001 | E | E | D | E | D | E | E | B ✓ |
| OT-0002 | A ✓ | A ✓ | D | E | E | A ✓ | E | E |
| OT-0003 | B ✓ | B ✓ | D | B ✓ | B ✓ | A | A | B ✓ |
| OT-0004 | A | A | D ✓ | A | D ✓ | D ✓ | A | C |
| OT-0005 | C | C | E | C | F | C | C | F |
| OT-0006 | C ✓ | C ✓ | C ✓ | A | C ✓ | B | E | C ✓ |
| OT-0007 | F | F | C ✓ | F | C ✓ | F | F | B |
| OT-0008 | D ✓ | D ✓ | F | D ✓ | F | D ✓ | C | C |
| OT-0009 | C | C | C | C | B | C | C | B |
| OT-0010 | B | C ✓ | B | C ✓ | B | B | C ✓ | C ✓ |
| OT-0011 | A ✓ | C | A ✓ | C | A ✓ | C | C | B |
| OT-0012 | D | A ✓ | D | D | D | A ✓ | D | A ✓ |
| OT-0013 | D ✓ | D ✓ | D ✓ | D ✓ | D ✓ | D ✓ | D ✓ | D ✓ |
| OT-0014 | B ✓ | B ✓ | B ✓ | B ✓ | B ✓ | B ✓ | B ✓ | B ✓ |
| OT-0015 | A | A | A | A | A | D ✓ | E | A |
| OT-0016 | D | D | D | D | D | C | C | C |
| OT-0017 | D ✓ | D ✓ | D ✓ | D ✓ | D ✓ | D ✓ | B | D ✓ |
| OT-0018 | B ✓ | B ✓ | B ✓ | B ✓ | B ✓ | E | E | E |
| OT-0019 | A | A | A | A | E | A | A | E |
| OT-0020 | B ✓ | B ✓ | D | A | D | A | C | A |

## Per question: thinking

A check mark means the letter agrees with the answer key; `-` means no letter could be parsed.

| question | av_interleaved | av_separate | video_only | frames_audio | frames_only | audio_only | subtitles_only | question_only |
|---|---|---|---|---|---|---|---|---|
| OT-0001 | E | E | D | E | D | E | E | A |
| OT-0002 | B | C | D | B | D | E | E | E |
| OT-0003 | B ✓ | B ✓ | B ✓ | B ✓ | B ✓ | A | B ✓ | B ✓ |
| OT-0004 | A | A | D ✓ | A | D ✓ | A | A | B |
| OT-0005 | A | C | A | D | D | D | C | F |
| OT-0006 | C ✓ | C ✓ | C ✓ | C ✓ | C ✓ | B | E | B |
| OT-0007 | F | F | C ✓ | F | A | F | D | B |
| OT-0008 | C | F | E | D ✓ | E | C | E | E |
| OT-0009 | B | C | C | C | B | B | C | B |
| OT-0010 | C ✓ | C ✓ | C ✓ | C ✓ | C ✓ | D | A | E |
| OT-0011 | C | C | A ✓ | B | A ✓ | C | C | B |
| OT-0012 | A ✓ | A ✓ | D | D | D | D | D | B |
| OT-0013 | D ✓ | D ✓ | D ✓ | D ✓ | D ✓ | D ✓ | B | D ✓ |
| OT-0014 | B ✓ | B ✓ | B ✓ | B ✓ | A | B ✓ | B ✓ | E |
| OT-0015 | A | A | A | D ✓ | A | D ✓ | D ✓ | E |
| OT-0016 | B ✓ | B ✓ | B ✓ | A | A | C | C | C |
| OT-0017 | D ✓ | D ✓ | F | D ✓ | A | D ✓ | B | D ✓ |
| OT-0018 | B ✓ | B ✓ | B ✓ | B ✓ | B ✓ | E | F | E |
| OT-0019 | A | A | B ✓ | A | E | A | A | E |
| OT-0020 | B ✓ | C | D | D | A | C | C | D |

## Interleaved audio-video against single modalities

Compares `av_interleaved` with `video_only` and `audio_only`.

| model | questions | right with both, wrong with each alone | wrong with both, right with one alone |
|---|---|---|---|
| instruct | 20 | 2 | 4 |
| thinking | 20 | 2 | 5 |
