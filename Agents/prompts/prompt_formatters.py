from Agents.board_clocks import alive_role_counts
from Agents.schemas import RetrievedObservation, RetrievedStrategyPoint
from Agents.schemas.game_events import (
    DayChannel,
    DaySummary,
    DayVote,
    DeathRecord,
    InvestigatorResult,
    WolfChannel,
)


def format_dead_roster(roster: list[DeathRecord]) -> str:
    """Render the public dead roster as one compact line: who is dead, their revealed role, and
    when/how they died — e.g. "player_2 (villager, night 1), player_5 (wolf, lynched day 2)".

    This is deterministic PUBLIC info (every death path announces the role), so it replaces the
    error-prone habit of re-parsing the game_master's death prose out of the transcript."""
    if not roster:
        return "No one has died yet."
    parts = []
    for d in roster:
        role = d.role or "role not revealed"
        when = f"night {d.day}" if d.phase == "night" else f"lynched day {d.day}"
        parts.append(f"{d.player} ({role}, {when})")
    return ", ".join(parts)


_ALIVE_ROLE_ORDER = ["wolf", "serial_killer", "healer", "investigator", "vigilante", "villager"]


def format_alive_roles(cast_role_counts: dict[str, int], roster: list[DeathRecord]) -> str:
    """Render the roles still in play as one line — e.g. "2 wolf, 1 serial killer, 3 villager".

    Like format_dead_roster this is deterministic PUBLIC info: the cast is fixed and public, and every
    death announces the dead player's role, so the fixed cast minus the revealed-dead roles is exactly
    what remains (census math shared with board_clocks, which derives criticality from the same
    subtraction). Render the survivors in a fixed role order (no pluralization — matches the tested
    study text). Returns "" when no census is available (legacy replay payloads that never carried
    cast_role_counts), or "none" if nothing is left."""
    if not cast_role_counts:
        return ""
    remaining = alive_role_counts(cast_role_counts, roster)
    parts = [
        f"{remaining[role]} {role.replace('_', ' ')}"
        for role in _ALIVE_ROLE_ORDER
        if remaining.get(role, 0) > 0
    ]
    return ", ".join(parts) or "none"


def format_day_channel(messages: list[DayChannel]) -> str:
    visible = [m for m in messages if not m.passed]
    if not visible:
        return "No messages yet."
    return "\n".join(f"{m.player}: {m.message}" for m in visible)


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
    # Only append the "vote:" suffix when a vote was cast — GM whiff notes (and any
    # discussion-round entry without a binding vote) carry vote="" and shouldn't render
    # a dangling "vote: ".
    return "\n".join(
        f"[Day {m.day}, Round {m.round}] {m.wolf}: {m.message}."
        + (f"  vote: {m.vote}" if m.vote else "")
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
    visible = [m for m in messages if not m.passed]
    if not visible:
        return "No messages yet."
    return "\n".join(
        f"[Day {m.day}] {m.player} ({roles.get(m.player, 'unknown')}): {m.message}"
        for m in visible
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


def format_retrieved_observations(observations: list[RetrievedObservation]) -> str:
    # Number each memory (1-based, in retrieval-relevance order) so a model asked to reason about a
    # specific memory can reference it by index. Unnumbered, the model cannot reliably track which
    # observation is which and emits verdicts for an arbitrary partial subset (forced_schema_screen).
    if not observations:
        return "No past observations available."
    lines = []
    for idx, item in enumerate(observations, 1):
        obs = item.observation
        parts = [f"Situation: {obs.situation}"]
        if obs.approach:
            parts.append(f"Approach: {obs.approach}")
        if obs.outcome:
            parts.append(f"Outcome: {obs.outcome}")
        lines.append(f"{idx}. " + " | ".join(parts))
    return "\n".join(lines)


def format_strategy_points(strategy_points: list[RetrievedStrategyPoint]) -> str:
    if not strategy_points:
        return "No dynamic strategy points available."
    formatted = []
    for idx, item in enumerate(strategy_points, 1):
        sp = item.strategy_point
        formatted.append(f"[{idx}] {sp.situation} → Action: {sp.action}")
    return "\n".join(formatted)


def format_agent_action(
    action_phase: str,
    message: DayChannel | None = None,
    vote: DayVote | None = None,
) -> str:
    if action_phase == "day_vote":
        return f"Vote target: {vote.votee if vote else '(not captured)'}"
    return f"Message: {message.message if message else '(silent)'}"
