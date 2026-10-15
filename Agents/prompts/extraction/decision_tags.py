"""The decision tagger's prompt (Agents/memory/extraction/decision_tags.py).

Observations extracted before 2026-10-13 do not say which decision they describe, so the
deterministic grade of that decision cannot be attached to them (decisions §13). This pass reads one
game's record and names, for each observation, the day or night of its decision and, for a wolf's
night, which of the pack's turns it was. It tags; it never judges.
"""

DECISION_TAG_PROMPT = """You are tagging lessons extracted from one finished game of a ten-seat Werewolf variant
with the decision each lesson is about. You do not judge the lessons.

Each lesson was written about one role's play in one phase (day discussion, day vote, or night
action). Find, in the game record, the decision of that role in that phase that the lesson describes:
match what the lesson says the role did (its target, claim, vote or night action, and what happened
around it) to where that role did it in the record.

- decision_day: the number of that decision. Day N's discussion and day N's vote are N. Night N is
  the night after day N: the record writes its actions "Night N:", and the wolves' talk that night
  "[Day N, Round r]". Use 0 only when the lesson describes a pattern over several decisions rather
  than one.
- pack_turn: only for a chanteuse or illusionist night_action lesson, the pack's turn it is about:
  chat (the wolves' talk that night, rounds 1 to 3), kill (the carrier naming the victim, written
  "[Day N, Round 4] player_x votes: ..."), skill (this wolf's own block or conceal, written
  "Night N: player_x (chanteuse) block ..." or "(illusionist) conceal"), or several. For every other
  lesson: none.

GAME RULES:
{rules}

GAME RECORD (the day discussion with the votes, the wolves' night talk, and every night action as the
engine resolved it):
{record}

ROLES: {roles}

LESSONS:
{lessons}"""
