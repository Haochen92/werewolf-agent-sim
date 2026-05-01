from dotenv import load_dotenv

from Agents.graphs.parent import parent_graph_compiled


def run_game(config: dict | None = None):
    return parent_graph_compiled.invoke({}, config=config)


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

