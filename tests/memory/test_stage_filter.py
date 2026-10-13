"""The stage filter (decisions §11): a retrieved lesson learned at another stage of the game is left
out — another alive bucket, a lost partner against a living one, uses left against none — before the
cap, so the cap refills from same-stage lessons. Off unless the run config turns it on."""

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


def test_with_the_filter_on_the_whole_cell_is_searched_and_the_cap_refills_with_same_stage_lessons(monkeypatch):
    from contextlib import contextmanager
    from datetime import datetime

    import Agents.tracing as tracing
    from Agents.memory.retrieval import lookup_cache, pipeline
    from Agents.memory.retrieval.dimension_gating import STAGE_FILTER_TOP_K
    from Agents.schemas.memory import RetrievedStrategyPoint, StoredStrategyPoint

    def lesson(key, score, alive):
        sp = StoredStrategyPoint(observation_count=1, last_observed=datetime(2026, 1, 1), situation=key,
                                 action="do", dimensions={"players_alive": alive})
        return RetrievedStrategyPoint(key=key, strategy_point=sp, matched_situation="s", score=score)

    asked = {}

    def fake_retrieve(store, payload, phase, situations, top_k, *_):
        asked["top_k"] = top_k
        return [], [lesson("late-a", 0.9, 4), lesson("early-a", 0.8, 9), lesson("late-b", 0.7, 3),
                    lesson("early-b", 0.6, 10), lesson("early-c", 0.5, 8), lesson("early-d", 0.4, 9)]

    @contextmanager
    def span(**_):
        yield SimpleNamespace(update=lambda **_: None)

    lookup_cache.clear()
    monkeypatch.setattr(pipeline, "_generate_situations_for_agent", lambda p, a: (["s"], [{"players_alive": 9}]))
    monkeypatch.setattr(pipeline, "_retrieve", fake_retrieve)
    monkeypatch.setattr(tracing.langfuse, "start_as_current_observation", span)
    config = build_runnable_config(RunConfig(stage_filter=True, memory_config={"chanteuse": True},
                                             retrieval_types_config={"observations": False, "strategy_points": True}))
    payload = {"current_day": 2, "current_round": 1, "day_round": "opening", "player_id": "p1",
               "player_role": "chanteuse", "day_channel": [], "strategy_points": []}
    _, meta = pipeline.enrich_payload_with_memory(payload, config, SimpleNamespace(store=object()), "day_discussion")
    assert asked["top_k"] == STAGE_FILTER_TOP_K
    assert [sp["key"] for sp in meta["retrieved_strategy_points"]] == ["early-a", "early-b", "early-c"]
    assert meta["stage_filtered"]["strategy_points"] == 2
