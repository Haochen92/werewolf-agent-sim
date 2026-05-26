"""Re-run extraction on frozen eval cases with different models and report quality."""

from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from Agents.llm_factory import create_chat_model

from Agents.extraction import build_extraction_prompt
from Agents.prompts import SITUATION_STANDARDS, EPISTEMIC_STATUS_RULE
from Agents.schemas import GameStrategyOutput
from evaluation.data.datasets import read_extraction_dataset

REPO_ROOT = Path(__file__).resolve().parent.parent
PLAYER_ID_RE = re.compile(r"player_\d+")

MODEL_CONFIGS = {
    "gemini-3.5-flash": {
        "model": "gemini-3.5-flash",
        "temperature": 0.0,
    },
    "gemini-3-flash-preview": {
        "model": "gemini-3-flash-preview",
        "temperature": 0.0,
    },
    "gemini-3.1-flash-lite-high": {
        "model": "gemini-3.1-flash-lite",
        "temperature": 0.0,
        "thinking_level": "high",
    },
    "gemini-2.5-flash": {
        "model": "gemini-2.5-flash",
        "temperature": 0.0,
    },
}


def run_extraction(llm, prompt: str) -> GameStrategyOutput | None:
    try:
        result = llm.with_structured_output(GameStrategyOutput).invoke(prompt)
        if isinstance(result, GameStrategyOutput):
            return result
        if isinstance(result, dict):
            return GameStrategyOutput.model_validate(result)
    except Exception as e:
        print(f"  ERROR: {e!s:.120}", flush=True)
    return None


def check_player_ids(items: list[dict]) -> int:
    count = 0
    for item in items:
        text = json.dumps(item)
        if PLAYER_ID_RE.search(text):
            count += 1
    return count


def format_samples(observations: list[dict], strategy_points: list[dict], n: int = 3):
    lines = []
    lines.append(f"\n=== SAMPLE OBSERVATIONS ===")
    for i, obs in enumerate(observations[:n], 1):
        lines.append(
            f"[{i}] perspective={obs.get('perspective', '?')}, "
            f"phase={obs.get('action_phase', '?')}"
        )
        lines.append(f"    situation: {obs.get('situation', '')}")
        if obs.get("information_landscape"):
            lines.append(f"    info_landscape: {obs['information_landscape']}")
        lines.append(f"    approach: {obs.get('approach', '')}")
        lines.append(f"    outcome: {obs.get('outcome', '')}")
    lines.append(f"\n=== SAMPLE STRATEGY POINTS ===")
    for i, sp in enumerate(strategy_points[:n], 1):
        lines.append(
            f"[{i}] perspective={sp.get('perspective', '?')}, "
            f"phase={sp.get('action_phase', '?')}"
        )
        lines.append(f"    situation: {sp.get('situation', '')}")
        if sp.get("information_landscape"):
            lines.append(f"    info_landscape: {sp['information_landscape']}")
        lines.append(f"    action: {sp.get('action', '')}")
    return "\n".join(lines)


def main():
    if len(sys.argv) < 3:
        print("Usage: extraction_model_comparison.py <model_key> <num_games> [start_offset]")
        print(f"Available models: {list(MODEL_CONFIGS.keys())}")
        sys.exit(1)

    model_key = sys.argv[1]
    num_games = int(sys.argv[2])
    start_offset = int(sys.argv[3]) if len(sys.argv) > 3 else 0

    if model_key not in MODEL_CONFIGS:
        print(f"Unknown model: {model_key}. Available: {list(MODEL_CONFIGS.keys())}")
        sys.exit(1)

    config = MODEL_CONFIGS[model_key]
    llm = create_chat_model(**config)

    dataset_path = REPO_ROOT / "eval_sets" / "extraction_v1.jsonl"
    all_records = read_extraction_dataset(dataset_path)
    records = all_records[start_offset : start_offset + num_games]

    print(f"Model: {model_key}", flush=True)
    print(f"Games: {num_games} (offset={start_offset})", flush=True)
    print(f"Dataset: {dataset_path}", flush=True)
    print("", flush=True)

    all_observations = []
    all_strategy_points = []
    results = []

    for i, record in enumerate(records, 1):
        case = record.extraction_case
        inputs = {
            "formatted_roles": "\n".join(
                f"{pid}: {role}" for pid, role in case.roles.items()
            ),
            "formatted_discussions": case.formatted_discussions,
            "formatted_strategy_notes": case.formatted_strategy_notes,
            "formatted_previous_strategies": "No previous role strategy summaries.",
            "game_outcome": case.game_outcome,
        }
        prompt = build_extraction_prompt(inputs)

        start = time.time()
        output = run_extraction(llm, prompt)
        elapsed = time.time() - start

        if output is None:
            print(f"[{i}/{num_games}] FAILED - game={case.game_id}", flush=True)
            continue

        obs = [o.model_dump(mode="json") for o in output.observations]
        sps = [s.model_dump(mode="json") for s in output.strategy_points]
        all_observations.extend(obs)
        all_strategy_points.extend(sps)

        results.append({
            "game_id": case.game_id,
            "game_outcome": case.game_outcome,
            "model": model_key,
            "observations": obs,
            "strategy_points": sps,
            "elapsed_seconds": round(elapsed, 1),
        })

        print(
            f"[{i}/{num_games}] OK - obs={len(obs)} sp={len(sps)} "
            f"time={elapsed:.1f}s game={case.game_id[:8]}",
            flush=True,
        )
        time.sleep(1.0)

    # Summary
    obs_with_ids = check_player_ids(all_observations)
    sp_with_ids = check_player_ids(all_strategy_points)

    print(f"\n=== SUMMARY ({model_key}) ===", flush=True)
    print(f"Games completed: {len(results)}/{num_games}", flush=True)
    print(
        f"Total observations: {len(all_observations)}, "
        f"Strategy points: {len(all_strategy_points)}",
        flush=True,
    )
    print(
        f"Observations with player_IDs: {obs_with_ids}/{len(all_observations)} "
        f"({100*obs_with_ids/max(len(all_observations),1):.1f}%)",
        flush=True,
    )
    print(
        f"Strategy points with player_IDs: {sp_with_ids}/{len(all_strategy_points)} "
        f"({100*sp_with_ids/max(len(all_strategy_points),1):.1f}%)",
        flush=True,
    )

    if all_observations or all_strategy_points:
        print(format_samples(all_observations, all_strategy_points), flush=True)

    # Save results
    out_dir = REPO_ROOT / "evidence" / "extraction_quality" / "model_comparison"
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = out_dir / f"{model_key}_{num_games}games_{timestamp}.jsonl"
    with out_file.open("w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    print(f"\nResults saved to {out_file}", flush=True)


if __name__ == "__main__":
    main()
