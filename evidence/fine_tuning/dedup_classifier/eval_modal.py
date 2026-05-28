"""Evaluate fine-tuned dedup classifier on golden eval set via Modal.

Loads the LoRA adapter from the Modal volume, runs inference on the 65
golden eval cases, and outputs a predictions JSONL compatible with
dedup_score.py.

Usage:
    # Run eval on Modal, download predictions, score locally:
    modal run evidence/fine_tuning/dedup_classifier/eval_modal.py \
        --run-name qwen1b_run1

    # Then score with existing eval pipeline:
    poetry run python -m evaluation.experiments.dedup_score \
        --dataset eval_sets/dedup_ft_predictions.jsonl \
        --golden eval_sets/dedup_v2_golden_labels.json
"""

from __future__ import annotations

import json
import re
import modal

MINUTES = 60

app = modal.App("dedup-classifier-eval")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "torch==2.6.0",
        "transformers>=4.51",
        "peft>=0.15",
        "accelerate>=1.4",
        "bitsandbytes>=0.45",
        "huggingface_hub",
    )
)

vol = modal.Volume.from_name("dedup-finetune-output")


@app.function(
    image=image,
    gpu="T4",
    timeout=30 * MINUTES,
    secrets=[modal.Secret.from_name("huggingface")],
    volumes={"/output": vol},
)
def run_eval(
    eval_cases_json: str,
    run_name: str = "qwen1b_run1",
    base_model: str = "Qwen/Qwen2.5-1.5B-Instruct",
    max_new_tokens: int = 256,
) -> str:
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from peft import PeftModel
    import torch
    import os

    lora_path = f"/output/{run_name}/lora_adapter"
    if not os.path.exists(lora_path):
        available = os.listdir("/output")
        raise FileNotFoundError(
            f"Adapter not found at {lora_path}. Available runs: {available}"
        )

    print(f"Loading base model: {base_model}")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        quantization_config=bnb_config,
        device_map="auto",
        dtype=torch.bfloat16,
    )
    tokenizer = AutoTokenizer.from_pretrained(base_model)

    print(f"Loading LoRA adapter: {lora_path}")
    model = PeftModel.from_pretrained(model, lora_path)
    model.eval()

    cases = json.loads(eval_cases_json)
    print(f"Running inference on {len(cases)} cases...")

    results = []
    for i, case in enumerate(cases):
        prompt = case["prompt"]
        messages = [{"role": "user", "content": prompt}]
        template_kwargs = dict(tokenize=False, add_generation_prompt=True)
        try:
            text = tokenizer.apply_chat_template(
                messages, **template_kwargs, enable_thinking=False,
            )
        except TypeError:
            text = tokenizer.apply_chat_template(messages, **template_kwargs)
        inputs = tokenizer(text, return_tensors="pt").to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                temperature=None,
                top_p=None,
            )

        response = tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:],
            skip_special_tokens=True,
        ).strip()

        decision_match = re.search(r"DECISION:\s*([DKMdkm])", response)
        decision = decision_match.group(1).upper() if decision_match else "?"

        results.append({
            "case_index": case["case_index"],
            "case_id": case["case_id"],
            "item_type": case["item_type"],
            "decision": decision,
            "raw_response": response,
        })

        if (i + 1) % 10 == 0:
            print(f"  {i + 1}/{len(cases)} done")

    print(f"Inference complete. Decisions: {dict(__import__('collections').Counter(r['decision'] for r in results))}")
    return json.dumps(results)


@app.local_entrypoint()
def main(
    run_name: str = "qwen1b_run1",
    base_model: str = "Qwen/Qwen2.5-1.5B-Instruct",
    source: str = "eval_sets/dedup_v2_sampled.jsonl",
    output: str = "eval_sets/dedup_ft_predictions.jsonl",
):
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path.cwd()))
    from evaluation.data.datasets import read_dedup_dataset
    from Agents.prompts.dedup import OBSERVATION_DEDUP_PROMPT, STRATEGY_DEDUP_PROMPT
    from Agents.prompts.standards import EPISTEMIC_STATUS_RULE, SITUATION_STANDARDS

    records = read_dedup_dataset(Path(source))
    print(f"Loaded {len(records)} eval cases from {source}")

    def format_candidates_strategy(candidates):
        lines = []
        for c in candidates:
            lines.append(
                f"[{c.candidate_number}] Candidate: {c.candidate_number}; "
                f"Key: {c.key} "
                f"(similarity={c.similarity:.3f}, observed={c.observation_count}x)\n"
                f"    Action: {c.action or ''}\n"
                f"    Situation: {c.situation}"
            )
        return "\n\n".join(lines)

    def format_candidates_observation(candidates):
        lines = []
        for c in candidates:
            lines.append(
                f"[{c.candidate_number}] Candidate: {c.candidate_number}; "
                f"Key: {c.key} "
                f"(similarity={c.similarity:.3f}, observed={c.observation_count}x)\n"
                f"    Situation: {c.situation}\n"
                f"    Approach: {c.approach or ''}\n"
                f"    Outcome: {c.outcome or ''}"
            )
        return "\n\n".join(lines)

    eval_cases = []
    for idx, record in enumerate(records):
        case = record.dedup_case
        entry = case.new_entry

        if case.item_type == "observation":
            prompt = OBSERVATION_DEDUP_PROMPT.format(
                new_role=case.perspective,
                new_situation=entry.get("situation", ""),
                new_approach=entry.get("approach", ""),
                new_outcome=entry.get("outcome", ""),
                total_similar_count=len(case.candidates),
                top_n=len(case.candidates),
                existing_entries=format_candidates_observation(case.candidates),
            )
        else:
            prompt = STRATEGY_DEDUP_PROMPT.format(
                situation_standards=SITUATION_STANDARDS,
                epistemic_status_rule=EPISTEMIC_STATUS_RULE,
                new_role=case.perspective,
                new_situation=entry.get("situation", ""),
                new_action=entry.get("action", ""),
                total_similar_count=len(case.candidates),
                top_n=len(case.candidates),
                existing_entries=format_candidates_strategy(case.candidates),
            )

        eval_cases.append({
            "case_index": idx,
            "case_id": record.case_id,
            "item_type": case.item_type,
            "prompt": prompt,
        })

    print(f"Sending {len(eval_cases)} cases to Modal for inference...")
    results_json = run_eval.remote(
        eval_cases_json=json.dumps(eval_cases),
        run_name=run_name,
        base_model=base_model,
    )

    results = json.loads(results_json)

    out_path = Path(output)
    with out_path.open("w") as f:
        for idx, record in enumerate(records):
            case = record.dedup_case
            r = results[idx]

            replayed_record = {
                "eval_set_id": f"dedup_ft_{run_name}",
                "case_id": record.case_id,
                "trace_id": record.trace_id,
                "observation_id": record.observation_id,
                "span_name": record.span_name,
                "game_id": case.game_id,
                "item_type": case.item_type,
                "perspective": case.perspective,
                "action_phase": case.action_phase,
                "decision": r["decision"],
                "auto": record.auto,
                "dedup_case": {
                    **case.model_dump(mode="json"),
                    "decision": r["decision"],
                    "decision_detail": {"raw_response": r["raw_response"]},
                },
            }
            f.write(json.dumps(replayed_record) + "\n")

    from collections import Counter
    decisions = Counter(r["decision"] for r in results)
    print(f"\nPredictions written to {out_path}")
    print(f"Decision distribution: {dict(decisions)}")
    print(f"\nScore with:")
    print(f"  poetry run python -m evaluation.experiments.dedup_score \\")
    print(f"      --dataset {out_path} \\")
    print(f"      --golden eval_sets/dedup_v2_golden_labels.json")
