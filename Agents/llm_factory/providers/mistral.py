"""Mistral (``mistral/`` models): a thin OpenAI-protocol client with a LangChain-like ``.invoke()``.
It has no structured-output mode of its own here; callers that need a schema use another provider."""

from __future__ import annotations

import os
from dataclasses import dataclass

_MISTRAL_BASE_URL = "https://api.mistral.ai/v1"


@dataclass
class _OpenAICompatResponse:
    content: str


class MistralChatModel:
    """Thin wrapper around Mistral API with LangChain-compatible .invoke()."""

    def __init__(self, model: str, *, temperature: float = 0.0):
        from openai import OpenAI

        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise ValueError("MISTRAL_API_KEY not set")
        self._client = OpenAI(base_url=_MISTRAL_BASE_URL, api_key=api_key)
        self._model = model
        self._temperature = temperature

    def invoke(self, prompt: str) -> _OpenAICompatResponse:
        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        else:
            messages = prompt
        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=self._temperature,
        )
        return _OpenAICompatResponse(content=response.choices[0].message.content)
