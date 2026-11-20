# Visit-wording A/B: judge rubric

You judge single public lines that AI players said in a werewolf game, one turn each. Every line was
generated from a frozen game state (its case); `case_context.md` gives, per `case_id`, the true roles,
every player's private night records (ground truth), the claims on record and the last lines before the
turn. Read the context of a line's case before judging it.

The lines come from two prompt versions that word night actions differently: one says "visit" /
"follow" / "came to" / "went to", the other "target" / "track". Treat those words as synonyms. Judge
content only; never guess or mention which version a line came from.

## The rules that matter here

- A night action carried out on a player is a visit (targets them). A blocked action makes no visit.
- A Sentinel's watch on X shows who came to X that night (who targeted X), never where X went. The
  Sentinel itself is never listed in its own result.
- A Trailseer's follow (track) on X shows whom X went to (targeted), or that X went to no one; never who
  came to X.
- A visit shows only that someone came, not which action they took.
- Nobody is told that anyone visited them, or who: a player learns of visits to itself only from a watch
  or follow result, or a "You were roleblocked" notice. The watched or followed player does not see the
  watcher or follower.
- "X came to me" and "I followed X and X went to me" describe the same fact when the follow result says
  X visited the speaker. That is not an error.

## Per line, three labels

1. `mech` (1/0): the line states or relies on something false about these mechanics: e.g. that a watch
   shows where someone went, that a follow shows who came, that a visited player saw or would have seen
   its visitor, that a watcher should appear in its own result, that a visit reveals the action. A player
   lying about its own role or result is NOT `mech` unless the lie itself relies on wrong mechanics.
   Repeating someone else's claim faithfully is not `mech`.
2. `chew` (1/0): the line's main point is the rules or the words themselves (which ability shows what,
   the direction or wording of a result, "came to" vs "went to", watch vs follow language, what a term
   means) rather than players, claims and votes. A short clause of clarification in passing that serves
   a point about a player is 0.
3. `clear` (1/0/null; only for `slice == "report"`, else null): the speaker states its OWN night result
   correctly against its records (who, which night, which direction) and unambiguously. A deliberate lie
   by an evil speaker about a fake result counts as clear if it is internally coherent. A line that does
   not report its own result at all is 0. "(passed)" is 0.

Write one JSON object per line to your output file: `{"id": ..., "mech": 0|1, "chew": 0|1, "clear":
0|1|null, "note": "<= 20 words, only when a label is 1 (or clear is 0)"}`.
