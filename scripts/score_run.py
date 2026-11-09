#!/usr/bin/env python3
"""Score one run directory: writes scores.json, scores.md and predictions_flat.csv next to predictions/."""
import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from omnitalk_baseline.data import load_questions, read_jsonl  # noqa: E402
from omnitalk_baseline.scoring import accuracy_rows, breakdown, crossmodal_counts, item_matrix, markdown_report  # noqa: E402

FLAT_FIELDS = ("model", "condition", "question_id", "clip_id", "answer", "parsed_letter", "parse_method", "correct", "prompt_tokens",
               "output_tokens", "finish_reason", "hit_max_tokens", "think_closed", "error")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", required=True, type=Path)
    p.add_argument("--questions", type=Path, default=ROOT / "data/questions.jsonl")
    args = p.parse_args()

    records = [r for path in sorted((args.run / "predictions").glob("*.jsonl")) for r in read_jsonl(path)]
    if not records:
        sys.exit(f"no predictions under {args.run}")
    used = {r["question_id"] for r in records}
    questions = [q for q in load_questions(args.questions) if q["question_id"] in used]
    by_id = {q["question_id"]: q for q in questions}
    conditions = list(dict.fromkeys(r["condition"] for path in sorted((args.run / "predictions").glob("*.jsonl")) for r in read_jsonl(path)[:1]))
    meta_files = sorted(args.run.glob("meta_*.json"))
    if meta_files:
        declared = json.loads(meta_files[0].read_text())["conditions"]
        conditions = [c for c in declared if c in conditions] + [c for c in conditions if c not in declared]

    rows, matrix = accuracy_rows(records), item_matrix(records, questions)
    cross = crossmodal_counts(matrix)
    scores = {"note": "Accuracy is agreement with the provisional, model-written answer key.", "per_condition": rows,
              "by_relation": breakdown(records, by_id, "relation"), "by_target": breakdown(records, by_id, "target"),
              "by_question_review": breakdown(records, by_id, "question_review"), "crossmodal": cross, "per_question": matrix}
    (args.run / "scores.json").write_text(json.dumps(scores, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (args.run / "scores.md").write_text(markdown_report(rows, matrix, cross, conditions), encoding="utf-8")
    with open(args.run / "predictions_flat.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FLAT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    print(f"{len(records)} records scored in {args.run}")


if __name__ == "__main__":
    main()
