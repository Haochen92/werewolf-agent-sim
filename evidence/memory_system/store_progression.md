# Memory Store Progression: `old_strateg_archive` → v7

A cross-experiment synthesis of how the episodic-memory store evolved across ~8 versions. This is a
**portfolio progression piece**, not a new experiment: every number here is sourced from a dated
evidence folder (cited inline), and the value is the *narrative that connects them*. If you read one
thing, read the arc below — it turns eight store versions into a single story.

## The arc: the bottleneck kept moving

Each version is best understood not as "a better store" but as a **response to where the binding
constraint had moved**. Once a version exhausted one bottleneck, the next bottleneck became visible
and defined the next version:

```
  architecture            store hygiene           retrieval precision         content quality
 (monolithic→RAG)   →   (redundancy→dedup)   →   (namespacing→dimensions)  →   (the loop)
   Phase 0→1              Phase 2                   v5→v6                        v7
```

The most important thing this progression demonstrates is **diagnostic discipline**: the later
versions (v6, v7) return *negative and open* results, and those are the most informative versions in
the set — they are what relocated the bottleneck from "retrieve better" to "the content itself is the
limit." A reader should come away understanding that the negative findings were *earned*, not failures.

---

## 1. Phase 0 — `old_strateg_archive`: monolithic strategy injection

**What it was.** The earliest system extracted "learnings" from postgame transcripts and accumulated
them into a single strategy document per role (228 items across 4 role namespaces), injected wholesale
as a system prompt at game start.

**Driver to leave it.** Over 10+ iterations, transcript inspection showed genuinely increasing
sophistication — so the *idea* (cross-game learning) was sound. But the failure mode was
**overfitting**: a single doc accumulated every lesson including contradictory edge cases, recent
games dominated the text, and agents rigidly applied advice from a specific past situation to a
current one where it didn't hold. This is the only transition in the whole progression driven by a
qualitative architecture failure rather than a measured metric.

*Source: `effectiveness/report.md` §System Evolution (Phase 0).*

## 2. Phase 1 — modular RAG (v1–v3): retrieve the situation, not the doc

**What changed.** Decompose memory into two retrievable types — **observations** (factual accounts of
past events) and **strategy points** (prescriptive advice) — stored in a vector store, namespaced by
role, retrieved per turn by semantic match on the agent's current situation summary.

**Why.** Directly targets overfitting: surface only situation-relevant memories instead of dumping the
whole strategy doc. Retrieval *is* the anti-overfitting mechanism.

**What it exposed.** The new bottleneck was **store hygiene**. As games accumulated, the raw store
filled with near-duplicates — by v3, retrieval showed ~52% observation redundancy and ~77% strategy-
point redundancy. Retrieval slots were being spent on copies.

*Source: `effectiveness/report.md` §Phase 1; `dedup/store_retrieval_impact/experiment_log.md`.*

## 3. Phase 2 — dedup + action-phase namespacing (v3_deduped → v4 → v4_deduped → v4_deduped_v2)

**What changed.** Two moves: (a) a **batch deduplication pipeline** — agglomerative clustering then an
LLM judges each cluster KEEP / MERGE (observations only) / DISCARD; (b) **action-phase namespace
segregation** (discussion vs vote vs night), so a night-action lesson can't surface during day
discussion. The v4 store (522 items, pre-dedup) is the noisier, larger store that anchors Batch B of
the effectiveness study.

**What happened — dedup is a Goldilocks problem.** The first dedup prompts (v0) merged too
aggressively: a 39% store reduction that *hurt* observation relevance at n=39 (it crossed from
removing redundancy into removing distinct lessons). Tuned prompts (v3: anti-over-merge calibration,
indexed cluster keys, a pre-merge verification checklist) settled on a conservative ~17% reduction
that gave the best efficiency and unique-lesson counts while holding relevance. **The tradeoff named
here:** dedup trades recall of rare-but-distinct lessons for precision of the retrieval slate, and the
break-even is prompt-sensitive, not a fixed similarity threshold.

**The finding that foreshadows everything after.** Strategy-point redundancy *never responded to
dedup* — it stayed ~59–77% across every store. That ruled out "dedup harder" and reframed it as a
**content-coverage gap**: the store simply lacked entries for some situations. This is the first
signal that the eventual bottleneck would be content, not plumbing.

*Source: `dedup/store_retrieval_impact/experiment_log.md`; `dedup/README.md`; `effectiveness/report.md` Batch B.*

> **Interlude — the effectiveness study (v3_deduped vs v4).** The headline A/B on these stores showed
> memory *can* move outcomes dramatically (Batch A all-enabled **70%→97%, Fisher p=0.012**) but that
> the *same* condition collapsed to baseline on the v4 store + action-phase config (73.3%, p=1.0).
> Configuration sensitivity — not a stable memory effect — was the dominant factor. That unresolved
> sensitivity is precisely what motivated rebuilding from scratch.
> *Source: `effectiveness/report.md` §Results/Decision. (Independently re-verified: every p-value and
> CI in that report reproduces exactly from the raw JSONLs via a separate code path.)*

## 4. v5.0 — the rebuild (a discontinuity, not an increment)

**What changed.** A full-system rebuild underneath the store: **sequential discussion scheduler**
(replacing concurrent), **9-player / 3-faction casting** (serial killer added), and **per-role
extraction with Vertex prefix caching**, plus a final whole-store dedup pass.

**Why this is a hard version boundary, not a tweak.** Per the project's variant-versioning policy, a
structural redesign is a fresh-generation A/B, not a replayable config flag. v4 win-rates *do not
transfer* to v5 — it is a different game (different player count, role set, and turn order). Every
result after v5 stands on a fresh baseline; comparing a v5 number to a v4 number is a category error.

**Result.** Re-established memory-off baselines on the new foundation (villagers 67% / SK 27% /
wolves 7%), which become the reference point for all subsequent A/Bs.

*Source: `effectiveness/v5_seeding_plan.md`; `effectiveness/v5_baseline_proxy_analysis.md`.*

## 5. v5_1 — the compounding pilot that named the real problem

**What changed.** Memory-ON build games seeded from v5.0, run with **raw retrieval (top_k=3,
rerank/filter OFF)** and a growing store — deliberately the *uncurated* condition.

**What happened (the pivotal hypothesis).** Town play got *worse* with memory (villagers −32pp;
mislynches, correct-elimination, and wolf-catching all degraded), while wolves' own deception proxies
*also* dropped. So wolves' +33pp win lift came from **degraded town decision-making, not better wolf
deception** — memory was *distracting* the town. This is a confounded pilot (unpaired, growing store,
raw retrieval, small unequal N) and is labelled directional-only — but it produced the hypothesis that
drove v6: the problem is **regime-mismatched lessons** (endgame town retrieving mid-game strategy),
and the lever is retrieval precision.

*Source: `effectiveness/v5_baseline_proxy_analysis.md` §Key read.*

## 6. v6 — the dimension-schema store: attack retrieval precision

**What changed.** A **per-cell structured situation schema** (11 cells = role × {day, night}; day
merges discussion+vote because their validity boundary is the same, night is gated separately because
it genuinely differs). Crucially, **criticality numerics** (players-alive, distance-to-parity,
is-swing, bullets-left) were pulled *out* of the free-text embedding — where a bi-encoder mangles
magnitude — and exposed to an **exact structured reranker gate**. Extraction guidance is auto-generated
from one schema (single source of truth), closing prompt-field drift across extraction / query /
embedding / dedup.

**Why.** Directly tests the v5_1 hypothesis: if distraction is regime-mismatch, then gating retrieval
on structured criticality (not fuzzy embedding similarity) should recover town benefit.

**Result — HOLD, not GO.** The full store built cleanly (919 observations / 17 namespaces; a
consensus-direction hindsight leak was found and driven to 0%). But the criticality screen validated
only weakly — the headline endgame-concentration effect rested on a held-out subset of **n=7**, too
underpowered to call a clean win. The honest call was HOLD.

*Source: `phase_b/dimension_schema_build_spec.md`; `phase_b/v6_full_store.md`;
`phase_b/criticality_screen/experiment_log.md`.*

## 7. v6_1 — the paired A/B that relocated the bottleneck

**What changed.** A clean **paired A/B** on 30 shared boards (identical role draws, memory the only
variable), 6 arms (town/SK × observations/strategy-points/both), retrieval pinned raw for comparability.

**Result — the reframe.** No outcome reached p<0.05, but the *pattern* was decisive and consistent:

- Town memory **did not replicate** the earlier benefit (town-obs +6pp, NS; decision-quality Δ≈0).
- **Strategy-point-form memory trended *harmful*** for both town and the deceiver; observations were
  neutral; only **synergy** (observations cross-checking strategy points) rescued it.
- Memory was faithfully retrieved and followed (~99% follow-rate on applicable strategy points) — yet
  **following it did not improve decisions.**

That last line is the whole progression's hinge. If memory is retrieved correctly and followed
faithfully and *still* doesn't help, the bottleneck is **not retrieval precision** — it is the
**content quality** of lessons mined from a system's own capped play, which mirror mediocre play and
carry no decision-improving signal. v6's premise (fix retrieval) was disproven by its own clean test.

*Source: `effectiveness/v6_sp_ab/experiment_log.md`.*

## 8. v7 — the compounding loop: make the store improve its own content

**What changed.** The store stops being a static index and becomes **self-updating**. Across
generations it runs a closed loop: **de-lucked credit assignment** (grade each *followed* directive by
the realized decision quality against a memory-off baseline — never win/loss, which is luck-laden) →
**credit-aware synthesis** (rewrite directives to condition on their actual track record) → **prune /
evict / decay** (drop stably-harmful, never-followed, or stale-and-rare items).

**Why.** The v6_1 reframe left exactly one lever: content quality can only improve via realized-outcome
feedback, and a static index cannot do that. The loop is the direct, and only, response to that
diagnosis. The frontier question it was built to answer: *does memory that compounds across games help
more over time?* — distinct from *does having memory help?*

**Results, honestly bounded:**

| Claim | Status | Evidence |
|---|---|---|
| Static memory helps town | ✅ **valid** | **+17pp, p=0.013** (paired same-epoch A/B — a *different* experiment from the loop) |
| The system demonstrably learns | ✅ **valid** | Credit fires, synthesis engages, prune/decay cull — mechanism, outcome-independent |
| Compounding *improves play* | ❓ **open** | Both paid loop runs invalid (below) |

**Why the compounding answer is open — two invalid runs, two causes.** Run-1's de-lucked baseline was
drawn from a biased subset of decisions, distorting the very lift that drives credit and the slope.
The rerun *looked* clean (paired, cost-capped, replicated) but silently executed `all_enabled` instead
of the intended `town_only` — so the town signal sits inside a wolf/SK **arms race**, and a first-pass
analysis even rationalized its null against a "null control" that didn't exist. A by-product of the
slip: a *tentative, underpowered* positive compounding signal for **wolf** memory (+0.086 slope over
gens 2–6) — direction worth believing, magnitude not, at 4 games/gen.

**The durable deliverable is the eval instrument.** The headline of v7 is as much the *rigor* as the
memory system: the instrument caught two invalid runs and a halo in the first-pass analysis, and the
`--expect-factions` arm guard now makes the config slip crash on generation 1 (~$0.50) instead of
surviving to a $65 null. Honest negatives and a retracted claim beat a fragile positive.

*Source: `v7_final/report.md`; `v7_final/experiment_log.md` §11–12; `evaluation/src/loop/`.*

---

## Summary table

| Version | Era | The change | Driver (prior version's exhausted bottleneck) | Result |
|---|---|---|---|---|
| `old_strateg_archive` | Phase 0 | Monolithic strategy doc/role (228 items), injected wholesale | — | Sophistication up, but **overfitting** |
| v1–v3 (RAG) | Phase 1 | Observations + strategy-points, vector retrieval by role+phase | Kill overfitting → situation-specific retrieval | Works; store grows **noisy** (~52%/~77% redundancy) |
| v3_deduped → v4_deduped_v2 | Phase 2 | Batch dedup + action-phase namespacing | Redundant slots crowd out signal | Dedup is **Goldilocks**; SP redundancy is a **content gap**, not a dedup gap |
| v5.0 | Rebuild | Sequential scheduler, 9p/3-faction, per-role extraction | v4 baselines no longer transfer | Fresh baselines (67/27/7) |
| v5_1 | Pilot | Raw memory-ON build games | Explore compounding | **Raw memory distracts town**; hypothesis = regime-mismatch (confounded) |
| v6 / v6_0 | Dimension schema | Per-cell schema; criticality → structured reranker gate | Fix retrieval precision | 919 obs / 17 cells; criticality gating **weakly validated → HOLD** |
| v6_1 | Paired A/B | 6-arm paired A/B, raw retrieval | Isolate obs vs SP | Memory followed but **doesn't improve decisions** → **content is the bottleneck**, not retrieval |
| v7 | Compounding loop | Self-updating store: credit→synthesize→prune→decay | Content can only improve via outcome feedback | Static **+17pp (valid)**; learns **(valid)**; **compounding = open** (runs invalid) |

## Lessons (transferable)

- **In a learning system, the bottleneck migrates — and naming where it currently sits is the real
  work.** Four times here, exhausting one constraint (architecture, hygiene, precision) made the next
  one visible. A version that doesn't relocate the bottleneck isn't progress, even if its store is
  "cleaner."
- **Faithful retrieval + faithful following + no improvement = a content problem, not a retrieval
  problem.** The ~99%-follow / Δ≈0-decision result (v6_1) is the cleanest possible disproof of a
  retrieval-precision thesis, and it could only be seen because the A/B was paired and the follow-rate
  was instrumented. Measure adherence separately from outcome.
- **A store mined from a system's own capped play reproduces that system's ceiling.** Self-distilled
  memory regresses toward mediocre play unless an outside signal (realized de-lucked outcomes) grades
  it. This is why v7 had to become a *loop*, not a bigger index.
- **The eval harness is the deliverable when the system is hard to measure.** Two invalid runs and a
  retracted halo, each caught by an added invariant, are worth more to the portfolio than a fragile
  positive — and cheap guards (`--expect-factions`) convert a class of silent confounds into loud,
  generation-1 crashes.
- **Structural rebuilds reset the measurement frame.** v4→v5 numbers are not comparable; treating a
  redesign as a fresh A/B (not a replay) is what keeps the comparisons honest.

## What this enables / blocks

- **Open:** the town compounding question — answerable by a single **town-only** loop rerun (now arm-
  guarded), *or* deliberately deferred if the demonstrable-learning capability (v7 Claim 2) is judged
  sufficient for the product story.
- **Ship-ready now:** static memory's +17pp town benefit and the *visible* learning loop (a memory
  inspector showing an agent retrieve and act on a specific past-game lesson) are the differentiated,
  demo-able capabilities that don't depend on resolving the compounding magnitude.

## Provenance

- **Synthesized at:** repo `a317c92` (2026-06-22), branch `feature-dimension-schema`.
- **This document produces no new data** — it is a pointer-and-narrative layer over existing records.
  Authoritative numbers and their provenance live in the cited source folders:
  `evidence/memory_system/effectiveness/` (Phase 0–2, v5, v6_1), `evidence/dedup/` (Phase 2),
  `evidence/phase_b/` (v6), `evidence/v7_final/` (v7), and the loop code at `evaluation/src/loop/`.
- Where this synthesis restates a statistic (e.g. 70%→97% p=0.012; v7 +17pp p=0.013), the figure is
  quoted from those folders, not recomputed here; the effectiveness A/B and v5 pilot figures were
  independently re-verified against the raw JSONLs during this synthesis.
