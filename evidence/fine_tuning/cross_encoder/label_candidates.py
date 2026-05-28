"""Label retrieval candidates using multi-model consensus.

For each (golden_situation, memory_text) pair, asks multiple Gemini models
to rate relevance on a 0/1/2 scale. Outputs per-model scores and a consensus
label for easy disagreement analysis.

Usage:
    # Trial run: label 3 cases to spot-check model agreement
    poetry run python evidence/fine_tuning/cross_encoder/label_candidates.py \
        --trial --trial-cases 3

    # Full run: label all cases
    poetry run python evidence/fine_tuning/cross_encoder/label_candidates.py

    # Resume from a partial run
    poetry run python evidence/fine_tuning/cross_encoder/label_candidates.py \
        --resume
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from collections import Counter

REPO_ROOT = Path(__file__).resolve().parents[3]
CANDIDATES_PATH = (
    REPO_ROOT / "evidence" / "fine_tuning" / "cross_encoder"
    / "candidates_for_labeling.json"
)
OUTPUT_DIR = REPO_ROOT / "evidence" / "fine_tuning" / "cross_encoder"

LABEL_PROMPT = """\
You are labeling retrieval results for a werewolf social deduction game's episodic memory system.

A player in a specific game situation is retrieving past experiences from memory. Rate how relevant each retrieved memory is to the player's current situation.

## Current situation (the retrieval query)
{golden_situation}

## Retrieved memory
{memory_text}

## Relevance scale
- **2** = Highly relevant: The memory directly addresses the same game dynamic, information landscape, or strategic challenge. A player in the current situation would clearly benefit from recalling this.
- **1** = Partially relevant: The memory is related (similar role, similar phase, overlapping themes) but addresses a different angle, specificity level, or game phase. Useful background but not a direct match.
- **0** = Not relevant: The memory describes a fundamentally different situation. Recalling it would not help the player.

## Key factors to consider
- Does the memory address the same type of strategic challenge (e.g., analyzing voting records, navigating information-starved situations, managing role exposure)?
- Is the game phase comparable (early vs mid vs endgame)?
- Does the memory involve the same role dynamics?
- Would recalling this memory actually help the player decide what to do?

Respond with ONLY a single digit: 0, 1, or 2."""


def _format_memory_text(item: dict, mem_type: str) -> str:
    if mem_type == "observation":
        parts = [f"Situation: {item['situation']}"]
        if item.get("approach"):
            parts.append(f"Approach: {item['approach']}")
        if item.get("outcome"):
            parts.append(f"Outcome: {item['outcome']}")
        return " | ".join(parts)
    else:
        return f"Situation: {item['situation']} | Action: {item['action']}"


THINKING_MODELS = {"gemini-3.1-flash-lite", "gemini-2.5-flash", "gemini-2.5-pro"}


def _extract_text(content) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        texts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                texts.append(block["text"])
            elif isinstance(block, str):
                texts.append(block)
        return " ".join(texts).strip()
    return str(content).strip()


def _call_model(model_name: str, prompt: str, max_retries: int = 3) -> int | None:
    from Agents.llm_factory import create_chat_model

    kwargs = {}
    if model_name in THINKING_MODELS:
        kwargs["thinking_level"] = "medium"

    for attempt in range(max_retries):
        try:
            llm = create_chat_model(model_name, temperature=0.0, **kwargs)
            response = llm.invoke(prompt)
            text = _extract_text(response.content)
            for char in text:
                if char in "012":
                    return int(char)
            print(f"    WARNING: {model_name} returned unparseable: {text!r}")
            return None
        except Exception as e:
            if attempt < max_retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"    Retry {attempt + 1} for {model_name}: {e}")
                time.sleep(wait)
            else:
                print(f"    FAILED {model_name}: {e}")
                return None
    return None


def _compute_consensus(scores: dict[str, int | None]) -> dict:
    valid = {k: v for k, v in scores.items() if v is not None}
    if not valid:
        return {"label": None, "confidence": "no_response", "scores": scores}

    values = list(valid.values())
    if len(set(values)) == 1:
        return {"label": values[0], "confidence": "unanimous", "scores": scores}

    counter = Counter(values)
    majority_label, majority_count = counter.most_common(1)[0]
    if majority_count >= 2:
        return {"label": majority_label, "confidence": "majority", "scores": scores}

    return {"label": round(sum(values) / len(values)), "confidence": "split", "scores": scores}


def label_all(
    candidates_path: Path,
    models: list[str],
    output_path: Path,
    trial_cases: int | None = None,
    resume: bool = False,
):
    with open(candidates_path) as f:
        data = json.load(f)

    cases = data["cases"]
    if trial_cases:
        cases = cases[:trial_cases]

    existing_labels = {}
    if resume and output_path.exists():
        with open(output_path) as f:
            existing = json.load(f)
        for case in existing.get("cases", []):
            for item in case.get("observation_labels", []) + case.get("strategy_labels", []):
                existing_labels[f"{case['case_index']}:{item['key']}"] = item
        print(f"Resuming: {len(existing_labels)} items already labeled")

    results = []
    total_items = 0
    total_unanimous = 0
    total_majority = 0
    total_split = 0

    for case in cases:
        case_idx = case["case_index"]
        golden_sits = case["golden_situations"]
        query = "\n".join(golden_sits)

        obs_labels = []
        sp_labels = []

        items_to_label = []
        for obs in case["retrieved_observations"]:
            items_to_label.append(("observation", obs))
        for sp in case["retrieved_strategy_points"]:
            items_to_label.append(("strategy_point", sp))

        print(f"\nCase {case_idx} ({case['player_role']} {case['action_phase']}): "
              f"{len(items_to_label)} items")

        for mem_type, item in items_to_label:
            item_key = f"{case_idx}:{item['key']}"

            if item_key in existing_labels:
                entry = existing_labels[item_key]
                if mem_type == "observation":
                    obs_labels.append(entry)
                else:
                    sp_labels.append(entry)
                total_items += 1
                continue

            memory_text = _format_memory_text(item, mem_type)
            prompt = LABEL_PROMPT.format(
                golden_situation=query,
                memory_text=memory_text,
            )

            scores = {}
            for model in models:
                score = _call_model(model, prompt)
                scores[model] = score
                time.sleep(0.3)

            consensus = _compute_consensus(scores)
            total_items += 1
            if consensus["confidence"] == "unanimous":
                total_unanimous += 1
            elif consensus["confidence"] == "majority":
                total_majority += 1
            elif consensus["confidence"] == "split":
                total_split += 1

            entry = {
                "key": item["key"],
                "relevance": consensus["label"],
                "score": item["score"],
                "situation": item["situation"],
                "model_scores": consensus["scores"],
                "confidence": consensus["confidence"],
            }
            if mem_type == "observation":
                entry["approach"] = item.get("approach", "")
                entry["outcome"] = item.get("outcome", "")
                obs_labels.append(entry)
            else:
                entry["action"] = item.get("action", "")
                sp_labels.append(entry)

            label_char = str(consensus["label"]) if consensus["label"] is not None else "?"
            conf_char = consensus["confidence"][0].upper()
            model_strs = " ".join(
                f"{m.split('-')[-1]}={s}" for m, s in scores.items()
            )
            print(f"  [{label_char}]{conf_char} {model_strs} | {item['situation'][:70]}...")

        results.append({
            "case_index": case_idx,
            "case_id": case["case_id"],
            "player_role": case["player_role"],
            "day": case["day"],
            "round": case["round"],
            "action_phase": case["action_phase"],
            "golden_situations": golden_sits,
            "observation_labels": obs_labels,
            "strategy_labels": sp_labels,
        })

    output = {
        "description": "Multi-model consensus labels for retrieval candidates",
        "models": models,
        "stats": {
            "total_items": total_items,
            "unanimous": total_unanimous,
            "majority": total_majority,
            "split": total_split,
        },
        "cases": results,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
        f.write("\n")

    print(f"\n{'='*60}")
    print(f"Labeled {total_items} items across {len(results)} cases")
    print(f"  Unanimous: {total_unanimous} ({total_unanimous/max(total_items,1)*100:.0f}%)")
    print(f"  Majority:  {total_majority} ({total_majority/max(total_items,1)*100:.0f}%)")
    print(f"  Split:     {total_split} ({total_split/max(total_items,1)*100:.0f}%)")
    print(f"Wrote: {output_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--candidates", type=Path, default=CANDIDATES_PATH,
        help="Input candidates JSON",
    )
    parser.add_argument(
        "--output", type=Path,
        default=OUTPUT_DIR / "consensus_labels.json",
    )
    parser.add_argument(
        "--models", nargs="+",
        default=["gemini-3.1-flash-lite", "gemini-2.5-pro", "gemini-2.0-flash"],
        help="Models to use for consensus labeling",
    )
    parser.add_argument("--trial", action="store_true", help="Run trial with subset of cases")
    parser.add_argument("--trial-cases", type=int, default=3)
    parser.add_argument("--resume", action="store_true", help="Resume from partial output")
    args = parser.parse_args()

    trial_cases = args.trial_cases if args.trial else None
    label_all(
        candidates_path=args.candidates,
        models=args.models,
        output_path=args.output,
        trial_cases=trial_cases,
        resume=args.resume,
    )


if __name__ == "__main__":
    main()
