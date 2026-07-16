# The strategy-point store — synthesis, credit-driven curation, and the injection lanes

> **Scope:** the per-store mechanism doc for strategy points, under the framework in
> [`report.md`](report.md) (stores × layers × operations; the cross-cutting principles it defines
> are cited here by number, e.g. "principle 2"). An SP is a situation-conditioned directive an
> agent may follow, with live counters (`follow_count / positive_count / negative_count`); a real
> one is quoted in report §1. The SP tick is `evaluation/src/loop/consolidate.py`, one call per
> generation; the per-item utility it consumes is the credit layer
> ([`../credit/report.md`](../credit/report.md)); the 2026-06-19 design lineage is
> [`../v7_final/consolidation_design.md`](../v7_final/consolidation_design.md).
> **Status:** split out of the parent report 2026-07-15; mechanism as of the 2026-07-14 reviews
> (suite 684 green, uncommitted, `feature-dimension-schema`).

**Role and consumers.** Strategy points are the store the compounding thesis rides on: the loop's
one *generative* step writes them, credit grades them, curation keeps the good ones, and the next
generation's agents retrieve them. Written by synthesis (below); read at every agent decision via
RAG retrieval (§5); graded by the credit layer after each generation. Because the growth step is
an LLM writing new text, this store is the only one that can *create* bad content — which is why
most of the system's guards concentrate here (report §4).

## 0. The SP lifecycle, end to end (the generation graph)

An SP's whole life is a single loop that spans a generation's games and the curation tick after
them. Reading it top to bottom is reading one full turn of the compounding cycle:

> **retrieve & follow** *(inside each game)* → **credit** *(after the games)* →
> **consolidate** *(the tick)* → **retrieve & follow** *(next generation)*

Concretely, per generation the driver runs these in order (`driver.py`):

1. **Retrieve & follow** — inside each game, agents retrieve SPs for their situation and either
   follow or reject each one; those choices are recorded (§5).
2. **Credit** (`credit.credit_apply`) — after the generation's games, each *followed* SP is graded
   by the outcome, updating its `follow_count / positive_count / negative_count` against a
   memory-OFF baseline (the credit layer, [`../credit/report.md`](../credit/report.md)).
3. **Consolidate** (`consolidate.consolidate`) — the SP tick: observation decay → synthesis → SP
   dedup → prune/evict, in that fixed order (§1).
4. The next generation's agents retrieve the updated store, and the loop repeats.

Steps 2 and 3 are the whole point — credit *measures* each SP, and consolidation *acts* on that
measurement, so the store improves rather than merely growing. The sections below zoom into step 3:
§1 is the tick as a whole, §2 its growth step, §3 its dedup, §4 its removal steps, and §5 is the
retrieval (step 1) that closes the loop.

## 1. The tick — four steps, order load-bearing

One call (`consolidate`) runs four steps in a deliberate order:
**observation decay → synthesis (every k gens) → SP dedup → prune/evict last.**

The ordering is load-bearing at both ends. Synthesis runs before dedup because synthesis *appends*
and dedup exists to collapse what it appended. Prune runs **last**, on the post-dedup counts,
because the dedup absorbs a discarded duplicate's counts into its survivor — which can push that
survivor across the prune threshold. Under the old order (prune first) a strongly-bad SP could
cross the threshold *after* the prune pass, escape for a generation, and get followed — the harmful
tail that dragged outcomes below baseline (report §5, pathology 4).

There is also a cadence split: the cheap deterministic steps (decay, prune, evict, credit) run
**every** generation, while the one paid LLM step (synthesis, plus its dedup) runs every
`synth_every_k_gens = 2` — culls are fast, growth is slow. Observation decay is documented with its
own store ([`observations.md`](observations.md) §3); it runs first here so the synthesizer only
distills surviving evidence.

## 2. Growth — credit-aware synthesis

Synthesis distills a cell's observation clusters into new SPs. First, what a *cluster* is and how it
is built — it is the same greedy, seed-based routine batch dedup uses (`cluster_mode = "bounded"`),
*not* a connected-components sweep. A cell's observations are first partitioned by **situation
regime** (a `gate_key`: is-swing × alive-bucket × consensus-direction), so a cluster never mixes
regimes. Within a regime, observations are taken as *seeds* most-reinforced first (highest
`observation_count`); each seed runs a similarity search, and neighbours scoring above cosine 0.70
join it, up to 15 per cluster. Each observation is claimed by exactly one cluster — the first seed
to reach it, never merged transitively — and a seed with no neighbour above 0.70 forms no cluster,
leaving its observation a lone *singleton* that is never synthesized alone. A cluster is therefore
one recurring lesson in slightly different words, and synthesis writes at most one new SP per
cluster. (In the loop only *new arrivals* may seed — old observations still join as neighbours —
which is the seed-from-new optimization described below.)

Uncontrolled, synthesis is the bloat engine (report §5, pathologies 1–3), so three **admission
checks** sit in front of it (the code calls them "gates," but they are guard conditions, unrelated to
the `gate_key` above) — two decide whether a whole *cell* synthesizes at all, and one decides which
*clusters* inside an admitted cell do:

- **The new-evidence check** *(per cell)*. A cell re-synthesizes only when it gained ≥
  `synth_min_new_obs = 4` new observations — counted by **arrival** (first-seen generation), not by
  net count change. The net-change version silently stalls: once decay removes as many obs as arrive,
  the trigger reads "no new obs" even though fresh evidence did arrive (the gen-6 stall, fixed in
  place). A *depleted* cell (fewer than `synth_replenish_floor = 3` SPs total, because prune/evict
  culled it) is exempt, so the replenish path can still refill it.
- **The hard cap** *(per cell, on the contested lane)*. A cell whose *unproven* SPs already number ≥
  `synth_cell_unproven_cap = 12` skips synthesis entirely (depleted cells exempt). Proven SPs sit in
  earned slots *outside* this quota — "proven" here is positive lift with ≥2 follows, the same
  predicate as the §4 exemption — so a cell full of proven SPs still admits synthesis and keeps
  exploring; the cap only blocks piling more untested candidates onto an already-full contested lane.
  The value 12 is anchored on the run-1 bloat record (report §1): a *healthy* cell held about 5 SPs
  and a *bloated* one about 34, so 12 sits ~2.4× the healthy size and well under the runaway. Since
  that runaway was overwhelmingly unproven duplicates, the same value guards the same failure. Note
  the cap limits *growth*, not size: culls run every generation while synthesis runs only every k, so a
  capped cell resumes growing as soon as credit drains its lane (an unproven SP leaves by proving out,
  souring, or being evicted). Capped cells are counted and printed each generation, so the cap biting
  is observable, not silent. *(Re-scoped 2026-07-14 from a total-size cap — §6.7 ruling, log §5; knob
  renamed from `synth_cell_sp_cap`.)*
- **The new-clusters-only check** *(per cluster)*. Within an admitted cell, only clusters that carry a
  new obs are re-synthesized. Without it, every cluster in an admitted cell would regenerate SP
  variants of already-distilled lessons each tick — variants that don't exact-dedup — and the store
  compounded ~6× per run (5.4 → 34 SPs/cell).

**Why the checks run before clustering — a before-and-after.** Clustering runs a similarity search
for each *seed* observation to gather its neighbours; it is the expensive, store-size-scaling part of
the tick (the embeddings themselves are cached, but each search scans the cell). The two *cell-level*
checks above are computable from cheap counts alone (record keys, the generation sidecar, the SP lane
sizes), so they can run *first* and let a skipped cell pay no search cost. Take a cell holding **30
old observations and 2 new ones**:

- *Before* (pre-2026-07-14, the store-bounding review — log §4): every cell was clustered in full
  first, and only then did the checks cut the LLM synthesis calls. With every obs seeding a search,
  our cell paid ~32 searches every tick — even if the checks then skipped it — so the clustering bill
  grew with the whole store.
- *After:* the checks decide first, from counts; only an admitted cell clusters; and it seeds its
  clusters **from the new arrivals only**. The same cell now runs ~2 searches — one per new
  observation — and the 30 old obs still join those clusters as members. The new-bearing clusters
  come out identical, without ever building the all-old clusters the new-clusters-only check would
  have discarded anyway. (A *depleted* cell is the exception: it re-clusters in full, because it has
  to replenish from its old clusters.)

The net effect: per-tick clustering cost dropped from O(cell size²) to O(new obs × cell size), so it
now tracks the generation's new-obs inflow rather than the accumulated store. (A new obs with no
neighbour above cosine 0.70 stays a singleton, and singletons are never synthesized — a lone
observation waits for corroborating evidence before it can fire.)

What makes synthesis credit-*aware* is the **track record** it is handed. For every SP already in the
cell with at least `synth_track_min_follow = 5` follows, that SP's realized (de-luck) lift is rendered
into the synthesis prompt — for example, "realized lift +0.26, followed 9×: <action>…". The prompt
then instructs the model to weight *that* signal, not the observations' own outcome tags (which track
faction-won, i.e. luck — report §5, pathology 11). Concretely, a directive the track record shows
*under*performed is treated as a **corrective** — do the opposite or a refinement, never re-prescribe
the loser — while one that measured well is reinforced. This is not a filter and not wording mimicry:
the model still writes new IF-THEN strategy points from the cluster, and the track record only steers
*which advice* they give. Without it, synthesis tends to regenerate exactly what prune just killed,
because it would be trusting those luck-laden observation tags.

Two pieces of bookkeeping keep this auditable. The `with_track_record` counter reports, each
generation, how many cells actually synthesized *with* a track record; a value of 0 means the
credit-aware mechanism the whole thesis rests on is silently not firing yet. And every new SP
carries `distilled_from` — the keys of the SPs whose record fed its synthesis — so a revised SP can
be joined back to its parents' credit history offline. (That lineage is for offline audit only; it
is never shown to agents.)

## 3. Admission — SP dedup, keep/discard, freeze-old

Synthesis appends, so a KEEP/DISCARD dedup runs right after it, collapsing a near-duplicate onto
the **credited older survivor**, which absorbs the duplicate's counts and timestamps. Two rules
define it, both instances of the identity principle (report §2.3, principle 2): SPs are never
*merged* — combining two directives into one text is incoherent, because one of them stops meaning
what its counters measured — and the boundary is **freeze-old** (only the just-synthesized SPs are
candidates to die; prior SPs are frozen, so accumulated credit history always survives). It reuses
the production dedup core on flash-lite — safe here because KEEP/DISCARD is schema-enforced with no
merge text to get wrong. Without this step, near-duplicate SPs smear one lesson's follows across
several rows and none of them ever accumulates actionable evidence (report §5, pathology 5).

One scope limit, tracked as agenda item §6.4 (report): the dedup only runs when synthesis added SPs
in this tick, so a *seeded* store's pre-existing near-duplicates are never collapsed in-loop — a
seed store must arrive already deduped (one report-only batch-dedup pass before launch).

## 4. Removal — prune and evict, with two mercy rules

- **Prune** drops the stably harmful: realized lift < `prune_tau = −0.15` with ≥
  `prune_min_follow = 8` follows. The lift is differenced against the same-instrument memory-OFF
  base for the SP's cell (and `sp_type`) — the credit layer's baseline-coherence rule, enforced by
  `invariants.py::assert_baseline_coherence`.
- **Evict** drops the dead weight: retrieved ≥ `evict_min_retrieved = 8` times, never followed —
  but only when the rejection was **on the merits**. The verdict counters distinguish "the agent
  applied it and overrode it" (override-dominant → evict) from "the agent said it didn't apply
  here" (`not_relevant`-dominant → **spared**): the latter is a retrieval/scoping miss, and
  deleting the SP would blame content for a retrieval artifact (report §5, pathology 6).
- **The proven-SP exemption** overrides both: any SP with positive lift and ≥
  `protect_min_follow = 2` follows is never dropped, by prune, evict, or any future age rule. A
  rare-but-proven lesson survives; degradation is credit-only — an SP leaves the store by souring
  (negative lift) or by being dead weight, never by merely getting old (principle 4).

## 5. The consumption layers — lanes, tiering, and the exploration slot

The store's cells hold two implicit lanes: **proven** (positive lift, ≥2 follows) and **contested**
(everything else, including the never-yet-retrieved). Retrieval is where the lanes matter, because
SP credit is **usage-gated** — an SP earns or sours only when an agent follows it — so whatever
retrieval surfaces is the only thing that can ever accumulate evidence.

The path an SP travels to reach a prompt: RAG retrieval over the cell (top-k 10 on the reranked
path, 5 on the narrow path) → the per-situation cap of 3 (`RETRIEVAL_KEEP_PER_SITUATION`, the one
choke point every retrieval path passes) → injection into the prompt's memory block. Two rules act
at the cap, both from the 2026-07-14 lane ruling (report §6.7, log §5):

- **Proven tiering** (`sp_proven_tiering`, default-on): proven SPs rank ahead of contested ones,
  so earned advice is what usually fills the ≤3 slots.
- **The exploration slot** (`sp_exploration_slot`, default-on): if all kept SPs are proven and the
  pool holds an unproven one, the best unproven candidate takes the lowest slot. This is the
  contested lane's drain — without it, a cell whose slots are locked by proven SPs would starve
  every new candidate of the retrieval opportunity credit requires (report §5, pathology 7), and
  the §2 cap would then block that cell's synthesis forever.

Two predicates called "proven" deliberately differ, and both sites carry a comment saying so: the
game side (`Agents/memory/retrieval/filters.py`) uses follow ≥ 5 ∧ positives > negatives, because
the read path has no base rates; the loop side (`consolidate.py`) uses lift with
`protect_min_follow = 2`. The lane pieces *not* adopted from the tell ledger, with standing
reasons, are recorded at report §6.7.

**Currency caveat.** This whole read-path filter stack — proven tiering, the exploration slot, and
the `_sp_is_proven` heuristic — is *wired and default-on* (flags in `retrieval/plan_gating.py`,
applied in `retrieval/pipeline.py`), and its predicate was updated for v7's de-lucked counts
(execution plan §0.5). But it has never shaped a live v7 store: no fold-bearing loop run has
exercised it (§7 gap 1), and the read-path judges are the least-measured surface in the eval sweep.
So its applicability to v7 is asserted by construction, not verified in a run — treat this section as
the *intended* read path, pending the first live fold.

The exploration slot changes live-game retrieval behavior, so it is an epoch-bundle member exactly
like proven tiering (execution plan §0.4): it ships with the next prompt-epoch bundle, never
mid-baseline.

## 6. Verification specific to this store

The cross-store verification inventory is report §5 (pathology rows 1–7, 9, 11 are SP-side). Two
items carry the most weight for this store:

- **The prune threshold cuts reproducible signal, not noise** (the report §6.2 check, run
  2026-07-14; `heldout_credit_reproduction`, zero spend — it re-scores existing v6ab dumps).
  Method: the threshold cannot be validated on the same games that produced the flags (the metric
  would be grading its own homework), so the archive was split into two halves by game, every SP's
  lift measured on each half independently, and two non-circular questions asked — do the two
  measurements agree, and do SPs flagged harmful on half A stay harmful on half B, which never saw
  the flags? Result: Pearson(lift_A, lift_B) = +0.54 at n = 31 comparable SPs (noise would read
  ~0); A-flagged losers (lift_A < −0.15) stayed negative on the held-out half in 8/9 cases against
  a 61% base rate; the one flip sat at 3 follows, below the prune rule's ≥8 floor (all 4 flagged
  SPs at ≥8 follows stayed negative). Direction-credible at small n — a directional check, not a
  calibration.
- **Synthesis *quality* is unjudged.** The mechanism is suite-verified (checks, cap, track record,
  lineage), but no judge has scored whether synthesized SPs are *good* distillations — the
  extraction judge has zero references from the loop. Tracked since the eval sweep; the planned
  closure is the SP-synthesis golden authored during the ownership walkthrough (execution plan
  §R, Phase-2 labeling).

## 7. Gaps and open points (2026-07-15)

Criticality-ordered; the walkthrough agenda items live in report §6 and are not repeated here.

1. **Lane composition under a live run is unmeasured** — the contested-lane cap and exploration
   slot are suite-verified but have never shaped a real store (no fold-bearing loop run yet;
   report §5 "not yet verified"). Post-run readout.
2. **Synthesis quality unjudged** (§6 above) — the biggest instrument gap on this store's path.
3. **Design-anchored knobs unswept** — `prune_tau` is the only checked knob (§6); the follow/
   retrieve floors (8/8/2) and the cap value 12 are pinned as design-anchored in the pre-reg with
   a post-run sensitivity readout.
4. **Removal may not even trigger within the run horizon; store convergence is unproven.** Prune
   needs ≥8 follows and evict needs ≥8 retrievals (§4). Inside a ≤10-generation experiment many SPs
   will never accumulate 8 of either, so the removal machinery is largely a *limit* property the run
   cannot exercise. Within the run the store grows close to monotonically, held mainly by the
   contested-lane cap (§2), not by prune/evict. Whether any of the three stores plateaus at this
   eviction-vs-generation rate is an open question we have not estimated: a crude projection off the
   v2 smoke's follow/arrival distributions is conceivable, but ~6 generations of smoke won't fit a
   convergence curve. Deferred; a post-run store read should expect near-monotonic growth and judge
   whether that is a problem at the run's scale. *(Raised 2026-07-15.)*
