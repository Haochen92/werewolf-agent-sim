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
from evaluation.src.model_admission.seat_schemas import SEAT_SCHEMAS, TABLE, reply_problem
from server.game.model_catalog import SUPPORTED_GAME_MODELS

pytestmark = pytest.mark.live


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
    out = llm.with_structured_output(schema).invoke(TABLE + role_line)
    elapsed = time.time() - started

    problem = reply_problem(schema, out, acted_field, tokens)
    assert problem is None, f"{model}: {problem}"
    print(f"{model:32s} {schema.__name__:24s} {elapsed:5.1f}s")
