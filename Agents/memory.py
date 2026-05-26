from datetime import datetime
from logging import getLogger
import uuid

from dotenv import load_dotenv
from langgraph.store.base import BaseStore
from langgraph.store.memory import InMemoryStore
from Agents.llm_factory import create_embeddings

from Agents.prompts import RERANK_PROMPT
from Agents.schemas import (
    RerankResult,
    RetrievedObservation,
    RetrievedStrategyPoint,
    StoredObservation,
    StoredStrategy,
    StoredStrategyPoint,
)

load_dotenv()

logger = getLogger(__name__)

DEDUP_THRESHOLD = 0.90
RERANK_TOP_K = 10
RERANK_KEEP = 3
RETRIEVAL_KEEP_PER_SITUATION = 3


def retrieve_observations_for_agent(
    store: BaseStore,
    role: str,
    action_phase: str,
    situations: list[str],
    top_k: int = 3,
) -> list[RetrievedObservation]:
    namespace = ("observations", role, action_phase)
    retrieved_by_key: dict[str, RetrievedObservation] = {}
    for situation in situations:
        try:
            items = store.search(namespace, query=situation, limit=top_k)
            for item in items:
                retrieved_observation = RetrievedObservation(
                    key=item.key,
                    observation=StoredObservation.model_validate(item.value),
                    matched_situation=situation,
                    score=item.score,
                )
                existing = retrieved_by_key.get(item.key)
                if existing is None or (retrieved_observation.score or 0.0) > (
                    existing.score or 0.0
                ):
                    retrieved_by_key[item.key] = retrieved_observation
        except Exception:
            continue

    return list(retrieved_by_key.values())


def retrieve_strategy_points_for_agent(
    store: BaseStore,
    role: str,
    action_phase: str,
    situations: list[str],
    top_k: int = 3,
) -> list[RetrievedStrategyPoint]:
    namespace = ("strategy_points", role, action_phase)
    retrieved_by_key: dict[str, RetrievedStrategyPoint] = {}

    for situation in situations:
        try:
            items = store.search(
                namespace,
                query=situation,
                limit=top_k,
            )
            for item in items:
                retrieved_strategy_point = RetrievedStrategyPoint(
                    key=item.key,
                    strategy_point=StoredStrategyPoint.model_validate(item.value),
                    matched_situation=situation,
                    score=item.score,
                )
                existing = retrieved_by_key.get(item.key)
                if existing is None or (retrieved_strategy_point.score or 0.0) > (
                    existing.score or 0.0
                ):
                    retrieved_by_key[item.key] = retrieved_strategy_point
        except Exception:
            continue

    return list(retrieved_by_key.values())


def store_strategy(store: BaseStore, new_strategies: dict[str, str], game_id: str = ""):
    for role, strategy in new_strategies.items():
        stored = StoredStrategy(
            game_id=game_id,
            content=strategy,
            created_at=datetime.now(),
        )
        store.put(("strategy", role), f"game_{game_id}", stored.model_dump())
        store.put(("strategy", role), "latest", stored.model_dump())


embeddings = create_embeddings(
    "gemini-embedding-001",
    output_dimensionality=1536,
)

store = InMemoryStore(
    index={
        "dims": 1536,
        "embed": embeddings,
        "fields": ["situation"],
    }
)
