"""Drafting a human seat's line from rough notes — the composing an LLM seat does for itself,
offered to the human.

An LLM seat writes its own message. A human on a phone, against a clock, often has only
fragments: "4 dodging, why abstain, agree with 8". This helper rewrites those into one plain
line in the player's own voice, saying only what the notes say. With no notes at all, the
player has left the line to it: it writes one of its own from the discussion so far, for the
player to read, edit or drop. It runs outside the engine (a server request, not a turn),
returns text only, and the player still has to send the line themselves. Failing here costs
nothing: the player can always type the line out.
"""

from logging import getLogger

from langchain_core.prompts import ChatPromptTemplate

from Agents.llm_factory import get_llm
from Agents.schemas.human_player import HumanTurnRequest

logger = getLogger(__name__)


# The table the line is said to, shared by both prompts. {ask} is the notes, or the word that
# there are none.
_TABLE = """You are {player_id}, speaking to {audience}. Living players: {roster}

The discussion so far:
{dialogue}
{pack_talk}
{ask}

The line:"""

DRAFTING_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You turn a Werewolf player's rough notes into the one line they will say out loud.

Write exactly one message, in the first person, as the player speaking: at most 60 words,
plain and direct, no flourish. Say only what the notes say. Never add an accusation, a claim
about anyone's role, or a fact the notes do not contain. "@player_4" or "@4" in the notes
means that player; refer to players by their ids, as the table does. Never mention the
notes, and never reveal or guess the player's own role. Output the line only: no quotes,
no preamble.""",
        ),
        ("human", _TABLE),
    ]
)

# No notes: the player asked for a line without saying what it should be about.
FREE_DRAFTING_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You write the one line a Werewolf player will say out loud next. The player has
left it to you: they will read your line, and send it, edit it or drop it.

Write exactly one message, in the first person, as the player speaking: at most 60 words,
plain and direct, no flourish. Make it useful to the discussion: a question to someone, a
read on someone and why, or a reply to what was just said. Ground it only in what has been
said and who is alive; never invent an event, a vote or a claim that did not happen. Refer
to players by their ids, as the table does. Never reveal or guess the player's own role.
Output the line only: no quotes, no preamble.""",
        ),
        ("human", _TABLE),
    ]
)


def draft_from_notes(request: HumanTurnRequest, notes: str) -> str:
    """One line saying what ``notes`` say, in the player's voice, for the discussion turn
    ``request`` asks about (the day table, or the pack at night). Blank ``notes`` leave the
    line to the model: one of its own, grounded in the discussion so far.

    Raises RuntimeError, with the cause, when the model call fails or returns nothing; the
    caller tells the player to type the line instead. Never returns an empty string.
    """
    to_pack = request.phase == "wolf_channel"
    roster = [p for p in request.surviving_players if p != request.player_id]
    notes = notes.strip()
    prompt = DRAFTING_PROMPT if notes else FREE_DRAFTING_PROMPT
    try:
        reply = (prompt | get_llm()).invoke(
            {
                "player_id": request.player_id,
                "audience": "your fellow wolves, in private" if to_pack else "the whole table",
                "roster": ", ".join(roster),
                "dialogue": request.dialogue or "Nothing has been said yet today.",
                "pack_talk": f"\nYour pack's talk tonight:\n{request.wolf_channel}\n" if to_pack else "",
                "ask": f"Notes:\n{notes}" if notes else "No notes: the line is yours to write.",
            },
            config={"run_name": f"draft_line_{request.player_id}"},
        )
        line = _one_line(reply.content)
    except Exception as exc:
        logger.warning("drafting a line for %s failed: %s", request.player_id, exc)
        raise RuntimeError(f"drafting failed: {exc}") from exc
    if not line:
        raise RuntimeError("drafting returned an empty line")
    return line


def _one_line(content) -> str:
    """The model's reply as the single line the player will send: whitespace collapsed and
    wrapping quotes dropped. Some backends return the content as parts, not one string."""
    if isinstance(content, list):
        content = " ".join(
            part.get("text", "") if isinstance(part, dict) else str(part) for part in content
        )
    return " ".join(str(content).split()).strip('"“” ')
