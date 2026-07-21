"""Import shim — decision scoring GRADUATED to ``Agents.memory.consolidation.decision_scoring``
(go-live 2026-07-21). The deterministic vote/night scorers are production credit primitives now;
eval callers (replay screens, instrument-validation studies, the frozen loop harness) keep this
path so the recorded history stays runnable. New code should import from the Agents home.
"""

from Agents.memory.consolidation.decision_scoring import (  # noqa: F401
    POWER_ROLES,
    REPLAYABLE_DECEIVER_ROLES,
    REPLAYABLE_TOWN_ROLES,
    THREAT_ROLES,
    NightOutcome,
    VoteOutcome,
    allow_abstain_for,
    no_lynch_streak_before,
    query_criticality,
    score_night_target,
    score_vote,
    wolf_vote_is_good,
)
