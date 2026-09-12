"""The house's purse: which model a new game runs on and who pays (server/house.py)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from server.config import ServerSettings
from server.house import (
    KEY_DEFAULT_MODEL,
    KEY_ENABLED,
    KEY_GAMES_PER_DAY,
    HouseClosed,
    HousePolicy,
    ModelNeedsKey,
)


class Settings:
    """A settings store that remembers what was saved."""

    def __init__(self, stored=None):
        self.stored = dict(stored or {})
        self.saved = []

    async def load(self):
        return dict(self.stored)

    async def save(self, key, value):
        self.stored[key] = value
        self.saved.append((key, value))


class Games:
    """A games table that reports a fixed number of house-funded starts today."""

    def __init__(self, used_today=0):
        self.used_today = used_today
        self.asked_since = []

    async def count_house_games_since(self, since):
        self.asked_since.append(since)
        return self.used_today


def _house(stored=None, used_today=0, **defaults):
    return HousePolicy(Settings(stored), Games(used_today),
                       ServerSettings(WW_POSTGRES_DSN="", **defaults), cache_seconds=0)


async def test_an_empty_choice_resolves_to_the_default_and_the_house_pays():
    house = _house()
    assert await house.authorize("", "") == "gemini-3.5-flash-lite"  # first house row


async def test_the_default_is_a_live_setting_with_a_process_fallback():
    assert (await _house(HOUSE_DEFAULT_MODEL="gemini-3.1-flash-lite").status()
            ).default_model == "gemini-3.1-flash-lite"
    stored = {KEY_DEFAULT_MODEL: "gemini-3.6-flash"}
    assert (await _house(stored, HOUSE_DEFAULT_MODEL="gemini-3.1-flash-lite").status()
            ).default_model == "gemini-3.6-flash"  # the stored knob wins
    # A stored default that is not a house row any more is ignored, not honoured.
    assert (await _house({KEY_DEFAULT_MODEL: "gemini-2.5-pro"}).status()
            ).default_model == "gemini-3.5-flash-lite"


async def test_a_player_key_runs_any_row_and_is_never_counted():
    house = _house({KEY_ENABLED: False}, used_today=999)
    assert await house.authorize("sk-1", "gemini-2.5-pro") == "gemini-2.5-pro"
    assert await house.authorize("sk-1", "deepseek/deepseek-v4-flash") == "deepseek/deepseek-v4-flash"


async def test_a_player_funded_row_needs_a_key():
    with pytest.raises(ModelNeedsKey, match="requires api_key"):
        await _house().authorize("", "gemini-2.5-pro")


async def test_an_unknown_model_is_a_lookup_error():
    with pytest.raises(LookupError, match="unsupported model"):
        await _house().authorize("", "gpt-9")


async def test_the_kill_switch_closes_the_house_for_good():
    with pytest.raises(HouseClosed, match="switched off") as caught:
        await _house({KEY_ENABLED: False}).authorize("", "")
    assert caught.value.reset_at is None
    assert (await _house(HOUSE_FUNDED_ENABLED=False).status()).remaining == 0


async def test_the_daily_cap_closes_the_house_until_midnight_utc():
    house = _house({KEY_GAMES_PER_DAY: 3}, used_today=3)
    with pytest.raises(HouseClosed, match="3 games for today") as caught:
        await house.authorize("", "")
    reset = caught.value.reset_at
    assert reset.tzinfo is not None and (reset.hour, reset.minute) == (0, 0)
    assert reset > datetime.now(timezone.utc)
    # The count is asked from the start of the UTC day.
    since = house._games.asked_since[-1]
    assert (since.hour, since.minute, since.tzinfo) == (0, 0, timezone.utc)

    under = _house({KEY_GAMES_PER_DAY: 3}, used_today=2)
    assert await under.authorize("", "") == "gemini-3.5-flash-lite"
    assert (await under.status()).remaining == 1


async def test_update_validates_and_takes_effect_at_once():
    house = _house()
    status = await house.update(default_model="gemini-3.6-flash", games_per_day=1,
                                enabled=True)
    assert (status.default_model, status.games_per_day) == ("gemini-3.6-flash", 1)
    assert house._settings.saved == [
        (KEY_ENABLED, True), (KEY_DEFAULT_MODEL, "gemini-3.6-flash"), (KEY_GAMES_PER_DAY, 1)]
    with pytest.raises(ValueError, match="house-funded row"):
        await house.update(default_model="gemini-2.5-pro")
    with pytest.raises(ValueError, match="0 or more"):
        await house.update(games_per_day=-1)


# ---- over HTTP: the doors and the admin endpoint ------------------------------------------

def test_the_house_closed_answers_402_at_both_doors(api_client, monkeypatch):
    house = api_client.app.state.resources.house
    monkeypatch.setattr(house, "_defaults", ServerSettings(WW_POSTGRES_DSN="",
                                                            HOUSE_FUNDED_ENABLED=False))
    for door in ("/games", "/rooms"):
        r = api_client.post(door, json={})
        assert r.status_code == 402, r.text
        assert "switched off" in r.json()["detail"]
    # A key still opens either door (the game is never launched here: 422 on the fake key
    # would come from the engine, so stop at the gate by asking for an unknown model).
    r = api_client.post("/games", json={"api_key": "sk-1", "model": "gpt-9"})
    assert r.status_code == 422 and "unsupported model" in r.json()["detail"]


def test_admin_house_is_hidden_without_a_token_and_guarded_with_one(api_client, monkeypatch):
    from server.config import server_settings

    assert api_client.get("/admin/house").status_code == 404
    monkeypatch.setattr(server_settings, "ADMIN_TOKEN", "s3cret")
    assert api_client.get("/admin/house").status_code == 403
    assert api_client.get("/admin/house", headers={"X-Admin-Token": "nope"}).status_code == 403

    ok = {"X-Admin-Token": "s3cret"}
    before = api_client.get("/admin/house", headers=ok).json()
    assert before["default_model"] == "gemini-3.5-flash-lite" and before["enabled"] is True

    r = api_client.put("/admin/house", headers=ok,
                       json={"default_model": "gemini-3.1-flash-lite", "games_per_day": 2})
    assert r.status_code == 200, r.text
    after = r.json()
    assert (after["default_model"], after["games_per_day"], after["remaining"]) == (
        "gemini-3.1-flash-lite", 2, 2)
    # The menu reflects it at once (storage is off, so it lives in memory until restart).
    menu = api_client.get("/models").json()
    assert [m["model"] for m in menu["models"] if m["is_default"]] == ["gemini-3.1-flash-lite"]
    assert menu["house"]["games_per_day"] == 2

    r = api_client.put("/admin/house", headers=ok, json={"default_model": "gemini-2.5-pro"})
    assert r.status_code == 422
    r = api_client.put("/admin/house", headers=ok, json={"unknown": 1})
    assert r.status_code == 422
