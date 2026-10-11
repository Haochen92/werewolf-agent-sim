"""The de-halo judge's prompt (Agents/memory/extraction/dehalo.py).

A second pass over a game's freshly extracted observations: it keeps a verdict only when the record
links the move to the outcome credited or blamed, and turns an outcome that merely followed the
move into 'unclear'. Chosen on the v8 smoke game, where Claude Haiku 5.5 caught every clear halo
verdict and erased none of the mechanically supported ones (evidence/memory_system/v8).
"""

DEHALO_PROMPT = """You are checking the verdicts of lessons extracted from one finished game of a ten-seat
Werewolf variant. Each lesson records what one player did and judges its net effect on that player's
side: positive, negative, mixed or unclear.

Your only job is to catch HALO verdicts: a verdict that credits or blames a move for an outcome the
record does not connect to that move. The usual sign is a verdict that simply follows which side won:
a town move called positive because town won, an evil move called negative because evil lost, a vote
or an abstain credited with something another player did later for their own reasons.

For each lesson:
- KEEP the verdict when something in the record (a message, a vote, a night result, a strategy note)
  links this move to the outcome it is credited or blamed for. A mechanical consequence counts (a
  sigil struck the attacker; a watch caught a visitor who was then voted out on that evidence).
- Change it to "unclear" when the outcome merely followed the move, or came from other players'
  own decisions that the record does not tie to this move.
- Change it to the other direction only when the record directly shows the move worked against the
  player's own side (for example, a town player voting to eliminate a player later revealed as town).
Do not judge whether the move was wise, and never reason about what a different move would have done.

GAME RULES:
{rules}

GAME RECORD:
{record}

FINAL STRATEGY NOTES:
{notes}

GAME OUTCOME: {outcome}

LESSONS:
{lessons}

Return one judgment for every lesson, by its index."""
