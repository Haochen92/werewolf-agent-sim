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


def _target_field_for_output_key(output_key: str) -> str | None:
    if output_key in {"day_votes", "wolf_channel"}:
        return "vote_target"
    if output_key in {
        "healer_target",
        "investigator_target",
        "serial_killer_target",
        "vigilante_target",
    }:
        return output_key
    return None


def _with_dynamic_target_enum(
    output_schema: type[BaseModel],
    output_key: str,
    valid_targets: list[str],
) -> type[BaseModel]:
    target_field = _target_field_for_output_key(output_key)
    if not target_field or not valid_targets:
        return output_schema

    target_literal = Literal[tuple(valid_targets)]
    fields: dict[str, tuple[Any, Any]] = {}
    for field_name, field in output_schema.model_fields.items():
        annotation = target_literal if field_name == target_field else field.annotation
        default = ... if field.is_required() else field.default
        fields[field_name] = (annotation, default)

    return create_model(
        f"{output_schema.__name__}_{output_key}_TargetEnum",
        **fields,
    )


