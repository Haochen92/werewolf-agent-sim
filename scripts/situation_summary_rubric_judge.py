"""Score situation summary outputs with a rubric-based judge (per-dimension scores)."""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from Agents.llm_factory import create_chat_model

from Agents.formatters import format_day_channel
from evaluation.core.formatters import format_eval_private_context, format_eval_situations
from evaluation.core.schemas import SituationSummaryScores
from evaluation.data.datasets import read_eval_dataset
from evaluation.judges.prompts import SUMMARY_RUBRIC_SYSTEM_PROMPT, SUMMARY_RUBRIC_USER_PROMPT

REPO_ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = REPO_ROOT / "eval_sets" / "v4_filtering_eval.jsonl"
OUTPUT_DIR = REPO_ROOT / "evidence" / "situation_summary_quality" / "model_comparison"

JUDGE_MODEL = "gemini-3.1-pro-preview"

MODEL_OUTPUT_FILES = {
    "flash-lite-default": "outputs_flash-lite-default_20260524_162057.jsonl",
    "flash-lite-medium": "outputs_flash-lite-medium_20260524_162057.jsonl",
    "2.5-flash": "outputs_2.5-flash_20260524_162057.jsonl",
    "3.5-flash": "outputs_3.5-flash_20260524_162057.jsonl",
}


def load_outputs(filename: str) -> list[dict]:
    path = OUTPUT_DIR / filename
    with path.open() as f:
        return [json.loads(line) for line in f]


def run_rubric_judge(llm, record, situations: list[str]) -> SituationSummaryScores | None:
    case = record.eval_case
    user_prompt = SUMMARY_RUBRIC_USER_PROMPT.format(
        player_id=case.player_id,
        player_role=case.player_role,
        day=case.day,
        round=case.round,
        action_phase=case.action_phase,
        day_channel_excerpt=format_day_channel(case.visible_discussion),
        private_context=format_eval_private_context(case.private_context),
        situations=format_eval_situations(situations),
    )
    try:
        result = llm.with_structured_output(SituationSummaryScores).invoke(
            [
                {"role": "system", "content": SUMMARY_RUBRIC_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]
        )
        if isinstance(result, dict):
            return SituationSummaryScores.model_validate(result)
        return result
    except Exception as exc:
        print(f"    JUDGE ERROR: {exc!s:.80}", flush=True)
        return None


def main():
    num_cases = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    records = read_eval_dataset(DATASET_PATH)[:num_cases]

    llm = create_chat_model(JUDGE_MODEL)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = OUTPUT_DIR / f"rubric_judge_{timestamp}.jsonl"

    print(f"Cases: {num_cases}", flush=True)
    print(f"Models: {list(MODEL_OUTPUT_FILES.keys())}", flush=True)
    print(f"Judge: {JUDGE_MODEL}", flush=True)
    print(f"Output: {out_file}", flush=True)
    print("", flush=True)

    all_scores: dict[str, list[SituationSummaryScores]] = {k: [] for k in MODEL_OUTPUT_FILES}

    for model_key, filename in MODEL_OUTPUT_FILES.items():
        outputs = load_outputs(filename)
        print(f"=== Judging {model_key} ===", flush=True)

        for i, (record, output) in enumerate(zip(records, outputs), 1):
            situations = output["situations"]
            scores = run_rubric_judge(llm, record, situations)

            if scores is None:
                print(f"  [{i}/{num_cases}] FAILED", flush=True)
                continue

            all_scores[model_key].append(scores)
            print(
                f"  [{i}/{num_cases}] faith={scores.faithfulness} "
                f"spec={scores.specificity} retr={scores.retrieval_usefulness} "
                f"nred={scores.non_redundancy} role={scores.role_perspective}",
                flush=True,
            )

            with out_file.open("a") as f:
                f.write(json.dumps({
                    "model": model_key,
                    "case_id": record.case_id,
                    "player_role": record.player_role,
                    "day": record.day,
                    "round": record.round,
                    **scores.model_dump(mode="json"),
                }) + "\n")

            time.sleep(1.0)
        print("", flush=True)

    # Summary table
    dims = ["faithfulness", "specificity", "retrieval_usefulness", "non_redundancy", "role_perspective"]
    print(f"\n{'Model':<25} " + " ".join(f"{d[:6]:>7}" for d in dims) + "    Avg", flush=True)
    print("-" * 75, flush=True)

    for model_key, scores_list in all_scores.items():
        if not scores_list:
            continue
        avgs = {d: sum(getattr(s, d) for s in scores_list) / len(scores_list) for d in dims}
        overall = sum(avgs.values()) / len(dims)
        print(
            f"{model_key:<25} "
            + " ".join(f"{avgs[d]:7.2f}" for d in dims)
            + f"   {overall:.2f}",
            flush=True,
        )


if __name__ == "__main__":
    main()
