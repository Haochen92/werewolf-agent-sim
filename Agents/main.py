from dotenv import load_dotenv

from Agents.agents import prompt_log
from Agents.compute_metrics import compute_game_metrics, push_scores_to_langfuse
from Agents.game_config import GameConfig
from Agents.graphs.parent import parent_graph_compiled
from Agents.memory import store
from Agents.memory_persistence import (
    MemoryPersistenceConfig,
    seed_memory_from_config,
)
from Agents.tracing import (
    Metrics,
    build_game_config,
    flush,
    langfuse,
)


INITIAL_STATE = {
    "day_channel": [],
    "day_summaries": [],
    "wolf_channel": [],
    "investigator_results": [],
    "day_votes": [],
}




def run_game(
    memory_config: dict | None = None,
    session_id: str | None = None,
    game_config: GameConfig | dict | None = None,
    memory_persistence_config: MemoryPersistenceConfig | dict | None = None,
):
    seed_memory_from_config(memory_persistence_config, target_store=store)
    config = build_game_config(
        memory_config,
        session_id,
        game_config,
        memory_persistence_config,
    )
    game_id = config["configurable"]["game_id"]
    normalized_game_config = config["configurable"]["game_config"]
    normalized_memory_persistence_config = config["configurable"][
        "memory_persistence_config"
    ]
    metrics = Metrics()
    initial_state = {key: value.copy() for key, value in INITIAL_STATE.items()}

    prompt_log.clear()

    with langfuse.start_as_current_observation(
        as_type="span",
        name="werewolf-game",
        input=initial_state,
    ) as root:
        root.update_trace(
            name="werewolf_game",
            session_id=session_id,
            input=initial_state,
            output={"status": "running"},
            metadata={
                "game_id": game_id,
                "memory_config": config["configurable"]["memory_config"],
                "game_config": normalized_game_config,
                "memory_persistence_config": normalized_memory_persistence_config,
            },
        )
        flush()

        try:
            result = parent_graph_compiled.invoke(
                initial_state,
                config=config,
                context={"metrics": metrics},
            )
        except Exception as exc:
            error_output = {
                "status": "error",
                "error": repr(exc),
            }
            root.update(output=error_output, level="ERROR", status_message=str(exc))
            root.update_trace(output=error_output)
            flush()
            raise

        final_output = {
            "status": "success",
            "result": result,
            "raw_metrics": metrics.model_dump(mode="json")
        }
        root.update(output=final_output)
        root.update_trace(output=final_output)

        game_metrics = compute_game_metrics(result, metrics)
        push_scores_to_langfuse(game_metrics, root.trace_id, session_id)

    flush()
    return result

def main():
    load_dotenv()
    result = run_game()

    print(f"Winner: {result['winner']}")
    print(f"Game lasted {result['current_day']} days")
    print(f"Surviving wolves: {result['surviving_wolves']}")
    print(f"Surviving villagers: {result['surviving_villagers']}")

    for msg in result["day_channel"]:
        print(f"[Day {msg.day}, Round {msg.round}] {msg.player}: {msg.message}")


if __name__ == "__main__":
    main()
