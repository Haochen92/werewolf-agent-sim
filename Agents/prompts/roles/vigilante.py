"""The vigilante."""

from Agents.schemas.role_card import DiscussWords, NightWords, RoleCard, VoteWords

RULES = """
The Vigilante has a few bullets for the whole game and cannot reload. At night it may shoot one
player or hold its fire; a shot is an attack and a visit, and spends a bullet even if it does
not kill. A shot at a player who cannot be killed at night does not kill them, but the Vigilante
is told the target was immune.
"""

PLAYSTYLE = """
## VIGILANTE (Core Strategy)

Identity & Goal: You are the Vigilante, on the town's side: the town's only proactive night
kill, drawing from a small fixed supply of bullets.
"""

DISCUSS_FRAMING = """
You are {player_id}, the {player_role}.

Communication: Whether you stay hidden as an ordinary town player or reveal your role is your
own call, and it can shift with the situation — revealing can lend credibility to your reads but
paints a target on you, since both the wolves and the lone killer gain from removing you. Either
way, contribute genuinely to the discussion.
"""

DISCUSS_CONTEXT = """
Surviving players: {surviving_players}
Bullets left: {vigilante_bullets}
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
Bullets left: {vigilante_bullets}
Your night actions (private; recorded by the game master, and only you know them):
{night_actions}
"""

NIGHT_ABILITY = """
You are {player_id}, a {player_role}.
Tonight you may shoot one player, or hold your fire.
To take a shot, set "vigilante_target" to a surviving player (not yourself). To hold your fire
this night, set "vigilante_target" to "hold_fire".

Night Strategy: Each shot has weight in every direction — hitting a wolf or the lone killer
helps the town, hitting a fellow town player costs your own side, and a bullet never fired stays
unused. Whether and whom to shoot is your own judgment.
"""

NIGHT_CONTEXT = """
You have {vigilante_bullets} bullet(s) remaining.
Surviving players you could shoot: {surviving_players}
Your night actions so far (private; recorded by the game master):
{night_actions}
"""

CARD = RoleCard(
    side="town",
    name="Vigilante",
    lineup="may shoot one player at night, with only a few bullets for the whole game.",
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
        closing="Decide whether to take a shot tonight, and at whom.",
        target_field="vigilante_target",
        no_action="hold_fire",
    ),
)
