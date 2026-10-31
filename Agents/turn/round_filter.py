"""The filter a collected opening round goes through before its lines are published.

One cheap call on the opening's lines in the order they will be published, drawn that day, so a
repeat is judged against the lines the players will read before it (``filter_openings``): an
allow-list. An opening may hold a role claim, the speaker's own night action or result, or a
challenge to an earlier claim; agents often speak when told to pass, so the call labels each line's
kind and everything else is held, as is a repeat of an earlier opening that is not a claim (two players
claiming the same role is the contest the opening is for). The label is kept on the entry for
analysis.

A held line becomes a pass marker that keeps the text for the record only: no prompt shows it, its
author's included, and the note written with it is dropped (format_day_channel; collect_round). The call judges only the kind of a statement, never
its truth, so a false claim is kept. It fails open: any error, or a missing verdict, keeps the
line. A human's line is never held (collect_round undoes a verdict against one; the entry itself
does not know the seat). The sweep turns' echo gate, which judges one line against the day so far,
is Agents/turn/echo_gate.py; the parallel proactive round this module once filtered went
sequential on 2026-10-07 (step 4c).
"""

from logging import getLogger

from langchain_core.prompts import ChatPromptTemplate

from Agents.llm_factory import get_llm_judge
from Agents.schemas import OpeningVerdicts
from Agents.schemas.game_events import DayChannel, DiscussionPassReason

logger = getLogger(__name__)


OPENING_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You read the opening statements several players in a Werewolf game wrote AT THE SAME TIME, before
the day's discussion, none of them having seen the others. An opening may hold only three kinds of
statement, and your job is to label each line's kind:

- claim: the speaker claims a role for themselves, or claims a role that someone else claimed (a
  counterclaim). Two players claiming the same role are both claims.
- night_action: the speaker states their OWN night action or its result: whom they protected,
  checked, shot, watched, followed, blocked or set a sigil on, a bet or a pick they made, that they
  held fire or did nothing, and what they saw or learned.
- challenge: the speaker disputes a claim made on an earlier day, with a reason.
- repeat: the line only repeats an earlier line in this list, and is not a claim.
- other: anything else: a deduction, a suspicion, advice, a comment on the game, padding around one
  of the kinds above that is itself mostly something else.

A line that holds one of the three kinds plus a sentence of something else (a question, a deduction
from it) is still that kind.
Judge only what kind of statement it is, never whether it is true.""",
        ),
        (
            "human",
            """The lines, in order:
{lines}

Give one verdict per line, in the same order.""",
        ),
    ]
)

ALLOWED_OPENING_KINDS = {"claim", "night_action", "challenge"}


def filter_openings(entries: list[DayChannel]) -> list[DayChannel]:
    """The opening round's entries with everything but a claim, an own night action or a
    challenge turned into held pass markers; every spoken line gets its kind label. Order kept."""
    spoken = [entry for entry in entries if not entry.passed and entry.message]
    if not spoken:
        return entries

    kinds = _judge_kinds(spoken)
    if kinds is None:
        return entries
    # The speaker's own structured fields settle the kind when they say it: a line that filled in a
    # night action (each kept only when the line names it; turn/resolve.py), or claimed a role the
    # line names. The judge had labelled such lines "other" (persona voice games, 2026-10-18).
    for entry in spoken:
        declared = _declared_kind(entry)
        if declared is not None:
            kinds[entry.player] = declared

    out: list[DayChannel] = []
    for entry in entries:
        if entry.passed or not entry.message:
            out.append(entry)
            continue
        kind = kinds.get(entry.player)
        if kind is None:  # no verdict for this player: keep the line
            out.append(entry)
        elif kind in ALLOWED_OPENING_KINDS:
            out.append(entry.model_copy(update={"opening_kind": kind}))
        else:
            held = _held(entry, DiscussionPassReason.OPENING_FILTERED)
            out.append(held.model_copy(update={"opening_kind": kind}))
    return out


def _declared_kind(entry: DayChannel) -> str | None:
    """"night_action" or "claim" when the speaker's own fields say so and the line bears it out;
    None leaves the line to the judge."""
    if entry.claimed_night_actions:
        return "night_action"
    if entry.claim != "none" and entry.claim.replace("_", " ") in entry.message.lower():
        return "claim"
    return None


def _judge_kinds(spoken: list[DayChannel]) -> dict[str, str] | None:
    """player -> the kind label; None = the call failed, so the caller keeps everything."""
    numbered = "\n".join(f"{i + 1}. {entry.player}: {entry.message}" for i, entry in enumerate(spoken))
    try:
        result = (OPENING_PROMPT | get_llm_judge().with_structured_output(OpeningVerdicts)).invoke(
            {"lines": numbered},
            config={"run_name": "opening_filter"},
        )
    except Exception as exc:  # fail open: a filter error must not silence anyone
        logger.warning("opening filter failed: %s; keeping every line", exc)
        return None
    kinds: dict[str, str] = {}
    for verdict in result.verdicts:
        kinds[verdict.player.strip()] = verdict.kind
    return kinds


def _held(entry: DayChannel, reason: DiscussionPassReason) -> DayChannel:
    """The pass marker that replaces a held line: the text is kept for its author only. Its
    addressed targets stay on the marker for records; the closing and the reactive queue skip
    every pass."""
    return entry.model_copy(update={
        "message": "",
        "passed": True,
        "pass_reason": reason,
        "gated": True,
        "gated_candidate": entry.message,
    })
