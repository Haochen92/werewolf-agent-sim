# Evidence report pass: proposal

Prepared 2026-10-25 for the owner's review. **Nothing in `evidence/` has been changed.** This is the plan
for bringing every folder's `report.md` to the standard of the two revised evaluation reports
([deterministic audits](../../evidence/evaluation/deterministic_audits/report.md),
[factual errors](../../evidence/evaluation/factual_errors/report.md)), with each folder's
`experiment_log.md` holding the chronological detail.

**How it was made.** Five read-only passes, one per area, read every report in full against the two
exemplars and the style guide, read enough of each log to tell poor presentation from missing evidence,
and spot-checked mechanism claims against today's code. Each graded a report on two separate axes:
editorial condition (matches / light edit / rewrite / missing report) and structure (keep / merge / split /
relocate). Numbers were not audited one by one; contradictions and overstated claims were flagged. The full
assessments, with section-level detail and the code each claim was checked against, are in
[`assessments/`](assessments/). I re-checked the claims a decision below depends on (marked ✓).

`evaluation/` was not re-graded (revised 2026-10-23/24).

---

## 0. The rubric for the pass

**What the exemplars do well** is explanatory organisation, not just short sentences: they make the
reader understand the engineering before asking them to weigh its evidence. The deterministic-audits
report says why code suits the question before listing checks, groups them by method, takes each case
through purpose, mechanism, result and limits, and ties a measurement to what changed. The factual-errors
report defines its subject with examples and non-examples, separates measuring frequency from testing a
known failure, gives a workflow (find → freeze → diagnose → compare) and teaches the method through one
worked example before broadening. One is a taxonomy of methods, the other a diagnostic workflow: the
structure follows the subject.

**The rule:** explain the question, the distinction needed to answer it, how the method works, what the
evidence showed and what changed. Use concrete examples and precise limits. Choose a structure that serves
the subject; do not copy the exemplar's headings.

**Choose the document's type before its tense.** Each rewrite is tagged with one:

| Type | It explains | Tense and history |
|---|---|---|
| Current-system reference | What runs now, why, and what supports it | Present tense; how it got here goes to the log |
| Experiment or decision report | What was tested then, what was learned, what decision followed | Keeps the mechanism as it ran then; a dated note says what superseded it. Never rewritten as if it tested today's code: a code check today cannot say what ran in June |
| Area overview | How the components or investigations fit together, and the current conclusion | Present tense; each finding stated with its essential scope and linked to its detailed home |

**Every superseded or negative record opens with a four-line card:** the question, the test with its N,
the answer, and what followed (the `## In short` block in `evaluation/model_admission/report.md` is the
shape). It is the unit the owner revises from and the unit a write-up block lifts; the detail below it is
there if a reader pushes. Where the work list says "dated status line" on a superseded or negative
document, it means this card.

**Code anchors are `path::symbol`, never line numbers.** The assessments found rotted line anchors in
tracing, metrics, dedup, store_curation and the discussion tagger; a symbol survives an edit above it.

**Learned from the pilot (2026-10-26),** kept only where it transfers beyond that report:
- **Say what a measure counts and what it cannot see:** its unit (per message, per game, per event),
  its denominator, and its blind spots. A rate per message is not a rate per event; counts that do not
  add up name their remainder.
- **A mechanism is not its outcome, and an outcome count is not an effect.** A rule that gives a turn
  does not make the turn an answer; served is not used, merged is not correct, retrieved is not
  helpful. "7 of 7 voted out" says nothing about what the change did without a comparison.
- **Every current-system reference opens with a version line:** the code snapshot it describes, and a
  note that historical results belong to the setup they ran on.
- **Optional, for reports that record several design decisions:** a decision index, and a "when to
  revisit" table (the assumption each choice rests on, and the evidence that would justify changing
  it). Not a default section.

**The exemplars are models of presentation, not of claim strength.** Two of their sentences are stronger
than the scoped wording since adopted, and are corrected in the first commit so they are not imitated:
deterministic audits case 2, "✅ for soundness: nothing false is said" (true within what the oracle
tested); factual errors step 3 and its worked example, "If rewording the fact fixes it, the cause was the
wording" / "So the cause was the wording" (the rewording points to the wording; one turn replayed is not a
general cause).

---

## 1. Decisions for the owner

**Ruled 2026-10-26:** §3.4 group B (consolidations) and group C (optional cleanup) approved; the
discussion tagger moves to `credit/` (filing only); `extraction/day_summary/` and
`dedup/incremental_convergence.md` stay where they are.

**Ruled and done 2026-10-26:** D1 (gameplay grouped under `evidence/gameplay/`), D2 (the memory hub and
the merged v7 report, with `v7_final/` and `execution_plan/` moved under `memory_system/v7/`), D3 (the
wording, applied in the effectiveness report), D4 (one retrieval area report, written in step 5), D5
(all five group A moves), D6, D7 (the pilot). Step 4, the moves, landed in five commits (`8fb7cd88`,
`18686b32`, `bde9da1e`, `430956c0`, `5ffb009d`). Two choices made in the move: `gameplay/data/` stays one
folder (the roles and deduction data were not split out of it, so no README path had to change), and
`role_set/` moved whole to `gameplay/roles/role_set/`. Runs, logs and frozen scripts inside
`evidence/` keep the paths they recorded.

| # | Decision | Recommendation |
|---|---|---|
| D1 | Group the gameplay folders into `evidence/gameplay/` (§3.1) | Yes, with the layout in §3.1 |
| D2 | Make `memory_system/` the memory overview: `store_progression.md` rewritten as its `report.md`; `v7_final/` and `execution_plan/` merged into one v7 report (§3.2) | Yes to the hub and the merged report; the physical move of `v7_final/` and `execution_plan/` under `memory_system/` is optional (many inbound links) |
| D3 | `execution_plan/report.md` §5 says "No memory version was shown to help"; `effectiveness/report.md` says the June A/B on the v5 store improved selected town decision measures (healer saves p=0.005, correct eliminations p=0.028, N=30). The later v6-store A/B (+6 points, p=0.77) is **not a replication**: a different store, a changed prompt bundle and a higher no-memory baseline ✓ | Replace the sentence with three separate findings: "The June static-memory A/B reported improvements on selected town decision measures. A later A/B on a different store, run against a higher no-memory baseline, found no town effect; it was not a replication of the June test. Separately, the pre-registered v7 endpoint detected no compounding benefit." Keep "the investigation is closed" apart from "the hypothesis was disproved" throughout |
| D4 | Merge the three short May retrieval reports (filtering, reranking, capacity limits) into one `retrieval/report.md` | Yes, as an area report: the read path today, then the May study with each experiment's setup and limits kept distinguishable, and a dated note on what shipped |
| D5 | The moves in §3.4, group A | Yes to the five moves in group A; groups B and C need no decision |
| D6 | `CLAUDE.md` still says "Existing `evidence/`: FREEZE", and `refactor/eval_architecture_convention.md` §4 records the freeze | Record the scope of your 2026-10-23 ruling, not an open editing rule: "Reports, hubs and logs may be rewritten and restructured; keep the honest journey (logs are not laundered into hindsight); date what changes; retracted numbers are corrected in place with a dated note". Done in the first commit (§5 step 1): every agent briefed on the repo reads the FREEZE line and will refuse to touch `evidence/` |
| D7 | Pilot | Rewrite `sequential_discussion/report.md` first, under the rubric in §0 |

---

## 2. Summary of the condition

About 60 documents across 22 folders. In short:

| Condition | Count | Folders / documents |
|---|---|---|
| Matches | 8 | `extraction/selection`, `extraction/tell_extraction`, `credit/report.md`, `agent_boundaries` (one sentence to add), `dedup/experiment_log.md`, `store_curation/experiment_log.md`, `tracing/fingerprinting/experiment_log.md`, `refactor/` (status lines only) |
| Light edit | ~20 | see §4 |
| Rewrite | 9 | `sequential_discussion`, `discussion_tagger`, `dedup`, `retrieval` (3 → 1), `store_curation`, `store_progression` (→ memory hub), `v7_final` (+ `execution_plan`), `tracing`, `metrics` |
| Missing report, warranted | 5 | gameplay hub (problems 2–5 unwritten), `generation_prompt` (→ turn prompt), roles (role sheet + `role_set` + Phase 3), `memory_system/v8` (the current memory system has no report), `fine_tuning` (one report over the four trained tracks: trained and evaluated, not wired) |
| Missing report, not warranted | 9 | `role_set` (into roles), `retrieval/context_eval`, `retrieval/per_day_discussion`, `memory_system/augmentation`, `forced_schema_screen`, `v6_sp_ab`, dedup sub-logs, `refactor`, `cross_project_synthesis` |

The common faults, in order of how often they appear:

1. **Several eras of truth on one page.** A June body, then a gap table, then an October addendum that
   overrules the body (`dedup`, `store_progression`, `retrieval/filtering`, `retrieval/reranking`). The
   reader must reconcile them. The fix depends on the type (§0): a current-system reference gets one
   present-tense account with the history in the log; an experiment report keeps what it tested, with a
   dated note on what superseded it.
2. **"How it works today" describing a design the code no longer has** (`sequential_discussion`,
   `discussion_tagger`, `store_curation`, `metrics`, `tracing`, `v7_final`).
3. **One finding told in several places with different numbers** (the outcome halo, the stage filter, the
   June A/B told four times, the v7 verdict three times). Each gets one home (§3.5).
4. **Terms used before they are defined** (SP, v5_0, de-lucked, halo, consumption mode, gate_key).

---

## 3. Structure

### 3.1 Gameplay (D1)

**Purpose:** how the AI players are given information, take part in the day's discussion and reach
decisions, the roles and rules they play under, and how each was investigated and improved. Who may know
what is defined in `agent_boundaries/`, which stays where it is as the one authoritative account and is
linked from here.

```
evidence/gameplay/
  report.md               overview: problems → causes → interventions (grows from game_play_enhancement/report.md;
                          problem 1, factual errors, is already written; 2–5 to write)
  discussion_evidence.md  the journey log, kept whole, with a section index at its head (drafted in the assessment)
  discussion/             from sequential_discussion/: the day discussion today (rewrite) + quality_gate/;
                          the one home of the persona-voice and silence work (2026-10-18): the voices decision (on in
                          hosted games since 2026-10-19, off in batch) and the silence ruling, today recorded only in data/ READMEs; hub problem 4 links here
  turn_prompt/            from generation_prompt/: NEW report (what a seat reads at its turn, in what order,
                          what it must output, which choices were tested); a short section on the record
                          each seat reads (day summary, claim ledger) that links to extraction/day_summary/,
                          which stays with the extraction mechanics (owner 2026-10-26)
  deduction/              from reasoning_failures/: report, catalogue (authoritative), reviews v1–v3 in reviews/
                          (superseded; folded into the catalogue), counter-claim data
  roles/                  NEW report: role_sheet.md (authoritative), wiring census (historical),
                          role_set's June log (superseded history), the evil-contest thread and its data
  data/                   the rest of game_play_enhancement/data/
```

Placement by intervention: **evil covers** ("claim, never deny") were a role-card change, so they live in
`roles/`; the deduction report keeps one paragraph on what the engine's evil-seat lines added. The
assessment's own numbers show the card text moved claims 13 → 33, the engine's lines 33 → 44. The
**counter-claim line** was an engine line, screened and dropped, so it stays in `deduction/`.
Measurement stays in `evaluation/factual_errors`; the gameplay overview keeps the interventions.

### 3.2 Memory (D2, D3)

```
memory_system/
  report.md           the hub (area overview): today's system in one paragraph, then one row per version (change,
                      why, headline result with N and scope, link). Rewritten from store_progression.md; the
                      headline matches the owning report word for word, and the detail stays there
  v8/                 the current system: NEW report.md (what each stage does, what was measured, what was not:
                      no memory-on vs memory-off run; memory is off by default in served games ✓)
  effectiveness/      the June static A/B; absorbs decision_replay/report_screening_layer.md as its screening section
  v7/                 ONE report built on execution_plan/report.md, led by the method (pre-registration, the power
                      simulation, a signed endpoint) and then the result (no compounding detected); v7_final's loop
                      design, the two invalid June runs and the arm guard follow as the history that forced the method
  strategy_adoption/  May adoption field → the June forced-verdict screen → today's per-lesson verdict field
  ablation/           May, observations vs strategy points (dated: served games now use strategy points only ✓)
```

The component folders stay top-level and separate: `extraction/`, `dedup/`, `retrieval/`, `store_curation/`,
`credit/`, `fine_tuning/`, `caching/`. The hub links to each.

### 3.3 Retrieval (D4)

One `retrieval/report.md`, an area report in two parts. First the read path today (situation call → fetch
5 → keep 3 per situation; strategy points only in served games; lookup reused within a day or night,
refreshed on a new role claim). Then the May study as it ran: one section per optional stage (filter,
rerank, wider fetch), each with its own setup, store version, "5 scenarios, one judge" or N=120 beside each
number, its limits, and a dated note on what shipped (none of them by default). The three current reports
become dated log entries.
`per_day_discussion/` gets a dated addendum: per-day reuse shipped in v8 as a cost decision, without the
A/B the log said it needed.

### 3.4 Relocations (D5)

**A. Moves that need your decision (D5).** Each is placed by the folder's reader question.

| Move | Reader question, and why this home |
|---|---|
| `retrieval/context_eval/` → `evaluation/labeling/context_eval/` | "Can a cheap model label memory relevance well enough to train and evaluate a reranker?" Its findings are about label validity (strong judges agree ~80%; most disagreements are topical over-crediting), which is labelling's question; `labeling/` already uses its §6 as protocol. The links from the reranker's training log are kept. **Not just a move:** the labelling report covers its over-crediting finding (case 2, 514 of 1,848) and its protocol, but not its own question, "does a labeller need the game context?" Add one case to `labeling/report.md`: context moved the labels (cheap model toward the careful judges); the careful judges' ceiling (80.5% binary, 64.5% exact); flash-lite with context at 77%; the reranker re-scored on strict labels (observations down ~0.06–0.09 NDCG@5). The deferred two-gold design goes in its gaps |
| `model_drift/drift_surfaces_and_guards.md` → `evaluation/experimental_controls/` | "Which components can a provider change under us, and what guards each?" The origin record of the drift controls; precedent: `variance_reduction_levers.md` |
| `model_selection/report.md` → `evaluation/model_admission/` | "How was the seat model chosen in July 2026?" The predecessor model admission already cites. Kept whole as a dated record: admission summarises only its method lesson, while the per-game costs and turn times, the one-model-per-job slots and the benchmark analysis live only here |
| `discussion_tagger/` → `credit/discussion_tagger/` | "Could an LLM judge score discussion for memory credit?" A credit signal, retired 2026-07-13 ✓ |
| `cross_project_synthesis/` → `writeup/lessons/` | Write-up drafting material, not an evidence record |

**Approved rename (owner 2026-10-26):** `extraction/selection/` → `extraction/observation_quality/`. The
folder's task is the quality of what extraction writes, in two questions: did it pick the right moves
(pivotal, non-generic; tested once on three nine-seat games, unmeasured on ten seats), and did it judge
each one correctly (the outcome halo, de-halo, the rule grade). The report opens on the two questions; the
halo stays the main finding and selection the open gap. About 15 files reference the path, one of them
code (`evaluation/experiments/`). Add to its "what is not established": dropping observations de-halo
marks unclear, as a candidate filter, with its three risks (unclear means unknown, not bad, and the judge
is unsized; it would empty vote and discussion cells, where the halo is strongest; its changes fall mostly
on the losing side, so the store would learn from winners) and the cheap screen (a third store variant,
about $5, count the emptied cells and read a sample).

**B. Consolidations inside a folder** (no decision needed; part of that folder's rewrite):
`tracing/implementation_notes/` becomes one `tracing/experiment_log.md` (the same 422 incident is told
three times); `dedup/README.md` and `batch_architecture.md` fold into the dedup report;
`decision_replay/report_screening_layer.md` folds into the effectiveness report.

**C. Optional cleanup:** `dedup/golden_eval/` → `dedup/embedding_prefilter/data/` (one file, one
consumer); `memory_system/augmentation/` → `extraction/` (low value).

**Not moving:** `agent_boundaries/`, `caching/`, `fine_tuning/` (sibling of memory, not a campaign),
`metrics/` (stays as the nine-seat design record that `evaluation/metrics/` already names it as), the dedup
sub-logs, the retrieval run dumps, `situation_summary/outputs/retrieval_golden_labels.json` (reranker
training reads it), every `data/` folder unless its README paths are updated in the same commit.

**Moves go in their own commit,** separate from prose edits, and check operational paths, not only Markdown
links: scripts, loaders and runner outputs that read these paths (about 70 code files reference the
gameplay folders alone).

### 3.5 One detailed home per finding

Each finding gets one authoritative detailed account. Other reports may state the result and its essential
scope in a sentence, consistent with the home, and link to it; what they may not do is restate it with
different numbers or a different conclusion, which is the fault found today.

| Finding | Detailed home | Others summarise and link |
|---|---|---|
| The outcome halo | `extraction/selection` §4 | `post_game` §4, the halo case study's closing note (both currently restate different numbers) |
| Query construction, stage filter | `extraction/situation_summary` | `situation_dimensions` §4–5 (their baselines conflict: 36 vs 41 of 96) |
| Claude batching, cache-write overrun | `caching` §3.6/§4.6 | `post_game` (one sentence) |
| The June static A/B | `memory_system/effectiveness` | the hub, v7, the screening section |
| The v7 compounding verdict | the merged v7 report | the hub, `effectiveness` "What remains open" |
| Observation and strategy-point admission (dedup) | `dedup` | `store_curation` (one line per store) |
| "Filtering doesn't stack on a clean store" | `retrieval` | `dedup/store_retrieval_impact` (the measurement) |
| Discussion-tagger validation | `evaluation/llm_judge/discussion_tagger.md` | `discussion_tagger` |
| Drift controls | `evaluation/experimental_controls` | `model_drift` (moved beside it) |
| The silence ruling and the voices (2026-10-18/19) | `gameplay/discussion` | the gameplay hub, problem 4 |

---

## 4. Work list

Size: **S** = status line or a few sentences; **M** = several passages; **L** = rewrite or new report.

### Fix regardless of the rest (one small commit, first)

These state something the record has retracted or does not establish.

| Where | Problem | Fix |
|---|---|---|
| `credit/blindspot_fix/experiment_log.md` §④c, §⑥, §⑦ | Cites the retracted "+17/+33pp; reranked p=0.013" as a result | Dated correction line at each, pointing to the static-memory correction |
| `memory_system/store_progression.md`, `v7_final/report.md` | Repeat the arm-joining "+17→+33pp" | Handled by their rewrites (L below) |
| `v7_final/report.md`; `effectiveness/report.md` "What remains open" | Compounding called "open"; v7 closed negative | Handled by the v7 merge; one sentence in effectiveness |
| `effectiveness/report.md` ×2, `report_screening_layer.md` ×1, `model_drift` L99–101 | Drift asserted ("most likely silent Vertex-side model drift", "endpoint drift by elimination") | "Suspected, not established" (the 2026-10-25 paired re-test: p = 0.18) |
| `extraction/post_game/model_comparison/v7_refresh/README.md:36` | "flash-lite drifts ~daily" as established | Suspected |
| `metrics/report.md` §2, `candidate_ledger.md` | "the static-memory proof" | "the June static-memory result" |
| `effectiveness/report.md` verdict | "The benefit is epoch-sensitive … the cause is a risen no-memory baseline" (a cause stated as established) | "One plausible reading" (D3) |
| The two exemplars | The two overstatements in §0 | Scoped wording |

### Gameplay

| Document | Size | Action |
|---|---|---|
| `sequential_discussion/report.md` → `discussion/` | L | *Reference.* **Pilot.** Rewrite as the day discussion today (opening round → reactive obligations → sweeps → closing defence); the June concurrent → sequential decision and the quality gate as the case study, with N; the novelty gate kept as a falsified idea, not a mechanism; and a section on persona voices and silence (voices on in hosted games since 2026-10-19, the silence ruling), written from the 2026-10-18 `data/` READMEs, since this report is their one home (§3.5). Its file references are stale (`decision.py`, `novelty_agent.py` no longer exist) |
| `generation_prompt/` → `turn_prompt/report.md` | L | *Reference.* New report: layout, board facts, results wording, the record (day summary + claim ledger), output schema, tested choices with N. Log §0 retitled "The call as of 2026-07-08" |
| `roles/report.md` | L | *Reference.* New: the current cast and win logic, why it changed, the balance batches and the hold (with N), the evil contest |
| `gameplay/report.md` | M | *Area overview.* Write problems 2–5 as short sections over the component reports; name the model in the thinking-budget row |
| `discussion_evidence.md` | S | Add the section index; mark the answered §9 questions |
| `reasoning_failures/report.md` | M | Move the card-text share of the evil-cover result to roles; split the "levers tried" paragraph; fix catalogue slice 2 (`public` mode missing) |
| `role_sheet.md`, wiring census, `role_set` log | S | R11 change-log entry; "historical" banners |
| `agent_boundaries/report.md` | S | One sentence: the deduction engine is a payload consumer, with a link |
| `extraction/day_summary/report.md` (stays in `extraction/`) | M | Reconcile "66 summaries" with §6; name which tagger; fix the ledger/accusations contradiction |

### Memory campaigns

| Document | Size | Action |
|---|---|---|
| `memory_system/report.md` (from `store_progression.md`) | L | *Area overview.* The hub (§3.2) |
| v7 report (`execution_plan` + `v7_final`) | L | *Experiment report.* Merged report (§3.2). It leads with the method: the question, the power simulation, the pre-registration and its amendment, the signed endpoint; then the result; then the June loop runs as the history that made pre-registration necessary. The method is what the record defends; the null is its honest result. Repoint provenance to `execution_plan/data/`; D3 |
| `v8/report.md` | L | *Reference.* New report; update README status |
| `fine_tuning/report.md` | L | *Experiment report.* New, written as a training record, not a failure report: what each of the four trained tracks achieved (the retrieval reranker at NDCG@5 0.882 and its label-leak diagnosis lead; the ONNX benchmarking beside it), why each was held, and what remains untested. Deployment status, checked: both cross-encoders are implemented and trained in `training/`, but no code in `Agents/` or `server/` loads them, so neither is reachable from a game or the memory pipeline ✓ (the dedup pipeline names the prefilter "the planned swap-in … not yet wired in"; the live reranker is an LLM call). "Not in production" is stated as that, not as infeasible |
| `effectiveness/report.md` | M | Absorb the screening section's **findings** (memory's direction per faction at the decision level; the cheap-lever ladder), linking to `evaluation/evaluation_scopes/turn/` for the frozen-turn method rather than re-explaining it. In that section: "later proved to be model drift" → suspected; "a powered whole-game test" → the N=30 wording; check its "+17 / +23 pp win" row against the static-memory correction (win rate was the underpowered direction, not the verdict). Also: scope note (every game here ran at zero reasoning tokens); define terms; drift fixes |
| `ablation/report.md`, `strategy_adoption/report.md` | S–M | Dated status lines naming today's mechanism; the June forced-verdict screen as the step to today's verdict field |
| `v7_final/` side docs, `judge_validation_protocol.md`, v5 files | S | One-line status each |

### Memory pipeline

| Document | Size | Action |
|---|---|---|
| `dedup/report.md` | L | *Reference.* One present-tense account: the layered stack as it runs, evidence per layer with N, the merge path built but off, the incremental post-game pass built but off (freeze-old guard live, `created_at` fix open, not re-tuned on the current models; `incremental_convergence.md` stays in place as its diagnosis record), what is unmeasured. Gap table to the log; fold `README.md` and `batch_architecture.md` (whose "two-pass" is described wrongly) |
| `retrieval/report.md` | L | *Area report* (§3.3, D4) |
| `store_curation/report.md` | L | *Reference.* Today's two passes (credit pass, no model call; learning tick, never prunes ✓) with v7 as the design they graduated from; keep the pathology table; agenda and suite counts to the log. `tells.md` headed "v7 loop only": the served game loads no tell book ✓ |
| `discussion_tagger/report.md` | M | *Decision report.* Short record ending in the 2026-07-13 retirement; validation left to the llm_judge page. Moving it is a filing decision only: whether it appears in the write-up stays a separate call |
| `extraction/post_game`, `situation_summary`, `situation_dimensions`, halo case study | S–M | Point to the one home for the halo and the stage filter (§3.5); reconcile the cost figure with caching |
| `credit/read_tactic_credit_redesign.md` | S | Remove the bookkeeping sentences; date "current legacy scorer" |
| `caching/report.md` | M | §3.5 (the enforced retry and the 20-game break rate; where the schema mode is really set: a database row the code seed contradicts), §6 site default (now Haiku), post-game link |

### Measurement and infrastructure

| Document | Size | Action |
|---|---|---|
| `tracing/report.md` | L | *Reference.* Two run paths: batch (Langfuse trace + local sidecar + fingerprint) and served (replay events, prompt captures, Postgres checkpoints; eval cases only in Langfuse, no fingerprint). SDK internals and the 422 forensics to the log |
| `tracing/fingerprinting/report.md` | M | Re-verify the gap list: role prompts unhashed, a Claude game labelled with a Google backend, served games carry no fingerprint |
| `metrics/report.md` | L | *Decision report.* A dated record: how the nine-seat basket was chosen (48 → 11), and one paragraph on why the policy changed (rules first, owner 2026-10-24) pointing to `evaluation/metrics/`; §5 and §7 to pointers |
| `metrics/README.md` and data READMEs | S | Code pointers |
| `refactor/` three records | S | Dated status lines (and D6) |
| `model_drift/drift_surfaces_and_guards.md` (moving beside `variance_reduction_levers.md`) | S | Fix the audit's conclusion (on the fix list); mark "Immune: local fine-tuned models" as describing components that are not deployed (neither cross-encoder is wired, so the "the vendor can't move them" sentence must not be reused); dated status line |
| `evaluation/experimental_controls/report.md` §1 | S | Add the component map in two or three sentences, so the report answers "what can a provider change under us?": the seat model, the embedding model (most exposed and silent: an alias only), and the model-run helpers (classifiers, dedup judges, the summariser) |
| `evaluation/model_admission/report.md` "In short" | S | Add the selection premise (owner 2026-10-26): which models were tried was set by budget and the credits available at the time (Gemini credits, then Claude credits), not by a search for the best model; the checks ask whether a model is good enough and affordable, and catch a switch that would make play worse |
| `evidence/README.md` | M | *Area overview.* The top-level index and the owner's revision entry point; about 1,950 words, with stale rows (caching: "every in-game turn pays full price by decision"; selection: "gated by the memory-pipeline prompt freeze"; per_day_discussion: "PARKED"). Rewrite last (§5 step 6), once the layout is final: one row per component with its reference report, its one-line result with N, and its state (live / built and off / superseded) |
| `model_selection/report.md` (moving to `evaluation/model_admission/`) | S | Kept whole as a dated decision report, not merged: model admission covers only its method lesson in one sentence. Reader question: "within the budget available, which model held a seat well enough, and what did each cost?" Re-head "Current selection (2026-07-26)" as "July 2026 selection (nine-seat; superseded)"; "clearly the strongest table" → "strongest in the owner's reads". It stays the source for the cost-and-latency topic (block 96: one model per job by its binding constraint) |

---

## 5. Order

1. **The constraint fixes** (above) and D6, the `CLAUDE.md` freeze line and `refactor/eval_architecture_convention.md` §4, one commit. D6 goes first because every agent briefed on the repo reads the FREEZE line and will refuse to touch `evidence/`.
2. **The pilot:** `sequential_discussion/report.md` rewritten in place under the §0 rubric. You review it
   against the exemplars; the rubric is adjusted before the remaining rewrites are commissioned.
3. **Finalise the layout** (D1, D2, D5) with what the pilot taught.
4. **Moves**, one commit per area, links and operational paths updated, no prose changes.
5. **Rewrites and new reports by area:** gameplay → memory campaigns (the verdict homes first: hub, v7,
   effectiveness) → memory pipeline → measurement. Headless drafting in parallel within an area; I review
   each against the code for mechanism claims and against this list for scope, then you read the L items.
6. **Close out:** rewrite `evidence/README.md` as the top-level index (§4); mark each folder done in the map's folder walk (the ten `evaluation/` rows there are
   already done but still say pending).
