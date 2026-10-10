"""Structured-output schemas of the ten-seat game: what each turn answers with.

⚠️ MODEL-VISIBLE, like ``output.py``: every ``Field(description=...)`` here is sent to the model.
Never add a class docstring (it folds into the JSON schema); comments only.

Three fields list role names: the role guess in a read, the role a player claims in a discussion
message, and the role the fortune teller names on a bet. A game must name only the roles it dealt
(a game that drew the speculator never shows the fortune teller), so each class below is written
once with its role list left open, as ``ReadRole`` or ``NamedRole``, and the functions at the
bottom fill it with the dealt roles. The field order verdicts -> reads -> strategy -> action
is the tested lever (output.py, PlayerRead) and is kept on every turn.
"""

from __future__ import annotations

import json
from typing import Generic, Literal, TypeVar

from pydantic import Field, field_validator

from Agents.schemas.game_events import AddressedTarget
from Agents.schemas.output import LenientToolCallModel, MemoryVerdict, StrategyVerdict

ReadRole = TypeVar("ReadRole")
"""The role guess in a read: "unclear" or a dealt role."""
NamedRole = TypeVar("NamedRole")
"""A role a player names: "none" or a dealt role (a claim, the fortune teller's bet)."""


class LineupModel(LenientToolCallModel):
    # Base for every schema in this module. Pydantic names a filled class after its roles
    # ("PlayerRead[Literal['unclear', 'investigator', ...]]"); the model must see the plain class
    # name instead, as the tool name and as the key of each nested definition.

    @classmethod
    def model_parametrized_name(cls, params) -> str:
        return cls.__name__

    @classmethod
    def model_json_schema(cls, *args, **kwargs) -> dict:
        schema = super().model_json_schema(*args, **kwargs)
        renames = {key: d["title"] for key, d in schema.get("$defs", {}).items() if key != d.get("title", key)}
        if not renames:
            return schema
        text = json.dumps(schema)
        for key, title in renames.items():
            text = text.replace(f'"#/$defs/{key}"', f'"#/$defs/{title}"')
        schema = json.loads(text)
        schema["$defs"] = {renames.get(key, key): d for key, d in schema["$defs"].items()}
        return schema


# --- The parts every acting turn opens with ---


class PlayerRead(LineupModel, Generic[ReadRole]):
    player: str = Field(description="A living player's ID (never your own).")
    why: str = Field(description="One line of evidence for this read; write 'unchanged' if your read has not moved.")
    suspected_role: ReadRole = Field(description="Your best guess of this player's role; 'unclear' if you cannot tell.")
    confidence: Literal["low", "high"] = Field(description="How sure you are.")

    # "medium" is the standard off-menu invention on tool-calling backends; fold it to "low"
    # (as output.PlayerRead does). Validators never enter the JSON schema.
    @field_validator("confidence", mode="before")
    @classmethod
    def _fold_medium_to_low(cls, value):
        if isinstance(value, str) and value.strip().lower() == "medium":
            return "low"
        return value


class TurnOutput(LineupModel, Generic[ReadRole]):
    strategy_verdicts: list[StrategyVerdict] = Field(
        default_factory=list,
        description="One verdict per numbered strategy point shown, in order; empty list if none shown.",
    )
    memory_applicability: list[MemoryVerdict] = Field(
        default_factory=list,
        description="One verdict per numbered observation shown, in order; empty list if none shown.",
    )
    reads: list[PlayerRead[ReadRole]] = Field(description="One read per living player other than yourself.")
    updated_strategy: str


# --- Day ---


class DayDiscussOutput(TurnOutput[ReadRole], Generic[ReadRole, NamedRole]):
    pass_turn: bool = Field(
        description="True only if you have nothing new to add and decline to speak. False when answering/defending.",
    )
    message: str
    claim: NamedRole = Field(description='The role you claim in this message, outright or by describing its action as yours ("I watched player_5" claims sentinel), or "none" if you make no claim.')
    addressed_targets: list[AddressedTarget] = Field(
        description="List of targets addressed in the discussion. Empty list if none.",
    )


class DayVoteOutput(TurnOutput[ReadRole], Generic[ReadRole]):
    vote_target: str = Field(description='exact player_id from the surviving players list, or "abstain"')


# --- Night: one per role, on the field its card names (NightWords.target_field) ---


class InvestigatorOutput(TurnOutput[ReadRole], Generic[ReadRole]):
    investigator_target: str = Field(description='exact player_id from the surviving players list, or "no_check"')


class SentinelOutput(TurnOutput[ReadRole], Generic[ReadRole]):
    sentinel_target: str = Field(description='exact player_id from the surviving players list, or "no_watch"')


class TrailseerOutput(TurnOutput[ReadRole], Generic[ReadRole]):
    trailseer_target: str = Field(description="exact player_id from the surviving players list")


class HealerOutput(TurnOutput[ReadRole], Generic[ReadRole]):
    healer_target: str = Field(description="exact player_id from the surviving players list")


class VigilanteOutput(TurnOutput[ReadRole], Generic[ReadRole]):
    vigilante_target: str = Field(description='exact player_id from the surviving players list, or "hold_fire"')


class SigilistOutput(TurnOutput[ReadRole], Generic[ReadRole]):
    sigil_target: str = Field(description='exact player_id from the surviving players list, or "keep_sigil"')


class ChanteuseOutput(TurnOutput[ReadRole], Generic[ReadRole]):
    block_target: str = Field(description="exact player_id from the surviving players list")


class IllusionistOutput(TurnOutput[ReadRole], Generic[ReadRole]):
    conceal: Literal["conceal", "no_conceal"] = Field(
        description='"conceal" to hide the role of the player the pack kills tonight, "no_conceal" to keep your uses.',
    )


class SerialKillerOutput(TurnOutput[ReadRole], Generic[ReadRole]):
    serial_killer_target: str = Field(description="exact player_id from the surviving players list")


class NecromancerOutput(TurnOutput[ReadRole], Generic[ReadRole]):
    necromancer_target: str = Field(description='exact player_id from the surviving players list, or "stay_put"')
    body: str = Field(description='The dead player whose ability you use tonight; "none" if you stay put.')


class SpeculatorOutput(TurnOutput[ReadRole], Generic[ReadRole]):
    speculator_pick: Literal["town", "wolves", "lone_killer", "self", "not_yet"] = Field(
        description='The side you pick tonight: "town", "wolves", "lone_killer" or "self"; or "not_yet" to wait.',
    )


class FortuneTellerOutput(TurnOutput[ReadRole], Generic[ReadRole, NamedRole]):
    bet_target: str = Field(description="exact player_id from the surviving players list")
    bet_role: NamedRole = Field(
        description='The role you also name on the bet, for two points if right; "none" to bet on the death alone.',
    )


# --- The pack's turns ---


class WolfChatOutput(TurnOutput[ReadRole], Generic[ReadRole]):
    pass_turn: bool = Field(description="True to pass this round with nothing to add; false when you speak.")
    message: str


class CarrierOutput(TurnOutput[ReadRole], Generic[ReadRole]):
    kill_target: str = Field(description="exact player_id from the surviving non-wolf players list")


# --- Filled per game ---


def _read_roles(lineup: list[str]):
    return Literal[("unclear", *lineup)]


def _named_roles(lineup: list[str]):
    return Literal[("none", *lineup)]


def day_discuss_output(lineup: list[str]) -> type[DayDiscussOutput]:
    """The day discussion schema of a game with this lineup."""
    return DayDiscussOutput[_read_roles(lineup), _named_roles(lineup)]


def day_vote_output(lineup: list[str]) -> type[DayVoteOutput]:
    """The day vote schema of a game with this lineup."""
    return DayVoteOutput[_read_roles(lineup)]


def wolf_chat_output(lineup: list[str]) -> type[WolfChatOutput]:
    """The pack chat schema of a game with this lineup."""
    return WolfChatOutput[_read_roles(lineup)]


def carrier_output(lineup: list[str]) -> type[CarrierOutput]:
    """The carrier's kill schema of a game with this lineup."""
    return CarrierOutput[_read_roles(lineup)]


NIGHT_OUTPUTS: dict[str, type[TurnOutput]] = {
    "investigator": InvestigatorOutput,
    "sentinel": SentinelOutput,
    "trailseer": TrailseerOutput,
    "healer": HealerOutput,
    "vigilante": VigilanteOutput,
    "sigilist": SigilistOutput,
    "chanteuse": ChanteuseOutput,
    "illusionist": IllusionistOutput,
    "serial_killer": SerialKillerOutput,
    "necromancer": NecromancerOutput,
    "speculator": SpeculatorOutput,
    "fortune_teller": FortuneTellerOutput,
}
"""Each role's night schema, before its role lists are filled."""


def night_output(role: str, lineup: list[str]) -> type[TurnOutput]:
    """The night schema of one dealt role in a game with this lineup."""
    if role not in lineup:
        raise ValueError(f"{role} is not dealt in {lineup}")
    if role == "fortune_teller":  # the bet also names a role
        return FortuneTellerOutput[_read_roles(lineup), _named_roles(lineup)]
    return NIGHT_OUTPUTS[role][_read_roles(lineup)]
