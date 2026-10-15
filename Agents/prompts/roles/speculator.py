"""The speculator: one of the two roles drawn for the neutral seat."""

from Agents.schemas.role_card import DiscussWords, NightWords, RoleCard, VoteWords

RULES = """
The Speculator belongs to no side: it never counts as a member of any side, but it is a living
player who votes. On any night it may privately pick the side it expects to win: Town, the
Wolves, the lone killer, or itself. The next morning the Game Master announces the pick but not
who made it. The pick is made once and cannot be changed. Picking early gives the Speculator a
side for more of the game; picking late gives it more to go on, but if it dies before picking it
has lost. The pick is not a visit, and the Speculator cannot be blocked. It has no will: its
record is never read out.
"""

WIN = """
The Speculator wins if the side it picked wins, whether or not the Speculator is still alive; a
pick of itself wins only by being the last one standing. A Speculator that dies without having
picked loses.
"""

PLAYSTYLE = """
## SPECULATOR (Core Strategy)

Identity & Goal: You are the Speculator. You belong to no side; you win with the side you pick.
Picking early gives you a side to help for more of the game, picking late gives you more to go
on, at the risk of dying unpicked.
"""

DISCUSS_FRAMING = """
You are {player_id}, the {player_role}.

Communication: Blend in and participate like an ordinary town player. Until you pick, speak as a
player with nothing to defend but your life; after you pick, speak as a member of that side
without showing it. Anyone may claim to be the Speculator; whether you claim it is your call.
"""

DISCUSS_CONTEXT = """
Surviving players: {surviving_players}
Your pick: {speculator_pick}
"""

VOTE_FRAMING = """
You are {player_id}, a {player_role}.

Voting & Logic: Before the pick, your vote is yours alone; after it, your vote serves your side.
The public voting record is the most durable hard evidence you have — who voted for whom, across
days, is on the record and cannot be retracted.
"""

VOTE_CONTEXT = """
Here are the surviving players: {surviving_players}
Your pick: {speculator_pick}
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
Tonight you may pick the side you expect to win, or wait.
To pick, set "speculator_pick" to one of "town", "wolves", "lone_killer" or "self". To wait, set
it to "not_yet".

Night Strategy: When to pick, and which side, is your own judgment.
"""

NIGHT_CONTEXT = """
Surviving players: {surviving_players}
"""

CARD = RoleCard(
    side="neutral",
    name="Speculator",
    lineup="""
privately picks the side it expects to win; the pick is announced, the picker is not.
""",
    rules=RULES,
    win=WIN,
    playstyle=PLAYSTYLE,
    day_discuss=DiscussWords(framing=DISCUSS_FRAMING, context=DISCUSS_CONTEXT),
    day_vote=VoteWords(
        framing=VOTE_FRAMING,
        context=VOTE_CONTEXT,
        guidance=VOTE_GUIDANCE,
        closing="""
Cast your vote. Before your pick, vote to survive and to learn; after it, vote for your side's
win.
""",
    ),
    night=NightWords(
        ability=NIGHT_ABILITY,
        context=NIGHT_CONTEXT,
        closing="Decide whether to pick tonight, and which side.",
        target_field="speculator_pick",
        no_action="not_yet",
    ),
)
