"""A served game keeps the evaluation cases it built.

A batch game writes its evaluation cases to a file. A served game builds the same list in memory;
these tests show that it is saved when the game ends, in a compressed form that reads back
unchanged, and that a failed save never fails the game. The database side (the table, the shelf
life, the export the evaluation code reads) is in tests/server/integration.
"""
from __future__ import annotations

import asyncio
import copy
import json

from server.storage.eval_cases import RECORD_FORMAT, decode_cases, encode_cases
from tests.fixtures.server import FakeGraph
from tests.server.test_durability import RecordingGameRepository


def case_record(name: str, i: int) -> dict:
    """A record shaped like the one the engine appends for each case, with a transcript that
    repeats from case to case as a real game's does."""
    transcript = [f"player_{n % 10 + 1}: line {n} of the day's discussion" for n in range(i + 40)]
    return {"kind": "agent_action_eval", "id": f"{name}-{i}", "name": f"agent_action_eval_{i}",
            "trace_id": f"trace-{name}", "parent_observation_id": None, "metadata": {},
            "input": None, "output": {"eval_case": {"game": name, "transcript": transcript}}}


class CaseBuildingGraph(FakeGraph):
    """Plays the fixture game and adds one case to the game's own list between chunks, the way
    the engine does as each decision is made."""

    def __init__(self, name: str, chunks: list[dict], build_cases: bool = True) -> None:
        super().__init__(chunks)
        self.name = name
        self.build_cases = build_cases

    async def astream(self, payload, **kwargs):
        i = 0
        async for chunk in super().astream(payload, **kwargs):
            if self.build_cases:
                kwargs["context"]["eval_sink"].records.append(case_record(self.name, i))
            i += 1
            yield chunk


class DecodingRepository(RecordingGameRepository):
    """Keeps what a game saved, unpacked, or refuses to save at all."""

    def __init__(self, fail: bool = False) -> None:
        super().__init__()
        self.fail = fail

    async def record_eval_cases(self, game_id, cases, *, n_cases, partial, record_format):
        if self.fail:
            raise ConnectionError("test: database unavailable")
        return await super().record_eval_cases(
            game_id, decode_cases(cases), n_cases=n_cases, partial=partial,
            record_format=record_format)


def test_cases_read_back_unchanged_from_their_compressed_form():
    # Arrange
    records = [case_record("alpha", i) for i in range(30)]

    # Act
    blob = encode_cases(records)

    # Assert
    assert decode_cases(blob) == records
    as_text = "\n".join(json.dumps(r) for r in records)
    assert len(blob) * 5 < len(as_text)  # the transcripts repeat, which is why they are compressed


def test_a_game_with_no_cases_packs_to_an_empty_list():
    assert decode_cases(encode_cases([])) == []


async def test_concurrent_served_games_each_save_only_their_own_cases(quiet_session, fixture_chunks):
    # Arrange: two served games that share one repository
    repository = DecodingRepository()
    sessions = {name: quiet_session(CaseBuildingGraph(name, copy.deepcopy(fixture_chunks)),
                                    repository=repository)
                for name in ("alpha", "beta")}

    # Act: run both games at once
    for session in sessions.values():
        session.start()
    await asyncio.wait_for(asyncio.gather(*(s.wait_finished() for s in sessions.values())), 30)

    # Assert
    for name, session in sessions.items():
        assert session.error is None and session.game_over
        saved, n_cases, partial, record_format = repository.eval_cases[session.game_id]
        assert saved == [case_record(name, i) for i in range(len(fixture_chunks))]
        assert n_cases == len(fixture_chunks)
        assert partial is False  # the game ran in one process from its start
        assert record_format == RECORD_FORMAT


async def test_a_game_resumed_after_a_restart_saves_its_cases_marked_partial(
        quiet_session, fixture_chunks):
    """The cases built before the restart were in the old process's memory, so the saved row
    holds only the rest and has to say so."""
    # Arrange
    repository = DecodingRepository()
    session = quiet_session(CaseBuildingGraph("alpha", fixture_chunks), repository=repository)

    # Act: run the game the way recovery does after a restart
    session.resume_game(waiting_on_humans=False)
    await asyncio.wait_for(session.wait_finished(), 30)

    # Assert
    assert session.error is None and session.game_over
    _, _, partial, _ = repository.eval_cases[session.game_id]
    assert partial is True


async def test_a_game_that_built_no_cases_saves_no_row(quiet_session, fixture_chunks):
    # Arrange
    repository = DecodingRepository()
    session = quiet_session(CaseBuildingGraph("alpha", fixture_chunks, build_cases=False),
                            repository=repository)

    # Act
    session.start()
    await asyncio.wait_for(session.wait_finished(), 30)

    # Assert
    assert session.error is None and session.game_over
    assert repository.eval_cases == {}


async def test_cases_that_cannot_be_saved_never_fail_the_game(quiet_session, fixture_chunks):
    # Arrange: a repository that cannot save cases
    repository = DecodingRepository(fail=True)
    session = quiet_session(CaseBuildingGraph("alpha", fixture_chunks), repository=repository)

    # Act: run the game to its end
    session.start()
    await asyncio.wait_for(session.wait_finished(), 30)

    # Assert
    assert session.error is None and session.game_over
    assert len(repository.completions) == 1 and repository.eval_cases == {}
