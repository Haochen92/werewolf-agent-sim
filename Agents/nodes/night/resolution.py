"""Cross-role night resolution: turns the roles' individual night actions into outcomes.

All present night actors (wolves / healer / SK / vigilante / investigator) act in ONE
parallel superstep — the fan-out list comes from check_game_end_day, and every phase
edges into NIGHT_RESOLUTION, the barrier, which resolves the kills AND the investigation
(delivered only if the investigator survived) in one node with one metric span.
"""

from langgraph.runtime import Runtime

from Agents.schemas import DayChannel, DaySummary, DeathRecord, InvestigatorResult, WolfChannel
from Agents.state import (
    OrchestratorGraph,
)



from Agents.tracing import (
    GraphContext,
    NightResolutionMetric,
    langfuse,
)

from Agents.nodes.orchestrator import (
    _faction_counts,
    _nullify_special_roles,
)
from Agents.rules.resolution import collect_attacks, resolve_attacks


# Public death-announcement flavor per attacker: (verb, subject phrase). Reveals the
# attacker TYPE (so the town learns an SK/vigilante exists once they act) but never the
# attacker's identity.
_ATTACK_FLAVOR = {
    "wolves": ("killed", "the wolves"),
    "serial_killer": ("stabbed", "the serial killer"),
    "vigilante": ("shot", "the vigilante"),
}


def _join(items: list[str]) -> str:
    """Join names into an English list: "a", "a and b", "a, b and c"."""
    if len(items) <= 1:
        return items[0] if items else ""
    return ", ".join(items[:-1]) + " and " + items[-1]


def night_resolution(state: OrchestratorGraph, runtime: Runtime[GraphContext]):
    """Resolve the whole night: kills (wolves / SK / vigilante) plus the investigation.

    The BSP barrier after the parallel night fan-out: every actor's target is already
    committed when this runs. All actions are simultaneous — a killed healer's protection
    still applies, and a killed investigator's probe still happened but is NOT delivered
    (a dead investigator learns nothing). A probe on a player who died the same night IS
    delivered: the role is fixed truth, redundant with the dawn reveal. Emits the night's
    single metric span (kill + investigation data; the metric records the act even when
    the result goes undelivered).
    """
    current_day = state.get("current_day", 1)
    wolves_target = state.get("wolves_kill_target")
    healer_target = state.get("healer_target")
    serial_killer_target = state.get("serial_killer_target")
    vigilante_target = state.get("vigilante_target")
    sk_player = state.get("serial_killer_player")

    roles = state["roles"]
    wolves_before, town_before, sk_before = _faction_counts(state)

    # The shared kernel (Agents.rules.resolution) owns attack collection + precedence —
    # the wire translator calls the SAME functions, so game and wire cannot drift.
    attacks_on = collect_attacks(wolves_target, serial_killer_target, vigilante_target)
    outcomes = resolve_attacks(attacks_on, healer_target, sk_player)
    deaths = sorted(t for t, o in outcomes.items() if o == "killed")

    kill_successful = bool(wolves_target and wolves_target in deaths)
    healer_saved = bool(wolves_target and wolves_target == healer_target)
    serial_killer_kill_landed = bool(serial_killer_target and serial_killer_target in deaths)
    vigilante_kill_landed = bool(vigilante_target and vigilante_target in deaths)

    investigator_target = state.get("investigator_target")
    metric = NightResolutionMetric(
        day=current_day,
        wolves_target=wolves_target,
        wolf_target_role=roles.get(wolves_target) if wolves_target else None,
        healer_target=healer_target,
        investigator_target=investigator_target,
        investigator_target_role=roles.get(investigator_target) if investigator_target else None,
        kill_successful=kill_successful,
        healer_saved=healer_saved,
        serial_killer_target=serial_killer_target,
        serial_killer_target_role=roles.get(serial_killer_target) if serial_killer_target else None,
        vigilante_target=vigilante_target,
        vigilante_target_role=roles.get(vigilante_target) if vigilante_target else None,
        serial_killer_kill_landed=serial_killer_kill_landed,
        vigilante_kill_landed=vigilante_kill_landed,
        deaths=deaths,
        wolves_before=wolves_before,
        town_before=town_before,
        sk_before=sk_before,
    )
    runtime.context["metrics"].night_resolutions.append(metric)
    with langfuse.start_as_current_observation(
        as_type="span",
        name=f"night_resolution_day_{current_day}",
    ) as span:
        span.update(metadata=metric.model_dump())

    state_update: dict = {}

    # Survival-gated delivery: the probe happened regardless (it's on the metric above),
    # but only a living investigator receives the result.
    investigator = state.get("investigator_player")
    if investigator_target and investigator and investigator not in deaths:
        state_update["investigator_results"] = [
            InvestigatorResult(
                day=current_day,
                player_investigated=investigator_target,
                role_revealed=roles.get(investigator_target, "unknown"),
            )
        ]

    # The vigilante spends a bullet whenever it takes a shot, even if healed or whiffed.
    if vigilante_target:
        state_update["vigilante_bullets"] = max(0, state.get("vigilante_bullets", 0) - 1)

    # A shot at the night-immune target (the SK) doesn't kill, but the vigilante learns
    # the target was immune — a private, reliable confirmation of the serial killer.
    # (A shot stopped by a heal does NOT trigger this, so there is no false positive.)
    if vigilante_target and outcomes.get(vigilante_target) == "immune":
        state_update["vigilante_results"] = [
            f"Night of day {current_day}: you shot {vigilante_target}, but they were unharmed "
            f"— immune to night kills, which confirms {vigilante_target} is the serial killer."
        ]

    # A wolf kill on the night-immune target (the SK) is publicly SILENT — announcing it would
    # out the SK — so the wolves can only infer the whiff from absence. Mirror the vigilante's
    # private confirmation: drop a game-master note into the wolf channel so BOTH wolves learn
    # the immune target is the serial killer. (A heal gives outcome "saved", not "immune", so a
    # healed target never triggers this — no false positive; the save is announced publicly.)
    if wolves_target and outcomes.get(wolves_target) == "immune":
        state_update["wolf_channel"] = [
            WolfChannel(
                day=current_day,
                round=2,
                wolf="game_master",
                message=(
                    f"Night of day {current_day}: your kill on {wolves_target} failed — "
                    f"{wolves_target} was unharmed, immune to night kills, which confirms "
                    f"{wolves_target} is the serial killer."
                ),
                vote="",
            )
        ]

    lines: list[str] = []
    announced_save = False
    dead_roster: list[DeathRecord] = []
    for target in sorted(attacks_on):
        outcome = outcomes[target]
        if outcome == "immune":
            continue  # silent
        attackers = attacks_on[target]
        phrase = _join([_ATTACK_FLAVOR[a][1] for a in attackers])
        if outcome == "saved":
            # Use a neutral verb so it doesn't read as "killed ... but saved".
            lines.append(f"{target} was attacked by {phrase} but was saved by the healer!")
            announced_save = True
        else:  # killed
            verb = _ATTACK_FLAVOR[attackers[0]][0] if len(attackers) == 1 else "attacked"
            lines.append(
                f"{target} was {verb} by {phrase} last night. They were a {roles[target]}."
            )
            # The announcement above publicly reveals the dead player's role, so record it
            # on the deterministic dead roster (death order = sorted attack order this night).
            dead_roster.append(
                DeathRecord(player=target, role=roles[target], day=current_day, phase="night")
            )
            _nullify_special_roles(state_update, target, state)

    if dead_roster:
        state_update["dead_roster"] = dead_roster

    if not deaths and not announced_save:
        lines.append("No one died last night.")

    if deaths:
        state_update["surviving_wolves"] = [
            p for p in state["surviving_wolves"] if p not in deaths
        ]
        state_update["surviving_villagers"] = [
            p for p in state["surviving_villagers"] if p not in deaths
        ]

    message = f"Night of day {current_day}: " + " ".join(lines)
    state_update["day_channel"] = [
        DayChannel(
            day=current_day,
            seq=sum(1 for m in state["day_channel"] if m.day == current_day),
            player="game_master",
            message=message,
        )
    ]
    state_update["day_summaries"] = [DaySummary(day=current_day, summary=message)]
    return state_update
