# Evaluation exhibits

A running menu of concrete examples of how this project evaluates itself, for chapter 4 (Evaluation
rigor) and the portfolio site. One entry per closed experiment, added when it closes. The entries
point at the record; they never copy it. The chapter and the site hand-pick from here.

Each entry: the question, the method (code), one concrete example, the number with its caveat, where
the record is, and how it would be shown:

- **content**: prose and numbers written into the page;
- **export**: an interactive piece, fed by a small JSON written by a script in this repo (only the
  displayed fields, stamped with the commit), never hand-copied;
- **link**: a replay on the live site or a folder on GitHub.

---

## From the first Haiku 5.5 game (2026-10-12)

### 1. Replaying the turns that went wrong, instead of playing new games

- **Question:** do three prompt fixes stop the failures the owner saw in a live game?
- **Method:** 18 turns frozen from the game's own LangGraph checkpoints, each re-run 5 times on the
  old and the new prompts; a hand-written expectation per turn, judged by Claude Sonnet 5.5 as one
  batch. `evaluation/experiments/haiku_game_turn_cases.py`, `eval-hallucination-bench`
  (`evaluation/config/hallucination_bench_haiku_game.json`).
- **Example:** an investigator answering "I visited nobody on night 2". Before: *"you say no one
  visited you, but player_9's watch has me and player_8 at your door, so your no-visit story doesn't
  hold."* After: *"player_6, you still haven't said who you went to that night."*
- **Number:** public messages that read a visit the wrong way, 16 of 35 → 5 of 35. A few dollars of
  Claude, no new games.
- **Caveat:** a replay is a regression check on known failures, not a rate; full games come next.
- **Record:** `evidence/game_play_enhancement/discussion_evidence.md` §8.6;
  `evidence/game_play_enhancement/data/haiku_turn_replay/`.
- **Show:** export (a before/after viewer over the samples of two or three hand-picked turns), plus a
  link to the game's replay.

### 2. Checking the suspected cause before fixing it

- **Question:** the town was "too quiet". Was the silence gate blocking real messages?
- **Method:** every pass in the game's event stream carries why it happened (`pass_reason`, `gated`).
- **Number:** 0 of 69 passes were gated; all were the model's own choice. Compared across models on
  the same prompts: Haiku passed 61% of later turns, Luna 5–22%, gemini-3.5-flash 12–34%.
- **Why it matters:** the obvious fix (loosen the gate) would have changed nothing.
- **Record:** `discussion_evidence.md` §8.6 (the table).
- **Show:** content (the table).

### 3. A cheap metric that could not see the problem

- **Question:** do Haiku's replies repeat themselves more than other models'?
- **Method tried first:** a word-overlap count of each line against the speaker's earlier lines that
  day. It found 0–10% on every model.
- **What reading found:** one player gave the same watch result four times in one day, in new words
  each time. Repetition of a point is about meaning, so it needs a reader or a judge.
- **Record:** `discussion_evidence.md` §8.6; the rule it confirms is in §8.5 and the project's
  "semantic eval is not string parsing" practice.
- **Show:** content (two of the repeated lines side by side, and the metric's 0%).

### 4. A fix that failed, and the diagnosis from the agent's own notes

- **Question:** does asking town players to state their vote reasons make them speak?
- **Number:** v1 ("if you already lean toward voting a player out, say why") moved open-floor passes
  from 24 of 25 to 23 of 25. The players' private notes said why: no lean had formed yet (it forms in
  the vote call), and their own earlier note said "stay quiet unless addressed". v2 ("decide now whom
  you would vote for if the vote were held now") got 16 of 25, and one reply surfaced the argument
  the real game never heard: *"player_1 voted player_4 when the table was on player_6."*
- **Cost found:** on a day already carrying a misread, the newly talkative players said the misread
  aloud (5 messages) instead of keeping it in their private reads.
- **Record:** `discussion_evidence.md` §8.6; `evaluation/config/hallucination_bench_haiku_game_vote_v2.json`.
- **Show:** content (v1 vs v2 wording, the pass counts, the quote).

### 5. Checking the judge against a human read

- **Question:** can the LLM judge's counts be trusted?
- **Method:** every visit-direction sample was read by hand before the judge's verdicts came back.
- **Number:** judge 16 → 5 bad messages; hand read about 19 → 6. One judge verdict read was wrong
  (it marked "the Illusionist was revealed as a wolf" as false; the Illusionist is a wolf).
- **Record:** `discussion_evidence.md` §8.6; an earlier case of a judge misled by an over-broad
  expectation is §8.5, learning 4.
- **Show:** content.

### 6. Where an error starts versus where it spreads

- **Question:** does a stated rule stop an error that other players have already made?
- **Method:** the same turns split into origin turns (no misreading yet in the transcript) and cascade
  turns (other players already said it).
- **Number:** on cascade turns, players speaking in the exchange mostly applied the rule (bad messages
  11 of 20 → 3 of 20), but the private reads of players outside it copied the misreading regardless
  (8 of 10 before, 9 of 10 after).
- **Caveat:** only 3 origin turns, too few to measure the rule there on its own.
- **Record:** `discussion_evidence.md` §8.6; the earlier cascade replay (an illusionist rule, f02) in §8.4.
- **Show:** content (a two-row table).

---

## From earlier work

### 7. Retracting the headline result

- **What happened:** the portfolio headline "static memory helps the town, +17pp, p=0.013" welded the
  effect size of one A/B arm onto the p-value of another. Re-verified from the raw records: the raw
  arm was +17pp at p=0.267 (not significant); the reranked arm was +33pp at p=0.013. The robust anchor
  became the raw arm's proxy basket (healer saves +0.23 p=0.005, correct eliminations +0.17 p=0.028,
  mislynch rate −0.17 p=0.036).
- **Record:** `evidence/v7_final/report.md`, `evidence/v7_final/evaluator_review.md` (finding F7),
  `evidence/memory_system/store_progression.md`.
- **Show:** content. Worth leading with: it shows the checking, not just the result.

### 8. A pre-registered negative result, and a scope condition found afterwards

- **What happened:** the v7 question (does memory compound across generations?) was pre-registered
  with a power analysis first (a +0.15 lift undetectable at any affordable size; minimum detectable
  +0.20 at 200 games), run, and closed negative. Later it emerged that every memory game ran with zero
  reasoning tokens; arms were matched, so the comparison stands, but every memory verdict is scoped to
  "a non-reasoning player", and the record says so.
- **Record:** `evidence/execution_plan/power_analysis/mde_table.md`, `evidence/v7_final/report.md`
  (addendum), `evidence/game_play_enhancement/discussion_evidence.md` §6.7.
- **Show:** content.

### 9. An outcome halo in the extractor's verdicts, and the pass that corrects it

- **What happened:** the extractor's per-move verdict tracked who won, not whether the move mattered
  (won: 64% positive, 25% negative; lost: 21% and 65%; n=932). A de-halo pass (Claude Haiku 5.5)
  re-reads each verdict against the game record; over the 12 ten-seat seeding games it revised 146 of
  567 verdicts (26%), mostly to "unclear", a few over-corrected.
- **Record:** `evidence/extraction/selection/netverdict_calibration.py`,
  `evidence/memory_system/v8/experiment_log.md` (2026-10-11).
- **Show:** content, perhaps one verdict before and after (export).

### 10. Screening synthesized advice for wrong rules

- **What happened:** strategy points synthesized from game lessons were read against the rules. On
  flash-lite 9% stated a wrong rule; on Sonnet 5.5 20% (more specific, so more to get wrong); a revised
  prompt brought Sonnet to 11%. The 19 flagged points stay out of the published store.
- **Record:** `evidence/memory_system/v8/experiment_log.md`, `evidence/memory_system/v8/data/seeding/rule_screen*.md`.
- **Show:** content, with one flagged point and the rule it broke.

### 11. Recalibrating thresholds when the embedding model changed

- **What happened:** moving the memory store to Qwen3-Embedding-8B, each similarity threshold was
  remapped by percentile and the dedup prefilter re-set on hand-labelled duplicate pairs (zero errors
  on the labels). The same labels showed the old model's prefilter values had been miscalibrated since
  an earlier model change. Retrieval was checked old against new: 81% of top-5 results shared, and a
  read of five disagreements split evenly.
- **Record:** `evidence/memory_system/v8/experiment_log.md` (embedder migration),
  `evidence/memory_system/v8/data/embedder_migration/`.
- **Show:** content.

### 12. Embedding similarity is not a duplicate judge

- **What happened:** paraphrases of the same advice sit far apart in embedding space and different
  advice can sit close, so similarity only shrinks the candidate set; an LLM classifier makes the
  keep-or-discard call.
- **Record:** `evidence/dedup/`.
- **Show:** content (one pair of each kind with its cosine).

## From the v8 memory gate and the offline re-extraction (2026-10-12 to 10-13)

### 13. Testing a retrieval change on frozen lookups, without playing a game

- **Question:** the seats were shown lessons that did not fit; would filtering by the stage of the game
  help, and does a larger store help?
- **Method:** 96 lookups from seven memory-on games, frozen with the situation each seat wrote, searched
  again offline under each variant (no filter, filter after the cut to three, filter before it); every
  lesson read for fit by Sonnet subagents given the games' true roles. `evaluation/experiments/
  v8_gate_lookups.py`, `v8_stage_filter_replay.py`, `v8_reextract_reads.py`.
- **Example:** a Chanteuse on day 2 with nine alive and her partner alive, shown three lessons that all
  need a dead partner or three players left; the stored board of each lesson already said so.
- **Number:** fit 15% → 25% with the filter on the 12-game store; on the 40-game store, lookups served a
  fitting lesson 30 → 52 of 96. Embeddings only, a few cents a variant.
- **Caveat:** fit stops near a quarter: the remaining misfits hinge on events (being named at a door, a
  rival claim) that the stage fields do not record. Different readers across the two reads.
- **Record:** `evidence/memory_system/v8/experiment_log.md` (the gate, parts one and two; the 40-game
  read); `evidence/memory_system/v8/data/gate/`, `data/reextract/fit/`.
- **Show:** content (the variant table and the Chanteuse example), or export (one lookup with its lesson
  sets and verdicts under each variant).

### 14. Checking a model-written field against the engine's own count

- **Question:** the extractor writes how many uses of a limited ability a player had left. Is it right?
- **Method:** each game's nights replayed through the engine's own spending rule (`resolution._spent`)
  to get the true count, matched to each extracted observation.
- **Number:** 84% exact; 15% gave the count after the night's action instead of before. Rewording the
  field to "before this decision" raised exact matches to 89%, but some-left against none-left, the part
  the filter uses, stayed wrong in about 4–6%, so the fix is structural: compute the count from the
  record, as the seat's own already is.
- **Record:** `experiment_log.md` (the gate part two; the Flash re-extraction).
- **Show:** content.

### 15. A cost estimate that missed, and the probe that found why

- **Question:** what does batched Claude extraction cost?
- **What happened:** a two-game check quoted at under $0.50 cost $2.69: no call read the prompt cache. A
  three-call probe ($0.005) showed the enforced output schema is part of Claude's cache key, so a
  fan-out with a schema per call never shares a prefix; the fix writes the schema as text after the
  cached part. The same check found the cost summary priced 1-hour cache writes as plain input. A later
  run still cost twice its estimate, through a retry path that rewrote the cache; that is fixed too.
- **Number:** per game, $1.27 as first run against about $0.45 with the cache read.
- **Record:** `experiment_log.md` (the Claude batch check; the 21-game Sonnet run);
  `Agents/memory/claude_structured.py`.
- **Show:** content (the probe's three usage lines).

### 16. A dedup gate built on model-written labels

- **Question:** the point dedup ran, yet readers found 65 duplicate groups (78 points) in 605. Why?
- **Finding:** the dedup splits points by labels the synthesis model writes (direction, honesty) so that
  rival moves never merge; the labels are noisy, and 37 of the 65 groups crossed them, so those points
  were never compared. Complements exhibit 12: the candidate step, not only the judge, can hide
  duplicates.
- **Record:** `experiment_log.md` (the 40-game store read; the publish note);
  `evidence/memory_system/v8/data/reextract/points/`.
- **Show:** content (one duplicate pair with the two labels that kept it apart).
