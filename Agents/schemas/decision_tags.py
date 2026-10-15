"""The decision tagger's output: one tag per extracted observation.

Model-visible (the tagger's structured output), so field docs are ``Field(description=)`` and the
classes carry no docstring (it would fold into the JSON schema sent to the model).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

PackTurn = Literal["chat", "kill", "skill", "several", "none"]


class DecisionTag(BaseModel):
    index: int = Field(description="The lesson's index.")
    decision_day: int = Field(description="The day or night number of the decision the lesson describes; "
                                          "0 for a pattern over several decisions.")
    pack_turn: PackTurn = Field(description="For a chanteuse or illusionist night_action lesson, the pack's "
                                            "turn: chat, kill, skill or several; none for every other lesson.")


class DecisionTags(BaseModel):
    tags: list[DecisionTag] = Field(description="One tag per lesson.")
