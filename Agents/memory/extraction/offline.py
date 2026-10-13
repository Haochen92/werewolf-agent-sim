"""Offline extraction: what the batch job makes of a finished game's saved extraction input.

Extraction never runs in a live game (owner's ruling 2026-10-12, evidence/memory_system/v8/
decisions.md §11): a game saves its input when it ends (the post-game node) and the offline job
extracts in batches. This module holds the job's parts: the inputs of games that ended before
inputs were saved (rebuilt from their records), the batched extraction and de-halo pass, and the
replay's "what this game taught" payload, the same shape the post-game node once streamed. The
entry point is scripts/extract_batch.py.
"""

from __future__ import annotations

from logging import getLogger
from typing import Any

from Agents.schemas.memory import BaseSituation

logger = getLogger(__name__)


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



_NOT_VISITS = ("pick", "bet", "hold_fire")


def record_from_event_log(game_id: str, events: list[dict]) -> dict:
    """A served game's record in the shape the batch runner writes and the credit grader reads
    (consolidation/grading.py): roles, each night's records, choices, deaths and outcome (attackers,
    attacks, conceals, visits), each day's votes and lynch, the day channel's accusations, and the
    result. Rebuilt from the durable wire events; night choices come from the actors' own records
    (a blocked action keeps its record), the pack's kill from its carrier.

    A player is not told its result on the night it dies, so the wire has no record of its action that
    night, only its choice (``night_action``). That record is rebuilt where the public result decides it
    (a protection saved its target or not, a check reads by the target's side, a bet or a shot by the
    deaths) and marked ``unknown`` where it does not (a watch, a follow, a block, a conceal), which the
    grader leaves ungraded."""
    from Agents.rules.night_record import PACK_ACTOR

    roles, winner, neutral_result = {}, None, None
    records: dict[int, dict] = {}
    carriers: dict[int, str] = {}
    night_deaths: dict[int, list] = {}
    night_saves: dict[int, list] = {}
    night_choices: dict[int, list] = {}
    votes: dict[int, list] = {}
    lynches: dict[int, dict] = {}
    day_channel: list[dict] = []
    for e in sorted(events, key=lambda e: e["seq"]):
        t, day = e["type"], e.get("day")
        if t == "roles_assigned":
            roles = e["roles"]
        elif t == "game_over":
            winner, neutral_result = e.get("winner"), e.get("neutral_result")
        elif t == "night_record":  # sent once per recipient; kept once
            key = (e["actor"], e["action"], e.get("target"))
            records.setdefault(day, {}).setdefault(key, {k: e.get(k) for k in (
                "actor", "action", "target", "result", "outcome")} | {"day": day, "seen": e.get("seen") or []})
        elif t == "wolf_kill_decided":
            carriers[day] = e["carrier"]
        elif t == "night_result":
            night_deaths[day] = e.get("deaths") or []
            night_saves[day] = [x["player"] for x in e.get("saves") or []]
        elif t == "night_action":
            night_choices.setdefault(day, []).append(e)
        elif t == "vote_cast":
            votes.setdefault(day, []).append({"voter": e["voter"], "votee": e["votee"]})
        elif t == "lynch_result":
            lynches[day] = e
        elif t == "addressed_targets":
            day_channel.append({"day": day, "player": e["player"], "passed": False,
                                "addressed_targets": e.get("targets") or []})
        elif t == "speech":
            day_channel.append({"day": day, "player": e["player"], "passed": False, "addressed_targets": [],
                                "message": e.get("message", "")})

    nights = []
    for day in sorted(set(records) | set(night_choices)):
        deaths = night_deaths.get(day, [])
        recs = list(records.get(day, {}).values()) + _untold_records(
            day, night_choices.get(day, []), records.get(day, {}), roles,
            [d["player"] for d in deaths], night_saves.get(day, []))
        concealed = [d["player"] for d in deaths if d.get("concealed")]
        choices, attackers, attacks_on, visits = [], [], {}, []
        for r in recs:
            went_ahead = r["result"] != "roleblocked"
            if r["actor"] == PACK_ACTOR:
                actor = carriers.get(day)
                choices.append({"actor": actor, "kind": "kill", "role": roles.get(actor), "target": r["target"]})
                if went_ahead and actor:
                    attackers.append(actor)
                    attacks_on.setdefault(r["target"], []).append({"attacker": actor, "attacker_type": "wolves"})
                    if r["target"] not in concealed:  # a conceal hides the carrier's visit to its victim
                        visits.append([actor, r["target"]])
                continue
            kind = {"shoot": "kill"}.get(r["action"], r["action"])
            choices.append({"actor": r["actor"], "kind": kind, "role": roles.get(r["actor"]), "target": r["target"]})
            if not went_ahead:
                continue
            if r["action"] in ("kill", "shoot"):
                attackers.append(r["actor"])
                attacks_on.setdefault(r["target"], []).append({"attacker": r["actor"]})
            if r["action"] not in _NOT_VISITS and r["target"]:
                visits.append([r["actor"], r["target"]])
        nights.append({"day": day, "records": recs, "choices": choices, "deaths": [d["player"] for d in deaths],
                       "outcome": {"attackers": attackers, "attacks_on": attacks_on, "concealed": concealed,
                                   "visits": visits}})
    days = []
    for day in sorted(set(votes) | set(lynches)):
        lynch = lynches.get(day, {})
        days.append({"day": day, "votes": votes.get(day, []), "vote_counts": lynch.get("vote_counts") or {},
                     "voted_player": lynch.get("player"), "no_vote": lynch.get("outcome") == "no_vote",
                     "voted_player_role": lynch.get("role")})
    return {"game_id": game_id, "roles": roles, "winner": winner, "neutral_result": neutral_result,
            "night_resolutions": nights, "day_resolutions": days, "day_channel": day_channel}


def _untold_records(day: int, choices: list[dict], records: dict, roles: dict, died: list[str],
                    saved: list[str]) -> list[dict]:
    """The records of actors who chose an action that night but were told nothing (they died): the
    result where the public outcome decides it, else ``unknown``."""
    from Agents.schemas.roles import ROLE_SPECS, WOLVES

    told = {actor for actor, _action, _target in records}
    rebuilt = []
    for c in choices:
        actor, role, target = c.get("actor"), c.get("role"), c.get("target")
        if actor in told or role not in ROLE_SPECS or role == "necromancer":
            continue
        action = {"vigilante": "shoot"}.get(role, ROLE_SPECS[role].night_action)
        if action == "protect":
            result = "saved" if target in saved else "no_attack"
        elif action == "investigate":
            result = "suspicious" if ROLE_SPECS.get(roles.get(target, ""), None) and \
                ROLE_SPECS[roles[target]].side == WOLVES else "not_suspicious"
        elif action in ("kill", "shoot"):
            result = "killed" if target in died else "saved" if target in saved else "immune"
        elif action == "bet":
            result = "self_bet" if target == actor else "scored_1" if target in died else "missed"
        elif action == "pick":
            result = "picked"
        else:
            result = "unknown"
        rebuilt.append({"day": day, "actor": actor, "action": action, "target": target, "result": result,
                        "outcome": "", "seen": [], "untold": True})
    return rebuilt

# --- The job: saved inputs extracted in Claude batches -----------------------------------------
# One call per (game, dealt role, phase), as live extraction made them (cell_units.ROLE_UNITS): a
# game's calls share its prefix (the rules, the standards and the whole game record), marked for
# Claude's cache. A batch runs in no set order, so each game's first call goes direct and writes the
# prefix to the 1-hour cache; its other calls go in the batch and read it. Nothing is wasted: the
# direct call's answer is kept. Each call has its own cell schema, and an enforced schema is part of
# Claude's cache key, so the schema goes as text after the prefix (schema_in_prompt). A call the
# batch loses, or whose reply does not validate, goes in a second batch the same way (still reading
# the cache); what fails again is sent direct with the schema enforced and no cache marker: under its
# own schema it could only write a prefix no other call reads (in the first Sonnet run, 2026-10-12,
# 91 such retries each wrote a 16k prefix at the 1-hour rate, $7 of a $20 run).

def load_inputs(paths: list[str]) -> list[tuple[dict, Any]]:
    """(metadata, ExtractionCase) for each saved input in the given case files: records of kind
    ``extraction_input``, and ``postgame_extraction`` (an extracted game, whose input is reused)."""
    import json
    from pathlib import Path

    from Agents.schemas.evaluation import ExtractionCase

    out = []
    for path in paths:
        for line in Path(path).read_text().splitlines():
            record = json.loads(line)
            if record.get("kind") not in ("extraction_input", "postgame_extraction"):
                continue
            case = ExtractionCase.model_validate(record["output"]["extraction_case"])
            out.append((record.get("metadata") or {}, case.model_copy(update={"observations": [], "strategy_points": []})))
    return out


def cell_calls(case) -> tuple[str, list[tuple[str, str, str, type]]]:
    """The game's shared prefix and its calls: (role, action_phase, prompt, schema) for each phase
    of each dealt role."""
    from Agents.memory.extraction.cell_units import ROLE_UNITS
    from Agents.memory.extraction.inputs import (
        build_cell_extraction_prefix,
        build_cell_observation_tail,
        extraction_inputs_from_frozen_case,
    )
    from Agents.schemas.memory import cell_observation_schema_for, cell_observations_extraction_schema

    prefix = build_cell_extraction_prefix(extraction_inputs_from_frozen_case(case.model_dump()))
    calls = []
    for role in dict.fromkeys(case.roles.values()):
        for _group, wording, phase in ROLE_UNITS.get(role, []):
            obs_schema = cell_observation_schema_for(role, phase)
            schema = cell_observations_extraction_schema(role, phase)
            if obs_schema is None or schema is None:
                continue
            calls.append((role, phase, prefix + build_cell_observation_tail(role, wording, phase, obs_schema), schema))
    return prefix, calls


def _observations(result, phase: str) -> list:
    observations = list(result.observations)
    if phase in ("day_discussion", "day_vote"):  # one phase per call: the tag is the call's
        for o in observations:
            o.action_phase = phase
    return observations


def extract_cases(cases: list, model: str, thinking_level: str | None = None,
                  warm: bool = True, workers: int = 8) -> dict[str, dict]:
    """Extract each case's observations; by game id: {"observations", "missing", "model_used"}."""
    from concurrent.futures import ThreadPoolExecutor

    from Agents.llm_factory.providers.anthropic import batch_parse, parse_with_claude

    games = {case.game_id: cell_calls(case) for case in cases}
    keyed: dict[str, tuple[str, str, str, str, type, str]] = {}
    for gi, (game_id, (prefix, calls)) in enumerate(games.items()):
        for ci, (role, phase, prompt, schema) in enumerate(calls):
            keyed[f"g{gi}_c{ci}"] = (game_id, role, phase, prompt, schema, prefix)

    def direct(key: str, schema_in_prompt: bool = True):
        _game, _role, _phase, prompt, schema, prefix = keyed[key]
        try:
            return parse_with_claude(prompt, schema, model, thinking_level,
                                     cache_prefix=prefix if schema_in_prompt else None, cache_ttl="1h",
                                     schema_in_prompt=schema_in_prompt)[0]
        except Exception as e:  # noqa: BLE001 — a lost cell is reported, never fatal
            logger.warning("Direct extraction call %s failed: %s", key, e)
            return None

    leads = [next(k for k in keyed if keyed[k][0] == g) for g in games] if warm else []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        parsed = dict(zip(leads, pool.map(direct, leads)))
    rest = {k: (v[3], v[4], v[5]) for k, v in keyed.items() if k not in parsed}
    if rest:
        parsed.update(batch_parse(rest, model, thinking_level, cache_ttl="1h", schema_in_prompt=True))
    again = {k: (keyed[k][3], keyed[k][4], keyed[k][5]) for k, v in parsed.items() if v is None}
    if again:
        logger.info("%d calls lost or unvalidated; a second batch", len(again))
        parsed.update(batch_parse(again, model, thinking_level, cache_ttl="1h", schema_in_prompt=True))
    lost = [k for k, v in parsed.items() if v is None]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        parsed.update(zip(lost, pool.map(lambda k: direct(k, schema_in_prompt=False), lost)))

    out = {g: {"observations": [], "missing": [], "model_used": model} for g in games}
    for key, result in parsed.items():
        game_id, role, phase, *_ = keyed[key]
        if result is None:
            out[game_id]["missing"].append(f"{role}/{phase}")
        else:
            out[game_id]["observations"] += _observations(result, phase)
    return out


def extract_cases_gemini(cases: list) -> tuple[dict[str, dict], dict]:
    """Extract each case online on the game's extraction model (Gemini, ``DEFAULT_PRO_MODEL``) with
    its explicit prefix cache, the live extractor's path; by game id as ``extract_cases``, and the
    token usage by model. Gemini's cache holds the prompt text alone, so every cell reads it whatever
    its schema; Gemini batch is not built (decisions §11)."""
    from langchain_core.callbacks import get_usage_metadata_callback

    from Agents.memory.extraction.extraction_agent import extract_postgame_per_cell
    from Agents.memory.extraction.inputs import extraction_inputs_from_frozen_case

    out = {}
    with get_usage_metadata_callback() as cb:
        for i, case in enumerate(cases, 1):
            roles = tuple(dict.fromkeys(case.roles.values()))
            result = extract_postgame_per_cell(extraction_inputs_from_frozen_case(case.model_dump()), roles=roles,
                                               cache_prefix=True)
            observations = list(result.output.observations) if result else []
            missing = result.model_used.split("(missing: ", 1)[1].rstrip(")").split(",") if (
                result and "(missing: " in result.model_used) else ([] if result else ["all"])
            out[case.game_id] = {"observations": observations, "missing": missing,
                                 "model_used": result.model_used if result else "failed"}
            logger.info("Extracted %d of %d: %s, %d observations", i, len(cases), case.game_id[:8], len(observations))
    return out, dict(cb.usage_metadata)


def dehalo_cases(cases: list, extracted: dict[str, dict], config) -> dict[str, dict]:
    """The de-halo pass over each game's observations as one batch (``config``: DehaloConfig), the
    verdicts rewritten in place; by game id, the de-halo record."""
    from Agents.llm_factory.providers.anthropic import batch_parse, parse_with_claude
    from Agents.memory.extraction.dehalo import apply_judgments, dehalo_prompt
    from Agents.memory.extraction.inputs import extraction_inputs_from_frozen_case
    from Agents.schemas.dehalo import Judgments

    if not config.enabled:
        return {}
    prompts = {f"g{i}": (case.game_id, dehalo_prompt(extracted[case.game_id]["observations"],
                                                     extraction_inputs_from_frozen_case(case.model_dump())))
               for i, case in enumerate(cases) if extracted[case.game_id]["observations"]}
    judged = batch_parse({k: (p, Judgments) for k, (_g, p) in prompts.items()}, config.model, config.thinking_level)
    records = {}
    for key, (game_id, prompt) in prompts.items():
        result = judged.get(key)
        if result is None:
            try:
                result = parse_with_claude(prompt, Judgments, config.model, config.thinking_level)[0]
            except Exception as e:  # noqa: BLE001 — verdicts stay as extracted
                logger.warning("De-halo of %s failed: %s", game_id, e)
        if result is not None:
            records[game_id] = apply_judgments(extracted[game_id]["observations"], result, config.model,
                                               config.thinking_level, {"batched": True})
    return records


def extracted_games(paths: list[str]) -> list[tuple[str, list]]:
    """(game id, observations as cell models) per game in the job's ``extracted.jsonl`` files, games
    with a human seat left out (they never teach the store)."""
    import json
    from pathlib import Path

    from Agents.schemas.memory import cell_observation_schema_for

    games = []
    for path in paths:
        for line in Path(path).read_text().splitlines():
            case = json.loads(line)["output"]["extraction_case"]
            if case.get("human_players"):
                continue
            observations = [cell_observation_schema_for(o["perspective"], o["action_phase"]).model_validate(
                _with_decision_fields(o)) for o in case["observations"]]
            games.append((case["game_id"], observations))
    return games


def _with_decision_fields(observation: dict) -> dict:
    """An observation extracted before it named its decision (2026-10-13) loads with decision_day -1
    (not tagged) and, on a wolf's night, pack_turn "several"; the tagging pass supplies the real ones."""
    from Agents.schemas.memory import PACK_NIGHT_ROLES

    filled = {"decision_day": -1, **observation}
    if observation.get("action_phase") == "night_action" and observation.get("perspective") in PACK_NIGHT_ROLES:
        filled.setdefault("pack_turn", "several")
    return filled


def write_extracted_store(paths: list[str], out) -> dict:
    """Write the job's extracted observations into a fresh store at ``out`` the way the post-game
    node did: each game's observations deduplicated against the store as they go in, then dumped."""
    from pathlib import Path

    from langgraph.store.memory import InMemoryStore

    from Agents.memory.deduplication import run_downstream_observation_dedup
    from Agents.memory.persistence.config import memory_store_paths
    from Agents.memory.persistence.dump import dump_memory_to_json_files
    from Agents.memory.store import store as indexed_store

    target = InMemoryStore(index=indexed_store.index_config)
    stats = {"games": 0, "observations": 0, "kept": 0, "discarded": 0, "failed": 0}
    for i, (game_id, observations) in enumerate(extracted_games(paths), 1):
        s = run_downstream_observation_dedup(target, observations, game_id)
        stats["games"] += 1
        stats["observations"] += len(observations)
        for k in ("kept", "discarded", "failed"):
            stats[k] += getattr(s, k)
        logger.info("%3d %s: %d observations, kept %d, discarded %d", i, game_id[:8], len(observations),
                    s.kept, s.discarded)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    obs_path, sp_path = memory_store_paths(out)
    dump_memory_to_json_files(obs_path, sp_path, target_store=target)
    return stats
