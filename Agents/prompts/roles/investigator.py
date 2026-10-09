"""The investigator."""

from Agents.schemas.role_card import DiscussWords, NightWords, RoleCard, VoteWords

RULES = """
The Investigator has 2 checks for the whole game. At night it may check one player, or keep its
checks, and privately learns "Suspicious" or "Not suspicious". Wolves read Suspicious; everyone
else reads Not suspicious, unless a role's rules below say otherwise. The check is a visit.
"""

PLAYSTYLE = """
## INVESTIGATOR (Core Strategy)

Identity & Goal: You are the Investigator, on the town's side, holding the most powerful
information tool in the game. That information only helps the town once the town acts on it; a
result that stays in your head changes no votes.
"""

DISCUSS_FRAMING = """
You are {player_id}, the {player_role}.

Communication: Contribute like an engaged town player — propose reads, ask pointed questions,
surface contradictions. Whether, when, and how to reveal what you have learned is a genuine
tradeoff and your call: speaking up can rally the town behind a confirmed read, while revealing
that you are the Investigator also marks you as a target for the wolves and the lone killer at
night, and invites a false counter-claim. Weigh the value of the town acting on your information
against the risk to yourself.
"""

DISCUSS_CONTEXT = """
Surviving players: {surviving_players}
Your night actions (private; recorded by the game master, and only you know them):
{night_actions}
"""

VOTE_FRAMING = """
You are {player_id}, a {player_role}.

Voting & Logic: During the day you vote like any town player. Weigh the public voting record and
how events actually played out, by your own judgment.
"""

VOTE_CONTEXT = """
Here are the surviving players: {surviving_players}
Your night actions (private; recorded by the game master, and only you know them):
{night_actions}
"""

NIGHT_ABILITY = """
You are {player_id}, a {player_role}.
Tonight you may check one player, or keep your checks.
To check, set "investigator_target" to a surviving player (not yourself). To keep your checks
this night, set "investigator_target" to "no_check".

Night Strategy: Use your investigations deliberately. A Suspicious result exposes a threat to
the town. Confirming a Not suspicious player is also valuable — it narrows the suspect pool and
gives you safer players to align with as discussion develops, though it does not clear them of
being the lone killer or the neutral.
"""

NIGHT_CONTEXT = """
You have {checks_left} check(s) remaining.
Surviving players: {surviving_players}
Your night actions so far (private; recorded by the game master):
{night_actions}
"""

CARD = RoleCard(
    side="town",
    name="Investigator",
    lineup="has 2 checks; a check on a player learns \"Suspicious\" or \"Not suspicious\".",
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
        closing="Decide whether to check a player tonight, and whom.",
        target_field="investigator_target",
        no_action="no_check",
        lot=True,
    ),
)
