"""Every model that rides graph state is on the checkpoint serializer's allowlist.

A human turn resumes the game from its checkpoint, and the serializer turns any class not on
its allowlist into a plain dict. Code that then reads an attribute crashes the game: the private
night record (NightActionRecord) was left off, and the first game whose human survived a night
died on resume with "'dict' object has no attribute 'day'" (2026-10-04). This walks every graph
state's annotations, so a model added to state without its allowlist entry fails here first.
"""
from __future__ import annotations

import enum
import importlib
import inspect
import pkgutil
import typing

from pydantic import BaseModel

import Agents.state
from Agents.memory.checkpointer import _STATE_MODEL_ALLOWLIST, durable_serde
from Agents.schemas.game_events import NightActionRecord


def _state_classes():
    for info in pkgutil.walk_packages(Agents.state.__path__, "Agents.state."):
        module = importlib.import_module(info.name)
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if cls.__module__ == module.__name__ and typing.is_typeddict(cls):
                yield cls


def _ours(cls) -> bool:
    return cls.__module__.startswith("Agents.")


def _models_in(annotation, found: set) -> None:
    for arg in typing.get_args(annotation):
        _models_in(arg, found)
    if not inspect.isclass(annotation) or annotation in found or not _ours(annotation):
        return
    if issubclass(annotation, BaseModel):
        found.add(annotation)
        for f in annotation.model_fields.values():
            _models_in(f.annotation, found)
    elif issubclass(annotation, enum.Enum):
        found.add(annotation)


def test_every_model_in_graph_state_is_allowlisted():
    found: set = set()
    for cls in _state_classes():
        for hint in typing.get_type_hints(cls, include_extras=True).values():
            _models_in(hint, found)
    assert NightActionRecord in found  # the walk reaches the state's models
    missing = sorted(c.__name__ for c in found - set(_STATE_MODEL_ALLOWLIST))
    assert not missing, f"add to _STATE_MODEL_ALLOWLIST in Agents/memory/checkpointer.py: {missing}"


def test_the_night_record_survives_a_checkpoint_round_trip():
    serde = durable_serde()
    record = NightActionRecord(day=1, actor="player_9", action="protect", target="player_3", outcome="no_attack")
    back = serde.loads_typed(serde.dumps_typed({"night_actions": [record]}))["night_actions"][0]
    assert isinstance(back, NightActionRecord) and back.day == 1
