"""The composed rules block matches its rendered golden, and every dealt role has its words.

The golden under Agents/prompts/goldens/ is the review surface for the rules: when a role's
fragments change, regenerate it on purpose (``poetry run python -m Agents.prompts.goldens.render``)
and read the diff in English.
"""
from __future__ import annotations

from importlib import import_module

from Agents.prompts.compose import rules_block
from Agents.schemas.role_card import RoleCard
from Agents.prompts.goldens.render import CASTS, RENDERED_DIR
from Agents.schemas.roles import ALL_LINEUPS


def test_rendered_rules_match_the_composed_text():
    for filename, cast in CASTS.items():
        rendered = (RENDERED_DIR / filename).read_text()
        assert rendered == rules_block(cast) + "\n", f"{filename} is stale: run Agents.prompts.goldens.render"


def test_the_goldens_deal_every_role():
    assert {role for cast in CASTS.values() for role in cast} == {role for cast in ALL_LINEUPS for role in cast}


def test_every_dealt_role_has_a_card():
    for role in {role for cast in ALL_LINEUPS for role in cast}:
        card = import_module(f"Agents.prompts.roles.{role}").CARD
        assert isinstance(card, RoleCard)
        assert card.side in ("town", "wolves", "lone_killer", "neutral")


def test_an_undealt_role_leaves_no_trace():
    cast = ["investigator", "vigilante", "healer", "chanteuse", "serial_killer"]
    text = rules_block(cast)
    assert "Illusionist" not in text and "Sentinel" not in text and "Speculator" not in text
    assert "Chanteuse:" in text and "three sides" in text


def test_no_lineup_names_a_role_it_did_not_deal():
    names = {role: import_module(f"Agents.prompts.roles.{role}").CARD.name
             for cast in ALL_LINEUPS for role in cast}
    for cast in ALL_LINEUPS:
        text = rules_block(cast).lower()
        assert "10 players" in text
        for role, name in names.items():
            if role not in cast:
                assert name.lower() not in text, f"{cast[-2:]} names the undealt {name}"
