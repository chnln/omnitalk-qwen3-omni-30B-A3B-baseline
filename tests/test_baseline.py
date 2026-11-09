"""Checks that need no GPU, no weights and no clips."""
import re
import subprocess
from pathlib import Path

import pytest
import yaml

from omnitalk_baseline.conditions import Condition, build_message, build_multi_modal_data, load_conditions
from omnitalk_baseline.data import load_manifest, load_questions
from omnitalk_baseline.engine import compare_interleaving, modality_token_counts, modality_violations
from omnitalk_baseline.parse import parse_letter, split_thinking
from omnitalk_baseline.prompts import Prompts, format_time, render_question
from omnitalk_baseline.scoring import accuracy_rows, crossmodal_counts, item_matrix

ROOT = Path(__file__).resolve().parents[1]
OPTIONS = {"A": "the red cup", "B": "the blue cup", "C": "the bowl", "D": "the plate"}
ITEM = {"question_id": "q1", "question": 'What does "that" mean {here}?', "options": OPTIONS}
PROMPTS = Prompts("Q: {question}\n{options}", "Subs:\n{subtitles}", "Frame at {time}:")


class FakeMedia:
    video = "video-tensor"
    audio = "audio-array"
    sample_fps = 2.0
    frames = {2: [("img0", 0.0), ("img1", 61.0)]}


@pytest.mark.parametrize("text,letter,method", [
    ("A", "A", "bare_letter"), ("(C).", "C", "bare_letter"), ("**B**", "B", "bare_letter"), ("  d", None, "unparsed"),
    ("Answer: C", "C", "explicit"), ("The answer is D.", "D", "explicit"), ("the correct option is (B)", "B", "explicit"),
    ("B. the blue cup", "B", "leading_letter"), ("A man walks in", None, "unparsed"), ("It is the bowl.", "C", "option_text"),
    ("", None, "empty"), (None, None, "empty"),
    ("The answer is B, not option A.", "B", "explicit"), ("B. The blue cup, rather than option A.", "B", "leading_letter"),
    ("Not option A; the answer is C.", "C", "explicit"), ("The answer is a green leaf.", None, "unparsed"),
])
def test_parse_letter(text, letter, method):
    assert parse_letter(text, OPTIONS) == (letter, method)


def test_split_thinking():
    assert split_thinking("<think>\nhmm</think>\n\nB") == {"think_closed": True, "thinking_text": "hmm", "answer_text": "B"}
    assert split_thinking("<think>still going")["answer_text"] is None


def test_render_keeps_braces_in_question():
    assert render_question(PROMPTS.question, ITEM).startswith('Q: What does "that" mean {here}?\nA. the red cup')


def test_format_time():
    assert format_time(61.2) == "01:01"


def test_config_conditions_are_valid():
    config = yaml.safe_load((ROOT / "configs/baseline.yaml").read_text())
    conditions = load_conditions(config)
    assert conditions["video_only"].expected == {"video": True, "image": False, "audio": False}
    assert conditions["question_only"].expected == {"video": False, "image": False, "audio": False}
    assert conditions["frames_audio"].expected == {"video": False, "image": True, "audio": True}


def test_invalid_condition_rejected():
    with pytest.raises(ValueError):
        Condition(name="x", visual="none", audio="interleaved")


def types(message):
    return [part["type"] for part in message[0]["content"]]


def test_interleaved_has_no_audio_item_and_uses_audio_in_video():
    cond = Condition("av", "video", "interleaved")
    message, _ = build_message(cond, ITEM, FakeMedia, PROMPTS, None)
    assert types(message) == ["video", "text"]
    data, kwargs = build_multi_modal_data(cond, FakeMedia, 16000)
    assert data == {"video": "video-tensor", "audio": ("audio-array", 16000)}
    assert kwargs == {"fps": 2.0, "use_audio_in_video": True}


def test_video_only_gets_no_audio():
    cond = Condition("v", "video", "none")
    data, kwargs = build_multi_modal_data(cond, FakeMedia, 16000)
    assert "audio" not in data and kwargs == {"fps": 2.0, "use_audio_in_video": False}


def test_frames_are_captioned_with_their_time():
    cond = Condition("f", "frames", "separate", num_frames=2)
    message, text = build_message(cond, ITEM, FakeMedia, PROMPTS, None)
    assert types(message) == ["text", "image", "text", "image", "audio", "text"]
    assert "Frame at 01:01:" in text
    data, kwargs = build_multi_modal_data(cond, FakeMedia, 16000)
    assert data["image"] == ["img0", "img1"] and kwargs == {"use_audio_in_video": False}


def test_question_only_has_no_media():
    cond = Condition("q", "none", "none")
    message, _ = build_message(cond, ITEM, FakeMedia, PROMPTS, None)
    assert types(message) == ["text"]
    assert build_multi_modal_data(cond, FakeMedia, 16000) == ({}, {})


def test_subtitles_are_required_when_requested():
    with pytest.raises(ValueError):
        build_message(Condition("s", "none", "none", subtitles=True), ITEM, FakeMedia, PROMPTS, None)


def test_data_files_are_consistent():
    questions = load_questions(ROOT / "data/questions.jsonl")
    manifest = load_manifest(ROOT / "data/clips_manifest.jsonl")
    assert {q["clip_id"] for q in questions} == set(manifest)
    for q in questions:
        assert list(q["options"]) == list("ABCD") and q["answer"] in q["options"]
        assert q["answer_status"] == "provisional"
        assert (ROOT / "data/subtitles" / f"{q['clip_id']}.txt").is_file()
    assert sum("smoke" in q["subsets"] for q in questions) == 3
    for entry in manifest.values():
        assert re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]) and entry["has_audio"]
        assert abs(entry["source"]["end_seconds"] - entry["source"]["start_seconds"] - entry["duration_s"]) < 1.0


def test_scoring_counts_unparsed_as_wrong():
    records = [
        dict(model="m", condition="av_interleaved", question_id="q1", correct=True, parsed_letter="A", prompt_tokens=10, output_tokens=1),
        dict(model="m", condition="video_only", question_id="q1", correct=False, parsed_letter=None, prompt_tokens=8, output_tokens=2),
        dict(model="m", condition="audio_only", question_id="q1", correct=False, parsed_letter="B", prompt_tokens=4, output_tokens=1),
    ]
    rows = {r["condition"]: r for r in accuracy_rows(records)}
    assert rows["av_interleaved"]["correct"] == 1 and rows["video_only"]["unparsed"] == 1
    matrix = item_matrix(records, [{"question_id": "q1"}])
    assert crossmodal_counts(matrix)[0]["av_right_both_single_wrong"] == 1


V, A = 1, 2


def tokens(*pattern):
    return [t for token, count in pattern for t in [token] * count]


def test_interleaving_identical():
    ids = tokens((V, 10), (A, 13), (V, 10), (A, 13))
    result = compare_interleaving(ids, list(ids), V, A)
    assert result["identical"] and result["ok"] and result["max_audio_offset_tokens"] == 0


def test_interleaving_one_token_shift_is_tolerated():
    result = compare_interleaving(tokens((V, 10), (A, 14), (V, 10), (A, 12)), tokens((V, 10), (A, 13), (V, 10), (A, 13)), V, A)
    assert not result["identical"] and result["ok"] and result["max_audio_offset_tokens"] == 1


def test_interleaving_extra_audio_at_the_end_is_tolerated():
    result = compare_interleaving(tokens((V, 10), (A, 13), (V, 10), (A, 14)), tokens((V, 10), (A, 13), (V, 10), (A, 13)), V, A)
    assert result["ok"] and result["audio_token_delta"] == 1 and result["max_audio_offset_tokens"] == 0


def test_interleaving_within_half_a_grid_passes_and_beyond_fails():
    reference = tokens((V, 10), (A, 13), (V, 10), (A, 13))
    near = compare_interleaving(tokens((V, 10), (A, 19), (V, 10), (A, 7)), reference, V, A)
    far = compare_interleaving(tokens((V, 10), (A, 26), (V, 10)), reference, V, A)
    assert near["ok"] and near["max_audio_offset_tokens"] == 6
    assert not far["ok"] and far["max_audio_offset_tokens"] == 13


def test_modality_violation_reports_leaked_audio():
    counts = modality_token_counts([7, 7, 8], {"video": 7, "audio": 8, "image": 9})
    assert counts == {"video": 2, "audio": 1, "image": 0}
    assert modality_violations(counts, {"video": True, "audio": False, "image": False}) == ["audio: 1 tokens, expected none"]


def test_failed_requests_are_reported_and_not_scored():
    records = [
        dict(model="m", condition="c", question_id="q1", correct=True, parsed_letter="A", prompt_tokens=10, output_tokens=1, error=None),
        dict(model="m", condition="c", question_id="q2", correct=False, parsed_letter=None, error="boom"),
    ]
    row = accuracy_rows(records)[0]
    assert (row["n"], row["request_errors"], row["correct"]) == (1, 1, 1)
    assert item_matrix(records, [{"question_id": "q2"}, {"question_id": "q1"}])["m"]["q2"] == {}


def test_a_text_condition_needs_no_media_object():
    cond = Condition("q", "none", "none")
    message, _ = build_message(cond, ITEM, None, PROMPTS, None)
    assert types(message) == ["text"] and build_multi_modal_data(cond, None, 16000) == ({}, {})


LOCAL_PATH = re.compile(r"/home/[a-z0-9]+/|/projects/\d+/|/scratch-(?:shared|local)/|/gpfs/|/Users/[A-Za-z0-9]+/|\bprjs\d+\b|\buusei\d+\b")


def test_tracked_files_hold_no_local_paths():
    tracked = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    offenders = []
    for name in tracked:
        path = ROOT / name
        if name == "tests/test_baseline.py" or not path.is_file() or path.stat().st_size > 50_000_000:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if match := LOCAL_PATH.search(text):
            offenders.append(f"{name}: {match.group(0)}")
    assert not offenders, offenders
