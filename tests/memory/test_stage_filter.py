"""The stage filter (decisions §11): a retrieved lesson learned at another stage of the game is left
out — another alive bucket, a lost partner against a living one, uses left against none — after the
cap, with no refill. Off unless the run config turns it on."""

from types import SimpleNamespace

from Agents.config.langgraph import build_runnable_config
from Agents.config.run import RunConfig
from Agents.memory.retrieval.dimension_gating import drop_other_stages, stage_mismatch
from Agents.memory.retrieval.plan_gating import retrieval_plan


def test_each_stage_fact_is_compared_only_where_both_sides_have_it():
    seat = {"players_alive": 9, "ally_revealed": False, "uses_left": 2}
    assert stage_mismatch(seat, {"players_alive": 8, "ally_revealed": False, "uses_left": 1}) == []
    assert stage_mismatch(seat, {"players_alive": 6}) == ["alive"]
    assert stage_mismatch(seat, {"ally_revealed": True}) == ["partner"]
    assert stage_mismatch(seat, {"uses_left": 0}) == ["uses"]
    assert stage_mismatch({"bullets_left": 0}, {"bullets_left": 2}) == ["uses"]
    assert stage_mismatch(seat, {}) == []


def test_lessons_from_another_stage_are_dropped_per_matched_situation():
    def item(situation, dims):
        return SimpleNamespace(matched_situation=situation, strategy_point=SimpleNamespace(dimensions=dims))

    early, late = item("s1", {"players_alive": 9}), item("s1", {"players_alive": 4})
    other = item("s2", {"players_alive": 4})
    kept = drop_other_stages([early, late, other], {"s1": {"players_alive": 10}, "s2": {"players_alive": 3}},
                             lambda it: it.strategy_point.dimensions)
    assert kept == [early, other]


def test_the_filter_is_off_unless_the_run_config_turns_it_on():
    payload = {"player_role": "chanteuse", "current_day": 2}
    off = retrieval_plan(build_runnable_config(RunConfig()), payload, object(), "day_discussion")
    on = retrieval_plan(build_runnable_config(RunConfig(stage_filter=True)), payload, object(), "day_discussion")
    assert off.stage_filter is False and on.stage_filter is True
