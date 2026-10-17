"""Ask the provider one trivial question with a player's key before a game is resumed on
it. A key that is wrong, expired or out of credit fails here, with the provider's own
complaint, instead of killing the game on its first real turn."""

from __future__ import annotations

import asyncio
import logging

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 20.0


class KeyRefused(ValueError):
    """The provider would not serve the model on this key; the message says why."""


async def check_key(model: str, api_key: str) -> None:
    """Raise KeyRefused with a one-line reason when the provider will not serve this
    model on this key. The sync client runs in a worker thread so the loop stays free."""
    from Agents.llm_factory import GAME_LLM, GameLLM, create_chat_model
    from Agents.llm_factory.chat import provider_name
    from Agents.llm_factory.embeddings import provider_complaint

    def call() -> None:
        token = GAME_LLM.set(GameLLM(api_key=api_key, model=model))
        try:
            # Temperature 1: OpenAI's reasoning models (GPT-6 Luna) refuse any other value.
            create_chat_model(model, temperature=1.0).invoke("Reply with the single word OK.")
        finally:
            GAME_LLM.reset(token)

    try:
        await asyncio.wait_for(asyncio.to_thread(call), timeout=_TIMEOUT_SECONDS)
    except asyncio.TimeoutError as exc:
        raise KeyRefused(f"{provider_name(model)} did not answer within "
                         f"{int(_TIMEOUT_SECONDS)} s. Try again.") from exc
    except Exception as exc:  # the provider's complaint is the useful part
        detail = provider_complaint(exc).replace(api_key, "***")
        raise KeyRefused(f"{provider_name(model)} refused this key: {detail}.") from exc
