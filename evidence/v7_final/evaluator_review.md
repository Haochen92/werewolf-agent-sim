## v7 Pre-Rerun Evaluator Review — verdicts, ranked gaps, and the rerun plan

**Date:** 2026-07-02 · **Charge:** the external-evaluator pass specced in `EVALUATOR_BRIEF.md` §0 —
design / evidence / apparatus verdicts, ranked gaps, alternatives, and a plan, before any third paid
loop run. **Read-only pass:** no code changed; fixes below are recommendations.

**Evidence base:** EVALUATOR_BRIEF, report.md, plan.md, consolidation_design.md,
discussion_credit_design.md, `memory_system/store_progression.md` read in full;
`experiment_log.md` (§11j/§12) and `memory_system/effectiveness/paired_ab/` verified against the
record; `evaluation/src/loop/` code verified against the design docs (file:line cites below).

---

## Verdict summary (the five axes)


| Axis                 | Verdict                                                                                                                                                                                                                                                           |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Design soundness     | **Sound core** — de-luck credit, paired same-epoch OFF arm, recompute-not-accumulate window, no-merge SPs are all well-reasoned and code-verified halo-free on the vote/night path. Three weaknesses: slope power (F2), lift selection-bias (F5), SP bloat (F4). |
| Evidence credibility | Retractions honest and complete;**but the headline "+17pp p=0.013" is a fusion error** (raw +17pp p=0.267; the p=0.013 belongs to reranked +33pp) — fix before any portfolio use (F7).                                                                           |
| Apparatus validity   | Deterministic core trustworthy;**one live halo path remains: discussion credit via tagger valence at base 0** + an arm-blind tag cache (F1). Several silent-N fallbacks on the credit path (F6).                                                                  |
| Gaps                 | Ranked F1–F7 below; the top three are cheap/offline.                                                                                                                                                                                                             |
| Alternatives         | Keep the architecture;**change the measurement design**: endpoint store-transplant A/B + accumulate-only ablation arm; demote in-loop slope to diagnostic (F3).                                                                                                   |

---

## Findings in detail

### F1 (critical) — the retracted discussion-halo mechanism is still live in the loop's credit path

The §12f retraction ("+0.556 discussion lift was a halo — a level never differenced against
no-memory") fixed the *analysis* (`v2_salvage.py` used the deterministic day-vote floor). But the
loop code still does the retracted thing: tagger verdicts feed credit as **valence** with base rate
pinned to 0 (`evaluation/src/loop/credit.py:106,127` — "treated as already de-lucked → base 0").
On a rerun, every discussion-SP's lift = raw level, and that feeds **synthesis track records and
prune decisions**. Compounding risks amplifying it (plan.md §10d's vicious-spiral warning).

Two contributing defects:

- `tag_game_cached` keys by `(game_id, version)` only, not arm (`discussion_tagger.py:277`) — the
  exact cache-collision class that corrupted the first §12f re-score. Latent today (OFF arm never
  tagged) but armed the moment anyone tags the OFF arm to build a base rate.
- Design said "structure, never valence" (`discussion_credit_design.md` §7); the implementation
  feeds the holistic verdict. The §12g validation (blinded partial-r +0.56 wolf / +0.60 SK)
  validates the verdict as a *deceiver-skill metric*, not as a *differenced credit signal* — and
  town partial-r ≈ +0.02, so for a town-only rerun the tagger contributes ~pure noise-at-a-level.

**Fix options (pick one before rerun):**

- **(a) Recommended for a town-only rerun:** route discussion credit through the deterministic
  day-vote-endpoint floor (already built + used by `v2_salvage.py`) and drop tagger valence from
  credit; keep the tagger as a deceiver diagnostic. Cheapest, and town's discussion signal is the
  vote anyway.
- (b) If tagger credit is kept: arm-qualify the tag-cache key, tag the OFF-arm window too, and
  compute per-cell tagger base rates from it (real lift, not level).

### F2 (high) — the slope criterion is underpowered by construction at 6 gens

Run-1 per-gen ON−OFF noise sd ≈ 0.156. OLS slope SE = sd/√Σ(x−x̄)²: ≈0.049 at 5 usable gens (the
observed wolf slope +0.086 is ~1.7σ) vs ≈0.012 at the full 13 gens. **Gen count enters slope power
quadratically; games/gen only linearly.** Stopping at gen-6 made any slope unreadable regardless of
arm validity. Additional structure problems: gen scores are autocorrelated through the shared store
(OLS p-values anti-conservative), and the OFF arm alone drifted 0.119→0.389 within run-1 (§11g
"dominant noise source") — the differenced series is the only readable one.

### F3 (high) — answer compounding at the endpoint, not on the trajectory

**Recommended design change (the main alternative):**

1. Run the loop (town-only, arm-guarded) primarily to *evolve the store*, not to measure.
2. **Endpoint store-transplant A/B (new confirmatory test):** freeze the evolved store; run a
   static paired A/B — evolved store vs control store — same epoch, ~30 paired boards, scored on
   the validated proxy basket (the project's most trusted instrument, |r|≈0.6, machinery that
   already exists). This converts "does it compound?" into the exact shape the apparatus is proven
   to answer, and is immune to mid-run drift (both arms same epoch at test time).
3. **Control store = accumulate-only ablation, reconstructable offline for ~$0:** replay the loop's
   per-gen dumps through merge+dedup only (skip credit/synthesis/prune) to build the "same games,
   no consolidation" store. Evolved-vs-accumulated isolates the *loop's value-add* (credit-driven
   consolidation) from mere data volume — without it, an evolved-store win is confounded with
   "more games of mining." (Cold-store vs memory-off is already answered by the standing static A/B.)
4. The in-loop slope demotes to a **diagnostic** (still recorded/plotted, never confirmatory).

This dissolves most of F2 (the slope no longer carries the verdict), halves the pressure to run 13
gens, and reuses validated machinery end to end.

### F4 (high) — SP bloat is a mechanical anti-compounding force inside the ON arm

v2 grew 0→227 SPs ~linearly (follow_p50 ~5); run-1 hit 318–537 with follow_p50→1. Retrieval slots
are fixed, so unproven SPs displace proven ones — the loop's own output degrades the treatment
being measured. Contributing inert mechanisms (all confirmed in code):

- **Dead-weight evictor can never fire:** `merge_new_obs` folds observations only
  (`merge.py:24,72-76`); per-game SP adoption counters are discarded with the dumps
  (`driver.py:263-264`); synth SPs are born at `retrieved_count=0` and stay there → the
  `retrieved≥8` predicate is unreachable (`consolidate.py:32-42,69`; `credit.py:145-150`).
- **New-clusters-only gate is live code but ineffective at v2 cadence** (k=1 × 4 games spread over
  17 cells → nearly every cell gets new obs every gen; `cells_synthed` = 17,16,17,15,11,15).
- **No revise op exists** — synthesis appends only (`consolidate.py:187-198`); the design's
  "salvageable → revise" band (consolidation_design §4/§5) is unimplemented, so mediocre SPs
  neither improve nor leave.

**Fix (pick the cheap subset):** report.md §8's own proven-tier proposal — proven working set owns
the primary retrieval budget, unproven reserve retrieved rarely; the dead-weight evictor becomes
demote-to-reserve. Retrieval-side, offline-testable. Minimum viable alternative: merge adoption
counters back (or recompute from eval cases alongside credit) + raise `synth_min_new_obs`/`k`.

### F5 (medium-high) — residual selection confound in lift

Lift = SP's followed-decision mean − **cell-wide** OFF base rate. Follows are a selected subset
(retrieval match + agent applicability); if an SP fires in harder/easier-than-cell-average spots,
lift is biased even with a valid OFF arm. Held-out reproduction (r=+0.54) proves *stability*, not
*unbiasedness* — a situation-selection bias reproduces across halves. **Offline, zero-spend fix:**
stratify base rates by the already-persisted structured dims (`is_swing`, `dist_parity`,
`alive_bucket`); re-run held-out reproduction + the b1 drop-set sensitivity grid under stratified
baselines. If the drop set is stable, current thresholds stand; if not, this just saved a rerun
from mis-pruning.

### F6 (medium) — silent-N / fail-open paths still on the credit path

- Per-cell base-rate fallback to **0** when a cell has no OFF data (`credit_backfill.py:218`) =
  silent halo for that cell; `assert_base_rates` only checks map non-emptiness.
- Credit iterators silently `continue` on unresolvable `eval_cases_path`
  (`credit_backfill.py:153,180`; `credit.py:39,82`) — the strict invariant is a parallel pass, not
  a replacement.
- Tagger failure returns empty tags (`discussion_tagger.py:251-253`).
- `off_baseline=False` silently falls back to ON-derived (haloed) base rates (`credit.py:120`).
- No invariant asserts ON and OFF actually played identical boards (pairing relies on `run_batch`
  determinism from a shared `game_id`).

**Fix:** per-cell base-rate coverage assert (exclude uncovered cells from credit rather than halo
them); hard-fail `off_baseline=False` in experiment mode; a board-equality assert (role-draw hash
per pair); skipped-row counters in every credit function.

### F7 (medium, $0) — claim hygiene before portfolio use

- Fix the **"+17pp, p=0.013" fusion** in `v7_final/report.md` (§5a + the one-line claim set) and
  `memory_system/store_progression.md` (§8 + summary table + provenance note). The paired-A/B
  record says: raw town +17pp **p=0.267**; reranked +33pp **p=0.013**; rerank-vs-raw Wilcoxon
  **null**; ~7/24 proxy tests p<0.05, none Bonferroni-surviving — the load-bearing evidence is
  cross-arm town consistency + the proxy basket, and the honest headline is "+17–33pp across arms,
  win-rate significant only in the reranked arm."
- Reconcile the pairing contradiction (§11g "2–4× variance cut" vs §12b "pairing maxed,
  within-pair correlation ~0 at gen level") — §12b is the better-evidenced reading.

### F8 (context, no action) — things checked and found sound

- Vote/night credit chain is clean: no win/loss or `net_verdict` anywhere in credit, synthesis
  inputs, prune, or `measure.py` (code-verified). Prune thresholds, proven-SP exemption, SP
  no-merge, obs decay all match the design doc.
- The guard layer that exists is good: arm-factions + arm-declared (fail-closed pre-spend),
  within-run fingerprint consistency, dead-credit / discussion-credit-engaged /
  base-rates-nonempty / score-nonzero asserts, cost pinning on the driver's own process.
- Epoch drift is handled correctly *within* a run by the concurrent OFF arm (the differenced series
  is drift-robust in expectation); cross-run comparison remains forbidden — quantified drift is
  ≈2.5× run-to-run noise with a faction-ranking inversion overnight (`paired_ab/experiment_log.md`).
- The wolf "tentative-positive": defensible as *direction-only* at 4 games/gen (~1.7σ); the
  validated deceiver instrument (tagger partial-r) makes a future wolf-only run measurable, but it
  is not required to answer the pre-registered town question.

---

## The plan

### Phase 0 — zero-spend, before anything else

1. **Claim-hygiene edits (F7):** correct the p-value fusion in `v7_final/report.md` +
   `store_progression.md`; one line reconciling §11g/§12b pairing claims.
2. **Stratified-baseline sensitivity study (F5):** offline recompute of lift / held-out
   reproduction / b1 drop set with dim-stratified base rates on the existing v6ab + v2 ledgers.
3. **Accumulate-only store reconstruction (F3.3):** replay v2 per-gen dumps through merge+dedup
   only → verify the ablation-control store is buildable offline as designed.

### Phase 1 — small code changes gating the rerun (dependency order)

1. **F1 fix:** discussion credit → deterministic day-vote floor (drop tagger valence from credit);
   arm-qualify the tag-cache key regardless.
2. **F6 guards:** per-cell base-rate coverage assert; hard-fail `off_baseline=False`;
   board-equality assert; skipped-row counters.
3. **F4 — proven-tier/reserve retrieval split, now GATING (upgraded from optional during the
   discussion round — see "Further clarifications" §3 and the birth-to-maturity argument):**
   adoption-counter merge-back (or recompute-from-eval-cases) + the tier split per the spec in
   Further-clarifications §3 (graduate on follows + non-negative shrunk lift; demote-to-reserve
   replaces delete for the dead-weight evictor; fixed 1-of-k exploration slot). Raise
   `synth_min_new_obs`/`synth_every_k` as the cheap companion throttle.
4. **Proxy-coverage joins (from the round-2 discussion — cheap, deterministic, high value):**
   (a) healer block-a-kill credit (attack join in `_night_credit` — the second-strongest validated
   channel, r=+0.42 G2, currently un-credited); (b) `role_claims` structured persist +
   find→lynch transmission join (discussion_credit_design §4–5 — unlocks the investigator's real
   channel). Both reuse validated signals; no new proxy invention.
5. Tests for each (the loop is already the best-tested layer; keep it that way).

### Phase 2 — pre-register, then run (~$35–55 total)

1. **Pre-register the analysis** (a v2_salvage-style script written *before* the run): primary
   endpoint = endpoint transplant A/B on the validated town proxy basket (evolved vs
   accumulate-only, paired boards, same epoch); secondary = per-gen ON−OFF diagnostic slope;
   stopping rule re-stated; `--expect-factions town_only` in the command line of record.
2. **Run the loop:** town-only, paired ON/OFF, 8–10 gens × 4 games/arm (~$20–30). The OFF arm
   doubles as the epoch canary (record its level per gen).
3. **Endpoint transplant A/B:** ~30 paired boards, evolved vs accumulate-only store (~$15–20).
4. Analysis runs the pre-registered script only; everything else is labeled exploratory.

### Phase 3 — decision tree (pre-committed)

- **Transplant A/B positive on the basket** → compounding demonstrated at endpoint; freeze, write
  up, ship (frontend / memory-inspector per the roadmap).
- **Null/negative with the loop mechanically healthy** → honest answer: consolidation does not beat
  accumulation at this scale; freeze with the negative, Claim 2 (visible learning) carries the
  demo. Do **not** escalate N (per the original stopping rule).
- **Content-ceiling signature (evolved ≈ accumulated ≈ cold on the basket)** → the wall is
  extraction/substrate, not consolidation. The queued localization experiment already exists:
  `extraction_coverage_ab_spec.md` — the recall test (capture rate of leverage-flagged do-or-die
  turns) + the **model-capability arm** (a stronger extraction model is the cheapest real
  extraction improvement, since the loop re-mines every game). Extraction improvement is
  *contingent on this branch* — do NOT change the extractor before the rerun (it would confound
  the one-variable contrast; extraction quality is shared by both transplant arms and therefore
  differenced out of the confirmatory test).
- **Wolf follow-up (optional, later):** only if the town answer lands and budget allows — a
  wolf-only arm measured on the tagger instrument; the one direction with a positive prior.

### Verification

- Phase 0/1 items are offline: existing ledgers + unit/invariant tests (`poetry run pytest`), no
  game spend.
- Phase 2's own guards verify the run (arm guard at gen-1 ≈ $0.50 blast radius; fingerprint
  asserts; the new board-equality assert).

---

## Explicit answers to EVALUATOR_BRIEF §6 questions not covered above

- **Is (role×phase) cell granularity right?** Yes for storage/retrieval; too coarse as the *lift
  baseline* stratum — hence F5 (stratify the baseline by dims, keep cells as-is).
- **Does Claim 1 bear on compounding?** No — orthogonal (it anchors "memory helps"; the transplant
  ablation is what isolates compounding). It does calibrate instrument sensitivity: the proxy
  basket detected effects at N=30 that win-rate could not.
- **Which conclusions rest on LLM judges?** After F1, none on the credit path (vote/night credit
  deterministic; discussion via the deterministic floor). The tagger remains a validated *deceiver
  diagnostic*. Adherence/retrieval judges are diagnostics only (code-verified: not imported by any
  loop credit path) — their calibration debt does not block the rerun.
- **Does unjudged consolidation quality threaten the compounding claim?** Under the endpoint
  design, no — the transplant A/B measures consolidation's net effect directly, which is stronger
  than judging synthesis quality per-item.
- **Are "SPs never merge / coarse grading / offense-defense-as-diagnostic" consistent with the
  compounding thesis?** Yes, mutually consistent at current density (median ~3 follows/SP) — but
  they push all content-improvement onto append-and-prune, which is why F4 (bloat control /
  tiering) is load-bearing rather than cosmetic.

## Further Clarifications:


## 1) Why would an OFF-arm tagger baseline ever be needed?

It's conditional on *which fix you pick* for F1, and on *which faction* you're running.

The core rule your own credit design enforces: credit must be a **lift** — (outcome when following the SP) minus (what memoryless play scores in the same cell). For votes and night actions you get that second term from `compute_base_rates` over the OFF arm. But tagger verdicts currently enter credit at base 0 (`credit.py:106,127`), i.e. as a raw *level*. Positive tagger verdicts happen with or without memory — that's precisely the §12f halo — so a discussion SP racks up "positive" credit even if it adds nothing over no-memory play, then survives prune and gets a flattering track record in synthesis. To turn that level into a lift you need the *memory-off base rate of tagger verdicts per cell* — which means running the tagger over the OFF-arm games too. That's all "building the OFF-arm tagger baseline" means. The OFF games already exist (you need them for vote/night base rates anyway); the extra cost is tagging them (flash-lite, cheap) plus fixing the arm-blind cache key first, or the OFF arm silently gets served the ON arm's tags — the exact §12f collision.

Whether you need it:

* **Town-only run: no.** Town's tagger verdict adds \~nothing beyond the vote proxy (§12g partial-r ≈ +0.02). Drop tagger valence from credit, score discussion SPs by the deterministic day-vote-endpoint floor (already differenced against the OFF arm, already built in `v2_salvage.py`). No OFF-arm tagging needed.
* **SK-only (or wolf-only) run: probably yes.** Deceiver discussion skill is the thing the vote proxy structurally can't see and the tagger demonstrably can (partial r +0.55–0.60, blinded, verbosity-controlled). SK's day discussion is existential (the day vote is its only death). If you leave discussion SPs in the abstain set they accumulate ungoverned (bloat, F4); if you credit them via the tagger, the base-0 halo is live — so you need the OFF-arm verdict base rate. For an SK-only arm this baseline is also clean: opponents are memoryless in both arms, so the OFF-arm tagger distribution is a valid counterfactual.

## 2) "Integral vs slope"

The compounding claim has two distinct versions:

* **Cumulative (the integral):** "after k generations, the credit→consolidate loop produced a better store than you'd have gotten without it." One endpoint number. The transplant A/B measures exactly this: evolved store vs accumulate-only store, head to head, at the end.
* **Trajectory (the slope):** "decision quality is *still rising* at generation k — run more generations and it keeps improving." This is what the in-loop per-gen slope tries to measure, and it's the only version that tells you about plateau vs continued growth, i.e. whether gen 20 would beat gen 10.

The transplant design deliberately gives up the second to nail the first. If consolidation did all its good in generations 1–2 and flatlined after, the endpoint test still reads "positive" and can't tell you that shape. That's the real trade. My argument for accepting it: at your measured noise floor (per-gen ON−OFF sd ≈ 0.156), the slope was never going to be readable at any N you'd pay for — you'd need \~13 gens to resolve a 0.03/gen slope, and even then autocorrelation through the shared store makes the p-value optimistic. So the choice isn't "integral vs slope," it's "integral vs nothing." And the portfolio claim — *a store that updates itself from outcomes beats a store that just accumulates* — is the integral. You keep the per-gen plot as a free descriptive diagnostic for shape hints.

## 3) The proven-tier / reserve split, in full

The problem it attacks: at v2's endpoint you had 227 SPs competing for \~3 retrieval slots per decision. Follows spread thin (follow\_p50 \~5; run-1 p50 → 1), so almost nothing reaches the maturity gate (N≥8), so prune/keep decisions starve for evidence, while unproven ballast displaces the handful of SPs with proven track records. It's a vicious cycle: bloat → diluted follows → nothing matures → nothing can be pruned or promoted → more bloat.

The mechanism (retrieval-side only, store untouched):

* **Proven working set** per cell: SPs with, say, ≥2–3 follows and non-negative shrunk lift. They own most of the retrieval budget (e.g. 2 of top-3 slots).
* **Unproven reserve**: freshly synthesized and low-follow SPs. They get one exploration slot (round-robin or recency-weighted) — enough to *earn* follows and graduate, not enough to crowd out the playbook.
* **Graduation/relegation** run at consolidation time from the credit ledger you already compute: graduate on follows + positive lift; relegate on souring or dead-weight (the inert evictor gets a real job — demote-to-reserve instead of delete, so nothing unproven is destroyed).

What it buys, mapped to your findings: it caps the anti-compounding force (F4) without deleting potential; it *concentrates* follows so credit density rises and the maturity gates you already built start actually firing; and it's offline-testable — replay retrieval over frozen eval cases and check that proven SPs claim the slots. Risks to tune: exploration slot too small and new SPs never earn follows (store fossilizes); too generous and you're back to noise. Start with a fixed 1-of-k reserve slot. Bonus: "the proven playbook with per-SP track records" is exactly the artifact a memory-inspector demo wants to show.

## On your v6 observation — you're right, and it sharpens the point

For **v6** you're correct and I overstated: demotion didn't fail, it *didn't exist* — the count fields were never populated (`--no-memory-dump`, layer-4 "open circuit" per plan.md §1b). Bad SPs persisted because nothing could touch them.

Your second observation — the LLM drawing wrong conclusions from early-game noise, and those bad strategies being reused despite losing games — is exactly the failure mode v7's machinery was built for, and it's worth checking each piece against it: the **rolling-window recompute** ages out early verdicts; **shrinkage + the maturity gate** stop a 2-follow fluke from being trusted; **prune-by-lift** (held-out validated: flagged losers stay negative 89%) removes the mature bad ones; and **credit-aware synthesis** conditions rewrites on the realized track record instead of the extraction-time hindsight verdict. The residual gap — and this is where your eyeballed observation still bites in v7 — is the *window between birth and maturity*: a wrong early conclusion gets followed and does damage for up to \~8 follows before prune is allowed to convict it. That window is inherent to evidence-based demotion; the tiering split is the mitigation, because an unproven SP only ever holds the one exploration slot while it's still on trial. That's the strongest argument for treating F4's full version as gating rather than optional.

## Further clarifications — round 2 (proxies, extraction, project value)

### 4) Proxy validity — the honest tier list (assessment, informs but doesn't block the rerun)

- **Town basket (threat-hit vote, correct-elimination, mislynch, healer-save): genuinely validated,
  the trustworthy core.** |r|≈0.55–0.65 held pooled, OFF-only, and at N=180 reconfirmation; the
  coupling is *mechanical* (town wins by lynching threats) → likely epoch-robust. Caveats: the
  per-decision grain that credit consumes is weaker than the game-grain headline (G2: r=+0.33 vs
  +0.56), and it sees discussion only through the vote endpoint (fine for town per §12g).
- **Wolf blend (r≈+0.20): directionally validated, weak, and Goodhart-able.** A compounding effect
  measured through an r=0.2 surrogate attenuates badly, and "vote with the plurality" is trivially
  satisfiable by herding — it credits blending, not influence. The tagger (partial r +0.56/+0.60,
  blinded, verbosity-controlled) supersedes it for any deceiver *measurement*; remember its bounds
  (N=24, single-epoch, uncalibrated LLM).
- **SK day credit ("any non-self lynch = positive"): the weakest link, structurally.** It is
  survival-of-the-day credit, near-constant, mostly cancelled by base-rate differencing, and
  adjacent to the passive-SK tautology (A2). SK's separable channel is night kill-lands (r=+0.26).
- **Channels credited despite null separability** (investigator-night find r=0.00; wolf-night
  targeting r=−0.11): the recorded keep-all-channels decision is defensible (nulls diagnosed as
  prompt caps; shrinkage + maturity gates bound damage) but these follows dilute credit density —
  the scarce resource per F4. **Healer is the mirror image:** its best channel (block-a-kill,
  r=+0.42) is validated but un-credited — hence the Phase-1 item 4a join.
- **Cross-cutting:** all proxy validations are epoch-provisional; mechanics-coupled proxies should
  transfer, behavioral surrogates (blend) should be re-checked on the rerun's own OFF arm (free —
  the data is already recorded).

**Verdict on "can the proxies be improved":** near the ceiling on *inventing* proxies (beyond the
deterministic shadows lies the counterfactual-replay cost cliff, §6 tier-3); not at the ceiling on
*exploiting* them. The four exploitation moves, in value order: (1) healer attack-join credit,
(2) role_claims persist + transmission join, (3) tagger calibration via a small human-golden set
(raises the deceiver-instrument trust ceiling more than any new surrogate), (4) statistics —
dim-stratified baselines (F5) + regression-adjusting decision scores on persisted board dims
(free variance reduction). (1)+(2) are Phase-1 item 4; (3) is optional, pre-wolf-arm; (4) is
Phase 0 item 2 plus the pre-registered analysis.

### 5) Is postgame extraction the cap? (sequencing decision)

The ceiling concern is mostly *upstream* of the extractor (extraction faithfully mines whatever the
play contains; mediocre play → faithful lessons about mediocre play). The extractor's one
undiagnosed weakness is **recall** — dangerous for the loop because omission is unrecoverable
(C-v) — and recall is unmeasurable today except via the already-specced leverage-flagged
capture-rate screen. **Decision: do NOT improve extraction before the rerun.** (i) Extraction
quality is shared by both transplant arms → differenced out of the confirmatory contrast; (ii)
changing it mid-flight breaks one-variable-at-a-time; (iii) the contingent response is already
specced (`extraction_coverage_ab_spec.md`, recall test + model-capability arm) and now sits as an
explicit Phase-3 branch (content-ceiling signature).

### 6) On "inconclusive = huge value loss" — the framing to keep

"Does memory help?" is **already answered** (Claim 1, paired A/B, standing) — the rerun cannot
un-answer it. The open question is strictly narrower: does the self-updating loop beat
accumulation? For that, a **conclusive negative is a finding** (plan.md §8 pre-committed to this);
the genuinely catastrophic outcome is a **third invalid/unreadable run** — and every gating fix
(F1, F6, pre-registration) plus the endpoint design exists to prevent exactly that: a paired
endpoint contrast on the validated basket cannot come back "too noisy to call" the way a 6-gen
slope can. The banked portfolio value — memory demonstrably helps + the system demonstrably
learns + an instrument rigorous enough to catch its own invalid runs — does not depend on the
compounding verdict.
