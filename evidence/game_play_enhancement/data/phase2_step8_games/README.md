# Phase 2 step 8: the comparison games (2026-10-07)

Four AI-only games on the Phase 2 day (the opening round, the sequential sweep with the per-line
echo gate, the closing defence; discussion_evidence.md §7.4), played on `gemini-3.5-flash-lite`
with memory off, at HEAD `d9e9aee9` (the engine and server code of that commit; the working tree's
uncommitted changes were frontend-only). Game 3 ran into Vertex 429s and a third of its model calls
went to the rescue model (`gemini-3.1-flash-lite`), so game 4 was played as its replacement; game 3
is kept and marked. The counts are in `counts.md`; the reading, the verdict and the investigator finding are in `report.md`.

## Files

Per game (`gameN`):

- `gameN.manifest.json`: game id, git SHA (and the dirty paths at the time), runtime fingerprint,
  model and thinking level, the full run config, start/end times, duration, token usage by model
  (the server's `UsageMeter`), cost in USD (`server.game.usage.game_cost`), the leak check's verdict.
- `gameN.record.json`: the final state in the batch-record shape (roles, the whole `day_channel`
  with every entry's round, firing reason and pass reason, day summaries, day and night resolutions,
  investigator results, the leak check's list).
- `gameN.chunks.jsonl`: every chunk the game streamed the production way (`stream_mode=["updates",
  "custom"], subgraphs=True, version="v2"`), each with the time it arrived (`t`). Day and round
  durations are read from these.
- `gameN.calls.json`: one row per model call: the graph node that made it, its namespace, model,
  start and end time. Calls per day are attributed from these.

Shared:

- `counts.json` / `counts.md`: the per-game, per-day counts, for these games and the baselines.
- `baselines/replay_832404e9.json`: the v2 website game's replay as the endpoint served it on
  2026-10-07 (cached so the counts can be rerun offline).
- `judge/<game>/{reads.jsonl,summary.json,review.md}`: the evidence judge's reads (gemini-2.5-pro),
  for these games and for `832404e9`, re-read with the same judge for a like-for-like comparison.

## How it was produced

- The games: `evaluation/experiments/phase2_step8_capture.py --label gameN`, one process per game (the
  day graph's turn cache is process-wide, so games never share it). It is the step 6 capture script
  (which mirrors `Agents.main.run_game`'s setup and streams the production way) copied into the repo
  and changed in three ways: arrival times on the chunks, a model-call log, and the final state
  written out as a record. No Langfuse handler is attached.
- The counts and the judge: `evaluation/experiments/phase2_step8_counts.py` (add `--judge` to run the
  judge where it is not cached). The judge is `evaluation/experiments/discussion_evidence.py`'s,
  reused unchanged (`read_messages`, `score`, `review_sheet`).

## Reading the counts

- "n/a" means the record lacks the field the count needs; nothing is approximated. The v2 game has no
  rounds, no timing and no call log; the 4b smoke game has no votes; the 4c rerun is two replayed days.
- Calls per day are the model calls whose start falls inside the day's window (the root chunk before
  the day's first chunk to the `DAY_PHASE` chunk) and whose namespace is the day graph. The echo
  gate's calls run inside the `discuss` node, so `discuss` counts turns plus gate calls; the counts
  also re-derive the gate's calls from the transcript (`gate_calls_derived`), and the two agree on
  every voting day of the four games but one (game 4, day 3: one call more than derived, a retry).
- "cap" compares the day's spoken lines before the closing with the utterance cap for the day's
  survivors (`max(6, ceil(3 x alive))`); it says whether the cap could have bitten, not that it did.
- The leak check in each manifest flags "wolf_channel in wolf_vote phase": a false positive of
  `check_wolf_channel_isolation`, whose list of wolf output keys predated the separate `wolf_vote`
  turn (fixed 2026-10-07, after these games). No other leak was flagged.
