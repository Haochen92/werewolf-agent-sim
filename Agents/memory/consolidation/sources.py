"""Where credit's games come from: batch-run games from their files, served games from the database.

Credit (decisions §14) needs each game's record (roles, nights, days, the day channel's accusations,
the result) and each memory-on decision with the verdicts its seat gave the lessons it was shown. A
batch run writes both (the game record and its eval-case sidecar). A served game keeps neither: its
record is rebuilt from the wire events (``record_from_event_log``) and its decisions from the
``memory_consulted`` events (``eval_cases_from_events``), in the same shapes, so the credit code reads
either. Only AI-only games teach (the poisoning rule); a served game with a human seat is never loaded.
"""

from __future__ import annotations

import glob
import json
import os
from pathlib import Path

from Agents.rules.night_record import PACK_ACTOR
from Agents.schemas.roles import ROLE_SPECS, WOLVES


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


    roles, winner, neutral_result = {}, None, None
    records: dict[int, dict] = {}
    carriers: dict[int, str] = {}
    night_deaths: dict[int, list] = {}
    night_saves: dict[int, list] = {}
    night_self_bet_saves: dict[int, list] = {}
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
            # A save may be a fortune teller's own self-bet (announced since 2026-10-17), not a protection.
            night_saves[day] = [x["player"] for x in e.get("saves") or [] if not x.get("self_bet")]
            night_self_bet_saves[day] = [x["player"] for x in e.get("saves") or [] if x.get("self_bet")]
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
            [d["player"] for d in deaths], night_saves.get(day, []), night_self_bet_saves.get(day, []))
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
                    saved: list[str], self_bet_saved: list[str] = ()) -> list[dict]:
    """The records of actors who chose an action that night but were told nothing (they died): the
    result where the public outcome decides it, else ``unknown``."""


    told = {actor for actor, _action, _target in records}
    rebuilt = []
    for c in choices:
        actor, role, target = c.get("actor"), c.get("role"), c.get("target")
        if actor in told or role not in ROLE_SPECS or role == "necromancer":
            continue
        action = {"vigilante": "shoot"}.get(role, ROLE_SPECS[role].night_action)
        if action == "protect":
            result = "saved" if target in saved else "self_bet_saved" if target in self_bet_saved else "no_attack"
        elif action == "investigate":
            result = "suspicious" if ROLE_SPECS.get(roles.get(target, ""), None) and \
                ROLE_SPECS[roles[target]].side == WOLVES else "not_suspicious"
        elif action in ("kill", "shoot"):
            result = ("killed" if target in died else "saved" if target in saved
                      else "self_bet_saved" if target in self_bet_saved else "immune")
        elif action == "bet":
            result = "self_bet" if target == actor else "scored_1" if target in died else "missed"
        elif action == "pick":
            result = "picked"
        else:
            result = "unknown"
        rebuilt.append({"day": day, "actor": actor, "action": action, "target": target, "result": result,
                        "outcome": "", "seen": [], "untold": True})
    return rebuilt

# The wolves' night turns, as the round a decision's event carries (role sheet: the chat rounds 1 to 3,
# the carrier's kill round 4, a skill turn round 5).
_PACK_TURN_BY_ROUND = {1: "chat", 2: "chat", 3: "chat", 4: "kill", 5: "skill"}


def eval_cases_from_events(events: list[dict], record: dict) -> list[dict]:
    """A served game's memory-on decisions in the eval-case shape credit reads: one per
    ``memory_consulted`` event (the lessons shown, by store key, and the seat's verdict on each), with
    the decision itself from the record: the vote cast, the night turn's kind, the day's speech and
    accusations (pooled over the day, as credit grades a seat's discussion once per day)."""
    roles = record.get("roles") or {}
    votes = {(v["voter"], d["day"]): v["votee"] for d in record.get("day_resolutions") or [] for v in d.get("votes") or []}
    acted = {(r["actor"], n["day"]): r for n in record.get("night_resolutions") or [] for r in n.get("records") or []}
    speech: dict[tuple, dict] = {}
    for m in record.get("day_channel") or []:
        day = speech.setdefault((m["player"], m["day"]), {"message": "", "passed": True, "addressed_targets": []})
        if m.get("message"):
            day["message"] = (day["message"] + " " + m["message"]).strip()
            day["passed"] = False
        day["addressed_targets"] += m.get("addressed_targets") or []
    cases, seen = [], set()
    for e in sorted(events, key=lambda e: e["seq"]):
        if e.get("type") != "memory_consulted":
            continue
        unit = (e["player"], e["day"], e.get("round"), e["action_phase"])
        if unit in seen:  # a re-run node fires the event again
            continue
        seen.add(unit)
        player, day, phase, role = e["player"], e["day"], e["action_phase"], e.get("role") or roles.get(e["player"])
        ec = {"player_id": player, "player_role": role, "day": day, "round": e.get("round"), "action_phase": phase,
              "memory_enabled": True,
              "strategy_index_to_key": {str(lesson["index"]): lesson["key"] for lesson in e.get("lessons") or []},
              "strategy_verdicts": [{"strategy_index": v["strategy_index"], "verdict": v["verdict"]}
                                    for v in e.get("verdicts") or []]}
        if phase == "day_vote":
            ec["agent_vote"] = {"votee": votes.get((player, day))} if (player, day) in votes else None
        elif phase == "night_action":
            own = acted.get((player, day))
            if ROLE_SPECS.get(role) and ROLE_SPECS[role].side == WOLVES and e.get("round") in _PACK_TURN_BY_ROUND:
                kind = _PACK_TURN_BY_ROUND[e["round"]]
                if kind == "skill":
                    kind = ROLE_SPECS[role].night_action if own and own["action"] == ROLE_SPECS[role].night_action \
                        else "declined"
            else:
                kind = "declined" if own is None else "hold_fire" if own["action"] == "hold_fire" else \
                    ROLE_SPECS[role].night_action if role in ROLE_SPECS else own["action"]
            ec["agent_night_action"] = {"kind": kind, "target": own.get("target") if own else None}
        else:
            ec["agent_message"] = speech.get((player, day), {"message": "", "passed": True, "addressed_targets": []})
        cases.append(ec)
    return cases


def games_from_db(dsn: str | None = None, *, memory: bool | None = True, since: str | None = None) -> list[dict]:
    """Completed AI-only ten-seat served games (memory on by default; None = either), each as a record
    with its decisions inline (``eval_cases``). Read only. ``since``: an ISO time, games finished after it."""
    import psycopg
    from psycopg.rows import dict_row

    dsn = dsn or os.environ.get("WW_POSTGRES_DSN")
    query = ("select game_id from games where status = 'completed' and n_humans = 0 "
             "and jsonb_array_length(coalesce((select payload->'lineup' from events e "
             "where e.game_id = games.game_id and e.seq = 1), '[]')) = 10")
    params: list = []
    if memory is not None:
        query += " and memory = %s"
        params.append(memory)
    if since:
        query += " and finished_at > %s"
        params.append(since)
    games = []
    with psycopg.connect(dsn, autocommit=True, row_factory=dict_row,
                         options="-c default_transaction_read_only=on") as conn:
        for row in conn.execute(query + " order by finished_at", params).fetchall():
            events = [r["payload"] for r in conn.execute(
                "select payload from events where game_id = %s order by seq", (row["game_id"],)).fetchall()]
            record = record_from_event_log(row["game_id"], events)
            record["eval_cases"] = eval_cases_from_events(events, record)
            record["source"] = "server"
            games.append(record)
    return games


def games_from_files(spec: str) -> list[dict]:
    """The batch-run game records a glob (or a space-separated list of globs) names, each with its
    eval-case sidecar path resolved (records store it relative to where the batch ran)."""
    games = []
    for dump in sorted(f for pattern in spec.split() for f in glob.glob(pattern)):
        for line in open(dump):
            if not line.strip():
                continue
            g = json.loads(line)
            g["eval_cases_path"] = resolve_cases_path(g.get("eval_cases_path"), dump)
            g["source"] = "batch"
            games.append(g)
    return games


def resolve_cases_path(path: str | None, dump: str) -> str | None:
    """The eval-case sidecar of a record. A batch folder moved after the run leaves a stale path; it is
    then found by name under the dump's folder."""
    if not path:
        return None
    if os.path.exists(path):
        return path
    found = sorted(glob.glob(str(Path(dump).parent / "**" / Path(path).name), recursive=True))
    return found[0] if found else None
