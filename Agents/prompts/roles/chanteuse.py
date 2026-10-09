"""The chanteuse."""

from Agents.prompts.roles import pack
from Agents.schemas.role_card import NightWords, RoleCard

RULES = """
Each night the Chanteuse also blocks one player's night action; the same player may be blocked
again on later nights. A blocked player is told "You were roleblocked", does nothing that night
and makes no visit. The block works on Town players and on wolves; the lone killer and the
neutral cannot be blocked, and the Chanteuse is told when a block did not take. Blocking is a
visit.
"""

PLAYSTYLE = """
## CHANTEUSE (Core Strategy)
""" + pack.IDENTITY

NIGHT_ABILITY = """
You are {player_id}, a {player_role}.
Besides the pack's kill, tonight you block one player, not yourself or your allies.

Your Skill: Whom to block is your own judgment. A block that does not take tells you the target
is the lone killer or the neutral.
"""

NIGHT_CONTEXT = """
Surviving non-wolf players you can block: {surviving_villagers}
The pack's target tonight: {wolves_target}
Your blocks so far (private; recorded by the game master):
{night_actions}
"""

CARD = RoleCard(
    side="wolves",
    name="Chanteuse",
    lineup="a wolf; each night also blocks one player's night action.",
    rules=RULES,
    playstyle=PLAYSTYLE,
    day_discuss=pack.DISCUSS,
    day_vote=pack.VOTE,
    night=NightWords(
        ability=NIGHT_ABILITY,
        context=NIGHT_CONTEXT,
        closing="Choose a player to block tonight.",
        target_field="block_target",
        lot=True,
    ),
)
