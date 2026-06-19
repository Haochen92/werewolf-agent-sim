# v7 (final memory iteration) — build log

**What this is:** the chronological narrative of the v7 credit / consolidation / discussion-credit build —
the reasoning, each test and its result, each conclusion, and (most importantly) **what we cut and why.**
The design docs (`plan.md`, `consolidation_design.md`, `discussion_credit_design.md`) hold the *current
state*; this holds the *journey*. All work below is zero-spend on the existing v6ab dumps unless noted.

**One-line throughline:** at every step we **removed an imposed prior or a free-but-dirty shortcut in
favor of clean signal.** The list of things we *cut* is the real result (see §10).

---

## 0. The reframe (the premise everything rests on)
v7 is the last memory iteration; its headline is the **compounding loop** (self-correcting content via
realized-outcome credit + decay), **still un-run** (the one paid test). The cheap-screen campaign
relocated the binding constraint: **CONTENT, not retrieval.** Every retrieval lever is closed (rerank ≈
raw; the LLM reranker already judges top-k relevance; structured dimension-gating validated null Δ−2%; the
agent already filters applicability inline). **The decisive tell: following the *applicable* memory still
doesn't improve decisions (G3a)** → the cap is content *quality*, and only the loop can fix it.
(`plan.md` §1a.)

## 1. The cheap-screen campaign (the foundation, pre-registered gates)
- **G1 — investigator de-cap:** the "survival is primary / don't accuse early" framing is FALSE+HARMFUL
  (caps the find→lynch transmission chain). Shipped the neutral transmit prompt as default; baseline kept
  runnable. A correctness fix, not a treatment.
- **G2 — separability (PASS, channel-specific):** decision quality is attributable above a luck-null
  per-faction (town day-vote r=+0.56, healer-block +0.42, SK-kill +0.26, wolf-blend +0.22). NULL:
  investigator-night-find (transmission cap), wolf-night-targeting. **Ruling: G2 is a DIAGNOSTIC that
  localizes prompt caps, NOT a channel pruner — keep all channels; fix the nulls at the prompt.**
- **G3a — verdict-validity (decisive):** decay-on-override is **DEGENERATE** — agents follow ~99% of
  applicable SPs (town day-votes: 3 overrides vs 334 follows). **→ credit must be the realized de-luck
  OUTCOME of followed decisions, NOT the agent's override choice.** This reshaped all of (a).
- **G3b — target-advocacy (PASS):** the offense channel is real, creditable, separable (advocacy→lynch
  Δ+0.46; per-game advocacy-precision ↔ town_won r=+0.45).
- **G3c + gating:** retrieval precision is the bottleneck and similarity is *blind* to applicability;
  structured dimension-gating beats similarity but **its LLM-judge replay came back FLAT (Δ−2%)** →
  retrieval **parked**, knob default-off.
- **Leverage-anchor:** extraction selection can anchor on leverage *decisiveness* (the P(win|miss) floor),
  not marginal Δ (which is flat).

## 2. (a) Credit — built + validated
**Problem (first principles):** the store has no notion of which memories are *good*; the only quality
signal (`net_verdict`) is an **outcome halo** (calibrated to faction-won, not pivotalness).

**Discovery:** half of (a) already existed — `adoption.py` writes `follow/override` counts live during
play. The missing half was the **outcome tally** (`positive/negative_count`) — never written. (a) closes
that join: followed SP × the decision's **de-luck proxy** (`score_vote`/`score_night_target`, faction-
relative) → a credit ledger.

**Design rulings:** SP-only (observations ride frequency × criticality, not credit — you don't *follow* an
observation); reward = de-luck per-decision proxy, **never game win/loss** (the halo).

**Result** (`credit_backfill.py`, ledger 100% key-joined to v6_1): mean **RAW +0.43 → LIFT +0.03** once
baselined against memory-off — i.e. **memory is a wash, confirming the prior null** (the +0.43 was the
halo). NOT flat: ~20 SPs help, ~18 hurt — including the single **most-followed note (79 follows) being a
net loser.** Face validity (winners = credibility/info-protection plays; losers = vague defensive notes).

**Held-out validation** (`heldout_credit_reproduction.py`): split games, losers on A stay negative on B
**89% vs 61% base; Pearson(lift_A,lift_B)=+0.54**. Real signal, not circular; the lone flip had 3 follows
→ vindicates the evidence floor.

## 3. b1 prune — built + executed
**Thresholds** (`consolidation_design.md` §6a): **N≥8** (follow floor — derived from the noise floor:
median 3 follows is mostly variance), **τ≤−0.15** (drop only notes ≥0.15 *worse than no-memory* — "harmful
beyond the noise band"). Pragmatic, not statistical (CI-based is ideal but n too small).

**Executed** (`consolidation_prune.py --apply`): 8 stably-bad SPs → `memory_stores/v6_1_b1pruned`
(1% removed, 298 follows prevented). Canonical untouched, live pointer NOT flipped, guard-asserted
(no positive-lift/thin dropped). Dropped notes = the passive/vague advice, as expected.

## 4. (b) Consolidation — designed
**Model:** (a) is the thermometer, (b) the thermostat; the store is the shared state. **SP ops = keep /
discard(dup) / drop(bad) / revise — NO MERGE** (merge is observation-only: obs pool *evidence* for a fact,
strategies are *directives* — averaging two directives is incoherent → discard-the-worse). **Revise =
in-place** (keep lineage, re-earn trust on post-revision credit). **b1 free + b2 paid LLM synthesis**
(every 5 games, rolling window, revise/keep/drop). Single trigger (T1 mature+mediocre→revise).

## 5. §10 cleanups — three priors removed
- **Density guard:** §10a hid two things — aggregate weight-fit (regress a role's composite across
  hundreds of decisions → reliable, sets thresholds) **ON**; per-SP *dimensional* credit (slice ~3 follows
  by axis = noise) **OFF**. The latter is the per-dimension trap; §10a's "per-point grain" wording invited
  it back.
- **Offense floor DROPPED:** a hard "offense must be non-zero" rule **imposes a prior** — if passivity
  wins, it forces the agent off the optimum (the halo, reversed). The v6 passive-SK came from crediting a
  *surrogate* (`suspicion_drawn`), not from a missing floor → **guard the metric, not the policy.** Three
  mechanisms catch the collapse without a prior (outcome-anchored credit · leverage-weighting · maturity
  gate). Offense/defense demoted to a *diagnostic*.
- **LLM-valence — weight, don't discard:** measured the halo-load (`net_verdict` vs `role_faction_won`,
  932 obs): **corr +0.45, NOT pure halo; ~22% residual disagrees with the outcome** = the additive signal.
  → use the de-haloed residual (structure = high-weight feature; valence = low, empirically-weighted).

## 6. Windowed-credit test — REJECTED a deterministic delay window
**Hypothesis (user):** a decision's value is "felt on another day"; extend the credit window.
**Test** (`windowed_credit.py`): immediate de-luck vs survival@1/@2 vs terminal. **Survival is orthogonal
to decision quality (imm↔surv1 +0.14) and drifts to halo with window length (surv1→surv2→terminal =
+0.14→+0.37→1.0).** → the **clean⊥delayed⊥free triangle**, empirical: the free delayed signal trades
cleanliness for delay. **Don't wire a deterministic window.** The genuinely-delayed/causal cases are
discussion SPs → route to (d)/(c2), not a window.

## 7. (c) Extraction redesign — scoped
The extraction pass *is* the omniscient hindsight LLM (it already emits the haloed `net_verdict`), so fold
the credit-LLM work into it rather than building a separate judge. **c1** = the selection anchor (which
lessons extract, deterministic leverage). **c2** = emission redesign: emit *structure* (omission, causal
swing, influence) as features; de-halo the valence. **Success metric = does `corr(net_verdict, faction_won)`
drop below +0.45** while structure fields populate. Freeze-gated (versioned variant + re-validate).

## 8. (d) Discussion credit — designed + free floor measured
**d0 cut:** the free deterministic advocacy signal is **thin/redundant-with-votes** (target-correctness,
not discussion-specific) and the other free signal (lead-vs-blend) is null → **committed to d-full.**

**Design:** role-by-role objectives → **7 primitives / 3 axes** (offense/defense/transmission), used as a
**detection lens, not credit buckets** — *tag fine, credit coarse* (per-axis ≤3, the score_tier rule).
Architecture: **per-round-chunked, deferred flash-lite tagger**, structure-not-valence; `role_claims`
needs a small gameplay-neutral persist; the agent's own reasoning is a carrier on the EvalCase.

**Amendments (the critique rounds):**
- **A1** — framing + credibility need only **end-of-day**, not end-of-game.
- **A2** — **determinism ⊥ halo:** "conceal = heat-low + survived" being deterministic makes it cheap to
  compute, NOT safe to credit (the passive-SK tautology). Concealment credit keeps the §10a brackets
  regardless of being free.
- **A3** — add the **night-action (exposure) endpoint:** the day-vote is the consensus axis and is blind
  to discussion consequences that land at *night* (reveal-risk, confirm-out, the *hidden read*).
- **A4** — the agent's **own reasoning** (vote/night rationale) de-confounds night-attribution + surfaces
  hidden reads + gives self-reported influence chains. **Per-round chunking dissolves the
  post-game-vs-end-of-day dichotomy** (input unit ⊥ when-fired → deferred per-round = one flash-lite call
  per round, not per game).

**Coverage map:** deterministic covers the *outcomes* of **6 of 7 primitives**; **framing is the one it
can't even detect** (the irreducible LLM job). The **vote** is a global all-player endpoint giving final
heat on self + teammates (team-aware — key for wolf/town team play).

**Free-floor measurements** (`discussion_coverage_check.py`):
- **M1 — day-vote endpoint credit = the broad free win:** 100 discussion SPs credited (2.4× the advocacy-
  only 41), held-out **Pearson +0.51 (n=51)** ≈ board's +0.54. Defense reach: 31% of turns under heat.
- **M2 — Part-3 night-exposure is frequent + vote-blind:** deceivers night-kill power roles without visible
  day-heat — **wolves→power 71%, SK→power 62%** — i.e. most power-role deaths happen at night on reads the
  day-vote never flagged. Worth wiring; the night-reasoning (A4) is what attributes it.

## 9. Conclusions / current state
- The **free deterministic floor is strong + broad** (day-vote endpoint +0.51 + heat + night-exposure) —
  covers the outcomes of most role objectives.
- The **LLM tagger narrows** to framing-detection + credibility + reasoning-attribution, validated by
  **incremental** Gate B (does it predict beyond the deterministic floor — the honest kill-test).
- **Built + validated + committed:** (a) credit, b1 prune, the (d) free floor. **Designed:** b2, c1/c2,
  d-full tagger.
- **Build order:** reasoning carrier + `role_claims` persist (neutral) → wire the deterministic floor
  (free) → b2 + c2 + d-full tagger (paid, each with a kill-test) → **the compounding loop** (the headline
  paid test, NOT run, awaiting green-light).

## 10. ⭐ What we CUT, and why (the journey's real output)
| Cut | Why |
|---|---|
| Game-outcome / `net_verdict` as credit | outcome halo — replaced by de-luck per-decision proxy |
| Per-SP dimensional credit (T2) / §10a "per-point grain" | density trap — ~3 follows can't be sliced by axis |
| T3 "fresh-evidence" trigger · T4 conflict-merge | T3 = what synthesis does; T4 = dedup's job |
| Merge for strategy points | merge pools *evidence* (obs); directives can't be averaged |
| The offense floor | imposes a prior; guard the metric (surrogate) not the policy |
| Deterministic delay window (survival) | orthogonal to decision quality + drifts to halo (the triangle) |
| d0 advocacy-only discussion credit (as sufficient) | thin/redundant-with-votes; lead-vs-bled null |
| Per-message counterfactual | needs a resample; coarse credit over many instances is the stand-in |
| Treating "deterministic" as "safe to credit" (A2) | determinism ⊥ halo — cheap to compute ≠ de-circularized |

**Not cut, kept honest:** every paid build (b2, c2, d-full) carries an explicit kill-test, and the free
floor is strong enough that the paid pieces are refinements, not leaps of faith.
