"""v6 per-cell prompt composition — the single place that turns a cell schema into prompt text.

The alignment rule (spec §4/§5): every surface derives from two sources of truth —
  1. per-dimension guidance = the `Field(description=)` on each mixin (written once), and
  2. which dims a cell has = the mixin DAG (`cell_*_schema_for`).
`dimension_menu` GENERATES the prompt's field list from the cell schema's `Field(description=)`, so the
extraction prompt, the live-query prompt, the embedding (`compose_situation_embed`), the model schema
(`with_structured_output`), and the dedup fragments all move together — no hand-maintained dim list can
drift. The only genuinely per-cell prose is the driver + horizon (spec §2/§6), held in a registry here.
"""

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
    ("investigator", "night"): {"driver": "information gain — which check resolves the most uncertainty (target landscape)", "horizon": _IMMEDIATE},
    ("vigilante", "day"): {"driver": "your own survival while you still hold a bullet (forward_exposure)", "horizon": _IMMEDIATE},
    ("vigilante", "night"): {"driver": "shot confidence × cost, given bullets remaining (target landscape, reversibility)", "horizon": _IMMEDIATE},
    ("wolf", "day"): {"driver": "concealment — managing heat and the gap between your private knowledge and the public read (forward_exposure + public/private), accounting for whether your partner is revealed", "horizon": _NET},
    ("wolf", "night"): {"driver": "kill value minus pattern-risk to your cover (target landscape), plus partner coordination", "horizon": _NET},
    ("serial_killer", "day"): {"driver": "solo concealment — managing heat and the public/private gap (forward_exposure + public/private)", "horizon": _NET},
    ("serial_killer", "night"): {"driver": "survival and faction-balance — who to remove to reach a last-standing win (target landscape)", "horizon": _NET},
}

_HORIZON_TEXT = {
    _IMMEDIATE: (
        "HORIZON — immediate-first: lead the outcome with what happened that turn / next step, then "
        "note the eventual game result. (impact_on_final_game_outcome still records the NET effect.)"
    ),
    _NET: (
        "HORIZON — net-first: lead the outcome with the end-of-game consequence (a move that helped in "
        "the moment but cost the game later is a NET NEGATIVE — say so and name the causal chain), then "
        "the immediate effect."
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
