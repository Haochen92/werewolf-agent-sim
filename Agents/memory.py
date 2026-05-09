from datetime import datetime
import uuid

from dotenv import load_dotenv
from langgraph.store.memory import InMemoryStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from Agents.schemas import (
    Observation,
    SituationSummary,
    StoredObservation,
    StoredStrategy,
    StoredStrategyPoint,
    StrategyPoint,
)

load_dotenv()

DEDUP_THRESHOLD = 0.90

def store_observation(store: InMemoryStore, extracted_observations: list[Observation], game_id: str=""):
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

def store_strategy(store: InMemoryStore, new_strategies: dict[str, str], game_id: str=""):
    for role, strategy in new_strategies.items():
        stored = StoredStrategy(
            game_id=game_id,
            content=strategy,
            created_at=datetime.now()
        )
        store.put(("strategy", role), f"game_{game_id}", stored.model_dump())
        store.put(("strategy", role), "latest", stored.model_dump())


def store_strategy_points(
    store: InMemoryStore,
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
    store: InMemoryStore,
    role: str,
    day_channel,
    current_day: int,
    current_round: int,
    previous_strategy: str,
    top_k: int = 3,
) -> dict[str, list[str]]:
    from Agents.agents import get_llm
    from Agents.formatters import format_day_channel
    from Agents.prompts import SITUATION_ROLE_LENS, SITUATION_SUMMARY_PROMPT

    recent_messages = [message for message in day_channel if message.day == current_day]
    recent_events = (
        format_day_channel(recent_messages)
        if recent_messages
        else "No events yet today."
    )

    role_lens = SITUATION_ROLE_LENS.get(role, "")

    prompt = SITUATION_SUMMARY_PROMPT.format(
        player_role=role,
        current_day=current_day,
        current_round=current_round,
        recent_events=recent_events,
        previous_strategy=previous_strategy or "No strategy yet.",
        role_lens=role_lens,
    )

    try:
        result = get_llm().with_structured_output(SituationSummary).invoke(prompt)
        situations = result.situations
    except Exception:
        situations = [f"Day {current_day} as {role}, round {current_round}"]

    seen_keys: set[str] = set()
    retrieved_observations: list[str] = []
    for situation in situations:
        try:
            items = store.search(("observations", role), query=situation, limit=top_k)
            for item in items:
                if item.key not in seen_keys:
                    seen_keys.add(item.key)
                    retrieved_observations.append(item.value["content"])
        except Exception:
            continue

    return {
        "situations": situations,
        "retrieved_observations": retrieved_observations,
    }


def retrieve_strategy_points_for_agent(
    store: InMemoryStore,
    role: str,
    situations: list[str],
    top_k: int = 5,
) -> list[str]:
    seen_keys: set[str] = set()
    results: list[str] = []

    for situation in situations:
        try:
            items = store.search(
                ("strategy_points", role),
                query=situation,
                limit=top_k,
            )
            for item in items:
                if item.key in seen_keys:
                    continue
                seen_keys.add(item.key)

                stored_situation = item.value.get("content", "")
                stored_action = item.value.get("action", "")
                if stored_action:
                    results.append(f"{stored_situation} -> {stored_action}")
                elif stored_situation:
                    results.append(stored_situation)
        except Exception:
            continue

    return results


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
