"""Every schema a seat is asked for, with a short in-character prompt for each and the check its
reply must pass. Shared by the live regression test (tests/live/test_model_structured_output.py)
and the model admission run, so both ask the same questions and judge the answers the same way."""

from __future__ import annotations

from Agents.schemas.lineup_output import (
    carrier_output,
    day_discuss_output,
    day_vote_output,
    night_output,
    wolf_chat_output,
)
from Agents.schemas.output import DaySummaryOutput
from Agents.schemas.roles import LONE_KILLER_ROLES, NEUTRAL_ROLES, ROLE_SPECS, lineup, roles

OTHERS = ("Mia", "Omar", "Lena", "Theo", "Ivy")
TABLE = (
    "You are Ralph in a 10-player Werewolf game, day 2. Alive: Ralph, " + ", ".join(OTHERS) + ". "
    "Yesterday Omar accused Mia with no evidence and Mia stayed silent. "
)

_PICK = "Name exactly one of the surviving players listed above, never yourself"
LINEUP = lineup(LONE_KILLER_ROLES[0], NEUTRAL_ROLES[0])
"""The lineup the day and pack schemas are filled with."""


def _lineup_with(role: str) -> list[str]:
    """A lineup that deals this role (its drawn seat comes out as the role)."""
    return lineup(role if role in LONE_KILLER_ROLES else LONE_KILLER_ROLES[0],
                  role if role in NEUTRAL_ROLES else NEUTRAL_ROLES[0])


# Each role's night ask: (the role line, the non-player answers its field allows). The role lines
# mirror the real prompts' conventions: a role with a no-action word may answer it; every other
# target names a surviving player.
_NIGHT_LINES = {
    "investigator": f"You are the investigator. Choose who to investigate tonight. {_PICK}.",
    "sentinel": f"You are the sentinel. Choose whose house to watch tonight. {_PICK}.",
    "trailseer": f"You are the trailseer. Choose whom to follow tonight. {_PICK}.",
    "vigilante": f"You are the vigilante with one bullet left. To shoot, {_PICK.lower()}; to hold your fire, answer \"hold_fire\".",
    "sigilist": f"You are the sigilist with one sigil left. To set it, {_PICK.lower()}; to keep it, answer \"keep_sigil\".",
    "healer": f"You are the healer. Choose who to protect tonight. {_PICK}.",
    "chanteuse": f"You are the chanteuse, a wolf; your partner is Theo. Choose whom to block tonight. {_PICK}.",
    "illusionist": "You are the illusionist, a wolf; your partner is Theo. Choose whether to conceal the role of tonight's kill.",
    "serial_killer": f"You are the serial killer. Choose tonight's victim. {_PICK}.",
    "necromancer": f"You are the necromancer. The dead are Ada (healer) and Ben (vigilante). To act through one of them, {_PICK.lower()} and name the body; to stay put, answer \"stay_put\" with body \"none\".",
    "speculator": "You are the speculator. Pick the side you think will win, or wait.",
    "fortune_teller": f"You are the fortune teller. Bet on who dies tonight. {_PICK}, and name their role if you can.",
}

# (schema, the role line, the field the game acts on, the non-player answers that field
# allows). A day vote may be "abstain"; a role's no-action word is allowed on its field. The
# engine also reads "" as no action, so it is allowed wherever a token is.
SEAT_SCHEMAS = [
    (day_discuss_output(LINEUP), "You are the sentinel. Give your discussion contribution.", "message", ()),
    (day_vote_output(LINEUP), f"You are the sentinel. Cast your lynch vote. {_PICK}, or \"abstain\".", "vote_target", ("abstain", "")),
    (wolf_chat_output(LINEUP), "You are the chanteuse, a wolf; your partner is Theo. Discuss tonight's kill.", "message", ()),
    (carrier_output(LINEUP), f"You are the chanteuse, a wolf; your partner is Theo. You carry the pack's kill tonight. {_PICK} other than Theo.", "kill_target", ()),
    *[
        (night_output(role, _lineup_with(role)), _NIGHT_LINES[role], ROLE_SPECS[role].target_field,
         (ROLE_SPECS[role].no_action, "") if ROLE_SPECS[role].no_action else ())
        for role in roles
    ],
    (DaySummaryOutput, "You are the game master. Summarise yesterday's discussion and vote for the record.", None, ()),
]
# The fields that name a player: the vote, the carrier's kill, and every night field but the
# illusionist's conceal and the speculator's pick (those choose a word, not a player).
_TARGET_FIELDS = {"vote_target", "kill_target"} | {
    spec.target_field for name, spec in ROLE_SPECS.items()
    if not spec.retired and spec.target_field not in ("conceal", "speculator_pick")
}


def reply_problem(schema: type, out: object, acted_field: str | None, tokens: tuple[str, ...]) -> str | None:
    """What is wrong with a seat's reply, or None when the game could act on it."""
    if not isinstance(out, schema):
        return f"returned {type(out).__name__}, not {schema.__name__}"
    if acted_field is not None:
        value = getattr(out, acted_field)
        if not isinstance(value, str):
            return f"{acted_field} is {type(value).__name__}"
        passed = getattr(out, "pass_turn", False)  # a discussion or pack chat turn may pass
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
