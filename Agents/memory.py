from datetime import datetime
import uuid

from dotenv import load_dotenv
from langgraph.store.base import BaseStore
from langgraph.store.memory import InMemoryStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from Agents.schemas import (
    Observation,
    RetrievedObservation,
    RetrievedStrategyPoint,
    StoredObservation,
    StoredStrategy,
    StoredStrategyPoint,
    StrategyPoint,
)

load_dotenv()

DEDUP_THRESHOLD = 0.90

def store_observation(store: BaseStore, extracted_observations: list[Observation], game_id: str=""):
    for obs in extracted_observations:
        perspective = obs.perspective
        content = obs.content

        items = store.search(("observations", perspective), query=content, limit=1)
        if items:
            item = items[0]
            score = item.score
            if score and score >= DEDUP_THRESHOLD:
                observation = StoredObservation.model_validate(item.value)
                observation.observation_count += 1
                observation.last_observed = datetime.now()
                store.put(("observations",perspective), item.key, observation.model_dump())
                continue

        new_observation = StoredObservation(
            observation_count=1,
            last_observed=datetime.now(),
            content=obs.content,
            game_id=game_id
        )
        store.put(("observations",perspective), str(uuid.uuid4()),new_observation.model_dump())


def store_strategy_points(
    store: BaseStore,
    extracted_strategy_points: list[StrategyPoint],
    game_id: str = "",
):
    for point in extracted_strategy_points:
        perspective = point.perspective
        situation_text = point.situation

        items = store.search(("strategy_points", perspective), query=situation_text, limit=1)
        if items:
            item = items[0]
            score = item.score
            if score and score >= DEDUP_THRESHOLD:
                stored_point = StoredStrategyPoint.model_validate(item.value)
                stored_point.observation_count += 1
                stored_point.last_observed = datetime.now()
                stored_point.action = point.action
                store.put(("strategy_points", perspective), item.key, stored_point.model_dump())
                continue

        stored_point = StoredStrategyPoint(
            observation_count=1,
            last_observed=datetime.now(),
            content=situation_text,
            action=point.action,
            game_id=game_id,
        )
        store.put(("strategy_points", perspective), str(uuid.uuid4()), stored_point.model_dump())


def retrieve_observations_for_agent(
    store: BaseStore,
    role: str,
    situations: list[str],
    top_k: int = 3,
) -> list[RetrievedObservation]:
    retrieved_by_key: dict[str, RetrievedObservation] = {}
    for situation in situations:
        try:
            items = store.search(("observations", role), query=situation, limit=top_k)
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
    situations: list[str],
    top_k: int = 3,
) -> list[RetrievedStrategyPoint]:
    retrieved_by_key: dict[str, RetrievedStrategyPoint] = {}

    for situation in situations:
        try:
            items = store.search(
                ("strategy_points", role),
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



def store_strategy(store: BaseStore, new_strategies: dict[str, str], game_id: str=""):
    # legacy code for storing a monolithic strategy string per role. 
    for role, strategy in new_strategies.items():
        stored = StoredStrategy(
            game_id=game_id,
            content=strategy,
            created_at=datetime.now()
        )
        store.put(("strategy", role), f"game_{game_id}", stored.model_dump())
        store.put(("strategy", role), "latest", stored.model_dump())

embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-2-preview",
)

store = InMemoryStore(
    index={
        "dims": 1536,
        "embed": embeddings,
        "fields": ["content"]
    }
)
