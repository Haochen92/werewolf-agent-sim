from Agents.state import DayChannel, DaySummary, InvestigatorResult, WolfChannel


def format_day_channel(messages: list[DayChannel]) -> str:
    if not messages:
        return "No messages yet."
    return "\n".join(
        f"[Day {m.day}, Round {m.round}] {m.player}: {m.message}" for m in messages
    )


def format_day_channel_for_day(messages: list[DayChannel], current_day: int) -> str:
    return format_day_channel([m for m in messages if m.day == current_day])


def format_day_summaries(summaries: list[DaySummary], before_day: int | None = None) -> str:
    selected = [
        summary for summary in summaries
        if before_day is None or summary.day < before_day
    ]
    if not selected:
        return "No previous day summaries yet."
    return "\n\n".join(
        f"[Day {summary.day}]\n{summary.summary}" for summary in selected
    )


def format_wolf_channel(messages: list[WolfChannel]) -> str:
    if not messages:
        return "No messages yet."
    return "\n".join(
        f"[Day {m.day}, Round {m.round}] {m.wolf}: {m.message}.  vote: {m.vote}"
        for m in messages
    )


def format_investigator_results(results: list[InvestigatorResult]) -> str:
    if not results:
        return "No investigations yet."
    return "\n".join(
        f"Day {r.day}: {r.player_investigated} was revealed as {r.role_revealed}"
        for r in results
    )

def format_day_channel_postgame(messages: list[DayChannel], roles: dict[str, str]) -> str:
    if not messages:
        return "No messages yet."
    return "\n".join(
        f"[Day {m.day}, Round {m.round}] {m.player} ({roles.get(m.player, 'unknown')}): {m.message}"
        for m in messages
    )
    
 
def format_strategy_notes_postgame(
    agent_strategies: dict[str, str], roles: dict[str, str]
) -> str:
    if not agent_strategies:
        return "No strategy notes recorded."
    return "\n".join(
        f"{player} ({roles.get(player, 'unknown')}): {strategy}"
        for player, strategy in agent_strategies.items()
    )
 
 
def format_roles(roles: dict[str, str]) -> str:
    return "\n".join(f"{player}: {role}" for player, role in roles.items())


def format_initial_strategies(initial_strategies: dict[str, str]) -> str:
    if not initial_strategies:
        return "No initial strategies recorded."
    return "\n".join(
        f"{role.capitalize()}: {strategy}"
        for role, strategy in initial_strategies.items()
    )


def format_retrieved_observations(observations: list[str]) -> str:
    if not observations:
        return "No past observations available."
    return "\n".join(f"- {observation}" for observation in observations)


def format_strategy_points(strategy_points: list[str]) -> str:
    if not strategy_points:
        return "No dynamic strategy points available."
    return "\n".join(f"- {strategy_point}" for strategy_point in strategy_points)
