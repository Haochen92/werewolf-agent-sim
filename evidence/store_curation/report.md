# Store curation: controlling growth and deciding which lessons to keep

This page describes how the memory store is curated today: what decides which observations and
lessons stay, which are removed, and what keeps the store's size and running cost in check. It also
covers the evidence behind each rule. The rules come from the v7 learning loop of June and July 2026,
which is described here only as the design they graduated from; its result is told in the
[v7 report](../memory_system/v7/report.md). The review sessions that shaped the rules, in date order,
are in the [experiment log](experiment_log.md).

**Version.** This describes the code at the `feature-frontend-v1` branch head on 2026-10-26
(`5d8ea41c`), checked against the code named in each statement. Every measured result below was
taken on the nine-seat v7 loop and belongs to that game, store and model; none was re-run on today's
code. No ten-seat learning tick is recorded.

## Design and evidence at a glance

- **What runs.** Two passes keep the store, both run by hand. The **credit pass** (no model call)
  grades every lesson from the memory-on games it is given, then prunes those below its comparison threshold and evicts
  the ones seats keep rejecting. The **learning tick** (paid) folds in new observations, lets
  observations that stopped recurring age out and writes new lessons; its duplicate-lesson removal is
  built and off until tuned ([batch log](../dedup/batch_dedup/experiment_log.md), 2026-10-26). It never prunes or evicts.
- **What supports it.** Eleven ways a store degrades were found in the v7 loop's runs and reviews,
  and each got a guard. All eleven guards are in today's code, one of them in a changed form. One
  threshold was checked: lessons flagged harmful on one half of a game archive stayed harmful on the
  other half in 8 of 9 cases.
- **What is not known.** The thresholds were set on nine seats and are not validated for ten. No
  learning tick has run on ten seats. Nobody has judged whether synthesised lessons are good. The
  removal rules are slow, so within any run measured so far the stores grew almost without pause.
- **Tells are not served.** The behaviour-to-role hints the v7 loop also curated are not part of
  today's game.

**Terms used below.**

- An **observation** is a short account of one move and its effect, written by a model from a
  finished game. It is evidence: it says what happened, not what to do.
- A **lesson**, stored as a **strategy point**, is advice for one role at one kind of decision,
  written by a model from a group of similar observations.
- A **cell** is one role's shelf for one kind of decision (day discussion, day vote or night). Ten
  seats drawn from twelve roles give 36 cells.
- A lesson's **lift** is the average grade of the decisions made while following it, minus the
  average grade of the same kind of decision in games played without memory. The grades come from a
  fixed table per role and action ([credit report](../credit/report.md)). Lift above zero means the
  lesson's followers did better than play without memory.
- The code calls a lesson **proven** when its lift is above zero over at least 2 follows. This is a protection rule, not statistical proof that the lesson helps. Every other lesson is
  **unproven**. Lift compares outcomes associated with following advice; it does not isolate the advice's causal effect.

## Why a store needs curating

An append-only memory risks crowding retrieval and retaining weak advice. The v7 loop exposed two reasons to curate it.

- **Volume.** Its first paid run grew the lesson store from 0 to 227 with no ceiling. Healthy cells
  held about 5 lessons; bloated ones about 34. Retrieval keeps only a few lessons per situation, so a
  crowded cell lowers the chance that the right one is among them.
- **Quality.** Without removal, a lesson that measures harmful keeps being shown and followed. And
  near-duplicate lessons split one piece of advice's follows across several rows, so none of them
  gathers enough evidence for credit to act on.

Duplicates gained additional costs once the store started grading and writing its own contents. Before
v7, a duplicate's one cost was clutter in the few retrieval slots, which a cheap dedup removed.
Credit made a duplicate lesson cost evidence (the split follows above). Synthesis made a duplicate
observation cost compute, because synthesis groups observations and every redundant one inflates
that work and the variants it writes.

The two passes address different parts of this problem: credit revisits lessons using recorded decisions; learning adds observations and synthesises advice under growth controls.

## The two passes today

```
memory-on games ──► credit pass (no model call) ──► prune, evict ──► publish
                     grade each followed lesson
offline extraction ─► learning tick (paid) ──────────────────────────► publish
                       fold observations → age out → synthesise (every 2nd tick) → lesson dedup (off until tuned)
```

Both passes live in `Agents/memory/consolidation/tick.py` and end by publishing the store to the
Postgres database the server reads (`Agents/memory/consolidation/publish.py`). No schedule runs
them. They were split on 2026-10-13: credit needs only the games' records, so it can run without model API charges, while extraction and synthesis are paid and run in batches
([v8 decisions](../memory_system/v8/decisions.md) §14). How the passes fit the rest of the memory
system is in the [v8 report](../memory_system/v8/report.md), "Keeping the store: two passes, both run
by hand"; this page gives the rules each pass applies.

### The credit pass: grade, then prune and evict

**The credit pass rebuilds each lesson's counters and applies the removal rules.** It calls no model (`tick.py::run_credit_pass`).

1. **Recount.** Every lesson's counters (follows; good, neutral and bad grades; times shown,
   overridden and judged not relevant) are set from the games in the window, not added to what was
   there (`credit.py::credit_apply`). A lesson absent from the window stops carrying old credit. A
   lesson shown on every turn of a day counts as shown once for that decision.
2. **Fold in discarded duplicates.** When the lesson dedup has discarded a lesson as a duplicate,
   the survivor records its key, and the follows recorded against that key count for the survivor
   (`credit.py::_fold_merged`).
3. **Compare with play without memory.** Each lesson's lift is taken against the memory-off games of
   the same kind of decision, supplied as a separate set of games. A lesson whose decisions have no
   memory-off comparison is left unscored and is never pruned.
4. **Apply the rules** (`store_ops.py::prune_and_evict`), in this order:
   - **Protect** a proven lesson (lift above 0, at least 2 follows). The prune and evict rules spare it for this pass; a later window can change its status.
   - **Prune** a lesson whose lift is below −0.15 after at least 8 follows.
   - **Evict** a lesson shown at least 8 times and never followed, but only when seats overrode it
     ("it applies, but I have a better move") at least once and at least as often as they judged it
     not relevant. A lesson mostly judged not relevant was shown in the wrong situation; that is a
     retrieval miss, and it is kept (`store_ops.py::_evict_ok`).

Every change is recorded with its numbers (`db.py::record_credit_run`). In a game with a human seat
only the AI seats' decisions are graded (`credit_rules.py::iter_eval_cases`; since 2026-10-26,
[v8 decisions](../memory_system/v8/decisions.md) §15). The one recorded pass, over 20 ten-seat games on
2026-10-14, pruned 4 lessons and evicted 4 ([v8 report](../memory_system/v8/report.md), "Does the
credit pass run on ten-seat games?").

### The learning tick: fold, age out, synthesise, dedup

**The learning tick adds evidence and advice; it removes only observations (duplicates at the fold, and those that stop recurring), while its duplicate-lesson removal is off until tuned.** It is `tick.py::run_tick`, which turns prune and evict off for the call.

1. **Fold in new observations** from the offline extraction job (`obs_fold.py::merge_new_obs`). A
   new observation that duplicates a stored one is discarded, and the stored one's count rises. A
   near-duplicate is kept as a separate record, and no text is rewritten. Stored observations are
   never judged against each other (the freeze-old guard): the fold names the observations it
   appended as the only new ones (since 2026-10-26; the [dedup report](../dedup/report.md), "Preserving old entries during incremental dedup"). The judge is Claude Haiku 5.5 (`TickConfig.dedup_model`). The
   dedup stack itself is told in the [dedup report](../dedup/report.md).
2. **Advance the clocks.** For each observation the database keeps the tick it first appeared and
   the tick its count last rose (`tick.py::_stamp_obs_generations`; table `obs_generations`).
3. **Age out** an observation once it has gone 4 ticks per time it has been seen without being seen
   again (`store_ops.py::evict_observations`). An observation seen once gets 4 ticks; one seen ten
   times gets 40; any new sighting restarts the clock.
4. **Synthesise**, on every second tick (`store_ops.py::synthesize`; Claude Sonnet 5.5,
   `TickConfig.model`). Three checks decide where synthesis runs, all before any grouping is done:
   - a cell is considered only if at least 4 observations *arrived* since the last synthesis, counted
     by the tick they first appeared;
   - a cell already holding 12 unproven lessons is skipped (proven lessons do not count toward the
     12);
   - within a cell, only groups that contain a new observation are synthesised.

   A cell with fewer than 3 lessons is exempt from the first two checks, so it can refill. The
   groups are built from the new arrivals outward: each new observation gathers its nearest
   neighbours in the cell, at most 15, within the same situation and game stage. An observation with
   no close neighbour is never synthesised on its own. Each lesson already followed at least 5 times
   is shown to synthesis with its lift, so the model can take poor past scores into account. Whether that produces better advice has not been measured.
5. **Remove duplicate lessons**: built, off until tuned (`TickConfig.sp_dedup=False` since 2026-10-26;
   [batch log](../dedup/batch_dedup/experiment_log.md), 2026-10-26). Switched on, it runs only when synthesis added lessons
   (`store_ops.py::_dedup_strategy_points`). A new lesson that duplicates an older one is discarded;
   the older one, which holds the credit history, always survives and records the discarded key. Two
   lessons are never merged into one text.

The tick then saves a snapshot of the generation and publishes.

### What a seat sees of this

In served games memory is the player's switch and starts off; with it on, seats are shown lessons
only, never observations (`server/game/run_config.py::game_run_config`). The counts the credit pass writes also order what a seat is shown
(`Agents/memory/retrieval/filters.py`). Lessons followed at least 5 times with more good grades than
bad are placed first. When every kept lesson is such a lesson, the lowest slot goes to the best
untried one, because a lesson earns credit only when a seat follows it, and a lesson never shown can
never earn. This read-side test of "proven" differs on purpose from the credit pass's: the read path
has no memory-off averages to compare with. The full read path is in the
[v8 report](../memory_system/v8/report.md), "In a game: looking lessons up".

## Why the two stores are kept differently

Observations record past moves; lessons recommend future ones. Their retention rules therefore use different signals.

| | Observations | Lessons |
|---|---|---|
| What it is | what happened in a game | what to do in a situation |
| Used for follow-based credit? | no: seats report follows only for lessons; an observation can carry its decision's fixed-table grade (`decision_grade`), which synthesis shows only when `TickConfig.synth_outcome` is `"grade"` (default `"verdict"`) | yes, when a seat reports following it |
| Signal used for retention | recurrence and time since last sighting | lift and reported adoption |
| A duplicate | is discarded and the stored one's count rises | stays while the lesson dedup is off; when it runs, it is discarded and its follows go to the survivor |
| Removed when | it stops recurring | it measures harmful, or is shown and rejected on its merits |
| What can go wrong | volume | synthesis can write bad advice |

The lesson side carries most of the guards because its growth step is a model writing new text, so
growth itself can create bad content. Observations can also contain extraction errors; their retention rule uses recurrence, not a direct quality judgement. Dedup and aging control their volume.

Four rules hold across both:

- **Credit feeds curation; it does not judge it.** The lift that decides what to keep never decides
  whether memory works. That verdict comes from separate whole-game tests (the
  [memory hub](../memory_system/report.md)).
- **An item's meaning stays fixed so its evidence stays meaningful.** Lesson text is never merged,
  and a dedup only ever discards the newer copy, so the counters on a surviving lesson still measure
  the advice they counted.
- **Cheap checks run before paid ones.** Exact-match and count checks run before any embedding
  search, and an embedding search only nominates candidates for the model judge.
- **No lesson is removed for age.** A lesson leaves only by measuring harmful or by being rejected on
  its merits; one currently protected by the credit rule is spared by prune and evict. Observations are the exception by design: recurrence is
  the signal this retention rule uses, so they leave when it stops.

## What supports it: eleven failure modes and their guards

The rules address failures observed in v7 runs or identified in design reviews. The v7
runs could not answer whether memory compounds (the [v7 report](../memory_system/v7/report.md),
"The June loop runs"), but they surfaced most of what is known about curating a store. The
"Surfaced by" column separates what the runs showed (rows 1–4) from what reviews caught by reading
the mechanism.

| # | Failure | Surfaced by | Guard | In today's code |
|---|---|---|---|---|
| 1 | Lesson store grew without limit: 0 → 227, bloated cells about 34 lessons against about 5 | the first paid loop run | a cap per cell, on unproven lessons since 2026-07-14 | yes: 12 unproven (`TickConfig.synth_cell_unproven_cap`) |
| 2 | Already-condensed groups re-synthesised every tick, about 6× growth per run (5.4 → 34 lessons per cell) | loop run store records | only groups with a new observation are synthesised; groups grow from new arrivals | yes (`store_ops.py::_synth_cluster`) |
| 3 | Synthesis stalled silently: counting the net change let aging-out cancel new arrivals, so the trigger read "nothing new" | generation 6 of the v2 smoke run | arrivals counted by the tick they first appeared | yes (the `obs_generations` table) |
| 4 | A harmful lesson escaped pruning for a generation: the dedup added a discarded duplicate's counts to it after the prune had run | forensics of the runs' below-baseline tail | prune last, on the counts after dedup | changed: pruning moved to the credit pass, which recounts from the games and folds in discarded duplicates' follows first (`credit.py::_fold_merged`) |
| 5 | Near-duplicate lessons split one lesson's follows, so no row gathered enough evidence | design review, 2026-06-19 | keep/discard lesson dedup onto the older, credited survivor | built, off until tuned (2026-10-26, [batch log](../dedup/batch_dedup/experiment_log.md), 2026-10-26); the survivor records the discarded key (v8 decisions §14) |
| 6 | Good advice evicted for a retrieval miss | the v7 plan's pre-run fix programme | evict only when overrides dominate; spare a lesson mostly judged not relevant | yes (`store_ops.py::_evict_ok`) |
| 7 | A new lesson could never earn credit: credit needs follows, and a cell full of proven lessons never showed it | lane review, 2026-07-14 | a guaranteed slot for the best unproven lesson; the cap counts unproven lessons only | yes (`filters.py::_ensure_exploration_slot`) |
| 8 | Any observation seen twice never aged out, so store size had no bound | store-bounding review, 2026-07-14 | aging out scaled by count, clocked from the last sighting | yes (`store_ops.py::evict_observations`) |
| 9 | Grouping cost grew with the whole store, and was paid even by cells the checks then skipped | store-bounding review, 2026-07-14 | checks before grouping; groups grow from new arrivals | yes (`store_ops.py::synthesize`) |
| 10 | Repeated dedup passes kept re-judging old entries as neighbours arrived, eroding the store past the ~17% duplicate rate where it worked best | dedup campaign, 2026-06-09 ([diagnosis](../dedup/incremental_convergence.md)) | stored entries are never judged against each other | yes, in the observation fold, which names its new entries (the lesson dedup does the same but is off until tuned; since 2026-10-26; the [dedup report](../dedup/report.md), "Preserving old entries during incremental dedup") |
| 11 | Synthesis rewrote advice that pruning had just removed, because observations' verdicts follow which side won | design, 2026-06-19 | synthesis shown each lesson's measured lift | yes (`store_ops.py::_track_record`); the mechanism is checked, the quality of what it writes is not |

The v7 loop also checked, every generation, that each lesson's memory-off comparison came from the
same grading as its follows (`evaluation/src/loop/invariants.py::assert_baseline_coherence`). That
check did not graduate. Today the credit pass takes its memory-off games as a separate, required
input and grades them with the same table, but nothing asserts it.

### The one threshold that was checked

**One split-archive check found that negative lift often persisted on held-out games.** It supports the retention signal's direction on this sample, without establishing that the removed lessons caused harm. The review ranked the prune threshold (−0.15) as the only setting
that could plausibly flip a run's conclusion, since it decides what is deleted every generation.

*The test* (2026-07-14, no cost). A nine-seat game archive was split in two by game, and every
lesson's lift was measured on each half separately, so the flags from one half could be checked on
games that never produced them.

*The result.* The two halves' lifts correlated at +0.54 over 31 lessons that could be compared
(noise would give about 0). Of the 9 lessons flagged harmful on the first half, 8 stayed negative on
the second, against a 61% rate for lessons overall. The one that flipped had 3 follows, below the
rule's floor of 8; all 4 flagged lessons with at least 8 follows stayed negative.

*How sure we are.* It shows direction on a small sample, not a calibrated threshold. It was run on
nine seats, and the threshold is unvalidated for ten. Method and data:
[the strategy-point store](strategy_points.md) §6.

The other settings were set by design reasoning and never swept, with three exceptions anchored in a
record: the cap of 12 (from the 227-lesson run: about 2.4 times a healthy cell, well under a bloated
one), the aging-out allowance of 4 (an allowance of 2 dropped about 250 observations a generation and
starved synthesis), and the cap of 3 lessons kept per situation (kept when the May capacity study scored five per
situation slightly higher; the fetch widened to five and the cap stayed, see the
[retrieval report](../retrieval/report.md), "The wider fetch").
Every setting, with where its value came from, is in the [settings ledger](knobs.md).

## How the stores grow: no plateau in any run so far

**Do the stores level off? Not within any run measured: removal is slow next to how often the passes
run, so the stores grow almost without pause.**

The rules' own arithmetic shows why (one v7 generation corresponds to one learning tick today). An
observation seen three times needs 12 quiet ticks before it
ages out, so in a run of ten ticks or fewer only observations seen once ever leave. A lesson needs 8
follows to be pruned or 8 showings to be evicted, which many lessons never reach in ten generations.
Within a run like that, the lesson store is held mainly by the cap of 12 unproven lessons per cell,
not by removal.

The July v7 learning run shows the same (4 generations of 10 memory-on games each; the run's
generation history, `../memory_system/v7/execution_plan/data/v7_compound_town5/loop_history.json`):

| After generation | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| Observations kept | 187 | 380 | 547 | 718 |
| Observations aged out | 0 | 0 | 0 | 0 |
| Lessons kept | 0 | 82 | 77 | 168 |
| Lessons pruned | 0 | 0 | 5 | 5 |

Nothing was evicted in any generation; 6 and 7 never-followed lessons were spared in the last two
because seats mostly judged them not relevant. The tells store grew the same way in a 30-game
simulation (see [the tells, in the v7 loop](#the-design-it-graduated-from-the-v7-loop)).

**How the design limits repeated work.** The controls aim to tie model work mainly to new arrivals, instead of reprocessing the entire store each tick. The fold's judge sees only groups that contain a new observation. Synthesis groups only from new
arrivals (a cell being refilled regroups in full), after checks computed from counts alone. Credit is arithmetic over the games in its window.
This does not make total cost independent of store size: searching, publishing, storage, re-embedding the whole store at each tick's fold, and occasional full regrouping still depend on the stored records. What growth can still cost is quality: stale
observations stay in the store and can join a synthesis group as members. That is why aging out
exists, even though it rarely bites within a short run.

*How sure we are.* Whether any store would level off at these rates was never estimated: the v2
smoke run's six generations are too few to fit a curve. Today's published store holds 2,008
observations and 490 lessons; no learning tick has run on it, so its growth under the tick is
unrecorded.

## The design it graduated from: the v7 loop

The rules above were built for the v7 loop (`evaluation/src/loop/`), which ran on the nine-seat game.
It played games in generations and, after each generation, ran one step that did everything: credit,
aging out, synthesis every second generation, lesson dedup and, last, prune and evict
(`evaluation/src/loop/consolidate.py`). The lesson and observation rules graduated into
`Agents/memory/consolidation/` on 2026-07-21 and were ported to the ten-seat game on 2026-10-13, when
the one step became the two passes above. The loop's run checks stayed behind with its experiment
harness: the check that observations never reached a prompt, the check on which factions had memory,
and the memory-off check above. Served games enforce strategy points only through their own
configuration (`server/game/run_config.py::game_run_config`).

The verdict on the loop, in the owner's wording: the June static-memory A/B reported improvements on
selected town decision measures; a later A/B on a different store, run against a higher no-memory
baseline, found no town effect and was not a replication of the June test; separately, the
pre-registered v7 endpoint detected no compounding benefit. The investigation is closed; the
hypothesis was not disproved. Those experiments used the player model at its minimal thinking setting. The test and its numbers are in the [v7 report](../memory_system/v7/report.md).

**The tells, in the v7 loop.** The loop curated a third store that did not graduate: **tells**,
behaviour-to-role hints mined from past games ("a player accused of holding a hostile role
counter-accuses the accuser of using the claim as a distraction": evil in 27 of 30 sightings). Once a
generation a *fold* matched new wordings to known tells, recounted every tell's evidence from an
append-only record, retired tells that never recurred, and published a capped list of at most 48
per channel for a detector to scan. A short book of the strongest tells was shown to every seat. The
fold ran four times inside the July learning run, adding 170 to 202 new tells each time, and the
July test's memory games showed every seat a book; the effect of the tells was never separated from
the lessons'.

Before it was built, the fold was tried on 1,109 candidates mined from 30 nine-seat games. The store
reached 740 entries, with about 22 new ones a game in games 21–30. A whole-corpus review took it to
596 (one family of retaliation votes alone had arrived as 27 wordings), and new entries still arrived
at about 16 a game. The share of each batch of new entries that was ever seen again fell from 37%
(games 1–10) to 19% (11–20) to 11% (21–25); later batches had less time to recur, so this does not
show the core had stopped growing. The vote channel was 38% redundant and the discussion channel 8%.
The mechanism, its checks and its gaps are in [the tell store](tells.md), which describes the v7
loop only; the build journey is in the [tell extraction log](../extraction/tell_extraction/experiment_log.md).

In served games no tell book is loaded: the book is read only when `WW_TELL_BOOK` is set
(`Agents/memory/tell_book.py::tell_book_block`), and in the repository only the loop's driver and
tests set it; nothing in the server code or its deployment files does.

## What is not known

Each item limits a specific claim above.

- **The thresholds on ten seats.** Prune, protect and evict use the nine-seat values, unvalidated for
  ten seats. The four prunes of the one ten-seat credit pass rest on them.
- **The learning tick on ten seats.** `ten_seat_v2` was built by a one-off script, not by the tick,
  and no ten-seat tick is recorded. The rule screen that left 37 lessons out of the published store
  was a one-off review; nothing screens what the tick would write.
- **Whether synthesised lessons are good.** The checks, the cap and the track record are tested as
  mechanism; no judge has scored whether a synthesised lesson is a good condensation of its group.
- **The read-side ordering.** The proven-first order and the slot for an untried lesson are on by
  default; their effect on what seats follow has not been measured.
- **The similarity thresholds.** The grouping thresholds are set per embedding model (0.46 on Qwen,
  the served embedder; 0.65 on gemini-embedding-2), the Qwen values remapped from the Gemini ones by
  percentile on 2026-10-12. The original values were chosen before the tells work found that
  absolute cosine scores in these stores sit close together; a check of where each threshold falls in
  its own store's spread was never run.
- **Whether curation makes play better.** No test compares a curated store with an uncurated one, and
  no ten-seat test compares memory on with off ([v8 report](../memory_system/v8/report.md), "What is
  not known").

The agenda of the 2026-07-14 ownership walkthrough, which this page used to carry as its §6, is kept
with its item numbers in the [experiment log](experiment_log.md), entry 9; code comments and the v7
plan cite those items as "report §6.N".

## Sources and implementation

| What | Where |
|---|---|
| The two passes and their command line | `Agents/memory/consolidation/tick.py` (`run_credit_pass`, `run_tick`) |
| Settings | `Agents/memory/consolidation/config.py::TickConfig` |
| Prune, evict, aging out, synthesis, lesson dedup | `Agents/memory/consolidation/store_ops.py` |
| Observation fold | `Agents/memory/consolidation/obs_fold.py::merge_new_obs` |
| Credit recount and duplicate folding | `Agents/memory/consolidation/credit.py::credit_apply` |
| Clocks, records of each pass, publishing | `Agents/memory/consolidation/db.py`, `publish.py`; `Agents/memory/persistence/postgres.py::publish` |
| Grouping thresholds | `Agents/llm_factory/embeddings.py::SIMILARITY_THRESHOLDS` |
| Read-side ordering | `Agents/memory/retrieval/filters.py` |
| The v7 loop | `evaluation/src/loop/` (`consolidate.py`, `driver.py`, `invariants.py`, `tell_fold.py`) |
| Mechanism detail as built for v7 | [observations](observations.md), [strategy points](strategy_points.md), [tells](tells.md), [settings ledger](knobs.md) |
| Review sessions and rulings | [experiment log](experiment_log.md) |
| Why the passes are split | [v8 decisions](../memory_system/v8/decisions.md) §14 |
| Design lineage | [`consolidation_design.md`](../memory_system/v7/consolidation_design.md) (2026-06-19); the tell ledger in [`read_tactic_credit_redesign.md`](../credit/read_tactic_credit_redesign.md) §3 |

*Rewritten 2026-10-26 from the July framework document, whose text is in git history. No code, tests
or experiments were run for this revision; statements about today's code were checked by reading it.*
