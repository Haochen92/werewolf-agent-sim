"""Speaking voices for the AI seats (RunConfig.persona_voices; owner, 2026-10-18): each puppet has
one, drawn from its look, so a seat sounds like the puppet standing at it. The line goes in the seat's
part of every spoken-round prompt (day_discuss.py).

A voice says how a seat sounds, never what it thinks: no voice may lean on suspicion, firmness or a
side, or hint at a role, as no costume may (server/game/cast.py). The persona screen
(evidence/game_play_enhancement/data/persona_line/) found such lines read more like people (25 of 30
blind) and moved the argument no more than sampling noise does.
"""

from __future__ import annotations

import random
import re

VOICES: dict[str, str] = {
    "owl": "Mild and bookish, a little professorial. Tidy words, never rushed.",
    "hare": "Polished and a touch theatrical, like a host introducing the next act.",
    "cat": "Elegant and cool, with an amused, faintly arch edge.",
    # No quoted catchphrase: a quoted "right then" opened most of the badger's lines (persona games, 2026-10-18).
    "badger": "Brisk and polite, like a porter on a busy shift: short and practical.",
    "cyclops": "Sweet and dreamy, a little sentimental, with soft exclamations.",
    "threeEyes": "Easy-going and artsy, with a colourful turn of phrase.",
    "dragon": "Smooth and businesslike, clipped like a banker between appointments.",
    "onion": "Prim and proper, polite to a fault, with quaint, old-fashioned phrasing.",
    # No sea phrases: "kept watch over player_8" turned a healer's protect into a sentinel's verb, and
    # "Captain's log" opened a line (silence calibration games, 2026-10-18).
    "whale": "Steady and unhurried, with a captain's calm.",
    "polarBear": "Hearty and outdoorsy, friendly and plain, like a hiker on the trail.",
    "shade": "Chirpy and quick, with a light, sing-song rhythm.",
    "kitsune": "Graceful and softly spoken, courteous and composed.",
    "mushroom": "Breezy and plucky, a pilot's cheerful chatter.",
    "lionCub": "Soldierly and correct: crisp, formal, by-the-book phrasing, like an officer on parade.",
    "automaton": ("Precise and tidy, like a clerk sorting the post, with a touch of mechanical charm "
                  "and a dry little politeness."),
}
"""One per puppet of the catalogue (server/game/cast.py; a server test keeps the two in step). The
Lion Cub's formality and the Automaton's mechanical touch are theirs alone (owner, 2026-10-18)."""

PERSONA_PARAGRAPH = (
    "\nYour voice at the table: {voice} This is how you sound, not what you think: it never changes "
    "your facts, your claims, how sure you are or what you ask for."
)
"""Fills {persona_paragraph} right after the tone block; it opens with the line break, so an empty
slot leaves the prompt byte for byte as it was."""


def house_puppet(game_id: str, player_id: str) -> str:
    """The puppet a seat gets with no server to deal one (a batch game): the puppets in a
    game-seeded order, dealt by seat number, so no two seats share one and a rerun deals the same."""
    order = list(VOICES)
    random.Random(f"{game_id}:puppets").shuffle(order)
    seat = int(re.search(r"\d+", player_id).group())
    return order[(seat - 1) % len(order)]


def persona_paragraph(payload: dict) -> str:
    """The slot's text for this turn: "" unless the game has voices on and the seat is an AI's. The
    voice is the puppet's at the seat (a served game's cast), else the house draw's; a puppet with
    no voice gets none."""
    if not payload.get("persona_voices") or payload.get("human_player"):
        return ""
    puppet = payload.get("seat_puppet") or house_puppet(str(payload.get("game_id") or ""), payload["player_id"])
    voice = VOICES.get(puppet)
    return PERSONA_PARAGRAPH.format(voice=voice) if voice else ""
