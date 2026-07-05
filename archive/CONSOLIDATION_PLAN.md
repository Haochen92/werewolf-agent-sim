# Consolidation & Write-up — Reading Plan

> **Working doc — temporary.** A reading guide + note-capture sheet for the evidence read pass.
> Delete (or fold into the write-up) when the consolidation is done. NOT portfolio content.
> Parked at root for discoverability — move it into `writeup/` or git-ignore it if you'd rather.

## ⭐ PER-FOLDER TREATMENT + SEQUENCE (the operating procedure, from `sequential_discussion`)

For **each** folder: **evaluate → propose a per-folder plan → user approves → EXECUTE the reorg → THEN
content-review.** Reorg runs BEFORE the review (gated on plan-approval) — never review a folder whose
structure is about to change. The plan evaluates three things:

1. **Distill the `.md` → the two canonical log types.** `experiment_log.md` = chronological **journey**
   (absorb scattered design docs / build trackpads / scratch `.md` into ONE; no laundering — keep every
   failure / decision / consideration). `report.md` = type-4 **how-it-works reference** (destination-first:
   orientation → guarantee → model → verify → case-study → criticality+freshness gaps; pull durable
   verdicts UP). Subfolder sub-studies keep their own `experiment_log`; verdicts surface up into the parent
   `report.md`.
2. **Placement & naming.** Does the container/subfolders belong here? Rename placeholders to accurate names;
   HOIST OUT misfits to their correct category, then EXCLUDE the hoisted content from the parent `report.md`
   (brief chronological pointer kept in the journey log only).
3. **Layout: root = ONLY `.md`.** Non-md → `scripts/` (.py) + `data/` (.jsonl/.log/results/transcripts).
   Propagate EVERY reference on a move/rename — hardcoded script paths (`OUT=`, `__file__` `parents[]`),
   cross-folder refs, `.md` links, external repo files, AND memory files; `git mv`; verify zero stale refs.

(The "three outputs" below is the *content-review* step #4 — it now runs AFTER the reorg, not as the trigger
for it.)

## What you're doing — per folder, three outputs

1. **QC the log** — the foundation everything else is distilled from. Is it coherent, internally
   consistent, and do the conclusions actually *follow*? These logs are LLM-authored: catch the
   **unrevised early errors that left a wrong conclusion standing**, and the contradictions. Decision rule:
   - **KEEP** the honest journey — what was tried, real failures/dead-ends, and claims you *revised*
     (shown as revisions, like the +0.556 retraction). This is the asset.
   - **FIX** wrong standing conclusions + contradictions — as a *visible* correction ("initially
     concluded X; corrected to Y because Z"), which fixes correctness *and* keeps the honesty.
   - **CLEAN** pure careless / LLM-noise with no journey value (it only signals "unsupervised").
   - Balance: not so messy it looks unsupervised, not so synthesized it looks machine-written —
     visible human QC is itself the signal.
2. **Distil the lessons → narrative** — what the folder contributes to its `writeup/` chapter
   (*why* + *what-found*) + any `docs/` cross-ref. (You can only distil correct lessons from a QC'd log.)
3. **Leave it clean-on-peek** — *flag* tidy needs, don't move yet (batch after review): cruft to
   delete · raw-data to tuck into a labeled subfolder · a status header if parked / exploratory / superseded.

**Contract:** evidence is FROZEN *as an honest journey — not as a freeze on errors.* Because these logs
are LLM-authored, the read pass is a **human-QC pass** (the keep/fix/clean rule is #1 under "What you're
doing"): correctness first, the honest journey preserved, pure noise cleaned, coherence improved where
poor. What you must NOT do: *launder* a log into hindsight-clean prose, *restructure* the taxonomy, or
*over-synthesize* into machine-perfect text (visible human QC is itself a signal). The log is the
foundation the write-up distils from, so its *correctness* matters most; the heavy *stylistic* polish
still lands in the writeup chapter, not the raw log. Jot findings on the `→ notes:` line under each folder. When a chapter's folders are
all read, draft that chapter (link into evidence for proof, into `docs/` for how-it-works), then hand
me the batched tidy flags and I'll execute the moves.

---

## Folder classification (builds the rename+split inventory)

As each folder is read, tag its notes line with **`kind:`** — the inventory for the deferred
`evidence/ → experiments/` rename + split (decided 2026-06-24; do once, after the full read-pass,
propagating CLAUDE.md + ~15 memories + docs/ in one move):
- **`kind: experiment`** — empirical study with an *uncertain outcome* (A/Bs, ablations, screens).
  Stays in the renamed `experiments/` (or `research/`). Treatment = freeze + light QC (journey logs).
- **`kind: record`** — engineering decision-record / postmortem, *no uncertain outcome* (bugfix,
  architecture decision, mechanism writeup). Belongs in `docs/` (how-it-works) or a `decisions/`
  ADR area, NOT among experiments. Treatment = refine for understanding/organization (report-shaped).
- **`kind: mixed`** — flag if a folder carries both (note which artifacts split which way).

## Order: foundations → memory → eval → v7  (light → heavy)

### Ch. 1–2 · The game + game design & engine   ← START HERE (tomorrow's scope)

- **`role_set/`** — 3-faction lean-eval casting, abstain voting, SK-as-keystone. *Look for:* the
  two-casting-targets split (lean-eval vs rich-ship), cause-discipline (sequential fixes discussion,
  not roles), the per-namespace density argument, balance-deprioritized-because-paired-A/B.
  *Tidy:* clean; optional — tuck `smoke_run*` → `smoke_runs/`.  *(calibrated already)*
  → notes: **kind: TBD** (calibrated earlier, not yet kind-classified — likely `record`/design-decision
  with supporting smoke-runs, i.e. borderline `mixed`; confirm on a closer read).
- **`sequential_discussion/`** (+ `gate/`, `prompt_boundary/`) — concurrent→sequential discussion (Phase A#1),
  the silence gate, the prompt/memory boundary. *Look for:* the coordination-failure diagnosis, the
  stateless scheduler, prompt=how-to vs memory=what-signals-mean. *Tidy:* 9 `.py` = study code (stays);
  check for `__pycache__`.
  → notes: **kind: MIXED — breaks "one folder = one kind" (decided 2026-06-24, three-layer model).**
  The CONTAINER is an **architectural decision record** (concurrent → sequential scheduler) — justified by
  *design reasoning* (§2 "why concurrent fails"), NOT by an experiment; you can't falsify an architecture
  choice with a smoke test, only inform it. Its evidence standard = "is the rationale sound + tradeoffs
  named," and it gets *revisited when constraints change* (so it must carry alternatives-considered).
  Nested under it: (a) **sub-design decisions** (the 5 locked points + the silence rule) — also reasoning,
  also revisited-not-rerun; (b) **experiments** that attach to *specific sub-decisions* to de-risk/select
  them (Smoke 1 speech-act capability, Smoke 2 standalone-novelty, **Smoke 3 temp-sensitivity = a kept NULL
  result**, **Smoke 1b 1-D→2-D = data showed 1-D lossy**, **Smoke 4 folded-novelty FALSIFIED**) — standard
  = "probe valid / reproducible / confound named," *re-run or invalidated when doubted*; (c) the **gate
  A/B** = hybrid: experiment in *form* (rubric + transcripts + deterministic metrics) but its *job* is to
  **ratify the architecture decision** ("does sequential clear the bar") — an acceptance test, which is why
  it's report-shaped while the smokes are log-shaped. **Chapter spine (adopt verbatim): "an architectural
  decision (concurrent→sequential), supported by a chain of experiments, ratified by a gate."** Container
  → `decisions/` in the deferred split; smokes = experiment-evidence; gate = acceptance-report. Resolution
  for the rename: the **writeup leads as the decision + cites the rest as evidence**; the evidence folder
  stays physically intact (don't split the dir).
  - **⭐ Two precision points the spine MUST keep (they ARE the seniority signal):** (1) Smoke 4 killed a
    *sub-design* (fold novelty into the situation-summary call), NOT the architecture — the scheduler
    absorbed the hit by going deterministic. "I let data kill my design" = "a load-bearing *component*
    died and the architecture was robust to it." (2) **The story runs PAST Smoke 4.** Smoke 4 dropped
    *folded self-judged* novelty; post-build live runs (2026-06-04) surfaced proactive echo = empirical
    proof the *function* was still needed; the fix (b9c3b30) re-added novelty as a **disinterested external
    judge** — explicitly the Smoke-2/3 form, explicitly NOT the falsified self-judgment. Smoke 4's finding
    ("self-judgment is the problem, not novelty itself") is **load-bearing twice** (on the way down AND
    back up). The chain spans before *and* after the build; the chapter must run through the
    re-introduction, not stop at the falsification.
  - **⚠️ NARRATIVE CAUTION:** the taxonomy is the reader's *filing system*; the chapter's *story* is a
    LOOP (design-by-reasoning → falsified-by-data → redesign → retune-by-data). The "data overruled my
    design" signal exists ONLY because it was a loop — do NOT let the clean 3-layer labels iron the
    chronology into a waterfall where experiments politely confirm a pre-made call. Same hazard as
    "don't launder into hindsight-clean prose," at the structural level.
  - **QC FIX for §3.3 (plan.md) — distinguish WHICH LAYER moved + reasoning-vs-data.** `plan.md` §3.3 still
    shows the *as-designed* weighted-score scheduler (`score = pressure + intent − debt + …`) + a live
    novelty gate; both were superseded. Mark it: the weighted score → dropped by a later **design pass**
    (Stage 2 reactive/proactive); the novelty gate → dropped by an **experiment** (Smoke 4). A superseded
    *design decision* reads differently from a superseded *experiment* — say which, so the §3.3 reader
    isn't confused. **APPLIED 2026-06-24:** plan.md got a top STATUS banner (title added; distinguishes
    §3.3 = design-pass supersession vs §3.4/§3.8 novelty = Smoke-4 experiment supersession; flags the
    "novelty returned as external judge, not folded" form-fix) + 5 inline ⚠️ pointers (§3.3 score, §3.4
    silence, §3.8 ping-pong terminator, §4.1 NoveltyChecker/component drift, §4.4 Phase-2 wrong-in-form).
    Body reasoning untouched — §2 diagnosis + architecture rationale stand (freeze + visible-correction,
    log-class treatment).
  - **kind: was "experiment" (WRONG — flattened the container); corrected to MIXED above.** **READ + QC'd
    2026-06-24** (first pass): strong honest log, extensive visible supersession markers (Smoke-4, 1-D→2-D,
    budget 1→3, K total→consecutive); arc lands → A/B gate PASSED, Phase A#1 CLOSED (gate/experiment_log.md).
    **QC FIX (1) — APPLIED 2026-06-24:** stale top "READING GUIDE / CURRENT STATE (2026-06-03)" header
    ("Next = BUILD" while workstream built+tuned+CLOSED 2026-06-05) → one-line CLOSED banner added above it.
    Tidy: clean — no pycache, study scripts + colocated *_results.jsonl stay; gate/ + prompt_boundary/
    self-contained. Folder-name open-decision = settled (stays sequential_discussion). Writeup ch.2 lessons:
    cause-discipline (structural→scheduler not prompts); falsification-as-asset; stateless-by-recompute
    (day_channel = SoT → resume-safe + unit-testable); live-runs-earn-keep (domination + proactive-echo
    only visible in vivo).
  - **`phase0_build_checklist.md` — LABELED + consistency-verified 2026-06-24.** Relabeled honestly as an
    **agent build-trackpad frozen ~2026-06-04** (was pretending to be a human-owned spec); left
    un-laundered (chronological artifact). Verified its concrete claims against the repo: 5 drifts are
    TRACKED (checklist just froze early — opener_floor 1→3 `c1c4dc2`; recursion_limit formula `1ea5c9a`;
    novelty re-added as external judge `b9c3b30`; discharge broadened to `mention` `5672e22`; firing_reason
    now persisted on DayChannel `1cc1f4c`) + cosmetic naming drift + all pre-reorg file:line refs stale.
    Banner table records each with its tracking source.
  - **⚠️ CODE FLAG (not a doc issue) — `reengagement_cooldown_multiplier` default = 3, but recorded intent
    = ×1.** Born at `default=3` in `23959b2` (2026-06-04), never 1.0 in git; the same-day log note +
    checklist + the field's OWN comment all say ×1 ("one full table"). Consequence: `M = ceil(3·N) ≈ the
    day's utterance cap (ceil(3.0·N))`, so a directed pair must sit untouched ~the whole day before its
    K-count resets → the **"consecutive, not total-per-day" K-reset (the whole point of `23959b2`) rarely
    fires in-day** — detuned ~3× from intent, partially reverting the feature the commit added. Looks like
    a slip (`3` vs `1`): exhaustive search found NO evidence exploring/justifying `3.0` — every record
    (log:887, checklist:121, the field's own comment, commit `23959b2`'s "consecutive" intent) says ×1;
    gate/experiment_log.md (future-work #5) only flags these knobs as hand-set + sweep-deferred (i.e. never validated → how the
    slip survived). **FIXED 2026-06-24 → `default=1.0`** (`Agents/game_config.py:55`); comment already said
    "one full table" so now consistent; 22/22 `test_scheduler.py` green (no test pinned the default — they
    pass `reengagement_cooldown` explicitly). UNCOMMITTED.
  - **✅ CONSOLIDATION COMPLETE 2026-06-24.** Final structure = **2 canonical docs + 2 subfolder logs**:
    `report.md` (type-4 how-it-works; leads with a parallel→sequential motivation crediting parallel's
    merits) + `experiment_log.md` (chronological journey; absorbed the old `plan.md` + `phase0_build_
    checklist.md`) · `gate/experiment_log.md` (was `gate/report.md`; reframed as the study record, durable
    verdict pulled up into `report.md` §3–4) · `prompt_boundary/experiment_log.md` (kept). **Deleted** (git
    history preserves): `plan.md`, `phase0_build_checklist.md`. Review-feedback applied (checkpointer tense,
    echo-guarantee softened, self-grade cut, persona/FT future-work added, v5→v6_1 + roles-shipped currency,
    cooldown finding de-buried). Content-preservation diff run + 4 considerations restored (human
    integration, encoder-novelty, stateless-vs-stateful, storage-vs-display). **UNCOMMITTED** — code
    (cooldown fix) + evidence-doc edits both pending a commit.
- **`refactor/`** — structure audit + eval-architecture decision record (the 6/6–6/10 `Agents/` reorg).
  *Look for:* "the real gap was test coverage, not layout"; the reorg rationale; the
  evaluation=code / evidence=record charter.
  → notes:
- *(infra — light; fold into ch.2 or a docs note):* `caching/` (cache-layout debt), `prompt_versioning/`
  (runtime_fingerprint), `agent_boundaries/` (payload-gating leak checks).
  → notes: **all three kind: record** (engineering decision-records / mechanism writeups, no uncertain
  outcome → strong candidates for `docs/` HOW, not `experiments/`). `agent_boundaries/` **REFINED
  2026-06-24**: `experiment_log.md → report.md` (git mv); restructured guarantees-first (contract →
  4-layer model → verify → 109-flag case study → gaps) + pipeline orientation; **fixed 2 internal
  contradictions against the artifacts** — (a) vigilante_results leaked to the *vote* path too (not
  discussion-only); (b) the 109 = 76 wolf-flag-lines (38 inputs ×2) + 33 investigator, with vigilante
  =0/109 (no checker yet, added `8008623`). §1 contract + §2/§3 tables = the docs/HOW source.
  Further refinements APPLIED: Send-vs-compiled-subgraph note (layer 1); value-vs-sentinel mechanism
  (§3, why a flag ⟺ payload crossed); root-cause = misread of LangGraph schema-filtering (real only at
  typed channels + parent→child compiled-subgraph boundaries, NOT the Send-into-node path); wolf_channel
  corollary reframed as game-scoping aside (NOT a leak boundary, no check enforces it). ⚠️ Editor-clobber
  incident: disk reverted to pre-restructure draft mid-session → reconstructed in one atomic Write.
  `caching/` + `prompt_versioning/` not yet read.

### Ch. 3 · Episodic memory system   (the biggest — multi-session)

- **`memory_system/`** — THE A/B findings: `effectiveness/{paired_ab, decision_replay, v6_sp_ab}`,
  `ablation`, `augmentation`, `strategy_adoption`. *Look for:* town-helps / wolf-SK-null, net-horizon,
  the decision-replay screening layer, the v6 SP A/B.  *(114 files — the core results)*
  → notes:
- **`extraction/`** — extract pipeline v5→v6 (per-role fan-out → per-cell).  *(102 files)*
  → notes:
- **`dedup/`** — online / batch / gate-partition dedup mechanism, v5→v6.  *(51 files)*
  → notes:
- **`retrieval/`** — filtering / reranking / capacity / context_eval.  *(28 files)*
  → notes:
- **`phase_b/`** — dimension-build screens (criticality, forced-schema).
  → notes:
- *(supporting):* `extraction_selection/` (net_verdict halo), `model_drift/` (Vertex drift),
  `prompt_claims_audit/`.
  → notes:
- **`fine_tuning/`** — parked ML thread (CE reranker, dedup classifier, embedding, bandit).
  *Tidy:* add a status header — "exploratory, parked — see X for what shipped."  *(174 files — skim)*
  → notes:

### Ch. 4 · Evaluation rigor

> ⭐ **2026-06-27 — EVAL SOURCE-MAP + RELIABILITY INVENTORY built → `evidence/evaluation/source_map.md`**
> (provisional eval-hub folder; the judge-half companion to `tracing/`). Maps the whole `evaluation/`
> codebase + reliability-stamps every method (✅/🟡/⚠️/🔴/⏸/🔍). Spine = end-to-end A/B → component
> funnel → metrics+methodology. Has a v7-trust scorecard + a VERIFY-IN-CODE-LATER list. **Read it before
> drafting the eval `report.md`.** Key: wolf-memory null may be a *measurement gap*, not a ceiling.

- **`metrics/`** — de-lucked outcome proxies + the win-monotonicity validation (the validated basket).
  → notes:
- *(supporting):* `stats_used/` (untracked — commit it), `dedup/golden_eval/` (folded in from the former top-level `dedup_golden_eval/`), `eval_improvement/`,
  `tracing/` (Phase A#3 eval-capture pattern).
  → notes:

### Ch. 5 · Frontend — later (after the build).

### v7 · the compounding loop   (heavy — its own session)

- **`v7_final/`** — the loop design + the honest negative findings + the invalid-run post-mortem.
  *Tidy (heavy):* tuck run-data (`smoke_*`, `town_only_*`, `v2_full/gen*_store/`) → `runs/`; mark the
  INVALID runs; drop `__pycache__`. The CODE-review surface is `v7_final/review_map.md` (Folders +
  design-lineage table).  *(462 files)*
  → notes:

---

## Tomorrow, concretely
Read ch.1–2 folders (`role_set` → `sequential_discussion` → `refactor`, + skim the infra trio), jotting notes
above. That's a digestible first session and gives the opening of the write-up. Ping me to draft the
chapter from your notes, to dig into any folder, or to execute the tidy flags once you've reviewed them.

---

## 📇 APPENDIX — markdown file index + 6-category proposal  (captured 2026-06-27; revisit after the read/cleanup pass)

> **Why this is here.** Decided 2026-06-27: do a one-by-one **read + quick-cleanup pass** first, defer the
> reorg. This appendix freezes (a) a per-`.md` index of the 11 folders swept that day, and (b) a categorization
> proposal + its verification, so we don't re-derive either. Scope: **markdown narrative only** (the plan's
> `(N files)` counts include scripts/data; this is the prose subset). Covers 11 folders / 44 `.md`. NOTE the
> overlap with the chapter spine above: `prompt_boundary/` already consolidated; `prompt_versioning/` tagged
> infra→`docs/`; the rest map to Ch.3 (memory) and Ch.4 (eval-rigor).
>
> **UPDATE 2026-06-27 — tracing CONSOLIDATED (capture vs judge split).** `evidence/tracing/report.md`
> written (how-it-works, capture half only; Langfuse 3.14.6). `eval_improvement/` **merged into
> `evidence/tracing/implementation_notes/`** (it's capture-side instrumentation) alongside tracing's own
> `experiment_log.md` + `smoke_*.log` — so the index entries below for `tracing/` + `eval_improvement/` are
> superseded by `evidence/tracing/{report.md, implementation_notes/*}`; the `eval_improvement/` folder is
> removed. Establishes the operating split for cat ②/③: **capture (tracing) vs judge (evaluation system =
> metrics/ + memory_system eval reports + judges).**

### (a) Per-file index — what each `.md` is

**eval_improvement/**  *(→ Ch.4 / cat ② observability-capture · kind: record)*
- `ISSUE_frozen_set_fetch.md` — Langfuse 422 on heavy traces; fix = local `EvalCaseSink` (primary) + `trace.get`→name-scoped `get_many` (secondary). Shipped 2026-06-11.
- `frozen_set_fetch_explained.md` — plain-language companion; generalizes "emit eval cases locally, tracer = secondary archive."

**extraction/**  *(→ Ch.3 / cat ① memory-system · kind: experiment; quality=record-ish)*
- `day_summary/experiment_log.md` — day-summary extractor iteration; flash-lite+medium-thinking matches 3.5-flash; v4b structured output.
- `quality/report.md` — quality across 48 games; per-role beats single-pass; 2 judge bugs fixed (epistemic scope, specificity field); 3.5-flash best all-rounder.
- `situation_summary/experiment_log.md` — golden-label retrieval eval (NDCG); golden 0.783 vs pipeline 0.671; "Core dilemma" 5th dim; villager weakest.
- `situation_summary/report.md` — model comparison; flash-lite-default kept; thinking-budget hurts flash-lite; 2.5-flash role-perspective problem.

**extraction_selection/**  *(→ Ch.3 supporting / cat ① · kind: experiment)*
- `experiment_log.md` — `net_verdict` = outcome halo (not per-action causal); anchor selection w/ deterministic leverage; don't turn-scope. (2026-06-17)

**metrics/**  *(→ Ch.4 / cat ③b scoring · kind: experiment/record)*
- `experiment_log.md` — v0→v1→v2 metric design; v2 = outcome proxies + de-luck + monotonicity-validated. Impl 93b1137.
- `proxy_win_monotonicity.md` — validates proxies vs win (50 games); town basket |r|≈.55–.65; investigator NOT validated.
- `deceiver_metric_refinement.md` — wolf/SK signals (180 v6ab); wolf concealment-dominated; `sk_killed_wolf` survives; SK-lynch timing = keystone.
- `town_metric_refinement.md` — 3-faction refinement; `power_roles_killed_by_evil`; healer bug; `vigilante_wolf_kills_rate`; `investigator_find_to_lynch` (+0.396).
- `discussion_scoring_plan.md` — plan to score discussion; Phase 1 null (lead-vs-blend r=−0.093); Phase 2 tagger pending.
- `score_tier_design.md` — typed `GameScore` projection over 57 fields; COMPUTE-all vs SCORE-one-per-axis. Not impl.
- `variance_reduction_levers.md` — ⚠️ **MIS-FILED**: content is cat ④ experiment-design (pairing/CUPED/bootstrap), not ③b.

**model_drift/**  *(→ Ch.3 supporting / cat ④ experiments · kind: record)*
- `drift_surfaces_and_guards.md` — flash-lite alias drift; interleave arms; embedding model most-exposed; guards + canary. (2026-06-12)

**phase_b/**  *(→ Ch.3 / cat ① + ④ · kind: mostly plans + 2 screens)*
- `plan_review.md` — ⚠️ **ORPHAN**: cross-cutting Phase-B roadmap (labelling tracks; Phase C deleted).
- `dimension_schema_build_spec.md` — ① per-cell situation-standards schema (11 cells); hard-gate rule; state-not-prescription.
- `dedup_clustering_and_sp_extraction_plan.md` — ① dedup-as-predicate (cluster/merge/synth gates); `net_verdict` in merge gate; SPs synthesize-not-merge.
- `procedural_memory_experiment.md` — ① two-tier memory (obs vs SP); channel was config-disabled; replay-experiment design.
- `v6_full_store.md` — ① store build record: 919 obs, 17 ns, 11 cells; night-cell player-ID defect deferred.
- `v6_wide_migration_roadmap.md` — ⚠️ borderline orphan: v6 consumer-migration rollout plan.
- `criticality_screen/experiment_log.md` — ④ retrieval-conditioning screen; NOT robustly demonstrated → don't wire live.
- `forced_schema_screen/experiment_log.md` — ④ forced per-memory applicability; v6 neutralizes v5 "forcing hurts"; ⑤ prompt-body coverage fix (0.27→0.97).

**prompt_boundary/**  *(→ Ch.2, ALREADY CONSOLIDATED 2026-06-24 / cat ⑤ · kind: experiment)*
- `experiment_log.md` — prompt-vs-memory boundary; removed tone-policing pseudo-strategy; STOCK/POLICE markers down.

**prompt_claims_audit/**  *(→ Ch.3 supporting / cat ⑤ · kind: experiment)*
- `experiment_log.md` — investigator "conceal" FALSIFIED; wolf "blend" VALIDATED; targeted investigator rewrite + A/B. (2026-06-17)

**prompt_versioning/**  *(→ Ch.1–2 infra, kind: record → `docs/` / cat ⑥ provenance)*
- `prompt_versioning_analysis.md` — `runtime_fingerprint` (git SHA + bundle hash + model IDs); floating alias pinned.
- `rendering_layer_bundle_transition.md` — content-neutral bundle-hash change record (formatters moved into `prompts/`).

**memory_system/**  *(→ Ch.3 / cat ① + ④ — THE 1↔4 seam · kind: experiment)*
- `store_progression.md` — ⚠️ **SPINE**: narrative across 8 store versions (4-phase constraint migration). Sits above categories → candidate for `writeup/`.
- `effectiveness/report.md` — does memory help; Batch A 70→97% (p=.012) NOT replicated Batch B → paired A/B = determining.
- `effectiveness/v5_baseline_proxy_analysis.md` — pilot opposite direction (town −32pp); raw uncurated retrieval. Directional only.
- `effectiveness/v5_seeding_plan.md` — ④ seeding/seedability/cost; role-draw fix; generational stores.
- `effectiveness/decision_replay/experiment_log.md` — ③a replay instrument + ① results; town day-2 helps; cheap-lever ladder dead-ends.
- `effectiveness/decision_replay/report_screening_layer.md` — frames screen's role (triage + convergence, not verdict).
- `effectiveness/paired_ab/experiment_log.md` — KEYSTONE: epoch-drift discovery, raw/all-on/rerank arms, 6-step null ladder, net-horizon, Phase-B crisis.
- `effectiveness/paired_ab/nethorizon_design.md` — ① net-horizon outcome-framing store variant (freeze-clean).
- `effectiveness/paired_ab/report.md` — results table; town helps all arms (rerank-town +33pp p=.013); wolf/SK null.
- `effectiveness/paired_ab/report_nethorizon.md` — net-horizon arms; SK differential confirmed, wolf flat; Pareto-safe → adopt.
- `effectiveness/paired_ab/town_echo_read.md` — (b) followed-but-worse, not ignored; per-namespace framing rationale.
- `effectiveness/v6_sp_ab/experiment_log.md` — v6 strategy-points A/B; SP-alone harmful, obs+SP synergy; content reinforces capped play.
- `ablation/report.md` — obs vs SP ablation (120 turns); no sig diff → observations-only adopted (cheaper).
- `augmentation/experiment_log.md` — namespace augmentation; merge barely fired (stale prompt on verbose extraction).
- `strategy_adoption/judge_validation_protocol.md` — ③a LLM-judge calibration protocol (Bucket B); deferred.
- `strategy_adoption/report.md` — adoption tracking (retrieved/used); v2 schema-reorder lifted accuracy AND action quality (⑤ finding).

### (b) Categorization proposal + verification

**User's 6 categories (2026-06-27):** ① Memory system (store versions ← extraction changes via shared *situation standards*; sometimes synthesis, e.g. v7) · ② Tracing/observability (Langfuse, data/score capture) · ③ Evaluation = ③a instruments (action-replay / labelling / LLM-judge pipeline) + ③b scoring/metrics (proxies, judge criteria) · ④ Experiments + the fair-run problems & how the experiment system improved · ⑤ Prompt-engineering techniques · ⑥ Provenance (agent-managed).

**Verdict:** absorbs ~30/44 cleanly. The leaks are structural, not random:

- **Seam 1 — ① Memory vs ④ Experiments don't separate at file level.** The whole `effectiveness/` subtree (11 files) + `ablation` are BOTH "the memory result" and "the experiment" (e.g. `paired_ab/experiment_log` holds the verdict *and* the drift/bug/epoch methodology). ~12 files on this seam.
- **Seam 2 — ③a instruments are written up *inside* their results.** `decision_replay`, `ablation` (action-replay), `situation_summary` (golden-label), `eval_improvement` (capture), `judge_validation_protocol` — tool design + first findings co-located, so ③a can't be a clean folder.
- **Orphans (no home in the 6):** `phase_b/plan_review` (cross-cutting roadmap), `v6_wide_migration_roadmap` (rollout plan), `store_progression` (the narrative spine, above all buckets), `metrics/variance_reduction_levers` (mis-filed = ④), `strategy_adoption/report` (triple-homed ①+③a+⑤).
- **Reframe that closes the leaks:** ①②③⑥ are **content domains**; ④ and ⑤ are **cross-cutting layers**, not peer silos. Make ④ a *methodology* writeup (drift + variance + seeding + bug/epoch lessons pulled from the experiment logs) and ⑤ a *techniques* writeup that **cites** findings in their home folders. Then effectiveness splits cleanly (results→①, method→④) and prompt-eng stops scattering (theme, not folder).

**Reconcile-later deltas vs the chapter spine above:** spine puts `tracing/` + `eval_improvement/` under Ch.4 eval-rigor (supporting) whereas the 6-cat scheme makes ② its own category; spine files `model_drift/` + `prompt_claims_audit/` as Ch.3 "supporting" whereas 6-cat puts them in ④/⑤; spine already routes `prompt_versioning/`→`docs/` (= ⑥). Pick one lens (or map 6-cat → chapters) when we resume the reorg.
