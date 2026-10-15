"""The fortune teller: one of the two roles drawn for the neutral seat."""

from Agents.schemas.role_card import DiscussWords, NightWords, RoleCard, VoteWords

RULES = """
The Fortune Teller has no side: it never counts as a member of any side, but it is a living
player who votes. Every night it places a bet on who will die that night, by any cause, naming
the player and, if it wishes, their role: one point if that player dies, two if the named role
was also correct; a wrong role still scores one point for the death. A hidden role still scores.
Instead, up to twice per game, it may bet on itself: that night an attack on it fails, and no
points are scored. Bets are placed when the night starts and settled when it ends, when the
Fortune Teller is told the result; a vote during the day never scores. A bet is not a visit, the
Fortune Teller cannot be blocked, and it reads Not suspicious to the Investigator. It has no
will: its record is never read out.
"""

WIN = """
The Fortune Teller wins once it has scored two points, alongside whoever else wins; the game
goes on, and the points are kept even if it dies.
"""

PLAYSTYLE = """
## FORTUNE TELLER (Core Strategy)

Identity & Goal: You are the Fortune Teller. You belong to no side; you win by scoring two
points on your bets, and once you have won you cannot lose.
"""

DISCUSS_FRAMING = """
You are {player_id}, the {player_role}.

Communication: Blend in and participate like an ordinary town player. You have nothing to hide
but your role; whether to claim it is your call.
"""

DISCUSS_CONTEXT = """
Surviving players: {surviving_players}
Your points: {fortune_points} of 2. Self-bets left: {fortune_self_bets}
Your bets so far (private; recorded by the game master, and only you know them):
{night_actions}
"""

VOTE_FRAMING = """
You are {player_id}, a {player_role}.

Voting & Logic: A vote never scores, but who dies by day changes who dies by night. The public
voting record is the most durable hard evidence you have — who voted for whom, across days, is
on the record and cannot be retracted.
"""

VOTE_CONTEXT = """
Here are the surviving players: {surviving_players}
Your points: {fortune_points} of 2. Self-bets left: {fortune_self_bets}
Your bets so far (private; recorded by the game master, and only you know them):
{night_actions}
"""

VOTE_GUIDANCE = """
You are now voting to eliminate a player. You belong to no side, so the vote is yours to use as
you see fit.
You cannot vote for yourself.
You may also vote "abstain" when it is offered (an abstain plurality means no elimination).
{abstain_instruction}
"""

NIGHT_ABILITY = """
You are {player_id}, a {player_role}.
Tonight you bet on who will die.
To bet, set "bet_target" to a surviving player and "bet_role" to a role or "none". To bet on
yourself, set "bet_target" to your own player id.

Night Strategy: Whom to bet on, whether to name a role too, and when to spend a self-bet is your
own judgment.
"""

NIGHT_CONTEXT = """
Surviving players: {surviving_players}
Your points: {fortune_points} of 2. Self-bets left: {fortune_self_bets}
Your bets so far (private; recorded by the game master):
{night_actions}
"""

CARD = RoleCard(
    side="neutral",
    name="Fortune Teller",
    lineup="bets each night on who will die; wins by scoring two points.",
    rules=RULES,
    win=WIN,
    playstyle=PLAYSTYLE,
    day_discuss=DiscussWords(framing=DISCUSS_FRAMING, context=DISCUSS_CONTEXT),
    day_vote=VoteWords(
        framing=VOTE_FRAMING,
        context=VOTE_CONTEXT,
        guidance=VOTE_GUIDANCE,
        closing="""
Cast your vote. A vote never scores, but who dies by day changes who dies by night.
""",
    ),
    night=NightWords(
        ability=NIGHT_ABILITY,
        context=NIGHT_CONTEXT,
        closing="Place your bet for tonight.",
        target_field="bet_target",
    ),
)
