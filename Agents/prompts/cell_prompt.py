"""v6 per-cell PROMPT composition: turn a cell schema into prompt text. Two pieces only —
the generated dimension menu (WHICH dims, from each mixin Field(description)) and the per-cell
driver/horizon registry (what to LEAD WITH + outcome ordering). The alignment rule (spec
sections 4/5): every surface derives from (1) the per-dimension Field(description) and (2) the
mixin DAG (cell_*_schema_for), so extraction prompt, live-query prompt, embedding, model schema,
and dedup fragments move together. Data validators (e.g. consensus coercion) live in
Agents/memory/validators.py, not here."""

from __future__ import annotations

from pydantic import BaseModel

# Fields that are not situation/outcome DIMENSIONS — excluded from the generated menu (they are
# routing/identity, not described game state).
_NON_MENU_FIELDS = frozenset({"perspective", "action_phase"})


def dimension_menu(schema: type[BaseModel]) -> str:
    """One labeled bullet per dimension field of `schema`, text taken from its `Field(description=)`.
    Auto-tailors per cell (only the cell's fields appear) and cannot drift from the schema."""
    lines: list[str] = []
    for name, field in schema.model_fields.items():
        if name in _NON_MENU_FIELDS:
            continue
        desc = (field.description or "").strip()
        if not desc:
            continue
        lines.append(f"- {name}: {desc}")
    return "\n".join(lines)


def menu_field_names(schema: type[BaseModel]) -> set[str]:
    """The field names the generated menu covers — for the drift-guard test."""
    return {
        n for n, f in schema.model_fields.items()
        if n not in _NON_MENU_FIELDS and (f.description or "").strip()
    }


# The one piece of per-cell prose: what the extractor should LEAD WITH (driver) and how to order the
# outcome (horizon). Keyed by (role, phase-group) where phase-group ∈ {"day","night"}. Spec §2 table.
_IMMEDIATE = "immediate"
_NET = "net"
CELL_DRIVER_HORIZON: dict[tuple[str, str], dict[str, str]] = {
    ("villager", "day"): {"driver": "the hunt — who to trust and who to remove (consensus + target landscape)", "horizon": _IMMEDIATE},
    ("healer", "day"): {"driver": "your own survival and how exposed your role is (forward_exposure), with the hunt secondary", "horizon": _IMMEDIATE},
    ("healer", "night"): {"driver": "protection value × predicted threat to a target (target landscape)", "horizon": _IMMEDIATE},
    ("investigator", "day"): {"driver": "your private findings vs the public read (public/private divergence) and reveal timing", "horizon": _NET},
    ("investigator", "night"): {"driver": "information gain — which check resolves the most uncertainty, and whether to spend one of your limited checks tonight (target landscape, uses left)", "horizon": _IMMEDIATE},
    ("vigilante", "day"): {"driver": "your own survival while you still hold a bullet (forward_exposure)", "horizon": _IMMEDIATE},
    ("vigilante", "night"): {"driver": "shot confidence × cost, given bullets remaining (target landscape, reversibility)", "horizon": _IMMEDIATE},
    ("wolf", "day"): {"driver": "concealment — managing heat and the gap between your private knowledge and the public read (forward_exposure + public/private), accounting for whether your partner is revealed", "horizon": _NET},
    ("wolf", "night"): {"driver": "kill value minus pattern-risk to your cover (target landscape), plus partner coordination", "horizon": _NET},
    ("serial_killer", "day"): {"driver": "solo concealment — managing heat and the public/private gap (forward_exposure + public/private)", "horizon": _NET},
    ("serial_killer", "night"): {"driver": "survival and faction-balance — who to remove to reach a last-standing win (target landscape)", "horizon": _NET},
    # The ten-seat roles (plan 2026-10-11 §9). A driver names the decision, never the answer or its grade.
    ("sentinel", "day"): {"driver": "your private watch results vs the public read (public/private divergence), and when and how to share them", "horizon": _NET},
    ("sentinel", "night"): {"driver": "which door to watch so that a visit there matters (a likely victim, a suspect), and whether to spend one of your limited watches tonight (target landscape, uses left)", "horizon": _IMMEDIATE},
    ("trailseer", "day"): {"driver": "your private follow results vs the public read (public/private divergence), and when and how to share them", "horizon": _NET},
    ("trailseer", "night"): {"driver": "whose trail would confirm or clear a suspect (target landscape)", "horizon": _IMMEDIATE},
    ("sigilist", "day"): {"driver": "your own survival while you still hold a sigil (forward_exposure)", "horizon": _IMMEDIATE},
    ("sigilist", "night"): {"driver": "predicting who will attack tonight against the cost of a sigil, given sigils left; a sigil on a player who attacks strikes them, the vigilante included (target landscape, uses left)", "horizon": _IMMEDIATE},
    ("chanteuse", "day"): {"driver": "concealment — managing heat and the gap between your private knowledge and the public read (forward_exposure + public/private), accounting for whether your partner is revealed", "horizon": _NET},
    ("chanteuse", "night"): {"driver": "which town player's night action to cancel tonight (who is likely to protect, check, watch, follow, place a sigil or shoot), plus the pack's kill and partner coordination (target landscape), and what the night's private results revealed (an attack on an immune player identifies the lone killer) and whether it was used", "horizon": _IMMEDIATE},
    ("illusionist", "day"): {"driver": "concealment — managing heat and the gap between your private knowledge and the public read (forward_exposure + public/private), accounting for whether your partner is revealed", "horizon": _NET},
    ("illusionist", "night"): {"driver": "whether tonight's victim is worth a conceal (what their revealed role and record would tell the town), given conceals left, plus the pack's kill and partner coordination (target landscape, uses left), and what the night's private results revealed (an attack on an immune player identifies the lone killer) and whether it was used", "horizon": _IMMEDIATE},
    ("necromancer", "day"): {"driver": "solo concealment — managing heat and the public/private gap (forward_exposure + public/private)", "horizon": _NET},
    ("necromancer", "night"): {"driver": "which dead body's ability to use, on whom, and when to stay put, knowing an attack reads Suspicious to an investigator that night (target landscape)", "horizon": _NET},
    ("speculator", "day"): {"driver": "before your pick, reading which side is ahead; after it, helping the side you picked without exposing yourself (consensus + heat)", "horizon": _NET},
    ("speculator", "night"): {"driver": "when to make your one pick and which side, from how the board is trending; dying unpicked is a loss (target landscape)", "horizon": _NET},
    ("fortune_teller", "day"): {"driver": "your own survival and reading who is likely to die next (heat)", "horizon": _IMMEDIATE},
    ("fortune_teller", "night"): {"driver": "predicting tonight's death (and the victim's role), and when to bet on yourself instead, given self-bets left (target landscape, uses left)", "horizon": _IMMEDIATE},
}

_HORIZON_TEXT = {
    _IMMEDIATE: (
        "HORIZON — immediate-first: lead the outcome with what happened that turn / next step, then "
        "note the eventual game result. (impact_on_final_game_outcome still records the NET effect.)"
    ),
    _NET: (
        "HORIZON — net-first: lead the outcome with the end-of-game consequence, then the immediate "
        "effect. State an end-of-game consequence only when something in the record links it to the move, "
        "and say what links it; a later loss that merely followed the move is not a consequence of it. "
        "With no supported link, the end-of-game effect is 'unclear'."
    ),
}


def _phase_group(action_phase: str) -> str:
    return "night" if action_phase == "night_action" else "day"


def cell_driver_horizon(role: str, action_phase: str) -> str:
    """The per-cell 'lead with X / horizon' block, or '' if the cell isn't registered."""
    entry = CELL_DRIVER_HORIZON.get((role, _phase_group(action_phase)))
    if not entry:
        return ""
    return (
        f"DRIVER — for this cell, lead with: {entry['driver']}.\n"
        f"{_HORIZON_TEXT[entry['horizon']]}"
    )
