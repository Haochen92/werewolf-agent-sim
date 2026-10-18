"""The guard: deduction runs only for the roles and use limits the engine was verified for (owner,
2026-10-17). A new role or limit turns it off rather than risk a false "only X can…" line."""

from __future__ import annotations

from Agents.config.game import GameConfig
from Agents.deduction.seat_view import deduction_mode_for
from Agents.deduction.verified import VERIFIED_LIMITS, VERIFIED_ROLES, limits_verified
from Agents.schemas.roles import ALL_LINEUPS
from Agents.turn.pipeline import _with_deduction_mode


def test_every_dealt_role_is_verified_so_a_new_role_fails_here_first():
    # Adding a role to the game: verify the deduction engine for it (the catalogue's rows), then
    # add it to Agents/deduction/verified.py. Until then its games get no deduction.
    dealt = {role for lineup in ALL_LINEUPS for role in lineup}
    assert dealt == VERIFIED_ROLES


def test_a_cast_with_an_unverified_role_gets_no_deduction():
    lineup = sorted(VERIFIED_ROLES - {"speculator"}) + ["oracle"]
    assert deduction_mode_for({"lineup": lineup, "deduction_mode": "full"}) == "off"
    assert deduction_mode_for({"lineup": sorted(VERIFIED_ROLES), "deduction_mode": "full"}) == "full"


def test_the_standard_limits_are_the_verified_ones():
    assert limits_verified(GameConfig())
    assert all(getattr(GameConfig(), field) == value for field, value in VERIFIED_LIMITS.items())


def test_a_game_with_other_limits_gets_no_deduction():
    other = {"configurable": {"deduction_mode": "full", "game_config": GameConfig(sigils=3).model_dump()}}
    payload = _with_deduction_mode({}, other)
    assert payload["deduction_mode"] == "off"
    standard = {"configurable": {"deduction_mode": "full", "game_config": GameConfig().model_dump()}}
    assert _with_deduction_mode({}, standard)["deduction_mode"] == "full"
