"""Pydantic schemas, grouped by concern (re-exported flat for convenience).

output.py + the extraction/rerank models in memory.py are MODEL-VISIBLE structured-output contracts
(frozen — their schema is sent to the model); game_events / scheduler / metrics / evaluation and the
store/retrieval models in memory.py are internal records (state / tracing / storage), never sent to a
model.
"""

from Agents.schemas.roles import ActionPhase
from Agents.schemas.evaluation import (
    DaySummaryCase,
    DedupCandidate,
    DedupCase,
    EvalCase,
    EvalPrivateContext,
    EvalProvenance,
    ExtractionCase,
    NightAction,
)
from Agents.schemas.game_events import (
    AddressedTarget,
    DayChannel,
    DayRound,
    DaySummary,
    DayVote,
    DeathRecord,
    DiscussionPassReason,
    FiringReason,
    InvestigatorResult,
    NightActionRecord,
    RoundCandidate,
    WolfChannel,
)
from Agents.schemas.human_player import (
    HumanTurnRequest,
    HumanTurnResponse,
)
from Agents.schemas.memory import (
    CandidateRelevance,
    GameStrategyOutput,
    Observation,
    RerankResult,
    RetrievedObservation,
    RetrievedStrategyPoint,
    StoredObservation,
    StoredStrategy,
    StoredStrategyPoint,
    StrategyPoint,
)
from Agents.schemas.metrics import (
    ComputedGameMetrics,
    DayResolutionMetric,
    GameOutcome,
    GraphContext,
    Metrics,
    NightResolutionMetric,
)
from Agents.schemas.night import Attack, Bet, NightChoice, NightOutcome, NightReport
from Agents.schemas.lineup_output import (
    carrier_output,
    day_discuss_output,
    day_vote_output,
    night_output,
    wolf_chat_output,
)
from Agents.schemas.output import (
    AddressingExtraction,
    DaySummaryOutput,
    DaySummaryOutputV2,
    DaySummaryOutputV3,
    DaySummaryOutputV4,
    OpeningVerdict,
    OpeningVerdicts,
    LineEchoVerdict,
    SituationSummary,
)
from Agents.schemas.scheduler import (
    Balance,
    Decision,
    ReactiveItem,
)
from Agents.schemas.turn import (
    ResolvedDayDiscussion,
    ResolvedDayVote,
    ResolvedNightChoice,
    ResolvedTurn,
    ResolvedWolfDiscussion,
    TurnEffects,
    TurnKind,
)


__all__ = [
    "ActionPhase",
    "Attack",
    "Bet",
    "NightReport",
    "NightChoice",
    "NightOutcome",
    "AddressedTarget",
    "AddressingExtraction",
    "Balance",
    "CandidateRelevance",
    "ComputedGameMetrics",
    "DedupCandidate",
    "DedupCase",
    "DayChannel",
    "DayRound",
    "RoundCandidate",
    "DayResolutionMetric",
    "DaySummary",
    "DaySummaryCase",
    "DaySummaryOutput",
    "DaySummaryOutputV2",
    "DaySummaryOutputV3",
    "DaySummaryOutputV4",
    "DayVote",
    "DeathRecord",
    "Decision",
    "DiscussionPassReason",
    "EvalCase",
    "EvalPrivateContext",
    "EvalProvenance",
    "NightAction",
    "ExtractionCase",
    "FiringReason",
    "GameOutcome",
    "GameStrategyOutput",
    "GraphContext",
    "HumanTurnRequest",
    "HumanTurnResponse",
    "InvestigatorResult",
    "NightActionRecord",
    "Metrics",
    "NightResolutionMetric",
    "OpeningVerdict",
    "OpeningVerdicts",
    "LineEchoVerdict",
    "Observation",
    "ReactiveItem",
    "ResolvedDayDiscussion",
    "ResolvedDayVote",
    "ResolvedNightChoice",
    "ResolvedTurn",
    "ResolvedWolfDiscussion",
    "RerankResult",
    "RetrievedObservation",
    "RetrievedStrategyPoint",
    "SituationSummary",
    "StoredObservation",
    "StoredStrategy",
    "StoredStrategyPoint",
    "StrategyPoint",
    "TurnEffects",
    "TurnKind",
    "WolfChannel",
    "carrier_output",
    "day_discuss_output",
    "day_vote_output",
    "night_output",
    "wolf_chat_output",
]
