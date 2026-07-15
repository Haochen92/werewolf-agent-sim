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

Synthesis distills a cell's observation clusters into new SPs. Uncontrolled, this step is the bloat
engine (report §5, pathologies 1–3), so three gates sit in front of it:

- **The new-evidence gate.** A cell re-synthesizes only when it gained ≥ `synth_min_new_obs = 4`
  new observations — counted by **arrival** (first-seen generation), not by net count change. The
  net-change version silently stalls: once decay removes as many obs as arrive, the trigger reads
  "no new obs" even though fresh evidence did arrive (the gen-6 stall, fixed in place). A *depleted*
  cell (fewer than `synth_replenish_floor = 3` SPs, because prune/evict culled it) is exempt, so the
  replenish path still refills it.
- **The new-clusters-only gate.** Within an admitted cell, only clusters carrying a new obs are
  re-synthesized. Without this, every cluster in an admitted cell regenerated SP variants of
  already-distilled lessons each tick — variants that don't exact-dedup — and the store compounded
  ~6× per run (5.4 → 34 SPs/cell).
- **The hard cap — on the contested lane.** A cell whose *unproven* SPs already number ≥
  `synth_cell_unproven_cap = 12` skips synthesis entirely (depleted cells exempt). Proven SPs
  (positive lift, ≥2 follows — the same predicate as the §4 exemption, via a shared helper) occupy
  earned slots outside the quota, so a cell full of proven SPs still admits synthesis and keeps
  exploring; the cap only blocks piling more untested candidates onto an already-full contested
  lane. *(Re-scoped 2026-07-14 from a total-size cap — §6.7 ruling, log §5; the knob was renamed
  from `synth_cell_sp_cap`.)* 12 is anchored on the bloat record: ~2.4× the healthy ~5, well under
  the ~34 runaway — and the record's runaway population was overwhelmingly unproven duplicates, so
  the same value protects against the same failure. The cap gates *growth*, not size: culls run
  every generation and synthesis only every k, so a capped cell resumes growing once credit drains
  its lane (an unproven SP leaves by proving out, souring, or eviction). Capped cells are counted
  and printed per generation, so the gate biting is observable, not silent.

The gates run **before any clustering work** *(2026-07-14 store-bounding review, log §4)*.
Admission needs only record keys, the generation sidecar, and the cell's SP lane counts — all
deterministic arithmetic — so a skipped cell pays zero embedding cost. Previously every cell was
fully clustered first (one embedding search per obs) and the gates only cut the LLM calls, which
left the clustering bill scaling with total store size. An admitted cell then seeds its clusters
**from the new arrivals only**: each new obs pulls in its neighbors, and old obs still join
clusters as members. This reproduces exactly the new-bearing clusters the new-clusters-only gate
keeps, without building the all-old clusters it would discard. A depleted cell keeps full seeding,
because its replenish path must re-synthesize from old clusters. By construction, the per-tick
clustering cost now scales with the generation's new-obs inflow rather than with store size.
(Unchanged: a new obs with no similarity-0.70 neighbor stays a singleton, and singletons are never
synthesized — a lone observation waits for corroborating evidence before it can fire.)

What makes the synthesis credit-*aware* is the **track record**: the realized lift of every cell SP
with ≥ `synth_track_min_follow = 5` follows is rendered into the synthesis prompt ("realized lift
+0.26, followed 9×: <action>…"), so the model revises toward what measured well rather than
re-summarizing the observations blind. Without it, synthesis regenerates what prune killed, because
observation outcome tags track faction-won — luck (report §5, pathology 11). Two pieces of
bookkeeping make this auditable: the `with_track_record` counter exposes per generation how many
cells actually synthesized with a track record (0 means the thesis mechanism is silently not firing
yet), and every new SP carries `distilled_from` — the keys of the SPs whose record fed its
synthesis — so a revised SP joins back to its parents' credit history offline (lineage, never shown
to agents).

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
- **Synthesis *quality* is unjudged.** The mechanism is suite-verified (gates, cap, track record,
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
