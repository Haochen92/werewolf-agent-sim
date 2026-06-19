"""Post-game memory extraction — the upstream of the memory write path.

Turns a finished game into structured strategy/observation memory that seeds the
store (then gets deduped downstream). Two steps, mirroring the agent/`*_agent`
split used elsewhere:

  inputs.py            — format game state into the extraction prompt
  extraction_agent.py  — the post-game ``llm.invoke`` (primary → backup, retries)
  augment_agent.py     — focused re-extraction to deepen ONE (role, phase) namespace
"""

from .inputs import (
    build_extraction_prompt,
    build_role_extraction_prefix,
    build_role_extraction_prompt,
    build_role_extraction_tail,
    build_role_phase_extraction_tail,
    extraction_inputs_from_frozen_case,
    format_extraction_inputs,
)
from .extraction_agent import (
    EXTRACTION_ROLES,
    CellExtractionOutput,
    ExtractionResult,
    extract_postgame,
    extract_postgame_per_cell,
    extract_postgame_per_role,
)
from .augment_agent import (
    AugmentTarget,
    augment_game_over_targets,
    augment_namespace_for_game,
)
from .prefix_cache import PrefixCache, create_prefix_cache

__all__ = [
    "EXTRACTION_ROLES",
    "CellExtractionOutput",
    "ExtractionResult",
    "PrefixCache",
    "AugmentTarget",
    "create_prefix_cache",
    "augment_game_over_targets",
    "augment_namespace_for_game",
    "build_extraction_prompt",
    "build_role_extraction_prefix",
    "build_role_extraction_prompt",
    "build_role_extraction_tail",
    "build_role_phase_extraction_tail",
    "extraction_inputs_from_frozen_case",
    "extract_postgame",
    "extract_postgame_per_cell",
    "extract_postgame_per_role",
    "format_extraction_inputs",
]
