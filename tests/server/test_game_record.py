"""What a served game writes down about how it was run.

A served game's events show its moves. These tests cover the rest of its record: which code and
models ran it and under which trace (one entry per run of its task), which turns were decided by
the rescue model or by an engine default, how many engine steps were replayed from the turn
cache, and the game id on the log lines written on its behalf.
"""
from __future__ import annotations

import asyncio
import logging

from Agents.llm_factory import GameModels
from Agents.llm_factory.outcomes import RANDOM_DEFAULT, RESCUE
from Agents.observability.log_context import GAME_ID, GameIdFilter
from server.game import game_session as rt
from tests.fixtures.server import FakeGraph
from tests.server.test_durability import RecordingGameRepository, _updates


# ---- which code ran the game, and under which trace -----------------------------------------


def test_a_served_games_fingerprint_names_its_own_model_its_rescue_and_the_images_commit(
        monkeypatch):
    # Arrange: the server image has no git repository; its build recorded the commit instead
    monkeypatch.setattr(rt, "runtime_fingerprint", lambda game_model=None: {
        "git_commit": "unknown", "game_model": game_model or "the-environments-model"})
    monkeypatch.setenv("LANGFUSE_RELEASE", "087812dd")
    models = GameModels(model="deepseek/deepseek-v4-pro",
                        rescue_model="anthropic/claude-haiku-5-5")

    # Act
    fingerprint = rt.served_fingerprint(models)

    # Assert
    assert fingerprint["game_model"] == "deepseek/deepseek-v4-pro"  # not the environment's
    assert fingerprint["rescue_model"] == "anthropic/claude-haiku-5-5"
    assert fingerprint["git_commit"] == "087812dd"


async def test_each_run_of_a_games_task_is_recorded_with_its_fingerprint(quiet_session):
    # Arrange
    repository = RecordingGameRepository()
    session = quiet_session(FakeGraph([]), repository=repository)

    # Round 1: the game's first run
    session.start()
    await asyncio.wait_for(session.wait_finished(), timeout=10)
    (first,) = repository.runs
    assert first["recovered"] is False
    assert first["fingerprint"] == session.fingerprint
    assert first["fingerprint"]["prompt_bundle_hash"]  # the real fingerprint, not an empty dict
    # The same fingerprint rides on every span of the trace, as in a command-line game.
    assert session.config["metadata"]["runtime_fingerprint"] == session.fingerprint

    # Round 2: the game is run again the way recovery does after a restart
    session._graph = FakeGraph([])
    session.resume_game(waiting_on_humans=False)
    await asyncio.wait_for(session._task, timeout=10)
    assert [run["recovered"] for run in repository.runs] == [False, True]


# ---- turns the game's own model did not decide ----------------------------------------------


async def test_rescued_and_defaulted_turns_are_saved_on_the_games_row(
        quiet_session, fixture_chunks):
    # Arrange: a game during which the engine notes one rescued turn and one random vote
    class NotingGraph(FakeGraph):
        async def astream(self, payload, **kwargs):
            outcomes = kwargs["context"]["models"].outcomes
            outcomes.note(RESCUE, player="player_3", day=1, turn="day_channel")
            outcomes.note(RANDOM_DEFAULT, player="player_5", day=1, turn="day_votes")
            async for chunk in super().astream(payload, **kwargs):
                yield chunk

    repository = RecordingGameRepository()
    session = quiet_session(NotingGraph(fixture_chunks), repository=repository)

    # Act
    session.start()
    await asyncio.wait_for(session.wait_finished(), timeout=30)

    # Assert: the last save of the record holds both turns
    saved = [u["turn_outcomes"] for u in repository.updates if "turn_outcomes" in u][-1]
    assert saved["counts"]["rescue"] == 1 and saved["counts"]["random_default"] == 1
    assert {"player": "player_5", "day": 1, "turn": "day_votes",
            "path": "random_default"} in saved["turns"]
    assert saved["cached_steps"] == 0


def test_the_outcome_record_survives_a_change_of_the_games_models_object(quiet_session):
    """A game's models object is replaced when a player supplies a key and when the game ends.
    The record of rescued turns belongs to the game, so it must not go with the old object."""
    # Arrange
    session = quiet_session(FakeGraph([]))
    session._models.outcomes.note(RESCUE, player="player_2", day=1, turn="day_votes")

    # Act
    session._use_models(GameModels(model="anthropic/claude-haiku-5-5"))
    session._models.outcomes.note(RESCUE, player="player_4", day=1, turn="day_votes")

    # Assert
    assert session.turn_outcomes.count("rescue") == 2


def test_a_step_replayed_from_the_turn_cache_is_counted_and_logged(quiet_session, caplog):
    # Arrange
    session = quiet_session(FakeGraph([]))
    ballot = {"day_votes": [{"voter": "player_4", "votee": "player_6"}]}

    # Act: the engine re-emits a cached step twice
    with caplog.at_level("INFO"):
        session._on_chunk(_updates("vote", ballot, "DAY_PHASE", cached=True))
        session._on_chunk(_updates("vote", ballot, "DAY_PHASE", cached=True))

    # Assert
    assert session.cached_steps == 2
    lines = [r.getMessage() for r in caplog.records if "turn cache" in r.getMessage()]
    assert len(lines) == 2 and session.game_id in lines[0] and "vote" in lines[0]


def test_a_resumed_game_carries_on_its_saved_counts(quiet_session):
    # Arrange: what the game's row held before the restart
    saved = {"counts": {"rescue": 3, "failed_pass": 0, "random_default": 1, "no_action_default": 0},
             "turns": [], "cached_steps": 4}
    session = quiet_session(FakeGraph([]))

    # Act
    session.reload_history([], [], turn_outcomes=saved)

    # Assert
    assert session.turn_outcomes.count("rescue") == 3
    assert session.cached_steps == 4
    assert session._models.outcomes is session.turn_outcomes


# ---- the game id on log lines ---------------------------------------------------------------


def test_the_log_filter_stamps_a_line_with_its_game_or_a_dash():
    # Arrange
    stamp = GameIdFilter()
    record = logging.LogRecord("engine", logging.WARNING, __file__, 1, "rescued", None, None)

    # Round 1: outside any game
    assert stamp.filter(record) is True and record.game_id == "-"

    # Round 2: inside a game's context
    token = GAME_ID.set("game-123")
    try:
        assert stamp.filter(record) is True and record.game_id == "game-123"
    finally:
        GAME_ID.reset(token)


async def test_lines_logged_by_the_engines_worker_threads_carry_the_games_id(quiet_session):
    """The engine's steps run on worker threads, and its log lines name a seat, not a game.
    Two games run at once here; each worker thread must see its own game's id."""
    # Arrange: a graph whose step runs on a worker thread and reads the id a log line would get
    class ThreadedGraph(FakeGraph):
        def __init__(self):
            super().__init__([])
            self.seen: list[str] = []

        async def astream(self, payload, **kwargs):
            self.seen.append(await asyncio.to_thread(GAME_ID.get))
            async for chunk in super().astream(payload, **kwargs):
                yield chunk

    graphs = [ThreadedGraph(), ThreadedGraph()]
    sessions = [quiet_session(graph) for graph in graphs]

    # Act
    for session in sessions:
        session.start()
    await asyncio.wait_for(asyncio.gather(*(s.wait_finished() for s in sessions)), timeout=10)

    # Assert
    assert [graph.seen for graph in graphs] == [[s.game_id] for s in sessions]
    assert GAME_ID.get() == "-"  # the test's own context was never given a game
