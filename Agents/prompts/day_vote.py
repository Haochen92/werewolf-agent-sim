"""Day-vote prompt templates: each surviving role's elimination-vote ChatPromptTemplate.

Every template is the same scaffold — GAME_PREAMBLE, the role's CORE_STRATEGY, a vote system block,
and a shared transcript block (previous-day summaries + today's discussion) — wrapped around the one
info line that role is given (its private results, or the wolf rosters) and a closing "cast your vote"
instruction. The `_vote_template` factory holds the shared text once so each village-aligned role is a
one-line table entry; the wolf and the serial killer each pass a fully custom vote system block, since
their win conditions make "remove an anti-village threat" wrong.
"""

from langchain_core.prompts import ChatPromptTemplate

from Agents.prompts.common import GAME_PREAMBLE, build_system_prompt
from Agents.prompts.memory import DAY_VOTE_MEMORY_CONTEXT
from Agents.prompts.roles import (
    HEALER_CORE_STRATEGY,
    INVESTIGATOR_CORE_STRATEGY,
    SERIAL_KILLER_CORE_STRATEGY,
    VIGILANTE_CORE_STRATEGY,
    VILLAGER_CORE_STRATEGY,
    WOLF_CORE_STRATEGY,
)


# --- Shared transcript framing ---

_VOTE_HEADER = "Day {current_day}. Time to vote!\n\n"

_VOTE_TRANSCRIPT = """
== Previous days summary ==
{day_summaries}

=== Today's discussion ===
{day_channel}
=================================

"""


# Voting system suffix shared by the village-aligned roles (villager, healer,
# investigator, vigilante). The wolf and the serial killer each have their own vote
# system block — their win conditions make "remove an anti-village threat" wrong.
DAY_VOTE_SYSTEM_SUFFIX = """
You are {player_id}, a {player_role}.
You are now at the end of the current day of discussion. Vote to eliminate the player you believe is most likely to be a threat to the village — a wolf or the serial killer.
You must vote from one of the surviving players, or "abstain" when it is offered.
You cannot vote for yourself.
{abstain_instruction}

You must respond with a valid JSON:
{{"strategy_verdicts": [{{"strategy_index": 1, "verdict": "follow", "why": "short reason vs your current board"}}], "memory_applicability": [{{"memory_index": 1, "verdict": "partly_applies", "why": "short reason vs your current board"}}], "vote_target": "exact player_id from the surviving players list, or \\"abstain\\"", "updated_strategy": "your updated private strategy note"}}
"""


# --- Factory ---

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
    "Known surviving wolves: {surviving_wolves}\n"
    "\nYour private wolf channel (night coordination + game-master notes):\n{wolf_channel}\n"
    "This channel is private to the wolves. Never quote, reference, or hint at its contents in public discussion — parroting night coordination outs you.\n",
    "\nCast your vote. Choose the target that best preserves your cover.",
    system=build_system_prompt(
        GAME_PREAMBLE,
        WOLF_CORE_STRATEGY,
        """
You are {player_id}, a {player_role}.
You are now voting to eliminate a player.
You cannot vote for yourself.
Avoid voting for your wolf allies by default, unless refusing to join an overwhelming majority against a clearly doomed ally would expose you.
Try to vote in a way that does not raise suspicion about your identity. The serial killer is also your enemy — if it is exposed, or looks likely to survive into an endgame where it threatens your win, helping the village remove it can be worth a vote. Otherwise target a villager, but preserve your cover by voting for a wolf ally when the village consensus is decisive to vote out that exposed wolf ally.
You may also vote "abstain" when it is offered (an abstain plurality means no elimination) — blending with an abstaining village can be good cover, and a no-lynch day costs the village a chance to find a wolf.
{abstain_instruction}

You must respond with a valid JSON:
{{"strategy_verdicts": [{{"strategy_index": 1, "verdict": "follow", "why": "short reason vs your current board"}}], "memory_applicability": [{{"memory_index": 1, "verdict": "partly_applies", "why": "short reason vs your current board"}}], "vote_target": "exact player_id from the surviving players list, or \\"abstain\\"", "updated_strategy": "your updated private strategy note"}}
""",
    ),
)


SERIAL_KILLER_DAY_VOTE = _vote_template(
    "Here are the surviving players: {surviving_players}\n",
    "\nCast your vote. Vote in the way that best deflects suspicion from you and removes a threat to your survival.\n",
    system=build_system_prompt(
        GAME_PREAMBLE,
        SERIAL_KILLER_CORE_STRATEGY,
        """
You are {player_id}, a {player_role}.
You are now voting to eliminate a player. You work alone — every wolf and villager is your enemy, and you win by being among the last left standing.
You cannot vote for yourself.
Vote to remove whoever most threatens your survival — usually whoever is closing in on you, or a strong player who could organize the others against you — while casting your vote in a way that keeps you read as ordinary town and never hints that you are the serial killer.
You may also vote "abstain" when it is offered (an abstain plurality means no elimination) — blending with an abstaining village can be good cover.
{abstain_instruction}

You must respond with a valid JSON:
{{"strategy_verdicts": [{{"strategy_index": 1, "verdict": "follow", "why": "short reason vs your current board"}}], "memory_applicability": [{{"memory_index": 1, "verdict": "partly_applies", "why": "short reason vs your current board"}}], "vote_target": "exact player_id from the surviving players list, or \\"abstain\\"", "updated_strategy": "your updated private strategy note"}}
""",
    ),
)


VIGILANTE_DAY_VOTE = _vote_template(
    "Here are the surviving players: {surviving_players}\n"
    "What you have learned from your shots: {vigilante_results}\n",
    "\nCast your vote. Choose the player you find most suspicious.\n",
    core_strategy=VIGILANTE_CORE_STRATEGY,
)
