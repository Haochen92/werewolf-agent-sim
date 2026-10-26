# Retrieval: how a seat finds its lessons, and what the May study of the optional stages showed

**What does a seat see from memory, and did the extra stages tested in May make it better? It sees up
to three lessons per described situation, found by similarity search alone; the extra stages showed
directions on five test cases and none is on by default.** Before a decision, a seat with memory on
describes its situation in a short model call, searches its own shelf of the store for the closest
lessons, and is shown the best few. In May 2026 three optional stages after the search were tested on
the nine-seat game: a filter against near-repeats, a model reranker, and a wider fetch. Each moved the
judge's scores in some direction on small samples. None was switched on by default, and served games
use none of them.

This page has two parts. [Part 1](#part-1-the-read-path-today) is the read path as it runs today.
[Part 2](#part-2-the-may-2026-study-of-the-optional-stages) is the May study as it ran, one section per
stage, each with its own setup, store and sample size beside every number, and a dated note on what
shipped. How the search query is written and checked is told in the
[situation query report](../extraction/situation_summary/report.md); the rest of the memory system is in
the [v8 report](../memory_system/v8/report.md) and the [memory hub](../memory_system/report.md).

**Version.** Part 1 describes the code at the `feature-frontend-v1` branch head on 2026-10-26
(`5d8ea41c`), checked against the code named in each statement. Part 2's results belong to the
nine-seat game, the May stores, the embedding model and the judge they ran on, named in each section;
none was re-run on today's code.

**Terms used below.**

- An **observation** is a short account of one move and its effect, written by a model from a finished
  game. A **lesson**, stored as a **strategy point**, is short advice for one role in one kind of
  situation, written by a model from a group of observations.
- A **cell** is one role's shelf for one kind of decision (day discussion, day vote, night action). A
  seat searches only its own role's cell for the decision it is making.
- A **situation** is the one- or two-part description of the seat's position that the seat's model
  writes before the search. Each part is searched separately.
- A **lookup** is one situation call plus the searches it feeds.

## Part 1: the read path today

### When a seat looks up

**Before most decisions from day 2 on, if memory is on for that game.** The rules are in
`Agents/memory/retrieval/plan_gating.py::retrieval_plan`. A seat makes no lookup:

- on day 1 or the night after it (the night shares day 1's number), since nothing has happened that a
  lesson could match;
- on a day turn if it is a town seat: town day lessons are written for the owner to review and never
  served (`TOWN_DAY_PHASES`; the ruling is in [v8 decisions](../memory_system/v8/decisions.md) §5);
- when memory is off for its role, or no store is loaded.

A human seat decides without the agent pipeline and makes no lookup. In served games memory is the
player's switch for every AI seat at once and starts off; that is described in the
[v8 report](../memory_system/v8/report.md), "What is deployed, and since when".

### One lookup, step by step

1. **Describe the situation.** A short call to the game's model writes one or two situations in the same
   labelled fields the stored lessons were written in (`Agents/memory/retrieval/situation_agent.py::_generate_situations_for_agent`).
   The [situation query report](../extraction/situation_summary/report.md) tells how this query was
   designed and tested.
2. **Search the cell.** Each situation is searched against the seat's cell by embedding similarity, and
   **five** items are fetched per situation. An item found by both situations is kept once, with its
   higher score (`Agents/memory/retrieval/accessors.py::retrieve_strategy_points_for_agent`).
3. **Keep three per situation.** The cap keeps the best **three** per situation
   (`RETRIEVAL_KEEP_PER_SITUATION`, applied by `Agents/memory/retrieval/filters.py::cap_per_situation`),
   so a seat sees at most six. Fetching five and keeping three matters only when the two situations
   find the same item: the situation that lost it refills from its fourth or fifth hit. The reason the
   fetch is five and the cap three is told in [the wider fetch](#the-wider-fetch-how-many-observations-to-show).
4. **Order by track record.** Two steps use the counts the credit pass writes onto each lesson. A lesson
   followed at least five times with more good grades than bad counts as **proven**
   (`filters.py::_sp_is_proven`). At the cap, if every lesson kept for a situation is proven, the
   weakest is swapped for the best unproven candidate, so an untried lesson gets a chance to be followed
   and scored (the **exploration slot**). After the cap, proven lessons are moved ahead of unproven ones
   without changing the order within each group (`filters.py::partition_proven_first`). Both are on by
   default and do nothing on a store without counts. Whether the published store carries counts is
   discussed in the [v8 report](../memory_system/v8/report.md), "In a game: looking lessons up".

**Served games retrieve strategy points only, never observations**
(`server/game/run_config.py::game_run_config`). The town half of the store never had observations, so
serving them would give the two sides different memory. Batch games retrieve both kinds by default
(`Agents/config/run.py::DEFAULT_RETRIEVAL_TYPES_CONFIG`).

### When a lookup is reused

**Within a seat's day discussion and within a night; never for a vote.** A seat makes one lookup at its
first discussion turn of the day and reuses it for its later turns, until someone makes a new role
claim that day (a new player and role pair; a claimant repeating its claim does not count). Every vote
looks up afresh. A seat makes one lookup a night; a wolf makes two, one for the pack's chat and one for
its kill and ability, because the talk moves from candidate targets to a plan the first lookup could
not anticipate (`Agents/memory/retrieval/lookup_cache.py`; the wolf split is passed as
`lookup_scope` by `Agents/turn/pipeline.py`).

Only the lessons selected and the lookup's record are kept, never a verdict: each decision records its
own verdicts, and a reused lookup's record says it was reused and where it was made. The cache lives in
the process and holds at most 1,024 lookups, so a server restart means a fresh lookup. A payload with
no game id (a test, a bench replay) is never cached.

*Why.* On the owner's first ten-seat game, memory on meant about 60 lookups, 27 of them discussion
turns of evil or neutral seats, at 2 to 5 turns per seat a day; reuse brings that to about 38, plus one
per new claim ([v8 decisions](../memory_system/v8/decisions.md) §10). It was ruled on cost
(2026-10-12). It was not compared with per-turn lookups in play; the nine-seat pre-test that asked
whether it would change what seats see is in [the per-day discussion log](per_day_discussion/experiment_log.md).

*Not checked.* Whether a lookup reused across a day's turns fits the later turns as well as a fresh one
would.

### Built and off

Four optional stages sit between the search and the cap. Each is switched per game, and per role where
the table says so; all four are off by default and off in served games.

| Stage | What it does | Switch and default | Evidence |
|---|---|---|---|
| Near-repeat filter | Drops an observation too similar to one already kept (a cosine line per embedding model: 0.87 on gemini-embedding-2, 0.80 on Qwen3-Embedding-8B); spreads strategy points out by MMR (relevance weighed against similarity to those already picked, λ = 0.8) | `filtering_config` per role on `Agents/config/run.py::RunConfig`, off for every role | May study, [the filter](#the-near-repeat-filter) |
| Model reranker | A model call re-scores the candidates against the situations and keeps the best three of each kind in total; falls back to search order on a failed call (`Agents/memory/retrieval/rerank_agent.py`) | `reranking_config` per role and per kind, off for every role | May study, [the reranker](#the-model-reranker) |
| Field-matching tilt | Raises or lowers each item's score by how well its situation fields match the query's, then re-sorts; never drops an item (`Agents/memory/retrieval/dimension_gating.py`) | `dimension_gating_config` per role, read from the run's config only; not on `RunConfig` | [Situation fields](../extraction/situation_dimensions/report.md): no benefit, left off |
| Stage filter | Leaves out lessons learned at another stage of the game (players alive, partner lost, uses left) and lets the cap refill from same-stage lessons in the cell | `Agents/config/run.py::DEFAULT_STAGE_FILTER`, off | [v8 report](../memory_system/v8/report.md), "Do the lessons a seat is shown fit its decision?" |

When the filter, the reranker or the tilt is on, the search fetches ten per situation instead of five
(`RERANK_TOP_K`); when the stage filter is on, it fetches fifty, close to the whole cell
(`dimension_gating.py::STAGE_FILTER_TOP_K`). The whole flow is
`Agents/memory/retrieval/pipeline.py::enrich_payload_with_memory`.

### How well today's path fits the decision

**About one lesson in seven fitted the decision on the twelve-game store; about a quarter fit with a
larger store and the stage filter, which is off in served games.** That check (96 lookups from seven
ten-seat games, read by model readers) is told in full in the
[v8 report](../memory_system/v8/report.md), "Do the lessons a seat is shown fit its decision?". Its
readers found that the search matched the role, not the stage of the game, and that the similarity
score did not track fit. The May study below tested a different question: not whether a set fits, but
whether stages after the search made the set less repetitive and more relevant.

## Part 2: the May 2026 study of the optional stages

> **In short (record of May 2026; superseded as a description of the read path).**
> - **Question.** After the search, do a near-repeat filter, a model reranker or a wider fetch give a
>   seat a better set of memories?
> - **Tests.** The filter and the reranker: 5 frozen decisions from nine-seat games, the sets scored by
>   one model judge, on the v4 stores. The wider fetch: 120 frozen decisions replayed with 3, 5 or 7
>   observations per situation, the decisions scored by one model judge.
> - **Answer.** Directions only. The filter helped on a store full of duplicates and hurt on a cleaned
>   one. The reranker made strategy-point sets less repetitive on 5 cases. Five observations per
>   situation scored slightly above three and seven, with no significance test.
> - **What followed.** None of the three is on by default. The cap of three per situation is the one
>   stage of that pipeline that always runs, and the wider fetch was built as a fetch width with the
>   cap still after it, so it never reached the prompt.

### What the study was for

**Similarity search returned variations on one lesson, and right-topic advice for the wrong moment.**
In one investigator case the search returned 12 observations, many teaching the same lesson ("acting on
weak reads causes mislynches") through different games. Strategy points failed differently: the search
returned mid-game advice for early-game situations, or endgame advice for a seat facing a day 1 with no
information. The items were about the right topic, so relevance was not the main fault; repetition and
timing were.

### How the sets were scored

**One model judge, after it groups the items by the lesson they teach.** Each test replayed retrieval
for frozen decisions captured from nine-seat games against an exported store, so the same store and the
same queries gave the same candidates in every run; only the stage under test and the judge changed.
The judge read the situation and the retrieved set and gave:

- **relevance** (1–5): does the set fit this situation;
- **efficiency** (1–5, higher is better): how little of the set repeats itself;
- **unique lessons**: how many distinct lessons the set teaches;
- a **redundancy ratio**, computed from those: 1 − unique lessons ÷ items, per case, then averaged
  (today's runner: `evaluation/src/replay/retrieval.py::redundancy_ratio`).

The judge needed two fixes before its scores meant anything. Gemini Flash-Lite, the first judge, scored
almost every set 3–4 and broke its output schema on about 30% of calls (it returned three redundant
pairs where the schema allowed two). Gemini 2.5 Flash had no failures in any later run and its scores
moved with the retrieval changes. Its first prompt defined repetition and novelty by different
standards (would the player act differently, against distinct anecdotes), so one nine-item set scored
relevance 5, redundancy 5 (most repetitive) and unique ideas 5 (most novel) at once
(`filtering/03_lambda08_flash_nocap.md`). The fix was structural: the judge first clusters the items by
lesson, then derives every score from the clusters, and the redundancy scale was flipped to efficiency
so every score points the same way. That cluster-first prompt is still the retrieval judge
(`evaluation/src/judges/prompts/retrieval.py`).

*What this instrument can and cannot see.* It scores a retrieved set, not a decision: a higher score
says the judge found the set less repetitive or better fitted, not that the seat played better. Every
filter and reranker number below comes from 5 cases (two healer, two investigator, one villager) and
one judge; it is a direction, not a size. No significance test was run.

### The near-repeat filter

**On a store full of duplicates, raising the similarity line from 0.85 to 0.92 kept the filter from
emptying the sets; on a cleaned store the filter made the sets worse.**

*Setup (2026-05-23).* Three steps after the search: a gate that drops an observation whose embedding is
too close to one already kept, MMR for strategy points, then the cap of three per situation. The search
fetched ten per situation to give the filter room. The store was **v4**: 522 items (324 observations,
198 strategy points) from the nine-seat game before its June rebuild, many of them near-duplicates.
Embeddings were gemini-embedding-001. Four runs, each changing one thing:

| Run | Cases | Change | Judge |
|---|---|---|---|
| 1 | 10 | gate at 0.85 | Gemini 2.5 Pro |
| 2 | 5 | gate at 0.92 | Flash-Lite (about 30% failed validation) |
| 3 | 5 | MMR λ = 0.8, no cap (one set of 12 items) | 2.5 Flash |
| 4 | 5 | the full pipeline with the cap, cluster-first judge | 2.5 Flash |

The judge changed between runs, so the runs are not comparable to each other on scores; each run
answers its own question.

*The similarity line.* At 0.85 the gate collapsed the sets: five of the ten cases in run 1 were cut to a
single observation, two of them from 15 and 16 candidates, and the average number of observations shown
fell from 4.9 to 1.6. At 0.92 the volume came back. The report of the time said 0.85 also removed pairs
that teach opposite lessons (a healer who stayed quiet and survived against one who spoke up and was
killed) because they share vocabulary. Run 1 does not show this: in that healer case the 0.85 line kept
both observations, and the judge called them "opposing strategies for this exact situation"
(`filtering/01_baseline_threshold085_pro.md`, first case). The opposing-pair argument was the hypothesis
behind raising the line, not an observed removal (corrected 2026-10-14).

*MMR.* At λ = 0.8, strategy-point sets kept mean relevance between 3.0 and 4.0 with efficiency 2–3;
lower values, by the report of the time, pulled in strategies for the wrong phase of the game (no table
was kept for them).

*The final run* (run 4, v4 store, 5 cases, 2.5 Flash):

| Kind | Items shown (mean, range) | Relevance | Efficiency | Unique lessons |
|---|---|---|---|---|
| Observations | 5.0 (3–6) | 4.20 | 3.40 | 2.80 |
| Strategy points | 4.0 (2–5) | 3.00 | 2.00 | 1.20 |

Medians and ranges per score are in `filtering/report.md`. The best case was an investigator's day
vote: five observations, each scored 5 on relevance, efficiency and unique lessons. The worst was a
healer's day vote: endgame consensus advice for an early, information-starved vote, relevance 1 and no
unique lessons (see [missing lessons](#what-every-stage-ran-into-missing-lessons)).

**Filtering does not stack on a cleaned store.** The same filter (gate at 0.92, MMR λ = 0.8) was then
run on **v4_deduped**, the v4 store after an aggressive batch dedup (150 observations, 167 strategy
points), against plain top-3 retrieval on the same store. Observations, 5 cases, 2.5 Flash:

| Observations on v4_deduped | Plain search | With the filter |
|---|---|---|
| Relevance | 4.60 | 4.00 |
| Efficiency | 4.00 | 3.60 |
| Unique lessons | 3.00 | 3.00 |
| Redundancy ratio | 25.0% | 40.0% |

Strategy-point relevance fell too (3.20 to 2.80), with efficiency about level (1.80 to 2.00); the full
row is in [the reranker table](#the-model-reranker). The record names two causes. The wider fetch (ten instead of
three) pulled in items on the right topic but for the wrong situation, which plain top-3 had left out.
And the gate over-removed: in one case it dropped one of two observations about endgame consensus
voting that taught different lessons (passive communication against vote alignment). Store dedup and
the filter both remove repetition, so on a cleaned store the filter removes useful items instead. The
measurement is recorded in the
[store dedup → retrieval impact log](../dedup/store_retrieval_impact/experiment_log.md), "Filtering on
a Clean Store"; this report is the finding's home.

*How sure we are.*

- Five cases and one judge per run; the dirty-store runs used three different judges.
- v4_deduped was later found to be over-merged: on 39 cases it lowered observation relevance against
  the raw store (4.51 to 4.26), and a more conservative dedup did better
  ([store dedup → retrieval impact](../dedup/store_retrieval_impact/experiment_log.md), "Phase 2"). The
  clean-store test therefore ran on a store that had lost useful entries, which may have left the
  filter less to work with. It was not repeated on the conservative store.
- The 0.92 line was set on gemini-embedding-001. Today the line is kept per embedding model
  (`Agents/llm_factory/embeddings.py::SIMILARITY_THRESHOLDS`, `retrieval_dedup_gate`); the Qwen value
  (0.80) was remapped by percentile, not re-tested by this study.

*What shipped (checked 2026-10-26).* The filter is built and off for every role by default and in
served games (`Agents/memory/retrieval/pipeline.py::_apply_filtering`, `filtering_config`). The record
of the time kept it as a switch for the gaps between batch dedup runs. The cap of three per situation
is the one step of that pipeline that always runs.

### The model reranker

**On a cleaned store, letting a model re-score the candidates made strategy-point sets less repetitive
and slightly more relevant on 5 cases; observations gained nothing; adding the filter first made it
worse.**

*Setup (2026-05-23).* The search fetched ten per situation; a model call (Gemini 3.1 Flash-Lite, the
players' model then) read the situations and the candidate texts, with no other game context, and
scored each candidate. The best three of each kind were kept in total, not per situation, and the
reranker skipped any kind with three or fewer candidates. The cap of three per situation followed.
Stores: v4_deduped (cleaned) and v4 (with duplicates). The same 5 cases; judge 2.5 Flash.

*Strategy points* (5 cases):

| Configuration | Store | Items shown | Relevance | Efficiency | Unique lessons | Redundancy ratio |
|---|---|---|---|---|---|---|
| Plain search | v4_deduped | 3.80 | 3.20 | 1.80 | 1.20 | 72.3% |
| Filter only | v4_deduped | 4.00 | 2.80 | 2.00 | 1.00 | 77.3% |
| **Rerank only** | v4_deduped | 2.80 | 3.80 | 3.60 | 1.80 | 40.0% |
| Filter, then rerank | v4_deduped | 2.80 | 3.00 | 2.20 | 1.00 | 66.7% |
| **Rerank only** | v4 | 2.80 | 4.00 | 3.40 | 1.80 | 40.0% |

Reranking alone raised efficiency from 1.80 to 3.60 and lowered the redundancy ratio from 72% to 40% on
the cleaned store; on the store with duplicates it did about as well, with the highest relevance of any
row (4.00). By case: a healer's day discussion went from relevance 3 / efficiency 2 to 5 / 5, a
villager's day discussion from 5 / 1 to 5 / 5, and a healer's day vote stayed at 1 / 1. Filtering before
reranking scored below reranking alone: the filter removed items the reranker would have kept, for the
same reasons as on the cleaned store above.

*Observations* (5 cases):

| Configuration | Store | Items shown | Relevance | Efficiency | Unique lessons | Redundancy ratio |
|---|---|---|---|---|---|---|
| Plain search | v4_deduped | 4.00 | 4.60 | 4.00 | 3.00 | 25.0% |
| Rerank only | v4_deduped | 3.00 | 4.40 | 3.80 | 2.00 | 33.3% |
| Rerank only | v4 | 3.00 | 4.60 | 3.60 | 2.00 | 33.3% |

Plain search already served observations well on the cleaned store; reranking kept three items instead
of four and lost a unique lesson. The record of the time read this as observations needing store dedup
and strategy points needing a reranker that reads the situation, not just the topic.

*How sure we are.*

- **Five cases, one judge.** "Doubled efficiency" is a change on 5 cases; read it as a direction.
- **Smaller sets.** The reranker keeps three per kind in total, so its strategy-point sets held 2.8
  items against 3.8 for plain search. A smaller set has less room to repeat itself, and the redundancy
  ratio falls when items drop and unique lessons do not, so part of the efficiency gain may come from
  set size rather than better choices. The study did not separate the two.
- **Cost not measured.** The report of the time called the call "essentially free"; no cost or latency
  was recorded.
- **Over-merged store.** As for the filter, the cleaned store was the one later found over-merged.

*In whole games.* The June static-memory A/B ran a reranked arm, on observations rather than the
strategy points this study recommended, and found no measured advantage over plain retrieval on the
town's vote accuracy (0.710 to 0.686, Wilcoxon p = 0.518, 30 paired boards, too few to exclude a small
effect); that arm also carries a drift caveat. That result is told in the
[effectiveness report](../memory_system/effectiveness/report.md), "Side-findings that shaped later
work".

*What shipped (checked 2026-10-26).* Both rerank switches, observations and strategy points, are off for
every role by default (`Agents/config/run.py::DEFAULT_RERANKING_CONFIG`). Served games retrieve strategy
points and do not rerank them, so the configuration this study recommended (rerank strategy points
only) has never run in a served game. When switched on, the reranker today calls the game's configured
model (`Agents/llm_factory::get_llm`), not Flash-Lite. A small trained model (a cross-encoder) was later
built to replace the call; it matched the LLM reranker on held-out labels and is not wired into the read
path. That work is told in the [fine-tuning report](../fine_tuning/report.md), "The retrieval reranker".

### The wider fetch: how many observations to show

**Five observations per situation scored slightly above three and seven on replayed decisions; the
change made afterwards widened the fetch but left the cap at three, so prompts kept seeing about three.**

*Setup (2026-05-24).* After the May ablation pointed to observations alone
([ablation report](../memory_system/ablation/report.md)), strategy points no longer shared the slots,
so the study asked whether more observations help a small model at a minimal thinking budget, or
dilute it. 120 decisions were drawn from 230 frozen turns (the adoption study's v2 set). For each, the
player regenerated its decision with observations only from v4_deduped, fetching 3, 5 or 7 per
situation, with no cap after the fetch. Seats describe more than one situation, so the average shown
per turn was 5.0, 7.6 and 9.8. Judge: 2.5 Flash, scoring the decision on three 1–5 scales: action
quality, strategy application (how well it used the guidance) and grounding.

| Decisions judged (120 each) | 3 per situation | 5 per situation | 7 per situation |
|---|---|---|---|
| Action quality | 4.33 | **4.40** | 4.26 |
| Strategy application | 4.20 | **4.35** | 4.34 |
| Grounding | 4.68 | 4.68 | 4.62 |

Five scored highest on action quality (+0.07 over three) and strategy application (+0.15), with
grounding unchanged. Seven kept the strategy-application gain (4.34) but fell below three on action
quality (4.26). The record of the time read this as about ten observations per turn being where the
small model starts to lose focus.

*How sure we are.* One judge; no significance test on differences of a few hundredths to 0.15 on a 1–5
scale; replayed decisions, not games; one store. The report of the time called the gain "consistent with
no downside"; two of three scores rising slightly at n = 120 is a lean, not a demonstrated gain.

*What reached the prompt.* The change was made on 2026-06-11 (`152cf1a9`) as the width of the fetch:
the search asks for five per situation. The cap of three per situation still runs after it, so a live
prompt gets at most three observations per situation, about the three-per-situation condition above.
The five-per-situation condition (about 7.6 a turn) was measured only in this replay. The only effect
of the wider fetch is the refill when two situations find the same item (Part 1, step 3). Every
observation-on campaign since June (the June A/B, v6, v7) therefore ran at an effective cap of three.
This was found on 2026-10-14 by re-checking the report against the code; the comment above the fetch in
`Agents/memory/retrieval/pipeline.py::enrich_payload_with_memory` now says so. The consequence is
small: the measured gain was +0.07 action quality with no test, and served games retrieve no
observations.

### What every stage ran into: missing lessons

**For some situations no stage could help, because the store held no lesson that fitted.** The healer's
day vote, an early vote with no information and the healer under scrutiny for how they talked, scored
relevance 1 for strategy points with plain search, with the filter, with the reranker, and with both,
on the cleaned store and on the one with duplicates. On the cleaned store there were only two strategy
points to choose from, both about mid- or endgame votes with a strong consensus forming. The judge's
reason, in the reranked run: "The current situation is an early, information-starved game with no
consensus, and the agent is under direct scrutiny for current communication behavior, making the
advice irrelevant." (`reranking/01_rerank_on_clean_store.md`, healer / day_vote.) That is one case
across five configurations. The filter study named a second gap of the same kind: no strategy point
for a healer who has revealed their role and must manage the wolves' targeting.

The wider measurement agrees. On 39 cases and three stores (raw, aggressively cleaned, conservatively
cleaned), strategy-point sets stayed about 59% redundant with about 1.9 unique lessons whatever the
dedup ([store dedup → retrieval impact](../dedup/store_retrieval_impact/experiment_log.md), "Phase 2").
Removing duplicates and filtering cannot surface a lesson that was never written. Whether this still
holds on today's store (about 500 strategy points against v4's 198) has not been measured.

## What is not known

- **None of the May stages has been tested on the ten-seat game or today's store and embedder.** Only
  the stage filter, which the May study did not include, has a ten-seat check (in the v8 report). The
  May harness and its 40-case frozen set belong to the nine-seat v4 store.
- **No stage has a whole-game result,** apart from the June reranked arm above, which was underpowered
  for a small effect and ran on observations.
- **Whether a reused day lookup fits later turns** (Part 1).

## Records

| What | Where |
|---|---|
| The filter study as written in May, with its four run dumps | [filtering/report.md](filtering/report.md); `filtering/01_…04_*.md` |
| The reranker study as written in May, with its two run dumps | [reranking/report.md](reranking/report.md); `reranking/01_*.md`, `02_*.md` |
| The capacity study as written in May, with configs and results | [capacity_limits/report.md](capacity_limits/report.md); `capacity_limits/eval_configs/`, `eval_results/` |
| Filtering on a cleaned store; the 39-case store comparison | [store dedup → retrieval impact](../dedup/store_retrieval_impact/experiment_log.md) |
| Per-day lookup reuse: the nine-seat pre-test | [per_day_discussion/experiment_log.md](per_day_discussion/experiment_log.md) |
| The reuse ruling | [v8 decisions](../memory_system/v8/decisions.md) §10 |
| Whether a cheap model can label relevance well enough to train a reranker | [labelling: context eval](../evaluation/labeling/context_eval/experiment_log.md) |
| The trained cross-encoder reranker | [fine-tuning report](../fine_tuning/report.md), "The retrieval reranker" |
| Read-path code | `Agents/memory/retrieval/` (`pipeline.py`, `plan_gating.py`, `accessors.py`, `filters.py`, `rerank_agent.py`, `dimension_gating.py`, `lookup_cache.py`, `situation_agent.py`); served config `server/game/run_config.py::game_run_config` |
| Retrieval judge and runner today | `evaluation/src/judges/prompts/retrieval.py`; `evaluation/src/cli_runner/regen_replay/both/retrieval.py`; configs `evaluation/config/reranking/`; frozen set `evaluation/frozen_eval_sets/v4_filtering_eval.jsonl` |

*Written 2026-10-26 from the three May reports (filtering, reranking, capacity limits) and their dated
addenda, the store dedup → retrieval impact log, the per-day discussion log and the v8 records; Part 1
checked by reading the code it names. No code, tests or experiments were run for this report.*
