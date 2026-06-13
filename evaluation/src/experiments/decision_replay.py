"""Decision-replay screen for memory framing — observational pass (Step 1).

Loads frozen town day_vote decisions from a batch's eval-case sidecars, scores
each RECORDED vote against the game's true roles, and validates the
``allow_abstain`` reconstruction against the votes that actually happened. This
is the no-LLM foundation/smoke: it proves the case loader, the roles join, and
the abstain recovery before any LLM replay.

The causal arms (swap the injected memory and/or the prompt -> regenerate the
vote -> re-score) build on the same scoring (``decision_scoring``) plus the
existing single-decision replay harness
(``evaluation.src.components.application.run_application_action``).

Run: ``poetry run python evaluation/src/experiments/decision_replay.py \
        --batch batch_results/ab_nh_town.jsonl``
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, OrderedDict
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from math import comb
from pathlib import Path
from typing import Any

from Agents.schemas import DayVote
from Agents.schemas.evaluation import EvalCase
from Agents.turn import _run_agent
from evaluation.src.components.application import (
    action_spec_for,
    application_case_for_judge,
)
from evaluation.src.components.decision_scoring import (
    REPLAYABLE_TOWN_ROLES,
    allow_abstain_for,
    score_vote,
)
from evaluation.src.components.memory_adherence import (
    DEFAULT_ADHERENCE_JUDGE_MODEL,
    judge_decision_adherence,
    summarize_adherence,
)
from evaluation.src.components.situation_summary import eval_case_to_agent_payload
from evaluation.src.data.local_cases import LocalCaseSource


def load_game_index(batch_path: Path) -> dict[str, dict[str, Any]]:
    """Map trace_id -> the ground truth a vote is scored against (roles +
    day_resolutions for abstain recovery), read straight from the batch records."""
    index: dict[str, dict[str, Any]] = {}
    with batch_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            tid = rec.get("trace_id")
            if not tid:
                continue
            index[tid] = {
                "game_id": rec.get("game_id"),
                "roles": rec.get("roles", {}) or {},
                "day_resolutions": rec.get("day_resolutions", []) or [],
                "winner": rec.get("winner"),
            }
    return index


def iter_town_vote_cases(
    batch_path: Path, roles: frozenset[str] = REPLAYABLE_TOWN_ROLES
) -> Iterator[tuple[EvalCase, dict[str, Any]]]:
    """Yield (case, game_info) for every replay-able day_vote decision with
    retrieved memory in the batch, for the given roles — the unit the screen
    scores. Defaults to the town roles; pass {'wolf'} for the deceiver day-vote."""
    source = LocalCaseSource(batch_path)
    index = load_game_index(batch_path)
    for tid in source.trace_ids():
        game = index.get(tid)
        if not game:
            continue
        for case in source.eval_cases(tid):
            if case.action_phase != "day_vote":
                continue
            if case.player_role not in roles:
                continue
            if not case.retrieved_observations:
                continue
            yield case, game


def _abstained_on_day(day: int, day_resolutions: list[dict]) -> bool:
    for res in day_resolutions:
        if res.get("day") == day:
            return any(v.get("votee") == "abstain" for v in res.get("votes", []))
    return False


def run_observational(batch_path: Path) -> dict[str, Any]:
    """Score recorded town votes against truth + validate abstain recovery."""
    cases = list(iter_town_vote_cases(batch_path))
    n = len(cases)
    hits = mislynch = abstain = allow_false = 0
    by_role: Counter[str] = Counter()
    by_role_hit: Counter[str] = Counter()
    by_day: Counter[int] = Counter()
    by_day_hit: Counter[int] = Counter()
    violations: list[dict[str, Any]] = []

    for case, game in cases:
        out = score_vote(case.agent_vote.votee if case.agent_vote else None, game["roles"])
        hits += out.hit_threat
        mislynch += out.is_town_mislynch
        abstain += out.is_abstain
        by_role[case.player_role] += 1
        by_role_hit[case.player_role] += out.hit_threat
        by_day[case.day] += 1
        by_day_hit[case.day] += out.hit_threat

        allow = allow_abstain_for(case.day, game["day_resolutions"])
        allow_false += not allow
        # Reconstructed "abstain not offered" but the day actually had an abstain
        # vote => the recovery is wrong.
        if not allow and _abstained_on_day(case.day, game["day_resolutions"]):
            violations.append({"game_id": game["game_id"], "day": case.day})

    pct = lambda a, b: round(a / b, 3) if b else None  # noqa: E731
    return {
        "batch": batch_path.name,
        "n_cases": n,
        "vote_accuracy": pct(hits, n),
        "mislynch_rate": pct(mislynch, n),
        "abstain_rate": pct(abstain, n),
        "by_role": {
            r: {"n": by_role[r], "accuracy": pct(by_role_hit[r], by_role[r])}
            for r in sorted(by_role)
        },
        "by_day": {
            d: {"n": by_day[d], "accuracy": pct(by_day_hit[d], by_day[d])}
            for d in sorted(by_day)
        },
        "allow_abstain_false_count": allow_false,
        "abstain_recovery_violations": violations,
    }


def run_adherence_smoke(
    batch_path: Path,
    n: int = 3,
    min_day: int = 3,
    model: str = DEFAULT_ADHERENCE_JUDGE_MODEL,
) -> None:
    """Judge adherence on a few recorded day>=min_day decisions and print the
    memories + labels side by side, so the rubric can be eyeballed cheaply."""
    cases = [(c, g) for c, g in iter_town_vote_cases(batch_path) if c.day >= min_day]
    take = min(n, len(cases))
    print(f"{len(cases)} eligible (day>={min_day}); judging first {take} with {model}\n")
    for case, game in cases[:n]:
        out = score_vote(
            case.agent_vote.votee if case.agent_vote else None, game["roles"]
        )
        verdict = (
            "HIT THREAT"
            if out.hit_threat
            else "MISLYNCH" if out.is_town_mislynch else "ABSTAIN" if out.is_abstain else "?"
        )
        print("=" * 88)
        print(
            f"game {str(game['game_id'])[:8]} | {case.player_role} | day {case.day} "
            f"r{case.round} | vote {out.votee} (role={out.votee_role}) -> {verdict}"
        )
        for i, item in enumerate(case.retrieved_observations, 1):
            obs = item.observation
            print(
                f"  [{i}] verdict={getattr(obs, 'net_verdict', '?')} :: "
                f"{(obs.approach or '')[:88]}"
            )
        result = judge_decision_adherence(case, model=model)
        if result is None:
            print("  (judge failed)")
            continue
        for r in result.per_memory:
            print(
                f"   -> [{r.memory_index}] dir={r.implied_direction} "
                f"action={r.action_followed} app={r.application} :: {r.evidence[:80]}"
            )
        print("  rollup:", summarize_adherence(result))


def _replay_vote(
    case: EvalCase,
    retrieved_observations: list[Any],
    allow_abstain: bool,
    prompt_template: Any | None = None,
) -> tuple[str | None, str]:
    """Regenerate one vote with a swapped memory block and the correct abstain
    choice set. Returns (votee, replayed updated_strategy). The prompt can be
    overridden too (a prompt-variant arm); default is the role's live template."""
    payload = eval_case_to_agent_payload(case)
    payload["retrieved_observations"] = retrieved_observations
    payload["strategy_points"] = []
    payload["allow_abstain"] = allow_abstain
    spec = action_spec_for(case)
    result = _run_agent(
        payload, prompt_template or spec.prompt_template, spec.output_schema, spec.output_key
    )
    if not result:
        return None, ""
    votes = result.get("day_votes", [])
    votee = votes[0].votee if votes else None
    updated = (result.get("agent_strategies") or {}).get(case.player_id, "")
    return votee, updated


def _select_diverse(
    batch_path: Path,
    n: int,
    min_day: int,
    max_day: int = 999,
    roles: frozenset[str] = REPLAYABLE_TOWN_ROLES,
) -> list[tuple[EvalCase, dict[str, Any]]]:
    """Pick ~n decisions in [min_day, max_day] for the given roles, spread ACROSS
    games (round-robin), so a sample isn't dominated by one game's decisions."""
    by_game: OrderedDict[str, list[tuple[EvalCase, dict[str, Any]]]] = OrderedDict()
    for case, game in iter_town_vote_cases(batch_path, roles):
        if case.day < min_day or case.day > max_day:
            continue
        by_game.setdefault(str(game["game_id"]), []).append((case, game))
    picked: list[tuple[EvalCase, dict[str, Any]]] = []
    depth = 0
    while len(picked) < n:
        added = False
        for pool in by_game.values():
            if len(pool) > depth:
                picked.append(pool[depth])
                added = True
                if len(picked) >= n:
                    break
        if not added:
            break
        depth += 1
    return picked


def mcnemar_p(b: int, c: int) -> float:
    """Two-sided exact-binomial McNemar p over the discordant pairs (b = memory
    HURT: off-correct & stored-wrong; c = memory HELPED: stored-correct &
    off-wrong). Concordant pairs carry no paired signal and are excluded."""
    m = b + c
    if m == 0:
        return 1.0
    k = min(b, c)
    tail = sum(comb(m, i) for i in range(k + 1)) / (2**m)
    return min(1.0, 2 * tail)


def _causal_one(
    case: EvalCase, game: dict[str, Any], do_judge: bool, judge_model: str
) -> tuple[dict[str, Any], Any, Any]:
    """Replay one decision off vs stored; return (display row, off outcome,
    stored outcome). Both arms use the per-decision abstain choice set."""
    roles = game["roles"]
    allow = allow_abstain_for(case.day, game["day_resolutions"])
    outcomes: dict[str, Any] = {}
    row: dict[str, Any] = {
        "game": str(game["game_id"])[:8],
        "role": case.player_role,
        "day": case.day,
        "recorded_vote": case.agent_vote.votee if case.agent_vote else None,
        "allow_abstain": allow,
    }
    for arm in ("off", "stored"):
        retrieved = [] if arm == "off" else case.retrieved_observations
        votee, updated = _replay_vote(case, retrieved, allow)
        out = score_vote(votee, roles)
        outcomes[arm] = out
        row[arm] = {"vote": votee, "role": out.votee_role, "hit": out.hit_threat}
        if do_judge and arm == "stored" and case.retrieved_observations:
            jcase = application_case_for_judge(
                case,
                agent_message=None,
                agent_vote=DayVote(voter=case.player_id, votee=votee or "abstain"),
                updated_strategy=updated,
            )
            adh = judge_decision_adherence(jcase, model=judge_model)
            row["stored_adherence"] = summarize_adherence(adh) if adh else None
    return row, outcomes["off"], outcomes["stored"]


def run_causal(
    batch_path: Path,
    n: int = 6,
    min_day: int = 3,
    max_day: int = 999,
    do_judge: bool = False,
    judge_model: str = DEFAULT_ADHERENCE_JUDGE_MODEL,
    max_workers: int = 6,
    roles: frozenset[str] = REPLAYABLE_TOWN_ROLES,
) -> dict[str, Any]:
    """The causal screen: replay each decision memory-OFF vs memory-AS-STORED in
    one sitting, score each regenerated vote against true roles, pair by decision.
    Decisions run concurrently (I/O-bound LLM calls). With do_judge, also label
    adherence on the stored arm's regenerated action. NOTE: hit_threat scoring is
    town-lensed (correct = votee is wolf/SK); for a wolf/SK run, read the raw
    votee roles from the rows, not the town accuracy summary."""
    cases = _select_diverse(batch_path, n, min_day, max_day, roles)
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = [ex.submit(_causal_one, c, g, do_judge, judge_model) for c, g in cases]
        results = [f.result() for f in futures]

    agg = {a: Counter() for a in ("off", "stored")}
    hurt = helped = failed = 0  # accuracy discordant pairs + dropped calls
    abst_induced = abst_removed = 0  # abstain discordant pairs (passivity probe)
    rows: list[dict[str, Any]] = []
    for row, off_out, stored_out in results:
        rows.append(row)
        # A failed replay returns votee=None; exclude the pair rather than miscount
        # it as a miss/abstain.
        if row["off"]["vote"] is None or row["stored"]["vote"] is None:
            failed += 1
            continue
        for arm, out in (("off", off_out), ("stored", stored_out)):
            agg[arm]["n"] += 1
            agg[arm]["hit"] += out.hit_threat
            agg[arm]["mislynch"] += out.is_town_mislynch
            agg[arm]["abstain"] += out.is_abstain
        if off_out.hit_threat and not stored_out.hit_threat:
            hurt += 1
        elif stored_out.hit_threat and not off_out.hit_threat:
            helped += 1
        if stored_out.is_abstain and not off_out.is_abstain:
            abst_induced += 1
        elif off_out.is_abstain and not stored_out.is_abstain:
            abst_removed += 1

    def rate(a: str, k: str) -> float | None:
        return round(agg[a][k] / agg[a]["n"], 3) if agg[a]["n"] else None

    summary = {
        a: {"n": agg[a]["n"], "accuracy": rate(a, "hit"), "mislynch": rate(a, "mislynch"), "abstain": rate(a, "abstain")}
        for a in ("off", "stored")
    }
    acc_off, acc_stored = summary["off"]["accuracy"], summary["stored"]["accuracy"]
    return {
        "batch": batch_path.name,
        "n_decisions": len(cases),
        "n_failed": failed,
        "arms": summary,
        "stored_minus_off_accuracy": (
            round(acc_stored - acc_off, 3)
            if acc_off is not None and acc_stored is not None
            else None
        ),
        "discordant": {
            "memory_hurt": hurt,
            "memory_helped": helped,
            "mcnemar_p": round(mcnemar_p(hurt, helped), 4),
        },
        "abstain_discordant": {
            "memory_induced_abstain": abst_induced,
            "memory_removed_abstain": abst_removed,
            "mcnemar_p": round(mcnemar_p(abst_induced, abst_removed), 4),
        },
        "rows": rows,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Decision-replay screen.")
    ap.add_argument(
        "--batch", required=True, type=Path, help="batch_results/<arm>.jsonl"
    )
    ap.add_argument(
        "--adherence-smoke",
        type=int,
        default=0,
        help="judge N recorded decisions with the adherence judge (LLM) instead "
        "of the no-LLM observational outcome pass",
    )
    ap.add_argument(
        "--causal",
        type=int,
        default=0,
        help="causal replay on N decisions: memory off vs as-stored, paired",
    )
    ap.add_argument(
        "--judge",
        action="store_true",
        help="with --causal, also label adherence on the stored arm",
    )
    ap.add_argument("--min-day", type=int, default=3)
    ap.add_argument("--max-day", type=int, default=999)
    ap.add_argument(
        "--roles",
        default="villager,healer,investigator",
        help="comma-separated player roles to replay (default town; e.g. 'wolf')",
    )
    ap.add_argument("--model", default=DEFAULT_ADHERENCE_JUDGE_MODEL)
    args = ap.parse_args()
    roles = frozenset(r.strip() for r in args.roles.split(",") if r.strip())
    if args.adherence_smoke:
        run_adherence_smoke(
            args.batch, n=args.adherence_smoke, min_day=args.min_day, model=args.model
        )
    elif args.causal:
        report = run_causal(
            args.batch,
            n=args.causal,
            min_day=args.min_day,
            max_day=args.max_day,
            do_judge=args.judge,
            judge_model=args.model,
            roles=roles,
        )
        print(json.dumps(report, indent=2))
    else:
        print(json.dumps(run_observational(args.batch), indent=2))


if __name__ == "__main__":
    main()
