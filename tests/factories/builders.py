"""Hand-written domain builders shared across suites (promoted from per-file duplicates).

Promotion policy: a builder moves here only when >=2 files carried the SAME definition;
semantic per-file variants stay local (and may wrap these, overriding defaults). Consumers
import under their established short alias where that keeps call sites untouched:
``from tests.factories.builders import strategy_point as _sp``.

Deliberately NOT polyfactory: this data carries cross-field game invariants (roles <->
survivors <-> votes) that random-valid generation would violate. Random generation is
reserved for the pure wire schemas in tests/factories/events.py.
"""

from __future__ import annotations

from types import SimpleNamespace

from Agents.schemas.human_player import HumanTurnRequest
from Agents.tracing import Metrics


def human_turn_request(**over) -> HumanTurnRequest:
    """A valid HITL interrupt request; override any field. Defaults = the villager
    day-vote shape the human-seat suites pin."""
    base = dict(
        player_id="p1", role="villager", phase="day_votes", day=1, instruction="",
        valid_targets=["p2", "p3"], can_pass=False, dialogue="", day_summaries="",
        surviving_players=["p1", "p2", "p3"], dead_roster="", alive_roles="", firing_brief="",
        wolf_channel="", previous_strategy="",
    )
    base.update(over)
    return HumanTurnRequest(**base)


def night_runtime(metrics: Metrics | None = None) -> SimpleNamespace:
    """The runtime stub night nodes receive: a context carrying only metrics."""
    return SimpleNamespace(context={"metrics": metrics or Metrics()})


def eval_case_part(case: dict) -> dict:
    """Wrap an eval case as the sidecar part the consolidation loop reads."""
    return {"kind": "agent_action_eval", "output": {"eval_case": case}}


def strategy_point(key, cell="villager/day_vote", **counts) -> dict:
    """A stored strategy_points record with zeroed counters; override any count."""
    v = {"action": key, "follow_count": 0, "positive_count": 0, "negative_count": 0,
         "neutral_count": 0, "retrieved_count": 0, "override_count": 0, "not_relevant_count": 0}
    v.update(counts)
    return {"key": key, "value": v, "namespace": ["strategy_points", *cell.split("/")]}


def day_vote_case(role, pid, votee, key=None, day=2, mem=True) -> dict:
    """A day-vote eval case; `key` attaches a followed strategy (the credit path)."""
    c = {"action_phase": "day_vote", "player_role": role, "player_id": pid, "day": day,
         "memory_enabled": mem, "agent_vote": {"votee": votee}}
    if key:
        c["strategy_index_to_key"] = {"0": key}
        c["strategy_verdicts"] = [{"verdict": "follow", "strategy_index": 0}]
    return c


def short_event_log(*, with_over: bool = True) -> list:
    """A three-event game log (start, a game-master line, game over) for the replay storage
    tests; ``with_over=False`` leaves the game unfinished."""
    from server.schemas import events as ev

    events = [
        ev.GameStarted(seq=1, day=1, seats=["p1", "p2"],
                       cast_role_counts={"wolf": 1, "villager": 1}),
        ev.GmMessage(seq=2, day=2, channel_seq=0, text="dawn"),
    ]
    if with_over:
        events.append(ev.GameOver(seq=3, day=3, winner="wolves"))
    return events


CREDIT_ROLES = {"player_1": "sentinel", "player_2": "chanteuse", "player_3": "trailseer",
                "player_4": "investigator", "player_5": "serial_killer"}
"""The five seats the consolidation (credit) tests grade."""

NO_LYNCH = {"day": 2, "no_vote": True, "voted_player": None, "vote_counts": {}}
"""A day resolution in which nobody was lynched."""


def credit_game_record(tmp, name: str, cases: list, *, roles: dict = CREDIT_ROLES, day_res=None,
                       night_res=None, human_player=None) -> str:
    """Write one game record for the credit pass, and its eval cases beside it, under ``tmp``;
    returns the record's path."""
    import json

    ecp = tmp / f"{name}_cases.jsonl"
    ecp.write_text("\n".join(json.dumps(eval_case_part(c)) for c in cases))
    rec = {"roles": roles, "eval_cases_path": str(ecp), "game_id": f"gid_{name}"}
    if day_res is not None:
        rec["day_resolutions"] = day_res
    if night_res is not None:
        rec["night_resolutions"] = night_res
    if human_player is not None:
        rec["human_player"] = human_player
    gp = tmp / f"{name}.jsonl"
    gp.write_text(json.dumps(rec))
    return str(gp)
