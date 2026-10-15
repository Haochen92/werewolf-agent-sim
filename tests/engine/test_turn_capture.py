"""The leak-check capture belongs to the game a turn runs in (Agents/turn/eval.py): the server runs
several games in one process, so each sets its own TurnCapture, and one-game callers keep the globals."""
from __future__ import annotations

import asyncio

from pydantic import BaseModel

from Agents.schemas.output import PlayerRead
from Agents.turn import prompt_log, reads_log
from Agents.turn.eval import TURN_CAPTURE, TurnCapture, log_prompt, record_reads


class _WithReads(BaseModel):
    reads: list[PlayerRead] = []


def _turn(game: str, i: int) -> None:
    payload = {"player_id": f"player_{i % 5 + 1}", "player_role": "healer", "current_day": 1,
               "current_round": 1, "surviving_players": []}
    log_prompt(payload, "day_channel", {"dialogue": f"{game} turn {i}"})
    read = PlayerRead(player="player_9", why=f"{game} read {i}", suspected_role="healer",
                      confidence="low")
    record_reads([read], payload, "day_channel", _WithReads)


async def _game(capture: TurnCapture, game: str, turns: int) -> None:
    # As the server's GameSession does: set inside the game's task; the engine's worker threads
    # (asyncio.to_thread here, LangGraph's executor in a real game) run in a copy of that context.
    TURN_CAPTURE.set(capture)
    for i in range(turns):
        await asyncio.to_thread(_turn, game, i)


async def test_two_games_running_at_once_never_write_into_each_others_capture():
    before = (len(prompt_log), len(reads_log))
    a, b = TurnCapture(), TurnCapture()
    await asyncio.gather(_game(a, "alpha", 60), _game(b, "beta", 45))

    assert [e["prompt_input"]["dialogue"] for e in a.prompts] == [f"alpha turn {i}" for i in range(60)]
    assert [e["prompt_input"]["dialogue"] for e in b.prompts] == [f"beta turn {i}" for i in range(45)]
    assert [r["reads"][0]["why"] for r in a.reads] == [f"alpha read {i}" for i in range(60)]
    assert [r["reads"][0]["why"] for r in b.reads] == [f"beta read {i}" for i in range(45)]
    assert (len(prompt_log), len(reads_log)) == before  # nothing fell through to the globals


def test_without_a_game_capture_turns_land_in_the_process_globals():
    before = (len(prompt_log), len(reads_log))
    try:
        _turn("solo", 0)
        assert prompt_log[-1]["prompt_input"] == {"dialogue": "solo turn 0"}
        assert prompt_log[-1]["player_id"] == "player_1" and prompt_log[-1]["output_key"] == "day_channel"
        assert reads_log[-1]["reads"][0]["why"] == "solo read 0"
    finally:
        del prompt_log[before[0]:], reads_log[before[1]:]
