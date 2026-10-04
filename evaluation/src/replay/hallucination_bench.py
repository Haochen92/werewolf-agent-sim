"""Hallucination bench, replay half: regenerate one frozen turn as the current code would send it.

A bench case freezes the game STATE at the moment an agent took its turn (its JSON form; see the
builder, ``data/builders/hallucination_bench.py``). Replay rebuilds the turn's payload with the
engine's own Send builders (``build_speaker_send`` for a discussion turn, ``fan_out_day`` for a vote)
and renders the production template and output schema for the speaker's role, so the prompt is
whatever the checked-out code sends today. The prompt version and the model therefore come from
the process this runs in (env flags such as ``WW_DISCUSSION_PROMPT``, and ``GOOGLE_GENAI_MODEL``):
the bench runner gives each arm its own process.

Day discussion and day votes only for now. Night turns go through per-role night builders and are
not covered yet.

Engine-written parts of an old state are brought up to the checked-out engine, as a game played on
it would have them: game-master summaries are labelled as such, ballot lines take today's wording,
and the private night record is rebuilt from the case's stored night targets when the state
predates it. What players and the summariser wrote stays as it was, unless an arm re-summarises
the earlier days (``resummarize``), which tests the current summariser.
"""

from __future__ import annotations

import random
import re
import time
from typing import Any

from Agents.schemas.game_events import (
    DayChannel,
    DaySummary,
    DeathRecord,
    FiringReason,
    InvestigatorResult,
    NightActionRecord,
    WolfChannel,
)

PHASES = ("day_discussion", "day_vote")

_LIST_MODELS = {
    "day_channel": DayChannel,
    "day_summaries": DaySummary,
    "dead_roster": DeathRecord,
    "investigator_results": InvestigatorResult,
    "wolf_channel": WolfChannel,
    "night_actions": NightActionRecord,
}

_BALLOT = re.compile(r"^(\s+\S+) voted for (\S+)$", re.M)
_GM_OPENERS = ("Night of day", "Here's the vote result")


def _engine_wording(text: str) -> str:
    """Ballot lines as the engine writes them now ("voted to eliminate" / "voted to abstain")."""
    return _BALLOT.sub(lambda m: f"{m.group(1)} voted to " + (
        "abstain" if m.group(2) == "abstain" else f"eliminate {m.group(2)}"), text)


def hydrate_state(state: dict[str, Any]) -> dict[str, Any]:
    """A case's JSON state → the typed state the engine's builders and formatters expect."""
    out = dict(state)
    summaries = []
    for x in state.get("day_summaries") or []:
        x = dict(x)
        # States from before summaries were labelled: a checkpoint read back through today's model
        # even says "discussion" for an announcement. No discussion summary opens like one.
        if (x.get("summary") or "").lstrip().startswith(_GM_OPENERS):
            x["source"] = "game_master"
        x.setdefault("source", "discussion")
        if x["source"] == "game_master":
            x["summary"] = _engine_wording(x["summary"])
        summaries.append(x)
    channel = [{**m, "message": _engine_wording(m["message"])} if m.get("player") == "game_master" else m
               for m in state.get("day_channel") or []]
    for key, model in _LIST_MODELS.items():
        source = {"day_summaries": summaries, "day_channel": channel}.get(key, state.get(key) or [])
        out[key] = [model.model_validate(x) for x in source]
    return out


def night_actions_from_resolutions(resolutions: list[dict], roles: dict[str, str], day: int,
                                   lynches: list[dict] | None = None) -> list[NightActionRecord]:
    """The private night record as the engine would have written it, from stored night targets
    (``wolves_target`` / ``healer_target`` / ``serial_killer_target`` / ``vigilante_target`` per night),
    for the nights before ``day``. Actors are the role holders alive at each nightfall (``lynches``:
    the day resolutions, so a player voted out that day doesn't act). Holding fire can't be told from
    not being asked, so it is left out."""
    from Agents.rules.night_record import night_action_records
    from Agents.rules.resolution import collect_attacks, resolve_attacks

    night_death: dict[str, int] = {}  # killed on night d: still acted that night
    for r in resolutions:
        for p in r.get("deaths") or []:
            night_death.setdefault(p, int(r["day"]))
    lynch_day = {x["voted_player"]: int(x["day"]) for x in lynches or [] if x.get("voted_player")}
    records: list[NightActionRecord] = []
    for r in sorted(resolutions, key=lambda r: int(r["day"])):
        d = int(r["day"])
        if d >= day:
            continue
        holder = lambda role: next((p for p, x in roles.items() if x == role  # noqa: E731
                                    and night_death.get(p, 10**9) >= d and lynch_day.get(p, 10**9) > d), None)
        sk = holder("serial_killer")
        attacks = collect_attacks(r.get("wolves_target"), r.get("serial_killer_target"), r.get("vigilante_target"))
        records += night_action_records(
            d, wolves_target=r.get("wolves_target"), healer_target=r.get("healer_target"),
            serial_killer_target=r.get("serial_killer_target"), vigilante_target=r.get("vigilante_target"),
            attacks_on=attacks, verdicts=resolve_attacks(attacks, r.get("healer_target"), sk), roles=roles,
            healer=holder("healer"), serial_killer=sk, vigilante=holder("vigilante"))
    return records


def resummarize(cases: list[dict[str, Any]], cache: dict[str, dict]) -> None:
    """Fill ``cache`` ("game|arm|day" → summary) with the earlier days' discussion summaries rewritten by
    the checked-out summariser, day by day, each given the game master's record and the claims on
    record as of that day, as in a live game. One pass per game, from its latest case."""
    from Agents.nodes.day.summary_agent import run_day_summary_agent
    from Agents.schemas.roles import cast_role_counts

    latest: dict[str, dict] = {}
    for c in cases:
        key = f"{c['game_id']}|{c.get('game_arm', '')}"
        if key not in latest or c["day"] > latest[key]["day"]:
            latest[key] = c
    for key, case in latest.items():
        state = hydrate_state(case["state"])
        record = [s for s in state["day_summaries"] if s.source == "game_master"]
        done: list[DaySummary] = []
        for d in sorted({m.day for m in state["day_channel"] if m.day < case["day"]}):
            msgs = [m for m in state["day_channel"] if m.day == d and m.player != "game_master"]
            if not msgs:
                continue
            if f"{key}|{d}" not in cache:
                context = sorted([s for s in record if s.day < d] + done, key=lambda s: s.day)
                # deaths known by day d's discussion: every lynch and night before it
                dead = [x for x in state.get("dead_roster") or [] if x.day < d]
                text, _, structured = run_day_summary_agent(
                    d, msgs, 1, day_summaries=context, dead_roster=dead,
                    cast_role_counts=cast_role_counts(state["roles"]))
                cache[f"{key}|{d}"] = {"summary": text, "structured": structured}
            done.append(DaySummary(day=d, **cache[f"{key}|{d}"]))


def _resummarized(case: dict[str, Any], state: dict[str, Any], cache: dict[str, dict]) -> list[DaySummary]:
    """The state's summaries with each earlier day's discussion summary swapped for the cached rewrite."""
    key = f"{case['game_id']}|{case.get('game_arm', '')}"
    out = []
    for s in state["day_summaries"]:
        new = cache.get(f"{key}|{s.day}") if s.source == "discussion" and s.day < case["day"] else None
        out.append(DaySummary(day=s.day, **new) if new else s)
    return out


def turn_payload(case: dict[str, Any], memory: str = "none",
                 summaries: dict[str, dict] | None = None) -> dict[str, Any]:
    """The payload the engine would hand this speaker's node, built by the engine's own builders.

    ``memory``: "none" (the default) leaves memories out, as the live site's memory-off games do;
    "captured" puts back the memories the agent was shown in the original game (the census games'
    June stores, so only meaningful when that is what is being tested). ``summaries``: a
    ``resummarize`` cache; the earlier days' discussion summaries are swapped for its rewrites.
    """
    from Agents.nodes.day.flow import build_speaker_send, fan_out_day
    from Agents.schemas import RetrievedObservation, RetrievedStrategyPoint

    state = hydrate_state(case["state"])
    if "night_actions" not in case["state"]:  # a state from before the record existed
        facts = case.get("facts") or {}
        state["night_actions"] = night_actions_from_resolutions(
            facts.get("night_resolutions") or [], state["roles"], case["day"], facts.get("day_resolutions"))
    if summaries is not None:
        state["day_summaries"] = _resummarized(case, state, summaries)
    speaker, role = case["speaker"], case["role"]
    if case["phase"] == "day_discussion":
        from Agents.config.game import GameConfig
        from Agents.nodes.day.flow import discussion_stage_controls

        firing = FiringReason.model_validate(case.get("firing_reason") or {"tier": "proactive"})
        voting_available, opener_floor = discussion_stage_controls(state["current_day"], GameConfig())
        payload = dict(build_speaker_send(state, speaker, role, firing, opener_floor,
                                          voting_available=voting_available).arg)
    elif case["phase"] == "day_vote":
        sends = fan_out_day(state, "vote", allow_abstain=True)
        payload = dict(next(s.arg for s in sends if s.arg["player_id"] == speaker))
    else:
        raise ValueError(f"bench replay covers {PHASES}, not {case['phase']}")
    if memory == "captured":
        mem = case.get("memory") or {}
        payload["retrieved_observations"] = [
            RetrievedObservation.model_validate(o) for o in mem.get("observations") or []]
        payload["strategy_points"] = [
            RetrievedStrategyPoint.model_validate(s) for s in mem.get("strategy_points") or []]
    return payload


def generate(case: dict[str, Any], n: int, memory: str = "none",
             summaries: dict[str, dict] | None = None) -> list[dict[str, Any]]:
    """Sample the turn ``n`` times on the process's game model; each sample's text units."""
    from langchain_core.callbacks import UsageMetadataCallbackHandler

    from Agents.llm_factory import get_llm
    from Agents.nodes.day.actors import DISCUSS_PROMPTS, VOTE_PROMPTS
    from Agents.prompts.prompt_inputs import build_agent_prompt_input
    from Agents.schemas import DayDiscussOutput, DayVoteOutput
    from Agents.turn.action_space import output_schema_with_legal_targets, valid_targets_for_action

    payload = turn_payload(case, memory, summaries)
    if case["phase"] == "day_discussion":
        template, schema, key = DISCUSS_PROMPTS[case["role"]], DayDiscussOutput, "day_channel"
    else:
        template, schema, key = VOTE_PROMPTS[case["role"]], DayVoteOutput, "day_votes"
    bound = output_schema_with_legal_targets(schema, key, valid_targets_for_action(payload, key))
    chain = template | get_llm().with_structured_output(bound)
    prompt_input = build_agent_prompt_input(payload)

    samples = []
    for i in range(n):
        out, err = None, ""
        usage, started = UsageMetadataCallbackHandler(), time.monotonic()  # retries count: they're billed
        for attempt in range(5):  # the shared Vertex pool answers bursts with 429s: back off and retry
            try:
                out = chain.invoke(prompt_input, config={"callbacks": [usage]})
                break
            except Exception as e:
                err = str(e)[:300]
                if "429" not in err and "RESOURCE_EXHAUSTED" not in err and "504" not in err:
                    break
                time.sleep(min(60, 4 * 2 ** attempt) + random.random() * 3)
        if out is None:  # recorded; the sample counts as invalid and a rerun regenerates it
            samples.append({"sample": i, "valid": False, "error": err, "units": []})
            continue
        units = []
        message = getattr(out, "message", "") or ""
        if message.strip() and not getattr(out, "pass_turn", False):
            units.append({"unit": "message", "text": message})
        if (out.updated_strategy or "").strip():
            units.append({"unit": "updated_strategy", "text": out.updated_strategy})
        # A hand-written expectation can be about private beliefs too (a read calling a true
        # statement a lie), so golden cases also judge the reads.
        if case.get("golden") and getattr(out, "reads", None):
            units.append({"unit": "reads", "text": "\n".join(
                f"{r.player}: {r.suspected_role} ({r.confidence}): {r.why}" for r in out.reads)})
        samples.append({"sample": i, "valid": True, "units": units,
                        "vote": getattr(out, "vote_target", None),
                        "usage": _usage_totals(usage, time.monotonic() - started)})
    return samples


def _usage_totals(handler: Any, seconds: float) -> dict[str, float]:
    """One sample's tokens over every model call it made (cached is the part of input the provider
    served from cache; reasoning is billed as output), and its wall time including any 429 back-off."""
    totals = {"input": 0, "cached": 0, "output": 0, "reasoning": 0}
    for u in handler.usage_metadata.values():
        totals["input"] += u.get("input_tokens", 0)
        totals["cached"] += (u.get("input_token_details") or {}).get("cache_read", 0) or 0
        totals["output"] += u.get("output_tokens", 0)
        totals["reasoning"] += (u.get("output_token_details") or {}).get("reasoning", 0)
    return {**totals, "seconds": round(seconds, 2)}
