"""Speaking voices (RunConfig.persona_voices; owner, 2026-10-18): off, the discuss prompt is byte for
byte the golden (test_draft_preview); on, each AI seat's prompt carries the voice of the puppet at its
seat right after the tone block, and a human seat's never does."""

from __future__ import annotations

from types import SimpleNamespace

from Agents.nodes.day.actors import discuss, preview_discuss
from Agents.prompts.voices import PERSONA_PARAGRAPH, VOICES, house_puppet, persona_paragraph
from tests.factories.scripted_model import FakeModels
from tests.fixtures.day_discuss_prompt_golden import ROLES, capturing_llm, runtime, speaker_payload

TONE_END = "Make one main point, with\nthe evidence needed to understand it."
ON = {"game_id": "g", "persona_voices": True}


def _discuss_prompt(role: str, configurable: dict, seat_puppets: dict | None = None) -> str:
    sent: list = []
    run = runtime(FakeModels(seat=capturing_llm(sent)))
    if seat_puppets is not None:
        run = SimpleNamespace(context={**run.context, "seat_puppets": seat_puppets}, store=run.store)
    discuss(speaker_payload(role), {"configurable": configurable}, run)
    return sent[0][1][1]


def _voice_line(puppet: str) -> str:
    return PERSONA_PARAGRAPH.format(voice=VOICES[puppet])


def test_a_batch_game_deals_every_seat_its_own_puppet_and_a_rerun_the_same():
    # Arrange
    seats = [f"player_{n}" for n in range(1, 11)]

    # Act
    puppets = [house_puppet("game-a", seat) for seat in seats]

    # Assert
    assert len(set(puppets)) == 10 and set(puppets) <= set(VOICES)
    assert puppets == [house_puppet("game-a", seat) for seat in seats]
    assert puppets != [house_puppet("game-b", seat) for seat in seats]


def test_no_voice_when_off_for_a_human_seat_or_for_a_puppet_without_one():
    # Arrange
    seat = {"player_id": "player_3", "game_id": "g"}

    # Act and assert
    assert persona_paragraph(seat) == ""
    assert persona_paragraph({**seat, "persona_voices": True, "human_player": True}) == ""
    assert persona_paragraph({**seat, "persona_voices": True, "seat_puppet": "unicorn"}) == ""
    assert persona_paragraph({**seat, "persona_voices": True, "seat_puppet": "owl"}) == _voice_line("owl")
    assert persona_paragraph({**seat, "persona_voices": True}) == _voice_line(house_puppet("g", "player_3"))


def test_the_voice_follows_the_tone_block_only_when_the_game_has_voices():
    # Arrange
    role = ROLES[0]

    # Act: the discussion prompt without voices and with them
    off = _discuss_prompt(role, {"game_id": "g"})
    on = _discuss_prompt(role, ON)

    # Assert
    puppet = house_puppet("g", speaker_payload(role)["player_id"])
    assert "Your voice at the table" not in off
    assert f"{TONE_END}\nYour voice at the table: {VOICES[puppet]} This is how you sound" in on
    assert on.replace(_voice_line(puppet), "") == off


def test_a_served_seat_speaks_in_the_voice_of_the_puppet_the_server_dealt_it():
    # Arrange: a seat the server dealt a puppet other than the house one
    role = ROLES[0]
    seat = speaker_payload(role)["player_id"]
    dealt = next(p for p in VOICES if p != house_puppet("g", seat))

    # Act
    prompt = _discuss_prompt(role, ON, seat_puppets={seat: dealt})

    # Assert
    assert _voice_line(dealt) in prompt


def test_a_human_seats_draft_gets_no_voice():
    # Arrange
    sent: list = []
    models = FakeModels(seat=capturing_llm(sent))

    # Act: preview the draft for a human seat
    preview_discuss({**speaker_payload(ROLES[0]), "human_player": True}, {"configurable": ON}, runtime(),
                    models=models)

    # Assert
    assert "Your voice at the table" not in sent[0][1][1]
