# v8 memory: experiment log (ten-seat seeding)

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

## 2026-10-11 — Extraction model: 2.5-pro → 3.8 Flash

**Why.** The pilot cost about $2 a game. Langfuse puts extraction at $1.00–1.19 a game on
gemini-2.5-pro ($1.25 in / $10 out per 1M). Its visible output (24–30k tokens a game) explains
about $0.30 of that; the rest is mostly its thinking, billed as output.

**Run.** Two pilot games (`286816b0` Serial Killer + Speculator, `cc80ecdf` Necromancer + Fortune
Teller) were re-extracted from their saved extraction cases with the same prompts, the explicit
prefix cache and the dealt roles only:
- `extraction_inputs_from_frozen_case` → `extract_postgame_per_cell`;
- primary and backup both set to the candidate model;
- token usage taken from LangChain's usage callback.

Outputs are in `data/extraction_model_comparison/`.

Making the run fixed a bug: a saved case carries no lineup, so a re-run had an empty rules block.
The lineup is now rebuilt from the roles.

| Model (per 1M in/out) | Cost, game 1 / 2 | Observations | Unclear verdicts | Player IDs | Counterfactual phrasing* |
|---|---|---|---|---|---|
| 2.5-pro ($1.25/$10) | $1.16 / $1.19 | 45 / 52 | 5 / 3 | 6 / 4 | 5 / 3 |
| 3.8 Flash ($0.75/$3.75, promo to 2026-12-31) | ~$0.36 / ~$0.32 | 32 / 34 | 3 / 1 | 0 / 0 | 6 / 2 |
| 3.5-flash-lite ($0.30/$2.50) | ~$0.07 / ~$0.06 | 45 / 43 | 5 / 10 | 5 / 18 | 0 / 0 |

\*A regex for "had I/we", "would have", "instead of", "should have" in the approach or end-of-game
field: a pointer for reading, not a measure. The 3.8 Flash and 3.5-flash-lite costs are computed
from token counts at Google's list prices. Vertex prices were not confirmed; Google's Vertex pricing
page did not load. 3.8 Flash spent about 58–70k thinking tokens a game, most of its cost.

**Read** (same cells side by side: Chanteuse, Necromancer and Sentinel nights; one reading):
- **3.8 Flash** was specific and mechanically right: the reanimated body seen at a watched door, a
  borrowed shot stopped by the Healer. Its end-of-game claims point at what happened ("reporting
  the watch on day five directly exposed the surviving wolf").
- **2.5-pro** is not clearly better. Several end-of-game fields are the bare word "positive" or
  "negative", and one Necromancer verdict calls killing a wolf "against my win condition".
- **3.5-flash-lite** wrote trivial observations (the Necromancer's forced night-1 stay) and thin
  verdicts, and leaked player IDs into 18 of 43 observations in one game.

**Ruling (owner, 2026-10-11): switch extraction to gemini-3.8-flash.** The backup becomes
gemini-2.5-pro: a different family and quota pool, used only when the primary fails. Expected cost
is about $0.9 play plus about $0.35 extraction a game, against about $2 on 2.5-pro. After the promo
ends, 3.8 Flash's price doubles.

**Considered, not built:** batch extraction (Vertex batch, 50% off).
- On Vertex the cache discount (90% off cached input) and the batch discount do not stack.
- Extraction input is already mostly cached, so batch would mainly halve the output.
- About $2–3 on a 12-game seeding, for about 250–350 lines (defer extraction, build and submit the
  job through Cloud Storage, parse, write the store offline).
- Two things are open: whether a Vertex batch job can use an explicit cache at all, and the cache's
  hourly storage cost while a job queues.
- Listed in plan §9.4.

## 2026-10-11 — The day extracted as two calls: discussion and vote

**Why.** In the pilot, one day call per role tagged nearly every day observation `day_vote`: a day
moment ends in a vote, so the vote became its outcome. An evil player's discussion turn retrieves
from `day_discussion`, which was nearly empty (0 for the Chanteuse and the Speculator).

**Change.** Each role now gets three calls: discussion, vote, night. Each day call is told what
belongs to the other, and every observation is tagged with the call's phase.

**Check.** Pilot game `cc80ecdf` re-extracted with gemini-3.8-flash:

| | Discussion | Vote | Night | Observations | Extraction cost |
|---|---|---|---|---|---|
| Before (one day call) | 0 | 16 | 18 | 34 | ~$0.32 |
| After (two day calls) | 16 | 18 | 19 | 53 | ~$0.50 |

The new discussion lessons are about the talk itself:
- the Chanteuse defending its partner's fake Investigator claim;
- the Illusionist claiming Investigator when the Trailseer caught it at the victim's door;
- the Necromancer's silence while its outlier vote was examined;
- the Fortune Teller's read of a cornered claimant, which set up its scoring bet.

Expected cost is now about $0.9 play plus about $0.5 extraction a game.
