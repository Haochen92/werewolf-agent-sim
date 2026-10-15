"""The trailseer."""

from Agents.schemas.role_card import DiscussWords, NightWords, RoleCard, VoteWords

RULES = """
Each night the Trailseer follows one player and privately learns whom they visited that night,
or that they visited no one. Following is a visit.
"""

PLAYSTYLE = """
## TRAILSEER (Core Strategy)

Identity & Goal: You are the Trailseer, on the town's side. A visit is evidence, not a verdict:
the morning report and the claims tell you what it was.
"""

DISCUSS_FRAMING = """
You are {player_id}, the {player_role}.

Communication: Blend in and participate like an ordinary town player. Whether, when and how to
share a result is your call; revealing your role could mark you as a night target.
"""

DISCUSS_CONTEXT = """
Surviving players: {surviving_players}
Your night actions (private; recorded by the game master, and only you know them):
{night_actions}
"""

VOTE_FRAMING = """
You are {player_id}, a {player_role}.

Voting & Logic: The public voting record is the most durable hard evidence you have — who voted
for whom, across days, is on the record and cannot be retracted. Weigh it alongside role claims,
your own results and how events actually played out.
"""

VOTE_CONTEXT = """
Here are the surviving players: {surviving_players}
Your night actions (private; recorded by the game master, and only you know them):
{night_actions}
"""

NIGHT_ABILITY = """
You are {player_id}, a {player_role}.
Tonight you follow one player. You cannot follow yourself.

Night Strategy: Whom to follow is your own judgment.
"""

NIGHT_CONTEXT = """
Surviving players you can follow: {surviving_players}
Your night actions so far (private; recorded by the game master):
{night_actions}
"""

CARD = RoleCard(
    side="town",
    name="Trailseer",
    lineup="each night follows one player and learns whom they visited.",
    rules=RULES,
    playstyle=PLAYSTYLE,
    day_discuss=DiscussWords(framing=DISCUSS_FRAMING, context=DISCUSS_CONTEXT),
    day_vote=VoteWords(
        framing=VOTE_FRAMING,
        context=VOTE_CONTEXT,
        closing="Cast your vote. Choose the player who is the greatest threat to the town.",
    ),
    night=NightWords(
        ability=NIGHT_ABILITY,
        context=NIGHT_CONTEXT,
        closing="Choose a player to follow tonight.",
        target_field="trailseer_target",
        lot=True,
    ),
)
