from dotenv import load_dotenv
from langfuse.langchain import CallbackHandler

from Agents.agents import prompt_log
from Agents.graphs.parent import parent_graph_compiled
from Agents.tracing import langfuse, build_game_config, flush, compute_and_push_scores


INITIAL_STATE = {
    "day_channel": [],
    "day_summaries": [],
    "wolf_channel": [],
    "investigator_results": [],
    "day_votes": [],
}




def run_game(memory_config: dict | None = None, session_id: str | None = None):
    config = build_game_config(memory_config, session_id)
    game_id = config["configurable"]["game_id"]

    prompt_log.clear()

    with langfuse.start_as_current_observation(
        as_type="span", name="werewolf-game"
    ) as root:
        root.update_trace(
            session_id=session_id,
            metadata={
                "game_id": game_id,
                "memory_config": config["configurable"]["memory_config"],
            },
        )

        result = parent_graph_compiled.invoke(INITIAL_STATE, config=config)

        # store trace_id for potential post-game score pushing
        compute_and_push_scores(result, root.trace_id)

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
