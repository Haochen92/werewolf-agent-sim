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

from Agents.prompts import (
    HEALER_NIGHT,
    INVESTIGATOR_NIGHT,
    SERIAL_KILLER_NIGHT,
    VIGILANTE_NIGHT,
    WOLF_NIGHT_DISCUSS,
)
from Agents.schemas import DayVote
from Agents.schemas.evaluation import EvalCase
from Agents.schemas.output import (
    HealerOutput,
    InvestigatorOutput,
    SerialKillerOutput,
    VigilanteOutput,
    WolfNightDiscussOutput,
)
from Agents.prompts.prompt_formatters import format_day_channel
from Agents.turn import _run_agent
from evaluation.src.components.application import (
    action_spec_for,
    application_case_for_judge,
    run_application_action,
)
from evaluation.src.components.decision_scoring import (
    REPLAYABLE_TOWN_ROLES,
    THREAT_ROLES,
    allow_abstain_for,
    score_night_target,
    score_vote,
)

# Night-action spec map (role -> prompt, output schema, output_key) mirroring
# application.ACTION_SPECS for the day. _run_agent already handles these night
# output_keys; the wolf kill rides the wolf_channel vote field.
NIGHT_SPECS: dict[str, tuple[Any, Any, str]] = {
    "wolf": (WOLF_NIGHT_DISCUSS, WolfNightDiscussOutput, "wolf_channel"),
    "serial_killer": (SERIAL_KILLER_NIGHT, SerialKillerOutput, "serial_killer_target"),
    "healer": (HEALER_NIGHT, HealerOutput, "healer_target"),
    "investigator": (INVESTIGATOR_NIGHT, InvestigatorOutput, "investigator_target"),
    "vigilante": (VIGILANTE_NIGHT, VigilanteOutput, "vigilante_target"),
}
from evaluation.src.components.memory_adherence import (
    DEFAULT_ADHERENCE_JUDGE_MODEL,
    judge_decision_adherence,
    judge_discussion_stance,
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


def iter_cases(
    batch_path: Path,
    roles: frozenset[str] = REPLAYABLE_TOWN_ROLES,
    phase: str = "day_vote",
) -> Iterator[tuple[EvalCase, dict[str, Any]]]:
    """Yield (case, game_info) for every replay-able decision in the given phase
    with retrieved memory, for the given roles — the unit the screen scores.
    phase='day_vote' (default) or 'night_action'; roles default to town."""
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
    cases = list(iter_cases(batch_path))
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
    cases = [(c, g) for c, g in iter_cases(batch_path) if c.day >= min_day]
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
    phase: str = "day_vote",
) -> list[tuple[EvalCase, dict[str, Any]]]:
    """Pick ~n decisions in [min_day, max_day] for the given roles+phase, spread
    ACROSS games (round-robin), so a sample isn't dominated by one game."""
    by_game: OrderedDict[str, list[tuple[EvalCase, dict[str, Any]]]] = OrderedDict()
    for case, game in iter_cases(batch_path, roles, phase):
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


def _replay_night(
    case: EvalCase, retrieved_observations: list[Any], prompt_template: Any | None = None
) -> str | None:
    """Regenerate one night target with a swapped memory block. The wolf kill
    rides the wolf_channel vote field; other roles return their *_target directly."""
    payload = eval_case_to_agent_payload(case)
    payload["retrieved_observations"] = retrieved_observations
    payload["strategy_points"] = []
    prompt, schema, output_key = NIGHT_SPECS[case.player_role]
    result = _run_agent(payload, prompt_template or prompt, schema, output_key)
    if not result:
        return None
    if output_key == "wolf_channel":
        wc = result.get("wolf_channel", [])
        return wc[0].vote if wc else None
    return result.get(output_key)


def run_night_causal(
    batch_path: Path,
    n: int = 60,
    roles: frozenset[str] = frozenset({"wolf"}),
    max_workers: int = 6,
) -> dict[str, Any]:
    """Night-kill screen: replay each night target memory-off vs as-stored in one
    sitting, score against true roles. For deceivers (wolf/SK) the metric is
    POWER-TARGETING — did the kill land on a town power role (investigator/healer/
    vigilante), the A/B's wolf night proxy — paired by decision."""
    cases = _select_diverse(batch_path, n, 1, 999, roles, phase="night_action")

    def one(case: EvalCase, game: dict[str, Any]):
        row: dict[str, Any] = {
            "game": str(game["game_id"])[:8],
            "role": case.player_role,
            "day": case.day,
            "recorded_target": (
                case.agent_night_action.target if case.agent_night_action else None
            ),
        }
        outs = {}
        for arm in ("off", "stored"):
            retrieved = [] if arm == "off" else case.retrieved_observations
            o = score_night_target(_replay_night(case, retrieved), game["roles"])
            outs[arm] = o
            row[arm] = {"target": o.target, "role": o.target_role, "power": o.hit_power}
        return row, outs["off"], outs["stored"]

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        results = [f.result() for f in [ex.submit(one, c, g) for c, g in cases]]

    agg = {a: Counter() for a in ("off", "stored")}
    power_more = power_less = failed = 0
    rows: list[dict[str, Any]] = []
    for row, off, stored in results:
        rows.append(row)
        if row["off"]["target"] is None or row["stored"]["target"] is None:
            failed += 1
            continue
        for arm, o in (("off", off), ("stored", stored)):
            agg[arm]["n"] += 1
            agg[arm]["power"] += o.hit_power
            agg[arm]["threat"] += o.hit_threat
            agg[arm]["town"] += o.hit_town
        if stored.hit_power and not off.hit_power:
            power_more += 1
        elif off.hit_power and not stored.hit_power:
            power_less += 1

    def rate(a: str, k: str) -> float | None:
        return round(agg[a][k] / agg[a]["n"], 3) if agg[a]["n"] else None

    summary = {
        a: {"n": agg[a]["n"], "power_targeting": rate(a, "power"), "hit_threat": rate(a, "threat"), "hit_town": rate(a, "town")}
        for a in ("off", "stored")
    }
    p_off, p_st = summary["off"]["power_targeting"], summary["stored"]["power_targeting"]
    return {
        "batch": batch_path.name,
        "phase": "night_action",
        "roles": sorted(roles),
        "n_decisions": len(cases),
        "n_failed": failed,
        "arms": summary,
        "stored_minus_off_power_targeting": (
            round(p_st - p_off, 3) if p_off is not None and p_st is not None else None
        ),
        "power_discordant": {
            "memory_more_power": power_more,
            "memory_less_power": power_less,
            "mcnemar_p": round(mcnemar_p(power_more, power_less), 4),
        },
        "rows": rows,
    }


PASSIVE_STANCES = frozenset({"passive_or_hedging", "defensive_only"})


def run_discussion_causal(
    batch_path: Path,
    n: int = 60,
    roles: frozenset[str] = REPLAYABLE_TOWN_ROLES,
    judge_model: str = "gemini-2.5-flash",
    max_workers: int = 6,
) -> dict[str, Any]:
    """Discussion screen: replay each town day_discussion turn memory-off vs
    as-stored, score the regenerated turn's stance (outcome-blind). Probes the
    anti-aggression hypothesis at the single-turn level — does memory make town
    more passive / less likely to name a real threat on the SAME board?"""
    cases = _select_diverse(batch_path, n, 1, 999, roles, phase="day_discussion")

    def one(case: EvalCase, game: dict[str, Any]):
        day_ctx = format_day_channel(case.visible_discussion)
        row: dict[str, Any] = {
            "game": str(game["game_id"])[:8], "role": case.player_role, "day": case.day
        }
        outs = {}
        for arm in ("off", "stored"):
            retrieved = [] if arm == "off" else case.retrieved_observations
            _, agent_message, _, _ = run_application_action(
                case, retrieved_observations=retrieved, strategy_points=[]
            )
            msg = agent_message.message if agent_message else ""
            stance = judge_discussion_stance(
                msg, day_ctx, case.player_id, case.day, model=judge_model
            )
            accused = stance.accused_player if stance else None
            outs[arm] = {
                "stance": stance.stance if stance else None,
                "accused": accused,
                "accused_role": game["roles"].get(accused) if accused else None,
                "silent": not (msg or "").strip(),
            }
            row[arm] = outs[arm]
        return row, outs["off"], outs["stored"]

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        results = [f.result() for f in [ex.submit(one, c, g) for c, g in cases]]

    agg = {a: Counter() for a in ("off", "stored")}
    passive_more = passive_less = 0
    rows: list[dict[str, Any]] = []
    for row, off, stored in results:
        rows.append(row)
        for arm, o in (("off", off), ("stored", stored)):
            if o["stance"] is None:
                continue
            agg[arm]["n"] += 1
            agg[arm]["passive"] += o["stance"] in PASSIVE_STANCES or o["silent"]
            agg[arm]["drives"] += o["stance"] == "drives_suspicion"
            agg[arm]["accuses_threat"] += o["accused_role"] in THREAT_ROLES
            agg[arm]["silent"] += bool(o["silent"])
        if off["stance"] and stored["stance"]:
            op = off["stance"] in PASSIVE_STANCES or off["silent"]
            sp = stored["stance"] in PASSIVE_STANCES or stored["silent"]
            if sp and not op:
                passive_more += 1
            elif op and not sp:
                passive_less += 1

    def rate(a: str, k: str) -> float | None:
        return round(agg[a][k] / agg[a]["n"], 3) if agg[a]["n"] else None

    summary = {
        a: {"n": agg[a]["n"], "passive": rate(a, "passive"), "drives_suspicion": rate(a, "drives"), "accuses_threat": rate(a, "accuses_threat"), "silent": rate(a, "silent")}
        for a in ("off", "stored")
    }
    p_off, p_st = summary["off"]["passive"], summary["stored"]["passive"]
    return {
        "batch": batch_path.name,
        "phase": "day_discussion",
        "roles": sorted(roles),
        "n_decisions": len(cases),
        "arms": summary,
        "stored_minus_off_passive": (
            round(p_st - p_off, 3) if p_off is not None and p_st is not None else None
        ),
        "passive_discordant": {
            "memory_more_passive": passive_more,
            "memory_less_passive": passive_less,
            "mcnemar_p": round(mcnemar_p(passive_more, passive_less), 4),
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
        help="causal day-vote replay on N decisions: memory off vs as-stored, paired",
    )
    ap.add_argument(
        "--night",
        type=int,
        default=0,
        help="causal night-action replay on N decisions (power-targeting metric); "
        "use with --roles wolf or --roles serial_killer",
    )
    ap.add_argument(
        "--discussion",
        type=int,
        default=0,
        help="causal day_discussion replay on N town turns (passivity / threat-naming)",
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
    elif args.night:
        print(json.dumps(run_night_causal(args.batch, n=args.night, roles=roles), indent=2))
    elif args.discussion:
        print(json.dumps(run_discussion_causal(args.batch, n=args.discussion, roles=roles), indent=2))
    else:
        print(json.dumps(run_observational(args.batch), indent=2))


if __name__ == "__main__":
    main()
