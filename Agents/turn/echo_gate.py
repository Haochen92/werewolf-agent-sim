"""The echo gate: a sweep turn that adds nothing to today's discussion is held, not published.

When the scheduler gives the floor to a player who has not spoken (a proactive sweep turn), the
line it gets back is judged against the day's spoken lines before it is published: if it adds
nothing, the turn becomes a pass marker that keeps the text for the record only: no prompt shows it,
its author's included, and the strategy note written with it is dropped (format_day_channel;
actors.discuss), so the table hears each point once and the author holds no belief it was said. Reactive turns are never gated (an answer is owed even if it repeats), nor is a human
seat (resolve_decision checks both before calling here).

The bar (owner, 2026-10-18, replacing Phase 2 step 4b's "the same point"): the open floor no longer
tells seats that a pass costs nothing, so they speak by default and the gate does the sorting. It
holds a restatement (of a line or of the record), an agreement with no new reason, a repeated
request and filler; it keeps a new fact, a reading of the seat's own with its reason (even against
the table), and a question or test nobody has asked. A player's claim about their own role or night
action, or confirming or denying what was said about themselves, is always kept. On the open-floor
lines judged blind in the silence calibration, it held 12 of 29 restatements and none of 36
worthwhile lines (evidence/gameplay/data/silence_calibration/). The judge never weighs
truth. It fails open: any error keeps the line. One cheap call per sweep turn at low thinking
(Agents/llm_factory.get_llm_judge; minimal held 9 of 29).
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
            """You read a Werewolf day discussion and one NEW line a player has just written on the
open floor, having read the lines before it. Your job is to say whether the new line adds anything,
so the table hears each point once and no filler.

A line adds something when it has at least one of:
- a fact the table does not have yet: the speaker's claim about their OWN role, or their own night
  action or result. Repeating what the morning report, the game master's record or an earlier line
  already says is not a new fact;
- a reading of its own: an inference, a consequence or a point of view that no earlier line put,
  with its reason. It counts even when it disagrees with the table, and even when it starts from an
  earlier observation, as long as it gives a new reason or draws a different conclusion;
- a question or a test aimed at a specific named player that no earlier line put to them, or a
  concrete check that names who should do what. A general call ("whoever has a result, post it",
  "let's hear claims", "everyone name a vote") adds something only if no earlier line made one.
A player confirming or denying what was said about THEMSELVES always adds something.

A line adds nothing when all it does is one or more of:
- restate a point an earlier line made, or what the record already says, in any wording;
- agree with an earlier line without a new reason;
- repeat a request or a question an earlier line already made, even in other words;
- filler: say there is little to go on, urge caution or patience, say the speaker will wait or hold
  their information, or give general advice that names no player, fact or test.

Judge the line part by part: if any one part adds something, the line adds something.
Judge only whether it adds, never whether it is true or wise.

Answer in three steps, in order: the new line's point in one sentence; what it adds (exactly
"nothing" if it adds nothing); then, only if it adds nothing, the player whose earlier line it
restates, agrees with or repeats (the first one), or "none" if it is filler that repeats no
particular line.""",
        ),
        (
            "human",
            """The discussion so far:
{earlier}

The new line, from {player}:
{message}

First its point, then what it adds, then (only if it adds nothing) whose line it repeats, or "none".""",
        ),
    ]
)


def line_echo_of(message: str, player: str, earlier: list[DayChannel]) -> str:
    """Why ``message`` is held: the player whose earlier spoken line it repeats, or "filler"; "" when
    it adds something (or nothing was said yet, or the judge failed: the gate fails open)."""
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
        verdict = (LINE_ECHO_PROMPT | get_llm_judge("low").with_structured_output(LineEchoVerdict)).invoke(
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
    if named.lower() == "none":
        return "filler"
    if named == "" or named == player:
        return ""
    # Only a player who actually spoke earlier can be echoed; anything else is a judge slip.
    for entry in spoken:
        if entry.player == named:
            return named
    return ""
