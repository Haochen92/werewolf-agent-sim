"""A seat's memory lookup is reused within a day's discussion and within a night (v8 plan D4, owner's
ruling 2026-10-12): the situation call and the search run once, until a new role claim that day; a
vote always looks up afresh; a payload with no game id is never cached."""

from contextlib import contextmanager
from types import SimpleNamespace

import pytest

import Agents.tracing as tracing
from Agents.memory.retrieval import lookup_cache
from Agents.memory.retrieval import pipeline


@pytest.fixture
def calls(monkeypatch):
    lookup_cache.clear()
    made = []

    def fake_situations(payload, action_phase):
        made.append((payload["player_id"], payload["current_day"], action_phase))
        return [f"situation {len(made)}"], []

    @contextmanager
    def span(**_):
        yield SimpleNamespace(update=lambda **_: None)

    monkeypatch.setattr(pipeline, "_generate_situations_for_agent", fake_situations)
    monkeypatch.setattr(pipeline, "_retrieve", lambda *a, **k: ([], []))
    monkeypatch.setattr(tracing.langfuse, "start_as_current_observation", span)
    yield made
    lookup_cache.clear()


def _payload(day=2, channel=(), player="p1", role="chanteuse"):
    return {"current_day": day, "current_round": 1, "player_id": player, "player_role": role,
            "day_channel": list(channel), "strategy_points": []}


def _line(player, claim="none", day=2):
    return {"day": day, "player": player, "claim": claim, "message": "..."}


def _enrich(payload, phase, game_id="g1"):
    config = {"configurable": {"game_id": game_id}}
    return pipeline.enrich_payload_with_memory(payload, config, SimpleNamespace(store=object()), phase)


def test_a_days_discussion_reuses_its_first_lookup(calls):
    _, first = _enrich(_payload(), "day_discussion")
    _, second = _enrich(_payload(channel=[_line("p4")]), "day_discussion")
    assert len(calls) == 1
    assert first["lookup_reused"] is False and second["lookup_reused"] is True
    assert second["situations"] == first["situations"] and second["lookup_round"] == 1


def test_a_new_claim_refreshes_it_and_a_repeated_claim_does_not(calls):
    _enrich(_payload(), "day_discussion")
    claimed = [_line("p4", "investigator")]
    _enrich(_payload(channel=claimed), "day_discussion")
    _enrich(_payload(channel=claimed + [_line("p4", "investigator")]), "day_discussion")
    assert len(calls) == 2


def test_a_vote_always_looks_up_afresh(calls):
    _enrich(_payload(), "day_vote")
    _enrich(_payload(), "day_vote")
    assert len(calls) == 2


def test_a_night_shares_one_lookup_and_the_next_night_does_not(calls):
    for _ in range(3):  # the pack's chat rounds, the kill, the ability
        _enrich(_payload(day=2), "night_action")
    _enrich(_payload(day=3), "night_action")
    assert len(calls) == 2


def test_seats_and_games_do_not_share_a_lookup(calls):
    _enrich(_payload(player="p1"), "day_discussion")
    _enrich(_payload(player="p6"), "day_discussion")
    _enrich(_payload(player="p1"), "day_discussion", game_id="g2")
    assert len(calls) == 3


def test_no_game_id_means_no_reuse(calls):
    _enrich(_payload(), "day_discussion", game_id="")
    _enrich(_payload(), "day_discussion", game_id="")
    assert len(calls) == 2
