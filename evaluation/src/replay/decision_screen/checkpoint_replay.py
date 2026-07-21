"""Checkpoint replay — the compounding question's low-noise readout: one fixed exam,
scored against each generation's store snapshot from a loop run.

The question
------------
Does the loop's store get BETTER as it grows — and do agents CONSEQUENTLY decide
better? The live loop re-rolls a game's worth of luck every generation (fresh
ON/OFF matches; one diverging vote cascades through the whole game), so a
per-generation slope drowns in noise (see evidence/execution_plan/power_analysis/).
This replay freezes the boards ONCE and varies only the store, so the only thing
moving across the curve is the memory.

The arms design (what the curve separates)
-------------------------------------------
Arms = an EMPTY store (no-memory control) + each generation snapshot gen1..genN.
Reading the curve left to right:

    empty ─────► gen1 ─────► ... ─────► genN
      |            |                      |
      +-- STATIC --+                      |
      value of a one-shot seeded store    |
                   +----- LOOP GROWTH -----+
                   the compounding the loop is supposed to produce

So gen1 doubles as the static-store baseline: empty→gen1 is the static replication
(does a seeded store help at all?), gen1→genN is the loop's compounding (does
iterating help beyond the seed?). The pre-registered PRIMARY comparison is the
paired gen-final vs gen-1 McNemar; empty vs gen-1 is the secondary static check.

The two traps designed out (both from prior scar tissue)
--------------------------------------------------------
1. Model drift. If gen-1 and gen-N snapshots are scored under different API epochs,
   the curve confounds store-progress with drift. So the whole sweep runs in ONE
   process, one day, one backend, and iterates CASE-MAJOR (for each case, all arms
   are scored back-to-back) — temporal drift is then common-mode within a case and
   cannot correlate with the snapshot index. The old recorded loop results are never
   compared against; only these fresh same-batch replays are.
2. Same-game leakage. If a case comes from a game the loop later trained on, a
   gen-k store already contains observations extracted from that very game — the leak
   that manufactured the criticality screen's fake +0.25 endgame signature. So cases
   are drawn from a HELD-OUT corpus (v6ab, the v6 epoch that never fed the v7 loop),
   AND a leakage guard asserts no selected case's game_id appears in any snapshot's
   observation provenance, refusing to run (loud, listing offenders) otherwise.

What is frozen vs live
----------------------
FROZEN per case: the board, the visible discussion, and the retrieval QUERY
(``case.situations``, recorded in the game — never regenerated, so the query text is
identical across every arm). LIVE per (case, arm): the embedding search against that
arm's rebuilt snapshot store (production-pinned: raw retrieval, top_k=5, cap 3 per
situation, no rerank/filter/dimension-gating — the loop's default read path), then the
production decision prompt regenerates the vote/target, scored MECHANICALLY (de-lucked
against true roles):

- DAY VOTES — town lens (correct = hits a real threat) for town roles, deceiver lens
  (correct = induces a mislynch) for wolf/SK.
- NIGHT ACTIONS — the loop's own role-aware credit lens ``_night_credit`` (REUSED from
  ``evaluation/src/loop/credit_backfill.py`` — the same lens the loop's credit path
  grades with, not a copy): investigator positive on a threat-hit, vigilante positive
  on a threat-shot / NEGATIVE on friendly fire, wolf/SK positive on a power-or-threat
  kill, hold/abstain neutral.

Verdict mapping (decided, pre-registered) — the sweep reports TWO readouts:
1. McNemar correctness pairing: ``correct = (verdict == "positive")`` — neutral and
   negative both count as not-correct (banking the action must not pair-flip as a win).
2. The curve table ALSO carries the raw −1/0/+1 mean per ``VERDICT_VALUE``
   (measure.py's convention), so a friendly-fire regression stays visible even where
   the positive-rate is flat. Day votes carry the matching value
   (+1 correct / 0 abstain / −1 otherwise). Both numbers land in the artifact.

Role coverage: ``--factions town`` exams day-votes (villager/healer/investigator)
PLUS night actions for investigator/vigilante/healer — ALL through the loop's own
``_night_credit`` (healer included since its 2026-07-13 promotion into production credit:
the loop lens IS the validated ``healer_town_save_rate`` construct, scored off the
``night_resolutions`` attack-join this screen already performs). The screen-local
``_healer_night_credit`` lens this file used to carry was DELETED at that promotion — its
gate ("healer isn't in production credit yet") closed, and one grader beats two that can
drift. A missing night_resolutions row degrades to neutral here (the replay must never
crash on a sparse record); the loop's credit path skips such cases instead.
Villagers have no night action. Historical dry run (v6ab_townsp): 64 healer night cases
joined their night_resolutions entry cleanly (94/94 day-join hit).

Run command
-----------
    poetry run eval-checkpoint-replay \\
        --cases batch_results/v6ab_townsp.jsonl \\
        --run evidence/v7_final/runs/town_only_run2 \\
        --n 100 --factions town \\
        --out evidence/execution_plan/checkpoint_replay/

``--run`` auto-discovers the ``gen*_store/`` snapshots under a loop-run directory;
``--snapshot label=path`` can name them explicitly instead. Results (a markdown
summary + a JSON artifact with a provenance manifest) land in
``evidence/execution_plan/checkpoint_replay/`` by default.

Cost
----
The town exam pool = day-votes PLUS investigator/vigilante/healer nights (the pool grew
with the night lenses, but ``--n`` still caps the exam): ~100 cases x ~11 arms (empty +
gen1..gen10) ≈ 1100 flash-lite decision calls ≈ $3–4, plus the retrieval embedding
calls (each arm's store is embedded once at load; each case's frozen situations are
embedded per arm). Tests stub both the decision LLM and retrieval — the paid sweep
runs later on user sign-off.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, OrderedDict
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from Agents.memory import (
    RETRIEVAL_KEEP_PER_SITUATION,
    retrieve_observations_for_agent,
    retrieve_strategy_points_for_agent,
)
from Agents.memory.retrieval import cap_per_situation
from Agents.run_fingerprint import git_revision
from Agents.schemas.evaluation import EvalCase
from evaluation.src.data.sources.sidecar import LocalCaseSource
from evaluation.src.loop.credit_backfill import (
    NIGHT_CREDIT_ROLES,
    VERDICT_VALUE,
    _night_credit,
)
from evaluation.src.loop.decision_scoring import (
    REPLAYABLE_DECEIVER_ROLES,
    REPLAYABLE_TOWN_ROLES,
    allow_abstain_for,
    score_vote,
    wolf_vote_is_good,
)
from evaluation.src.replay.decision_screen.cases import load_game_index
from evaluation.src.replay.decision_screen.replay import _replay_night, _replay_vote
from evaluation.src.replay.decision_screen.stats import mcnemar_p

# Production-default read path (Agents.memory.retrieval.pipeline non-wide branch):
# raw embedding search top_k=5, then cap RETRIEVAL_KEEP_PER_SITUATION per situation,
# no rerank / filter / dimension-gating (all default-off in the loop). The sweep pins
# to this so the only thing varying across arms is the STORE, not the read config.
PROD_RETRIEVAL_TOP_K = 5

EMPTY_ARM = "empty"


class CheckpointLeakageError(RuntimeError):
    """A selected case's game_id appears in a snapshot's observation provenance —
    the same-game leak the held-out design exists to prevent. Fail loud, never run."""


# ---------------------------------------------------------------------------
# case selection — situations-based (the frozen retrieval query), day-stratified
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _CasePlan:
    """One (phase, roles, scoring-lens) slice of the case set."""

    phase: str
    roles: frozenset[str]
    lens: str  # day votes: "town" | "wolf"; night actions: "night_credit"


# Town night actions the screen grades — every one through the loop's own credit lens
# (healer joined NIGHT_CREDIT_ROLES 2026-07-13; the screen-local healer lens was deleted at
# that promotion — module docstring). villagers have no night action.
TOWN_NIGHT_ROLES = frozenset({"investigator", "vigilante", "healer"})
# Honesty guard: every town-night role the screen exams IS graded by the loop's lens.
assert TOWN_NIGHT_ROLES <= NIGHT_CREDIT_ROLES

# What a faction run exams. town = day-votes on the town lens (the pending town-only
# rerun's target) + investigator/vigilante nights on the loop's credit lens.
# deceiver = wolf/SK day-votes (deceiver lens) + their nights (same credit lens).
FACTION_PLANS: dict[str, list[_CasePlan]] = {
    "town": [
        _CasePlan("day_vote", REPLAYABLE_TOWN_ROLES, "town"),
        _CasePlan("night_action", TOWN_NIGHT_ROLES, "night_credit"),
    ],
    "deceiver": [
        _CasePlan("day_vote", REPLAYABLE_DECEIVER_ROLES, "wolf"),
        _CasePlan("night_action", REPLAYABLE_DECEIVER_ROLES, "night_credit"),
    ],
}
FACTION_PLANS["both"] = FACTION_PLANS["town"] + FACTION_PLANS["deceiver"]


@dataclass
class _CaseSpec:
    """A selected exam item: the frozen case, its ground-truth game, and the lens
    its regenerated decision is scored under."""

    case: EvalCase
    game: dict[str, Any]
    lens: str


def _iter_query_cases(
    batch_path: Path, roles: frozenset[str], phase: str
) -> Iterator[tuple[EvalCase, dict[str, Any]]]:
    """Yield (case, game) for every decision in the phase/roles that carries a frozen
    retrieval query (``situations``). Unlike ``cases.iter_cases`` this filters on
    ``situations`` (the query we re-retrieve with), NOT on recorded retrieved memory —
    the sweep re-retrieves from each snapshot, so an SP-only source arm (retrieved_obs
    empty but situations present, e.g. v6ab_townsp) is fully usable."""
    source = LocalCaseSource(batch_path)
    index = load_game_index(batch_path)
    for tid in source.trace_ids():
        game = index.get(tid)
        if not game:
            continue
        for case in source.eval_cases(tid):
            if case.action_phase != phase:
                continue
            if case.player_role not in roles:
                continue
            if not case.situations:
                continue
            yield case, game


def _stratify(
    pool: list[tuple[EvalCase, dict[str, Any]]], n: int, seed: int
) -> list[tuple[EvalCase, dict[str, Any]]]:
    """Round-robin across days (each day up to its availability), and within a day
    across games — the same day-stratified, cross-game spread as cases._select_diverse,
    so early days don't dominate. Each game's own cases are also (seeded-)shuffled:
    the depth-0 walk otherwise always takes a game's FIRST case in file order, which
    collapses mixed-role pools to whichever role serializes first (measured: a 67/23
    vigilante/investigator night pool selected 47/3 without it). Deterministic given
    seed."""
    import random

    by_day: dict[int, OrderedDict[str, list[tuple[EvalCase, dict[str, Any]]]]] = {}
    for case, game in pool:
        by_day.setdefault(case.day, OrderedDict()).setdefault(
            str(game["game_id"]), []
        ).append((case, game))

    rng = random.Random(seed)
    day_queues: dict[int, list[tuple[EvalCase, dict[str, Any]]]] = {}
    for day, games in by_day.items():
        game_pools = list(games.values())
        rng.shuffle(game_pools)
        for game_pool in game_pools:
            rng.shuffle(game_pool)  # unbias the depth-0 pick from file order
        queue: list[tuple[EvalCase, dict[str, Any]]] = []
        depth = 0
        while any(len(p) > depth for p in game_pools):
            for p in game_pools:
                if len(p) > depth:
                    queue.append(p[depth])
            depth += 1
        day_queues[day] = queue

    days = sorted(day_queues)
    picked: list[tuple[EvalCase, dict[str, Any]]] = []
    idx = 0
    while len(picked) < n and any(idx < len(day_queues[d]) for d in days):
        for d in days:
            if idx < len(day_queues[d]):
                picked.append(day_queues[d][idx])
                if len(picked) >= n:
                    break
        idx += 1
    return picked


def select_cases(
    batch_path: Path,
    n: int,
    factions: str,
    min_day: int = 2,
    seed: int = 0,
) -> list[_CaseSpec]:
    """Select ~n exam cases from the held-out batch for the faction config,
    day-stratified within each (phase, roles) plan. min_day=2 skips day-1 decisions,
    matching the loop's scoring convention (loop.measure skip_day1=True)."""
    plans = FACTION_PLANS.get(factions)
    if plans is None:
        raise ValueError(f"unknown factions '{factions}'; choose {sorted(FACTION_PLANS)}")
    pools = [
        [
            (c, g)
            for c, g in _iter_query_cases(batch_path, plan.roles, plan.phase)
            if c.day >= min_day
        ]
        for plan in plans
    ]
    # Even quota per plan; a plan whose pool is short (e.g. few night decisions per
    # game) hands its unused quota to the other plans, so the exam stays ~n.
    per_plan = max(1, n // len(plans))
    takes = [min(per_plan, len(pool)) for pool in pools]
    leftover = n - sum(takes)
    for i, pool in enumerate(pools):
        if leftover <= 0:
            break
        extra = min(leftover, len(pool) - takes[i])
        takes[i] += extra
        leftover -= extra
    specs: list[_CaseSpec] = []
    for plan, pool, take in zip(plans, pools, takes):
        for case, game in _stratify(pool, take, seed):
            specs.append(_CaseSpec(case=case, game=game, lens=plan.lens))
    return specs


def case_set_hash(specs: list[_CaseSpec]) -> str:
    """Stable identity of the exam: sha256 over sorted (game_id, player_id, day,
    phase, lens) — pins WHICH decisions were graded, for the provenance manifest."""
    keyed = sorted(
        f"{s.game['game_id']}|{s.case.player_id}|{s.case.day}|{s.case.action_phase}|{s.lens}"
        for s in specs
    )
    return hashlib.sha256("\n".join(keyed).encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# snapshots — rebuild each generation's store + read its observation provenance
# ---------------------------------------------------------------------------


@dataclass
class _Snapshot:
    label: str
    directory: Path
    game_ids: frozenset[str]  # provenance for the leakage guard
    store: Any  # rebuilt InMemoryStore (None until loaded)


def discover_snapshots(run_dir: Path) -> list[tuple[str, Path]]:
    """Find ``gen<N>_store/`` snapshot directories under a loop-run dir, sorted by
    generation. Skips the mixed ``gen<N>_on_store_g*`` per-game dumps."""
    found: list[tuple[int, str, Path]] = []
    for child in run_dir.iterdir():
        if not child.is_dir():
            continue
        name = child.name
        if name.startswith("gen") and name.endswith("_store") and "_on_store" not in name:
            digits = "".join(ch for ch in name[3:] if ch.isdigit())
            if digits and (child / "observations.json").exists():
                found.append((int(digits), name.replace("_store", ""), child))
    return [(label, path) for _, label, path in sorted(found)]


def _snapshot_game_ids(directory: Path) -> frozenset[str]:
    """All non-empty source game_ids across a snapshot's observation + SP files —
    the provenance the leakage guard checks. (Synthesized SPs carry an empty game_id,
    so observations are the reliable source; SPs are folded in defensively.)"""
    ids: set[str] = set()
    for filename in ("observations.json", "strategy_points.json"):
        path = directory / filename
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for items in payload.get("namespaces", {}).values():
            for item in items:
                gid = (item.get("value") or {}).get("game_id")
                if gid:
                    ids.add(str(gid))
    return frozenset(ids)


def assert_no_leakage(specs: list[_CaseSpec], snapshots: list[_Snapshot]) -> None:
    """Refuse to run if any selected case's game fed any snapshot's store."""
    case_game_ids = {str(s.game["game_id"]) for s in specs}
    offenders: list[str] = []
    for snap in snapshots:
        overlap = sorted(case_game_ids & snap.game_ids)
        if overlap:
            offenders.append(f"{snap.label}: {len(overlap)} game(s) {overlap[:5]}")
    if offenders:
        raise CheckpointLeakageError(
            "same-game leakage — selected exam games appear in snapshot provenance; "
            "draw cases from a held-out corpus:\n  " + "\n  ".join(offenders)
        )


# ---------------------------------------------------------------------------
# retrieval (production-pinned) + one decision, scored
# ---------------------------------------------------------------------------


def _retrieve_for_case(
    store: Any, case: EvalCase, top_k: int, keep: int, retrieval_types: str = "both"
) -> tuple[list[Any], list[Any]]:
    """Live embedding search of the frozen query (``case.situations``) against one
    snapshot store, pinned to the loop's production read config. ``retrieval_types``
    mirrors run_batch's injection knob (RETRIEVAL_TYPES_CONFIGS names): the v7 loop runs
    "strategy_points_only" (obs are synthesis substrate, never injected — store_curation
    report §6.8), so a sweep matched to a v7 condition must pin it; "both" = the
    v5/v6-era default this screen originally shipped with."""
    observations: list[Any] = []
    if retrieval_types != "strategy_points_only":
        observations = cap_per_situation(
            retrieve_observations_for_agent(
                store, case.player_role, case.action_phase, case.situations, top_k=top_k
            ),
            get_situation=lambda o: o.matched_situation,
            get_score=lambda o: o.score or 0.0,
            keep=keep,
        )
    strategy_points: list[Any] = []
    if retrieval_types != "observations_only":
        strategy_points = cap_per_situation(
            retrieve_strategy_points_for_agent(
                store, case.player_role, case.action_phase, case.situations, top_k=top_k
            ),
            get_situation=lambda sp: sp.matched_situation,
            get_score=lambda sp: sp.score or 0.0,
            keep=keep,
        )
    return observations, strategy_points


def _night_res_for_day(game: dict[str, Any], day: int) -> dict[str, Any] | None:
    """The ``night_resolutions`` entry for ``day`` (the healer attack-join), or None if
    absent. Joins by ``day`` directly — the same key the loop's tagger uses to attach
    night deaths (loop/discussion_tagger.py:242) and the vote router uses for abstain
    recovery — so a night_action case at ``case.day`` maps to that night's resolution."""
    for nr in game.get("night_resolutions") or []:
        if nr.get("day") == day:
            return nr
    return None


def _decide_and_score(
    spec: _CaseSpec, observations: list[Any], strategy_points: list[Any]
) -> dict[str, Any] | None:
    """Regenerate one decision with the injected memory and de-luck score it against
    true roles. Returns {"correct": bool, "value": float} — correct feeds the McNemar
    pairing, value is the raw −1/0/+1 verdict mean for the curve (see docstring's
    verdict mapping). None = the replay dropped the call (excluded from the pairing,
    never miscounted as a miss).

    Night actions all score through the loop's own role-aware credit lens
    (credit_backfill._night_credit) — healer included since its 2026-07-13 promotion, via
    the night_resolutions attack-join this screen performs; a missing row degrades to
    neutral (the replay never crashes on a sparse record; the loop's credit path skips
    instead). correct = positive verdict; neutral (banked/plain-townie kill/unattacked
    protect) and negative (vigilante friendly fire / shielded threat) are both not-correct."""
    case, roles = spec.case, spec.game["roles"]
    if case.action_phase == "night_action":
        target = _replay_night(case, observations, strategy_points=strategy_points)
        if target is None:
            return None
        night_res = _night_res_for_day(spec.game, case.day)
        verdict = _night_credit(case.player_role, target, roles, night_res) or "neutral"
        return {"correct": verdict == "positive", "value": VERDICT_VALUE[verdict]}
    allow = allow_abstain_for(case.day, spec.game["day_resolutions"])
    votee, _ = _replay_vote(
        case, observations, allow, strategy_points=strategy_points
    )
    if votee is None:
        return None
    outcome = score_vote(votee, roles)
    correct = wolf_vote_is_good(outcome) if spec.lens == "wolf" else outcome.hit_threat
    value = 1.0 if correct else (0.0 if outcome.is_abstain else -1.0)
    return {"correct": bool(correct), "value": value}


def _replay_case_all_arms(
    spec: _CaseSpec,
    arm_order: list[str],
    stores: dict[str, Any],
    top_k: int,
    keep: int,
    retrieval_types: str = "both",
) -> dict[str, dict[str, Any] | None]:
    """Score ONE case across every arm back-to-back (case-major anti-drift). The
    empty arm injects [] (no retrieval); each snapshot arm re-retrieves from its store."""
    results: dict[str, dict[str, Any] | None] = {}
    for arm in arm_order:
        if arm == EMPTY_ARM:
            observations, strategy_points = [], []
        else:
            observations, strategy_points = _retrieve_for_case(
                stores[arm], spec.case, top_k, keep, retrieval_types
            )
        results[arm] = _decide_and_score(spec, observations, strategy_points)
    return results


def run_sweep(
    specs: list[_CaseSpec],
    arm_order: list[str],
    stores: dict[str, Any],
    top_k: int = PROD_RETRIEVAL_TOP_K,
    keep: int = RETRIEVAL_KEEP_PER_SITUATION,
    max_workers: int = 6,
    retrieval_types: str = "both",
) -> list[dict[str, dict[str, Any] | None]]:
    """Run the full case-major sweep. Cases run concurrently (I/O-bound), but each
    case's arms are scored together inside one worker, so drift stays common-mode
    within a case and cannot align with the snapshot index. Returns one
    arm -> {correct, value} dict per case, in case order (identical case set across
    every arm → paired)."""
    if max_workers <= 1:
        return [
            _replay_case_all_arms(spec, arm_order, stores, top_k, keep, retrieval_types)
            for spec in specs
        ]
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = [
            ex.submit(
                _replay_case_all_arms, spec, arm_order, stores, top_k, keep, retrieval_types
            )
            for spec in specs
        ]
        return [f.result() for f in futures]


# ---------------------------------------------------------------------------
# stats / readout
# ---------------------------------------------------------------------------


def _paired_mcnemar(
    per_case: list[dict[str, dict[str, Any] | None]], before: str, after: str
) -> dict[str, Any]:
    """Exact McNemar over discordant pairs of two arms (both scored on the same case),
    on the CORRECT bool (night: verdict==positive — see the verdict mapping).
    hurt = before-correct & after-wrong; helped = after-correct & before-wrong."""
    hurt = helped = 0
    for res in per_case:
        b, a = res.get(before), res.get(after)
        if b is None or a is None:
            continue
        b_ok, a_ok = b["correct"], a["correct"]
        if b_ok and not a_ok:
            hurt += 1
        elif a_ok and not b_ok:
            helped += 1
    return {
        "before": before,
        "after": after,
        "helped": helped,
        "hurt": hurt,
        "mcnemar_p": round(mcnemar_p(hurt, helped), 4),
    }


def summarize(
    per_case: list[dict[str, dict[str, Any] | None]], arm_order: list[str]
) -> dict[str, Any]:
    """Per-arm readout on the identical case set — BOTH numbers of the verdict
    mapping: accuracy (positive-rate, the McNemar convention) and mean_value (the raw
    −1/0/+1 mean, measure.py's VERDICT_VALUE convention) — plus the pre-registered
    paired tests."""
    agg: dict[str, Counter] = {arm: Counter() for arm in arm_order}
    value_sum: dict[str, float] = {arm: 0.0 for arm in arm_order}
    for res in per_case:
        for arm in arm_order:
            v = res.get(arm)
            if v is None:
                continue
            agg[arm]["n"] += 1
            agg[arm]["hits"] += int(v["correct"])
            value_sum[arm] += v["value"]
    curve = {
        arm: {
            "n": agg[arm]["n"],
            "accuracy": (
                round(agg[arm]["hits"] / agg[arm]["n"], 3) if agg[arm]["n"] else None
            ),
            "mean_value": (
                round(value_sum[arm] / agg[arm]["n"], 3) if agg[arm]["n"] else None
            ),
        }
        for arm in arm_order
    }
    snapshot_arms = [a for a in arm_order if a != EMPTY_ARM]
    out: dict[str, Any] = {
        "n_cases": len(per_case),
        "arm_order": arm_order,
        "curve": curve,
    }
    if len(snapshot_arms) >= 2:
        # PRIMARY: does loop growth help? gen-final vs gen-1, paired.
        out["primary_gen_final_vs_gen1"] = _paired_mcnemar(
            per_case, snapshot_arms[0], snapshot_arms[-1]
        )
    if snapshot_arms and EMPTY_ARM in arm_order:
        # SECONDARY: static replication — does a seeded store help at all?
        out["secondary_empty_vs_gen1"] = _paired_mcnemar(
            per_case, EMPTY_ARM, snapshot_arms[0]
        )
    return out


# ---------------------------------------------------------------------------
# orchestration + artifacts
# ---------------------------------------------------------------------------


def _load_snapshots(snapshot_dirs: list[tuple[str, Path]]) -> list[_Snapshot]:
    """Read each snapshot's provenance and rebuild its store (embeds all items once)."""
    from evaluation.src.replay.retrieval import build_store_from_snapshots

    snapshots: list[_Snapshot] = []
    for label, directory in snapshot_dirs:
        print(f"Loading snapshot '{label}' from {directory}", flush=True)
        store = build_store_from_snapshots(
            directory / "observations.json", directory / "strategy_points.json"
        )
        snapshots.append(
            _Snapshot(
                label=label,
                directory=directory,
                game_ids=_snapshot_game_ids(directory),
                store=store,
            )
        )
    return snapshots


def _manifest(
    cases_path: Path,
    specs: list[_CaseSpec],
    snapshots: list[_Snapshot],
    top_k: int,
    keep: int,
    factions: str,
    retrieval_types: str = "both",
) -> dict[str, Any]:
    """Provenance stamp: git SHA, the pinned retrieval config, the case-set hash, and
    the snapshot source paths — the pointer back to what produced this readout."""
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        **git_revision(),
        "cases_batch": str(cases_path),
        "factions": factions,
        "case_set_hash": case_set_hash(specs),
        "n_cases": len(specs),
        "retrieval_config": {
            "pinned_to": "loop production read path (raw, non-wide)",
            "top_k": top_k,
            "keep_per_situation": keep,
            "retrieval_types": retrieval_types,
            "rerank": False,
            "filter": False,
            "dimension_gating": False,
        },
        "snapshots": [
            {"label": s.label, "path": str(s.directory), "n_source_games": len(s.game_ids)}
            for s in snapshots
        ],
    }


def _render_markdown(result: dict[str, Any]) -> str:
    """A skimmable summary: the manifest header, the per-arm curve, and the two tests."""
    m = result["manifest"]
    s = result["summary"]
    lines = [
        "# Checkpoint replay — compounding readout",
        "",
        f"- cases: `{m['cases_batch']}` (factions={m['factions']}, N={s['n_cases']})",
        f"- git: `{m['git_commit']}`{' (dirty)' if m.get('git_dirty') else ''}",
        f"- retrieval: {m['retrieval_config']['pinned_to']} "
        f"(top_k={m['retrieval_config']['top_k']}, "
        f"keep={m['retrieval_config']['keep_per_situation']}, rerank=off)",
        f"- case-set hash: `{m['case_set_hash']}`",
        "",
        "## Curve (per-arm, identical case set — both verdict-mapping readouts)",
        "",
        "accuracy = positive-rate (the McNemar correctness convention: night neutral/",
        "negative count as not-correct); mean value = raw −1/0/+1 verdict mean",
        "(VERDICT_VALUE convention), which keeps friendly-fire regressions visible.",
        "",
        "| arm | N | accuracy | mean value (−1..+1) |",
        "| --- | --- | --- | --- |",
    ]
    for arm in s["arm_order"]:
        c = s["curve"][arm]
        lines.append(f"| {arm} | {c['n']} | {c['accuracy']} | {c['mean_value']} |")
    lines.append("")
    if "primary_gen_final_vs_gen1" in s:
        p = s["primary_gen_final_vs_gen1"]
        lines += [
            "## PRIMARY — loop growth (gen-final vs gen-1, paired McNemar)",
            "",
            f"- {p['after']} helped={p['helped']}, hurt={p['hurt']} → "
            f"p={p['mcnemar_p']}",
            "",
        ]
    if "secondary_empty_vs_gen1" in s:
        p = s["secondary_empty_vs_gen1"]
        lines += [
            "## SECONDARY — static store (empty vs gen-1, paired McNemar)",
            "",
            f"- gen1 helped={p['helped']}, hurt={p['hurt']} → p={p['mcnemar_p']}",
            "",
        ]
    return "\n".join(lines)


def run_checkpoint_replay(
    cases_path: Path,
    snapshot_dirs: list[tuple[str, Path]],
    out_dir: Path,
    n: int = 100,
    factions: str = "town",
    min_day: int = 2,
    top_k: int = PROD_RETRIEVAL_TOP_K,
    keep: int = RETRIEVAL_KEEP_PER_SITUATION,
    max_workers: int = 6,
    seed: int = 0,
    retrieval_types: str = "both",
) -> dict[str, Any]:
    """Full sweep: select the exam, load snapshots, guard against leakage, replay
    case-major, summarize, and write the JSON + markdown artifacts. Makes real LLM /
    embedding calls (the paid sweep); tests exercise the pieces with stubs."""
    specs = select_cases(cases_path, n, factions, min_day=min_day, seed=seed)
    if not specs:
        raise ValueError(f"no exam cases selected from {cases_path} for factions={factions}")
    snapshots = _load_snapshots(snapshot_dirs)
    assert_no_leakage(specs, snapshots)

    arm_order = [EMPTY_ARM] + [s.label for s in snapshots]
    stores = {s.label: s.store for s in snapshots}
    print(
        f"Sweeping {len(specs)} cases x {len(arm_order)} arms "
        f"({', '.join(arm_order)})",
        flush=True,
    )
    per_case = run_sweep(specs, arm_order, stores, top_k, keep, max_workers, retrieval_types)
    summary = summarize(per_case, arm_order)
    result = {
        "manifest": _manifest(cases_path, specs, snapshots, top_k, keep, factions,
                              retrieval_types),
        "summary": summary,
        "per_case": per_case,
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = out_dir / f"checkpoint_replay_{factions}_{stamp}.json"
    md_path = out_dir / f"checkpoint_replay_{factions}_{stamp}.md"
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(result), encoding="utf-8")
    print(f"Wrote {json_path}\nWrote {md_path}", flush=True)
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_snapshot_args(
    run_dir: Path | None, snapshot_specs: list[str] | None
) -> list[tuple[str, Path]]:
    if snapshot_specs:
        out: list[tuple[str, Path]] = []
        for spec in snapshot_specs:
            label, _, path = spec.partition("=")
            if not path:
                raise ValueError(f"--snapshot expects label=path, got '{spec}'")
            out.append((label, Path(path)))
        return out
    if run_dir:
        found = discover_snapshots(run_dir)
        if not found:
            raise ValueError(f"no gen*_store/ snapshots found under {run_dir}")
        return found
    raise ValueError("pass --run <loop_run_dir> or one or more --snapshot label=path")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Replay a fixed decision exam against each loop-generation store snapshot."
    )
    parser.add_argument(
        "--cases", type=Path, required=True,
        help="Held-out batch jsonl whose frozen cases carry the retrieval query (e.g. batch_results/v6ab_townsp.jsonl).",
    )
    parser.add_argument("--run", type=Path, default=None, help="Loop-run dir to auto-discover gen*_store snapshots.")
    parser.add_argument("--snapshot", action="append", default=None, help="Explicit label=path snapshot (repeatable).")
    parser.add_argument("--out", type=Path, default=Path("evidence/execution_plan/checkpoint_replay"))
    parser.add_argument("--n", type=int, default=100)
    parser.add_argument("--factions", default="town", choices=sorted(FACTION_PLANS))
    parser.add_argument("--min-day", type=int, default=2)
    parser.add_argument("--top-k", type=int, default=PROD_RETRIEVAL_TOP_K)
    parser.add_argument("--max-workers", type=int, default=6)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--retrieval-types", default="both",
                        choices=["both", "strategy_points_only", "observations_only"],
                        help="Injection mode per arm (run_batch's knob): pin "
                             "strategy_points_only to match a v7 SP-only condition.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    snapshot_dirs = _parse_snapshot_args(args.run, args.snapshot)
    run_checkpoint_replay(
        cases_path=args.cases,
        snapshot_dirs=snapshot_dirs,
        out_dir=args.out,
        n=args.n,
        factions=args.factions,
        min_day=args.min_day,
        top_k=args.top_k,
        max_workers=args.max_workers,
        seed=args.seed,
        retrieval_types=args.retrieval_types,
    )


if __name__ == "__main__":
    main()
