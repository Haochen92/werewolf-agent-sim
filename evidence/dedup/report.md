# Deduplication: keeping repeated observations and lessons out of the memory store

This page describes how the project keeps duplicates out of the memory store today, layer by layer,
and what evidence supports each layer. How the design got here is told in
[the experiment log](experiment_log.md); the detail of each study is in the four sub-logs linked
under each layer.

**Version.** The code described here is the `feature-frontend-v1` snapshot of 2026-10-26
(`5d8ea41c458e7fc115a81eeeff2a14f560693551`). Each result belongs to the store, models and embedding
model it ran on, named beside it. Most of the evidence is from May and June 2026, on nine-seat stores
and Gemini models; today the dedup judges are Claude Haiku 5.5 and the embedding model is
Qwen3-Embedding-8B, and no accuracy test has been run on either.

## In short

- **What it does.** Before a judge model sees two entries, a rule on their structured fields (the
  gate) decides whether they may be compared at all, and an embedding check settles the plainly
  identical and the plainly different. The judge then only keeps or discards. Nothing rewrites an
  entry: the merge that would is built and switched off.
- **Where it runs.** Offline only, in three places: when an extraction job writes its games'
  observations into a store, when the learning tick folds new observations in, and after synthesis
  writes new lessons. No game deduplicates anything while it is played.
- **What supports it.** Two labelled sets scored the judges (65 single-entry cases, labelled by hand;
  111 entries in 11 clusters), a 232-case set checked the embedding lines, and one retrieval study (39 scenarios)
  compared a lightly and a heavily deduplicated store. All ran in May 2026 on a nine-seat store.
- **What is not known.** How accurate the current judges and embedding lines are on today's ten-seat
  store, and whether dedup changes how the players play.

## The problem

The memory store holds two kinds of entry, written offline after a game. An **observation** records
one move in one game: the situation, the move (the *approach*) and what it led to (the *outcome*). A
**lesson** (in the code, a *strategy point*) is a rule, "in this situation, do this", which a model
condenses from groups of observations. Entries are kept per role and kind of decision, and a seat
searching for advice is shown the closest three per situation it describes.

Over many games the same lesson is written again and again. Copies cost twice. They take the three
places a seat is shown, so it sees one piece of advice three times. And since the credit pass scores
lessons by the decisions they led to, two copies of one lesson split its follows, so neither gathers
enough evidence to be kept or pruned ([store curation](../store_curation/report.md)).

The bar every layer is held to: **remove the repetition without removing a distinct lesson.** The two
errors are not equal. A wrong discard is permanent: a lesson from a rare situation may never be
written again. A wrong keep is recoverable bloat that a later pass can still collapse. So each layer
leans towards keeping where it is unsure. How far the whole store should lean either way is a
question left open on purpose, because the answer depends on how retrieval and play use the store,
not on any prompt ([per-extraction log](per_extraction/experiment_log.md), "The open question").

## What counts as a duplicate

**The trigger is the situation.** It is the only field the store embeds for search
(`Agents/memory/store.py`, `fields=["situation"]`), so the working test in every dedup prompt is
"would a search that finds A also find B?" Sharing a situation is necessary, not sufficient:

- **Two observations** are duplicates only if all three parts match: the same situation, the same kind
  of move (not the same wording or degree), and the same kind of outcome. A different outcome makes a
  contrasting lesson, which is kept. The same situation and outcome with a variant of the move is the
  case a merge would combine; with the merge off, both are kept.
- **Two lessons** in the same situation are duplicates unless their actions differ in target, timing,
  direction or risk.

These rules were pinned down by relabelling, not declared up front. Three labelled cases show the edges
(the rulings are in the [per-extraction log](per_extraction/experiment_log.md), the full text in
[tricky_cases.md](per_extraction/tricky_cases.md)):

| Pair | Ruling | Why |
|---|---|---|
| A healer pattern seen with "2 saves" and with "3 saves" | duplicate | a difference of degree, not of kind |
| The same villager response to two different wolf tactics | kept apart | a different opposing move is a different lesson |
| The same failed defence mid-game and in the endgame | duplicate | the game phase alone does not make a new lesson |

## Where dedup runs today

| Step | When | What is compared | What the judge may do | Code |
|---|---|---|---|---|
| **Write** | an offline extraction job writes its games into a fresh store | each new observation against the entries written before it in that job | keep or discard | `Agents/memory/extraction/offline.py::write_extracted_store` → `Agents/memory/deduplication/pipeline.py::_dedup_single_memory` |
| **Fold** | the learning tick adds a window's new observations to the store | the store's observations, in clusters | keep or discard (a merge is turned into a keep) | `Agents/memory/consolidation/obs_fold.py::merge_new_obs` |
| **Lesson dedup** | the learning tick, after synthesis has added lessons | the store's lessons, in clusters | keep or discard; the kept lesson's text never changes | `Agents/memory/consolidation/store_ops.py::_dedup_strategy_points` |

Both tick steps are run by hand (`Agents/memory/consolidation/tick.py`); no schedule runs them, and no
ten-seat learning tick is recorded ([v8 report](../memory_system/v8/report.md)). The published store
`ten_seat_v2` was built by a one-off script that ran the write step and the lesson dedup, then had a
review drop the duplicates the dedup missed (below).

The write step works one entry at a time, as each arrives. The fold and the lesson dedup are the
**batch pass**: they cluster a whole store and judge each cluster in one call. The batch pass exists
because the one-at-a-time step is greedy. It compares a new entry with its five nearest neighbours at
the moment it lands, and never looks again at a pair it has kept, so near-duplicates that missed each
other's window build up ([batch log](batch_dedup/experiment_log.md), "Why a second pass").

## The layers

The write step runs four filters in this order, cheapest first: search, gate, embedding check, judge;
a pair stops at the first layer that decides it. The batch pass runs the same search (as clustering),
gate and judge, without the embedding check.

### 1. Search: which entries are candidates

**What it does.** The write step searches the new entry's situation within its role and kind of
decision, takes the five nearest, and keeps those above a floor (0.36 on Qwen; 0.55 on the Gemini
embedder). If none clears it, the entry is stored without a judge. The batch pass builds clusters
instead: it takes the most-reinforced entry as a seed, adds those of its ten nearest neighbours (above
0.50 on Qwen) that share its gate partition and are not already in a cluster, and repeats
(`clustering.py::_bounded_seed_clusters`). A size cap of 15 is set, but at a search width of ten it
does not bind.

**Why cluster, and why this method.** A store of hundreds of entries fits in no prompt, and comparing
every pair would take a model call per pair; clustering decides what is compared, and the judge
decides what is a duplicate. A clustering that links A to C because both resemble B (union-find, or the
hierarchical method) put all of a role's entries for one kind of decision into one cluster at any
threshold low enough to catch real duplicates. The seeded method cannot chain, so each entry lands in one small cluster. The other two
methods remain behind a setting, unused.

**Evidence.** On the 111-entry set, judges were right on 80–100% of entries in clusters below 15
entries and on 26–74% above it, which set the cap. Neither line binds much today: both floors sit below
nearly every pair of entries for the same role and kind of decision, so the gate and the judge do the
separating
([v8 log](../memory_system/v8/experiment_log.md), "Embedder").

### 2. The gate: which candidates may be compared at all

**What it does.** Each observation carries structured fields describing its board. The gate compares
only entries that agree on them (`Agents/memory/dedup_gate.py`):

- **Partition** (`gate_key`): whether the moment was a swing, how many players were alive (early: 8 or
  more; mid: 5 to 7; late: 4 or fewer), and which way the room's consensus pointed.
- **Pair checks** (`compatible`): the verdict on the move, whether the board was rich or poor in
  information, and whether the player was safe or exposed. Entries that differ on any of these are
  never duplicates.
- **Lessons** are partitioned by their own two labels instead (`sp_gate_key`): the move's direction
  (for example, pressing an accuser or lying low) and its honesty.

The partition is kept to three fields because each added field splits buckets until most hold one
entry; the fields that change the playbook are pair checks for the same reason. The judge is shown only
what the gate did not decide: the gated fields are hidden from its prompt (`situation_for_dedup`), so
it cannot re-argue them. Entries without these fields (stores built before June 2026) pass the gate
untouched, and the batch pass can run without it (`gate_enabled`). The gate belongs to dedup only:
retrieval's filters on these fields are built and off by default, and served games do not turn them
on.

**Why.** Situations used to be one block of prose with repeated section labels, and the labels made
every pair look alike. On the June v6 store, hierarchical clustering at 0.70 put 916 of 919
observations into clusters of the maximum size, and a threshold sweep had no stable middle: one blob
up to 0.80, usable clusters only between 0.88 and 0.90, fragments by 0.92. The structured fields were
well spread where the embedding was not, so they became the gate
([clustering plan](dedup_clustering_and_sp_extraction_plan.md), a historical record).

**Evidence and limits.** The gate's rules are unit-tested (`tests/memory/test_dedup_gate.py`). Its
effect on accuracy has never been scored: both labelled sets predate the structured fields, so the
gate does nothing on them. On the lesson side it has a measured cost: of 65 groups of duplicate lessons
that model readers found in the 40-game store, 37 crossed the direction or honesty labels, so the
dedup never compared them ([v8 log](../memory_system/v8/experiment_log.md), 2026-10-13).

### 3. The embedding check: decide the plain cases without a judge

**What it does.** For the pairs left, the write step embeds a more telling field than the situation:
an observation's whole text, a lesson's action. If the highest similarity to any candidate is at or
above a discard line, the entry is discarded as a copy and the survivor's count goes up; below a keep
line, it is stored; between the two, the judge decides. If embedding fails, the judge decides
(`Agents/memory/deduplication/prefilter.py`). The lines are kept per embedding model
(`Agents/llm_factory/embeddings.py`, `SIMILARITY_THRESHOLDS`):

| Line | Qwen3 (today) | Gemini, set in May |
|---|---|---|
| Observation: keep below / discard at or above | 0.72 / 0.94 | 0.935 / 0.96 |
| Lesson action: keep below / discard at or above | 0.61 / 0.88 | 0.81 / 0.93 |

The discard lines sit near identical text, because a discard cannot be undone.

**Where it is live.** Only for observations, in the write step. Lessons are deduplicated by the batch
pass, which does not call it.

**Evidence: the ceiling.** In May, on `gemini-embedding-001`, the lines were set on the 65 labelled
cases and checked on 232 broader cases (five games' entries searched against a store built from five
others, labelled by two Gemini models). The broader set caught a small-sample
artefact: on the 65 cases a lesson discard line of 0.90 made no errors, on the 232 it was too
aggressive, and 0.93 shipped. At those lines about 23% of decisions needed no judge (lessons: 10.3%
discarded, 4.3% kept; observations: 6.0% discarded, 25.0% kept). Three attempts to decide more (3,072
dimensions, a similarity-tuned embedding mode, a second similarity axis) all decided less on the 232
cases. The reason is that embeddings capture topic, not stance. Case 155 pairs "Prioritize
investigating players who are actively pushing narratives…" with "Avoid investigating the most vocal
leader…"; the two are opposite advice, labelled a keep, and their actions embed at 0.913 on Gemini and
0.881 on Qwen. So the embedding
check can only ever settle the extremes (about 15–30% of cases); the middle needs the judge
([prefilter log](embedding_prefilter/experiment_log.md)).

**Evidence: today's lines.** The Qwen lines were derived on 2026-10-12 from the 65 cases alone, at
zero errors there. Re-embedding the 232 cases on Qwen (2026-10-14) showed two problems:

- The lesson discard line of 0.88 would discard two labelled keeps, case 155 and case 85 (the same
  pair of opposing advice). The path is not live, so no lesson has been lost to it.
- The observation lines barely act: nothing falls below 0.72 (the lowest case is 0.74) and 2 of 116
  cases reach 0.94, so the live path decides 1.7% of these cases without a judge.

Two corrections came out of the same check. The May observation counts do not reproduce from the cache
kept beside them (15 discards and 34 keeps with one error each way, against the 7 and 29 at zero errors
reported), so the May observation lines are near-zero-error, not zero-error. And when the embedder moved
from `gemini-embedding-001` to `-2` on 2026-07-16, the lines were not moved with it; on the labelled
cases `-2` needed a keep line below 0.50, so for three months the Gemini check stored some labelled
duplicates (extra entries, no lost ones). A line means something only for the model it was set on.

### 4. The judge: keep or discard

**What it does.** The pairs still undecided go to a model with the new entry and its candidates; it
answers keep or discard, and its schema offers nothing else (`Agents/memory/deduplication/schemas.py`).
A discard adds the new entry's count to the survivor. If the model fails after retries, the entry is
stored (`pipeline.py`). The write step's judge is Claude Haiku 5.5 at low thinking since 2026-10-15
(`Agents/llm_factory/accessors.py`, `DEFAULT_DEDUP_MODEL`; before that, Gemini 3.1 Flash-Lite, chosen
on cost and speed). Its prompts are in `Agents/prompts/dedup.py`, last changed on 2026-06-16, when
the fields the gate decides were taken out of them; for lessons they show the action before the
situation.

**Evidence.** The 65-case set ([per-extraction log](per_extraction/experiment_log.md)) was sampled
from 390 dedup decisions across 30 nine-seat games and labelled by hand, in two rounds of review that
changed 14 labels. Scored on it, the prompt went through eleven versions; the lessons that moved the
score:

- **A lean in one direction has no neutral setting.** "When unsure, prefer discard" raised discard
  recall to 93% and cut keep recall to 41% on Flash-Lite; removing it flooded merges. A note naming one
  specific difference ("a different wording is not a different move") fixed the failure without the
  tilt.
- **Order beat instruction.** Showing a lesson's action before its situation raised Flash-Lite's
  lesson accuracy from 72% to 84%, where added paragraphs of rules had not helped.
- **Merge left the one-at-a-time step.** It was rare (5 of 65 labels), both models over-called it
  (15 and 8 predictions), and a wrong merge corrupted the entry. With keep or discard only, on the same
  backend, Flash-Lite rose from 73.8% to 80.0% and Gemini 3.5 Flash to 83.1%; a final rule that all
  three parts must match took Flash-Lite to 83.1% (errors of discarding a keep: 9 → 4).

The scores before and after a switch from Google AI Studio to Vertex AI are not comparable: the
backend alone moved one run from 76.9% to 73.8% at temperature 0.

### 5. The batch pass: the fold and the lesson dedup

**What it does.** For each role and kind of decision, and within each gate partition, the batch pass
builds clusters (layer 1), sends each cluster of two or more to the judge in one call, and applies its
answers (`Agents/memory/batch_deduplication/orchestration.py`, `operations.py`). Applying an answer is
deterministic:

- the survivor is the judge's pick; a pick that is not in the cluster fails safe, deleting nothing;
- the survivor takes the summed counts of everything it absorbs (seen, shown, used, and the verdicts),
  so collapsing five entries keeps their combined weight;
- nothing is written unless the run is told to apply; a dry run only counts.

The two steps that use it differ in what the judge may change:

- **The fold** runs it on observations, judging on Haiku 5.5 (`TickConfig.dedup_model`), in
  **triage-only** mode: the judge's keeps and discards stand, and any merge it proposes becomes a keep,
  so near-duplicates stay separate and no text is rewritten (`TwoPassConfig.skip_verify`).
- **The lesson dedup** runs it on lessons after synthesis, also on Haiku 5.5, and only if synthesis
  added lessons. Three rules hold whatever the judge says (2026-10-13): the kept lesson keeps its own
  text and fields; a lesson learned at another stage of the game (players alive, pack partner lost, a
  limited ability used up) is never discarded into one from a different stage, since retrieval's
  stage filter (built, off by default) would serve each to different seats; and a discarded lesson's key is listed on its survivor, so the
  follows recorded against it still count (`operations.py::_apply_strategy_operation`,
  `_merged_metadata`; [v8 decisions](../memory_system/v8/decisions.md) §14).

Both run in **incremental mode**, which is meant to freeze old entries (next section).

**Evidence: the judge on clusters.** The 111-entry set (11 clusters from the nine-seat v4 store: 77
keeps, 20 discards, 14 merges; [batch log](batch_dedup/experiment_log.md)) showed why a cheap judge can
be trusted to keep or discard but not to merge. Gemini 3.1 Flash-Lite's calls by what it said:

| Flash-Lite said | Right |
|---|---|
| keep | 56 of 61 (91.8%) |
| discard | 13 of 15 (86.7%) |
| merge | 11 of 34 (32.4%) |

Triage-only mode is built on that asymmetry: it keeps the reliable calls and drops the unreliable one.
The same set scored the single-model options (Gemini 3.5 Flash 86.5%, 2.5 Pro 83.8%, Flash-Lite 72.1%,
Flash-Lite with an anti-merge prompt 85.6%) and the prompt changes that moved them, in the log.

**Evidence: the store-level effect.** The retrieval study ([retrieval impact
log](store_retrieval_impact/experiment_log.md), phase 2) compared three nine-seat stores on 39
scenarios of a 40-case set, with Gemini 2.5 Flash scoring each retrieval from 1 to 5:

| Store (scores for observations) | Entries, both kinds | Relevance | Efficiency | Distinct lessons |
|---|---|---|---|---|
| Not deduplicated | 522 | 4.51 | 3.26 | 2.62 |
| Deduplicated by the tuned prompt (−17%) | 432 | 4.44 | 3.44 | 2.82 |
| Deduplicated by the untuned prompt (−39%) | 320 | 4.26 | 3.26 | 2.41 |

The light dedup traded a little relevance for more efficiency and more distinct lessons; no
significance test was run, so it is a trade, not an improvement. The heavy dedup lost relevance on
observations (−0.28 on average; 2 scenarios better, 24 the same, 14 worse) and gained no efficiency.
An earlier five-scenario run had shown the heavy store winning everywhere; the 39 overturned it. This
is why every setting above leans towards keeping.

**Evidence: the lesson dedup on ten seats.** Building `ten_seat_v2` (2026-10-12/13, Flash-Lite as
judge), the lesson dedup took the 40 games' 694 synthesised lessons to 605. Model readers then found 65
groups of duplicates still in the 605 (78 lessons, 13%). Besides the 37 groups the gate kept apart, 28
shared labels and were kept anyway; the run kept no record of why. A dry run on the 605 showed the judge itself was the
larger problem:

| Partition | Lessons dropped | Readers' groups caught | Drops across stages |
|---|---|---|---|
| direction and honesty (live) | 30 | 9 of 65 | 10 |
| honesty only | 55 | 16 of 65 | 25 |

Two of the three rules above came from this run: the stage rule, and the end of rewriting (the judge
had rewritten one lesson in 605 when it still could). The 78 duplicates were left out of the published
store by hand. The dry run's reading (split by honesty and stage instead of direction, and use a
stronger judge) has not been built; the judge has since changed to Haiku 5.5 without a re-run.

The write step on the same build kept 2,008 of 2,277 observations, discarding 269 as copies; nearly
all of the build's 4.7 hours went to it. Earlier, folding 562 observations from parallel seed games
into a fresh store (Flash-Lite, triage-only) collapsed 9.

## Built and off

### The rewriting merge

The batch pass can also merge: a cheap model triages every cluster, and only the entries it marks as
merges go to a stronger model, which decides again and writes the merged text (`cluster_agent.py`,
`_two_pass_cluster_dedup`). On the 111-entry set this scored best of everything tried: 99 of 111
(89.2%), with 28 entries escalated, against 86.5% for the best single model. It is off because the
merged text could not be trusted:

- Flash-tier models drop two of the three merged fields; three prompt changes to stop it each broke the
  structured output on several clusters.
- Gemini 2.5 Pro, the one model that kept all three, added game context that was not in the sources in
  3 of the 9 merges a judge reviewed.
- Nothing between the judge and the store checks merged text against its sources. The fabrication
  judge exists only in the evaluation code.

So the fold runs triage-only (the mode was added on 2026-06-22) and lessons never merge (since
2026-10-13). The
two-pass mode can still be run by hand (`Agents/memory/batch_deduplication/cli.py --two-pass`). Its
default models are now Haiku 5.5 and Sonnet 5.5, neither of which has been scored on the set.

### The post-game incremental pass

The batch pass was also built to run after games, on new entries only (`IncrementalDedupConfig`). It
is off twice over: its switch defaults off, and since extraction moved out of the game nothing calls
it. Its incremental mode is the one the fold and the lesson dedup now use, and two pieces of it matter
to them.

**The freeze-old guard (built, unit-tested).** A second full run of the batch pass on an
already-deduplicated store removed another 45 of 432 entries (10.4%). Some were real misses; others
merged entries that different searches would find. The diagnosis
([incremental_convergence.md](incremental_convergence.md), kept as the diagnosis record): re-running
with nothing new changes nothing, but every new entry reopens the settled old entries around it, so the
store erodes with no fixed point. The fix, built on 2026-06-16, is in the apply layer: an operation
that would remove one old entry into another is refused, and when an old and a new entry collapse, the
old one survives (`operations.py::_frozen_old_conflict`, `_resolve_survivor`;
`tests/memory/test_batch_dedup.py`). Run by hand without incremental mode, the pass has no guard and
re-judges everything, old against old; that is the mode the second-run test used.

**What the guard depends on (open).** "Old" means created before the store's last dedup run. Two
things weaken that boundary. A merged survivor does not keep its creation time, and loading a store
resets every entry's, so the boundary holds within a run, not across runs (the guard's Fix 1, never
built; moot while nothing merges). The second weakness is fixed. Until 2026-10-26 the guard
engaged only when the store's folder carried the previous run's time marker
(`incremental.py::_read_last_dedup_at`), and the learning tick builds a new folder from the database
each time without one, so its fold would have re-judged the whole store, old against old; a marker
alone would not have helped, since an extracted observation's creation time can predate it. Now
both tick steps name their new entries: the fold passes the observations it appended, and the
lesson dedup the lessons synthesis just wrote (`BatchDedupRunConfig.new_keys`,
`orchestration.py::incremental_new_keys`; `tests/memory/test_dedup_new_keys.py`). No tick had run on
ten seats, so the old behaviour was never observed.

## What dedup cannot do

Dedup removes repetition; it cannot add a lesson the store does not have. In the retrieval study,
lessons stayed about 59% redundant on every store, deduplicated or not, because the nine-seat store
(198 lessons) had no entries for some common situations. Today's store holds about 500 lessons and
served games retrieve only lessons; whether the gap is still one of coverage is unmeasured
([retrieval impact log](store_retrieval_impact/experiment_log.md), addendum 2026-10-14).

## How sure we are

What the layers rest on:

- **Accuracy on labelled sets**: 65 cases for the one-at-a-time judge, 111 entries for the batch judge,
  232 cases for the embedding lines. All nine-seat content from May 2026, all scored on Gemini models.
- **Store-level effect**: one retrieval study, 39 scenarios, one judge model, no significance test.
- **Mechanics**: the gate, the embedding lines, survivor choice, count summing, the freeze-old guard
  and dry-run safety are unit-tested (`tests/memory/test_dedup_gate.py`, `test_dedup_thresholds.py`,
  `test_batch_dedup.py`). An aggregate score cannot isolate these bugs, and a unit test cannot judge a
  duplicate.

What has not been checked:

- **The current judges on today's store.** They were scored only on the May sets (2026-10-26, one run
  each). The one-at-a-time
  judge, Haiku 5.5, scored 52 of 65 (80.0%), level with the May judges' 83.1%. The batch judge, Haiku 5.5
  as the fold runs it, was right on 84 of 93 keeps but only 11 of 18 discards (Flash-Lite in May: 13 of
  15), so in the fold and the lesson dedup about one discard in three may delete a distinct entry
  ([per-extraction log](per_extraction/experiment_log.md), [batch log](batch_dedup/experiment_log.md),
  addenda 2026-10-26).
- **The current embedding lines** rest on 65 cases; on the 232 they would discard two keeps.
- **The gate** has never been scored on a labelled set.
- **The trace re-check**: every dedup decision logs its similarity scores so the lines could be re-set
  from real decisions; that re-check has not been run.
- **Play**: no test has asked whether dedup changes how the players play.

## When to revisit

| Choice | Rests on | What would justify changing it |
|---|---|---|
| Keep or discard only, no merge | merged text unverified; fabrication in 3 of 9 Pro merges | a check of merged text against its sources, wired before the store is written |
| Lessons partitioned by direction and honesty | the labels separate rival moves | the dry-run's alternative (honesty and stage) catching more of the readers' groups without cross-stage drops |
| Haiku 5.5 as judge | cost; level with the May judges one at a time (80% on 65) | its batch discards: 11 of 18 right against Flash-Lite's 13 of 15; a judge or prompt that discards as safely in the fold |
| Qwen lines from 65 cases | zero errors on those cases | a check on the 232 cases or on logged decisions |
| Lean towards keeping | a wrong discard is permanent | a retrieval or play measure showing the duplicates kept cost more than the lessons saved |

## Records

| Record | Holds |
|---|---|
| [experiment_log.md](experiment_log.md) | the journey from cosine dedup to the gate; the June gap audit and its October rows |
| [per_extraction/](per_extraction/experiment_log.md) | the one-at-a-time judge: the 65-case set, prompt versions 1–11b, the end of merge |
| [batch_dedup/](batch_dedup/experiment_log.md) | the batch pass: clustering, the 111-entry set, the two-pass merge, merge quality, the idempotency test |
| [embedding_prefilter/](embedding_prefilter/experiment_log.md) | the embedding lines: calibration, the 232 cases, the ceiling, the Qwen re-check |
| [store_retrieval_impact/](store_retrieval_impact/experiment_log.md) | the retrieval study, five scenarios then 39 |
| [incremental_convergence.md](incremental_convergence.md) | the non-convergence diagnosis and the two fixes |
| [dedup_clustering_and_sp_extraction_plan.md](dedup_clustering_and_sp_extraction_plan.md) | the June plan that produced the gate (historical) |
