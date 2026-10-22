# Measuring compounding — journey log (June to October 2026)

> **What this is.** The chronological path from "we cannot tell whether memory compounds" to a
> signed pre-registration and the run it governed. Later entries supersede earlier ones. Where a
> design changed, the change is shown in its place rather than edited away.
>
> **Companion docs.** The decision, stated destination-first: [`report.md`](report.md). This log
> condenses the planning documents in this folder (`phase_b_plan_review.md`,
> `compounding_measurement_plan.md`, `power_analysis/`, `v7_run_preregistration_DRAFT.md`,
> `v6_wide_migration_roadmap.md`), removed on 2026-10-22 and kept in git history at commit `24dfd3a7`. Terms used below (generation,
> strategy point, de-lucked decision score, slope, board, epoch, MDE) are defined in `report.md`
> §1–3.

---

## ① Motivation — one noisy number per generation

**2026-06-12 · Phase B planning review.** The first sign of the measurement problem came before the
loop existed. The review deleted a planned large win-rate experiment. The reasons it gave were that
drift in the hosted model "makes any big-N number fragile", and that the durable asset is the
method, not the point estimate. It also ruled that per-role comparisons sat below the measured
detection floor (about 0.18 vote accuracy at 30 games), so those choices were assigned by reasoning
rather than measured. From then on, each change was to be measured at the level where it acts, and
whole-game runs were kept for two named cases.

**2026-06-21 to 06-23 · two loop runs, both invalid.** The first had a biased baseline. The second
silently gave memory to every faction instead of town only (`../v7_final/report.md` §5c). Both were
read with the planned slope, and the second also showed how noisy that readout was: per-generation
means swung by ±0.2 to 0.3 at 4 games per generation.

The incumbent design was defensible. A trend across generations is the natural picture of
"getting better with play", and the de-lucked score had been validated as measuring the right thing.
The root cause was that the run size had been chosen by budget, not by what the test could detect.
The July plan's standing-gates list puts it plainly: "every design step is pre-registered except N".

## ② Design — size the wall before paying (2026-07-04 plan)

The plan diagnosed the instruments as "valid but underpowered". Nothing in the stack would
manufacture a false positive any more, but the game-to-game noise swamped the hoped-for +0.1 to +0.2
improvement. Its summary: "the enemy is noise, not missing gold labels". Two tempting moves were
rejected. Buying more games would not fix a readout that might be hopeless at any affordable size.
A broad labelling push would make the ruler more accurate without making the games less noisy.

What it proposed instead:

- **A claim ladder, written before any run**, so that a later deferral reads as scoping and not as
  salvage after a null. Rung 1 (having memory at all) belonged to the earlier fixed-store
  experiment. Rung 2a: the loop improves the store. Rung 2b: agents consequently decide
  better on frozen boards. Rung 3: this shows up as live wins, deferred and costed.
- **Phase 0 starts with a $0 power analysis.** If detection at an affordable size came back near
  10%, that number would justify the redesign in advance instead of a third null discovering it.
- **Candidate redesigns, held until the analysis ran:** checkpoint replay (a fixed exam re-answered
  against each generation's store) and strategy-point lineage (per-rule before and after
  comparisons).

## ③ Verify → decide

**2026-07-05 · the power analysis.** *Catches:* the risk that the planned run could not detect a
plausible effect at any size the project could pay for. Method: resample memory-off games from three
earlier sets, plant a known straight-line improvement, run the planned slope test 2,000 times per
setting ($0, `power_analysis/mde_table.md`).

- **The plan's noise assumption was wrong.** Per-game noise was 0.27 to 0.33, not ±0.9. The ±0.9 had
  been the spread of one graded decision, and a game averages several.
- **Even so, the slope test could not see the plausible effect.** A planted +0.15 was detected 11% of
  the time at the size of the last run (24 games, $7) and 56% at 200 games ($56). The smallest effect
  detected 80% of the time at 200 games was +0.20.
- **Checks:** a closed-form formula with no shared code gave 11/53/78% against the simulation's
  11/56/81% on three reference settings, and the planted-zero false-alarm rate sat at 2–3%.

*Decision:* retire the slope as the compounding readout. The question is recorded as open, not
answered. The same day, the lineage field (`distilled_from`) shipped, and the owner proposed the
end-point paired A/B: build the store silently, then compare the final store against the
generation-1 store on shared boards. The argument (`power_analysis/decision_rationale.md` §5) is that
a step measured on paired boards is far easier to detect than an unpaired ramp.

**2026-07-11 · the plan adopts the end-point A/B as the run's single primary endpoint.** Final store
against generation-1 store on 30 shared boards, graded with the town decision score. Checkpoint
replay moved to one batch after the run, on held-out games, so that a store could never be tested on
decisions from the games it learned from. The plan's closing instruction: "do not re-grow a slope
readout mid-run".

**2026-07-13 · pre-registration drafted.** Its §3 named the control as the memory-off baseline,
which disagreed with the plan's adopted design (generation-1 store). The discrepancy was carried to
signing rather than resolved silently.

**2026-07-16 · smoke test passed; pre-registration signed; run launched.** The signature resolved the
control question in a revision section (§8): three conditions on 20 shared boards each, with final
against generation-1 as primary and memory-off as secondary. It also limited the run to the town
arm, set the size (4 generations × 10 memory games + 10 memory-off games, plus 60 endpoint games,
$77–98 within a $150 reserve), and fixed the stopping rule and interpretation commitments (report
§4). Partial generations from crashed attempts were later set aside in quarantine folders, not
pooled, as the signed rules required.

**2026-07-19 · build run complete.** Four generations, $25.74, final store of 168 strategy points.

**2026-07-20 · endpoint amended, then run.** Before any endpoint game, the owner changed the design to
30 boards × {final store, memory off}. The recorded reasons: the generation-1 snapshot held no
strategy points and no per-generation tell book existed, and the freed games tightened the primary
comparison's standard error by about 22% (`batch_results/v7_endpoint_ab/PREREG_AMENDMENT.md`). The
primary now tests the built store against no memory, not compounding against a starting store.

*Result (60 games):* town decision score 0.147 lower with memory, per board (p ≈ 0.06), lower on 19
of 30 boards. Read as committed: no detected compounding, with the point estimate leaning toward
harm. A secondary vote-level measure was clearer (threat votes about 15 points fewer, abstentions
31% against about 23%, p < .001, counted per vote). Forensics: `../credit/blindspot_fix/`.

**2026-07-21 · closure.** The owner declined a further run (about $25) and closed the memory
research: no memory configuration certified as beneficial on the current epoch, no store promoted,
live play ships with memory off.

**2026-10-04 · scope addendum.** Every endpoint game ran at thinking level "minimal", which produced
zero reasoning tokens for this model. Arms matched, so the comparison stands, but every verdict
above is about a player that does not reason.

## ④ Remaining questions

- Whether a store would compound in live play once abstentions are graded as costly. A grading fix
  was built after the run and checked only against recorded games; a live run to test it was
  considered and declined (2026-07-21).
- What memory does for a player that reasons before acting. No game in this program tested it.

---

**Sources.** `phase_b_plan_review.md` (2026-06-12) · `../v7_final/report.md` §5c (the June runs) ·
`compounding_measurement_plan.md` (TL;DR, claim ladder, §0.1–0.3, §R, standing gates, sequencing) ·
`power_analysis/mde_table.md` and `decision_rationale.md` (2026-07-05) ·
`v7_run_preregistration_DRAFT.md` (§1–4, §7, §8; signed 2026-07-16) ·
`batch_results/v7_compound_town5/` · `batch_results/v7_endpoint_ab/` ·
`../credit/blindspot_fix/experiment_log.md` §①, §⑥, §⑦.
