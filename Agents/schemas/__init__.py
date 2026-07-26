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
    DaySummary,
    DayVote,
    DeathRecord,
    FiringReason,
    InvestigatorResult,
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
from Agents.schemas.output import (
    AddressingExtraction,
    DayDiscussOutput,
    DaySummaryOutput,
    DayVoteOutput,
    HealerOutput,
    InvestigatorOutput,
    NoveltyJudgment,
    SerialKillerOutput,
    SituationSummary,
    VigilanteOutput,
    WolfNightDiscussOutput,
    WolfNightVoteOutput,
)
from Agents.schemas.scheduler import (
    Balance,
    Decision,
    ReactiveItem,
)


__all__ = [
    "ActionPhase",
    "AddressedTarget",
    "AddressingExtraction",
    "Balance",
    "CandidateRelevance",
    "ComputedGameMetrics",
    "DedupCandidate",
    "DedupCase",
    "DayChannel",
    "DayDiscussOutput",
    "DayResolutionMetric",
    "DaySummary",
    "DaySummaryCase",
    "DaySummaryOutput",
    "DayVote",
    "DayVoteOutput",
    "DeathRecord",
    "Decision",
    "EvalCase",
    "EvalPrivateContext",
    "EvalProvenance",
    "NightAction",
    "ExtractionCase",
    "FiringReason",
    "GameOutcome",
    "GameStrategyOutput",
    "GraphContext",
    "HealerOutput",
    "HumanTurnRequest",
    "HumanTurnResponse",
    "InvestigatorOutput",
    "InvestigatorResult",
    "Metrics",
    "NightResolutionMetric",
    "NoveltyJudgment",
    "Observation",
    "ReactiveItem",
    "SerialKillerOutput",
    "VigilanteOutput",
    "RerankResult",
    "RetrievedObservation",
    "RetrievedStrategyPoint",
    "SituationSummary",
    "StoredObservation",
    "StoredStrategy",
    "StoredStrategyPoint",
    "StrategyPoint",
    "WolfChannel",
    "WolfNightDiscussOutput",
    "WolfNightVoteOutput",
]
