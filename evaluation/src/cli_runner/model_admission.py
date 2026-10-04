"""eval-model-admission: the gameplay checks a model passes before it joins the model menu.

For each model in the config: structured output on every seat schema under each calling mode,
the recommended mode, the provider's smallest cacheable prompt, and how much of real game turns
it serves from cache (see ``evaluation/src/model_admission``). One JSON record per model goes to
``evaluation/eval_results/model_admission/<label>/``, stamped with the runtime fingerprint, and a
short table is printed. Costs real money (pennies per model) and needs the provider's credential.

  poetry run eval-model-admission --config evaluation/config/template/model_admission_example.json

Config keys: ``label``; ``models``; ``thinking_level`` (omit for each model's game level,
``Agents/llm_factory/accessors.py`` game_thinking_level); ``modes`` (omit for every mode the
model's protocol allows); ``samples_per_schema`` (default 3); ``workers`` (default 4);
``caching``: ``floor_sizes`` (target prompt tokens), ``wait_s``, ``dataset`` (a hallucination
bench frozen set), ``cases`` (how many of its discussion cases to replay).
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from evaluation.src.core.settings import REPO_ROOT, load_project_env

DEFAULT_DATASET = "evaluation/frozen_eval_sets/hallucination_bench_v2.jsonl"


def _cases(dataset: Path, n: int) -> list[dict]:
    """Ordinary discussion turns (controls first), past day 1 so the transcript has some length."""
    rows = [json.loads(line) for line in dataset.read_text().splitlines() if line.strip()]
    rows = [r for r in rows if r["phase"] == "day_discussion" and r["day"] >= 2]
    rows.sort(key=lambda r: (r.get("slice") != "control", r["case_id"]))
    return rows[:n]


def admit(model: str, cfg: dict) -> dict:
    from Agents.llm_factory.accessors import game_thinking_level
    from Agents.run_fingerprint import runtime_fingerprint
    from evaluation.src.model_admission import probes

    thinking = cfg.get("thinking_level", game_thinking_level(model))
    modes = [m for m in cfg.get("modes") or probes.modes_for(model) if m in probes.modes_for(model)]
    structured = []
    for mode in modes:
        print(f"  {model}: structured output, {mode} ...", flush=True)
        structured.append(probes.probe_structured(
            model, mode, thinking, cfg.get("samples_per_schema", 3), cfg.get("workers", 4)))
    mode, why = probes.recommend_mode(structured, thinking)

    caching_cfg = cfg.get("caching") or {}
    wait_s = caching_cfg.get("wait_s", 8)
    print(f"  {model}: cache floor ...", flush=True)
    floor_rows = probes.probe_cache_floor(model, caching_cfg.get("floor_sizes", [256, 512, 1024, 2048, 4096, 8192]), wait_s)
    floor = next((r["target_tokens"] for r in floor_rows if r["cached_tokens"]), None)
    real = []
    for case in _cases(REPO_ROOT / caching_cfg.get("dataset", DEFAULT_DATASET), caching_cfg.get("cases", 2)):
        print(f"  {model}: real prompts, case {case['case_id']} ...", flush=True)
        real.append(probes.probe_real_prompts(model, mode or modes[0], thinking, case, wait_s))

    # The short probes can pass while real turns fail (DeepSeek V4 Pro, auto_tool, 2026-10-04: 27/27
    # probes, 3 of 6 real turns answered in prose), so real-turn failures qualify the recommendation.
    real_calls = [r[v] for r in real for v in ("first", "next_turn", "other_seat")]
    real_failed = sum(1 for c in real_calls if c["error"])
    if mode and real_failed:
        why += f"; but it failed {real_failed} of {len(real_calls)} real game turns"

    def share(variant: str) -> float | None:
        rows = [r[variant] for r in real if r[variant]["input"]]
        return round(sum(r["cached"] for r in rows) / sum(r["input"] for r in rows), 3) if rows else None

    return {
        "model": model,
        "run_at": datetime.now(timezone.utc).isoformat(),
        "runtime_fingerprint": runtime_fingerprint(),
        "thinking_level": thinking,
        "structured": structured,
        "recommended_mode": mode,
        "recommended_mode_why": why,
        "cache_floor": {"floor_tokens": floor, "sizes": floor_rows},
        "real_prompts": real,
        "real_prompt_failures": f"{real_failed}/{len(real_calls)}",
        "cached_share": {"next_turn": share("next_turn"), "other_seat": share("other_seat")},
    }


def _print(record: dict) -> None:
    print(f"\n{record['model']}  (thinking {record['thinking_level']})")
    for r in record["structured"]:
        m = r["mean_per_call"]
        print(f"  {r['mode']:12s} {r['passed']:>7s}  reasoning {m['reasoning']:>6}  out {m['output']:>6}  {m['seconds']:>5}s")
        for f in r["failures"][:3]:
            print(f"      {f['schema']}: {f['problem'][:120]}")
    print(f"  recommended: {record['recommended_mode']} ({record['recommended_mode_why']})")
    sizes = ", ".join(f"{r['input_tokens']}→{r['cached_tokens']}" for r in record["cache_floor"]["sizes"])
    print(f"  cache floor: {record['cache_floor']['floor_tokens']} target tokens  (input→cached: {sizes})")
    for r in record["real_prompts"]:
        parts = [f"{v} {r[v]['input']} in / {r[v]['cached']} cached (shared ≈{r[v].get('shared_prefix_est', '-')})"
                 for v in ("first", "next_turn", "other_seat")]
        print(f"  {r['case_id']}: " + "; ".join(parts))
    print(f"  real game turns failed: {record['real_prompt_failures']}")
    print(f"  cached share: next turn {record['cached_share']['next_turn']}, other seat {record['cached_share']['other_seat']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    load_project_env()
    cfg = json.loads(Path(args.config).read_text())
    out_dir = REPO_ROOT / "evaluation/eval_results/model_admission" / cfg["label"]
    out_dir.mkdir(parents=True, exist_ok=True)
    for model in cfg["models"]:
        record = admit(model, cfg)
        (out_dir / f"{model.replace('/', '__')}.json").write_text(json.dumps(record, indent=1))
        _print(record)
    print(f"\nrecords: {out_dir.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
