"""Post-game memory extraction — the upstream of the memory write path.

Turns a finished game into structured strategy/observation memory that seeds the
store (then gets deduped downstream). Two steps, mirroring the agent/`*_agent`
split used elsewhere:

  inputs.py            — format game state into the extraction prompt
  extraction_agent.py  — the post-game ``llm.invoke`` (primary → backup, retries)
"""

from .inputs import (
    build_extraction_prompt,
    build_role_extraction_prefix,
    build_role_extraction_prompt,
    build_role_extraction_tail,
    format_extraction_inputs,
)
from .extraction_agent import (
    EXTRACTION_ROLES,
    ExtractionResult,
    extract_postgame,
    extract_postgame_per_role,
)
from .prefix_cache import PrefixCache, create_prefix_cache

__all__ = [
    "EXTRACTION_ROLES",
    "ExtractionResult",
    "PrefixCache",
    "create_prefix_cache",
    "build_extraction_prompt",
    "build_role_extraction_prefix",
    "build_role_extraction_prompt",
    "build_role_extraction_tail",
    "extract_postgame",
    "extract_postgame_per_role",
    "format_extraction_inputs",
]
