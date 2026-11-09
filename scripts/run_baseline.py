#!/usr/bin/env python3
"""Run one model over the question list under each input condition.

One process per model (vLLM does not release the GPUs cleanly). Writes one JSONL file per condition under
<output-dir>/predictions and meta_<model>.json. Exit code 3 means a check on the prompt failed: a modality that
should be absent reached the model, or the interleaving differs from the Hugging Face processor.
"""
import argparse
import json
import os
import platform
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from omnitalk_baseline.conditions import build_message, build_multi_modal_data, load_conditions  # noqa: E402
from omnitalk_baseline.data import load_manifest, load_questions, load_subtitles, resolve_clip  # noqa: E402
from omnitalk_baseline.engine import (compare_interleaving, generate, load_engine, modality_token_counts,  # noqa: E402
                                      modality_violations, reference_input_ids)
from omnitalk_baseline.media import decode_clip  # noqa: E402
from omnitalk_baseline.parse import parse_letter, split_thinking  # noqa: E402
from omnitalk_baseline.prompts import load_prompts  # noqa: E402

GATE_FAILED = 3


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", required=True, help="a key under models: in the config")
    p.add_argument("--output-dir", required=True, type=Path)
    p.add_argument("--config", type=Path, default=ROOT / "configs/baseline.yaml")
    p.add_argument("--questions", type=Path, default=ROOT / "data/questions.jsonl")
    p.add_argument("--manifest", type=Path, default=ROOT / "data/clips_manifest.jsonl")
    p.add_argument("--subtitles-dir", type=Path, default=ROOT / "data/subtitles")
    p.add_argument("--clips-dir", type=Path, default=Path(os.environ.get("OMNITALK_CLIPS_DIR", ROOT / "data/clips")))
    p.add_argument("--subset", default=None, help="only questions in this subset (for example smoke or core)")
    p.add_argument("--question-ids", default="", help="comma-separated question ids")
    p.add_argument("--conditions", default="", help="comma-separated condition names; default all, in config order")
    p.add_argument("--no-verify-clips", action="store_true", help="skip the SHA-256 check, for clips you cut yourself")
    return p.parse_args()


def package_versions() -> dict:
    from importlib.metadata import version

    return {name: version(name) for name in ("vllm", "torch", "transformers", "qwen-omni-utils", "librosa", "decord")}


def write_package_list(path: Path) -> None:
    from importlib.metadata import distributions

    path.write_text("\n".join(sorted(f"{d.metadata['Name']}=={d.version}" for d in distributions())) + "\n", encoding="utf-8")


def gpu_names() -> list[str]:
    import torch

    return [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]


def main():
    args = parse_args()
    config = yaml.safe_load(args.config.read_text())
    model_cfg = config["models"][args.model]
    conditions = load_conditions(config)
    if args.conditions:
        conditions = {name: conditions[name] for name in args.conditions.split(",")}
    prompts = load_prompts(ROOT / config["prompt_file"])
    questions = load_questions(args.questions, args.subset, set(filter(None, args.question_ids.split(","))) or None)
    manifest = load_manifest(args.manifest)
    clip_paths = {q["clip_id"]: resolve_clip(manifest[q["clip_id"]], args.clips_dir, verify=not args.no_verify_clips) for q in questions}
    subtitles = {q["clip_id"]: load_subtitles(args.subtitles_dir, q["clip_id"]) for q in questions}
    pred_dir = args.output_dir / "predictions"
    pred_dir.mkdir(parents=True, exist_ok=True)
    write_package_list(args.output_dir / "pip_freeze.txt")

    sample_rate = config["media"]["audio_sample_rate"]
    frame_counts = {c.num_frames for c in conditions.values() if c.num_frames}
    meta = {"model": args.model, "hf_id": model_cfg["hf_id"], "revision": model_cfg["revision"], "config_file": args.config.name,
            "prompt_file": config["prompt_file"], "subset": args.subset, "n_questions": len(questions), "conditions": list(conditions),
            "sampling": model_cfg["sampling"], "seed": config["seed"], "engine": config["engine"], "media": config["media"],
            "slurm_job_id": os.environ.get("SLURM_JOB_ID"), "python": platform.python_version(), "packages": package_versions(),
            "gpus": gpu_names(), "started": time.strftime("%Y-%m-%d %H:%M:%S"), "groups": []}
    meta_path = args.output_dir / f"meta_{args.model}.json"

    def save_meta():
        meta_path.write_text(json.dumps(meta, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    t0 = time.time()
    media = {cid: decode_clip(path, config["media"], frame_counts) for cid, path in clip_paths.items()}
    meta["media_decode_s"] = round(time.time() - t0, 1)
    print(f"decoded {len(media)} clips in {meta['media_decode_s']} s", flush=True)

    t0 = time.time()
    mm_limits = {"video": 1, "audio": 1, "image": max(frame_counts, default=0)}
    llm, processor, pad_ids = load_engine(model_cfg, config["engine"], mm_limits, config["seed"])
    from vllm import SamplingParams

    meta["model_load_s"] = round(time.time() - t0, 1)
    print(f"loaded {model_cfg['hf_id']} in {meta['model_load_s']} s", flush=True)
    save_meta()

    sampling = dict(model_cfg["sampling"], seed=config["seed"])
    is_thinking = "thinking" in model_cfg["hf_id"].lower()
    references: dict[str, list[int]] = {}
    gate_errors: list[str] = []

    for name, cond in conditions.items():
        requests, records = [], []
        for q in questions:
            message, text = build_message(cond, q, media[q["clip_id"]], prompts, subtitles[q["clip_id"]])
            chat = processor.apply_chat_template(message, add_generation_prompt=True, tokenize=False)
            data, kwargs = build_multi_modal_data(cond, media[q["clip_id"]], sample_rate)
            request = {"prompt": chat}
            if data:
                request["multi_modal_data"] = data
                request["mm_processor_kwargs"] = kwargs
            requests.append(request)
            records.append({"question_id": q["question_id"], "clip_id": q["clip_id"], "model": args.model, "hf_id": model_cfg["hf_id"],
                            "condition": name, "user_text": text, "chat_text": chat, "sampling": sampling,
                            "media": media[q["clip_id"]].info() if (cond.visual != "none" or cond.audio != "none") else None,
                            "answer": q["answer"], "answer_status": q["answer_status"]})
        size = config["batch_size"]
        print(f"=== {args.model} / {name}: {len(requests)} requests, {time.strftime('%H:%M:%S')}", flush=True)
        group_start = time.time()
        with open(pred_dir / f"{args.model}__{name}.jsonl", "w", encoding="utf-8") as f:
            for i in range(0, len(requests), size):
                batch_requests, batch_records = requests[i:i + size], records[i:i + size]
                results = generate(llm, batch_requests, [SamplingParams(**sampling)] * len(batch_requests))
                for question_i, (record, (output, wall, batch, error)) in enumerate(zip(batch_records, results), start=i):
                    question = questions[question_i]
                    record.update(timing={"batch_wall_s": round(wall, 1), "batch_size": batch}, error=error)
                    if output is None:
                        record.update(parsed_letter=None, parse_method="error", correct=False)
                        f.write(json.dumps(record, ensure_ascii=False) + "\n")
                        continue
                    ids = list(output.prompt_token_ids or [])
                    completion = output.outputs[0]
                    counts = modality_token_counts(ids, pad_ids)
                    problems = modality_violations(counts, cond.expected)
                    if cond.audio == "interleaved":
                        clip = question["clip_id"]
                        if clip not in references:
                            references[clip] = reference_input_ids(processor, record["chat_text"], media[clip])
                        check = compare_interleaving(ids, references[clip], pad_ids["video"], pad_ids["audio"])
                        record["interleaving"] = check
                        if not check["ok"] or check["n_audio_runs"] < 2:
                            problems.append(f"interleaving differs from the Hugging Face processor: {check}")
                    if problems:
                        gate_errors += [f"{name}/{record['question_id']}: {p}" for p in problems]
                    raw = completion.text
                    thinking = split_thinking(raw) if is_thinking else {}
                    answer_text = thinking["answer_text"] if is_thinking else raw
                    letter, method = parse_letter(answer_text, question["options"])
                    record.update(thinking)
                    record.update(prompt_tokens=len(ids), modality_tokens=counts, output_tokens=len(completion.token_ids),
                                  finish_reason=completion.finish_reason, hit_max_tokens=len(completion.token_ids) >= sampling["max_tokens"],
                                  output_text=raw, parsed_letter=letter, parse_method=method, correct=letter == question["answer"],
                                  gate_problems=problems)
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                f.flush()
        meta["groups"].append({"condition": name, "n": len(requests), "wall_s": round(time.time() - group_start, 1)})
        save_meta()
        if gate_errors:
            meta["gate_errors"] = gate_errors
            save_meta()
            print("GATE FAILED:\n" + "\n".join(gate_errors), flush=True)
            sys.exit(GATE_FAILED)
    meta["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
    save_meta()


if __name__ == "__main__":
    main()
