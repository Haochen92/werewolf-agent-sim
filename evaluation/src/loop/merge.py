"""Import shim — the obs fold GRADUATED to ``Agents.memory.consolidation.obs_fold`` (go-live
2026-07-21; its own docstring always called the freeze-old dedup core the production-reusable
piece). The frozen loop harness (driver) and its tests keep this path; new code imports from
the Agents home.
"""

from Agents.memory.consolidation.obs_fold import (  # noqa: F401
    collect_new_obs,
    merge_new_obs,
)
