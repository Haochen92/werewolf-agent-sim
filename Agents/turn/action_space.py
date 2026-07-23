"""Legal-move enforcement for an agent action.

Two halves of one concern — keep the LLM inside the game's rules:
  - ``_valid_targets_for_action`` / ``_validate_target`` compute who is a legal
    target for an ``output_key`` (surviving players/villagers, plus the
    ``abstain`` and ``hold_fire`` sentinels) and check a chosen target.
  - ``_with_dynamic_target_enum`` rewrites the output schema so the target field
    is a ``Literal[valid_targets]`` the model structurally cannot violate.
"""

from typing import Any, Literal

from pydantic import BaseModel, create_model


def _validate_target(target: str, valid_targets: list[str], player_id: str) -> str | None:
    """Returns the target if valid, None if not."""
    if target in valid_targets and target != player_id:
        return target
    return None


def _valid_targets_for_action(payload: dict[str, Any], output_key: str) -> list[str]:
    player_id = payload.get("player_id", "")
    if output_key == "wolf_channel":
        targets = payload.get("surviving_villagers", [])
    elif output_key in {
        "day_votes",
        "healer_target",
        "investigator_target",
        "serial_killer_target",
        "vigilante_target",
    }:
        targets = payload.get("surviving_players", [])
    else:
        return []
    valid = [target for target in targets if target != player_id]
    # Relaxed voting: "abstain" is a sentinel target that competes in the tally; an
    # abstain plurality (or tie) yields no lynch. Dropped on a forced day.
    if output_key == "day_votes" and payload.get("allow_abstain"):
        valid.append("abstain")
    # The vigilante may hold fire to save a bullet (the SK is compulsive — no sentinel).
    if output_key == "vigilante_target":
        valid.append("hold_fire")
    return valid


# Which field on the output schema holds the chosen target, per output_key. Day votes and the
# wolf-night channel name it "vote_target"; every night role names the field after its own key.
_TARGET_FIELD_BY_OUTPUT_KEY = {
    "day_votes": "vote_target",
    "wolf_channel": "vote_target",
    "healer_target": "healer_target",
    "investigator_target": "investigator_target",
    "serial_killer_target": "serial_killer_target",
    "vigilante_target": "vigilante_target",
}


def _with_dynamic_target_enum(
    output_schema: type[BaseModel],
    output_key: str,
    valid_targets: list[str],
) -> type[BaseModel]:
    """Rebuild ``output_schema`` so its target field is a ``Literal`` of exactly ``valid_targets``.

    Binding the model to that literal makes an illegal target (a dead player, self) structurally
    impossible to generate, rather than something we catch afterwards.
    """
    target_field = _TARGET_FIELD_BY_OUTPUT_KEY.get(output_key)
    if target_field is None:
        # This action names no target (day discussion) — nothing to constrain; the schema is
        # already correct as-is.
        return output_schema

    if not valid_targets:
        # A target action reached with an empty legal set means the win-condition check failed to
        # end the game first (e.g. no surviving villagers = wolves already won). Never normal —
        # fail here, at the broken invariant, not later as an IndexError in the random fallback.
        raise ValueError(
            f"{output_key}: no legal targets — the win-condition check should have ended "
            f"the game before this action ran"
        )

    # Subclass the original schema, overriding ONLY the target field's type with a Literal of the
    # legal set. Reusing the original FieldInfo keeps the field's description, validators, and
    # required status; every other field and the model config is inherited unchanged.
    target_literal = Literal[tuple(valid_targets)]
    original_target = output_schema.model_fields[target_field]
    return create_model(
        f"{output_schema.__name__}_{output_key}_TargetEnum",
        __base__=output_schema,
        **{target_field: (target_literal, original_target)},
    )


