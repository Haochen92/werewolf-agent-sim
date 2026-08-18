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
        wolf_channel="", investigator_results="", vigilante_results="", previous_strategy="",
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
