"""Wire-contract fuzz over the WHOLE event registry (polyfactory random-valid instances).

Enumerated from DurableEvent's subclasses, so a newly added event class is swept in
automatically: it must carry a registered tier, survive a JSON round-trip (the wire is
the serialization format — design notes 5b), and produce a well-formed SSE frame whose
id line is exactly its seq. Failures land here at author time, not in a viewer's stream.
"""
from __future__ import annotations

import pytest

from server.routes.games import _frame
from server.schemas import events as ev
from tests.factories.events import durable_event_types, event_factory


@pytest.mark.parametrize("cls", durable_event_types(), ids=lambda c: c.__name__)
def test_every_durable_event_is_tiered_round_trippable_and_framable(cls):
    # Arrange: a random valid instance of the event class
    event = event_factory(cls).build()

    # Round 1: the tier and the JSON round-trip
    assert ev.EVENT_TIERS[event.type] in set(ev.Tier)  # tier registered, valid
    assert cls.model_validate_json(event.model_dump_json()) == event  # wire round-trip

    # Round 2: the SSE frame
    frame = _frame("game", event)
    assert frame.startswith(f"id: {event.seq}\n")  # durable => id line advances the cursor
    assert "event: game\n" in frame and frame.endswith("\n\n")


def test_ephemeral_frames_carry_no_id_line(human_turn_request_factory):
    # Round 1: a PhaseProgress frame
    # PhaseProgress has no seq — its frame must not advance Last-Event-ID (ruled 2026-08-18).
    snapshot = ev.PhaseProgress(day=1, stage="night", done=1, total=4)
    assert _frame("pacing", snapshot).startswith("event: pacing\n")

    # Round 2: a human-turn request
    # And the registered polyfactory fixture builds valid interrupt payloads wholesale.
    request = human_turn_request_factory.build()
    assert request.player_id and request.phase
