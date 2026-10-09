"""The sentinel."""

from Agents.schemas.role_card import DiscussWords, NightWords, RoleCard, VoteWords

RULES = """
Each night the Sentinel watches one player and privately learns the names of everyone who
visited them that night, or that no one did. Watching is a visit.
"""

PLAYSTYLE = """
## SENTINEL (Core Strategy)

Identity & Goal: You are the Sentinel, on the town's side. A visitor is evidence, not a verdict:
a kill, a protection, a check, a block and a sigil all look the same at the door.
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
Tonight you watch one player. You cannot watch yourself.

Night Strategy: Whom to watch is your own judgment.
"""

NIGHT_CONTEXT = """
Surviving players you can watch: {surviving_players}
Your night actions so far (private; recorded by the game master):
{night_actions}
"""

CARD = RoleCard(
    side="town",
    name="Sentinel",
    lineup="each night watches one player and learns who visited them.",
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
        closing="Choose a player to watch tonight.",
        target_field="sentinel_target",
        lot=True,
    ),
)
