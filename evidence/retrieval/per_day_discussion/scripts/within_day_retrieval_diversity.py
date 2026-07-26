"""FROZEN RECORD (2026-07-07) — pre-test for the per-day discussion-retrieval design variant.

Question this answers (the $0 gate before any build): how often do an agent's per-TURN discussion
retrievals WITHIN one day actually return different memories? Today every discussion turn pays a
situation-summary LLM call + retrieval (Agents/turn/pipeline.py -> enrich_payload_with_memory).
If within-day retrievals are mostly identical, per-turn granularity is paying LLM calls for
near-duplicate results and a per-day grain is close to a free lunch; if they pivot mid-day, the
divergence rate quantifies what a per-day design must preserve (e.g. event-triggered re-retrieval).

Method: scan every eval-case sidecar dataset (batch_results/eval_cases/<dataset>/<game>.jsonl,
schema eval_case_v2), keep day_discussion cases with memory_enabled and retrieval not skipped,
group by (dataset, game, player, day), and compare the retrieved key-sets across the day's turns:
  - identical-day rate: all turns retrieved the exact same set (observations+SPs combined);
  - mean consecutive-turn Jaccard (obs and SPs separately; J(empty,empty)=1);
  - turns per retrieving agent-day (the situation-LLM-call savings factor of a per-day grain).
Multi-turn agent-days are the units; single-turn days can't diverge and are excluded from
diversity rates (counted separately). No LLM, recompute-only over existing artifacts.

Signal-vs-noise split (second pass, same run): retrieved-set churn is only *valuable* adaptation
if it tracks a genuinely changed situation. The live query is itself LLM-generated per turn, so
churn can also be query-regeneration instability or top-k boundary swaps among near-tied scores.
Discriminator: per consecutive turn pair, compare the situation-QUERY text similarity (word-set
Jaccard of the composed `situations` strings) against the retrieved-set Jaccard. First run showed
NO pair exceeds 0.8 query similarity — the LLM rewords the query every turn (sit-J ~0.26,
near-constant across arms/factions/epochs) — so the discriminator is graded, not binary: the
Pearson correlation of (query-text similarity, retrieved-set overlap) across pairs, plus tercile
means. If set overlap does not rise with query similarity even within the observed range, the
churn is decoupled from what the query says — retrieval-side noise, not situation adaptation.

    poetry run python evidence/retrieval/per_day_discussion/scripts/within_day_retrieval_diversity.py

Output: evidence/retrieval/per_day_discussion/data/within_day_retrieval_diversity.json + stdout table.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
EVAL_CASES = REPO_ROOT / "batch_results/eval_cases"
OUT = REPO_ROOT / "evidence/retrieval/per_day_discussion/data/within_day_retrieval_diversity.json"

FACTION = {"wolf": "wolf", "serial_killer": "sk"}  # everything else -> town


def _keys(items: list) -> frozenset:
    return frozenset(i.get("key") for i in items if isinstance(i, dict))


def _sit_tokens(situations: list) -> frozenset:
    return frozenset(" ".join(s for s in situations if isinstance(s, str)).lower().split())


def _jaccard(a: frozenset, b: frozenset) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def _collect(dataset_dir: Path) -> dict:
    """(game, player, day) -> sorted [(round, obs_keys, sp_keys)] for memory-on discussion turns."""
    groups: dict[tuple, list] = defaultdict(list)
    roles: dict[tuple, str] = {}
    for game_file in sorted(dataset_dir.glob("*.jsonl")):
        with open(game_file) as f:
            for line in f:
                case = json.loads(line)
                if case.get("kind") != "agent_action_eval":
                    continue
                ec = (case.get("output") or {}).get("eval_case") or {}
                if ec.get("action_phase") != "day_discussion":
                    continue
                if not ec.get("memory_enabled") or ec.get("retrieval_skipped_reason"):
                    continue
                gk = (game_file.stem, ec["player_id"], ec["day"])
                groups[gk].append(
                    (
                        ec.get("round", 0),
                        _keys(ec.get("retrieved_observations") or []),
                        _keys(ec.get("retrieved_strategy_points") or []),
                        _sit_tokens(ec.get("situations") or []),
                    )
                )
                roles[gk] = ec.get("player_role", "?")
    return {gk: (sorted(turns), roles[gk]) for gk, turns in groups.items()}


def _analyze(groups: dict) -> dict:
    per_faction: dict[str, dict] = defaultdict(
        lambda: {
            "agent_days": 0,
            "multi_turn_days": 0,
            "identical_days": 0,
            "turns": 0,
            "jaccard_obs": [],
            "jaccard_sp": [],
            "diverged_days": 0,
            "sit_jaccard": [],
            "pair_sit_set": [],
        }
    )
    for (game, player, day), (turns, role) in groups.items():
        f = per_faction[FACTION.get(role, "town")]
        f["agent_days"] += 1
        f["turns"] += len(turns)
        if len(turns) < 2:
            continue
        f["multi_turn_days"] += 1
        combined = [obs | sp for _, obs, sp, _ in turns]
        identical = all(c == combined[0] for c in combined)
        f["identical_days"] += identical
        f["diverged_days"] += not identical
        for (_, o1, s1, t1), (_, o2, s2, t2) in zip(turns, turns[1:]):
            f["jaccard_obs"].append(_jaccard(o1, o2))
            f["jaccard_sp"].append(_jaccard(s1, s2))
            sit_j = _jaccard(t1, t2)
            f["sit_jaccard"].append(sit_j)
            f["pair_sit_set"].append((sit_j, _jaccard(o1 | s1, o2 | s2)))
    out = {}
    for faction, f in per_faction.items():
        mt = f["multi_turn_days"]
        out[faction] = {
            "agent_days_with_retrieval": f["agent_days"],
            "total_retrieving_turns": f["turns"],
            "turns_per_agent_day": round(f["turns"] / f["agent_days"], 2) if f["agent_days"] else None,
            "multi_turn_agent_days": mt,
            "identical_all_turns_rate": round(f["identical_days"] / mt, 3) if mt else None,
            "diverged_rate": round(f["diverged_days"] / mt, 3) if mt else None,
            "mean_consecutive_jaccard_obs": (
                round(sum(f["jaccard_obs"]) / len(f["jaccard_obs"]), 3) if f["jaccard_obs"] else None
            ),
            "mean_consecutive_jaccard_sp": (
                round(sum(f["jaccard_sp"]) / len(f["jaccard_sp"]), 3) if f["jaccard_sp"] else None
            ),
            "mean_consecutive_sit_text_jaccard": (
                round(sum(f["sit_jaccard"]) / len(f["sit_jaccard"]), 3) if f["sit_jaccard"] else None
            ),
            **_sit_set_relation(f["pair_sit_set"]),
        }
    return out


def _sit_set_relation(pairs: list[tuple[float, float]]) -> dict:
    """Does query-text similarity predict retrieved-set overlap? Pearson r + tercile means."""
    n = len(pairs)
    if n < 9:
        return {"sit_set_pearson_r": None, "set_j_by_sit_tercile": None, "n_pairs": n}
    xs, ys = [p[0] for p in pairs], [p[1] for p in pairs]
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in pairs)
    vx = sum((x - mx) ** 2 for x in xs) ** 0.5
    vy = sum((y - my) ** 2 for y in ys) ** 0.5
    r = cov / (vx * vy) if vx and vy else float("nan")
    by_sit = sorted(pairs)
    k = n // 3
    terciles = [
        round(sum(y for _, y in chunk) / len(chunk), 3)
        for chunk in (by_sit[:k], by_sit[k : 2 * k], by_sit[2 * k :])
    ]
    return {
        "sit_set_pearson_r": round(r, 3) if r == r else None,
        "set_j_by_sit_tercile": terciles,
        "n_pairs": n,
    }


def main() -> None:
    results = {}
    for dataset_dir in sorted(EVAL_CASES.iterdir()):
        if not dataset_dir.is_dir():
            continue
        groups = _collect(dataset_dir)
        if not groups:
            continue
        results[dataset_dir.name] = _analyze(groups)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=2))
    print(f"-> {OUT.relative_to(REPO_ROOT)}\n")
    hdr = (
        f"{'dataset':38} {'faction':7} {'aDays':>5} {'multi':>5} {'t/day':>5} "
        f"{'identical':>9} {'J(obs)':>6} {'J(sp)':>6}"
    )
    print(hdr)
    print("-" * len(hdr))
    for ds, factions in results.items():
        for faction, m in sorted(factions.items()):
            ident = m["identical_all_turns_rate"]
            print(
                f"{ds:38} {faction:7} {m['agent_days_with_retrieval']:>5} "
                f"{m['multi_turn_agent_days']:>5} {m['turns_per_agent_day']:>5} "
                f"{(f'{ident:.0%}' if ident is not None else '—'):>9} "
                f"{(m['mean_consecutive_jaccard_obs'] if m['mean_consecutive_jaccard_obs'] is not None else '—'):>6} "
                f"{(m['mean_consecutive_jaccard_sp'] if m['mean_consecutive_jaccard_sp'] is not None else '—'):>6}"
            )


if __name__ == "__main__":
    main()
