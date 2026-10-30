# Memory chapter: what we present and defend

Draft for the owner's edit, 2026-10-26. Working backwards: this page fixes what the memory chapter claims
and the evidence each claim rests on. Everything outside it is archive: kept, not presented, not
polished. Each row was checked against the code at `4a514794` and the records the same day.

**Execution states.** *Served*: runs in served games. *Offline*: an offline job that has actually run on
the ten-seat system. *Built, not exercised*: implemented, no recorded ten-seat run. *Off*: built and
switched off. The pipeline migration (planned, not built) will change some of these; the rows it
touches are marked ⟳.

**Support types.** Experiment · failure investigation · operational constraint · design judgement ·
owner ruling.

## The argument

The system turns past games into situational advice. Plausible advice can be irrelevant, misleading or
counterproductive, so the engineering is in controlling how advice is **produced**, **selected** and
**retained**.

```
game records → observations → lessons → retrieval during play → feedback and curation
```

## 1. Producing advice

| Step | What runs (anchor) | State | Support | The numbers to defend | Trade-off |
|---|---|---|---|---|---|
| Extraction runs after games, in batches, never during play | `scripts/extract_batch.py` → `Agents/memory/extraction/offline.py::extract_cases` (first call per game direct, to write the prefix cache) | Offline ⟳ (served games' inputs are saved; nothing extracts them yet) | Operational constraint + owner ruling (v8 decisions §11) | Sonnet 5.5, measured over 21 games: about $0.95 a game, against about $0.45 with the cache working; 15% of batch requests wrote the prefix instead of reading it (caching report §4.6) | lessons lag the games by hours; batch cache hits are not guaranteed |
| An observation records one move and its effect, written by a model that sees every hidden role | `Agents/memory/extraction/inputs.py::format_extraction_inputs` | Offline | Design judgement | — | the extractor knows more than any player did; the lesson must be usable without that knowledge |
| A second pass corrects the outcome halo | `Agents/memory/extraction/dehalo.py::apply_judgments` (part of the batch job by default) | Offline | Experiment, twice: the problem and the fix | **Problem** (1,472 observations, 40 games): a good move was called positive 23% of the time for the losing side, 83% for the winning side. **Fix** (482 observations, 19 games): the losing side's negative verdicts fell 53% → 27%; the winning side's positive ones barely moved, 57% → 54%. It revises 25–29% of verdicts per run | one more batch per game (about $0.006); it relabels verdicts, it does not rewrite text |
| Synthesis turns a cell's observations into lessons | `Agents/memory/consolidation/store_ops.py::synthesize` (Sonnet 5.5) | Ran once, in the one-off build of the published store ($5.31); the regular cadence is built, not exercised | Design judgement; a rule review of its output | The review (four model readers) flagged 37 of 605 lessons (6.1%) as breaking a rule; they and 78 reader-found duplicates were left out of the published store | nothing screens what later synthesis writes; whether lessons are strategically good was never judged |

## 2. Selecting advice during play

| Step | What runs (anchor) | State | Support | The numbers to defend | Trade-off |
|---|---|---|---|---|---|
| Retrieve for the situation, not the role | `Agents/memory/retrieval/pipeline.py::enrich_payload_with_memory`; the seat describes its situation in a short model call (`situation_agent.py`) | Served | Failure investigation: a whole-role document of 228 items was applied where it did not hold | fetch 5, keep up to 3 per situation, up to 2 situations | a model call per lookup; a lookup can miss a lesson that fits |
| Reuse a lookup until the situation changes | `Agents/memory/retrieval/lookup_cache.py` (discussion turns until a new claim; within a night) | Served | Operational constraint (cost and latency) | about 60 → 38 lookups in one measured game | later turns may get advice fitted to an earlier moment (unmeasured) |
| Seats are shown lessons, never raw observations | `server/game/run_config.py::game_run_config` | Served | Owner ruling 2026-07-15: observations are material for synthesis | — | a lesson is one step removed from what happened |
| No lookup on day 1 or its night | `Agents/memory/retrieval/plan_gating.py::retrieval_plan` | Served | Design judgement: nothing has happened yet that a lesson could match | — | night-1 lessons exist in the store and go unused |
| Town seats get no lessons on discussion turns; town votes are served like every other side's | `plan_gating.py` (`TOWN_UNSERVED_PHASES`) | Served once redeployed | Owner rulings (v8 decisions §5, §17): withheld information, the cost v7's credit missed, cannot be graded in talk, so town discussion advice is reviewed by the owner into role prompts; the vote rules now grade an abstention that leaves a day without a lynch | 76 town vote lessons were already in the published store, never served | town vote lessons enter play unreviewed; credit is their check |
| Each shown lesson gets a verdict: follow, override or not relevant | `Agents/turn/adoption.py::process_strategy_adoption` | Served | Design judgement: credit needs to know what was followed | — | the verdict is the seat's own report, not proof of cause |
| Lessons with a good record go first; one slot is kept for an untried lesson | `Agents/memory/retrieval/filters.py::partition_proven_first`, `_ensure_exploration_slot` | Served | Design judgement (a new lesson could otherwise never earn credit) | 29 of the 490 published lessons count as proven | the "proven" rule is a heuristic, not evidence that a lesson helps |

Reliability details worth one line each: the situation call retries once with the schema enforced, then
falls back to a generic query (`situation_agent.py`); a memory-on game is refused (409) when no usable
store is published (`server/routes/_shared.py::require_memory_available`).

**Rejected, one line:** reranking and filtering after the search are built and off; the May studies found
no clear gain (5 cases; 120 decisions).

## 3. Retaining advice

| Step | What runs (anchor) | State | Support | The numbers to defend | Trade-off |
|---|---|---|---|---|---|
| Dedup keeps or discards; it never rewrites text | at extraction write: `deduplication::run_downstream_observation_dedup`; at the tick's fold: `consolidation/obs_fold.py` (triage-only) | Write step offline (the published store: 2,277 → 2,008 observations); fold built, not exercised | Experiment + failure investigation | Aggressive dedup lost relevance (40 scenarios: 2 better, 24 the same, 14 worse); merged text invented facts in 3 of 9 reviewed merges | copies stay in the store as bloat |
| Old entries are never judged against each other | `batch_deduplication/operations.py::_frozen_old_conflict`; the caller names the new entries | Built | Failure investigation: a second full pass removed another 45 of 432 entries (10.4%) | — | duplicates already in the store stay |
| Credit grades the decisions behind each followed lesson against the hidden roles, relative to memory-off play of the same role and decision | `consolidation/credit.py::sp_lift` (small samples shrunk); `store_ops.py::prune_and_evict` | Offline ⟳ (one run, 20 batch games) | Design judgement: win or loss is mostly the deal, and a deceiver's win can hide bad play; failure investigation (v7): abstention scored zero and survived pruning | the one run: 148 lessons credited, 4 pruned, 4 evicted, 50 protected (it ran; it does not show credit helps) | rules cannot grade discussion; thresholds are v7's, unvalidated for ten seats |
| Credit (free) runs apart from learning (paid) | `consolidation/tick.py` (`credit` / `learn`) | Credit offline; learning built, not exercised | Owner ruling (v8 decisions §14) | — | two passes to operate |
| Growth controls | `store_ops.py::evict_observations` (age-out), `TickConfig.synth_cell_unproven_cap = 12` | Built, not exercised | Failure investigation: a nine-seat run grew 0 → 227 lessons with bloated cells | 18 of 36 published cells already hold more than 12 unproven lessons, so synthesis would skip them until credit drains them | stores still grow; no plateau measured |
| Publish replaces the served index | `persistence/postgres.py::publish` | Offline ⟳ | Design judgement: counters are recounted from the records, so adding would double-count | 490 lessons, 2,008 observations published 2026-10-14 | a reader mid-publish can see a partial index |
| Provenance: every item can be traced and every change audited | observations carry `game_id`; lessons carry `source_observations`; a discarded duplicate lesson's key is listed on its survivor (`operations.py::_merged_metadata`); every prune and evict is logged with its numbers in `credit_runs.changes` | Served records; offline logs | Design judgement: credit and any later reversal (for example, dropping what human games taught) need to find an item's sources | — | a discarded duplicate *observation* only raises its survivor's count; its own key and game are not recorded |

**Rejected, one line:** the lesson dedup after synthesis is built and off; on the labelled set its judge
deleted 7 distinct lessons.

## 4. Product

| Step | What runs (anchor) | State | Support | Trade-off |
|---|---|---|---|---|
| Memory is the player's switch, off by default | `TicketOffice.tsx` `useState(false)`; deployment gate `WW_MEMORY_ENABLED` (on in production since 2026-10-14) | Served | Owner ruling 2026-10-26: its benefit on ten seats is untested, and testing it needs new labelling and runs; memory on is for demonstration | players who never open the switch never see the feature |

## 5. Does it help?

The earlier fixed-store test reported a limited positive result on selected town measures: the healer
saved the real target 37% → 60% of the time (p = 0.005) and town eliminations hit an enemy 47% → 64%
(p = 0.028), while the town's win rate rose 27% → 43% (p = 0.27), with multiple-comparison and
low-baseline caveats (nine-seat game, 30 paired boards). A later comparison on a different store found no
clear benefit (+6 points, p = 0.77), in a period whose no-memory baseline had risen. The learning loop's
final memory also showed no benefit (town decision score 0.147 lower, worse on 19 of 30 boards, p = 0.065;
its memory included tells). The ten-seat system has not been tested against memory off.

## 6. Gaps

- The ten-seat memory has not been tested against memory off.
- No learning tick has run on ten seats; credit has never read a served game.
- Nobody has judged whether synthesised lessons are strategically good.
- Stores keep growing; no plateau has been measured.
- Credit's thresholds are unvalidated for ten seats.

## Not presented (archive)

Retrieval filtering, reranking and capacity studies (beyond the one line); fine-tuning; the stage filter;
tells; namespace augmentation; the early unpaired batches and the `v5_1` pilot; the replay screens'
lever ladder; the dedup prompt and threshold tuning history; v7's internal plans and reviews; v8's
gate reads and seeding data.

## Questions for the owner

1. ~~Memory off by default: the reason?~~ Answered 2026-10-26 (section 4).
2. ~~The abstention blind spot?~~ Kept as the v7 story that shaped credit's design (owner 2026-10-26).
3. Anything here you would not want to defend, or anything missing you would?

## L2 evidence selected on 2026-10-27

The four L2 pages requested by the owner select the following supporting detail from the approved
content plan. This extends the earlier archive boundary for the specific retrieval-fit story and
supporting checks below; it does not bring every filter study or experimental run into the chapter.

| Page | Selected evidence and scope | Source |
|---|---|---|
| Matching situations | 96 of 352 lookups in seven ten-seat games on the earlier 12-game store; four Sonnet model readers: 39/268 lessons fit, 79 partly, 150 not; 36/96 lookups had a fit. Discussion/vote/night fit: 7/13/19%. Current query composition and numeric overwrite; retrieve five, keep three; separate retrieval-proven heuristic from credit protection. Stage filter retained as a qualitative trade-off, off in served games; no new whole-game benefit claim. | situation_summary/report.md §§1–5; situation_dimensions/report.md; v8/report.md retrieval review; retrieval/filters.py and plan_gating.py inspected 2026-10-27 |
| Store upkeep | Two-pass dedup 99/111 label agreement versus best single model 96/111, historical nine-seat set. A model judge flagged unsupported context in 3/9 reviewed merges; classification agreement did not validate rewritten text. Current write/fold/dedup states and provenance limitations retained. | dedup/report.md; batch_dedup/experiment_log.md |
| Curation | 13/15 reported follows matched actions in a model-read sample; current score compares like decisions with memory-off and shrinks by n/(n+5). Prune/protect/evict rules are heuristics carried from v7, not calibrated ten-seat findings. Abstention's 19 follows: 2 good/15 neutral/2 bad before, 2 good/17 bad after; score 0 to −0.62 after correcting rules and baseline. One 20-game ten-seat credit demonstration, not a learning-cycle or benefit test. | credit/report.md §§3–6; consolidation/credit.py; retrieval/filters.py |
| Effectiveness | June and later stores kept separate. July pre-registration preceded learning; endpoint amendment followed learning but preceded test games. Trend simulation's 11% detection at 24 games concerns an assumed +0.15 gain and was not repeated for the amended paired endpoint. Endpoint −0.147, 19/30 worse, paired t p=.065 and Wilcoxon p=.105; lessons plus tells as treatment. **Added 2026-10-28 (page reorganised around what each test led to; only findings still in today's design):** early unpaired batches and the `v5_1` pilot, one row only, as the reason for paired boards, a frozen store and a same-window baseline (extends the archive line above). June: no deceiver benefit (wolf 33% → 30%, p=1.00; lone killer 40% → 20%, p=.15), read as "a win can hide bad play", which is why credit grades decisions, not results; a baseline from an earlier period shifted (Fisher p=.0028), so a baseline is played in the comparison's own window. v6: town lessons arm trended worse on vote accuracy (−0.086) and correct eliminations (−0.103), p about .19–.25, not significant; town lessons repeated the town's own weak play, read from examples (the log's content analyses are word-based or qualitative, never judge-confirmed). Supports "the advice itself was one limit", never "the limit". NOT presented: the v6 "77% vs 32% abstain" (withdrawn 2026-10-28, day-2-heavy follows against an all-day rate) and "followed 63–66% vs 69%" (same comparison, not re-checked by day). Retrieval mismatch from v6 not presented: its fix (field-matching tilt) showed no benefit and is off. Next-test sizes: SD of the July per-board gaps 0.418 (30 boards, nine-seat); 95% margin ±0.15 at 30 boards, ±0.11 at 61, ±0.07 at 138; 80% power for a 0.15 gap at 61 boards, for 0.10 at 138. Cost per game: $0.08–0.26 on Haiku 5.5 (16 memory-off ten-seat games, $2.48 total); memory-on cost not measured on its own. | effectiveness/report.md; effectiveness/detailed_results.md (June A/B, side-findings, discarded baseline); v6_sp_ab/experiment_log.md (mechanism 1, 3, 4; caveats); v7/report.md; v7_endpoint_ab/paired_boards.json; gameplay/data/persona_voice_games/README.md; retrieval/report.md (field-matching tilt off); Evaluation/fair_comparisons page |

**Current routing boundary:** town-vote retrieval is enabled in code by the 2026-10-27 change; the
presented-set row above records deployment as pending redeploy. L2 copy describes the code policy,
without asserting that production has already adopted it. Town discussion remains excluded.
**Discussion scoring boundary:** rules score some recorded discussion consequences, but do not
measure the value of information withheld. Do not shorten this to “discussion has no grading rules.”
