from Agents.state import DayChannel, InvestigatorResult, WolfChannel


def format_day_channel(messages: list[DayChannel]) -> str:
    if not messages:
        return "No messages yet."
    return "\n".join(
        f"[Day {m.day}, Round {m.round}] {m.player}: {m.message}" for m in messages
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

