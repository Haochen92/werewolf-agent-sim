from logging import getLogger

from Agents.prompts import RERANK_PROMPT
from Agents.schemas import (
    RerankResult,
    RetrievedObservation,
    RetrievedStrategyPoint,
)

logger = getLogger(__name__)

RERANK_TOP_K = 10
RERANK_KEEP = 3


def _format_observation_candidate(obs: RetrievedObservation) -> str:
    parts = [f"Situation: {obs.observation.situation}"]
    if obs.observation.approach:
        parts.append(f"Approach: {obs.observation.approach}")
    if obs.observation.outcome:
        parts.append(f"Outcome: {obs.observation.outcome}")
    return " | ".join(parts)


def _format_strategy_point_candidate(sp: RetrievedStrategyPoint) -> str:
    if sp.strategy_point.action:
        return f"{sp.strategy_point.situation} -> {sp.strategy_point.action}"
    return sp.strategy_point.situation


def _rerank(
    llm,
    situations: list[str],
    candidate_texts: list[str],
) -> RerankResult | None:
    chain = RERANK_PROMPT | llm.with_structured_output(RerankResult)
    numbered = "\n".join(
        f"[{i}] {text}" for i, text in enumerate(candidate_texts)
    )
    situations_text = "\n".join(f"- {s}" for s in situations)
    try:
        return chain.invoke(
            {"situations": situations_text, "candidates": numbered},
            config={"run_name": "rerank_candidates"},
        )
    except Exception as e:
        logger.warning(f"Reranking failed, falling back to bi-encoder order: {e}")
        return None


def _apply_rerank_scores(
    rerank_result: RerankResult | None,
    bi_encoder_scores: list[float | None],
    keep: int = RERANK_KEEP,
) -> list[int]:
    """Return indices to keep, ordered by (relevance desc, bi-encoder desc)."""
    n = len(bi_encoder_scores)
    if rerank_result is None:
        ranked = sorted(
            range(n), key=lambda i: bi_encoder_scores[i] or 0.0, reverse=True
        )
        return ranked[:keep]

    score_map = {
        r.index: r.relevance for r in rerank_result.rankings if r.index < n
    }
    ranked = sorted(
        range(n),
        key=lambda i: (score_map.get(i, 0), bi_encoder_scores[i] or 0.0),
        reverse=True,
    )
    return ranked[:keep]


def rerank_observations(
    llm,
    situations: list[str],
    observations: list[RetrievedObservation],
    keep: int = RERANK_KEEP,
) -> list[RetrievedObservation]:
    if len(observations) <= keep:
        return observations
    candidate_texts = [_format_observation_candidate(o) for o in observations]
    result = _rerank(llm, situations, candidate_texts)
    indices = _apply_rerank_scores(
        result, [o.score for o in observations], keep
    )
    return [observations[i] for i in indices]


def rerank_strategy_points(
    llm,
    situations: list[str],
    strategy_points: list[RetrievedStrategyPoint],
    keep: int = RERANK_KEEP,
) -> list[RetrievedStrategyPoint]:
    if len(strategy_points) <= keep:
        return strategy_points
    candidate_texts = [
        _format_strategy_point_candidate(sp) for sp in strategy_points
    ]
    result = _rerank(llm, situations, candidate_texts)
    indices = _apply_rerank_scores(
        result, [sp.score for sp in strategy_points], keep
    )
    return [strategy_points[i] for i in indices]
