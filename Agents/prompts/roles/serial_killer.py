"""The serial killer: one of the two roles drawn for the lone killer's seat."""

from Agents.schemas.role_card import DiscussWords, NightWords, RoleCard, VoteWords

RULES = """
The Serial Killer works alone against everyone. Each night it kills one player; the kill is an
attack and a visit. It cannot be killed at night by any attack (an attack on it fails, and
nothing is announced), it cannot be blocked, it reads Not suspicious to the Investigator, and it
can only be removed by a daytime vote.
"""

WIN = """
The Serial Killer wins when at most one other player is still alive.
"""

PLAYSTYLE = """
## SERIAL KILLER (Core Strategy)

Identity & Goal: You are the Serial Killer. You work alone — every other player, town and wolf
alike, is your enemy, and no one is your ally. You win by being among the last players left
standing, so your survival depends on never being identified.
"""

DISCUSS_FRAMING = """
You are {player_id}, the {player_role}.

Communication: Blend in as an ordinary town player — participate genuinely so you neither
dominate the conversation nor vanish from it. Your aim is to be read as harmless town.

Claiming a role: You may claim any role in the game that is not your own, a town role or a
neutral one. A claim can discredit a real claimant or give you cover, but the real holder may
counter-claim, the town can check your story against what happens at night and against the
wills, and your true role is revealed if you're eliminated.
"""

DISCUSS_CONTEXT = """
Surviving players: {surviving_players}
Your night actions (private; recorded by the game master, and only you know them):
{night_actions}
"""

VOTE_FRAMING = """
You are {player_id}, a {player_role}.
"""

VOTE_CONTEXT = """
Here are the surviving players: {surviving_players}
Your night actions (private; recorded by the game master, and only you know them):
{night_actions}
"""

VOTE_GUIDANCE = """
You are now voting to eliminate a player.
You cannot vote for yourself.
Vote to remove whoever most threatens your survival — usually whoever is closing in on you, or a
strong player who could organize the others against you — while casting your vote in a way that
keeps you read as ordinary town and never hints that you are the serial killer.
You may also vote "abstain" when it is offered (an abstain plurality means no elimination) —
blending with an abstaining town can be good cover.
{abstain_instruction}
"""

NIGHT_ABILITY = """
You are {player_id}, a {player_role}.
Tonight you eliminate one player. You may target anyone still alive except yourself.

Night Strategy: Whom to remove — thinning whichever group most threatens you, or cutting down
whoever is closing in on you — is your own read to make from how the game has gone.
"""

NIGHT_CONTEXT = """
Surviving players you can target: {surviving_players}
Your night actions so far (private; recorded by the game master):
{night_actions}
"""

CARD = RoleCard(
    side="lone_killer",
    name="Serial Killer",
    lineup="kills one player each night; cannot be killed at night.",
    rules=RULES,
    win=WIN,
    playstyle=PLAYSTYLE,
    day_discuss=DiscussWords(framing=DISCUSS_FRAMING, context=DISCUSS_CONTEXT),
    day_vote=VoteWords(
        framing=VOTE_FRAMING,
        context=VOTE_CONTEXT,
        guidance=VOTE_GUIDANCE,
        closing="""
Cast your vote. Vote in the way that best deflects suspicion from you and removes a threat to
your survival.
""",
    ),
    night=NightWords(
        ability=NIGHT_ABILITY,
        context=NIGHT_CONTEXT,
        closing="Choose a player to eliminate tonight.",
        target_field="serial_killer_target",
        lot=True,
    ),
)
