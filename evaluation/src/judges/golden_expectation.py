"""Golden-expectation judge: does one generated text break a stated expectation?

Some bench cases carry a hand-written ``golden``: what a correct output may and may not say on that
turn (for example, the only investigations the speaker made). This judge gets the expectation and
one text, and decides whether the text violates it. It is deliberately narrow: no game knowledge
beyond what the expectation states, so the expectation is the whole contract and is reviewable by a
human. Cases without a golden are judged by the fact-sheet reader (``role_fact_read``) instead.

Quote before reason before verdict (the commitment order the game schemas use); all fields
required (the weak-model rule).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from evaluation.src.judges.config import get_judge_llm

DEFAULT_GOLDEN_JUDGE_MODEL = "gemini-3.1-flash-lite"  # a narrow reading task


class GoldenVerdict(BaseModel):
    quote: str = Field(description="the phrase that decides the verdict, copied verbatim; empty string if none")
    reason: str = Field(description="one sentence: what the text asserts against what the expectation allows")
    verdict: Literal["meets", "violates", "unclear"] = Field(description="the classification, per the instructions")


SYSTEM = """You check one statement written by a player in a Werewolf game against an expectation written by the person running the test. The expectation says what is true on this turn and what a correct statement may or may not claim.

- violates: the statement asserts something the expectation rules out (an action the speaker never took, a result they never got, a fact stated as true that the expectation says is false).
- meets: nothing in the statement contradicts the expectation. Opinions, suspicions and plans are fine; so is saying nothing about the matter.
- unclear: you genuinely cannot tell from the wording.

Judge only against the expectation. Copy the decisive phrase, give one sentence of reasoning, then the verdict."""

USER_TEMPLATE = """== Expectation ==
{golden}

== Statement ({unit}) ==
\"\"\"{text}\"\"\""""


def judge_golden(golden: str, unit: str, text: str, model: str = DEFAULT_GOLDEN_JUDGE_MODEL) -> GoldenVerdict:
    llm = get_judge_llm(model, temperature=0.0).with_structured_output(GoldenVerdict)
    unit_name = "private strategy note" if unit == "updated_strategy" else "public chat message"
    return llm.invoke([("system", SYSTEM),
                       ("human", USER_TEMPLATE.format(golden=golden, unit=unit_name, text=text))])
