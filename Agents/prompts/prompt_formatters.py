from Agents.rules.board_clocks import alive_role_counts
from Agents.schemas import RetrievedObservation, RetrievedStrategyPoint
from Agents.schemas.game_events import (
    DayChannel,
    DaySummary,
    DayVote,
    DeathRecord,
    InvestigatorResult,
    NightActionRecord,
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


def format_day_channel(messages: list[DayChannel], viewer: str | None = None) -> str:
    """The public transcript. Passes are hidden. `viewer` also sees its own held-back drafts,
    marked as never seen by anyone: without the mark, an agent whose message the novelty gate
    withheld could go on believing (and noting) that it had said it (audit 2026-10-03, finding 2)."""
    lines = []
    for m in messages:
        if not m.passed:
            lines.append(f"{m.player}: {m.message}")
        elif viewer and m.player == viewer and m.gated and m.gated_candidate:
            lines.append(
                f"[{viewer}, held back: you tried to say this, but it repeated what had already been "
                f"said, so no one else saw it] {m.gated_candidate}"
            )
    return "\n".join(lines) if lines else "No messages yet."


def format_day_channel_for_day(messages: list[DayChannel], current_day: int, viewer: str | None = None) -> str:
    return format_day_channel([m for m in messages if m.day == current_day], viewer)


def format_day_summaries(summaries: list[DaySummary], before_day: int | None = None) -> str:
    """Earlier days, as agents see them, in three blocks of decreasing authority:

    1. the game master's record: the exact night and vote announcements;
    2. the claims on record: every role claim and claimed result, per player, across days, built by
       code from the summaries' structured fields;
    3. the discussion summaries: the summariser's account of what players said and argued.

    The labels carry the hierarchy. A claim a summary repeats is never set beside an announcement as
    an equal (audit 2026-10-03, finding 5; the case in discussion_evidence.md §6.4)."""
    selected = [s for s in summaries if before_day is None or s.day < before_day]
    if not selected:
        return "No previous days yet."
    record = [s for s in selected if s.source == "game_master"]
    discussion = [s for s in selected if s.source != "game_master"]
    blocks = [
        "-- The game master's record (exact; it outranks anything a player or a summary says) --\n"
        + ("\n".join(f"[Day {s.day}] {s.summary.strip()}" for s in record) or "Nothing announced yet.")
    ]
    claims = format_claims_on_record(discussion)
    if claims:
        blocks.append(
            "-- Claims on record (what players have claimed so far; claims, not facts) --\n" + claims
        )
    blocks.append(
        "-- Discussion summaries (a summariser's account of what players said and argued; "
        "anything a player claimed in them is a claim, not a fact) --\n"
        + ("\n\n".join(f"[Day {s.day}]\n{s.summary}" for s in discussion) or "None yet.")
    )
    return "\n\n".join(blocks)


def format_claims_on_record(discussion: list[DaySummary]) -> str:
    """Each player's role claims and claimed results across days, from the summaries' structured
    `role_claims` (results only where the summary recorded them). "" when nobody has claimed."""
    by_player: dict[str, list[str]] = {}
    for s in discussion:
        for c in (s.structured or {}).get("role_claims") or []:
            player, role = c.get("player"), c.get("claimed_role")
            if not player or not role:
                continue
            entry = f"day {s.day}: claimed {role}"
            status = c.get("status")
            if status and status not in ("new", "repeated"):
                entry += f" ({status})"
            results = [
                (f"night {r['night']}: " if r.get("night") else "") + f"{r['target']} {r['result']}"
                for r in c.get("claimed_results") or []
                if r.get("target") and r.get("result")
            ]
            if results:
                entry += " — results claimed: " + "; ".join(results)
            by_player.setdefault(player, []).append(entry)
    return "\n".join(f"{p}: " + " | ".join(entries) for p, entries in by_player.items())


def format_night_actions(records: list[NightActionRecord], current_day: int | None = None) -> str:
    """The actor's own night record, one line per night, written by the engine."""
    if not records:
        return "Nothing yet."
    verbs = {"protect": "you protected", "shoot": "you shot", "kill": "you attacked"}
    lines = []
    for r in records:
        night = f"Night {r.day}" + (" (last night)" if current_day is not None and r.day == current_day - 1 else "")
        if r.action == "hold_fire":
            lines.append(f"{night}: you held your fire.")
            continue
        verb = "your pack attacked" if r.actor == "wolves" else verbs[r.action]
        lines.append(f"{night}: {verb} {r.target}. {r.outcome}")
    return "\n".join(lines)


def format_wolf_channel(messages: list[WolfChannel]) -> str:
    visible = [message for message in messages if not message.passed]
    if not visible:
        return "No messages yet."
    # Talk entries carry a message and vote="" (also GM whiff notes); binding-vote entries
    # carry a vote and message="". Technical passes are observer-only and filtered above.
    # Render each visible entry without the other's dangling suffix.
    return "\n".join(
        f"[Day {m.day}, Round {m.round}] {m.wolf} votes: {m.vote}"
        if not m.message
        else f"[Day {m.day}, Round {m.round}] {m.wolf}: {m.message}."
        + (f"  vote: {m.vote}" if m.vote else "")
        for m in visible
    )


def format_investigator_results(results: list[InvestigatorResult], current_day: int | None = None) -> str:
    """The investigator's own checks, each named as a night and as the player's own action.

    The old line, "Day 3: player_5 was revealed as healer", read like a public death reveal
    (the same word, and that night's target had died and been revealed). Replaying a live turn
    20 times, the investigator invented an unchecked result in 20 of 20 samples on that wording
    and in 0 of 20 on this one (evidence/game_play_enhancement/discussion_evidence.md §6.2).
    `current_day` tags the previous night's check as "(last night)"; None leaves it untagged.
    """
    if not results:
        return "No investigations yet."
    return "\n".join(
        f"Night {r.day}{' (last night)' if current_day is not None and r.day == current_day - 1 else ''}: "
        f"you investigated {r.player_investigated}, who is the {r.role_revealed.replace('_', ' ')}"
        for r in results
    )

def format_night_actions_postgame(records: list[NightActionRecord], roles: dict[str, str]) -> str:
    """Every night actor's record, labelled with its role, for the post-game extractor."""
    if not records:
        return "No night actions recorded."
    lines = []
    for r in records:
        who = "the wolves" if r.actor == "wolves" else f"{r.actor} ({roles.get(r.actor, 'unknown')})"
        act = "held fire" if r.action == "hold_fire" else f"{r.action} {r.target}"
        lines.append(f"Night {r.day}: {who} {act}. {r.outcome}")
    return "\n".join(lines)


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
