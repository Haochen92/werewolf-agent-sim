"""Polyfactory factories over the wire contract (server/schemas/events.py).

Random-VALID instances for schema-contract fuzzing. The wire rows are pure data — no
cross-field game invariants — which is exactly where random generation is safe; anything
game-semantic (states, votes, eval cases) belongs to the hand-written builders in
tests/factories/builders.py instead.

`durable_event_types()` enumerates the registry by construction (DurableEvent
subclasses), so contract tests cover every row automatically — a newly added event
class is swept in without anyone editing a test.
"""

from __future__ import annotations

from polyfactory import Use
from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.pytest_plugin import register_fixture

from Agents.schemas.human_player import HumanTurnRequest
from server.schemas import events as ev


def durable_event_types() -> list[type[ev.DurableEvent]]:
    return sorted(ev.DurableEvent.__subclasses__(), key=lambda c: c.__name__)


def event_factory(cls: type[ev.DurableEvent]) -> type[ModelFactory]:
    overrides = {}
    if cls is ev.DaySummaryStructured:
        # `data` is the PROVISIONAL untyped dict; unconstrained fuzzing puts non-JSON
        # types in it (Decimal), which fail round-trip by serialization, not by contract.
        # Real summarizer data is JSON-born, so fuzz JSON-native content only.
        overrides["data"] = Use(lambda: {"accusations": ["p1 -> p2"], "role_claims": {}})
    return ModelFactory.create_factory(cls, **overrides)


@register_fixture
class HumanTurnRequestFactory(ModelFactory[HumanTurnRequest]):
    """Fuzzed-but-valid interrupt payloads (fixture name: human_turn_request_factory)."""
