"""Legal-move enforcement for an agent action.

Two halves of one concern — keep the LLM inside the game's rules:
  - ``valid_targets_for_action`` / ``validate_target`` compute who is a legal
    target for an ``output_key`` (surviving players, plus the ``abstain`` and the
    no-action words) and check a chosen target.
  - ``output_schema_with_legal_targets`` rewrites the output schema so the target field
    is a ``Literal[valid_targets]`` the model structurally cannot violate.

A night turn's ``output_key`` is its role's target field (Agents/schemas/roles.py), so the
registry says what the choice is: a player, a word (the speculator's side, the illusionist's
conceal), or a player with the role's no-action word beside it.
"""

from typing import Any, Literal

from pydantic import BaseModel, create_model

from Agents.schemas.roles import PICKABLE_SIDES, ROLE_SPECS, role_for_field

# The pack's kill: the carrier names a non-wolf.
KILL_TARGET = "kill_target"
# Night keys whose choice is a word, not a player: the words offered, in order.
WORD_CHOICES: dict[str, tuple[str, ...]] = {
    "speculator_pick": (*PICKABLE_SIDES, "not_yet"),
    "conceal": ("conceal", "no_conceal"),
}


def validate_target(target: str, valid_targets: list[str], player_id: str) -> str | None:
    """Returns the target if valid, None if not."""
    if target in valid_targets and target != player_id:
        return target
    return None


def valid_targets_for_action(payload: dict[str, Any], output_key: str) -> list[str]:
    """The legal answers for a turn's choice field, in the order the prompt lists them."""
    player_id = payload.get("player_id", "")
    if output_key in WORD_CHOICES:
        return list(WORD_CHOICES[output_key])
    role = role_for_field(output_key)
    if output_key == "day_votes":
        targets = payload.get("surviving_players", [])
    elif output_key == KILL_TARGET or (role is not None and ROLE_SPECS[role].pack):
        # The pack's kill and a wolf's skill are never on a wolf.
        targets = payload.get("surviving_villagers", [])
    elif role is not None:
        targets = payload.get("surviving_players", [])
    else:
        return []
    valid = [target for target in targets if target != player_id]
    # The fortune teller may bet on itself (a self-bet) while it has one left: the one choice
    # that names the actor.
    if role == "fortune_teller" and player_id and (payload.get("uses_left") or 0) > 0:
        valid.append(player_id)
    # Relaxed voting: "abstain" is a sentinel target that competes in the tally; an
    # abstain plurality (or tie) yields no lynch. Dropped on a forced day.
    if output_key == "day_votes" and payload.get("allow_abstain"):
        valid.append("abstain")
    if role is not None and ROLE_SPECS[role].no_action:
        valid.append(ROLE_SPECS[role].no_action)
    return valid


def target_field_of(output_key: str) -> str | None:
    """Which field on the output schema holds the chosen target: "vote_target" for a day vote,
    the key itself for a night turn, None for a message-only turn (day_channel, wolf_channel)."""
    if output_key == "day_votes":
        return "vote_target"
    if output_key == KILL_TARGET or role_for_field(output_key) is not None:
        return output_key
    return None


def output_schema_with_legal_targets(
    output_schema: type[BaseModel],
    output_key: str,
    valid_targets: list[str],
) -> type[BaseModel]:
    """Rebuild ``output_schema`` so its target field is a ``Literal`` of exactly ``valid_targets``.

    Binding the model to that literal makes an illegal target (a dead player, self) structurally
    impossible to generate, rather than something we catch afterwards.
    """
    target_field = target_field_of(output_key)
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
