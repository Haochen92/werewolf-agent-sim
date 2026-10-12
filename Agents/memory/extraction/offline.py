"""Offline extraction: what the batch job makes of a finished game's saved extraction input.

Extraction never runs in a live game (owner's ruling 2026-10-12, evidence/memory_system/v8/
decisions.md §11): a game saves its input when it ends (the post-game node) and the offline job
extracts in batches. This module holds what the job hands on: the replay's "what this game taught"
payload, the same shape the post-game node once streamed.
"""

from __future__ import annotations

from typing import Any

from Agents.schemas.memory import BaseSituation


def extracted_dimensions(item: Any) -> dict | None:
    """The structured fields of one extracted v6 cell record, dumped the way the store write keeps
    them (store_ops: ``dimensions=model_dump``). None for a legacy Observation / StrategyPoint,
    which has no structured situation."""
    return item.model_dump(mode="json") if isinstance(item, BaseSituation) else None


def memory_extracted_payload(output: Any, *, day: int) -> dict[str, Any]:
    """What a finished game taught, for its replay's X-ray: the raw extraction, before any dedup
    against the store (a served game never writes the store, so there is no post-dedup form)."""
    observations = [
        {"perspective": o.perspective, "action_phase": o.action_phase, "situation": o.situation,
         "approach": getattr(o, "approach", ""), "outcome": getattr(o, "outcome", ""),
         "net_verdict": getattr(o, "net_verdict", ""), "dimensions": extracted_dimensions(o)}
        for o in output.observations
    ]
    strategy_points = [
        {"perspective": s.perspective, "action_phase": s.action_phase, "situation": s.situation,
         "action": s.action, "dimensions": extracted_dimensions(s)}
        for s in output.strategy_points
    ]
    return {"event": "memory_extracted", "day": day,
            "observations": observations, "strategy_points": strategy_points}


# --- Inputs for games that ended before inputs were saved ---------------------------------------
# Both rebuild the state fields format_extraction_inputs reads. Checked on the 12 v8 seeding games
# against the input live extraction used (decisions §11): the same discussion and wolf chat bar one
# pack vote line on a game's last night, and the newer note for a seat that died in the night (live
# state drops it; these keep it).

def _case(game_id: str, roles: dict, lineup: list, winner: str | None, state: dict,
          human_players: list | None = None):
    from Agents.memory.extraction.inputs import format_extraction_inputs
    from Agents.observability import extraction_span_name
    from Agents.schemas.evaluation import ExtractionCase

    inputs = format_extraction_inputs({"roles": roles, "lineup": lineup, "winner": winner or "unknown", **state})
    return ExtractionCase(
        span_name=extraction_span_name(game_id), game_id=game_id, game_outcome=inputs["game_outcome"],
        roles=roles, lineup=list(lineup), human_players=list(human_players or []),
        formatted_discussions=inputs["formatted_discussions"],
        formatted_strategy_notes=inputs["formatted_strategy_notes"],
    )


def _seat_order(roles: dict) -> list[str]:
    return sorted(roles, key=lambda p: int(p.rsplit("_", 1)[1]))


def input_from_run_records(game: dict, cases: list[dict]):
    """A run_batch game's extraction input, from its game record (discussion, night records,
    outcome) and its decision cases (each seat's last note; the wolf chat in the wolf seats'
    context). ``game`` is the record as run_batch wrote it (some fields as Python reprs)."""
    import ast

    from Agents.schemas.game_events import DayChannel, NightActionRecord, WolfChannel

    def field(name):
        value = game[name]
        return ast.literal_eval(value) if isinstance(value, str) and value[:1] in "[{" else value

    roles, nights = field("roles"), field("night_resolutions")
    notes, wolf = {}, {}
    for c in cases:
        if c.get("updated_strategy"):
            notes[c["player_id"]] = c["updated_strategy"]
        for m in (c.get("private_context") or {}).get("wolf_channel") or []:
            wolf[(m["day"], m["round"], m["wolf"], m.get("message"), m.get("vote"))] = m
    state = {
        "day_channel": [DayChannel.model_validate(m) for m in field("day_channel")],
        "wolf_channel": [WolfChannel.model_validate(m) for m in wolf.values()],
        "night_actions": [NightActionRecord.model_validate(r) for n in nights for r in n["records"]],
        "dead_roster": [{"player": p, "day": n["day"], "phase": "night"} for n in nights for p in n["deaths"]],
        "agent_strategies": {p: notes[p] for p in _seat_order(roles) if p in notes},
    }
    return _case(game["game_id"], roles, field("lineup"), game.get("winner"), state)


def input_from_event_log(game_id: str, events: list[dict], human_players: list | None = None):
    """A served game's extraction input, from its durable wire events: the speeches and the game
    master's lines, the wolf chat,
    each actor's night record (sent once per recipient; kept once), the night deaths, each seat's
    last strategy update, the roles and the outcome. The pack's binding kill votes are not wire
    messages, so the wolf chat has no vote lines."""
    from Agents.schemas.game_events import DayChannel, NightActionRecord, WolfChannel

    roles, lineup, winner, notes = {}, [], None, {}
    day_channel, wolf_channel, records, dead = [], [], {}, []
    for e in sorted(events, key=lambda e: e["seq"]):
        t = e["type"]
        if t == "roles_assigned":
            roles = e["roles"]
        elif t == "game_started":
            lineup = e.get("lineup") or []
        elif t == "game_over":
            winner = e.get("winner")
        elif t == "speech":
            day_channel.append(DayChannel(day=e["day"], seq=e.get("channel_seq", e["seq"]), player=e["player"],
                                          message=e["message"], claim=e.get("claim") or "none"))
        elif t == "gm_message":  # the game master's lines in the day channel (votes, night news)
            day_channel.append(DayChannel(day=e["day"], seq=e.get("channel_seq", e["seq"]),
                                          player="game_master", message=e["text"]))
        elif t == "wolf_message":
            wolf_channel.append(WolfChannel(day=e["day"], round=e["round"], wolf=e["wolf"],
                                            message=e.get("message") or "", vote="",
                                            passed=bool(e.get("passed"))))
        elif t == "night_record":
            key = (e["day"], e["actor"], e["action"], e.get("target"))
            records.setdefault(key, NightActionRecord(
                day=e["day"], actor=e["actor"], action=e["action"], target=e.get("target"),
                outcome=e.get("outcome") or "", result=e.get("result") or "", seen=e.get("seen") or []))
        elif t == "night_result":
            dead += [{"player": d["player"], "day": e["day"], "phase": "night"} for d in e.get("deaths") or []]
        elif t == "strategy_update":
            notes[e["player"]] = e["strategy"]
    state = {"day_channel": day_channel, "wolf_channel": wolf_channel, "night_actions": list(records.values()),
             "dead_roster": dead, "agent_strategies": {p: notes[p] for p in _seat_order(roles) if p in notes}}
    return _case(game_id, roles, lineup, winner, state, human_players)
