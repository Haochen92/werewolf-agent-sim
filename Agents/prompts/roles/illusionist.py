"""The illusionist."""

from Agents.prompts.roles import pack
from Agents.schemas.role_card import NightWords, RoleCard

RULES = """
Twice per game the Illusionist may hide the role of the player the wolves killed that night. The
morning report then says "Their role is hidden by an illusionist" instead of the role, that
player has no will, and the Illusionist privately learns the role. Hiding the body also hides the
attacking trace: the carrier's visit to that victim is not seen by a Sentinel watching the victim
or a Trailseer following the carrier. The carrier's other visit that night is still seen, and so is
the Illusionist's own visit to hide the body, unless the Illusionist carried the kill itself: then it
leaves no trace at that door at all. If the wolves' victim survived, nothing is hidden, the use is
kept, and every visit to the victim is seen.
"""

PLAYSTYLE = """
## ILLUSIONIST (Core Strategy)
""" + pack.IDENTITY

NIGHT_ABILITY = """
You are {player_id}, a {player_role}.
Tonight you may hide the role of the player the pack kills, or keep your uses.
To hide tonight's victim, set "conceal" to "conceal". To keep your uses, set it to "no_conceal".

Your Skill: When to spend a use is your own judgment; a use is kept if the victim survives.
"""

NIGHT_CONTEXT = """
You have {conceal_uses} use(s) remaining.
The pack's target tonight: {wolves_target}
Your conceals so far (private; recorded by the game master):
{night_actions}
"""

CARD = RoleCard(
    side="wolves",
    name="Illusionist",
    lineup="a wolf; twice per game may hide the role of the player the wolves killed.",
    rules=RULES,
    playstyle=PLAYSTYLE,
    day_discuss=pack.DISCUSS,
    day_vote=pack.VOTE,
    night=NightWords(
        ability=NIGHT_ABILITY,
        context=NIGHT_CONTEXT,
        closing="Decide whether to hide tonight's victim.",
        target_field="conceal",
        no_action="no_conceal",
    ),
)
