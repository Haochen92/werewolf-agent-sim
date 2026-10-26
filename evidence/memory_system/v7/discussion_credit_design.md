# v7 (d-full) — discussion credit: design + brainstorm

**Date:** 2026-06-19 · **Status:** DESIGN/brainstorm, not built. Committed to d-full (the deterministic
free signals are too weak alone — see `consolidation_design.md` §8 / the d0 first-principles cut).
d-full's real job is the **deceiver concealment axis + the qualitative town residual**; town transmission
is mostly cheap/deterministic. No code; this is the reference when we build.

**Why d at all:** discussion SPs sit in (b)'s ABSTAIN set — un-creditable, so consolidation can't govern
them. d unblocks that. The genuinely-additive discussion value (concealment, transmission, the
delayed/causal cases the windowed-credit test couldn't reach) lives on the social axis only an LLM sees.

---

## 1. Role by role — what each wants in discussion, and the ways (the lens)

**Town**
- **Villager** (pure social): find threats from behavior · aggregate reads · build a correct-lynch
  consensus · avoid mislynch · catch deception. Ways: accuse · defend · question/demand-claim ·
  synthesize · propose vote · pile on · stay quiet · flag contradiction.
- **Investigator** (the transmission role): + **transmit a confirmed read so the village acts** · time
  the reveal (early=night-killed, late=wasted) · establish credibility vs a wolf fake-claim · survive
  while holding info. Ways: hard reveal · soft-signal · bank credibility · contest a counter-claimer ·
  time to a pivotal vote · blend/withhold (the cap the G1 de-cap targets).
- **Healer** (value = hidden & alive): + **stay hidden** · rare endgame claim · quietly vouch for known-town.
- **Vigilante** (can confirm the immune SK): + reveal a shot-confirm ("shot X, immune ⇒ SK") · weight
  accusations with the kill threat · avoid friendly-fire rep.

**Deceivers**
- **Wolf** (allies, parity): **conceal** (#1) · misdirect onto town · protect allies subtly · muddy
  consensus · recon power roles to night-kill · fake-claim · control bandwagons · bus an ally · manage heat.
- **Serial killer** (solo, night-immune, day-vote is its ONLY death): **survive the day-vote**
  (existential) · conceal · misdirect · play town-vs-wolves · manage heat under pressure · avoid the
  vigilante/investigator confirm-out.

## 2. Commonality — 7 primitives, 3 axes (SCAFFOLDING, not credit buckets)

| Primitive | Offense | Defense | Transmission |
|---|:--:|:--:|:--:|
| Accuse / advocate | ● | | |
| Frame / synthesize | ● | | |
| Lead / follow bandwagon | ● | | |
| Defend (self/ally) | | ● | |
| Blend / withhold | | ● | |
| Deflect under pressure | | ● | |
| Claim / reveal (true or fake) | ● | ● | ● |

- **Offense** = steer the room · **Defense** = manage heat · **Transmission** = private truth → public action.
- **Asymmetry:** town value ≈ transmission + correct offense (verifiable vs roles/votes); deceiver value
  ≈ concealment (heat — hard to ground). So **town discussion credit is tractable/cheap; the LLM tagger's
  real job is the deceiver concealment axis.**

## 3. ⭐ The granularity ladder — tag fine, credit coarse

The 7 primitives are the **tagger's detection vocabulary** (structure = observation; fine grain is fine).
But **credit must stay coarse** — crediting per-primitive splits thin follows into 7 buckets = the exact
per-dimension-SP density trap we cut.

| Grain | Role | Verdict |
|---|---|---|
| 7 primitives | tagger detection (a lens) | **compute/observe** here |
| ≤3 axes (offense/defense/transmission) | the **ceiling** for credit decomposition | max reward granularity |
| 1 transition outcome | did heat/consensus move the right way | **where credit likely lives** (density) |

This is the `score_tier_design` rule: compute every act as a lens (diagnostic), score one rep per
empirically-independent axis. **Tagger sees fine; credit stays coarse (per-axis ≤3, probably 1).**

## 4. What's deterministic vs what truly needs the LLM

| Signal | Source | LLM? |
|---|---|---|
| stance (accuse/defend/agree/neutral) + target + `seq` | `addressed_targets` | ❌ free |
| actual consensus (who voted whom) | `day_resolutions.vote_counts/votes` | ❌ free |
| lead vs follow (move precede the bandwagon?) | `seq` + vote timing | ❌ free (but Gate-A null) |
| role claims / reveals | `day_summary` `role_claims` — **computed then DISCARDED to free text** | ⚠ needs a small **gameplay-neutral structured PERSIST** first, then free |
| transmission outcome (find→lynch, shot→lynch) | player-ID join: claim × `day_resolutions` × roles | ❌ free (once claims persisted) |
| heat trajectory / tone | day_channel text | ✅ LLM |
| credibility (claim believed?) | room reaction | ✅ LLM |
| deception quality (honest defense vs cover) | text + roles | ✅ LLM |

⚠ **Correction (2026-06-19):** `role_claims` is NOT sitting in the data — `DaySummaryOutput` flattens to
free text before persist. So town-transmission credit = *small neutral persist build, then free join* —
real, small, not free.

## 5. Architecture — minimize LLM, no per-day live tagging

1. **Persist `role_claims`** off the existing per-day `day_summary` call — gameplay-NEUTRAL (no prompt
   change, agents see nothing new; just stop discarding the structured output). Unblocks transmission.
2. **Deterministic skeleton** — stance / votes / seq / transmission(find→lynch). Covers **town offense +
   transmission** with no LLM.
3. **One post-game flash-lite pass** for the residual (heat trajectory, credibility, deception) = the
   **deceiver concealment axis**. flash-lite (cheap; tagging structure is its wheelhouse) with an
   **ALL-REQUIRED schema** (flash-lite chokes on optional fields). **Structure, not valence** (per §10f —
   valence is circular; deterministic transitions supply valence). **Day-chunked within the pass** for
   attention on long transcripts.
4. **Credit = the coarse transition outcome, per-axis (≤3) at most**, ground-truth-conditioned
   (undeserved-heat-shed ≠ deserved-heat-escaped), aggregated over many instances.

### Why post-game, not after-each-day
- **Hindsight** (the main reason): post-game knows how each day *resolved* + whether a read was *later
  validated* — exactly what credit needs; per-day would have to guess it.
- **Freeze-safety**: a separate post-game pass doesn't touch the fed-to-agents `day_summary`; extending
  that per-day call to emit tags would (conditions Phase-B + the A/B).
- **No live need**: tags never feed back into play → per-day latency buys nothing.
- **Trajectory consistency**: one pass tags the whole heat arc coherently.
- The one pull toward per-day (attention on a long transcript) is handled by **day-chunking inside the
  post-game pass**. The per-day `day_summary` is still the right home for the *neutral `role_claims`
  persist* (step 1) — that part IS per-day, the *tagging* is post-game.

## 6. Counterfactual — out of scope, and coarse credit dissolves the need
True "did THIS message cause the shift" = remove it and **re-simulate the day** (a full generation per
message) — combinatorial, out (§6 tier-3). But **coarse credit makes it unnecessary**: crediting at the
act-type/per-axis level **over many instances** makes the observational aggregate the stand-in for the
*average* causal effect. The per-message counterfactual is only needed for *fine per-message* credit,
which the granularity ladder forbids. `seq` (lead-vs-follow) is the only per-instance causal hint, and
it's weak (Gate-A null) → lean on the aggregate.

## 7. Honest flaws / expect-coarse
- **Discussion is the noisiest channel** — `lead-vs-blend` already null (Gate A); `suspicion_drawn`
  outcome-proximate. Expect to fall to **per-axis/per-day** grain; per-turn may be below noise → a
  **documented limitation**, not a cue to build the counterfactual machine.
- **Deceiver concealment is hardest to ground** (shed-heat ↔ survived ↔ won tautology) → credit
  *undeserved*-heat-shed (role-conditioned) + lean on the de-haloed disagreement residual (§10f).
- **Halo**: the post-game tagger has hindsight → emit STRUCTURE, never valence.

## 8. Cost summary
- **Live change:** only the `role_claims` structured persist (gameplay-neutral, ~free).
- **New spend:** one post-game flash-lite pass per game (day-chunked, all-required schema). No per-day
  live LLM. Can share c2's prefix cache / ride the same post-game omniscient pass.
- **Gate B** (from the discussion-scoring plan) still governs go/no-go: does exposure-trajectory tagging
  actually *lead* `suspicion_drawn`? If null even at coarse grain → documented limitation, stop.

---

## AMENDMENTS (2026-06-19, round 2 — three corrections)

**A1. The LLM residual needs at most END-OF-DAY, not end-of-game.** Framing-DETECTION needs no hindsight
(read the message; per-turn capable) — the deterministic transition scores whether it *worked*.
Credibility ("believed?") needs the day's reactions/vote = end-of-day (full-game only adds "eventually
validated" = role-conditioned = deterministic anyway). So we are NOT dependent on post-game for the two
residuals (post-game stays convenient for multi-day deterministic joins + c2 cache sharing only).

**A2. ⭐ Determinism ⊥ halo — "conceal/survive = heat-low + survived" is the passive-SK TAUTOLOGY, cheap to
compute ≠ safe to credit.** Making the surrogate deterministic does NOT de-circularize it (suspicion ≈
survived ≈ won). So concealment/heat credit wears the §10a brackets UNCHANGED whether LLM or deterministic:
offense-paired (silence can't win the basket); role-conditioned deserved-vs-undeserved (deterministic — a
wolf shedding DESERVED heat = the deception working, credit as deception-skill not abstract-good);
leverage-weighted + disagreement-with-outcome residual (credit concealment that HELD AGAINST THE RUN, not
heat low because the game was already won). "It's deterministic now" must not relax the guard.

**A3. ⭐ Add the NIGHT-ACTION endpoint — the EXPOSURE axis the day-vote can't see.** The day-vote = the
CONSENSUS axis (who got lynched); it structurally misses discussion consequences that land at NIGHT:
power-role revealed/exposed → night-KILLED (the reveal-timing COST, the other half of find→lynch);
deceiver/power-role tipped a HIDDEN read → vigilante-shot / investigator-targeted / SK-killed. The hidden
read is deception-relevant and the vote literally can't show it (a reader who didn't voice it / acted at
night manifests ONLY as a night action). Mostly deterministic (`night_resolutions` join: day-N discussion
→ night-N targeting by faction/role). CAVEAT: attribution confounded (we see the kill, not the killer's
reason — discussion vs being-a-known-power-role). IMPORTANCE: high for the investigator reveal-RISK
(revealed→died) and deceiver CONFIRM-OUT (exposed→shot) — both vote-invisible — but noisy → add
role/leverage-conditioned, expect noise; MEASURE how often discussion precedes a vote-invisible
night-targeting (free dump check) rather than guess the weight.

**Amended credit endpoints:** day-vote (consensus, team-aware) + night-action (exposure: reveal-risk +
confirm-out) + multi-day find→lynch — all deterministic, post-game for all horizons. LLM residual
(framing-detect + credibility) = end-of-day. De-halo brackets apply to ALL concealment credit (A2).

**A4. ⭐ AGENT REASONING as a tagger input + PER-ROUND chunking (2026-06-19).** The agent's own
reasoning (vote justification, night-target rationale) is captured free-text deterministic tagging can't
use — and it's a causal unlock: (i) DE-CONFOUNDS Part-3 night attribution (the killer's reasoning states
WHY it targeted — discussion vs known-power-role), (ii) surfaces the HIDDEN READ (a voter's reasoning
reveals reads formed-but-never-voiced — the deception signal the vote misses), (iii) self-reported
INFLUENCE chains ("Y convinced me") = cleaner than the null seq lead-vs-follow proxy → rescues causal
attribution. CAVEAT: it's the agent's ACCOUNT (LLMs confabulate) + helps ATTRIBUTION (who/why) NOT valence
(valence stays on the deterministic outcome; structure-not-valence). ⭐**CHUNKING — dissolves the
post-game-vs-end-of-day dichotomy: two orthogonal choices.** INPUT UNIT = PER-ROUND (one day's discussion
+ that day's votes+reasonings + that night's actions+reasonings) — small/focused/flash-lite-friendly (the
real lever; whole-game-in-one-call is bad for flash-lite). WHEN-fired = live-per-round vs deferred; tags
never feed play → DEFERRED wins (no live latency, night reasonings present, instruction-prefix cached
across rounds). → **per-round-chunked, fired deferred = ONE flash-lite call per ROUND, not per game.**
Timing: role_claims persist still rides the per-day day_summary (offense/transmission, pre-night); the
night-inclusive tagging is end-of-round/deferred (night reasoning doesn't exist at day_summary time).
