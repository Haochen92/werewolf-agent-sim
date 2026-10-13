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
- The other 13 cells got no points. *Corrected 2026-10-11:* this first said they had fewer than
  the 4 new observations synthesis requires (`synth_min_new_obs`). That gate is waived for a cell
  holding fewer than 3 points (`synth_replenish_floor`), so on a fresh store synthesis ran on every
  cell with observations. Two of the 13 were empty (Chanteuse and Speculator `day_discussion`); in
  the rest, synthesis made no point from what was there (the Speculator's `day_vote` had 6
  observations), and the Fortune Teller's night cell got 2 points from 3 observations in 2 games.

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

## 2026-10-11 — The smoke game, halo in verdicts, and the de-halo pass

**Smoke game** (`batch_results/v8_smoke/`, code at `4a78bf7f`): one game with the day split, the
death-night records and gemini-3.8-flash extraction.
- Serial Killer and Speculator, 3 days, town win; leak check clean; 30 extraction calls, none failed.
- 43 observations; the "never told" marks on all three night deaths.
- $1.03, now priced correctly in Langfuse (3.6 and 3.8 Flash entries added at the promo price).

**Claude's read of the game and its 43 observations:**
- **42 factually correct.** One invented the Serial Killer citing the Investigator's check.
- **The retaliation chain is supported:** the Sigilist's note names the player who voted against it.
- **Halo:**
  - town (won): about 21 positive, 1 negative of 28; evil (lost): 7 negative, 1 positive of 11;
  - five day-2 abstains credited with the Sigilist's later kill;
  - the Vigilante's hold called positive; the Investigator's check on the Serial Killer called positive.
- **Redundancy:** the day-3 vote extracted 7 times, the day-2 abstain 5 times, once per role.
- **Missed:** the pack's attack on the immune Serial Killer told the wolves who the lone killer was.

**Prompt fixes** (`de4134b2`): outcome is not credit; skip a vote that just joined the majority; the
pack's night results in the Chanteuse and Illusionist drivers.
- Halo about halved (~20% → ~10% by one reading).
- The duplicate abstains are gone.
- The day-3 vote is still extracted per role, and the immune-target lesson is still missed.

**Extraction by model** (same game, same fixed prompts; `data/dehalo_compare/`):

| Model | Cost | Observations | Halo (one reading) | Errors | Player IDs |
|---|---|---|---|---|---|
| gemini-3.8-flash | $0.51 (cached) | 40 | ~4–5 | ~0 | 0 |
| Claude Haiku 5.5 | $0.11 (no cache hit; ~$0.06 with) | 47 | ~1–2 | 2 | 5 |
| Claude Sonnet 5.5 | $1.79 (no cache hit; ~$0.85 with) | 52 | ~1 | 1 small | 0 |

The Claude runs did not reuse the cached prefix: each cell's output schema precedes it. All three
missed the Sigilist's note as evidence and the immune-target lesson.

**De-halo judges** on the 40 gemini-3.8-flash observations. "Clear halo" means the 4 cases a reader
would call halo; "wrongly erased" means the 3 mechanically supported verdicts turned to unclear.

| Judge | Cost | Changed | Clear halo caught (of 4) | Supported verdicts wrongly erased |
|---|---|---|---|---|
| gemini-3.8-flash | $0.077 | 10 | 4 | 3 |
| Claude Sonnet 5 | $0.168 | 3 | 3 | 0 |
| Claude Sonnet 5.5 | $0.113 | 11 | 4 | 1–3 |
| Claude Haiku 5.5 | $0.006 | 5 | 4 | 0 |

**Ruling (owner): extraction stays on gemini-3.8-flash with the fixed prompts, plus a de-halo pass**
(`395cfa7f`).
- It is configurable: on/off, model and thinking level (`ExtractionConfig.dehalo`, environment
  defaults `MEMORY_DEHALO_*`), set to Claude Haiku 5.5 by default.
- It is a deliberate exception to the no-extra-judge rule, and the memory pipeline's first Claude
  dependency (`CLAUDE_API_KEY`).
- One live run of the stage on the original 43 observations revised 6 verdicts. It also turned the
  wasted first sigil to "unclear", which the comparison run had kept. The judge varies between runs;
  these are single samples, one game, one reader.
- The Claude call is not traced through Langfuse; its tokens are in the de-halo record.

## 2026-10-11 — Bulk seeding: 12 games, merge and offline synthesis

**Run.** 12 AI-only games, three per lineup, retrieval off, extraction on (gemini-3.8-flash, fixed
prompts) with the de-halo pass (Claude Haiku 5.5). Three parallel `run_batch` processes of 4 games
(`--cycle-lineups`, so each process dealt every lineup once), each dumping to its own store
(`memory_stores/v8_seed_{a,b,c}`); code at `7640156e`. Records: `batch_results/v8_seed_*/`. Per-game
table: `data/seeding/games.json`.
- Winners: town 6, wolves 4, Serial Killer 1, Necromancer 1; 3–6 days. No leak flagged, no failures.
- **Rate limits.** Three processes on one Vertex quota hit 429s on the game model (flash-lite); the
  stall rescue covered most. Process c's fourth game (Necromancer + Fortune Teller) lost five
  discussion turns to technical passes and then had five day votes cast at random by the fallback in
  one day, so it was stopped before extraction and replaced by one game run alone afterwards
  (`v8_seed_d`, `--lineup-offset 3`, added for this). Of the 12 kept games, one has a single missed
  discussion turn (process b, game 4); no kept game has a random vote. Next time: two processes, not
  three.
- **De-halo cut off on long games.** Haiku 5.5 thinks by default, and thinking counts against
  `max_tokens`: four games passed 16k and the JSON was cut off, so the pass was skipped and verdicts
  kept as extracted. Fixed (`efa232de`: 32k with an explicit timeout); the four games were
  backfilled after their process finished (`scripts/dehalo_backfill.py`: the same pass on the
  extraction case, the matching stored verdicts rewritten, the record marked `backfilled`).
- **Cost:** $16.46 from the Langfuse session totals (including the stopped game's partial run),
  about $1.35 a game, plus about $0.15 of Haiku de-halo calls (four of them cut off). The merge's
  dedup and synthesis are not included.

**De-halo over the 12 games:** 146 of 567 verdicts revised (26%), against 5–6 of 40–43 on the smoke
game. Mostly negative → unclear (90) and positive → unclear (35); 6 negative → positive.
- A read of one game's 19 revisions: most are fair (blame for a later death or a lost vote that the
  record does not tie to the move), a few over-correct. A Fortune Teller's death after it did not
  self-bet was turned to unclear although a self-bet gives immunity by rule; a Sigilist's vote to
  unclear although the next day's voters plausibly cited it.
- The stored verdict mix after de-halo: 217 unclear, 169 positive, 129 negative, 38 mixed of 553.
  The originals are in the de-halo records, so the pass can be re-judged or reverted.

**Merge.** `merge_new_obs` into `memory_stores/v8_seed` (fresh store; flash-lite dedup triage, no
merge writes): 562 observations, 9 cross-process duplicates collapsed, 553 kept.

**Coverage** (`data/seeding/coverage.md`):
- Every retrieved cell has observations from 5–12 distinct games (the drawn roles 5–6 of their 6
  possible, the fixed roles 11–12). No top-up games needed.
- The day split worked: `day_discussion` holds 8–25 observations per cell (the pilot had 0–4).

**Synthesis.** Offline `consolidate()` on a copy (`memory_stores/v8_seed_synth`; credit, prune and
eviction off; gemini-3.1-flash-lite): 165 points, 150 after point dedup, in all 36 cells (1–9 a cell).
The first attempt failed on 429 twelve times; every retry succeeded. No player IDs in any point.
Provenance (`source_observations`, `synthesis_log.jsonl`) is in the store.

**Rule errors in strategy points** (`data/seeding/rule_screen.md`, one read):
- 14 of 150 points state a rule the game does not have (8 high confidence, 6 medium). Examples: a borrowed
  block is announced as reanimated; a Healer's save is "essentially permanent";
  on a save the Illusionist's visit is not seen; a sigil can punish a lone killer. Sigilist and
  Illusionist mechanics account for 8.
- Traced to source observations, the errors are mostly synthesis over-generalising from facts that
  are right (two Healer saves of the same player → permanent protection), not extraction mistakes.
  Synthesis is given the rules block and still does it.
- **Found on the way, outside memory:** the agents' rules text says the pack's "carrier rotates
  unless the pack agrees otherwise", but `pack_carrier` only rotates by seat order. Two points
  follow the rules text.

## 2026-10-12 — Synthesis on Claude Sonnet 5.5

**Ruling (owner):** not flash-lite for synthesis. Sonnet 5.5 chosen (Claude credits; Gemini had
$24.90 left). Built a Claude path for synthesis (`8bfc7995`) and, on the owner's word, batch mode for
offline Claude runs (`c5a6ba0c`, `df2efb0b`: one Message Batch at half price, the opening lines and
rules block cached; a two-request probe took 5.4 min and read the cache).

**Run** (direct calls; batch was built during it): `memory_stores/v8_seed_synth_sonnet`, from the same
merged store. 112 calls, 1.11M input and 180k output tokens, **$4.02** (about $1.65 batched and
cached). 176 points, 164 after point dedup, all 36 cells, no player IDs.

**Rule screen** (`data/seeding/rule_screen_sonnet.md`): 32 of 164 points (20%) state a wrong rule,
against 14 of 150 (9%) for flash-lite. The points are about three times longer and more specific;
stating more mechanics, they state more wrong ones. A stronger synthesis model alone does not fix
it. The long points also lengthen every memory-on game prompt.

**Claude's read of advice quality, both stores** (7 cells side by side: Healer, Investigator and
Sentinel night; Chanteuse discussion; Illusionist and Serial Killer vote; Speculator night. One reader):
- **flash-lite:** short (median 33 words) and readable, but mostly advice that needs no game data
  ("prioritize contested players", "avoid rogue votes"), few conditions, rarely a reason.
- **Sonnet 5.5:** decision rules with a trigger, an action, a reason and an exception, often tied
  correctly to mechanics: a Not suspicious check also clears the Serial Killer and the neutral; a
  Speculator dying unpicked loses; a watch on a suspect shows who visits them, not where they go; a
  lone-killer's only exit is the vote. More useful where right. Problems besides the 20% rule errors:
  - long (median 109 words, max 178), often several directives in one point;
  - **town day advice inside town night cells** (a Sentinel night point that is all about what to
    share on Day 2): 31 of 34 town night points mention claiming, sharing or reporting (a regex
    pointer, confirmed in the cells read). Town day is not retrieved by ruling, and this brings it
    back through the night cells;
  - some situations narrowed to one game's endgame, and one anecdote ("in one game a Necromancer…").
- Implied synthesis-prompt changes: mechanics only as the rules block states them; one directive
  per point, about two sentences and its reason; advice about the cell's own action only; no game
  anecdotes.

## 2026-10-12 — Re-synthesis with mechanics, phase and length rules (batched)

**Prompt** (`ccb9b96a`): rely on mechanics only as the rules state them; prescribe only the cell's
own phase; one move per point in at most three sentences. Anecdotes stay (owner). Conflicting points
in a cell stay too: credit is meant to settle them once memory-on games exist (owner).

**Run:** Sonnet 5.5 as one Message Batch (`TickConfig(batch=True)`), store
`memory_stores/v8_seed_synth_sonnet2`. All 112 requests returned parsed, no retries; 350k uncached
input, 583k cache reads, 199k cache writes, 170k output: **$1.51** (against $4.02 direct). 185
points, 176 after dedup, all 36 cells, no player IDs.

| | flash-lite | Sonnet | Sonnet, revised prompt |
|---|---|---|---|
| Points | 150 | 164 | 176 |
| Words per action (median / max) | 33 / 53 | 109 / 178 | 66 / 102 |
| Wrong rule (one read) | 9% | 20% | 11% |
| Town night points giving day advice | — | most | 1 of 32 |

The structure Sonnet brought (trigger, move, reason, exception) is kept at about half the length.
Remaining errors cluster on the Sigilist's result, the lone killers' immunity to a sigil, and Day 1
(`data/seeding/rule_screen_sonnet2.md`).

**Production candidate `memory_stores/ten_seat_v1`** (owner, 2026-10-12: keep the flagged points
flagged, serve only the valid ones). The 19 points of `rule_screen_sonnet2.md` carry a `rule_flag`
(screen, confidence, claim, rule) in `v8_seed_synth_sonnet2`; `ten_seat_v1` is that store without
them: 157 points, at least one in every cell. Not yet loaded by a server: a fresh directory embeds
its points on first load (gemini-embedding-2).

## 2026-10-12 — Embedder: gemini-embedding-2 → Qwen3-Embedding-8B

**Why (owner):** Gemini credits will lapse and gemini-embedding-2 ($0.20/M, multimodal) is the
priciest embedder on OpenRouter. Compared live 2026-10-12 (OpenRouter's model API, Voyage's pricing
page): Qwen3-Embedding-8B $0.01/M, voyage-4-lite $0.02, voyage-4 $0.06 (Voyage direct: 200M tokens
free), OpenAI text-embedding-3-small $0.02. Chosen: Qwen3-8B on the existing OpenRouter key (open
weights, 32k context, sizes 32–4096). At our volume (the whole store ~0.2M tokens; a game well under
0.1M) every option costs cents.

**Built:** `MEMORY_EMBEDDING_MODEL` (default now `qwen/qwen3-embedding-8b`, `507116a7`, `85daf18a`);
OpenRouter hosts pinned to Nebius then DeepInfra (two hosts' vectors for one text differ, cosine
~0.998; SiliconFlow serves fp8); every cosine threshold read per model from
`SIMILARITY_THRESHOLDS`; a store cache now records its embedding model and is refused under
another (`a32a396c`: before, a switch would have served Gemini vectors to Qwen queries); seeding
batches 64 records a call on OpenRouter (`6a7823f5`: 13 min → 40 s for 710 records). Canary re-pinned.

**Thresholds** (`data/embedder_migration/`):

| Threshold | Gemini | Qwen | How |
|---|---|---|---|
| dedup candidate | 0.55 | 0.36 | below every within-cell pair on both (Gemini's lowest 0.670, Qwen's 0.476) |
| synthesis clustering | 0.65 | 0.46 | same |
| batch clustering | 0.70 | 0.50 | same |
| retrieval dedup gate | 0.87 | 0.80 | percentile: p68 of within-cell situation pairs |
| obs content keep / discard | 0.935 / 0.96 | 0.72 / 0.94 | dedup_v2 golden labels, zero errors |
| SP action keep / discard | 0.81 / 0.93 | 0.61 / 0.88 | dedup_v2 golden labels, zero errors |

- The prefilter thresholds were set on gemini-embedding-001 and never remapped in July. On the
  golden labels, gemini-embedding-2 needs keep < 0.50 for zero errors (production 0.81 / 0.935), so
  today's Gemini prefilter auto-keeps some labelled duplicates. Left as is: that path is retiring.
  Percentile mapping would have carried the miscalibration to Qwen (keep 0.90 / 0.69).
- Qwen's prefilter decides fewer pairs without the LLM (obs 7.5%, SPs 16% of golden cases).

**Retrieval check** (observation situations as stand-in queries, top-5 strategy points in the
cell, 236 queries): 81% of the top 5 shared, same first point 55%. Read of five first-point
disagreements: Qwen better on 2, Gemini on 2, neither on 1. No sign of worse retrieval; the gate's
relevance check (judge: Claude Haiku 5.5, owner 2026-10-12) on real queries is the real test,
replaying the same queries on both embeddings.

**`ten_seat_v1` re-indexed on Qwen** (cache signature recorded); a healer-night query returned three
on-target protection points in 0.8 s.

## 2026-10-12 — The gate, part one: seven memory-on games, their cost, and a read of 96 lookups

**Games.** Four on Claude Haiku 5.5 (one per lineup) and three on GPT-6 Luna, every seat AI, memory on
for every role (strategy points only, `ten_seat_v1`, extraction off), on the code after the day's query
fixes (`a0282a71`): the rules, dead roster and seat's exact state in the query, D4's lookup reuse with the
wolf night split. All seven completed. The first Luna launch crashed every game on day 2's opening: a
round turn's payload has no `current_round`, which the lookup's trace name read (fixed `bdb2ff76`; no
live memory game since the rounds were built).

**Cost** (Langfuse token counts priced from the catalogue; the Haiku runs shared a session per two games):
Luna $0.155, $0.188, $0.217 a game, memory lookups 20–28% of it (30–61 lookups); Haiku about $0.15 and
$0.21 a game, lookups about 40% (about 45–60 lookups). The Haiku turns' cached tokens did not reach
Langfuse then (fixed `d9e346fd`) and the situation prompt was sent uncached (fixed `1ad07a81`), so the
Haiku lookup share should fall well below that now.

**The read** (`evaluation/experiments/v8_gate_lookups.py`; `data/gate/`): 352 lookups (517 decisions),
a sample of 96 stratified by model, role and phase, read by four Claude Sonnet subagents against the
rules texts with the games' true roles (`data/gate/read/`, a summary per part):

- Lessons: 39 of 268 fit the decision (15%), 79 partly (29%), 150 do not (56%); 36 of 96 lookups had at
  least one fitting lesson. Day phases worst (discussion 7% fit, vote 13%), night 19%; Luna 18%, Haiku 11%.
- The pattern every reader reported: retrieval matches the role, not the game's stage. Lessons for an
  exposed or dead partner, the last three or four players, night 1 or a pick already made were served
  to seats on day 2 or 3 with seven to nine alive, and the similarity score did not track fit (one
  healer lookup: the worst-fitting lesson scored 0.887, the best 0.829). Each lesson does store the board
  it was learned on (players alive, partner revealed, uses left), but retrieval does not use it (this
  entry first said no stage field existed; corrected in the next entry).
- The seats mostly rejected the lessons that did not fit (seat verdicts sound in 65, mixed in 25, never
  wrong outright), so the harm is cost and prompt room more than misplay; the mixed cases include a few
  where a fitting lesson was dismissed or a lesson nudged a worse move.
- Situations: 37 of 96 had at least one error. Eight were the query's own swing line ("the game can end
  within one more elimination" beside a parity count of five or six), which counted the town's win and,
  after a concealed death, any possible placement of the body (wording fixed `6c3d2329`). The rest are
  the model's: the necromancer believing it is invisible to checks, a no-effect sigil read as clearing,
  an empty follow read as clearing a body attacker, miscounts.
- Leaks: no lesson names a player id; 17 lookups had lessons carrying one past game's detail ("in one
  case ended the wolf faction outright"), mild. No situation stated a concealed role as fact.

**Gate, relevance: not met.** One lesson in seven fits; the store is too small and too mixed in stage for
a similarity search to choose well, which the outside review had predicted for its small cells.

## 2026-10-12 — The gate, part two: a stage filter on the stored boards

**Question.** Every lesson stores the board it was learned on, from extraction through synthesis, and
the seat's own board is computed exactly. Would leaving out lessons from another stage fix relevance?
v7 already has a soft version (`dimension_gating.py`: a ±30% score tilt on the alive bucket and the swing
flag, never a drop), off by default and off in the gate games.

**Check 1: are the stored counts right?** (free, offline) The 196 extracted observations that carry
uses left (or the vigilante's bullets) against the true count, replayed from each seeding game's nights
with the engine's own spending rule (`resolution._spent`): 165 exact (84%), 29 give the count *after*
the night's action rather than before it, 2 impossible (a vigilante with 3 shots). As some-left vs
none-left, 7 of 196 are wrong, nearly all a last use written as 0, which would hide a "spend your last
one" lesson from the seats it is for. The field's description does not say before or after; the
seat's value is before.

**Check 2: the replay** (`evaluation/experiments/v8_stage_filter_replay.py`; `data/gate/stage_filter/`).
The 96 read lookups searched again from the situations the seats wrote (one embedding call each;
the unfiltered top three reproduced what the seats were shown in 91 of 96), with a lesson left out when
its alive bucket (8+, 5–7, 4 or fewer), partner-lost flag or uses-left (some vs none) differs from the
seat's. The 28 lessons the filter promoted that the first read had not judged were read by one Sonnet
subagent with the same rubric (`read.jsonl`).

| Lessons shown | Lessons | Fit | Partly | Do not fit | Lookups with a fit | Empty lookups |
|---|---|---|---|---|---|---|
| As in the gate games | 264 | 15% | 30% | 55% | 36 | 0 |
| Filtered, the gap left empty | 114 | 25% | 35% | 39% | 28 | 25 |
| Filtered, the gap refilled from the cell | 143 | 22% | 36% | 43% | 30 | 18 |

- The filter drops 69% of the misfits (101 of 146) and a quarter of the fitting lessons (10 of 39), all
  of those on the alive bucket. A looser alive rule (within two players) keeps 6 more fitting lessons
  but 32 more misfits.
- Refilling from the cell mostly adds misfits: of the 28 promoted lessons, 2 fit. The cells hold few
  lessons for any one stage, so a filtered lookup should show fewer lessons, not different ones.
- Uses left never applied here: no sampled seat had run out, and no stored night lesson was learned at
  zero uses. The Speculator's lessons that assume a pick already made (four lookups in part one's read alone) are the case it
  would catch, but the Speculator's cells have no uses field (the pick is its one use; `uses=1`).

**Reading.** The stored board is a real stage signal: filtering on it lifts fit from 15% to 25% and
removes most misfits, at a cost of a quarter of the fitting lessons and 25 lookups left with nothing
(which also saves their prompt room). It does not reach a store where most lessons fit; that needs more
lessons per stage (more source games) as well. Next (owner): uses left defined as before the action and
added to the cells that lack it (the Speculator, the limited-use roles' day cells), then re-extraction.

## 2026-10-12 — Offline extraction: a Claude batch check, for cost

**Run** (`scripts/extract_batch.py`, code at `ba9cd549`; `batch_results/extraction_runs/check_*`): the two
pilot games (`286816b0`, `cc80ecdf`) extracted from their backfilled inputs by Claude Haiku 5.5 and
Sonnet 5.5, thinking off, 30 calls a game (every dealt role's discussion, vote and night), each game's
first call direct to write its prefix to the 1-hour cache and the other 58 calls as one Message Batch;
the de-halo pass (Haiku) as a second batch. No call was lost; both batches took about 10 minutes.

**The cache did not work: no call read it.** A game's 30 calls share a 16.3k-token prefix, but each has
its own output schema, and the schema is part of Claude's cache key (a probe: the same prefix under
another schema wrote anew, under the same schema read it). So every call wrote the whole prefix, at
the 1-hour rate (2x input). The fix is to give the schema as text after the prefix rather than as an
enforced output format (a reply that does not parse is retried with the format).

| | Haiku 5.5 | Sonnet 5.5 |
|---|---|---|
| Cost of the 2 games, as run | $0.135 | $2.55 (de-halo $0.01 of it) |
| Per game, as run | $0.07 | $1.27 |
| Per game, prefix cached (estimate) | ~$0.03 | ~$0.45, about 60% of it output |
| Observations (2 games) | 146 | 136 |
| With a player id in the text | 74 (51%) | 9 (7%) |
| `uses_left` some-vs-none wrong | 3 of 77 | 2 of 73 |

For comparison, 3.8 Flash with the day split cost about $0.50 a game online (the day-split entry) and
wrote no player ids in its comparison games. The run cost $2.69 against an estimate of under $0.50: the
estimate assumed the cache worked. `claude_structured` had also priced the 1-hour cache writes as plain
input (its summaries said $1.68); fixed.

**Reading.** Haiku is out for extraction: it writes player ids into half its observations, as Flash Lite
did. Sonnet, with the cache fixed, costs about what 3.8 Flash does online. The owner's call: the job
itself runs on 3.8 Flash while the Gemini credit lasts.

**Fixed the same day** (`claude_structured`, ``schema_in_prompt``): the cell's schema goes as text
after the cached prefix, the reply is validated in code, and one that does not validate is asked for
again with the schema enforced. A probe on game `286816b0` (Haiku, three cells of different roles and
phases): the first call wrote the 12.7k-token prefix, the next two read it, and all three replies
validated ($0.006). The prefix is 3.6k tokens smaller than before because the enforced schema had
added hidden text of its own. The extraction job uses this mode for Claude.

## 2026-10-12 — Re-extraction on 3.8 Flash: the 12 seeding and 7 gate games

**Run** (`scripts/extract_batch.py --model gemini-3.8-flash`, code at `cf63039f`;
`batch_results/extraction_runs/flash_seed_gate_2026-10-12/`): the 19 games' backfilled inputs extracted
online on the live extractor's path (explicit Vertex prefix cache, medium thinking), with the
`uses_left` field now counted before the decision and present in every cell of a limited-use role;
the de-halo pass as one Haiku batch. 570 calls, none lost, no backup model used, 57 minutes.

- **Cost: $10.42** — $10.33 on 3.8 Flash at its promo prices (uncached input $0.93, cached $0.43,
  output $8.97, of which thinking $7.35) and $0.09 de-halo. About $0.55 a game; thinking is 71% of it.
- **872 observations** (39–56 a game): discussion 308, vote 238, night 326.
- **Player ids:** 1 observation of 872.
- **De-halo:** 220 of 872 verdicts revised (25%; the seeding pass revised 26%).
- **`uses_left`** against the count replayed from the game records (527 observations carry it): 471 exact
  (89%; 84% before the definition said "before"), 55 the count after the decision, 1 impossible. Some
  vs none is wrong in 23 (4.4%), mostly a last use written as 0, so the definition alone did not fix
  what the stage filter compares. The exact fix: the observation records the day of its decision and
  the count is computed from the record, as the seat's own is.

## 2026-10-12 — The remaining 21 games on Claude Sonnet 5.5, batched

**Run** (owner's choice; `extract_batch.py --model claude-sonnet-5-5 --thinking off`, code at `9bd2677b`;
`batch_results/extraction_runs/sonnet_rest_2026-10-12/`): the 16 served games of 2026-10-10, the 4 pilot
games and the smoke game, from their backfilled inputs, the schema as text after the cached prefix.
630 calls, none lost, 16 minutes; de-halo as one Haiku batch.

- **Cost: $19.99**, against an estimate of about $9.50. Output $7.39 (1.28M tokens, as expected). The
  rest was cache writes:
  - about 91 replies (15%) did not validate and were retried direct with the schema enforced; under its
    own schema each retry wrote a 16k prefix that no other call reads, at the 1-hour rate: $7.02;
  - about 92 batch requests (15%) wrote the game's prefix instead of reading the first call's ($3.01):
    Anthropic does not promise cache hits in a batch.
  - Fixed for later runs (`claude_structured`, `offline`): a reply that does not validate goes in a
    second batch the same way, and only what fails again is sent direct, enforced and uncached; the
    validation errors are now logged (this run's were not, so their cause is unknown).
- **1,405 observations** (about 67 a game, against Flash's 46): discussion 475, vote 436, night 494.
  Player ids in 18 (1.3%). De-halo revised 407 (29%).
- **`uses_left`**, on the 5 games with local records (191 observations): 74% exact, some vs none wrong in
  5.8% (Flash: 89%, 4.4%).

## 2026-10-12 — The 40-game store and its synthesis

**Build** (`scripts/build_v8_store.py`, code at `c3815883`): the 40 games' extracted observations (19
on 3.8 Flash, 21 on Sonnet 5.5) written into a fresh store as the post-game node did, each game's
observations deduplicated against the store on the way in (flash-lite triage): 2,277 observations,
2,008 kept, 269 merged, none failed (`memory_stores/v8_reextract`). Then `consolidate()` on a copy
(`memory_stores/v8_reextract_synth`; Sonnet 5.5 as one Message Batch, the revised synthesis prompt;
credit, prune and eviction off, since no v8 credit pass has run): 694 points, **605 after point dedup**,
in all 36 cells. **$5.31** for synthesis; 4.7 hours in all, nearly all of it the dedup on write.

| | ten_seat_v1 | v8_reextract_synth |
|---|---|---|
| Source games | 12 | 40 |
| Points | 157 (176 before the rule flag) | 605 |
| Points per cell | 1–12 | 5–35 |
| Median / max action words | 66 / 102 | 68 / 112 |
| Player ids | 0 | 0 |
| Limited-use roles' points with `uses_left` | night cells only | 337 of 337 |

The Sonnet-extracted games gave about 45% more observations each, so they weigh more in synthesis
than the Flash games. Not yet screened for rule errors (`ten_seat_v1`'s screen flagged 11%).

## 2026-10-13 — The 40-game store read: fit, rule errors and duplicates

**Fit** (`evaluation/experiments/v8_stage_filter_replay.py --store memory_stores/v8_reextract_synth`,
`v8_reextract_reads.py`; `data/gate/stage_filter_40games/`, `data/reextract/fit/`): the gate's 96 read
lookups searched again, from the situations the seats wrote, against the 40-game store (cells of 5–35
points, 15 on average, against about 4); the 412 lessons shown or kept read by four Sonnet subagents
on the gate read's rubric. Different readers from the first read, so the comparison is approximate.

| Lessons shown | ten_seat_v1 (12 games) | 40-game store |
|---|---|---|
| Top 3, no filter | 15% fit · 36 lookups with a fit | 19% · 41 |
| Stage filter, the gap left empty | 25% · 28 (25 empty) | 27% · 33 (17 empty) |
| Stage filter, the gap refilled from the cell | 22% · 30 (18 empty) | 24% · **52** (2 empty) |

- Fit rises a little; the gain is coverage. With the cells three to four times larger, refilling after
  the filter now finds a same-stage lesson for most lookups, so it beats leaving the gap empty.
- By phase (refilled): discussion 20%, vote 16%, night 29%.
- The readers name the remaining misfit the same way: lessons keyed to an event the seat does not have
  (named at a victim's door, a rival claim, the room turning on the partner, a wolf just voted out).
  The stage fields (alive bucket, partner lost, uses left) do not record events.

**Rule errors and duplicates** (`data/reextract/points/`: four Sonnet subagents, each a quarter of the
cells, against the pool's rules block):
- **37 of 605 points state a wrong rule (6.1%; 9 high, 28 medium)**, against 11% for `ten_seat_v1`'s
  screen. They cluster as before: the Sigilist's "no effect" (read as "protected" or as clearing the
  target), who an "immune" result can be (the Necromancer is immune on night 1 too), the pack choosing
  its carrier, a Day 1 vote. One reader asked whether a wolf-and-Serial-Killer attack on one victim is
  announced; it is (the morning names each kind of attacker), so those points stand.
- **65 duplicate groups, 78 points to drop** (13%) in the readers' judgement: the same move in the same
  situation and stage; conflicting moves and different stages left apart. The point dedup missed them
  because it compares embeddings of the situation only.
- Without both: **498 points**, the smallest cell the Speculator's night (3).
- The readers differ: one quarter flagged 4 rule errors, another 13.

**Published `memory_stores/ten_seat_v2`** (`scripts/publish_v8_store.py`; owner, 2026-10-13): the
40-game store's 605 points, without the 37 the rule screen flagged and the 78 duplicates, 498 points in
all 36 cells (the smallest, the Speculator's night, 3). The working store keeps every point, the
flagged ones marked `rule_flag` and the duplicates `duplicate_of` (with the point kept). The live stage
filter now searches the whole cell and filters before the cap, which refills from same-stage lessons
(`a123f0dd`); it stays off until memory is turned on with this store.

**Why the point dedup missed the duplicates.** It splits a cell's points by the labels synthesis gives
them (direction and honesty) before it compares any, so that rival moves never merge; the labels are
noisy, and 37 of the readers' 65 groups crossed them, so those points were never compared. The other
28 groups shared labels and were kept anyway (the run kept no record of why). Next: split by honesty
only, and check on this store, as a dry run, how many of the readers' groups that catches.

## 2026-10-13 — The point dedup, dry, against the readers' duplicates

**Run** (`evaluation/experiments/v8_sp_dedup_dry_run.py`; `data/reextract/dedup_dry_run/`): the batch
point dedup run without writing on the working store's 605 points, with the judge synthesis uses
(gemini-3.1-flash-lite), under the current split (direction and honesty) and honesty only; the points
it would drop compared with the readers' 65 groups (78 points).

| Split | Groups | Points dropped | Readers' groups caught | Drops across stages |
|---|---|---|---|---|
| direction + honesty | 12 | 30 | 9 of 65 | 10 |
| honesty only | 24 | 55 | 16 of 65 | 25 |

- Loosening the split finds more, but the judge is the problem: it misses three quarters of the readers'
  groups and merges points the readers kept apart. Of its 55 drops, 25 merge points whose stage differs
  (alive bucket, partner lost, uses left), the distinction the stage filter now depends on, and others
  merge different moves ("reveal the check as one data point" with "state the limits of a Not
  suspicious result").
- The judge could also rewrite the point it kept (it did once in 605 in the real run); it no longer can
  (`2036f83a`).
- **Reading:** split by honesty and by the stage facts (not by direction), and judge with a stronger
  model, batched; `ten_seat_v2` already has the readers' groups applied.

**Synthesis split by stage** (`feef97cd`): in `ten_seat_v2`, 17 of the 72 points labelled with the pack's
partner lost (24%) and 54 of the 270 labelled with uses left (20%) were written from source lessons
that disagree on that fact (the alive bucket was already split: 0 of 498), so their label holds for
only some of their sources. Synthesis clusters now split by both, so each point comes from one stage;
the point dedup refuses to discard across stages (`08dea470`). `ten_seat_v2` is left as built (owner).

## 2026-10-13 — Where v8 stands (closed for now, owner)

**Built:** a game saves its extraction input and extracts nothing; an offline job extracts saved inputs
(Gemini online with its prefix cache, or Claude batches with the schema after the cached prefix),
de-halos them as a batch and builds a store; 40 ten-seat games extracted, synthesized and screened into
`ten_seat_v2` (498 points); the seat's lookups reused within a day and a night; the stage filter in live
retrieval (off by default) that refills the top three with same-stage lessons.

**Measured:** fit of the lessons a seat is shown, 15% (12-game store, no filter) → 24–27% (40-game store,
stage filter), with 52 of 96 lookups served a fitting lesson against 36; rule errors in synthesized
points 6% (from 11%); extraction about $0.55 a game on 3.8 Flash, $0.95 on Sonnet as run. No effect on
play is claimed: no memory-on games have been graded (the credit port is after launch, plan §9.6).

**Open, by choice:**
- Served games: the job's writing of a memory-on game's lessons into its replay, the replay's "lessons
  being written" notice, and migration 0012 on the live database (none deployed; memory is off in
  served games).
- `uses_left` from the record (the decision day on each lesson); a free correction for the 40 games.
- The point dedup's judge (flash-lite caught 16 of 65 duplicates in the dry run); event-level matching
  to lift fit past about a quarter; the credit port.

## 2026-10-13 — Reopened: the credit port, the verdict halo, and decision tags

**Credit ported** (`d9141ce2`; table plan §9.6 item 10, why decisions §12). Each decision is graded by
the owner's ideal / neutral / undesirable table (`Agents/memory/consolidation/grading.py`); credit
counts one verdict per lesson per seat per scope, compares each lesson with the memory-off results of
its own turn kinds, and leaves a lesson with no baseline unscored. On the 12 seeding games the
memory-off means look as the rules predict (the Fortune Teller −0.60, most bets miss; the Sigilist
−0.35, most sigils miss; the pack's kill +0.42); on the 7 gate games 49 lessons were credited, the
most-followed 7 times (none prunable at 8).

**The verdict halo measured** (decisions §13; `evaluation/experiments/v8_verdict_halo.py`, data
`data/halo/`). 482 night and vote observations of 19 games: the extraction judge's verdict weights the
side winning +0.74 against +0.33 for the decision's deterministic grade; after de-halo +0.50, the
change one-sided (losers' negatives 53% → 27%, winners' positives 57% → 54%). Ruled: observations name
their decision, both outcome signals are kept, and which one synthesis reads is a setting.

**Decision tags.** Extraction now asks each observation for `decision_day` (and `pack_turn` on a wolf's
night). The 2,277 observations of the 40 games already extracted were tagged by Claude Haiku 5.5, one
batched request per game with its saved input (`scripts/tag_observation_decisions.py`; $0.08).
- Free checks: 2,100 tags match a decision the saved input records, 151 match none (mostly limited-use
  roles declining a night action, which leaves no line), 26 name a pattern over several; where the
  observation's own text states one day, the tag agrees 95–97% by phase.
- **Blind read** (`evaluation/experiments/v8_decision_tag_check.py`, data `data/decision_tags/`): six
  games at random, 17 random observations each, one Sonnet reader per game naming each decision from
  the record without seeing the tag. **98 of 102 agree (96.1% ± 3.8%)**; the day alone 101 of 102. Three
  of the four are a wolf's night tagged "several" where the reader chose the skill (the lesson speaks of
  the block and the pack's kill together); one is a Healer protection put a night early. The flagged
  set (unmatched, or disagreeing with the text's day) agrees 24 of 25: the unmatched tags are mostly
  real declines, and the text check's disagreements mostly its own misreading of a day mentioned as
  background. The bar set beforehand was 90%.
