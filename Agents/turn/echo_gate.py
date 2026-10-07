"""The echo gate: a sweep turn that repeats a point already made today is held, not published.

When the scheduler gives the floor to a player who has not spoken (a proactive sweep turn), the
line it gets back is judged against the day's spoken lines before it is published: if an earlier
line makes the same point, the turn becomes a pass marker that keeps the text, so its author sees
on the next turn that it was never said (format_day_channel marks it) and the table hears each
point once. Reactive turns are never gated (an answer is owed even if it repeats), nor is a human
seat (resolve_decision checks both before calling here).

The test is the one the owner ruled for in Phase 2 step 4b: the same point, not merely "nothing
new". A line that adds a reason, a fact, a different target or a different conclusion is kept; a
player's claim about their own role or night action, or confirming or denying what was said about
themselves, is never a duplicate. The judge never weighs truth. It fails open: any error keeps the
line. One cheap call per sweep turn (Agents/llm_factory.get_llm_judge).
"""

from logging import getLogger

from langchain_core.prompts import ChatPromptTemplate

from Agents.llm_factory import get_llm_judge
from Agents.schemas import LineEchoVerdict
from Agents.schemas.game_events import DayChannel

logger = getLogger(__name__)


LINE_ECHO_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You read a Werewolf day discussion and one NEW line a player has just written, having read
the lines before it. Your job is to say whether the new line makes a point an earlier line already
made, so the table hears each point once.

Two lines make the same point when they say the same thing about the game: the same observation,
the same suspicion of the same player for the same reason, the same proposal. Different wording
does not matter. A line that adds a new reason, a new fact, names a different player, or draws a
different conclusion is a different point, even if it starts from the same observation. So is a
line that builds on an earlier point with a next step, a consequence or a request (asking to hear
from named players, asking a player to explain something), and a line that answers or challenges a
specific player about what they said, rather than merely agreeing with them.

Never a duplicate, whatever was said before: a player's claim about their OWN role or night action,
a player confirming or denying what was said about THEMSELVES, and a question that asks a specific
player something no earlier line asked.

The speaker read the earlier lines and was told not to repeat them, so most new lines are new.
Hold only a clear restatement: when in doubt, it is a different point.

Answer in three steps, in order: the new line's point in one sentence; what it adds that no earlier
line said (exactly "nothing" if nothing); then, only if it adds nothing, the player whose earlier
line already made the whole point (the first one that did). Judge only whether points coincide,
never whether they are true or wise.""",
        ),
        (
            "human",
            """The discussion so far:
{earlier}

The new line, from {player}:
{message}

First its point, then what it adds, then (only if it adds nothing) who said it first.""",
        ),
    ]
)


def line_echo_of(message: str, player: str, earlier: list[DayChannel]) -> str:
    """The player whose earlier spoken line makes the same point as ``message``, or "" when the line
    is new (or nothing was said yet, or the judge failed: the gate fails open)."""
    spoken: list[DayChannel] = []
    for entry in earlier:
        if entry.passed or not entry.message or entry.player == "game_master":
            continue
        spoken.append(entry)
    if not spoken:
        return ""

    numbered_lines: list[str] = []
    for index, entry in enumerate(spoken):
        numbered_lines.append(f"{index + 1}. {entry.player}: {entry.message}")
    try:
        verdict = (LINE_ECHO_PROMPT | get_llm_judge().with_structured_output(LineEchoVerdict)).invoke(
            {"earlier": "\n".join(numbered_lines), "player": player, "message": message},
            config={"run_name": f"echo_gate_{player}"},
        )
    except Exception as exc:  # fail open: a gate error must not silence anyone
        logger.warning("echo gate failed for %s: %s; keeping the line", player, exc)
        return ""

    # The hold needs both answers to agree: the line adds nothing, and a named earlier line made
    # the point. A small judge names the player a line credits ("player_5 is right that...") as
    # the line it repeats even when the line goes on to add a step, so the "adds" answer is the
    # one that decides (offline check 2026-10-07).
    adds = (verdict.adds or "").strip().lower().rstrip(".")
    if adds != "nothing":
        return ""
    named = (verdict.same_point_as or "").strip()
    if named == "" or named == player:
        return ""
    # Only a player who actually spoke earlier can be echoed; anything else is a judge slip.
    for entry in spoken:
        if entry.player == named:
            return named
    return ""
