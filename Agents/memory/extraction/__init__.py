"""Post-game memory extraction — the upstream of the memory write path.

Turns a finished game into structured strategy/observation memory that seeds the
store (then gets deduped downstream). Two steps, mirroring the agent/`*_agent`
split used elsewhere:

  inputs.py            — format game state into the extraction prompt
  extraction_agent.py  — the post-game ``llm.invoke`` (primary → backup, retries)
"""

from .inputs import (
    build_extraction_prompt,
    build_role_extraction_prompt,
    format_extraction_inputs,
)
from .extraction_agent import ExtractionResult, extract_postgame

__all__ = [
    "ExtractionResult",
    "build_extraction_prompt",
    "build_role_extraction_prompt",
    "extract_postgame",
    "format_extraction_inputs",
]
