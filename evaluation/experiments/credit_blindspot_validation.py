"""Step-1 validation of the credit blind-spot fix pair — $0, pure re-scoring of runs already on disk.

The v7 endpoint (batch_results/v7_endpoint_ab, 2026-07-20) showed the credit instrument is
structurally blind to the caution/concealment SP family (abstain pins at neutral; concealment never
reaches a creditable endpoint), so prune could not remove the SPs that transcript forensics identified
as the town-deadlock mechanism. The fixes: (1) LoopConfig.abstain_credit="deadlock_negative", (2) the
conversion channel (conversion_credit.py). This runner asks, against data we already own:

  SENSITIVITY   — do the forensically-labeled HARMFUL flagships become prune-reachable under the fixes?
  SPECIFICITY   — do the labeled GOOD (engagement / conversion-positive) flagships stay protected?
  FALSE-PENALTY — how many abstains does the new rule penalize in the one defensible context
                  (the room mislynched without them)?

Two corpora, because the fixes were DESIGNED on the endpoint: the loop run's games
(v7_compound_town5) are different games and blunt the circularity. Passing here is necessary, not
sufficient — generalization needs a fresh run (step 3, not authorized). Labels live in this file
(FLAGSHIPS) as action-text prefixes resolved against the store at runtime; the 07-20 forensics are
the label source, quoted in evidence/credit_blindspot_fix/experiment_log.md.

  poetry run python evaluation/experiments/credit_blindspot_validation.py
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from evaluation.src.loop.config import LoopConfig  # noqa: E402
from evaluation.src.loop.consolidate import prune_and_evict  # noqa: E402
from evaluation.src.loop.conversion_credit import (  # noqa: E402
    CONVERSION_CHANNEL, conversion_apply, conversion_lift,
)
from evaluation.src.loop.credit import base_for, credit_apply, sp_lift  # noqa: E402
from evaluation.src.loop.credit_backfill import compute_base_rates  # noqa: E402

# Flagship labels from the 2026-07-20 endpoint forensics (matched on action-text prefix — keys are
# store-instance-specific). "harmful" = the deadlock family's most-cited members; "good" = proven
# engagement/conversion SPs a clumsy fix must NOT nuke.
FLAGSHIPS = {
    "harmful_abstain": "Abstain from voting when the information landscape is entirely speculative",
    "harmful_silence_inv": "Maintain silence regarding high-value investigation results",
    "harmful_silence_healer": "Maintain strict silence regarding your role and your night-time",
    "good_engage_healer": "Maintain active engagement with the vote rather than abstaining",
    "good_comm_vig": "When parity is imminent, prioritize clear communication",
    "good_convert_vig": "Prioritize voting for the target identified by a claimed investigator",
}
CAUTION_FAMILY = ("concealment", "risk_policy")  # sp_type union; direction=defensive joins below


def _corpus_globs(loop_run: Path, endpoint: Path) -> dict[str, tuple[str, str]]:
    return {
        "loop_run": (" ".join(str(loop_run / f"gen{g}_on.jsonl") for g in (1, 2, 3, 4)),
                     " ".join(str(loop_run / f"gen{g}_off.jsonl") for g in (1, 2, 3, 4))),
        "endpoint": (" ".join(str(endpoint / f"ep_on_g{k}.jsonl") for k in range(30)),
                     " ".join(str(endpoint / f"ep_off_g{k}.jsonl") for k in range(30))),
    }


def _iter_sps(store: dict):
    for ns_key, recs in store.get("namespaces", {}).items():
        cell = "/".join(ns_key.split("/")[1:])
        for r in recs:
            yield cell, r


def _flagship_keys(store: dict) -> dict[str, str]:
    out = {}
    for _cell, r in _iter_sps(store):
        action = r["value"].get("action", "")
        for name, prefix in FLAGSHIPS.items():
            if action.startswith(prefix):
                out[name] = r["key"]
    return out


def _in_caution_family(v: dict) -> bool:
    dims = v.get("dimensions") or {}
    return dims.get("sp_type") in CAUTION_FAMILY or v.get("direction") == "defensive"


def _score_variant(sp_src: Path, workdir: Path, tag: str, on_glob: str, off_glob: str,
                   rule: str, window_days: int) -> tuple[Path, dict]:
    """One (corpus, rule) cell: credit + conversion counters onto a fresh copy of the store, then the
    prune/evict simulation under the matching LoopConfig. Returns (store copy path, result row)."""
    cell_dir = workdir / tag
    cell_dir.mkdir(parents=True, exist_ok=True)
    sp = cell_dir / "strategy_points.json"
    shutil.copy(sp_src, sp)
    base_rates = compute_base_rates(off_glob, abstain_rule=rule)
    credit_apply(sp, on_glob, base_rates=base_rates, discussion=True, off_window=off_glob,
                 abstain_rule=rule)
    conversion_apply(sp, on_glob, off_window=off_glob, window_days=window_days)
    store = json.loads(sp.read_text())
    rates = json.loads((cell_dir / "base_rates.json").read_text())
    fixes_on = rule == "deadlock_negative"
    cfg = LoopConfig(conversion_credit=fixes_on)
    pruned_store = json.loads(sp.read_text())  # prune mutates; keep the credited store intact on disk
    stats = prune_and_evict(pruned_store["namespaces"], rates, cfg)
    surviving = {r["key"] for _c, r in _iter_sps(pruned_store)}
    (cell_dir / "pruned_strategy_points.json").write_text(json.dumps(pruned_store, indent=2))

    per_sp = {}
    fam_removed = fam_total = 0
    for cell, r in _iter_sps(store):
        v = r["value"]
        removed = r["key"] not in surviving
        if _in_caution_family(v):
            fam_total += 1
            fam_removed += removed
        per_sp[r["key"]] = {
            "action": v.get("action", "")[:70], "cell": cell,
            "follow": v.get("follow_count", 0),
            "lift": sp_lift(v, base_for(rates, cell, v.get("sp_type"))),
            "conv_n": v.get("conversion_pos_count", 0) + v.get("conversion_neg_count", 0),
            "conv_lift": conversion_lift(v, base_for(rates, CONVERSION_CHANNEL)),
            "removed": removed,
        }
    row = {"prune_stats": stats, "caution_family": {"total": fam_total, "removed": fam_removed},
           "conversion_base": rates.get(CONVERSION_CHANNEL), "per_sp": per_sp}
    return sp, row


def _abstain_census(on_glob: str) -> dict:
    """The false-penalty context table: for every town day-2+ ON-arm abstain, what did the day resolve
    to? deadlock_negative penalizes ONLY the no_lynch bucket; lynched_town is the defensible abstain."""
    from evaluation.src.loop.credit_backfill import TOWN_VOTE_ROLES, _expand_dumps
    census: Counter = Counter()
    for dump in _expand_dumps(on_glob):
        for line in open(dump):
            if not line.strip():
                continue
            g = json.loads(line)
            roles, path = g.get("roles"), g.get("eval_cases_path")
            if not roles or not path or not Path(path).exists():
                continue
            day_out = {}
            for dr in g.get("day_resolutions", []):
                if dr.get("no_vote") or not dr.get("voted_player"):
                    day_out[dr["day"]] = "no_lynch"
                else:
                    role = dr.get("voted_player_role") or roles.get(dr["voted_player"])
                    day_out[dr["day"]] = ("lynched_threat" if role in ("wolf", "serial_killer")
                                          else "lynched_town")
            for cl in open(path):
                if not cl.strip():
                    continue
                ec = (json.loads(cl).get("output") or {}).get("eval_case") or {}
                if (ec.get("action_phase") == "day_vote" and ec.get("day") != 1
                        and ec.get("player_role") in TOWN_VOTE_ROLES and ec.get("memory_enabled")
                        and (ec.get("agent_vote") or {}).get("votee") in (None, "", "abstain")):
                    census[day_out.get(ec.get("day"), "unresolved")] += 1
    total = sum(census.values())
    return {"total": total, "by_day_outcome": dict(census),
            "penalized_by_new_rule": census.get("no_lynch", 0),
            "defensible_spared": census.get("lynched_town", 0)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--loop-run", type=Path, default=Path("batch_results/v7_compound_town5"))
    ap.add_argument("--endpoint", type=Path, default=Path("batch_results/v7_endpoint_ab"))
    ap.add_argument("--store", type=Path,
                    default=Path("batch_results/v7_endpoint_ab/final_store_snapshot/strategy_points.json"))
    ap.add_argument("--out", type=Path, default=Path("evidence/credit_blindspot_fix"))
    ap.add_argument("--window-days", type=int, default=LoopConfig.conversion_window_days)
    args = ap.parse_args()

    workdir = args.out / "scored_stores"
    store0 = json.loads(args.store.read_text())
    flagships = _flagship_keys(store0)
    missing = set(FLAGSHIPS) - set(flagships)
    if missing:
        raise SystemExit(f"flagship labels not found in store (prefix drift?): {missing}")

    result: dict = {"store": str(args.store), "flagship_keys": flagships, "cells": {}}
    for corpus, (on_glob, off_glob) in _corpus_globs(args.loop_run, args.endpoint).items():
        for rule in ("neutral", "deadlock_negative"):
            tag = f"{corpus}__{rule}"
            print(f"scoring {tag} ...", flush=True)
            _sp, row = _score_variant(args.store, workdir, tag, on_glob, off_glob,
                                      rule, args.window_days)
            result["cells"][tag] = row
        result["cells"][f"{corpus}__abstain_census"] = _abstain_census(on_glob)

    # ---- the verdict table ------------------------------------------------------------------------
    lines = ["# Step-1 validation — blind-spot fix pair (sensitivity / specificity / false-penalty)",
             "", "Rule columns: legacy = abstain neutral, no conversion; fixed = deadlock_negative + "
             "conversion term. `removed` = pruned OR evicted in the simulation.", ""]
    verdicts = {}
    for corpus in ("loop_run", "endpoint"):
        lines += [f"## corpus: {corpus}", "",
                  "| flagship | follow | legacy lift | fixed lift | conv n | conv lift | removed legacy→fixed |",
                  "| --- | --- | --- | --- | --- | --- | --- |"]
        legacy = result["cells"][f"{corpus}__neutral"]["per_sp"]
        fixed = result["cells"][f"{corpus}__deadlock_negative"]["per_sp"]
        for name, key in flagships.items():
            lo, fi = legacy[key], fixed[key]
            expect_removed = name.startswith("harmful")
            ok = (fi["removed"] == expect_removed) if expect_removed else (not fi["removed"])
            verdicts[f"{corpus}/{name}"] = ok
            fmt = lambda x: "—" if x is None else f"{x:+.2f}"  # noqa: E731
            lines.append(
                f"| {name} | {fi['follow']} | {fmt(lo['lift'])} | {fmt(fi['lift'])} "
                f"| {fi['conv_n']} | {fmt(fi['conv_lift'])} "
                f"| {lo['removed']}→{fi['removed']} {'✅' if ok else '❌'} |")
        fam_l = result["cells"][f"{corpus}__neutral"]["caution_family"]
        fam_f = result["cells"][f"{corpus}__deadlock_negative"]["caution_family"]
        cen = result["cells"][f"{corpus}__abstain_census"]
        lines += ["",
                  f"- caution family removed: legacy {fam_l['removed']}/{fam_l['total']} → "
                  f"fixed {fam_f['removed']}/{fam_f['total']}",
                  f"- prune stats legacy: {result['cells'][f'{corpus}__neutral']['prune_stats']} | "
                  f"fixed: {result['cells'][f'{corpus}__deadlock_negative']['prune_stats']}",
                  f"- abstain census: {cen['total']} town abstains — new rule penalizes "
                  f"{cen['penalized_by_new_rule']} (no-lynch days), spares "
                  f"{cen['defensible_spared']} defensible (room mislynched) — "
                  f"{cen['by_day_outcome']}", ""]
    passed = sum(verdicts.values())
    lines += ["## Verdict", "",
              f"- flagship checks passed: {passed}/{len(verdicts)}",
              *(f"  - {'✅' if ok else '❌'} {k}" for k, ok in sorted(verdicts.items())), ""]
    result["verdicts"] = verdicts

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "step1_validation.json").write_text(json.dumps(result, indent=2))
    (args.out / "step1_validation.md").write_text("\n".join(lines))
    print("\n".join(lines))
    print(f"\nwrote {args.out}/step1_validation.{{json,md}}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
