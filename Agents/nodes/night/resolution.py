"""Cross-role night resolution: turns the night's choices into outcomes.

All present night actors act in ONE parallel superstep — the fan-out list comes from
route_night_actors, and every phase edges into NIGHT_RESOLUTION, the barrier. This node hands
the night's choices to the shared layer (Agents.rules.night), which applies every rule at once,
and writes what came of them: the deaths and the dead roster, each actor's private record, the
abilities spent, the neutrals' pick and points, and the morning report with the dead town roles'
disclosures. The public outcome is also committed as the night report, which the wire reads.
"""

from langgraph.runtime import Runtime

from Agents.schemas import DayChannel, DaySummary, DeathRecord
from Agents.schemas.night import NightReport
from Agents.schemas.roles import ROLE_SPECS
from Agents.state import OrchestratorGraph
from Agents.tracing import GraphContext, NightResolutionMetric, langfuse
from Agents.nodes.orchestrator import remove_from_buckets, side_counts
from Agents.rules.night import is_pack_kill, resolve_night
from Agents.rules.night_record import disclosure, night_action_records
from Agents.rules.seats import seat_order


# Public death-announcement flavor per attacker: (verb, subject phrase). Reveals the
# attacker TYPE (so the town learns a lone killer or a vigilante exists once they act) but never
# the attacker's identity.
_ATTACK_FLAVOR = {
    "wolves": ("killed", "the wolves"),
    "serial_killer": ("stabbed", "the serial killer"),
    "vigilante": ("shot", "the vigilante"),
    "sigilist": ("struck down", "a sigil"),
}

_SIDE_WORDS = {"town": "Town", "wolves": "the Wolves", "lone_killer": "the lone killer", "self": "itself"}


def _join(items: list[str]) -> str:
    """Join names into an English list: "a", "a and b", "a, b and c"."""
    if len(items) <= 1:
        return items[0] if items else ""
    return ", ".join(items[:-1]) + " and " + items[-1]


def _spent(state: OrchestratorGraph, choices, outcome) -> dict[str, int]:
    """The limited abilities after tonight: a shot, a sigil and a self-bet are spent on the
    attempt; a conceal only when a body was concealed; the pick once made; nothing by an action
    a block cancelled, by a declined action, or by a turn that is not the ability itself (an
    illusionist carrying the pack's kill, an ordinary bet)."""
    uses = dict(state.get("uses_left", {}))
    for choice in choices:
        spec = ROLE_SPECS[choice.role]
        if spec.uses is None or choice.role not in uses:
            continue
        if choice.kind != spec.night_action:
            continue  # the carrier's kill, hold_fire and the other no-action words
        if choice.actor in outcome.blocked:
            continue  # a blocked action was never carried out, so nothing was spent
        if choice.kind == "conceal" and not outcome.concealed:
            continue
        if choice.kind == "bet" and choice.target != choice.actor:
            continue
        uses[choice.role] = max(0, uses[choice.role] - 1)
    return uses


def night_resolution(state: OrchestratorGraph, runtime: Runtime[GraphContext]):
    """Resolve the whole night: every choice through the shared layer, then what each actor
    learns, what was spent, and what the morning says.

    The BSP barrier after the parallel night fan-out: every actor's choice is already
    committed when this runs. All actions are simultaneous — a killed healer's protection
    still applies, and a killed investigator's check still happened but its result is not
    delivered (a dead player learns nothing from the night it died). Emits the night's single
    metric span.
    """
    current_day = state.get("current_day", 1)
    roles = state["roles"]
    choices = list(state.get("night_choices", []))
    before = side_counts(state)

    outcome = resolve_night(choices, roles, current_day)
    attacks_on, verdicts, deaths = outcome.attacks_on, outcome.verdicts, outcome.deaths
    pack_target = next((c.target for c in choices if is_pack_kill(c)), None)

    metric = NightResolutionMetric(
        day=current_day,
        wolves_target=pack_target,
        wolf_target_role=roles.get(pack_target) if pack_target else None,
        kill_successful=bool(pack_target and pack_target in deaths),
        deaths=deaths,
        wolves_before=before["wolves"],
        town_before=before["town"],
        sk_before=before["lone_killer"],
        choices=[c.__dict__ for c in choices],
    )
    runtime.context["metrics"].night_resolutions.append(metric)
    with langfuse.start_as_current_observation(
        as_type="span",
        name=f"night_resolution_day_{current_day}",
    ) as span:
        span.update(metadata=metric.model_dump())

    state_update: dict = {"uses_left": _spent(state, choices, outcome)}

    # Each actor's private record of what it did and what it may know of the result. A player
    # who died tonight gets no record of tonight (it learns nothing from the night it died).
    tonight_records = [r for r in night_action_records(choices, outcome, roles) if r.actor not in deaths]
    state_update["night_actions"] = tonight_records

    # The neutrals' running state.
    for actor, side in outcome.picks:
        state_update["speculator_pick"] = side
    points = sum(bet.points for bet in outcome.bets)
    if points:
        state_update["fortune_points"] = state.get("fortune_points", 0) + points

    # The dead role's disclosure reads the earlier nights only: a player does not receive its
    # result the night it dies, so the GM reads out nothing from tonight (owner, 2026-10-08).
    earlier_records = list(state.get("night_actions", []))

    lines: list[str] = []
    report_deaths: list[tuple[str, str, list[str]]] = []
    report_saves: list[tuple[str, list[str]]] = []
    dead_roster: list[DeathRecord] = []
    for target in seat_order(attacks_on):
        verdict = verdicts[target]
        if verdict == "immune":
            continue  # silent
        attacker_types = [attack.attacker_type for attack in attacks_on[target]]
        phrase = _join([_ATTACK_FLAVOR[t][1] for t in attacker_types])
        if verdict == "saved":
            # Use a neutral verb so it doesn't read as "killed ... but saved".
            lines.append(f"{target} was attacked by {phrase} but was saved by the healer!")
            report_saves.append((target, attacker_types))
            continue

        # Killed. The announcement names the attacker type, and the role unless concealed.
        verb = _ATTACK_FLAVOR[attacker_types[0]][0] if len(attacker_types) == 1 else "attacked"
        if target in outcome.concealed:
            lines.append(f"{target} was {verb} by {phrase} last night. Their role is hidden by an illusionist.")
            dead_roster.append(DeathRecord(player=target, role="", day=current_day, phase="night", concealed=True))
            report_deaths.append((target, "", attacker_types))
        else:
            role_words = roles[target].replace("_", " ")
            lines.append(f"{target} was {verb} by {phrase} last night. They were a {role_words}.")
            dead_roster.append(DeathRecord(player=target, role=roles[target], day=current_day, phase="night"))
            report_deaths.append((target, roles[target], attacker_types))
            # A revealed town role's record is published with the reveal, before the next death.
            record_line = disclosure(target, roles[target], earlier_records)
            if record_line:
                lines.append(record_line)

    if dead_roster:
        state_update["dead_roster"] = dead_roster
    if not deaths and not report_saves:
        lines.append("No one died last night.")

    # The speculator's pick: the side, never the seat.
    pick = outcome.picks[-1][1] if outcome.picks else None
    if pick:
        lines.append(f"The Speculator has picked {_SIDE_WORDS.get(pick, pick)}.")

    if deaths:
        remove_from_buckets(state_update, state, deaths)

    message = f"Night of day {current_day}: " + " ".join(lines)
    state_update["day_channel"] = [
        DayChannel(
            day=current_day,
            seq=sum(1 for m in state["day_channel"] if m.day == current_day),
            player="game_master",
            message=message,
        )
    ]
    state_update["day_summaries"] = [DaySummary(day=current_day, summary=message, source="game_master")]
    state_update["night_report"] = NightReport(night=current_day, deaths=report_deaths, saves=report_saves, pick=pick)
    return state_update
