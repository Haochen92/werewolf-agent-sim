# Dedup/clustering tuning + strategy-points extraction — plan (2026-06-15)

**Status:** PLAN for review, no code. Prerequisite for the v6 store build's `+strategy_points` arm and
for clean observation dedup. Scope is **LLM-based dedup tuning only** — the cross-encoder prefilter
(fork-#3) stays deferred. Pointers: `dimension_schema_build_spec.md`, `procedural_memory_experiment.md`,
`evidence/phase_b/plan_review.md` (Track 2). Code lives in `Agents/memory/batch_deduplication/`
(agglomerative clustering + 2-pass LLM) and `Agents/memory/deduplication/` (incremental pairwise).

## Why this is needed now (empirical findings)

Probes on `memory_stores/v6_0` (the v6 observation store):

1. **Agglomerative clustering at the default 0.70 over-merges into nonsense.** Every namespace collapses
   into ONE blob, chopped into arbitrary `max_cluster_size`=15 chunks (916/919 obs land in max-size
   clusters). The clusters are not semantically coherent — they're "everything is loosely similar,"
   sliced by the size cap.
2. **Threshold-only tuning is fragile — no stable elbow.** Sweep (wolf/day_vote n=43; villager/day_vote
   n=54; healer/night n=55): one blob through 0.80 → 2 clusters at 0.85 → reasonable at 0.88–0.90 →
   fragments by 0.92. It jumps blob→fragments with no robust middle, because the embedding cosine is
   compressed (~0.79–0.87 baseline).
3. **Cause = prose-blob embedding + scaffolding dilution.** The stored/embedded `situation` is the
   composed blob with repeated section labels ("Information landscape: … Stakes: … Consensus: …").
   That shared scaffolding inflates baseline similarity and kills discrimination. Stripping the labels
   in a test increased cluster counts at the same threshold (more discrimination).
4. **But the structured gate-fields are well-distributed** — they discriminate where the embedding can't:
   `is_swing` ~balanced (28F/15T wolf, 29F/25T villager), `players_alive` spread 3→9,
   `consensus_direction` 3-way. These are exactly the v6 fields we extracted.
5. **Current dedup feeds the prose blob, not the structured fields.** Both `deduplication/dedup_agent.py`
   (incremental, pairwise KEEP/DISCARD, `composed_situation`) and `batch_deduplication/` (agglomerative
   clusters → 2-pass triage[flash-lite]+verify[pro], `_format_cluster_entries` emits `situation` blob +
   approach/outcome). This is the stale-prose-blob under-firing noted in the namespace-augmentation probe.

## The core idea: "similar" is an EXPLICIT predicate over the structured fields, not a cosine threshold

With v6's many fields, what counts as "the same situation" must be defined over the fields, with the
embedding used only *within* a structurally-matched group. Three layers:

1. **Cluster gate (defines a candidate group) — the MINIMAL hard-gate fields** (spec §0: a field is a
   hard gate only when crossing it makes the lesson INVALID):
   - **criticality regime**: `is_swing` + a coarse `players_alive`/`distance_to_parity` bucket
     (e.g. early 8–9 / mid 5–7 / late ≤4). Early-vs-endgame is a different playbook.
   - **`consensus_direction`** (aligns / opposes / none) — the social situation flips.
   - role-specific where it flips the playbook: **`divergence_sign`** (investigator/deceiver day),
     **`bullets_left`==0 vs >0** (vigilante), **`ally_revealed`** (wolf).
   Keep it MINIMAL — gating on *all* fields over-fragments (the inverse failure). Then
   **embedding-cluster the free-text dims WITHIN each gate group** (the gates split the cosine blob into
   regime-coherent groups; the embedding refines inside, where a stable threshold now exists because the
   group is already homogeneous).
2. **Merge gate (collapse true duplicates inside a cluster):** + `approach` + **`net_verdict`** — the
   verdict-aware key from spec Track 2. Same situation+approach but DIFFERENT net verdict = NOT a
   duplicate; it's the contrast that teaches context-dependence (merging it would collapse the signal).
3. **sp-synthesis uses the WHOLE cluster including mixed verdicts** — the positive/negative spread across
   the cluster *is* the rule's weighting ("works when X, fails when Y").

## Strategy-points extraction (the asymmetry that drives the design)

- **Observations merge cleanly** (factual situation→outcome records, count-weighted).
- **Strategy points do NOT merge** (prescriptive rules; merging two rules' text is lossy). So: don't
  merge per-run sp — **synthesize sp fresh from the cluster.**
- **Design:** keep the v5 **dual extraction** per run (obs + sp) for a baseline; at **batch dedup**, form
  clusters and send each to TWO consumers: (a) obs **merge/dedup**, (b) **sp-synthesizer** (1–N sp per
  cluster — a rich cluster yields several distinct rules). The synthesized sp inherits the cluster's v6
  situation dimensions (retrieval key) + an action distilled from the cluster's approaches + the valenced
  counts (the reward signal) — the "triple-duty schema" for free.
- **"Try all 3" experiment** (cheap, since cluster-synth piggybacks on the clustering already computed for
  dedup): per-run+merge sp / cluster-synthesized sp / both — scored on the deceiver decision-replay.
  Caveat: if clusters are thin/incoherent, cluster-synth degenerates to ≈ per-run — which itself is the
  signal that the clustering tuning below is the blocker.

## Punch list (LLM-based; NOT the CE prefilter)

1. **Gate-then-embed clustering** on the structured fields (minimal gate + within-group embedding),
   replacing the single-threshold agglomerative pass in `batch_deduplication/clustering.py`.
2. **Embed distinctive content, not the scaffolded blob.** Needs an embed-text vs display-text split:
   the stored `situation` shown to the agent stays full/labeled, but the EMBEDDING (retrieval + clustering)
   uses a label-stripped / distinctive-content representation. (Open: store a separate embed key, or
   reduce scaffolding in the composed string.)
3. **Feed the dedup + sp-synth prompts the STRUCTURED fields** (situation dims / approach / criticality /
   net_verdict), not the prose blob — `_format_cluster_entries` + the dedup prompts.
4. **Add the sp-synthesizer** as a second consumer of the clusters (reuse the standards/epistemic/quality
   blocks; allow multiple sp per cluster).
5. **Validate** on v6_0: cluster-coherence by eye + the 3-way sp experiment on the deceiver replay.

## Sequencing & risks

- This tuning is a **prerequisite** for the `+strategy_points` gate arm (clusters feed sp-synth) and
  improves observation dedup quality; do it **before** the full v6 store build/freeze-gate.
- **NOT** in scope: the CE/cross-encoder prefilter (fork-#3, deferred); a v6 procedural *cell schema*
  (the "perfect it" we're skipping — reuse the existing sp extraction shape).
- **Risk:** gate granularity (too coarse → over-merge persists; too fine → over-fragment) — tune the
  criticality buckets + which role-specific gates apply. The within-group embedding threshold should be
  re-checked per gate group (homogeneous groups may want a different cut than the global sweep suggested).
- **Risk:** the embed-text/display-text split touches `compose_situation_embed` + every `.situation`
  consumer (retrieval, dedup, display) — verify no path embeds the display text or shows the stripped text.
