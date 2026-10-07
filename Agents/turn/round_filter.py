"""The filters a collected round goes through before its lines are published.

Two filters, one cheap call each, on the lines of a round in seat order:

- ``filter_openings`` (the opening round): an allow-list. An opening may hold a role claim, the
  speaker's own night action or result, or a challenge to an earlier claim; agents often speak
  when told to pass, so one call labels each line's kind and everything else is held, as is a
  repeat of an earlier opening that is not a claim (two players claiming the same role is the
  contest the opening is for). The label is kept on the entry for analysis.
- ``filter_round_echoes`` (the proactive round): several players writing at the same moment on
  the same board often make the same point in different words, which is what ended concurrent
  discussion in Phase A. The call says, for each line, whether an EARLIER line makes the same
  point; the first of each group stays.

A held line becomes a pass marker that keeps the text, so its author sees on the next turn that
it was never said (format_day_channel marks it). Both calls judge only the kind or sameness of a
statement, never its truth, so a false claim is kept. Both fail open: any error, or a missing or
inconsistent verdict, keeps the line. A human's line is never held (collect_round undoes a
verdict against one; the entry itself does not know the seat).
"""

from logging import getLogger

from langchain_core.prompts import ChatPromptTemplate

from Agents.llm_factory import get_llm_judge
from Agents.schemas import OpeningVerdicts, RoundEchoVerdicts
from Agents.schemas.game_events import DayChannel, DiscussionPassReason

logger = getLogger(__name__)


ROUND_ECHO_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You read the lines several players in a Werewolf discussion wrote AT THE SAME TIME, none
of them having seen the others. Your job is to find lines that make the same point, so the table
hears each point once.

Two lines make the same point when they say the same thing about the game: the same observation,
the same suspicion of the same player for the same reason, the same proposal. Different wording
does not matter. A line that adds a new reason, a new fact, names a different player, or draws a
different conclusion is a different point, even if it starts from the same observation.

Never a duplicate, whatever else was said: a player's claim about their OWN role or night action, a
player confirming or denying what was said about THEMSELVES, and a question that asks a specific
player something no earlier line asked.

For each line, in order, answer: does an EARLIER line in this list make the same point? If so,
name that earlier line's player (the first one that does). If not, leave it empty. Judge only
whether points coincide, never whether they are true or wise.""",
        ),
        (
            "human",
            """The lines, in order:
{lines}

Give one verdict per line, in the same order.""",
        ),
    ]
)


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
  investigated or shot, that they held fire, and what they learned.
- challenge: the speaker disputes a claim made on an earlier day, with a reason.
- repeat: the line only repeats an earlier line in this list, and is not a claim.
- other: anything else: a deduction, a suspicion, advice, a comment on the game, padding around one
  of the kinds above that is itself mostly something else.

A line that holds one of the three kinds plus a sentence of something else is still that kind.
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


def filter_round_echoes(entries: list[DayChannel]) -> list[DayChannel]:
    """The round's entries with echoes turned into held pass markers. Order is kept.

    ``entries`` are one round's lines in the order they will be published. Passes pass through
    untouched; the spoken agent lines go to the judge together. A line is held only
    when its named "same point" line comes EARLIER in the order and is itself kept, so a chain of
    duplicates collapses onto the first and a verdict pointing forward or at an unknown player is
    ignored.
    """
    spoken = [entry for entry in entries if not entry.passed and entry.message]
    if len(spoken) < 2:
        return entries

    same_point_as = _judge(spoken)
    if same_point_as is None:
        return entries

    kept_players: set[str] = set()
    out: list[DayChannel] = []
    for entry in entries:
        if entry.passed or not entry.message:
            out.append(entry)
            continue
        earlier = same_point_as.get(entry.player, "")
        is_echo = earlier and earlier != entry.player and earlier in kept_players
        if is_echo:
            out.append(_held(entry, DiscussionPassReason.ROUND_ECHO))
        else:
            kept_players.add(entry.player)
            out.append(entry)
    return out


def _judge(spoken: list[DayChannel]) -> dict[str, str] | None:
    """player -> the earlier player whose line makes the same point ("" if none). None = the call
    failed, so the caller keeps everything."""
    numbered = "\n".join(f"{i + 1}. {entry.player}: {entry.message}" for i, entry in enumerate(spoken))
    try:
        result = (ROUND_ECHO_PROMPT | get_llm_judge().with_structured_output(RoundEchoVerdicts)).invoke(
            {"lines": numbered},
            config={"run_name": "round_echo_filter"},
        )
    except Exception as exc:  # fail open: a filter error must not silence anyone
        logger.warning("round echo filter failed: %s; keeping every line", exc)
        return None
    verdicts: dict[str, str] = {}
    for verdict in result.verdicts:
        verdicts[verdict.player.strip()] = (verdict.same_point_as or "").strip()
    return verdicts


def _held(entry: DayChannel, reason: DiscussionPassReason) -> DayChannel:
    """The pass marker that replaces a held line: the text is kept for its author only. Its
    addressed targets stay on the marker: an echoed accusation still counts its accuser for the
    closing defence (closing_speakers; owner, 2026-10-07), while the reactive queue skips held
    lines, so nobody is asked to answer a line that was never shown."""
    return entry.model_copy(update={
        "message": "",
        "passed": True,
        "pass_reason": reason,
        "gated": True,
        "gated_candidate": entry.message,
    })
