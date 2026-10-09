"""The sigilist."""

from Agents.schemas.role_card import DiscussWords, NightWords, RoleCard, VoteWords

RULES = """
The Sigilist has 2 sigils for the whole game. At night it may place one on a player, or keep its
sigils. If that player attacks anyone that night, the sigil strikes them: an attack of its own,
resolved after theirs, which protection or night immunity can stop; their original attack
resolves as normal either way. A death by sigil is announced as struck down by a sigil. The
Sigilist is told whether the sigil struck, or the healer saved its target from it; otherwise only
that the sigil had no effect, which is what both a target who did not attack and an attacker
night immunity protected look like. A sigil is spent when placed, whether or not it triggers.
Placing a sigil is a visit.
"""

PLAYSTYLE = """
## SIGILIST (Core Strategy)

Identity & Goal: You are the Sigilist, on the town's side, with two sigils for the whole game. A
sigil on a player who does not attack is spent for nothing.
"""

DISCUSS_FRAMING = """
You are {player_id}, the {player_role}.

Communication: Blend in and participate like an ordinary town player. A death by sigil tells the
town that a sigil struck, not who placed it; what you say is your call.
"""

DISCUSS_CONTEXT = """
Surviving players: {surviving_players}
Sigils left: {sigils_left}
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
Sigils left: {sigils_left}
Your night actions (private; recorded by the game master, and only you know them):
{night_actions}
"""

NIGHT_ABILITY = """
You are {player_id}, a {player_role}.
Tonight you may place a sigil on one player, or keep your sigils.
To place a sigil, set "sigil_target" to a surviving player (not yourself). To keep your sigils
this night, set "sigil_target" to "keep_sigil".

Night Strategy: Whether and where to place a sigil is your own judgment.
"""

NIGHT_CONTEXT = """
You have {sigils_left} sigil(s) remaining.
Surviving players you could mark: {surviving_players}
Your night actions so far (private; recorded by the game master):
{night_actions}
"""

CARD = RoleCard(
    side="town",
    name="Sigilist",
    lineup="""
has 2 sigils; a sigil placed on a player strikes them if they attack anyone that night.
""",
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
        closing="Decide whether to place a sigil tonight, and on whom.",
        target_field="sigil_target",
        no_action="keep_sigil",
        lot=True,
    ),
)
