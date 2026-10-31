"""The extraction prompt forbids player ids in observations; code enforces it (2026-10-28). A call whose
observations name a seat is sent again once, and an observation that still names one never reaches the
store."""

from __future__ import annotations

import json

from pydantic import BaseModel

import Agents.schemas.memory as memory_schemas
from Agents.memory.extraction.offline import extracted_games, names_a_player


class _Obs(BaseModel):
    perspective: str
    action_phase: str
    situation: str
    decision_day: int = -1


def test_names_a_player_reads_every_text_field():
    assert names_a_player({"situation": "the quiet sentinel", "approach": "voted player_3 out"})
    assert not names_a_player({"situation": "the quiet sentinel", "players_alive": 7})
    assert not names_a_player({"situation": "a player_role claim"})  # not a seat number
    assert names_a_player(_Obs(perspective="healer", action_phase="day_vote", situation="saved player_10"))


def test_an_observation_naming_a_player_is_left_out_of_the_fold(tmp_path, monkeypatch):
    monkeypatch.setattr(memory_schemas, "cell_observation_schema_for", lambda role, phase: _Obs)
    observations = [{"perspective": "healer", "action_phase": "day_vote", "situation": "the claimed sentinel"},
                    {"perspective": "healer", "action_phase": "day_vote", "situation": "player_4 claimed sentinel"}]
    path = tmp_path / "extracted.jsonl"
    path.write_text(json.dumps({"output": {"extraction_case": {"game_id": "g1", "observations": observations}}}))
    [(game_id, kept)] = extracted_games([str(path)])
    assert game_id == "g1" and [o.situation for o in kept] == ["the claimed sentinel"]
