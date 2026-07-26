# Credit blind-spot fix pair — validation before any rerun (2026-07-21)

**Status: CLOSED 2026-07-21 (see §⑥).** Steps 1–2 complete (instrument-grain validation + on-epoch
screen recovery + the ④c/④d/④e forensics); the live gate/step-3 was considered, arms agreed, then
DECLINED by the owner — the program closes on the precise concession in §⑥ (no certified
current-epoch live benefit; epoch-stamped positives and all mechanism findings stand).

## ① Motivation

The v7 endpoint (`batch_results/v7_endpoint_ab`, 2026-07-20; pre-registered primary −0.147 paired,
19/30 boards memory-hurt) traced the harm to a caution/concealment SP family the credit instrument is
STRUCTURALLY blind to, verified against the store and the code:

1. **Abstain scores neutral** (`_vote_credit`: `is_abstain → "neutral"`) — the flagship abstain SP sat
   at follow=19, 15 neutral → utility 0.00, unprunable at any generation count, while abstaining's harm
   (the forgone threat-lynch) is opportunity cost a per-decision realized-outcome proxy never sees.
   95% of ON-arm town abstains (111/117) fell on days that ended in NO LYNCH — the deadlock itself.
2. **Concealment has no creditable endpoint** — "Maintain silence regarding high-value investigation
   results" was retrieved 179× with follow_count=0: a concealment SP is never "followed" as a discrete
   act, so the follow-joined ledger cannot touch it, and scope-aware evict spared it
   (not_relevant-dominant in the loop window). Meanwhile the endpoint's conversion chain collapsed:
   investigator find→lynch 47.5%→26.7%, finds lynched 13→4, wolf wins 4→9.

The fixes (both config-flagged, default = frozen legacy):

- **Fix 1 — `LoopConfig.abstain_credit="deadlock_negative"`**: a town abstain on a day that resolved
  to no-lynch scores negative; any landed lynch (threat or townmate) keeps it neutral (abstaining from
  a mislynch is the defensible 2% case). Ledger-only: `measure.py` calls the shared grading without
  the keyword, so the pre-registered measurement proxy is frozen by construction
  (`tests/test_credit_blindspot_fix.py::test_measure_is_pinned_to_the_legacy_rule`).
- **Fix 2 — `LoopConfig.conversion_credit=True`** (`evaluation/src/loop/conversion_credit.py`): a
  deterministic find→lynch conversion endpoint. Attribution is RETRIEVAL-based (not follow-based) on
  purpose — that is the only way to reach follow=0 concealment SPs — so the tally is baselined against
  the OFF arm's conversion rate through the same construct and shrunk before it can prune.

## ② Validation design (steps, cheapest first)

- **Step 1 ($0)** — `evaluation/experiments/credit_blindspot_validation.py`: re-score the two runs we
  already own under {legacy, fixed} rules × {loop_run `v7_compound_town5`, endpoint} corpora, then
  simulate prune/evict. Labels = the 07-20 forensics flagships (3 harmful, 3 good), resolved by
  action-text prefix. The loop-run corpus exists to blunt circularity (the fixes were designed on the
  endpoint); real generalization still needs step 3.
- **Step 2 (~$1–2)** — the existing `eval-checkpoint-replay` screen (SP-only injection added as
  `--retrieval-types`, matching the v7 read path), 4 arms × 100 held-out v6ab town cases:
  {empty, full 168-SP store, legacy-pruned 152, fixed-pruned 142}. The legacy-pruned arm isolates the
  MARGINAL effect of the fixes over plain endpoint-window re-crediting. Pre-registered prediction:
  fixed-pruned's day-vote abstain rate falls toward OFF's ~23% and threat-hit rises toward ~50%
  relative to full_store; empty is the no-memory anchor.

## ③ Step-1 results (2026-07-21, artifacts: `step1_validation.{json,md}`)

**Fix 1 validates cleanly on both corpora.**

- *Sensitivity*: the abstain flagship goes lift 0.00→**−0.62** (loop) and −0.11→**−0.83** (endpoint)
  and is pruned under the fixed config in both.
- *Specificity*: all three good flagships stay protected, and their lifts IMPROVE under the new rule
  (e.g. healer "maintain active engagement" −0.06→+0.17 on the endpoint corpus): pricing abstains
  negative lowers the cell base, so genuine engagement stands out more.
- *False-penalty*: of 117 endpoint / 165 loop-run town abstains, the rule penalizes only the no-lynch
  deadlock bucket (111 / 160) and spares the defensible mislynch-day abstains (2 / 1).

**Fix 2 is a valid channel but a weak per-SP convictor at this data size.**

- The construct sees the arm-level collapse clearly: under the refined windowing (see below), endpoint
  ON resolves 20/23 finds with conversion mean **−0.30** vs OFF 26/31 at **+0.385**.
- Per-SP attribution of the investigator-silence flagship is thin: only 6 endpoint-window tallies
  (retrieval dilution — at 168 SPs it is no longer ubiquitously retrieved; its 179× was a ≤82-SP-store
  loop-window figure), converting ≈ at base → conv lift −0.03, not prune-triggering. It is still
  REMOVED on the endpoint corpus, but by scope-aware evict (endpoint-window adoption counters are
  override-dominant 3≥1, unlike the loop window's not_relevant-dominant 44>31). This echoes the 07-20
  finding: the harm is collective/interlocking and resists single-SP localization; the conversion
  channel's contribution is REACHABILITY (follow=0 is no longer untouchable) + the arm-level signal,
  not a hanging verdict on this one SP.
- **Known v1 scope gap (honest ❌, kept red in the table)**: the healer-silence flagship is untouchable
  by ALL current instruments — conversion v1 is investigator-only (a healer "conversion" analog has no
  obviously deterministic endpoint). Whack-a-mole instance #1; if the fixes ever graduate, this is the
  next axis selection pressure will find.
- Store-level: caution-family removals 9→19 of 89 (endpoint corpus); prune totals 16→26 of 168.

*Design iteration recorded mid-step-1*: the first windowing voided any find whose window the game
ended inside, which would have excluded early-deadlock games; refined to void only windows with ZERO
played days (days-played is outcome-independent). Empirically the refinement changed no endpoint
number (all voids there are night-deaths of the found target), but the rule is now right by
construction.

## ④ Step-2 results (2026-07-21, artifacts: `replay/checkpoint_replay_town_20260721_051155.*`)

**NULL — and diagnosably so: the screen is insensitive to this failure mode, not evidence the fixes
lack behavioral effect.** 100 held-out v6ab town cases × {empty, full_store 168, legacy_pruned 152,
fixed_pruned 142}, SP-only injection, one process/day/backend, case-major:

| arm | day-vote hit | day-vote abstain | night hit | overall mean value |
| --- | --- | --- | --- | --- |
| empty | 62% | 14% | 18% | +0.28 |
| full_store | 58% | 12% | 18% | +0.23 |
| legacy_pruned | 60% | 14% | 18% | +0.26 |
| fixed_pruned | 60% | 14% | 16% | +0.25 |

Paired McNemar fixed_pruned-vs-full_store: helped 7 / hurt 7, p=1.0 (the artifact's
"gen-final vs gen-1" header is the template's generic label for last-vs-first snapshot arm).

Why this is an instrument limit and not an exoneration of the full store:

1. **The treatment WAS administered** — an embedding-only exposure check found ≥1 caution-family SP
   in the injected top-3 on **35/50 day-vote cases** (mean 3.0 SPs injected). Yet abstain moved 12–14%
   across all arms, nowhere near the live ON arm's 31%.
2. **The endpoint's harm was trajectory-level, and frozen single decisions cannot express it.** The
   07-20 forensics located the damage in the interlock (concealment → impoverished discussion →
   room-wide abstain cascade → mislynch of power roles). A replayed case inherits v6ab's FROZEN
   discussion — which was generated without these SPs, so the impoverishment never happened, and the
   "information landscape entirely speculative" trigger condition mostly doesn't hold. The same
   lesson as the 2026-06-13 framing screen: off-policy vote screens cannot see harms that live in the
   discussion trajectory.
3. Even the full store's LIVE deficit (−15pp threat-hit) barely registers here (−4pp, n=50, within
   noise) — the screen fails to reproduce the harm itself, so it cannot detect the harm's removal.

*(The v6ab verdict above was superseded the same day by the corrected exam below — kept because the
diagnosis of WHY v6ab was insensitive is itself a finding.)*

## ④b Corrected step-2 (owner-directed, 2026-07-21): on-epoch exam + fixed-credit RESYNTHESIS

Owner caught two design errors in ④: (1) the exam should be the v7 games' own failure decisions,
not a previous epoch's — the endpoint games ARE held-out for this store (SP provenance = the 40 loop
games; 0/30 game-id overlap verified) while being on-epoch and enriched for the harm, with transcripts
where the caution SPs' trigger conditions genuinely hold; (2) prune-only understates the fix — the
loop's synthesis is credit-AWARE, so the counterfactual store is a full `consolidate()` tick under the
new counters, not 168−26.

**Resynthesis tick** (`resynth_store/`, seeded with the LOOP-window fix-credited SPs — what a real
fixed-credit gen-4 tick would have seen — + the 718-obs substrate): synth added 131 SPs across 5
cells (4 with track record: the −0.62-lift abstain row was in the prompt), 6 cells capped, SP-dedup
collapsed 299→143, prune → **142 SPs**. ⭐Notable: the resynth store still carries **83
caution-union SPs vs prune-only's 72** — even with explicit negative track records, synthesis
regenerates caution content. Fixed credit enables REMOVAL once follows accumulate; it does not stop
the generator PROPOSING caution. (Generative-prior half of the Goodhart story, now measured.)

**Sweep** (`replay_onepoch/`, 100 endpoint-ON town cases × 5 arms, SP-only):

| arm | overall mean value | day-vote hit | day-vote abstain | day-vote mislynch-vote | night hit |
| --- | --- | --- | --- | --- | --- |
| empty | +0.13 | 46% | 18% | 36% | 16% |
| full_store (168) | **+0.04** | **42%** | 12% | **46%** | 12% |
| legacy_pruned (152) | +0.12 | 46% | 14% | 40% | 18% |
| fixed_pruned (142) | **+0.14** | 46% | 16% | **38%** | 20% |
| fixed_resynth (142) | +0.10 | 44% | 14% | 42% | 18% |

Readings (screen-grade: direction + consistency, NOT significance — discordant-pair counts are 2–6,
McNemar p 0.5–1.0):

1. **The harm now reproduces**: full_store sits at the bottom of every readout (−0.09 mean value vs
   empty; mislynch-vote 46% vs 36%) — confirming ④'s null was the v6ab epoch mismatch, not an
   inherent replay limit at the single-decision grain.
2. **The fixes recover the full deficit at this grain**: fixed_pruned ≥ empty on every readout and
   never hurt a single paired day-vote vs full_store (helped 2 / hurt 0). Ordering matches the
   pre-registered direction everywhere: full < resynth ≤ legacy ≤ fixed_pruned.
3. **Decomposition of the live harm**: on these frozen deadlock contexts the direct-injection
   component expresses as MISLYNCH-VOTING (46→38% removable by pruning), while the abstain cascade
   barely expresses at all (12–18% here vs 31% live, and EMPTY abstains most) — the abstain half of
   the live harm is carried by the trajectory (impoverished discussion), the mislynch half
   substantially by injection. This sharpens ④'s claim rather than reversing it: the screen can see
   the injection component on-epoch; only live games can see the cascade component.
4. fixed_resynth lands between full and fixed_pruned, consistent with its higher caution load (83 vs
   72) — dedup re-absorbed synth output onto credited survivors, so the tick mostly re-litigated
   rather than improved the mix. A fixed-credit LOOP would prune these as follows accrue (their
   negative credit is now visible), but that is a multi-tick claim = step 3.

**Combined verdict (supersedes ④'s):** the fixed credit removes the harmful content (step 1), and the
removal recovers the store's full per-decision deficit on the actual failure boards (④b, directional,
n=50 day votes/arm). The remaining untested claim is the trajectory/cascade component and loop
convergence — live paired games, step 3, still unauthorized under the stopping rule.

## ④c Related forensics (2026-07-21): did the STATIC obs benefit ride the same caution lever?

Owner question after ④b: the June static-obs result (+17/+33pp) came from the same self-play
extraction — how did IT avoid the caution trap? $0 census on the original A/B dumps (`ab_arms_town`,
`ab_rr_town`, `ab_baseline`+`_recovered`; pooled OFF n=30; win rates reconcile 27→43/60%), same
vote-grain metrics as the endpoint forensics:

| arm | town day2+ hit | abstain | townmate-vote |
| --- | --- | --- | --- |
| OFF (n=384 votes) | 41% | 24% | 35% |
| raw obs (n=447) | **55%** (z=+4.0) | 22% (z=−0.8) | **23%** (z=−3.7) |
| reranked (n=433) | **53%** (z=+3.4) | 26% (z=+0.6) | **21%** (z=−4.4) |

**The obs benefit rode the INFERENCE lever, not the caution lever** — abstains flat, discrimination
sharply up: the mirror-opposite of the v7 SP signature (hit 50→35, abstain 23→31, townmate-vote
27→34). Also the structural reason obs escaped the Goodhart dynamic: descriptive content with no
adoption grip, certified by the game-level instrument, and — decisively — NO loop: selection
pressure can only concentrate harm into a blind spot when there is iteration under a partial
measure. A static store's failure mode is staleness, not self-amplification. (Bonus: this census is
the raw-arm proxy-basket anchor the static-memory correction called for — z≈4 at the vote grain
makes the static claim stronger than its NS win-rate arm suggested.) Epoch caveat unchanged: two
epoch-movers shipped since June (reads-bundle prompts, embedding -2), so live promotion still goes
through the mandatory freeze gate, whose readout should now include this lever census.

## ④d Obs-instead-of-SP + the two-channel self-correction question (2026-07-21)

**Owner question 1: would injecting the v7 run's own 718 observations (RAG) instead of SPs have done
better?** Substrate census first: the v7 obs are **34% caution-flavored vs 13% in the proven June
v5_0 store** (~3×) — plausibly self-referential contamination (extracted from games played UNDER SP
injection, so the store partly diaries the caution-shaped play). Sweep (`replay_obs/`, same 100
endpoint-ON cases, `observations_only`): **obs_v7 ≡ empty exactly (0.31 accuracy / +0.14 mean,
both)**. Answer at this grain: harmless but worthless — avoids the SP store's −0.09, delivers zero
lift. The caution flavor did NOT taint decisions (descriptive mood + agent discretion neutralize),
and the 427 positive-inference records did not help on these boards either.

**Owner question 2 (the bafflement): if caution is bad, why didn't (1) later-game obs or (2) SP
credit catch it?** Both checked against the store:

- The failures WERE recorded: 198/718 obs carry `net_verdict: negative` in dimensions (incl. literal
  "led to a stalled vote" records). Channel (1) was not blind — it was SEVERED (§6.8 retired obs
  from prompts; only route to behavior = obs→synthesis→SP) and then LAGGED: injection loop = 1 tick,
  correction loop ≥ 3 ticks (deploy → collective failure → failure obs → synthesis with negative
  track records, only available after gen-3 credit → counter-SP out-competes ~90 incumbents). The
  run had ~2 synthesis ticks.
- The immune response HAD begun: **9 anti-caution counter-SPs existed**, the strongest ("maintain
  active engagement rather than abstaining") at follow=21, +13/−6, proven-protected. Outnumbered
  ~10:1, ~2 ticks from relevance at run end.
- Channel (2)'s deeper failure: credit is DELIBERATELY de-lucked/outcome-independent (the anti-halo
  design) — and the deadlock harm lives entirely in the discarded channel (games lost through
  votes-not-cast, no single bad scored decision). The anti-halo choice and the blind spot are one
  design decision seen from two sides; fixes 1–2 re-admit narrow deterministic outcome slices
  without re-opening the halo.
- Under OLD credit the incumbents were neutral-sheltered → the race was rigged, more generations
  entrench. Under FIXED credit the incumbents bleed (−0.62/−0.83) while the counter-meme keeps
  +0.17 → the sharpest form of the step-3 question: **was the run shorter than the system's
  self-correction lag, rather than the system incapable of self-correction?**
- Unifying line: every instrument (extraction, credit, replay) records per-agent EVENTS; this
  failure was a collective NON-EVENT, perceivable only at the game-outcome grain both instruments
  were deliberately built to ignore.

**Third-architecture note (owner's "no credit for obs" hesitancy):** presence-lift credit for obs is
feasible — demonstrated on the June raw arm ($0): 67 obs reach n≥8 co-presences; head median +0.21;
a convictable harmful tail exists (6 below −0.15, worst −0.49 at n=15). Prune-only, head-grain,
same shape as the conversion channel. Candidate ship config: obs injection + presence-lift prune +
per-epoch aggregate gate (no self-amplification anywhere) — but ④d's null means the CURRENT v7 obs
store adds nothing on the failure boards; a clean-substrate re-mine would precede any obs promotion.

## ④e Is the new abstain credit MEASURING or ASSUMING? (owner validity challenge, 2026-07-21)

Challenge: is the abstain SP's −0.62/−0.83 "negative outcomes associated with the concealment/abstain
play," or just "abstain always scores negative" baked into the meter? Decomposition run:

- **Base-differencing removes the blanket price**: under the new rule the OFF base for the same cell
  drops ~0.2 (loop +0.20→+0.02, endpoint +0.14→−0.08) — ambient abstaining is priced into the
  baseline, so blanket-penalty alone would cancel to lift ≈ 0. The SP's follows sit 0.8–0.9 BELOW
  same-cell no-memory ambient.
- **Within-SP discrimination is real but rarely triggered**: of the SP's followed abstains, 26/27
  (endpoint) sat on no-lynch days; the 1 lynch-landed abstain was spared. Arm-wide 6/117 spared.
- ⭐**BUT day-conditioning exposes a real bundling**: OFF vigilantes ON no-lynch days score −0.82 —
  nearly the SP's −0.97. Day-conditioned lift ≈ −0.15 (endpoint) / ≈ 0 (loop). So ~−0.74 of the raw
  −0.89 lift is "deadlock days are bad for everyone," ~−0.15 is within-day excess.
- **Why day-conditioning OVER-controls**: the day outcome is the MEDIATOR of the claimed harm
  (SP → abstains → vote-mass collapse → no-lynch); conditioning on it cuts the causal path. The
  mediator is real, not pure selection: paired boards show the arm CAUSES excess deadlock (33% vs
  27% of day2+ days on identical boards; 13 boards vs 9). No per-decision deterministic grading can
  separate mediator from selector — counterfactual blindness in a new costume.
- **Exposure is bounded to the abstain ACT**: non-abstain advice firing on the same doomed days is
  target-scored (threat-hit stays positive on a deadlock day). The at-risk class = individually
  irrelevant abstains — whose act still has a known-sign marginal effect (removing vote mass only
  pushes toward no-lynch).
- ⭐**The pivotality refinement REOPENS the original blind spot**: "negative only if the abstainer
  could have completed a plurality" spares every abstainer in a mass-abstain deadlock (no individual
  is pivotal in a collective failure, by construction). The blunt contextual rule is the price of
  charging collective harm at all; it knowingly prunes {deadlock contributors} ∪ {deadlock
  parasites} under asymmetric loss (a parasite SP never helps, so wrongly pruning it is cheap).

Verdict: the instrument is a PRUNING SELECTOR under asymmetric loss, not an unbiased causal
estimator — adopted deliberately, with the marginal (~−0.15) vs context (~−0.74) split now on
record. Specificity held empirically (lynch-landed abstains spared; engagement SPs GAINED lift).

## ⑤ Limitations

- Steps 1–2 validate the INSTRUMENT and the store-level effect off-policy. They cannot show the loop
  CONVERGES to a good store under the new credit (the whack-a-mole question) — that is step 3, a fresh
  build run + endpoint, not authorized.
- Circularity: fixes designed on the endpoint data; the loop-run corpus is different games but the
  same epoch/store lineage. Treat step-1 passes as necessary, not sufficient.
- `conversion_min_n=5` / `conversion_window_days=2` are ruled defaults, not swept (knob-pinning policy,
  `evidence/store_curation/knobs.md`).
- The legacy-pruned replay arm re-credits on the ENDPOINT window — it is not identical to "what the
  live run's prune actually did" (loop-window credit), it is the fair same-window comparator for the
  marginal-effect question.

## ⑥ CLOSURE (owner decision, 2026-07-21): no gate run — concede no certified current-epoch benefit

Owner considered and DECLINED the combined freeze-gate A/B ({OFF, v7-obs, fixed_pruned SP} × 15
boards, ~$25; arms were agreed before the decision to stop). Ruling: close the memory-research
program here and concede the promotion claim rather than spend further.

**The concession, stated precisely:** under the runs performed, NO memory configuration demonstrates
a certified live benefit over baseline on the CURRENT epoch. (a) The static-obs result (+17/+33pp;
reranked p=0.013; vote-grain hit z≈+4.0, §④c) is real but EPOCH-STAMPED — June epoch, never
re-measured across the reads-bundle (2026-07-09) and embedding-2 shifts. (b) v7 procedural/
compounding: pre-registered negative-leaning (primary −0.147, p≈.06; decision-grain harm p<.001).
(c) The credit fixes: instrument-grain validated only; live effect untested (the ④b recovery is
screen-grade). Consequences: no store promotion · live ships memory-OFF · the roadmap's freeze gate
has nothing to certify (consistent) · every positive claim carries its epoch stamp.

**Not conceded:** the June result within its epoch; the mechanism findings (inference-vs-caution
lever, the blind-spot forensics, Goodhart selection under a partial measure, the self-correction-lag
hypothesis, the night-channel placebo); the fix pair's instrument-grain validation. These are the
research product and they are complete.

Project framing adopted with the closure (owner, same session): research project — "an exploration
of whether episodic and procedural memory can improve agent play under a limited number of games
(gemini flash-lite class models)" — with a DIFFERENTIATED verdict, not a null: episodic helped
(epoch-stamped, mechanism-verified), procedural harmed (mechanism diagnosed), self-correction was
structurally blocked (then fixed at instrument grain), and the remaining questions are precisely
costed and deliberately unspent. Frontend proceeds as the research-visibility layer (memory
inspector + replay viewer + playable game), not as a memory-wins product claim.
