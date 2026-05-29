"""Build SFT dataset for dedup classifier fine-tuning.

Assembles all 863 labeled cases into chat-format training examples:
- system: dedup prompt instructions
- user: new entry + candidates (formatted exactly as inference)
- assistant: DECISION + REASONING

Reasoning sources:
- Cases where our label matches flash-3.5: use flash-3.5's reasoning
- Cases where our label differs + detailed colabeling reasoning: use ours
- Cases where our label differs + terse colabeling reasoning (80 hard cases):
  generate fresh reasoning via LLM

Adds metadata: difficulty tier (1-5), item_type, case_index.

Usage:
    # Generate reasoning for 80 hard cases (needs Vertex AI credentials):
    poetry run python evidence/fine_tuning/dedup_classifier/build_sft_dataset.py --generate-reasoning

    # Build dataset (assumes reasoning already generated):
    poetry run python evidence/fine_tuning/dedup_classifier/build_sft_dataset.py --build
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

DIR = Path(__file__).parent

STRATEGY_DEDUP_PROMPT = None
OBSERVATION_DEDUP_PROMPT = None
SITUATION_STANDARDS = None
EPISTEMIC_STATUS_RULE = None


def _load_prompts():
    global STRATEGY_DEDUP_PROMPT, OBSERVATION_DEDUP_PROMPT
    global SITUATION_STANDARDS, EPISTEMIC_STATUS_RULE
    from Agents.prompts.dedup import (
        STRATEGY_DEDUP_PROMPT as _s,
        OBSERVATION_DEDUP_PROMPT as _o,
    )
    from Agents.prompts.standards import (
        SITUATION_STANDARDS as _ss,
        EPISTEMIC_STATUS_RULE as _er,
    )
    STRATEGY_DEDUP_PROMPT = _s
    OBSERVATION_DEDUP_PROMPT = _o
    SITUATION_STANDARDS = _ss
    EPISTEMIC_STATUS_RULE = _er


def _load_data():
    agreed = [json.loads(l) for l in (DIR / "agreed_labels.jsonl").read_text().splitlines() if l.strip()]
    disagreed = [json.loads(l) for l in (DIR / "disagreed_labels.jsonl").read_text().splitlines() if l.strip()]
    colab = [json.loads(l) for l in (DIR / "colabeling_log.jsonl").read_text().splitlines() if l.strip()]
    return agreed, disagreed, colab


def _format_strategy_entries(candidates: list) -> str:
    lines = []
    for c in candidates:
        lines.append(
            f"[{c['candidate_number']}] Candidate: {c['candidate_number']}; "
            f"Key: {c['key']} "
            f"(similarity={c['similarity']:.3f}, observed={c.get('observation_count', 1)}x)\n"
            f"    Action: {c.get('action', '')}\n"
            f"    Situation: {c.get('situation', '')}"
        )
    return "\n\n".join(lines)


def _format_observation_entries(candidates: list) -> str:
    lines = []
    for c in candidates:
        lines.append(
            f"[{c['candidate_number']}] Candidate: {c['candidate_number']}; "
            f"Key: {c['key']} "
            f"(similarity={c['similarity']:.3f}, observed={c.get('observation_count', 1)}x)\n"
            f"    Situation: {c.get('situation', '')}\n"
            f"    Approach: {c.get('approach', '')}\n"
            f"    Outcome: {c.get('outcome', '')}"
        )
    return "\n\n".join(lines)


def format_prompt(case: dict) -> str:
    _load_prompts()
    ne = case["new_entry"]
    candidates = case["candidates"]

    if case["item_type"] == "strategy_point":
        return STRATEGY_DEDUP_PROMPT.format(
            situation_standards=SITUATION_STANDARDS,
            epistemic_status_rule=EPISTEMIC_STATUS_RULE,
            new_role=case["perspective"],
            new_situation=ne["situation"],
            new_action=ne["action"],
            total_similar_count=len(candidates),
            top_n=len(candidates),
            existing_entries=_format_strategy_entries(candidates),
        )
    else:
        return OBSERVATION_DEDUP_PROMPT.format(
            new_role=case["perspective"],
            new_situation=ne["situation"],
            new_approach=ne["approach"],
            new_outcome=ne["outcome"],
            total_similar_count=len(candidates),
            top_n=len(candidates),
            existing_entries=_format_observation_entries(candidates),
        )


def format_assistant_output(label: str, reasoning: str, candidates: list | None = None, decision_only: bool = False) -> str:
    if decision_only:
        return label
    if label == "D":
        out = f"DECISION: D\nREASONING: {reasoning}"
        if candidates:
            top = candidates[0]
            out += f"\nDuplicate of candidate: C{top['candidate_number']}"
        return out
    return f"DECISION: K\nREASONING: {reasoning}"


def _find_best_duplicate_candidate(case: dict) -> int:
    return case["candidates"][0]["candidate_number"]


def generate_reasoning_for_hard_cases():
    """Generate reasoning for the 80 hard cases using flash-2.5 via Vertex AI."""
    from Agents.llm_factory import create_chat_model

    agreed, disagreed, colab = _load_data()
    all_cases_by_idx = {a["case_index"]: a for a in agreed}
    all_cases_by_idx.update({d["case_index"]: d for d in disagreed})

    hard_cases = []
    for rec in colab:
        idx = rec["case_index"]
        src = all_cases_by_idx.get(idx)
        if not src:
            continue
        flash35 = src["model_decisions"]["gemini-3.5-flash"]["decision"]
        if flash35 != rec["label"] and len(rec.get("reasoning", "")) <= 50:
            hard_cases.append((rec, src))

    print(f"Found {len(hard_cases)} hard cases needing reasoning generation")

    _load_prompts()
    model = create_chat_model("gemini-3.1-flash-lite", thinking_level="medium")

    output_path = DIR / "generated_reasoning.jsonl"
    existing = {}
    if output_path.exists():
        for line in output_path.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                existing[r["case_index"]] = r
        print(f"  {len(existing)} already generated, skipping those")

    with open(output_path, "a") as f:
        for i, (rec, src) in enumerate(hard_cases):
            if rec["case_index"] in existing:
                continue

            prompt_text = format_prompt(src)

            label_word = "KEEP (K)" if rec["label"] == "K" else "DISCARD (D)"
            if rec["label"] == "K":
                criteria_hint = (
                    "referencing the specific criteria from the prompt (different situation, "
                    "different action direction, different approach, opposite outcome, etc.). "
                    "Be specific about what differs between the new entry and the top candidate."
                )
            else:
                criteria_hint = (
                    "referencing the specific criteria from the prompt (same situation AND same "
                    "action direction, same approach AND same outcome). "
                    "Be specific about what matches between the new entry and the top candidate."
                )

            meta_prompt = (
                f"You are reviewing a dedup decision. The correct answer for this case is {label_word}.\n\n"
                f"Given the dedup prompt and case below, write 2-3 sentences explaining WHY this case "
                f"should be {label_word}, {criteria_hint}\n\n"
                "Output ONLY the reasoning sentences, nothing else.\n\n"
                f"--- DEDUP PROMPT AND CASE ---\n{prompt_text}"
            )

            try:
                response = model.invoke(meta_prompt)
                content = response.content
                if isinstance(content, list):
                    reasoning = "".join(
                        block["text"] for block in content if block.get("type") == "text"
                    ).strip()
                else:
                    reasoning = content.strip()
            except Exception as e:
                print(f"  Error on case {rec['case_index']}: {e}")
                time.sleep(5)
                continue

            result = {"case_index": rec["case_index"], "reasoning": reasoning}
            f.write(json.dumps(result) + "\n")
            f.flush()

            if (i + 1) % 10 == 0:
                print(f"  Generated {i + 1}/{len(hard_cases)}")
            time.sleep(0.5)

    print(f"Done. Reasoning saved to {output_path}")


def build_dataset(decision_only: bool = False):
    """Assemble the full SFT dataset from all labeled cases."""
    _load_prompts()
    agreed, disagreed, colab = _load_data()

    agreed_by_idx = {a["case_index"]: a for a in agreed}
    disagreed_by_idx = {d["case_index"]: d for d in disagreed}

    gen_reasoning_path = DIR / "generated_reasoning.jsonl"
    generated = {}
    if gen_reasoning_path.exists():
        for line in gen_reasoning_path.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                generated[r["case_index"]] = r["reasoning"]

    examples = []

    for rec in colab:
        idx = rec["case_index"]
        src = agreed_by_idx.get(idx) or disagreed_by_idx.get(idx)
        if not src:
            print(f"Warning: no source data for case_index {idx}")
            continue

        prompt_text = format_prompt(src)
        label = rec["label"]
        difficulty = rec.get("difficulty", 3)

        flash35 = src["model_decisions"]["gemini-3.5-flash"]
        if flash35["decision"] == label:
            reasoning = flash35["reasoning"]
        elif idx in generated:
            reasoning = generated[idx]
        elif len(rec.get("reasoning", "")) > 50:
            reasoning = rec["reasoning"]
        else:
            print(f"Warning: no usable reasoning for case {idx} (terse: '{rec.get('reasoning', '')}')")
            continue

        assistant_output = format_assistant_output(label, reasoning, src["candidates"] if label == "D" else None, decision_only=decision_only)

        examples.append({
            "messages": [
                {"role": "user", "content": prompt_text},
                {"role": "assistant", "content": assistant_output},
            ],
            "metadata": {
                "case_index": idx,
                "item_type": src["item_type"],
                "difficulty": difficulty,
                "perspective": src.get("perspective", ""),
                "action_phase": src.get("action_phase", ""),
            },
        })

    # Add unanimous-K cases (not in colabeling log)
    colab_indices = {r["case_index"] for r in colab}
    for case in agreed:
        if case["case_index"] in colab_indices:
            continue
        if case["agreement"] != "unanimous" or case["label"] != "K":
            continue

        prompt_text = format_prompt(case)
        reasoning = case["model_decisions"]["gemini-3.5-flash"]["reasoning"]
        assistant_output = format_assistant_output("K", reasoning, decision_only=decision_only)

        examples.append({
            "messages": [
                {"role": "user", "content": prompt_text},
                {"role": "assistant", "content": assistant_output},
            ],
            "metadata": {
                "case_index": case["case_index"],
                "item_type": case["item_type"],
                "difficulty": 5,
                "perspective": case.get("perspective", ""),
                "action_phase": case.get("action_phase", ""),
            },
        })

    suffix = "_decision_only" if decision_only else ""
    output_path = DIR / f"sft_dataset{suffix}.jsonl"
    with open(output_path, "w") as f:
        for ex in examples:
            f.write(json.dumps(ex) + "\n")

    from collections import Counter
    tiers = Counter(ex["metadata"]["difficulty"] for ex in examples)
    labels = Counter(
        "D" if ex["messages"][1]["content"].strip().startswith("D") else "K"
        for ex in examples
    )
    types = Counter(ex["metadata"]["item_type"] for ex in examples)

    print(f"SFT dataset: {len(examples)} examples → {output_path}")
    print(f"  Labels: {dict(labels)}")
    print(f"  Types: {dict(types)}")
    print(f"  Difficulty tiers: {dict(sorted(tiers.items()))}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--generate-reasoning", action="store_true")
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--decision-only", action="store_true",
                        help="Assistant output is just D or K (no reasoning)")
    args = parser.parse_args()

    if args.generate_reasoning:
        generate_reasoning_for_hard_cases()
    if args.build:
        build_dataset(decision_only=args.decision_only)
    if not args.generate_reasoning and not args.build:
        parser.print_help()
