"""Guards for the live tell-book channel (2026-07-13): env gating (no WW_TELL_BOOK => empty block
everywhere = the baseline arm), the per-turn roles-alive filter, and the prompt slot actually
rendering through build_agent_prompt_input + a real day-vote template."""

from __future__ import annotations

import json

from Agents.memory.tell_book import _load, tell_book_block
from Agents.prompts.day_vote import day_vote_template
from Agents.prompts.prompt_inputs import build_agent_prompt_input
from Agents.schemas.roles import lineup

BOOK = [
    {"tell_id": "vote_9", "channel": "vote", "text": "votes a player who drew no discussion",
     "subject_role": "wolf", "subject_count": 12, "n": 16, "subject_lift": 0.31},
    {"tell_id": "disc_4", "channel": "discussion", "text": "goes silent when directly accused",
     "subject_role": "serial_killer", "subject_count": 6, "n": 9, "subject_lift": 0.22},
]
# The v1 book was mined from nine-seat games, so the filter is pinned on a nine-seat census; the
# prompt tests run a ten-seat payload, where the serial-killer tell still applies.
CENSUS = {"villager": 3, "wolf": 2, "serial_killer": 1, "healer": 1, "investigator": 1, "vigilante": 1}
LINEUP = lineup("serial_killer", "speculator")
TEN_SEAT_CENSUS = {role: 1 for role in LINEUP}


def _book_env(tmp_path, monkeypatch):
    p = tmp_path / "book.json"
    p.write_text(json.dumps(BOOK))
    monkeypatch.setenv("WW_TELL_BOOK", str(p))
    _load.cache_clear()
    return p


def test_no_env_means_empty_block(monkeypatch):
    monkeypatch.delenv("WW_TELL_BOOK", raising=False)
    assert tell_book_block([], CENSUS) == ""


def test_block_renders_and_filters_revealed_roles(tmp_path, monkeypatch):
    _book_env(tmp_path, monkeypatch)
    block = tell_book_block([], CENSUS)
    assert "drew no discussion" in block and "silent when directly accused" in block
    assert "12/16" in block                       # calibration attached
    # both wolves revealed dead -> the wolf-subject tell leaves; the SK tell stays
    dead = [{"player": "p1", "role": "wolf"}, {"player": "p2", "role": "wolf"}]
    block2 = tell_book_block(dead, CENSUS)
    assert "drew no discussion" not in block2 and "silent when directly accused" in block2
    # no census on the payload (legacy replay) -> render nothing rather than an unfiltered book
    assert tell_book_block([], {}) == ""


def test_book_reaches_a_real_prompt(tmp_path, monkeypatch):
    _book_env(tmp_path, monkeypatch)

    pi = build_agent_prompt_input({
        "player_id": "p1", "player_role": "healer", "current_day": 2, "lineup": LINEUP,
        "surviving_players": ["p1", "p2"], "cast_role_counts": TEN_SEAT_CENSUS, "dead_roster": [],
    })
    assert "silent when directly accused" in pi["tell_book"]
    rendered = day_vote_template("healer").format_messages(**pi)
    human = rendered[-1].content
    # the book sits ABOVE the reads instruction (evidence before belief)
    assert human.index("silent when directly accused") < human.index("record your current read")


def test_memory_off_payloads_render_without_book(monkeypatch):
    monkeypatch.delenv("WW_TELL_BOOK", raising=False)

    pi = build_agent_prompt_input({"player_id": "p1", "player_role": "healer", "lineup": LINEUP,
                                   "surviving_players": ["p1", "p2"]})
    assert pi["tell_book"] == ""
    human = day_vote_template("healer").format_messages(**pi)[-1].content
    assert human.startswith("\nBefore your decision")   # the empty slot leaves the prompt unchanged
