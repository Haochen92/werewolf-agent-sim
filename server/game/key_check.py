"""Ask the provider one trivial question with a player's key before a game is resumed on
it. A key that is wrong, expired or out of credit fails here, with the provider's own
complaint, instead of killing the game on its first real turn."""

from __future__ import annotations

import asyncio
import logging

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 20.0


async def check_key(model: str, api_key: str) -> None:
    """Raise ValueError with a one-line reason when the provider will not serve this
    model on this key. The sync client runs in a worker thread so the loop stays free."""
    from Agents.llm_factory import GAME_LLM, GameLLM, create_chat_model

    def call() -> None:
        token = GAME_LLM.set(GameLLM(api_key=api_key, model=model))
        try:
            create_chat_model(model, temperature=0.0).invoke("Reply with the single word OK.")
        finally:
            GAME_LLM.reset(token)

    try:
        await asyncio.wait_for(asyncio.to_thread(call), timeout=_TIMEOUT_SECONDS)
    except asyncio.TimeoutError as exc:
        raise ValueError(f"the provider did not answer within {int(_TIMEOUT_SECONDS)} s") from exc
    except Exception as exc:  # the provider's complaint is the useful part
        detail = repr(exc).replace(api_key, "***")
        raise ValueError(f"the provider rejected this key: {detail[:300]}") from exc
