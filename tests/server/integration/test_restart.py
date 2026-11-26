"""A hosted game that was running when the server stopped is brought back from the database and
plays on to its end.

The test uses the server's real pieces on a real Postgres database in the test container: the
graph runtime (the Postgres checkpoint saver and the compiled game graph), the game repository,
the live game registry, a real `GameSession` started through the solo door, and the real boot
recovery (`recover_registry`). Only the models are replaced: every seat's turn runs on the
scripted model, passed in through the session's graph context, and the day summary, opening
filter and echo check are the `scripted_model` fixture's replacements. The lesson store the
runtime opens is empty, so the game runs with memory off.

What "the server stopped" means here: the old process's games are suspended the way the server's
shutdown suspends them, its runtime and database are closed, and every object it held is dropped;
a new set of objects is then built over the same database. That is a stop between two steps of
the game, at the moment it waits on a human. It is not a kill of the process in the middle of a
write: a test in one process cannot cut a write to Postgres half-way, so what a crash during a
checkpoint or event write leaves behind is not covered here.

The scripted players share one random generator across the engine's worker threads, so the game
played differs from run to run. The test asserts only what holds for any game.
"""

from __future__ import annotations

import asyncio
import gc

from server.database_models.game import COMPLETED
from server.housekeeping.recovery import recover_registry
from server.game.run_config import game_run_config
from server.storage.game_repository import event_log_shortfall
from tests.factories.served_game import (
    GAME_TIMEOUT_S,
    checkpoint_questions,
    delegate_until_over,
    give_models,
    open_server,
    stored_event_seqs,
    wait_for_question,
)

HUMAN_TOKEN = "seat-token-of-the-human"


async def test_a_game_running_when_the_server_stopped_is_recovered_and_plays_to_its_end(
        server_tables_dsn, scripted_model, refuse_real_models):
    """A restart must give the waiting player the same question back and let the game finish
    with an event log that has no gap and no duplicate. Every earlier recovery test built its
    checkpoint by hand and stored no events; this one stops a game the engine itself paused."""
    # Arrange: a server on the test database, and a solo game with one human seat
    first = await open_server(server_tables_dsn)
    running = [first]  # stopped at the end whatever happens, so a failure leaves no game task behind
    try:
        session = await first.registry.start_instant(
            game_run_config(memory=False, human_player=1), api_key="", model="",
            seat_tokens=[HUMAN_TOKEN])
        give_models(session, scripted_model(1))
        session.subscribe(HUMAN_TOKEN)  # the player's page is open, so a solo game does not wait for them
        game_id = session.game_id

        # Act, part one: the game runs until it parks on the human seat's first question
        seat = await wait_for_question(session, first.graph)
        asked_before = session.pending_requests[seat]
        stored_question = await checkpoint_questions(first.graph, session)
        events_before = len(session.log)

        # Act, part two: the server stops, and a new one starts on the same database
        await first.stop()
        running.remove(first)
        del session, first  # nothing of the old process is kept
        gc.collect()
        second = await open_server(server_tables_dsn)
        running.append(second)
        await recover_registry(second.registry, second.repository)
        revived = second.registry.get(game_id)
        assert revived is not None, "recovery did not bring the game back"
        give_models(revived, scripted_model(2))
        revived.subscribe(HUMAN_TOKEN)

        # Assert: the game is back, parked on the same question, with the events it had sent
        assert list(revived.pending_requests) == [seat]
        asked_after = revived.pending_requests[seat]
        assert [asked_after.model_dump()] == stored_question  # the engine's own question, as stored
        for field in ("player_id", "role", "phase", "day", "valid_targets", "can_pass"):
            assert getattr(asked_after, field) == getattr(asked_before, field), field
        assert len(revived.log) == events_before

        # Act, part three: the player hands every turn to its agent, and the game runs to its end
        await delegate_until_over(revived)
        await asyncio.wait_for(revived.wait_finished(), timeout=GAME_TIMEOUT_S)

        # Assert: the game finished, and its stored event log is whole
        assert revived.error is None
        assert revived.game_over
        row = await second.repository.load_game(game_id)
        assert row.status == COMPLETED
        seqs = await stored_event_seqs(second.database, game_id)
        assert seqs == list(range(1, len(revived.log) + 1))  # numbered from 1, no gap, no duplicate
        assert event_log_shortfall(len(revived.log), len(seqs), seqs[-1]) is None
        assert row.n_events == len(revived.log)
    finally:
        for process in running:
            await process.stop()
