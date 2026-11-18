"""A scripted model: it answers every model call of a game with a valid object, without a network.

What it replaces. In a game, each seat's turn asks a chat model for an object of one output
schema (a discussion line, a vote, a night target). The tests that play a whole game replace
that model with `ScriptedModel`, so a game runs offline, costs nothing, and plays the same way
on every run with the same seed. `tests/fixtures/model.py` builds it, as `ScriptedModels`, which
the test passes to the game in the graph context. `FakeModels` hands over one fake per model slot
for a test of a single function.

What it returns for each field of the schema it is asked for:

- a `Literal` field (a target, a vote, a role): one of its values, drawn from a seeded
  `random.Random`, so a target is always one the rules allow. A seat named in `spare` is never
  drawn while the field offers any other value;
- a `bool`: False; an `int`: 1;
- a `str`: "a line" for `message`, "none" for `bet_role`, "x" for any other;
- a `list`: empty, except `reads`, which gets one read filled the same way;
- any other type: None.

A schema with a `pass_turn` field passes its turn six times in ten (the message is then empty).
The draws are made in field order from one generator, so the same seed and the same order of
calls give the same answers.

What a test that uses it cannot show: what a real model says to a prompt; how often a real
model's answer fails validation; how long a turn takes. Those need a measured run with a real
model (see `docs/testing.md`, section 1).
"""

from __future__ import annotations

import random
import typing

from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel

from Agents.llm_factory import GameModels


def fill(schema: type[BaseModel], rng: random.Random, spare: frozenset[str] = frozenset()) -> BaseModel:
    """Any schema, filled: a Literal gets one of its values, so a target is always legal. A
    spared seat is never chosen while the Literal offers anything else."""
    values = {}
    for name, field in schema.model_fields.items():
        ann, origin = field.annotation, typing.get_origin(field.annotation)
        if origin is typing.Literal:
            options = typing.get_args(ann)
            values[name] = rng.choice([v for v in options if v not in spare] or options)
        elif ann is bool:
            values[name] = False
        elif ann is str:
            values[name] = "a line" if name == "message" else ("none" if name == "bet_role" else "x")
        elif ann is int:
            values[name] = 1
        elif origin is list or ann is list:
            item = typing.get_args(ann)[0] if typing.get_args(ann) else None
            # One read, built from the lineup's own read class, so the effects must accept it.
            values[name] = [fill(item, rng, spare).model_dump()] if name == "reads" and item is not None else []
        else:
            values[name] = None
    if "pass_turn" in values and rng.random() < 0.6:
        values["pass_turn"], values["message"] = True, ""
    return schema.model_validate(values)


class ScriptedModel:
    """Stands in for a chat model: `with_structured_output(schema)` returns a runnable that
    answers every prompt with `fill(schema, ...)`. All the seats of a game share one generator."""

    model = "fake"

    def __init__(self, rng: random.Random, spare: frozenset[str] = frozenset()):
        self.rng, self.spare = rng, spare

    def with_structured_output(self, schema, **kwargs):
        return RunnableLambda(lambda prompt: fill(schema, self.rng, self.spare))


class ScriptedModels(GameModels):
    """The models of a scripted game, for the graph context's ``models``: every seat's turn gets
    a `ScriptedModel` on the one shared generator, and there is no rescue model. The other
    slots are not used by a scripted game: the fixture replaces the day summary, the opening
    filter and the echo check (`tests/fixtures/model.py`)."""

    def __init__(self, rng: random.Random, spare: frozenset[str] = frozenset()):
        self.rng, self.spare = rng, spare

    def seat(self):
        return ScriptedModel(self.rng, self.spare)

    def seat_rescue(self):
        return None


class FakeModels(GameModels):
    """A `GameModels` that returns the fake given for each slot, and None for a slot not
    given, so a test hands the code under test exactly the models it needs and no real one."""

    def __init__(self, *, seat=None, seat_rescue=None, summary=None, summary_rescue=None,
                 judge=None, extractor=None):
        self._seat, self._seat_rescue = seat, seat_rescue
        self._summary, self._summary_rescue = summary, summary_rescue
        self._judge, self._extractor = judge, extractor

    def seat(self):
        return self._seat

    def seat_rescue(self):
        return self._seat_rescue

    def summary(self):
        return self._summary

    def summary_rescue(self):
        return self._summary_rescue

    def judge(self, default_thinking_level: str = "minimal"):
        return self._judge

    def extractor(self):
        return self._extractor
