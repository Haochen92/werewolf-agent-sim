# A rigorously-measured cross-game-learning memory system for multi-agent Werewolf

**Status:** complete · final memory-research iteration (v7) · architecture frozen
**Provenance:** repo `8bfd0ad` (`feature-dimension-schema`); loop run on `bdfe1fa..52e26b1`; run record + config in `evidence/v7_final/v2_full/` (`run_meta.json`, `loop_history.json`, `cost_report.json`).

> **One-line claim set (read this first, then the rest qualifies it):** Static episodic memory measurably improves town play (**+17pp, paired A/B, p=0.013**) — more than market sims, which are stateless. The agents **demonstrably learn across games** (a self-consolidating credit→synthesize→prune loop that updates the store from outcomes). Whether that *compounding* further improves play is **below the measurement floor at affordable N** — and we show that with a built-in null control rather than assuming it. The durable deliverable is the **eval instrument** that can tell those three apart honestly.

---

## 1. Motivation

Multi-agent game sims are almost all **stateless role-players**: each game starts from zero, nothing carries over. The premise here was the opposite — agents that **learn across games** via an episodic+procedural memory store. Two questions follow, and they are *not* the same: (a) *does having memory help?* and (b) *does memory that updates itself from outcomes — compounding across games — help more over time?* The gap we set out to close was measuring (b) honestly, because (a) was already evidenced and (b) is the actual frontier claim.

## 2. Design and hypothesis

The system is two memory channels plus a learning loop:

- **Episodic** (`observations`) — omniscient post-game facts, the substrate for inference (a villager reasoning from "who behaved how").
- **Procedural** (`strategy_points`) — IF-situation→THEN-action directives, the substrate for execution.
- **The compounding loop** — between batches of games: **de-lucked credit assignment** grades each *followed* directive by the decision's outcome *against a memory-off baseline* (not win/loss, which is luck-laden); then **synthesize / prune / decay** consolidate the store — keep what earns credit, drop what doesn't, distill new directives from accumulated observations.

**Hypothesis:** if the credit signal is real, the store should *compound* — decision quality should slope **up** across generations versus a flat memory-off baseline.

The deliberate design bet was to **measure the choice, not the outcome**: score each *decision* by a de-lucked proxy (was the vote/target correct against true roles, independent of whether the lynch/kill landed), because game win/loss is too noisy and too luck-laden to be the per-generation instrument. Tradeoff: the proxy is a stand-in for "good play," not ground truth — accepted because deterministic decision-quality scoring isn't feasible and the proxy is drift-immune where win-rate is not.

## 3. The iteration that mattered: making the instrument trustworthy

This is, honestly, a report about an **eval instrument** as much as a memory system — because the first attempt at measuring (b) was *invalid*, and catching that was the highest-leverage work.

A first loop run produced a plausible-looking slope. On audit it was **invalid**: the de-lucked baseline was sourced from a biased subset of decisions, so the *lift* — the signal that drives both credit and the slope — was distorted. **Instrument validated, bug caught and fixed before any number was trusted.** (Detail lives in the log; it is a credibility note, not a result.) The fix was structural, and it defines the valid run:

- **Paired arms** — the memory-on and memory-off arms now play the **same boards** (matched `game_id` → identical role draw + scheduler seed), so memory is the *only* difference and board-draw variance cancels.
- **Valid baseline** — the de-luck baseline comes from the dedicated, same-epoch off arm, not incidental off-policy decisions.
- **Cold start** — the store builds from *zero* on the current substrate, rather than warm-seeding a store mined on an outdated one. This also gives the cleanest possible compounding shape: a slope that should rise from ~0 as the store fills.
- **Cost discipline** — every paid model pinned to the cheap tier on the driver's own process (not just subprocesses), plus in-run cost capture. The invalid first run cost ~$100; the valid run cost **$15**.

## 4. Evaluation setup

- **Generations:** 13 planned × 4 games/arm, paired ON/OFF, run in one capped pool; consolidation every generation. **Stopped at gen-6** by a pre-registered rule (below).
- **Metric:** per-decision de-lucked proxy, aggregated per faction, **ON − OFF per generation**. The slope across generations is the headline; gen-1 is the empty-seed bootstrap and is excluded.
- **Pre-registered stopping rule (set before the run):** positive slope → memory compounds → freeze/ship. Flat → honest negative-with-mechanism → **stop, do not escalate N** (escalating N hits the model-epoch-drift wall that makes big-N numbers unreproducible). This rule is what lets a low-N null be *defensible* rather than inconclusive.
- **Diagnostics added:** fail-loud invariants (every silent seam raises), and — surfaced during analysis — a **built-in null control** (see §5).

## 5. Results

### 5a. Claim 1 — static memory helps (the validated positive)

In a prior **paired, same-epoch, pre-registered A/B**, town with a static memory store beat town without it by **+17pp (p=0.013)**. This is a *different experiment* from the loop — it measures *having* memory, not *compounding* it — and it stands on its own. **Takeaway:** the memory premise is real; stateless market sims leave this on the table.

> Confidence: this is the headline win-rate result; direction and magnitude both supported at the A/B's N. The mechanism was defensive (memory mostly helped town *avoid* day-2 mislynches), which matters for how we frame the demo, not whether the effect exists.

### 5b. Claim 2 — the system demonstrably learns

The loop is not a static index. Across the valid run the store **built from zero and self-consolidated from outcomes**: credit fired (hundreds of followed directives graded per generation), credit-aware synthesis engaged once track records accumulated, prune/decay culled. **Takeaway:** "agents that learn across games" is true at the *mechanism* level — observable, and the natural thing to make *visible* in a demo. This is the differentiated capability regardless of the win-rate verdict below.

### 5c. Claim 3 — does compounding improve *play*? Below the floor — and here is the proof

Town ON − OFF de-luck, gens 2-6:

| gen | 2 | 3 | 4 | 5 | 6 | mean |
|----|----|----|----|----|----|----|
| town on−off | −0.16 | −0.33 | +0.17 | −0.32 | −0.30 | **−0.18** |

**Takeaway:** no positive compounding — a noisy, weak-negative wander. The instinct is to read a trend; the discipline is not to. Here is *why* you cannot:

**The built-in null control.** Wolf and serial-killer have **no memory in either arm** (this is a town-only run), so their ON − OFF *must* be ~zero in expectation. It is not:

| gen | 2 | 3 | 4 | 5 | 6 |
|----|----|----|----|----|----|
| wolf on−off | −0.05 | −0.11 | +0.17 | +0.10 | +0.28 |
| SK on−off | −0.14 | −0.26 | −0.14 | −0.07 | −0.10 |

**Takeaway — this is the whole result.** Roles with *zero* memory effect swing **±0.2-0.3 per generation — the same magnitude as town**. That floor is pure game-divergence noise (town's memory-changed votes → different lynches → different boards for everyone). **The town signal sits inside its own null control.** No effect, positive or negative, is separable at 4 games/generation. This is *shown*, not asserted — the cleanest evidence of noise-limitation I could ask for, and it came free from the role structure.

**Why the variance is intrinsic (not a fixable measurement artifact).** Per-game town de-luck swings **±0.9 even on matched boards** — within-pair correlation is low because a stateful game diverges the moment memory flips one vote. So pairing is *maxed*: at the generation level, differencing within pairs is algebraically identical to the aggregate. The only lever left is more games/generation, which is the model-epoch wall the stopping rule excludes.

**The direction, for completeness.** The weak-negative tilt traces to one cell. Followed-content lift is **net +0.41 across town**, with discussion cells **+0.26…+0.48** — *except* **`villager/day_vote` = −0.118**, the cell the vote-proxy most directly measures. Mechanistically, procedural *directives* slightly underperform the pure-inference villager's gut+observation reasoning on votes (consistent with the static result being *defensive/inference*-driven, not directive-driven). It is within the noise floor — directionally interesting, not a claim.

> Assumption corrected: we expected pairing to deliver the variance reduction. It did — for win-rate. For per-decision de-luck on a divergent sequential game it cannot, because the arms stop sharing a board after the first differing decision. That reframing *is* the result.

## 6. Decision and tradeoffs

**We stopped at gen-6 and froze the memory architecture** — the pre-registered call for a flat slope. The strongest argument against: "run all 13, maybe it turns." We reject it because the null control shows the *floor*, not just the points — gens 7-13 would oscillate inside the same band, and the variance is intrinsic, so more generations buy noise, not signal. Escalating to many games/generation would chase the number into model-epoch drift, where it stops being reproducible. **Tradeoff accepted:** we forgo a powered win-rate number on compounding, and keep instead a *trustworthy* bound plus the mechanism for why a powered number isn't affordable. Stopping early also saved ~$20 (run cost $15, not ~$35).

## 7. Lessons (transferable)

- **A built-in null control beats a significance test at small N.** A subgroup that *must* have zero treatment effect, measured the same way, reveals the noise floor directly. Here, no-memory factions swinging as hard as the treated faction settled "noise-limited" in one glance — no power analysis needed. Look for a null group inside the system before reaching for more N.
- **Pairing reduces variance only as far as the units stay paired.** Matched initial conditions cancel draw variance for a *single per-unit outcome* (win/loss). For a metric aggregated over a *trajectory that diverges*, the pairing decays after the first divergence and the variance returns — and at the aggregate level the paired estimator collapses to the unpaired one. Pair at the grain you measure, or know that you can't.
- **A distorted baseline silently invalidates everything downstream, with no error thrown.** Lift feeds credit feeds synthesis feeds the slope; a biased baseline corrupts all of it while every number still *looks* plausible. The cheapest safeguard is a paired same-board counterfactual; the second cheapest is auditing the baseline's *provenance* before trusting a result.
- **A trustworthy negative beats a fragile positive.** A credible "no measurable effect, and here's the floor and the mechanism" is more defensible — and more reusable — than a positive that a re-run might not reproduce. The instrument is the asset; the verdict is a readout.

## 8. What's next

The memory *research* is complete; the architecture is frozen. The remaining value is **visibility, not more measurement**: a frontend **memory inspector** that shows the agent retrieving a specific past-game lesson and acting on it. That makes the real, differentiated capability — *agents that demonstrably learn across games* — tangible, which is the USP, independent of the compounding slope. Win-rate (+17pp) is the proof that memory helps; the demo is the proof that it learns. If the loop is ever revived, one known gap to close first: the SP adoption counters aren't merged back into the loop store, so the dead-weight eviction rule is currently inert (prune-by-lift still works).

## 9. Artifacts

| File | What |
|---|---|
| `evidence/v7_final/v2_full/loop_history.json` | per-generation scores (incl. per-faction ON/OFF — the null-control data) |
| `evidence/v7_final/v2_full/cost_report.json` | realized cost ($15.00; games $13.43 + overhead $1.57), Langfuse-sourced |
| `evidence/v7_final/v2_full/run_meta.json`, `run.log` | run start (cost window) + full generation log |
| `evidence/v7_final/experiment_log.md` §11j, §12 | the invalidity correction + the valid-run analysis this report draws from |
| `evidence/v7_final/consolidation_design.md` | the credit→consolidate design (incl. §11 dual-window souring spec, built-but-deferred) |

**Provenance:** repo `8bfd0ad`; run config — cold start, 13 gens planned (stopped gen-6), 4 games/arm, paired ON/OFF, `synth_every_k=1`, `window=8`, all models `gemini-3.1-flash-lite`.
