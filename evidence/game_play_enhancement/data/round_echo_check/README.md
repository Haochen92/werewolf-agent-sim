# Round echo filter: offline check (2026-10-07)

What the proactive round's echo filter (`Agents/turn/round_filter.py`) would hold, run over material
that existed before any live round: the two Phase 2 smoke games' real proactive rounds and the June
games' voting days (each day's spoken proactive lines treated as if said at once). Produced by
`evaluation/experiments/round_echo_filter_check.py`; `results.jsonl` has every round with its kept
and held lines, `report.md` the held lines next to what they were judged to repeat, for reading.

Two things to know when reading it:

- The June lines were spoken one after another, each speaker seeing the earlier ones, and the
  novelty gate of the time had already removed some echoes. So the June hold rate understates how
  much a true parallel round repeats itself. The smoke rounds are the honest specimens.
- The step-4b smoke game's day 2 and day 3 each show a proactive round twice. That transcript was
  played before the duplicate-publication bug was fixed (the second proactive round re-published
  the first round's lines), so the checker read each duplicated block as its own round. The holds
  in the repeated blocks are the same lines twice, not extra evidence.

The prompt was revised once from this material: the vigilante's "I can confirm your read on me" was
held as a repeat of "player_2's check looks solid", so the prompt now says a player's claim about
their own role or night action, or confirming or denying what was said about themselves, is never a
duplicate. The results here are from the revised prompt.
