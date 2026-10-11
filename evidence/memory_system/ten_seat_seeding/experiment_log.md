# Ten-seat memory seeding: experiment log

The plan is `plan.md` (§9 is the final plan). This log records what was run and what came of it.
Nothing here is a claim that memory improves play.

## 2026-10-11 — Pilot: one game per lineup, extraction → synthesis

**Run.** Four AI-only games, one per lineup (`run_batch --configs extract_only --cycle-lineups
--no-memory-seed --dump-store-dir memory_stores/ten_seat_pilot`). Retrieval off, extraction on for
every dealt role, fresh store. Code at `c8115536`: the §9.2 prompts, cells and gating. Game model
gemini-3.5-flash-lite (thinking medium); extraction gemini-2.5-pro (backup 3.5-flash); Vertex.
Records: `batch_results/ten_seat_pilot/`. Store: `memory_stores/ten_seat_pilot/`. Both are
gitignored.

| Game | Lone killer, neutral | Winner | Days | Observations kept |
|---|---|---|---|---|
| 1 | Serial Killer, Speculator | town | 5 | 45 |
| 2 | Serial Killer, Fortune Teller | town | 5 | 44 |
| 3 | Necromancer, Speculator | Necromancer | 6 | 53 |
| 4 | Necromancer, Fortune Teller | town | 5 | 52 |

**Synthesis.** Run offline on a copy (`memory_stores/ten_seat_pilot_synth/`): `consolidate()`
with credit, prune and eviction off, and no database or bootstrap store. The production tick was
not used: it writes generations to the Postgres the deployed server shares, and its default
bootstrap is the nine-seat `v7_fixed` store. Synthesis model gemini-3.1-flash-lite.
- 51 strategy points in 23 of 36 cells.
- The other 13 cells had fewer than the 4 new observations synthesis requires (`synth_min_new_obs`).

**Cost.** $8.08 for the four games, from the Langfuse session total. That is about $2.02 a game:
about $0.70 play (the balance runs' figure), the rest extraction and dedup. The synthesis pass is
not included.

**Coverage.**
- 194 observations, in all 36 cells of the 12 roles. Only dealt roles were extracted.
- Town day is included (it is extracted for review).
- **Skew:** the merged day cell tags almost every day observation `day_vote`. `day_discussion` has
  0–4 per cell, and 0 for the Chanteuse and the Speculator. An evil player's discussion turn
  retrieves from `day_discussion`, so that namespace will be thin unless retrieval also reads
  `day_vote` or the tagging changes.

**Quality (one read of samples, not a measurement).**
- **Verdicts:** 103 negative, 61 positive, 18 mixed, 12 unclear. Only 6% unclear.
- **The evidence rule did not stop every counterfactual conclusion.** A Chanteuse observation ends
  "Had I blocked the Sigilist instead, my partner would have survived", a move the game never
  tested, using a role the Chanteuse did not know at the time.
- **Supported links do appear,** e.g. a Sentinel's watch "when claimed on Day 2, directly led to the
  town … eliminating the Illusionist".
- **The naming rule broke in 16 of 194 observations** (`player_N` in a field). No strategy point has
  one.
- **The strategy points read as ten-seat play:** sigils, borrowed bodies, Trailseer and Sentinel
  claims; no Seer, Villager or Werewolf. Some are weak or generic (the Healer's night 1 "randomly
  select a target"), and one uses Town of Salem jargon ("NK").
- **Not done:** the plan's by-eye comparison of old and new extraction prompts on the same cells.

**Leak screen.** Game 4 was flagged with 4 "leaks", all false positives. The Chanteuse wrote a
phrase in the wolf chat on night 2 that the Illusionist legitimately reads, and the same phrase was
in its private read. `check_*` read why-text should exempt text the author also wrote where the
recipient can see it.
