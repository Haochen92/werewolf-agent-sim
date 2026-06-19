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

**Does synthesis (regeneration) self-correct the SP wash? — eyeballed 2026-06-19
(`sp_synthesis_quality_check.py` underpowered via lexical join — synthesis PARAPHRASES, so token-overlap
can't trace carry-forward; switched to manual read of worst-credited per-game SPs vs the synth store
`v6_1_sp_cluster`).** The cluster-synth prompt drops `net_verdict` from the CLUSTER KEY but weights
directives by the cluster's outcome SPREAD — and that outcome is the obs' HALOED `net_verdict`. So
synthesis optimizes the halo, not de-luck lift. Result is **FACTION-SPLIT, exactly as halo⊥de-luck
predicts:**
- **Town (villager/day_vote):** worst per-game SP = "advocate and vote to ABSTAIN" (−0.20/69-follow);
  synth FLIPPED it → "do not abstain, force a resolution, a tie benefits evil." Self-corrected — because
  here passivity loses on BOTH halo and de-luck (they agree).
- **Deceiver (serial_killer/day_vote):** worst per-game SP = "deflect, vote with the bloc, ABSTAIN to
  minimize record" (−0.30/79-follow); synth REPRODUCED it nearly verbatim ("blend in, join the majority,
  abstain with them"). NOT corrected — here "blend+survive" looks good on the halo but is bad on de-luck
  (the passive-SK tautology); they DECOUPLE, and halo-weighted synthesis carries the loser through.
- ⇒ **Synthesis self-corrects where halo≈de-luck (town) and fails where they decouple (wolf/SK).** The
  loop's (a)+(b) de-luck credit is therefore MOST needed on DECEIVER cells; a go/no-go should watch them
  specifically. (Caveat: town read is partly the plausibility trap — active SPs match our anti-caution
  prior; the SK read is firmer — concrete carry-forward of a −0.30-credited directive.)

**⚠ EPOCH-STABILITY caveat (user, 2026-06-19) — these verdicts are v6ab-conditional, not laws.** The
held-out reproduction (Pearson +0.54) proves SAMPLE-stability *within* the v6ab epoch, NOT epoch-stability;
"stably bad" should read **"bad in v6ab."** Epoch drift is known real here (it killed cross-run
comparisons). And we're actively changing the meta (town de-cap → shifts what SK plays against), so
passive-SK's value is especially likely to move. Split: **(i)** board-OBSERVABLE variation (passive bad
when town votes aggressively) = a conditioning failure → carry the condition (C-ii) + slice credit by it;
**(ii)** HIDDEN epoch variable (model vintage/backend) = not conditionable → re-credit per epoch (rolling
window §3C). Consequences: the **b1 prune is epoch-PROVISIONAL** (kept reversible on a copy, pointer not
flipped — correct), a mechanism validated in v6ab **does not transfer free** to the loop's run epoch (must
re-validate in-epoch), and **no single-epoch credit — incl. the deceiver-split above — is a fixed prior;
it's a hypothesis the loop re-tests on-policy.** No free test exists (epoch drift makes cross-epoch games
incomparable).

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

**⚠ Prior-record correction (2026-06-19) — the de-halo must NOT undo a validated win.** The current
net-effect-first `outcome` ordering was *deliberately adopted* as the v5 default, not an accident: net-
horizon framing REMOVED the SK harm (`sk_lynched` 0.80→0.63, win 20%→37%, `paired_ab/report_nethorizon.md`
2026-06-12) because immediate/success-framed SK entries were **cost-blind**; wolf stayed FLAT (+0.03 — an
*adherence* gap, not framing); and for town the right framing is **situation-dependent** (`decision_replay`
2026-06-13: net/cautious helps day-2 info-starved +0.167, but cautious is the game-level problem → no
blanket horizon wins). ⇒ Three constraints on c (now in `plan.md` §3 D′): **C-i** drop the *luck*, keep the
*cost + causal chain* (de-luck ≠ de-delay); **C-ii** emit the *condition*, never one global framing;
**C-iii** the wolf is an adherence/injection item, not c's job. And **D″:** the (d) discussion tagger is
c's discussion slice (one project) but likely a separate cheaper call feeding extraction — don't pay for
two omniscient reads.

**⚠ Consumption-model correction (2026-06-19, user) — split the de-halo by surface.** The agent is now
fed the **synthesized strategy_point as the directive** and **observations as a fact-checker** (case
evidence that corrects/overrides the rule — `Agents/prompts/memory/context.py` synergy instruction). The
framing experiments above were measured when *observations were the directive* — that regime is gone. ⇒
**C-iv** (now in `plan.md` §3 D′): steering de-halo + situation-conditioning migrate UP to **SP synthesis
(b2)**; **C-i (cost/causal chain) stays on the observation emitter and matters MORE** (it's what powers the
`override` fact-check); observation C-ii de-emphasizes to accurate situation-dimensions + clean facts; and
the `decision_replay` framing result is a **re-validate-under-new-regime target**, not a given. This also
re-weights c: a chunk of its de-halo work is really **b2 synthesis-prompt** work.

**⭐ SYNTHESIS A/B — credit-aware synthesis WORKS (2026-06-19, `synth_deluck_ab.py`, pro-2.5, READ
eval).** The binding lever. 3-way per deceiver cell: **H** halo-synthesis (current, weights per-obs
net_verdict) · **D** credit-aware (weights the REALIZED de-luck track record from the ledger, asked for a
CONDITIONED directive) · **S** pure-prune survivor (just the top-lift credited SP, no synthesis).
- **First-principles reframe (user, "thinking cap"):** there is NO clean STATIC de-luck signal for
  deceiver decisions (deterministic proxy weak/null; an LLM "decision-quality" re-judge is UNVALIDATABLE —
  re-derives the halo or the survival tautology). The ONLY trustworthy de-luck signal is **realized credit**
  (the ledger, from played games: SK-blend = −0.30). So the de-luck arm feeds the realized track record,
  not an LLM judge. And synthesis only beats pure-prune if it produces a better-CONDITIONED rule than the
  top survivor (else "just prune (b)").
- **Result (SK day_vote, all 3 clusters):** H reproduced the passive **blend loser** every time; **D
  produced a conditioned active policy** every time ("default blend for cover → PIVOT to lead the vote
  against an analytical threat in the endgame; attack methods not role; don't escalate speculatively" —
  fusing the +0.26 winner, the −0.30 loss-guard, and the default into one IF/THEN). **D > S**: S is the
  right-but-narrow endgame move alone; D adds the default + switch-condition + guard. D's conditions are
  ledger-grounded, not invented.
- **SK night_action:** H ≈ D (both reasonable; D adds a refinement) — no stark halo⊥de-luck decoupling
  there, so credit-awareness is ~neutral. ⇒ **credit-aware synthesis corrects the inversions where halo
  and de-luck decouple (the deceiver day-vote), neutral elsewhere** — exactly the right behavior. wolf/
  day_vote skipped (no credited SPs ≥5 follows).
- **⚠ PRODUCTION-COST constraint (user):** pro synthesis ≈ **40s/call**; full store (~17 cells × ~3-5
  clusters) SERIAL on pro ≈ **30-60 min**, every 5 games = untenable. Mitigations: **concurrency**
  (independent calls → ~3-5 min at 16 workers; `synth_deluck_ab.py` parallelized — proved it), **incremental
  re-synth** (only cells with new obs → seconds), frequency, tiering. ⇒ the loop's synthesis must be
  **incremental + concurrent** (pro per-call, FEW calls, parallel) — a real loop-design requirement.
- **FLASH-LITE synthesis RUN (2026-06-19, full A/B `--tag flite`, both SK cells × 3 clusters):**
  **flash-lite ≈ pro at synthesis.** Day_vote (the decoupled cell): every cluster's D produced active,
  track-record-grounded directives (eliminate-the-analyst +0.26, amplify-against-target +0.15,
  vote-with-majority-for-cover +0.15) and **avoided the blend loser** — same as pro; H reproduced the
  blend loser as always. Night (neutral): H≈D, both reasonable, same as pro. **~3× faster** (flash-lite
  ≈15s/call vs pro ≈45s). The single-cluster "thinness" earlier was an artifact — on the full run
  flash-lite covers the full gradient (incl. the cover regime). ⇒ **"pro justified at synthesis" is mostly
  REFUTED** (pro buys marginal regime-boundary crispness, not correctness) and **the production-cost
  concern DISSOLVES** (flash-lite + incremental + concurrent → seconds/cycle). Loop synthesis = flash-lite,
  pro only as a quality top-up. Caveat: a READ, n=2 cells; true followed-and-helps = the loop.
- **DIMS-ALIGNMENT check (user, `inspect_synth_dims.py`) — RESOLVED + refined.** The situation dimensions
  are the RETRIEVAL key (LLM-assigned per SP at synthesis, same schema as obs, composed → embedding +
  reranker features); clusters are gate_key-partitioned (is_swing + alive-bucket + consensus) = one regime.
  Worry: a CROSS-REGIME conditioned directive (mid blend / endgame pivot) with single-regime dims would
  retrieve in only one regime (the conditioning dormant). Inspection of the actual D output: synthesis
  **SPLITS the gradient into regime-scoped SPs with dims matching each branch** (e.g. SP@alive=6 mid-cover,
  SP@alive=3 is_swing endgame-pivot) — retrieval-ALIGNED — and even generates a properly-scoped ENDGAME SP
  from a MID-game cluster by pulling the track-record winner (coverage propagation). BUT non-deterministic
  (an earlier run blobbed it). **Fix (shipped): added a SPLIT-BY-REGIME instruction to CREDIT_SYNTH_PROMPT**
  — "if the right move changes across regimes, emit one SP per regime with dims set to that regime; never
  fuse a cross-regime gradient." Re-verify: D produced **3 regime-scoped, dims-aligned SPs**, and correctly
  distinguished *active blend* (vote-with-majority, +0.15, kept) from *passive abstain* (minimize-record,
  −0.30, dropped) — the gradient read right, not winner-copied. ⇒ the conditioning is retrievable; the
  content win survives into the retrieval layer. (Still pending the true followed-and-helps test = the loop.)

**Settled (2026-06-19) — leverage anchor = soft prior + budget, NOT a whitelist.** Two extraction concerns
raised: (i) self-judged "pivotal moments" = a selection-layer halo; (ii) the 6–12 obs / 3–8 SP floor pads
low-value content. The fix is to anchor selection on the deterministic leverage FACT (do-or-die =
P(win|miss) floor) + a leverage-derived budget — but **only as a soft must-cover + budget, never a
turn-scoped whitelist** (that re-imposes §344, loses the causal-chain pass, gates discovery). Decisive
reason: **omission is unrecoverable, commission is recoverable** — the credit loop prunes over-extraction
but can't credit a never-extracted lesson → extraction errs **high-recall**; and the leverage signal is
town-day-vote-only (night / framing / omissions blind), so a whitelist would blank-out the channels c wants
to improve. Recorded in `plan.md` §3 D-anchor.

**Free pre-screens RUN (2026-06-19, `extraction_quota_screen.py`, RAW no-dedup v6_1 store = 932 obs / 20
games / 17 cells, built by the LIVE prompt builder `build_cell_observation_tail`):**
- **Screen 1 — quota-binding: DISPELLED.** mean **2.78** obs/game-cell, median 3, **max 6, 98% BELOW the
  prompt's 6-floor, 0% near the 12-cap.** The extractor UNDER-delivers, varies naturally (1→6) — no
  padding-to-ceiling. (Reinforces recall-is-the-risk: the model already errs too-few.)
- **Screen 2 — near-restatement: DISPELLED.** mean intra-cell Jaccard 0.21, **0 near-restatement pairs**
  (>0.5), no size→redundancy slope (r=−0.03). Multi-obs cells are DISTINCT, not padded.
- ⇒ **Both padding hypotheses are out.** (a)'s store-is-a-wash (lift +0.03) is therefore NOT from padding;
  by elimination it concentrates on **confabulation / validity / halo** — which the free screens cannot
  touch (needs re-extraction or downstream credit) and which c2 + the credit loop target.
- **Re-prioritization:** the quota→leverage-budget fix (§D) drops to LOW priority (quota non-binding); the
  leverage anchor narrows to **validity-only** (kill the self-judged-pivotal halo, not set a budget).

**The real extraction question is RECALL, not de-halo (user, 2026-06-19).** De-luck credit / synthesis /
prune all operate only on what extraction captured — **omission is the one error the loop can never fix**
(commission gets pruned; a never-extracted lesson is permanent). So "does it capture what's NEEDED" gates
everything de-halo does. Free directional reads: the extractor is **thin** (median 3 obs/cell) but **NOT
temporally blind** (obs span early 250 / late 194 / parity 333 across all cells — not early-clustered). But
"captures what's needed" is **not free-measurable** — it's a counterfactual, and the leverage-labeled
corpus (v6ab town day-votes) never extracted obs. ⇒ **the right extraction A/B is a RECALL test
(capture-rate of leverage-flagged pivotal turns), NOT a de-halo framing test** — de-halo only matters for
lessons already captured. Plus a **model-capability arm** (gemini-2.5-pro vs 3.5-flash vs 3.1-flash-lite):
the loop re-extracts every game, so extraction-model cost dominates its recurring bill — a cheap-enough
model makes the whole loop cheaper. Full design + kill-tests + the small-slice pre-gate (the "don't pay for
nothing" guard) in `extraction_coverage_ab_spec.md`. ⚠ flash-lite breaks on the schema's `str|None` dims
(needs an all-required variant); all results epoch-conditional + freeze-gated.

**BUILT + RUN (2026-06-19) — model arm + recall arm.** Model-arm pre-gate CLEARED: flash-lite VIABLE (the
`str|None` parse fear did NOT materialize); pro/3.5/lite comparable on volume + distinctness; de-halo
inconclusive on 3 games. Recall arm (`recall_flags.py` flagger + `--anchors-from` suggestive-anchor +
`recall_capture_metric.py`) = WEAK: **the suggestive anchor does NOT rescue flash-lite's recall** —
within-model anchor on=off (3/12 flagged turns hit), reading shows only ~+1 obs on a flagged context,
manufacture guard clean. pro covers flagged turns ~10× denser (47 vs 4 obs on flags) — a real gap the
anchor doesn't close. ⇒ don't scale the flash-lite-rescue.

**QUALITY READ (manual, the decisive evidence):** read full obs across pro/flash-3.5/flash-lite on the same
games/cells. All three identify the SAME critical observations (the SK's fatal vote-record; the Investigator
mislynch) — extraction quality is GOOD even on cheap models. **flash-3.5 ≈ pro** (same pivotal moments,
causal chains, obs count 165≥144); **flash-lite correct but THIN** (drops secondary lessons = recall cost).
And the obs CORRECTLY say passivity hurt the SK while the synthesized SP prescribes blending → **extraction
is right, synthesis inverts it (halo-keyed)** — confirming the binding lever is synthesis (a)+(b), NOT
extraction. Net: for a cheaper loop use **flash-3.5** (≈pro, not anchored-lite); put real spend on the
synthesis fix.

**AMPLIFY arm + metric-reliability correction (2026-06-19).** Added a v6-cell `--amplify` mode (exhaustive
deep single-slice pass — the namespace-amplification idea ported to the cell path) and ran flash-lite
amplify on 3 games. **NULL:** total obs DROPPED (116<123), no pivotal-turn gain (still 3/12 by the
metric); the "be exhaustive" instruction doesn't transfer to flash-lite (quality-bar conservatism wins).
⭐**But the manual read overturned the capture METRIC:** on the heavily-flagged SK night cell, flash-lite
(base AND amplify) capture the same night-kill sequence as pro (3 obs each) while the metric scored it 25%
— the metric only counts obs stating a parseable alive-count, which pro's verbose situations do and
flash-lite's terse ones don't → the 10× "gap" is largely a verbosity artifact. **Revised:** flash-lite
already covers the critical pivotal turns ~comparably to pro (mildly thinner in places); neither anchor nor
amplify is needed; trust the READ over the parse-metric. Binding lever stays **synthesis (a)+(b)**.

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

## 8b. LOOP INFRASTRUCTURE — BUILT (2026-06-19, `evaluation/src/loop/`)
The compounding loop, wired + toggleable (config-flag policy). Components:
- **c (extract):** the existing `run_batch --memory-store-dir X` already does seed-from-X → play → extract
  → dump-back-to-X. Reused as-is; model env-pinned to flash-lite.
- **a (`credit.py`):** `credit_apply` recomputes the de-luck ledger over a rolling window (the dumps glob)
  and SETS pos/neg/neu/follow on matching SPs + persists `base_rates.json`; `sp_lift` recovers the
  BASELINED lift (raw counts carry the halo). **Credits all 3 channels** — vote + night + **d's free
  discussion floor** (day-vote endpoint, `_discussion_ledger`) so the discussion channel isn't invisible
  to consolidation. Tested offline: lift gradients match the ledger (SK vote blend −0.30…+0.26; SK
  discussion passive −0.45…active +0.32).
- **b (`consolidate.py`):** `prune_and_evict` (LLM-free: drop lift<τ&follow≥N + rejected
  retrieved≥R&follow==0, never positive) + `synthesize` (incremental, credit-aware CREDIT_SYNTH_PROMPT,
  flash-lite, concurrent; existing SPs persist so credit accumulates). Prune tested offline (drops the 8
  b1 SPs incl the −0.30 loser).
- **driver (`driver.py`):** `run_loop` per generation = run_batch (c) → credit (a) → consolidate (b) →
  `generation_score`; run-specific store (canonical frozen), warm/cold start, rolling window.
- **measure (`measure.py`):** `generation_score` = mean de-luck decision value, memory ON vs OFF × faction
  (ON should slope up vs flat OFF; outcome-independent). Tested offline.
- **Models:** flash-lite for extract + synth (validated ≈ pro, ~3× faster → cost dissolved); toggle → pro.
- **NEXT:** the one-rotation gate (1 gen, warm-start v6_1, small N — the first loop spend, the
  mechanism/safety check) → then the multi-generation slope run (the headline paid test). LLM discussion
  tagger (framing/credibility) = deferred paid refinement, separate from d's wired free floor.

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
