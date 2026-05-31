"""Does flash-lite, made to reason first, match the strong judges?

The drift run handed flash-lite the pro summary + context and it still erred. This
tests the other hypothesis: maybe flash-lite is a fine *judge* but needs to do the
reasoning itself. Condition C = give flash-lite the full game state with NO pro
summary, make it write its own situation analysis first, THEN rate the memory
(chain-of-thought). Compare agreement with the strong judges (chatgpt+sonnet)
against two benchmarks on the SAME items:

    A. query-only flashlite (summary+memory, no context)        -> from merged labels
    B. context+pro-summary flashlite (direct rate, no CoT)      -> from context_labels.json
    C. context + self-analysis flashlite (CoT, no pro summary)  -> this run

If C beats B, eliciting flash-lite's own reasoning closes the gap to the pros — cheap
context labeling could then scale. If C ~ B, flash-lite is capability-limited as a
judge and we should stick with the strong judges.

Usage:
    poetry run python evidence/retrieval/context_eval/scripts/flashlite_self_summary_judge.py \
        [--sample 400] [--seed 42] [--resume]
"""
from __future__ import annotations

import argparse
import json
import random
import re
from pathlib import Path

from evaluation.labeling.adapters.context_relevance import ContextRerankerAdapter
from evaluation.labeling.base import LabelItem
from evaluation.labeling.config import ModelSpec
from evaluation.labeling.engine import label_items

REPO_ROOT = Path(__file__).resolve().parents[4]
LABELS_DIR = (
    REPO_ROOT / "evidence" / "fine_tuning" / "cross_encoder" / "reranker"
    / "labels" / "round2_expanded"
)
CANDIDATES = LABELS_DIR / "expanded_candidates_for_labeling.json"
MERGED = LABELS_DIR / "expanded_merged_labels.json"
EVAL_DATASET = REPO_ROOT / "eval_sets" / "v4_reranker_expanded.jsonl"
CTX_LABELS = REPO_ROOT / "evidence" / "retrieval" / "context_eval" / "labels" / "context_labels.json"
OUT = REPO_ROOT / "evidence" / "retrieval" / "context_eval" / "labels" / "cot_labels.json"

MODEL = ModelSpec(name="gemini-3.1-flash-lite", thinking_level="low")
ITEM_WORKERS = 8

COT_PROMPT = """\
You are evaluating an episodic-memory system for a werewolf social deduction game.

Below is the full game state a player faces. Do two things, IN ORDER:

1. ANALYSIS: In 2-4 sentences, work out what actually matters for THIS player right now
   — the live tensions, the game phase, the information available, this player's role
   and exposure, and the concrete decision they face.

2. RELEVANCE: Given your analysis, rate how useful it would be for this player to recall
   the candidate memory below.
   - 2 = highly useful: directly bears on a real tension or decision live right now.
   - 1 = partially useful: related but a different angle, phase, or specificity.
   - 0 = not useful: a fundamentally different situation; recalling it would not help here.

## Game state
{game_state}

## Candidate memory from the past
{memory_text}

Write your ANALYSIS first, then on the FINAL line output EXACTLY: RELEVANCE: <0, 1, or 2>"""


class FlashliteCoTAdapter(ContextRerankerAdapter):
    """Self-analysis-then-rate; full context, no pro summary in the prompt."""

    def format_prompt(self, item: LabelItem) -> str:
        return COT_PROMPT.format(
            game_state=item.context["game_state"],
            memory_text=item.context["memory_text"],
        )

    def parse_response(self, text: str):
        # Prefer the digit after the final "RELEVANCE:" marker; fall back to last 0/1/2.
        matches = re.findall(r"RELEVANCE\s*:?\s*([012])", text, re.IGNORECASE)
        if matches:
            return int(matches[-1])
        digits = re.findall(r"[012]", text)
        return int(digits[-1]) if digits else None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sample", type=int, default=400)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    adapter = FlashliteCoTAdapter(eval_dataset_path=EVAL_DATASET)
    items = adapter.load_items(CANDIDATES)
    n = len(items)
    if args.sample and args.sample < n:
        idx = sorted(random.Random(args.seed).sample(range(n), args.sample))
        items = [items[i] for i in idx]
    print(f"CoT-labeling {len(items)}/{n} items with flash-lite (self-analysis then rate)")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    results = label_items(items, [MODEL], adapter, OUT, resume=args.resume,
                          max_item_workers=ITEM_WORKERS)
    cot = {(r["case_index"], r["key"]): r["model_scores"].get(MODEL.name) for r in results}

    # benchmarks on the SAME items
    ctx = {(r["case_index"], r["key"]): r["model_scores"].get(MODEL.name)
           for r in json.load(open(CTX_LABELS))["results"]}
    merged = {(r["case_index"], r["key"]): r["labeling"]["scores"]
              for r in json.load(open(MERGED))["results"]}

    def b(x):
        return None if x is None else int(x >= 1)

    rows = {"A_query_only": [0, 0], "B_context_prosummary": [0, 0], "C_context_self_cot": [0, 0]}
    toward = away = same = ncmp = 0
    for k, c in cot.items():
        sc = merged.get(k)
        if sc is None or c is None:
            continue
        strong = (sc["chatgpt"] + sc["sonnet"]) / 2
        sb = int(strong >= 1)
        q, x = sc["flashlite"], ctx.get(k)
        for name, val in (("A_query_only", q), ("B_context_prosummary", x), ("C_context_self_cot", c)):
            if val is None:
                continue
            rows[name][1] += 1
            rows[name][0] += int(b(val) == sb)
        # did CoT move closer to strong than the context(B) condition?
        if x is not None:
            ncmp += 1
            dC, dB = abs(c - strong), abs(x - strong)
            if dC < dB:
                toward += 1
            elif dC > dB:
                away += 1
            else:
                same += 1

    print(f"\n{'='*70}\nAGREEMENT WITH STRONG JUDGES (binary useful cut), same items\n{'='*70}")
    report = {"sample": len(cot), "seed": args.seed, "conditions": {}}
    for name, (hit, tot) in rows.items():
        rate = hit / tot if tot else 0
        report["conditions"][name] = {"agree": hit, "n": tot, "rate": round(rate, 4)}
        print(f"  {name:24s}: {hit}/{tot} = {rate:.1%}")
    report["cot_vs_context_B"] = {"toward_strong": toward, "away": away, "same": same, "n": ncmp}
    print(f"\nCoT (C) vs context (B), distance to strong judges:")
    print(f"  C closer: {toward} ({toward/ncmp:.1%})   B closer: {away} ({away/ncmp:.1%})   tie: {same}")
    null_c = sum(v is None for v in cot.values())
    report["cot_nulls"] = null_c
    print(f"\nCoT parse failures: {null_c}/{len(cot)}")
    (OUT.parent / "cot_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Wrote {OUT.parent / 'cot_report.json'}")


if __name__ == "__main__":
    main()
