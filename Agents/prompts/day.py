"""Day-phase prompt templates: each surviving role's discuss + vote ChatPromptTemplate.

Every template is the same scaffold — GAME_PREAMBLE, the role's CORE_STRATEGY, and a
shared transcript block (previous-day summaries + today's discussion) — wrapped around
two role-specific pieces: a framing paragraph and the one info line that role is given
(its private results, or the wolf rosters). Two factories (_discuss_template,
_vote_template) hold the shared text once so each role is a one-line table entry. Wolf
is the structural outlier: roster framing + a cover reminder on discuss, and its own
vote system block, which it passes as overrides.
"""

from langchain_core.prompts import ChatPromptTemplate

from Agents.prompts.common import (
    DAY_DISCUSS_RESPONSE_FORMAT,
    DISCUSSION_SILENCE_RULE,
    GAME_PREAMBLE,
    TONE_INSTRUCTION,
    build_system_prompt,
)
from Agents.prompts.memory import DAY_DISCUSSION_MEMORY_CONTEXT, DAY_VOTE_MEMORY_CONTEXT
from Agents.prompts.roles import (
    HEALER_CORE_STRATEGY,
    INVESTIGATOR_CORE_STRATEGY,
    SERIAL_KILLER_CORE_STRATEGY,
    VIGILANTE_CORE_STRATEGY,
    VILLAGER_CORE_STRATEGY,
    WOLF_CORE_STRATEGY,
)


# --- Shared transcript framing (identical across roles) ---

_DISCUSS_HEADER = """
Day {current_day} discussion.
{firing_brief}
"""

_DISCUSS_TRANSCRIPT = """
== Previous days summary ==
{day_summaries}

== Today's discussion ==
{day_channel}
=========================
"""

_VOTE_HEADER = "Day {current_day}. Time to vote!\n\n"

_VOTE_TRANSCRIPT = """
== Previous days summary ==
{day_summaries}

=== Today's discussion ===
{day_channel}
=================================

"""


# Voting system suffix shared by every village-aligned + SK role (wolf overrides it).
DAY_VOTE_SYSTEM_SUFFIX = """
You are {player_id}, a {player_role}.
You are now at the end of the current day of discussion. Vote to eliminate a player you suspect is a wolf.
You must vote from one of the surviving players, or "abstain" when it is offered.
You cannot vote for yourself.
{abstain_instruction}

You must respond with a valid JSON:
{{"adopted_strategy_keys": [1, 3], "vote_target": "exact player_id from the surviving players list, or \\"abstain\\"", "updated_strategy": "your updated private strategy note"}}
"""


# --- Factories ---

def _discuss_template(core_strategy, framing, context, *, trailer=""):
    """Build a day-discussion template from the shared scaffold.

    `framing` is the role's identity/goal paragraph, `context` the info line(s) it gets
    (surviving players + any private results), `trailer` an optional reminder after the
    transcript (only the wolf uses it, for the speak-like-a-villager cover note).
    """
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                build_system_prompt(
                    GAME_PREAMBLE,
                    core_strategy,
                    framing,
                    TONE_INSTRUCTION,
                    DAY_DISCUSS_RESPONSE_FORMAT,
                ),
            ),
            (
                "human",
                _DISCUSS_HEADER
                + context
                + _DISCUSS_TRANSCRIPT
                + trailer
                + DAY_DISCUSSION_MEMORY_CONTEXT
                + DISCUSSION_SILENCE_RULE,
            ),
        ]
    )


def _vote_template(context, closing, *, core_strategy=None, system=None):
    """Build a day-vote template from the shared scaffold.

    `context` is the info line(s) (surviving players + any private results), `closing`
    the role's final "cast your vote" instruction. Most roles share DAY_VOTE_SYSTEM_SUFFIX
    via `core_strategy`; the wolf passes a fully custom `system` block instead.
    """
    sys_block = system or build_system_prompt(GAME_PREAMBLE, core_strategy, DAY_VOTE_SYSTEM_SUFFIX)
    return ChatPromptTemplate.from_messages(
        [
            ("system", sys_block),
            (
                "human",
                _VOTE_HEADER + context + _VOTE_TRANSCRIPT + DAY_VOTE_MEMORY_CONTEXT + closing,
            ),
        ]
    )


# --- Discussion templates ---

VILLAGER_DAY_DISCUSS = _discuss_template(
    VILLAGER_CORE_STRATEGY,
    """
You are {player_id}, a {player_role}.
As a villager, you have no special abilities. Use reasoning and social deduction to figure out
who the wolves are and convince others to vote them out.
""",
    """
Surviving players: {surviving_players}
""",
)


HEALER_DAY_DISCUSS = _discuss_template(
    HEALER_CORE_STRATEGY,
    """
You are {player_id}, the {player_role}.
During the day, speak as a normal villager while protecting your cover. Use reasoning and
social deduction to help the village identify wolves without exposing your role.
""",
    """
Surviving players: {surviving_players}
""",
)


INVESTIGATOR_DAY_DISCUSS = _discuss_template(
    INVESTIGATOR_CORE_STRATEGY,
    """
You are {player_id}, the {player_role}.
As the investigator, you can use your investigation result to guide your decision.
Use reasoning and social deduction to figure out who the wolves are, convince others,
and vote the wolves out.
""",
    """
Surviving players: {surviving_players}
Investigation results: {investigator_results}
""",
)


WOLF_DAY_DISCUSS = _discuss_template(
    WOLF_CORE_STRATEGY,
    """
You are {player_id}, the {player_role}.
As the wolf, conceal your real identity and convince everyone else that you are a villager.
If any of your fellow wolf allies are suspected, try to convince the villagers otherwise
without revealing your own identity.
""",
    """Surviving villagers: {surviving_villagers}.
Surviving allies: {surviving_wolves}.
""",
    trailer="""Based on the discussion, try to speak like a villager. Do NOT reveal your allies identities.
""",
)


SERIAL_KILLER_DAY_DISCUSS = _discuss_template(
    SERIAL_KILLER_CORE_STRATEGY,
    """
You are {player_id}, the {player_role}.
You are playing alone against everyone. During the day, pose as an ordinary villager:
join the hunt for the wolves, deflect suspicion from yourself, and never reveal that you
are the serial killer. You can be voted out, so blending in is survival.
""",
    """
Surviving players: {surviving_players}
""",
)


VIGILANTE_DAY_DISCUSS = _discuss_template(
    VIGILANTE_CORE_STRATEGY,
    """
You are {player_id}, the {player_role}.
You are on the village's side. Use reasoning and social deduction to help find the wolves
and the serial killer. Whether to stay hidden as an ordinary villager or to claim your role
is your own decision and can change with the situation: staying hidden keeps you safe, while
claiming — or hinting at what your shots have taught you — can lend weight to your reads but
paints a target on you (both the wolves and the serial killer gain from removing you).
""",
    """
Surviving players: {surviving_players}
What you have learned from your shots: {vigilante_results}
""",
)


# --- Vote templates ---

VILLAGER_DAY_VOTE = _vote_template(
    "Here are the surviving players: {surviving_players}\n",
    "\nCast your vote. Choose the player you find most suspicious.\n",
    core_strategy=VILLAGER_CORE_STRATEGY,
)


HEALER_DAY_VOTE = _vote_template(
    "Here are the surviving players: {surviving_players}\n",
    "\nCast your vote. Choose the player you find most suspicious while protecting your cover.\n",
    core_strategy=HEALER_CORE_STRATEGY,
)


INVESTIGATOR_DAY_VOTE = _vote_template(
    "Here are the surviving players: {surviving_players}\n"
    "Here are your investigation results: {investigator_results}\n",
    "\nCast your vote. Choose the player you find most suspicious.\n",
    core_strategy=INVESTIGATOR_CORE_STRATEGY,
)


WOLF_DAY_VOTE = _vote_template(
    "Surviving villagers: {surviving_villagers}\n"
    "Known surviving wolves: {surviving_wolves}\n",
    "\nCast your vote. Choose the target that best preserves your cover.",
    system=build_system_prompt(
        GAME_PREAMBLE,
        WOLF_CORE_STRATEGY,
        """
You are {player_id}, a {player_role}.
You are now voting to eliminate a player.
You cannot vote for yourself.
Avoid voting for your wolf allies by default, unless refusing to join an overwhelming majority against a clearly doomed ally would expose you.
Try to vote in a way that does not raise suspicion about your identity;
usually target a villager, but preserve your cover by voting for a wolf ally when the village consensus is decisive to vote out that exposed wolf ally.
You may also vote "abstain" when it is offered (an abstain plurality means no elimination) — blending with an abstaining village can be good cover, and a no-lynch day costs the village a chance to find a wolf.
{abstain_instruction}

You must respond with a valid JSON:
{{"adopted_strategy_keys": [1, 3], "vote_target": "exact player_id from the surviving players list, or \\"abstain\\"", "updated_strategy": "your updated private strategy note"}}
""",
    ),
)


SERIAL_KILLER_DAY_VOTE = _vote_template(
    "Here are the surviving players: {surviving_players}\n",
    "\nCast your vote. Vote in the way that best deflects suspicion from you and removes a threat to your survival.\n",
    core_strategy=SERIAL_KILLER_CORE_STRATEGY,
)


VIGILANTE_DAY_VOTE = _vote_template(
    "Here are the surviving players: {surviving_players}\n"
    "What you have learned from your shots: {vigilante_results}\n",
    "\nCast your vote. Choose the player you find most suspicious.\n",
    core_strategy=VIGILANTE_CORE_STRATEGY,
)
