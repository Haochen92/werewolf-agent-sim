"""v6 dimension-accuracy audit ($0, deterministic) — Phase 1 of the eval-hardening pass.

The finding this tests: every v6 situation dimension is LLM-filled at query time and NO filled value
was ever checked against ground truth, yet production retrieval GATING keys on
``players_alive``(bucket) / ``is_swing`` / ``exposure_class`` / ``info_landscape_class`` and returned
~0/negative. If the fills are inaccurate those nulls are UNINFORMATIVE, not negative
(``evidence/evaluation/hardening_pass/experiment_log.md`` §2.1). This audit recomputes the
deterministically-knowable dims from each case's OWN frozen board (never the outcome) and scores the
query-side fill against that truth.

Data: the loop-era eval-case sidecars are the ONLY place query-side ``situation_dimensions`` are
persisted (``batch_results/{town_only_run1,town_only_run2,v2_full,legacy}``); the batch records that
carry roles + night/day resolutions live in ``evidence/v7_final/<run>/gen*_{on,off}.jsonl`` and are
joined per game by ``trace_id``.

Epistemic split (MANDATORY): ``players_alive`` / ``bullets_left`` / ``ally_revealed`` are
agent-knowable, so a mismatch is PURE FILL ERROR. ``distance_to_parity`` / ``is_swing`` compare the
fill to an OMNISCIENT truth (wolf-faction parity), so for TOWN roles a mismatch conflates fill error
with the agent's epistemic limit (a villager cannot know the wolf count) → reported as
"vs-omniscient disagreement"; for WOLF roles it is ~true fill accuracy (a wolf knows the wolf count —
caveat: the parity metric ignores the serial killer, which wolves also cannot see).

  poetry run python evaluation/src/experiments/dimension_audit.py            # runs the $0 audit
  poetry run python evaluation/src/experiments/dimension_audit.py --regen    # BLOCKED (spends money)
"""

from __future__ import annotations

import argparse
import contextlib
import glob
import io
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from Agents.game_config import GameConfig
from Agents.memory.retrieval.dimension_gating import _alive_bucket
from Agents.schemas.evaluation import EvalCase
from evaluation.src.data.sources.sidecar import LocalCaseSource
from evaluation.src.loop.decision_scoring import query_criticality

TOWN_ROLES = frozenset({"villager", "healer", "investigator", "vigilante"})

# Runs whose sidecars carry query-side v6 dimensions, mapped to the batch records that carry roles +
# resolutions. Loop runs write records to evidence/v7_final/<run>/; the legacy smoke runs keep theirs
# at the batch_results/legacy top level.
DEFAULT_RUNS: dict[str, list[str]] = {
    "town_only_run1": sorted(
        glob.glob("evidence/v7_final/town_only_run1/gen*_on.jsonl")
        + glob.glob("evidence/v7_final/town_only_run1/gen*_off.jsonl")
    ),
    "town_only_run2": sorted(
        glob.glob("evidence/v7_final/town_only_run2/gen*_on.jsonl")
        + glob.glob("evidence/v7_final/town_only_run2/gen*_off.jsonl")
    ),
    "v2_full": sorted(
        glob.glob("evidence/v7_final/v2_full/gen*_on.jsonl")
        + glob.glob("evidence/v7_final/v2_full/gen*_off.jsonl")
    ),
    "legacy": [
        "batch_results/legacy/v6live_smoke.jsonl",
        "batch_results/legacy/v6smoke_wolfboth.jsonl",
        "batch_results/legacy/v6smoke2_wolfboth.jsonl",
        "batch_results/legacy/v6smoke3_skboth.jsonl",
        "batch_results/legacy/sidecar_smoke_001.jsonl",
    ],
}


# ── Truth computation (pure; from the case's OWN frozen state, never the outcome) ────────────────
def players_alive_true(case: EvalCase) -> int:
    """Agent-knowable: the survivor roster the agent was shown."""
    return len(case.private_context.surviving_players)


def bullets_left_true(day: int, night_resolutions: list[dict], loadout: int) -> int:
    """Agent-knowable vigilante bullet count entering ``day``'s decision. DAY precedes NIGHT within a
    day number (parent graph: DAY_PHASE -> DAY_RESOLUTION -> night), so nights with ``day < case.day``
    have already resolved; each carries a non-null ``vigilante_target`` iff the vigilante shot."""
    shots = sum(
        1
        for nr in night_resolutions
        if nr.get("day", 0) < day and nr.get("vigilante_target") is not None
    )
    return max(0, loadout - shots)


def _wolf_partners(case: EvalCase, roles: dict[str, str]) -> set[str]:
    return {p for p, r in roles.items() if r == "wolf" and p != case.player_id}


def ally_revealed_true_absent(case: EvalCase, roles: dict[str, str]) -> bool:
    """Agent-knowable PRIMARY variant: a wolf partner is no longer among the acting wolf's surviving
    partners (dead/eliminated). A wolf tracks its partners' liveness directly."""
    surviving = set(case.private_context.surviving_wolves)
    return any(p not in surviving for p in _wolf_partners(case, roles))


def ally_revealed_true_lynched(case: EvalCase, roles: dict[str, str], day_resolutions: list[dict]) -> bool:
    """SECONDARY variant: a wolf partner was LYNCHED with its role revealed on a prior day."""
    partners = _wolf_partners(case, roles)
    return any(
        res.get("day", 0) < case.day
        and res.get("voted_player") in partners
        and res.get("voted_player_role") == "wolf"
        for res in day_resolutions
    )


# ── Data loading (join sidecar cases to batch records by trace_id) ───────────────────────────────
def iter_run_cases(batch_files: Iterable[str], run_label: str) -> Iterator[tuple[EvalCase, dict, str]]:
    """Yield (case, batch_record, run_label) for every eval case in the run. The batch record carries
    roles + night/day resolutions; the sidecar (followed via ``eval_cases_path``) carries the cases."""
    for bf in batch_files:
        path = Path(bf)
        if not path.exists():
            continue
        recs: dict[str, dict] = {}
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("trace_id"):
                recs[rec["trace_id"]] = rec
        with contextlib.redirect_stdout(io.StringIO()):  # silence the "skipped N games" chatter
            source = LocalCaseSource(path)
        for tid in source.trace_ids():
            rec = recs.get(tid)
            if not rec:
                continue
            for case in source.eval_cases(tid):
                yield case, rec, run_label


# ── Comparison rows: one per (situation, computable dim) ─────────────────────────────────────────
def _num_row(dim, run, role, phase, day, epi, filled, true) -> dict | None:
    if filled is None or true is None:
        return None
    try:
        filled = int(filled)
    except (TypeError, ValueError):
        return None
    return {"dim": dim, "run": run, "role": role, "phase": phase, "day": day, "epistemic": epi,
            "kind": "num", "filled": filled, "true": int(true),
            "match": filled == int(true), "abs_err": abs(filled - int(true))}


def _bool_row(dim, run, role, phase, day, epi, filled, true) -> dict | None:
    if filled is None or true is None:
        return None
    filled, true = bool(filled), bool(true)
    return {"dim": dim, "run": run, "role": role, "phase": phase, "day": day, "epistemic": epi,
            "kind": "bool", "filled": filled, "true": true, "match": filled == true}


def rows_for_case(case: EvalCase, rec: dict, run: str, loadout: int) -> tuple[list[dict], Counter]:
    """All comparison rows + an enum-value tally for one case (over its 1-2 situations)."""
    roles = rec.get("roles", {}) or {}
    # The board roster is required to compute the criticality truth. Wolf NIGHT-action cases do NOT
    # persist private_context.surviving_players (empty), so their alive/distance/is_swing truth is
    # UNCOMPUTABLE from the case's own frozen state — we skip those three dims (never score a fill
    # against a bogus 0) and count them, rather than silently corrupting the wolf accuracy numbers.
    have_roster = len(case.private_context.surviving_players) > 0
    alive_t = players_alive_true(case)
    _, dist_t, swing_t = query_criticality(case.private_context.surviving_players, roles)
    bullets_t = bullets_left_true(case.day, rec.get("night_resolutions", []) or [], loadout)
    ally_absent_t = ally_revealed_true_absent(case, roles)
    ally_lynch_t = ally_revealed_true_lynched(case, roles, rec.get("day_resolutions", []) or [])
    role, phase, day = case.player_role, case.action_phase, case.day
    town_lens = role in TOWN_ROLES or role == "serial_killer"  # SK also can't see wolf count

    rows: list[dict] = []
    enums: Counter = Counter()
    for d in case.situation_dimensions:
        if not isinstance(d, dict):
            continue
        if have_roster:
            rows.append(_num_row("players_alive", run, role, phase, day, "agent_knowable",
                                 d.get("players_alive"), alive_t))
            rows.append(_num_row("distance_to_parity", run, role, phase, day,
                                 "vs_omniscient" if town_lens else "true_fill", d.get("distance_to_parity"), dist_t))
            rows.append(_bool_row("is_swing", run, role, phase, day,
                                 "vs_omniscient" if town_lens else "true_fill", d.get("is_swing"), swing_t))
        if "bullets_left" in d and role == "vigilante":
            rows.append(_num_row("bullets_left", run, role, phase, day, "agent_knowable",
                                 d.get("bullets_left"), bullets_t))
        if "ally_revealed" in d and role == "wolf":
            rows.append(_bool_row("ally_revealed", run, role, phase, day, "agent_knowable",
                                 d.get("ally_revealed"), ally_absent_t))
            rows.append(_bool_row("ally_revealed__lynched_variant", run, role, phase, day,
                                 "agent_knowable", d.get("ally_revealed"), ally_lynch_t))
        for enum_field in ("exposure_class", "info_landscape_class", "consensus_direction",
                           "divergence_sign", "my_position"):
            if d.get(enum_field) is not None:
                enums[f"{role}|{enum_field}|{d[enum_field]}"] += 1
    return [r for r in rows if r is not None], enums


# ── Aggregation ──────────────────────────────────────────────────────────────────────────────────
def _mean(xs: list) -> float | None:
    return round(sum(xs) / len(xs), 4) if xs else None


def _summ(rows: list[dict]) -> dict[str, Any]:
    if not rows:
        return {"n": 0}
    kind = rows[0]["kind"]
    out: dict[str, Any] = {"n": len(rows), "exact_acc": _mean([int(r["match"]) for r in rows])}
    if kind == "num":
        out["mae"] = _mean([r["abs_err"] for r in rows])
        out["signed_bias"] = _mean([r["filled"] - r["true"] for r in rows])
    else:
        cm = Counter((r["filled"], r["true"]) for r in rows)  # (filled, true)
        out["confusion"] = {f"filled={f}|true={t}": c for (f, t), c in sorted(cm.items())}
    return out


def _split(rows: list[dict], key: str) -> dict[str, Any]:
    buckets: dict[Any, list] = defaultdict(list)
    for r in rows:
        buckets[r[key]].append(r)
    return {str(k): _summ(v) for k, v in sorted(buckets.items(), key=lambda kv: str(kv[0]))}


def aggregate(all_rows: list[dict]) -> dict[str, Any]:
    dims = sorted({r["dim"] for r in all_rows})
    per_dim: dict[str, Any] = {}
    for dim in dims:
        drows = [r for r in all_rows if r["dim"] == dim]
        per_dim[dim] = {
            "epistemic": drows[0]["epistemic"] if len(set(r["epistemic"] for r in drows)) == 1 else "mixed",
            "overall": _summ(drows),
            "by_role": _split(drows, "role"),
            "by_run": _split(drows, "run"),
            "by_phase": _split(drows, "phase"),
            "by_day": _split(drows, "day"),
        }

    # Gating-granularity: alive_bucket accuracy (the number the gate actually keys on) + is_swing.
    alive_rows = [r for r in all_rows if r["dim"] == "players_alive"]
    bucket_rows = [{**r, "match": _alive_bucket(r["filled"]) == _alive_bucket(r["true"])} for r in alive_rows]
    swing_rows = [r for r in all_rows if r["dim"] == "is_swing"]
    swing_wolf = [r for r in swing_rows if r["role"] == "wolf"]
    swing_town = [r for r in swing_rows if r["role"] in TOWN_ROLES]
    gating = {
        "alive_bucket_acc": {"overall": _mean([int(r["match"]) for r in bucket_rows]),
                             "n": len(bucket_rows), "by_role": _split(bucket_rows, "role")},
        "is_swing_agreement": {
            "wolf_side_true_acc": {"acc": _mean([int(r["match"]) for r in swing_wolf]), "n": len(swing_wolf)},
            "town_side_vs_omniscient": {"acc": _mean([int(r["match"]) for r in swing_town]), "n": len(swing_town)},
        },
    }
    return {"per_dim": per_dim, "gating_granularity": gating}


def decision_rule(gating: dict[str, Any]) -> dict[str, Any]:
    """The PRE-REGISTERED confirm/re-open rule (verbatim from the plan; kappa arm pending Phase 3)."""
    alive_bucket = gating["alive_bucket_acc"]["overall"]
    wolf_swing = gating["is_swing_agreement"]["wolf_side_true_acc"]["acc"]
    gated = {"alive_bucket_acc": alive_bucket, "wolf_side_is_swing_acc": wolf_swing}
    computable = [v for v in gated.values() if v is not None]
    any_below_080 = any(v < 0.80 for v in computable)
    if any_below_080:
        branch = "RE-OPEN"
    elif (alive_bucket is not None and alive_bucket >= 0.90
          and wolf_swing is not None and wolf_swing >= 0.80):
        branch = "CONFIRM (deterministic arm; enum-kappa arm PENDING Phase 3)"
    else:
        branch = "MIDDLE BAND (verdict stands with quantified attenuation caveat)"
    mean_err = _mean([1 - v for v in computable])  # ē over the gated dims we can check
    return {
        "gated_dims_deterministic": gated,
        "kappa_arm": "PENDING — exposure_class / info_landscape_class kappas come from the Phase-3 "
                     "human+pro-LLM spot-check; not computable in this $0 deterministic audit.",
        "branch": branch,
        "mean_gated_error_rate_ebar": mean_err,
        "tilt_attenuation_1_minus_2ebar": round(1 - 2 * mean_err, 4) if mean_err is not None else None,
    }


def stored_side_consistency(store_dir: Path) -> dict[str, Any]:
    """Limitation bound: the STORED (extraction-time) fills are not truth-computable offline, but two
    internal-consistency invariants are cheap — |distance_to_parity| <= players_alive and
    players_alive in [3..9] (the 9-player casting floor is 3)."""
    obs_path = store_dir / "observations.json"
    if not obs_path.exists():
        return {"store": str(store_dir), "error": "observations.json not found"}
    doc = json.loads(obs_path.read_text())
    n = dist_ok = alive_ok = 0
    for entries in doc.get("namespaces", {}).values():
        for e in entries:
            v = e.get("value", {})
            a, dparity = v.get("players_alive"), v.get("distance_to_parity")
            if a is None or dparity is None:
                continue
            n += 1
            dist_ok += int(abs(dparity) <= a)
            alive_ok += int(3 <= a <= 9)
    return {"store": str(store_dir), "n_obs_with_criticality": n,
            "dist_le_alive_frac": round(dist_ok / n, 4) if n else None,
            "alive_in_3_9_frac": round(alive_ok / n, 4) if n else None}


# ── Runner ───────────────────────────────────────────────────────────────────────────────────────
def run_audit(runs: dict[str, list[str]], store_dir: Path, loadout: int) -> dict[str, Any]:
    all_rows: list[dict] = []
    enums: Counter = Counter()
    coverage: dict[str, dict] = {}
    for label, files in runs.items():
        games = cases = with_dims = no_roster = 0
        role_dims: Counter = Counter()
        seen_games: set[str] = set()
        for case, rec, _ in iter_run_cases(files, label):
            gid = rec.get("game_id") or rec.get("trace_id")
            if gid not in seen_games:
                seen_games.add(gid)
                games += 1
            cases += 1
            if case.situation_dimensions:
                with_dims += 1
                role_dims[case.player_role] += 1
                if not case.private_context.surviving_players:
                    no_roster += 1  # criticality truth uncomputable (see rows_for_case)
                rows, e = rows_for_case(case, rec, label, loadout)
                all_rows.extend(rows)
                enums.update(e)
        coverage[label] = {
            "batch_files": len(files), "n_games": games, "n_cases_total": cases,
            "n_cases_with_dims": with_dims,
            "n_dims_cases_no_roster_criticality_uncomputable": no_roster,
            "coverage": round(with_dims / cases, 4) if cases else None,
            "dims_by_role": dict(role_dims),
        }

    agg = aggregate(all_rows)
    enum_dist: dict[str, dict[str, int]] = defaultdict(dict)
    for k, c in enums.items():
        role, field, val = k.split("|", 2)
        enum_dist[f"{role}|{field}"][val] = c
    return {
        "provenance": {
            "git_sha": subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True,
                                      text=True).stdout.strip(),
            "vigilante_loadout_assumed": loadout,
            "coverage_per_run": coverage,
            "n_situation_rows_total": len(all_rows),
        },
        "per_dim": agg["per_dim"],
        "gating_granularity": agg["gating_granularity"],
        "decision_rule": decision_rule(agg["gating_granularity"]),
        "enum_distributions_no_ground_truth": {
            k: dict(sorted(v.items())) for k, v in sorted(enum_dist.items())
        },
        "stored_side_consistency": stored_side_consistency(store_dir),
    }


def _fmt(x: Any) -> str:
    return "  n/a" if x is None else f"{x:>5}" if isinstance(x, int) else f"{x:>5.3f}"


def print_summary(report: dict[str, Any]) -> None:
    print("\n=== v6 DIMENSION-ACCURACY AUDIT (deterministic, $0) ===")
    print(f"git {report['provenance']['git_sha']}  "
          f"situation-rows={report['provenance']['n_situation_rows_total']}")
    print("\ncoverage per run (cases-with-dims / total):")
    for run, c in report["provenance"]["coverage_per_run"].items():
        print(f"  {run:<16} {c['n_cases_with_dims']:>5}/{c['n_cases_total']:<6} "
              f"({(c['coverage'] or 0):.1%})  games={c['n_games']}  {c['dims_by_role']}")
    print("\nper-dimension (overall):")
    print(f"  {'dim':<32} {'epistemic':<14} {'n':>6} {'exact':>7} {'mae':>7}")
    for dim, d in report["per_dim"].items():
        o = d["overall"]
        print(f"  {dim:<32} {d['epistemic']:<14} {o.get('n',0):>6} "
              f"{_fmt(o.get('exact_acc'))} {_fmt(o.get('mae'))}")
    g = report["gating_granularity"]
    print("\ngating-granularity (what the retrieval gate keys on):")
    print(f"  alive_bucket_acc     overall={_fmt(g['alive_bucket_acc']['overall'])}  "
          f"n={g['alive_bucket_acc']['n']}")
    for role, s in g["alive_bucket_acc"]["by_role"].items():
        print(f"      by-role {role:<14} acc={_fmt(s.get('exact_acc'))} n={s['n']}")
    sw = g["is_swing_agreement"]
    print(f"  is_swing wolf-side true acc={_fmt(sw['wolf_side_true_acc']['acc'])} "
          f"n={sw['wolf_side_true_acc']['n']}  |  town-side vs-omniscient="
          f"{_fmt(sw['town_side_vs_omniscient']['acc'])} n={sw['town_side_vs_omniscient']['n']}")
    dr = report["decision_rule"]
    print(f"\nDECISION RULE -> {dr['branch']}")
    print(f"  gated deterministic dims: {dr['gated_dims_deterministic']}")
    print(f"  ebar={dr['mean_gated_error_rate_ebar']}  "
          f"tilt_attenuation(1-2ebar)={dr['tilt_attenuation_1_minus_2ebar']}")
    print(f"  {dr['kappa_arm']}")
    sc = report["stored_side_consistency"]
    print(f"\nstored-side consistency ({sc.get('store')}): "
          f"|dist|<=alive={_fmt(sc.get('dist_le_alive_frac'))} "
          f"alive in[3,9]={_fmt(sc.get('alive_in_3_9_frac'))} n={sc.get('n_obs_with_criticality')}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--store", type=Path, default=Path("memory_stores/v6_1"),
                    help="v6 store for the stored-side internal-consistency bound")
    ap.add_argument("--out", type=Path,
                    default=Path("evidence/phase_b/dimension_accuracy_audit/data"),
                    help="directory for the JSON artifact")
    ap.add_argument("--loadout", type=int, default=GameConfig.model_fields["vigilante_bullets"].default,
                    help="vigilante bullet loadout (game_config is not persisted; defaults to the "
                    "GameConfig default, same as compute_metrics)")
    ap.add_argument("--regen", action="store_true",
                    help="OPTIONAL PAID ARM (regenerate ~200 query fills on ab_* cases via live LLM "
                    "calls to audit parity with the gating screen's query path). THIS SPENDS MONEY — "
                    "it is intentionally gated and NOT implemented as an auto-run; requires sign-off.")
    args = ap.parse_args()

    if args.regen:
        raise SystemExit(
            "REFUSED: --regen spends money (live LLM regeneration of ~200 query-side fills, ~$1). "
            "The deterministic audit is $0 and is what this pass runs. Re-generation parity is a "
            "separately-approved paid arm — get explicit sign-off, then wire the regeneration path."
        )

    report = run_audit(DEFAULT_RUNS, args.store, args.loadout)
    args.out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = args.out / f"dimension_audit_{stamp}.json"
    out_path.write_text(json.dumps(report, indent=2))
    print_summary(report)
    print(f"\nartifact -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
