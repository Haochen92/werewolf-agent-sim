"""The screen runners built on the replay substrate — each replays a cohort of
frozen decisions memory-OFF vs memory-AS-STORED (and schema/framing variants),
scores every regenerated action mechanically (outcome-blind), and pairs by
decision for an exact McNemar test.

Screens:
- ``run_observational``       no-LLM foundation smoke: score RECORDED votes vs truth
- ``run_causal``              day-vote off/stored, town or wolf lens
- ``run_night_causal``        night-target off/stored, deceiver power-targeting
- ``run_discussion_causal``   day-discussion stance (passivity / threat-naming)
- ``run_reorder_test`` / ``run_reorder_adoption``  vote-first vs reason-first schema
- ``run_coherence_test``      reasoning->vote sync under each schema
- ``run_applicability_probe`` forced per-memory verdict on a planted mismatch
- ``run_framing_rewrite_screen``  net-first vs immediate-first outcome framing
- ``run_adherence_scan`` / ``run_adherence_smoke``  adherence-judge label rollups
"""

from __future__ import annotations

import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Literal

from pydantic import BaseModel, Field

from Agents.llm_factory import create_chat_model
from Agents.prompts.prompt_formatters import format_day_channel
from Agents.schemas import DayVote
from Agents.schemas.evaluation import EvalCase
from evaluation.src.loop.decision_scoring import (
    REPLAYABLE_TOWN_ROLES,
    THREAT_ROLES,
    allow_abstain_for,
    score_night_target,
    score_vote,
    wolf_vote_is_good,
)
from evaluation.src.loop.memory_adherence import (
    DEFAULT_ADHERENCE_JUDGE_MODEL,
    judge_decision_adherence,
    judge_discussion_stance,
    summarize_adherence,
)
from evaluation.src.replay.application import (
    application_case_for_judge,
    run_application_action,
)
from evaluation.src.replay.decision_screen.cases import (
    _abstained_on_day,
    _find_case,
    _find_endgame_plant,
    _select_diverse,
    iter_cases,
)
from evaluation.src.replay.decision_screen.replay import (
    _replay_night,
    _replay_vote,
    _replay_vote_structured,
)
from evaluation.src.replay.decision_screen.schemas import (
    DayVoteOutputMemoryLinked,
    DayVoteOutputReasonFirst,
)
from evaluation.src.replay.decision_screen.stats import mcnemar_p


def run_observational(batch_path) -> dict[str, Any]:
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
    batch_path,
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
    batch_path,
    n: int = 6,
    min_day: int = 3,
    max_day: int = 999,
    do_judge: bool = False,
    judge_model: str = DEFAULT_ADHERENCE_JUDGE_MODEL,
    max_workers: int = 6,
    roles: frozenset[str] = REPLAYABLE_TOWN_ROLES,
    lens: Literal["town", "wolf"] = "town",
) -> dict[str, Any]:
    """The causal screen: replay each decision memory-OFF vs memory-AS-STORED in
    one sitting, score each regenerated vote against true roles, pair by decision.
    Decisions run concurrently (I/O-bound LLM calls). With do_judge, also label
    adherence on the stored arm's regenerated action.

    `lens` sets what "accuracy" means: town (default, correct = votee is wolf/SK,
    ``hit_threat``) or wolf (deceiver lens, correct = the vote INDUCES a town mislynch,
    ``wolf_vote_is_good``) — pass ``lens='wolf'`` with ``--roles wolf`` (or
    serial_killer) so a deceiver run is scored on its own win condition, not town's."""
    cases = _select_diverse(batch_path, n, min_day, max_day, roles)
    good = (lambda out: out.hit_threat) if lens == "town" else wolf_vote_is_good
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
            agg[arm]["hit"] += good(out)
            agg[arm]["mislynch"] += out.is_town_mislynch
            agg[arm]["abstain"] += out.is_abstain
        if good(off_out) and not good(stored_out):
            hurt += 1
        elif good(stored_out) and not good(off_out):
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
        "lens": lens,
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


def run_night_causal(
    batch_path,
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
    batch_path,
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


def run_reorder_test(
    batch_path,
    n: int = 60,
    min_day: int = 3,
    roles: frozenset[str] = REPLAYABLE_TOWN_ROLES,
    max_workers: int = 6,
) -> dict[str, Any]:
    """Judge-FREE 2x2 causal test of the vote-before-reasoning fix: replay each
    decision under {vote-first schema, reason-first schema} x {memory off, stored}.
    If the memory effect (stored - off net value) appears under reason-first but
    not vote-first, the schema order was suppressing the memory->vote connection
    and the prior nulls were an adoption artifact, not a content verdict."""
    cases = _select_diverse(batch_path, n, min_day, 999, roles, phase="day_vote")
    schemas = {
        "vote_first": None,
        "reason_first": DayVoteOutputReasonFirst,
        "memory_linked": DayVoteOutputMemoryLinked,
    }

    def one(case: EvalCase, game: dict[str, Any]):
        allow = allow_abstain_for(case.day, game["day_resolutions"])
        outc, votees = {}, {}
        for sname, sch in schemas.items():
            for arm in ("off", "stored"):
                retrieved = [] if arm == "off" else case.retrieved_observations
                votee, _ = _replay_vote(case, retrieved, allow, schema_override=sch)
                votees[(sname, arm)] = votee
                outc[(sname, arm)] = score_vote(votee, game["roles"])
        return outc, votees

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        results = [f.result() for f in [ex.submit(one, c, g) for c, g in cases]]

    def netval(o: Any) -> int:
        return 1 if o.hit_threat else (-1 if o.is_town_mislynch else 0)

    agg = {(s, a): [0, 0] for s in schemas for a in ("off", "stored")}  # [sum, n]
    failed = 0
    for outc, votees in results:
        if any(v is None for v in votees.values()):  # drop a decision if any arm failed
            failed += 1
            continue
        for key, o in outc.items():
            agg[key][0] += netval(o)
            agg[key][1] += 1

    def nv(s: str, a: str) -> float | None:
        total, k = agg[(s, a)]
        return round(total / k, 3) if k else None

    by_schema = {}
    for s in schemas:
        off_nv, st_nv = nv(s, "off"), nv(s, "stored")
        by_schema[s] = {
            "off_netvalue": off_nv,
            "stored_netvalue": st_nv,
            "memory_effect": round(st_nv - off_nv, 3)
            if off_nv is not None and st_nv is not None
            else None,
        }
    off_v, me_v = nv("vote_first", "off"), by_schema["vote_first"]["memory_effect"]
    vs_vote_first = {}
    for s in schemas:
        if s == "vote_first":
            continue
        off_s, me_s = nv(s, "off"), by_schema[s]["memory_effect"]
        vs_vote_first[s] = {
            "baseline_lift": round(off_s - off_v, 3)
            if off_s is not None and off_v is not None
            else None,
            "did_memory_effect": round(me_s - me_v, 3)
            if me_s is not None and me_v is not None
            else None,
        }
    return {
        "batch": batch_path.name,
        "n_decisions": len(cases),
        "n_failed": failed,
        "by_schema": by_schema,
        "vs_vote_first": vs_vote_first,
    }


def run_reorder_adoption(
    batch_path,
    n: int = 40,
    min_day: int = 3,
    roles: frozenset[str] = REPLAYABLE_TOWN_ROLES,
    judge_model: str = DEFAULT_ADHERENCE_JUDGE_MODEL,
    max_workers: int = 6,
) -> dict[str, Any]:
    """Did reason-first actually raise memory CONSIDERATION/adoption (the
    mechanism step 2's outcome read assumes)? Replay the STORED arm under
    {vote-first, reason-first}, capture the agent's reasoning, judge adherence.
    If reason-first lifts applied/followed and drops ignored, the reorder
    strengthened the memory->action connection."""
    cases = _select_diverse(batch_path, n, min_day, 999, roles, phase="day_vote")
    schemas = {
        "vote_first": None,
        "reason_first": DayVoteOutputReasonFirst,
        "memory_linked": DayVoteOutputMemoryLinked,
    }

    def one(case: EvalCase, game: dict[str, Any]):
        allow = allow_abstain_for(case.day, game["day_resolutions"])
        out = {}
        for sname, sch in schemas.items():
            votee, updated = _replay_vote(
                case, case.retrieved_observations, allow, schema_override=sch
            )
            jcase = application_case_for_judge(
                case,
                agent_message=None,
                agent_vote=DayVote(voter=case.player_id, votee=votee or "abstain"),
                updated_strategy=updated,
            )
            out[sname] = judge_decision_adherence(jcase, model=judge_model)
        return out

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        results = [f.result() for f in [ex.submit(one, c, g) for c, g in cases]]

    app = {s: Counter() for s in schemas}
    follow = {s: Counter() for s in schemas}
    nmem = {s: 0 for s in schemas}
    for out in results:
        for s in schemas:
            adh = out[s]
            if adh is None:
                continue
            for r in adh.per_memory:
                nmem[s] += 1
                app[s][r.application] += 1
                follow[s][r.action_followed] += 1

    by_schema = {}
    for s in schemas:
        k = nmem[s] or 1
        by_schema[s] = {
            "n_memories": nmem[s],
            "applied": round(app[s]["applied"] / k, 3),
            "ignored": round(app[s]["ignored"] / k, 3),
            "followed": round(follow[s]["followed"] / k, 3),
            "contradicted": round(follow[s]["contradicted"] / k, 3),
        }
    return {"batch": batch_path.name, "n_decisions": len(cases), "by_schema": by_schema}


_GRID_CONDITIONS = [
    ("off / vote-first", "off", None),
    ("stored / vote-first", "stored", None),
    ("stored / reason-first", "stored", DayVoteOutputReasonFirst),
    ("stored / memory-linked", "stored", DayVoteOutputMemoryLinked),
]


def replay_condition_grid(
    batch_path,
    specs: list[tuple[str, str, int, str]],
    samples: int = 3,
    max_workers: int = 6,
) -> list[dict[str, Any]]:
    """For each named decision, replay it under {memory off, memory on x vote-first /
    reason-first / memory-linked} and capture BOTH the final vote and the reasoning,
    sampling each condition `samples` times (temp 1.0 -> a single draw is noisy). Shows
    whether reordering the schema lets the memory actually reach the VOTE, not just the
    words — and keeps the recorded (original-game) vote+reasoning as the reference."""
    out: list[dict[str, Any]] = []
    for game_prefix, role, day, mem_substr in specs:
        case, game = _find_case(batch_path, game_prefix, role, day, mem_substr)
        if case is None:
            out.append({"spec": [game_prefix, role, day], "error": "not found"})
            continue
        roles = game["roles"]
        allow = allow_abstain_for(case.day, game["day_resolutions"])
        tasks = [
            (ci, arm, sch)
            for ci, (_, arm, sch) in enumerate(_GRID_CONDITIONS)
            for _ in range(samples)
        ]

        def run_task(t: tuple[int, str, Any]):
            ci, arm, sch = t
            retrieved = [] if arm == "off" else case.retrieved_observations
            votee, updated = _replay_vote(case, retrieved, allow, schema_override=sch)
            return ci, votee, updated

        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            results = list(ex.map(run_task, tasks))
        by_ci: dict[int, list[tuple[str | None, str]]] = {}
        for ci, votee, updated in results:
            by_ci.setdefault(ci, []).append((votee, updated))

        conditions = []
        for ci, (label, _, _) in enumerate(_GRID_CONDITIONS):
            draws = by_ci.get(ci, [])
            conditions.append(
                {
                    "label": label,
                    "votes": [
                        {"votee": v, "role": roles.get(v) if v else None} for v, _ in draws
                    ],
                    "reasoning_sample": draws[0][1] if draws else "",
                }
            )
        out.append(
            {
                "game": game_prefix,
                "role": role,
                "day": day,
                "player_id": case.player_id,
                "allow_abstain": allow,
                "threats": sorted(p for p, r in roles.items() if r in THREAT_ROLES),
                "recorded": {
                    "votee": case.agent_vote.votee if case.agent_vote else None,
                    "role": roles.get(case.agent_vote.votee) if case.agent_vote else None,
                    "reasoning": case.updated_strategy,
                },
                "conditions": conditions,
            }
        )
    return out


class VoteReasoningCoherence(BaseModel):
    """The single choice a reasoning note CONCLUDES on, read blind to the actual vote."""

    stated_choice: str = Field(
        description="Exactly one of: a player_id the note concludes to vote for; "
        "'abstain' if it concludes to vote for no one; 'unclear' if it weighs options "
        "without committing to one."
    )
    quote: str = Field(
        description="The clause that states the choice; empty string if unclear."
    )


_COH_SYSTEM = """You read a Werewolf player's PRIVATE reasoning note, written around a day-phase vote, and report the SINGLE choice the reasoning CONCLUDES on. Output exactly one of:
- a player_id (e.g. player_6) - if the note concludes the writer should vote for that player;
- abstain - if it concludes the writer should vote for no one / hold;
- unclear - if it weighs suspects without committing to one.

Judge ONLY what the note concludes. You are NOT told who they actually voted for - do not infer from who seems most guilty. Look for the committing statement, e.g. 'I will vote for X', 'I will target X', 'I am voting X', 'I will abstain'. If the note discusses several suspects but never lands on one, that is unclear."""

_COH_USER = """Players in this game: {players}
Abstain available this vote: {allow}

Reasoning note:
{reasoning}

Which single choice does this note CONCLUDE on?"""


def _norm_choice(x: str | None) -> str:
    """Normalize a vote/stated choice to a comparable token (player_N / abstain / unclear)."""
    if not x:
        return "unclear"
    t = x.strip().lower().replace("player ", "player_").replace(" ", "")
    return t or "unclear"


def _judge_coherence(
    reasoning: str | None,
    players: list[str],
    allow_abstain: bool,
    model: str = "gemini-2.5-flash",
) -> tuple[str, str]:
    """Return (stated_choice, quote): which choice the reasoning concludes on, blind
    to the real vote. Empty/blank reasoning -> ('unclear', '')."""
    if not reasoning or not reasoning.strip():
        return "unclear", ""
    user = _COH_USER.format(
        players=", ".join(players),
        allow="yes" if allow_abstain else "no",
        reasoning=reasoning,
    )
    llm = create_chat_model(model).with_structured_output(VoteReasoningCoherence)
    try:
        r = llm.invoke(
            [
                {"role": "system", "content": _COH_SYSTEM},
                {"role": "user", "content": user},
            ],
            config={"run_name": "coherence_judge"},
        )
        return (r.stated_choice or "unclear").strip(), r.quote or ""
    except Exception:  # noqa: BLE001 - judge is best-effort
        return "unclear", ""


def run_coherence_test(
    batch_path,
    n: int = 40,
    min_day: int = 3,
    roles: frozenset[str] = REPLAYABLE_TOWN_ROLES,
    judge_model: str = "gemini-2.5-flash",
    max_workers: int = 6,
) -> dict[str, Any]:
    """Does reordering SYNCHRONIZE the vote with the reasoning? Replay each decision
    (memory on) under {vote-first, reason-first, memory-linked}; a judge reads ONLY the
    reasoning and reports the choice it concludes on; compare to the real vote ->
    synced / desync / unclear. The reason-first synced rate is the key number: it is the
    fraction of decisions where the channel memory->reasoning->vote is intact (a low rate
    means the agent deliberates then gut-votes anyway, so even GOOD memory won't reach the
    vote). vote-first is the reference (its reasoning is written after the vote)."""
    cases = _select_diverse(batch_path, n, min_day, 999, roles, phase="day_vote")
    schemas = {
        "vote_first": None,
        "reason_first": DayVoteOutputReasonFirst,
        "memory_linked": DayVoteOutputMemoryLinked,
    }

    def one(case: EvalCase, game: dict[str, Any]):
        allow = allow_abstain_for(case.day, game["day_resolutions"])
        players = sorted(game["roles"].keys())
        by_schema = {}
        for sname, sch in schemas.items():
            votee, updated = _replay_vote(
                case, case.retrieved_observations, allow, schema_override=sch
            )
            stated, quote = _judge_coherence(updated, players, allow, model=judge_model)
            by_schema[sname] = {
                "vote": votee,
                "stated": stated,
                "quote": quote,
                "reasoning": updated,
            }
        return {
            "game": str(game["game_id"])[:8],
            "role": case.player_role,
            "day": case.day,
            "allow_abstain": allow,
            "by_schema": by_schema,
        }

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        rows = [f.result() for f in [ex.submit(one, c, g) for c, g in cases]]

    def classify(d: dict[str, Any]) -> str:
        stated = _norm_choice(d["stated"])
        if stated == "unclear":
            return "unclear"
        return "synced" if stated == _norm_choice(d["vote"]) else "desync"

    agg = {s: Counter() for s in schemas}
    desync_examples: list[dict[str, Any]] = []
    for row in rows:
        for s in schemas:
            d = row["by_schema"][s]
            if d["vote"] is None:
                agg[s]["failed"] += 1
                continue
            verdict = classify(d)
            agg[s][verdict] += 1
            agg[s]["n"] += 1
            if verdict == "desync" and len(desync_examples) < 15:
                desync_examples.append(
                    {
                        "game": row["game"],
                        "schema": s,
                        "role": row["role"],
                        "voted": d["vote"],
                        "reasoning_concluded": d["stated"],
                        "quote": (d["quote"] or "")[:160],
                        "reasoning": (d["reasoning"] or "")[:320],
                    }
                )

    def rate(s: str, k: str) -> float | None:
        return round(agg[s][k] / agg[s]["n"], 3) if agg[s]["n"] else None

    by_schema = {
        s: {
            "n": agg[s]["n"],
            "synced": rate(s, "synced"),
            "desync": rate(s, "desync"),
            "unclear": rate(s, "unclear"),
        }
        for s in schemas
    }
    return {
        "batch": batch_path.name,
        "n_decisions": len(cases),
        "by_schema": by_schema,
        "desync_examples": desync_examples,
    }


def _planted_verdict(verdicts: list[Any], planted_index: int, total: int) -> str:
    """The model's OWN verdict on the planted memory: match by stated memory_index, else
    (one-row-per-memory) take the last row, else 'not_mentioned'."""
    for v in verdicts:
        if getattr(v, "memory_index", None) == planted_index:
            return v.verdict
    if len(verdicts) == total:
        return verdicts[-1].verdict
    return "not_mentioned"


def run_applicability_probe(
    batch_path,
    n: int = 20,
    day: int = 3,
    max_workers: int = 6,
) -> dict[str, Any]:
    """CAPABILITY probe (judge-FREE): can flash-lite reason about a memory's applicability
    when FORCED to? Inject one clearly-mismatched ENDGAME memory into each mid-game
    (day=`day`) town decision and replay under the forced-structured schema, which makes
    the model emit one applies/partly/does-not verdict PER memory (it cannot skip it).
    Measure (1) the model's OWN verdict on the planted endgame memory — does it say
    does_not_apply — and (2) whether the vote is protected vs the planted noise
    (structured+plant vs vote-first+plant vs clean baseline). Full verdict rows are kept
    for hand-reading: are the calls on the REAL memories sensible, or is it rubber-stamping?"""
    planted = _find_endgame_plant(batch_path)
    if planted is None:
        return {"error": "no endgame plant found in this batch"}
    planted_sit = (getattr(planted.observation, "situation", "") or "")[:220]
    cases = _select_diverse(batch_path, n, day, day, REPLAYABLE_TOWN_ROLES, "day_vote")

    def one(case: EvalCase, game: dict[str, Any]):
        allow = allow_abstain_for(case.day, game["day_resolutions"])
        roles = game["roles"]
        real = list(case.retrieved_observations or [])
        with_plant = real + [planted]
        planted_index = len(with_plant)  # 1-based: the plant is appended last
        result = _replay_vote_structured(case, with_plant, allow)
        if result is None:
            verdicts, votee_sm, reasoning = [], None, ""
        else:
            verdicts = list(getattr(result, "memory_applicability", []) or [])
            votee_sm = getattr(result, "vote_target", None)
            reasoning = getattr(result, "updated_strategy", "") or ""
        treat = _planted_verdict(verdicts, planted_index, len(with_plant))
        votee_ctrl, _ = _replay_vote(case, with_plant, allow)  # vote-first, same plant
        votee_base, _ = _replay_vote(case, real, allow)  # vote-first, no plant
        return {
            "game": str(game["game_id"])[:8],
            "role": case.player_role,
            "day": case.day,
            "n_real_memories": len(real),
            "n_verdicts": len(verdicts),
            "planted_verdict": treat,
            "all_verdicts": [
                {
                    "i": getattr(v, "memory_index", None),
                    "verdict": v.verdict,
                    "why": (v.why or "")[:140],
                }
                for v in verdicts
            ],
            "reasoning": (reasoning or "")[:500],
            "vote_sm_plant": {"v": votee_sm, "hit": score_vote(votee_sm, roles).hit_threat},
            "vote_ctrl_plant": {"v": votee_ctrl, "hit": score_vote(votee_ctrl, roles).hit_threat},
            "vote_base_clean": {"v": votee_base, "hit": score_vote(votee_base, roles).hit_threat},
        }

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        rows = [f.result() for f in [ex.submit(one, c, g) for c, g in cases]]

    treat: Counter[str] = Counter(r["planted_verdict"] for r in rows)
    n_total = sum(treat.values())
    n_emitting = sum(1 for r in rows if r["all_verdicts"])

    def acc(key: str) -> float | None:
        vals = [int(r[key]["hit"]) for r in rows if r[key]["v"] is not None]
        return round(sum(vals) / len(vals), 3) if vals else None

    return {
        "batch": batch_path.name,
        "n_decisions": len(rows),
        "day": day,
        "planted_memory_situation": planted_sit,
        "n_decisions_emitting_verdicts": n_emitting,
        "planted_verdict_dist": dict(treat),
        "rejection_rate": round(treat["does_not_apply"] / n_total, 3) if n_total else None,
        "engaged_as_applicable": round(
            (treat["fully_applies"] + treat["partly_applies"]) / n_total, 3
        )
        if n_total
        else None,
        "vote_accuracy": {
            "structured_applicability_with_plant": acc("vote_sm_plant"),
            "vote_first_with_plant": acc("vote_ctrl_plant"),
            "vote_first_clean_baseline": acc("vote_base_clean"),
        },
        "rows": rows,
    }


class _ImmediateRewrite(BaseModel):
    rewritten: str = Field(
        description="The outcome re-emphasized toward the IMMEDIATE consequence, using only facts "
        "already present in the original."
    )


_IMMEDIATE_REWRITE_PROMPT = """Rewrite this Werewolf memory's OUTCOME so it leads with the IMMEDIATE consequence of the move — what happened that same night or on the very next step — and de-emphasizes the eventual game result (who ultimately won or lost). Use ONLY facts already stated in the text; do NOT add new players, roles, or events, and do not invent a consequence. Keep it to 1-2 sentences in the same neutral, factual voice.

OUTCOME:
{outcome}"""


def _immediate_rewrite(outcome: str, model: str = "gemini-2.5-flash") -> str:
    """Re-emphasize an outcome toward its immediate consequence (the role-horizon
    framing), holding the facts. Returns the original unchanged on failure."""
    if not outcome or not outcome.strip():
        return outcome
    llm = create_chat_model(model).with_structured_output(_ImmediateRewrite)
    try:
        r = llm.invoke(
            [{"role": "user", "content": _IMMEDIATE_REWRITE_PROMPT.format(outcome=outcome)}],
            config={"run_name": "immediate_rewrite"},
        )
        return (r.rewritten or outcome).strip()
    except Exception:  # noqa: BLE001 - best-effort
        return outcome


def run_framing_rewrite_screen(
    batch_path,
    n: int = 40,
    min_day: int = 3,
    max_day: int = 999,
    roles: frozenset[str] = REPLAYABLE_TOWN_ROLES,
    rewrite_model: str = "gemini-2.5-flash",
    audit_path=None,
    max_workers: int = 6,
) -> dict[str, Any]:
    """Cheap framing fact-check (no store rebuild): hold the retrieved ENTRIES fixed and
    vary ONLY the outcome FRAMING. Rewrite each net-first outcome toward its immediate
    consequence (re-emphasis, no new facts — only the outcome is shown to the agent), then
    replay each town day-vote under off / net (as-stored) / immediate (rewritten), paired
    on the same board. Scored on net-value (hit +1 / mislynch -1 / abstain 0) so
    situation-appropriate caution is credited, plus an abstain decomposition keyed on
    whether a threat was findable (the memory-OFF arm hit one). Tests whether immediate
    emphasis relieves the net-first content's blanket caution. NOTE: a synthetic reframe of
    the net entries, not the real immediate-first store — a directional screen."""
    cases = _select_diverse(batch_path, n, min_day, max_day, roles, "day_vote")

    # Rewrite each DISTINCT outcome once (dedup across decisions), in parallel.
    distinct = {
        o
        for case, _ in cases
        for item in (case.retrieved_observations or [])
        if (o := getattr(item.observation, "outcome", "") or "")
    }
    outcomes = sorted(distinct)
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        rewrites = list(ex.map(lambda o: _immediate_rewrite(o, rewrite_model), outcomes))
    rewrite_map = dict(zip(outcomes, rewrites))
    if audit_path:
        audit_path.write_text(
            json.dumps(
                [{"net": o, "immediate": rewrite_map[o]} for o in outcomes], indent=2
            )
        )

    def swap(observations: list[Any]) -> list[Any]:
        out = []
        for item in observations or []:
            o = getattr(item.observation, "outcome", "") or ""
            new_o = rewrite_map.get(o)
            if new_o and new_o != o:
                new_obs = item.observation.model_copy(update={"outcome": new_o})
                out.append(item.model_copy(update={"observation": new_obs}))
            else:
                out.append(item)
        return out

    def one(case: EvalCase, game: dict[str, Any]):
        allow = allow_abstain_for(case.day, game["day_resolutions"])
        roles_map = game["roles"]
        real = list(case.retrieved_observations or [])
        arms = {"off": [], "net": real, "immediate": swap(real)}
        out = {}
        for arm, retrieved in arms.items():
            votee, _ = _replay_vote(case, retrieved, allow)
            out[arm] = score_vote(votee, roles_map)
        return out

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        results = [f.result() for f in [ex.submit(one, c, g) for c, g in cases]]

    def netval(o: Any) -> int:
        return 1 if o.hit_threat else (-1 if o.is_town_mislynch else 0)

    arms = ("off", "net", "immediate")
    agg = {a: Counter() for a in arms}
    nv = {a: [0, 0] for a in arms}  # [sum, n]
    imm_better = imm_worse = 0
    for res in results:
        off_findable = res["off"].hit_threat  # a threat was findable from the board alone
        for a in arms:
            o = res[a]
            agg[a]["n"] += 1
            agg[a]["hit"] += o.hit_threat
            agg[a]["mislynch"] += o.is_town_mislynch
            agg[a]["abstain"] += o.is_abstain
            if o.is_abstain:
                agg[a]["abstain_gave_up_threat" if off_findable else "abstain_defensible"] += 1
            nv[a][0] += netval(o)
            nv[a][1] += 1
        di, dn = netval(res["immediate"]), netval(res["net"])
        if di > dn:
            imm_better += 1
        elif di < dn:
            imm_worse += 1

    def rate(a: str, k: str) -> float | None:
        return round(agg[a][k] / agg[a]["n"], 3) if agg[a]["n"] else None

    summary = {
        a: {
            "n": agg[a]["n"],
            "net_value": round(nv[a][0] / nv[a][1], 3) if nv[a][1] else None,
            "hit": rate(a, "hit"),
            "mislynch": rate(a, "mislynch"),
            "abstain": rate(a, "abstain"),
            "abstain_gave_up_threat": agg[a]["abstain_gave_up_threat"],
            "abstain_defensible": agg[a]["abstain_defensible"],
        }
        for a in arms
    }
    return {
        "batch": batch_path.name,
        "n_decisions": len(cases),
        "n_distinct_outcomes_rewritten": len(outcomes),
        "arms": summary,
        "immediate_minus_net_net_value": (
            round(summary["immediate"]["net_value"] - summary["net"]["net_value"], 3)
            if summary["immediate"]["net_value"] is not None
            and summary["net"]["net_value"] is not None
            else None
        ),
        "paired_immediate_vs_net": {
            "immediate_better": imm_better,
            "immediate_worse": imm_worse,
            "mcnemar_p": round(mcnemar_p(imm_worse, imm_better), 4),
        },
    }


def run_adherence_scan(
    batch_path,
    n: int = 40,
    min_day: int = 3,
    roles: frozenset[str] = REPLAYABLE_TOWN_ROLES,
    judge_model: str = DEFAULT_ADHERENCE_JUDGE_MODEL,
    max_workers: int = 6,
) -> dict[str, Any]:
    """Judge adherence on N RECORDED town decisions (no replay) and aggregate the
    labels — answers 'did the agent actually follow the injected memory?', to
    separate a memory-content null from a memory-not-adopted null. Each case
    already carries the agent's real vote + reasoning + the memory it was given."""
    cases = _select_diverse(batch_path, n, min_day, 999, roles, phase="day_vote")
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        results = [
            f.result()
            for f in [ex.submit(judge_decision_adherence, c, model=judge_model) for c, _ in cases]
        ]
    app: Counter[str] = Counter()
    follow: Counter[str] = Counter()
    direction: Counter[str] = Counter()
    n_dec = n_mem = 0
    for adh in results:
        if adh is None:
            continue
        n_dec += 1
        for r in adh.per_memory:
            n_mem += 1
            app[r.application] += 1
            follow[r.action_followed] += 1
            direction[r.implied_direction] += 1
    pct = lambda k: round(app[k] / n_mem, 3) if n_mem else None  # noqa: E731
    return {
        "batch": batch_path.name,
        "n_decisions_judged": n_dec,
        "n_memories_labeled": n_mem,
        "application": dict(app),
        "action_followed": dict(follow),
        "implied_direction": dict(direction),
        "pct_applied": pct("applied"),
        "pct_overrode": pct("overrode_with_reason"),
        "pct_ignored": pct("ignored"),
    }
