"""Decision-replay screen for memory framing — observational pass (Step 1).

Loads frozen town day_vote decisions from a batch's eval-case sidecars, scores
each RECORDED vote against the game's true roles, and validates the
``allow_abstain`` reconstruction against the votes that actually happened. This
is the no-LLM foundation/smoke: it proves the case loader, the roles join, and
the abstain recovery before any LLM replay.

The causal arms (swap the injected memory and/or the prompt -> regenerate the
vote -> re-score) build on the same scoring (``decision_scoring``) plus the
existing single-decision replay harness
(``evaluation.src.replay.application.run_application_action``).

Run: ``poetry run python evaluation/src/experiments/decision_replay.py \
        --batch batch_results/ab_nh_town.jsonl``
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, OrderedDict
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from math import comb
from pathlib import Path
from typing import Any, Literal

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
    MemoryVerdict,
    SerialKillerOutput,
    VigilanteOutput,
    WolfNightDiscussOutput,
)
from Agents.llm_factory import create_chat_model, get_llm
from Agents.prompts.prompt_formatters import format_day_channel
from Agents.prompts.prompt_inputs import build_agent_prompt_input
from Agents.turn import _run_agent
from Agents.turn.action_space import _valid_targets_for_action, _with_dynamic_target_enum
from evaluation.src.replay.application import (
    action_spec_for,
    application_case_for_judge,
    run_application_action,
)
from evaluation.src.loop.decision_scoring import (
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
from evaluation.src.loop.memory_adherence import (
    DEFAULT_ADHERENCE_JUDGE_MODEL,
    judge_decision_adherence,
    judge_discussion_stance,
    summarize_adherence,
)
from evaluation.src.replay.situation_summary import eval_case_to_agent_payload
from evaluation.src.data.sources.sidecar import LocalCaseSource
from pydantic import BaseModel, Field


class DayVoteOutputReasonFirst(BaseModel):
    """Experimental reason-before-act variant of DayVoteOutput: updated_strategy
    (the reasoning, where injected memory gets integrated) is emitted BEFORE
    vote_target, so the model thinks before committing the vote instead of
    snap-voting then rationalizing. Field semantics match production; only the
    ORDER differs. Used as a replay input, never written to production."""

    adopted_strategy_keys: list[int] = Field(
        default_factory=list,
        description="Indices of strategy points whose advice your action follows, empty list if none match",
    )
    updated_strategy: str
    vote_target: str


class DayVoteOutputMemoryLinked(BaseModel):
    """Reason-before-act with an explicit memory-LINKING step: the reasoning field
    (kept named updated_strategy so the live extractor + the adherence judge read
    it unchanged) is emitted FIRST and its description forces the agent to connect
    the retrieved memories to THIS vote before committing. Aim is to maximize
    memory consideration, not the score. Replay input only."""

    adopted_strategy_keys: list[int] = Field(
        default_factory=list,
        description="Indices of strategy points whose advice your action follows, empty list if none match",
    )
    updated_strategy: str = Field(
        description=(
            "Before you vote, reason about THIS vote: go through the retrieved "
            "memories one by one, decide which actually apply to the current "
            "players and situation, and state explicitly how each changes (or does "
            "not change) who you should vote for. Make the link between the "
            "memories and your final choice explicit; if none apply, say so and why."
        )
    )
    vote_target: str


class DayVoteOutputSituationMatch(BaseModel):
    """Situation-applicability variant: updated_strategy (emitted BEFORE vote_target)
    is instructed to compare EACH retrieved observation's situation to the current
    board across the decision-relevant dimensions, judge how much it applies, and
    apply each lesson only to that degree. Capability probe — tests whether the game
    model can reason about applicability when asked explicitly. adopted_strategy_keys
    is intentionally DROPPED: we inject no strategy points, so it would be a vestigial
    no-op that competes with the observation-applicability prose we're testing.
    Replay input only."""

    updated_strategy: str = Field(
        description=(
            "Before you vote, go through the retrieved observations ONE BY ONE and compare each "
            "one's situation to your CURRENT board: the evidence available and how credible it is, "
            "how many players and which roles remain and who this vote would remove, and the "
            "consensus and who is targeting whom. For each, state whether it FULLY applies, PARTLY "
            "applies, or does NOT apply to your board, and why. Then decide, applying each lesson "
            "only to the degree its situation matches yours."
        )
    )
    vote_target: str


class DayVoteOutputStructuredApplicability(BaseModel):
    """Forced-structured applicability variant: ONE verdict row per retrieved
    observation (the model cannot skip the assessment), emitted BEFORE the vote.
    Capability probe — does the game model produce sensible per-memory verdicts? Captured
    by a direct chain call (a new field is dropped by _run_agent's mapping). No
    adopted_strategy_keys (vestigial here). Replay input only."""

    memory_applicability: list[MemoryVerdict] = Field(
        description="Produce ONE verdict per retrieved observation, in the SAME ORDER they are listed. "
        "For each, compare its situation to your current board and judge whether it fully applies, "
        "partly applies, or does not apply."
    )
    updated_strategy: str = Field(
        description="Your vote reasoning, applying each observation only to the degree your "
        "memory_applicability verdict says it applies."
    )
    vote_target: str


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
    schema_override: Any | None = None,
) -> tuple[str | None, str]:
    """Regenerate one vote with a swapped memory block and the correct abstain
    choice set. Returns (votee, replayed updated_strategy). prompt_template and
    schema_override let an arm vary the prompt or the output schema (e.g. the
    reason-first DayVoteOutput); defaults are the role's live template + schema."""
    payload = eval_case_to_agent_payload(case)
    payload["retrieved_observations"] = retrieved_observations
    payload["strategy_points"] = []
    payload["allow_abstain"] = allow_abstain
    spec = action_spec_for(case)
    result = _run_agent(
        payload,
        prompt_template or spec.prompt_template,
        schema_override or spec.output_schema,
        spec.output_key,
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


def run_reorder_test(
    batch_path: Path,
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
    batch_path: Path,
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


# Judge-FREE engagement read (reuses the paired_ab echo logic): how much of the
# agent's post-retrieval reasoning is drawn from the words of the memory it was
# given. Every prior "did it engage the memory" number came from the adherence
# judge (which reads STATED reasoning and may agree with the agent); this is the
# first measure that needs no LLM to score.
_ECHO_STOP = set(
    """the a an and or but if then else of to in on at by for with from as is are was were be been
    being this that these those it its their they them he she his her you your we our i my me will would can
    could should may might must do does did not no yes so very more most much many few both all any each
    other some such than too then once here there when where which who whom what how why into out up down off
    over under again further about against between through during before after above below their them having
    have has had your yours ourselves a's able about above according""".split()
)


def _echo_toks(s: str | None) -> set[str]:
    if not s:
        return set()
    return {w for w in re.findall(r"[a-z]{4,}", s.lower()) if w not in _ECHO_STOP}


def _echo(reasoning: str | None, mem_text: str) -> float | None:
    """Fraction of the reasoning's distinctive (>=4-char, non-stopword) tokens that
    also appear in the memory text; None if the reasoning has no scorable tokens."""
    s, m = _echo_toks(reasoning), _echo_toks(mem_text)
    return (len(s & m) / len(s)) if s else None


def _mem_text(case: EvalCase) -> str:
    """The stable/actionable text of a decision's retrieved memory (each entry's
    approach + situation) — what the reasoning would echo if it actually engaged
    the memory. Outcome wording is excluded (it changes across framings)."""
    bag: list[str] = []
    for item in case.retrieved_observations or []:
        obs = item.observation
        bag.append(getattr(obs, "approach", "") or "")
        bag.append(getattr(obs, "situation", "") or "")
    return " ".join(bag)


def run_echo_consideration(
    batch_path: Path,
    n: int = 150,
    min_day: int = 3,
    roles: frozenset[str] = REPLAYABLE_TOWN_ROLES,
    max_workers: int = 6,
) -> dict[str, Any]:
    """Judge-FREE engagement screen. Replay the STORED arm under each of the three
    schemas {vote-first, reason-first, memory-linked} and measure how much of the
    regenerated reasoning is drawn from the retrieved memory (echo), ABOVE a
    shuffled-memory floor (the same reasoning scored against a foreign decision's
    memory). The floor is taken per-schema and per-decision, so it cancels verbosity:
    a longer memory-flavored note overlaps ANY memory, and only echo-above-floor
    isolates genuine drawing-on. Paired by decision -> does the memory-LINKED wording
    make the reasoning engage the memory more than plain vote-first, with no judge?"""
    cases = _select_diverse(batch_path, n, min_day, 999, roles, phase="day_vote")
    schemas = {
        "vote_first": None,
        "reason_first": DayVoteOutputReasonFirst,
        "memory_linked": DayVoteOutputMemoryLinked,
    }

    def one(case: EvalCase, game: dict[str, Any]):
        allow = allow_abstain_for(case.day, game["day_resolutions"])
        reasonings = {}
        for sname, sch in schemas.items():
            _, updated = _replay_vote(
                case, case.retrieved_observations, allow, schema_override=sch
            )
            reasonings[sname] = updated
        return {"mem": _mem_text(case), "reasonings": reasonings}

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        results = [f.result() for f in [ex.submit(one, c, g) for c, g in cases]]

    # Per decision i, per schema s: own-memory echo and the foreign-memory floor
    # (same reasoning vs decision (i+k)'s memory). per_dec[s][i] = own - floor keeps
    # it paired so the schema-vs-schema deltas align on the same decisions.
    mems = [r["mem"] for r in results]
    k = len(results) // 3 or 1
    own_by: dict[str, list[float]] = {s: [] for s in schemas}
    floor_by: dict[str, list[float]] = {s: [] for s in schemas}
    per_dec: dict[str, dict[int, float]] = {s: {} for s in schemas}
    for i, r in enumerate(results):
        foreign = mems[(i + k) % len(mems)] if mems else ""
        for s in schemas:
            own = _echo(r["reasonings"][s], r["mem"])
            flo = _echo(r["reasonings"][s], foreign)
            if own is not None:
                own_by[s].append(own)
            if flo is not None:
                floor_by[s].append(flo)
            if own is not None and flo is not None:
                per_dec[s][i] = own - flo

    avg = lambda xs: round(sum(xs) / len(xs), 4) if xs else None  # noqa: E731
    by_schema = {
        s: {
            "n": len(per_dec[s]),
            "echo": avg(own_by[s]),
            "shuffle_floor": avg(floor_by[s]),
            "echo_above_floor": avg(list(per_dec[s].values())),
        }
        for s in schemas
    }
    vf = per_dec["vote_first"]
    vs_vote_first = {}
    for s in schemas:
        if s == "vote_first":
            continue
        paired = [per_dec[s][i] - vf[i] for i in per_dec[s] if i in vf]
        vs_vote_first[s] = {
            "n_paired": len(paired),
            "delta_echo_above_floor": avg(paired),
        }
    return {
        "batch": batch_path.name,
        "n_decisions": len(cases),
        "by_schema": by_schema,
        "engagement_vs_vote_first": vs_vote_first,
    }


def run_echo_judge_validation(
    batch_path: Path,
    n: int = 40,
    min_day: int = 3,
    roles: frozenset[str] = REPLAYABLE_TOWN_ROLES,
    judge_model: str = DEFAULT_ADHERENCE_JUDGE_MODEL,
    max_workers: int = 6,
) -> dict[str, Any]:
    """Does the judge-free echo agree with the adherence JUDGE? Replay each decision
    once (production vote-first schema), then score the SAME regenerated action two
    ways: echo (lexical draw-on) and the judge's per-memory applied/overrode/ignored.
    If they agree, judge-engaged decisions carry higher echo than judge-ignored ones.
    Each row also keeps the memory + reasoning + the judge's per-memory evidence, so
    the JUDGE'S OWN accuracy can be read by hand (echo can't validate the judge — only
    a human can say whether 'applied' was the right call on a given reasoning)."""
    cases = _select_diverse(batch_path, n, min_day, 999, roles)

    def one(case: EvalCase, game: dict[str, Any]):
        allow = allow_abstain_for(case.day, game["day_resolutions"])
        votee, updated = _replay_vote(case, case.retrieved_observations, allow)
        mem = _mem_text(case)
        echo_own = _echo(updated, mem)
        jcase = application_case_for_judge(
            case,
            agent_message=None,
            agent_vote=DayVote(voter=case.player_id, votee=votee or "abstain"),
            updated_strategy=updated,
        )
        adh = judge_decision_adherence(jcase, model=judge_model)
        labels = [
            {
                "application": r.application,
                "action_followed": r.action_followed,
                "implied_direction": r.implied_direction,
                "evidence": r.evidence,
            }
            for r in (adh.per_memory if adh else [])
        ]
        nmem = len(labels)
        applied = sum(la["application"] == "applied" for la in labels)
        overrode = sum(la["application"] == "overrode_with_reason" for la in labels)
        ignored = sum(la["application"] == "ignored" for la in labels)
        return {
            "game": str(game["game_id"])[:8],
            "role": case.player_role,
            "day": case.day,
            "echo": round(echo_own, 4) if echo_own is not None else None,
            "n_mem": nmem,
            "frac_applied": round(applied / nmem, 3) if nmem else None,
            "frac_engaged": round((applied + overrode) / nmem, 3) if nmem else None,
            "frac_ignored": round(ignored / nmem, 3) if nmem else None,
            "vote": votee,
            "mem_text": mem[:500],
            "reasoning": (updated or "")[:500],
            "labels": labels,
        }

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        rows = [f.result() for f in [ex.submit(one, c, g) for c, g in cases]]

    scored = [r for r in rows if r["echo"] is not None and r["frac_engaged"] is not None]
    engaged = [r["echo"] for r in scored if r["frac_engaged"] >= 0.5]
    ign = [r["echo"] for r in scored if r["frac_ignored"] is not None and r["frac_ignored"] > 0.5]
    mean = lambda xs: round(sum(xs) / len(xs), 4) if xs else None  # noqa: E731
    rho = pval = None
    try:  # rank correlation of echo vs judge engagement, if scipy is present
        from scipy.stats import spearmanr

        es = [r["echo"] for r in scored]
        fs = [r["frac_engaged"] for r in scored]
        if len(es) >= 5:
            rs = spearmanr(es, fs)
            rho, pval = round(float(rs.statistic), 3), round(float(rs.pvalue), 4)
    except Exception:  # noqa: BLE001 - correlation is a nice-to-have
        pass
    return {
        "batch": batch_path.name,
        "n_decisions": len(rows),
        "n_scored": len(scored),
        "echo_when_judge_engaged": {"n": len(engaged), "mean_echo": mean(engaged)},
        "echo_when_judge_ignored": {"n": len(ign), "mean_echo": mean(ign)},
        "spearman_echo_vs_frac_engaged": {"rho": rho, "p": pval},
        "rows": rows,
    }


_GRID_CONDITIONS = [
    ("off / vote-first", "off", None),
    ("stored / vote-first", "stored", None),
    ("stored / reason-first", "stored", DayVoteOutputReasonFirst),
    ("stored / memory-linked", "stored", DayVoteOutputMemoryLinked),
]


def _find_case(
    batch_path: Path, game_prefix: str, role: str, day: int, mem_substr: str
) -> tuple[EvalCase | None, dict[str, Any] | None]:
    """Locate ONE frozen decision by game-id prefix + role + day, disambiguating
    same-game/same-role/same-day villagers by a substring of their retrieved memory
    (the memory is frozen on the case, so this is deterministic)."""
    for case, game in iter_cases(batch_path, frozenset({role}), "day_vote"):
        if (
            str(game["game_id"]).startswith(game_prefix)
            and case.day == day
            and mem_substr in _mem_text(case)
        ):
            return case, game
    return None, None


def replay_condition_grid(
    batch_path: Path,
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
    batch_path: Path,
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


def _find_endgame_plant(batch_path: Path) -> Any | None:
    """Grab a real retrieved-observation object whose situation is unmistakably an
    ENDGAME (four-player / final-three), to inject as a clear mismatch into mid-game
    decisions. Reusing a real object guarantees a valid schema for the replay."""
    for case, _ in iter_cases(batch_path, REPLAYABLE_TOWN_ROLES, "day_vote"):
        for item in case.retrieved_observations or []:
            s = (getattr(item.observation, "situation", "") or "").lower()
            if "endgame" in s and any(
                k in s for k in ("four-player", "four player", "final-three", "final three", "three remaining")
            ):
                return item
    return None


def _replay_vote_structured(
    case: EvalCase, retrieved_observations: list[Any], allow_abstain: bool
) -> Any | None:
    """Regenerate one vote under DayVoteOutputStructuredApplicability, returning the RAW
    structured object — _run_agent's mapping drops unknown fields, so the per-memory
    memory_applicability list would be lost through it. Mirrors _run_agent's structured
    call (dynamic target enum keeps vote_target a legal player) without the mapping."""
    payload = eval_case_to_agent_payload(case)
    payload["retrieved_observations"] = retrieved_observations
    payload["strategy_points"] = []
    payload["allow_abstain"] = allow_abstain
    spec = action_spec_for(case)
    valid_targets = _valid_targets_for_action(payload, spec.output_key)
    schema = _with_dynamic_target_enum(
        DayVoteOutputStructuredApplicability, spec.output_key, valid_targets
    )
    chain = spec.prompt_template | get_llm().with_structured_output(schema)
    try:
        return chain.invoke(
            build_agent_prompt_input(payload),
            config={"run_name": f"applic_{case.player_id}"},
        )
    except Exception:  # noqa: BLE001 - best-effort replay
        return None


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
    batch_path: Path,
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
    batch_path: Path,
    n: int = 40,
    min_day: int = 3,
    max_day: int = 999,
    roles: frozenset[str] = REPLAYABLE_TOWN_ROLES,
    rewrite_model: str = "gemini-2.5-flash",
    audit_path: Path | None = None,
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
    batch_path: Path,
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
        "--adherence-scan",
        type=int,
        default=0,
        help="judge adherence on N RECORDED decisions and aggregate (did the "
        "agent follow the memory?) — no replay",
    )
    ap.add_argument(
        "--reorder",
        type=int,
        default=0,
        help="judge-free 2x2: replay N decisions under vote-first vs reason-first "
        "schema x memory off vs stored (tests the reason-before-act fix)",
    )
    ap.add_argument(
        "--reorder-adoption",
        type=int,
        default=0,
        help="judge adoption under vote-first vs reason-first (did reorder raise "
        "memory consideration?)",
    )
    ap.add_argument(
        "--echo",
        type=int,
        default=0,
        help="judge-FREE engagement: replay N decisions under vote-first vs "
        "reason-first vs memory-linked, measure how much each schema's reasoning "
        "draws on the retrieved memory (echo above a shuffled-memory floor)",
    )
    ap.add_argument(
        "--echo-validate",
        type=int,
        default=0,
        help="validate echo against the adherence judge on N replayed decisions: "
        "does echo agree with applied/ignored, and is the judge itself accurate "
        "(rows keep memory+reasoning+judge evidence to read by hand)",
    )
    ap.add_argument(
        "--coherence",
        type=int,
        default=0,
        help="does reordering SYNC vote with reasoning? Replay N decisions under "
        "vote-first/reason-first/memory-linked; judge reads the reasoning blind and "
        "its concluded choice is compared to the real vote (synced/desync/unclear)",
    )
    ap.add_argument(
        "--applicability",
        type=int,
        default=0,
        help="CAPABILITY probe: inject a clearly-mismatched ENDGAME memory into N "
        "mid-game decisions under the situation-match schema; does the agent reason "
        "it out as not-applicable (rejection rate + reasoning to read by hand)?",
    )
    ap.add_argument(
        "--framing",
        type=int,
        default=0,
        help="framing fact-check: hold the retrieved entries fixed, rewrite each "
        "outcome net->immediate, replay N town day-votes off/net/immediate, paired "
        "(net-value + abstain decomposition)",
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
    elif args.adherence_scan:
        print(json.dumps(run_adherence_scan(args.batch, n=args.adherence_scan, min_day=args.min_day, roles=roles), indent=2))
    elif args.reorder:
        print(json.dumps(run_reorder_test(args.batch, n=args.reorder, min_day=args.min_day, roles=roles), indent=2))
    elif args.reorder_adoption:
        print(json.dumps(run_reorder_adoption(args.batch, n=args.reorder_adoption, min_day=args.min_day, roles=roles), indent=2))
    elif args.echo:
        print(json.dumps(run_echo_consideration(args.batch, n=args.echo, min_day=args.min_day, roles=roles), indent=2))
    elif args.echo_validate:
        print(json.dumps(run_echo_judge_validation(args.batch, n=args.echo_validate, min_day=args.min_day, roles=roles, judge_model=args.model), indent=2))
    elif args.coherence:
        print(json.dumps(run_coherence_test(args.batch, n=args.coherence, min_day=args.min_day, roles=roles), indent=2))
    elif args.applicability:
        print(json.dumps(run_applicability_probe(args.batch, n=args.applicability, day=args.min_day), indent=2))
    elif args.framing:
        print(json.dumps(run_framing_rewrite_screen(
            args.batch, n=args.framing, min_day=args.min_day, max_day=args.max_day, roles=roles,
            audit_path=Path(
                f"evidence/memory_system/effectiveness/decision_replay/content_pilot/immediate_rewrites_d{args.min_day}-{args.max_day}.json"
            ),
        ), indent=2))
    else:
        print(json.dumps(run_observational(args.batch), indent=2))


if __name__ == "__main__":
    main()
