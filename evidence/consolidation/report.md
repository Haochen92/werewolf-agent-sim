# Consolidation — how the two memory stores compound

> **Scope:** the mechanism. The compounding loop has **two curation ticks**, one per memory kind:
> **SP consolidation** (`evaluation/src/loop/consolidate.py` — observation decay, credit-aware
> synthesis, SP dedup, prune/evict) and the **tell fold** (`evaluation/src/loop/tell_fold.py` —
> wording resolution, instance ledger, probation verdicts, checklist publication, the injected book).
> This doc presents each step with its reason, then the differences that force two mechanisms, then
> the open review points. It is the review basis for the consolidation ownership walkthrough (the
> §R "D2" gate); revisions from that review land here, dated.
> **Companions:** the per-item utility both ticks consume is the credit layer
> ([`../credit/report.md`](../credit/report.md)); the tell ledger's design rationale with its
> rejected alternatives is the design record
> ([`../discussion_tagger/read_tactic_credit_redesign.md`](../discussion_tagger/read_tactic_credit_redesign.md),
> §3); the mining/detection instrument and the runs cited in §5 are the tell-extraction log
> ([`../extraction/tell_extraction/experiment_log.md`](../extraction/tell_extraction/experiment_log.md));
> the SP side's 2026-06-19 design lineage is
> [`../v7_final/consolidation_design.md`](../v7_final/consolidation_design.md).
> **Status:** first written 2026-07-14, against the uncommitted v1 wiring on
> `feature-dimension-schema`; revised the same day across three review sessions — store bounding
> (§2.1–§2.2, log §4), the SP lane ruling (§6.7, log §5), and the fold-ownership review (§3
> orientation, §6.1/§6.3 resolved, §6.2 checked; log §7). Suite 684 green. Of the §6 agenda, what
> remains open: §6.2's tracked prefilter limitation, §6.4's signing-time pin, and §6.5's post-run
> readout.

> **Orientation — one loop, two curation ticks.** Each generation of games feeds both stores, and
> each store has its own keep/drop/grow step before the next generation reads it:
>
> **games → extraction (observations) + mining (tell wordings) → credit (per-item utility)
> → SP consolidation *(every generation)* + tell fold *(every epoch)* → store v(g+1) + checklist
> v(k+1) + injected book → next games**
>
> Compounding, mechanically, IS these two ticks: without them the stores only append, and an
> appending store gets worse, not better (§1). Credit is the input to both and the referee of
> neither — whether the loop *helped* is always measured outside it (credit report §1).

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

The tell store degrades the same two ways at a different grain: mining produces a new wording for
essentially the same behavior in almost every game (the same tell arrived as 27 distinct wordings in
one 30-game sample), and a checklist that only grows makes detection cost scale with corpus size
instead of game count.

So each store has a curation tick whose job is the same three verbs — **keep** what earned its
place, **drop** what measured dead or harmful, **grow** only where fresh evidence justifies it —
implemented very differently per store (§4 explains why they cannot be one mechanism).

For concreteness, the two item kinds being curated. A strategy point is a situation-conditioned
directive (this one lifted from a smoke-run store, trimmed):

> *situation:* "Healer is operating during day discussion … Stakes: maintaining your status as an
> unexposed power role is more valuable than pushing a specific lynch early …" → *action:* (a
> directive the agent may follow), with live counters `follow_count / positive_count / negative_count`.

A tell is a falsifiable behavior→role fact (this one from the v1 seed book, `tell_id: disc_530`):

> "A player who is being accused of holding a hostile role counter-accuses their accuser of using
> the role claim as a distraction to protect themselves." — evil 27/30, shrunk lift +0.49.

## 2. The SP tick — `consolidate.py`, every generation

One call (`consolidate`) runs four steps in a deliberate order:
**observation decay → synthesis (every k gens) → SP dedup → prune/evict last.**

The ordering is load-bearing at both ends. Synthesis runs before dedup because synthesis *appends*
and dedup exists to collapse what it appended. Prune runs **last**, on the post-dedup counts,
because the dedup absorbs a discarded duplicate's counts into its survivor — which can push that
survivor across the prune threshold. Under the old order (prune first) a strongly-bad SP could
cross the threshold *after* the prune pass, escape for a generation, and get followed — the harmful
tail that dragged outcomes below baseline. There is also a cadence split: the cheap deterministic
steps (decay, prune, evict, credit) run **every** generation, while the one paid LLM step
(synthesis, plus its dedup) runs every `synth_every_k_gens = 2` — culls are fast, growth is slow.

### 2.1 Observation decay

Observations carry no credit (nothing "follows" an observation, so there is no outcome to grade —
credit report §1), so they cannot be pruned by lift. The selection is a **count-scaled allowance
clocked from the last reinforcement**: an obs is dropped once it has gone
`obs_evict_min_age × observation_count` generations without being reinforced. A once-seen obs gets
one 4-generation window; a count-N obs gets N windows; any reinforcement restarts the clock. So a
still-recurring lesson keeps surviving, while a lesson that stopped recurring eventually decays no
matter how often it was once seen — nothing in the store is immortal.

*(Revised 2026-07-14, store-bounding review — log §4.)* The original rule was age × frequency: drop
only obs that were BOTH old AND never reinforced. That made any obs with count ≥ 2 immortal, which
left the reinforced core as the store's one unbounded term — and store size is exactly what the
per-tick clustering cost scales with (§2.2). The count-scaled rule strictly generalizes it: for a
count-1 obs the two rules are identical.

Both clocks (first-seen and last-reinforced generation) live in a driver sidecar keyed by record
key; a reinforcement is detected as a rise in the record's `observation_count`. The record key is
stable across dedup merges, so a merged-and-reinforced obs keeps its original *age* but restarts its
*clock* — exactly the "old but proven" case the rule wants to keep alive. The named trade-off:
evicting a reinforced obs resets its identity. Its next rewording re-enters as a count-1 singleton
with no history and can re-trigger synthesis of an already-distilled lesson, so the rule trades
store size for occasional re-litigation. The ruled fallback, if a live run shows the scaled rule
failing to bound the store: a per-cell size ceiling that evicts the least-recently-touched obs.
Decay runs before synthesis so the synthesizer only distills surviving evidence.

### 2.2 Credit-aware synthesis

Synthesis distills a cell's observation clusters into new SPs. Uncontrolled, this step is the bloat
engine, so three gates sit in front of it:

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
  (positive lift, ≥2 follows — the same predicate as the §2.4 exemption, via a shared helper) occupy
  earned slots outside the quota, so a cell full of proven SPs still admits synthesis and keeps
  exploring; the cap only blocks piling more untested candidates onto an already-full contested
  lane. *(Revised 2026-07-14 from a total-size cap, §6.7 ruling; the knob was renamed from
  `synth_cell_sp_cap`.)* 12 is anchored on the bloat record: ~2.4× the healthy ~5, well under the
  ~34 runaway — and the record's runaway population was overwhelmingly unproven duplicates, so the
  same value protects against the same failure. The cap gates *growth*, not size: culls run every
  generation and synthesis only every k, so a capped cell resumes growing once credit drains its
  lane (an unproven SP leaves by proving out, souring, or eviction). Capped cells are counted and
  printed per generation, so the gate biting is observable, not silent.

The gates also run **before any clustering work** *(revised 2026-07-14, store-bounding review — log
§4)*. Admission needs only record keys, the generation sidecar, and the cell's SP lane counts —
all deterministic arithmetic — so a skipped cell pays zero embedding cost; previously every cell was fully clustered first (one
embedding search per obs) and the gates only cut the LLM calls, which left the clustering bill
scaling with total store size. An admitted cell then seeds its clusters **from the new arrivals
only**: each new obs pulls in its neighbors, and old obs still join clusters as members. This
reproduces exactly the new-bearing clusters the new-clusters-only gate keeps, without building the
all-old clusters it would discard. A depleted cell keeps full seeding, because its replenish path
must re-synthesize from old clusters. By construction, the per-tick clustering cost now scales with
the generation's new-obs inflow rather than with store size. (Unchanged: a new obs with no
similarity-0.70 neighbor stays a singleton, and singletons are never synthesized — a lone
observation waits for corroborating evidence before it can fire.)

What makes the synthesis credit-*aware* is the **track record**: the realized lift of every cell SP
with ≥ `synth_track_min_follow = 5` follows is rendered into the synthesis prompt ("realized lift
+0.26, followed 9×: <action>…"), so the model revises toward what measured well rather than
re-summarizing the observations blind. Two pieces of bookkeeping make this auditable: the
`with_track_record` counter exposes per generation how many cells actually synthesized with a track
record (0 means the thesis mechanism is silently not firing yet), and every new SP carries
`distilled_from` — the keys of the SPs whose record fed its synthesis — so a revised SP joins back
to its parents' credit history offline (lineage, never shown to agents).

### 2.3 SP dedup — keep/discard, freeze-old

Synthesis appends, so a KEEP/DISCARD dedup runs right after it, collapsing a near-duplicate onto the
**credited older survivor**, which absorbs the duplicate's counts and timestamps. Two rules define
it: SPs are never *merged* (combining two directives into one text is incoherent — one of them
stops meaning what its counters measured), and the boundary is **freeze-old** (only the
just-synthesized SPs are candidates to die; prior SPs are frozen, so accumulated credit history
always survives). It reuses the production dedup core on flash-lite — safe here because KEEP/DISCARD
is schema-enforced with no merge text to get wrong.

### 2.4 Prune and evict — with two mercy rules

- **Prune** drops the stably harmful: realized lift < `prune_tau = −0.15` with ≥
  `prune_min_follow = 8` follows. The lift is differenced against the same-instrument memory-OFF
  base for the SP's cell (and `sp_type`), the credit layer's baseline-coherence rule.
- **Evict** drops the dead weight: retrieved ≥ `evict_min_retrieved = 8` times, never followed —
  but only when the rejection was **on the merits**. The verdict counters distinguish "the agent
  applied it and overrode it" (override-dominant → evict) from "the agent said it didn't apply
  here" (`not_relevant`-dominant → **spared**): the latter is a retrieval/scoping miss, and deleting
  the SP would blame content for a retrieval artifact.
- **The proven-SP exemption** overrides both: any SP with positive lift and ≥
  `protect_min_follow = 2` follows is never dropped, by prune, evict, or any future age rule. A
  rare-but-proven lesson survives; degradation is credit-only — an SP leaves the store by souring
  (negative lift) or by being dead weight, never by merely getting old.

## 3. The tell tick — `tell_fold.py`, every epoch

**Three artifacts, one per job** *(orientation added 2026-07-14 after the ownership review — log §7;
these were the review's main confusion point)*. The **ledger** (`instances.jsonl`) is the append-only
event log: every mined and detected instance row, never edited, every tally recomputable from it.
The **canon** (`canon.json`) is the identity registry: every canonical tell ever admitted, with
frozen text and a status (incumbent / probation / archive); ledger rows point at canon entries, and
new wordings resolve against them. The **checklist** (`checklist_v{k}.json`) is the bounded
published subset of the canon (≤48 per channel) that detection actively scans games for. So the
canon gives instances somewhere to be filed, the ledger gives canon entries their evidence, and the
checklist is the active-duty roster drawn from the canon at each fold.

The fold's per-wording op set is exactly **{keep, discard}**, the mirror of SP dedup (§2.3): a new
wording either dies into a canonical (a discard — its instances credit the survivor) or becomes a
new canonical on probation (a keep). Merging or splitting *existing* canonicals is never a fold
operation. It belongs to the periodic strong-model audit, and only on evidence: a proposed merge
must survive pooled-lift arithmetic (a bad merge shows as visible lift dilution), and a null-lift
archive carries a split-check flag. Routine tick = binary verdicts; merge/split = escalation.

### 3.1 The two principles the fold is built on

**Curatorial, never generative.** A tell's meaning lives in its *extension* — which transcript
moments count as instances — so canonical text is **never rewritten**. A newly mined wording either
*dies into* an existing canonical (its instances credit the survivor; the wording is dropped at the
door) or becomes a new canonical on probation. Rewriting text would break denominator continuity
for every already-detected count; wording repair belongs to the periodic strong-model audit, not the
fold. This is the mirror-image of SP dedup's "never merge" rule, for the mirror-image reason: an
SP's meaning is its directive text, a tell's meaning is its instance set.

**Epoch-quantized.** Detection always runs against a **frozen checklist v_k**; curation happens only
at the fold (one per generation — at the run shape of 10 games/generation, the ledger design's N=10
cadence), and a strong-model audit runs every ~3 epochs. An online per-game dedup pass existed and
was retired (2026-07-12): it was the pipeline's most expensive component (178 LLM calls/game) AND
its least accurate — incremental one-at-a-time judging fragmented the head 2× (one bandwagon tell
split 18+11+10 across three canonicals). Tells have no same-game consumer (unlike observations,
which inject into the next prompt), so a ≤10-game consolidation delay costs nothing.

### 3.2 What one fold does

1. **Resolve the epoch's new wordings** against the same-channel canon, cheapest test first:
   normalized exact-match (free) → embedding prefilter (top-3 candidates at cosine ≥ 0.80 — house
   rule: the embedding only *nominates*, never judges) → a strict extensional LLM judge ("same tell
   iff a transcript reader would count the SAME moments as instances of both; a sub-type with a
   distinct mechanism is NOT the same"). Unresolved wordings become new canonicals on probation.
2. **Append instance rows** to an append-only ledger. All tallies **recompute from rows** on every
   fold (set, not accumulate), so a curation mistake never bakes into a counter. MINED rows are
   discovery only; **lift is computed from DETECTED rows exclusively** — mined rows are
   halo-exposed (a miner that has read the whole game), detector rows come from the role-blind
   instrument.
3. **Advance the probation clock** in *scanned games* — games whose detection ran with this tell on
   the checklist. Scanning is what produces evidence, so entry to the ledger can never require
   counts; the clock measures opportunity, not outcome.
4. **Rule verdicts.** A probation tell still a singleton after `K_PROBATION = 12` scanned games →
   archive (an evidence-*volume* cut, direction-neutral). An incumbent with fat support
   (n ≥ 20) and null lift (|shrunk lift| < 0.03) → archive **with a split-check flag** — a null
   blend can hide two directional sub-tells, so the audit re-examines it before it is trusted dead.
   The one forbidden move: never *retain-rank* by lift at thin support — that selects on noise (the
   probe's cleanest town tell began as a lift≈0 singleton).
5. **Publish checklist v_{k+1}**: per channel, up to 25 incumbents ranked by |shrunk lift| under a
   **direction-balanced quota** (evil-leaning and town-leaning both surface — every role's book
   needs candidates), all live probation (newest first, capped at 15), and spare slots up to the
   48-cap rotated to the **least-recently-scanned archive entries** — a zero-marginal-cost re-audit,
   so every archived tell eventually re-earns or re-fails on fresh counts.

Granularity is settled operationally, outside the fold's per-epoch loop: two same-channel tells are
THE SAME iff same instances AND same lift — semantics propose a merge, pooled-lift arithmetic
ratifies it (a bad merge shows as visible lift dilution). The one forbidden fold direction: never
merge a discriminating child into a ~0-lift generic parent.

### 3.3 The injected book

The book is built from the ledger at fold time (`tell_credit.build_book`), not retrieved per turn.
It is a **role-identification manual for every unrevealed role** (owner ruling 2026-07-14, which
removed the draft role-revealing exclusion: behavior→role inference is the mechanism's point, and
the shared book is symmetric — the same information lets wolves hunt an investigator, the healer
protect one, and the investigator learn to conceal). Selection is per (subject role, channel): the
top ~3 tells by **subject-role concentration** (`subject_lift` — the subject's shrunk share of
exhibitors over its cast prior) above a support floor. Note the deliberate divergence from credit:
§6.5 pays **positive evil-lift** tells only (a town-marker read backwards double-counts, and "look
town" credit is farmable), but a town-power-role tell with *negative* evil-lift still belongs in
the book — what pays and what informs are different questions. At render time
(`Agents/memory/tell_book.py`) the only logic is a roles-alive filter — a wolf-marker is dead
weight once both wolves are revealed dead. Arm gating is by environment (`WW_TELL_BOOK` = path to
the book; absent ⇒ empty block, which IS the baseline behavior). The book is public information —
behavior statistics from past games' *revealed* roles — so it needs no role gating or leak check;
every seat may read it.

## 4. Why two mechanisms, not one

Every structural difference below traces to one root: **an SP is a directive an agent follows; a
tell is a fact the world exhibits.**

| | SP consolidation | Tell fold |
|---|---|---|
| Item's meaning lives in | its directive text | its instance set (extension) |
| Credit arrives | usage-gated — only when followed (so the store must *manage exploration*; since the §6.7 ruling, a retrieval slot is guaranteed to the contested lane) | off-policy — every exhibitor in every game counts (so candidates mature uninjected; no exploration slot) |
| Growth step | **generative** — synthesis writes new text from observations | **none** — mining discovers wordings; the fold only admits, never writes |
| Dedup rule | keep/discard, survivor absorbs counts | drop-or-keep at the door, instance always kept; canonical text never touched |
| Cadence | every generation (synth every 2) | every epoch (fold), frozen checklist between |
| Quality verdict | realized lift vs same-instrument OFF base | hit-rate lift vs cast prior |

The asymmetry that matters most for the walkthrough: the SP tick can *create* bad content (synthesis
is an LLM writing directives — hence the cap, the track record, and the dedup chasing it), while the
tell tick can only *mis-file* content (wrong-merge, wrong-archive — hence freeze-text, recompute
from rows, and the audit). Their failure modes are disjoint, which is why their guards look nothing
alike.

## 5. What is verified, and by what

- **Unit suite**: both modules are covered by the loop tests (684 green, 2026-07-14, uncommitted
  working tree on `feature-dimension-schema`; the store-bounding revision added count-scaled decay,
  sidecar-stamping, gate-ordering, and seeded-clustering tests; the §6.7 lane ruling added
  contested-lane-cap and exploration-slot tests; the fold-ownership review added tripwire and
  bounded-index tests). Pure prune/evict and the fold logic are LLM-free by construction, so their
  tests run offline.
- **SP side — the negative-record ledger.** The v7 loop runs are invalid for the compounding
  *thesis* (v7_final report, §5c confound), but they were productive as mechanism stress tests:
  every guard in §2 traces to a named store pathology, most surfaced by a run or a review of run
  output. This table is the consolidated inventory (each row's mechanism is argued at the cited
  section; the credited baselines pruning relies on are guarded by
  `invariants.py::assert_baseline_coherence`, credit report §3):

  | # | Store pathology | Surfaced by | Standing guard |
  |---|---|---|---|
  | 1 | Unbounded SP growth — store 0→227, bloated cells ~34 SPs vs healthy ~5 | run-1 (the §12 bloat record) | per-cell cap; since 2026-07-14 on the contested lane (§2.2) |
  | 2 | Cluster re-synthesis compounding ~6×/run — variants of already-distilled lessons that don't exact-dedup | loop-run store records (5.4 → 34 SPs/cell) | new-clusters-only gate; clusters seed from new arrivals (§2.2) |
  | 3 | Silent synthesis stall — the net-change trigger cancels arrivals against decay and reads "no new obs" | gen 6 of the v2 smoke | arrivals counted by first-seen generation, via the driver sidecar (§2.2) |
  | 4 | Harmful-tail escape — prune-first ordering let dedup's count-absorption push a bad SP back over the threshold for a generation | run outcome forensics (the below-baseline tail) | prune runs last, on post-dedup counts (§2) |
  | 5 | Credit smearing — near-duplicate SPs split one lesson's follows so no row ever accumulates actionable evidence | design review 2026-06-19 | freeze-old KEEP/DISCARD SP dedup onto the credited survivor (§2.3) |
  | 6 | Wrong-blame eviction — deleting good content over a retrieval/scoping miss | the §0.4/§0.5 fix program | verdict-aware evict: override-dominant evicts, not_relevant-dominant spared (§2.4) |
  | 7 | Exploration starvation — credit is usage-gated, so a never-retrieved candidate never earns | §6.7 review, 2026-07-14 | guaranteed exploration slot at the retrieval cap + contested-lane quota (§6.7) |
  | 8 | Observation immortality — any obs at count ≥ 2 escaped decay forever, leaving store size unbounded | store-bounding review, 2026-07-14 (log §4) | count-scaled decay clocked from last reinforcement (§2.1) |
  | 9 | Clustering cost scaled with total store size and was paid even by gated-out cells | store-bounding review, 2026-07-14 (log §4) | gates before clustering; seed-from-new (§2.2) |
  | 10 | Incremental dedup non-convergence — old entries re-litigated as neighbors land, eroding the store past the ~17% sweet spot | dedup campaign, 2026-06-09 (`../dedup/incremental_convergence.md`) | freeze-old apply-guard (old↔old operations forbidden), live in the loop's obs fold |
  | 11 | Halo-weighted synthesis regenerates what prune killed — observation outcome tags track faction-won, i.e. luck | design 2026-06-19 (consolidation_design) | credit-aware synthesis over the realized track record (§2.2) — mechanism-verified only, quality unmeasured |
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

Ordered by criticality; all freshness-dated 2026-07-14 (verified against the working tree by read,
not by run).

1. **RESOLVED 2026-07-14 — the fold publication tripwire is built** (log §7; suite-verified same
   day). As raised: the fold is the critical path — a bad fold publishes a bad checklist v_{k+1}
   and detection runs against it for a whole epoch with no in-epoch correction, and the fold report
   was counts-only. Two always-on deterministic invariants now gate persistence and publication.

   **Monotone detected support.** The fold keeps no running counters: every fold it *recounts*
   every tell's support from scratch by re-reading the whole instance ledger (deliberate — a past
   curation mistake never bakes into a counter). That recount has one dependency: each row says
   "player X, game 41," and tallying it requires looking up game 41's roles in the `roles_by_game`
   map the fold is handed. If that map is ever missing an older game (a driver bug, a truncated
   file), every row from that game silently drops out of the recount. No error is raised; the
   tally just shrinks, and the checklist would publish from wrong numbers. The invariant exploits
   the one thing that cannot legitimately happen: the ledger is append-only, so a tell's count can
   only rise between folds. Each fold saves its counts in `state.json`, and the next fold asserts
   new ≥ saved for every tell. Any decrease means rows were lost in the recount, so the fold
   crashes loudly instead of publishing quietly-wrong numbers. (Receipt-box intuition: every
   receipt is kept forever and totals are recounted monthly from the box — if this month's recount
   of January is *lower* than last month's recount of January, you didn't spend less, you lost
   receipts.)

   **Head continuity.** The handful of tells doing the most detection work must not silently
   disappear from the card: a top-support incumbent may leave only via this fold's *explicit*
   null-lift verdict; any other exit means curation diverged from the fold's own rulings.

   On violation the fold raises before anything persists — the appended instance rows remain,
   because the ledger records what happened while the tripwire gates curation. Residual, tracked:
   wrong keep/discard verdicts at the single-wording grain remain possible (they are the two ways
   a binary verdict can be wrong); the tripwire catches their *systematic* form, and the periodic
   audit stays the semantic backstop.
2. **Threshold provenance is mixed — top-ranked knob now checked, rest pinned.** Evidence-anchored:
   the SP cap (bloat record), the credit window (density calculation). Design-anchored, never
   swept: `prune_tau = −0.15`, the three follow/retrieve floors (8/8/2), `K_PROBATION = 12`, the
   null-lift cut (0.03 at n≥20), the prefilter (0.80/top-3), the checklist caps (25/15/48). The
   review ranked `prune_tau` as the only knob that could plausibly flip a run conclusion, for this
   reason: every generation the loop *deletes* SPs whose lift falls below τ, and the compounding
   story assumes those deletions remove genuinely bad directives — if lift at that threshold were
   mostly noise, pruning would be deleting near-randomly, good SPs included, and the run would sit
   on a broken referee. That cannot be validated on the same games that produced the flags (the
   metric would be grading its own homework), so the check is held-out: split the v6ab archive
   into two halves by game, measure every SP's lift on each half *independently*, and ask two
   non-circular questions — do the two independent measurements agree, and do SPs flagged harmful
   on half A stay harmful on half B, which never saw the flags? Run 2026-07-14
   (`heldout_credit_reproduction`, zero spend — it re-scores existing dumps): Pearson(lift_A,
   lift_B) = +0.54 at n = 31 comparable SPs (noise would read ~0), and A-flagged losers
   (lift_A < −0.15) stayed negative on the held-out half in 8/9 cases against a 61% base rate.
   The one flip sat at 3 follows — the real prune rule refuses to act below 8 follows, and all 4
   flagged SPs at ≥8 follows stayed negative. Direction-credible at small n: the prune rule cuts
   reproducible signal, not noise. Tracked limitation: the prefilter 0.80/top-3 (the tell side's
   similarity threshold) remains uncalibrated — the data to calibrate it exists (the 30-game sim's
   resolved rows), but a replay harness is a new instrument and the closing rule is no new
   complications pre-run. The remaining knobs are pinned as design-anchored in the pre-reg, with a
   post-run sensitivity readout.
3. **RESOLVED 2026-07-14 — the fuzzy match index is bounded** (owner ruling at the walkthrough: a
   simple hard cap, chosen over the ledger design's unseen-based retirement; built and
   suite-verified same day, log §7). As raised: `_resolve_wordings` compared every new wording
   against the full same-channel canon, which grows ~16/game indefinitely — flat cost via the
   embedding prefilter, but growing nomination rot. The fuzzy stage (embedding prefilter → LLM
   judge) now consults a bounded per-channel index: all incumbents (already bounded by the verdict
   cycle), the 30 most recent probation entries, and the 10 most recently scanned archive entries —
   roughly 65 candidates per channel, flat as the singleton tail grows. Retirement from *matching*
   is not deletion: the free normalized exact-match stage stays global over the whole canon (an
   identical wording can never mint a duplicate identity), canon and ledger keep everything, and a
   wording whose true match was retired from the index re-enters as a new probation canonical that
   the periodic audit can reunite — tallies recompute from rows, so nothing is permanently lost.
   Tracked limitations: the 30/10 window sizes are design-anchored (unswept), and the append-only
   ledger still grows by design — inert during play, but the fold-time recompute-from-rows scan is
   linear in total history (trivial at run scale; snapshotting is the fix if it ever matters).

   Since this adds a third cap to the system, the disambiguation (each bounds a different surface,
   and only the first is SP-side):

   | Cap | Side | What it bounds |
   |---|---|---|
   | `synth_cell_unproven_cap = 12` (§2.2) | SP | how many *unproven* SPs a cell may hold before synthesis stops adding |
   | Checklist cap (48/channel, §3.2) | Tell | how many tells the *detector scans games for* each epoch |
   | Match-index cap (~65/channel, this item) | Tell | how many known tells a *new wording is compared against* at the fold |
4. **SP dedup only runs when synthesis added SPs** (`cfg.sp_dedup and syn.get("added")`). A seeded
   store's pre-existing near-duplicates are never collapsed in-loop — the run's seed store must
   therefore arrive already deduped. Verify that assumption holds for the run's actual seed.
   *Resolution path (2026-07-14):* the pre-reg is currently silent on the SP store's starting
   state and must pin it at signing. If the run starts cold (as both v2 smokes did), this item
   closes by construction — there is no seed to dedup. If seeded, run the batch dedup in
   report-only mode over the seed before launch.
5. **Probation pressure under open vocabulary.** The sim's funnel was healthy at 30 games, but the
   flat singleton inflow means the 15-slot probation lane is permanently contested; beyond 30 games
   the rotation/starvation behavior is unmeasured. Post-run readout, not a blocker.
6. **RESOLVED 2026-07-14 — the role-revealing exclusion is removed** (owner ruling, pre-reg §5
   now records it): the book is role-grain for every unrevealed role, `is_role_revealing` deleted,
   selection re-based on `subject_lift`, launch seed rebuilt as `tell_book_v2_seed.json` (34
   entries, all six roles). Residual for the walkthrough: the injection-channel screen result
   (27.5% changed, direction positive) was measured on the v1 wolf+SK-only book — the v2 book is
   unscreened, and the weakest tail entries (vigilante/healer at lift +0.03–0.06) are near-prior;
   whether the book needs a minimum-strength floor is a fair probe.
7. **RESOLVED 2026-07-14 — SP cells adopt the two tell-style lane pieces that transfer** (owner
   ruling, same day it was raised; log §5). The tell checklist manages its population in explicit
   lanes — ranked incumbents, a probation lane with an opportunity clock, an archive with rotation.
   An SP cell has the same populations implicitly (proven = positive lift with ≥2 follows,
   protected; unproven with live counters) but had no lane structure. Adopted: (a) the synthesis cap
   re-scoped to the **contested lane** (§2.2 — a cell full of proven SPs keeps exploring; a full
   contested lane stays blocked, and drains via credit); (b) a guaranteed **exploration slot** at
   the per-situation retrieval cap (`sp_exploration_slot`, default on): when all kept SPs are
   proven and the pool holds an unproven one, the best unproven candidate takes the lowest slot —
   SP credit is usage-gated (§4), so a candidate that is never retrieved never earns, and the slot
   is what drains (a)'s lane. The game-side proven predicate (follow ≥ 5 and positives > negatives)
   deliberately differs from the loop's lift-based one: the read path has no base rates. Rejected,
   reasons standing: archive-with-rotation (an archived tell re-earns at zero marginal cost at fold
   time, but an archived SP would need paid retrieval slots to re-earn — and the obs store already
   serves as the SP's archive, since deletion plus re-synthesis is the SP-native re-audit path) and
   a probation deadline (retrieval opportunity depends on the situation arising, so a
   generation-based clock would kill rare-situation SPs and violate §2.4's
   degradation-is-credit-only rule). Residuals for the walkthrough: the slot changes live-game
   retrieval behavior (an epoch-bundle member, like proven tiering), and the lane split's effect on
   store composition is unmeasured until a live run.

## Sources

- Code (maintained): `evaluation/src/loop/consolidate.py` · `tell_fold.py` · `tell_credit.py` ·
  `tells.py` · `config.py` (knob rationale lives in its comments) · `Agents/memory/tell_book.py` ·
  `Agents/memory/strategy_synthesis.py` (the synthesis prompt) — module table in
  [`evaluation/src/loop/README.md`](../../evaluation/src/loop/README.md).
- Evidence cited: tell-extraction log §10 (ledger sim) · §11 (consolidation №1) · §12
  (epoch-quantization ruling) · §16 (granularity screen)
  ([`../extraction/tell_extraction/experiment_log.md`](../extraction/tell_extraction/experiment_log.md));
  the credit layer and its invariants ([`../credit/report.md`](../credit/report.md)); the v7 run
  pre-registration draft
  ([`../execution_plan/v7_run_preregistration_DRAFT.md`](../execution_plan/v7_run_preregistration_DRAFT.md)).
- Design lineage: [`../v7_final/consolidation_design.md`](../v7_final/consolidation_design.md)
  (2026-06-19, SP side) · the tell ledger spec in
  [`../discussion_tagger/read_tactic_credit_redesign.md`](../discussion_tagger/read_tactic_credit_redesign.md) §3.
