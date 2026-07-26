# Phase B — updated plan review (2026-06-12)

Status: **plan record**, agreed in-session 2026-06-12 (post paired-A/B close + net-horizon
differential). Supersedes the Phase B sketch in the ship roadmap; the roadmap memory points here.
This is a planning artifact, not an experiment record — execution will produce its own
`evidence/<experiment>/` folders per convention.

## What changed above Phase B

- **Phase C (standalone big-N win-rate A/B) is DELETED.** The headline effectiveness result is the
  Phase A paired A/B suite + net-horizon differential (`evidence/memory_system/effectiveness/paired_ab/`):
  town +17/+33/+23pp; wolf/SK harm diagnosed → myopic-framing fix → SK harm removed. Rationale:
  (1) rerank ≈ raw → shipped config ≈ raw observations-only top-5, so the CE-reranker work is
  methodology depth, not a live-path change — nothing new for a big A/B to measure; (2) epoch drift
  (unpinnable flash-lite alias) makes any big-N number fragile and unreproducible — the durable
  asset is the method, not the point estimate.
- **Phase B is therefore re-framed**: from "labelling that gates the keystone measurement" to
  "component-measured optimization + the labelling/training methodology capstone." Its value is
  store quality + the portfolio story, measured at the level where each change acts.

## Preconditions and ordering (locked)

1. **Net-horizon N=30 verdict** (arms running). If adopt → **full-store rewrite pass (all roles)**
   + **town consistency shot** on the same seeds, run IN-EPOCH with this week's baseline
   (a null town result is a PASS — it is a regression check on a role family that already benefits,
   not a hoped improvement). + adherence echo-read on the nh sidecars + investigation write-up.
2. **Rewrite BEFORE dedup re-tune.** Decisive reason: dedup tuning is a labelling exercise and you
   label on final content — golden sets and merge-prompt calibration condition on the entry text
   distribution, which the rewrite changes for every entry ("label once on stable v5", in
   miniature). Also mechanical: the merge prompt can't support `composed_outcome` fields that don't
   exist yet. Cost of this order = a few wasted LLM calls rewriting entries dedup later merges
   (~431-entry store, trivial). Cost of the inverse = merges decided on stale text + a golden set
   that no longer describes the store.
3. Game-level instruments are reserved for the two cases below (targeted arms, freeze gate);
   everything else in Phase B is measured at component level.

**⭐AMENDED 2026-06-12 (nh verdict locked): item 1's "full-store rewrite (all roles)" is
SUPERSEDED by PER-NAMESPACE framing adoption** — town→raw store (validated; nh showed no benefit
anywhere + directional harm), SK→net-horizon (harm metric recovered: SK-lynched 0.80→0.633 ≈
baseline 0.60), wolf→OPEN (nh did NOT fix the day tell — elim rate 0.227→0.292→0.333; night
benefit retained → the queued night-only arm is the live question). Consequences:
- **No town rewrite, no town regression arm** — town store untouched; the failed nh_town arm is
  the evidence FOR the per-role config (also an epoch casualty — see
  `evidence/model_drift/drift_surfaces_and_guards.md`).
- **Two extraction-prompt families** routed per role-family (per-role fan-out already supports;
  adoption = routing flag + one-time shipping-store assembly with provenance). Maintenance cost is
  real: every extraction touch happens twice.
- **Track-2 golden sets + merge prompt must cover BOTH entry formats**; the verdict-aware merge
  key applies only to nh-format namespaces. Track-1/CE gold samples both formats. Also: the dedup
  **similarity thresholds were calibrated on one text distribution** — nh entries score in a
  shifted distribution → per-format threshold validation is mandatory, not optional.
- **⚠ Adherence semantics INVERT for negative-verdict nh entries** (track 3a/3b): a net-negative
  memory recommends AVOIDING its approach — following it is the failure, overriding it is correct
  application. Echo-read + applied/overrode/ignored labels must be verdict-aware for deceiver
  sidecars or they score backwards. (Once handled, `net_verdict` makes nh adherence EASIER to
  judge mechanically than raw outcome prose.)
- **Asymmetric labelling investment (2026-06-12):** two corpora ≠ two equal investments — depth
  follows measured value. Town corpus = full treatment (CE gold, relevance, quality audit).
  Deceiver corpus = minimum-to-operate (dedup goldens + verdict-aware adherence fix); defer
  relevance/CE depth until deceiver memory shows value worth optimizing (night-only arm is the
  trigger). Mitigations that keep cost ~1.2-1.3×, not 2×: retrieval/dedup never cross namespaces
  (no mixed-format pairs anywhere); `situation`/`approach` fields are format-identical (relevance
  labels mostly format-agnostic); batch labelling sessions by corpus; separation halves the blast
  radius of future framing changes. Rationale for keeping deceiver memory ON despite null outcome
  effects: gameplay variety + corpus generation for distillation/track-3/bandit follow-ups
  (memory-off deceivers stop producing the data the roadmap consumes); outcome harms = null at
  measured power, diagnosed raw-SK harm removed by nh.
- **Within-town per-role framing is ASSIGNED, not measured** (per-role arms are below the
  measured detection floor — ~0.18 vote-acc at N=30, see model_drift variance constants).
  Pre-registered assumption: framing follows deception exposure (net-horizon fixes
  immediate-vs-net divergence, a deceiver property; town's immediate outcomes are unconfounded).
  The freeze-time gate is the catch-all for unpredicted within-town exceptions.

## The three labelling tracks

### Track 1 — retrieval relevance (existing hardened methodology)

- **Unit**: (runtime situation summary, retrieved entry) pairs. Query = the situation summary the
  enrichment pipeline generated at decision time. Labels = pure-Q relevance (judged from query text
  alone; two-gold blinding, progressive labelling, acceptance gates — the
  `project-context-based-retrieval-eval` design, unchanged).
- **Source**: eval-case sidecars (`batch_results/eval_cases/<arm>/<game_id>.jsonl`) — case
  extraction is a query, not a pipeline run.
- **Sequencing**: AFTER the rewrite (labels condition on entry text); ideally after dedup lands
  (membership churn), though pair-level labels survive if both sides survive.
- **⭐Rider — entry-quality flag**: while reading each entry for relevance, one extra label:
  `fine / misleading framing / wrong lesson`. This is the **store audit** (defect detection), the
  only place in the funnel where a human reads store entries one at a time. It is NOT an
  extraction-function eval (see below). Justification: the myopic-framing entries were
  non-duplicate, highly relevant, and faithfully applied — they pass every other track; only a
  reading human catches them.
- **Output**: CE retrain gold (~130-case pure-Q set per the deferred plan) + store defect rate.

### Track 2 — dedup classifiers (two golden sets)

- **Online dedup**: KEEP / DISCARD only.
- **Batch/pro dedup**: KEEP / DISCARD / MERGE. (REPLACE/DIFFERENTIATE are dead ops everywhere —
  per the incremental-convergence decision, `evidence/dedup/incremental_convergence.md`.)
- Candidate pairs generated by semantic-retrieval match (the established ground-truth rule for
  same/different situation). Known starting point: both layers currently UNDER-fire on verbose
  per-role v5 output; merge prompt is stale for dims-embedded-in-situation prose and must gain
  `composed_outcome` support. One package: re-tune + fresh golden set + prefilter-CE.
- **Most tightly gated on the rewrite** (its labels and merge prompt read final entry format).
- **⭐Batch-merge redesign under net-horizon (agreed 2026-06-12).** Online dedup is unaffected
  (keep/discard on the composed blob, never merges — v5_0_nethorizon was built through it
  unchanged). Batch merge gains a verdict-aware key:
  - **Merge key = situation + approach + `net_verdict`.** Same situation/approach but different
    net verdict = NOT a duplicate — it's the contrast that teaches context-dependence, and
    situation-only retrieval co-retrieves both on the same query by design. Merging would
    collapse exactly the signal net-horizon built. Same verdict on all three = true duplicate.
    Different immediate response / same net verdict = mergeable (the lesson is the net outcome;
    verdict dominates). Contrast pairs may be noted in metadata — do NOT build linking
    infrastructure.
  - **Metadata aggregation (apply-layer code, freeze-safe, can be specced early):**
    `observation_count` → sum; `net_verdict` preserved (same-verdict-only merges, no "mixed"
    fudge); per-game win/loss provenance → aggregate into a rate ("appears in N games, role won
    M") — strictly more useful than the per-game bool.
  - **Under-fire fix:** feed the merge prompt the STRUCTURED fields (situation / approach /
    immediate / impact / net_verdict), not the prose blob — compare on the right dimensions
    instead of drowning in verbose prose.

### Track 3 — application / decision quality (the per-decision funnel)

Split by cost, all labels **outcome-blind** (never show the labeller the game result):

- **3a. Adherence — semi-mechanical, large-N, cheap.** For discrete decisions (votes, night
  targets): does the action agree with what the retrieved memory recommends? The nh echo-read is
  the prototype. No judge needed for the bulk; LLM only for ambiguous mapping.
- **3b. Application label — `applied / overrode-with-stated-reason / ignored`.** Keeps adherence
  separate from correctness: overrides can be RIGHT (the wolf 3v2 case), and the player_5 case is
  "overrode-with-reason, debatable quality" — a single used/not-used binary mangles it.
- **3c. Decision quality — sampled, judged.** Was the action defensible given the information
  available? LLM-judge with human-determined rubric + human spot-check layer (judge has a known
  information-gain blind spot — never judge-only). Agent self-report (`updated_strategy`, or an
  explicit "which memory did you use" output) is **pre-fill, not truth** — post-hoc
  rationalization-prone; progressive labelling (model pre-labels, human verifies, disagreement
  rate decides when to stop) is the pattern.
- **Sequencing freedom**: 3a/3b can start NOW on existing arm sidecars — they judge behavior that
  already happened against the memories actually injected; store-version churn doesn't invalidate
  them.
- **Bonus harness**: single-decision **replay** (same situation + same memories → regenerate
  decision) = the cheap testbed for the wolf memory-injection wrapper. Iterate wrapper wording on
  replayed decisions at pennies each; pay for a game-level arm only once a wording moves replay
  adherence. Turns the wrapper stretch item from "$8 per guess" into "$8 to confirm the winner."

## Extraction-level evaluation — DECISION: retire as a standing track, keep as parked diagnostic

The existing judged extraction stack (`evaluation/src/judges/extraction.py`,
`per_role_extraction.py`, `pairwise_extraction.py` + experiment runners) is NOT a Phase B track:

- **Text-level quality does not predict behavioral impact (the decisive reason).** Free-text
  quality CAN be gold-anchored — pairwise preference labels (A vs B from the same transcript)
  work fine, and `pairwise_extraction.py` already exists. But a pairwise gold set would have
  PREFERRED the myopic-framing entries: specific, well-attributed, fluent — they read as model
  extractions while poisoning SK play. Labellable and misleading is worse than unlabellable.
  The only measurement that has ever resolved an extraction question here was behavioral
  (the net-horizon differential).
- **No decision for the score to inform.** Extraction-prompt changes are rare deliberate events
  (one in project history) and get targeted game arms when they happen, because the question is
  always behavioral. A standing score that changes no decision violates the frozen
  "no machinery that changes no decision" rule.
- Rubrics are already stale post-composed_outcome and churn with every schema touch.

Detection coverage is replaced by: **track-1 quality-flag rider** (human reads entries) +
**free descriptive coverage stats** (per-(role,phase) namespace cell counts, as in the
namespace-augmentation probe) + the **freeze-time regression gate**. The judge machinery stays in
the repo, parked; refresh rubrics just-in-time ONLY if a behavioral signal demands a new
extraction investigation. ("Skip — but skip-with-a-net.")

## Game-level instruments (the only two)

1. **Targeted branch arms** — only when a branch's store/behavior changes (the nh wolf/SK arm
   pattern; the wrapper experiment follows it, gated behind replay).
2. **Freeze-time regression gate (MANDATORY)** — one all-on arm + one FRESH same-epoch baseline,
   run together at freeze (~$15–18; never reuse an old baseline). Required because dedup
   re-tune/merge rewrites store content for ALL roles, and the wolf/SK lesson is that content
   changes harm through emergent game channels no component eval sees.

**⭐Which arm at which checkpoint (settled 2026-06-12):** the adoption-time regression is
**town_only** (vs this week's `ab_arms_town`; opponents memory-free in both → the only delta is
town's memory content), NOT all-on — in an all-on arm the fixed SK wins more, so town wins less,
and opponent improvement masquerades as a town regression. All-on is reserved for the freeze gate
(tests what ships, holistically). Optional in-epoch nh all-on (~$9) re-anchors the headline on the
new store; if run, PRE-REGISTER: town win is ALLOWED to dip vs old all-on (+23pp) because a
functioning SK eats town wins — pass condition = town proxies (vote accuracy, mislynch) holding,
not the win cell.

## Tiered scope

- **Must-ship (this week, in-epoch):** nh N=30 verdict → store rewrite → town consistency shot →
  adherence echo-read → investigation write-up (the null → metric-artifact → mechanism → fix →
  differential arc; for the portfolio this narrative IS the product).
- **Phase B core:** track 2 (dedup golden sets + re-tune) → tracks 1+3 labels on the settled
  store → CE retrain (pure-Q gold, prefilter-threshold fix) → labelling-methodology capstone
  write-up.
- **Stretch:** wolf injection-wrapper (replay-first, then one arm; content-agnostic base-rate
  wording); adherence rubric formalized into the Phase B labelling doc.
- **Parked / roadmap-only:** strategy-points injection (NEW agent-visible feature, not an
  optimization — needs its own game-level arm if ever adopted); standing extraction eval (above);
  N=60 town replication; general-wrapper ablation; per-role town audits as experiments;
  fine-tuning exploration (option map + RL-hybrid/selection-bandit designs logged 2026-06-12 in
  `evidence/fine_tuning/agent_dialogue/` + `evidence/fine_tuning/memory_selection_bandit/`; note
  the synergy runs THIS way only: Phase B tracks 3a/3b/3c + merge-metadata aggregation de-noise
  that future work for free — nothing about it constrains Phase B).

## Exit

Phase B ends at: store settled (rewrite + re-tuned dedup) + labels banked + CE retrained +
regression gate PASSED → freeze → ship/frontend. Nothing big-N remains on the critical path.
