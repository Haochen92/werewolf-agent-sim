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
    from Agents.llm_factory import GameModels
    from Agents.llm_factory.chat import provider_name
    from Agents.llm_factory.embeddings import provider_complaint

    # A models object of its own, dropped after the one question: the key reaches the provider
    # by the same path a game's turn uses, and nothing of it is kept.
    models = GameModels(api_key=api_key, model=model)

    def call() -> None:
        models.probe().invoke("Reply with the single word OK.")

    try:
        await asyncio.wait_for(asyncio.to_thread(call), timeout=_TIMEOUT_SECONDS)
    except asyncio.TimeoutError as exc:
        raise KeyRefused(f"{provider_name(model)} did not answer within "
                         f"{int(_TIMEOUT_SECONDS)} s. Try again.") from exc
    except Exception as exc:  # the provider's complaint is the useful part
        detail = provider_complaint(exc, scrub=models.redact)
        raise KeyRefused(f"{provider_name(model)} refused this key: {detail}.") from exc
