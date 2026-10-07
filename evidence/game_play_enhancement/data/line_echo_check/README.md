# Echo gate: offline check, one line at a time (2026-10-07)

What the sweep turns' echo gate (`Agents/turn/echo_gate.py`, Phase 2 step 4c) would hold, run over
material that existed before any live sweep: the Phase 2 chunk catalogue's game (its proactive lines,
spoken and held, judged one at a time in transcript order) and the first 20 June voting days (the
sequential proactive picks of the old scheduler, each judged against the lines before it that day).
Produced by `evaluation/experiments/line_echo_gate_check.py --limit 20`; `results.jsonl` has every day
with its kept and held lines, `report.md` the held lines next to the line they were judged to repeat.

Three things to know when reading it:

- The June lines had already passed the novelty gate of the time, so every hold here is a line a
  gate once kept. The June rate therefore says how much stricter this gate is than that one, not how
  much a live sweep would hold; the catalogue game is the closer specimen, and small (16 lines).
- The prompt was revised twice on this material, re-running the same 20 days each time:
  - v1 (the parallel round's criterion, asked of one line): June 43 of 146 held (29%). Reading the
    holds showed a pattern: a line that credits an earlier speaker and then adds to their point
    ("player_5 is right that..., so let's also look at...") was held as a repeat of that speaker,
    which is the name-and-advance move the discussion prompt asks for.
  - v2 (the criterion spelled out: building on a point, asking to hear from named players,
    answering a specific player are different points; hold only a clear restatement): 39 of 146
    (27%). The wording alone changed little.
  - v3 (the verdict restructured so the judge first states the line's point, then what it adds,
    and may name a repeated line only when it adds nothing; the code holds only on that pair):
    27 of 146 (18%). This is the shipped form; the results here are from it.
- Two holds in the v3 sample go against the standing rule that a player confirming or denying what
  was said about themselves is never a duplicate (a healer confirming the investigator's check on
  them; a player denying they led a lynch). The engine does not rely on the judge for that rule:
  `resolve_decision` skips the gate when the line is tagged as a response to a player whose earlier
  line named the speaker.

Reading the v3 June holds by hand, about half are clear repeats and the rest are lines that add a
step or a target the judge did not credit. A small judge on this question errs toward holding; the
step 8 comparison games should count held lines per day alongside restated lines per day before
the threshold is tuned further.
