# Store curation — how the three memory stores grow, stay bounded, and improve

> **Scope:** the mechanism record for the loop's store layer. Three stores persist across games —
> **observations** (evidence a game generated), **strategy points** (directives an agent may
> follow), and **tells** (behavior→role facts the world exhibits) — and each has curation rules
> that decide what enters, what survives, and what reaches an agent's prompt. This doc is the
> framework: the stores and their layers (§2), the operation classes every rule belongs to (§2),
> why the mechanisms differ per store (§4), what is verified (§5), and the open review points
> (§6). Per-store mechanism detail lives in three companion docs in this folder:
> [`observations.md`](observations.md) · [`strategy_points.md`](strategy_points.md) ·
> [`tells.md`](tells.md).
> **Role in the run program:** review basis for the consolidation ownership walkthrough (the §R
> "D2" gate in [`../execution_plan/compounding_measurement_plan.md`](../execution_plan/compounding_measurement_plan.md)).
> §6 is the walkthrough agenda; its item numbers are stable references (the log and the plan cite
> them) — new items append, existing items never renumber.
> **Companions:** the per-item utility curation consumes is the credit layer
> ([`../credit/report.md`](../credit/report.md)); upstream instruments and build journeys are
> named per store in §3's lifecycle maps.
> **Status:** first written 2026-07-14 (as `evidence/consolidation/report.md`), revised the same
> day across three review sessions (log §4–§7). **Restructured 2026-07-15**: folder renamed to
> `store_curation/`, per-store detail split out. Section map for readers of the frozen log and
> plan: the old §2 (SP tick, incl. §2.1 observation decay) is now
> [`strategy_points.md`](strategy_points.md) + [`observations.md`](observations.md); the old §3
> (tell tick) is now [`tells.md`](tells.md); §1/§4/§5/§6 numbering is unchanged. Suite 684 green
> at the 07-14 review, uncommitted, `feature-dimension-schema`. Of the §6 agenda, open: §6.2's
> tracked prefilter limitation, §6.4's signing-time pin, and §6.5's post-run readout.

> **Orientation — one loop, two curation ticks, three stores.** Each generation of games feeds all
> three stores, and each store is curated before the next generation reads it:
>
> **games → extraction (observations) + mining (tell wordings) → credit (per-item utility)
> → SP consolidation *(every generation; carries observation decay)* + tell fold *(every epoch)*
> → store v(g+1) + checklist v(k+1) + injected book → next games**
>
> Compounding, mechanically, IS this curation: without it the stores only append, and an appending
> store gets worse, not better (§1). Credit is the input to curation and the referee of nothing —
> whether the loop *helped* is always measured outside it (credit report §1).

---

## 1. Why stores need curation at all

An uncurated memory store degrades in two distinct ways, and the loop's first paid run demonstrated
both (the "§12 bloat record", cited in the config's own comments):

- **Volume**: run-1 grew the SP store from 0 to 227 with no ceiling — bloated cells carried ~34 SPs
  where healthy cells ran ~5. Retrieval quality and prompt budget both degrade with cell size, so
  growth alone erodes the very effect the store exists to produce.
- **Quality**: without prune/evict, an SP that measures *harmful* keeps being retrieved and followed
  forever, and near-duplicate SPs smear one lesson's credit across several rows so none of them ever
  accumulates enough evidence to act on.

The other two stores degrade the same two ways at their own grain. The tell store: mining produces
a new wording for essentially the same behavior in almost every game (the same tell arrived as 27
distinct wordings in one 30-game sample), and a checklist that only grows makes detection cost
scale with corpus size instead of game count. The observation store: the same lesson re-arrives
reworded every game, and an observation that can never be dropped makes store size — and the
clustering cost that scales with it — unbounded.

So every store's curation does the same three verbs — **keep** what earned its place, **drop** what
measured dead or harmful, **grow** only where fresh evidence justifies it — implemented differently
per store (§4 explains why they cannot be one mechanism).

For concreteness, the three item kinds being curated. An observation is a situation → approach →
outcome record extracted post-game into one of 17 (role, phase) cells (this one from the v2 smoke
run's store, `observation_count: 2` — the same lesson arrived twice):

> *situation:* "Day 1, an information-starved opening where you established a baseline of being a
> helpful, cautious voice …" → *approach:* "You advocated for a measured pace on Day 1 to delay any
> momentum against you and discourage early investigation." → *outcome:* "Positive; successfully
> steered the village away from identifying an early target, preserving your anonymity."

A strategy point is a situation-conditioned directive with live counters (lifted from a smoke-run
store, trimmed):

> *situation:* "Healer is operating during day discussion … Stakes: maintaining your status as an
> unexposed power role is more valuable than pushing a specific lynch early …" → *action:* (a
> directive the agent may follow), with counters `follow_count / positive_count / negative_count`.

A tell is a falsifiable behavior→role fact (this one from the v1 seed book, `tell_id: disc_530`):

> "A player who is being accused of holding a hostile role counter-accuses their accuser of using
> the role claim as a distraction to protect themselves." — evil 27/30, shrunk lift +0.49.

## 2. The framework — stores, layers, operations

### 2.1 The three stores and their layers

Each store has *persistent* layers (what survives between games) and a *consumption* layer (what an
agent actually sees). Keeping the two apart matters: most curation acts on the persistent layers,
and only a small, bounded surface ever reaches a prompt.

| | Observations | Strategy points | Tells |
|---|---|---|---|
| One item is | evidence: a situation→approach→outcome record | a directive: situation-conditioned advice with follow/outcome counters | a fact: "behavior X marks role Y", carried by instances |
| Persistent layers | per-cell store (17 role×phase cells) + a generation sidecar carrying each record's first-seen and last-reinforced clocks | per-cell store with two implicit lanes — **proven** (positive lift, ≥2 follows) and **contested** (everything else) | **ledger** (`instances.jsonl`, append-only event rows) → **canon** (`canon.json`, every identity ever admitted) → **checklist** (`checklist_v{k}.json`, the ≤48/channel active-duty card detection scans for) |
| Consumption layer | **none in v7, by design** — synthesis substrate only; the injection role obs held in v5/v6 is superseded by the tell book (§6.8, RESOLVED: the run wiring now enforces this) | RAG retrieval (top-k, proven tiering, exploration slot) → injection ≤3 per situation | the **book** — a role-identification manual built from the ledger at fold time, injected at game start |
| Curation cadence | every generation (online dedup at game fold; decay inside the SP tick) | every generation (synthesis every 2) | every epoch (the fold); frozen checklist between folds |
| Code anchors | `evaluation/src/loop/merge.py`, `consolidate.py` | `evaluation/src/loop/consolidate.py`, `credit.py` | `evaluation/src/loop/tells.py`, `tell_credit.py`, `tell_fold.py`, `Agents/memory/tell_book.py` |

### 2.2 The operation taxonomy

Every curation rule in the system belongs to one of six classes. The class names are used
consistently in the per-store docs; where the codebase uses a different verb, this table is the
canonical definition.

| Class | What it does | Observations | Strategy points | Tells |
|---|---|---|---|---|
| **Growth** | adds items | post-game extraction (one pass per role×phase cell) | **synthesis** — the system's only *generative* op: an LLM writes new directive text from observation clusters, behind three gates | **mining** — discovers wordings in transcripts; the fold only admits, never writes |
| **Admission** | resolves an arriving item's identity: new, or a duplicate of an existing one | online freeze-old dedup at game fold — triage-only: exact duplicates collapse and pool counts; near-duplicates are kept separate | post-synthesis KEEP/DISCARD dedup — freeze-old, duplicate's counts absorbed by the credited older survivor, never a text merge | fold wording-resolution {keep, discard} — a new wording dies into a canonical or becomes a new probation canonical; canonical text never rewritten |
| **Removal** | drops or retires items, on evidence | **decay** — dropped after `obs_evict_min_age × observation_count` generations without reinforcement | **prune** (measured harmful: lift < −0.15 at ≥8 follows) + **evict** (dead weight: retrieved ≥8×, never followed — with mercy rules) | **archive** — probation singleton after 12 scanned games, or fat-support null lift (with a split-check flag); archive is retirement, never deletion |
| **Protection / promotion** | shields earned items, gives candidates a path to earn | any reinforcement restarts the decay clock | proven exemption (never dropped), proven tiering at retrieval, a guaranteed exploration slot for the best unproven candidate | probation→incumbent on recurrence; direction-balanced checklist quota; archive rotation re-audits retired tells at zero marginal cost |
| **Bounding** | keeps size and per-tick cost flat as history grows | decay is the size bound; clustering seeds from new arrivals only, so cost tracks inflow, not store size | admission gates run before any clustering; `synth_cell_unproven_cap = 12` caps the contested lane | checklist cap (48/channel) bounds detection; match-index cap (~65/channel) bounds wording resolution; epoch quantization bounds curation frequency |
| **Repair** | offline, evidence-ratified correction — never part of the routine tick | batch dedup (the full-store pass; merge with count pooling lives here) | a report-only batch-dedup pass over any seeded store before launch (§6.4) | the strong-model audit every ~3 epochs — the only place existing canonicals merge or split, ratified by pooled-lift arithmetic |

Four removal verbs, one distinction each — they are not synonyms. **Decay** removes for lack of
fresh evidence (nothing graded an observation; recurrence is its only signal). **Prune** removes on
measured harm (the item was followed and outcomes were bad). **Evict** removes dead weight (the
item was offered and never once used on the merits). **Archive** removes from *active duty* only —
the tell keeps its rows and can re-earn its way back.

### 2.3 Cross-cutting principles

Five rules recur across all three stores; the per-store docs point back here rather than
re-arguing them.

1. **Credit is input, never referee.** Curation consumes per-item utility (realized lift, hit-rate
   lift) to decide keeps and drops, but whether the loop *helped* is measured by instruments
   outside it. Without this split, the loop would grade its own homework.
2. **Identity boundaries protect credit continuity.** An item's accumulated evidence is only
   meaningful while the item keeps meaning the same thing. Hence: SP text is never merged (one of
   the two directives would stop meaning what its counters measured), tell text is never rewritten
   (a tell's meaning is which transcript moments count as instances), and dedup boundaries are
   **freeze-old** (only new arrivals can die; survivors keep their history). Observations are the
   deliberate exception — an obs is evidence, not a commitment, so exact duplicates pool their
   counts.
3. **Deterministic-cheap runs before paid-LLM.** Admission gates are key arithmetic; exact-match
   runs before the embedding prefilter, which only *nominates* candidates for the LLM judge (house
   rule: an embedding never judges). The tell side quantizes curation to epochs because tells have
   no same-game consumer — the delay is free, and batching the judgment made it more accurate:
   the retired online pass was both the pipeline's most expensive component (178 LLM calls/game)
   and the one that fragmented the head 2×.
4. **Nothing dies of age alone.** Removal requires evidence: an SP leaves by souring or by being
   dead weight (the proven exemption overrides every drop rule); an obs survives as long as it
   keeps recurring; an archived tell re-enters via rotation or recurrence. A pure age rule would
   delete rare-but-proven lessons, which is the exact content the store exists to keep.
5. **A curation mistake must not bake in.** Tell tallies recompute from ledger rows on every fold
   (set, not accumulate); the fold's publication tripwire crashes rather than publish shrunken
   counts; seed-store repair runs report-only first; merge/split of existing identities needs the
   audit's pooled-lift evidence.

## 3. The three stores in brief

Each store's full mechanism, knobs, and per-store gaps live in its own doc. This section is the
map: what each store is for, and where each lifecycle step's instrument and record live.

### Observations → [`observations.md`](observations.md)

The evidence layer: what happened, per (role, phase) cell, feeding SP synthesis. Carries no credit
(nothing "follows" an observation), so its curation runs on recurrence alone.

> **Lifecycle:** game → post-game per-cell extraction (record:
> [`../extraction/post_game/`](../extraction/post_game/report.md)) → online freeze-old dedup at
> game fold (`loop/merge.py`; design + goldens: [`../dedup/`](../dedup/report.md)) → count-scaled
> decay each generation → clustering substrate for SP synthesis. In v7, that is where the
> lifecycle ends: observations no longer reach prompts (§6.8, RESOLVED: the run wiring enforces it). Offline
> repair: batch dedup ([`../dedup/batch_architecture.md`](../dedup/batch_architecture.md)).

### Strategy points → [`strategy_points.md`](strategy_points.md)

The directive layer: distilled advice an agent may follow, credited by realized outcomes. The only
store with a *generative* growth step, which is why most of the system's guards concentrate here.

> **Lifecycle:** observation clusters → credit-aware synthesis every 2 generations, behind three
> gates (design lineage:
> [`../v7_final/consolidation_design.md`](../v7_final/consolidation_design.md)) → KEEP/DISCARD
> dedup → per-decision credit (record: [`../credit/report.md`](../credit/report.md)) → prune/evict
> with mercy rules → retrieval (proven tiering + exploration slot) → injection, ≤3 per situation.

### Tells → [`tells.md`](tells.md)

The fact layer: falsifiable behavior→role associations, credited off-policy (every exhibitor in
every game counts, whether or not anyone read the book). Grows by discovery, never by generation.

> **Lifecycle:** game → per-game mining + detection against the frozen checklist v_k (instrument +
> journey: [`../extraction/tell_extraction/`](../extraction/tell_extraction/experiment_log.md)) →
> epoch fold: resolve wordings, append ledger rows, rule verdicts, publish checklist v(k+1) →
> book built from the ledger at fold time, injected at game start (ledger design + rejected
> alternatives:
> [`../credit/read_tactic_credit_redesign.md`](../credit/read_tactic_credit_redesign.md) §3).
> Offline repair: strong-model audit every ~3 epochs.

## 4. Why the mechanisms differ per store

Every structural difference below traces to one root: **an observation is evidence a game
generated; a strategy point is a directive an agent follows; a tell is a fact the world exhibits.**

| | Observations | Strategy points | Tells |
|---|---|---|---|
| Item's meaning lives in | the recurring lesson — a rewording is the *same* evidence | its directive text | its instance set (which transcript moments count) |
| Credit arrives | never — nothing follows an obs, so there is no outcome to grade; recurrence is the only signal | usage-gated — only when followed, so the store must *manage exploration* (tiering, exploration slot) | off-policy — every exhibitor counts, so candidates mature uninjected and need no exploration slot |
| Growth step | extraction — new evidence arrives every game regardless of curation | **generative** — synthesis writes new text, so growth itself can create bad content | discovery — mining finds wordings; admission never writes |
| Duplicate handling | exact duplicates pool counts (evidence accumulates) | keep/discard onto the credited survivor; never merge | drop-or-keep at the door; instance always kept; text never touched |
| Removal evidence | stopped recurring | measured harmful, or dead weight | insufficient or null instance evidence — and reversible |
| Cadence | every generation | every generation (synthesis every 2) | every epoch, frozen checklist between |

The asymmetry that matters most for the walkthrough: the SP tick can *create* bad content
(synthesis is an LLM writing directives — hence the cap, the track record, and the dedup chasing
it), while the tell tick can only *mis-file* content (wrong-merge, wrong-archive — hence
freeze-text, recompute-from-rows, and the audit). The observation store can do neither; its risk is
pure volume, which is why decay is its one substantive rule. The failure modes are disjoint, which
is why the guards look nothing alike.

## 5. What is verified, and by what

- **Unit suite**: the loop modules are covered by the loop tests (684 green, 2026-07-14,
  uncommitted working tree on `feature-dimension-schema`; the store-bounding revision added
  count-scaled decay, sidecar-stamping, gate-ordering, and seeded-clustering tests; the §6.7 lane
  ruling added contested-lane-cap and exploration-slot tests; the fold-ownership review added
  tripwire and bounded-index tests). Pure prune/evict and the fold logic are LLM-free by
  construction, so their tests run offline.
- **SP side — the negative-record ledger.** The v7 loop runs are invalid for the compounding
  *thesis* (v7_final report, §5c confound), but they were productive as mechanism stress tests:
  every SP-side guard traces to a named store pathology, most surfaced by a run or a review of run
  output. This table is the consolidated inventory (each row's mechanism is argued in the
  per-store doc cited; the credited baselines pruning relies on are guarded by
  `invariants.py::assert_baseline_coherence`, credit report §3):

  | # | Store pathology | Surfaced by | Standing guard |
  |---|---|---|---|
  | 1 | Unbounded SP growth — store 0→227, bloated cells ~34 SPs vs healthy ~5 | run-1 (the §12 bloat record) | per-cell cap; since 2026-07-14 on the contested lane (`strategy_points.md` §2) |
  | 2 | Cluster re-synthesis compounding ~6×/run — variants of already-distilled lessons that don't exact-dedup | loop-run store records (5.4 → 34 SPs/cell) | new-clusters-only gate; clusters seed from new arrivals (`strategy_points.md` §2) |
  | 3 | Silent synthesis stall — the net-change trigger cancels arrivals against decay and reads "no new obs" | gen 6 of the v2 smoke | arrivals counted by first-seen generation, via the driver sidecar (`strategy_points.md` §2) |
  | 4 | Harmful-tail escape — prune-first ordering let dedup's count-absorption push a bad SP back over the threshold for a generation | run outcome forensics (the below-baseline tail) | prune runs last, on post-dedup counts (`strategy_points.md` §1) |
  | 5 | Credit smearing — near-duplicate SPs split one lesson's follows so no row ever accumulates actionable evidence | design review 2026-06-19 | freeze-old KEEP/DISCARD SP dedup onto the credited survivor (`strategy_points.md` §3) |
  | 6 | Wrong-blame eviction — deleting good content over a retrieval/scoping miss | the §0.4/§0.5 fix program | verdict-aware evict: override-dominant evicts, not_relevant-dominant spared (`strategy_points.md` §4) |
  | 7 | Exploration starvation — credit is usage-gated, so a never-retrieved candidate never earns | §6.7 review, 2026-07-14 | guaranteed exploration slot at the retrieval cap + contested-lane quota (`strategy_points.md` §5) |
  | 8 | Observation immortality — any obs at count ≥ 2 escaped decay forever, leaving store size unbounded | store-bounding review, 2026-07-14 (log §4) | count-scaled decay clocked from last reinforcement (`observations.md` §3) |
  | 9 | Clustering cost scaled with total store size and was paid even by gated-out cells | store-bounding review, 2026-07-14 (log §4) | gates before clustering; seed-from-new (`strategy_points.md` §2) |
  | 10 | Incremental dedup non-convergence — old entries re-litigated as neighbors land, eroding the store past the ~17% sweet spot | dedup campaign, 2026-06-09 ([`../dedup/incremental_convergence.md`](../dedup/incremental_convergence.md)) | freeze-old apply-guard (old↔old operations forbidden), live in the loop's obs fold |
  | 11 | Halo-weighted synthesis regenerates what prune killed — observation outcome tags track faction-won, i.e. luck | design 2026-06-19 (consolidation_design) | credit-aware synthesis over the realized track record (`strategy_points.md` §2) — mechanism-verified only, quality unmeasured |
- **Tell side, simulation before code**: the 30-game ledger simulation (tell-extraction log §10)
  replayed 1,109 mined rows through the spec — the funnel held (probation absorbed ~12%, recurrence
  re-entry fired), the head concentrated, and it produced the finding that killed the online dedup
  (2× head fragmentation). Its headline was then *re-scoped, not retracted*, by consolidation №1
  (log §11): batch consolidation took the store 740→596 (−19.5%), and splitting the "no saturation"
  curve showed the **recurring core converges** (~140 tells with support ≥2 at 30 games) while a
  flat ~16/game **singleton tail** keeps arriving — open vocabulary at move grain, so mining is a
  standing per-game pass and the bounded checklist is THE cost-control mechanism. Channel asymmetry
  is real (vote 38% redundant vs discussion 8% — small action alphabet), and the batch judge's
  measured wrong-merge rate was 1/44. The consolidated store seeds the v1 checklist.
- **Not yet verified**: no fold has run inside a live generation loop (the `--tells` smoke is the
  queued next step); everything cited above is offline replay on the v6ab archive, one epoch old.

## 6. Open review points — the walkthrough agenda

Ordered by criticality. Items 1–7 were the 2026-07-14 review agenda; their numbering is frozen
(the log and the execution plan cite it). Resolved items keep a short verdict here — the mechanism
they produced is described in the per-store doc, and the review narrative is in the log entry
cited.

1. **RESOLVED 2026-07-14 — the fold publication tripwire is built** (ruled and built same day; log
   §7). The fold is the critical path — a bad fold publishes a bad checklist that detection runs
   against for a whole epoch with no in-epoch correction. Two always-on deterministic invariants
   now gate persistence and publication: monotone detected support (a recount may never shrink —
   shrinkage means ledger rows were silently lost) and head continuity (a top incumbent leaves
   only via this fold's explicit null-lift verdict). Mechanism: `tells.md` §4. Residual, tracked:
   wrong keep/discard verdicts at the single-wording grain remain possible; the tripwire catches
   their *systematic* form, and the periodic audit stays the semantic backstop.
2. **Threshold provenance is mixed — top-ranked knob now checked, rest pinned.** Evidence-anchored:
   the SP cap (bloat record), the credit window (density calculation). Design-anchored, never
   swept: `prune_tau = −0.15`, the three follow/retrieve floors (8/8/2), `K_PROBATION = 12`, the
   null-lift cut (0.03 at n≥20), the prefilter (0.80/top-3), the checklist caps (25/15/48). The
   review ranked `prune_tau` as the only knob that could plausibly flip a run conclusion: every
   generation the loop *deletes* SPs whose lift falls below τ, and the compounding story assumes
   those deletions remove genuinely bad directives — if lift at that threshold were mostly noise,
   pruning would be deleting near-randomly, good SPs included. The held-out check ran 2026-07-14
   (`heldout_credit_reproduction`, zero spend; method and full numbers: `strategy_points.md` §6):
   Pearson(lift_A, lift_B) = +0.54 at n = 31, A-flagged losers stayed negative on the held-out
   half 8/9 against a 61% base rate, and the one flip sat below the prune rule's ≥8-follow floor.
   Direction-credible at small n: the prune rule cuts reproducible signal, not noise. Tracked
   limitation: the tell-side prefilter (0.80/top-3) remains uncalibrated — the data to calibrate
   it exists (the 30-game sim's resolved rows), but a replay harness is a new instrument and the
   closing rule is no new complications pre-run. The remaining knobs are pinned as design-anchored
   in the pre-reg, with a post-run sensitivity readout.
3. **RESOLVED 2026-07-14 — the fuzzy match index is bounded** (owner ruling: a simple hard cap
   over the ledger design's unseen-based retirement, "easy to build, easy to explain"; built and
   suite-verified same day, log §7). Wording resolution now consults ~65 candidates per channel,
   flat as the singleton tail grows; retirement from *matching* is not deletion. Mechanism and the
   three-cap disambiguation: `tells.md` §3/§5. Tracked limitations: the 30/10 window sizes are
   design-anchored (unswept); the fold-time recompute-from-rows scan is linear in total history
   (trivial at run scale; snapshotting is the fix if it ever matters).
4. **SP dedup only runs when synthesis added SPs** (`cfg.sp_dedup and syn.get("added")`). A seeded
   store's pre-existing near-duplicates are never collapsed in-loop — the run's seed store must
   arrive already deduped. *Resolution path (2026-07-14):* the pre-reg is silent on the SP store's
   starting state and must pin it at signing. Cold start (as both v2 smokes) closes this by
   construction; a seeded store gets one report-only batch-dedup pass first.
5. **Probation pressure under open vocabulary.** The sim's funnel was healthy at 30 games, but the
   flat singleton inflow means the 15-slot probation lane is permanently contested; beyond 30
   games the rotation/starvation behavior is unmeasured. Post-run readout, not a blocker.
6. **RESOLVED 2026-07-14 — the role-revealing exclusion is removed** (owner ruling, pre-reg §5
   records it): the book is a role-identification manual for every unrevealed role, selection
   re-based on subject-role concentration, launch seed rebuilt (`tell_book_v2_seed.json`, 34
   entries, all six roles). Mechanism: `tells.md` §6. Residual for the walkthrough: the
   injection-channel screen (27.5% changed, direction positive) was measured on the v1
   wolf+SK-only book — the v2 book is unscreened, and its weakest tail entries
   (vigilante/healer at lift +0.03–0.06) are near-prior; whether the book needs a
   minimum-strength floor is a fair probe.
7. **RESOLVED 2026-07-14 — SP cells adopt the two tell-style lane pieces that transfer** (owner
   ruling, same day it was raised; log §5): the synthesis cap re-scoped to the contested lane, and
   a guaranteed exploration slot at the retrieval cap. Rejected, reasons standing:
   archive-with-rotation (an archived SP would need paid retrieval slots to re-earn; the obs store
   already serves as the SP's archive, since deletion plus re-synthesis is the SP-native re-audit
   path) and a probation deadline (a generation-based clock would kill rare-situation SPs).
   Mechanism and residuals: `strategy_points.md` §5.
8. **RESOLVED 2026-07-15 — the v7 obs-injection retirement is now wired into the run path** (found
   while restructuring this folder, ruled + built the same day; log entry 8). The design stands
   (prompts carry tells + SPs; observations are synthesis substrate only) and the wiring now
   enforces it: a new `LoopConfig.retrieval_types` knob defaults to `strategy_points_only`, the
   loop driver passes `--retrieval-types` to every game (both arms), and a per-generation invariant
   (`assert_observations_retired`) fails loud on two record surfaces — the recorded per-game
   `retrieval_types_config["observations"]` and every memory-enabled ON decision's recorded
   `retrieved_observations` slot — so an obs+SP arm can never launch silently under the SP-only
   default. `"both"` reproduces
   the v5/v6 obs+SP injection for a comparison arm. Mechanism: `observations.md` §1. Two notes,
   unchanged: pulling observations out of prompts changes generation behavior, so it stays in the
   same epoch bundle as the other prompt-affecting changes; and the static-memory claim rungs that
   used obs injection (v5/v6 arms) are unaffected — this was a v7 arm-definition item, not a retraction.

## Sources

- Code (maintained): `evaluation/src/loop/consolidate.py` · `merge.py` · `tell_fold.py` ·
  `tell_credit.py` · `tells.py` · `config.py` (knob rationale lives in its comments) ·
  `Agents/memory/tell_book.py` · `Agents/memory/strategy_synthesis.py` (the synthesis prompt) —
  module table in [`evaluation/src/loop/README.md`](../../evaluation/src/loop/README.md).
- Per-store mechanism docs (this folder): [`observations.md`](observations.md) ·
  [`strategy_points.md`](strategy_points.md) · [`tells.md`](tells.md); review record:
  [`experiment_log.md`](experiment_log.md).
- Evidence cited: tell-extraction log §10 (ledger sim) · §11 (consolidation №1) · §12
  (epoch-quantization ruling) · §16 (granularity screen)
  ([`../extraction/tell_extraction/experiment_log.md`](../extraction/tell_extraction/experiment_log.md));
  the credit layer and its invariants ([`../credit/report.md`](../credit/report.md)); the v7 run
  pre-registration draft
  ([`../execution_plan/v7_run_preregistration_DRAFT.md`](../execution_plan/v7_run_preregistration_DRAFT.md)).
- Design lineage: [`../v7_final/consolidation_design.md`](../v7_final/consolidation_design.md)
  (2026-06-19, SP side) · the tell ledger spec in
  [`../credit/read_tactic_credit_redesign.md`](../credit/read_tactic_credit_redesign.md) §3.
