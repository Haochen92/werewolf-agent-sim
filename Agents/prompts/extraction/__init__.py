"""Extraction prompts, split by lifecycle: `postgame` (v5 whole-game prompts, kept for older paths and
experiments), `cell` (the per-cell prompts the offline extraction job runs), `day_summary` (in-game), `archive` (superseded/dead). Re-exported flat so
`from Agents.prompts.extraction import X` and `from Agents.prompts import X` keep working unchanged.
"""

from Agents.prompts.extraction.archive import (
    ARCHIVED_POSTGAME_EXTRACTION_PROMPT,
    V6_CELL_EXTRACTION_PROMPT,
    VILLAGER_DAY_EXTRACTION_PROMPT,
)
from Agents.prompts.extraction.cell import (
    CELL_EXTRACTION_PREFIX,
    CELL_OBSERVATION_TAIL,
    CELL_SP_SYNTHESIS_PROMPT,
    CELL_STRATEGY_TAIL,
)
from Agents.prompts.extraction.day_summary import DAY_SUMMARY_PROMPT
from Agents.prompts.extraction.postgame import (
    POSTGAME_EXTRACTION_PROMPT,
    ROLE_EXTRACTION_PREFIX,
    ROLE_EXTRACTION_TAIL,
    ROLE_PHASE_EXTRACTION_TAIL,
)

__all__ = [
    "ARCHIVED_POSTGAME_EXTRACTION_PROMPT",
    "CELL_EXTRACTION_PREFIX",
    "CELL_OBSERVATION_TAIL",
    "CELL_SP_SYNTHESIS_PROMPT",
    "CELL_STRATEGY_TAIL",
    "DAY_SUMMARY_PROMPT",
    "POSTGAME_EXTRACTION_PROMPT",
    "ROLE_EXTRACTION_PREFIX",
    "ROLE_EXTRACTION_TAIL",
    "ROLE_PHASE_EXTRACTION_TAIL",
    "V6_CELL_EXTRACTION_PROMPT",
    "VILLAGER_DAY_EXTRACTION_PROMPT",
]
