"""Rerank prompt: scores retrieved memory candidates by relevance to the agent situations."""

from langchain_core.prompts import ChatPromptTemplate


RERANK_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "human",
            """You are a relevance judge for a memory retrieval system in a Werewolf social deduction game.

A player is facing these situations:
{situations}

Below are memory candidates retrieved from past games. Score each candidate's relevance to the player's current situations.

Candidates:
{candidates}

Score every candidate from 1 (irrelevant) to 5 (highly relevant). A candidate is relevant if it describes a similar game dynamic, pressure pattern, or strategic dilemma — even if the surface details differ.""",
        )
    ]
)
