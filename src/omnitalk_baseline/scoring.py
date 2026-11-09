"""Tables over prediction records. "Correct" means agreement with the answer key in data/questions.jsonl."""
from __future__ import annotations

from collections import Counter, defaultdict

UNIMODAL = ("video_only", "audio_only")
PRIMARY = "av_interleaved"


def accuracy_rows(records: list[dict]) -> list[dict]:
    groups = defaultdict(list)
    for r in records:
        groups[(r["model"], r["condition"])].append(r)
    rows = []
    for (model, condition), everything in groups.items():
        group = _answered(everything)
        rows.append({"model": model, "condition": condition, "n": len(group), "request_errors": len(everything) - len(group),
                     "correct": sum(r["correct"] for r in group),
                     "accuracy": round(sum(r["correct"] for r in group) / len(group), 3) if group else None,
                     "unparsed": sum(r.get("parsed_letter") is None for r in group),
                     "hit_max_tokens": sum(bool(r.get("hit_max_tokens")) for r in group),
                     "letters": dict(sorted(Counter(r.get("parsed_letter") or "none" for r in group).items())),
                     "mean_prompt_tokens": round(_mean(r.get("prompt_tokens", 0) for r in group)),
                     "mean_output_tokens": round(_mean(r.get("output_tokens", 0) for r in group))})
    return rows


def breakdown(records: list[dict], questions: dict[str, dict], field: str) -> list[dict]:
    """Accuracy per model, condition and value of a question field such as target or relation."""
    groups = defaultdict(list)
    for r in _answered(records):
        groups[(r["model"], r["condition"], questions[r["question_id"]][field])].append(r["correct"])
    return [{"model": m, "condition": c, field: value, "n": len(hits), "correct": sum(hits)} for (m, c, value), hits in groups.items()]


def item_matrix(records: list[dict], questions: list[dict]) -> dict:
    """model -> question id -> condition -> predicted letter, for the per-question table."""
    matrix: dict = defaultdict(lambda: defaultdict(dict))
    for r in _answered(records):
        matrix[r["model"]][r["question_id"]][r["condition"]] = {"letter": r.get("parsed_letter"), "correct": r["correct"]}
    return {model: {q["question_id"]: dict(by_q.get(q["question_id"], {})) for q in questions} for model, by_q in matrix.items()}


def crossmodal_counts(matrix: dict) -> list[dict]:
    """How often the primary condition is right while each single-modality condition is wrong."""
    rows = []
    for model, by_q in matrix.items():
        complete = {q: conds for q, conds in by_q.items() if PRIMARY in conds and all(u in conds for u in UNIMODAL)}
        rows.append({"model": model, "n": len(complete),
                     "av_right_both_single_wrong": sum(c[PRIMARY]["correct"] and not any(c[u]["correct"] for u in UNIMODAL) for c in complete.values()),
                     "av_wrong_a_single_right": sum(not c[PRIMARY]["correct"] and any(c[u]["correct"] for u in UNIMODAL) for c in complete.values())})
    return rows


def _answered(records: list[dict]) -> list[dict]:
    """Requests that produced output. A request that failed says nothing about the model and is reported separately."""
    return [r for r in records if not r.get("error")]


def _mean(values) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def markdown_report(rows: list[dict], matrix: dict, cross: list[dict], condition_order: list[str]) -> str:
    lines = ["# Scores", "",
             "Accuracy is agreement with the answer key written by the question authors (`answer_status`: `author_key`), which has not been audited independently.", "",
             "## Per model and condition", "",
             "| model | condition | correct / n | request errors | unparsed | hit max tokens | predicted letters | mean input tokens | mean output tokens |",
             "|---|---|---|---|---|---|---|---|---|"]
    order = {c: i for i, c in enumerate(condition_order)}
    for r in sorted(rows, key=lambda x: (x["model"], order.get(x["condition"], 99))):
        letters = " ".join(f"{k}:{v}" for k, v in r["letters"].items())
        lines.append(f"| {r['model']} | {r['condition']} | {r['correct']}/{r['n']} | {r['request_errors']} | {r['unparsed']} | {r['hit_max_tokens']} | {letters} | {r['mean_prompt_tokens']} | {r['mean_output_tokens']} |")
    for model, by_q in matrix.items():
        lines += ["", f"## Per question: {model}", "", "A check mark means the letter agrees with the answer key; `-` means no letter could be parsed.", "",
                  "| question | " + " | ".join(condition_order) + " |", "|---|" + "---|" * len(condition_order)]
        for question, conds in by_q.items():
            cells = []
            for condition in condition_order:
                cell = conds.get(condition)
                cells.append("" if cell is None else f"{cell['letter'] or '-'}{' ✓' if cell['correct'] else ''}")
            lines.append(f"| {question} | " + " | ".join(cells) + " |")
    if cross:
        lines += ["", "## Interleaved audio-video against single modalities", "",
                  f"Compares `{PRIMARY}` with `{UNIMODAL[0]}` and `{UNIMODAL[1]}`.", "",
                  "| model | questions | right with both, wrong with each alone | wrong with both, right with one alone |", "|---|---|---|---|"]
        lines += [f"| {c['model']} | {c['n']} | {c['av_right_both_single_wrong']} | {c['av_wrong_a_single_right']} |" for c in cross]
    return "\n".join(lines) + "\n"
