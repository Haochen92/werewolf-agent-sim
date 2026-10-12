"""One structured-output call to a Claude model, for the memory pipeline's Claude stages.

The de-halo pass and (when configured) strategy synthesis call Claude directly through the
Anthropic SDK rather than the game's model factory. The key is CLAUDE_API_KEY (or
ANTHROPIC_API_KEY). These calls are not traced in Langfuse, so every call's tokens are added to
``usage_totals`` for the caller to report.
"""

from __future__ import annotations

import os
import threading
from typing import Any

from pydantic import BaseModel

_THINKING_OFF = {"minimal", "off", "none"}

usage_totals: dict[str, int] = {"calls": 0, "input_tokens": 0, "output_tokens": 0}
_lock = threading.Lock()


def claude_api_key() -> str | None:
    return os.getenv("CLAUDE_API_KEY") or os.getenv("ANTHROPIC_API_KEY")


def parse_with_claude(prompt: str, schema: type[BaseModel], model: str,
                      thinking_level: str | None = None) -> tuple[BaseModel | None, dict]:
    """The parsed output and token usage of one call. Raises when there is no key.

    Claude models think by default and thinking counts against max_tokens (a 46-lesson de-halo
    used about 12k), so the cap is 32k; above about 21k the SDK requires streaming unless the call
    sets its own timeout."""
    import anthropic

    api_key = claude_api_key()
    if not api_key:
        raise RuntimeError(f"no CLAUDE_API_KEY for {model}")
    kwargs: dict[str, Any] = {}
    level = (thinking_level or "").lower()
    if level in _THINKING_OFF:
        kwargs["thinking"] = {"type": "disabled"}
    elif level:
        kwargs["thinking"] = {"type": "adaptive"}
        kwargs["output_config"] = {"effort": level}
    response = anthropic.Anthropic(api_key=api_key).messages.parse(
        model=model, max_tokens=32000, timeout=600, output_format=schema,
        messages=[{"role": "user", "content": prompt}], **kwargs)
    usage = {"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens}
    with _lock:
        usage_totals["calls"] += 1
        usage_totals["input_tokens"] += usage["input_tokens"]
        usage_totals["output_tokens"] += usage["output_tokens"]
    return response.parsed_output, usage
