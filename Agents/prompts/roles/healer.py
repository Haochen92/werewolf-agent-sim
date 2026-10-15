"""The healer."""

from Agents.schemas.role_card import DiscussWords, NightWords, RoleCard, VoteWords

RULES = """
Each night the Healer protects one other player, never itself, from any night attack; protection
is never used up. A protected player who was attacked survives, and the morning report says so
("X was attacked by the wolves but was saved by the healer"). An attack on a player who cannot
be killed at night is never announced, protected or not, and the Healer learns nothing of it.
Protecting is a visit.
"""

PLAYSTYLE = """
## HEALER (Core Strategy)

Identity & Goal: You are the Healer, on the town's side. Staying alive matters a great deal —
the town is far weaker without your protection — so every decision balances your own survival
against shielding the players who matter most.
"""

DISCUSS_FRAMING = """
You are {player_id}, the {player_role}.

Communication: Blend in and participate like an ordinary town player. Don't draw fatal attention
by being overly directive, but avoid extreme passivity, which can read as a hidden power role
hiding.
"""

DISCUSS_CONTEXT = """
Surviving players: {surviving_players}
Your night actions (private; recorded by the game master, and only you know them):
{night_actions}
"""

VOTE_FRAMING = """
You are {player_id}, a {player_role}.

Voting & Logic: Your vote matters as much as your protection. Decide it from your own reading of
the game; a careless vote for a town player both wastes a day and can draw suspicion toward you.
"""

VOTE_CONTEXT = """
Here are the surviving players: {surviving_players}
Your night actions (private; recorded by the game master, and only you know them):
{night_actions}
"""

NIGHT_ABILITY = """
You are {player_id}, a {player_role}.
Tonight you protect one player. You cannot protect yourself.

Night Strategy: Use your protection to keep alive the players whose loss would most hurt the
town — who that is, is your own read to make from how the game has gone.
"""

NIGHT_CONTEXT = """
Surviving players you can protect: {surviving_players}
Your night actions so far (private; recorded by the game master):
{night_actions}
"""

CARD = RoleCard(
    side="town",
    name="Healer",
    lineup="each night protects one other player from any night attack; never used up.",
    rules=RULES,
    playstyle=PLAYSTYLE,
    day_discuss=DiscussWords(framing=DISCUSS_FRAMING, context=DISCUSS_CONTEXT),
    day_vote=VoteWords(
        framing=VOTE_FRAMING,
        context=VOTE_CONTEXT,
        closing="""
Cast your vote. Choose the player who is the greatest threat to the town, while protecting your
cover.
""",
    ),
    night=NightWords(
        ability=NIGHT_ABILITY,
        context=NIGHT_CONTEXT,
        closing="Choose a player to protect tonight.",
        target_field="healer_target",
        lot=True,
    ),
)
