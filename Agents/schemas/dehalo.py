"""The de-halo judge's output: one judgment per extracted observation.

Model-visible (the judge's structured output), so field docs are ``Field(description=)`` and the
classes carry no docstring (it would fold into the JSON schema sent to the model).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Judgment(BaseModel):
    index: int = Field(description="The lesson's index.")
    halo: bool = Field(description="True when the original verdict is not supported by the record.")
    revised_verdict: Literal["positive", "negative", "mixed", "unclear"] = Field(
        description="The verdict the record supports; the original one when it holds.")
    reason: str = Field(description="One sentence: what in the record supports or fails to support the verdict.")


class Judgments(BaseModel):
    judgments: list[Judgment] = Field(description="One judgment per lesson.")
