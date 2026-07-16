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
distillation. In v7 they have exactly one consumer — **SP synthesis** reads them as its clustering
*substrate*. "Substrate" here means the raw material a later process is built from (the sense a
chemist uses): observations are the base material synthesis operates on, not something read directly
(`strategy_points.md` §2).

They carry no credit — and the reason is structural, not a consequence of v7 pulling them out of
prompts. "Credit" in this system means *an agent followed this and the outcome was measurably good
or bad*, and only strategy points have the machinery for it: `follow_count / positive_count /
negative_count` live on `StoredStrategyPoint`, never on `StoredObservation`, which carries only
`observation_count`. An observation states what *happened*, not what to *do*, so there is nothing to
"follow" and no per-decision outcome to grade — and this was already true in v5/v6, when
observations *were* injected into prompts but still accrued no outcome credit. Could an observation
instead be credited *off-policy*, the way a tell is? Not usefully: an observation's own `outcome`
tag tracks faction-won, i.e. luck, so it is a halo signal rather than reliable credit (report §5,
pathology 11). Recurrence — how often the same lesson re-arrives — is therefore an observation's
only trustworthy quality signal, and all of its curation runs on it.

**The injection role is retired in v7.** In the v5/v6 static-memory arms, retrieved observations
were injected into prompts alongside SPs, and the proven static-memory effect rests on those arms
as run. The v7 read/tactic redesign supersedes that channel: prompts carry the **tell book**
(facts, credited by accuracy) and **retrieved SPs** (directives, credited by outcomes), and
observations stay behind the scenes as the synthesis substrate
([`../credit/read_tactic_credit_redesign.md`](../credit/read_tactic_credit_redesign.md) §3–§5).
One consequence worth naming: the obs store doubles as the SP store's *archive* — a deleted SP's
underlying evidence persists here, and deletion plus re-synthesis is the SP-native re-audit path
(report §6.7).

This retirement is *enforced* in the run path, not merely documented: a driver config default plus a
per-generation fail-loud invariant guarantee that no arm can silently reintroduce observation
injection. The enforcement mechanism — the config knob, the invariant, and the `"both"` escape
hatch for a v5/v6 comparison arm — is described with the other verification checks in §6, gap 1.

## 2. Layers

Two persistent layers. Both are keyed by an observation's **record key** — the `str(uuid.uuid4())`
assigned when a record is first stored ([`store_ops.py`](../../Agents/memory/deduplication/store_ops.py)
`store.put(namespace, str(uuid.uuid4()), …)`). The key is a UUID, *not* a hash of the content, and
it is stable across dedup merges for a specific reason: when a duplicate arrives, dedup discards the
incoming copy and keeps the existing record (§4), so the survivor keeps its original UUID and only
its `observation_count` changes.

- **The per-cell store** (`observations.json`) — 17 (role, phase) cells, e.g.
  `observations/villager/day_discussion`. Each record carries the situation/approach/outcome text,
  embedding-bearing dimension fields, and `observation_count` — how many times this lesson has
  arrived (pooled by admission, §4).
- **The generation sidecar** (`obs_generations.json`) — a small JSON file the loop driver rewrites
  once per generation ([`driver.py`](../../evaluation/src/loop/driver.py) `_stamp_obs_generations`).
  It holds the loop-time *clocks* the store records deliberately don't carry, as three maps, all
  keyed by the same record-key UUID as the store:

  ```json
  {
    "first_seen": { "<obs-uuid>": 3 },   // the generation this key first appeared
    "reinforced": { "<obs-uuid>": 7 },   // the generation its observation_count last rose
    "counts":     { "<obs-uuid>": 5 }    // last-seen count, kept only to detect the next rise
  }
  ```

  `first_seen` drives the synthesis new-evidence gate, which counts *arrivals* rather than net change
  (`strategy_points.md` §2); `reinforced` drives the count-scaled decay clock (§3); `counts` is pure
  bookkeeping — comparing this generation's `observation_count` against the stored count is how a
  genuine reinforcement (a *rise*) is told apart from an unchanged record. The clocks live outside
  the store on purpose. Each re-extraction stamps a fresh `created_at`, so a wall-clock timestamp
  inside the record would be a useless decay key; and because dedup and reseeding rewrite the store,
  keeping the clocks in a driver-owned sidecar means those passes can't corrupt them.

So the answer to "how does the sidecar link to an observation" is: **by the record-key UUID** — a
store record and its three sidecar entries share the same key. There is no consumption layer in v7
(§1); the "view" synthesis sees is the per-cell clustering described at `strategy_points.md` §2
(clusters seed from new arrivals; a new obs with no similarity-0.70 neighbor stays a singleton and
is never synthesized alone).

### 2.1 One generation, end to end (the code path)

The pieces above are updated by a fixed sequence each generation, all operating over the same
record-key UUID. This is the obs-consolidation pipeline in order:

1. **Play** — the generation's games run concurrently. Each seeds read-only from a gen-start
   *snapshot* of the store and dumps its own observations to a private temp store, so there is no
   shared-store write race (`driver.py`; `merge.py` header).
2. **Collect new arrivals** — `merge.collect_new_obs` takes the records whose keys are in a temp
   store but absent from the snapshot (the genuinely new observations), de-duplicated by key across
   the parallel temps.
3. **Append + freeze-old dedup** — `merge.merge_new_obs` appends them to `observations.json`, then
   runs the freeze-old batch dedup: an exact cross-game duplicate collapses onto the existing record
   and bumps its `observation_count`; a near-duplicate is kept separate; old records are never
   re-litigated (§4).
4. **Stamp the sidecar** — `driver._stamp_obs_generations` rewrites `obs_generations.json`: a brand
   new key gets `first_seen = reinforced = this generation`; a key whose `observation_count` rose is
   marked `reinforced = this generation`.
5. **Consolidate** — `consolidate.py` runs the SP tick, whose first step is `evict_observations`:
   decay out any observation that has gone `obs_evict_min_age × observation_count` generations since
   its last reinforcement (§3). Whatever survives is the evidence synthesis then clusters over
   (`strategy_points.md` §2).

## 3. Removal — count-scaled decay

Observations cannot be pruned by lift (no credit), so the selection is a **count-scaled allowance
clocked from the last reinforcement**: an obs is dropped once it has gone
`obs_evict_min_age × observation_count` generations without being reinforced (`obs_evict_min_age =
4`). Yes — the allowance is literally that product: a once-seen obs gets one 4-generation window, a
count-10 obs gets ten of them (40 generations of grace), and any reinforcement restarts the clock.
The rationale for scaling by count is that a lesson which has recurred many times is more
established, so it earns proportionally more grace before being dropped. And because any
reinforcement resets the clock, that large allowance only ever bites for an obs that *was* heavily
reinforced and then abruptly stopped recurring — it then decays on a long tail proportional to how
established it had become, rather than vanishing the moment it goes quiet. (The base window is 4, not
a tighter 2, because most obs are one-off singletons — game situations are diverse — and a window of
2 dropped ~250 obs per generation and starved synthesis.) So a still-recurring lesson keeps
surviving, while a
lesson that stopped recurring eventually decays no matter how often it was once seen — nothing in
the store is immortal, which matters because store size is exactly what the per-tick clustering
cost used to scale with.

*(Revised 2026-07-14, store-bounding review — log §4.)* The original rule was age × frequency:
drop only obs that were BOTH old AND never reinforced. That made any obs with count ≥ 2 immortal —
the store's one unbounded term (report §5, pathology 8). The count-scaled rule strictly
generalizes it: for a count-1 obs the two rules are identical. `obs_evict_max_count` was deleted
as subsumed.

The two scenarios are worth separating, because they are what the earlier drafts blurred. *While an
obs keeps recurring:* each reinforcement bumps its `observation_count` and resets its decay clock,
and — because the record key is a stable UUID (§2) — it does so while keeping its original first-seen
age. This is the "old but still proven" case the rule is built to keep alive (principle 4); it is
never evicted. *Once such an obs stops recurring* for its full (now large) allowance, it is dropped
from the store like any other, and its UUID — with the accumulated count and history attached to it
— is gone. The named trade-off is what happens after that: if the same lesson is re-extracted in a
later game, it re-enters under a *fresh* UUID as a count-1 singleton with no history, and can
re-trigger synthesis of an already-distilled lesson. So yes — it is evicted only after it passes the
threshold, and a later re-arrival genuinely starts afresh; the rule trades a bounded store for that
occasional re-litigation. The ruled fallback, if a live run shows the scaled rule failing to bound
the store: a per-cell size ceiling that evicts the least-recently-touched obs. Decay runs before
synthesis in the tick (`strategy_points.md` §1), so the synthesizer only distills surviving evidence.

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

In cost terms the pass is bounded by *inflow*, not store size. Each new obs is compared only against
its top-k nearest neighbours, and the KEEP/DISCARD decision is one flash-lite judge per new-obs
cluster — so the paid work is at most O(new obs) per generation and does not grow as the store
grows. The cosine search that *finds* those neighbours is O(cell size) per query, but that is cheap
arithmetic, the deterministic tier of principle 3, not the paid LLM tier. This is the property that
lets an online (per-generation) pass stay affordable while the store accumulates.

Why observations keep an online (per-generation) dedup pass at all, when tells retired theirs. Two
clarifications first, because this is easy to misread. It is *not* that tells skip deduplication —
tells are deduped too, just in a batch at the epoch fold rather than online after every game.
("Epoch-quantized" is the jargon for exactly that: curation is allowed to happen only at fixed fold
boundaries, in discrete steps, never continuously — the way a quantized value can only take set
levels.) And your instinct that the online tell dedup "wasn't very useful" is right, and then some:
the online tell pass was retired in 2026-07-12 because it was both the most expensive component in
the whole pipeline (178 LLM calls per game) *and* actively harmful — judging wordings one at a time
fragmented the most important tells, splitting a single bandwagon tell across three near-duplicate
entries (`tells.md` §2). So retiring it improved quality and cost at once.

What made retiring it *safe* is the downstream point: a tell has no same-cadence consumer. Nothing
in a game needs that game's tells before the next fold, so batching their dedup to the fold — a
delay of at most ~10 games — costs nothing. Observations have neither luxury. The very next tick's
synthesis clusters directly over the observation store, so an observation duplicate left standing
until some later batch pass would distort that clustering and double-trigger the new-evidence gate.
That in-cadence consumer is precisely what forces observations to dedup online while tells can wait.

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

1. **~~The §6.8 wiring gap~~ — RESOLVED 2026-07-15** (report §6.8; the design is §1 above). The v7
   retirement of observation injection is now enforced in the run path, not just documented. A
   `LoopConfig.retrieval_types` knob defaults to `strategy_points_only`, and the loop driver passes
   `--retrieval-types` to every game in both arms. A per-generation invariant,
   `assert_observations_retired`, then fails loud if either the recorded per-game config re-enabled
   observation retrieval, or any memory-ON decision's recorded `retrieved_observations` slot is
   non-empty — so an obs+SP arm can never launch silently under the SP-only default. (`"both"`
   deliberately re-enables obs injection for a v5/v6 comparison arm.) No longer a launch blocker.
2. **Decay will not bind within the experiment horizon — the store won't be seen to plateau.** This
   is sharper than "unverified" (raised 2026-07-15). The allowance is `4 × observation_count`
   generations (§3), so in a ≤10-generation run an obs that reached count ≥ 3 needs ≥12 quiet
   generations and is effectively immortal; in practice decay only ever culls count-1 singletons
   in-run. The size bound is therefore a *limit* property the experiment cannot exercise, and the obs
   store grows close to monotonically over the run. This is mitigated for *cost*: the store-bounding
   review decoupled per-tick clustering cost from store size (gates-before-cluster + seed-from-new,
   §4 and `strategy_points.md` §2), so the live risk is stale obs joining synthesis clusters as
   members, not a cost blow-up. Whether the store would ever plateau at this decay-vs-generation rate
   is unestimated — the v2 smoke's ~6 generations won't fit a convergence curve. The ruled LRU
   fallback (§3) exists for exactly this contingency. Post-run readout: expect near-monotonic growth,
   and judge whether it matters at the run's scale.
3. **Near-duplicate accumulation between repairs** — the online pass keeps near-dups separate by
   design, so the store carries paraphrase redundancy until an offline batch pass runs; at run
   scale this is bounded by decay, but no schedule pins when (or whether) a batch repair runs
   during the v7 run. Minor; flagged so the post-run store read expects it.
