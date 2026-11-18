# U13 working list: code and tests that could be cut before CI

<!-- Writing rules: docs/writing/core_rules.md. -->

A list for my ruling, made on 2026-11-18. It follows the map of the tests
([u13_test_map.md](u13_test_map.md)).

**Outcome, 2026-11-18.** I ruled the same day and the cut was made in the working folder; it is
not committed. Cut: groups A, B, C1, C2, C3, D, E, F, G, H (the scorers only), J and K, the two
nine-seat leak checks, and three experiment scripts that needed the cut code. That is 112 files,
24,072 lines and 208 tests. Kept: C4, I, L, M, the manual labelling tools, the notebooks and the
other experiment scripts. The annotated tag `pre-test-cut-2026-11-18` holds everything removed.
38 of the 39 consolidation tests now test the production file
(`tests/memory/test_store_ops.py`); one of them fails and waits for my ruling. The default set
went from 2,482 tests (2,481 passed, 1 skipped) to 2,312 (2,310 passed, 1 failed, 1 skipped).
The rest of this file is the list as it stood before the cut.

**The rule.** Code stays if it runs in production today (the server, the game engine, the
consolidation tick, the batch runner) or evaluates the current version of the system. Code that
is left over from a past experiment or a past design is deleted together with its tests. Before
the cut, an annotated git tag marks the last commit that holds it, and each affected `evidence/`
folder gets one line naming the tag. The reports and results in `evidence/` stay.

**How the list was made.** A read-only pass by a coding agent built a map of which file imports
which, over every Python file and notebook, and traced what the server, the game, the tick, the
batch runner and each `eval-*` command reach. Nothing was run except test collection. Seven of
its claims were then checked against the code by a second read; those are marked **checked**.
"Inferred" marks a conclusion drawn without a run.

## 1. One thing to do before any deletion

**The production consolidation code has almost no tests of its own.**
`Agents/memory/consolidation/store_ops.py` (the tick's pruning, eviction and synthesis) was copied
from the research version, `evaluation/src/loop/consolidate.py`, when it went live. The same
eight function names are in both files (**checked**). The 39 tests in
`tests/evaluation/test_loop_consolidate.py` test the research copy. The production copy is
touched by a few tests in `tests/memory` only. Deleting the research tests as they are would
remove the only tests of that logic.

So those tests are pointed at the production file first, and only then is the research copy
deleted. Whether the two copies still behave the same was not checked; pointing the tests at
production will show it.

## 2. Groups to rule on

| # | Group | Size | Tests only for it | Recommendation | What I need to decide |
|---|---|---|---|---|---|
| A | The frozen v7 loop, `evaluation/src/loop/` | 19 files, 4,524 lines | 141 | **Cut**, after three small moves (section 3) | Nothing, if I accept that v7 will not be rerun |
| B | Decision-replay screens and checkpoint replay, `evaluation/src/replay/decision_screen/` | 8 files, 2,617 lines | 17 | Cut with A | The evaluation README still lists `eval-checkpoint-replay` as a runner. It replays stores from a v7 loop run. Is that entry obsolete? |
| C1 | Tagger validation | 4 files, about 640 lines | 12 | Cut with A | The README lists `eval-tagger`. The tagger was retired from credit in July and kept "as a watch instrument". Still wanted? |
| C2 | Credit and power instruments (nine-seat, v7) | 7 files, 972 lines | 5 | **Cut** | Nothing |
| C3 | Nine-seat proxy validation | 9 files, 1,156 lines | 11 | **Cut** (inferred nine-seat only) | Nothing |
| C4 | Situation-dimension audit | 3 files, 578 lines | 10 | Not determined | Situation dimensions are still used in hosted retrieval. Does the audit work on ten-seat cases, and do I want it? |
| D | Concluded studies, `evaluation/src/studies/` | 14 files, 3,886 lines | none | **Cut** | Its README mentions "two held re-screens" that import it. Are those dropped? |
| E | Archived evaluation code, `evaluation/src/archive/` | 9 files, 2,157 lines | none | **Cut** | Nothing |
| F | Batch-dedup merge judge | 94 lines | none | Cut with D | Nothing |
| G | Three nine-seat audits (whiff conversion, scheduler access, recall flags) | 1,145 lines | 21 | Cut (inferred: they read nine-seat fields) | The README lists two of them as re-runnable. Confirm they are nine-seat only |
| H | June and July retrieval and reranker scorers, `labeling/label_scorer/` | 5 files, 1,393 lines | none | **Cut** | The manual labelling tools beside them (4 files, 1,206 lines) are not determined: still wanted for making gold labels? |
| I | Cross-encoder fine-tuning, `training/` | 12 files, 787 lines | none | Cut, if fine-tuning is closed | The dedup pipeline's description still calls the trained model a "planned swap-in". Is that plan closed? Cutting it also removes GPU dependencies, which helps the Poetry clean-up |
| J | Leftovers in `Agents/`: a validators file, an augmentation agent, archived extraction prompts | about 500 lines | 1 | Cut once D and K go | Nothing. Two package `__init__` files that the server imports need editing |
| K | Four closed one-off scripts (v5 augmentation, two A/B seed builders) | about 620 lines | none | **Cut** | Nothing |
| L | The v8 store-build and backfill scripts, with the decision-tag code | about 800 lines | 6 | Not determined | These built the lesson store that production reads today. v8 is "closed for now", not closed. Keep until v8 is ruled on? |
| M | The dedup threshold sweep and a command-line wrapper | about 300 lines | none | Not determined | The studies README says thresholds are rerun "only on embedding-model change". Keep for that case? |

Groups marked **Cut** with nothing to decide come to about 13,000 lines and about 157 tests. With
B, C1 and G it is about 17,500 lines and about 207 tests.

**Looks closed but is current, so it stays:** the rerank and filter stages of hosted retrieval;
`Agents/memory/batch_deduplication` (the tick uses it); the served-game extraction and
`scripts/extract_batch.py`; the decision-scoring module (model admission uses it);
`Agents/compute_metrics.py`, which keeps nine-seat metrics on purpose to score old records.

## 3. Moves needed before group A can go

- Two current files import decision scoring through a pass-through file in the loop folder
  (**checked**): `evaluation/src/diagnosis/sampler.py` and
  `evaluation/experiments/discussion_evidence.py`. They are pointed at the production path,
  `Agents.memory.consolidation.decision_scoring`.
- `tests/evaluation/test_loop_merge.py` (3 tests) and `tests/evaluation/test_board_clocks.py`
  (7 tests) test production code through the loop folder. They stay, with their imports pointed
  at the production path, and move to `tests/memory` and `tests/engine`.
- The consolidation tests of section 1 are pointed at `store_ops.py`.

About seven scripts inside `evidence/memory_system/v7/` import the loop and would stop running.
They are record code, and the tag keeps them runnable from the old commit.

## 4. The leak checks

All four were traced to the one place that writes a seat's prompt input.

| Check | Can its field appear in a ten-seat prompt input? | Recommendation |
|---|---|---|
| Investigator results | No. Nothing puts the field there (**checked**) | Remove. The night-record check does this job |
| Vigilante results | No (**checked**) | Remove |
| Healer target | No. The field exists as the Healer's output, but is not a prompt input | Remove, or keep as a guard with a planted-leak test. My call |
| Gated candidates | Yes. It is written by the echo gate and the opening filter | Keep, and add a planted-leak test |

One more finding: the batch runner runs an older, stricter check for held lines, and the newer
check (`check_held_lines_reach_only_their_author`) runs only in one test file. Which of the two
the batch runner should run is to be decided when the checks are edited.

## 5. `evaluation/experiments/` (61 scripts)

These are runners for single studies. By the lifecycle in `CLAUDE.md`, a finished study's runner
is deleted and git keeps it.

| Class | Scripts | Recommendation |
|---|---|---|
| Current: tested, or named as a step of model admission | 4 | Keep |
| Tied to closed v7 or nine-seat records | 3 | Cut |
| Tied to v8 or extraction records | 12 | Rule with group L |
| Ten-seat studies tied to dated records under `evidence/gameplay/` and elsewhere | about 38 | Cut each one whose study is finished. I need to say which studies are finished |
| General ten-seat tools (transcript rendering, cost repricing, the Langfuse viewer trial) | 4 | Not determined |

Some of these scripts import each other, so they are cut in groups, not one by one.

## 6. `notebooks/`

| File | Status | Recommendation |
|---|---|---|
| `fixtures/chunk_catalogue_phase3.jsonl` | The recorded game the tests replay | Keep. It is test data, so it could move under `tests/fixtures/` |
| `fixtures/chunk_catalogue_phase2.jsonl` | Read by two experiment scripts only | Goes when they go |
| `fixtures/chunk_catalogue.jsonl` (nine-seat) | Nothing reads it | Cut |
| `stream_chunk_catalogue.ipynb`, `parallel_interrupt_spike.ipynb`, `batch_analysis.ipynb` | Finished spikes; nothing references them | Cut |
| `hitl_spike_test.ipynb`, `hitl_durability_spike.ipynb` | Not committed; they go with my U5 note | Mine to decide; not part of this cut |

## Not checked

- Whether the research and production copies of the consolidation logic still behave the same.
- Whether groups G and C4 run correctly on ten-seat records.
- Which studies behind the experiment scripts are finished.
- Links from `evidence/` documents and `writeup/` pages to code paths that a cut would break.
- The frontend, the root `archive/` folder, and unused functions inside files that stay.
- `tests/engine`, `tests/server` and `tests/live` were not classified here; the map found no
  closed code behind them apart from the leak checks and one validators test.
