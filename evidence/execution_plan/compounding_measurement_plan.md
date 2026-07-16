# Measuring Compounding — Execution Plan

> **What this is.** A forward-looking implementation plan for the next stretch of the memory-compounding
> question (the v7 thesis: does the consolidation loop make memory *compound* across generations?). It
> synthesizes a design review of the current instrument stack into a sequenced, pre-registered plan.
> **Findings first, then the plan.**
>
> **Status:** revised 2026-07-11. Phase 0 executed (§0.1–0.5 stamped in place); the credit mechanism was
> then superseded by the read/tactic redesign
> (`../credit/read_tactic_credit_redesign.md`), and this plan now carries the final pre-run
> program — see **§R** below. No paid run yet.
> **Genre:** execution plan, not an experiment report — it *precedes* the work rather than recording it.
> Each completed piece graduates to its own `evidence/<topic>/` folder; this doc is the map.
> **Sources:** the situation-dimensions + both tagger reports, the proxy-discovery and scheduler-bias
> logs, the v7_final experiment_log (§0–§12g) + report, the post-game / day-summary extraction reports,
> the day-discussion prompt, a sampled `gen2_on` transcript, and a code read of
> `evaluation/src/loop/{consolidate,credit,decision_scoring}.py` +
> `evaluation/src/replay/decision_screen/`; **plus the 2026-07-04 credit-path code audit**
> (`evaluation/src/loop/{credit,credit_backfill,consolidate,driver,measure}.py`,
> `Agents/turn/adoption.py`, the dedup counter-absorb in `batch_deduplication/operations.py`,
> and the loop test suites) — its findings are folded into §0.5 and the component table.

---

## TL;DR

The instruments are **valid but underpowered**. Nothing in the component stack would manufacture a fake
positive anymore — the halo / config-slip / cross-epoch-baseline failure classes are all guarded. But at
4–5 games per generation, the game-level de-luck slope **cannot detect a plausible effect**: the intrinsic
per-game swing (±0.9 even on matched boards, per §12b) swamps the hoped-for +0.1–0.2 mean shift. The
enemy is **noise, not missing gold labels** — and the validated `+0.4`/`+0.5`-style numbers speak to
*validity*, not *power*, so they don't touch this.

So the highest-leverage work is **not** more games and **not** a broad labeling push. It is to change
*what the slope is read on*:

1. **Power analysis** ($0) — prove and size the wall before paying, so the readout redesign is
   pre-registered rather than discovered after another null.
2. **Checkpoint replay** (~a few $) — a *fixed exam* re-scored against each generation's store snapshot,
   which removes game-divergence noise entirely and directly measures both "the store improved" and
   "agents consequently decide better."
3. **SP-lineage tracking** (~a day, offline) — measure compounding at the *strategy-point grain* (dozens
   of before/after observations per run) instead of one noisy number per generation.
4. **Credit-scale fixes** ($0 code + one small spend decision) — ⭐**2026-07-04 code audit:** the loop's
   demotion pressure is correctly calibrated **only on the deterministic vote channel**. Discussion credit
   is graded against base 0 (a *level*, the §12f halo class, live inside the loop's own credit),
   tagger-night credit is baselined against a *different grading function* (units mismatch), and
   out-of-window credit never ages out despite the documented window semantics. Fix before any paid run
   (§0.5) — and Finding 1 is a **hard gate for the wolf arm specifically** (its primary instrument is the
   distorted channel).

Gold labels matter in exactly two load-bearing places — **revised 2026-07-11: the behavior detector and
SP-synthesis output** (the tagger golden went moot with its demotion to diagnostic); everything else on
the "unverified" list gets a cheap directional bound, not a certification. The re-scoped suite is in
Phase 2.

---

## R · 2026-07-11 revision — the read/tactic redesign and the final pre-run program

> Everything below §R is the 2026-07-04/05 plan with its execution stamps; it stays as the record. This
> section is what changed on 2026-07-10/11 and the program that now precedes the paid run. Design record:
> [`../credit/read_tactic_credit_redesign.md`](../credit/read_tactic_credit_redesign.md)
> (v1 scope in its §8).

**What changed since the 2026-07-05 stamps:**

- **New prompt epoch 2026-07-09** — the per-turn reads bundle shipped live. The next build run is
  fresh-epoch by construction and doubles as the bundled reset (reads + change E + wolf day-channel +
  SP tiering + dead-roster + anti-repetition + the injection swap below): cold-start, both arms
  in-epoch, no separate re-baseline.
- **Credit is redesigned (read/tactic decomposition, v1 scoped 2026-07-11).** Reads become tells
  (accuracy-credited facts, shrunk-lift ranked) plus a Brier ledger; day tactic credit = the day-vote
  endpoint with a faction-relative target-value rule; night credit = deterministic, read-partitioned; a
  guarded concealment floor; self-report attribution with a spot-check bound. **The tagger is demoted to
  a standing diagnostic** (its night override retired) — its golden is moot for credit.
- **Injection becomes two channels: tells + SPs; observations leave the prompt** (they remain the
  synthesis substrate). Hedges before spend: the injection-channel replay screen and the in-run Brier
  delta (book vs no book).
- **The labeling sweep is re-scoped** — Phase 2's priority table is rewritten in place below.
- **Ownership gate (user decision, 2026-07-11):** the run waits on the user personally re-deriving the
  two remaining un-owned load-bearing stages — a `decision_scoring` teach-back, and a consolidation
  **blind re-derivation** (blind derivation → code confrontation → delta classification: the method that
  produced the credit redesign). The consolidation confrontation also authors the ledger-anchored
  reference points for the SP-synthesis golden. Extraction is off the re-derivation list (user-driven
  spec); it gets one verification pass riding tell mining (are behaviors objectively described).

  > **2026-07-14 (owner) — format and scope of the consolidation gate revised.** Format = the
  > **walkthrough teach-back** (the agent presents the current pipeline, the owner probes and
  > revises — the same reformatted process the decision_scoring gate used), NOT a blind write-first
  > derivation. Scope = **both compounding mechanisms**: SP consolidation (`loop/consolidate.py`)
  > AND the tell epoch fold (`loop/tell_fold.py`), which had no unified mechanism record. Review
  > basis and record home: `evidence/store_curation/` (folder renamed from evidence/consolidation, 2026-07-15) (report.md = the presentation, §6 = the
  > agenda; walkthrough revisions land in its experiment_log.md). The synthesis-golden anchor
  > points remain a required output of the session.

**The critical path (target 1–2 working days, AI-implementation-heavy; owner marked):**

*Day 1*
1. `decision_scoring` teach-back — user writes a one-page spec from the code, adversarially reviewed
   (~2h user). Signs off the valence semantics the new day credit reuses.
2. Tell-mining offline probe on the v6ab dumps + dedup prompt v0 (AI, ~$0) → candidate tells, book-size
   reality check, cross-epoch material; user reviews a sample for the objective-description
   precondition (~30 min).
3. v1 credit wiring per the design record (AI): both ledgers, endpoint + target-value day credit,
   read-partitioned night credit, concealment floor with both guards, tagger override retired; extend
   `assert_baseline_coherence` with a **registered baseline type for tells** (cast-prior,
   arm-independent — not an OFF-arm base) so the invariant doesn't false-fire. Tests green.
4. Detector golden — AI pre-labels 30–50 stratified cases, user adjudicates (~1–1.5h user) + the
   role-blindness check. **Gates the run.**

*Day 2*
5. Consolidation blind re-derivation + confrontation (user, ~4–5h — the squeeze point). Output: the
   delta classification + the synthesis-golden anchor points. Gates the consolidation-integration
   sign-off only; the consolidation code is otherwise at its validated 2026-07-05 state.
6. Dedup-judge spot-check (15–20 merges, ~45 min user) · injection-channel replay screen + cross-epoch
   tell check (AI, ~$1–2).
7. Pre-registration, user-signed: arms (tells + SPs injected, obs substrate-only), ONE primary endpoint
   (town decision basket on the end-point A/B), stopping rule.
8. Smoke → launch the arm-guarded, fresh-epoch build run (Phase 1.1).

*Rides the run / post-run:* checkpoint replay (one batch, post-run by design) · Brier delta ·
endpoint-vs-first-link comparison · per-tactic density census · SP-lineage join · completeness-tail
labels · the validity-controls registry index (extends `../evaluation/methodology/report.md`) · the
personal stats one-pager (`interview_prep/`, local-only).

**Honesty clause (pre-registered):** the 1–2-day target holds only if (a) the detector golden bounds
acceptably and (b) the consolidation confrontation surfaces no validity-gating change. Either failure
slips the run — that is the gate working, not the plan failing.

---

## The claim ladder (the spine)

Every decision below hangs off one pre-registered ladder. Writing it down *before* the runs is what makes
a deferral read as **scoping**, not **salvage after a null**.

| Rung | Claim | Instrument | Status |
|---|---|---|---|
| **1** | *Having* memory improves live decisions (and directionally, wins). | Static paired A/B | ✅ **Proven.** Decision basket significant (healer-save p=0.005, correct-elim p=0.028); win-rate direction positive (single-arm win estimate underpowered — see `evidence/memory_system/effectiveness/report.md`; do **not** re-cite the retracted fused "+17pp p=0.013" headline). |
| **2a** | The consolidation **loop improves the store** — each generation's store is higher-quality than the last. | SP-lineage lift + prune/evict census + lift-weighted composition (no agent in this measurement) | ⏳ **Buildable now, $0–cheap.** |
| **2b** | **…and consequently agents decide better** — the same agent, on the same frozen decisions, decides better as the store advances. | Checkpoint replay curve | ⏳ **Buildable now, cheap.** |
| **3** | Loop-improved stores translate into **live-game wins** (in-situ, multi-turn, within-game compounding). | New paired live games at powered N | ⛔ **Deferred, cost-quantified.** The power calc attaches the price tag (illustratively ~hundreds of games/arm). Deferred ≠ false. |

> **ADOPTED (proposed 2026-07-05; adopted for run planning 2026-07-11):** the live slope is retired as
> the primary readout. The run's headline is the **end-point paired A/B** — final store vs initial
> (gen-1) store on 30 shared boards, replayed in one batch — converting the ramp into the step design
> that succeeded in the static A/B; see `power_analysis/decision_rationale.md` §7. This is Phase 1.1's
> pre-registered primary endpoint.

The honesty conditions (agreed in review): **pre-register the ladder before the run**, and **word rung 2b
precisely** — "the loop measurably improves the store's decision-steering quality on frozen boards," not
"agents win more over time." The gap between 2b and 3 (frozen boards vs in-situ behavior) is real, and the
G3c replay-flat precedent means replay can miss things — so replay is the *powered complement*, live pairs
are the *causal confirmation*. Either replay outcome **exits the "unmeasurable" state**: a rising curve is
signal; a flat curve is a *powered decision-level null* (a real verdict), unlike today's unpowered live
null.

---

## Findings — component sufficiency for detecting a positive v7 result

| Component | Verdict | The one thing that matters |
|---|---|---|
| Game substrate (flash-lite + prompts + scheduler) | ⚠️ Valid, poor SNR | Low-information dialogue → high intrinsic variance → the power wall. Symmetric across arms → threatens **power, not validity**. Scheduler exonerated by its own access audits. |
| Day summary | ✅ Sufficient | Runs identically in both arms; hard facts backstopped. Not a bottleneck. |
| Post-game extraction | ✅ Sufficient | Manual reads: cheap models capture the same pivotal lessons. Omission risk bounded. |
| Situation dims / retrieval | ✅ Sufficient | Aligned-query rewrite is a verified win; gating default-**off** so its "unknown" verdict never touches the run. Computable dims now deterministic (verified by construction). |
| Credit — deterministic vote channel | ✅ Sufficient | Paired same-epoch OFF-arm base rates + validated basket (r≈0.6). **Strongest instrument.** Join verified clean in the 2026-07-04 audit (conservation holds; glob/ordering bugs genuinely fixed). |
| Credit — discussion + tagger-night channels | ❌ **Insufficient as-is** (2026-07-04 audit) | Graded as a **level, not a lift**: tagger discussion base=0 (ambient positive-verdict rate inflates every discussion SP — the §12f halo class), tagger-night counts baselined against the *deterministic* OFF mean (grading-function mismatch, all 4 night cells), floor-mode base from ON-window incidental cases (the §11j class, verbatim). Fix = §0.5. |
| Credit — wolf/SK instruments | ⚠️ Sufficient-with-fixes | Tagger validated-but-uncalibrated (N=24, single-epoch); wolf slope inherits the `sk_lynched` dilution (77/180 v6ab games carry **zero** wolf-skill information). |
| Consolidation (synth/prune/evict) | ❌ Insufficient as-is | Three structural holes (§0.4) leave the store full of never-followed ballast; plus stale out-of-window credit feeds prune/protect/track-records (§0.5, Finding 2). |
| Measurement harness | ❌ Insufficient at N | Pairing decays after first divergence; §12b's own math collapses the paired estimator to unpaired. Valid but underpowered. |
| Metrics basket | ✅ Sufficient | Pre-registered, tiered; diagnostic additions (A2/B1/C1) usable as secondary slope lines. |

> **2026-07-11:** the two ❌ credit rows are superseded — §0.5's fixes shipped 2026-07-05, and the
> read/tactic redesign then replaced the discussion/tagger-night channels outright (§R). The
> consolidation row's §0.4 holes are closed; what remains open there is the ownership re-derivation
> (§R), not a code defect.

**On transcript quality** (game 1 of `gen2_on`, SK win, 5 days): the real issue is **information density**,
not coherence. Four players open day 3 with near-identical "I agree we can't keep abstaining…" despite the
tone instruction banning exactly that; the investigator is mislynched by a 5-vote pile-on seeded by one
counter-accusation. Implication: the ceiling on what memory can add is capped by how much *any* content
can steer a pile-on — this inflates variance more than it biases either arm. **Power problem, not validity
problem.** Fix hierarchy: prompt pass (cheap, epoch reset) → 3.5-flash upgrade (real money; worth a 10-game
pilot to measure *variance*, not quality). Batch any substrate change into **one** deliberate epoch bump.

---

## Phase 0 — $0 / cheap, before any paid run

### 0.1 Power analysis (MDE simulation) — ~½ day, $0, highest info/effort

**EXECUTED 2026-07-05** → readout + decision: `power_analysis/mde_table.md` +
`power_analysis/decision_rationale.md`. Headline: real per-game noise ≈0.3 (not ±0.9); +0.15
undetectable at every affordable config (11% at the v2-size run); MDE at 200 games ($56) = +0.20 →
slope readout retired at plausible effect sizes.

**Finding it addresses.** The `+0.4`/`+0.5` numbers are *validity* (the ruler is real). Power is a
different quantity entirely and the only one that involves N:

- **Validity** (~0.5–0.6): does the metric measure the right thing? ✅ done.
- **Effect size**: how big is the thing? Plausibly +0.1–0.2 per-game de-luck (static A/B + wolf trend).
- **Noise**: how much does the metric bounce for non-memory reasons? ±0.9/game even on matched boards.

The analogy: an accurate bathroom scale (validity) testing a 0.5 kg diet effect (effect) on someone whose
weight swings ±3 kg day-to-day (noise), by weighing 4 times (N). The scale being accurate doesn't save you.
Concretely, at N=4/gen the per-generation mean has SE ≈ 0.9/√4 ≈ 0.45 — 2–4× the effect — which is why
v2's gen means swung ±0.2–0.3 and "no slope" was foreordained regardless of the truth.

**Build.** A `$0` script that resamples existing per-game records (v2, v6ab, run-1), injects a *known* true
effect (0 / +0.1 / +0.15 / +0.2) into the resampled arms, runs the *planned* slope analysis many times, and
counts detection rate.
- **Output:** a table — "at N∈{4,5,10,20}/gen × {6,8,10} gens, detect a +0.15 effect X% of the time" — and
  the minimal detectable slope at the affordable N.
- **Reuse:** de-luck distributions via `evaluation/src/instrument_validation/proxies/metrics_common.load_v6ab()` +
  `decision_scoring`; keep it in `evaluation/src/instrument_validation/power/` (thin runner) → output to
  `evidence/execution_plan/power_analysis/`.
- **Pre-registration effect:** if detection at affordable N is ~10%, the experiment-as-designed buys a coin
  flip — and that number *pre-registers* the redesign in 0.2/0.3 instead of re-discovering futility for
  ~$30. It also produces the **costed deferral** for rung 3 ("a powered live test needs ~N games ≈ $X"),
  which is itself a credibility asset.

### 0.2 Checkpoint replay — a fixed exam instead of live matches — ~1–2 days, a few $

**Finding it addresses.** Today's readout re-rolls a huge amount of luck every generation (fresh ON/OFF
games; one different vote diverges the whole game). Replay builds the exam **once** and varies only the
store.

**Build.**
1. Freeze **~100 decision cases** ("here's the board + discussion-so-far; you're the villager — who do you
   vote?"). True roles known → deterministic de-luck grade.
2. After the run, re-answer the same cases with retrieval pointed at each generation's **store snapshot**
   (`gen1_store/…genN_store/`, already saved) + the empty-store control.
3. Plot decision quality vs generation. The only thing changing between points is the store → no
   game-divergence noise in the curve.

**The engine already exists.** `evaluation/src/replay/decision_screen/replay.py:_replay_vote` rebuilds the
agent payload from a frozen `EvalCase`, injects a swapped retrieved-memory block, and regenerates the
decision — scored by `decision_scoring`. The new work is: (a) drive it per store snapshot instead of per
arm, (b) case selection, (c) the curve/stats. Case machinery lives in `decision_screen/cases.py`.

**Why one instrument gives *both* rungs 2a and 2b.** A replay case runs the **real pipeline for one
decision**: frozen board → live query generation → retrieval against the checkpoint store → the actual
decision prompt → the agent votes → de-luck scored. The readout is the *agent's decision*, not a store
property. So:
- **Rung 2a ("store improves")** — content-level side evidence: lineage lift (0.3), prune removing
  negative-lift SPs, lift-weighted composition rising. *No agent in this measurement.*
- **Rung 2b ("agents consequently decide better")** — the replay curve itself: same agent, same frozen
  decisions, only the snapshot varies. **Replay covers the "consequently" directly** — new live games are
  needed **only** for rung 3 (in-situ multi-turn play, discussion dynamics, wins).

**Two traps to design out now (both from prior scar tissue):**
- **Model drift → replay everything in ONE batch after the run.** Not just a fresh off-arm: if gen-1 and
  gen-6 checkpoints are scored under different API epochs, the curve confounds store-progress with drift.
  So replay all snapshots + control **same day, same backend, one batch**. The frozen boards being from old
  games is fine (static inputs); it's the *scoring calls* that must share an epoch. (Vertex-vs-Google-AI and
  temp-drift lessons live in this class.) The old recorded results are never compared against — only fresh same-batch
  replays.
- **Same-game leakage.** If cases come from the loop's own games, a gen-k store contains observations
  extracted from the very game a case came from — the leak that produced the criticality screen's fake
  +0.25 endgame signature. **Fix:** draw cases from **held-out** games (v6ab, or a small fresh baseline
  batch that never feeds the loop), or exclude any case whose `game_id` appears in the snapshot's
  provenance. Pre-register the exclusion.

**Honest caveat (pre-registered):** replay measures decision-steering on frozen boards, not full downstream
behavior; G3c replay came back flat once. Replay = powered low-noise readout; live pairs = causal
confirmation.

### 0.3 SP-lineage tracking — compounding at the mechanism grain — ~1 day, offline

**SHIPPED 2026-07-05:** `distilled_from` field live in `evaluation/src/loop/consolidate.py` (+4 tests).

**Finding it addresses.** Credit already assigns each SP a realized lift; synthesis already rewrites the
store. **Nobody ever joins the two across generations** — nobody asks: *"synthesis produced SP X′ at gen 4;
did X′ then out-earn the older SPs it was distilled from in gens 5–6?"* That question **is** the compounding
hypothesis, at the individual-SP grain — dozens of paired before/after observations per run instead of one
noisy game-level slope. Aggregated ("revised SPs out-earned their sources in 18/24 cases"), it is far more
detectable *and* tells you *where* synthesis helps or hurts.

**Answer to "do we touch live code?": no gameplay code, either way.** Two paths, from the code read:

- **Fully offline on existing v2 artifacts, today, $0.** `gen1_store/…gen6_store/` + `loop_history.json`
  are on disk. A `v2_salvage`-style script diffs consecutive snapshots, finds each generation's
  newly-added SPs, and compares their later realized lift against the older same-cell SPs they were
  distilled from. **Catch:** shipped synthesis **mints new UUID keys with no parent pointer**
  (`consolidate.py:188` — the design's "revise in-place" became "grow-new + prune-old"), so matching a new
  SP to its sources is **fuzzy** (cell + text/embedding similarity). Fine for a *directional* v2 read; not
  exact.
- **Exact, for the next run — ~5 lines, entirely in `evaluation/src/loop/`.** At `consolidate.py:188`
  (where synthesis builds the new SP's `value` dict), also record the **keys of the existing SPs whose
  track record was fed in**. They are right there: `_track_record` (`consolidate.py:122`) already receives
  `sp_namespaces.get("strategy_points/{cell}", [])` and renders the rows that pass `follow_count >=
  synth_track_min_follow` — capture those keys into a `distilled_from: [...]` metadata field. **Zero
  gameplay effect** — it's inert metadata alongside the counters agents never see (`Agents/` untouched).
  Post-run analysis is then a trivial offline join.

**Recommendation:** add the `distilled_from` field **before** the town/wolf runs (so they produce exact
lineage for free); treat the fuzzy v2 pass as optional curiosity.

### 0.4 Consolidation fixes — un-dilute the store — ~1–2 days

> **ALL THREE BUILT 2026-07-05:** evict counters live (via the §0.5 pass — `credit_apply` SETs
> retrieved/override/not_relevant, windowed; `_evict_ok` fires in test); per-cell SP cap
> (`synth_cell_sp_cap=12`, `cells_capped` in the per-gen stats); proven-first SP tiering in retrieval
> (stable partition after `cap_per_situation`, `follow≥5 ∧ pos>neg`, config-gated `sp_proven_tiering`
> default-ON, recorded in `build_game_config` + per-turn retrieval metadata). Tiering is an
> epoch-bundle member (changes live behavior).
> **2026-07-14 store-bounding revision** (consolidation report §2.1–§2.2, §6.7): the cap knob is now
> `synth_cell_unproven_cap` and gates the CONTESTED lane only (proven SPs sit outside the quota); a
> guaranteed exploration slot (`sp_exploration_slot`, default-ON, epoch-bundle member) surfaces the
> best unproven SP at the per-situation retrieval cap; obs decay is count-scaled from last
> reinforcement (nothing immortal).

Three known holes leave most of the store as never-followed ballast that dilutes compounding. Without them,
a flat slope stays ambiguous ("loop never had signal to act on") — the exact ambiguity §10's
credit-distribution logging was built to avoid.

- **Evict rule inert.** SP adoption counters don't merge back, so the scope-aware evict
  (`config.evict`, `evict_min_retrieved`) never fires on real adoption history — confirmed in code:
  `_evict_ok` requires `override_count > 0` (`consolidate.py:42`), which is always zero in the loop.
  ⭐**Cheaper fix than the §12d "merge counters back" proposal** (2026-07-04 audit): the window's eval
  cases already carry everything needed — `strategy_verdicts` includes override/not_relevant and
  `strategy_index_to_key` gives retrieved — so `credit_apply` can SET
  `override_count`/`not_relevant_count`/`retrieved_count` in the same pass that sets follows. No merge
  change, and the counters become **window-consistent** with the credit (see §0.5).
- **Synth gate a no-op at k=1.** Bloat ran 0→227 SPs (follow_p50~5); the new-clusters-only gate
  (`_synth_cluster`) helped but the cell-level gate still admits too freely. Make it bite (raise
  `synth_min_new_obs` and/or add a per-cell SP cap).
- **No proven/unproven tiering** — the report's "cheapest unbuilt lever." Tier SPs on follow track-record
  so retrieval/synthesis prefer proven lessons; the never-drop floor (`config.py:76`) already protects
  rare-but-proven ones, so this extends an existing idea.

> **Scope note.** 0.4 and 0.5 are the Phase-0 items that change *loop behavior* (0.1–0.3 are pure
> readouts). Sequence them so they land **before** the paid runs (they change what the runs measure), but
> after 0.1–0.3 are at least scaffolded (they tell you whether the fixes moved anything).

### 0.5 Credit-scale fixes — from the 2026-07-04 code audit — ~1 day + one spend decision

> **DECIDED 2026-07-05 — option A (user):** tag the OFF arm too (~2× tagger spend; clean same-instrument
> base for discussion AND tagger-night credit). Options B/C rejected → the g3b/discussion_credit probe
> trio stays dated evidence (no standing re-open).
> **IMPLEMENTED same day (all three findings + the invariant):** `_tagger_off_base`/`_discussion_off_base`
> over the true OFF arm, mode-keyed `tagger/<cell>` entries in base_rates with a shared `base_for`
> selector (prune/synth/credit_distribution); window counters zeroed on every SP before ledger apply;
> adoption counters SET from the window's eval cases; `assert_baseline_coherence` wired in the driver
> (every credited channel needs a same-grading-function OFF base, raise-loud). **The wolf arm's
> Finding-1 gate is CLEARED.**
> **2026-07-11:** the tagger's demotion to diagnostic (§R) removes tagger *credit* entirely — the
> Option-A tagger OFF-arm bases now matter only if the diagnostic is read comparatively across arms
> (cheap, optional). What carries forward: the same-grading-function OFF-arm rule (the endpoint floor's
> `_discussion_off_base`) and `assert_baseline_coherence`, which needs a registered baseline type for
> tells (cast-prior, arm-independent) so it doesn't false-fire on the new channel.

A line-level audit of the credit path (`credit.py`, `credit_backfill.py`, `adoption.py`, `driver.py`,
`measure.py`, the dedup absorb, the loop tests). **The join itself is clean** — verdicts →
`strategy_index_to_key` → ledger → store SET is sound, conservation holds, the past bug-fixes (glob
expansion, synth→dedup→prune order) are genuinely in, dedup absorbs **all** counters (no lift dilution),
and SP namespaces are per-phase so the ledger-merge disjointness assumption holds. Three real defects, all
in the demotion machinery:

- **Finding 1 (HIGH) — discussion & tagger-night credit is a *level*, not a *lift*.** The §9 OFF-arm
  baseline fix only reached the deterministic vote/night ledger. (a) Tagger discussion credit is graded
  against **base 0** (`credit.py:106`) — but the ambient positive-verdict rate without memory is not 0
  (literally the retracted §12f halo; v2's own +0.26…+0.48 discussion "lift" is this inflation). (b) Under
  tagger mode the night SPs' counts become *read-quality* verdicts, yet consolidation recomputes lift
  against `base_rates.json`'s **deterministic-outcome** OFF means — a grading-function mismatch on all four
  night cells. (c) Floor-mode discussion base comes from `memory_enabled=False` cases **inside the
  ON-window glob** (`credit.py:50-51`) — the §11j "incidental off decisions" defect, verbatim; the "+0.51
  held-out" floor validation ran on v6ab globs that *included* the baseline arm, so the method validated
  while the loop wiring is wrong (same method-vs-wiring split as run-1).
  **Consequence:** prune's τ effectively becomes τ−ambient on discussion SPs, the protect-exemption
  (`lift>0`) shields nearly all of them, and synthesis track records overstate discussion advice.
  **Fix:** baseline every channel with the **same grading function on the OFF arm** — decision owned by
  the user (see Open questions): either **tag the OFF arm too** (~2× tagger spend, still ~1 flash-lite
  call/day/game; clean same-instrument base) or **demote discussion credit to synthesis-input-only**
  (never prune/protect on a level-scaled channel).
- **Finding 2 (MED) — stale credit never ages out.** `credit_apply` sets counters only for SPs present in
  the current window's ledger; out-of-window SPs are skipped (`credit.py:141-143`) and keep fossil counts
  forever — contradicting the documented "recomputed, set not accumulated" window semantics, and feeding
  fossil credit into prune, protect, `_track_record` (`min_follow=5`), and `credit_distribution`. No test
  covers the case. **Fix:** zero the four credit counters on every SP before applying the ledger (live
  adoption bumps can't conflict — per-game SP counter updates never reach the run store).
- **Finding 3 (MED) — evict inert; the cheap fix lives here.** Set
  `retrieved/override/not_relevant_count` from the same eval-case pass (see the amended §0.4 bullet) —
  which also makes them windowed, consistent with Finding 2's zeroing.

**Minor, note-only (quantify only if a result leans on them):** `measure.py`'s ON arm counts only
memory-*active* decisions while OFF counts all (`measure.py:61`; retrieval-skips ≈6–16% post-day-1 are a
non-random subset — report the `--on-all` variant alongside each gen as a standing check); the wolf blend
reference is the day's *final* plurality including the wolf's own vote, with `max()` tie-break by dict
order (noise, not bias, at small tallies); a tagged SP's night ledger entry replaces its deterministic
credit wholesale, so follows on tag-failed days silently vanish for that SP.

**Standing invariant to add (makes the class structural):** every credited channel must have a
`base_rates` entry produced by the **same grading function** as its counts, computed from the **OFF arm**
— assert it in `invariants.py` next to `assert_base_rates`. The §11j/§12f class has now appeared three
times (run-1 vote baseline, v2 salvage halo, loop discussion/night credit); guard it, don't re-catch it.

---

## Phase 1 — the paid runs (~$15–35 each), in order

Each run pre-registers **one** primary endpoint; everything else is exploratory (multiple-comparison
discipline — see Standing gates).

### 1.1 Town-only run — the clean experiment + positive control (revised 2026-07-11)
The clean experiment never actually run (the v2 slip ran `all_enabled`, not `town_only` — see the v2
post-mortem). Static town effect is the strongest validated signal, so it's the natural positive control.
Fresh epoch, new memory system (tells + SPs injected, obs substrate-only), cold start.
- **Guard:** `--expect-factions town_only` (the arm-guard shipped after the slip).
- **Primary (one endpoint): the end-point paired A/B** — final store vs the initial (gen-1) store on 30
  shared boards, replayed in one batch; town decision basket is the graded quantity.
- **Secondary/exploratory:** Brier delta (book vs no book), checkpoint-replay curve per snapshot,
  SP-lineage join, B1 accusation-precision, the endpoint-vs-first-link diagnostic comparison, tell-corpus
  growth (the saturation premise).
- Pre-register the **stopping rule** before gen 1.

### 1.2 Wolf-only arm — the v7 thesis test (revised 2026-07-11)
The only compounding-shaped signal actually observed (+0.086 slope, rising to +0.28 — from the
invalidated v2, so directional motivation only).
- **Instruments (new):** endpoint + target-value day credit, the concealment floor (both guards), tell
  hit-rates + Brier, A2 `wolf_power_kill_rate`. **The tagger verdict is a diagnostic here, not a
  ruler** — tag both arms only if the diagnostic will be read comparatively (cheap, optional).
- **Prerequisites:** the detector golden bounded (this replaces the old Finding-1 gate, which the
  redesign superseded); the concealment-floor guards verified in the smoke.
- **Kept from the original design:** stratify by `sk_lynched` — otherwise ~40% of games (77/180 in
  v6ab) carry zero wolf-skill information and dilute toward null by construction. Fresh-epoch
  calibration of the now-diagnostic tagger comes free.

---

## Phase 2 — the labeling sweep: where gold labels are worth the hours

Two filters decide whether labeling pays: **is the instrument load-bearing for the next decision?** and
**is the ground truth crisp?** Through them, the "unverified" list sorts into two *gold types* that must not
be mixed — mixing the constructions is the one way the sweep quietly measures the wrong thing.

### Gold type A — extraction/coverage (via `golden_set_method.md`)
Human authors the **atomic reference points** a correct output must contain; a **citing** LLM judge scores
semantic *coverage* (recall) + *faithfulness* (precision). Human time goes into authoring/verifying points
(draft-with-model, verify-by-hand); the n-sizing applies to **pairs**, not points.
- **Consumers:** day-summary, post-game obs, situation-summary — **plus SP-synthesis as a 4th consumer**
  (not in the doc's table yet; add it). Synthesis has an advantage: its reference points can be
  **ledger-anchored**, not purely semantic — *"must retain the +0.26 endgame-pivot lesson; must not carry
  forward the −0.30 passive-abstain directive"* — crisper than prose coverage points.
- **Mandatory one-off:** calibrate the coverage judge itself — hand-match 1–2 pairs, check per-point
  agreement (~90% ⇒ trust at scale; below ⇒ fix point *granularity*, per the method doc §"Calibrate the
  judge once"). Budget the half-hour, or you've swapped an uncalibrated summarizer-judge for an
  uncalibrated coverage-judge.

### Gold type B — verdict/classification (plain human agreement labels)
No reference points, no coverage judge — just human agreement on sampled cases.
- **Consumers (revised 2026-07-11):** the behavior detector (presence/absence of a behavior), the tell
  dedup judge (same-claim merges), tactic self-report attribution (does the action instantiate the
  followed SP), the silence/novelty rule — and the tagger verdict only in its diagnostic afterlife.
- **For soft judgments, score *agreement*, not correctness.** The silence rule and framing have no crisp
  truth, and flash-lite's silent-update tendency means labeler-vs-model disagreement isn't cleanly "model
  wrong." Report "agreed 11/15, 3 genuinely ambiguous" as a **bound on trust**, never an accuracy claim.

### Priority (rewritten 2026-07-11 for the read/tactic design; load-bearing first, completeness tail last)

| Target | Gold type | Verdict | n (rule of three) | Why |
|---|---|---|---|---|
| **Behavior detector (role-blind)** | B | **1st — gates the run** | 30–50, stratified; AI pre-label → human adjudication (~1–1.5h human) | Every tell hit-rate rides this pass — the redesign's one load-bearing golden (it replaces the tagger golden). Includes the role-blindness leak check: detection must not shift when roles are visible. |
| **SP-synthesis output** | A (ledger-anchored) | **2nd — reference points authored during the consolidation re-derivation (§R)** | per-cluster points | Unchanged rationale: synthesis is the compounding mechanism, it inverted a lesson once, and it has **never** been judged. Ledger-anchored points ("must retain the +0.26 lesson; must not carry the −0.30 directive") are crisper than prose coverage. |
| **Tell dedup judge** | B (spot-check) | **before trusting pooled counts** | 15–20 merges (~45 min) | Asymmetric risk sets the bar: a **wrong merge** pools counts of *different* claims and miscalibrates hit-rates; a missed merge only splits support (conservative). Bound, not golden. |
| **Tactic self-report attribution** | B (spot-check) | with the first credited window | ~15 (~30–45 min) | Bounds the dilution from ~99% follow rates; valence is deterministic, so the failure mode is smear, never sign error. |
| **Extraction objective-description check** | verification read, not a golden | rides the tell-mining probe (§R item 2) | sample | The tell-mining precondition: behaviors objectively described, never role-inferential. Absorbs the old post-game-obs row — same reassurance, cheaper form. |
| Discussion tagger | B | **Moot for credit (demoted to diagnostic 2026-07-11)**; optional tail | 30–50 only if ever needed | Label only if the diagnostic is ever cited as a headline number. |
| Situation dimensions | — | **Skip for now** (unchanged) | — | Live path is covered; the unverified parts are default-off or bounded. Labeling improves a knob you're not using. |
| Situation-summary semantic accuracy | A | **Defer** (unchanged) | — | Already measured by outcome (NDCG); stakes further reduced now that observations left the prompt. |
| Silence rule / novelty gate | B | **Defer; run the free audit first** (unchanged) | soft | Instrumentation shipped; the next batch gives a $0 descriptive answer first. |

### Guardrails (keep a low-N sweep honest)
- **AI-assisted labeling (added 2026-07-11).** AI pre-labels every set; the human adjudicates every case
  the AI flags as uncertain plus a stratified subsample of the confident ones. **The reported bound
  comes from the human-verified n only** — AI throughput widens coverage, it never substitutes for the
  bound — and human–AI disagreements are the most informative cases, never discarded.
- **Pre-commit before looking, per instrument:** the question, the n, and what counts as an error.
  Time-box each 30–60 min.
- **Size n by the rule of three, not vibes.** Zero errors in n items ⇒ 95% upper bound ≈ 3/n. n=10 ⇒
  "could still be wrong 30%"; n=15 ⇒ ~20%; n=30 ⇒ ~10%. Completeness-tier ⇒ n≈10–15; load-bearing ⇒
  n≈30–50. **Write the bound, not just the count.**
- **Stratify, don't random-sample.** Force the hard cases (the off-diagonal sampler is the template; the
  tagger equivalent samples verdicts that *disagree* with the vote-endpoint floor — where the tagger claims
  to add information).
- **File each mini-golden in the instrument's evidence folder and flip its gaps-table line** from
  "unverified" → "bounded: error ≈ X at n=15, directional." An explicit bound signals you checked; a blank
  signals you didn't look.
- **Sequence so the sweep can't delay decisive work.** The two load-bearing goldens + the paid runs come
  first; the completeness tail is fill-in work *while games run*.

> **On "label everything, scaled by load-bearing-ness":** endorsed. With AI pre-labeling, total program ≈
> **4–7 human-hours**; only the **detector golden** (and the synthesis reference points, which the
> consolidation re-derivation produces anyway) must land **before** the paid runs — the two spot-checks
> ride the first credited window.

---

## Phase 3 — new signal / deliberate epoch bump

**Free mines on the next batch ($0, already-shipped instrumentation unread):**
- Gate-selectivity audit (the `gated` flag + gated-candidate text now persist) — "what does the proactive
  gate eat, by role and stance?"
- C0 claim-timing joins (`role_claims` now persists — the field that was 0/180 in v6ab).
- `strategy_verdicts` "why"-text mining — *why* do agents follow SPs?
- **Wolf self-leak check (added 2026-07-05, with the wolf_channel day extension):** deterministic
  n-gram/substring overlap between each wolf's public day messages and its `wolf_channel` content — the
  original (untested) worry that day visibility makes wolves parrot night coordination in public. If it
  fires, the prompt-instruction mitigation needs teeth.

**One bundled epoch reset, if/when a stronger substrate is wanted (re-baseline once, never drip):**
- **Whiff-disclosure change E** (wolf-side): the whiff audit says visibility is the binding layer and the
  vigilante is the natural experiment proving conversion follows disclosure — this creates a genuinely
  *learnable* wolf lesson for memory to compound.
  **BUILT 2026-07-05** (wolf_channel note, vigilante-mirror; epoch-bump pending the bundled reset).
  **extended 2026-07-05:** wolf_channel now attached to wolf DAY discuss/vote payloads (fixes the
  day-lag + the empty day situation-summary slot); wolf day prompts carry a confidentiality
  instruction to guard against self-leak (parroting night coordination), flagged for next-batch
  measurement.
- Deferred prompt-pass items (structured dead-roster, anti-repetition — the day-3 "I agree we can't keep
  abstaining" loop).
  **BOTH BUILT 2026-07-05:** deterministic `dead_roster` state (every death path verified to publicly
  reveal the role — night kills at resolution announce, lynch at orchestrator announce) rendered in all
  day discuss/vote prompts; `ENGAGE_WITH_DISCUSSION_RULE` added once at the shared discuss-template level.
  **Known residual (reported, not fixed):** the repetition mechanism is the `opener_floor=3` novelty-gate
  bypass — the day's first 3 utterances are ungated by design, exactly where the identical openers landed;
  prompt-level fix shipped, mechanism deliberately untouched. Night prompts don't carry the roster yet
  (deferred). Current bundle contents: change E + wolf_channel day + SP tiering + dead-roster +
  anti-repetition.
- Optionally the 3.5-flash **variance** pilot (10 games, measured on variance not quality).

---

## One architecture idea worth a cheap flag

> **Superseded 2026-07-11:** the read/tactic redesign removes observation injection entirely (tells +
> SPs are the two channels), which subsumes this per-cell idea — the villager/day_vote question gets
> re-tested for free by the new arm rather than by a config flag.

v2's single negative cell was **villager/day_vote (−0.118)**: SP directives underperform villager gut+obs
inference exactly where the proxy looks. Consider a **per-cell channel config** — obs-only for villager
votes, SPs for power roles and deceivers — as a config-flag variant (a coexisting incremental A/B →
config flag, not a worktree, per the project's variant-versioning policy). Consistent with everything measured
(town benefit was defensive/obs-driven; SPs are the deceiver channel), and it's a one-line arm to add
whenever you're already paying for town games.

---

## Standing gates (apparatus feedback → make these permanent)

The rigor arc is genuinely strong — pre-registration, arm guard, invariants layer, paired arms, honest
retractions. The failure class that bit twice ("the harness ran a different experiment") is now guarded.
Three residual weaknesses, each with a standing fix:

1. **No power discipline.** Every design step is pre-registered except N, which was chosen by *budget*, not
   minimal-detectable-effect. → **Add the power calc (0.1) as a standing pre-run gate.** No paid run without
   an MDE table.
2. **A growing proxy garden** (validated + diagnostic tiers + tagger). → **Each run pre-registers exactly
   one primary endpoint and demotes the rest to exploratory**, or the multiple-comparison floor eventually
   hands you a fake positive that survives the other guards.
3. **All mechanism evidence lives at the game grain.** → **SP-lineage (0.3) + replay (0.2) move
   "compounding" from one-number-per-generation to many paired mechanism-level observations** — more
   powered *and* more demo-legible for the portfolio write-up.
4. **Baseline coherence is convention, not invariant** (new, from the 2026-07-04 audit). The
   level-not-lift class has now appeared **three times** (run-1's vote baseline §11j, the v2 salvage halo
   §12f, the loop's discussion/night credit §0.5). → **Make it structural:** an `invariants.py` assert
   that every credited channel has an OFF-arm `base_rates` entry produced by the *same grading function*
   as its counts. Stop re-catching this class by re-audit.

---

## Sequencing & bottom line

```
§R critical path (1–2 days)                    →  Phase 1 (paid, ~$15–35/run)    →  post-run
  D1: decision_scoring teach-back (user)           1.1 town-only, fresh epoch,       checkpoint replay
      tell-mining probe + dedup v0 (AI)                END-POINT A/B primary          (one batch) ·
      v1 credit wiring + invariants (AI)           1.2 wolf-only (detector           first-link vs
      detector golden: AI prelabel +                   golden bounded; sk_lynched     endpoint · density
      user adjudication ── GATES THE RUN               strata; tagger=diagnostic)     census · lineage ·
  D2: consolidation re-derivation (user)                                              tail labels ·
      dedup + attribution spot-checks                                                 controls registry
      replay screen + cross-epoch check (AI)
      pre-registration → smoke → LAUNCH
```

**Critical path / gates (2026-07-11):** the detector golden and the signed pre-registration gate the
launch; the consolidation confrontation gates only its own integration (the code is otherwise at its
validated 2026-07-05 state). The power discipline stands — the end-point A/B *is* the answer to the MDE
wall; do not re-grow a slope readout mid-run.

**Bottom line (2026-07-11):** ~1–2 gated days — two user derivations, one AI-prelabeled load-bearing
golden, the v1 credit build, two cheap screens — then run town-only and wolf-only on instruments that
are deterministic or explicitly bounded, with the tagger watching as a diagnostic.

**§6.8 obs-injection fix built (2026-07-15):** the loop no longer injects observations —
`LoopConfig.retrieval_types` defaults to `strategy_points_only`, the driver passes `--retrieval-types`
on both arms, and a per-generation invariant asserts the obs block is absent (recorded config +
sampled prompt input). Clears the store-curation §6.8 launch blocker; the pre-reg config pin still stands.

---

## Open questions / gaps (freshness: 2026-07-11)

- **Replay ≠ live compounding.** Rung 2b (frozen boards) and rung 3 (in-situ) are genuinely different; the
  G3c replay-flat precedent means a flat replay curve is a real null but a rising one still doesn't prove
  rung 3.
- **The detector golden's bound is unknown until labeled.** If it comes back poor, tell credit has no
  trustworthy floor and the run slips (the §R honesty clause). Same clause covers the consolidation
  confrontation surfacing a validity-gating change.
- **Tell-corpus saturation is a premise, not a fact.** Detection scores the full corpus each game;
  growth rate is a pre-registered first-run readout, with archive-below-floor as the relief valve
  (design record §8).
- **The reads_first "~40% cold filler" figure is from the session record** — re-confirm against the
  replay-probe outputs before it becomes load-bearing; the read-ordering re-arbitration rides the first
  smoke (it degrades the first-link *diagnostic*, not v1 credit).
- **Soft-label instruments (silence rule, framing) yield bounds, not certifications** — flash-lite's
  silent-update behavior means disagreement isn't cleanly "model wrong."
- **The audit's minor notes are logged, not fixed** (measure ON-arm selection asymmetry; wolf-blend
  self-inclusion/tie noise) — quantify only if a Phase-1 result leans on them; the `--on-all` standing
  check is the one cheap habit to adopt now. (The tagger partial-coverage override note retired with the
  override itself.)
- *Resolved since 2026-07-04:* the MDE prior (§0.1 executed — noise ≈0.3/game, slope retired); fuzzy v2
  lineage (`distilled_from` shipped); the §0.5 Finding-1 decision (Option A implemented, then largely
  mooted by the tagger demotion — see the §0.5 stamp).
