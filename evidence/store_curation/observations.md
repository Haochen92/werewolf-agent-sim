# The observation store — evidence, decay, and the synthesis substrate

> **Scope:** the per-store mechanism doc for observations, under the framework in
> [`report.md`](report.md) (its cross-cutting principles are cited by number). An observation is a
> situation → approach → outcome record extracted post-game into one of 17 (role, phase) cells; a
> real one is quoted in report §1. Curation code: online dedup at game fold
> (`evaluation/src/loop/merge.py`), decay inside the SP tick (`consolidate.py`). Seeding
> instrument and record: [`../extraction/post_game/`](../extraction/post_game/report.md); dedup
> design and goldens: [`../dedup/`](../dedup/report.md).
> **Status:** split out of the parent report 2026-07-15; mechanism as of the 2026-07-14
> store-bounding review (log §4; suite 684 green, uncommitted, `feature-dimension-schema`).

## 1. Role and consumers — substrate, not prompt content

Observations are the loop's evidence layer: what actually happened, per role and phase, before any
distillation. In v7 they have exactly one consumer — **SP synthesis** reads them as clustering
substrate (`strategy_points.md` §2). They carry no credit, because nothing "follows" an
observation: it states what happened, not what to do, so there is no outcome to grade (credit
report §1). Recurrence is their only quality signal, and all of their curation runs on it.

**The injection role is retired in v7.** In the v5/v6 static-memory arms, retrieved observations
were injected into prompts alongside SPs, and the proven static-memory effect rests on those arms
as run. The v7 read/tactic redesign supersedes that channel: prompts carry the **tell book**
(facts, credited by accuracy) and **retrieved SPs** (directives, credited by outcomes), and
observations stay behind the scenes as the synthesis substrate
([`../credit/read_tactic_credit_redesign.md`](../credit/read_tactic_credit_redesign.md) §3–§5).
One consequence worth naming: the obs store doubles as the SP store's *archive* — a deleted SP's
underlying evidence persists here, and deletion plus re-synthesis is the SP-native re-audit path
(report §6.7).

⚠ **Wiring gap, tracked as report §6.8 (2026-07-15):** the run path does not enforce the
retirement yet — `--retrieval-types` defaults to injecting both kinds and the loop driver never
overrides it, so a run launched as wired would still inject observations. The fix (driver passes
the SP-only retrieval config) gates the pre-reg config pin.

## 2. Layers

Two persistent layers, both keyed by the record key (stable across dedup merges):

- **The per-cell store** — 17 (role, phase) cells, e.g. `observations/villager/day_discussion`.
  Each record carries the situation/approach/outcome text, embedding-bearing dimension fields, and
  `observation_count` — how many times this lesson has arrived (pooled by admission, §4).
- **The generation sidecar** (`obs_generations.json`, maintained by the loop driver) — each
  record's **first-seen** generation (arrivals are counted by it — the synthesis new-evidence gate
  depends on arrival, not net change) and **last-reinforced** generation (a reinforcement is
  detected as a rise in `observation_count`). The sidecar exists because the store records
  themselves don't carry loop-time clocks; keeping the clocks outside the store means dedup and
  reseeding can't corrupt them.

There is no consumption layer in v7 (§1); the "view" synthesis sees is the per-cell clustering
described at `strategy_points.md` §2 (clusters seed from new arrivals; a new obs with no
similarity-0.70 neighbor stays a singleton and is never synthesized alone).

## 3. Removal — count-scaled decay

Observations cannot be pruned by lift (no credit), so the selection is a **count-scaled allowance
clocked from the last reinforcement**: an obs is dropped once it has gone
`obs_evict_min_age × observation_count` generations without being reinforced
(`obs_evict_min_age = 4`). A once-seen obs gets one 4-generation window; a count-N obs gets N
windows; any reinforcement restarts the clock. So a still-recurring lesson keeps surviving, while a
lesson that stopped recurring eventually decays no matter how often it was once seen — nothing in
the store is immortal, which matters because store size is exactly what the per-tick clustering
cost used to scale with.

*(Revised 2026-07-14, store-bounding review — log §4.)* The original rule was age × frequency:
drop only obs that were BOTH old AND never reinforced. That made any obs with count ≥ 2 immortal —
the store's one unbounded term (report §5, pathology 8). The count-scaled rule strictly
generalizes it: for a count-1 obs the two rules are identical. `obs_evict_max_count` was deleted
as subsumed.

The record key is stable across dedup merges, so a merged-and-reinforced obs keeps its original
*age* but restarts its *clock* — exactly the "old but proven" case the rule wants to keep alive
(principle 4). The named trade-off: evicting a reinforced obs resets its identity. Its next
rewording re-enters as a count-1 singleton with no history and can re-trigger synthesis of an
already-distilled lesson, so the rule trades store size for occasional re-litigation. The ruled
fallback, if a live run shows the scaled rule failing to bound the store: a per-cell size ceiling
that evicts the least-recently-touched obs. Decay runs before synthesis in the tick
(`strategy_points.md` §1), so the synthesizer only distills surviving evidence.

## 4. Admission — the online fold, freeze-old, triage-only

Each generation's parallel games produce new observations, and `loop/merge.py` folds them into the
run store before consolidation. Two properties define the pass:

- **Freeze-old.** Only new-key arrivals are dedup candidates; existing entries never re-litigate
  against each other (old↔old operations are forbidden by the apply-guard). This is what fixed the
  incremental non-convergence pathology — without the guard, old entries kept getting re-judged as
  neighbors landed, and repeated passes eroded the store past the ~17% duplicate-rate sweet spot
  ([`../dedup/incremental_convergence.md`](../dedup/incremental_convergence.md); report §5,
  pathology 10).
- **Triage-only.** The online pass runs KEEP/DISCARD, not text merge: an exact duplicate collapses
  onto the existing record and **pools counts** (`observation_count` rises — the reinforcement
  signal §3's clock runs on), while a near-duplicate is *kept separate*. Full merge — an LLM
  writing a combined text — exists only in the offline batch pipeline (§5). Pooling on exact match
  is the observation store's deliberate exception to the never-merge rules (principle 2): an obs
  is evidence, not a commitment, so the same lesson's arrivals should accumulate.

Why observations keep an online (per-generation) pass at all, when tells retired theirs: the
observation store is consumed *within the loop cadence* — the very next tick's synthesis clusters
over it — so duplicates left standing until some later batch pass would distort clustering and
double-trigger the new-evidence gate. Tells have no same-cadence consumer, which is exactly why
their curation could be epoch-quantized (`tells.md` §2).

## 5. Repair — batch dedup, offline only

The full-store pass — similarity clustering plus a strong-model judge that can MERGE (write a
combined text, pool counts) — is the offline repair tool, run deliberately and never inside the
loop tick: [`../dedup/batch_architecture.md`](../dedup/batch_architecture.md) for the mechanism,
[`../dedup/report.md`](../dedup/report.md) for the goldens (the KEEP/DISCARD decision-maker is
human-golden-anchored for both the online and batch passes). Its known behaviors shaped the loop's
design: incremental application without freeze-old does not converge (§4 above), and merge-writing
is the error-prone step (the strong merge-writer model fabricates fields at a measured 33% rate —
one reason the *online* pass is triage-only and merge stays offline, where output is reviewed).

## 6. Verification and gaps (2026-07-15)

**Verified.** The decay rule, sidecar stamping, and gate-ordering are unit-covered (part of the
684-green suite, 2026-07-14 — report §5); the freeze-old apply-guard is live in the loop's obs
fold; the dedup decision-maker is golden-anchored (see §5 pointers). The count-pooling +
clock-restart interaction (merged-and-reinforced keeps age, restarts clock) is covered by the
store-bounding review's tests.

**Gaps, criticality-ordered:**

1. **The §6.8 wiring gap** (report §6.8; §1 above) — the retired injection role is design and
   docstring, not yet driver config. Gates the pre-reg pin.
2. **Decay has never shaped a live long run** — the count-scaled rule is suite-verified and the
   v2 runs motivated it, but no run has yet exercised the bound over enough generations to
   confirm the store plateaus; the ruled LRU fallback (§3) exists for exactly that contingency.
   Post-run readout.
3. **Near-duplicate accumulation between repairs** — the online pass keeps near-dups separate by
   design, so the store carries paraphrase redundancy until an offline batch pass runs; at run
   scale this is bounded by decay, but no schedule pins when (or whether) a batch repair runs
   during the v7 run. Minor; flagged so the post-run store read expects it.
