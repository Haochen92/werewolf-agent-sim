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
"""

from __future__ import annotations

from typing import Any

from Agents.schemas.game_events import (
    DayChannel,
    DaySummary,
    DeathRecord,
    FiringReason,
    InvestigatorResult,
    WolfChannel,
)

PHASES = ("day_discussion", "day_vote")

_LIST_MODELS = {
    "day_channel": DayChannel,
    "day_summaries": DaySummary,
    "dead_roster": DeathRecord,
    "investigator_results": InvestigatorResult,
    "wolf_channel": WolfChannel,
}


def hydrate_state(state: dict[str, Any]) -> dict[str, Any]:
    """A case's JSON state → the typed state the engine's builders and formatters expect."""
    out = dict(state)
    for key, model in _LIST_MODELS.items():
        out[key] = [model.model_validate(x) for x in state.get(key) or []]
    return out


def turn_payload(case: dict[str, Any], memory: str = "none") -> dict[str, Any]:
    """The payload the engine would hand this speaker's node, built by the engine's own builders.

    ``memory``: "none" (the default) leaves memories out, as the live site's memory-off games do;
    "captured" puts back the memories the agent was shown in the original game (the census games'
    June stores, so only meaningful when that is what is being tested).
    """
    from Agents.nodes.day.flow import build_speaker_send, fan_out_day
    from Agents.schemas import RetrievedObservation, RetrievedStrategyPoint

    state = hydrate_state(case["state"])
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


def generate(case: dict[str, Any], n: int, memory: str = "none") -> list[dict[str, Any]]:
    """Sample the turn ``n`` times on the process's game model; each sample's text units."""
    from Agents.llm_factory import get_llm
    from Agents.nodes.day.actors import DISCUSS_PROMPTS, VOTE_PROMPTS
    from Agents.prompts.prompt_inputs import build_agent_prompt_input
    from Agents.schemas import DayDiscussOutput, DayVoteOutput
    from Agents.turn.action_space import output_schema_with_legal_targets, valid_targets_for_action

    payload = turn_payload(case, memory)
    if case["phase"] == "day_discussion":
        template, schema, key = DISCUSS_PROMPTS[case["role"]], DayDiscussOutput, "day_channel"
    else:
        template, schema, key = VOTE_PROMPTS[case["role"]], DayVoteOutput, "day_votes"
    bound = output_schema_with_legal_targets(schema, key, valid_targets_for_action(payload, key))
    chain = template | get_llm().with_structured_output(bound)
    prompt_input = build_agent_prompt_input(payload)

    samples = []
    for i in range(n):
        try:
            out = chain.invoke(prompt_input)
        except Exception as e:  # transport / parse: recorded, the sample counts as invalid
            samples.append({"sample": i, "valid": False, "error": str(e)[:300], "units": []})
            continue
        units = []
        message = getattr(out, "message", "") or ""
        if message.strip() and not getattr(out, "pass_turn", False):
            units.append({"unit": "message", "text": message})
        if (out.updated_strategy or "").strip():
            units.append({"unit": "updated_strategy", "text": out.updated_strategy})
        samples.append({"sample": i, "valid": True, "units": units,
                        "vote": getattr(out, "vote_target", None)})
    return samples
