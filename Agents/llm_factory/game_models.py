"""The models one game's turns run on, and the key they run on, as one object per game."""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

from . import accessors
from .chat import cached_chat_model, create_chat_model, provider_family, provider_name
from .health import ModelHealth
from .outcomes import TurnOutcomes


class GameModels:
    """One game's models: which model its turns run on, the player's key when the player pays,
    the count of stalled turns, and the clients built on the player's key.

    Whoever starts the game builds it and passes it in: the server's session and the batch runner
    put it in the graph context (``GraphContext.models``), and a test passes its own. The turn
    code asks it for a model and never looks one up, so two games in one process cannot take each
    other's model, key or stall count.

    No ``model`` and no ``api_key`` means the environment decides (the command line, batch runs,
    evaluations). A ``model`` without a key is a house-funded game on the server's credentials.
    ``rescue_model=None`` on a served game means no rescue: the typed technical pass keeps the
    game moving.

    The key is held here and nowhere else. It is never part of a graph's state or its run
    configuration, both of which are saved; the graph context that carries this object is not.
    """

    def __init__(self, *, model: str = "", api_key: str = "", rescue_model: str | None = None,
                 backup_key: str = "") -> None:
        self.model = model
        self.rescue_model = rescue_model
        self._api_key = api_key
        # The player's key for the rescue model's company, when that is another company than
        # the game's model (a saved second key, opt-in on the ticket).
        self._backup_key = backup_key
        # Shared by the game's threads: the stall count that sends a turn straight to the rescue
        # model (health.py).
        self.health = ModelHealth()
        # Which turns were not decided by the game's own model (outcomes.py).
        self.outcomes = TurnOutcomes()
        # The clients built on the player's key. Kept with the game, not in the process-wide
        # cache, so the key goes when the game's object is dropped.
        self._clients: dict[Any, Any] = {}

    # ---- the models a turn asks for ----------------------------------------------------------

    def seat(self) -> Any:
        """The model a seat's turn runs on."""
        model = self._game_model()
        return self._client(
            model, temperature=accessors.game_temperature(),
            thinking_level=accessors.game_thinking_level(model),
            **accessors.turn_request_budget(),
        )

    def seat_rescue(self) -> Any:
        """The model that takes a turn the seat's model failed, or None when no rescue applies:
        then the typed technical pass absorbs the failure."""
        model = self._rescue_model()
        if model is None:
            return None
        return self._client(
            model, temperature=accessors.game_temperature(),
            thinking_level=accessors.game_thinking_level(model),
            **accessors.turn_request_budget(),
        )

    def summary(self) -> Any:
        """The model that writes the day summary: the game's model at its summary level, with a
        longer wait (the summary's failure path is the raw transcript)."""
        model = self._game_model()
        return self._client(
            model, temperature=accessors.game_temperature(),
            thinking_level=accessors.summary_thinking_level(model),
            **accessors.summary_request_budget(),
        )

    def summary_rescue(self) -> Any:
        """The day summary's rescue, or None when no rescue applies."""
        model = self._rescue_model()
        if model is None:
            return None
        return self._client(
            model, temperature=accessors.game_temperature(),
            thinking_level=accessors.summary_thinking_level(model),
            **accessors.summary_request_budget(),
        )

    def judge(self, default_thinking_level: str = "minimal") -> Any:
        """The game's model for a yes-or-no judgment (the echo gate): minimal thinking unless the
        caller needs more or the environment sets it for every judge. Every caller keeps the line
        when the judge fails."""
        return self._client(
            self._game_model(), temperature=accessors.game_temperature(),
            thinking_level=accessors.judge_thinking_level(default_thinking_level),
            **accessors.turn_request_budget(),
        )

    def extractor(self) -> Any:
        """The game's model for tagging a human's line (who it addresses). Temperature 0, so the
        same line is tagged the same way on every run; a failed tag is no addressees."""
        return self._client(
            self._game_model(), temperature=0.0,
            thinking_level=accessors.extractor_thinking_level(),
            **accessors.turn_request_budget(),
        )

    def probe(self) -> Any:
        """A plain client on the game's model, for asking the provider one question to test a
        key before a game runs on it (server/game/key_check.py). Temperature 1: OpenAI's
        reasoning models refuse any other value."""
        return self._client(self._game_model(), temperature=1.0)

    # ---- what the turn code needs besides a model ------------------------------------------------

    def provider(self) -> str:
        """The company the game's key belongs to, as a player knows it."""
        return provider_name(self.model)

    def redact(self, text: str) -> str:
        """``text`` with this game's keys replaced. A provider's error can quote the key it
        refused, and such an error is logged and, when it ends a turn, saved in the game's
        checkpoint, so the text is scrubbed where the error is caught, before either."""
        for key in (self._api_key, self._backup_key):
            if key:
                text = text.replace(key, "***")
        return text

    def without_keys(self) -> GameModels:
        """The same models with no key and none of the clients built on one: what a game keeps
        once it has ended and will make no more calls."""
        return GameModels(model=self.model, rescue_model=self.rescue_model)

    # ---- how a key reaches a provider --------------------------------------------------------

    def _client(self, model: str, **args: Any) -> Any:
        """The chat model for ``model``. This is the one place a player's key is handed to a
        provider's client."""
        key = self._key_for(model)
        if not key:
            return create_chat_model(model, **args)
        return cached_chat_model(self._clients, model, game_key=key, **args)

    def _key_for(self, model: str) -> str:
        """The player's key, only when ``model`` is from the same company as the game's model;
        the backup key, only when it is from the rescue model's company. Any other model in the
        game runs on the server's own credentials, so a player's key is never sent to a company
        it does not belong to."""
        family = provider_family(model)
        if self._api_key and provider_family(self.model) == family:
            return self._api_key
        if self._backup_key and self.rescue_model and provider_family(self.rescue_model) == family:
            return self._backup_key
        return ""

    def _game_model(self) -> str:
        """The game's own model when it has one; otherwise the environment's, which is the
        local, batch and evaluation configuration."""
        return self.model or os.getenv("GOOGLE_GENAI_MODEL", accessors.DEFAULT_GAME_MODEL)

    def _rescue_model(self) -> str | None:
        """The rescue model's id, or None when no rescue applies.

        A served game uses the rescue it was given, on the same credential path as its model:
        house-funded stays on the server's credentials and a player's game on the player's key.
        Otherwise the environment's pair (``GAME_FALLBACK_MODEL``), or None when that equals the
        game's model: a second try on the identical model is not a rescue."""
        if self.model or self._api_key:
            return self.rescue_model or None
        model = os.getenv("GAME_FALLBACK_MODEL", accessors.DEFAULT_GAME_FALLBACK_MODEL)
        if model == os.getenv("GOOGLE_GENAI_MODEL", accessors.DEFAULT_GAME_MODEL):
            return None
        return model

    # ---- the key must not leave this object ----------------------------------------------------

    def __repr__(self) -> str:
        return f"GameModels(model={self.model!r}, rescue_model={self.rescue_model!r})"

    def __getstate__(self):
        raise TypeError("GameModels holds a player's key and is never saved or copied")


# The models of a caller that passed none: the environment's, one object for the process, so
# the stall count of a run without a graph context still builds up from turn to turn.
_ENV_MODELS = GameModels()


def env_models() -> GameModels:
    """The environment's models: what the command line, an evaluation script or a test with no
    models of its own runs on."""
    return _ENV_MODELS


def game_models(context: Mapping[str, Any] | None) -> GameModels:
    """The models in a graph context, or the environment's when the context has none (older
    tests build contexts without them, and a test runtime may have no context at all)."""
    return (context or {}).get("models") or env_models()
