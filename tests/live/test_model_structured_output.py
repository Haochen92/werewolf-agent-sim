"""Does every model on the served-game menu still return valid structured output?

A seat's turn is one call: the model is bound to a Pydantic schema through the factory's
tool-calling path and must come back with a fully populated object. A provider change
(a new model, a renamed id, a tool-calling regression) breaks that silently until a real
game fails mid-turn. This module is the regression gate: every row of
SUPPORTED_GAME_MODELS is asked for every seat-facing schema once, with a short in-character
prompt, and the reply must validate and fill the field the game acts on.

Costs real money and needs credentials, so it is marked ``live`` and skipped by default.
A model whose credential is absent is skipped, not failed. Run it when adding a menu row,
after a provider announcement, or before a deploy:

    poetry run pytest -m live tests/live -v
    poetry run pytest -m live tests/live -k deepseek      # one provider only

Never compare timings across runs as evidence of anything; they are printed for a feel.

Reading a failure: one call at the game's temperature is one sample, so a single failure
is a signal, not a verdict. Rerun that case several times with ``-k "<model> and <schema>"``
and read the rate. In a game a seat gets two attempts on its own model and then one on
its rescue model before it passes the turn (Agents/turn/agent_player.py), so an
occasional failure is absorbed; a rate near one in three is not, and the row's catalogue
comment should say so. First run, 2026-09-10: every row clean except DeepSeek V4.1 Flash
on the wolf vote, at about one failure in three.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from Agents.llm_factory.backends import create_chat_model
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
from server.game.model_catalog import SUPPORTED_GAME_MODELS

pytestmark = pytest.mark.live

OTHERS = ("Mia", "Omar", "Lena", "Theo", "Ivy")
_TABLE = (
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


def _credential_missing(model: str) -> str | None:
    """The reason to skip this model, or None when its credential looks present."""
    if model.startswith("deepseek/"):
        return None if os.getenv("DEEPSEEK_API_KEY") else "DEEPSEEK_API_KEY not set"
    if model.startswith("nim/"):
        return None if os.getenv("NVIDIA_API_KEY") else "NVIDIA_API_KEY not set"
    adc = Path.home() / ".config/gcloud/application_default_credentials.json"
    if os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or adc.exists():
        return None
    return "no Google credential (GOOGLE_API_KEY, GOOGLE_APPLICATION_CREDENTIALS, or gcloud ADC)"


@pytest.mark.parametrize("schema,role_line,acted_field,tokens", SEAT_SCHEMAS,
                         ids=[s.__name__ for s, *_ in SEAT_SCHEMAS])
@pytest.mark.parametrize("model", list(SUPPORTED_GAME_MODELS))
def test_model_returns_valid_structured_output(model, schema, role_line, acted_field, tokens):
    reason = _credential_missing(model)
    if reason:
        pytest.skip(reason)

    llm = create_chat_model(model, temperature=1.0)
    started = time.time()
    out = llm.with_structured_output(schema).invoke(_TABLE + role_line)
    elapsed = time.time() - started

    assert isinstance(out, schema), f"{model} returned {type(out).__name__}, not {schema.__name__}"
    if acted_field is not None:
        value = getattr(out, acted_field)
        assert isinstance(value, str), f"{model}: {acted_field} is {type(value).__name__}"
        passed = schema is DayDiscussOutput and out.pass_turn  # a discussion turn may pass
        if not (tokens or passed):
            assert value.strip(), f"{model}: {acted_field} came back empty"
        if acted_field in _TARGET_FIELDS:
            # The one semantic check worth making: a target must be a listed player or an
            # allowed token, so the model read the roster and the instruction rather than
            # inventing a name or a token of its own.
            allowed = set(OTHERS) | set(tokens)
            assert value.strip() in allowed, f"{model}: {acted_field}={value!r} not in {sorted(allowed)}"
    if hasattr(out, "reads"):
        assert out.reads, f"{model}: no player reads"
    print(f"{model:32s} {schema.__name__:24s} {elapsed:5.1f}s")
