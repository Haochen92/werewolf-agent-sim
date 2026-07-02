"""Off-policy per-turn vote-replay screen over frozen EvalCases.

The standing memory-effectiveness screen: take a decision as it was actually
frozen in a game (board, visible history, the memory it retrieved), swap ONLY the
injected memory block — memory-OFF vs memory-AS-STORED (and schema / outcome-framing
variants) — regenerate the action, and score it MECHANICALLY, blind to the eventual
game result. Decisions are paired and tested with an exact-binomial McNemar over the
discordant pairs. Two scoring lenses: ``town`` (correct = the vote/kill hits a real
threat / power role) and ``wolf`` (deceiver lens, correct = the vote induces a town
mislynch), so a deceiver arm is scored on its own win condition.

Layers (import from this package, not the submodules):
- ``cases``    case/game-index loading + day-stratified cohort selection (no LLM)
- ``replay``   off-policy regeneration of one decision with a swapped memory block
- ``schemas``  replay-INPUT output-schema variants (reason-first / memory-linked / …)
- ``stats``    ``mcnemar_p`` paired-discordant test
- ``screens``  the day-vote / night / discussion / framing / adherence screen runners

Records: evidence/memory_system/effectiveness/decision_replay/ (the study journey)
and evidence/evaluation/replay_screens/ (the apparatus write-up)."""

from evaluation.src.replay.decision_screen.cases import (
    _abstained_on_day,
    _find_case,
    _find_endgame_plant,
    _mem_text,
    _select_diverse,
    iter_cases,
    load_game_index,
)
from evaluation.src.replay.decision_screen.replay import (
    NIGHT_SPECS,
    _replay_night,
    _replay_vote,
    _replay_vote_structured,
)
from evaluation.src.replay.decision_screen.schemas import (
    DayVoteOutputMemoryLinked,
    DayVoteOutputReasonFirst,
    DayVoteOutputSituationMatch,
    DayVoteOutputStructuredApplicability,
    MemoryVerdict,
)
from evaluation.src.replay.decision_screen.screens import (
    PASSIVE_STANCES,
    VoteReasoningCoherence,
    _causal_one,
    replay_condition_grid,
    run_adherence_scan,
    run_adherence_smoke,
    run_applicability_probe,
    run_causal,
    run_coherence_test,
    run_discussion_causal,
    run_framing_rewrite_screen,
    run_night_causal,
    run_observational,
    run_reorder_adoption,
    run_reorder_test,
)
from evaluation.src.replay.decision_screen.stats import mcnemar_p

__all__ = [
    # cases
    "load_game_index",
    "iter_cases",
    "_abstained_on_day",
    "_select_diverse",
    "_mem_text",
    "_find_case",
    "_find_endgame_plant",
    # replay
    "NIGHT_SPECS",
    "_replay_vote",
    "_replay_night",
    "_replay_vote_structured",
    # schemas
    "MemoryVerdict",
    "DayVoteOutputReasonFirst",
    "DayVoteOutputMemoryLinked",
    "DayVoteOutputSituationMatch",
    "DayVoteOutputStructuredApplicability",
    # stats
    "mcnemar_p",
    # screens
    "run_observational",
    "run_adherence_smoke",
    "_causal_one",
    "run_causal",
    "run_night_causal",
    "run_discussion_causal",
    "run_reorder_test",
    "run_reorder_adoption",
    "replay_condition_grid",
    "VoteReasoningCoherence",
    "run_coherence_test",
    "run_applicability_probe",
    "run_framing_rewrite_screen",
    "run_adherence_scan",
    "PASSIVE_STANCES",
]
