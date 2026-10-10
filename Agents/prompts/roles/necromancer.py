"""The necromancer: one of the two roles drawn for the lone killer's seat."""

from Agents.schemas.role_card import DiscussWords, NightWords, RoleCard, VoteWords

RULES = """
The Necromancer works alone against everyone. On the first night it does nothing and cannot be
killed; from the second night on it can be killed like anyone else. Each night from the second,
it may pick a dead player whose role was announced and use that role's night ability on a
target, or stay put. The same body may be used night after night; a body whose role was hidden
cannot be used. Through a dead wolf it attacks (an Illusionist's body) or blocks (a
Chanteuse's body); an attack through the Illusionist's body also hides the victim's role if they
die, and the Necromancer learns it, while the Illusionist has conceals left (the two it started
with, less those it spent); through a dead Vigilante it shoots with no penalty for a miss; through a dead
Healer it protects; through a dead Sigilist it places a sigil; through a dead Investigator,
Sentinel or Trailseer it learns what that role would have learned. The dead player's name, not
the Necromancer's, is what a Sentinel or Trailseer sees at the door, and a sigil cannot punish
an attack made through a body. The morning names an attack made through a body by the body's kind,
reanimated ("killed by a reanimated wolf", "shot by a reanimated vigilante", "struck down by a
reanimated sigil"), so the town learns a Necromancer struck, though not who. On a night it
attacks, it reads Suspicious to the Investigator;
on other nights, Not suspicious. It cannot be blocked, and it can be removed by a daytime vote
or, from the second night, by a night attack.
"""

WIN = """
The Necromancer wins when at most one other player is still alive.
"""

PLAYSTYLE = """
## NECROMANCER (Core Strategy)

Identity & Goal: You are the Necromancer. You work alone — every other player, town and wolf
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
keeps you read as ordinary town and never hints that you are the necromancer.
You may also vote "abstain" when it is offered (an abstain plurality means no elimination) —
blending with an abstaining town can be good cover.
{abstain_instruction}
"""

NIGHT_ABILITY = """
You are {player_id}, a {player_role}.
Tonight you may act through a dead player's body, or stay put.
To act, set "body" to the dead player and "necromancer_target" to your target. To stay put
tonight, set "necromancer_target" to "stay_put" and "body" to "none".

Night Strategy: Which body to use, on whom, and when to stay put is your own judgment. Which
bodies exist is public, so the town knows what you could have done each night.
"""

NIGHT_CONTEXT = """
Bodies you can use tonight (dead players whose role was announced): {bodies}
Conceals left to the Illusionist's body, if it is dead: {body_conceals}
Surviving players: {surviving_players}
Your night actions so far (private; recorded by the game master):
{night_actions}
"""

CARD = RoleCard(
    side="lone_killer",
    name="Necromancer",
    lineup="from the second night, uses a dead player's night ability through their body.",
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
        closing="Decide whether to act tonight, through whom, and on whom.",
        target_field="necromancer_target",
        no_action="stay_put",
    ),
)
