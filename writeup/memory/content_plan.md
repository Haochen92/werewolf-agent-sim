# Memory: portfolio content plan

Planning document, 2026-10-27. Not page copy. It maps the memory evidence onto the chapter's Level 2 and
Level 3 pages, following the pattern of [`../game_design_orchestration/content_plan.md`](../game_design_orchestration/content_plan.md)
and the [Level 2 writing prompt](../portfolio-level-2-writing-prompt.md). Every claim a page makes must
appear in the claims boundary, [`../memory_presented_set.md`](../memory_presented_set.md); a page that
needs a claim outside it adds the claim there first, checked against the code and the record.

## Reading structure

- **Level 1, the chapter page** ([`memory.md`](memory.md), done): why memory, the pipeline, and five
  sections, each ending with a link to its Level 2 page.
- **Level 2, five pages,** one per Level 1 section. All five are now drafted for review. The retained
  long Level 1 passages supplied drafting material; each page develops its own opening, mechanism,
  featured story, verification and limits. A reader arriving directly understands the page without
  the chapter.
- **Level 3, three investigations,** each linked beneath the Level 2 subsection it deepens. The parent
  keeps the finding and its essential caveat; the Level 3 page adds method and analysis.

The levels answer different questions. Level 1: why did the system take this shape, and what was
established? Level 2: how does this part work, and why this design? Level 3: what exactly happened in the
investigation behind that choice? A story told at one level is only referred to at the others.

**Historical versus current.** Most investigations ran on the nine-seat game; the system described runs on
the ten-seat game. A page labels each: "an earlier nine-seat investigation" against "the current ten-seat
implementation". An old finding can explain why a design exists; its measured rate does not describe
today's system.

## The pages

| Level 1 section | Level 2 page | Reader's question | Featured story | Level 3 |
|---|---|---|---|---|
| The memory pipeline | **1. Extracting and synthesising lessons** (`extraction_synthesis/`) | How does a finished game become advice another player can use? | Outcome bias: verdicts that followed the winner, and the second review | *When winning made a move look good* |
| Retrieving situational advice with RAG | **2. Matching advice to the current situation** (`matching_situations/`) | How does a player find the lesson for the decision in front of it? | What counts as "the same situation": one schema for query and store, and how often the retrieved lessons actually fit | none |
| Deduplicating the memory store | **3. Removing duplicates** (`store_upkeep/`; retitled 2026-10-28) | How do you remove repetition without destroying distinctions or inventing content? | The best-scoring dedup was switched off: its score never checked the merged text, and one merge reversed its source | *What the merge score did not measure*; *How the dedup judge was built* |
| Curating the lessons | **4. Curating the lessons** (`curating_lessons/`) | How can the store reconsider its own advice? | Comparing with play without memory: the June day-2 lesson (2026-10-28; the July abstention case moved to its L3) | *Baseline matching and paired replay validation*; *The lesson that pruning failed to remove*; *How each decision is graded* |
| Evaluating memory effectiveness | **5. Testing whether memory helps** (`testing_memory/`) | What did the experiments actually establish? | The pre-registered endpoint: a planned test that could not see the effect, the amended comparison, and its result | none here; the detection question goes to the Evaluation chapter if it is not already there |

## Level 2 briefs

Numbers below are the ones each page may use, with their sample and source. A page selects; it does not
have to use them all.

### 1. Extracting and synthesising lessons

**Adds beyond Level 1:** what the extractor is given and why it runs offline; what an observation holds;
the tension of privileged hindsight; the outcome bias and its correction, with evidence; what synthesis
does and the one time it has run on ten seats.

**Mechanism.**
- The input: the game record, every role, the exact night actions and each player's notes, saved when a
  game ends (`Agents/memory/extraction/inputs.py::format_extraction_inputs`). One call per dealt role and
  phase, about 30 a game. Extraction runs offline in Claude Message Batches; each game's first call goes
  direct to write the shared prefix to the cache, the rest read it (`offline.py::extract_cases`; v8
  decisions §11). Measured on Sonnet 5.5 over 21 games: about $0.95 a game, against about $0.45 with the
  cache working; 15% of batch requests wrote the prefix instead of reading it (caching report §4.6).
- An observation: situation (in the cell's schema), approach, outcome, a net verdict, and the decision it
  names. Situations are to be written in what a player could have seen.
- Synthesis (Sonnet 5.5, `store_ops.py::synthesize`) groups a cell's observations into lessons, only where
  at least 4 new observations arrived, and shows existing lessons' measured lift once they have 5 follows.
  Ten-seat: one build (October 2026, $5.31); 694 lessons written, 605 after the lesson dedup; four Sonnet
  readers flagged 37 of 605 (6.1%) as breaking a rule, and those plus 78 reader-found duplicates were left
  out of the published 490. Nothing screens what later synthesis writes; strategic quality is unjudged.

**Featured story: outcome bias.** The rule grade of a move (from the hidden roles) served as a proxy for
whether it was good. Of moves graded good, the extractor called 23% positive when the player's side lost
and 83% when it won (1,472 observations, 40 games). Exhibit: the 2×2 (verdict by grade and side). The
second pass (Haiku 5.5, a batch per run, about $0.006 a game) re-reads each verdict against the move: the
losing side's negative verdicts fell 53% → 27%, the winning side's positives barely moved, 57% → 54% (482
observations, 19 games); it revises 25–29% of verdicts per run. Limits: verdicts only, not the text; the
grade is coarse, so the gap is an upper bound on the bias; whether lessons got better was not measured.
**Level 3 link** under this subsection.

**Sources:** `evidence/extraction/post_game/report.md`; `evidence/extraction/observation_quality/report.md`
and its halo case study; v8 decisions §11, §13; `evidence/store_curation/report.md` (synthesis); v8 report
§1.3, §3.2; `evidence/caching/report.md` §4.6.

**To check before drafting:** the observation field names as the page will show them; whether one real
observation and the lesson synthesised from it can be shown as the exhibit (the store keeps
`source_observations`).

### 2. Matching advice to the current situation

**Adds beyond Level 1:** why one document per role failed; the shape of the store (cells); how a lookup is
built, and why query and storage cannot drift apart; what reaches the prompt; when a seat does not look
up; how well retrieval fits today, and what was tried to improve it.

**Mechanism.**
- The whole-role document: 228 items across four roles, read whole at the start of each game; over ten
  or more rounds the advice grew more sophisticated, but recent games dominated, edge cases contradicted
  each other, and advice was applied where it did not hold (memory log, Era 1 Phase 0).
- Cells by role and decision phase. Before a decision, a short model call describes up to two situations
  in the cell's schema (`situation_agent.py`); facts code can compute (players alive, uses left) overwrite
  what the model wrote. Query and stored lessons are composed into text by the same function from the same
  schema (`Agents/schemas/memory.py::compose_situation_embed`); numbers and categories stay out of the
  embedding, since embeddings blur magnitudes and signs. Search: five candidates per situation, at most
  three kept (`accessors.py`).
- When a seat does not look up: day 1 and its night (nothing has happened that a lesson could match);
  human seats; town discussion turns (v8 decisions §5, §17). A lookup is reused across a seat's discussion
  turns until a new role claim, and within a night: about 60 → 38 lookups in one measured game (v8
  decisions §10). The situation call retries once, then falls back to a generic query.
- Lessons with a good record go first, and one slot is kept for an untried lesson (`filters.py`).

**Featured story: does a retrieved lesson fit?** Seven ten-seat games (2026-10-12), 96 of their 352
lookups read by four Sonnet readers against the rules and true roles: on the 12-game store, 15% of the
lessons shown fit, 29% partly, 56% did not; 36 of 96 lookups had at least one fitting lesson; day turns
fit worst (discussion 7%, vote 13%, night 19%). The readers saw the search match the role, not the stage
of the game, and the similarity score did not track fit. That motivated the stage filter (built, off in
served games). State plainly that the readers were models, and that the store was the earlier 12-game one.

**Tried and set aside (one paragraph):** filtering near-repeats and a model reranker (May, five cases),
more observations per situation (120 decisions), field gating (v6, no gain). The trained reranker belongs
on no page here beyond one clause, if any.

**Sources:** `evidence/extraction/situation_summary/report.md`, `situation_dimensions/report.md`;
`evidence/retrieval/report.md`; v8 report (the 96-lookup read); v8 decisions §10, §17;
`evidence/memory_system/experiment_log.md` (Era 1).

**To check before drafting:** the stage filter's measured precision and coverage (v8 report), and what the
page may claim about it.

### 3. Removing duplicates (retitled 2026-10-28)

**Adds beyond Level 1:** the two dedup paths and when each runs; what a duplicate is (the three-field
rule); why merging was switched off despite scoring best; protecting old entries; what a survivor keeps;
the judges and their limits; growth.

**Mechanism.**
- One-at-a-time, when the extraction job writes its games: an embedding prefilter, then a model judge that
  may discard only when situation, approach and outcome all match (`Agents/prompts/dedup.py`).
- Batch, when the learning tick folds new observations in: clusters, judged keep or discard only
  (triage-only); built, not yet run on ten seats. The lesson dedup after synthesis is built and off until
  tuned (Haiku discarded 7 distinct lessons of 18 discards on the 111-entry set; Sonnet 5.5 made no wrong
  discard).
- Aggressive against conservative: an untuned prompt cut a nine-seat store by 39% and made observation
  retrieval worse (40 scenarios: 2 better, 24 the same, 14 worse); the tuned prompt cut about 17%.
- Old entries are never judged against each other: repeated full passes kept eroding the store (a second
  pass removed another 45 of 432, 10.4%); the caller names the new entries (since 2026-10-26).
- A survivor keeps the discarded entry's counts; a discarded lesson's key is listed on its survivor so its
  follows still count (v8 decisions §14). Provenance: observations carry their game, lessons their source
  observations; a discarded observation's own key and game are not kept.
- Growth: observations age out when not seen again; at most 12 unproven lessons per cell before synthesis
  skips it (18 of 36 published cells are already over); stores grow with no measured plateau.

**Featured story: the merge that was switched off.** The two-pass batch dedup (a cheap model triages, a
stronger one writes merged text) scored best of everything tried on the 111-entry labelled set (99 of
111, 89.2%). Flash-tier models mostly dropped merged fields; Gemini 2.5 Pro kept them, and one of its
merges reversed a source (an Investigator who had found no wolf became one who had). Nothing between the
judge and the store checked merged text, so the active paths only keep or discard. (Corrected 2026-10-28:
the earlier "3 of 9 merges added game context" was a same-model review whose three flags were count totals,
two of them valid sums; see `store_upkeep/merge_fabrication.md`.) **Level 3 link** under this subsection.

**Sources:** `evidence/dedup/report.md` and its sub-logs (`batch_dedup/`, `per_extraction/`,
`embedding_prefilter/`, `store_retrieval_impact/`, `incremental_convergence.md`);
`evidence/store_curation/report.md`; v8 decisions §14.

### 4. Curating the lessons

**Adds beyond Level 1:** why a fixed store cannot improve; what a seat reports; the grading rules and why
they grade the decision; the baseline comparison and the thresholds; pruning, eviction, protection and
the exploration slot; credit apart from paid learning; the abstention case in full; what credit has run
on.

**Mechanism.**
- The fixed store's flaw: the seat sees only the advice, not its record, so a poor lesson keeps being
  followed. (Updated 2026-10-28: the 334-follows and 77%-vs-32% figures are off the page; the second
  compared day-2-heavy follows with an all-day rate.)
- Comparing like with like (2026-10-28): the June villager abstain lesson scored −0.20 against all days and
  −0.02 against day 2, where memory-off villagers abstained 85%; credit now matches the baseline on game day
  (`evidence/credit/day_matched_baseline/`), though on ten seats every day still falls back to all days
  until more memory-off games exist (12 seed games; floor 20 per day). The follow report checked on 100 ten-seat cases (74 of 81
  judgeable matched; `evidence/credit/attribution_check_ten_seat/`). What would show cause: a paired replay
  (not built for ten seats) and the whole-game A/B.
- Adoption: a verdict per shown lesson (follow, override, not relevant); no verdict field on a turn that
  showed no lessons, after Haiku copied "follow" onto 426 such turns.
- Grading: the owner's three questions per role (ideal, neutral, undesirable outcome), as a rule table
  (credit report §2); a decision is graded, not the game's result. A lesson's average grade is compared
  with memory-off decisions by the same role in the same phase, with small samples shrunk toward zero.
  Pruned when it measures harmful with enough follows; evicted when seats keep overriding it; protected
  once it has earned credit (`credit.py`, `store_ops.py::prune_and_evict`).
- Credit (free, no model call) runs apart from learning (paid synthesis) (v8 decisions §14). Publish
  replaces the served counters, recounted from the game records. Games with a human seat grade only their
  AI seats (§15).
- What it has run on: one ten-seat pass over 20 batch games. It shows the mechanism runs, not that it
  improves lessons (the counts are off the page).

**Featured story: the abstention lesson.** Quote the lesson (credit report §6). It was followed 19 times;
the town did worse with memory on 19 of 30 boards in that loop's endpoint; 111 of 117 town abstentions in
the memory games fell on days that ended with nobody voted out. Two gaps: every town abstention graded
neutral (the follows averaged exactly zero), and the missing memory-off comparison taken as zero, so the
score of 0.00 never reached the prune line (−0.15). The fix: an abstention on a day with no lynch is graded
bad; a lesson with no comparison is left unscored. Matched by day (2026-10-28), the missing baseline alone
would not have pruned it (−0.08); the corrected grading does (−0.38). Re-scoring in July pruned the lesson
and kept three lessons chosen in advance as good. Never replayed. A replay of 50 day votes per arm with the fixed
scoring's store recovered the deficit in direction only (not significant). **Level 3 link** under this
subsection.

**Limits:** thresholds are v7's, unvalidated for ten seats; adoption is the seat's own report, checked on a
sample; scores guide retention, not causal effect; the comparison was wrong once (pooled days); no test that
removed lessons made play worse.

**Sources:** `evidence/credit/report.md` (§2, §3, §6, §7); `evidence/store_curation/report.md`;
`evidence/memory_system/v7/report.md`; v8 decisions §12–17; `credit/blindspot_fix/experiment_log.md`.

### 5. Testing whether memory helps

**Adds beyond Level 1:** how a fair comparison was built (paired boards, decision measures graded against
the roles); what each comparison found with its own caveats; why the learning loop needed an amended test;
what the next test needs.

**Mechanism and evidence** (each experiment kept separate):
- Paired boards: the same deal and seed played with and without memory; it fixes the deal, not the model's
  sampling. Decision measures graded against hidden roles, because win rate at 30 boards could only see a
  difference of about 36 points.
- June fixed store (nine-seat, 30 boards, observations only): healer saves 37% → 60% (p = 0.005); town
  eliminations hitting an enemy 47% → 64% (p = 0.028); town win 27% → 43% (p = 0.27). Caveats beside it:
  the raw arm was not pre-registered and none of its 24 tests clears a correction for that many; the
  baseline may have drawn low (town measures improved when only the wolves or the lone killer had memory;
  a memory-off rerun of the same seeds the next day played at 51% villager wins over 59 games).
- A later store (v6): no town effect (+6 points, p = 0.77) in a period when memory-off play had improved.
- The learning loop (v7): two paid runs invalidated (a biased baseline; a configuration slip that ran the
  wrong arm, now caught by a guard). A no-cost simulation showed the planned generation-trend test was
  unlikely to detect the expected change. The amended, pre-registered endpoint: final memory against none
  on 30 boards, town decision score 0.147 lower, worse on 19 (paired t-test p = 0.065; Wilcoxon 0.105);
  reported as committed, "no compounding detected". It compares final memory with none, not one generation
  with the next, and its memory included tells.
- All of these ran at the player model's minimal thinking setting.
- Next: today's store frozen, memory on against memory off, matched deals, run in the same window; it needs
  new labelling and runs.

**Featured story: the pre-registered endpoint.** Why the planned test could not see the effect, why the
amendment was made before any endpoint game, and what reporting it "as committed" means. Links to page 4
for the diagnosis rather than retelling it.

**Sources:** `evidence/memory_system/effectiveness/report.md` (and `paired_ab/`); `evidence/memory_system/v7/report.md`;
`v7/execution_plan/report.md`.

**To check before drafting:** whether the Evaluation chapter already tells the power simulation; if so,
page 5 links to it.

## Level 3 investigations

| Investigation | Parent | Question | Method and analysis it adds |
|---|---|---|---|
| When winning made a move look good | Page 1 | Did the extractor judge moves by who won? | The rule grade as proxy truth; the 2×2 by side; why the gap is an upper bound; the de-halo design (what it may revise) and its before/after |
| What the merge score did not measure (retitled 2026-10-28; written, `store_upkeep/merge_fabrication.md`) | Page 3 | Why switch off the best-scoring dedup? | The two-pass design; the 111-entry set; field dropping across models; the reversed situation and how the same-model review ran; what a safe merge would need |
| The lesson that pruning failed to remove | Page 4 | How did a harmful lesson survive a learning loop? | The ledger of its 19 follows; the two gaps; the fix and the re-scoring; the replay screen; what it cannot show |
| How the dedup judge was built (owner, 2026-10-28) | Page 3 | How was the keep-or-discard judge tuned, and what can the embedding check not do? | The 65 hand-labelled cases and the 232-case recheck; the eleven prompt versions (action before situation, 72% to 84%; no neutral lean); thresholds per embedder and the three months on stale lines; the cluster-size accuracy; the gate's measured cost on lessons; the choice of model. Planned `store_upkeep/dedup_judge.md` |
| How each decision is graded (owner, 2026-10-28) | Page 4 | What counts as a good, neutral or bad move for each of the twelve roles? | The ten-seat rule table for votes, discussion and every night action (`evidence/credit/report.md` §2); the owner's three questions per role; the rows that need a word (the wolf's blend vote); the read exclusion; the tests that pin the table. Planned `curating_lessons/grading_rules.md` |

Kept as supporting evidence, not Level 3: situation-dimension tuning, the reranker training, threshold
sweeps, the replay-screen lever ladder, fine-tuning.

## Drafting rules

- The [Level 2 writing prompt](../portfolio-level-2-writing-prompt.md) and its rubric; the owner's voice
  (name the thing, familiar to specific, frame then parts, a caveat once beside its claim, evidence only
  where it pushed the design).
- Each page opens with the saved opening in its file, revised so it adds to the Level 1 paragraph rather
  than repeating it.
- First person only for work the record ties to the owner; readers and judges that were models are named
  as models.
- Built, run, deployed and validated are separate states (the claims boundary's execution states).

## Order and questions for the owner

**Answered 2026-10-27:** (1) page 1 first, reviewed before the rest; (2) page 5 keeps a short
subsection on detection, with a link to the Evaluation chapter; (3) the owner also read a sample of the
model readers' cases by hand (the number is not recorded): pages say so, without a count.

1. **Drafting order.** Proposed: page 1, reviewed by the owner before the rest, so the first page sets the
   pattern; then pages 2–5.
2. **Page 5's detection question:** link to the Evaluation chapter, or keep a short subsection here?
3. **Ownership of reviews.** Several findings rest on model readers (the 96-lookup read, the rule review,
   the merge judge). Where the owner also read cases by hand, say which, so the pages can say "I".

## Drafting completion and review handoff — 2026-10-27

Pages 2–5 now have full drafts, following the editorial review of page 1. They are not marked approved.

| Page | Main exhibit | Depth link |
|---|---|---|
| Matching advice | 96-lookup review, distinguishing 268 lesson assessments from lookup coverage | Related curation L2; no new L3 |
| Removing duplicates | Operation-label agreement contrasted with merged-text faithfulness | `store_upkeep/merge_fabrication.md`, `store_upkeep/dedup_judge.md` (written 2026-10-28) |
| Curating the lessons | The same 19 follows under original and corrected credit rules | Planned `curating_lessons/abstention_credit.md` |
| Testing whether memory helps | June fixed-store measures and the July paired endpoint, kept separate | Existing Evaluation `fair_comparisons.md#how-much-a-comparison-can-see` |

The drafts distinguish current code policy from deployment: October 27 enables town votes in code;
its production redeploy has not been independently confirmed. Town discussion remains excluded.
The prose does not adopt the older shorthand that discussion cannot be graded at all; some recorded
consequences can be graded, while withheld information remains a limitation.

Other interpretation corrections retained from page 1 review: rule grades are proxies, no quantified
share of the verdict gap is attributed to outcome bias, and no "upper bound" is asserted without
additional assumptions. The detailed briefs above preserve planning history; final page copy and
its source notes carry these narrower interpretations.

Source reports and selected implementation anchors were read; links and headings were checked.
No new games, model evaluations, database reads or statistical analyses were run. Remaining factual
review should confirm source-artifact mappings and deployment state before publication. The L3 pages
are specified but not drafted. Proposed human-curated store entries remain unbuilt and are mentioned
in the curation page, separately from the existing role-prompt review.
