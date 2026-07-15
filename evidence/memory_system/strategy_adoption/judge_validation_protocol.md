# Strategy-Adoption Judge — Validation Protocol

> **🛑 EXECUTION DEFERRED (2026-06-01).** The protocol below is final, but running it is parked until
> after the foundation rebuild — the spot-check labels would be on old-structure (parallel, 4-role,
> day-only, v4-DB) games that are about to change. The *method* is substrate-independent and carries
> forward; execute it on v5 transcripts — the roadmap's label-once-on-v5 phase.

> **Purpose.** The strategy-adoption judge ("did the agent meaningfully apply a useful
> strategy?") is the one **load-bearing** prompt-quality judge in the project — its output is
> *reported as evidence*, not just used to steer prompt iteration. This is the one judge that
> earns a small human calibration before its numbers go in the report. This doc specifies that
> calibration and explains why the project's *other* LLM-judges do **not** need it.

## Why this judge is the exception

Triage every LLM-as-judge in the project by **what its output is used for**, not by how
important the thing it judges feels:

| Bucket | Use of the judge's output | Rigor needed |
|---|---|---|
| **A — directional dev-aid** | rank prompt v1 vs v2, pick the better wording, iterate | none beyond cheap hygiene |
| **B — reported comparative claim** | "config X applies strategy more than config Y" | this protocol |
| **C — gold** | ground-truth labels other evals are scored against | full panel + human anchor (see `retrieval/context_eval`) |

The strategy-adoption judge is **bucket B**: it makes an **absolute** claim that gets quoted
("agents apply a useful strategy N% of the time"). Absolute claims need a calibration anchor.
The reason bucket A doesn't: a judge only needs to be **consistently** biased, not accurately
calibrated — if it's 5 points generous on *both* prompts, the *delta* (which prompt wins) is
still correct; the bias cancels in the comparison. Bucket B has no comparison to cancel against,
so the bias has to be *measured*.

Note the project's **headline** number — the memory-on vs memory-off **win rate** — is
**judge-free** (win/loss is objective). So no LLM-judge sits on the critical path of the
portfolio's load-bearing claim. This protocol protects a *secondary, qualitative* claim.

## The protocol (one-time, ~half a day of human time)

1. **Sample ~25–30 judgments, stratified across the full score range — oversample the contested
   middle.** Do **not** sample only high/low cases (the current habit elsewhere): extremes agree
   trivially and tell you nothing; bias and noise live in the 2–3 band where the call is genuinely
   ambiguous. Stratify so the sample over-represents the middle, not the tails.
2. **Blind, independent self-label.** Label the raw cases yourself **without seeing the judge's
   score**. Do *not* "review the judge's output and agree/disagree" — that anchors you to it and
   you'll rubber-stamp. Label cold, then join on case ID.
3. **Compute two numbers:**
   - **Agreement** (exact, or within-±1-band on the graded scale) = the judge's accuracy proxy.
   - **Directional-bias sign test** on the *disagreements only*: of the cases where you and the
     judge differ, count judge-higher vs judge-lower. Roughly balanced → noise (fine, it averages
     out). Lopsided (e.g. 9 of 11 disagreements have the judge scoring high) → **systematic
     inflation** — report the claim with that caveat or fix the rubric and re-spot-check.
4. **Scope the result honestly in the report**, one sentence:
   > "Strategy-adoption judge validated against ~28 blind human labels: 82% within-band agreement,
   > no significant directional skew (sign test p = …)."
   That sentence converts "I trusted an LLM" into "I spot-checked the load-bearing judge and it
   held" — the methodological-maturity signal a reviewer looks for.

**What this is NOT:** not a panel, not a third model, not a gold set. One labeler, ~28 labels,
an afternoon. (The full panel + human-anchor machinery is reserved for the bucket-C retrieval
gold — see `evidence/retrieval/context_eval/experiment_log.md` §6.)

## Why the other judges don't get this

Every other LLM-judge in the project is **bucket A** — used to compare prompt variants and steer
iteration, never to make a reported absolute claim. For that job, consistent bias is harmless
(it cancels in the delta), so a human accuracy audit buys nothing. The cheap hygiene upgrades are
sufficient and worth adopting wherever those judges are used:

- **Stratified** cross-check samples (not just high/low — the current weak spot).
- **Independent blind** second-LLM relabel, *not* "have the second model review the first's scores"
  (reviewing anchors the second model to the first; independent relabel is the real cross-check).
- **CoT + explicit rubric** in the judge prompt.
- **Honest scoping**: "used to rank prompt variants, not to make absolute quality claims."

The dividing line is exactly **relative vs absolute**: a judge whose output is a *comparison*
needs only consistency; a judge whose output is *quoted as a level* needs calibration. Only the
strategy-adoption judge is in the second category.
