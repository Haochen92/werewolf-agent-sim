"""Helping a human seat with its line, without saying anything for it.

Two helpers, both outside the engine (a server request, not a turn), returning text only;
the player still sends the line themselves, and failing costs nothing (they can type it).

- The day's speech is drafted by the seat's own agent: a preview of the turn it would take
  (``Agents.nodes.day.actors.preview_discuss``). ``player_direction`` writes the one block
  that preview may add after the agent's prompt: what the player asked for, their draft so
  far, their notes on the table. With none of that, nothing is added.
- The wolves' night talk still uses the note-rewriter here (``draft_from_notes``): rough
  notes ("4 dodging, agree with 8") become one plain line to the pack, saying only what the
  notes say; with no notes it writes a line of its own from the pack's talk.
"""

from logging import getLogger

from langchain_core.prompts import ChatPromptTemplate

from Agents.llm_factory import get_llm
from Agents.schemas.human_player import HumanTurnRequest

logger = getLogger(__name__)


# The pack the line is said to, shared by both prompts. {ask} is the notes, or the word that
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


def player_direction(
    notes: str,
    current: str = "",
    seat_notes: dict[str, str] | None = None,
    suspect: str = "",
) -> str:
    """The block a human player's steer adds after their agent's day-speech prompt, or ""
    when they gave none (the agent then gets exactly the prompt of the real turn).

    ``notes`` is what they want the line to do; ``current`` the line in their reply box,
    shown only alongside notes (it is what the notes revise); ``seat_notes`` and ``suspect``
    come from the player's own notebook on the table, by player id.
    """
    notes, current, suspect = notes.strip(), current.strip(), suspect.strip()
    table = "; ".join(f"{seat}: {' '.join(text.split())}"
                      for seat, text in (seat_notes or {}).items() if text.strip())
    lines = []
    if notes:
        lines.append(
            f"The human playing your seat gives you this direction for your message: {notes}")
        if current:
            lines.append(f"Their current draft of it: {current}")
    if table:
        lines.append(f"{'Their' if lines else 'The human playing your seat keeps these'} "
                     f"notes on the table: {table}")
    if suspect:
        lines.append(f"They suspect {suspect}.")
    if not lines:
        return ""
    if notes and current:
        ask = "Revise the draft as they ask"
    elif notes:
        ask = "Build your message around their direction"
    else:
        ask = "Weigh their notes as their reads, not as facts"
    lines.append(f"{ask}; everything above still applies. Speak this turn (pass_turn=false).")
    return "\n".join(lines)


def draft_from_notes(request: HumanTurnRequest, notes: str) -> str:
    """One line saying what ``notes`` say, in the player's voice, for the wolves' night talk
    turn ``request`` asks about. Blank ``notes`` leave the line to the model: one of its
    own, grounded in the talk so far.

    Raises RuntimeError, with the cause, when the model call fails or returns nothing; the
    caller tells the player to type the line instead. Never returns an empty string.
    """
    roster = [p for p in request.surviving_players if p != request.player_id]
    notes = notes.strip()
    prompt = DRAFTING_PROMPT if notes else FREE_DRAFTING_PROMPT
    try:
        reply = (prompt | get_llm()).invoke(
            {
                "player_id": request.player_id,
                "audience": "your fellow wolves, in private",
                "roster": ", ".join(roster),
                "dialogue": request.dialogue or "Nothing has been said yet today.",
                "pack_talk": f"\nYour pack's talk tonight:\n{request.wolf_channel}\n",
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
