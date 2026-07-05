"""Cross-role night resolution: turns the roles' individual night actions into deaths.

The night runs in two groups. GROUP 1 — all the killers plus the healer — acts
first, because their choices determine who dies; a phase is skipped only when its
actor is absent, and the group ends at KILL_RESOLUTION:

    wolves -> healer -> serial killer -> vigilante -> KILL_RESOLUTION

GROUP 2 — the pure-information investigator — runs AFTER kills resolve, and only
if it survived the night (and the game is not already decided): a dead
investigator's result is moot, so its phase is skipped to save the call.
NIGHT_FINALIZE then records the investigation and emits the night's single metric
span (one span carrying both kill and investigation data).
"""

from typing import Literal

from langgraph.runtime import Runtime

from Agents.schemas import DayChannel, DaySummary, InvestigatorResult, WolfChannel
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
    determine_winner,
)


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


def night_kill_resolution(state: OrchestratorGraph, runtime: Runtime[GraphContext]):
    """Resolve the night's kills (wolves / SK / vigilante) jointly.

    Runs BEFORE the investigator phase so a player killed this night does not act
    (the investigator is gated on surviving this resolution — its result would be
    moot). The healer is exempt: it acts in the pre-resolution group, so its
    protection still applies even if the healer itself dies tonight.

    Builds this night's NightResolutionMetric (investigator fields filled later in
    night_finalize) and appends it without emitting the langfuse span yet, so the
    night gets a single span carrying both kill and investigation data.
    """
    current_day = state.get("current_day", 1)
    wolves_target = state.get("wolves_kill_target")
    healer_target = state.get("healer_target")
    serial_killer_target = state.get("serial_killer_target")
    vigilante_target = state.get("vigilante_target")
    sk_player = state.get("serial_killer_player")

    roles = state["roles"]
    wolves_before, town_before, sk_before = _faction_counts(state)

    # Who attacked whom this night (a target may be hit by more than one killer).
    attacks_on: dict[str, list[str]] = {}
    for target, attacker in (
        (wolves_target, "wolves"),
        (serial_killer_target, "serial_killer"),
        (vigilante_target, "vigilante"),
    ):
        if target:
            attacks_on.setdefault(target, []).append(attacker)

    # Resolve protection + SK night-immunity once over the whole set. A player attacked
    # by multiple killers still dies at most once; the immune SK never dies at night and
    # such whiffs are SILENT (announcing them would out the SK).
    def _resolved(target: str) -> str:
        if target == sk_player:
            return "immune"  # silent whiff
        if target == healer_target:
            return "saved"
        return "killed"

    outcomes = {t: _resolved(t) for t in attacks_on}
    deaths = sorted(t for t, o in outcomes.items() if o == "killed")

    kill_successful = bool(wolves_target and wolves_target in deaths)
    healer_saved = bool(wolves_target and wolves_target == healer_target)
    serial_killer_kill_landed = bool(serial_killer_target and serial_killer_target in deaths)
    vigilante_kill_landed = bool(vigilante_target and vigilante_target in deaths)

    # Investigator fields are filled in night_finalize (it acts after this resolution).
    metric = NightResolutionMetric(
        day=current_day,
        wolves_target=wolves_target,
        wolf_target_role=roles.get(wolves_target) if wolves_target else None,
        healer_target=healer_target,
        investigator_target=None,
        investigator_target_role=None,
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

    state_update: dict = {}

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
            _nullify_special_roles(state_update, target, state)

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


def night_finalize(state: OrchestratorGraph, runtime: Runtime[GraphContext]):
    """Record the investigator's result (if it acted) and emit the night's metric span.

    The investigator runs only when it survived night_kill_resolution and the game is
    not already decided, so reaching here with an investigator_target means a live
    investigation. One langfuse span per night carries both kill and investigation data.
    """
    current_day = state.get("current_day", 1)
    investigator_target = state.get("investigator_target")
    roles = state["roles"]

    investigator_update = (
        [
            InvestigatorResult(
                day=current_day,
                player_investigated=investigator_target,
                role_revealed=roles.get(investigator_target, "unknown"),
            )
        ]
        if investigator_target
        else []
    )

    night_metrics = runtime.context["metrics"].night_resolutions
    if night_metrics:
        nr = night_metrics[-1]
        nr.investigator_target = investigator_target
        nr.investigator_target_role = (
            roles.get(investigator_target) if investigator_target else None
        )
        with langfuse.start_as_current_observation(
            as_type="span",
            name=f"night_resolution_day_{current_day}",
        ) as span:
            span.update(metadata=nr.model_dump())

    return {"investigator_results": investigator_update} if investigator_update else {}




def _vigilante_can_act(state: OrchestratorGraph) -> bool:
    """True iff a living vigilante still has a bullet — gates whether its phase runs."""
    return bool(state.get("vigilante_player")) and state.get("vigilante_bullets", 0) > 0


def _next_night_phase(state: OrchestratorGraph, after: str) -> str:
    """Shared night router: the next present actor's phase after `after`, in the fixed
    group-1 order (wolves → healer → SK → vigilante), skipping absent/spent actors;
    falls through to KILL_RESOLUTION when none remain."""
    order = [
        ("wolves", "WOLF_NIGHT_PHASE"),
        ("healer", "HEALER_NIGHT_PHASE"),
        ("serial_killer", "SERIAL_KILLER_NIGHT_PHASE"),
        ("vigilante", "VIGILANTE_NIGHT_PHASE"),
    ]
    present = {
        "healer": bool(state.get("healer_player")),
        "serial_killer": bool(state.get("serial_killer_player")),
        "vigilante": _vigilante_can_act(state),
    }
    start = next(i for i, (key, _) in enumerate(order) if key == after) + 1
    for key, node in order[start:]:
        if present.get(key):
            return node
    return "KILL_RESOLUTION"


def route_after_wolf_night(
    state: OrchestratorGraph,
) -> Literal[
    "HEALER_NIGHT_PHASE",
    "SERIAL_KILLER_NIGHT_PHASE",
    "VIGILANTE_NIGHT_PHASE",
    "KILL_RESOLUTION",
]:
    """Route out of the wolf phase to the next present group-1 actor."""
    return _next_night_phase(state, "wolves")


def route_after_healer_night(
    state: OrchestratorGraph,
) -> Literal[
    "SERIAL_KILLER_NIGHT_PHASE",
    "VIGILANTE_NIGHT_PHASE",
    "KILL_RESOLUTION",
]:
    """Route out of the healer phase to the next present group-1 actor."""
    return _next_night_phase(state, "healer")


def route_after_serial_killer_night(
    state: OrchestratorGraph,
) -> Literal["VIGILANTE_NIGHT_PHASE", "KILL_RESOLUTION"]:
    """Route out of the serial-killer phase to the next present group-1 actor."""
    return _next_night_phase(state, "serial_killer")


def route_after_kill_resolution(
    state: OrchestratorGraph,
) -> Literal["INVESTIGATOR_NIGHT_PHASE", "NIGHT_FINALIZE"]:
    """Group-2 gate: run the investigator only if the game is still undecided and the
    investigator survived the night's kills — otherwise its result is moot, so finalize."""
    if determine_winner(state) is not None:
        return "NIGHT_FINALIZE"
    if state.get("investigator_player"):
        return "INVESTIGATOR_NIGHT_PHASE"
    return "NIGHT_FINALIZE"


