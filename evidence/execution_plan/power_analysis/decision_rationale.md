# Why we retired the game-level slope readout for compounding

**Genre:** decision record. This is the plain-language version of the argument; the numbers live in
[`mde_table.md`](mde_table.md) and the plan that this feeds is
[`../compounding_measurement_plan.md`](../compounding_measurement_plan.md).

---

## 1. The decision (2026-07-05)

No more paid loop runs will use the **game-level slope readout** to answer whether memory compounds.
By "the game-level slope readout" we mean the plan to grade the average decision quality of each
generation of games and check whether that average trends upward as the loop keeps learning. A free
simulation showed that this readout is effectively blind: even when we *build in* a realistic
improvement and know for certain it is there, the readout almost never notices it, at any number of
games we could afford. So it is retired for this question. The compounding question itself is **not**
answered and **not** closed — it moves to the redesigned readouts in item 7.

## 2. The three rulers we can measure with

There are three ways to score a run, from noisiest to finest. Knowing which one this decision is about
prevents confusion later.

- **Win rate** — one win/loss per game. It is a single coin-flip-like outcome that depends heavily on
  luck of the board, so it is the noisiest ruler. It is never the anchor for any claim here.
- **The per-game decision score** — every vote and night action in a game is mechanically graded
  against the true hidden roles (a good move is +1, a neutral move 0, a bad move −1), then averaged
  over the game. This is a much steadier ruler than win rate because one game contains several graded
  moves. **The slope readout uses this ruler, so this whole analysis is about this ruler.**
- **The mechanism grain** — credit and lineage tracked for each individual strategy the loop writes
  down, which sits *below* the level of a whole game. This is the grain the redesigned readouts move
  to.

## 3. The method: a fire drill before we pay

The analysis is a rehearsal. Before paying for a real experiment, you rehearse it on data where you
already know the answer, and you count how often the planned test gets that answer right.

The recipe: take real games in which nothing was actually improving (the memory-OFF arms of past runs,
where agents had no memory to compound), secretly add a fake improvement of a size we choose, then run
the exact test we planned. We repeat this **2000 times** per setting so the detection rate is stable.
If the test notices a realistic improvement only 11% of the time *when we planted it and know it is
there*, then on a real run the same test would almost always come back with a false "no effect."

**Why the invalid past runs are still usable here.** The two prior paid runs were thrown out for their
*conclusions* — one had a biased credit baseline, the other accidentally ran the wrong arm. But this
rehearsal never uses their conclusions. It uses only their memory-OFF games as a sample of how much a
game's score naturally bounces around for reasons unrelated to memory. That kind of natural noise
survives a botched experiment. Three independent game corpora were measured and they agree closely on
that noise level: the per-game score wobbles with a spread (standard deviation, the typical distance a
score sits from its own average) of **0.33, 0.32, and 0.27**.

## 4. The result

The load-bearing correction is that the real per-game noise is about **0.3**, roughly three times
*smaller* than the ±0.9 the plan had assumed. The ±0.9 was the spread of a single graded move; a whole
game averages several moves, so its score is much steadier than one move. Smaller noise is good news
on its own, but the improvement we are hunting for is also small relative to it.

| What we planted | At the previous run's size (24 games) | At 200 games ($56) |
|---|---|---|
| a +0.15 total improvement | noticed **11%** of the time | noticed ~**56%** of the time |
| smallest improvement noticed 80%+ of the time | larger than any grid effect | **+0.20** |

"200 games" means 20 games in each of 10 generations (20 × 10), which costs about $56. Even there, a
+0.15 improvement is missed nearly half the time, and the smallest improvement the test can reliably
catch is +0.20.

An effect-scaling ladder (printed by the apparatus, `mde_table.md` §B2) shows how detection scales
with the size of the improvement, holding the run at the cheap 24-game size. The simulated rate is the
authoritative number; the independent closed-form figure sits alongside it:

| Planted improvement | Noticed (24 games, simulated) | Closed-form check |
|---|---|---|
| +0.15 | 11% | 11% |
| +0.30 | 29% | 33% |
| +0.45 | 58% | 62% |
| +0.60 | 85% | 86% |

So the readout is not blind to *everything*. If compounding were huge, around +0.6, we would already
have seen it in the runs we paid for. But the plausible band is **+0.1 to +0.2**, which is exactly
where the readout fails. We believe the band is that small because the largest memory effect ever
measured here is the proven static-memory result, worth about **+0.2** on this same scale, and the
scale is capped at +1.0 with the no-memory town already near +0.3. There is little headroom, and
compounding is a subtler effect than simply having memory at all.

## 5. Why this does not contradict "we proved memory works with only 30 games"

The static-memory proof and the compounding question look similar but are shaped completely
differently, and the shape is what decides how many games you need.

- The static proof measured a **step**: every memory-on game carried the full ~+0.2 effect at once,
  about half a standard deviation per game, so the signal was large and present in every game.
- The static proof was also **paired**: the same boards were played twice, once with memory and once
  without, with memory the only difference. Pairing cancels board-luck noise, because both copies of a
  board share the same luck. That is why 30 games were enough.

Compounding is the opposite on both counts. It is a **ramp**, not a step: the improvement accumulates
gradually, maybe +0.03 per generation, so early generations carry almost no signal and even the last
carries under a tenth of a standard deviation per game. And it **cannot be paired**: the moment memory
changes one action, the two copies of a board diverge, so there is no matched twin to cancel the luck.

A step you can pair at 30 games is far easier to measure than a ramp you cannot pair at 200. The
static proof also anchored on the pre-registered decision-quality basket, never on win rate, which was
too noisy to carry a conclusion even in that easier case.

## 6. What this does *not* mean

This is a verdict on our ability to **verify** compounding from game-level scores, not on the loop's
ability to **learn**. The loop's internal credit system can still promote and demote strategies from
noisy per-game signals, because it aggregates them over many games and corrects its own mistakes as it
goes. The caveat is that per-strategy lift measured at 5 to 10 follows still carries a wide error bar,
roughly ±0.3 to ±0.4. That uncertainty is exactly why the proven-versus-unproven tiering fix (plan
§0.4) matters: it stops the loop from over-trusting a strategy whose track record is still too thin to
believe.

## 7. The redesigned readout path

The compounding question moves off the game-level slope and onto three readouts that are either paired
by construction or measured at the finer mechanism grain.

1. **Strategy-point lineage.** A `distilled_from` field shipped 2026-07-05. From the next run onward,
   every revised strategy records exactly which older strategies it was distilled from. That turns one
   noisy slope per run into dozens of paired before-and-after comparisons: did the revised strategy
   out-earn the ones it replaced?
2. **Checkpoint replay** (plan §0.2, next to build). Freeze a fixed set of decision points, then
   re-answer that same exam against each generation's saved store. Because only the store changes
   between answers, the comparison is paired by construction, gives hundreds of decisions of signal
   instead of a handful of games, and is diagnostic — it tells you *where* the store got better.
3. **The end-point A/B** (proposed 2026-07-05 by the project owner, pending ratification in the plan).
   Build the store silently for K generations, then run one paired 30-board contrast: the final store
   against the initial store. This is the key move. It converts the undetectable ramp back into the
   step-shaped, paired measurement that already succeeded at 30 games. Using the initial store rather
   than no-memory as the control isolates *compounding* specifically from the static "having memory"
   effect that is already proven.

## 8. Why we trust a free analysis

Two independent methods were made to agree. The 2000-rehearsal simulation was checked against the
standard textbook formula for this kind of test, which shares no code with the resampling path; both
are printed side by side by the standing apparatus (`mde_table.md` §B2, anchor cells). The formula
predicts detection rates of **11% / 53% / 78%** for the three anchor cells; the simulation produced
**11% / 56% / 81%**. Two derivations that share no code and land within a few points of each other are the
standard of proof appropriate for a $0 analysis. As a further check, the "planted nothing" column of
the table sits right at the theoretical false-alarm rate of about 2–3%, confirming the test is not
crying wolf on empty data.

---

**Sources.** Numbers lifted from [`mde_table.md`](mde_table.md) (2026-07-05, seed 20260618, 2000
replicates, produced by `evaluation/src/instrument_validation/power/mde_simulation.py`). Plan context:
[`../compounding_measurement_plan.md`](../compounding_measurement_plan.md) §0.1 (power gate), §0.3
(lineage field), and the rung-3 claim ladder.
