# A rigorously-measured cross-game-learning memory system for multi-agent Werewolf

**Status:** v7 memory-research iteration · static-memory result solid · **compounding question OPEN** (the loop run that was meant to answer it was invalid — see §3/§5c)
**Provenance:** repo `8bfd0ad` (`feature-dimension-schema`); loop run on `bdfe1fa..52e26b1`; run record + config in `evidence/v7_final/v2_full/` (`run_meta.json`, `loop_history.json`, `cost_report.json`, `v2_salvage.py`).

> **One-line claim set (read this first, then the rest qualifies it):** Static episodic memory measurably improves town play (**+17pp, paired A/B, p=0.013**) — more than market sims, which are stateless. The agents **demonstrably learn across games** (a self-consolidating credit→synthesize→prune loop that updates the store from outcomes). Whether that *compounding* further improves play is **still open**: the loop run built to test it accidentally enabled memory for *all* factions (not the intended town-only), confounding the town signal in an arms race — though it does, by accident, show a **tentative positive compounding signal for *wolf* memory**. The durable deliverable is the **eval instrument plus the rigor around it**: it caught **two** invalid runs (a distorted baseline, then a config slip) and a halo in my own first-pass analysis — honest negatives and retracted claims beat fragile positives.

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

A first loop run produced a plausible-looking slope. On audit it was **invalid**: the de-lucked baseline was sourced from a biased subset of decisions, so the *lift* — the signal that drives both credit and the slope — was distorted. The structural fixes (below) addressed that. **But the rerun was invalid too, for a different reason**, caught only on a later independent re-audit (§5c): it enabled memory for *every* faction instead of the intended town-only, so the town signal sits inside an arms race. **Two invalid runs, two distinct causes — and the second is the more instructive, because the run *looked* clean (paired, cost-capped, replicated) and a first-pass analysis even rationalized its null with a "null control" that didn't exist.** That is the honest core of this report: a stateful-agent eval is a minefield of silent confounds, and the value is the discipline to keep finding them. The structural fixes that *do* hold:

- **Paired arms** — the memory-on and memory-off arms play the **same boards** (matched `game_id` → identical role draw + scheduler seed), so memory is the *only* difference and board-draw variance cancels.
- **Valid baseline** — the de-luck baseline comes from the dedicated, same-epoch off arm, not incidental off-policy decisions.
- **Cold start** — the store builds from *zero* on the current substrate, rather than warm-seeding a store mined on an outdated one.
- **Cost discipline** — every paid model pinned to the cheap tier on the driver's own process (not just subprocesses), plus in-run cost capture. First run ~$100; rerun **$15**.
- **Arm guard (added after the slip)** — the driver now reads the ON arm's *actual* enabled-faction set and crashes generation-1 unless it matches a **declared** `--expect-factions`, recording it in `loop_history`. The config slip that wasted the rerun would have been a $0.50 crash instead of a $65 null.

## 4. Evaluation setup

- **Generations:** 13 planned × 4 games/arm, paired ON/OFF, run in one capped pool; consolidation every generation. **Stopped at gen-6** by a pre-registered rule (below).
- **Intended arm:** town-only memory (deceivers frozen, so town learning is isolated). **What actually ran:** `configs=all_enabled` — every faction had memory. This is the invalidating slip (§5c); the analysis below is therefore *per-faction* on the run as it actually executed.
- **Metric:** per-decision de-lucked proxy, aggregated per faction, **ON − OFF per generation**. The slope across generations is the headline; gen-1 is the empty-seed bootstrap and is excluded.
- **Pre-registered stopping rule (set before the run):** positive slope → memory compounds → freeze/ship. Flat → honest negative-with-mechanism → **stop, do not escalate N**. *Caveat in hindsight:* this rule only fires validly on a valid arm — applying it to the confounded town signal was a category error (§5c).

## 5. Results

### 5a. Claim 1 — static memory helps (the validated positive)

In a prior **paired, same-epoch, pre-registered A/B**, town with a static memory store beat town without it by **+17pp (p=0.013)**. This is a *different experiment* from the loop — it measures *having* memory, not *compounding* it — and it stands on its own. **Takeaway:** the memory premise is real; stateless market sims leave this on the table.

> Confidence: this is the headline win-rate result; direction and magnitude both supported at the A/B's N. The mechanism was defensive (memory mostly helped town *avoid* day-2 mislynches), which matters for how we frame the demo, not whether the effect exists.

### 5b. Claim 2 — the system demonstrably learns

The loop is not a static index. Across the run the store **built from zero and self-consolidated from outcomes**: credit fired (hundreds of followed directives graded per generation), credit-aware synthesis engaged once track records accumulated, prune/decay culled. This is mechanism, not outcome — it holds regardless of the §5c confound, which is about *whether the consolidation improves play*, not *whether it happens*. **Takeaway:** "agents that learn across games" is true at the *mechanism* level — observable, and the natural thing to make *visible* in a demo. This is the differentiated capability regardless of the compounding verdict below.

### 5c. Claim 3 — does compounding improve *play*? UNRESOLVED — the run was confounded, and here is the honest post-mortem

The headline I first wrote here was wrong, and the way it was wrong is the most useful thing in this report.

**What I first claimed (RETRACTED):** "Town ON − OFF is a noisy weak-negative (mean −0.18); and wolf/SK — which *have no memory in either arm* — swing the same ±0.2-0.3, so that's the pure-noise floor; the town signal sits inside its own null control; therefore noise-limited, stop." It reads clean. It is false at the root.

**The defect (found on independent re-audit of the raw records):** the run did **not** enable memory town-only. `run.log` and every ON record's `memory_config` show **`all_enabled`** — wolf and SK had full memory too (their SPs took *hundreds* of follows; ~3 retrieved per decision on 84-94% of decisions). So:

- **The "null control" does not exist.** Wolf/SK were a live *treatment* arm. Their non-zero swing isn't a noise floor — it's their own (real) memory effect plus noise. The argument that "proved" noise-limitation was circular.
- **Wolf on−off actually *trends up*:** −0.14, −0.05, −0.11, +0.17, +0.10, **+0.28** (mean **+0.077**, OLS slope **+0.086** over gens 2-6) — the one monotone, compounding-shaped signal in the run, which I had dismissed as noise.
- **The town number is confounded by an arms race.** The vote proxy scores a town vote `positive` only if the votee is genuinely evil; better-concealed (memory-improved) wolves make town mislynch more, *mechanically* depressing the town proxy regardless of town's own skill. De-luck removes outcome luck — **not opponent strength**. ON-arm town (facing memory-wolves) vs OFF-arm town (facing memoryless wolves) is not a clean contrast.
- **The "+0.41 town / discussion +0.26-0.48" lift was a halo, retracted.** It was raw `(pos−neg)/follow` with the tagger baseline pinned to 0 — a *level*, never differenced against no-memory (positive verdicts occur with or without memory). Differenced properly via the free day-vote-endpoint floor, town discussion on−off is pure noise (mean ≈ −0.12); including discussion does **not** rescue the town number (−0.18 either way). A first re-score even got this wrong a second way — ON/OFF share `game_id` and tags cache per `game_id`, so it silently scored the OFF arm with ON-arm tags. Fixed.

**Repositioned result — the run is a valid *all-memory-on* per-faction A/B** (paired by board; `v2_salvage.py`, $0 re-read):

| faction | on−off mean (g2-6), vote+night | slope | read |
|---|---|---|---|
| **wolf** | **+0.077** | **+0.086 ↑** | tentative positive, compounding-shaped — the one real signal |
| town | −0.189 | −0.027 | **confounded** (arms race) — *not* a verdict on town memory |
| serial_killer | −0.142 | +0.027 | ≈ null |

**Takeaways, honestly bounded:** (1) the **town compounding question is unanswered** — the run can't isolate it, and no post-hoc analysis repairs a board that already contained memory-wolves; (2) the run accidentally produced a **tentative positive for wolf memory** (underpowered at 4 games/gen, ±0.2-0.3 swings — directional, not significant); (3) the noise *is* large — that observation from the original write-up survives; what does not survive is using it to declare the question settled.

> Why the variance is large (this part holds): per-game town de-luck swings **±0.9 even on matched boards**, because a stateful game diverges the moment memory flips one vote — so pairing decays after the first differing decision. More games/generation is the only lever, and it runs into model-epoch drift. That makes a *powered* compounding number genuinely expensive — but it does not excuse running (and reading) the wrong experiment.

## 6. Decision and tradeoffs

**The memory architecture is NOT frozen on this evidence** — that was the original (premature) call, made on the confounded run. The correct status: **static memory helps (Claim 1, solid); the system learns (Claim 2, solid); whether compounding improves play is open.** The cheapest path to actually answering it is a single **town-only** rerun (now guarded by `--expect-factions`, so the slip can't recur) at the same N — *or* deciding the demo value (Claim 2, visible learning) is sufficient and the powered compounding number isn't worth the model-epoch-drift cost. **Tradeoff:** the noise analysis is real (a powered per-decision compounding number is expensive), but "expensive to measure" was wrongly conflated with "measured and null." Those are different, and only the first is true.

## 7. Lessons (transferable)

- **A "null control" is only as good as the assumption that it's null — verify it from the data, not the intent.** I built a clean noise-floor argument on "wolf/SK have no memory," never checked the run's actual `memory_config`, and the records said otherwise. The most persuasive-looking argument in the first draft was the most wrong. Before trusting a control subgroup, assert it really received zero treatment.
- **Make the experiment's identity a checked invariant, not a launch-time intent.** The run silently executed `all_enabled` instead of `town_only` because the driver defaulted to it and nobody asserted the arm. The fix is mechanical and cheap: read what *actually* ran (the per-role memory map), assert it equals a *declared* expectation, fail loud on generation-1. A $0.50 crash beats a $65 null. Two of two invalid runs were "the harness ran a different experiment than I thought" — guard that class explicitly.
- **Pairing reduces variance only as far as the units stay paired.** Matched initial conditions cancel draw variance for a *single per-unit outcome* (win/loss). For a metric aggregated over a *trajectory that diverges*, the pairing decays after the first divergence — and at the aggregate level the paired estimator collapses to the unpaired one. Pair at the grain you measure, or know that you can't.
- **A distorted baseline silently invalidates everything downstream, with no error thrown.** Lift feeds credit feeds synthesis feeds the slope; a biased baseline corrupts all of it while every number still *looks* plausible — as does a halo (a level reported as a gain because it was never differenced against the control).
- **A trustworthy negative beats a fragile positive — but "expensive to measure" is not "measured and null."** The instrument is the asset; the verdict is a readout, and a readout from the wrong arm is not a verdict. Re-auditing your own clean-looking result is the job.

## 8. What's next

Two honest options, not one:

1. **Answer the compounding question** with a single **town-only** rerun (~$15, now guarded by `--expect-factions` so the slip can't recur). This is the clean experiment that was never actually run. Worth it if the compounding claim matters; skippable if Claim 2 (visible learning) carries the demo.
2. **Ship the visibility, treat compounding as open.** A frontend **memory inspector** that shows the agent retrieving a specific past-game lesson and acting on it makes the differentiated capability — *agents that demonstrably learn across games* — tangible. Win-rate (+17pp) proves memory helps; the demo proves it learns; the compounding magnitude stays an open, honestly-labeled question.

Either way, two known gaps if the loop is revived: (a) SP adoption counters aren't merged back into the loop store, so the dead-weight eviction rule is currently inert (prune-by-lift still works); (b) the new-clusters-only synthesis gate is a no-op at `k=1` with small games/gen (every cell gets new obs every tick), so the SP-bloat control it was built for was never actually exercised.

**One validated instrument lead** (for *deceiver* play, which the vote proxy can't measure): the omniscient discussion-tagger's verdict predicts the wolf/SK win **beyond** the de-luck vote proxy (partial r ≈ +0.56/+0.60), and that signal **survives blinding the tagger to the game outcome and controlling for verbosity** — so it's real skill, not outcome-leak or wordiness (`tagger_skill_retest.py`). It's correlational at N=24, so it validates *a metric*, not a memory effect — but it's the natural instrument for a future measurement of *deceiver* memory, the gap the town-centric vote proxy left open. (En route, a 2×2 ablation also confirmed the tagger's outcome-leak is negligible, so the production tagger keeps its hindsight; details in `experiment_log.md` §12g.)

## 9. Artifacts

| File | What |
|---|---|
| `evidence/v7_final/v2_full/loop_history.json` | per-generation scores (per-faction ON/OFF) + `arm_factions` |
| `evidence/v7_final/v2_full/v2_salvage.py` | the repositioned all-memory-on per-faction A/B (the corrected §5c table) |
| `evidence/v7_final/v2_full/run.log` | shows the actual arm: `all_enabled` (the slip) |
| `evidence/v7_final/v2_full/cost_report.json` | realized cost ($15.00; games $13.43 + overhead $1.57), Langfuse-sourced |
| `evidence/v7_final/experiment_log.md` §11j, §12 (incl. **§12f correction**) | invalidity corrections + the repositioned analysis |
| `evidence/v7_final/consolidation_design.md` | the credit→consolidate design (incl. §11 dual-window souring spec, built-but-deferred) |

**Provenance:** repo `8bfd0ad`; run config — cold start, 13 gens planned (stopped gen-6), 4 games/arm, paired ON/OFF, `synth_every_k=1`, `window=8`, all models `gemini-3.1-flash-lite`. **Arm as INTENDED:** town-only. **Arm as RUN:** `all_enabled` (the invalidating slip; §5c).
