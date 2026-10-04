"""Every schema a seat is asked for, with a short in-character prompt for each and the check its
reply must pass. Shared by the live regression test (tests/live/test_model_structured_output.py)
and the model admission run, so both ask the same questions and judge the answers the same way."""

from __future__ import annotations

from Agents.schemas.output import (
    DayDiscussOutput,
    DaySummaryOutput,
    DayVoteOutput,
    HealerOutput,
    InvestigatorOutput,
    SerialKillerOutput,
    VigilanteOutput,
    WolfNightDiscussOutput,
    WolfNightVoteOutput,
)

OTHERS = ("Mia", "Omar", "Lena", "Theo", "Ivy")
TABLE = (
    "You are Ralph in a 9-player Werewolf game, day 2. Alive: Ralph, " + ", ".join(OTHERS) + ". "
    "Yesterday Omar accused Mia with no evidence and Mia stayed silent. "
)

_PICK = "Name exactly one of the surviving players listed above, never yourself"

# (schema, the role line, the field the game acts on, the non-player answers that field
# allows). The role lines mirror the real prompts' conventions: a day vote may be "abstain"
# and a vigilante may "hold_fire"; every other target names a surviving player. The engine
# also reads "" as no action, so it is allowed wherever a token is.
SEAT_SCHEMAS = [
    (DayDiscussOutput, "You are a villager. Give your discussion contribution.", "message", ()),
    (DayVoteOutput, f"You are a villager. Cast your lynch vote. {_PICK}, or \"abstain\".", "vote_target", ("abstain", "")),
    (WolfNightDiscussOutput, "You are a werewolf; your partner is Theo. Discuss tonight's kill.", "message", ()),
    (WolfNightVoteOutput, f"You are a werewolf; your partner is Theo. Vote for tonight's kill. {_PICK} or Theo.", "vote_target", ()),
    (HealerOutput, f"You are the healer. Choose who to protect tonight. {_PICK}.", "healer_target", ()),
    (InvestigatorOutput, f"You are the investigator. Choose who to investigate tonight. {_PICK}.", "investigator_target", ()),
    (SerialKillerOutput, f"You are the serial killer. Choose tonight's victim. {_PICK}.", "serial_killer_target", ()),
    (VigilanteOutput, f"You are the vigilante with one bullet left. To shoot, {_PICK.lower()}; to hold your fire, answer \"hold_fire\".", "vigilante_target", ("hold_fire", "")),
    (DaySummaryOutput, "You are the game master. Summarise yesterday's discussion and vote for the record.", None, ()),
]
_TARGET_FIELDS = {"vote_target", "healer_target", "investigator_target", "serial_killer_target", "vigilante_target"}


def reply_problem(schema: type, out: object, acted_field: str | None, tokens: tuple[str, ...]) -> str | None:
    """What is wrong with a seat's reply, or None when the game could act on it."""
    if not isinstance(out, schema):
        return f"returned {type(out).__name__}, not {schema.__name__}"
    if acted_field is not None:
        value = getattr(out, acted_field)
        if not isinstance(value, str):
            return f"{acted_field} is {type(value).__name__}"
        passed = schema is DayDiscussOutput and out.pass_turn  # a discussion turn may pass
        if not (tokens or passed) and not value.strip():
            return f"{acted_field} came back empty"
        if acted_field in _TARGET_FIELDS:
            # The one semantic check worth making: a target must be a listed player or an
            # allowed token, so the model read the roster and the instruction rather than
            # inventing a name or a token of its own.
            allowed = set(OTHERS) | set(tokens)
            if value.strip() not in allowed:
                return f"{acted_field}={value!r} not in {sorted(allowed)}"
    if hasattr(out, "reads") and not out.reads:
        return "no player reads"
    return None
