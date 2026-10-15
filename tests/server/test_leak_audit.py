"""The leak audit for served games: each game saves its own prompts when it ends (GameSession),
the capture survives its compressed form, and the audit runs the batch runner's checks over it
(server/housekeeping/leak_audit.py)."""
from __future__ import annotations

import asyncio
import copy
from datetime import datetime, timezone
from types import SimpleNamespace

from Agents.prompts.prompt_inputs import build_agent_prompt_input
from Agents.schemas.game_events import DeathRecord
from Agents.turn import prompt_log
from Agents.turn.eval import TURN_CAPTURE, TurnCapture, log_prompt
from server.housekeeping.leak_audit import audit_capture, run_audit
from server.schemas.leak_audit import GameCapture
from server.storage.prompt_captures import (
    CaptureListing,
    build_capture,
    decode_capture,
    encode_capture,
)
from tests.engine.test_round_payload_leaks import SEATS, day_state, round_payloads
from tests.fixtures.server import FakeGraph
from tests.server.test_durability import RecordingGameRepository


def fixture_game(**state_over) -> GameCapture:
    """A saved ten-seat day: the opening round's prompts, built by the real payload builders and
    recorded by the real capture, with the state they were built from."""
    turns = TurnCapture()
    token = TURN_CAPTURE.set(turns)
    try:
        for payload in round_payloads("opening", SEATS):
            log_prompt(payload, "day_channel", build_agent_prompt_input(payload))
    finally:
        TURN_CAPTURE.reset(token)
    return build_capture(turns, day_state(**state_over), partial=False)


# ---- the capture's stored form ----------------------------------------------------------------


def test_a_capture_round_trips_through_its_compressed_form():
    capture = fixture_game()
    blob = encode_capture(capture)

    assert decode_capture(blob) == capture
    assert len(blob) * 5 < len(capture.model_dump_json())  # the prompts repeat; gzip earns its keep
    assert capture.final_state["wolf_channel"][0]["message"] == "take player_2 tonight"
    assert capture.prompt_log[0]["prompt_input"]["current_day"] == 2


# ---- the checks over a saved game ---------------------------------------------------------------


def test_the_audit_finds_the_saved_game_clean():
    assert audit_capture(decode_capture(encode_capture(fixture_game()))) == []


def test_the_audit_flags_a_planted_leak():
    capture = decode_capture(encode_capture(fixture_game()))
    villager = next(e for e in capture.prompt_log if e["player_id"] == "player_1")  # the sentinel
    villager["prompt_input"]["wolf_channel"] = "[Day 1] player_4: take player_2 tonight"

    leaks = audit_capture(capture)

    assert len(leaks) == 1 and "player_1 (sentinel)" in leaks[0]


def test_the_audit_reads_the_dead_roster_from_the_saved_state():
    # player_6 is recorded dead on night 1 yet was prompted on day 2.
    dead = [DeathRecord(player="player_6", role="serial_killer", day=1, phase="night")]
    leaks = audit_capture(decode_capture(encode_capture(fixture_game(dead_roster=dead))))

    assert leaks and all("dead player player_6" in leak for leak in leaks)


# ---- the served game writes its own capture --------------------------------------------------------


class CapturingRepository(RecordingGameRepository):
    def __init__(self, fail: bool = False) -> None:
        super().__init__()
        self.fail = fail

    async def record_capture(self, game_id, capture, *, n_prompts, partial):
        if self.fail:
            raise ConnectionError("test: database unavailable")
        return await super().record_capture(
            game_id, decode_capture(capture), n_prompts=n_prompts, partial=partial)


class PromptingGraph(FakeGraph):
    """Plays the fixture game, sending its agents a prompt between chunks the way the engine
    does: from a worker thread that runs in a copy of the game task's context."""

    def __init__(self, name: str, chunks: list[dict]) -> None:
        super().__init__(chunks)
        self.name = name

    async def astream(self, payload, **kwargs):
        i = 0
        async for chunk in super().astream(payload, **kwargs):
            await asyncio.to_thread(
                log_prompt, {"player_id": f"player_{i % 10 + 1}", "player_role": "healer",
                             "current_day": 1}, "day_channel", {"dialogue": f"{self.name} {i}"})
            i += 1
            yield chunk

    async def aget_state(self, config):
        return SimpleNamespace(values=day_state())


async def test_concurrent_served_games_each_save_only_their_own_prompts(quiet_session, fixture_chunks):
    before = len(prompt_log)
    repository = CapturingRepository()
    sessions = {name: quiet_session(PromptingGraph(name, copy.deepcopy(fixture_chunks)),
                                    repository=repository)
                for name in ("alpha", "beta")}
    for session in sessions.values():
        session.start()
    await asyncio.wait_for(asyncio.gather(*(s.wait_finished() for s in sessions.values())), 30)

    for name, session in sessions.items():
        assert session.error is None and session.game_over
        saved, n_prompts, partial = repository.captures[session.game_id]
        dialogue = [e["prompt_input"]["dialogue"] for e in saved.prompt_log]
        assert dialogue == [f"{name} {i}" for i in range(len(fixture_chunks))]
        assert n_prompts == len(fixture_chunks) and partial is False
        assert saved.final_state["roles"] == day_state()["roles"]
    assert len(prompt_log) == before  # the process-wide log is untouched by served games


async def test_a_capture_that_cannot_be_saved_never_fails_the_game(quiet_session, fixture_chunks):
    repository = CapturingRepository(fail=True)
    session = quiet_session(PromptingGraph("alpha", fixture_chunks), repository=repository)
    session.start()
    await asyncio.wait_for(session.wait_finished(), 30)

    assert session.error is None and session.game_over
    assert len(repository.completions) == 1 and repository.captures == {}


# ---- the audit command -------------------------------------------------------------------------


class FakeCaptureStore:
    def __init__(self, games: dict[str, GameCapture]) -> None:
        self.blobs = {game_id: encode_capture(c) for game_id, c in games.items()}
        self.verdicts: dict[str, list[str]] = {}

    async def list_captures(self, *, since=None, game_ids=()):
        when = datetime(2026, 10, 14, 4, 15, tzinfo=timezone.utc)
        return [CaptureListing(game_id, when, 7, False) for game_id in self.blobs
                if not game_ids or game_id in game_ids]

    async def load_capture(self, game_id):
        return decode_capture(self.blobs[game_id])

    async def record_verdict(self, game_id, leaks):
        self.verdicts[game_id] = leaks


async def test_the_audit_prints_a_line_per_game_records_verdicts_and_fails_on_a_leak(capsys):
    leaky = fixture_game()
    leaky.prompt_log[0]["prompt_input"]["wolf_channel"] = "[Day 1] player_4: take player_2 tonight"
    store = FakeCaptureStore({"g-clean": fixture_game(), "g-leaky": leaky})

    assert await run_audit(store) == 1
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 3  # one per game, then the summary
    assert "g-clean  clean" in lines[0] and "g-leaky  LEAK" in lines[1]
    assert store.verdicts["g-clean"] == [] and len(store.verdicts["g-leaky"]) == 1

    clean_only = FakeCaptureStore({"g-clean": fixture_game()})
    assert await run_audit(clean_only, record=False) == 0
    assert clean_only.verdicts == {}
