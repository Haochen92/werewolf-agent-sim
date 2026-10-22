# Write-up map

The working index for the portfolio write-up of the agent side (server and frontend are mapped
separately). The method is bottom-up: walk the `evidence/` tree folder by folder, collect the
building blocks each folder offers, and only when every folder is walked decide how the blocks group
into sections and what the headings are. No section structure is fixed before then.

Rules the walk follows (ruled 2026-10-13 and 2026-10-14):

- The write-up is the page content, drafted here and ported later. It is written for a hiring reader
  who meets the project cold. The evidence folder holds the details; the write-up links to them.
- Organisation is decided at the end, from the blocks. The earlier top-down cut (sections by artifact,
  skills as hub tags) is one candidate to test against the collected blocks, not the plan.
- Evidence stays frozen. A folder that is unreadable gets a report-style pass (synthesis layer only,
  journey logs are not laundered) before it is mined, so the write-up distils from a correct record.
  A folder is also re-verified against today's code before mining; a stale report is corrected first.
- The owner walks the folders in alphabetical order of `evidence/` (ruled 2026-10-22); the tables
  below keep the README grouping. A row walked by the AI without the owner's read says so in its
  notes and is revisited when the owner reaches it.

## The model (refined as we go; agreed after `agent_boundaries/`, 2026-10-14)

A **topic** is a unit of the page. Most topics are components (the information boundary, the
scheduler, the memory store). A skill becomes a topic too when it is broad enough and no single
component owns it: cost optimisation is the first (caching, batch inference, model choice by task and
cost attribution come from four folders), and a skill tag that keeps collecting blocks across topics is
promoted the same way (agreed 2026-10-14). Every topic is told through the same five **segments**, so a
segment is a slot a block fills, never a label:

| Segment | What goes in it |
|---|---|
| Problem | Why the thing had to exist, in the game's own terms. One paragraph. |
| Design | What was built and the reasoning: the principle, the alternatives, the trade-off accepted. |
| Verification | How we know it works, and how far that knowledge reaches (what the check is blind to). |
| Case study | One concrete episode that proved the design real: a regression, a before-and-after, a number. The exhibit lives here. |
| Gaps | What is still open, stated with its consequence. Every topic has one; it is not a finding. |

A **building block** is one thing the page could say or show, filed under a topic and a segment. It
carries four fields:

- **Segment**: which of the five slots it fills.
- **Skill tags**: the specific agentic-AI skill the block demonstrates, in the field's own term
  (context isolation, invariant checks, observability, prompt caching, retrieval, ...). Tags are
  deliberately narrow: "design principle", "debugging", "honest gaps" are not tags, since every topic
  has them; they are segments. A skill that collects enough blocks across topics may earn its own
  section at the end; otherwise it stays inside the topics it appeared in. The tags are also the
  hub's capability tags.
- **Exhibit form**, as in [`eval_exhibits.md`](eval_exhibits.md): **content** (prose, a number, a
  table on the page), **export** (an interactive piece fed by script-generated JSON), **link** (a
  replay on the live site or a folder or file on GitHub). A real example is always lifted from the
  record, never invented.
- **Source**: the evidence path (and the code path when the reader may want to verify).

Rules of thumb that came out of the first folder:
- A table of internals (eleven check names) means nothing to a stranger; a paragraph with one real
  line from the log and a link to the code does more. Tables are for things a reader compares.
- A number goes on the page with its caveat in the same sentence ("109 flags, none rendered").
- When a block's real reason lives in another topic (the public-by-design fields exist to cut
  hallucination), it is filed there, and the first topic keeps a one-line cross-reference. Parked
  cross-references are listed below so they are not lost.
- Terms: the owner tags in plain words; the ledger records the field's term next to it the first
  time (information boundary = context isolation; leak test = invariant checks over a post-hoc
  transcript audit; the capture point = observability; a prompt segment included only when the
  seat can act on it = conditional prompt composition, a sibling of isolation under context
  engineering: isolation is about what the agent may not know, composition about what it cannot use;
  the call that produces something never grades it = generator-verifier separation; a judge that
  counts without seeing the labels = blind annotation; a post-generation check with code deciding =
  output guardrail).

## Building blocks

The output of the walk. One entry per block, numbered in the order found, grouped by topic.

### Topic: the information boundary (`agent_boundaries/`)

| # | Segment | Block (one line) | Number and caveat | Skill tags | Exhibit (form) | Source |
|---|---|---|---|---|---|---|
| 1 | Problem | A social-deduction game is void, not degraded, if a role learns what it shouldn't, so each agent's prompt is built with only what its role may know | — | context isolation | content | `agent_boundaries/report.md` §1 |
| 2 | Design | Four layers on the prompt path (state schema, payload, prompt-input formatter, template); only payload construction enforces, the rest forward or filter by accident; so: enforce at construction, verify at the data layer | — | context isolation | the four-layer table, or a four-arrow figure with "enforced?" under each arrow (content) | `agent_boundaries/report.md` §2; code `Agents/nodes/day/flow.py::_private_fields` |
| 3 | Verification | Every model call's prompt input is captured; invariant checks audit the capture after each batch game; unit tests pin the builders field by field | 11 checks, 9 live on batch games and, nightly, on served games once deployed; blind to free-text memory and to two un-logged call sites | invariant checks, observability | paragraph with one real `LEAK:` line and the clean post-fix tail, link to `tests/leak_test.py` (content + link) | `agent_boundaries/report.md` §3 |
| 4 | Case study | A convenience superset payload put private fields into every role's prompt input; the first wired run flagged it; role-gating fixed it; root cause was a documented misread of the framework's Send semantics | 109 flags to 0; none rendered, so no game result was tainted | context isolation | before: `LEAK: player_2 (healer) received surviving_wolves: player_4, player_5`; after: empty block between the two banners, `EXIT: 0` (content; link to the folder) | `agent_boundaries/experiment_log.md` §2; logs colocated |
| 5 | Gaps | Memory retrieval is isolated by construction (role-keyed namespaces) but not asserted; served games audited nightly from 2026-10-14 but a game resumed after a restart is only partly captured | — | — | content | `agent_boundaries/report.md` §5 |
| 47 | Design | The deduction engine (its own topic below) reads one typed view built from the seat's own payload and nothing else, so a large injected feature landed inside the boundary without a second enforcement point; a metamorphic test renders a seat's lines under several hidden states compatible with its view and requires identical text | — | context isolation, metamorphic testing | one paragraph with the `SeatView` docstring's first line (content) | `reasoning_failures/report.md` §1, §3; code `Agents/deduction/seat_view.py` |

### Topic: cost optimisation (skill topic; from `caching/`, with `model_selection/`, `extraction/tell_extraction/` and the v8 offline ruling still to walk)

| # | Segment | Block (one line) | Number and caveat | Skill tags | Exhibit (form) | Source |
|---|---|---|---|---|---|---|
| 6 | Problem | A seat reads the whole transcript every turn, and extraction re-reads a finished game once per role and phase, so most input is repeated; caching is paying less for the repeat | — | prompt caching | content | `caching/report.md` §1 |
| 7 | Design | Caching is a per-provider contract, not a flag: automatic on DeepSeek, boundary-based on OpenAI, marked on Claude, a cache object on Gemini; writes cost 1.25x; an enforced schema is part of the cache key; a cache must be written before concurrent calls can read it | — | prompt caching | the provider table (content) | `caching/report.md` §2, §3.3 to §3.6 |
| 8 | Design | The shared-prefix layout: rules, then the public record, then everything that differs per seat, so votes, night actions and lookups share the day's transcript across seats | Luna about 28% less per call, no detected quality change; Haiku no per-call saving but it stopped passing nearly every free turn | prompt caching | before and after render with the cache boundary marked (content; generate the old render from tag `prompt-layout-baseline`) | `caching/experiment_log.md` §13 to §15; `Agents/prompts/layout.py` |
| 9 | Verification | Vertex's automatic cache was probed before anything was built and found dead on this pipeline's prompts in two probes four months apart; the layout change was checked in paired games and on the hallucination bench before going live | 0 cached tokens up to 8,192; the Oct 4 table is automatic caching only, Claude's row is a marked-prefix result | paired A/B, regression benchmark | content | `caching/report.md` §4.1 to §4.4 |
| 10 | Case study | A high cached share is not a proportional saving: output and reasoning dominate the bill, and an estimate that ignores cache writes and retries misses by multiples. Lead the topic with this | one extraction run $10.33 with $8.97 output; the Claude extraction estimate under $0.50 billed $2.69, then $19.99 against about $9.50 | cost attribution | two-column table, cached input share beside total cost change, for live play and for extraction (content) | `caching/report.md` §4.1, §4.6, §5 |
| 11 | Design | Offline and batch: extraction leaves the game, and Claude runs it as one batch after a direct call has written the prefix; schemas go into the prompt text so the batch shares one cache | batch is half price; synthesis $4.02 direct versus $1.51 batched, prompts differed so order of saving only | batch inference | content | `caching/report.md` §3.6; the v8 offline ruling |
| 12 | Gaps | Game quality under the layout measured only for factual errors; the bench lacks vote and night cases; the June extraction reorder never done | — | — | content | `caching/experiment_log.md` §16 |

### Topic: memory extraction (component; provisional, opened by the halo case study in `extraction/selection/`; the `extraction/` folders still to walk)

| # | Segment | Block (one line) | Number and caveat | Skill tags | Exhibit (form) | Source |
|---|---|---|---|---|---|---|
| 13 | Case study | The extraction judge grades the result, not the decision: with the outcome in hand it bills another faction's action to a player and back-propagates a loss onto the player's best move; shown on the owner's own seat, so intent is attested | N = 1 game, 2 entries, a mechanism exhibit; at scale the verdict follows the side winning +0.80 against the decision's grade +0.40 on 1,472 observations | LLM-as-judge, outcome bias | the two entries verbatim with the conceding clause and the verdict side by side (content) | `extraction/selection/outcome_halo_case_study.md`; `memory_system/v8/decisions.md` §13 |
| 14 | Design | Two answers, deliberately different: credit never reads the judge (deterministic grades from vote endpoints and read accuracy); the store keeps both the verdict and the grade behind a config flag, with a second-model de-halo pass on the verdict | de-halo removes about a third of the halo, losing side only (+0.80 to +0.53 on side-won, +0.40 to +0.36 on the grade); a different model that still sees the outcome is not independence; the grade variant of synthesis is designed, not run | LLM-as-judge, deterministic grading | content | `cross_project_synthesis/separating_generation_from_checking.md` §1; `memory_system/v8/decisions.md` §13; `credit/report.md` |

### Topic: memory consolidation, keeping the store clean (component; provisional, opened by `dedup/batch_dedup/`; the other dedup sub-logs and `store_curation/` still to walk)

Presentation rule agreed 2026-10-14: everything here is presentable, including the merge path the
deployed game no longer calls, provided each block states its state: **live**, **built and validated,
switched off**, or **superseded**. Never a fused claim that lets a measured result read as the deployed
behaviour.

| # | Segment | Block (one line) | Number and caveat | Skill tags | Exhibit (form) | Source |
|---|---|---|---|---|---|---|
| 17 | Problem | Online dedup is a greedy insertion-time check against top-N neighbours that never re-examines a kept pair and cannot merge, so near-duplicates accumulate; the batch pass re-clusters the whole store | — | memory consolidation | content | `dedup/batch_dedup/experiment_log.md` "Why a second pass" |
| 18 | Design | Which entries are compared together decides what the judge ever sees. Union-find and hierarchical clustering are transitive and collapse a namespace into one blob at any threshold that catches real duplicates; the greedy bounded method caps each cluster at 15 and runs inside a deterministic gate partition (live) | accuracy 26–74% above 15 entries vs 80–100% below; conservative 17% dedup beat aggressive 39% on retrieval at n=39 | near-duplicate clustering, embedding prefilter | the three-method table, recall against blast radius (content) | same log, "Forming the clusters"; `dedup/README.md` retrieval table |
| 19 | Design | Model cascade: Flash-Lite triages keep or discard, Pro sees only the merge candidates; flash-tier models drop two of three fields when rewriting a merge, a capacity limit no prompt fixed (built and validated, switched off: the deployed fold runs triage-only) | 89.2% on the golden set; 69% fewer Pro calls | model cascading (cross-ref from the cost topic) | the model-by-accuracy table with the two-pass row (content) | same log, "Two-pass pipeline", "Resolved recommendation" |
| 20 | Design | The prompt work that moved the number: indexed references instead of UUIDs (no truncation, fewer tokens), a before-merging checklist, neutral calibration | over-merge errors 12 to 2 on Pro from the checklist | rubric prompting, indexed references | content | same log, "Prompt Versions", "Key findings" |
| 21 | Case study | The idempotency test: a second run on an already-deduped store removed another 10.4%, part real misses, part merges of retrieval-distinct entries; diagnosed as non-convergence rather than non-idempotency and closed by the freeze-old apply guard (live) | 45 of 432 items on the second pass; the guard is live, the created_at carry-through is not | idempotent store operations | the before-and-after table, plus one lifted merge of two distinct situations (content) | same log, "Idempotency Test"; `dedup/incremental_convergence.md` |
| 22 | Verification | A 111-key golden set with accuracy by cluster size made every choice measurable, and the retrieval study checked that the deduped store retrieved better | n=39 cases; the Pro judge fabricates about a third of merges, caught by an eval-side judge only | golden-set evaluation | content | same log, "Dataset", "Merge Rewrite Quality"; `dedup/store_retrieval_impact/` |
| 23 | Gaps | Merge fabrication is unguarded in the apply path but the merge path is off; no non-Gemini model has been run on the golden set; the loop's threshold now comes from a per-embedding-model table | — | — | content | same log, addendum 2026-10-14; `dedup/report.md` gap table |
| 34 | Gaps | Lean discard or lean keep is deliberately unresolved: an over-discarded rare lesson is gone for good, an over-kept common one is recoverable bloat, and the right lean depends on downstream retrieval, not the prompt; the live prompt sits near neutral with targeted anti-over-discard notes | — | — | content | `dedup/per_extraction/experiment_log.md` ④ |
| 35 | Verification | The retrieval study behind the conservative choice: a 17% dedup raised efficiency and unique lessons with relevance near the raw store; a 39% dedup lost relevance with no efficiency gain; retrieval-time filtering did not stack on the clean store and ships off by default | n=39 scenarios, judge-scored, nine-seat v4 store; direction, not today's numbers; the reranker was not in the comparison | LLM-as-judge | the three-store table (content) | `dedup/store_retrieval_impact/experiment_log.md` phase 2 |
| 38 | Gaps | Strategy points were a coverage problem, not a duplication problem, on a 198-point store; the store now holds about 500 and the demo serves them alone with filtering and reranking off; unmeasured since May | — | — | content | same log, addendum 2026-10-14 |
| 24 | Design | A deterministic tier before any model: similarity on the discriminating field, auto-discard only at near-identical text because a discard is irreversible, auto-keep below a low line, the model for the middle, fail-open | about 23% of decisions without a model call on Gemini in May; on the current embedder the live observation path decides 1.7% of the cross-game cases; live for observations in store-building, dormant for strategy points | embedding triage (cost cross-ref; the calibration, the ceiling and the threshold gaps are blocks 25–27 under the embeddings topic) | content | `dedup/embedding_prefilter/experiment_log.md` "Design", addendum 2026-10-14 |

### Topic: embeddings, what similarity can and cannot decide (skill topic, promoted 2026-10-14; cases of how embeddings were used, each with its limit shown, presentable whether or not the path is deployed)

| # | Segment | Block (one line) | Number and caveat | Skill tags | Exhibit (form) | Source |
|---|---|---|---|---|---|---|
| 25 | Verification | A 65-case golden set calibrated the lines; a 232-case cross-game set dissolved a small-sample artifact that would have shipped too aggressive a discard line; three attempts to raise coverage all made it worse on the real distribution | the golden set alone said discard at 0.90, the broad set 0.93; the May observation counts are near-zero-error, not zero (one keep at 0.962, one duplicate at 0.925 in the colocated cache) | golden-set construction, ablation | the four-condition table (content) | same log, "Calibrate", "Validate", "Try to beat the ceiling", addendum |
| 26 | Case study | Embeddings capture topic, not stance: two opposite pieces of advice on the same topic embed 95% alike, so the 15 to 30% ceiling is a property of the space, shown on two embedders five months apart | 6 of the 8 highest-similarity keeps were genuine; case 155 at 0.913 on Gemini, 0.881 on Qwen, inside the zone on both | embedding limits (candidate topic) | case 155 verbatim, plus the strip plot of the 232 cases on both embedders (export: `data/cross_game_sims_by_embedder.json`; PNG for the record) | same log, "The ceiling, explained"; `evaluation/experiments/prefilter_similarity_exhibit.py` |
| 27 | Gaps | Thresholds re-derived on 65 old cases only: on the 232 the new strategy-point discard line would discard the log's own exemplar; the planned re-validation from live traces never run; the Gemini thresholds drifted unnoticed for three months after a model swap, a threshold being meaningful only for the model it was set on | 2 labelled keeps at or above 0.88 on Qwen | — | content | same log, addendum 2026-10-14 |

| 39 | Design | "Similar" became an explicit predicate over structured fields, not a cosine threshold: on the composed prose situations, hierarchical clustering at the default threshold put a whole namespace in one blob chopped by the size cap, a threshold sweep had no stable elbow, and the cause was shared scaffolding text inflating every similarity; the structured fields that were well distributed became the deterministic gate (built the next day) | 916 of 919 observations landed in max-size clusters at 0.70; usable clusters only in a 0.88 to 0.90 window before fragmenting | embedding limits, deterministic gating (consolidation cross-ref) | content; one lifted pair of composed situations showing the repeated labels | `dedup/dedup_clustering_and_sp_extraction_plan.md` "Why this is needed now"; `dedup/experiment_log.md` §9 |

| 46 | Verification | The first similarity line for filtering retrieved items (0.85) over-collapsed, and the line was raised to 0.92; it is now kept per embedding model | five of ten cases cut to one observation, two from 15 and 16 candidates; the report's opposing-pair example is not shown in its own run (that pair survived 0.85), so it is a hypothesis, not an exhibit | embedding limits | content (no lifted pair) | `retrieval/filtering/report.md` "Threshold tuning", addendum 2026-10-14; `01_baseline_threshold085_pro.md` |

Instances still to file here: the retrieval reranker (a cross-encoder over cosine; `retrieval/reranking/`,
`fine_tuning/cross_encoder/`), the per-model threshold table and the July drift
(`memory_system/v8/experiment_log.md`, embedder entry).

### Topic: retrieval (component; provisional, opened by one block from `dedup/store_retrieval_impact/`; the `retrieval/` folders still to walk)

| # | Segment | Block (one line) | Number and caveat | Skill tags | Exhibit (form) | Source |
|---|---|---|---|---|---|---|
| 36 | Design | Retrieval-time filtering (similarity gate, MMR, per-situation cap) does not stack on a clean store: the wider net pulls in situation-mismatched items and the gate over-removes, so it ships off by default as a safety net between batch runs | relevance 4.60 to 4.00 with filtering on the clean store, n=5 only; the reranker was never in this comparison | retrieval filtering | content | `dedup/store_retrieval_impact/experiment_log.md` "Filtering on a Clean Store" |
| 40 | Problem | Top-k by similarity returns variations on one lesson, and right-topic advice for the wrong moment: 12 observations for one investigator turn, mid-game advice for a day-1 information void. The fault is redundancy and timing, not topic | — | retrieval | content | `retrieval/filtering/report.md` "The Problem"; `retrieval/reranking/report.md` "The Problem" |
| 41 | Design | One fix per failure mode: observations fail on narrative duplication (fixed upstream by store dedup), strategy points on situation mismatch (an LLM reranker that reads the situation, not the topic), volume on a fixed cap. Stacking fixes for one problem over-corrects: filter plus rerank scored below rerank alone (built and validated, switched off: both default off, the served demo reranks nothing) | strategy-point efficiency 1.80 to 3.60, redundancy 72% to 40% with rerank alone; filter plus rerank 2.20; n=5 scenarios, nine-seat store, direction only | reranking, retrieval filtering | the five-configuration strategy-point table (content) | `retrieval/reranking/report.md` "Evaluation", addendum 2026-10-14 |
| 42 | Case study | Coverage, not retrieval, is the ceiling: the healer's day-vote case scored relevance 1 under every configuration, filtered, reranked, both, clean store or dirty, because no strategy point for an early, information-starved vote existed. The judge's zero unique lessons pointed at the missing content | n=1 case across 5 configurations; joins block 38 (strategy points a coverage problem) | retrieval, coverage analysis | that one case's row across the configurations, with the judge's reasoning line (content) | `retrieval/filtering/report.md` "Results"; `retrieval/reranking/report.md` case-level highlights |
| 43 | Design | More retrieved context has a saturation point for a small model: 3, 5 and 7 observations per situation, judged on the decisions they fed | action quality 4.33, 4.40, 4.26 at n=120; no significance test; one judge (2.5 Flash) | context budget | content | `retrieval/capacity_limits/report.md` |
| 44 | Gaps | The cap of 5 chosen above never reached the prompt: it was made as the fetch width, and the per-situation keep of 3 still runs after it, so every observation-on campaign since June ran at about the cap-3 condition. Found by re-verifying the report against the code. Also: the trained cross-encoder (a free replacement for the LLM reranker call) was never wired in | the measured gain was +0.07; the served game retrieves no observations | — | content | `retrieval/capacity_limits/report.md` addendum 2026-10-14; `Agents/memory/retrieval/pipeline.py` |

### Topic: the instruments (component; provisional, opened by one block; `evaluation/`, `metrics/`, `tracing/` still to walk)

| # | Segment | Block (one line) | Number and caveat | Skill tags | Exhibit (form) | Source |
|---|---|---|---|---|---|---|
| 45 | Design | A judge whose scores contradict each other is fixed by structure, not wording: the retrieval judge first groups the items by the lesson they teach, then derives every score from those groups, and every scale points the same way (redundancy flipped to efficiency). Before that, two metrics used different standards and one set scored maximum redundancy and maximum novelty at once; the cheapest judge also failed to discriminate and broke its schema on about 30% of calls | relevance 5, redundancy 5, unique ideas 5 on one 9-item set; Flash-Lite 30% malformed to 2.5 Flash 0%; n=5 per run | LLM-as-judge, judge design | the contradictory score line beside the "STEP 1 — CLUSTER BY LESSON" excerpt (content) | `retrieval/filtering/report.md` "Building the evaluation"; `03_lambda08_flash_nocap.md` l.221; `evaluation/src/judges/prompts/retrieval.py` |
| 37 | Case study | n=5 said dedup helped everything; n=39 showed the aggressive store had lost relevance, and the log keeps the first verdict in place and falsifies it below. Every claim carries its N as well as its epoch | observation relevance −0.28 at n=39, 2 wins 24 ties 14 losses | replication, sample size | the two phases side by side (content) | same log, phases 1 and 2 |
| 63 | Problem | The question was whether a memory that rewrites its own lessons gets better generation after generation; the planned test averaged the town's decision score per generation and looked for an upward trend, but one game's score wobbles widely with no memory at all (15 memory-off games ranged −0.15 to +0.93) | typical game-to-game spread 0.33 around a +0.33 average | power analysis | the 15 real scores as a line of numbers (content) | `execution_plan/report.md` §1 |
| 64 | Verification | Test the test before paying for it: pretend runs built from real memory-off games, a known improvement added on purpose (+0.03 per generation to +0.15), the planned trend test run 2,000 times, and the hit rate counted; checked by a textbook formula and by planting nothing (false alarms 2–3%) | caught 1 time in 9 at the affordable 24 games, about half the time at 200; a +0.60 was caught 85% of the time, so the test works, just not at the expected size; the simulation treats generations as independent, which likely flatters the test; cost $0 | power analysis, Monte Carlo simulation, bootstrap resampling | the planting table (+0.00 … +0.15) and the two-row result table (content) | `execution_plan/report.md` §2; code `evaluation/src/instrument_validation/power/mde_simulation.py` |
| 65 | Design | Instead of buying more games, the trend test was dropped and the question re-asked as a paired comparison: the same boards played with the finished memory and without, so both copies share the deal's luck; the cost accepted is losing when and how fast any change happened | the new design's own power was never simulated; rests on the argument that a finished memory carries its whole effect at once | experimental design, paired A/B | content | `execution_plan/report.md` §3 |
| 66 | Design | Pre-registration: the one main measure, the size, no stopping on results, and how a null or negative would be read were signed before any data, so the later negative-leaning result counts as a result; one change after signing (three conditions to two, before any test game) is disclosed with its reasons and what it changed | signed 2026-07-16; amended 2026-07-20 after the learning games, before any test game | pre-registration | content | `execution_plan/report.md` §4; `batch_results/v7_endpoint_ab/PREREG_AMENDMENT.md` |
| 67 | Case study | The signed run: memory-on town worse on 19 of 30 paired boards, main measure −0.147, p ≈ .06, reported as committed (no compounding detected, leaning toward harm); the cause traced to cautious lessons the scoring could not penalise (credit blocks 61) | not significant; players ran with zero reasoning tokens; links to the credit case study rather than retelling it | pre-registration, honest negative | content | `execution_plan/report.md` §5 |

### Topic: golden-set construction (skill topic, provisional; the per-extraction log is the fullest worked example, with batch dedup, the tell detector, the hallucination bench and the halo study still to add)

| # | Segment | Block (one line) | Number and caveat | Skill tags | Exhibit (form) | Source |
|---|---|---|---|---|---|---|
| 28 | Design | A golden set is built, not collected: hard cases sampled from the real store, labelled under a stated decision basis, an error-analysis file of the cases the baseline got wrong, and the labels audited when every model fails the same cases, since cross-model agreement against a label is a label smell | 4 of 6 merge labels were wrong; two revision rounds changed 14 of 65 labels, each tightening the ground truth | golden-set construction | one tricky case lifted: "2 saves" vs "3 saves", old label merge, new label discard (content) | `dedup/per_extraction/experiment_log.md` ②; `tricky_cases.md` |
| 29 | Design | A subjective label needs an operational rule: "same situation" became "would a query for A retrieve B", which settled most labelling disputes and later became the deterministic gate for the structured half of the call | — | golden-set construction, labelling rubric | content | same log, "What counts as a duplicate", ④ |

### Topic: prompt engineering (skill topic, provisional; the per-extraction log's four phases, with batch dedup's block 20 and the seat-prompt work still to add)

| # | Segment | Block (one line) | Number and caveat | Skill tags | Exhibit (form) | Source |
|---|---|---|---|---|---|---|
| 30 | Design | Directional calibration is a ratchet with no neutral position: "when in doubt discard" kills keeps, its absence floods merges; a targeted note about one specific difference fixes the failure mode without tilting the distribution | 3.5-flash 75.4% to 80.0% from v7 to v8, D recall 60% to 77% with K recall held | calibration bias | the cascade line beside the targeted note, two lines each, lifted from `prompt_history/` (content) | same log, ③ phases 2–3 |
| 31 | Design | Forcing explicit consideration of a rare option raises its false-positive rate: routing every case through a merge gate multiplied merge predictions despite "merge is rarest" | about 10x more merge predictions; v4 fell to 40% with 25 false merges | calibration bias, decision structure | content | same log, ③ phase 1 |
| 32 | Design | Presentation order beats instruction volume for a weak model: putting the action field before the situation field did what three added paragraphs and an extra output field could not | strategy-point accuracy 72% to 84% on Flash-Lite; 3.5-flash unmoved at 88% | field ordering | the before-and-after field order as a skeleton of headings (content) | same log, ③ phase 4 |
| 33 | Design | Shrink the action space to what the model does reliably: merge was removed from the online decision because wrong merges corrupted live entries, and both models improved once it was gone; the same move as "merge is Pro-only" in batch and the reshaped tell task | Flash-Lite 73.8% to 80.0%, 3.5-flash to 83.1% on the same backend; then 83.1% for Flash-Lite with the three-field rule | action-space design (lessons candidate) | one line of schema before and after (content) | same log, ③ endgame |

### Topic: deduction, what a seat is handed before it reasons (component; from `reasoning_failures/`, walked 2026-10-21)

| # | Segment | Block (one line) | Number and caveat | Skill tags | Exhibit (form) | Source |
|---|---|---|---|---|---|---|
| 48 | Problem | The Haiku seats absorb facts and do not take the first inferential step: a roleblocked healer, told by two players that player_7 had visited it, wrote every premise into its notes three times and never named player_7, when only the Chanteuse can roleblock. Four levers were tried first: a higher thinking budget moved votes but nothing else at 2.7x the output; a stronger summariser was not better; a rewritten note prompt was worse; a majority of three samples was no better than one because the errors repeat | budget: 98/160 right against 65/160, better on 12 of 16 cases, p = 0.003; Sonnet summary 18/30 flawed in each arm; majority 39% against 41%; all on frozen turns, n = 10 per case | deterministic injection (the field: neuro-symbolic grounding, code-computed context) | the healer's note beside the two premises (content) | `reasoning_failures/report.md` §1, §4; `experiment_log.md` §2–§4 |
| 49 | Design | Facts a seat would otherwise infer from prose sit on its payload as data (the dead roster with revealed roles, the cast census, the morning announcement, read-out wills), so no seat has to parse them; the engine's lines are the next rung on the same ladder. Filed here from the boundary topic's parked list | — | structured context | content | `agent_boundaries/report.md` §1; `reasoning_failures/report.md` §2 (`public/` reads mornings and wills as data) |
| 50 | Design | Every injected line carries its own grade in its wording (certain; follows if named claims are true; a complete list of explanations) and the one prohibition is never to state as absolute what some legal game makes false. Why absolute: injected text is taken up almost every time, so a wrong line is a deterministic falsehood in every game where it fires, not an occasional error | 10 of 10 replays wrote the injected fact into their notes | deterministic injection, calibrated output | the three-grade table with one real line each (content) | `reasoning_failures/report.md` §1; `deduction_catalogue.md` §0 |
| 51 | Design | Eight levels, one folder each, from the seat's own night result through public events, candidate roles, joins with claims, conditionals, claim comparisons and explanations to an evil seat's facts; candidate roles by constraint propagation that is sound but not complete (it may tell the seat less, never more than holds), with the exhaustive search kept only as the test oracle; roles described by traits, not names; two rendered blocks split at the prompt's cache boundary, entries in seat order because the model favours the first-named seat | seat block median 4 lines / 742 chars, p90 8 / 1,778, over 278 turns; public block median 1 line | constraint propagation, prompt caching, structured output | the level table plus one real seat block (content); a replay turn on the live site with the block visible (link, if the owner wants one) | `reasoning_failures/report.md` §2; code `Agents/deduction/` |
| 52 | Verification | Soundness is proved, coverage is not: every row has an executable example and a counterexample on the real night engine, a golden of its exact line, and two oracles: brute force over every deal of the cast that agrees with the view, and 20,000 random nights resolved by the real engine with every stated fact checked against the truth; the role-trait table is derived from the engine, not declared; four acceptance cases rebuild a failed turn from its frozen payload and require every listed sentence and none of the forbidden ones | 372 tests; 168 single-trait flips each caught; coverage has only the four acceptance cases as its test | oracle testing, property-based testing, metamorphic testing, golden tests | paragraph with the AC1 "must not say" sentence and why it is forbidden (content) | `reasoning_failures/report.md` §3; `tests/engine/deduction/`, `tests/factories/random_nights.py` |
| 53 | Case study | The fact lands, the behaviour does not: with the roleblock line injected the healer wrote the conclusion in every replay and still spoke in none, and a 2x2 on the turn's inputs found the cause in its own carried-forward "stay quiet" note, not the role card. The block was then placed before the note (three screens, no placement difference that survived n), and the remaining wrong vote on the frozen day-3 case traced partly to a moderator line fixed outside the engine | notes 10/10 against 0/10; spoke 0/10; neutral note spoke 9/20 against 3/20 (p = 0.08 this run, 0.007 pooled); AC2 vote for the real healer 5 of 25 with today's closing line, 9 of 25 before | replay screens, blind annotation | before/after night-record line, then the AC2 seat block (content) | `reasoning_failures/report.md` §4; `data/deduction_injection/`, `data/deduction_ac2_*` |
| 54 | Case study | The evil side: the engine gives a wolf or lone killer facts for a cover (which roles it could claim without contradiction, which night stories fit, which of its own visits a story must explain) and the cards give the advice; new card text alone did most of the work on frozen turns, the lines removed the last denials and contradictions, and in paired whole games the wolves went from no wins to three. A follow-up line naming what each counter-claimant had said was screened and dropped: it moved votes toward the named seat | claims 13 → 33 (card) → 44 (lines), denials 21 → 3 → 0 on 41 turns x 2 samples, judges differ across steps; 8 paired games: evil claimed 3 → 11 of 24, wolves 0 → 3 wins, a direction not an estimate; counter-claim line 12/16 → 12/17 pooled, 7/4 → 5/7 in its own case | paired A/B, blind annotation, negative result | the winners table and one cover line (content) | `reasoning_failures/report.md` §4; `game_play_enhancement/data/evil_cover_screen/`, `evil_cover_games/`, `counter_claim_votes/` |
| 55 | Gaps | No town-side outcome effect is claimed (reasoning-only assessment, frozen turns, small n, no paired town A/B); absorbed is not acted on beyond the four cases; one level (explanation branches) never fired on 278 turns; judge agreement unmeasured and the cover screen's steps had different judges; scope is the standard twelve roles and limits, outside which every seat gets nothing | — | — | content | `reasoning_failures/report.md` §5 |

### Topic: credit, how a game teaches the memory which lessons work (component; from `credit/`, filed 2026-10-22, report rewritten plain and approved 2026-10-22; the blocks' own wording not yet reviewed line by line)

| # | Segment | Block (one line) | Number and caveat | Skill tags | Exhibit (form) | Source |
|---|---|---|---|---|---|---|
| 56 | Problem | The memory holds lessons ("strategy points") that agents read before acting. To keep the good ones and drop the bad, each lesson needs a score. Winning the game is too blunt (a lesson used once in a long game barely decided it), and an agent saying it followed a lesson only says it used it, not that it helped. So each lesson is scored by the single decisions it was followed at | — | credit assignment (the field's term: deciding which earlier choice deserves the reward) | content | `credit/report.md` §1 |
| 57 | Design | Two different things were being scored as one: what an agent believed about the others (who is a wolf) and what it did with that belief. A wrong belief should not sink a good tactic. So they became two kinds of memory with two scores: a "tell" (a behaviour that goes with a role) is scored against the roles revealed at the end; a tactic is scored by the decision it led to. This replaced an LLM judge that graded a player's whole day at once and could not say which part went wrong | the split was built for the July nine-seat game; the tell half never reached the ten-seat game | credit assignment, deterministic grading | content: the two-question split in one paragraph; the one sentence of tagger history goes here | `credit/read_tactic_credit_redesign.md` §0–1 (alternatives §5) |
| 58 | Design | Scoring is plain code, no model call: one step records the facts of a decision (who was targeted, what their role turned out to be, what happened), and a small rule per role and action says whether that was good for the actor. Example: a wolf's vote scores well when it votes with the room, because blending in is the wolf's job, even when the room is voting out its own packmate | the rules name the skill they measure; they are not a full value of the play | deterministic grading, reward design | the ten-seat rule table, one row per role and action (content) | `credit/report.md` §2; code `Agents/memory/consolidation/grading.py` |
| 59 | Design | A lesson is credited only for doing better than no memory at all: its average score is compared with how the same role does on the same kind of decision in memory-off games, graded by the same rules, and a lesson with few uses is pulled toward zero so one lucky game cannot make it a star | on held-out games the scores ranked lessons consistently (r = +0.54 over 31 lessons); that shows the score is repeatable, not that using it improves play | baseline comparison, shrinkage for small samples | content | `credit/report.md` §3; `store_curation/strategy_points.md`; code `Agents/memory/consolidation/credit.py` (the `follow / (follow + 5)` damping) |
| 60 | Verification | A spot-check of whether "I followed lesson X" matched what the agent actually did: 13 of 15 did. One miss was an agent that claimed to follow "attack your accuser" and then passed its turn, so discussion credit now requires a spoken turn; the other spoke a soft defence instead, which no rule catches | 15 cases, judged by a model, not a person; the honest upper bound on the miss rate is about 36% | sampled audit | content | `credit/report.md` §5; `credit/attribution_spot_check.json` |
| 61 | Case study | The score can rise while play gets worse. In the July test memory hurt the town (worse on 19 of 30 paired boards). The cause was a blind spot in the rules: a town player abstaining from the vote scored "neutral", so the lesson "abstain when unsure" could never lose score and could never be pruned, yet nearly every abstain (111 of 117) fed a day where nobody was voted out. The investigator's finds turned into lynches far less often (47.5% to 26.7%). The fix scores an abstain on a no-lynch day as negative; it is the ten-seat game's rule today | primary result −0.147, p about .06 (leaning negative, not significant); the fix was checked on replays, never in live games; every one of these games ran with zero reasoning tokens (found 2026-10-04); a second cause found 2026-10-22: the 0.00 was measured against zero because the lesson was typed as concealment advice and no memory-off concealment average existed, so the code used 0; against the real vigilante day-vote average (+0.20 over 90) it is about −0.16, just past the prune line. Tell it as two gaps together; the ten-seat code closes both | Goodhart's law (a measure that becomes the target stops measuring), reward misspecification | content: the abstain lesson's score before and after the fix (0.00 to −0.62); link the closure | `credit/blindspot_fix/experiment_log.md` §1, §3, §6, §7 (owner read pending); `credit/report.md` §6; code `grading.py::town_abstain_grade` |
| 62 | Gaps | Nothing shows that credit-guided memory makes agents play better: the July run leaned negative and the fixes were never tested live. Whether "followed" claims are wrong at random or in a pattern is unknown. The tell book is built but not served. The served game runs memory off unless the deployment turns it on | — | — | content | `credit/report.md` §7; `server/config.py` (`WW_MEMORY_ENABLED` default off) |

### Topic: lessons (the cross-topic layer; one paragraph per lesson, each linking back to the segments it draws on)

| # | Segment | Block (one line) | Number and caveat | Skill tags | Exhibit (form) | Source |
|---|---|---|---|---|---|---|
| 15 | Lesson | Generation was separated from checking wherever the producing call had an incentive or an information advantage: a second model on outcome-driven verdicts, a detector denied the roles, a separate check of each finished line. A different model is not independence; withholding information is | de-halo removes a third of the halo and sees the outcome; the detector, same model, works because it never sees the roles | generator-verifier separation | the paragraph drafted in the file, linking to blocks 14 (de-halo), the tells block and the echo-gate block when filed | `cross_project_synthesis/separating_generation_from_checking.md` |
| 16 | Lesson | Where a rule could be code, it became code, and the model kept only what no reliable rule could do: turn order from the agents' own tags, the dead roster and night records from engine records, the night-1 default drawn by lot, board counts overriding the model's, credit graded from the record. Measurement drew the boundary both ways (a regex lost to the model at tagging; the model lost to arithmetic at counting) | tags missed an accusation on 24 of 183 messages; the credit table's thresholds unvalidated for ten seats; the nine-seat credit rules rewarded advice that hurt (−0.147, p≈.06) | deterministic-first design | the draft paragraph in the file, linking to eight instances across six topics | `cross_project_synthesis/deterministic_where_reliable.md` |

The deduction engine (blocks 50–52) is the largest instance of lesson 16: a whole layer of the seat's reasoning moved from the model to code, with the model keeping only the judgement between claimants.

Instances still to file in their own topics: tell detection (blind annotation) under the tells
topic from `store_curation/` and `extraction/tell_extraction/`; the echo gate (output guardrail)
under the discussion topic from `game_play_enhancement/` and `sequential_discussion/`.

### Parked cross-references

Blocks that belong to another topic, noted here so they are filed when that topic is walked.

- ~~The public-by-design fields exist to cut hallucination~~ filed 2026-10-21 as block 49 under the deduction topic.
- LangGraph `Send` delivers its payload verbatim; only a compiled subgraph filters to its input
  schema. Graph-node knowledge; file under an orchestration topic if one forms. From
  `agent_boundaries/experiment_log.md` §2.
- "Grade the decision, not the result" is a cross-topic lesson (the halo here, the de-lucked metrics,
  the credit grading rule); one paragraph in the lessons topic linking back. From `extraction/selection/`,
  `metrics/`, `credit/`.
- Conditional prompt composition (the rules block by round, ability counts only for limited roles,
  the necromancer's bodies from night 2, the human's ask, the memory block only when on): a design
  block for the prompt-assembly topic (`Agents/prompts/layout.py`, the role cards). Point to make:
  isolation is enforced at the payload because it is a guarantee; relevance is decided at the template
  because a wrong call there costs quality, not the game. Design block, not a finding (unmeasured).

## Folder walk

One row per evidence folder, in the order of `evidence/README.md`. **Status** is `pending` or `done`.
**Blocks** lists the block numbers the folder yielded (may be none). **Pass** says whether the folder
needed a report-style pass before mining (`ok` / `needs pass` / `done`). Notes pre-filled from memory
are caveats to keep in view while reading, not decisions.

### Memory pipeline

| Folder | Status | Blocks | Pass | Notes |
|---|---|---|---|---|
| `dedup/` (overview log, report, batch_architecture, clustering plan, incremental_convergence) | done 2026-10-14 | 39 (+ confirms 17–27) | done: overview and report given dated addenda for the v8 state (triage-only fold, SP keep/discard, per-model thresholds, merge path off) | the five align with the sub-logs; only the clustering plan adds a block (the gate's probe numbers) |
| `dedup/store_retrieval_impact/` | done 2026-10-14 | 35–38 | done: dated addendum (filtering not the reranker; store sizes now; demo serves SPs only) | phase 1 n=5 superseded; phase 2 n=39 current; judge-scored, not golden |
| `dedup/batch_dedup/` | done 2026-10-14 | 17–23 | done: dated live-state addendum (triage-only fold, SP keep/discard, threshold 0.65 from the per-embedding table, no non-Gemini regression) | n=111 golden; the merge path is built, validated, off |
| `dedup/per_extraction/` (+ tricky_cases) | done 2026-10-14 | 28–34 | done: dated currency note (live as the store-write step of offline extraction; prefilter values now per model; no non-Gemini re-run) | tricky_cases.md = the error analysis that both tuned the prompt and audited the labels; two cross-refs: backend shift at temp 0 (instruments), Flash-Lite kept with batch as the safety net (cost) |
| `dedup/embedding_prefilter/` | done 2026-10-14 | 24–27 | done: dated addendum (Qwen remap, the July drift, where it runs, the re-embedded 232 with two corrections) | the prefilter signal is computed live on content/action; the store indexes situations only |
| `retrieval/filtering/` | done 2026-10-14 | 40–42, 45, 46 | done: dated addendum (filters off by default and in the served game; line per embedder; code paths; the opposing-pair example not shown in run 1) | n=5, directional only; the judge redesign is the strongest block · **owner read pending** (walked by the AI 2026-10-14; revisit in order) |
| `retrieval/reranking/` | done 2026-10-14 | 41–42 | done: dated addendum (both rerank switches default off; served demo reranks nothing; cross-encoder trained, not wired) | n=5, directional only; the reranked A/B arm belongs to `memory_system/effectiveness/` · **owner read pending** (walked by the AI 2026-10-14; revisit in order) |
| `retrieval/capacity_limits/` | done 2026-10-14 | 43–44 | done: dated addendum (the cap of 5 never reached the prompt; live is about cap 3) | n=120, one judge, no significance test · **owner read pending** (walked by the AI 2026-10-14; revisit in order) |
| `retrieval/context_eval/` | pending | | | methodology final, execution deferred |
| `retrieval/per_day_discussion/` | pending | | | parked; churn is paraphrase noise |
| `extraction/post_game/` | pending | | | judge de-bug, per-role vs single pass, model bake-off |
| `extraction/situation_summary/` | pending | | | |
| `extraction/situation_dimensions/` | pending | | | v6 dimension build; gating NEGATIVE, default off |
| `extraction/day_summary/` | pending | | | structured digest that bounds context |
| `extraction/selection/` | pending | | | net_verdict = outcome halo; steer selection, never content |
| `extraction/tell_extraction/` | pending | | | task reshaped so Flash-Lite could do it; run billed 6x its quote |
| `extraction/selection/outcome_halo_case_study.md` (was `case_studies/`) | done 2026-10-14 | 13–14 | done: rewritten specimen-first with a dated "what happened since" note; moved into the selection folder, since a standalone folder implied a topic | the halo specimen; files under memory extraction, lesson "grade the decision, not the result" |
| `caching/` (report + experiment_log) | done 2026-10-14 | 6–12 | done: log §8 mechanism + Claude date fixed; report §4.2 mechanism column; report §1 scoped to caching with pointers to the other levers | feeds the cost topic; the other cost folders are still to walk |
| `memory_system/effectiveness/` (+ v6_sp_ab) | pending | | | n=30; static-memory "+17pp p=0.013" is a FUSION ERROR, cite only the corrected claim |
| `memory_system/ablation/` | pending | | | n=120; observations vs strategy points vs both |
| `memory_system/strategy_adoption/` (+ forced_schema_screen) | pending | | | adoption prompt v1-v3; verdict coverage 0.27 to 0.97 |
| `memory_system/augmentation/` | pending | | | parked |
| `memory_system/store_progression.md` | pending | | | |
| `memory_system/v8/` | pending | | | ten-seat port, reopened 2026-10-13 |
| `store_curation/` | pending | | | three stores grow and stay bounded; no plateau |

### Game engine and behaviour

| Folder | Status | Blocks | Pass | Notes |
|---|---|---|---|---|
| `role_set/` | pending | | | 9-seat design (Jun 1), superseded by the 10-seat / 12-role sheet |
| `sequential_discussion/` (+ quality_gate) | pending | | | concurrent to sequential, shipped; acceptance A/B |
| `generation_prompt/` (+ prompt_boundary, prompt_claims_audit, validation) | pending | | | prompt = how-to + facts, memory = what signals mean; one falsified tactic |
| `game_play_enhancement/discussion_evidence.md` | pending | | | votes-and-silence diagnosis; three-phase fix |
| `game_play_enhancement/role_sheet.md`, `phase3_wiring_census.md` | pending | | | current role ruling |
| `agent_boundaries/` | done 2026-10-14 | 1–5 | done: report revised against `0566de66`; forensics moved to a new experiment_log.md; batch wiring fixed + night-payload tests added | information-boundary guarantee; the exemplar report |
| `reasoning_failures/` (+ `game_play_enhancement/data/evil_cover_*`, `counter_claim_votes/`) | done 2026-10-21 | 47–55 | done: new `report.md` (reference doc) as the synthesis layer; catalogue, log and reviews left as the record; numbers lifted by a fact-sheet pass, none re-derived; record inconsistencies listed in the report's review note, not reconciled | the deduction engine; the second half of the boundary story |

### Evaluation apparatus

| Folder | Status | Blocks | Pass | Notes |
|---|---|---|---|---|
| `evaluation/report.md` + `source_map.md` | pending | | | the hub and the reliability ledger |
| `evaluation/methodology/` | pending | | | paired A/B; variance-reduction levers |
| `evaluation/metrics/` | pending | | | instrument trust for the de-lucked proxies |
| `evaluation/llm_judge/` | pending | | | judge misses information gain |
| `evaluation/labeling/` | pending | | | |
| `evaluation/sampled_human_review/` | pending | | | |
| `evaluation/dimension_extraction/` | pending | | | |
| `evaluation/discussion_tagger/` | done 2026-10-22 | — | not needed | no blocks: owner ruled 2026-10-22 to leave the tagger out of the write-up (retired to a diagnostic 2026-07-13, feeds no credit, runs in no game; the numbers are hard to defend in an interview). If `credit/` needs its history, one plain sentence, no tagger detail |
| `evaluation/replay_screens/` | pending | | | first Haiku game entries already in `eval_exhibits.md` |
| `evaluation/end_to_end_ab/` | pending | | | |
| `evaluation/loop/` | pending | | | |
| `evaluation/hardening_pass/` | pending | | | |
| `evaluation/hallucination_bench/` | pending | | | rates ~3% msgs / ~4% notes / 9.6% night; never cite 0.14% |
| `metrics/` (+ design, metrics_audit) | pending | | | metric design journey; de-lucked per-role proxies |
| `tracing/` | pending | | | capture half of eval |
| `tracing/fingerprinting/` | pending | | | provenance by runtime fingerprint |
| `model_drift/` | pending | | | interleave-arms guard; never compare to historical runs |

### The v6/v7 campaign

| Folder | Status | Blocks | Pass | Notes |
|---|---|---|---|---|
| `execution_plan/` | done 2026-10-22 | 63–67 | done 2026-10-22: five planning docs condensed into `report.md` (decision record, plain, with the score, the wobble and the planting explained) + `experiment_log.md`; originals kept until the owner decides | power analysis + pre-registration are the keepers; master plan, Phase B review, v6 roadmap = internal planning, no blocks. Statistics to learn parked in `interview_prep/stats_used/report.md` (untracked, ignored) |
| `v7_final/` (+ discussion_credit, extraction_screens, gates, synthesis_checks) | pending | | | v7 CLOSED NEGATIVE; all memory games had 0 reasoning tokens; config slip and the arm guard |
| `discussion_tagger/` | done 2026-10-22 | — | not needed | no blocks: owner ruled 2026-10-22 to leave the tagger out of the write-up (retired to a diagnostic 2026-07-13, feeds no credit, runs in no game; the numbers are hard to defend in an interview). If `credit/` needs its history, one plain sentence, no tagger detail |
| `credit/` (+ blindspot_fix) | done 2026-10-22 | 56–62 | done 2026-10-22: plain rewrite centred on the ten-seat code, approved and swapped in (the 10-19 version committed at `24dfd3a7` first) | §6 now tells the abstain case as two gaps (neutral abstain + missing comparison counted as zero), no chronology; `blindspot_fix/` itself not read by the owner (not needed for the page) |

### Training

| Folder | Status | Blocks | Pass | Notes |
|---|---|---|---|---|
| `fine_tuning/agent_dialogue/` | pending | | | |
| `fine_tuning/dedup_classifier/` | pending | | | closed |
| `fine_tuning/embedding/` | pending | | | |
| `fine_tuning/cross_encoder/` (reranker, dedup_prefilter) | pending | | | CE reranker v4 NDCG@5 0.882; prefilter deployed |
| `fine_tuning/memory_selection_bandit/` | pending | | | parked, paper design only |

### Meta and outside evidence

| Folder | Status | Blocks | Pass | Notes |
|---|---|---|---|---|
| `refactor/` | pending | | | structure audit, node factory, eval architecture convention |
| `cross_project_synthesis/` | done 2026-10-14 | 15–16 (+14 sourced) | ok, left as is | the lessons layer, not a topic; the README's candidate list is the queue for more lessons |
| `model_selection/` | pending | | | |
| `docs/agentic_ai_encountered_issues.md` | pending | | | Vertex stall and rescue model; outside evidence/ but part of the agent story |

## Organisation

Decided after the walk. Candidates are tested against the collected blocks here; nothing is fixed yet.

## Walk log

One line per session: date, folders walked, blocks added, passes done.

- 2026-10-14: map created, bottom-up method agreed. Walked `agent_boundaries/`: report re-verified against the code (roles, builders, layout, check count had drifted); found three checkers fed nothing on live games, fixed in `tests/leak_test.py` + run_batch + capture scripts, night-payload tests added; forensics moved to experiment_log.md. Blocks 1–5 in the ledger; the model (segments + skill tags + exhibit + source) written up above. Served-game leak audit built by an Opus agent, reviewed, recorded in the report §3/§5 and the log §6 (needs migration 0013 + cron on deploy). Walked `caching/`: fixed the log §8 (probe measures automatic caching; Claude row dated 10-11 and marked-prefix), the report §4.2 (mechanism column) and §1 (scoped to caching); blocks 6–12 under the first skill topic, cost optimisation; the model gained the skill-topic rule. Walked `case_studies/`: rewritten readable, then moved to `extraction/selection/outcome_halo_case_study.md` (a case study is a segment, not a folder); blocks 13–14 open a provisional memory-extraction topic. Walked `cross_project_synthesis/`: the lessons layer; blocks 15–16; three terms added to the glossary. Second lesson file `deterministic_where_reliable.md` written by an Opus agent (8 verified instances), spot-checked, indexed in the synthesis README. Walked `dedup/batch_dedup/`: blocks 17–23 open the memory-consolidation topic; the live/built-off/superseded presentation rule recorded. Walked `dedup/embedding_prefilter/`: blocks 24–27; first export exhibit built (re-embedded the 232 cases on Qwen; found the new SP discard line would drop case 155, and the May observation counts don't reproduce). Blocks 25–27 moved to a new skill topic, embeddings, so the material presents as how the tool was used rather than as a deployed component. Walked `dedup/per_extraction/`: blocks 28–34 open two provisional skill topics, golden-set construction and prompt engineering; presentation ruled as a phase table plus two lifted snippets and one tricky case. Walked `dedup/store_retrieval_impact/` (blocks 35–38, opening provisional retrieval and instruments topics) and the five top-level dedup docs (block 39 from the clustering plan; the rest align).
- 2026-10-14 (cont.): Walked `retrieval/filtering/`, `reranking/` and `capacity_limits/` together (one May story). Re-verification found the capacity decision (cap 5) was implemented as fetch width with the keep of 3 still after it, so it never reached the prompt; and run 1 contradicts the filtering report's opposing-pair example. Dated addenda on all three reports. Blocks 40–44 under retrieval, 45 under the instruments (judge design), 46 under embeddings. Lesson-queue pointer added (the cap joins "check that the experiment that ran is the one you meant").
- 2026-10-21: Walked `reasoning_failures/` with the evil-cover data from `game_play_enhancement/`. Wrote `reasoning_failures/report.md` (reference doc, destination-first) from a fact-sheet pass over every data sub-folder; the catalogue stays the frozen spec. Block 47 under the information boundary (the engine reads one `SeatView` from the seat's payload); new topic "deduction" with blocks 48–55; parked public-by-design item filed as 49; lesson 16 names the engine as its largest instance. Open for the owner: whether to cite the 0 → 3 wolf wins in an engine topic (it bundles card text with the lines), and which deploy SHA goes on the report header (`334a56e1` or `e486d3ca`).
- 2026-10-22: `discussion_tagger/` and `evaluation/discussion_tagger/` closed with no blocks; owner ruled the tagger out of the write-up. Noted: `discussion_tagger/report.md`'s consumer table still says both verdicts are credited through `_tagger_ledger` (removed 2026-07-13); left as is, since the folder is not mined.
- 2026-10-22: walk order is now alphabetical over `evidence/` (owner). The three `retrieval/` rows were walked by the AI without the owner's read; marked owner read pending.
- 2026-10-22: `credit/` filed as a new topic, blocks 56–62, written plainly because the owner found the report too technical; owner review pending. Verified against the ten-seat port in `Agents/memory/consolidation/`. Block 57 carries the one-sentence tagger history.
- 2026-10-22: `execution_plan/` condensed into a plain report + log, with the context (what a game score is, the 15 real memory-off scores, how an improvement was planted, why +0.15) added after the owner found the first version too technical; blocks 63–67 under the instruments topic. The statistics behind it (averaging, power, slope test) parked for study in the untracked interview-prep notes.
