"""Note prompt v1 (Changed / Reasoning / Plan), tested 2026-10-16 and NOT adopted.

Screened against the current wording on 14 frozen cases, Haiku 5.5 low, n=4, judged blind by a chat
subagent: fact errors 15 -> 27 of 56 samples, notes carrying a wrong deduction 15 -> 28, overclaims
6 -> 11; R1 still passed 7 of 8. Record: evidence/reasoning_failures/experiment_log.md §6.
The live wording stayed as it was (Agents/prompts/memory/context.py).
"""

# The private note (owner, 2026-10-16; evidence/reasoning_failures/experiment_log.md §5-6): a seat's
# note is shown on its next turn and replaced by the one it writes. The old wording ("Update your
# strategy notes based on new information") let a stance written early in the day, re-read every
# turn, keep a healer silent after the evidence changed. The note now separates what changed, the
# reasoning (reads are hypotheses; claims are not facts) and the plan, re-decided each turn, while
# keeping the conclusions that still hold (the vote's old "carry forward what still matters").
_NOTE_HEAD = """Your private note:
    Your previous private note is a reminder of your reasoning and plans, which may be mistaken or
    outdated (the game master's record and the transcript outrank it):
    {previous_strategy}

    Write a replacement note in three short parts. It replaces the previous note, so preserve the
    conclusions that still hold, and the plans you still endorse after the check below.
    Changed: any relevant new evidence or claims, or a mistake you now notice in your previous
    reasoning. Say what this changes; if nothing changes, say so briefly.
    Reasoning: the conclusions the evidence supports, and how certain they are. Treat your reads as
    hypotheses to check, not as evidence. Keep the rules and the game master's results (its
    announcements and your own night results) apart from players' claims and your own inferences:
    the transcript shows what a player said, not that it is true.
"""
_NOTE_TAIL = """    At most six sentences in all. This note is private and will not be shared with other players.
"""

DAY_DISCUSSION_MEMORY_CONTEXT = "{observations_block}{strategy_points_block}\n" + _NOTE_HEAD + """    Plan: what you will do this turn, and why. Say whether your updated conclusions warrant changing
    your previous plan, and whether sharing information or challenging a claim would help enough to
    justify speaking.
""" + _NOTE_TAIL


# The vote asks for updated_strategy, which replaces the note, so it must show the note it replaces:
# without it, anything only the note remembered was lost at every vote (audit 2026-10-03, finding 3).
DAY_VOTE_MEMORY_CONTEXT = "{observations_block}{strategy_points_block}\n" + _NOTE_HEAD + """    Plan: your vote, and why, and what to carry into the night. Say whether your updated conclusions
    warrant changing your previous plan.
""" + _NOTE_TAIL


NIGHT_ACTION_MEMORY_CONTEXT = "{night_observations_block}{strategy_points_block}\n" + _NOTE_HEAD + """    Plan: your action tonight, and why. Say whether your updated conclusions warrant changing your
    previous plan.
""" + _NOTE_TAIL
